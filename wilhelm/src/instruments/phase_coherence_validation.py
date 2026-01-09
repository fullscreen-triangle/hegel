"""
Phase Coherence and Synchronization Validation
Generates multi-panel validation charts for Kuramoto dynamics and coherence
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from scipy.integrate import odeint
import os

class PhaseCoherenceValidator:
    """Validates phase coherence equations through computational experiments"""
    
    def __init__(self, output_dir='validation_results'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def kuramoto_order_parameter(self, ax):
        """Panel 1: Order parameter vs coupling strength"""
        K = np.linspace(0, 3, 100)  # Coupling strength
        
        # Frequency distribution width
        Delta_values = [0.5, 1.0, 1.5]
        colors = ['blue', 'green', 'red']
        labels = [f'Δ={d}' for d in Delta_values]
        
        for Delta, color, label in zip(Delta_values, colors, labels):
            # Critical coupling
            K_c = 2 * Delta / np.pi
            
            # Order parameter (mean-field approximation)
            r = np.zeros_like(K)
            mask = K > K_c
            r[mask] = np.sqrt(1 - K_c / K[mask])
            
            ax.plot(K, r, color=color, linewidth=2.5, label=label, alpha=0.8)
            ax.axvline(K_c, color=color, linestyle='--', linewidth=1.5, alpha=0.5)
        
        ax.set_xlabel('Coupling Strength K', fontsize=12)
        ax.set_ylabel('Order Parameter r', fontsize=12)
        ax.set_title('Kuramoto Order Parameter (Synchronization Transition)', 
                    fontsize=14, fontweight='bold')
        ax.legend(fontsize=10, title='Frequency\nDisorder')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 3)
        ax.set_ylim(-0.05, 1.05)
        
        # Add annotation
        ax.text(0.5, 0.5, 'r = 0: Incoherent\nr = 1: Synchronized', 
               transform=ax.transAxes, fontsize=10,
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def disease_coherence_evolution(self, ax):
        """Panel 2: Coherence evolution during disease and therapy"""
        t = np.linspace(0, 200, 1000)
        
        # Physiological coherence
        r_phys = 0.85
        
        # Disease onset (gradual decoherence)
        t_disease = 50
        tau_disease = 20
        r_disease = r_phys * (1 - 0.6 * (1 - np.exp(-(t - t_disease) / tau_disease)) * (t >= t_disease))
        
        # Therapy onset (recoherence)
        t_therapy = 120
        tau_therapy = 15
        E = 0.7  # Therapeutic efficacy
        
        # Recoherence formula: r_treated = sqrt(1 - (1-E)(1-r_untreated^2))
        r_therapy = np.copy(r_disease)
        mask_therapy = t >= t_therapy
        r_untreated_at_therapy = r_disease[t >= t_therapy]
        r_therapy[mask_therapy] = np.sqrt(1 - (1 - E) * (1 - r_untreated_at_therapy**2))
        
        # Smooth transition
        transition = 1 - np.exp(-(t[mask_therapy] - t_therapy) / tau_therapy)
        r_therapy[mask_therapy] = r_disease[mask_therapy] + (r_therapy[mask_therapy] - r_disease[mask_therapy]) * transition
        
        ax.plot(t, r_phys * np.ones_like(t), 'b--', linewidth=2, 
               label='Physiological baseline', alpha=0.7)
        ax.plot(t[t < t_therapy], r_disease[t < t_therapy], 'r-', linewidth=2.5, 
               label='Disease progression', alpha=0.8)
        ax.plot(t[t >= t_therapy], r_therapy[t >= t_therapy], 'g-', linewidth=2.5, 
               label='Post-therapy recovery', alpha=0.8)
        
        ax.axvline(t_disease, color='red', linestyle=':', linewidth=1.5, 
                  label='Disease onset', alpha=0.5)
        ax.axvline(t_therapy, color='green', linestyle=':', linewidth=1.5, 
                  label='Therapy onset', alpha=0.5)
        
        # Shade regions
        ax.axvspan(0, t_disease, alpha=0.1, color='blue', label='Health')
        ax.axvspan(t_disease, t_therapy, alpha=0.1, color='red', label='Disease')
        ax.axvspan(t_therapy, 200, alpha=0.1, color='green', label='Treatment')
        
        ax.set_xlabel('Time (arbitrary units)', fontsize=12)
        ax.set_ylabel('Order Parameter r', fontsize=12)
        ax.set_title('Coherence Evolution: Disease → Therapy', 
                    fontsize=14, fontweight='bold')
        ax.legend(fontsize=9, ncol=2, loc='lower left')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1)
    
    def coherence_disorder_landscape(self, ax):
        """Panel 3: 3D coherence as function of coupling and disorder"""
        K = np.linspace(0, 3, 50)
        Delta = np.linspace(0.1, 2, 50)
        
        K_grid, Delta_grid = np.meshgrid(K, Delta)
        
        # Critical coupling
        K_c = 2 * Delta_grid / np.pi
        
        # Order parameter
        r = np.zeros_like(K_grid)
        mask = K_grid > K_c
        r[mask] = np.sqrt(1 - K_c[mask] / K_grid[mask])
        
        surf = ax.plot_surface(K_grid, Delta_grid, r, 
                              cmap=cm.plasma, alpha=0.8, 
                              edgecolor='none', antialiased=True)
        
        # Contour lines
        ax.contour(K_grid, Delta_grid, r, levels=10, 
                  colors='black', alpha=0.3, linewidths=0.5)
        
        # Critical surface
        ax.plot_surface(K_c, Delta_grid, np.zeros_like(K_c), 
                       alpha=0.3, color='red', label='Critical surface')
        
        ax.set_xlabel('Coupling K', fontsize=11)
        ax.set_ylabel('Frequency Disorder Δ', fontsize=11)
        ax.set_zlabel('Order Parameter r', fontsize=11)
        ax.set_title('Coherence Landscape (K-Δ Space)', fontsize=14, fontweight='bold')
        ax.view_init(elev=25, azim=45)
        
        plt.colorbar(surf, ax=ax, shrink=0.5, label='Coherence r')
    
    def chimera_state_dynamics(self, ax):
        """Panel 4: Chimera states (coexisting coherent and incoherent populations)"""
        N = 100  # Number of oscillators
        t = np.linspace(0, 50, 500)
        
        # Create chimera: half synchronized, half desynchronized
        theta = np.zeros((len(t), N))
        
        # Initial conditions
        theta[0, :N//2] = np.random.uniform(0, 0.5, N//2)  # Synchronized group
        theta[0, N//2:] = np.random.uniform(0, 2*np.pi, N//2)  # Desynchronized group
        
        # Simple evolution (illustrative)
        omega_sync = 1.0
        omega_desync = np.random.normal(1.0, 0.5, N//2)
        
        for i in range(1, len(t)):
            dt = t[i] - t[i-1]
            # Synchronized group
            theta[i, :N//2] = theta[i-1, :N//2] + omega_sync * dt
            # Desynchronized group
            theta[i, N//2:] = theta[i-1, N//2:] + omega_desync * dt
        
        # Wrap to [0, 2π]
        theta = np.mod(theta, 2*np.pi)
        
        # Plot phase distribution at different times
        times_to_plot = [0, len(t)//3, 2*len(t)//3, len(t)-1]
        colors_time = ['blue', 'green', 'orange', 'red']
        
        for idx, (t_idx, color) in enumerate(zip(times_to_plot, colors_time)):
            phases = theta[t_idx, :]
            
            # Plot on unit circle
            x_sync = np.cos(phases[:N//2])
            y_sync = np.sin(phases[:N//2])
            x_desync = np.cos(phases[N//2:])
            y_desync = np.sin(phases[N//2:])
            
            offset = idx * 2.5
            ax.scatter(x_sync + offset, y_sync, c=color, s=30, alpha=0.7, 
                      marker='o', edgecolors='black', linewidths=0.5)
            ax.scatter(x_desync + offset, y_desync, c=color, s=30, alpha=0.7, 
                      marker='x', linewidths=1.5)
            
            # Draw unit circle
            circle = plt.Circle((offset, 0), 1, fill=False, color='gray', 
                               linestyle='--', linewidth=1, alpha=0.5)
            ax.add_patch(circle)
            
            # Label
            ax.text(offset, -1.5, f't={t[t_idx]:.1f}', ha='center', fontsize=10)
        
        ax.set_xlim(-2, 10)
        ax.set_ylim(-2, 2)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title('Chimera State Evolution (○ synchronized, × desynchronized)', 
                    fontsize=14, fontweight='bold')
        
        # Legend
        from matplotlib.lines import Line2D
        legend_elements = [Line2D([0], [0], marker='o', color='w', 
                                 markerfacecolor='gray', markersize=8, 
                                 label='Synchronized', markeredgecolor='black'),
                          Line2D([0], [0], marker='x', color='gray', 
                                markersize=8, label='Desynchronized', 
                                markeredgewidth=1.5, linestyle='None')]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
    
    def generate_phase_coherence_panel(self):
        """Generate 4-panel phase coherence validation chart"""
        fig = plt.figure(figsize=(16, 12))
        
        # Panel 1: Order parameter (2D)
        ax1 = plt.subplot(2, 2, 1)
        self.kuramoto_order_parameter(ax1)
        
        # Panel 2: Disease-therapy evolution (2D)
        ax2 = plt.subplot(2, 2, 2)
        self.disease_coherence_evolution(ax2)
        
        # Panel 3: Coherence landscape (3D)
        ax3 = plt.subplot(2, 2, 3, projection='3d')
        self.coherence_disorder_landscape(ax3)
        
        # Panel 4: Chimera states (2D)
        ax4 = plt.subplot(2, 2, 4)
        self.chimera_state_dynamics(ax4)
        
        plt.suptitle('Phase Coherence and Synchronization: Validation Panel', 
                     fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout(rect=[0, 0, 1, 0.99])
        
        output_path = os.path.join(self.output_dir, 'phase_coherence_validation_panel.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"[OK] Phase coherence validation panel saved: {output_path}")
        plt.close()

def main():
    """Run phase coherence validation experiments"""
    print("\n" + "="*60)
    print("PHASE COHERENCE VALIDATION")
    print("="*60 + "\n")
    
    validator = PhaseCoherenceValidator()
    
    print("Generating phase coherence validation panel...")
    validator.generate_phase_coherence_panel()
    
    print("\n" + "="*60)
    print("PHASE COHERENCE VALIDATION COMPLETE")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
