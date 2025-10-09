import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import json
from scipy.fft import fft, fftfreq
from scipy.signal import find_peaks, welch
from scipy import stats


def main():
    # Load data using pandas
    with open('oxygen_substrate_data.json', 'r') as f:
        data = json.load(f)

    # Create oscillation DataFrame
    osc_df = pd.DataFrame({
        'time_ns': data['oscillation_pattern']['time_nanoseconds'],
        'amplitude': data['oscillation_pattern']['amplitudes']
    })

    frequency_hz = data['oscillation_pattern']['frequency_hz']

    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: Raw oscillation pattern
    ax1.plot(osc_df['time_ns'], osc_df['amplitude'], 'b-', linewidth=1, alpha=0.8)
    ax1.set_xlabel('Time (ns)')
    ax1.set_ylabel('Paramagnetic Amplitude')
    ax1.set_title(f'Oxygen Paramagnetic Oscillations (f = {frequency_hz:.2e} Hz)')
    ax1.grid(True, alpha=0.3)

    # Add envelope
    peaks, _ = find_peaks(np.abs(osc_df['amplitude']), distance=10)
    if len(peaks) > 0:
        ax1.plot(osc_df['time_ns'].iloc[peaks], osc_df['amplitude'].iloc[peaks],
                 'ro', markersize=3, alpha=0.6, label='Peaks')
        ax1.legend()

    # Plot 2: Frequency domain analysis
    # Perform FFT
    dt = osc_df['time_ns'].iloc[1] - osc_df['time_ns'].iloc[0]  # sampling interval in ns
    sampling_freq = 1 / (dt * 1e-9)  # Convert to Hz

    fft_vals = fft(osc_df['amplitude'])
    fft_freqs = fftfreq(len(osc_df), dt * 1e-9)

    # Only plot positive frequencies
    positive_freq_mask = fft_freqs > 0
    ax2.loglog(fft_freqs[positive_freq_mask], np.abs(fft_vals[positive_freq_mask]),
               'g-', linewidth=2)
    ax2.axvline(frequency_hz, color='red', linestyle='--', linewidth=2,
                label=f'Fundamental: {frequency_hz:.2e} Hz')
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('FFT Magnitude')
    ax2.set_title('Frequency Spectrum of Paramagnetic Oscillations')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Plot 3: Statistical analysis of oscillations
    # Calculate moving statistics
    window_size = 50
    rolling_mean = osc_df['amplitude'].rolling(window=window_size, center=True).mean()
    rolling_std = osc_df['amplitude'].rolling(window=window_size, center=True).std()

    ax3.plot(osc_df['time_ns'], osc_df['amplitude'], 'b-', alpha=0.3, linewidth=0.5, label='Raw Signal')
    ax3.plot(osc_df['time_ns'], rolling_mean, 'r-', linewidth=2, label=f'Moving Mean (n={window_size})')
    ax3.fill_between(osc_df['time_ns'],
                     rolling_mean - 2 * rolling_std,
                     rolling_mean + 2 * rolling_std,
                     alpha=0.2, color='red', label='±2σ Envelope')

    ax3.set_xlabel('Time (ns)')
    ax3.set_ylabel('Amplitude')
    ax3.set_title('Statistical Envelope of Paramagnetic Oscillations')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4: Phase space analysis
    # Create phase space plot (amplitude vs derivative)
    dt_ns = np.diff(osc_df['time_ns']).mean()
    amplitude_derivative = np.gradient(osc_df['amplitude'], dt_ns)

    scatter = ax4.scatter(osc_df['amplitude'], amplitude_derivative,
                          c=osc_df['time_ns'], cmap='viridis', s=10, alpha=0.6)
    ax4.set_xlabel('Amplitude')
    ax4.set_ylabel('dAmplitude/dt')
    ax4.set_title('Phase Space: Paramagnetic Oscillation Dynamics')
    ax4.grid(True, alpha=0.3)

    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax4)
    cbar.set_label('Time (ns)')

    plt.tight_layout()
    plt.savefig('paramagnetic_oscillation_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Print oscillation analysis
    print("Paramagnetic Oscillation Analysis:")
    print("=" * 50)
    print(f"Fundamental Frequency: {frequency_hz:.2e} Hz")
    print(f"Period: {1 / frequency_hz:.2e} seconds")
    print(f"Data Points: {len(osc_df)}")
    print(f"Time Span: {osc_df['time_ns'].max() - osc_df['time_ns'].min():.3f} ns")

    # Statistical properties
    print(f"\nAmplitude Statistics:")
    print(f"Mean: {osc_df['amplitude'].mean():.6f}")
    print(f"Std Dev: {osc_df['amplitude'].std():.6f}")
    print(f"Range: {osc_df['amplitude'].min():.6f} to {osc_df['amplitude'].max():.6f}")
    print(f"Peak-to-Peak: {osc_df['amplitude'].max() - osc_df['amplitude'].min():.6f}")

    # Frequency analysis
    dominant_freq_idx = np.argmax(np.abs(fft_vals[positive_freq_mask]))
    dominant_freq = fft_freqs[positive_freq_mask][dominant_freq_idx]
    print(f"\nDominant Frequency from FFT: {dominant_freq:.2e} Hz")
    print(f"Frequency Match: {abs(dominant_freq - frequency_hz) / frequency_hz * 100:.2f}% deviation")

    # Coherence analysis
    coherence_time = 1 / (2 * np.pi * osc_df['amplitude'].std())
    print(f"Estimated Coherence Time: {coherence_time:.2e} ns")


if __name__ == "__main__":
    main()
