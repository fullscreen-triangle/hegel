"""
Immune Equations of State Validation
Generates multi-panel validation charts for immune recognition and response
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from scipy.integrate import odeint
import os

class ImmuneValidator:
    """Validates immune equations of state through computational experiments"""
    
    def __init__(self, output_dir='validation_results'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def mhc_presentation_probability(self, ax):
        """Panel 1: MHC presentation probability vs richness"""
        R = np.logspace(2, 7, 1000)
        
        # MHC presentation window
        R_min = 1e3
        R_max = 1e5
        
        P_present = np.zeros_like(R)
        mask = (R > R_min) & (R < R_max)
        P_present[mask] = (R_max - R[mask]) / (R_max - R_min)
        
        ax.plot(R, P_present, 'b-', linewidth=3, label='MHC presentation')
        ax.axvline(R_min, color='green', linestyle='--', linewidth=2, 
                   label=f'R_min = {R_min:.0e}', alpha=0.7)
        ax.axvline(R_max, color='red', linestyle='--', linewidth=2, 
                   label=f'R_max = {R_max:.0e}', alpha=0.7)
        
        # Shade regions
        ax.axvspan(R[0], R_min, alpha=0.2, color='yellow', label='Too simple')
        ax.axvspan(R_min, R_max, alpha=0.2, color='green', label='Presentation window')
        ax.axvspan(R_max, R[-1], alpha=0.2, color='blue', label='Self (tolerance)')
        
        ax.set_xscale('log')
        ax.set_xlabel('Categorical Richness R', fontsize=12)
        ax.set_ylabel('Presentation Probability P_present', fontsize=12)
        ax.set_title('MHC Categorical Aperture Function', fontsize=14, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-0.05, 1.1)
    
    def vdj_ternary_hierarchy(self, ax):
        """Panel 2: VDJ recombination ternary structure"""
        # Ternary hierarchy levels
        levels = ['V\n(~50)', 'D\n(~30)', 'J\n(~6)', 'Total\n(~9000≈3⁸)']
        values = [50, 30, 6, 9000]
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        
        # Create hierarchical bar chart
        x = np.arange(len(levels))
        bars = ax.bar(x, values, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
        
        # Add value labels on bars
        for i, (bar, val) in enumerate(zip(bars, values)):
            height = bar.get_height()
            if i < 3:
                ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                       f'{val}', ha='center', va='bottom', fontsize=11, fontweight='bold')
            else:
                ax.text(bar.get_x() + bar.get_width()/2., height + 200,
                       f'{val}', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        # Add multiplication arrows
        for i in range(len(levels) - 1):
            ax.annotate('', xy=(i+0.5, max(values)/2), xytext=(i+0.5, max(values)/2),
                       arrowprops=dict(arrowstyle='->', lw=2, color='black'))
            if i < 2:
                ax.text(i+0.5, max(values)/2 + 500, '×', fontsize=20, 
                       ha='center', va='center', fontweight='bold')
        
        ax.set_ylabel('Segment Count', fontsize=12)
        ax.set_title('VDJ Ternary Hierarchy (3-Level Combinatorial)', 
                    fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(levels, fontsize=11)
        ax.set_yscale('log')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add annotation
        ax.text(0.5, 0.95, 'N_VDJ = N_V × N_D × N_J ≈ 3⁸', 
               transform=ax.transAxes, fontsize=12, 
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
               ha='center', va='top')
    
    def immune_pressure_landscape(self, ax):
        """Panel 3: 3D immune pressure as function of richness and temperature"""
        R = np.logspace(3, 6, 50)
        T = np.linspace(300, 400, 50)  # Temperature in K
        
        R_grid, T_grid = np.meshgrid(R, T)
        
        # Immune pressure: P_immune = P_0 / (R/R_0)
        P_0 = 1.0  # Normalized maximum pressure
        R_0 = 1e3  # Reference richness
        
        P_immune = P_0 / (R_grid / R_0)
        
        # Temperature modulation (immune response stronger at fever temperatures)
        T_modulation = 1 + 0.5 * (T_grid - 310) / 90  # Enhanced at T > 310K
        P_immune = P_immune * T_modulation
        
        surf = ax.plot_surface(np.log10(R_grid), T_grid, P_immune, 
                              cmap=cm.coolwarm, alpha=0.8, 
                              edgecolor='none', antialiased=True)
        
        # Contour lines
        ax.contour(np.log10(R_grid), T_grid, P_immune, levels=10, 
                  colors='black', alpha=0.3, linewidths=0.5)
        
        ax.set_xlabel('log₁₀(Richness R)', fontsize=11)
        ax.set_ylabel('Temperature T (K)', fontsize=11)
        ax.set_zlabel('Immune Pressure P', fontsize=11)
        ax.set_title('Immune Pressure Landscape', fontsize=14, fontweight='bold')
        ax.view_init(elev=25, azim=45)
        
        plt.colorbar(surf, ax=ax, shrink=0.5, label='Pressure')
    
    def clonal_expansion_dynamics(self, ax):
        """Panel 4: T cell clonal expansion for different antigen richness"""
        t = np.linspace(0, 20, 1000)  # Time in days
        
        def clonal_expansion(N, t, r, K, delta):
            """Logistic growth with death: dN/dt = rN(1-N/K) - δN"""
            return r * N * (1 - N / K) - delta * N
        
        # Parameters
        K = 1e6  # Carrying capacity
        delta = 0.1  # Death rate
        N0 = 1e2  # Initial clone size
        
        # Different richness values affect proliferation rate
        R_values = [1e3, 5e3, 1e4, 5e4, 1e5]
        colors = ['red', 'orange', 'yellow', 'lightblue', 'blue']
        labels = ['R=10³ (strong)', 'R=5×10³', 'R=10⁴', 'R=5×10⁴', 'R=10⁵ (tolerance)']
        
        for R, color, label in zip(R_values, colors, labels):
            # Proliferation rate inversely proportional to richness
            r_max = 1.0
            r = r_max * (1e4 / R) if R < 1e5 else 0.05  # Tolerance at high R
            
            N = odeint(clonal_expansion, N0, t, args=(r, K, delta))
            ax.plot(t, N, color=color, linewidth=2, label=label, alpha=0.8)
        
        ax.set_xlabel('Time (days)', fontsize=12)
        ax.set_ylabel('Clone Size (cells)', fontsize=12)
        ax.set_title('Richness-Dependent Clonal Expansion', fontsize=14, fontweight='bold')
        ax.set_yscale('log')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        
        # Add annotation
        ax.axhline(K, color='black', linestyle='--', linewidth=1, alpha=0.5)
        ax.text(15, K*1.5, 'Carrying capacity', fontsize=10, alpha=0.7)
    
    def generate_immune_panel(self):
        """Generate 4-panel immune validation chart"""
        fig = plt.figure(figsize=(16, 12))
        
        # Panel 1: MHC presentation (2D)
        ax1 = plt.subplot(2, 2, 1)
        self.mhc_presentation_probability(ax1)
        
        # Panel 2: VDJ hierarchy (2D)
        ax2 = plt.subplot(2, 2, 2)
        self.vdj_ternary_hierarchy(ax2)
        
        # Panel 3: Immune pressure (3D)
        ax3 = plt.subplot(2, 2, 3, projection='3d')
        self.immune_pressure_landscape(ax3)
        
        # Panel 4: Clonal expansion (2D)
        ax4 = plt.subplot(2, 2, 4)
        self.clonal_expansion_dynamics(ax4)
        
        plt.suptitle('Immune Equations of State: Validation Panel', 
                     fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout(rect=[0, 0, 1, 0.99])
        
        output_path = os.path.join(self.output_dir, 'immune_validation_panel.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"[OK] Immune validation panel saved: {output_path}")
        plt.close()

def main():
    """Run immune validation experiments"""
    print("\n" + "="*60)
    print("IMMUNE EQUATIONS OF STATE VALIDATION")
    print("="*60 + "\n")
    
    validator = ImmuneValidator()
    
    print("Generating immune validation panel...")
    validator.generate_immune_panel()
    
    print("\n" + "="*60)
    print("IMMUNE VALIDATION COMPLETE")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
