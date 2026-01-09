"""
Validation Suite for Partition-Based Equations of State and Categorical Dynamics

Generates validation plots:
1. Equations of State (4-panel plots for each regime)
2. Phase portraits for categorical dynamics
3. Eigenvalue analysis
4. Potential energy landscapes
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from typing import Dict, Tuple, Callable
import os


class ValidationSuite:
    """
    Complete validation suite for cellular state equations.
    
    Generates:
    - Equations of state validation (5 regimes)
    - Categorical dynamics phase portraits
    - Eigenvalue analysis
    - Potential energy surfaces
    """
    
    def __init__(self, output_dir: str = "validation_results"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Physical constants
        self.k_B = 1.380649e-23  # Boltzmann constant [J/K]
        self.h = 6.62607015e-34  # Planck constant [J·s]
        self.m_e = 9.1093837015e-31  # Electron mass [kg]
        self.c = 299792458  # Speed of light [m/s]
        
    def validate_all(self):
        """Run complete validation suite"""
        print("="*60)
        print("VALIDATION SUITE: Partition-Based Cellular State Equations")
        print("="*60)
        
        # 1. Equations of State
        print("\n[1/3] Validating Equations of State...")
        self.validate_equations_of_state()
        
        # 2. Categorical Dynamics
        print("\n[2/3] Validating Categorical Dynamics...")
        self.validate_categorical_dynamics()
        
        # 3. Phase Space Analysis
        print("\n[3/3] Analyzing Phase Space Structure...")
        self.analyze_phase_space()
        
        print(f"\n{'='*60}")
        print(f"Validation complete! Results saved to: {self.output_dir}/")
        print(f"{'='*60}")
    
    # ========================================================================
    # PART 1: EQUATIONS OF STATE VALIDATION
    # ========================================================================
    
    def validate_equations_of_state(self):
        """Validate all five equation of state regimes"""
        regimes = [
            ('neutral_gas', self.neutral_gas_eos),
            ('plasma', self.plasma_eos),
            ('degenerate', self.degenerate_eos),
            ('relativistic', self.relativistic_eos),
            ('bose_einstein', self.bose_einstein_eos)
        ]
        
        for name, eos_func in regimes:
            print(f"  - {name.replace('_', ' ').title()}...")
            self.plot_eos_4panel(name, eos_func)
    
    def neutral_gas_eos(self, V: np.ndarray, N: float, T: float) -> np.ndarray:
        """
        Neutral gas (ideal gas): PV = Nk_BT
        """
        return N * self.k_B * T / V
    
    def plasma_eos(self, V: np.ndarray, N: float, T: float) -> np.ndarray:
        """
        Plasma: P = Nk_BT/V × (1 - Γ/3)
        where Γ = (Ze)²/(4πε₀ a k_BT) is plasma parameter
        """
        # Typical plasma parameters
        Z = 1  # Singly ionized
        e = 1.602176634e-19  # Elementary charge
        epsilon_0 = 8.8541878128e-12  # Permittivity
        
        # Wigner-Seitz radius
        n = N / V  # Number density
        a = (3 / (4 * np.pi * n))**(1/3)
        
        # Plasma parameter
        Gamma = (Z * e)**2 / (4 * np.pi * epsilon_0 * a * self.k_B * T)
        
        # Pressure with plasma correction
        P_ideal = N * self.k_B * T / V
        return P_ideal * (1 - Gamma / 3)
    
    def degenerate_eos(self, V: np.ndarray, N: float, T: float) -> np.ndarray:
        """
        Degenerate electron gas: P = (ℏ²/5m)(3π²)^(2/3) (N/V)^(5/3)
        """
        hbar = self.h / (2 * np.pi)
        n = N / V  # Number density
        
        # Fermi pressure
        P_F = (hbar**2 / (5 * self.m_e)) * (3 * np.pi**2)**(2/3) * n**(5/3)
        
        # Thermal correction (small at T << T_F)
        E_F = (hbar**2 / (2 * self.m_e)) * (3 * np.pi**2 * n)**(2/3)
        T_F = E_F / self.k_B
        thermal_correction = 1 + (np.pi**2 / 12) * (T / T_F)**2
        
        return P_F * thermal_correction
    
    def relativistic_eos(self, V: np.ndarray, N: float, T: float) -> np.ndarray:
        """
        Relativistic gas: P = Nk_BT/V × [1 + (k_BT/mc²) + ...]
        """
        P_ideal = N * self.k_B * T / V
        
        # Relativistic correction
        relativistic_factor = 1 + (self.k_B * T) / (self.m_e * self.c**2)
        
        return P_ideal * relativistic_factor
    
    def bose_einstein_eos(self, V: np.ndarray, N: float, T: float) -> np.ndarray:
        """
        Bose-Einstein condensate: P ≈ 0 for T < T_c
        Above T_c: P = Nk_BT/V × g_{5/2}(z)
        """
        # Critical temperature (use average density)
        hbar = self.h / (2 * np.pi)
        n_avg = N / np.mean(V)
        m = 87 * 1.66053906660e-27  # Rb-87 mass [kg]
        T_c = (2 * np.pi * hbar**2 / (m * self.k_B)) * (n_avg / 2.612)**(2/3)
        
        # Pressure calculation
        P_ideal = N * self.k_B * T / V
        
        # Handle both scalar and array T
        T_arr = np.atleast_1d(T)
        condensed_fraction = np.where(T_arr < T_c, 0.01, 0.5)
        
        # If T was scalar, return scalar-compatible result
        if np.isscalar(T):
            return P_ideal * condensed_fraction[0]
        else:
            # T is array, broadcast properly
            return P_ideal * condensed_fraction[:, np.newaxis] if P_ideal.ndim > 1 else P_ideal * condensed_fraction
    
    def plot_eos_4panel(self, name: str, eos_func: Callable):
        """
        Generate 4-panel validation plot for equation of state:
        1. P vs V (isotherms)
        2. P vs T (isochores)
        3. PV vs T (compressibility)
        4. 3D surface: P(V, T)
        """
        fig = plt.figure(figsize=(14, 10))
        
        # Parameters
        N = 1e23  # Number of particles (1 mole ~ 6e23)
        V_range = np.linspace(1e-6, 1e-4, 100)  # Volume [m³]
        T_range = np.linspace(100, 1000, 100)  # Temperature [K]
        
        # Panel 1: P vs V (Isotherms)
        ax1 = fig.add_subplot(2, 2, 1)
        temperatures = [200, 400, 600, 800, 1000]
        for T in temperatures:
            P = eos_func(V_range, N, T)
            ax1.plot(V_range * 1e6, P / 1e5, label=f'T = {T} K')
        ax1.set_xlabel('Volume [cm³]')
        ax1.set_ylabel('Pressure [bar]')
        ax1.set_title(f'{name.replace("_", " ").title()}: Isotherms')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_xscale('log')
        ax1.set_yscale('log')
        
        # Panel 2: P vs T (Isochores)
        ax2 = fig.add_subplot(2, 2, 2)
        volumes = [1e-6, 2e-6, 5e-6, 1e-5, 2e-5]
        for V in volumes:
            P = eos_func(np.array([V]), N, T_range)
            ax2.plot(T_range, P / 1e5, label=f'V = {V*1e6:.1f} cm³')
        ax2.set_xlabel('Temperature [K]')
        ax2.set_ylabel('Pressure [bar]')
        ax2.set_title(f'{name.replace("_", " ").title()}: Isochores')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Panel 3: PV vs T (Compressibility factor)
        ax3 = fig.add_subplot(2, 2, 3)
        V_fixed = 1e-5  # Fixed volume
        P = eos_func(np.array([V_fixed]), N, T_range)
        PV = P * V_fixed
        PV_ideal = N * self.k_B * T_range
        Z = PV / PV_ideal  # Compressibility factor
        ax3.plot(T_range, Z, 'b-', linewidth=2)
        ax3.axhline(y=1, color='r', linestyle='--', label='Ideal gas (Z=1)')
        ax3.set_xlabel('Temperature [K]')
        ax3.set_ylabel('Compressibility Factor Z = PV/(Nk_BT)')
        ax3.set_title(f'{name.replace("_", " ").title()}: Deviation from Ideal')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Panel 4: 3D Surface P(V, T)
        ax4 = fig.add_subplot(2, 2, 4, projection='3d')
        V_mesh, T_mesh = np.meshgrid(V_range, T_range)
        P_mesh = np.zeros_like(V_mesh)
        for i in range(len(T_range)):
            P_mesh[i, :] = eos_func(V_range, N, T_range[i])
        
        surf = ax4.plot_surface(V_mesh * 1e6, T_mesh, P_mesh / 1e5,
                                cmap='viridis', alpha=0.8)
        ax4.set_xlabel('Volume [cm³]')
        ax4.set_ylabel('Temperature [K]')
        ax4.set_zlabel('Pressure [bar]')
        ax4.set_title(f'{name.replace("_", " ").title()}: P(V,T) Surface')
        fig.colorbar(surf, ax=ax4, shrink=0.5)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/eos_{name}.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    # ========================================================================
    # PART 2: CATEGORICAL DYNAMICS VALIDATION
    # ========================================================================
    
    def validate_categorical_dynamics(self):
        """Validate categorical dynamics with phase portraits"""
        print("  - Pendulum dynamics (categorical form)...")
        self.plot_categorical_pendulum()
        
        print("  - S-entropy trajectory...")
        self.plot_sentropy_trajectory()
        
        print("  - Memory reset dynamics...")
        self.plot_memory_reset()
    
    def plot_categorical_pendulum(self):
        """
        Phase portrait for categorical pendulum:
        ∂²θ/∂p² + (g/L)sinθ = 0
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Parameters
        g = 9.81  # Gravity [m/s²]
        L = 1.0   # Length [m]
        omega_0 = np.sqrt(g / L)
        
        # Panel 1: Phase portrait (θ vs ∂θ/∂p)
        ax1 = axes[0, 0]
        theta = np.linspace(-2*np.pi, 2*np.pi, 20)
        dtheta = np.linspace(-3, 3, 20)
        Theta, Dtheta = np.meshgrid(theta, dtheta)
        
        # Derivatives
        dTheta_dp = Dtheta
        dDtheta_dp = -omega_0**2 * np.sin(Theta)
        
        # Normalize for quiver plot
        M = np.sqrt(dTheta_dp**2 + dDtheta_dp**2)
        M[M == 0] = 1
        dTheta_dp_norm = dTheta_dp / M
        dDtheta_dp_norm = dDtheta_dp / M
        
        ax1.quiver(Theta, Dtheta, dTheta_dp_norm, dDtheta_dp_norm, M,
                   cmap='viridis', alpha=0.6)
        
        # Add trajectories
        for E in [0.5, 1.0, 2.0, 4.0]:
            theta_traj = np.linspace(-np.pi, np.pi, 1000)
            # Energy: E = (1/2)(∂θ/∂p)² + ω₀²(1 - cosθ)
            dtheta_traj_sq = 2 * E - 2 * omega_0**2 * (1 - np.cos(theta_traj))
            valid = dtheta_traj_sq >= 0
            dtheta_traj = np.sqrt(dtheta_traj_sq[valid])
            ax1.plot(theta_traj[valid], dtheta_traj, 'r-', linewidth=1.5, alpha=0.7)
            ax1.plot(theta_traj[valid], -dtheta_traj, 'r-', linewidth=1.5, alpha=0.7)
        
        ax1.set_xlabel('θ [rad]')
        ax1.set_ylabel('∂θ/∂p [rad/partition]')
        ax1.set_title('Categorical Pendulum: Phase Portrait')
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='k', linewidth=0.5)
        ax1.axvline(x=0, color='k', linewidth=0.5)
        
        # Panel 2: Time series with memory reset
        ax2 = axes[0, 1]
        p = np.linspace(0, 30, 1000)  # Partition coordinate
        
        # Simulate pendulum with memory reset every 10 partitions
        theta_full = []
        dtheta_full = []
        p_full = []
        
        for category in range(3):
            p_cat = p[:333]  # One category
            theta_0 = np.random.uniform(-np.pi/4, np.pi/4)  # Random initial
            dtheta_0 = np.random.uniform(-0.5, 0.5)
            
            # Solve within category
            theta_cat = theta_0 * np.cos(omega_0 * p_cat) + (dtheta_0/omega_0) * np.sin(omega_0 * p_cat)
            dtheta_cat = -theta_0 * omega_0 * np.sin(omega_0 * p_cat) + dtheta_0 * np.cos(omega_0 * p_cat)
            
            theta_full.extend(theta_cat)
            dtheta_full.extend(dtheta_cat)
            p_full.extend(p_cat + category * 10)
        
        ax2.plot(p_full, theta_full, 'b-', linewidth=2, label='θ(p)')
        for c in [10, 20]:
            ax2.axvline(x=c, color='r', linestyle='--', linewidth=2, alpha=0.7)
        ax2.set_xlabel('Partition Coordinate p')
        ax2.set_ylabel('θ [rad]')
        ax2.set_title('Memory Reset at Category Boundaries')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.text(5, 0.8, 'Category 1', fontsize=10)
        ax2.text(15, 0.8, 'Category 2', fontsize=10)
        ax2.text(25, 0.8, 'Category 3', fontsize=10)
        
        # Panel 3: Potential energy
        ax3 = axes[1, 0]
        theta_pot = np.linspace(-2*np.pi, 2*np.pi, 500)
        U = omega_0**2 * (1 - np.cos(theta_pot))
        ax3.plot(theta_pot, U, 'g-', linewidth=2)
        ax3.fill_between(theta_pot, 0, U, alpha=0.3, color='green')
        ax3.set_xlabel('θ [rad]')
        ax3.set_ylabel('Potential Energy U(θ)')
        ax3.set_title('Potential Energy Landscape')
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=0, color='k', linewidth=0.5)
        
        # Panel 4: Frequency spectrum
        ax4 = axes[1, 1]
        # FFT of oscillation
        dt = 0.01
        t = np.arange(0, 10, dt)
        theta_t = 0.5 * np.cos(omega_0 * t)
        
        fft = np.fft.fft(theta_t)
        freq = np.fft.fftfreq(len(t), dt)
        power = np.abs(fft)**2
        
        positive_freq = freq > 0
        ax4.plot(freq[positive_freq], power[positive_freq], 'b-', linewidth=2)
        ax4.axvline(x=omega_0/(2*np.pi), color='r', linestyle='--', 
                    label=f'ω₀/(2π) = {omega_0/(2*np.pi):.2f} Hz')
        ax4.set_xlabel('Frequency [Hz]')
        ax4.set_ylabel('Power Spectrum')
        ax4.set_title('Frequency Analysis')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.set_xlim(0, 2)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/categorical_pendulum.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_sentropy_trajectory(self):
        """Plot trajectory in S-entropy space"""
        fig = plt.figure(figsize=(14, 10))
        
        # Generate trajectory
        t = np.linspace(0, 10, 1000)
        
        # S-entropy coordinates evolve periodically
        S_k = 0.5 + 0.3 * np.sin(0.5 * t)
        S_t = 0.5 + 0.2 * np.sin(0.8 * t + np.pi/4)
        S_e = 0.5 + 0.25 * np.sin(0.3 * t + np.pi/2)
        
        # 3D trajectory
        ax1 = fig.add_subplot(2, 2, 1, projection='3d')
        scatter = ax1.scatter(S_k, S_t, S_e, c=t, cmap='viridis', s=10)
        ax1.plot(S_k, S_t, S_e, 'b-', alpha=0.3, linewidth=1)
        ax1.set_xlabel('S_k (Knowledge)')
        ax1.set_ylabel('S_t (Temporal)')
        ax1.set_zlabel('S_e (Evolution)')
        ax1.set_title('Trajectory in S-Entropy Space')
        fig.colorbar(scatter, ax=ax1, label='Time')
        
        # 2D projections
        ax2 = fig.add_subplot(2, 2, 2)
        ax2.plot(S_k, S_t, 'b-', linewidth=2)
        ax2.set_xlabel('S_k')
        ax2.set_ylabel('S_t')
        ax2.set_title('S_k - S_t Projection')
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(0, 1)
        ax2.set_ylim(0, 1)
        
        ax3 = fig.add_subplot(2, 2, 3)
        ax3.plot(S_k, S_e, 'g-', linewidth=2)
        ax3.set_xlabel('S_k')
        ax3.set_ylabel('S_e')
        ax3.set_title('S_k - S_e Projection')
        ax3.grid(True, alpha=0.3)
        ax3.set_xlim(0, 1)
        ax3.set_ylim(0, 1)
        
        ax4 = fig.add_subplot(2, 2, 4)
        ax4.plot(S_t, S_e, 'r-', linewidth=2)
        ax4.set_xlabel('S_t')
        ax4.set_ylabel('S_e')
        ax4.set_title('S_t - S_e Projection')
        ax4.grid(True, alpha=0.3)
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/sentropy_trajectory.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_memory_reset(self):
        """Visualize memory reset at categorical boundaries"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Simulate system with and without memory reset
        n_points = 1000
        p = np.linspace(0, 30, n_points)
        
        # Panel 1: With memory reset (correct)
        ax1 = axes[0, 0]
        x_reset = []
        points_per_cat = n_points // 3
        
        for cat in range(3):
            start_idx = cat * points_per_cat
            end_idx = (cat + 1) * points_per_cat if cat < 2 else n_points
            p_cat = p[start_idx:end_idx] - p[start_idx]  # Reset to 0 for each category
            x_0 = np.random.uniform(-1, 1)
            x_cat = x_0 * np.exp(-0.1 * p_cat) * np.cos(p_cat)
            x_reset.extend(x_cat)
        
        ax1.plot(p, x_reset, 'b-', linewidth=2)
        for c in [10, 20]:
            ax1.axvline(x=c, color='r', linestyle='--', linewidth=2)
        ax1.set_xlabel('Partition Coordinate p')
        ax1.set_ylabel('State Variable x')
        ax1.set_title('WITH Memory Reset (Correct)')
        ax1.grid(True, alpha=0.3)
        
        # Panel 2: Without memory reset (accumulates history)
        ax2 = axes[0, 1]
        x_no_reset = np.zeros(len(p))
        x_no_reset[0] = 1.0
        for i in range(1, len(p)):
            x_no_reset[i] = x_no_reset[i-1] * 0.999 + 0.1 * np.sin(p[i])
        
        ax2.plot(p, x_no_reset, 'r-', linewidth=2)
        for c in [10, 20]:
            ax2.axvline(x=c, color='gray', linestyle='--', linewidth=2, alpha=0.5)
        ax2.set_xlabel('Partition Coordinate p')
        ax2.set_ylabel('State Variable x')
        ax2.set_title('WITHOUT Memory Reset (Wrong - History Accumulates)')
        ax2.grid(True, alpha=0.3)
        
        # Panel 3: Phase coherence with reset
        ax3 = axes[1, 0]
        phases = []
        for cat in range(10):
            phase_cat = np.random.uniform(0, 2*np.pi, 50)
            phases.extend(phase_cat)
        
        p_extended = np.linspace(0, 100, 500)
        ax3.scatter(p_extended, phases, c='blue', s=10, alpha=0.6)
        for c in range(10, 100, 10):
            ax3.axvline(x=c, color='r', linestyle='--', alpha=0.3)
        ax3.set_xlabel('Partition Coordinate p')
        ax3.set_ylabel('Phase [rad]')
        ax3.set_title('Phase Reset at Each Category')
        ax3.grid(True, alpha=0.3)
        
        # Panel 4: Histogram of initial conditions
        ax4 = axes[1, 1]
        initial_conditions = [np.random.uniform(-1, 1) for _ in range(1000)]
        ax4.hist(initial_conditions, bins=50, color='green', alpha=0.7, edgecolor='black')
        ax4.set_xlabel('Initial Condition x₀')
        ax4.set_ylabel('Frequency')
        ax4.set_title('Distribution of Initial Conditions After Reset')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/memory_reset.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    # ========================================================================
    # PART 3: PHASE SPACE ANALYSIS
    # ========================================================================
    
    def analyze_phase_space(self):
        """Analyze phase space structure"""
        print("  - Eigenvalue analysis...")
        self.plot_eigenvalue_analysis()
        
        print("  - Phase plane analysis...")
        self.plot_phase_plane()
        
        print("  - Potential energy surface...")
        self.plot_potential_energy_3d()
    
    def plot_eigenvalue_analysis(self):
        """Eigenvalue analysis for categorical dynamics"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Linearized system: dx/dp = Ax
        # For pendulum: [θ, ∂θ/∂p]' = [0, 1; -ω₀², 0] [θ, ∂θ/∂p]'
        
        omega_0_values = np.linspace(0.5, 5, 100)
        
        # Panel 1: Eigenvalues vs parameter
        ax1 = axes[0, 0]
        eigenvalues_real = []
        eigenvalues_imag = []
        
        for omega_0 in omega_0_values:
            A = np.array([[0, 1], [-omega_0**2, 0]])
            eigvals = np.linalg.eigvals(A)
            eigenvalues_real.append(eigvals.real)
            eigenvalues_imag.append(eigvals.imag)
        
        eigenvalues_real = np.array(eigenvalues_real)
        eigenvalues_imag = np.array(eigenvalues_imag)
        
        ax1.plot(omega_0_values, eigenvalues_imag[:, 0], 'b-', linewidth=2, label='λ₁ (imag)')
        ax1.plot(omega_0_values, eigenvalues_imag[:, 1], 'r-', linewidth=2, label='λ₂ (imag)')
        ax1.axhline(y=0, color='k', linestyle='--', alpha=0.5)
        ax1.set_xlabel('ω₀ [rad/partition]')
        ax1.set_ylabel('Imaginary Part of Eigenvalue')
        ax1.set_title('Eigenvalues vs System Parameter')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Panel 2: Complex plane (eigenvalue locus)
        ax2 = axes[0, 1]
        ax2.plot(eigenvalues_real[:, 0], eigenvalues_imag[:, 0], 'b-', linewidth=2, label='λ₁')
        ax2.plot(eigenvalues_real[:, 1], eigenvalues_imag[:, 1], 'r-', linewidth=2, label='λ₂')
        ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
        ax2.axvline(x=0, color='k', linestyle='--', alpha=0.5)
        ax2.set_xlabel('Real Part')
        ax2.set_ylabel('Imaginary Part')
        ax2.set_title('Eigenvalue Locus in Complex Plane')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.axis('equal')
        
        # Panel 3: Stability diagram
        ax3 = axes[1, 0]
        damping_values = np.linspace(0, 2, 100)
        stability = []
        
        for damping in damping_values:
            A_damped = np.array([[0, 1], [-omega_0_values[50]**2, -damping]])
            eigvals = np.linalg.eigvals(A_damped)
            max_real = np.max(eigvals.real)
            stability.append(max_real)
        
        ax3.plot(damping_values, stability, 'g-', linewidth=2)
        ax3.axhline(y=0, color='r', linestyle='--', linewidth=2, label='Stability boundary')
        ax3.fill_between(damping_values, -1, 0, alpha=0.3, color='green', label='Stable')
        ax3.fill_between(damping_values, 0, 1, alpha=0.3, color='red', label='Unstable')
        ax3.set_xlabel('Damping Coefficient')
        ax3.set_ylabel('Max Real(λ)')
        ax3.set_title('Stability Diagram')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Panel 4: Eigenvector field
        ax4 = axes[1, 1]
        omega_0 = 2.0
        A = np.array([[0, 1], [-omega_0**2, 0]])
        eigvals, eigvecs = np.linalg.eig(A)
        
        # Plot eigenvectors
        for i in range(2):
            vec = eigvecs[:, i].real
            ax4.arrow(0, 0, vec[0], vec[1], head_width=0.1, head_length=0.1,
                     fc=f'C{i}', ec=f'C{i}', linewidth=2, label=f'v₁ (λ={eigvals[i]:.2f})')
        
        ax4.set_xlabel('θ component')
        ax4.set_ylabel('∂θ/∂p component')
        ax4.set_title('Eigenvectors in Phase Space')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.axis('equal')
        ax4.set_xlim(-1.5, 1.5)
        ax4.set_ylim(-1.5, 1.5)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/eigenvalue_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_phase_plane(self):
        """Detailed phase plane analysis"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        omega_0 = np.sqrt(9.81)
        
        # Panel 1: Nullclines
        ax1 = axes[0, 0]
        theta = np.linspace(-np.pi, np.pi, 500)
        
        # θ-nullcline: ∂θ/∂p = 0
        ax1.axhline(y=0, color='b', linewidth=2, label='θ-nullcline')
        
        # ∂θ/∂p-nullcline: ∂²θ/∂p² = 0 → sinθ = 0
        ax1.axvline(x=0, color='r', linewidth=2, label='∂θ/∂p-nullcline')
        ax1.axvline(x=np.pi, color='r', linewidth=2)
        ax1.axvline(x=-np.pi, color='r', linewidth=2)
        
        # Fixed points
        ax1.plot(0, 0, 'go', markersize=15, label='Stable (center)')
        ax1.plot(np.pi, 0, 'ro', markersize=15, label='Unstable (saddle)')
        ax1.plot(-np.pi, 0, 'ro', markersize=15)
        
        ax1.set_xlabel('θ [rad]')
        ax1.set_ylabel('∂θ/∂p')
        ax1.set_title('Nullclines and Fixed Points')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(-np.pi, np.pi)
        ax1.set_ylim(-3, 3)
        
        # Panel 2: Separatrix
        ax2 = axes[0, 1]
        theta_sep = np.linspace(-np.pi, np.pi, 1000)
        # Separatrix energy: E = 2ω₀² (at saddle point)
        E_sep = 2 * omega_0**2
        dtheta_sep_sq = 2 * E_sep - 2 * omega_0**2 * (1 - np.cos(theta_sep))
        valid = dtheta_sep_sq >= 0
        dtheta_sep = np.sqrt(dtheta_sep_sq[valid])
        
        ax2.plot(theta_sep[valid], dtheta_sep, 'r-', linewidth=3, label='Separatrix')
        ax2.plot(theta_sep[valid], -dtheta_sep, 'r-', linewidth=3)
        
        # Add some trajectories inside
        for E in [0.5, 1.0, 1.5]:
            theta_traj = np.linspace(-np.pi, np.pi, 1000)
            dtheta_traj_sq = 2 * E - 2 * omega_0**2 * (1 - np.cos(theta_traj))
            valid_traj = dtheta_traj_sq >= 0
            if np.any(valid_traj):
                dtheta_traj = np.sqrt(dtheta_traj_sq[valid_traj])
                ax2.plot(theta_traj[valid_traj], dtheta_traj, 'b-', alpha=0.5, linewidth=1)
                ax2.plot(theta_traj[valid_traj], -dtheta_traj, 'b-', alpha=0.5, linewidth=1)
        
        ax2.set_xlabel('θ [rad]')
        ax2.set_ylabel('∂θ/∂p')
        ax2.set_title('Separatrix and Bounded Trajectories')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Panel 3: Basin of attraction
        ax3 = axes[1, 0]
        theta_grid = np.linspace(-2*np.pi, 2*np.pi, 100)
        dtheta_grid = np.linspace(-4, 4, 100)
        Theta_grid, Dtheta_grid = np.meshgrid(theta_grid, dtheta_grid)
        
        # Energy at each point
        E_grid = 0.5 * Dtheta_grid**2 + omega_0**2 * (1 - np.cos(Theta_grid))
        
        contour = ax3.contourf(Theta_grid, Dtheta_grid, E_grid, levels=20, cmap='viridis')
        fig.colorbar(contour, ax=ax3, label='Energy')
        ax3.set_xlabel('θ [rad]')
        ax3.set_ylabel('∂θ/∂p')
        ax3.set_title('Energy Landscape (Basin of Attraction)')
        ax3.grid(True, alpha=0.3)
        
        # Panel 4: Poincaré section
        ax4 = axes[1, 1]
        # Simulate and take Poincaré section at θ = 0
        poincare_points = []
        
        for E in np.linspace(0.1, 3.9, 20):
            # At θ = 0: E = (1/2)(∂θ/∂p)² + ω₀²(1 - 1) = (1/2)(∂θ/∂p)²
            dtheta_at_zero = np.sqrt(2 * E)
            if dtheta_at_zero < 4:
                poincare_points.append((0, dtheta_at_zero))
                poincare_points.append((0, -dtheta_at_zero))
        
        if poincare_points:
            poincare_points = np.array(poincare_points)
            ax4.scatter(poincare_points[:, 0], poincare_points[:, 1], 
                       c='blue', s=50, alpha=0.7)
        
        ax4.set_xlabel('θ [rad]')
        ax4.set_ylabel('∂θ/∂p')
        ax4.set_title('Poincaré Section at θ = 0')
        ax4.grid(True, alpha=0.3)
        ax4.set_xlim(-0.5, 0.5)
        ax4.set_ylim(-4, 4)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/phase_plane.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_potential_energy_3d(self):
        """3D potential energy surface"""
        fig = plt.figure(figsize=(14, 10))
        
        # Panel 1: 3D surface
        ax1 = fig.add_subplot(2, 2, 1, projection='3d')
        theta = np.linspace(-2*np.pi, 2*np.pi, 100)
        dtheta = np.linspace(-4, 4, 100)
        Theta, Dtheta = np.meshgrid(theta, dtheta)
        
        omega_0 = np.sqrt(9.81)
        E = 0.5 * Dtheta**2 + omega_0**2 * (1 - np.cos(Theta))
        
        surf = ax1.plot_surface(Theta, Dtheta, E, cmap='viridis', alpha=0.8)
        ax1.set_xlabel('θ [rad]')
        ax1.set_ylabel('∂θ/∂p')
        ax1.set_zlabel('Total Energy E')
        ax1.set_title('Energy Surface E(θ, ∂θ/∂p)')
        fig.colorbar(surf, ax=ax1, shrink=0.5)
        
        # Panel 2: Contour plot
        ax2 = fig.add_subplot(2, 2, 2)
        contour = ax2.contour(Theta, Dtheta, E, levels=20, cmap='viridis')
        ax2.clabel(contour, inline=True, fontsize=8)
        ax2.set_xlabel('θ [rad]')
        ax2.set_ylabel('∂θ/∂p')
        ax2.set_title('Energy Contours')
        ax2.grid(True, alpha=0.3)
        
        # Panel 3: Potential only
        ax3 = fig.add_subplot(2, 2, 3)
        U = omega_0**2 * (1 - np.cos(theta))
        ax3.plot(theta, U, 'b-', linewidth=2)
        ax3.fill_between(theta, 0, U, alpha=0.3)
        ax3.set_xlabel('θ [rad]')
        ax3.set_ylabel('Potential Energy U(θ)')
        ax3.set_title('Potential Energy Function')
        ax3.grid(True, alpha=0.3)
        
        # Mark equilibria
        ax3.plot(0, 0, 'go', markersize=15, label='Stable minimum')
        ax3.plot(np.pi, 2*omega_0**2, 'ro', markersize=15, label='Unstable maximum')
        ax3.plot(-np.pi, 2*omega_0**2, 'ro', markersize=15)
        ax3.legend()
        
        # Panel 4: Force field
        ax4 = fig.add_subplot(2, 2, 4)
        F = -omega_0**2 * np.sin(theta)
        ax4.plot(theta, F, 'r-', linewidth=2)
        ax4.axhline(y=0, color='k', linestyle='--', alpha=0.5)
        ax4.fill_between(theta, 0, F, where=(F>0), alpha=0.3, color='blue', label='Restoring')
        ax4.fill_between(theta, 0, F, where=(F<0), alpha=0.3, color='red', label='Destabilizing')
        ax4.set_xlabel('θ [rad]')
        ax4.set_ylabel('Force F = -dU/dθ')
        ax4.set_title('Force Field')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/potential_energy_3d.png', dpi=300, bbox_inches='tight')
        plt.close()


# Convenience function
def run_validation(output_dir: str = "validation_results"):
    """Run complete validation suite"""
    suite = ValidationSuite(output_dir=output_dir)
    suite.validate_all()
    return suite
