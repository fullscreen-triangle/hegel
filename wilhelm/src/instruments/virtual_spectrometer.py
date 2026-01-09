"""
Virtual Categorical Spectrometer

Primary measurement instrument that exists only during observation.
Activates secondary instruments for sequential validation.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PartitionCoordinates:
    """Partition coordinates (n, ℓ, m, s)"""
    n: int  # Principal quantum number
    l: int  # Angular momentum
    m: int  # Magnetic quantum number
    s: float  # Spin (+1/2 or -1/2)
    
    def capacity(self) -> int:
        """2n² capacity theorem"""
        return 2 * self.n**2
    
    def is_valid(self) -> bool:
        """Validate partition coordinate constraints"""
        if self.n < 1:
            return False
        if not (0 <= self.l < self.n):
            return False
        if not (-self.l <= self.m <= self.l):
            return False
        if self.s not in [-0.5, 0.5]:
            return False
        return True


@dataclass
class SEntropyCoordinates:
    """S-entropy coordinates (S_k, S_t, S_e) ∈ [0,1]³"""
    S_k: float  # Knowledge entropy
    S_t: float  # Temporal entropy
    S_e: float  # Evolution entropy
    
    def is_valid(self) -> bool:
        """Validate S-entropy bounds"""
        return (0 <= self.S_k <= 1 and 
                0 <= self.S_t <= 1 and 
                0 <= self.S_e <= 1)
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array"""
        return np.array([self.S_k, self.S_t, self.S_e])


class VirtualCategoricalSpectrometer:
    """
    Virtual spectrometer that exists only during measurement.
    
    Measures partition coordinates through frequency/energy analysis,
    then validates through sequential instrument activation.
    """
    
    def __init__(self):
        self.is_active = False
        self.current_measurement = None
        self.validation_chain = []
        
    def activate(self):
        """Open categorical aperture"""
        self.is_active = True
        self.validation_chain = []
        
    def deactivate(self):
        """Close categorical aperture"""
        self.is_active = False
        self.current_measurement = None
        self.validation_chain = []
    
    def measure_partition_coordinates(
        self, 
        frequency: float,
        temperature: float = 300.0
    ) -> PartitionCoordinates:
        """
        Measure partition coordinates from frequency.
        
        Energy: E = hν = k_B T × (structure factor)
        Principal quantum number: n ~ √(E / E_0)
        """
        if not self.is_active:
            raise RuntimeError("Spectrometer not active. Call activate() first.")
        
        # Physical constants
        h = 6.62607015e-34  # Planck constant [J·s]
        k_B = 1.380649e-23  # Boltzmann constant [J/K]
        
        # Energy from frequency
        E = h * frequency
        
        # Thermal energy scale
        E_thermal = k_B * temperature
        
        # Principal quantum number from energy
        # n ~ √(E / E_thermal)
        n = max(1, int(np.sqrt(E / E_thermal)))
        
        # Angular momentum from partition structure
        # For thermal equilibrium, ℓ distributed over [0, n-1]
        # Use most probable value: ℓ ~ n/2
        l = max(0, n // 2)
        
        # Magnetic quantum number
        # For unpolarized sample, m = 0 most probable
        m = 0
        
        # Spin (assume unpolarized, random)
        s = 0.5 if np.random.random() > 0.5 else -0.5
        
        coords = PartitionCoordinates(n=n, l=l, m=m, s=s)
        
        if not coords.is_valid():
            # Fallback to ground state
            coords = PartitionCoordinates(n=1, l=0, m=0, s=0.5)
        
        self.current_measurement = coords
        return coords
    
    def partition_to_sentropy(
        self, 
        coords: PartitionCoordinates
    ) -> SEntropyCoordinates:
        """
        Transform partition coordinates to S-entropy coordinates.
        
        S_k(n,ℓ) = 1/(1 + exp(-α_k(n²/(ℓ+1) - β_k)))
        S_t(n,m) = 1/(1 + exp(-α_t(n²/(|m|+1) - β_t)))
        S_e(n,s) = 1/(1 + exp(-α_e(n²/(2|s|+1) - β_e)))
        """
        # Scaling parameters (chosen to map [1,∞) → [0,1])
        alpha_k = 0.1
        alpha_t = 0.1
        alpha_e = 0.1
        beta_k = 5.0
        beta_t = 5.0
        beta_e = 5.0
        
        # S_k: Knowledge entropy
        x_k = coords.n**2 / (coords.l + 1) - beta_k
        S_k = 1.0 / (1.0 + np.exp(-alpha_k * x_k))
        
        # S_t: Temporal entropy
        x_t = coords.n**2 / (abs(coords.m) + 1) - beta_t
        S_t = 1.0 / (1.0 + np.exp(-alpha_t * x_t))
        
        # S_e: Evolution entropy
        x_e = coords.n**2 / (2 * abs(coords.s) + 1) - beta_e
        S_e = 1.0 / (1.0 + np.exp(-alpha_e * x_e))
        
        return SEntropyCoordinates(S_k=S_k, S_t=S_t, S_e=S_e)
    
    def validate_with_instruments(
        self,
        coords: PartitionCoordinates,
        instruments: List[str]
    ) -> Dict[str, float]:
        """
        Sequential validation through multiple instruments.
        
        Returns ambiguity reduction at each step.
        """
        if not self.is_active:
            raise RuntimeError("Spectrometer not active.")
        
        # Initial ambiguity (all possible configurations)
        N_0 = 1e60  # ~10^60 possible microscopic states
        
        # Exclusion factors per instrument
        exclusion_factors = {
            'vibration': 1e-15,
            'dielectric': 1e-15,
            'em_field': 1e-15,
            'microscopy': 1e-15
        }
        
        ambiguity = N_0
        results = {'initial': N_0}
        
        for i, instrument in enumerate(instruments):
            epsilon = exclusion_factors.get(instrument, 1e-10)
            ambiguity *= epsilon
            results[f'after_{instrument}'] = ambiguity
            self.validation_chain.append((instrument, ambiguity))
        
        results['final'] = ambiguity
        results['unique'] = ambiguity < 10  # Essentially unique determination
        
        return results
    
    def frequency_from_partition(
        self,
        coords: PartitionCoordinates,
        temperature: float = 300.0
    ) -> float:
        """
        Calculate frequency from partition coordinates.
        
        Inverse of measure_partition_coordinates.
        """
        k_B = 1.380649e-23
        h = 6.62607015e-34
        
        # Energy from partition coordinates
        E = k_B * temperature * coords.n**2
        
        # Frequency from energy
        frequency = E / h
        
        return frequency
