# Finite Observer - Constrained to single frequency/scale level
import numpy as np
from typing import Dict, Tuple, Optional

class FiniteObserver:
    """
    Each oscillation frequency level has a finite observer
    - Limited to its specific frequency range
    - Computes only local parameters at its scale
    - Cannot see cross-scale patterns (that's for transcendent observer)
    """
    
    def __init__(self, frequency_range: Tuple[float, float], 
                 scale_name: str, temporal_window: float):
        self.frequency_range = frequency_range  # (min_freq, max_freq)
        self.scale_name = scale_name           # 'molecular', 'cellular', 'systemic'
        self.temporal_window = temporal_window  # Maximum observation time
        self.local_state = {}                  # Current scale state
        self.information_capacity = self._calculate_finite_capacity()
    
    def _calculate_finite_capacity(self) -> float:
        """Finite observer has bounded information processing capacity"""
        freq_bandwidth = self.frequency_range[1] - self.frequency_range[0]
        return freq_bandwidth * self.temporal_window  # bits
    
    def observe_local_oscillations(self, sbml_components: Dict) -> Dict:
        """
        Observe only oscillations within this frequency range
        - Cannot see other scales
        - Provides local parameters for transcendent observer
        """
        local_oscillations = {}
        
        for component_id, component_data in sbml_components.items():
            # Filter to only observe oscillations in range
            component_freq = self._extract_component_frequency(component_data)
            
            if self.frequency_range[0] <= component_freq <= self.frequency_range[1]:
                local_oscillations[component_id] = {
                    'frequency': component_freq,
                    'amplitude': self._measure_amplitude(component_data),
                    'phase': self._measure_phase(component_data),
                    'local_coupling': self._measure_local_coupling(component_data)
                }
        
        self.local_state = local_oscillations
        return local_oscillations
    
    def provide_gear_interface(self) -> Dict:
        """
        Provide standardized interface for transcendent observer
        - Gear ratios will be calculated by transcendent observer
        - This observer only provides local measurements
        """
        if not self.local_state:
            return {}
            
        return {
            'scale': self.scale_name,
            'frequency_range': self.frequency_range,
            'dominant_frequency': self._calculate_dominant_frequency(),
            'total_oscillatory_energy': self._calculate_total_energy(),
            'local_parameters': self.local_state,
            'coupling_strengths': self._measure_coupling_strengths()
        }
    
    def _extract_component_frequency(self, component_data: Dict) -> float:
        """Extract characteristic frequency of biological component"""
        # Simplified - would use actual SBML kinetic parameters
        if 'kinetic_law' in component_data:
            return component_data.get('characteristic_frequency', 1.0)
        return 1.0
    
    def _measure_amplitude(self, component_data: Dict) -> float:
        """Measure oscillation amplitude at this scale"""
        return component_data.get('concentration', 1.0)
    
    def _measure_phase(self, component_data: Dict) -> float:
        """Measure oscillation phase at this scale"""
        return np.random.uniform(0, 2*np.pi)  # Simplified
    
    def _measure_local_coupling(self, component_data: Dict) -> float:
        """Measure coupling strength to other components at same scale"""
        return component_data.get('coupling_strength', 0.5)
    
    def _calculate_dominant_frequency(self) -> float:
        """Calculate the dominant frequency at this scale"""
        if not self.local_state:
            return sum(self.frequency_range) / 2
            
        frequencies = [comp['frequency'] for comp in self.local_state.values()]
        amplitudes = [comp['amplitude'] for comp in self.local_state.values()]
        
        # Weighted average by amplitude
        if amplitudes:
            return np.average(frequencies, weights=amplitudes)
        return sum(self.frequency_range) / 2
    
    def _calculate_total_energy(self) -> float:
        """Calculate total oscillatory energy at this scale"""
        if not self.local_state:
            return 0.0
            
        total_energy = 0.0
        for comp in self.local_state.values():
            # E = (1/2) * amplitude^2 * frequency^2
            total_energy += 0.5 * comp['amplitude']**2 * comp['frequency']**2
            
        return total_energy
    
    def _measure_coupling_strengths(self) -> Dict:
        """Measure coupling between components at this scale"""
        coupling_matrix = {}
        
        if len(self.local_state) < 2:
            return coupling_matrix
            
        components = list(self.local_state.keys())
        for i, comp1 in enumerate(components):
            for j, comp2 in enumerate(components[i+1:], i+1):
                freq1 = self.local_state[comp1]['frequency']
                freq2 = self.local_state[comp2]['frequency']
                
                # Coupling strength inversely related to frequency difference
                freq_diff = abs(freq1 - freq2)
                coupling = 1.0 / (1.0 + freq_diff)
                
                coupling_matrix[f"{comp1}-{comp2}"] = coupling
                
        return coupling_matrix
