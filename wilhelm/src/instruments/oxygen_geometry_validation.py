"""
Oxygen Gas Model and Geometric Configuration Validation
Generates multi-panel validation charts for O2 master clock and cytoplasmic geometry
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import os

class OxygenGeometryValidator:
    """Validates oxygen gas model and geometric configurations"""
    
    def __init__(self, output_dir='validation_results'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def oxygen_rotational_spectrum(self, ax):
        """Panel 1: O2 rotational energy levels and frequency spectrum"""
        # Rotational quantum numbers
        j = np.arange(0, 20)
        
        # Rotational constant for O2 (cm^-1)
        B_e = 1.4457  # cm^-1
        
        # Energy levels: E_j = B_e * j(j+1)
        E_j = B_e * j * (j + 1)
        
        # Transition frequencies: ΔE = E_{j+1} - E_j = 2B_e(j+1)
        omega_j = 2 * B_e * (j + 1)
        
        # Plot energy levels
        for i, (j_val, E_val) in enumerate(zip(j, E_j)):
            ax.hlines(E_val, j_val - 0.3, j_val + 0.3, colors='blue', linewidth=2)
            if i < len(j) - 1:
                # Draw transitions
                ax.arrow(j_val + 0.15, E_val, 0, E_j[i+1] - E_val - 0.5, 
                        head_width=0.2, head_length=0.3, fc='red', ec='red', 
                        alpha=0.5, linewidth=1)
                # Label frequency
                if i < 10:
                    ax.text(j_val + 0.5, (E_val + E_j[i+1]) / 2, 
                           f'{omega_j[i]:.1f}', fontsize=8, color='red')
        
        ax.set_xlabel('Rotational Quantum Number j', fontsize=12)
        ax.set_ylabel('Energy E_j (cm⁻¹)', fontsize=12)
        ax.set_title('O₂ Rotational Energy Spectrum', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Add annotation
        textstr = f'E_j = B_e × j(j+1)\nB_e = {B_e} cm⁻¹\nω ≈ 10¹³ Hz'
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.7)
        ax.text(0.7, 0.95, textstr, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', bbox=props)
    
    def oxygen_harmonic_partitioning(self, ax):
        """Panel 2: Frequency partitioning of O2 master clock"""
        # Fundamental frequency (normalized)
        omega_O2 = 1.0
        
        # Number of harmonics
        N = 16
        n = np.arange(1, N+1)
        omega_n = (n / N) * omega_O2
        
        # Cellular processes with natural frequencies
        num_processes = 50
        omega_processes = np.random.uniform(0.1, 1.0, num_processes)
        
        # Phase-locking bandwidth
        Delta_omega_lock = 0.05
        
        # Color code by which harmonic they lock to
        colors = []
        locked_harmonics = []
        for omega_p in omega_processes:
            # Find nearest harmonic
            distances = np.abs(omega_n - omega_p)
            nearest_idx = np.argmin(distances)
            if distances[nearest_idx] < Delta_omega_lock:
                colors.append(plt.cm.tab20(nearest_idx % 20))
                locked_harmonics.append(nearest_idx)
            else:
                colors.append('gray')
                locked_harmonics.append(-1)
        
        # Plot harmonics as vertical lines
        for i, omega in enumerate(omega_n):
            ax.axvline(omega, color='blue', alpha=0.3, linewidth=2, linestyle='--')
            ax.text(omega, 1.05, f'{i+1}', ha='center', fontsize=8, color='blue')
        
        # Plot cellular processes
        for omega_p, color, locked in zip(omega_processes, colors, locked_harmonics):
            if locked >= 0:
                ax.scatter(omega_p, 0.5, c=[color], s=100, alpha=0.8, 
                          edgecolors='black', linewidths=1, marker='o')
            else:
                ax.scatter(omega_p, 0.5, c=[color], s=100, alpha=0.5, 
                          edgecolors='red', linewidths=2, marker='x')
        
        # Shade locking bandwidth around first few harmonics
        for omega in omega_n[:5]:
            ax.axvspan(omega - Delta_omega_lock, omega + Delta_omega_lock, 
                      alpha=0.1, color='green')
        
        ax.set_xlim(0, 1.1)
        ax.set_ylim(0, 1.2)
        ax.set_xlabel('Frequency ω (normalized to ω_O₂)', fontsize=12)
        ax.set_title('O₂ Master Clock Frequency Partitioning', 
                    fontsize=14, fontweight='bold')
        ax.set_yticks([])
        
        # Legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color='blue', linestyle='--', linewidth=2, 
                   label='O₂ harmonics (ω_n = n/N × ω_O₂)'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='green', 
                   markersize=10, label='Phase-locked process', markeredgecolor='black'),
            Line2D([0], [0], marker='x', color='red', markersize=10, 
                   label='Unlocked process', linestyle='None', markeredgewidth=2)
        ]
        ax.legend(handles=legend_elements, loc='upper left', fontsize=9)
    
    def cytoplasmic_volume_geometry(self, ax):
        """Panel 3: 3D geometric configuration of cytoplasmic volumes with O2 distribution"""
        # Create cytoplasmic volume (sphere)
        u = np.linspace(0, 2 * np.pi, 30)
        v = np.linspace(0, np.pi, 20)
        x_cell = 10 * np.outer(np.cos(u), np.sin(v))
        y_cell = 10 * np.outer(np.sin(u), np.sin(v))
        z_cell = 10 * np.outer(np.ones(np.size(u)), np.cos(v))
        
        # Plot cell membrane
        ax.plot_surface(x_cell, y_cell, z_cell, alpha=0.1, color='blue', 
                       edgecolor='blue', linewidth=0.3)
        
        # O2 molecules distributed throughout (paramagnetic centers)
        num_O2 = 30
        O2_positions = np.random.randn(num_O2, 3) * 7  # Inside cell
        
        for pos in O2_positions:
            ax.scatter(*pos, c='red', s=100, alpha=0.8, marker='o', 
                      edgecolors='darkred', linewidths=1)
        
        # Localized cytoplasmic volumes (where conjugates act)
        num_volumes = 5
        volume_centers = np.random.randn(num_volumes, 3) * 5
        volume_radius = 2
        
        for i, center in enumerate(volume_centers):
            # Draw localized volume as wireframe sphere
            u_v = np.linspace(0, 2 * np.pi, 15)
            v_v = np.linspace(0, np.pi, 10)
            x_v = volume_radius * np.outer(np.cos(u_v), np.sin(v_v)) + center[0]
            y_v = volume_radius * np.outer(np.sin(u_v), np.sin(v_v)) + center[1]
            z_v = volume_radius * np.outer(np.ones(np.size(u_v)), np.cos(v_v)) + center[2]
            
            ax.plot_surface(x_v, y_v, z_v, alpha=0.3, color='green', 
                           edgecolor='darkgreen', linewidth=0.5)
            
            # Enzyme in center of volume
            ax.scatter(*center, c='purple', s=200, alpha=1.0, marker='*', 
                      edgecolors='black', linewidths=1)
        
        ax.set_xlabel('X (nm)', fontsize=10)
        ax.set_ylabel('Y (nm)', fontsize=10)
        ax.set_zlabel('Z (nm)', fontsize=10)
        ax.set_title('Cytoplasmic Geometry: O₂ Distribution & Localized Volumes', 
                    fontsize=14, fontweight='bold')
        ax.view_init(elev=20, azim=45)
        
        # Legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='red', 
                   markersize=8, label='O₂ molecules', markeredgecolor='darkred'),
            Line2D([0], [0], marker='*', color='w', markerfacecolor='purple', 
                   markersize=12, label='Enzyme', markeredgecolor='black'),
            Line2D([0], [0], color='green', linewidth=3, alpha=0.5, 
                   label='Localized volume (conjugate action)')
        ]
        ax.legend(handles=legend_elements, loc='upper left', fontsize=9)
    
    def conjugate_frequency_ladder(self, ax):
        """Panel 4: Frequency ladder/gear ratio created by conjugates"""
        # Frequency levels
        levels = ['O₂ Master\nClock', 'Conjugate\nIntermediate', 'Enzyme\n(diseased)', 
                 'Enzyme\n(+ conjugate)']
        frequencies = [1.0, 0.55, 0.3, 0.55]  # Normalized
        colors = ['blue', 'purple', 'red', 'green']
        
        # Create ladder diagram
        y_positions = np.arange(len(levels))
        
        for i, (level, freq, color) in enumerate(zip(levels, frequencies, colors)):
            # Draw frequency bar
            rect = FancyBboxPatch((0, y_positions[i] - 0.3), freq, 0.6, 
                                 boxstyle="round,pad=0.05", 
                                 edgecolor=color, facecolor=color, 
                                 alpha=0.6, linewidth=2)
            ax.add_patch(rect)
            
            # Label
            ax.text(-0.05, y_positions[i], level, ha='right', va='center', 
                   fontsize=11, fontweight='bold')
            ax.text(freq + 0.02, y_positions[i], f'ω = {freq:.2f}', 
                   ha='left', va='center', fontsize=10)
        
        # Draw connections
        # O2 → Conjugate
        ax.annotate('', xy=(0.55, y_positions[1]), xytext=(1.0, y_positions[0]),
                   arrowprops=dict(arrowstyle='->', lw=2, color='black', alpha=0.5))
        ax.text(0.75, (y_positions[0] + y_positions[1]) / 2 + 0.1, 
               'Phase-lock', fontsize=9, ha='center', style='italic')
        
        # Conjugate → Enzyme
        ax.annotate('', xy=(0.55, y_positions[3]), xytext=(0.55, y_positions[1]),
                   arrowprops=dict(arrowstyle='->', lw=2, color='black', alpha=0.5))
        ax.text(0.65, (y_positions[1] + y_positions[3]) / 2, 
               'Frequency\nconversion', fontsize=9, ha='left', style='italic')
        
        # Show mismatch
        ax.plot([0.3, 0.55], [y_positions[2], y_positions[2]], 'r--', linewidth=2, alpha=0.5)
        ax.plot([0.55, 0.55], [y_positions[2], y_positions[3]], 'g--', linewidth=2, alpha=0.5)
        ax.text(0.425, y_positions[2] - 0.15, 'Δω (deficit)', fontsize=9, 
               ha='center', color='red', style='italic')
        
        ax.set_xlim(-0.3, 1.2)
        ax.set_ylim(-0.5, len(levels) - 0.5)
        ax.set_xlabel('Frequency ω (normalized)', fontsize=12)
        ax.set_title('Conjugate Therapy: Frequency Ladder Mechanism', 
                    fontsize=14, fontweight='bold')
        ax.set_yticks([])
        ax.grid(True, alpha=0.3, axis='x')
        
        # Add annotation box
        textstr = ('Conjugate creates intermediate\nfrequency layer enabling\nenzyme synchronization to O₂\n\n'
                  'ω_conjugate = √(ω_O₂ × ω_enzyme)\n\n'
                  'Acts as "frequency gear ratio"\nor "impedance matcher"')
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.7)
        ax.text(0.98, 0.5, textstr, transform=ax.transAxes, fontsize=9,
               verticalalignment='center', horizontalalignment='right', bbox=props)
    
    def generate_oxygen_geometry_panel(self):
        """Generate 4-panel oxygen geometry validation chart"""
        fig = plt.figure(figsize=(16, 12))
        
        # Panel 1: O2 rotational spectrum (2D)
        ax1 = plt.subplot(2, 2, 1)
        self.oxygen_rotational_spectrum(ax1)
        
        # Panel 2: Frequency partitioning (2D)
        ax2 = plt.subplot(2, 2, 2)
        self.oxygen_harmonic_partitioning(ax2)
        
        # Panel 3: Cytoplasmic geometry (3D)
        ax3 = plt.subplot(2, 2, 3, projection='3d')
        self.cytoplasmic_volume_geometry(ax3)
        
        # Panel 4: Frequency ladder (2D)
        ax4 = plt.subplot(2, 2, 4)
        self.conjugate_frequency_ladder(ax4)
        
        plt.suptitle('Oxygen Gas Model & Geometric Configuration: Validation Panel\n' + 
                     'Master Clock, Frequency Partitioning, and Conjugate Therapy', 
                     fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout(rect=[0, 0, 1, 0.99])
        
        output_path = os.path.join(self.output_dir, 'oxygen_geometry_validation_panel.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"[OK] Oxygen geometry validation panel saved: {output_path}")
        plt.close()

def main():
    """Run oxygen geometry validation experiments"""
    print("\n" + "="*60)
    print("OXYGEN GAS MODEL & GEOMETRY VALIDATION")
    print("="*60 + "\n")
    
    validator = OxygenGeometryValidator()
    
    print("Generating oxygen geometry validation panel...")
    validator.generate_oxygen_geometry_panel()
    
    print("\n" + "="*60)
    print("OXYGEN GEOMETRY VALIDATION COMPLETE")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
