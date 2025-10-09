import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import json
import seaborn as sns


def main():
    # Load data using pandas
    with open('membrane_quantum_resolution_data.json', 'r') as f:
        data = json.load(f)

    # Create results DataFrame
    results_df = pd.DataFrame({
        'accuracy': data['raw_accuracies'],
        'confidence': data['raw_confidences'],
        'molecule': data['test_molecules'],
        'processing_time': data['processing_times_microseconds'],
        'trial': range(len(data['raw_accuracies']))
    })

    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: Molecular recognition heatmap
    # Create pivot table for heatmap
    results_df['trial_group'] = results_df['trial'] // 5  # Group every 5 trials
    pivot_accuracy = results_df.pivot_table(values='accuracy',
                                            index='molecule',
                                            columns='trial_group',
                                            aggfunc='mean')

    sns.heatmap(pivot_accuracy, annot=False, cmap='RdYlBu_r', ax=ax1,
                cbar_kws={'label': 'Accuracy'})
    ax1.set_title('Molecular Recognition Accuracy Heatmap')
    ax1.set_xlabel('Trial Group (×5)')
    ax1.set_ylabel('Molecule Type')

    # Plot 2: Recognition confidence patterns
    molecule_order = results_df.groupby('molecule')['confidence'].mean().sort_values(ascending=False).index

    box_data = [results_df[results_df['molecule'] == mol]['confidence'].values for mol in molecule_order]
    bp = ax2.boxplot(box_data, labels=molecule_order, patch_artist=True)

    colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow', 'lightpink']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)

    ax2.set_xlabel('Molecule Type')
    ax2.set_ylabel('Confidence Score')
    ax2.set_title('Recognition Confidence Distribution by Molecule')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3, axis='y')

    # Plot 3: Processing time patterns
    molecule_stats = results_df.groupby('molecule').agg({
        'processing_time': ['mean', 'std', 'min', 'max']
    })
    molecule_stats.columns = ['mean_time', 'std_time', 'min_time', 'max_time']
    molecule_stats = molecule_stats.sort_values('mean_time')

    x_pos = np.arange(len(molecule_stats))
    bars = ax3.bar(x_pos, molecule_stats['mean_time'] * 1e9,
                   yerr=molecule_stats['std_time'] * 1e9,
                   alpha=0.7, capsize=5, color=colors)

    ax3.set_xlabel('Molecule Type')
    ax3.set_ylabel('Processing Time (ns)')
    ax3.set_title('Average Processing Time by Molecule')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(molecule_stats.index, rotation=45)
    ax3.set_yscale('log')
    ax3.grid(True, alpha=0.3, axis='y')

    # Add value labels
    for bar, time_val in zip(bars, molecule_stats['mean_time'] * 1e9):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width() / 2., height * 1.1,
                 f'{time_val:.1f}', ha='center', va='bottom', fontsize=9)

    # Plot 4: Performance correlation matrix
    # Create correlation data
    corr_data = results_df[['accuracy', 'confidence', 'processing_time']].copy()
    corr_data['processing_time_log'] = np.log10(corr_data['processing_time'])
    corr_data = corr_data.drop('processing_time', axis=1)
    corr_data.columns = ['Accuracy', 'Confidence', 'Log Processing Time']

    correlation_matrix = corr_data.corr()

    # Create correlation heatmap
    mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
    sns.heatmap(correlation_matrix, mask=mask, annot=True, cmap='coolwarm',
                center=0, square=True, ax=ax4, cbar_kws={'label': 'Correlation'})
    ax4.set_title('Performance Metrics Correlation')

    plt.tight_layout()
    plt.savefig('molecular_recognition_patterns.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Print molecular analysis
    print("Molecular Recognition Analysis:")
    print("=" * 50)

    # Overall molecule performance
    molecule_performance = results_df.groupby('molecule').agg({
        'accuracy': ['mean', 'std'],
        'confidence': ['mean', 'std'],
        'processing_time': ['mean', 'std']
    }).round(4)

    print("\nMolecule Performance Summary:")
    for molecule in molecule_performance.index:
        acc_mean = molecule_performance.loc[molecule, ('accuracy', 'mean')]
        acc_std = molecule_performance.loc[molecule, ('accuracy', 'std')]
        conf_mean = molecule_performance.loc[molecule, ('confidence', 'mean')]
        time_mean = molecule_performance.loc[molecule, ('processing_time', 'mean')]

        print(f"{molecule.capitalize():10}: Acc={acc_mean:.3f}±{acc_std:.3f}, "
              f"Conf={conf_mean:.3f}, Time={time_mean:.2e}μs")

    # Best and worst performing molecules
    best_molecule = molecule_performance[('accuracy', 'mean')].idxmax()
    worst_molecule = molecule_performance[('accuracy', 'mean')].idxmin()

    print(f"\nBest Recognition: {best_molecule.capitalize()}")
    print(f"Worst Recognition: {worst_molecule.capitalize()}")


if __name__ == "__main__":
    main()
