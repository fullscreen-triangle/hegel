import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json


def main():
    # Load data using pandas
    with open('electron_cascade_data.json', 'r') as f:
        data = json.load(f)

    # Extract validation results and metadata
    validation_df = pd.DataFrame([data['validation_results']]).T
    validation_df.columns = ['result']
    validation_df['status'] = validation_df['result'].apply(lambda x: str(x).lower() == 'true')

    metadata = data['metadata']

    # Create summary figure
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

    # Plot 1: Validation results summary
    labels = ['Quantum Speed\nAchieved', 'Speed Advantage\nConfirmed',
              'Energy\nEfficient', 'Network Coverage\nFast']
    colors = ['green' if status else 'red' for status in validation_df['status']]

    bars = ax1.bar(labels, [1] * len(labels), color=colors, alpha=0.7, edgecolor='black')
    ax1.set_ylabel('Validation Status')
    ax1.set_title('Validation Results Summary')
    ax1.set_ylim(0, 1.2)
    ax1.set_yticks([0, 1])
    ax1.set_yticklabels(['Failed', 'Passed'])

    # Add result labels
    for bar, result in zip(bars, validation_df['result']):
        ax1.text(bar.get_x() + bar.get_width() / 2., 0.5,
                 str(result), ha='center', va='center', fontweight='bold', color='white')

    # Plot 2: Claims validated
    claims = metadata['claims_validated']
    claims_df = pd.DataFrame({'claim': claims, 'validated': [1] * len(claims)})

    ax2.barh(range(len(claims)), claims_df['validated'],
             color='lightblue', alpha=0.7, edgecolor='black')
    ax2.set_yticks(range(len(claims)))
    ax2.set_yticklabels(claims)
    ax2.set_xlabel('Validation Status')
    ax2.set_title('Claims Validated')
    ax2.set_xlim(0, 1.2)

    # Plot 3: Performance metrics summary
    max_speed_advantage = max(data['speed_comparison']['speed_advantage'])
    min_energy_ratio = min(data['energy_efficiency']['efficiency_advantage'])
    max_comm_advantage = max(data['communication_systems']['cascade_advantage'])
    network_connectivity = data['network_topology']['connectivity']

    metrics_df = pd.DataFrame({
        'metric': ['Speed\nAdvantage', 'Energy\nEfficiency', 'Communication\nAdvantage', 'Network\nConnectivity'],
        'value': [max_speed_advantage, min_energy_ratio, max_comm_advantage, network_connectivity]
    })
    metrics_df['log_value'] = metrics_df['value'].apply(lambda x: np.log10(x) if x > 0 else 0)

    bars = ax3.bar(metrics_df['metric'], metrics_df['log_value'],
                   color=['blue', 'red', 'green', 'purple'], alpha=0.7, edgecolor='black')
    ax3.set_ylabel('Log₁₀(Performance Metric)')
    ax3.set_title('Key Performance Metrics (Log Scale)')
    ax3.grid(True, alpha=0.3, axis='y')

    # Add value labels
    for bar, value in zip(bars, metrics_df['value']):
        height = bar.get_height()
        label = f'{value:.2e}' if value >= 1000 else f'{value:.2f}'
        ax3.text(bar.get_x() + bar.get_width() / 2., height,
                 label, ha='center', va='bottom', rotation=45, fontsize=8)

    # Plot 4: Module information and summary
    info_text = f"""Module: {metadata['module']}
Timestamp: {metadata['timestamp']}
Claims Validated: {len(claims)}
Network Nodes: {data['network_topology']['node_count']}
Network Edges: {len(data['network_topology']['edges'])}

Tests Passed: {sum(validation_df['status'])}/{len(validation_df)}"""

    ax4.text(0.1, 0.9, info_text, fontsize=11, transform=ax4.transAxes,
             verticalalignment='top', fontfamily='monospace')

    # Add validation summary with styling
    passed_tests = sum(validation_df['status'])
    total_tests = len(validation_df)
    success_rate = passed_tests / total_tests * 100

    summary_text = f"Overall Success Rate: {success_rate:.1f}%"
    color = 'green' if success_rate >= 75 else 'orange' if success_rate >= 50 else 'red'

    ax4.text(0.1, 0.2, summary_text, fontsize=14, fontweight='bold',
             transform=ax4.transAxes, color=color)

    ax4.set_xlim(0, 1)
    ax4.set_ylim(0, 1)
    ax4.axis('off')
    ax4.set_title('Study Summary')

    plt.tight_layout()
    plt.savefig('validation_summary.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Print detailed validation summary
    print("Validation Summary:")
    print("=" * 50)
    for index, row in validation_df.iterrows():
        status = "✓ PASS" if row['status'] else "✗ FAIL"
        print(f"{index.replace('_', ' ').title():25}: {status}")

    print(f"\nOverall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")


if __name__ == "__main__":
    main()
