"""
MoleculeMapper: A model for mapping molecular structures and identifiers across different databases
and notation systems.
"""

import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors

class MolecularEncoder(nn.Module):
    """
    Neural network model to encode molecular structures into embeddings.
    Uses a graph neural network architecture to process molecular graphs.
    """
    def __init__(self, input_dim=300, hidden_dim=256, output_dim=128):
        super(MolecularEncoder, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        
        # Encoder layers
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, output_dim)
        
        self.dropout = nn.Dropout(0.2)
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.bn2 = nn.BatchNorm1d(hidden_dim)
        
    def forward(self, x):
        # Encoder
        x = F.relu(self.bn1(self.fc1(x)))
        x = self.dropout(x)
        x = F.relu(self.bn2(self.fc2(x)))
        x = self.dropout(x)
        x = self.fc3(x)
        return x


class MoleculeMapper:
    """
    MoleculeMapper provides functionality to convert molecular identifiers and structures
    between different formats and to compute similarity between molecules.
    """
    def __init__(self, model_path=None, device=None):
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        self.encoder = MolecularEncoder().to(self.device)
        
        # Load pre-trained model if available
        if model_path and os.path.exists(model_path):
            self.encoder.load_state_dict(torch.load(model_path, map_location=self.device))
            self.encoder.eval()
        
        # Database of known molecular identifiers
        self.id_mappings = {
            # Dictionary mapping between various identifier systems
            # Example: 'CHEBI:12345': {'pubchem': '123456', 'drugbank': 'DB00123'}
        }
        
    def molecule_to_fingerprint(self, mol_smiles):
        """
        Convert a molecule from SMILES to Morgan fingerprint.
        
        Args:
            mol_smiles (str): SMILES representation of the molecule
            
        Returns:
            np.ndarray: Morgan fingerprint as a numpy array
        """
        try:
            mol = Chem.MolFromSmiles(mol_smiles)
            if mol is None:
                raise ValueError(f"Could not parse SMILES: {mol_smiles}")
                
            # Generate Morgan fingerprint
            fingerprint = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
            return np.array(fingerprint)
        except Exception as e:
            raise ValueError(f"Error generating fingerprint: {str(e)}")
            
    def get_embedding(self, mol_smiles):
        """
        Generate an embedding vector for a molecule.
        
        Args:
            mol_smiles (str): SMILES representation of the molecule
            
        Returns:
            np.ndarray: Embedding vector
        """
        fingerprint = self.molecule_to_fingerprint(mol_smiles)
        
        # Convert to tensor and get embedding
        with torch.no_grad():
            input_tensor = torch.FloatTensor(fingerprint).to(self.device)
            if input_tensor.dim() == 1:
                input_tensor = input_tensor.unsqueeze(0)
                
            embedding = self.encoder(input_tensor)
            return embedding.cpu().numpy().flatten()
            
    def calculate_similarity(self, mol_smiles1, mol_smiles2):
        """
        Calculate similarity between two molecules.
        
        Args:
            mol_smiles1 (str): SMILES representation of first molecule
            mol_smiles2 (str): SMILES representation of second molecule
            
        Returns:
            float: Similarity score between 0 and 1
        """
        embedding1 = self.get_embedding(mol_smiles1)
        embedding2 = self.get_embedding(mol_smiles2)
        
        # Calculate cosine similarity
        similarity = F.cosine_similarity(
            torch.FloatTensor(embedding1).unsqueeze(0),
            torch.FloatTensor(embedding2).unsqueeze(0)
        ).item()
        
        return (similarity + 1) / 2  # Convert from [-1, 1] to [0, 1]
        
    def map_identifier(self, molecule_id, source_db='chebi', target_db='pubchem'):
        """
        Map a molecular identifier from one database to another.
        
        Args:
            molecule_id (str): Molecule identifier
            source_db (str): Source database name
            target_db (str): Target database name
            
        Returns:
            str: Mapped identifier or None if not found
        """
        # Try direct mapping from known dictionary
        if molecule_id in self.id_mappings:
            mappings = self.id_mappings[molecule_id]
            if target_db in mappings:
                return mappings[target_db]
                
        # TODO: Add API calls to public databases for more comprehensive mapping
        
        return None
        
    def infer_properties(self, mol_smiles):
        """
        Infer molecular properties from SMILES representation.
        
        Args:
            mol_smiles (str): SMILES representation of the molecule
            
        Returns:
            dict: Dictionary of molecular properties
        """
        try:
            mol = Chem.MolFromSmiles(mol_smiles)
            if mol is None:
                raise ValueError(f"Could not parse SMILES: {mol_smiles}")
                
            # Calculate basic properties
            properties = {
                'molecular_weight': Descriptors.MolWt(mol),
                'logp': Descriptors.MolLogP(mol),
                'num_h_donors': Descriptors.NumHDonors(mol),
                'num_h_acceptors': Descriptors.NumHAcceptors(mol),
                'num_rotatable_bonds': Descriptors.NumRotatableBonds(mol),
                'num_heavy_atoms': mol.GetNumHeavyAtoms(),
                'formula': Chem.rdMolDescriptors.CalcMolFormula(mol)
            }
            
            return properties
        except Exception as e:
            raise ValueError(f"Error inferring properties: {str(e)}")
            
    def train(self, smiles_list, batch_size=32, epochs=10, lr=0.001):
        """
        Train the molecular encoder model on a dataset of SMILES strings.
        
        Args:
            smiles_list (list): List of SMILES strings
            batch_size (int): Batch size for training
            epochs (int): Number of training epochs
            lr (float): Learning rate
            
        Returns:
            dict: Training metrics
        """
        self.encoder.train()
        
        # Prepare data
        fingerprints = []
        for smiles in smiles_list:
            try:
                fp = self.molecule_to_fingerprint(smiles)
                fingerprints.append(fp)
            except:
                continue
                
        if not fingerprints:
            raise ValueError("No valid molecules for training")
            
        # Convert to tensor
        train_data = torch.FloatTensor(np.array(fingerprints)).to(self.device)
        
        # Set up optimizer
        optimizer = torch.optim.Adam(self.encoder.parameters(), lr=lr)
        
        # Training loop with contrastive learning objectives
        metrics = {'epoch_losses': []}
        
        for epoch in range(epochs):
            total_loss = 0
            
            # Process in batches
            for i in range(0, len(train_data), batch_size):
                batch = train_data[i:i+batch_size]
                
                # Zero gradients
                optimizer.zero_grad()
                
                # Forward pass
                embeddings = self.encoder(batch)
                
                # Calculate contrastive loss
                loss = self._contrastive_loss(embeddings)
                
                # Backward and optimize
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
                
            # Record metrics
            avg_loss = total_loss / (len(train_data) // batch_size)
            metrics['epoch_losses'].append(avg_loss)
            print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
            
        self.encoder.eval()
        return metrics
        
    def _contrastive_loss(self, embeddings, temperature=0.5):
        """
        Contrastive loss function for training the encoder.
        
        Args:
            embeddings (torch.Tensor): Batch of embeddings
            temperature (float): Temperature parameter for softmax
            
        Returns:
            torch.Tensor: Loss value
        """
        # Normalize embeddings
        embeddings_norm = F.normalize(embeddings, p=2, dim=1)
        
        # Compute similarity matrix
        similarity_matrix = torch.matmul(embeddings_norm, embeddings_norm.t()) / temperature
        
        # Mask out self-similarity
        mask = torch.eye(similarity_matrix.size(0), device=self.device)
        mask = 1 - mask
        
        # Compute loss
        similarity_matrix = similarity_matrix * mask
        positives = similarity_matrix.diag()
        negatives = similarity_matrix.sum(dim=1) - positives
        
        loss = -torch.log(torch.exp(positives) / (torch.exp(positives) + negatives)).mean()
        
        return loss
        
    def save_model(self, path):
        """Save encoder model to disk."""
        torch.save(self.encoder.state_dict(), path)
