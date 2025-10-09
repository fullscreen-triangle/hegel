import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import json
from scipy import stats


def main():
    # Load data using pandas
    with open('membrane_quantum_resolution_data.json', 'r') as f:
        data = json.load(f)

    # Create main DataFrame
    results_df = pd.DataFrame({
        'accuracy': data['raw_accuracies'],
        'confidence': data['raw_confidences'],
        'molecule': data['test_molecules'],
        'processing_time': data['processing_times_microseconds']
    })

    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

    # Plot 1: Accuracy distribution
    ax1.hist(results_df['accuracy'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    ax1.axvline(results_df['accuracy'].mean(), color='red', linestyle='--', linewidth=2,
                label=f'Mean: {results_df["accuracy"].mean():.4f}')
    ax1.axvline(results_df['accuracy'].median(), color='orange', linestyle='--', linewidth=2,
                label=f'Median: {results_df["accuracy"].median():.4f}')
    ax1.set_xlabel('Accuracy')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Accuracy Distribution')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Accuracy vs Confidence scatter
    scatter = ax2.scatter(results_df['confidence'], results_df['accuracy'],
                          c=results_df['processing_time'], cmap='viridis', alpha=0.6)
    ax2.set_xlabel('Confidence')
    ax2.set_ylabel('Accuracy')
    ax2.set_title('Accuracy vs Confidence (colored by processing time)')
    plt.colorbar(scatter, ax=ax2, label='Processing Time (μs)')

    # Add correlation line
    slope, intercept, r_value, p_value, std_err = stats.linregress(results_df['confidence'], results_df['accuracy'])
    line = slope * results_df['confidence'] + intercept
    ax2.plot(results_df['confidence'], line, 'r--', alpha=0.8,
             label=f'R² = {r_value ** 2:.3f}')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Plot 3: Performance by molecule type
    molecule_stats = results_df.groupby('molecule').agg({
        'accuracy': ['mean', 'std'],
        'confidence': 'mean',
        'processing_time': 'mean'
    }).round(4)

    molecule_stats.columns = ['accuracy_mean', 'accuracy_std', 'confidence_mean', 'processing_time_mean']

    x_pos = np.arange(len(molecule_stats))
    bars = ax3.bar(x_pos, molecule_stats['accuracy_mean'],
                   yerr=molecule_stats['accuracy_std'],
                   alpha=0.7, capsize=5, color=['red', 'blue', 'green', 'orange', 'purple'])
    ax3.set_xlabel('Molecule Type')
    ax3.set_ylabel('Mean Accuracy')
    ax3.set_title('Accuracy by Molecule Type')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(molecule_stats.index, rotation=45)
    ax3.grid(True, alpha=0.3, axis='y')

    # Add value labels on bars
    for bar, acc, std in zip(bars, molecule_stats['accuracy_mean'], molecule_stats['accuracy_std']):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width() / 2., height + std + 0.001,
                 f'{acc:.3f}', ha='center', va='bottom', fontsize=9)

    # Plot 4: Processing time distribution (log scale)
    ax4.hist(np.log10(results_df['processing_time']), bins=25, alpha=0.7,
             color='lightcoral', edgecolor='black')
    ax4.set_xlabel('Log₁₀(Processing Time) [μs]')
    ax4.set_ylabel('Frequency')
    ax4.set_title('Processing Time Distribution (Log Scale)')
    ax4.grid(True, alpha=0.3)

    # Add statistics text
    mean_time = results_df['processing_time'].mean()
    median_time = results_df['processing_time'].median()
    ax4.text(0.05, 0.95, f'Mean: {mean_time:.2e} μs\nMedian: {median_time:.2e} μs',
             transform=ax4.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    plt.savefig('accuracy_performance_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Print summary statistics
    print("Performance Analysis Summary:")
    print("=" * 50)
    print(f"Overall Success Rate: {data['success_rate']:.1%}")
    print(f"Mean Accuracy: {results_df['accuracy'].mean():.4f} ± {results_df['accuracy'].std():.4f}")
    print(f"Mean Confidence: {results_df['confidence'].mean():.4f} ± {results_df['confidence'].std():.4f}")
    print(f"Mean Processing Time: {results_df['processing_time'].mean():.2e} μs")
    print(f"Accuracy-Confidence Correlation: {r_value:.3f} (p={p_value:.3e})")

    print("\nMolecule-specific Performance:")
    print(molecule_stats)


if __name__ == "__main__":
    main()
