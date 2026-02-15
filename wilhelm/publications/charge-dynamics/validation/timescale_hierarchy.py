import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
from matplotlib.patches import Rectangle, FancyBboxPatch, FancyArrowPatch

def figure8_integrated_timescale_hierarchy():
    """
    Figure 8: Integrated Timescale Hierarchy
    (A) Logarithmic timeline (10^-10 to 10^0 s)
    (B) Frequency spectrum (Hz)
    (C) 3D timescale-process-energy landscape
    (D) Cellular oscillations (gamma, cardiac, circadian)
    """
    # Set style
    plt.style.use('seaborn-v0_8-paper')
    sns.set_palette("husl")
    
    # Create figure
    fig = plt.figure(figsize=(16, 14))
    
    # Timescale data from validation
    processes = [
        'Molecular vibrations',
        'Quantum tunneling',
        'Debye screening (K⁺)',
        'Debye screening (Na⁺)',
        'RC charging',
        'Protein conformational',
        'O₂ oscillation period',
        'O₂ coherence time',
        'Chamber formation',
        'Chamber lifetime',
        'Resonance period (342 Hz)',
        'Action potential',
        'Heartbeat',
        'Circadian rhythm'
    ]
    
    timescales = np.array([
        1e-13,      # Molecular vibrations
        0.8e-9,     # Quantum tunneling
        0.335e-9,   # Debye K+
        0.492e-9,   # Debye Na+
        0.318e-9,   # RC time
        1e-9,       # Protein conformational
        1e-6,       # O2 period
        20e-6,      # O2 coherence
        1e-6,       # Chamber formation
        523e-6,     # Chamber lifetime
        2.92e-3,    # Resonance (1/342 Hz)
        1e-3,       # Action potential
        1.0,        # Heartbeat
        86400       # Circadian (24 hr)
    ])
    
    colors = [
        '#E63946', '#F77F00', '#F77F00', '#F77F00', '#F77F00',
        '#FCBF49', '#06D6A0', '#06D6A0', '#118AB2', '#118AB2',
        '#073B4C', '#073B4C', '#6A4C93', '#9D4EDD'
    ]
    
    # ========== PANEL A: Logarithmic Timeline ==========
    ax1 = fig.add_subplot(2, 2, 1)
    
    # Plot timescales on log scale
    log_times = np.log10(timescales)
    y_positions = np.arange(len(processes))
    
    # Horizontal bars
    for i, (proc, log_t, color) in enumerate(zip(processes, log_times, colors)):
        ax1.barh(i, log_t - (-13), left=-13, height=0.6, 
                color=color, alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Add time label
        if timescales[i] < 1e-6:
            time_str = f'{timescales[i]*1e9:.2f} ns'
        elif timescales[i] < 1e-3:
            time_str = f'{timescales[i]*1e6:.0f} μs'
        elif timescales[i] < 1:
            time_str = f'{timescales[i]*1e3:.1f} ms'
        else:
            time_str = f'{timescales[i]:.1f} s'
        
        ax1.text(log_t + 0.3, i, time_str, va='center', fontsize=9, 
                fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', 
                facecolor='white', alpha=0.8))
    
    ax1.set_yticks(y_positions)
    ax1.set_yticklabels(processes, fontsize=10)
    ax1.set_xlabel('log₁₀(Time) [s]', fontsize=13, fontweight='bold')
    ax1.set_title('(A) Timescale Hierarchy: 17 Orders of Magnitude', 
                  fontsize=14, fontweight='bold', pad=15)
    ax1.set_xlim(-13, 5)
    ax1.grid(True, alpha=0.3, axis='x')
    
    # Add vertical dividers for key regions
    regions = [
        (-13, -9, 'Quantum\nRegime', 'lightyellow'),
        (-9, -6, 'Electrostatic\nScreening', 'lightgreen'),
        (-6, -3, 'Chamber\nDynamics', 'lightblue'),
        (-3, 0, 'Cellular\nSignaling', 'lightcoral'),
        (0, 5, 'Physiological\nRhythms', 'lavender')
    ]
    
    for x_start, x_end, label, color in regions:
        ax1.axvspan(x_start, x_end, alpha=0.1, color=color)
        ax1.text((x_start + x_end)/2, len(processes) + 0.5, label, 
                ha='center', va='bottom', fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.6))
    
    # ========== PANEL B: Frequency Spectrum (FIXED) ==========
    ax2 = fig.add_subplot(2, 2, 2)
    
    # Convert timescales to frequencies
    frequencies = 1 / timescales
    log_freqs = np.log10(frequencies)
    
    # Plot as scatter with vertical lines (manual stem plot)
    for i, (log_f, y_pos, color) in enumerate(zip(log_freqs, y_positions, colors)):
        # Vertical line (stem)
        ax2.plot([log_f, log_f], [0, y_pos], color=color, 
                linewidth=2, alpha=0.7)
        # Marker
        ax2.scatter([log_f], [y_pos], s=100, c=[color], 
                   edgecolors='black', linewidth=2, zorder=10)
    
    # Baseline
    ax2.axhline(0, color='black', linewidth=1)
    
    # Add frequency labels for key processes
    key_indices = [1, 8, 9, 10, 11]  # Tunneling, chamber formation, lifetime, resonance, AP
    for idx in key_indices:
        freq_str = f'{frequencies[idx]:.2e} Hz' if frequencies[idx] > 1e6 else f'{frequencies[idx]:.0f} Hz'
        ax2.annotate(freq_str, xy=(log_freqs[idx], y_positions[idx]),
                    xytext=(10, 0), textcoords='offset points',
                    fontsize=8, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', lw=1))
    
    ax2.set_xlabel('log₁₀(Frequency) [Hz]', fontsize=13, fontweight='bold')
    ax2.set_ylabel('Process', fontsize=13, fontweight='bold')
    ax2.set_title('(B) Frequency Domain: Spectral Hierarchy', 
                  fontsize=14, fontweight='bold', pad=15)
    ax2.set_yticks(y_positions)
    ax2.set_yticklabels(processes, fontsize=10)
    ax2.grid(True, alpha=0.3, axis='x')
    ax2.set_xlim(-5, 14)
    ax2.set_ylim(-1, len(processes))
    
    # Add frequency bands
    bands = [
        (0, 3, 'Physiological', 'lavender'),
        (3, 6, 'Cellular', 'lightblue'),
        (6, 9, 'Molecular', 'lightgreen'),
        (9, 14, 'Quantum', 'lightyellow')
    ]
    
    for f_start, f_end, label, color in bands:
        ax2.axvspan(f_start, f_end, alpha=0.1, color=color)
    
    # ========== PANEL C: 3D Timescale-Process-Energy Landscape ==========
    ax3 = fig.add_subplot(2, 2, 3, projection='3d')
    
    # Create parameter space
    log_time_range = np.linspace(-13, 5, 100)
    process_range = np.arange(len(processes))
    
    T_mesh, P_mesh = np.meshgrid(log_time_range, process_range)
    
    # Energy landscape (arbitrary model showing activation energies)
    # E(t, p) = E0 * exp(-|log(t) - log(t_process)|^2)
    E_mesh = np.zeros_like(T_mesh)
    
    for i, (log_t, proc) in enumerate(zip(log_times, processes)):
        E_peak = 10 * (1 + i/len(processes))  # Increasing energy for longer timescales
        width = 1.0
        E_mesh[i, :] = E_peak * np.exp(-((T_mesh[i, :] - log_t)**2) / (2 * width**2))
    
    # Plot surface
    surf = ax3.plot_surface(T_mesh, P_mesh, E_mesh, cmap='plasma', 
                           alpha=0.9, linewidth=0, antialiased=True, shade=True)
    
    # Mark validation points
    validation_indices = [1, 2, 8, 9, 10]  # Key measured timescales
    for idx in validation_indices:
        ax3.scatter([log_times[idx]], [idx], [E_mesh[idx, np.argmin(np.abs(T_mesh[idx, :] - log_times[idx]))]],
                   s=200, c='red', marker='*', edgecolors='black', 
                   linewidth=2, zorder=10)
    
    # Add contour lines
    ax3.contour(T_mesh, P_mesh, E_mesh, levels=10, 
               colors='black', alpha=0.3, linewidths=1)
    
    ax3.set_xlabel('log₁₀(Time) [s]', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Process Index', fontsize=11, fontweight='bold')
    ax3.set_zlabel('Activation Energy (kT)', fontsize=11, fontweight='bold')
    ax3.set_title('(C) Energy Landscape: Multi-Scale Dynamics', 
                  fontsize=14, fontweight='bold', pad=15)
    
    ax3.view_init(elev=25, azim=135)
    
    # Colorbar
    cbar = fig.colorbar(surf, ax=ax3, shrink=0.5, aspect=10, 
                       label='Energy (kT)', pad=0.1)
    cbar.ax.tick_params(labelsize=10)
    
    # Add annotation
    ax3.text2D(0.05, 0.95, 
              'Red stars:\nValidated timescales\nfrom experiments',
              transform=ax3.transAxes, fontsize=10, fontweight='bold',
              verticalalignment='top',
              bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    # ========== PANEL D: Cellular Oscillations ==========
    ax4 = fig.add_subplot(2, 2, 4)
    
    # Generate oscillation waveforms
    t = np.linspace(0, 5, 5000)  # 5 seconds
    
    # Gamma oscillations (40 Hz, from chamber resonance harmonics)
    gamma = np.sin(2 * np.pi * 40 * t) * np.exp(-0.1 * t)
    
    # Cardiac rhythm (1 Hz)
    cardiac = 0.5 * np.sin(2 * np.pi * 1 * t)
    
    # Respiration (0.25 Hz)
    respiration = 0.3 * np.sin(2 * np.pi * 0.25 * t)
    
    # Combined signal
    combined = gamma + cardiac + respiration
    
    # Plot individual components
    ax4.plot(t, gamma + 3, linewidth=1.5, color='#E63946', 
            label='Gamma (40 Hz)', alpha=0.8)
    ax4.plot(t, cardiac + 1.5, linewidth=2, color='#118AB2', 
            label='Cardiac (1 Hz)', alpha=0.8)
    ax4.plot(t, respiration, linewidth=2, color='#06D6A0', 
            label='Respiration (0.25 Hz)', alpha=0.8)
    ax4.plot(t, combined - 1.5, linewidth=2, color='#073B4C', 
            label='Combined signal', alpha=0.9)
    
    # Add horizontal separators
    for y in [2.5, 0.75, -0.75]:
        ax4.axhline(y, color='gray', linestyle='--', linewidth=1, alpha=0.3)
    
    # Mark chamber resonance frequency
    f_chamber = 342  # Hz
    period_chamber = 1 / f_chamber
    n_periods = int(5 / period_chamber)
    
    for i in range(min(n_periods, 50)):  # Limit to 50 marks
        ax4.axvline(i * period_chamber, color='purple', 
                   linestyle=':', linewidth=0.5, alpha=0.3)
    
    ax4.set_xlabel('Time (s)', fontsize=13, fontweight='bold')
    ax4.set_ylabel('Normalized Amplitude', fontsize=13, fontweight='bold')
    ax4.set_title('(D) Physiological Oscillations: Multi-Scale Coherence', 
                  fontsize=14, fontweight='bold', pad=15)
    ax4.legend(fontsize=10, loc='upper right', framealpha=0.95)
    ax4.grid(True, alpha=0.3, axis='x')
    ax4.set_xlim(0, 5)
    ax4.set_ylim(-3, 4)
    
    # Add FFT inset
    ax4_inset = ax4.inset_axes([0.6, 0.05, 0.38, 0.35])
    
    # FFT of combined signal
    fft_vals = np.fft.fft(combined)
    fft_freq = np.fft.fftfreq(len(combined), t[1] - t[0])
    power = np.abs(fft_vals)**2
    
    # Plot positive frequencies
    mask = (fft_freq > 0) & (fft_freq < 50)
    ax4_inset.semilogy(fft_freq[mask], power[mask], 
                      linewidth=2, color='#073B4C')
    
    # Mark peaks
    peak_freqs = [0.25, 1.0, 40.0]
    for pf in peak_freqs:
        idx = np.argmin(np.abs(fft_freq - pf))
        ax4_inset.scatter([fft_freq[idx]], [power[idx]], 
                         s=100, c='red', marker='o', 
                         edgecolors='black', linewidth=1.5, zorder=10)
    
    ax4_inset.set_xlabel('Frequency (Hz)', fontsize=9, fontweight='bold')
    ax4_inset.set_ylabel('Power', fontsize=9, fontweight='bold')
    ax4_inset.set_title('Frequency Spectrum', fontsize=10, fontweight='bold')
    ax4_inset.grid(True, alpha=0.3, which='both')
    ax4_inset.set_xlim(0, 50)
    
    # Add timescale comparison table
    table_data = [
        ['Oscillation', 'Frequency', 'Period', 'Origin'],
        ['Gamma', '40 Hz', '25 ms', 'Chamber resonance'],
        ['Cardiac', '1 Hz', '1 s', 'Pacemaker cells'],
        ['Respiration', '0.25 Hz', '4 s', 'Brainstem'],
        ['Circadian', '11.6 μHz', '24 hr', 'Gene expression']
    ]
    
    table = ax4.table(cellText=table_data, cellLoc='center', loc='upper left',
                     bbox=[0.02, 0.55, 0.55, 0.42],
                     colWidths=[0.15, 0.12, 0.12, 0.16])
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.5)
    
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
            
            # Highlight chamber resonance
            if i == 1:
                table[(i, j)].set_facecolor('#ffeb99')
    
    # Overall title
    fig.suptitle('Figure 8: Integrated Timescale Hierarchy & Physiological Coherence', 
                 fontsize=18, fontweight='bold', y=0.995)
    
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    plt.savefig('figure8_integrated_timescale_hierarchy.png', dpi=300, bbox_inches='tight')
    plt.savefig('figure8_integrated_timescale_hierarchy.pdf', bbox_inches='tight')
    print("✅ Figure 8 saved: figure8_integrated_timescale_hierarchy.png/pdf")
    plt.show()


def main():
    """Main function to generate Figure 8"""
    print("Generating Figure 8: Integrated Timescale Hierarchy...")
    figure8_integrated_timescale_hierarchy()
    print("Done!")


if __name__ == "__main__":
    main()
