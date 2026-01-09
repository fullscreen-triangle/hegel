"""
Validation Experiments for Partition-Based Equations of State

This module creates 3D visualizations of thermodynamic states with comprehensive
metric panels, extending the spectroscopy validation framework to all five
thermodynamic regimes:
1. Neutral Gas
2. Plasma
3. Degenerate Matter
4. Relativistic Gas
5. Bose-Einstein Condensate

Each state is visualized with:
- 3D phase space representation (position, momentum, energy)
- S-entropy coordinate trajectory
- Thermodynamic metrics (P, V, T, S, etc.)
- Partition coordinate distributions
- Comparison with theoretical predictions
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from mpl_toolkits.mplot3d import Axes3D
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import seaborn as sns
from scipy.stats import maxwell
from scipy.special import zeta

# Physical constants
kB = 1.380649e-23  # Boltzmann constant (J/K)
hbar = 1.054571817e-34  # Reduced Planck constant (J·s)
c = 299792458  # Speed of light (m/s)
me = 9.1093837015e-31  # Electron mass (kg)
mp = 1.67262192369e-27  # Proton mass (kg)
e = 1.602176634e-19  # Elementary charge (C)
epsilon0 = 8.8541878128e-12  # Vacuum permittivity (F/m)


@dataclass
class PartitionCoordinates:
    """Partition coordinates (n, ℓ, m, s) for a particle"""
    n: int  # Radial partition depth
    ell: int  # Angular complexity (0 ≤ ℓ < n)
    m: int  # Orientation (-ℓ ≤ m ≤ ℓ)
    s: float  # Chirality (±1/2)
    
    def __post_init__(self):
        assert 0 <= self.ell < self.n, f"Invalid ℓ={self.ell} for n={self.n}"
        assert abs(self.m) <= self.ell, f"Invalid m={self.m} for ℓ={self.ell}"
        assert abs(self.s) == 0.5, f"Invalid spin s={self.s}"


@dataclass
class SEntropyCoordinates:
    """S-entropy coordinates (S_k, S_t, S_e) ∈ [0,1]³"""
    Sk: float  # Knowledge entropy (momentum space)
    St: float  # Temporal entropy (time/frequency space)
    Se: float  # Evolution entropy (energy/action space)
    
    def __post_init__(self):
        assert 0 <= self.Sk <= 1, f"Invalid S_k={self.Sk}"
        assert 0 <= self.St <= 1, f"Invalid S_t={self.St}"
        assert 0 <= self.Se <= 1, f"Invalid S_e={self.Se}"
    
    def norm(self) -> float:
        """Euclidean norm in S-entropy space"""
        return np.sqrt(self.Sk**2 + self.St**2 + self.Se**2)
    
    def distance(self, other: 'SEntropyCoordinates') -> float:
        """Distance between two points in S-entropy space"""
        return np.sqrt((self.Sk - other.Sk)**2 + 
                      (self.St - other.St)**2 + 
                      (self.Se - other.Se)**2)


@dataclass
class ThermodynamicState:
    """Complete thermodynamic state with all observables"""
    name: str
    N: int  # Number of particles
    V: float  # Volume (m³)
    T: float  # Temperature (K)
    P: float  # Pressure (Pa)
    U: float  # Internal energy (J)
    S: float  # Entropy (J/K)
    F: float  # Helmholtz free energy (J)
    mu: float  # Chemical potential (J)
    
    # Partition coordinates for all particles
    partition_coords: List[PartitionCoordinates]
    
    # S-entropy trajectory
    s_entropy_trajectory: List[SEntropyCoordinates]
    
    # Phase space coordinates
    positions: np.ndarray  # (N, 3) array
    momenta: np.ndarray  # (N, 3) array
    
    # Regime-specific parameters
    regime_params: Dict[str, float]


def partition_to_s_entropy(pc: PartitionCoordinates, 
                          alpha_k: float = 5.0, 
                          alpha_t: float = 5.0, 
                          alpha_e: float = 5.0,
                          beta_k: float = 10.0,
                          beta_t: float = 10.0,
                          beta_e: float = 10.0) -> SEntropyCoordinates:
    """
    Map partition coordinates to S-entropy coordinates using sigmoid functions.
    
    Equations from the paper:
    S_k = 1/(1 + exp(-α_k(n²/(ℓ+1) - β_k)))
    S_t = 1/(1 + exp(-α_t(n²/(|m|+1) - β_t)))
    S_e = 1/(1 + exp(-α_e(n²/(2|s|+1) - β_e)))
    """
    Sk = 1.0 / (1.0 + np.exp(-alpha_k * (pc.n**2 / (pc.ell + 1) - beta_k)))
    St = 1.0 / (1.0 + np.exp(-alpha_t * (pc.n**2 / (abs(pc.m) + 1) - beta_t)))
    Se = 1.0 / (1.0 + np.exp(-alpha_e * (pc.n**2 / (2*abs(pc.s) + 1) - beta_e)))
    
    return SEntropyCoordinates(Sk, St, Se)


def generate_neutral_gas_state(N: int = 1000, 
                               V: float = 1e-3, 
                               T: float = 300.0,
                               m: float = 28 * 1.66054e-27) -> ThermodynamicState:
    """
    Generate a neutral gas state (ideal gas).
    
    Equation of state: PV = NkT
    """
    # Thermodynamic quantities
    P = N * kB * T / V
    U = (3/2) * N * kB * T
    S = N * kB * (np.log(V / N) + (3/2) * np.log(2 * np.pi * m * kB * T / hbar**2) + 5/2)
    F = U - T * S
    mu = kB * T * np.log(N / V * (hbar**2 / (2 * np.pi * m * kB * T))**(3/2))
    
    # Generate positions uniformly in cubic volume
    L = V**(1/3)
    positions = np.random.uniform(-L/2, L/2, (N, 3))
    
    # Generate momenta from Maxwell-Boltzmann distribution
    sigma_p = np.sqrt(m * kB * T)
    momenta = np.random.normal(0, sigma_p, (N, 3))
    
    # Generate partition coordinates
    # For ideal gas, n is determined by de Broglie wavelength
    partition_coords = []
    for i in range(N):
        p_mag = np.linalg.norm(momenta[i])
        lambda_dB = hbar / p_mag if p_mag > 0 else hbar / np.sqrt(m * kB * T)
        n = max(1, int(L / lambda_dB))
        
        # ℓ uniformly distributed from 0 to n-1
        ell = np.random.randint(0, min(n, 1000))  # Cap at 1000 to avoid overflow
        
        # m uniformly distributed from -ℓ to ℓ
        m_val = np.random.randint(-ell, ell + 1) if ell > 0 else 0
        
        # s randomly ±1/2
        s = np.random.choice([-0.5, 0.5])
        
        partition_coords.append(PartitionCoordinates(n, ell, m_val, s))
    
    # Generate S-entropy trajectory (equilibrium: stays near fixed point)
    s_entropy_trajectory = []
    for _ in range(100):
        # Sample random particle
        pc = np.random.choice(partition_coords)
        s_coord = partition_to_s_entropy(pc)
        s_entropy_trajectory.append(s_coord)
    
    regime_params = {
        'mass': m,
        'thermal_velocity': np.sqrt(2 * kB * T / m),
        'mean_free_path': V / (N * np.pi * (1e-10)**2),  # Assuming 1 Å collision diameter
        'collision_time': 1e-10  # Approximate
    }
    
    return ThermodynamicState(
        name="Neutral Gas",
        N=N, V=V, T=T, P=P, U=U, S=S, F=F, mu=mu,
        partition_coords=partition_coords,
        s_entropy_trajectory=s_entropy_trajectory,
        positions=positions,
        momenta=momenta,
        regime_params=regime_params
    )


def generate_plasma_state(N: int = 1000,
                         V: float = 1e-3,
                         T: float = 1e6,
                         Z: int = 1) -> ThermodynamicState:
    """
    Generate a plasma state with Coulomb interactions.
    
    Equation of state: PV = (N_e + N_i)kT(1 - Γ/3)
    where Γ = e²/(4πε₀ a kT) is the plasma parameter
    """
    # For hydrogen plasma: N_e = N_i = N/2
    N_e = N // 2
    N_i = N // 2
    
    # Calculate plasma parameter
    n_e = N_e / V  # Electron density
    a = (3 / (4 * np.pi * n_e))**(1/3)  # Wigner-Seitz radius
    Gamma = (Z * e)**2 / (4 * np.pi * epsilon0 * a * kB * T)
    
    # Thermodynamic quantities with Debye-Hückel correction
    P = (N_e + N_i) * kB * T / V * (1 - Gamma / 3)
    U = (3/2) * (N_e + N_i) * kB * T * (1 - Gamma / 12)
    
    # Entropy (including Coulomb contribution)
    lambda_dB_e = hbar / np.sqrt(2 * np.pi * me * kB * T)
    lambda_dB_i = hbar / np.sqrt(2 * np.pi * mp * kB * T)
    S_e = N_e * kB * (np.log(V / N_e) + (3/2) * np.log(2 * np.pi * me * kB * T / hbar**2) + 5/2)
    S_i = N_i * kB * (np.log(V / N_i) + (3/2) * np.log(2 * np.pi * mp * kB * T / hbar**2) + 5/2)
    S = S_e + S_i - N_e * kB * Gamma / 2
    
    F = U - T * S
    mu = kB * T * np.log(n_e * lambda_dB_e**3)
    
    # Generate positions (with Debye screening correlation)
    L = V**(1/3)
    positions = np.random.uniform(-L/2, L/2, (N, 3))
    
    # Generate momenta (Maxwell-Boltzmann for both species)
    momenta = np.zeros((N, 3))
    sigma_p_e = np.sqrt(me * kB * T)
    sigma_p_i = np.sqrt(mp * kB * T)
    momenta[:N_e] = np.random.normal(0, sigma_p_e, (N_e, 3))
    momenta[N_e:] = np.random.normal(0, sigma_p_i, (N_i, 3))
    
    # Generate partition coordinates
    partition_coords = []
    for i in range(N):
        mass = me if i < N_e else mp
        p_mag = np.linalg.norm(momenta[i])
        lambda_dB = hbar / p_mag if p_mag > 0 else hbar / np.sqrt(mass * kB * T)
        n = max(1, int(L / lambda_dB))
        
        ell = np.random.randint(0, min(n, 1000))
        m_val = np.random.randint(-ell, ell + 1) if ell > 0 else 0
        s = np.random.choice([-0.5, 0.5])
        
        partition_coords.append(PartitionCoordinates(n, ell, m_val, s))
    
    # Generate S-entropy trajectory
    s_entropy_trajectory = []
    for _ in range(100):
        pc = np.random.choice(partition_coords)
        s_coord = partition_to_s_entropy(pc)
        s_entropy_trajectory.append(s_coord)
    
    # Debye length
    lambda_D = np.sqrt(epsilon0 * kB * T / (n_e * e**2))
    
    regime_params = {
        'plasma_parameter': Gamma,
        'debye_length': lambda_D,
        'electron_density': n_e,
        'ion_density': N_i / V,
        'coupling_regime': 'weakly coupled' if Gamma < 1 else 'strongly coupled'
    }
    
    return ThermodynamicState(
        name="Plasma",
        N=N, V=V, T=T, P=P, U=U, S=S, F=F, mu=mu,
        partition_coords=partition_coords,
        s_entropy_trajectory=s_entropy_trajectory,
        positions=positions,
        momenta=momenta,
        regime_params=regime_params
    )


def generate_degenerate_matter_state(N: int = 1000,
                                    V: float = 1e-9,
                                    T: float = 4.2) -> ThermodynamicState:
    """
    Generate a degenerate electron gas state.
    
    Equation of state: P = (2/5)nE_F where E_F = (ℏ²/2m)(3π²n)^(2/3)
    """
    n = N / V  # Number density
    k_F = (3 * np.pi**2 * n)**(1/3)  # Fermi wavevector
    E_F = hbar**2 * k_F**2 / (2 * me)  # Fermi energy
    
    # Thermodynamic quantities (T=0 limit)
    P = (2/5) * n * E_F
    U = (3/5) * N * E_F
    
    # Entropy (low temperature correction)
    theta = kB * T / E_F  # Degeneracy parameter
    S = (np.pi**2 / 3) * N * kB * theta
    
    F = U - T * S
    mu = E_F * (1 - (np.pi**2 / 12) * theta**2)
    
    # Generate positions uniformly
    L = V**(1/3)
    positions = np.random.uniform(-L/2, L/2, (N, 3))
    
    # Generate momenta from Fermi-Dirac distribution
    # Fill states up to Fermi level
    momenta = np.zeros((N, 3))
    for i in range(N):
        # Sample from Fermi sphere
        p_mag = k_F * hbar * np.random.random()**(1/3)  # Uniform in k-space volume
        theta_p = np.arccos(2 * np.random.random() - 1)
        phi_p = 2 * np.pi * np.random.random()
        
        momenta[i, 0] = p_mag * np.sin(theta_p) * np.cos(phi_p)
        momenta[i, 1] = p_mag * np.sin(theta_p) * np.sin(phi_p)
        momenta[i, 2] = p_mag * np.cos(theta_p)
    
    # Generate partition coordinates (fill from n=1 upward)
    partition_coords = []
    n_F = int(np.sqrt(3 * N / 2)**(1/3))  # Fermi partition depth
    
    particle_idx = 0
    for n in range(1, n_F + 2):
        for ell in range(n):
            for m in range(-ell, ell + 1):
                for s in [-0.5, 0.5]:
                    if particle_idx >= N:
                        break
                    partition_coords.append(PartitionCoordinates(n, ell, m, s))
                    particle_idx += 1
                if particle_idx >= N:
                    break
            if particle_idx >= N:
                break
        if particle_idx >= N:
            break
    
    # Generate S-entropy trajectory
    s_entropy_trajectory = []
    for _ in range(100):
        pc = np.random.choice(partition_coords)
        s_coord = partition_to_s_entropy(pc)
        s_entropy_trajectory.append(s_coord)
    
    regime_params = {
        'fermi_energy': E_F,
        'fermi_wavevector': k_F,
        'fermi_temperature': E_F / kB,
        'degeneracy_parameter': theta,
        'fermi_partition_depth': n_F
    }
    
    return ThermodynamicState(
        name="Degenerate Matter",
        N=N, V=V, T=T, P=P, U=U, S=S, F=F, mu=mu,
        partition_coords=partition_coords,
        s_entropy_trajectory=s_entropy_trajectory,
        positions=positions,
        momenta=momenta,
        regime_params=regime_params
    )


def generate_relativistic_gas_state(N: int = 1000,
                                   V: float = 1e-3,
                                   T: float = 1e10) -> ThermodynamicState:
    """
    Generate a relativistic gas state (ultra-relativistic limit).
    
    Equation of state: P = (1/3)aT⁴ where a = π²k⁴/(15ℏ³c³)
    """
    # Stefan-Boltzmann constant
    a = np.pi**2 * kB**4 / (15 * hbar**3 * c**3)
    
    # Thermodynamic quantities
    P = (1/3) * a * T**4
    U = 3 * P * V  # U = 3PV for ultra-relativistic gas
    
    # Entropy
    S = 4 * a * T**3 * V
    
    F = U - T * S
    mu = 0  # For photon gas
    
    # Generate positions uniformly
    L = V**(1/3)
    positions = np.random.uniform(-L/2, L/2, (N, 3))
    
    # Generate momenta from relativistic distribution
    # E = pc for ultra-relativistic particles
    momenta = np.zeros((N, 3))
    for i in range(N):
        # Sample energy from Planck distribution
        E = kB * T * (-np.log(np.random.random()))  # Exponential distribution
        p_mag = E / c
        
        # Random direction
        theta_p = np.arccos(2 * np.random.random() - 1)
        phi_p = 2 * np.pi * np.random.random()
        
        momenta[i, 0] = p_mag * np.sin(theta_p) * np.cos(phi_p)
        momenta[i, 1] = p_mag * np.sin(theta_p) * np.sin(phi_p)
        momenta[i, 2] = p_mag * np.cos(theta_p)
    
    # Generate partition coordinates
    partition_coords = []
    for i in range(N):
        p_mag = np.linalg.norm(momenta[i])
        lambda_C = hbar / (me * c)  # Compton wavelength
        n_max = min(int(L / lambda_C), 10000)  # Cap at 10000 to avoid overflow
        n = max(1, np.random.randint(1, min(n_max + 1, 10000)))
        
        ell = np.random.randint(0, min(n, 1000))
        m_val = np.random.randint(-ell, ell + 1) if ell > 0 else 0
        s = np.random.choice([-0.5, 0.5])
        
        partition_coords.append(PartitionCoordinates(n, ell, m_val, s))
    
    # Generate S-entropy trajectory
    s_entropy_trajectory = []
    for _ in range(100):
        pc = np.random.choice(partition_coords)
        s_coord = partition_to_s_entropy(pc)
        s_entropy_trajectory.append(s_coord)
    
    regime_params = {
        'adiabatic_index': 4/3,
        'thermal_energy': kB * T,
        'rest_mass_energy': me * c**2,
        'relativistic_parameter': kB * T / (me * c**2),
        'radiation_constant': a
    }
    
    return ThermodynamicState(
        name="Relativistic Gas",
        N=N, V=V, T=T, P=P, U=U, S=S, F=F, mu=mu,
        partition_coords=partition_coords,
        s_entropy_trajectory=s_entropy_trajectory,
        positions=positions,
        momenta=momenta,
        regime_params=regime_params
    )


def generate_bec_state(N: int = 10000,
                      V: float = 1e-12,
                      T: float = 100e-9,
                      m: float = 87 * 1.66054e-27,
                      a_s: float = 5.3e-9) -> ThermodynamicState:
    """
    Generate a Bose-Einstein condensate state.
    
    Critical temperature: T_c = (2πℏ²/mk)(n/ζ(3/2))^(2/3)
    Equation of state: P = (2πℏ²a_s/m)n² for T < T_c
    """
    n = N / V
    
    # Critical temperature
    T_c = (2 * np.pi * hbar**2 / (m * kB)) * (n / zeta(3/2))**(2/3)
    
    # Interaction parameter (always define it)
    g = 4 * np.pi * hbar**2 * a_s / m
    
    # Condensate fraction
    if T < T_c:
        N_0 = N * (1 - (T / T_c)**(3/2))
    else:
        N_0 = 0
    
    # Thermodynamic quantities
    if T < T_c:
        # Interacting BEC
        P = (1/2) * g * (N_0 / V)**2
        U = (1/2) * g * N_0**2 / V
    else:
        # Normal gas
        P = N * kB * T / V
        U = (3/2) * N * kB * T
    
    # Entropy
    if T < T_c:
        S = (5/2) * (N - N_0) * kB * (T / T_c)**(3/2)
    else:
        lambda_th = hbar / np.sqrt(2 * np.pi * m * kB * T)
        S = N * kB * (np.log(V / N) + (3/2) * np.log(2 * np.pi * m * kB * T / hbar**2) + 5/2)
    
    F = U - T * S
    mu = g * N_0 / V if T < T_c else kB * T * np.log(n * (hbar**2 / (2 * np.pi * m * kB * T))**(3/2))
    
    # Generate positions
    L = V**(1/3)
    positions = np.zeros((N, 3))
    
    # Condensate particles at origin (with small spread)
    if N_0 > 0:
        sigma_0 = hbar / np.sqrt(m * g * N_0 / V)  # Healing length
        positions[:int(N_0)] = np.random.normal(0, sigma_0, (int(N_0), 3))
    
    # Thermal cloud uniformly distributed
    N_th = N - int(N_0)
    if N_th > 0:
        positions[int(N_0):] = np.random.uniform(-L/2, L/2, (N_th, 3))
    
    # Generate momenta
    momenta = np.zeros((N, 3))
    
    # Condensate: all particles in ground state (p ≈ 0)
    if N_0 > 0:
        sigma_p_0 = hbar / (2 * sigma_0)
        momenta[:int(N_0)] = np.random.normal(0, sigma_p_0, (int(N_0), 3))
    
    # Thermal cloud: Maxwell-Boltzmann
    if N_th > 0:
        sigma_p_th = np.sqrt(m * kB * T)
        momenta[int(N_0):] = np.random.normal(0, sigma_p_th, (N_th, 3))
    
    # Generate partition coordinates
    partition_coords = []
    
    # Condensate: all in (n=1, ℓ=0, m=0, s=±1/2)
    for i in range(int(N_0)):
        s = np.random.choice([-0.5, 0.5])
        partition_coords.append(PartitionCoordinates(1, 0, 0, s))
    
    # Thermal cloud: distributed over excited states
    for i in range(N_th):
        n = np.random.randint(2, 10)  # Excited states
        ell = np.random.randint(0, min(n, 1000))
        m_val = np.random.randint(-ell, ell + 1) if ell > 0 else 0
        s = np.random.choice([-0.5, 0.5])
        partition_coords.append(PartitionCoordinates(n, ell, m_val, s))
    
    # Generate S-entropy trajectory
    s_entropy_trajectory = []
    for _ in range(100):
        pc = np.random.choice(partition_coords)
        s_coord = partition_to_s_entropy(pc)
        s_entropy_trajectory.append(s_coord)
    
    regime_params = {
        'critical_temperature': T_c,
        'condensate_fraction': N_0 / N,
        'scattering_length': a_s,
        'healing_length': hbar / np.sqrt(m * g * N_0 / V) if N_0 > 0 else 0,
        'interaction_parameter': g * n / (kB * T) if T > 0 else np.inf
    }
    
    return ThermodynamicState(
        name="Bose-Einstein Condensate",
        N=N, V=V, T=T, P=P, U=U, S=S, F=F, mu=mu,
        partition_coords=partition_coords,
        s_entropy_trajectory=s_entropy_trajectory,
        positions=positions,
        momenta=momenta,
        regime_params=regime_params
    )


def create_3d_panel_visualization(state: ThermodynamicState, 
                                 save_path: Optional[str] = None):
    """
    Create comprehensive 3D panel visualization for a thermodynamic state.
    
    Layout:
    - Top left: 3D phase space (position-momentum)
    - Top right: 3D S-entropy trajectory
    - Middle left: Partition coordinate distribution
    - Middle right: Thermodynamic metrics (radar chart)
    - Bottom left: Velocity/momentum distribution
    - Bottom right: Energy distribution
    """
    fig = plt.figure(figsize=(20, 16))
    gs = GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)
    
    # Set style
    sns.set_style("whitegrid")
    colors = sns.color_palette("husl", 8)
    
    # ============ Panel 1: 3D Phase Space ============
    ax1 = fig.add_subplot(gs[0, 0], projection='3d')
    
    # Sample subset for visualization
    sample_size = min(500, state.N)
    idx = np.random.choice(state.N, sample_size, replace=False)
    
    # Plot positions colored by momentum magnitude
    p_mag = np.linalg.norm(state.momenta[idx], axis=1)
    scatter1 = ax1.scatter(state.positions[idx, 0] * 1e6,  # Convert to μm
                          state.positions[idx, 1] * 1e6,
                          state.positions[idx, 2] * 1e6,
                          c=p_mag, cmap='viridis', s=20, alpha=0.6)
    
    ax1.set_xlabel('x (μm)', fontsize=10)
    ax1.set_ylabel('y (μm)', fontsize=10)
    ax1.set_zlabel('z (μm)', fontsize=10)
    ax1.set_title(f'{state.name}: Phase Space\n(colored by momentum)', fontsize=12, fontweight='bold')
    plt.colorbar(scatter1, ax=ax1, label='|p| (kg·m/s)', shrink=0.5)
    
    # ============ Panel 2: 3D S-Entropy Trajectory ============
    ax2 = fig.add_subplot(gs[0, 1], projection='3d')
    
    # Extract trajectory coordinates
    Sk_traj = [s.Sk for s in state.s_entropy_trajectory]
    St_traj = [s.St for s in state.s_entropy_trajectory]
    Se_traj = [s.Se for s in state.s_entropy_trajectory]
    
    # Plot trajectory
    ax2.plot(Sk_traj, St_traj, Se_traj, 'o-', color=colors[0], 
            alpha=0.5, markersize=3, linewidth=1)
    
    # Plot start and end points
    ax2.scatter([Sk_traj[0]], [St_traj[0]], [Se_traj[0]], 
               color='green', s=100, marker='o', label='Start', zorder=5)
    ax2.scatter([Sk_traj[-1]], [St_traj[-1]], [Se_traj[-1]], 
               color='red', s=100, marker='s', label='End', zorder=5)
    
    # Draw unit cube
    ax2.set_xlim([0, 1])
    ax2.set_ylim([0, 1])
    ax2.set_zlim([0, 1])
    
    ax2.set_xlabel('$S_k$ (knowledge)', fontsize=10)
    ax2.set_ylabel('$S_t$ (temporal)', fontsize=10)
    ax2.set_zlabel('$S_e$ (evolution)', fontsize=10)
    ax2.set_title(f'{state.name}: S-Entropy Trajectory', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=8)
    
    # ============ Panel 3: Regime-Specific Parameters (Text Box) ============
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.axis('off')
    
    param_text = f"{state.name}\nRegime Parameters:\n\n"
    for key, value in state.regime_params.items():
        if isinstance(value, float):
            param_text += f"{key}: {value:.3e}\n"
        else:
            param_text += f"{key}: {value}\n"
    
    ax3.text(0.1, 0.9, param_text, transform=ax3.transAxes,
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
            family='monospace')
    
    # ============ Panel 4: Partition Coordinate Distribution ============
    ax4 = fig.add_subplot(gs[1, 0])
    
    # Extract partition depths
    n_values = [pc.n for pc in state.partition_coords]
    ell_values = [pc.ell for pc in state.partition_coords]
    
    # Histogram of n values
    n_counts, n_bins = np.histogram(n_values, bins=min(50, max(n_values)))
    ax4.bar(n_bins[:-1], n_counts, width=np.diff(n_bins), 
           color=colors[1], alpha=0.7, edgecolor='black')
    
    ax4.set_xlabel('Partition Depth $n$', fontsize=10)
    ax4.set_ylabel('Count', fontsize=10)
    ax4.set_title('Partition Depth Distribution', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    # ============ Panel 5: Angular Complexity Distribution ============
    ax5 = fig.add_subplot(gs[1, 1])
    
    # Histogram of ℓ values
    ell_counts, ell_bins = np.histogram(ell_values, bins=min(30, max(ell_values) + 1))
    ax5.bar(ell_bins[:-1], ell_counts, width=np.diff(ell_bins),
           color=colors[2], alpha=0.7, edgecolor='black')
    
    ax5.set_xlabel('Angular Complexity $\\ell$', fontsize=10)
    ax5.set_ylabel('Count', fontsize=10)
    ax5.set_title('Angular Complexity Distribution', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    
    # ============ Panel 6: Thermodynamic Metrics (Radar Chart) ============
    ax6 = fig.add_subplot(gs[1, 2], projection='polar')
    
    # Normalize metrics to [0, 1] for radar chart
    metrics = {
        'Pressure': state.P,
        'Temperature': state.T,
        'Entropy': state.S,
        'Energy': state.U,
        'Free Energy': abs(state.F),
        'Chem. Pot.': abs(state.mu)
    }
    
    # Normalize by taking log and scaling
    normalized_metrics = {}
    for key, value in metrics.items():
        if value > 0:
            normalized_metrics[key] = (np.log10(value) - np.log10(min(metrics.values()))) / \
                                     (np.log10(max(metrics.values())) - np.log10(min(metrics.values())))
        else:
            normalized_metrics[key] = 0
    
    categories = list(normalized_metrics.keys())
    values = list(normalized_metrics.values())
    
    # Number of variables
    N_metrics = len(categories)
    angles = np.linspace(0, 2 * np.pi, N_metrics, endpoint=False).tolist()
    values += values[:1]  # Complete the circle
    angles += angles[:1]
    
    ax6.plot(angles, values, 'o-', linewidth=2, color=colors[3])
    ax6.fill(angles, values, alpha=0.25, color=colors[3])
    ax6.set_xticks(angles[:-1])
    ax6.set_xticklabels(categories, fontsize=9)
    ax6.set_ylim(0, 1)
    ax6.set_title('Normalized Thermodynamic Metrics', fontsize=12, fontweight='bold', pad=20)
    ax6.grid(True)
    
    # ============ Panel 7: Velocity Distribution ============
    ax7 = fig.add_subplot(gs[2, 0])
    
    # Calculate velocity magnitudes
    velocities = state.momenta / np.array([state.regime_params.get('mass', me)] * 3)
    v_mag = np.linalg.norm(velocities, axis=1)
    
    # Histogram
    ax7.hist(v_mag, bins=50, color=colors[4], alpha=0.7, edgecolor='black', density=True)
    
    # Theoretical distribution (if applicable)
    if state.name == "Neutral Gas":
        m = state.regime_params['mass']
        v_theory = np.linspace(0, max(v_mag), 100)
        f_MB = maxwell.pdf(v_theory, scale=np.sqrt(kB * state.T / m))
        ax7.plot(v_theory, f_MB, 'r--', linewidth=2, label='Maxwell-Boltzmann')
        ax7.legend()
    
    ax7.set_xlabel('Velocity (m/s)', fontsize=10)
    ax7.set_ylabel('Probability Density', fontsize=10)
    ax7.set_title('Velocity Distribution', fontsize=12, fontweight='bold')
    ax7.grid(True, alpha=0.3)
    
    # ============ Panel 8: Energy Distribution ============
    ax8 = fig.add_subplot(gs[2, 1])
    
    # Calculate kinetic energies
    if state.name == "Relativistic Gas":
        # Relativistic energy: E = sqrt((pc)² + (mc²)²)
        E_kin = np.sqrt((np.linalg.norm(state.momenta, axis=1) * c)**2 + (me * c**2)**2)
    else:
        # Non-relativistic: E = p²/(2m)
        m = state.regime_params.get('mass', me)
        E_kin = np.sum(state.momenta**2, axis=1) / (2 * m)
    
    # Histogram
    ax8.hist(E_kin / (kB * state.T), bins=50, color=colors[5], 
            alpha=0.7, edgecolor='black', density=True)
    
    ax8.set_xlabel('Energy / $k_B T$', fontsize=10)
    ax8.set_ylabel('Probability Density', fontsize=10)
    ax8.set_title('Energy Distribution', fontsize=12, fontweight='bold')
    ax8.grid(True, alpha=0.3)
    
    # ============ Panel 9: Equation of State Verification ============
    ax9 = fig.add_subplot(gs[2, 2])
    ax9.axis('off')
    
    # Calculate theoretical predictions
    if state.name == "Neutral Gas":
        P_theory = state.N * kB * state.T / state.V
        equation = "$PV = Nk_BT$"
    elif state.name == "Plasma":
        Gamma = state.regime_params['plasma_parameter']
        P_theory = state.N * kB * state.T / state.V * (1 - Gamma / 3)
        equation = "$PV = Nk_BT(1 - \\Gamma/3)$"
    elif state.name == "Degenerate Matter":
        n = state.N / state.V
        E_F = state.regime_params['fermi_energy']
        P_theory = (2/5) * n * E_F
        equation = "$P = (2/5)nE_F$"
    elif state.name == "Relativistic Gas":
        a = state.regime_params['radiation_constant']
        P_theory = (1/3) * a * state.T**4
        equation = "$P = (1/3)aT^4$"
    elif state.name == "Bose-Einstein Condensate":
        if state.T < state.regime_params['critical_temperature']:
            g = 4 * np.pi * hbar**2 * state.regime_params['scattering_length'] / state.regime_params.get('mass', 87 * 1.66054e-27)
            N_0 = state.N * state.regime_params['condensate_fraction']
            P_theory = (1/2) * g * (N_0 / state.V)**2
            equation = "$P = (1/2)g n_0^2$"
        else:
            P_theory = state.N * kB * state.T / state.V
            equation = "$PV = Nk_BT$"
    else:
        P_theory = state.P
        equation = "Unknown"
    
    # Calculate deviation
    deviation = abs(state.P - P_theory) / P_theory * 100
    
    verification_text = f"Equation of State Verification\n\n"
    verification_text += f"Equation: {equation}\n\n"
    verification_text += f"Measured P: {state.P:.3e} Pa\n"
    verification_text += f"Theoretical P: {P_theory:.3e} Pa\n"
    verification_text += f"Deviation: {deviation:.2f}%\n\n"
    
    if deviation < 1:
        verification_text += "✓ Excellent agreement"
        color = 'lightgreen'
    elif deviation < 5:
        verification_text += "✓ Good agreement"
        color = 'lightyellow'
    else:
        verification_text += "⚠ Check parameters"
        color = 'lightcoral'
    
    ax9.text(0.1, 0.9, verification_text, transform=ax9.transAxes,
            fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor=color, alpha=0.7),
            family='monospace')
    
    # Overall title
    fig.suptitle(f'{state.name} State: Complete Thermodynamic Characterization',
                fontsize=16, fontweight='bold', y=0.98)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved visualization to {save_path}")
    
    return fig


def generate_all_state_visualizations(output_dir: str = "validation_outputs"):
    """Generate visualizations for all five thermodynamic states"""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generating thermodynamic states...")
    
    # Generate all states
    states = [
        generate_neutral_gas_state(N=1000, V=1e-3, T=300.0),
        generate_plasma_state(N=1000, V=1e-3, T=1e6),
        generate_degenerate_matter_state(N=1000, V=1e-9, T=4.2),
        generate_relativistic_gas_state(N=1000, V=1e-3, T=1e10),
        generate_bec_state(N=10000, V=1e-12, T=100e-9)
    ]
    
    # Create visualizations
    for state in states:
        print(f"\nCreating visualization for {state.name}...")
        filename = f"{output_dir}/{state.name.lower().replace(' ', '_')}_visualization.png"
        create_3d_panel_visualization(state, save_path=filename)
        plt.close()
    
    print(f"\nAll visualizations saved to {output_dir}/")
    
    # Create summary comparison
    create_comparative_summary(states, output_dir)


def create_comparative_summary(states: List[ThermodynamicState], output_dir: str):
    """Create a comparative summary figure showing all states side-by-side"""
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    # Plot S-entropy trajectories for all states
    for idx, state in enumerate(states):
        ax = axes[idx]
        
        # Extract trajectory
        Sk_traj = [s.Sk for s in state.s_entropy_trajectory]
        St_traj = [s.St for s in state.s_entropy_trajectory]
        Se_traj = [s.Se for s in state.s_entropy_trajectory]
        
        # 2D projection (Sk vs St)
        ax.plot(Sk_traj, St_traj, 'o-', alpha=0.5, markersize=2)
        ax.scatter([Sk_traj[0]], [St_traj[0]], color='green', s=100, marker='o', label='Start', zorder=5)
        ax.scatter([Sk_traj[-1]], [St_traj[-1]], color='red', s=100, marker='s', label='End', zorder=5)
        
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        ax.set_xlabel('$S_k$ (knowledge)', fontsize=10)
        ax.set_ylabel('$S_t$ (temporal)', fontsize=10)
        ax.set_title(f'{state.name}', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    
    # Hide extra subplot
    axes[-1].axis('off')
    
    fig.suptitle('S-Entropy Trajectories: Comparative Summary', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    save_path = f"{output_dir}/comparative_summary.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved comparative summary to {save_path}")
    plt.close()


if __name__ == "__main__":
    print("=" * 80)
    print("PARTITION-BASED EQUATIONS OF STATE: VALIDATION EXPERIMENTS")
    print("=" * 80)
    print("\nGenerating comprehensive 3D visualizations for all thermodynamic states...")
    print("This extends the spectroscopy validation framework to thermodynamics.\n")
    
    generate_all_state_visualizations()
    
    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)
    print("\nAll visualizations include:")
    print("  1. 3D phase space representation")
    print("  2. S-entropy trajectory in [0,1]³ space")
    print("  3. Partition coordinate distributions")
    print("  4. Thermodynamic metrics (radar chart)")
    print("  5. Velocity/momentum distributions")
    print("  6. Energy distributions")
    print("  7. Equation of state verification")
    print("\nThese visualizations validate the partition-based framework across")
    print("all five thermodynamic regimes with quantitative agreement metrics.")

