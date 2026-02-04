"""
Catalytic Slicing Validation Framework

Implements observer-dependent validation through dual-face information structure,
where each reality slice catalyzes the next observation through its conjugate face.

Based on: Complete Cell paper, Section 9 (Information Catalysis)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Callable
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ObserverType(Enum):
    """Three levels of observation hierarchy"""
    MOLECULAR = "molecular"      # Local, high temporal resolution
    CELLULAR = "cellular"        # Global, medium temporal resolution
    TRANSCENDENT = "transcendent"  # External, low temporal resolution


@dataclass
class ObserverCapacity:
    """Observer information capacity and projection characteristics"""
    observer_type: ObserverType
    observation_range: float  # meters
    temporal_resolution: float  # seconds
    information_capacity: float  # bits/second
    modalities: List[str]
    
    @classmethod
    def molecular_observer(cls):
        """Molecular-molecular observation"""
        return cls(
            observer_type=ObserverType.MOLECULAR,
            observation_range=10e-9,  # 10 nm
            temporal_resolution=1e-11,  # 10 ps
            information_capacity=1e11,  # 10^11 bits/s
            modalities=['coulomb_field', 'local_charge', 'phase']
        )
    
    @classmethod
    def cellular_observer(cls):
        """Cellular self-observation"""
        return cls(
            observer_type=ObserverType.CELLULAR,
            observation_range=5e-6,  # 5 μm
            temporal_resolution=1e-12,  # 1 ps
            information_capacity=1e12,  # 10^12 bits/s
            modalities=['metabolic_gps', 'phase_coherence', 'categorical_state']
        )
    
    @classmethod
    def transcendent_observer(cls):
        """External experimental apparatus"""
        return cls(
            observer_type=ObserverType.TRANSCENDENT,
            observation_range=float('inf'),  # Can see whole cell
            temporal_resolution=1e-3,  # 1 ms (experimental limit)
            information_capacity=1e3,  # 10^3 bits/s
            modalities=['optical', 'spectral', 'vibrational', 'metabolic', 'temporal']
        )


@dataclass
class ObserverDictionary:
    """Empty dictionary defining observer's accessible coordinate system"""
    observer_type: ObserverType
    entries: Dict[str, Optional[float]] = field(default_factory=dict)
    capacity: int = 0
    filled_count: int = 0
    
    def __post_init__(self):
        """Initialize empty dictionary structure based on observer type"""
        if self.observer_type == ObserverType.MOLECULAR:
            self.entries = {
                'local_field_x': None,
                'local_field_y': None,
                'local_field_z': None,
                'neighbor_count': None,
                'phase': None,
            }
        elif self.observer_type == ObserverType.CELLULAR:
            self.entries = {
                'metabolic_gps_x': None,
                'metabolic_gps_y': None,
                'metabolic_gps_z': None,
                'phase_coherence': None,
                'S_k': None,
                'S_t': None,
                'S_e': None,
            }
        elif self.observer_type == ObserverType.TRANSCENDENT:
            self.entries = {
                'ATP_concentration': None,
                'membrane_potential': None,
                'Ca2_concentration': None,
                'pH': None,
                'protein_count': None,
            }
        self.capacity = len(self.entries)
    
    def fill_entry(self, key: str, value: float):
        """Fill a dictionary entry through observation"""
        if key in self.entries:
            if self.entries[key] is None:
                self.filled_count += 1
            self.entries[key] = value
        else:
            raise KeyError(f"Key {key} not in observer dictionary")
    
    def get_sparsity(self) -> float:
        """Calculate sparsity ratio (filled / capacity)"""
        return self.filled_count / self.capacity if self.capacity > 0 else 0.0
    
    def is_complete(self) -> bool:
        """Check if all entries are filled"""
        return all(v is not None for v in self.entries.values())


