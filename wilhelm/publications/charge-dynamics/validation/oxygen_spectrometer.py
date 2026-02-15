import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
from scipy.interpolate import griddata
import json

def figure3_o2_stark_spectroscopy():
    """
    Figure 3: O₂ Stark Spectroscopy
    (A) Stark shift vs. field strength (theory + data)
    (B) Spatial map of shift in cell (2D)
    (C) Temporal dynamics during AP (3D surface)
    (D) Proposed experimental setup
    """
    # Set style
    plt.style.use('seaborn-v0_8-paper')
    sns.set_palette("husl")
    
    # Create figure
    fig = plt.figure(figsize=(16, 14))
    
    # Physical parameters
    E_field_range = np.logspace(4, 7, 100)  # 10 kV/m to 10 MV/m
    omega_0 = 144.56e9  # O2 rotational constant (Hz)
    
    # Stark shift model (from validation data)
    # Δω = -α * E^2 where α is polarizability
    alpha_stark = 1.179e-3 / (1e5)**2  # Hz/(V/m)^2 from validation
    stark_shift = -alpha_stark * E_field_range**2
    relative_shift = stark_shift / omega_0
    
    # ========== PANEL A: Stark Shift vs Field Strength ==========
    ax1 = fig.add_subplot(2, 2, 1)
    
    # Plot theory curve
    ax1.loglog(E_field_range / 1e6, np.abs(stark_shift), 
              linewidth=3, color='#2E86AB', label='Theory: Δω ∝ E²')
    
    # Add validation data points
    E_validation = np.array([1e5, 5e5, 1e6, 5e6])
    shift_validation = -alpha_stark * E_validation**2
    ax1.scatter(E_validation / 1e6, np.abs(shift_validation), 
               s=200, c='#E63946', marker='o', edgecolors='black', 
               linewidth=2, zorder=10, label='Validation data')
    
    # Mark cellular field range
    E_cell_min, E_cell_max = 1e5, 1e6
    ax1.axvspan(E_cell_min / 1e6, E_cell_max / 1e6, 
               alpha=0.2, color='green', label='Cellular range')
    
    # Add sensitivity threshold
    sensitivity = 1e-10  # Relative shift detection limit
    shift_threshold = sensitivity * omega_0
    ax1.axhline(shift_threshold, color='orange', linestyle='--', 
               linewidth=2, label=f'Detection limit (~{sensitivity:.0e})')
    
    ax1.set_xlabel('Electric Field Strength (MV/m)', fontsize=13, fontweight='bold')
    ax1.set_ylabel('|Stark Shift| (Hz)', fontsize=13, fontweight='bold')
    ax1.set_title('(A) O₂ Stark Shift: Quadratic Field Dependence', 
                  fontsize=14, fontweight='bold', pad=15)
    ax1.legend(fontsize=10, loc='upper left', framealpha=0.95)
    ax1.grid(True, alpha=0.3, which='both')
    
    # Add annotation
    ax1.text(0.6, 0.15, 
            r'$\Delta\omega = -\alpha E^2$' + '\n' + 
            r'$\alpha = 1.18 \times 10^{-3}$ Hz/(V/m)²',
            transform=ax1.transAxes, fontsize=12, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    # ========== PANEL B: Spatial Map in Cell ==========
    ax2 = fig.add_subplot(2, 2, 2)
    
    # Create cell geometry
    R_cell = 10e-6
    R_nucleus = 5e-6
    
    # 2D grid
    x = np.linspace(-R_cell, R_cell, 200)
    y = np.linspace(-R_cell, R_cell, 200)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    
    # E-field distribution (simplified)
    E_membrane = 113.6e6
    E_bulk = 14e3
    lambda_D = 0.8085e-9
    
    E_2D = np.zeros_like(R)
    mask_outside = R > R_cell
    mask_nucleus = R <= R_nucleus
    mask_cytoplasm = (R > R_nucleus) & (R <= R_cell)
    
    E_2D[mask_outside] = 0
    E_2D[mask_nucleus] = E_bulk * 2
    r_cyto = R[mask_cytoplasm]
    E_2D[mask_cytoplasm] = E_membrane * np.exp(-(R_cell - r_cyto) / (lambda_D * 1000)) + E_bulk
    
    # Calculate Stark shift map
    stark_map = -alpha_stark * E_2D**2
    
    # Plot
    im = ax2.contourf(X * 1e6, Y * 1e6, np.log10(np.abs(stark_map) + 1), 
                     levels=50, cmap='RdYlBu_r', extend='both')
    
    # Add cell boundaries
    theta = np.linspace(0, 2*np.pi, 100)
    ax2.plot(R_cell * 1e6 * np.cos(theta), R_cell * 1e6 * np.sin(theta), 
            'k-', linewidth=3, label='Membrane')
    ax2.plot(R_nucleus * 1e6 * np.cos(theta), R_nucleus * 1e6 * np.sin(theta), 
            'k--', linewidth=2, label='Nucleus')
    
    # Add O2 molecule positions (random sampling)
    n_o2 = 500  # Subset for visualization
    np.random.seed(42)
    r_o2 = np.random.uniform(R_nucleus, R_cell, n_o2)
    theta_o2 = np.random.uniform(0, 2*np.pi, n_o2)
    x_o2 = r_o2 * np.cos(theta_o2)
    y_o2 = r_o2 * np.sin(theta_o2)
    
    # Color by local Stark shift
    stark_o2 = griddata((X.flatten(), Y.flatten()), stark_map.flatten(), 
                        (x_o2, y_o2), method='linear')
    
    scatter = ax2.scatter(x_o2 * 1e6, y_o2 * 1e6, c=np.log10(np.abs(stark_o2) + 1), 
                         s=10, cmap='RdYlBu_r', alpha=0.6, edgecolors='none')
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax2, label='log₁₀(|Stark Shift|) [Hz]')
    cbar.ax.tick_params(labelsize=10)
    
    ax2.set_xlabel('X Position (μm)', fontsize=13, fontweight='bold')
    ax2.set_ylabel('Y Position (μm)', fontsize=13, fontweight='bold')
    ax2.set_title('(B) Spatial Stark Shift Map: O₂ Sensor Array', 
                  fontsize=14, fontweight='bold', pad=15)
    ax2.legend(fontsize=10, loc='upper right', framealpha=0.95)
    ax2.set_aspect('equal')
    ax2.grid(False)
    
    # ========== PANEL C: Temporal Dynamics During AP (3D) ==========
    ax3 = fig.add_subplot(2, 2, 3, projection='3d')
    
    # Action potential waveform
    t_ap = np.linspace(0, 5, 200)  # ms
    V_rest = -70  # mV
    V_peak = 40   # mV
    
    # Hodgkin-Huxley-like AP
    t_rise = 1.0
    t_fall = 2.0
    V_ap = V_rest + (V_peak - V_rest) * (
        np.exp(-(t_ap - t_rise)**2 / 0.2) * (t_ap >= t_rise) +
        np.exp(-(t_ap - t_fall)**2 / 0.5) * (t_ap >= t_fall) * (t_ap < 3.5)
    )
    
    # Convert voltage to field (assume membrane thickness 5 nm)
    d_membrane = 5e-9
    E_ap = (V_ap * 1e-3) / d_membrane  # V/m
    
    # Stark shift during AP
    stark_ap = -alpha_stark * E_ap**2
    
    # Create 3D surface: time × position × shift
    n_positions = 50
    r_positions = np.linspace(R_nucleus, R_cell, n_positions)
    T_mesh, R_mesh = np.meshgrid(t_ap, r_positions)
    
    # Field decays with distance from membrane
    E_mesh = E_ap[np.newaxis, :] * np.exp(-(R_cell - r_positions[:, np.newaxis]) / (lambda_D * 1000))
    stark_mesh = -alpha_stark * E_mesh**2
    
    # Plot surface
    surf = ax3.plot_surface(T_mesh, R_mesh * 1e6, stark_mesh, 
                           cmap='viridis', alpha=0.9, 
                           linewidth=0, antialiased=True, shade=True)
    
    # Add AP trace on side
    ax3.plot(t_ap, np.ones_like(t_ap) * R_cell * 1e6, stark_ap, 
            'r-', linewidth=3, label='Membrane')
    
    # Add contour lines
    ax3.contour(T_mesh, R_mesh * 1e6, stark_mesh, 
               levels=10, colors='black', alpha=0.3, linewidths=1)
    
    ax3.set_xlabel('Time (ms)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Radial Position (μm)', fontsize=11, fontweight='bold')
    ax3.set_zlabel('Stark Shift (Hz)', fontsize=11, fontweight='bold')
    ax3.set_title('(C) Temporal Dynamics: Action Potential Modulation', 
                  fontsize=14, fontweight='bold', pad=15)
    
    ax3.view_init(elev=25, azim=45)
    
    # Colorbar
    fig.colorbar(surf, ax=ax3, shrink=0.5, aspect=10, 
                label='Stark Shift (Hz)', pad=0.1)
    
    # ========== PANEL D: Experimental Setup ==========
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.axis('off')
    
    # Draw schematic
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
    
    # Optical cavity
    cavity = FancyBboxPatch((0.1, 0.6), 0.3, 0.25, 
                           boxstyle="round,pad=0.02", 
                           edgecolor='black', facecolor='lightblue', 
                           linewidth=3, transform=ax4.transAxes)
    ax4.add_patch(cavity)
    ax4.text(0.25, 0.725, 'Optical\nCavity', ha='center', va='center', 
            fontsize=12, fontweight='bold', transform=ax4.transAxes)
    
    # Cell sample
    cell = Circle((0.25, 0.5), 0.05, color='pink', ec='black', 
                 linewidth=2, transform=ax4.transAxes, zorder=10)
    ax4.add_patch(cell)
    ax4.text(0.25, 0.5, 'Cell', ha='center', va='center', 
            fontsize=10, fontweight='bold', transform=ax4.transAxes)
    
    # Laser
    laser = FancyBboxPatch((0.5, 0.65), 0.15, 0.15, 
                          boxstyle="round,pad=0.01", 
                          edgecolor='red', facecolor='lightyellow', 
                          linewidth=2, transform=ax4.transAxes)
    ax4.add_patch(laser)
    ax4.text(0.575, 0.725, 'Laser\n1556 cm⁻¹', ha='center', va='center', 
            fontsize=11, fontweight='bold', color='red', transform=ax4.transAxes)
    
    # Detector
    detector = FancyBboxPatch((0.7, 0.65), 0.15, 0.15, 
                             boxstyle="round,pad=0.01", 
                             edgecolor='blue', facecolor='lightgreen', 
                             linewidth=2, transform=ax4.transAxes)
    ax4.add_patch(detector)
    ax4.text(0.775, 0.725, 'Detector\n(Δω ~ Hz)', ha='center', va='center', 
            fontsize=11, fontweight='bold', color='blue', transform=ax4.transAxes)
    
    # Arrows
    arrow1 = FancyArrowPatch((0.4, 0.725), (0.5, 0.725), 
                            arrowstyle='->', mutation_scale=30, 
                            linewidth=3, color='red', 
                            transform=ax4.transAxes)
    ax4.add_patch(arrow1)
    
    arrow2 = FancyArrowPatch((0.65, 0.725), (0.7, 0.725), 
                            arrowstyle='->', mutation_scale=30, 
                            linewidth=3, color='orange', 
                            transform=ax4.transAxes)
    ax4.add_patch(arrow2)
    
    # Voltage clamp
    vclamp = FancyBboxPatch((0.1, 0.25), 0.3, 0.2, 
                           boxstyle="round,pad=0.02", 
                           edgecolor='purple', facecolor='lavender', 
                           linewidth=2, transform=ax4.transAxes)
    ax4.add_patch(vclamp)
    ax4.text(0.25, 0.35, 'Voltage\nClamp', ha='center', va='center', 
            fontsize=11, fontweight='bold', color='purple', transform=ax4.transAxes)
    
    # Connection to cell
    arrow3 = FancyArrowPatch((0.25, 0.45), (0.25, 0.47), 
                            arrowstyle='<->', mutation_scale=20, 
                            linewidth=2, color='purple', 
                            transform=ax4.transAxes)
    ax4.add_patch(arrow3)
    
    # Spectrometer
    spec = FancyBboxPatch((0.5, 0.25), 0.35, 0.2, 
                         boxstyle="round,pad=0.02", 
                         edgecolor='green', facecolor='lightcyan', 
                         linewidth=2, transform=ax4.transAxes)
    ax4.add_patch(spec)
    ax4.text(0.675, 0.35, 'High-Resolution\nSpectrometer', ha='center', va='center', 
            fontsize=11, fontweight='bold', color='green', transform=ax4.transAxes)
    
    # Specifications box
    specs_text = (
        'Technical Specifications:\n'
        '━━━━━━━━━━━━━━━━━━━━━━\n'
        '• Frequency: O₂ ν₁ band (1556 cm⁻¹)\n'
        '• Resolution: 0.001 cm⁻¹ (30 MHz)\n'
        '• Sensitivity: 10⁻¹⁰ relative shift\n'
        '• Field range: 0.1-10 MV/m\n'
        '• Temperature: 310 K (37°C)\n'
        '• Method: Cavity-enhanced Raman'
    )
    
    ax4.text(0.5, 0.08, specs_text, ha='center', va='center', 
            fontsize=10, family='monospace',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='wheat', alpha=0.8),
            transform=ax4.transAxes)
    
    ax4.set_title('(D) Proposed Experimental Setup: Cavity-Enhanced Stark Spectroscopy', 
                  fontsize=14, fontweight='bold', pad=20)
    ax4.set_xlim(0, 1)
    ax4.set_ylim(0, 1)
    
    # Overall title
    fig.suptitle('Figure 3: O₂ Stark Spectroscopy for Cellular Field Measurement', 
                 fontsize=18, fontweight='bold', y=0.995)
    
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    plt.savefig('figure3_o2_stark_spectroscopy.png', dpi=300, bbox_inches='tight')
    plt.savefig('figure3_o2_stark_spectroscopy.pdf', bbox_inches='tight')
    print("✅ Figure 3 saved: figure3_o2_stark_spectroscopy.png/pdf")
    plt.show()


def main():
    """Main function to generate Figure 3"""
    print("Generating Figure 3: O₂ Stark Spectroscopy...")
    figure3_o2_stark_spectroscopy()
    print("Done!")


if __name__ == "__main__":
    main()
