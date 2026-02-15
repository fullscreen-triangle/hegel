import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
from scipy.interpolate import griddata

def figure1_spatial_field_architecture():
    """
    Figure 1: Spatial Field Architecture
    (A) Radial E-field profile (membrane → nucleus)
    (B) 2D field heatmap (cell cross-section)
    (C) 3D equipotential surfaces
    (D) Chamber locations (∇E maxima)
    """
    # Set style
    plt.style.use('seaborn-v0_8-paper')
    sns.set_palette("husl")
    
    # Create figure with 2x2 subplots
    fig = plt.figure(figsize=(16, 14))
    
    # Physical parameters from validation data
    R_cell = 10e-6  # 10 μm cell radius
    R_nucleus = 5e-6  # 5 μm nuclear radius
    lambda_D = 0.8085e-9  # Debye length (m)
    E_membrane = 113.6e6  # V/m at membrane surface
    E_debye = 41.8e6  # V/m at Debye length
    E_bulk = 14e3  # V/m in bulk cytoplasm
    Q_genome = -2.307e-10  # Effective genomic charge (C)
    Q_membrane = -1.011e-10  # Membrane charge (C)
    
    # ========== PANEL A: Radial E-field Profile ==========
    ax1 = fig.add_subplot(2, 2, 1)
    
    # Create radial distance array (membrane to nucleus)
    r = np.linspace(R_nucleus, R_cell, 1000)
    
    # E-field model: exponential decay from membrane + genomic contribution
    E_field = (E_membrane * np.exp(-(R_cell - r) / lambda_D) + 
               E_bulk * (1 + np.exp(-(r - R_nucleus) / lambda_D)))
    
    # Plot with log scale
    ax1.semilogy(r * 1e6, E_field, linewidth=3, color='#2E86AB', label='Total E-field')
    ax1.axhline(E_membrane, color='#A23B72', linestyle='--', linewidth=2, 
                label=f'Membrane surface: {E_membrane/1e6:.1f} MV/m')
    ax1.axhline(E_debye, color='#F18F01', linestyle='--', linewidth=2,
                label=f'Debye screened: {E_debye/1e6:.1f} MV/m')
    ax1.axhline(E_bulk, color='#C73E1D', linestyle='--', linewidth=2,
                label=f'Bulk cytoplasm: {E_bulk/1e3:.1f} kV/m')
    
    # Mark Debye length
    ax1.axvline(R_cell * 1e6 - lambda_D * 1e9 / 1000, color='gray', 
                linestyle=':', linewidth=1.5, alpha=0.7)
    ax1.text(R_cell * 1e6 - 0.3, 1e7, r'$\lambda_D$ = 0.81 nm', 
             fontsize=11, rotation=90, va='bottom')
    
    ax1.set_xlabel('Radial Distance from Center (μm)', fontsize=13, fontweight='bold')
    ax1.set_ylabel('Electric Field Strength (V/m)', fontsize=13, fontweight='bold')
    ax1.set_title('(A) Radial E-field Profile: Membrane → Nucleus', 
                  fontsize=14, fontweight='bold', pad=15)
    ax1.legend(fontsize=10, loc='upper right', framealpha=0.95)
    ax1.grid(True, alpha=0.3, which='both')
    ax1.set_xlim(R_nucleus * 1e6, R_cell * 1e6)
    ax1.set_ylim(1e4, 2e8)
    
    # ========== PANEL B: 2D Field Heatmap ==========
    ax2 = fig.add_subplot(2, 2, 2)
    
    # Create 2D grid for cell cross-section
    x = np.linspace(-R_cell, R_cell, 200)
    y = np.linspace(-R_cell, R_cell, 200)
    X, Y = np.meshgrid(x, y)
    
    # Calculate distance from center
    R = np.sqrt(X**2 + Y**2)
    
    # E-field magnitude in 2D (simplified model)
    E_2D = np.zeros_like(R)
    
    # Outside cell: zero field
    mask_outside = R > R_cell
    E_2D[mask_outside] = 0
    
    # Inside nucleus: genomic field
    mask_nucleus = R <= R_nucleus
    E_2D[mask_nucleus] = E_bulk * 2
    
    # Cytoplasm: exponential decay
    mask_cytoplasm = (R > R_nucleus) & (R <= R_cell)
    r_cyto = R[mask_cytoplasm]
    E_2D[mask_cytoplasm] = (E_membrane * np.exp(-(R_cell - r_cyto) / (lambda_D * 1000)) + 
                            E_bulk)
    
    # Plot heatmap
    im = ax2.contourf(X * 1e6, Y * 1e6, np.log10(E_2D + 1), 
                      levels=50, cmap='plasma', extend='both')
    
    # Add cell and nuclear boundaries
    theta = np.linspace(0, 2*np.pi, 100)
    ax2.plot(R_cell * 1e6 * np.cos(theta), R_cell * 1e6 * np.sin(theta), 
             'w-', linewidth=3, label='Membrane')
    ax2.plot(R_nucleus * 1e6 * np.cos(theta), R_nucleus * 1e6 * np.sin(theta), 
             'w--', linewidth=2, label='Nuclear envelope')
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax2, label='log₁₀(E-field) [V/m]')
    cbar.ax.tick_params(labelsize=10)
    
    ax2.set_xlabel('X Position (μm)', fontsize=13, fontweight='bold')
    ax2.set_ylabel('Y Position (μm)', fontsize=13, fontweight='bold')
    ax2.set_title('(B) 2D Field Heatmap: Cell Cross-Section', 
                  fontsize=14, fontweight='bold', pad=15)
    ax2.legend(fontsize=10, loc='upper right', framealpha=0.95)
    ax2.set_aspect('equal')
    ax2.grid(False)
    
    # ========== PANEL C: 3D Equipotential Surfaces ==========
    ax3 = fig.add_subplot(2, 2, 3, projection='3d')
    
    # Create 3D grid
    n_points = 50
    u = np.linspace(0, 2 * np.pi, n_points)
    v = np.linspace(0, np.pi, n_points)
    
    # Plot multiple equipotential surfaces at different radii
    field_levels = [1e4, 1e5, 1e6, 1e7]
    colors = ['#440154', '#31688e', '#35b779', '#fde724']
    alphas = [0.3, 0.4, 0.5, 0.6]
    
    for i, E_level in enumerate(field_levels):
        # Calculate radius for this field level (simplified)
        if E_level >= E_membrane:
            r_surface = R_cell
        elif E_level <= E_bulk:
            r_surface = R_nucleus
        else:
            # Exponential decay model
            r_surface = R_cell - lambda_D * 1000 * np.log(E_membrane / E_level)
            r_surface = np.clip(r_surface, R_nucleus, R_cell)
        
        # Spherical coordinates
        x_surf = r_surface * np.outer(np.cos(u), np.sin(v))
        y_surf = r_surface * np.outer(np.sin(u), np.sin(v))
        z_surf = r_surface * np.outer(np.ones(np.size(u)), np.cos(v))
        
        # Plot surface
        ax3.plot_surface(x_surf * 1e6, y_surf * 1e6, z_surf * 1e6, 
                        color=colors[i], alpha=alphas[i], 
                        label=f'{E_level/1e6:.0f} MV/m' if E_level >= 1e6 else f'{E_level/1e3:.0f} kV/m')
    
    ax3.set_xlabel('X (μm)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Y (μm)', fontsize=11, fontweight='bold')
    ax3.set_zlabel('Z (μm)', fontsize=11, fontweight='bold')
    ax3.set_title('(C) 3D Equipotential Surfaces', 
                  fontsize=14, fontweight='bold', pad=15)
    
    # Set equal aspect ratio
    max_range = R_cell * 1e6
    ax3.set_xlim(-max_range, max_range)
    ax3.set_ylim(-max_range, max_range)
    ax3.set_zlim(-max_range, max_range)
    
    # Viewing angle
    ax3.view_init(elev=20, azim=45)
    
    # ========== PANEL D: Chamber Locations (∇E Maxima) ==========
    ax4 = fig.add_subplot(2, 2, 4)
    
    # Calculate gradient magnitude
    dy, dx = np.gradient(E_2D)
    grad_E = np.sqrt(dx**2 + dy**2)
    
    # Mask outside cell
    grad_E[mask_outside] = 0
    
    # Plot gradient magnitude
    im2 = ax4.contourf(X * 1e6, Y * 1e6, np.log10(grad_E + 1), 
                       levels=50, cmap='viridis', extend='both')
    
    # Find local maxima (chamber locations)
    from scipy.ndimage import maximum_filter
    from scipy.ndimage import label
    
    # Apply maximum filter to find peaks
    neighborhood_size = 10
    local_max = maximum_filter(grad_E, neighborhood_size) == grad_E
    
    # Remove background
    background = (grad_E < np.percentile(grad_E[~mask_outside], 80))
    local_max[background] = False
    local_max[mask_outside] = False
    
    # Get coordinates of chambers
    chamber_y, chamber_x = np.where(local_max)
    chamber_x_um = X[0, chamber_x] * 1e6
    chamber_y_um = Y[chamber_y, 0] * 1e6
    
    # Plot chamber locations
    ax4.scatter(chamber_x_um, chamber_y_um, c='red', s=100, 
               marker='x', linewidths=3, label=f'Chambers (n={len(chamber_x)})', 
               zorder=10)
    
    # Add cell boundaries
    ax4.plot(R_cell * 1e6 * np.cos(theta), R_cell * 1e6 * np.sin(theta), 
             'w-', linewidth=3, label='Membrane')
    ax4.plot(R_nucleus * 1e6 * np.cos(theta), R_nucleus * 1e6 * np.sin(theta), 
             'w--', linewidth=2, label='Nuclear envelope')
    
    # Add chamber radius circles (7.2 nm)
    r_chamber = 7.2e-9  # From validation data
    for i in range(min(10, len(chamber_x))):  # Show first 10 chambers
        circle = plt.Circle((chamber_x_um[i], chamber_y_um[i]), 
                           r_chamber * 1e9 / 1000,  # Convert to μm
                           color='yellow', fill=False, linewidth=1.5, 
                           linestyle='--', alpha=0.6)
        ax4.add_patch(circle)
    
    # Colorbar
    cbar2 = plt.colorbar(im2, ax=ax4, label='log₁₀(|∇E|) [V/m²]')
    cbar2.ax.tick_params(labelsize=10)
    
    ax4.set_xlabel('X Position (μm)', fontsize=13, fontweight='bold')
    ax4.set_ylabel('Y Position (μm)', fontsize=13, fontweight='bold')
    ax4.set_title('(D) Chamber Locations at ∇E Maxima', 
                  fontsize=14, fontweight='bold', pad=15)
    ax4.legend(fontsize=10, loc='upper right', framealpha=0.95)
    ax4.set_aspect('equal')
    ax4.grid(False)
    
    # Overall title
    fig.suptitle('Figure 1: Spatial Field Architecture in Living Cells', 
                 fontsize=18, fontweight='bold', y=0.995)
    
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    plt.savefig('figure1_spatial_field_architecture.png', dpi=300, bbox_inches='tight')
    plt.savefig('figure1_spatial_field_architecture.pdf', bbox_inches='tight')
    print("✅ Figure 1 saved: figure1_spatial_field_architecture.png/pdf")
    plt.show()


def main():
    """Main function to generate Figure 1"""
    print("Generating Figure 1: Spatial Field Architecture...")
    figure1_spatial_field_architecture()
    print("Done!")


if __name__ == "__main__":
    main()
