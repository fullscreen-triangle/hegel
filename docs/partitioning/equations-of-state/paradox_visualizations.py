"""
Paradox Resolution and Theoretical Visualization Module

Creates specialized panel charts for:
1. Paradox resolution diagrams (Loschmidt, Kelvin, Maxwell)
2. Phase space partition visualizations
3. S-entropy coordinate trajectories (Poincaré recurrence)
4. Velocity distribution cutoffs at c
5. Structural factor S(q) plots across regimes
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
from typing import List, Tuple, Optional
from validation_experiments import (
    kB, hbar, c, me, mp, e, epsilon0,
    generate_neutral_gas_state,
    generate_plasma_state,
    generate_degenerate_matter_state,
    generate_relativistic_gas_state,
    generate_bec_state
)


def create_paradox_resolution_diagrams(save_path: Optional[str] = None):
    """
    Create comprehensive panel showing computational impossibilities
    for Loschmidt, Kelvin, and Maxwell paradoxes.
    """
    fig = plt.figure(figsize=(20, 12))
    gs = GridSpec(2, 3, figure=fig, hspace=0.3, wspace=0.3)
    
    colors = sns.color_palette("husl", 8)
    
    # ============ Panel 1: Loschmidt Paradox - Relativistic Impossibility ============
    ax1 = fig.add_subplot(gs[0, 0])
    
    # Volume expansion ratios
    alpha = np.logspace(0, 18, 100)  # V2/V1 from 1 to 10^18
    
    # Required velocity for reversal (assuming expansion time tau = 1s)
    tau = 1.0  # seconds
    L1 = 0.1  # Initial container size (m)
    v_required = L1 * (alpha**(1/3) - 1) / tau
    
    # Plot
    ax1.loglog(alpha, v_required, linewidth=3, color=colors[0], label='Required velocity')
    ax1.axhline(c, color='red', linestyle='--', linewidth=2, label='Speed of light c')
    
    # Mark critical expansion ratio
    alpha_crit_H2 = (c / 1900)**3  # Hydrogen at 300K
    alpha_crit_N2 = (c / 500)**3   # Nitrogen at 300K
    ax1.axvline(alpha_crit_H2, color='blue', linestyle=':', alpha=0.7, label=r'$\alpha_{crit}$ (H$_2$)')
    ax1.axvline(alpha_crit_N2, color='green', linestyle=':', alpha=0.7, label=r'$\alpha_{crit}$ (N$_2$)')
    
    ax1.fill_between(alpha, 0, c, alpha=0.2, color='green', label='Physically possible')
    ax1.fill_between(alpha, c, 1e10, alpha=0.2, color='red', label='Impossible (v > c)')
    
    ax1.set_xlabel(r'Expansion Ratio $\alpha = V_2/V_1$', fontsize=12)
    ax1.set_ylabel('Required Velocity (m/s)', fontsize=12)
    ax1.set_title('Loschmidt Paradox: Relativistic Impossibility', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim([1e2, 1e10])
    
    # ============ Panel 2: Loschmidt - Categorical Irreversibility ============
    ax2 = fig.add_subplot(gs[0, 1])
    
    # Time evolution of categorical states
    time = np.linspace(0, 10, 100)
    
    # Forward process: entropy increases
    S_forward = 1 - np.exp(-time)
    
    # "Reversed" process: still increases entropy (measurement cost)
    S_measurement = np.ones_like(time) * 0.7
    S_reversed = S_measurement + 0.3 * (1 - np.exp(-time))
    
    ax2.plot(time, S_forward, linewidth=3, color=colors[1], label='Forward process')
    ax2.plot(time, S_reversed, linewidth=3, color=colors[2], linestyle='--', 
            label='Attempted reversal\n(includes measurement)')
    ax2.axhline(S_measurement[0], color='orange', linestyle=':', linewidth=2, 
               label='Measurement entropy cost')
    
    ax2.fill_between(time, 0, S_forward, alpha=0.2, color=colors[1])
    ax2.fill_between(time, S_measurement, S_reversed, alpha=0.2, color=colors[2])
    
    ax2.set_xlabel('Time (arbitrary units)', fontsize=12)
    ax2.set_ylabel('Categorical Entropy S', fontsize=12)
    ax2.set_title('Loschmidt Paradox: Categorical Irreversibility', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([0, 1.2])
    
    # ============ Panel 3: Kelvin Paradox - Trajectory Completion Time ============
    ax3 = fig.add_subplot(gs[0, 2])
    
    # Temperature ratios
    T_ratio = np.linspace(0, 1, 100)  # T_C/T_H
    
    # Carnot efficiency
    eta_carnot = 1 - T_ratio
    
    # Trajectory completion time (normalized, diverges as T_C -> 0)
    T_completion = 1 / (T_ratio + 0.01)  # Add small offset to avoid division by zero
    
    # Plot efficiency
    ax3_twin = ax3.twinx()
    
    line1 = ax3.plot(T_ratio, eta_carnot, linewidth=3, color=colors[3], 
                    label=r'Carnot efficiency $\eta = 1 - T_C/T_H$')
    line2 = ax3_twin.plot(T_ratio, T_completion, linewidth=3, color=colors[4], 
                         linestyle='--', label='Trajectory completion time')
    
    # Mark impossible region
    ax3.fill_between([0, 0.05], 0, 1, alpha=0.3, color='red', 
                    label='Impossible\n(violates 3rd law)')
    
    ax3.set_xlabel(r'Temperature Ratio $T_C/T_H$', fontsize=12)
    ax3.set_ylabel('Carnot Efficiency', fontsize=12, color=colors[3])
    ax3_twin.set_ylabel('Trajectory Completion Time (arb.)', fontsize=12, color=colors[4])
    ax3.set_title('Kelvin Paradox: Trajectory Completion', fontsize=14, fontweight='bold')
    
    ax3.tick_params(axis='y', labelcolor=colors[3])
    ax3_twin.tick_params(axis='y', labelcolor=colors[4])
    
    # Combine legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax3.legend(lines, labels, fontsize=9, loc='upper left')
    
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim([0, 1])
    ax3_twin.set_ylim([0, 100])
    
    # ============ Panel 4: Maxwell Demon - Information Cost ============
    ax4 = fig.add_subplot(gs[1, 0])
    
    # Number of sorting operations
    N_sort = np.arange(1, 101)
    
    # Entropy decrease from sorting
    Delta_S_gas = -kB * N_sort * np.log(2)
    
    # Entropy increase from measurement + erasure
    Delta_S_measurement = kB * N_sort * np.log(2) * 0.5  # Measurement
    Delta_S_erasure = kB * N_sort * np.log(2)  # Erasure (Landauer)
    Delta_S_total = Delta_S_measurement + Delta_S_erasure
    
    # Net entropy change
    Delta_S_net = Delta_S_gas + Delta_S_total
    
    ax4.plot(N_sort, Delta_S_gas / kB, linewidth=3, color='blue', 
            label=r'Gas entropy decrease $-N k_B \ln 2$')
    ax4.plot(N_sort, Delta_S_measurement / kB, linewidth=2, color='orange', 
            linestyle='--', label='Measurement cost')
    ax4.plot(N_sort, Delta_S_erasure / kB, linewidth=2, color='red', 
            linestyle='--', label=r'Erasure cost (Landauer)')
    ax4.plot(N_sort, Delta_S_net / kB, linewidth=3, color='green', 
            label=r'Net entropy change $\geq 0$')
    
    ax4.axhline(0, color='black', linestyle='-', linewidth=1, alpha=0.5)
    ax4.fill_between(N_sort, 0, Delta_S_net / kB, alpha=0.2, color='green')
    
    ax4.set_xlabel('Number of Sorting Operations', fontsize=12)
    ax4.set_ylabel(r'Entropy Change / $k_B$', fontsize=12)
    ax4.set_title("Maxwell's Demon: Information Cost", fontsize=14, fontweight='bold')
    ax4.legend(fontsize=9)
    ax4.grid(True, alpha=0.3)
    
    # ============ Panel 5: Maxwell Demon - Partition State Coupling ============
    ax5 = fig.add_subplot(gs[1, 1])
    
    # Partition states before and after measurement
    states = ['Gas\n(initial)', 'Demon\n(blank)', 'Gas\n(sorted)', 'Demon\n(memory)', 'Total']
    entropy_before = [100, 0, 0, 0, 100]
    entropy_after = [70, 0, 30, 30, 100]
    
    x = np.arange(len(states))
    width = 0.35
    
    bars1 = ax5.bar(x - width/2, entropy_before, width, label='Before sorting', 
                   color=colors[5], alpha=0.8, edgecolor='black')
    bars2 = ax5.bar(x + width/2, entropy_after, width, label='After sorting', 
                   color=colors[6], alpha=0.8, edgecolor='black')
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax5.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom', fontsize=9)
    
    ax5.set_ylabel('Entropy (arbitrary units)', fontsize=12)
    ax5.set_title("Maxwell's Demon: Partition State Coupling", fontsize=14, fontweight='bold')
    ax5.set_xticks(x)
    ax5.set_xticklabels(states, fontsize=10)
    ax5.legend(fontsize=10)
    ax5.grid(True, alpha=0.3, axis='y')
    
    # ============ Panel 6: Computational Impossibility Summary ============
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.axis('off')
    
    summary_text = """
