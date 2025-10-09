import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import json
from scipy import signal
from sklearn.preprocessing import StandardScaler


def main():
    # Load data using pandas
    with open('membrane_quantum_resolution_data.json', 'r') as f:
        data = json.load(f)

    # Create results DataFrame with trial sequence
    results_df = pd.DataFrame({
        'trial': range(len(data['raw_accuracies'])),
        'accuracy': data['raw_accuracies'],
        'confidence': data['raw_confidences'],
        'molecule': data['test_molecules'],
        'processing_time': data['processing_times_microseconds']
    })

    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: Time series of accuracy with trend
    ax1.plot(results_df['trial'], results_df['accuracy'], 'b-', alpha=0.6, linewidth=1)

    # Add rolling average
    window_size = 10
    rolling_mean = results_df['accuracy'].rolling(window=window_size, center=True).mean()
    ax1.plot(results_df['trial'], rolling_mean, 'r-', linewidth=2,
             label=f'{window_size}-trial moving average')

    # Add overall trend line
    z = np.polyfit(results_df['trial'], results_df['accuracy'], 1)
    p = np.poly1d(z)
    ax1.plot(results_df['trial'], p(results_df['trial']), 'g--', linewidth=2,
             label=f'Trend (slope: {z[0]:.2e})')

    ax1.set_xlabel('Trial Number')
    ax1.set_ylabel('Accuracy')
    ax1.set_title('Accuracy Time Series with Trend Analysis')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Processing time evolution
    # Normalize processing times and apply smoothing
    scaler = StandardScaler()
    normalized_times = scaler.fit_transform(results_df[['processing_time']]).flatten()

    ax2.scatter(results_df['trial'], results_df['processing_time'],
                c=results_df['accuracy'], cmap='viridis', alpha=0.6, s=30)

    # Add smoothed trend
    smoothed_times = signal.savgol_filter(results_df['processing_time'],
                                          window_length=min(21, len(results_df) // 2 * 2 + 1),
                                          polyorder=3)
    ax2.plot(results_df['trial'], smoothed_times, 'r-', linewidth=2,
             label='Smoothed trend')

    ax2.set_xlabel('Trial Number')
    ax2.set_ylabel('Processing Time (μs)')
    ax2.set_title('Processing Time Evolution (colored by accuracy)')
    ax2.set_yscale('log')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Add colorbar
    scatter = ax2.collections[0]
    plt.colorbar(scatter, ax=ax2, label='Accuracy')

    # Plot 3: Molecular sequence analysis
    # Create molecular sequence pattern
    molecule_map = {mol: i for i, mol in enumerate(results_df['molecule'].unique())}
    results_df['molecule_code'] = results_df['molecule'].map(molecule_map)

    # Plot molecular sequence
    ax3.plot(results_df['trial'], results_df['molecule_code'], 'ko-', markersize=4, alpha=0.7)

    # Color code by performance
    for mol, code in molecule_map.items():
        mol_trials = results_df[results_df['molecule'] == mol]['trial']
        mol_accuracy = results_df[results_df['molecule'] == mol]['accuracy']
        ax3.scatter(mol_trials, [code] * len(mol_trials),
                    c=mol_accuracy, cmap='RdYlGn', s=50, alpha=0.8)

    ax3.set_xlabel('Trial Number')
    ax3.set_ylabel('Molecule Type')
    ax3.set_title('Molecular Test Sequence (colored by accuracy)')
    ax3.set_yticks(list(molecule_map.values()))
    ax3.set_yticklabels(list(molecule_map.keys()))
    ax3.grid(True, alpha=0.3)

    # Plot 4: Performance stability analysis
    # Calculate rolling statistics
    window_sizes = [5, 10, 15, 20]
    colors = ['blue', 'green', 'orange', 'red']

    for window, color in zip(window_sizes, colors):
        if window <= len(results_df):
            rolling_std = results_df['accuracy'].rolling(window=window, center=True).std()
            ax4.plot(results_df['trial'], rolling_std, color=color, linewidth=2,
                     label=f'{window}-trial window', alpha=0.7)

    ax4.set_xlabel('Trial Number')
    ax4.set_ylabel('Accuracy Standard Deviation')
    ax4.set_title('Performance Stability Analysis')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    # Add stability zones
    ax4.axhline(y=0.01, color='green', linestyle=':', alpha=0.5, label='High Stability')
    ax4.axhline(y=0.02, color='orange', linestyle=':', alpha=0.5, label='Medium Stability')
    ax4.axhline(y=0.03, color='red', linestyle=':', alpha=0.5, label='Low Stability')

    plt.tight_layout()
    plt.savefig('time_series_trend_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Print trend analysis
    print("Time Series Analysis:")
    print("=" * 50)

    # Calculate trend statistics
    accuracy_trend = np.polyfit(results_df['trial'], results_df['accuracy'], 1)[0]
    time_trend = np.polyfit(results_df['trial'], np.log10(results_df['processing_time']), 1)[0]

    print(f"Accuracy Trend: {accuracy_trend:.2e} per trial")
    print(f"Processing Time Trend: {time_trend:.2e} log(μs) per trial")

    # Performance stability
    overall_std = results_df['accuracy'].std()
    recent_std = results_df['accuracy'].tail(20).std()

    print(f"Overall Accuracy Stability: σ = {overall_std:.4f}")
    print(f"Recent Accuracy Stability (last 20): σ = {recent_std:.4f}")

    stability_change = (recent_std - overall_std) / overall_std * 100
    print(f"Stability Change: {stability_change:+.1f}%")

    # Molecular sequence analysis
    molecule_switches = (results_df['molecule'] != results_df['molecule'].shift()).sum() - 1
    print(f"Molecular Switches: {molecule_switches}")
    print(f"Average Trials per Molecule: {len(results_df) / len(results_df['molecule'].unique()):.1f}")


if __name__ == "__main__":
    main()
