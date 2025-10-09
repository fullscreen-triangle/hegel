import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import json


def main():
    # Load data using pandas
    with open('oxygen_substrate_data.json', 'r') as f:
        data = json.load(f)

    # Create enhancement DataFrame
    enhancement_df = pd.DataFrame({
        'molecule_count': data['enhancement_comparison']['molecule_counts'],
        'with_oxygen': data['enhancement_comparison']['with_oxygen_capacity'],
        'without_oxygen': data['enhancement_comparison']['without_oxygen_capacity'],
        'enhancement_factor': data['enhancement_comparison']['enhancement_factor']
    })

    # Clean data - remove any invalid values
    enhancement_df = enhancement_df.replace([np.inf, -np.inf], np.nan).dropna()

    print(f"Data loaded: {len(enhancement_df)} valid data points")
    print(
        f"Enhancement factor range: {enhancement_df['enhancement_factor'].min():.2f} to {enhancement_df['enhancement_factor'].max():.2f}")

    # Create figure with subplots - adjust figure size to prevent layout issues
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

    # Plot 1: Capacity comparison (with vs without oxygen)
    ax1.loglog(enhancement_df['molecule_count'], enhancement_df['with_oxygen'],
               'g-', linewidth=3, marker='o', markersize=4, label='With Oxygen Substrate')
    ax1.loglog(enhancement_df['molecule_count'], enhancement_df['without_oxygen'],
               'r-', linewidth=3, marker='s', markersize=4, label='Without Oxygen (Diffusion)')

    ax1.set_xlabel('Molecule Count')
    ax1.set_ylabel('Information Processing Capacity')
    ax1.set_title('Oxygen Substrate vs Diffusion-Based Processing')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Add enhancement factor annotation
    avg_enhancement = enhancement_df['enhancement_factor'].mean()
    ax1.text(0.05, 0.95, f'Average Enhancement:\n{avg_enhancement:.0f}x',
             transform=ax1.transAxes, bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8),
             verticalalignment='top', fontsize=10, fontweight='bold')

    # Plot 2: Enhancement factor consistency
    ax2.semilogx(enhancement_df['molecule_count'], enhancement_df['enhancement_factor'],
                 'purple', linewidth=3, marker='d', markersize=6)

    mean_enhancement = enhancement_df['enhancement_factor'].mean()
    std_enhancement = enhancement_df['enhancement_factor'].std()

    # Handle case where std might be 0 or very small
    if std_enhancement > 0:
        ax2.axhline(mean_enhancement, color='red', linestyle='--', linewidth=2,
                    label=f'Mean: {mean_enhancement:.0f}x')
        ax2.fill_between(enhancement_df['molecule_count'],
                         mean_enhancement - std_enhancement,
                         mean_enhancement + std_enhancement,
                         alpha=0.2, color='red', label=f'±1σ: {std_enhancement:.1f}')

        y_min = max(0, mean_enhancement - 3 * std_enhancement)
        y_max = mean_enhancement + 3 * std_enhancement
    else:
        ax2.axhline(mean_enhancement, color='red', linestyle='--', linewidth=2,
                    label=f'Mean: {mean_enhancement:.0f}x')
        y_min = mean_enhancement * 0.9
        y_max = mean_enhancement * 1.1

    ax2.set_xlabel('Molecule Count')
    ax2.set_ylabel('Enhancement Factor')
    ax2.set_title('Oxygen Enhancement Factor Consistency')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(y_min, y_max)

    # Plot 3: Relative advantage visualization
    capacity_ratio = enhancement_df['with_oxygen'] / enhancement_df['without_oxygen']

    # Limit the number of bars to prevent overcrowding
    n_bars = min(20, len(enhancement_df))
    indices = np.linspace(0, len(enhancement_df) - 1, n_bars, dtype=int)

    bars = ax3.bar(range(n_bars), capacity_ratio.iloc[indices],
                   color=plt.cm.viridis(np.linspace(0, 1, n_bars)),
                   alpha=0.8, edgecolor='black', width=0.8)

    ax3.set_xlabel('Sample Index')
    ax3.set_ylabel('Capacity Ratio (With/Without O₂)')
    ax3.set_title('Oxygen Advantage Across Molecular Scales')
    ax3.set_yscale('log')
    ax3.grid(True, alpha=0.3, axis='y')

    # Add value labels on selected bars
    for i, (bar, ratio) in enumerate(zip(bars, capacity_ratio.iloc[indices])):
        if i % 5 == 0:  # Label every 5th bar to avoid crowding
            height = bar.get_height()
            if height > 0:  # Only label positive values
                ax3.text(bar.get_x() + bar.get_width() / 2., height * 1.1,
                         f'{ratio:.0f}x', ha='center', va='bottom', fontsize=8)

    # Plot 4: Enhancement factor analysis - robust version
    enhancement_values = enhancement_df['enhancement_factor'].values
    unique_values = np.unique(enhancement_values)

    print(f"Unique enhancement factor values: {len(unique_values)}")
    print(f"Enhancement factors: {unique_values}")

    if len(unique_values) == 1:
        # All values are the same - show as a single bar
        ax4.bar([0], [1], width=0.5, alpha=0.7, color='blue', edgecolor='black')
        ax4.set_xlim(-1, 1)
        ax4.set_xlabel('Enhancement Factor')
        ax4.set_ylabel('Frequency')
        ax4.set_title(f'Enhancement Factor: Constant at {unique_values[0]:.0f}x')
        ax4.text(0, 0.5, f'{unique_values[0]:.0f}x\n(100% of data)',
                 ha='center', va='center', fontweight='bold', fontsize=12)
        ax4.set_xticks([0])
        ax4.set_xticklabels([f'{unique_values[0]:.0f}x'])

    elif len(unique_values) <= 5:
        # Few unique values - show as bar chart
        value_counts = pd.Series(enhancement_values).value_counts().sort_index()
        bars = ax4.bar(range(len(value_counts)), value_counts.values,
                       alpha=0.7, color='blue', edgecolor='black')
        ax4.set_xlabel('Enhancement Factor')
        ax4.set_ylabel('Frequency')
        ax4.set_title('Enhancement Factor Distribution')
        ax4.set_xticks(range(len(value_counts)))
        ax4.set_xticklabels([f'{val:.0f}x' for val in value_counts.index])

        # Add value labels on bars
        for bar, count in zip(bars, value_counts.values):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width() / 2., height + 0.1,
                     f'{count}', ha='center', va='bottom', fontweight='bold')

    else:
        # Many unique values - use adaptive binning
        data_range = enhancement_values.max() - enhancement_values.min()
        if data_range > 0:
            # Calculate appropriate number of bins
            n_bins = min(15, max(3, int(np.sqrt(len(enhancement_values)))))
            try:
                ax4.hist(enhancement_values, bins=n_bins, alpha=0.7, color='blue',
                         edgecolor='black', density=True)
            except ValueError:
                # If still fails, use explicit bin edges
                bin_edges = np.linspace(enhancement_values.min(),
                                        enhancement_values.max(), n_bins + 1)
                ax4.hist(enhancement_values, bins=bin_edges, alpha=0.7, color='blue',
                         edgecolor='black', density=True)
        else:
            # All values are the same (shouldn't happen due to earlier check)
            ax4.bar([0], [1], width=0.5, alpha=0.7, color='blue', edgecolor='black')
            ax4.set_xlim(-1, 1)

        # Add statistics
        mean_val = enhancement_df['enhancement_factor'].mean()
        median_val = enhancement_df['enhancement_factor'].median()

        ax4.axvline(mean_val, color='red', linestyle='--', linewidth=2,
                    label=f'Mean: {mean_val:.0f}x')
        ax4.axvline(median_val, color='orange', linestyle='--', linewidth=2,
                    label=f'Median: {median_val:.0f}x')

        ax4.set_xlabel('Enhancement Factor')
        ax4.set_ylabel('Probability Density')
        ax4.set_title('Enhancement Factor Distribution')
        ax4.legend()

    ax4.grid(True, alpha=0.3)

    # Adjust layout with more space
    plt.subplots_adjust(left=0.1, bottom=0.1, right=0.95, top=0.95, wspace=0.3, hspace=0.4)

    # Save with error handling
    try:
        plt.savefig('enhancement_factor_analysis.png', dpi=300, bbox_inches='tight')
        print("Plot saved successfully!")
    except Exception as e:
        print(f"Error saving plot: {e}")
        plt.savefig('enhancement_factor_analysis.png', dpi=150)  # Lower DPI fallback

    plt.show()

    # Print enhancement analysis
    print("\nOxygen Enhancement Analysis:")
    print("=" * 50)
    print(f"Data points: {len(enhancement_df)}")
    print(f"Average Enhancement Factor: {avg_enhancement:.0f}x")

    if std_enhancement > 0:
        print(f"Enhancement Consistency: σ = {std_enhancement:.2f}")
        print(f"Coefficient of Variation: {(std_enhancement / avg_enhancement) * 100:.2f}%")
    else:
        print("Enhancement Factor is constant across all measurements")

    # Scale analysis
    print(f"\nScale Analysis:")
    print(
        f"Molecule Count Range: {enhancement_df['molecule_count'].min():.2e} to {enhancement_df['molecule_count'].max():.2e}")
    print(
        f"Capacity Range (with O₂): {enhancement_df['with_oxygen'].min():.2e} to {enhancement_df['with_oxygen'].max():.2e}")
    print(
        f"Capacity Range (without O₂): {enhancement_df['without_oxygen'].min():.2e} to {enhancement_df['without_oxygen'].max():.2e}")

    # Practical implications
    smallest_enhancement = enhancement_df['enhancement_factor'].min()
    largest_enhancement = enhancement_df['enhancement_factor'].max()
    print(f"\nPractical Impact:")
    print(f"Minimum Enhancement: {smallest_enhancement:.0f}x faster than diffusion")
    print(f"Maximum Enhancement: {largest_enhancement:.0f}x faster than diffusion")

    if avg_enhancement > 0:
        variation = ((largest_enhancement - smallest_enhancement) / avg_enhancement) * 100
        print(f"Consistency: {variation:.1f}% variation around mean")


if __name__ == "__main__":
    main()