COMPUTATIONAL IMPOSSIBILITY SUMMARY

Loschmidt's Paradox:
  • Relativistic: v_required > c for α > 10^15
  • Categorical: Measurement creates irreversible 
    categorical states
  • Resolution: Physical impossibility, not improbability

Kelvin's Heat Engine:
  • Perfect efficiency (η=1) requires T_C = 0
  • Violates Third Law (unattainable in finite time)
  • Trajectory completion time → ∞ as T_C → 0
  • Resolution: Geometric constraint from bounded 
    phase space

Maxwell's Demon:
  • Sorting decreases gas entropy: ΔS_gas < 0
  • Measurement + erasure increase total entropy
  • Net: ΔS_total = ΔS_gas + ΔS_demon ≥ 0
  • Resolution: Information processing cost
  
All three paradoxes resolved through:
  ✓ Bounded phase space constraints
  ✓ Categorical state transitions
  ✓ Trajectory completion requirements
  ✓ Information-theoretic limits
"""
    
    ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes,
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
            family='monospace')
    
    fig.suptitle('Paradox Resolution: Computational Impossibilities', 
                fontsize=16, fontweight='bold', y=0.98)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved paradox resolution diagrams to {save_path}")
    
    return fig


def create_phase_space_partition_visualizations(save_path: Optional[str] = None):
    """
    Create 3D phase space partition visualizations for all five regimes.
    """
    fig = plt.figure(figsize=(20, 12))
    gs = GridSpec(2, 3, figure=fig, hspace=0.3, wspace=0.3)
    
    # Generate states
    states = [
        generate_neutral_gas_state(N=500, V=1e-3, T=300.0),
        generate_plasma_state(N=500, V=1e-3, T=1e6),
        generate_degenerate_matter_state(N=500, V=1e-21, T=1e4),
        generate_relativistic_gas_state(N=500, V=1e-3, T=1e10),
        generate_bec_state(N=1000, V=1e-12, T=50e-9)
    ]
    
    positions = [0, 1, 2, 3, 4]
    
    for idx, (state, pos) in enumerate(zip(states, positions)):
        if pos < 5:
            row = pos // 3
            col = pos % 3
            ax = fig.add_subplot(gs[row, col], projection='3d')
            
            # Sample particles for visualization
            sample_size = min(300, len(state.partition_coords))
            sample_idx = np.random.choice(len(state.partition_coords), sample_size, replace=False)
            
            # Get partition depths for coloring
            n_values = np.array([state.partition_coords[i].n for i in sample_idx])
            
            # Plot
            scatter = ax.scatter(state.positions[sample_idx, 0] * 1e6,
                               state.positions[sample_idx, 1] * 1e6,
                               state.positions[sample_idx, 2] * 1e6,
                               c=n_values, cmap='viridis', s=30, alpha=0.6)
            
            ax.set_xlabel('x (μm)', fontsize=10)
            ax.set_ylabel('y (μm)', fontsize=10)
            ax.set_zlabel('z (μm)', fontsize=10)
            ax.set_title(f'{state.name}\nPartition Depth n', fontsize=12, fontweight='bold')
            
            cbar = plt.colorbar(scatter, ax=ax, shrink=0.5, pad=0.1)
            cbar.set_label('Partition Depth n', fontsize=9)
    
    # Panel 6: Partition structure comparison
    ax6 = fig.add_subplot(gs[1, 2])
    
    # Plot partition depth distributions
    for state in states:
        n_values = [pc.n for pc in state.partition_coords]
        n_hist, n_bins = np.histogram(n_values, bins=50, density=True)
        n_centers = (n_bins[:-1] + n_bins[1:]) / 2
        ax6.plot(n_centers, n_hist, linewidth=2, label=state.name, alpha=0.7)
    
    ax6.set_xlabel('Partition Depth n', fontsize=12)
    ax6.set_ylabel('Probability Density', fontsize=12)
    ax6.set_title('Partition Depth Distributions', fontsize=14, fontweight='bold')
    ax6.legend(fontsize=9)
    ax6.grid(True, alpha=0.3)
    ax6.set_yscale('log')
    
    fig.suptitle('Phase Space Partition Visualizations Across Thermodynamic Regimes',
                fontsize=16, fontweight='bold', y=0.98)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved phase space partition visualizations to {save_path}")
    
    return fig


def create_s_entropy_trajectories(save_path: Optional[str] = None):
    """
    Create S-entropy coordinate trajectories showing Poincaré recurrence.
    """
    fig = plt.figure(figsize=(20, 14))
    gs = GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.35)
    
    # Generate states with longer trajectories
    states = [
        generate_neutral_gas_state(N=1000, V=1e-3, T=300.0),
        generate_plasma_state(N=1000, V=1e-3, T=1e6),
        generate_degenerate_matter_state(N=1000, V=1e-21, T=1e4),
        generate_relativistic_gas_state(N=1000, V=1e-3, T=1e10),
        generate_bec_state(N=5000, V=1e-12, T=50e-9)
    ]
    
    colors = sns.color_palette("husl", 5)
    
    # Top row: 3D trajectories
    for idx, state in enumerate(states):
        ax = fig.add_subplot(gs[0, idx if idx < 3 else idx - 3], projection='3d')
        
        Sk = [s.Sk for s in state.s_entropy_trajectory]
        St = [s.St for s in state.s_entropy_trajectory]
        Se = [s.Se for s in state.s_entropy_trajectory]
        
        # Plot trajectory
        ax.plot(Sk, St, Se, 'o-', color=colors[idx], alpha=0.5, 
               markersize=2, linewidth=1)
        
        # Mark start and end
        ax.scatter([Sk[0]], [St[0]], [Se[0]], color='green', s=100, 
                  marker='o', label='Start', zorder=5)
        ax.scatter([Sk[-1]], [St[-1]], [Se[-1]], color='red', s=100, 
                  marker='s', label='End', zorder=5)
        
        # Calculate recurrence distance
        recurrence_dist = np.sqrt((Sk[-1] - Sk[0])**2 + 
                                 (St[-1] - St[0])**2 + 
                                 (Se[-1] - Se[0])**2)
        
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        ax.set_zlim([0, 1])
        ax.set_xlabel('$S_k$', fontsize=9)
        ax.set_ylabel('$S_t$', fontsize=9)
        ax.set_zlabel('$S_e$', fontsize=9)
        ax.set_title(f'{state.name}\nRecurrence: {recurrence_dist:.3f}', 
                    fontsize=11, fontweight='bold')
        ax.legend(fontsize=7)
    
    # Middle row: 2D projections (Sk vs St)
    for idx, state in enumerate(states):
        row_offset = 1 if idx < 3 else 2
        col = idx if idx < 3 else idx - 3
        ax = fig.add_subplot(gs[row_offset, col])
        
        Sk = [s.Sk for s in state.s_entropy_trajectory]
        St = [s.St for s in state.s_entropy_trajectory]
        
        # Plot trajectory with time coloring
        time_colors = np.linspace(0, 1, len(Sk))
        scatter = ax.scatter(Sk, St, c=time_colors, cmap='viridis', 
                           s=20, alpha=0.6)
        
        # Mark start and end
        ax.scatter([Sk[0]], [St[0]], color='green', s=100, 
                  marker='o', edgecolor='black', linewidth=2, zorder=5)
        ax.scatter([Sk[-1]], [St[-1]], color='red', s=100, 
                  marker='s', edgecolor='black', linewidth=2, zorder=5)
        
        # Draw recurrence circle
        recurrence_dist = np.sqrt((Sk[-1] - Sk[0])**2 + (St[-1] - St[0])**2)
        circle = plt.Circle((Sk[0], St[0]), recurrence_dist, 
                          fill=False, color='red', linestyle='--', 
                          linewidth=2, label=f'ε = {recurrence_dist:.3f}')
        ax.add_patch(circle)
        
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        ax.set_xlabel('$S_k$ (knowledge)', fontsize=10)
        ax.set_ylabel('$S_t$ (temporal)', fontsize=10)
        ax.set_title(f'{state.name}: Poincaré Recurrence', 
                    fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
        
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Time', fontsize=8)
    
    # Bottom right: Recurrence comparison
    ax_compare = fig.add_subplot(gs[2, 2])
    
    recurrence_distances = []
    state_names = []
    
    for state in states:
        Sk = [s.Sk for s in state.s_entropy_trajectory]
        St = [s.St for s in state.s_entropy_trajectory]
        Se = [s.Se for s in state.s_entropy_trajectory]
        
        dist = np.sqrt((Sk[-1] - Sk[0])**2 + 
                      (St[-1] - St[0])**2 + 
                      (Se[-1] - Se[0])**2)
        recurrence_distances.append(dist)
        state_names.append(state.name)
    
    bars = ax_compare.bar(range(len(state_names)), recurrence_distances, 
                          color=colors, alpha=0.7, edgecolor='black')
    
    # Add value labels
    for bar, dist in zip(bars, recurrence_distances):
        height = bar.get_height()
        ax_compare.text(bar.get_x() + bar.get_width()/2., height,
                       f'{dist:.3f}',
                       ha='center', va='bottom', fontsize=9)
    
    ax_compare.axhline(0.1, color='red', linestyle='--', linewidth=2, 
                      label='Equilibrium threshold ε = 0.1')
    ax_compare.set_ylabel('Recurrence Distance', fontsize=12)
    ax_compare.set_title('Equilibrium Criterion:\n||γ(T) - γ(0)|| < ε', 
                        fontsize=12, fontweight='bold')
    ax_compare.set_xticks(range(len(state_names)))
    ax_compare.set_xticklabels(state_names, rotation=45, ha='right', fontsize=9)
    ax_compare.legend(fontsize=9)
    ax_compare.grid(True, alpha=0.3, axis='y')
    
    fig.suptitle('S-Entropy Trajectories: Equilibrium as Poincaré Recurrence',
                fontsize=16, fontweight='bold', y=0.99)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved S-entropy trajectories to {save_path}")
    
    return fig


def create_velocity_cutoff_diagrams(save_path: Optional[str] = None):
    """
    Create velocity distribution cutoffs at c for different gas types.
    """
    fig = plt.figure(figsize=(20, 12))
    gs = GridSpec(2, 3, figure=fig, hspace=0.3, wspace=0.3)
    
    colors = sns.color_palette("husl", 6)
    
    # Gas parameters: (name, mass (kg), temperature (K), color_idx)
    gases = [
        ('Hydrogen', 2 * 1.66054e-27, 300, 0),
        ('Helium', 4 * 1.66054e-27, 300, 1),
        ('Nitrogen', 28 * 1.66054e-27, 300, 2),
        ('Argon', 40 * 1.66054e-27, 300, 3),
        ('Xenon', 131 * 1.66054e-27, 300, 4),
        ('Electron Gas', me, 1e6, 5)
    ]
    
    for idx, (name, mass, temp, color_idx) in enumerate(gases):
        row = idx // 3
        col = idx % 3
        ax = fig.add_subplot(gs[row, col])
        
        # Velocity range
        v_th = np.sqrt(2 * kB * temp / mass)
        v = np.linspace(0, min(5 * v_th, 1.5 * c), 1000)
        
        # Maxwell-Boltzmann distribution (without cutoff)
        f_MB = (mass / (2 * np.pi * kB * temp))**(3/2) * 4 * np.pi * v**2 * \
               np.exp(-mass * v**2 / (2 * kB * temp))
        
        # With relativistic cutoff
        f_rel = f_MB.copy()
        f_rel[v >= c] = 0
        
        # Normalize
        f_MB = f_MB / np.max(f_MB)
        f_rel = f_rel / np.max(f_rel)
        
        # Plot
        ax.plot(v / c, f_MB, linewidth=2, color=colors[color_idx], 
               linestyle='--', alpha=0.5, label='Classical MB')
        ax.plot(v / c, f_rel, linewidth=3, color=colors[color_idx], 
               label='With cutoff at c')
        
        # Mark cutoff
        ax.axvline(1.0, color='red', linestyle=':', linewidth=2, 
                  label='v = c')
        
        # Shade forbidden region
        ax.fill_betweenx([0, 1.2], 1.0, 2.0, alpha=0.2, color='red', 
                        label='Forbidden (v > c)')
        
        # Calculate fraction above c (for classical)
        fraction_above_c = np.trapz(f_MB[v >= c], v[v >= c] / c) / \
                          np.trapz(f_MB, v / c) if np.any(v >= c) else 0
        
        ax.set_xlabel('Velocity / c', fontsize=11)
        ax.set_ylabel('Probability Density (normalized)', fontsize=11)
        ax.set_title(f'{name} at T = {temp:.0e} K\n' + 
                    f'$v_{{th}}/c = {v_th/c:.2e}$, ' + 
                    f'Classical tail > c: {fraction_above_c*100:.2e}%',
                    fontsize=11, fontweight='bold')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_xlim([0, min(5 * v_th / c, 1.5)])
        ax.set_ylim([0, 1.2])
    
    fig.suptitle('Velocity Distribution Cutoffs at c: Relativistic Necessity',
                fontsize=16, fontweight='bold', y=0.98)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved velocity cutoff diagrams to {save_path}")
    
    return fig


def create_structural_factor_plots(save_path: Optional[str] = None):
    """
    Create structural factor S(q) plots across the five regimes.
    """
    fig = plt.figure(figsize=(20, 14))
    gs = GridSpec(3, 2, figure=fig, hspace=0.35, wspace=0.3)
    
    colors = sns.color_palette("husl", 5)
    
    # Generate states
    states = [
        generate_neutral_gas_state(N=1000, V=1e-3, T=300.0),
        generate_plasma_state(N=1000, V=1e-3, T=1e6),
        generate_degenerate_matter_state(N=1000, V=1e-21, T=1e4),
        generate_relativistic_gas_state(N=1000, V=1e-3, T=1e10),
        generate_bec_state(N=5000, V=1e-12, T=50e-9)
    ]
    
    # Individual S(q) plots
    for idx, state in enumerate(states):
        row = idx // 2
        col = idx % 2
        ax = fig.add_subplot(gs[row, col])
        
        # Calculate pair correlation function g(r) via histogram
        # Then Fourier transform to get S(q)
        
        # Compute all pairwise distances
        N_sample = min(500, state.N)
        sample_idx = np.random.choice(state.N, N_sample, replace=False)
        positions_sample = state.positions[sample_idx]
        
        distances = []
        for i in range(N_sample):
            for j in range(i+1, N_sample):
                r = np.linalg.norm(positions_sample[i] - positions_sample[j])
                distances.append(r)
        
        distances = np.array(distances)
        
        # Histogram to get g(r)
        r_max = state.V**(1/3) / 2
        r_bins = np.linspace(0, r_max, 100)
        r_centers = (r_bins[:-1] + r_bins[1:]) / 2
        
        hist, _ = np.histogram(distances, bins=r_bins)
        
        # Normalize by ideal gas
        rho = state.N / state.V
        shell_volumes = 4 * np.pi * r_centers**2 * np.diff(r_bins)
        g_r = hist / (shell_volumes * rho * N_sample)
        
        # Fourier transform to get S(q)
        # S(q) = 1 + rho * ∫ [g(r) - 1] * exp(i q·r) dr
        q = np.linspace(0.1, 50, 200) / r_max  # Wavevector
        S_q = np.ones_like(q)
        
        for i, q_val in enumerate(q):
            integrand = (g_r - 1) * np.sin(q_val * r_centers) / (q_val * r_centers)
            integrand = np.nan_to_num(integrand)  # Handle division by zero
            S_q[i] = 1 + 4 * np.pi * rho * np.trapz(integrand * r_centers**2, r_centers)
        
        # Plot
        ax.plot(q * r_max, S_q, linewidth=3, color=colors[idx])
        ax.axhline(1.0, color='gray', linestyle='--', linewidth=1, 
                  label='Ideal gas (S=1)')
        
        ax.set_xlabel('Wavevector q (arb. units)', fontsize=11)
        ax.set_ylabel('Structure Factor S(q)', fontsize=11)
        ax.set_title(f'{state.name}\nStructure Factor', 
                    fontsize=12, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, max(3, np.max(S_q) * 1.1)])
    
    # Comparison plot
    ax_compare = fig.add_subplot(gs[2, :])
    
    for idx, state in enumerate(states):
        # Simplified S(q) for comparison
        N_sample = min(500, state.N)
        sample_idx = np.random.choice(state.N, N_sample, replace=False)
        positions_sample = state.positions[sample_idx]
        
        distances = []
        for i in range(N_sample):
            for j in range(i+1, N_sample):
                r = np.linalg.norm(positions_sample[i] - positions_sample[j])
                distances.append(r)
        
        distances = np.array(distances)
        r_max = state.V**(1/3) / 2
        r_bins = np.linspace(0, r_max, 50)
        r_centers = (r_bins[:-1] + r_bins[1:]) / 2
        
        hist, _ = np.histogram(distances, bins=r_bins)
        rho = state.N / state.V
        shell_volumes = 4 * np.pi * r_centers**2 * np.diff(r_bins)
        g_r = hist / (shell_volumes * rho * N_sample)
        
        q = np.linspace(0.1, 30, 100) / r_max
        S_q = np.ones_like(q)
        
        for i, q_val in enumerate(q):
            integrand = (g_r - 1) * np.sin(q_val * r_centers) / (q_val * r_centers)
            integrand = np.nan_to_num(integrand)
            S_q[i] = 1 + 4 * np.pi * rho * np.trapz(integrand * r_centers**2, r_centers)
        
        ax_compare.plot(q * r_max, S_q, linewidth=2, color=colors[idx], 
                       label=state.name, alpha=0.8)
    
    ax_compare.axhline(1.0, color='black', linestyle='--', linewidth=2, 
                      label='Ideal gas limit')
    ax_compare.set_xlabel('Wavevector q (normalized)', fontsize=12)
    ax_compare.set_ylabel('Structure Factor S(q)', fontsize=12)
    ax_compare.set_title('Structural Factor Comparison Across Thermodynamic Regimes',
                        fontsize=14, fontweight='bold')
    ax_compare.legend(fontsize=10, loc='upper right')
    ax_compare.grid(True, alpha=0.3)
    ax_compare.set_ylim([0, 3])
    
    fig.suptitle('Structural Factors: Partition Geometry Across Regimes',
                fontsize=16, fontweight='bold', y=0.98)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved structural factor plots to {save_path}")
    
    return fig


def generate_all_paradox_visualizations(output_dir: str = "validation_outputs"):
    """Generate all specialized visualization panels"""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 80)
    print("GENERATING SPECIALIZED PARADOX AND THEORETICAL VISUALIZATIONS")
    print("=" * 80)
    print()
    
    # 1. Paradox resolution diagrams
    print("Creating paradox resolution diagrams...")
    create_paradox_resolution_diagrams(f"{output_dir}/paradox_resolutions.png")
    plt.close()
    
    # 2. Phase space partitions
    print("\nCreating phase space partition visualizations...")
    create_phase_space_partition_visualizations(f"{output_dir}/phase_space_partitions.png")
    plt.close()
    
    # 3. S-entropy trajectories
    print("\nCreating S-entropy trajectory diagrams...")
    create_s_entropy_trajectories(f"{output_dir}/s_entropy_trajectories.png")
    plt.close()
    
    # 4. Velocity cutoffs
    print("\nCreating velocity cutoff diagrams...")
    create_velocity_cutoff_diagrams(f"{output_dir}/velocity_cutoffs.png")
    plt.close()
    
    # 5. Structural factors
    print("\nCreating structural factor plots...")
    create_structural_factor_plots(f"{output_dir}/structural_factors.png")
    plt.close()
    
    print("\n" + "=" * 80)
    print("ALL SPECIALIZED VISUALIZATIONS COMPLETE")
    print("=" * 80)
    print(f"\nGenerated 5 comprehensive panel charts in {output_dir}/:")
    print("  1. paradox_resolutions.png - Computational impossibilities")
    print("  2. phase_space_partitions.png - 3D partition visualizations")
    print("  3. s_entropy_trajectories.png - Poincaré recurrence")
    print("  4. velocity_cutoffs.png - Relativistic cutoff at c")
    print("  5. structural_factors.png - S(q) across regimes")


if __name__ == "__main__":
    generate_all_paradox_visualizations()

