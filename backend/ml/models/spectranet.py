"""
SpectraNet: A deep learning model for analysis and interpretation of mass spectrometry data
"""

import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import torch.optim as optim
import pandas as pd
from scipy.signal import savgol_filter
from sklearn.preprocessing import StandardScaler


class MassSpecDataset(Dataset):
    """Dataset class for mass spectrometry data"""
    def __init__(self, spectra, labels=None, transform=None):
        """
        Args:
            spectra (np.ndarray): Mass spectrometry spectra data with shape (n_samples, n_mz_values)
            labels (np.ndarray, optional): Labels for each spectrum if available
            transform (callable, optional): Transform to apply to the data
        """
        self.spectra = spectra
        self.labels = labels
        self.transform = transform
        
    def __len__(self):
        return len(self.spectra)
        
    def __getitem__(self, idx):
        spectrum = self.spectra[idx]
        
        if self.transform:
            spectrum = self.transform(spectrum)
            
        # Convert to tensor
        spectrum = torch.FloatTensor(spectrum)
        
        if self.labels is not None:
            label = self.labels[idx]
            label = torch.tensor(label)
            return spectrum, label
        else:
            return spectrum


class SpectraNetEncoder(nn.Module):
    """
    Neural network encoder for mass spectrometry data.
    Converts raw MS data into embeddings for further analysis.
    """
    def __init__(self, input_dim=2000, hidden_dims=[1024, 512, 256], latent_dim=128):
        super(SpectraNetEncoder, self).__init__()
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.latent_dim = latent_dim
        
        # Build encoder network
        modules = []
        
        # Input layer
        modules.append(nn.Linear(input_dim, hidden_dims[0]))
        modules.append(nn.BatchNorm1d(hidden_dims[0]))
        modules.append(nn.ReLU())
        
        # Hidden layers
        for i in range(len(hidden_dims) - 1):
            modules.append(nn.Linear(hidden_dims[i], hidden_dims[i+1]))
            modules.append(nn.BatchNorm1d(hidden_dims[i+1]))
            modules.append(nn.ReLU())
            modules.append(nn.Dropout(0.2))
            
        # Output layer
        modules.append(nn.Linear(hidden_dims[-1], latent_dim))
        
        self.encoder = nn.Sequential(*modules)
        
    def forward(self, x):
        return self.encoder(x)


class SpectraNetDecoder(nn.Module):
    """
    Neural network decoder for mass spectrometry data.
    Reconstructs MS data from latent embeddings.
    """
    def __init__(self, latent_dim=128, hidden_dims=[256, 512, 1024], output_dim=2000):
        super(SpectraNetDecoder, self).__init__()
        self.latent_dim = latent_dim
        self.hidden_dims = hidden_dims
        self.output_dim = output_dim
        
        # Build decoder network
        modules = []
        
        # Input layer
        modules.append(nn.Linear(latent_dim, hidden_dims[0]))
        modules.append(nn.BatchNorm1d(hidden_dims[0]))
        modules.append(nn.ReLU())
        
        # Hidden layers
        for i in range(len(hidden_dims) - 1):
            modules.append(nn.Linear(hidden_dims[i], hidden_dims[i+1]))
            modules.append(nn.BatchNorm1d(hidden_dims[i+1]))
            modules.append(nn.ReLU())
            modules.append(nn.Dropout(0.2))
            
        # Output layer
        modules.append(nn.Linear(hidden_dims[-1], output_dim))
        
        self.decoder = nn.Sequential(*modules)
        
    def forward(self, x):
        return self.decoder(x)