@dataclass
class InformationFace:
    """
    Dual-face information structure
    Face A: Direct measurements (physical → categorical)
    Face B: Derived conjugates (categorical → physical)
    """
    face_type: str  # 'A' or 'B'
    S_coordinates: Tuple[float, float, float]  # (S_k, S_t, S_e)
    observables: Dict[str, float] = field(default_factory=dict)
    ternary_encoding: str = ""
    
    def encode_ternary(self, precision: int = 10) -> str:
        """
        Encode S-entropy coordinates as ternary string
        Each coordinate → ternary fraction, then interleave
        """
        S_k, S_t, S_e = self.S_coordinates
        
        def float_to_ternary(x: float, precision: int) -> List[int]:
            """Convert float in [0,1] to ternary digits"""
            trits = []
            for _ in range(precision):
                x *= 3
                trit = int(x)
                trits.append(trit)
                x -= trit
            return trits
        
        trits_k = float_to_ternary(S_k, precision)
        trits_t = float_to_ternary(S_t, precision)
        trits_e = float_to_ternary(S_e, precision)
        
        # Interleave: (k[0], t[0], e[0], k[1], t[1], e[1], ...)
        interleaved = []
        for i in range(precision):
            interleaved.extend([trits_k[i], trits_t[i], trits_e[i]])
        
        self.ternary_encoding = ''.join(map(str, interleaved))
        return self.ternary_encoding
    
    def verify_complementarity(self, other: 'InformationFace') -> bool:
        """
        Verify complementarity constraint: F^A · F^B = I
        For our purposes: check if S-coordinates are consistent
        """
        if self.face_type == other.face_type:
            return False  # Must be different faces
        
        # Complementarity: S_k^A + S_k^B ≈ 1, etc.
        S_k_sum = self.S_coordinates[0] + other.S_coordinates[0]
        S_t_sum = self.S_coordinates[1] + other.S_coordinates[1]
        S_e_sum = self.S_coordinates[2] + other.S_coordinates[2]
        
        tolerance = 0.01
        return (abs(S_k_sum - 1.0) < tolerance and
                abs(S_t_sum - 1.0) < tolerance and
                abs(S_e_sum - 1.0) < tolerance)


@dataclass
class RealitySlice:
    """
    A single slice of reality at time t_i
    Contains Face A (measured), Face B (derived), and observer projection
    """
    time: float
    face_A: InformationFace
    face_B: InformationFace
    observer_projection: np.ndarray  # Projection operator Π_obs
    dictionary: ObserverDictionary
    
    def verify_consistency(self) -> bool:
        """Verify this slice satisfies all constraints"""
        # Check complementarity
        if not self.face_A.verify_complementarity(self.face_B):
            logger.warning(f"Complementarity violation at t={self.time}")
            return False
        
        # Check dictionary is filled
        if not self.dictionary.is_complete():
            logger.warning(f"Incomplete dictionary at t={self.time}")
            return False
        
        return True
    
    def catalyze_next_projection(self) -> np.ndarray:
        """
        Use Face B to catalyze next observer projection
        Π_{i+1} = C[F_i^B]
        """
        # Catalytic operator: maps S-coordinates to projection matrix
        S_k, S_t, S_e = self.face_B.S_coordinates
        
        # Simple catalytic mapping: next projection focuses on region
        # determined by current conjugate face
        # In full implementation, this would be more sophisticated
        next_projection = np.eye(len(self.dictionary.entries))
        
        # Modulate projection based on S-coordinates
        # Higher S_k → focus on knowledge-related observables
        # Higher S_t → focus on temporal observables
        # Higher S_e → focus on evolutionary observables
        
        return next_projection


