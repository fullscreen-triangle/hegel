import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
import json

def figure5_o2_oscillator_array():
    """
    Figure 5: O₂ Oscillator Array
    (A) Phase distribution (120k molecules)
    (B) Coherence time decay
    (C) 3D spatial distribution in cell
    (D) Frequency spectrum (FFT)
    """
    # Set style
    plt.style.use('seaborn-v0_8-paper')
    sns.set_palette("husl")
    
    # Create figure
    fig = plt.figure(figsize=(16, 14))
    
    # Load or generate O2 data
    n_o2 = 120442
    concentration = 0.0002  # M (200 μM)
    cell_volume = 1e-15  # m³ (1 fL)
    oscillation_freq = 1000.0  # Hz
    
    # Generate phase data (uniform distribution)
    np.random.seed(42)
    phases = np.random.uniform(0, 2*np.pi, n_o2)
    
    # O2 parameters from validation
    coherence_time = 20e-6  # s (20 μs)
    jitter_fraction = 0.05
    period_mean = 1e-6  # s (1 μs, corresponding to 1 MHz)
    
    # ========== PANEL A: Phase Distribution ==========
    ax1 = fig.add_subplot(2, 2, 1)
    
    # Histogram
    bins = np.linspace(0, 2*np.pi, 50)
    counts, edges = np.histogram(phases, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2
    
    # Plot as polar histogram
    ax1_polar = plt.subplot(2, 2, 1, projection='polar')
    width = 2*np.pi / len(centers)
    bars = ax1_polar.bar(centers, counts, width=width, 
                         color='#2E86AB', alpha=0.7, edgecolor='black', linewidth=1)
    
    # Color bars by phase
    for bar, center in zip(bars, centers):
        bar.set_facecolor(cm.hsv(center / (2*np.pi)))
        bar.set_alpha(0.8)
    
    ax1_polar.set_theta_zero_location('N')
    ax1_polar.set_theta_direction(-1)
    ax1_polar.set_title('(A) Phase Distribution: 120,442 O₂ Molecules\n(Uniform Distribution)', 
                       fontsize=14, fontweight='bold', pad=20)
    ax1_polar.set_ylim(0, counts.max() * 1.1)
    
    # Add statistics
    phase_mean = np.mean(phases)
    phase_std = np.std(phases)
    uniformity = 1 - (phase_std / (2*np.pi / np.sqrt(12)))  # Deviation from uniform
    
    ax1_polar.text(0.5, 0.95, 
                  f'N = {n_o2:,}\n'
                  f'Mean: {phase_mean:.2f} rad\n'
                  f'Std: {phase_std:.2f} rad\n'
                  f'Uniformity: {uniformity:.3f}',
                  transform=ax1_polar.transAxes, fontsize=10, fontweight='bold',
                  verticalalignment='top', horizontalalignment='center',
                  bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    # ========== PANEL B: Coherence Time Decay ==========
    ax2 = fig.add_subplot(2, 2, 2)
    
    # Time array
    t = np.linspace(0, 100e-6, 1000)  # 0 to 100 μs
    
    # Coherence function (exponential decay)
    coherence = np.exp(-t / coherence_time)
    
    # Add noise/dephasing
    coherence_with_jitter = coherence * (1 - jitter_fraction * (1 - np.exp(-t / (coherence_time / 5))))
    
    # Plot
    ax2.plot(t * 1e6, coherence, linewidth=3, color='#2E86AB', 
            label='Ideal coherence', linestyle='--', alpha=0.7)
    ax2.plot(t * 1e6, coherence_with_jitter, linewidth=3, color='#E63946', 
            label=f'With jitter ({jitter_fraction*100:.0f}%)')
    
    # Mark coherence time
    ax2.axvline(coherence_time * 1e6, color='green', linestyle='--', linewidth=2, 
               label=f'τ_coherence = {coherence_time*1e6:.0f} μs')
    ax2.axhline(1/np.e, color='gray', linestyle=':', linewidth=2, 
               label='1/e threshold', alpha=0.7)
    
    # Mark chamber lifetime
    tau_chamber = 523e-6
    ax2.axvline(tau_chamber * 1e6, color='purple', linestyle='-', linewidth=2.5, 
               label=f'Chamber lifetime = {tau_chamber*1e6:.0f} μs', alpha=0.7)
    
    # Shade averaging window
    n_cycles = tau_chamber / coherence_time
    ax2.axvspan(0, coherence_time * 1e6, alpha=0.2, color='yellow', 
               label=f'{n_cycles:.0f} cycles per chamber')
    
    ax2.set_xlabel('Time (μs)', fontsize=13, fontweight='bold')
    ax2.set_ylabel('Coherence Function', fontsize=13, fontweight='bold')
    ax2.set_title('(B) Temporal Coherence: 26 Cycles per Chamber', 
                  fontsize=14, fontweight='bold', pad=15)
    ax2.legend(fontsize=10, loc='upper right', framealpha=0.95)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, 1.1)
    
    # Add SNR calculation
    SNR = np.sqrt(n_cycles)
    ax2.text(0.05, 0.05, 
            f'Signal averaging:\n'
            f'SNR improvement = √{n_cycles:.0f} = {SNR:.1f}×',
            transform=ax2.transAxes, fontsize=11, fontweight='bold',
            verticalalignment='bottom',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
    
    # ========== PANEL C: 3D Spatial Distribution ==========
    ax3 = fig.add_subplot(2, 2, 3, projection='3d')
    
    # Generate 3D positions (random in cytoplasm)
    R_cell = 10e-6
    R_nucleus = 5e-6
    
    # Sample positions (subset for visualization)
    n_plot = 5000
    positions = []
    
    while len(positions) < n_plot:
        # Random position in sphere
        r = np.random.uniform(0, R_cell, 1)[0]
        theta = np.random.uniform(0, np.pi, 1)[0]
        phi = np.random.uniform(0, 2*np.pi, 1)[0]
        
        x = r * np.sin(theta) * np.cos(phi)
        y = r * np.sin(theta) * np.sin(phi)
        z = r * np.cos(theta)
        
        # Check if in cytoplasm (not nucleus)
        r_check = np.sqrt(x**2 + y**2 + z**2)
        if r_check > R_nucleus and r_check <= R_cell:
            positions.append([x, y, z])
    
    positions = np.array(positions)
    
    # Assign phases (subset from full array)
    phases_subset = phases[:n_plot]
    
    # Plot O2 molecules colored by phase
    scatter = ax3.scatter(positions[:, 0] * 1e6, 
                         positions[:, 1] * 1e6, 
                         positions[:, 2] * 1e6,
                         c=phases_subset, cmap='hsv', 
                         s=5, alpha=0.6, edgecolors='none')
    
    # Add cell boundary (wireframe sphere)
    u = np.linspace(0, 2 * np.pi, 30)
    v = np.linspace(0, np.pi, 20)
    x_cell = R_cell * np.outer(np.cos(u), np.sin(v))
    y_cell = R_cell * np.outer(np.sin(u), np.sin(v))
    z_cell = R_cell * np.outer(np.ones(np.size(u)), np.cos(v))
    ax3.plot_wireframe(x_cell * 1e6, y_cell * 1e6, z_cell * 1e6, 
                      color='black', alpha=0.2, linewidth=0.5)
    
    # Add nuclear boundary
    x_nuc = R_nucleus * np.outer(np.cos(u), np.sin(v))
    y_nuc = R_nucleus * np.outer(np.sin(u), np.sin(v))
    z_nuc = R_nucleus * np.outer(np.ones(np.size(u)), np.cos(v))
    ax3.plot_wireframe(x_nuc * 1e6, y_nuc * 1e6, z_nuc * 1e6, 
                      color='gray', alpha=0.3, linewidth=0.5)
    
    ax3.set_xlabel('X (μm)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Y (μm)', fontsize=11, fontweight='bold')
    ax3.set_zlabel('Z (μm)', fontsize=11, fontweight='bold')
    ax3.set_title('(C) 3D Spatial Distribution: Cytoplasmic O₂ Array', 
                  fontsize=14, fontweight='bold', pad=15)
    
    # Set equal aspect ratio
    max_range = R_cell * 1e6
    ax3.set_xlim(-max_range, max_range)
    ax3.set_ylim(-max_range, max_range)
    ax3.set_zlim(-max_range, max_range)
    
    ax3.view_init(elev=20, azim=45)
    
    # Colorbar
    cbar = fig.colorbar(scatter, ax=ax3, shrink=0.5, aspect=10, 
                       label='Phase (rad)', pad=0.1, ticks=[0, np.pi, 2*np.pi])
    cbar.ax.set_yticklabels(['0', 'π', '2π'])
    
    # Add density annotation
    density = n_o2 / (cell_volume * 1e18)  # molecules/μm³
    ax3.text2D(0.05, 0.95, 
              f'Density: {density:.0f} molecules/μm³\n'
              f'Total: {n_o2:,} molecules\n'
              f'Volume: {cell_volume*1e18:.1f} μm³',
              transform=ax3.transAxes, fontsize=10, fontweight='bold',
              verticalalignment='top',
              bbox=dict(boxstyle='round', facecolor='lightcyan', alpha=0.8))
    
    # ========== PANEL D: Frequency Spectrum ==========
    ax4 = fig.add_subplot(2, 2, 4)
    
    # Generate time series
    dt = 1e-9  # 1 ns sampling
    duration = 1e-3  # 1 ms
    t_series = np.arange(0, duration, dt)
    
    # Oscillation signal (sum of all O2 molecules with phases)
    # Use subset for computational efficiency
    n_fft = 10000
    phases_fft = phases[:n_fft]
    
    # Signal: sum of cosines with different phases
    signal = np.zeros(len(t_series))
    for i, phase in enumerate(phases_fft[:100]):  # Use first 100 for speed
        signal += np.cos(2 * np.pi * oscillation_freq * t_series + phase)
    
    # Add noise
    signal += np.random.normal(0, 0.1 * np.std(signal), len(signal))
    
    # FFT
    fft_vals = np.fft.fft(signal)
    fft_freq = np.fft.fftfreq(len(signal), dt)
    
    # Power spectrum
    power = np.abs(fft_vals)**2
    
    # Plot positive frequencies only
    mask_pos = fft_freq > 0
    freq_pos = fft_freq[mask_pos]
    power_pos = power[mask_pos]
    
    # Plot
    ax4.semilogy(freq_pos / 1e3, power_pos, linewidth=2, color='#2E86AB', alpha=0.7)
    
    # Mark oscillation frequency
    ax4.axvline(oscillation_freq / 1e3, color='red', linestyle='--', linewidth=3, 
               label=f'Oscillation: {oscillation_freq/1e3:.0f} kHz')
    
    # Mark harmonics
    for n in range(2, 5):
        ax4.axvline(n * oscillation_freq / 1e3, color='orange', 
                   linestyle=':', linewidth=2, alpha=0.7,
                   label=f'{n}× harmonic' if n == 2 else '')
    
    # Mark chamber frequency
    f_chamber = 1 / (523e-6)
    ax4.axvline(f_chamber / 1e3, color='purple', linestyle='-', linewidth=2.5, 
               label=f'Chamber: {f_chamber:.0f} Hz', alpha=0.7)
    
    ax4.set_xlabel('Frequency (kHz)', fontsize=13, fontweight='bold')
    ax4.set_ylabel('Power Spectral Density', fontsize=13, fontweight='bold')
    ax4.set_title('(D) Frequency Spectrum: Coherent Oscillations', 
                  fontsize=14, fontweight='bold', pad=15)
    ax4.legend(fontsize=10, loc='upper right', framealpha=0.95)
    ax4.grid(True, alpha=0.3, which='both')
    ax4.set_xlim(0, 5)
    
    # Add peak annotation
    peak_idx = np.argmax(power_pos[freq_pos < 5000])
    peak_freq = freq_pos[peak_idx]
    peak_power = power_pos[peak_idx]
    
    ax4.annotate(f'Peak: {peak_freq:.0f} Hz\nPower: {peak_power:.2e}',
                xy=(peak_freq / 1e3, peak_power), xytext=(20, 20),
                textcoords='offset points', fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.3', lw=2))
    
    # Overall title
    fig.suptitle('Figure 5: O₂ Oscillator Array as Distributed Field Sensor', 
                 fontsize=18, fontweight='bold', y=0.995)
    
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    plt.savefig('figure5_o2_oscillator_array.png', dpi=300, bbox_inches='tight')
    plt.savefig('figure5_o2_oscillator_array.pdf', bbox_inches='tight')
    print("✅ Figure 5 saved: figure5_o2_oscillator_array.png/pdf")
    plt.show()


def main():
    """Main function to generate Figure 5"""
    print("Generating Figure 5: O₂ Oscillator Array...")
    figure5_o2_oscillator_array()
    print("Done!")


if __name__ == "__main__":
    main()