class SpectraNet:
    """
    SpectraNet: A model for analyzing and interpreting mass spectrometry data
    """
    def __init__(self, input_dim=2000, latent_dim=128, hidden_dims=[1024, 512, 256], 
                 device=None, model_path=None):
        """
        Initialize the SpectraNet model
        
        Args:
            input_dim (int): Dimension of input mass spec data
            latent_dim (int): Dimension of latent space
            hidden_dims (list): Dimensions of hidden layers
            device (str): Device to run model on ('cuda' or 'cpu')
            model_path (str): Path to load pre-trained model from
        """
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.hidden_dims = hidden_dims
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Initialize encoder and decoder
        self.encoder = SpectraNetEncoder(
            input_dim=input_dim,
            hidden_dims=hidden_dims,
            latent_dim=latent_dim
        ).to(self.device)
        
        self.decoder = SpectraNetDecoder(
            latent_dim=latent_dim,
            hidden_dims=list(reversed(hidden_dims)),
            output_dim=input_dim
        ).to(self.device)
        
        # Classifier for compound identification
        self.classifier = nn.Sequential(
            nn.Linear(latent_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1)  # For binary classification, change for multi-class
        ).to(self.device)
        
        # Load pre-trained model if available
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
            
        # Data preprocessing
        self.scaler = StandardScaler()
        
    def preprocess_spectrum(self, spectrum, normalize=True, denoise=True, align=True):
        """
        Preprocess a mass spectrometry spectrum
        
        Args:
            spectrum (np.ndarray): Raw mass spec data
            normalize (bool): Whether to normalize the spectrum
            denoise (bool): Whether to apply denoising
            align (bool): Whether to align peaks
            
        Returns:
            np.ndarray: Preprocessed spectrum
        """
        # Apply Savitzky-Golay filter for smoothing/denoising
        if denoise:
            window_length = min(11, len(spectrum) - 1 if len(spectrum) % 2 == 0 else len(spectrum) - 2)
            if window_length > 2:
                spectrum = savgol_filter(spectrum, window_length, 2)
        
        # Normalize to unit intensity
        if normalize:
            max_intensity = np.max(np.abs(spectrum))
            if max_intensity > 0:
                spectrum = spectrum / max_intensity
                
        # Additional alignment techniques would go here
        
        return spectrum
        
    def batch_preprocess(self, spectra_batch):
        """
        Preprocess a batch of spectra
        
        Args:
            spectra_batch (np.ndarray): Batch of raw spectra
            
        Returns:
            np.ndarray: Preprocessed spectra
        """
        processed = np.array([self.preprocess_spectrum(s) for s in spectra_batch])
        
        # Standardize the data
        if not hasattr(self, 'scaler_fitted') or not self.scaler_fitted:
            self.scaler.fit(processed)
            self.scaler_fitted = True
            
        return self.scaler.transform(processed)
        
    def get_embedding(self, spectrum):
        """
        Generate embedding for a spectrum
        
        Args:
            spectrum (np.ndarray): Mass spec data
            
        Returns:
            np.ndarray: Embedding vector
        """
        # Preprocess the spectrum
        processed = self.preprocess_spectrum(spectrum)
        processed = self.scaler.transform(processed.reshape(1, -1))
        
        # Convert to tensor
        input_tensor = torch.FloatTensor(processed).to(self.device)
        
        # Get embedding
        with torch.no_grad():
            embedding = self.encoder(input_tensor)
            return embedding.cpu().numpy().flatten()
            
    def train_autoencoder(self, spectra, batch_size=32, epochs=50, lr=0.001):
        """
        Train the autoencoder on mass spec data
        
        Args:
            spectra (np.ndarray): Training spectra
            batch_size (int): Batch size
            epochs (int): Number of epochs
            lr (float): Learning rate
            
        Returns:
            dict: Training metrics
        """
        # Preprocess data
        processed_spectra = self.batch_preprocess(spectra)
        
        # Create dataset and dataloader
        dataset = MassSpecDataset(processed_spectra)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        # Optimizer
        params = list(self.encoder.parameters()) + list(self.decoder.parameters())
        optimizer = optim.Adam(params, lr=lr)
        
        # Train autoencoder
        self.encoder.train()
        self.decoder.train()
        
        metrics = {'epoch_losses': []}
        
        for epoch in range(epochs):
            total_loss = 0
            
            for batch in dataloader:
                # Move batch to device
                if isinstance(batch, tuple):
                    batch = batch[0]  # If dataset returns (data, labels)
                batch = batch.to(self.device)
                
                # Zero gradients
                optimizer.zero_grad()
                
                # Forward pass
                latent = self.encoder(batch)
                recon = self.decoder(latent)
                
                # Reconstruction loss
                loss = F.mse_loss(recon, batch)
                
                # Backward and optimize
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
                
            # Record metrics
            avg_loss = total_loss / len(dataloader)
            metrics['epoch_losses'].append(avg_loss)
            print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.6f}")
            
        self.encoder.eval()
        self.decoder.eval()
        return metrics
        
    def train_classifier(self, spectra, labels, batch_size=32, epochs=30, lr=0.001):
        """
        Train the classifier for compound identification
        
        Args:
            spectra (np.ndarray): Training spectra
            labels (np.ndarray): Binary labels (0/1) for each spectrum
            batch_size (int): Batch size
            epochs (int): Number of epochs
            lr (float): Learning rate
            
        Returns:
            dict: Training metrics
        """
        # Preprocess data
        processed_spectra = self.batch_preprocess(spectra)
        
        # Create dataset and dataloader
        dataset = MassSpecDataset(processed_spectra, labels)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        # Freeze encoder weights
        for param in self.encoder.parameters():
            param.requires_grad = False
            
        # Optimizer for classifier only
        optimizer = optim.Adam(self.classifier.parameters(), lr=lr)
        
        # Loss function
        criterion = nn.BCEWithLogitsLoss()
        
        # Train classifier
        self.classifier.train()
        
        metrics = {'epoch_losses': [], 'epoch_accs': []}
        
        for epoch in range(epochs):
            total_loss = 0
            correct = 0
            total = 0
            
            for spectrum, label in dataloader:
                # Move data to device
                spectrum = spectrum.to(self.device)
                label = label.float().to(self.device)
                
                # Zero gradients
                optimizer.zero_grad()
                
                # Forward pass
                with torch.no_grad():
                    embedding = self.encoder(spectrum)
                
                output = self.classifier(embedding).squeeze()
                
                # Loss and accuracy
                loss = criterion(output, label)
                pred = (torch.sigmoid(output) > 0.5).float()
                correct += (pred == label).sum().item()
                total += label.size(0)
                
                # Backward and optimize
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
                
            # Record metrics
            avg_loss = total_loss / len(dataloader)
            accuracy = correct / total
            metrics['epoch_losses'].append(avg_loss)
            metrics['epoch_accs'].append(accuracy)
            print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}, Acc: {accuracy:.4f}")
            
        # Unfreeze encoder for future training
        for param in self.encoder.parameters():
            param.requires_grad = True
            
        self.classifier.eval()
        return metrics
        
    def predict(self, spectrum):
        """
        Predict compound presence from a spectrum
        
        Args:
            spectrum (np.ndarray): Mass spec data
            
        Returns:
            float: Probability of compound presence
        """
        # Preprocess
        processed = self.preprocess_spectrum(spectrum)
        processed = self.scaler.transform(processed.reshape(1, -1))
        
        # Convert to tensor
        input_tensor = torch.FloatTensor(processed).to(self.device)
        
        # Predict
        with torch.no_grad():
            embedding = self.encoder(input_tensor)
            output = self.classifier(embedding).squeeze()
            prob = torch.sigmoid(output).item()
            
        return prob
        
    def reconstruct(self, spectrum):
        """
        Reconstruct a spectrum from its embedding
        
        Args:
            spectrum (np.ndarray): Mass spec data
            
        Returns:
            np.ndarray: Reconstructed spectrum
        """
        # Preprocess
        processed = self.preprocess_spectrum(spectrum)
        processed = self.scaler.transform(processed.reshape(1, -1))
        
        # Convert to tensor
        input_tensor = torch.FloatTensor(processed).to(self.device)
        
        # Encode and decode
        with torch.no_grad():
            embedding = self.encoder(input_tensor)
            recon = self.decoder(embedding)
            
        # Convert back to original scale
        recon = self.scaler.inverse_transform(recon.cpu().numpy())
        
        return recon.flatten()
        
    def save_model(self, path):
        """Save model to disk"""
        state_dict = {
            'encoder': self.encoder.state_dict(),
            'decoder': self.decoder.state_dict(),
            'classifier': self.classifier.state_dict(),
            'input_dim': self.input_dim,
            'latent_dim': self.latent_dim,
            'hidden_dims': self.hidden_dims,
        }
        torch.save(state_dict, path)
        
    def load_model(self, path):
        """Load model from disk"""
        state_dict = torch.load(path, map_location=self.device)
        
        # Update model dimensions
        self.input_dim = state_dict.get('input_dim', self.input_dim)
        self.latent_dim = state_dict.get('latent_dim', self.latent_dim)
        self.hidden_dims = state_dict.get('hidden_dims', self.hidden_dims)
        
        # Rebuild models if dimensions changed
        if self.encoder.input_dim != self.input_dim or self.encoder.latent_dim != self.latent_dim:
            self.encoder = SpectraNetEncoder(
                input_dim=self.input_dim,
                hidden_dims=self.hidden_dims,
                latent_dim=self.latent_dim
            ).to(self.device)
            
            self.decoder = SpectraNetDecoder(
                latent_dim=self.latent_dim,
                hidden_dims=list(reversed(self.hidden_dims)),
                output_dim=self.input_dim
            ).to(self.device)
            
        # Load weights
        self.encoder.load_state_dict(state_dict['encoder'])
        self.decoder.load_state_dict(state_dict['decoder'])
        self.classifier.load_state_dict(state_dict['classifier'])
        
        # Set to eval mode
        self.encoder.eval()
        self.decoder.eval()
        self.classifier.eval()