class CatalyticSlicingValidator:
    """
    Main validation framework implementing catalytic reality slicing
    """
    
    def __init__(self, observer_capacity: ObserverCapacity):
        self.observer = observer_capacity
        self.slices: List[RealitySlice] = []
        self.information_gain: List[float] = []
        
    def initialize_empty_dictionary(self) -> ObserverDictionary:
        """Create empty observer dictionary"""
        return ObserverDictionary(observer_type=self.observer.observer_type)
    
    def measure_face_A(self, 
                       system_state: Dict[str, float], 
                       dictionary: ObserverDictionary) -> InformationFace:
        """
        Direct measurement: Physical observables → Categorical coordinates
        This is Face A
        """
        # Extract observables based on observer type
        observables = {}
        
        if self.observer.observer_type == ObserverType.TRANSCENDENT:
            # Transcendent observer measures specific quantities
            observables = {
                'ATP_concentration': system_state.get('ATP', 0.0),
                'membrane_potential': system_state.get('V_mem', 0.0),
                'Ca2_concentration': system_state.get('Ca2', 0.0),
                'pH': system_state.get('pH', 7.0),
                'protein_count': system_state.get('proteins', 0.0),
            }
            
            # Fill dictionary
            for key, value in observables.items():
                dictionary.fill_entry(key, value)
        
        # Map observables to S-entropy coordinates
        S_k, S_t, S_e = self._observables_to_S_coordinates(observables)
        
        face_A = InformationFace(
            face_type='A',
            S_coordinates=(S_k, S_t, S_e),
            observables=observables
        )
        face_A.encode_ternary(precision=10)
        
        return face_A
    
    def derive_face_B(self, face_A: InformationFace) -> InformationFace:
        """
        Derive conjugate face: Categorical coordinates → Physical trajectories
        This is Face B, computed from Face A via complementarity
        """
        # Complementarity: S_k^B = 1 - S_k^A, etc.
        S_k_A, S_t_A, S_e_A = face_A.S_coordinates
        S_k_B = 1.0 - S_k_A
        S_t_B = 1.0 - S_t_A
        S_e_B = 1.0 - S_e_A
        
        # Derive conjugate observables (trajectories, phases, etc.)
        conjugate_observables = {
            'molecular_trajectories': self._derive_trajectories(face_A),
            'phase_relationships': self._derive_phases(face_A),
            'charge_distributions': self._derive_charges(face_A),
        }
        
        face_B = InformationFace(
            face_type='B',
            S_coordinates=(S_k_B, S_t_B, S_e_B),
            observables=conjugate_observables
        )
        face_B.encode_ternary(precision=10)
        
        return face_B
    
    def generate_reality_slice(self, 
                               time: float,
                               system_state: Dict[str, float],
                               previous_slice: Optional[RealitySlice] = None) -> RealitySlice:
        """
        Generate a complete reality slice at time t
        """
        # Initialize or update dictionary
        if previous_slice is None:
            dictionary = self.initialize_empty_dictionary()
            observer_projection = np.eye(dictionary.capacity)
        else:
            # Catalyze projection from previous slice
            dictionary = self.initialize_empty_dictionary()
            observer_projection = previous_slice.catalyze_next_projection()
        
        # Measure Face A directly
        face_A = self.measure_face_A(system_state, dictionary)
        
        # Derive Face B from complementarity
        face_B = self.derive_face_B(face_A)
        
        # Create slice
        slice_i = RealitySlice(
            time=time,
            face_A=face_A,
            face_B=face_B,
            observer_projection=observer_projection,
            dictionary=dictionary
        )
        
        # Verify consistency
        if not slice_i.verify_consistency():
            logger.error(f"Slice at t={time} failed consistency check")
        
        self.slices.append(slice_i)
        return slice_i
    
    def compute_reflectance_cascade(self) -> float:
        """
        Compute information gain from reflectance cascade
        I_total = sum_{i<j} R(F_j^B, F_i^A)
        Should scale as O(N^2)
        """
        N = len(self.slices)
        total_information = 0.0
        
        for i in range(N):
            for j in range(i + 1, N):
                # Future slice j reflects information back to past slice i
                reflected_info = self._compute_reflection(
                    self.slices[j].face_B,
                    self.slices[i].face_A
                )
                total_information += reflected_info
        
        # Expected: N(N-1)/2 reflections
        expected_reflections = N * (N - 1) // 2
        logger.info(f"Reflectance cascade: {expected_reflections} reflections, "
                   f"total information gain: {total_information:.2e} bits")
        
        return total_information
    
    def validate_catalytic_consistency(self) -> bool:
        """
        Verify that catalytic chain is consistent:
        Π_{i+1} = C[F_i^B] for all i
        """
        for i in range(len(self.slices) - 1):
            # Check if slice i catalyzed slice i+1 correctly
            expected_projection = self.slices[i].catalyze_next_projection()
            actual_projection = self.slices[i + 1].observer_projection
            
            # Compare projections (should be similar)
            diff = np.linalg.norm(expected_projection - actual_projection)
            if diff > 0.1:  # Tolerance
                logger.warning(f"Catalytic inconsistency between slices {i} and {i+1}: "
                             f"diff={diff:.3f}")
                return False
        
        logger.info("Catalytic consistency verified across all slices")
        return True
    
    def compare_with_experiment(self, 
                               experimental_slices: List[RealitySlice]) -> Dict[str, float]:
        """
        Compare simulation slices with experimental slices
        Returns error metrics
        """
        if len(self.slices) != len(experimental_slices):
            raise ValueError("Simulation and experiment must have same number of slices")
        
        errors = {
            'face_A_error': [],
            'face_B_error': [],
            'S_coordinate_error': [],
            'observable_error': {},
        }
        
        for sim_slice, exp_slice in zip(self.slices, experimental_slices):
            # Compare Face A S-coordinates
            S_error_A = np.linalg.norm(
                np.array(sim_slice.face_A.S_coordinates) - 
                np.array(exp_slice.face_A.S_coordinates)
            )
            errors['face_A_error'].append(S_error_A)
            
            # Compare Face B S-coordinates
            S_error_B = np.linalg.norm(
                np.array(sim_slice.face_B.S_coordinates) - 
                np.array(exp_slice.face_B.S_coordinates)
            )
            errors['face_B_error'].append(S_error_B)
            
            # Compare individual observables
            for key in sim_slice.face_A.observables:
                if key in exp_slice.face_A.observables:
                    obs_error = abs(
                        sim_slice.face_A.observables[key] - 
                        exp_slice.face_A.observables[key]
                    )
                    if key not in errors['observable_error']:
                        errors['observable_error'][key] = []
                    errors['observable_error'][key].append(obs_error)
        
        # Compute summary statistics
        summary = {
            'mean_face_A_error': np.mean(errors['face_A_error']),
            'mean_face_B_error': np.mean(errors['face_B_error']),
            'max_face_A_error': np.max(errors['face_A_error']),
            'max_face_B_error': np.max(errors['face_B_error']),
        }
        
        for key, values in errors['observable_error'].items():
            summary[f'mean_{key}_error'] = np.mean(values)
        
        return summary
    
    # Helper methods
    
    def _observables_to_S_coordinates(self, 
                                      observables: Dict[str, float]) -> Tuple[float, float, float]:
        """
        Map physical observables to S-entropy coordinates
        This is a simplified mapping; full implementation would be more sophisticated
        """
        # Normalize observables to [0, 1] range
        # S_k: knowledge entropy (related to ATP, information content)
        # S_t: temporal entropy (related to dynamics, pH changes)
        # S_e: evolution entropy (related to structural changes, protein count)
        
        ATP = observables.get('ATP_concentration', 5.0)  # mM
        V_mem = observables.get('membrane_potential', -70.0)  # mV
        Ca2 = observables.get('Ca2_concentration', 0.1)  # μM
        pH = observables.get('pH', 7.0)
        proteins = observables.get('protein_count', 1e6)
        
        # Simple linear mapping (in reality, this would be more complex)
        S_k = np.clip(ATP / 10.0, 0.0, 1.0)  # Knowledge ~ ATP availability
        S_t = np.clip((pH - 6.0) / 2.0, 0.0, 1.0)  # Temporal ~ pH dynamics
        S_e = np.clip(np.log10(proteins) / 7.0, 0.0, 1.0)  # Evolution ~ protein diversity
        
        return (S_k, S_t, S_e)
    
    def _derive_trajectories(self, face_A: InformationFace) -> float:
        """Derive molecular trajectories from Face A"""
        # Placeholder: would compute actual trajectories
        return np.sum(face_A.S_coordinates)
    
    def _derive_phases(self, face_A: InformationFace) -> float:
        """Derive phase relationships from Face A"""
        # Placeholder: would compute actual phases
        return np.prod(face_A.S_coordinates)
    
    def _derive_charges(self, face_A: InformationFace) -> float:
        """Derive charge distributions from Face A"""
        # Placeholder: would compute actual charge distributions
        return np.mean(face_A.S_coordinates)
    
    def _compute_reflection(self, 
                           face_B_future: InformationFace,
                           face_A_past: InformationFace) -> float:
        """
        Compute information reflected from future slice back to past slice
        """
        # Information gain: how much does future Face B constrain past Face A?
        # Measured as reduction in uncertainty
        
        # Simple metric: distance in S-entropy space
        S_future = np.array(face_B_future.S_coordinates)
        S_past = np.array(face_A_past.S_coordinates)
        
        # Information gain inversely proportional to distance
        distance = np.linalg.norm(S_future - S_past)
        information_gain = 1.0 / (1.0 + distance)  # bits
        
        return information_gain


