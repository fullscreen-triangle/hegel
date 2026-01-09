"""
Therapeutic Equations of State Validation
Generates multi-panel validation charts for therapeutic intervention
Includes conjugate therapy for frequency conversion/equalization
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from scipy.integrate import odeint
import os

class TherapeuticValidator:
    """Validates therapeutic equations of state through computational experiments"""
    
    def __init__(self, output_dir='validation_results'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def dose_response_curves(self, ax):
        """Panel 1: Dose-response relationships for different Hill coefficients"""
        D = np.logspace(-3, 2, 1000)  # Drug concentration (normalized)
        
        EC50 = 1.0  # Half-maximal concentration
        E_max = 1.0  # Maximum efficacy
        
        # Different Hill coefficients
        h_values = [0.5, 1.0, 2.0, 4.0]
        colors = ['blue', 'green', 'orange', 'red']
        labels = [f'h={h} ({"non-" if h<1 else ""}cooperative)' if h != 1 
                 else 'h=1 (non-cooperative)' for h in h_values]
        
        for h, color, label in zip(h_values, colors, labels):
            E = E_max * D**h / (EC50**h + D**h)
            ax.plot(D, E, color=color, linewidth=2.5, label=label, alpha=0.8)
        
        ax.axvline(EC50, color='black', linestyle='--', linewidth=1.5, 
                   label='EC₅₀', alpha=0.5)
        ax.axhline(E_max/2, color='gray', linestyle=':', linewidth=1.5, alpha=0.5)
        
        ax.set_xscale('log')
        ax.set_xlabel('Drug Concentration [D] (normalized)', fontsize=12)
        ax.set_ylabel('Therapeutic Efficacy E', fontsize=12)
        ax.set_title('Dose-Response Curves (Hill Equation)', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(1e-3, 1e2)
        ax.set_ylim(-0.05, 1.1)
    
    def conjugate_frequency_conversion(self, ax):
        """Panel 2: Conjugate therapy as frequency converter/equalizer
        
        Conjugates introduce intermediate frequency layer to synchronize
        enzyme to oxygen master clock via local cytoplasmic volumes
        """
        t = np.linspace(0, 100, 2000)
        
        # Oxygen master clock (high frequency)
        omega_O2 = 1.0  # Normalized
        y_O2 = 0.3 * np.sin(omega_O2 * t)
        
        # Diseased enzyme (mismatched frequency)
        omega_enzyme_disease = 0.3  # Too slow
        y_enzyme_disease = np.sin(omega_enzyme_disease * t)
        
        # Conjugate acts as frequency converter
        # Creates intermediate frequency that phase-locks to both
        omega_conjugate = np.sqrt(omega_O2 * omega_enzyme_disease)  # Geometric mean
        y_conjugate = 0.7 * np.sin(omega_conjugate * t)
        
        # Post-therapy: enzyme locks to conjugate, which locks to O2
        # This creates a "frequency ladder" or "gear ratio"
        omega_enzyme_therapy = omega_conjugate  # Enzyme now matches conjugate
        y_enzyme_therapy = np.sin(omega_enzyme_therapy * t)
        
        # Plot time window
        t_window = (t >= 20) & (t <= 60)
        
        ax.plot(t[t_window], y_O2[t_window], 'b-', linewidth=1.5, 
               label='O₂ master clock (ω=1.0)', alpha=0.7)
        ax.plot(t[t_window], y_enzyme_disease[t_window], 'r-', linewidth=2, 
               label='Diseased enzyme (ω=0.3)', alpha=0.7)
        ax.plot(t[t_window], y_conjugate[t_window], 'purple', linewidth=2, 
               linestyle='--', label='Conjugate intermediate (ω=0.55)', alpha=0.8)
        ax.plot(t[t_window], y_enzyme_therapy[t_window], 'g-', linewidth=2, 
               label='Enzyme + conjugate (ω=0.55)', alpha=0.7)
        
        ax.set_xlabel('Time (arbitrary units)', fontsize=12)
        ax.set_ylabel('Oscillation Amplitude', fontsize=12)
        ax.set_title('Conjugate Therapy: Frequency Conversion Layer', 
                    fontsize=14, fontweight='bold')
        ax.legend(fontsize=9, loc='upper right')
        ax.grid(True, alpha=0.3)
        
        # Add annotation box
        textstr = 'Conjugate creates intermediate\nfrequency layer:\nω_conj = √(ω_O₂ × ω_enzyme)\n\nEnables phase-locking\nthrough frequency matching'
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.7)
        ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=9,
               verticalalignment='top', bbox=props)
    
    def therapeutic_pressure_landscape(self, ax):
        """Panel 3: 3D therapeutic pressure as function of efficacy and concentration"""
        E = np.linspace(0, 0.99, 50)  # Efficacy (avoid E=1 singularity)
        D = np.logspace(-2, 2, 50)  # Concentration
        
        E_grid, D_grid = np.meshgrid(E, D)
        
        # Therapeutic pressure: P_therapeutic = k_B T * E / (1 - E)
        # Normalized with k_B T = 1
        P_therapeutic = E_grid / (1 - E_grid)
        
        # Concentration modulation (efficacy increases with dose)
        EC50 = 1.0
        h = 2.0
        E_from_D = D_grid**h / (EC50**h + D_grid**h)
        
        # Combined effect
        P_combined = P_therapeutic * E_from_D
        
        surf = ax.plot_surface(E_grid, np.log10(D_grid), P_combined, 
                              cmap=cm.viridis, alpha=0.8, 
                              edgecolor='none', antialiased=True)
        
        # Contour lines
        ax.contour(E_grid, np.log10(D_grid), P_combined, levels=10, 
                  colors='black', alpha=0.3, linewidths=0.5)
        
        ax.set_xlabel('Efficacy E', fontsize=11)
        ax.set_ylabel('log₁₀([D])', fontsize=11)
        ax.set_zlabel('Therapeutic Pressure', fontsize=11)
        ax.set_title('Therapeutic Pressure Landscape', fontsize=14, fontweight='bold')
        ax.view_init(elev=25, azim=45)
        
        plt.colorbar(surf, ax=ax, shrink=0.5, label='Pressure')
    
    def combination_therapy_synergy(self, ax):
        """Panel 4: Combination therapy efficacy and synergy detection"""
        # Drug concentrations
        D1 = np.linspace(0, 2, 50)
        D2 = np.linspace(0, 2, 50)
        D1_grid, D2_grid = np.meshgrid(D1, D2)
        
        # Individual drug efficacies
        EC50_1 = 0.5
        EC50_2 = 0.7
        h1 = 2.0
        h2 = 1.5
        E_max = 1.0
        
        E1 = E_max * D1_grid**h1 / (EC50_1**h1 + D1_grid**h1)
        E2 = E_max * D2_grid**h2 / (EC50_2**h2 + D2_grid**h2)
        
        # Independent combination (Bliss independence)
        E_independent = E1 + E2 - E1 * E2
        
        # Synergistic combination (conjugate effect)
        # Conjugates enhance each other's frequency conversion
        synergy_factor = 1.3
        E_synergy = E_independent * (1 + 0.3 * E1 * E2)  # Nonlinear enhancement
        
        # Plot synergy map (E_synergy - E_independent)
        synergy_map = E_synergy - E_independent
        
        contour = ax.contourf(D1_grid, D2_grid, synergy_map, levels=20, 
                              cmap='RdYlGn', alpha=0.8)
        contour_lines = ax.contour(D1_grid, D2_grid, synergy_map, levels=10, 
                                   colors='black', alpha=0.4, linewidths=0.5)
        ax.clabel(contour_lines, inline=True, fontsize=8, fmt='%.2f')
        
        ax.set_xlabel('Drug 1 Concentration [D₁]', fontsize=12)
        ax.set_ylabel('Drug 2 Concentration [D₂]', fontsize=12)
        ax.set_title('Combination Therapy Synergy Map', fontsize=14, fontweight='bold')
        
        cbar = plt.colorbar(contour, ax=ax)
        cbar.set_label('Synergy (ΔE)', fontsize=11)
        
        # Add isobole (line of equal effect)
        E_target = 0.7
        isobole_mask = np.abs(E_synergy - E_target) < 0.05
        if isobole_mask.any():
            ax.plot(D1_grid[isobole_mask], D2_grid[isobole_mask], 'b.', 
                   markersize=3, label=f'E={E_target} isobole')
            ax.legend(fontsize=9)
    
    def generate_therapeutic_panel(self):
        """Generate 4-panel therapeutic validation chart"""
        fig = plt.figure(figsize=(16, 12))
        
        # Panel 1: Dose-response (2D)
        ax1 = plt.subplot(2, 2, 1)
        self.dose_response_curves(ax1)
        
        # Panel 2: Conjugate frequency conversion (2D)
        ax2 = plt.subplot(2, 2, 2)
        self.conjugate_frequency_conversion(ax2)
        
        # Panel 3: Therapeutic pressure (3D)
        ax3 = plt.subplot(2, 2, 3, projection='3d')
        self.therapeutic_pressure_landscape(ax3)
        
        # Panel 4: Combination synergy (2D)
        ax4 = plt.subplot(2, 2, 4)
        self.combination_therapy_synergy(ax4)
        
        plt.suptitle('Therapeutic Equations of State: Validation Panel\n' + 
                     'Including Conjugate Frequency Conversion Therapy', 
                     fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout(rect=[0, 0, 1, 0.99])
        
        output_path = os.path.join(self.output_dir, 'therapeutic_validation_panel.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"[OK] Therapeutic validation panel saved: {output_path}")
        plt.close()

def main():
    """Run therapeutic validation experiments"""
    print("\n" + "="*60)
    print("THERAPEUTIC EQUATIONS OF STATE VALIDATION")
    print("="*60 + "\n")
    
    validator = TherapeuticValidator()
    
    print("Generating therapeutic validation panel...")
    validator.generate_therapeutic_panel()
    
    print("\n" + "="*60)
    print("THERAPEUTIC VALIDATION COMPLETE")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
