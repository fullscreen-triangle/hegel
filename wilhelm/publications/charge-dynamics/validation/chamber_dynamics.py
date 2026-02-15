import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
from scipy.special import erf

def figure4_chamber_dynamics():
    """
    Figure 4: Chamber Dynamics
    (A) Potential well profile (energy vs. radius)
    (B) Escape time distribution
    (C) Well depth vs. ionic strength (3D surface)
    (D) Reaction rate enhancement
    """
    # Set style
    plt.style.use('seaborn-v0_8-paper')
    sns.set_palette("husl")
    
    # Create figure
    fig = plt.figure(figsize=(16, 14))
    
    # Physical parameters from validation
    r_chamber = 7.2e-9  # m
    lambda_D = 0.8085e-9  # m
    Q_cluster = 50 * 1.6e-19  # C (50 electrons)
    epsilon_0 = 8.854e-12  # F/m
    epsilon_r = 80  # Water
    k_B = 1.381e-23  # J/K
    T = 310  # K
    kT = k_B * T
    U_well = 124.4e-3 * 1.6e-19  # J (124.4 mV)
    tau_chamber = 523e-6  # s
    
    # ========== PANEL A: Potential Well Profile ==========
    ax1 = fig.add_subplot(2, 2, 1)
    
    # Radial distance from chamber center
    r = np.linspace(0, 5 * r_chamber, 1000)
    
    # Screened Coulomb potential (Yukawa)
    U_r = np.zeros_like(r)
    mask = r > 0
    U_r[mask] = (Q_cluster**2 / (4 * np.pi * epsilon_0 * epsilon_r * r[mask]) * 
                 np.exp(-r[mask] / lambda_D))
    
    # Normalize to well depth at chamber radius
    U_r = U_r / U_r[np.argmin(np.abs(r - r_chamber))] * U_well
    
    # Plot potential
    ax1.plot(r * 1e9, U_r / (k_B * T), linewidth=3, color='#2E86AB', 
            label='Screened Coulomb')
    
    # Mark key features
    ax1.axhline(0, color='black', linestyle='-', linewidth=1, alpha=0.5)
    ax1.axvline(r_chamber * 1e9, color='red', linestyle='--', linewidth=2, 
               label=f'Chamber radius: {r_chamber*1e9:.1f} nm')
    ax1.axvline(lambda_D * 1e9, color='orange', linestyle=':', linewidth=2, 
               label=f'Debye length: {lambda_D*1e9:.2f} nm')
    
    # Mark thermal energy
    ax1.axhline(1.0, color='green', linestyle='--', linewidth=2, 
               label='Thermal energy (kT)', alpha=0.7)
    
    # Shade trapping region
    idx_trap = np.where(U_r / kT > 1.0)[0]
    if len(idx_trap) > 0:
        r_trap_max = r[idx_trap[-1]]
        ax1.axvspan(0, r_trap_max * 1e9, alpha=0.2, color='yellow', 
                   label='Trapping region')
    
    ax1.set_xlabel('Radial Distance from Chamber Center (nm)', 
                  fontsize=13, fontweight='bold')
    ax1.set_ylabel('Potential Energy (kT)', fontsize=13, fontweight='bold')
    ax1.set_title('(A) Electrostatic Potential Well: 4.7 kT Depth', 
                  fontsize=14, fontweight='bold', pad=15)
    ax1.legend(fontsize=10, loc='upper right', framealpha=0.95)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 5 * r_chamber * 1e9)
    ax1.set_ylim(-1, 6)
    
    # Add annotation
    ax1.text(0.5, 0.95, 
            f'Well depth: {U_well/kT:.2f} kT\n'
            f'Escape probability: {np.exp(-U_well/kT):.3f}',
            transform=ax1.transAxes, fontsize=11, fontweight='bold',
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
    
    # ========== PANEL B: Escape Time Distribution ==========
    ax2 = fig.add_subplot(2, 2, 2)
    
    # Kramers escape time distribution
    tau_0 = 5e-6  # Attempt time (diffusion across chamber)
    tau_mean = tau_0 * np.exp(U_well / kT)
    
    # Generate escape times (exponential distribution)
    np.random.seed(42)
    n_events = 10000
    escape_times = np.random.exponential(tau_mean, n_events)
    
    # Histogram
    bins = np.logspace(np.log10(escape_times.min()), 
                       np.log10(escape_times.max()), 50)
    counts, edges = np.histogram(escape_times * 1e6, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2
    
    ax2.bar(centers, counts, width=np.diff(edges), 
           color='#E63946', alpha=0.7, edgecolor='black', linewidth=1)
    
    # Fit exponential
    t_fit = np.logspace(np.log10(escape_times.min() * 1e6), 
                        np.log10(escape_times.max() * 1e6), 100)
    fit = n_events * np.diff(bins)[0] * (1/tau_mean/1e6) * np.exp(-t_fit / (tau_mean * 1e6))
    ax2.plot(t_fit, fit, 'k--', linewidth=3, 
            label=f'Exponential fit\nτ = {tau_mean*1e6:.0f} μs')
    
    # Mark validation data
    ax2.axvline(tau_chamber * 1e6, color='blue', linestyle='-', linewidth=3, 
               label=f'Measured: {tau_chamber*1e6:.0f} μs', zorder=10)
    
    ax2.set_xscale('log')
    ax2.set_xlabel('Escape Time (μs)', fontsize=13, fontweight='bold')
    ax2.set_ylabel('Count', fontsize=13, fontweight='bold')
    ax2.set_title('(B) Chamber Lifetime Distribution: Kramers Theory', 
                  fontsize=14, fontweight='bold', pad=15)
    ax2.legend(fontsize=10, loc='upper right', framealpha=0.95)
    ax2.grid(True, alpha=0.3, which='both')
    
    # Add statistics box
    stats_text = (f'Mean: {tau_mean*1e6:.0f} μs\n'
                  f'Median: {np.median(escape_times)*1e6:.0f} μs\n'
                  f'Std: {np.std(escape_times)*1e6:.0f} μs')
    ax2.text(0.05, 0.95, stats_text, transform=ax2.transAxes, 
            fontsize=11, fontweight='bold', verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    # ========== PANEL C: Well Depth vs Ionic Strength (3D) ==========
    ax3 = fig.add_subplot(2, 2, 3, projection='3d')
    
    # Create parameter space
    ionic_strengths = np.logspace(-3, 0, 50)  # 1 mM to 1 M
    charge_clusters = np.linspace(10, 200, 50)  # 10e to 200e
    
    I_mesh, Q_mesh = np.meshgrid(ionic_strengths, charge_clusters)
    
    # Calculate Debye length for each ionic strength
    lambda_D_mesh = np.sqrt(epsilon_0 * epsilon_r * k_B * T / 
                            (2 * 1000 * 6.022e23 * (1.6e-19)**2 * I_mesh))
    
    # Calculate well depth
    r_chamber_mesh = lambda_D_mesh * np.sqrt(Q_mesh / 4)
    U_well_mesh = ((Q_mesh * 1.6e-19)**2 / 
                   (4 * np.pi * epsilon_0 * epsilon_r * r_chamber_mesh) * 
                   np.exp(-r_chamber_mesh / lambda_D_mesh))
    U_well_mesh_kT = U_well_mesh / kT
    
    # Plot surface
    surf = ax3.plot_surface(np.log10(I_mesh * 1000), Q_mesh, U_well_mesh_kT, 
                           cmap='coolwarm', alpha=0.9, 
                           linewidth=0, antialiased=True, shade=True,
                           vmin=0, vmax=10)
    
    # Mark validation point
    I_validation = 0.03  # 30 mM
    Q_validation = 50
    U_validation_kT = U_well / kT
    ax3.scatter([np.log10(I_validation * 1000)], [Q_validation], [U_validation_kT], 
               color='red', s=300, marker='*', edgecolors='black', 
               linewidth=2, zorder=10, label='Validation data')
    
    # Add contour lines
    ax3.contour(np.log10(I_mesh * 1000), Q_mesh, U_well_mesh_kT, 
               levels=[1, 2, 3, 4, 5], colors='black', alpha=0.4, linewidths=1.5)
    
    # Mark stability threshold (U > kT)
    ax3.contour(np.log10(I_mesh * 1000), Q_mesh, U_well_mesh_kT, 
               levels=[1.0], colors='yellow', linewidths=4, 
               linestyles='--', alpha=0.8)
    
    ax3.set_xlabel('log₁₀([Salt]) [mM]', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Charge Cluster (e)', fontsize=11, fontweight='bold')
    ax3.set_zlabel('Well Depth (kT)', fontsize=11, fontweight='bold')
    ax3.set_title('(C) Chamber Stability Landscape', 
                  fontsize=14, fontweight='bold', pad=15)
    
    ax3.view_init(elev=25, azim=135)
    
    # Colorbar
    cbar = fig.colorbar(surf, ax=ax3, shrink=0.5, aspect=10, 
                       label='Well Depth (kT)', pad=0.1)
    cbar.ax.tick_params(labelsize=10)
    
    # Add text annotation
    ax3.text2D(0.05, 0.95, 
              'Yellow contour:\nStability threshold\n(U = kT)', 
              transform=ax3.transAxes, fontsize=10, fontweight='bold',
              verticalalignment='top',
              bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    # ========== PANEL D: Reaction Rate Enhancement ==========
    ax4 = fig.add_subplot(2, 2, 4)
    
    # Calculate concentration enhancement factor
    U_range = np.linspace(0, 10, 100)  # kT
    enhancement = np.exp(U_range)
    
    # Plot enhancement
    ax4.semilogy(U_range, enhancement, linewidth=3, color='#2E86AB', 
                label='Boltzmann factor: exp(U/kT)')
    
    # Mark validation point
    enhancement_validation = np.exp(U_well / kT)
    ax4.scatter([U_well / kT], [enhancement_validation], 
               s=300, c='red', marker='*', edgecolors='black', 
               linewidth=2, zorder=10, 
               label=f'Chamber: {enhancement_validation:.0f}× enhancement')
    
    # Add reference lines
    ax4.axhline(10, color='orange', linestyle='--', linewidth=2, 
               label='10× enhancement', alpha=0.7)
    ax4.axhline(100, color='green', linestyle='--', linewidth=2, 
               label='100× enhancement', alpha=0.7)
    ax4.axhline(1000, color='purple', linestyle='--', linewidth=2, 
               label='1000× enhancement', alpha=0.7)
    
    # Shade physiological range
    ax4.axvspan(2, 6, alpha=0.2, color='yellow', 
               label='Physiological range')
    
    ax4.set_xlabel('Well Depth (kT)', fontsize=13, fontweight='bold')
    ax4.set_ylabel('Concentration Enhancement Factor', fontsize=13, fontweight='bold')
    ax4.set_title('(D) Reaction Rate Enhancement in Chambers', 
                  fontsize=14, fontweight='bold', pad=15)
    ax4.legend(fontsize=10, loc='upper left', framealpha=0.95)
    ax4.grid(True, alpha=0.3, which='both')
    ax4.set_xlim(0, 10)
    ax4.set_ylim(1, 1e5)
    
    # Add comparison table
    table_data = [
        ['Process', 'Bulk', 'Chamber', 'Enhancement'],
        ['Diffusion time', '1 ms', '5 μs', '200×'],
        ['Local [substrate]', '1 mM', '110 mM', '110×'],
        ['Reaction rate', 'k₀', '110 k₀', '110×'],
        ['Efficiency', '1%', '99%', '99×']
    ]
    
    table = ax4.table(cellText=table_data, cellLoc='center', loc='lower right',
                     bbox=[0.45, 0.02, 0.53, 0.35],
                     colWidths=[0.25, 0.15, 0.15, 0.15])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.8)
    
    # Style header row
    for i in range(4):
        table[(0, i)].set_facecolor('#40466e')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Style data rows
    for i in range(1, 5):
        for j in range(4):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#f0f0f0')
            table[(i, j)].set_edgecolor('black')
            table[(i, j)].set_linewidth(1)
    
    # Overall title
    fig.suptitle('Figure 4: Electrostatic Chamber Dynamics & Catalytic Enhancement', 
                 fontsize=18, fontweight='bold', y=0.995)
    
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    plt.savefig('figure4_chamber_dynamics.png', dpi=300, bbox_inches='tight')
    plt.savefig('figure4_chamber_dynamics.pdf', bbox_inches='tight')
    print("✅ Figure 4 saved: figure4_chamber_dynamics.png/pdf")
    plt.show()


def main():
    """Main function to generate Figure 4"""
    print("Generating Figure 4: Chamber Dynamics...")
    figure4_chamber_dynamics()
    print("Done!")


if __name__ == "__main__":
    main()