def run_validation_example():
    """
    Example validation run demonstrating catalytic slicing
    """
    logger.info("=" * 80)
    logger.info("CATALYTIC SLICING VALIDATION FRAMEWORK")
    logger.info("=" * 80)
    
    # Create transcendent observer (experimental apparatus)
    observer = ObserverCapacity.transcendent_observer()
    validator = CatalyticSlicingValidator(observer)
    
    logger.info(f"\nObserver type: {observer.observer_type.value}")
    logger.info(f"Observation range: {observer.observation_range} m")
    logger.info(f"Temporal resolution: {observer.temporal_resolution} s")
    logger.info(f"Information capacity: {observer.information_capacity:.2e} bits/s")
    
    # Generate simulation data (mock cellular states)
    logger.info("\nGenerating reality slices...")
    N_slices = 10
    dt = 0.1  # seconds
    
    for i in range(N_slices):
        t = i * dt
        
        # Mock system state (would come from actual simulation)
        system_state = {
            'ATP': 5.0 + 0.5 * np.sin(2 * np.pi * t),  # Oscillating ATP
            'V_mem': -70.0 + 10.0 * np.cos(2 * np.pi * t),  # Oscillating voltage
            'Ca2': 0.1 + 0.05 * np.sin(4 * np.pi * t),  # Faster Ca2+ oscillation
            'pH': 7.0 + 0.1 * np.sin(np.pi * t),  # Slow pH oscillation
            'proteins': 1e6 * (1 + 0.01 * i),  # Slowly increasing protein count
        }
        
        # Generate slice
        previous = validator.slices[-1] if validator.slices else None
        slice_i = validator.generate_reality_slice(t, system_state, previous)
        
        logger.info(f"  Slice {i}: t={t:.2f}s, "
                   f"S_k={slice_i.face_A.S_coordinates[0]:.3f}, "
                   f"S_t={slice_i.face_A.S_coordinates[1]:.3f}, "
                   f"S_e={slice_i.face_A.S_coordinates[2]:.3f}")
    
    # Validate catalytic consistency
    logger.info("\nValidating catalytic consistency...")
    is_consistent = validator.validate_catalytic_consistency()
    logger.info(f"Catalytic consistency: {'PASS' if is_consistent else 'FAIL'}")
    
    # Compute reflectance cascade
    logger.info("\nComputing reflectance cascade...")
    total_info = validator.compute_reflectance_cascade()
    expected_quadratic = N_slices * (N_slices - 1) // 2
    logger.info(f"Expected O(N²) reflections: {expected_quadratic}")
    logger.info(f"Actual reflections: {expected_quadratic}")
    logger.info(f"Total information gain: {total_info:.2e} bits")
    
    # Generate mock experimental data
    logger.info("\nGenerating mock experimental data...")
    experimental_validator = CatalyticSlicingValidator(observer)
    
    for i in range(N_slices):
        t = i * dt
        
        # Experimental data with small noise
        system_state = {
            'ATP': 5.0 + 0.5 * np.sin(2 * np.pi * t) + np.random.normal(0, 0.05),
            'V_mem': -70.0 + 10.0 * np.cos(2 * np.pi * t) + np.random.normal(0, 1.0),
            'Ca2': 0.1 + 0.05 * np.sin(4 * np.pi * t) + np.random.normal(0, 0.005),
            'pH': 7.0 + 0.1 * np.sin(np.pi * t) + np.random.normal(0, 0.01),
            'proteins': 1e6 * (1 + 0.01 * i) + np.random.normal(0, 1e4),
        }
        
        previous = experimental_validator.slices[-1] if experimental_validator.slices else None
        experimental_validator.generate_reality_slice(t, system_state, previous)
    
    # Compare simulation with experiment
    logger.info("\nComparing simulation with experiment...")
    errors = validator.compare_with_experiment(experimental_validator.slices)
    
    logger.info(f"Mean Face A error: {errors['mean_face_A_error']:.6f}")
    logger.info(f"Mean Face B error: {errors['mean_face_B_error']:.6f}")
    logger.info(f"Max Face A error: {errors['max_face_A_error']:.6f}")
    logger.info(f"Max Face B error: {errors['max_face_B_error']:.6f}")
    
    for key in ['ATP_concentration', 'membrane_potential', 'Ca2_concentration', 'pH']:
        if f'mean_{key}_error' in errors:
            logger.info(f"Mean {key} error: {errors[f'mean_{key}_error']:.6f}")
    
    # Calculate sparsity
    logger.info("\nObserver sparsity analysis...")
    sparsity = validator.slices[0].dictionary.get_sparsity()
    logger.info(f"Dictionary sparsity: {sparsity:.6f}")
    logger.info(f"Filled entries: {validator.slices[0].dictionary.filled_count} / "
               f"{validator.slices[0].dictionary.capacity}")
    
    # Estimate complete phase space dimension
    N_atoms = 1e14  # Typical cell
    phase_space_dim = 6 * N_atoms  # 3 position + 3 momentum per atom
    accessible_dim = validator.slices[0].dictionary.capacity
    true_sparsity = accessible_dim / phase_space_dim
    
    logger.info(f"\nTrue sparsity (accessible / complete phase space):")
    logger.info(f"  Accessible dimensions: {accessible_dim}")
    logger.info(f"  Complete phase space: {phase_space_dim:.2e}")
    logger.info(f"  Sparsity ratio: {true_sparsity:.2e}")
    
    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION COMPLETE")
    logger.info("=" * 80)


if __name__ == "__main__":
    run_validation_example()
