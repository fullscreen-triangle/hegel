#!/usr/bin/env python3
"""
Finite Observer - Methodical Scientific Implementation
====================================================

Each oscillation frequency level has a finite observer constrained to single frequency/scale level.
This module implements finite observers as methodical scientific experiments with comprehensive 
result saving, validation metrics, and visualization panels.

Key Features:
- Limited to specific frequency range and temporal window
- Bounded information processing capacity
- Local oscillation observation and measurement
- Standardized gear interface for transcendent observer
- Scientific result tracking and visualization
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Tuple, Optional, List, Any
import json
import os
from datetime import datetime
import pickle

class FiniteObserver:
    """
    Each oscillation frequency level has a finite observer
    - Limited to its specific frequency range
    - Computes only local parameters at its scale
    - Cannot see cross-scale patterns (that's for transcendent observer)
    """
    
    def __init__(self, frequency_range: Tuple[float, float], 
                 scale_name: str, temporal_window: float, observer_id: str = None):
        self.frequency_range = frequency_range  # (min_freq, max_freq)
        self.scale_name = scale_name           # 'molecular', 'cellular', 'systemic'
        self.temporal_window = temporal_window  # Maximum observation time
        self.local_state = {}                  # Current scale state
        self.information_capacity = self._calculate_finite_capacity()
        self.observer_id = observer_id or f"finite_{scale_name}_{datetime.now().strftime('%H%M%S')}"
        
        # Scientific tracking
        self.experiment_log = []
        self.measurements = []
        self.validation_metrics = {}
        self.results = {
            'observer_config': {
                'id': self.observer_id,
                'frequency_range': frequency_range,
                'scale_name': scale_name,
                'temporal_window': temporal_window,
                'information_capacity': self.information_capacity
            },
            'observations': [],
            'local_states': [],
            'gear_interface_data': [],
            'validation_results': {}
        }
    
    def _calculate_finite_capacity(self) -> float:
        """Finite observer has bounded information processing capacity"""
        freq_bandwidth = self.frequency_range[1] - self.frequency_range[0]
        return freq_bandwidth * self.temporal_window  # bits
    
    def observe_local_oscillations(self, sbml_components: Dict, timestamp: Optional[str] = None) -> Dict:
        """
        Observe only oscillations within this frequency range
        - Cannot see other scales
        - Provides local parameters for transcendent observer
        - Tracks all observations for scientific analysis
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        local_oscillations = {}
        observed_components = 0
        total_components = len(sbml_components)
        
        self.experiment_log.append({
            'timestamp': timestamp,
            'action': 'observe_local_oscillations',
            'total_components': total_components
        })
        
        for component_id, component_data in sbml_components.items():
            # Filter to only observe oscillations in range
            component_freq = self._extract_component_frequency(component_data)
            
            if self.frequency_range[0] <= component_freq <= self.frequency_range[1]:
                observation = {
                    'frequency': component_freq,
                    'amplitude': self._measure_amplitude(component_data),
                    'phase': self._measure_phase(component_data),
                    'local_coupling': self._measure_local_coupling(component_data),
                    'timestamp': timestamp,
                    'component_id': component_id
                }
                
                local_oscillations[component_id] = observation
                self.measurements.append(observation)
                observed_components += 1
        
        # Record observation statistics
        observation_stats = {
            'timestamp': timestamp,
            'total_components': total_components,
            'observed_components': observed_components,
            'observation_rate': observed_components / total_components if total_components > 0 else 0,
            'dominant_frequency': self._calculate_dominant_frequency_from_dict(local_oscillations),
            'total_energy': self._calculate_total_energy_from_dict(local_oscillations)
        }
        
        self.results['observations'].append(observation_stats)
        self.local_state = local_oscillations
        self.results['local_states'].append({
            'timestamp': timestamp,
            'state': local_oscillations.copy()
        })
        
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
    
    def _calculate_dominant_frequency_from_dict(self, oscillations: Dict) -> float:
        """Calculate dominant frequency from oscillations dictionary"""
        if not oscillations:
            return sum(self.frequency_range) / 2
            
        frequencies = [comp['frequency'] for comp in oscillations.values()]
        amplitudes = [comp['amplitude'] for comp in oscillations.values()]
        
        # Weighted average by amplitude
        if amplitudes:
            return np.average(frequencies, weights=amplitudes)
        return sum(self.frequency_range) / 2
    
    def _calculate_total_energy_from_dict(self, oscillations: Dict) -> float:
        """Calculate total energy from oscillations dictionary"""
        if not oscillations:
            return 0.0
            
        total_energy = 0.0
        for comp in oscillations.values():
            # E = (1/2) * amplitude^2 * frequency^2
            total_energy += 0.5 * comp['amplitude']**2 * comp['frequency']**2
            
        return total_energy
    
    def validate_observer_performance(self) -> Dict[str, Any]:
        """Validate the finite observer's performance with scientific metrics"""
        
        validation = {
            'information_capacity_utilization': 0.0,
            'observation_consistency': 0.0,
            'frequency_selectivity': 0.0,
            'temporal_stability': 0.0,
            'measurement_precision': 0.0
        }
        
        if not self.measurements:
            self.validation_metrics = validation
            return validation
        
        # 1. Information capacity utilization
        total_observed = len(self.measurements)
        max_capacity = self.information_capacity
        validation['information_capacity_utilization'] = min(total_observed / max_capacity, 1.0) if max_capacity > 0 else 0
        
        # 2. Observation consistency (frequency distribution)
        frequencies = [m['frequency'] for m in self.measurements]
        if frequencies:
            freq_std = np.std(frequencies)
            freq_mean = np.mean(frequencies)
            validation['observation_consistency'] = 1.0 / (1.0 + freq_std/freq_mean) if freq_mean > 0 else 0
        
        # 3. Frequency selectivity (how well it stays within range)
        in_range_count = sum(1 for f in frequencies if self.frequency_range[0] <= f <= self.frequency_range[1])
        validation['frequency_selectivity'] = in_range_count / len(frequencies) if frequencies else 0
        
        # 4. Temporal stability (consistency over time)
        if len(self.results['observations']) > 1:
            observation_rates = [obs['observation_rate'] for obs in self.results['observations']]
            rate_std = np.std(observation_rates)
            rate_mean = np.mean(observation_rates)
            validation['temporal_stability'] = 1.0 / (1.0 + rate_std/rate_mean) if rate_mean > 0 else 0
        
        # 5. Measurement precision (amplitude consistency)
        amplitudes = [m['amplitude'] for m in self.measurements]
        if amplitudes:
            amp_cv = np.std(amplitudes) / np.mean(amplitudes) if np.mean(amplitudes) > 0 else 1
            validation['measurement_precision'] = 1.0 / (1.0 + amp_cv)
        
        self.validation_metrics = validation
        self.results['validation_results'] = validation
        
        return validation
    
    def generate_scientific_report(self, output_dir: str = "finite_observer_results"):
        """Generate comprehensive scientific report with visualizations"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Ensure we have validation metrics
        if not self.validation_metrics:
            self.validate_observer_performance()
        
        # Create comprehensive visualization panel
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(f'Finite Observer Scientific Analysis: {self.observer_id}', 
                    fontsize=16, fontweight='bold')
        
        # 1. Frequency distribution of observations
        ax1 = axes[0, 0]
        if self.measurements:
            frequencies = [m['frequency'] for m in self.measurements]
            ax1.hist(frequencies, bins=20, alpha=0.7, color='blue', edgecolor='black')
            ax1.axvline(self.frequency_range[0], color='red', linestyle='--', label='Range Min')
            ax1.axvline(self.frequency_range[1], color='red', linestyle='--', label='Range Max')
            ax1.set_xlabel('Frequency (Hz)')
            ax1.set_ylabel('Count')
            ax1.set_title('Frequency Distribution of Observations')
            ax1.legend()
        else:
            ax1.text(0.5, 0.5, 'No observations recorded', ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title('Frequency Distribution (No Data)')
        
        # 2. Amplitude vs Frequency scatter
        ax2 = axes[0, 1]
        if self.measurements:
            frequencies = [m['frequency'] for m in self.measurements]
            amplitudes = [m['amplitude'] for m in self.measurements]
            ax2.scatter(frequencies, amplitudes, alpha=0.6, color='green')
            ax2.set_xlabel('Frequency (Hz)')
            ax2.set_ylabel('Amplitude')
            ax2.set_title('Amplitude vs Frequency')
        else:
            ax2.text(0.5, 0.5, 'No measurements available', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Amplitude vs Frequency (No Data)')
        
        # 3. Observation rate over time
        ax3 = axes[0, 2]
        if self.results['observations']:
            times = range(len(self.results['observations']))
            rates = [obs['observation_rate'] for obs in self.results['observations']]
            ax3.plot(times, rates, 'o-', color='purple', alpha=0.7)
            ax3.set_xlabel('Observation Number')
            ax3.set_ylabel('Observation Rate')
            ax3.set_title('Observation Rate Over Time')
            ax3.grid(True, alpha=0.3)
        else:
            ax3.text(0.5, 0.5, 'No observation history', ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Observation Rate (No Data)')
        
        # 4. Validation metrics radar chart
        ax4 = axes[1, 0]
        if self.validation_metrics:
            metrics = list(self.validation_metrics.keys())
            values = list(self.validation_metrics.values())
            
            angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False)
            values += values[:1]  # Complete the circle
            angles = np.concatenate([angles, [angles[0]]])
            
            ax4 = fig.add_subplot(2, 3, 4, projection='polar')
            ax4.plot(angles, values, 'o-', linewidth=2, color='red')
            ax4.fill(angles, values, alpha=0.25, color='red')
            ax4.set_xticks(angles[:-1])
            ax4.set_xticklabels([m.replace('_', '\n') for m in metrics])
            ax4.set_ylim(0, 1)
            ax4.set_title('Validation Metrics')
        else:
            ax4.text(0.5, 0.5, 'No validation metrics', ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('Validation Metrics (No Data)')
        
        # 5. Energy distribution
        ax5 = axes[1, 1]
        if self.results['observations']:
            energies = [obs['total_energy'] for obs in self.results['observations']]
            ax5.plot(range(len(energies)), energies, 's-', color='orange', alpha=0.7)
            ax5.set_xlabel('Observation Number')
            ax5.set_ylabel('Total Energy')
            ax5.set_title('Total Energy Over Time')
            ax5.grid(True, alpha=0.3)
        else:
            ax5.text(0.5, 0.5, 'No energy data', ha='center', va='center', transform=ax5.transAxes)
            ax5.set_title('Energy Analysis (No Data)')
        
        # 6. Observer configuration and statistics
        ax6 = axes[1, 2]
        config_text = f"""Observer Configuration:
        
ID: {self.observer_id}
Scale: {self.scale_name}
Frequency Range: {self.frequency_range[0]:.2e} - {self.frequency_range[1]:.2e} Hz
Temporal Window: {self.temporal_window:.2e} s
Information Capacity: {self.information_capacity:.2e} bits

Performance Statistics:
Total Measurements: {len(self.measurements)}
Total Observations: {len(self.results['observations'])}
Experiment Log Entries: {len(self.experiment_log)}

Latest Metrics:
Capacity Utilization: {self.validation_metrics.get('information_capacity_utilization', 0):.3f}
Frequency Selectivity: {self.validation_metrics.get('frequency_selectivity', 0):.3f}
Temporal Stability: {self.validation_metrics.get('temporal_stability', 0):.3f}
        """
        
        ax6.text(0.05, 0.95, config_text, transform=ax6.transAxes, 
                verticalalignment='top', fontfamily='monospace', fontsize=8)
        ax6.set_title('Observer Configuration & Stats')
        ax6.axis('off')
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/{self.observer_id}_analysis.png", dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Scientific analysis saved to {output_dir}/{self.observer_id}_analysis.png")
    
    def save_results(self, output_dir: str = "finite_observer_results"):
        """Save all experimental results and data"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Save main results as JSON
        with open(f"{output_dir}/{self.observer_id}_results.json", 'w') as f:
            json.dump(self.results, f, indent=4, default=str)
        
        # Save measurements as CSV
        if self.measurements:
            measurements_df = pd.DataFrame(self.measurements)
            measurements_df.to_csv(f"{output_dir}/{self.observer_id}_measurements.csv", index=False)
        
        # Save experiment log as CSV
        if self.experiment_log:
            log_df = pd.DataFrame(self.experiment_log)
            log_df.to_csv(f"{output_dir}/{self.observer_id}_experiment_log.csv", index=False)
        
        # Save observer state as pickle for reuse
        with open(f"{output_dir}/{self.observer_id}_observer_state.pickle", 'wb') as f:
            pickle.dump(self, f)
        
        print(f"Results saved to {output_dir}/")
        return f"{output_dir}/{self.observer_id}_results.json"


def create_example_finite_observers() -> List[FiniteObserver]:
    """Create example finite observers at different scales for testing"""
    
    observers = [
        # Molecular scale observer
        FiniteObserver(
            frequency_range=(1e12, 1e15),  # THz range
            scale_name="molecular",
            temporal_window=1e-12,  # picoseconds
            observer_id="molecular_observer"
        ),
        
        # Cellular scale observer  
        FiniteObserver(
            frequency_range=(1e3, 1e6),   # kHz to MHz
            scale_name="cellular", 
            temporal_window=1e-3,   # milliseconds
            observer_id="cellular_observer"
        ),
        
        # Tissue scale observer
        FiniteObserver(
            frequency_range=(1e0, 1e3),   # Hz to kHz
            scale_name="tissue",
            temporal_window=1e0,    # seconds
            observer_id="tissue_observer"
        )
    ]
    
    return observers


def create_example_sbml_components() -> Dict:
    """Create example SBML components for testing"""
    
    components = {
        # Molecular level components
        'ATP_synthase': {
            'characteristic_frequency': 1e13,  # 10 THz
            'concentration': 1.5,
            'coupling_strength': 0.8,
            'kinetic_law': 'michaelis_menten'
        },
        
        'glucose_transporter': {
            'characteristic_frequency': 5e12,  # 5 THz  
            'concentration': 0.8,
            'coupling_strength': 0.6,
            'kinetic_law': 'mass_action'
        },
        
        # Cellular level components
        'calcium_pump': {
            'characteristic_frequency': 1e5,   # 100 kHz
            'concentration': 2.1,
            'coupling_strength': 0.9,
            'kinetic_law': 'hill_equation'
        },
        
        'membrane_potential': {
            'characteristic_frequency': 5e4,   # 50 kHz
            'concentration': 1.2,
            'coupling_strength': 0.7,
            'kinetic_law': 'voltage_gated'
        },
        
        # Tissue level components
        'heart_rhythm': {
            'characteristic_frequency': 1.2,   # 1.2 Hz
            'concentration': 1.0,
            'coupling_strength': 0.95,
            'kinetic_law': 'pacemaker'
        },
        
        'breathing_control': {
            'characteristic_frequency': 0.3,   # 0.3 Hz  
            'concentration': 1.0,
            'coupling_strength': 0.85,
            'kinetic_law': 'respiratory_center'
        }
    }
    
    return components


def main():
    """Main function for testing finite observer system methodically"""
    
    print("="*70)
    print("FINITE OBSERVER METHODICAL SCIENTIFIC EXPERIMENT")
    print("="*70)
    
    # Create observers at different scales
    observers = create_example_finite_observers()
    
    # Create example biological components
    sbml_components = create_example_sbml_components()
    
    print(f"Created {len(observers)} finite observers:")
    for obs in observers:
        print(f"  - {obs.observer_id}: {obs.scale_name} scale, "
              f"freq range {obs.frequency_range[0]:.0e}-{obs.frequency_range[1]:.0e} Hz")
    
    print(f"\nTesting with {len(sbml_components)} SBML components")
    
    # Run observations for each observer
    for i, observer in enumerate(observers):
        print(f"\n--- Running Experiment {i+1}: {observer.observer_id} ---")
        
        # Perform multiple observations to test temporal behavior
        for t in range(3):
            timestamp = f"2024-01-01T10:{t:02d}:00"
            print(f"Observation {t+1} at {timestamp}")
            
            observations = observer.observe_local_oscillations(sbml_components, timestamp)
            print(f"  Observed {len(observations)} components in frequency range")
            
            gear_interface = observer.provide_gear_interface()
            observer.results['gear_interface_data'].append({
                'timestamp': timestamp,
                'gear_data': gear_interface.copy()
            })
        
        # Validate observer performance
        print("Validating observer performance...")
        validation = observer.validate_observer_performance()
        
        print("Validation Results:")
        for metric, value in validation.items():
            print(f"  {metric}: {value:.3f}")
        
        # Generate scientific report
        print("Generating scientific report...")
        observer_dir = f"finite_observer_results/{observer.observer_id}"
        observer.generate_scientific_report(observer_dir)
        
        # Save results
        print("Saving experimental data...")
        result_file = observer.save_results(observer_dir)
        print(f"Results saved to: {result_file}")
    
    # Summary analysis
    print("\n" + "="*70)
    print("EXPERIMENT SUMMARY")
    print("="*70)
    
    total_measurements = sum(len(obs.measurements) for obs in observers)
    print(f"Total measurements across all observers: {total_measurements}")
    
    print(f"\nObserver Performance Summary:")
    for obs in observers:
        if obs.validation_metrics:
            selectivity = obs.validation_metrics['frequency_selectivity']
            stability = obs.validation_metrics['temporal_stability']
            print(f"  {obs.observer_id}: Selectivity={selectivity:.3f}, Stability={stability:.3f}")
    
    print(f"\nResults saved in: finite_observer_results/")
    print("Each observer has comprehensive analysis and visualizations!")
    
    print("\n" + "="*70)
    print("FINITE OBSERVER EXPERIMENT COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
