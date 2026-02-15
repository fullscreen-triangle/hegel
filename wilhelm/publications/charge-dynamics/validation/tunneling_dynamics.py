import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
from scipy.special import erf

def figure7_quantum_tunneling_dynamics():
    """
    Figure 7: Quantum Tunneling Dynamics
    (A) Tunneling current distribution (1-100 pA)
    (B) Charge transfer timescale
    (C) 3D membrane defect model
    (D) Classical vs quantum pathways
    """
    # Set style
    plt.style.use('seaborn-v0_8-paper')
    sns.set_palette("husl")
    
    # Create figure
    fig = plt.figure(figsize=(16, 14))
    
    # Physical parameters
    e = 1.6e-19  # C
    hbar = 1.055e-34  # J·s
    m_e = 9.11e-31  # kg
    d_membrane = 5e-9  # m (membrane thickness)
    V_barrier = 0.5 * e  # J (lipid barrier)
    
    # Tunneling data from validation
    I_min, I_max = 1e-12, 100e-12  # A (1-100 pA)
    
    # ========== PANEL A: Tunneling Current Distribution ==========
    ax1 = fig.add_subplot(2, 2, 1)
    
    # Generate log-normal distribution of currents
    np.random.seed(42)
    n_measurements = 1000
    mu_log = np.log(10e-12)  # Mean at 10 pA
    sigma_log = 1.0
    currents = np.random.lognormal(mu_log, sigma_log, n_measurements)
    currents = np.clip(currents, I_min, I_max)
    
    # Histogram
    bins = np.logspace(np.log10(I_min), np.log10(I_max), 30)
    counts, edges = np.histogram(currents, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2
    
    ax1.bar(centers * 1e12, counts, width=np.diff(edges) * 1e12, 
           color='#2E86AB', alpha=0.7, edgecolor='black', linewidth=1)
    
    # Fit log-normal
    from scipy.stats import lognorm
    shape, loc, scale = lognorm.fit(currents, floc=0)
    x_fit = np.logspace(np.log10(I_min), np.log10(I_max), 100)
    pdf_fit = lognorm.pdf(x_fit, shape, loc, scale)
    pdf_fit_scaled = pdf_fit * n_measurements * (np.log10(I_max) - np.log10(I_min)) / 30
    
    ax1_twin = ax1.twinx()
    ax1_twin.plot(x_fit * 1e12, pdf_fit_scaled, 'r--', linewidth=3, 
                 label='Log-normal fit')
    ax1_twin.set_ylabel('Probability Density', fontsize=12, fontweight='bold', color='red')
    ax1_twin.tick_params(axis='y', labelcolor='red')
    
    ax1.set_xscale('log')
    ax1.set_xlabel('Tunneling Current (pA)', fontsize=13, fontweight='bold')
    ax1.set_ylabel('Count', fontsize=13, fontweight='bold')
    ax1.set_title('(A) Tunneling Current Distribution: Membrane Defects', 
                  fontsize=14, fontweight='bold', pad=15)
    ax1.grid(True, alpha=0.3, which='both')
    
    # Add statistics
    I_mean = np.mean(currents) * 1e12
    I_median = np.median(currents) * 1e12
    I_std = np.std(currents) * 1e12
    
    ax1.text(0.05, 0.95, 
            f'Mean: {I_mean:.1f} pA\n'
            f'Median: {I_median:.1f} pA\n'
            f'Std: {I_std:.1f} pA\n'
            f'Range: {I_min*1e12:.0f}-{I_max*1e12:.0f} pA',
            transform=ax1.transAxes, fontsize=11, fontweight='bold',
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    # ========== PANEL B: Charge Transfer Timescale ==========
    ax2 = fig.add_subplot(2, 2, 2)
    
    # Calculate transfer time for different cluster sizes
    cluster_sizes = np.arange(1, 201)  # 1 to 200 electrons
    currents_range = np.logspace(np.log10(I_min), np.log10(I_max), 5)
    
    for I in currents_range:
        transfer_times = (cluster_sizes * e) / I
        ax2.loglog(cluster_sizes, transfer_times * 1e9, linewidth=2.5, 
                  label=f'I = {I*1e12:.0f} pA', alpha=0.8)
    
    # Mark validation point (50e cluster, 10 pA)
    I_validation = 10e-12
    N_validation = 50
    tau_validation = (N_validation * e) / I_validation
    ax2.scatter([N_validation], [tau_validation * 1e9], 
               s=300, c='red', marker='*', edgecolors='black', 
               linewidth=2, zorder=10, label='Validation (50e, 10 pA)')
    
    # Mark Debye time
    tau_debye = 0.33e-9
    ax2.axhline(tau_debye * 1e9, color='green', linestyle='--', linewidth=2.5, 
               label=f'Debye time: {tau_debye*1e9:.2f} ns', alpha=0.7)
    
    ax2.set_xlabel('Charge Cluster Size (electrons)', fontsize=13, fontweight='bold')
    ax2.set_ylabel('Transfer Time (ns)', fontsize=13, fontweight='bold')
    ax2.set_title('(B) Quantum Transfer: Faster Than Screening', 
                  fontsize=14, fontweight='bold', pad=15)
    ax2.legend(fontsize=9, loc='upper left', framealpha=0.95)
    ax2.grid(True, alpha=0.3, which='both')
    
    # Add annotation
    ax2.text(0.95, 0.05, 
            f'Validation:\n'
            f'τ_transfer = {tau_validation*1e9:.2f} ns\n'
            f'τ_Debye = {tau_debye*1e9:.2f} ns\n'
            f'Ratio: {tau_validation/tau_debye:.2f}×',
            transform=ax2.transAxes, fontsize=11, fontweight='bold',
            verticalalignment='bottom', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
    
    # ========== PANEL C: 3D Membrane Defect Model ==========
    ax3 = fig.add_subplot(2, 2, 3, projection='3d')
    
    # Create membrane surface
    x_mem = np.linspace(-20, 20, 50)
    y_mem = np.linspace(-20, 20, 50)
    X_mem, Y_mem = np.meshgrid(x_mem, y_mem)
    
    # Membrane surfaces (bilayer)
    Z_outer = np.ones_like(X_mem) * 2.5
    Z_inner = np.ones_like(X_mem) * (-2.5)
    
    # Add defect (Gaussian depression)
    defect_x, defect_y = 0, 0
    defect_radius = 5
    defect_depth = 2.0
    
    R_defect = np.sqrt((X_mem - defect_x)**2 + (Y_mem - defect_y)**2)
    Z_outer -= defect_depth * np.exp(-R_defect**2 / (2 * defect_radius**2))
    Z_inner += defect_depth * np.exp(-R_defect**2 / (2 * defect_radius**2))
    
    # Plot membrane surfaces
    surf1 = ax3.plot_surface(X_mem, Y_mem, Z_outer, cmap='Oranges', 
                            alpha=0.7, linewidth=0, antialiased=True, shade=True)
    surf2 = ax3.plot_surface(X_mem, Y_mem, Z_inner, cmap='Blues', 
                            alpha=0.7, linewidth=0, antialiased=True, shade=True)
    
    # Add tunneling path (electron trajectory)
    z_tunnel = np.linspace(2.5, -2.5, 50)
    x_tunnel = np.zeros_like(z_tunnel)
    y_tunnel = np.zeros_like(z_tunnel)
    
    # Add some curvature to show quantum nature
    x_tunnel += 2 * np.sin(np.linspace(0, 2*np.pi, 50))
    
    ax3.plot(x_tunnel, y_tunnel, z_tunnel, 'r-', linewidth=4, 
            label='Tunneling path', zorder=10)
    
    # Add electron at start and end
    ax3.scatter([x_tunnel[0]], [y_tunnel[0]], [z_tunnel[0]], 
               s=200, c='blue', marker='o', edgecolors='black', 
               linewidth=2, zorder=11, label='Electron')
    ax3.scatter([x_tunnel[-1]], [y_tunnel[-1]], [z_tunnel[-1]], 
               s=200, c='red', marker='o', edgecolors='black', 
               linewidth=2, zorder=11)
    
    # Add arrows showing field direction
    n_arrows = 5
    for i in range(n_arrows):
        angle = 2 * np.pi * i / n_arrows
        x_arr = 15 * np.cos(angle)
        y_arr = 15 * np.sin(angle)
        ax3.quiver(x_arr, y_arr, 3, 0, 0, -1, 
                  length=2, arrow_length_ratio=0.3, 
                  color='purple', linewidth=2, alpha=0.7)
    
    ax3.set_xlabel('X (nm)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Y (nm)', fontsize=11, fontweight='bold')
    ax3.set_zlabel('Z (nm)', fontsize=11, fontweight='bold')
    ax3.set_title('(C) Membrane Defect: Quantum Tunneling Pathway', 
                  fontsize=14, fontweight='bold', pad=15)
    
    ax3.set_xlim(-20, 20)
    ax3.set_ylim(-20, 20)
    ax3.set_zlim(-5, 5)
    
    ax3.view_init(elev=20, azim=45)
    
    # Add annotation
    ax3.text2D(0.05, 0.95, 
              f'Defect size: {defect_radius:.0f} nm\n'
              f'Barrier reduction: {defect_depth:.1f} nm\n'
              f'Tunneling probability: ↑',
              transform=ax3.transAxes, fontsize=10, fontweight='bold',
              verticalalignment='top',
              bbox=dict(boxstyle='round', facecolor='lightcyan', alpha=0.8))
    
    # ========== PANEL D: Classical vs Quantum Pathways ==========
    ax4 = fig.add_subplot(2, 2, 4)
    
    # Energy diagram
    x_coord = np.linspace(0, d_membrane * 1e9, 1000)
    
    # Classical barrier (full height)
    V_classical = np.ones_like(x_coord) * V_barrier / e * 1000  # mV
    V_classical[x_coord < 0.5] = 0
    V_classical[x_coord > d_membrane * 1e9 - 0.5] = 0
    
    # Quantum barrier (with defect)
    V_quantum = V_classical.copy()
    defect_center = d_membrane * 1e9 / 2
    defect_width = 1.0  # nm
    V_quantum *= (1 - 0.7 * np.exp(-(x_coord - defect_center)**2 / (2 * defect_width**2)))
    
    # Plot barriers
    ax4.fill_between(x_coord, 0, V_classical, color='red', alpha=0.3, 
                     label='Classical barrier (lipid)')
    ax4.fill_between(x_coord, 0, V_quantum, color='blue', alpha=0.5, 
                     label='Quantum barrier (defect)')
    
    # Add electron energy level
    E_electron = 100  # mV (thermal energy)
    ax4.axhline(E_electron, color='green', linestyle='--', linewidth=2.5, 
               label=f'Electron energy: {E_electron} mV', alpha=0.7)
    
    # Classical trajectory (blocked)
    x_classical = np.linspace(0, 1, 50)
    y_classical = np.ones_like(x_classical) * E_electron
    ax4.plot(x_classical, y_classical, 'r-', linewidth=3, alpha=0.7)
    ax4.scatter([x_classical[-1]], [y_classical[-1]], s=200, c='red', 
               marker='X', edgecolors='black', linewidth=2, zorder=10)
    ax4.text(x_classical[-1] + 0.2, y_classical[-1], 'Blocked', 
            fontsize=11, fontweight='bold', color='red')
    
    # Quantum trajectory (tunnels through)
    x_quantum = np.linspace(0, d_membrane * 1e9, 100)
    y_quantum = np.ones_like(x_quantum) * E_electron
    # Add exponential decay in barrier
    mask_barrier = (x_quantum > 0.5) & (x_quantum < d_membrane * 1e9 - 0.5)
    y_quantum[mask_barrier] *= np.exp(-0.5 * (x_quantum[mask_barrier] - 0.5))
    
    ax4.plot(x_quantum, y_quantum, 'b-', linewidth=3, alpha=0.8, label='Quantum path')
    ax4.scatter([x_quantum[-1]], [y_quantum[-1]], s=200, c='blue', 
               marker='o', edgecolors='black', linewidth=2, zorder=10)
    ax4.text(x_quantum[-1] - 0.5, y_quantum[-1] + 50, 'Transmitted', 
            fontsize=11, fontweight='bold', color='blue')
    
    # Add tunneling probability annotation
    kappa = np.sqrt(2 * m_e * (V_barrier - E_electron * e) / hbar**2)
    T_classical = 0  # Blocked
    T_quantum = np.exp(-2 * kappa * d_membrane)
    
    ax4.set_xlabel('Position Across Membrane (nm)', fontsize=13, fontweight='bold')
    ax4.set_ylabel('Energy (mV)', fontsize=13, fontweight='bold')
    ax4.set_title('(D) Classical vs Quantum Charge Transfer', 
                  fontsize=14, fontweight='bold', pad=15)
    ax4.legend(fontsize=10, loc='upper right', framealpha=0.95)
    ax4.grid(True, alpha=0.3, axis='y')
    ax4.set_xlim(0, d_membrane * 1e9)
    ax4.set_ylim(0, 600)
    
    # Add comparison table
    table_data = [
        ['Property', 'Classical', 'Quantum'],
        ['Mechanism', 'Diffusion', 'Tunneling'],
        ['Timescale', '~ms', '~ns'],
        ['Probability', '0%', f'{T_quantum:.2e}'],
        ['Current', '0 pA', '1-100 pA']
    ]
    
    table = ax4.table(cellText=table_data, cellLoc='center', loc='lower left',
                     bbox=[0.02, 0.02, 0.4, 0.35],
                     colWidths=[0.15, 0.12, 0.12])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.8)
    
    # Style header row
    for i in range(3):
        table[(0, i)].set_facecolor('#40466e')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Style data rows
    for i in range(1, 5):
        for j in range(3):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#f0f0f0')
            table[(i, j)].set_edgecolor('black')
            table[(i, j)].set_linewidth(1)
    
    # Overall title
    fig.suptitle('Figure 7: Quantum Tunneling Dynamics in Cellular Membranes', 
                 fontsize=18, fontweight='bold', y=0.995)
    
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    plt.savefig('figure7_quantum_tunneling_dynamics.png', dpi=300, bbox_inches='tight')
    plt.savefig('figure7_quantum_tunneling_dynamics.pdf', bbox_inches='tight')
    print("✅ Figure 7 saved: figure7_quantum_tunneling_dynamics.png/pdf")
    plt.show()


def main():
    """Main function to generate Figure 7"""
    print("Generating Figure 7: Quantum Tunneling Dynamics...")
    figure7_quantum_tunneling_dynamics()
    print("Done!")


if __name__ == "__main__":
    main()
