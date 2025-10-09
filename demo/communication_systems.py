import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import json


def main():
    # Load data using pandas
    with open('electron_cascade_data.json', 'r') as f:
        data = json.load(f)

    # Convert communication systems data to DataFrame
    comm_df = pd.DataFrame(data['communication_systems'])

    # Create figure
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

    # Define colors
    colors = ['red', 'blue', 'green', 'orange']

    # Plot 1: Communication capacity comparison (bar plot)
    bars = ax1.bar(comm_df['systems'], comm_df['capacities_bits_per_sec'],
                   color=colors, alpha=0.7, edgecolor='black')
    ax1.set_ylabel('Capacity (bits/sec)')
    ax1.set_title('Communication System Capacities')
    ax1.set_yscale('log')
    ax1.grid(True, alpha=0.3, axis='y')

    # Add value labels on bars
    for bar, capacity in zip(bars, comm_df['capacities_bits_per_sec']):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2., height,
                 f'{capacity:.0e}', ha='center', va='bottom', rotation=45)

    # Plot 2: Cascade advantage factors (excluding cascade itself)
    non_cascade_df = comm_df[comm_df['systems'] != 'Cascade'].copy()
    non_cascade_colors = [colors[i] for i in range(1, len(colors))]

    ax2.bar(non_cascade_df['systems'], non_cascade_df['cascade_advantage'],
            color=non_cascade_colors, alpha=0.7, edgecolor='black')
    ax2.set_ylabel('Cascade Advantage Factor')
    ax2.set_title('Cascade Advantage Over Other Systems')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3, axis='y')

    # Add value labels
    for i, (system, advantage) in enumerate(zip(non_cascade_df['systems'], non_cascade_df['cascade_advantage'])):
        ax2.text(i, advantage, f'{advantage:.0e}', ha='center', va='bottom', rotation=45)

    # Plot 3: Relative performance (normalized to cascade)
    comm_df['relative_performance'] = comm_df['capacities_bits_per_sec'] / comm_df['capacities_bits_per_sec'].iloc[0]

    ax3.bar(comm_df['systems'], comm_df['relative_performance'],
            color=colors, alpha=0.7, edgecolor='black')
    ax3.set_ylabel('Relative Performance (Cascade = 1)')
    ax3.set_title('Performance Relative to Cascade System')
    ax3.set_yscale('log')
    ax3.grid(True, alpha=0.3, axis='y')

    # Plot 4: Information processing comparison over time
    time_points = np.linspace(0, 10, 100)

    for i, (system, capacity, color) in enumerate(zip(comm_df['systems'],
                                                      comm_df['capacities_bits_per_sec'],
                                                      colors)):
        throughput = capacity * np.ones_like(time_points)
        linewidth = 3 if system == 'Cascade' else 2
        ax4.plot(time_points, throughput, color=color, linewidth=linewidth,
                 label=system, alpha=0.8)

    ax4.set_xlabel('Time (arbitrary units)')
    ax4.set_ylabel('Information Throughput (bits/sec)')
    ax4.set_title('Sustained Information Throughput')
    ax4.set_yscale('log')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('communication_systems_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Print summary statistics
    print("Communication Systems Analysis:")
    print("-" * 40)
    for _, row in comm_df.iterrows():
        print(
            f"{row['systems']:12}: {row['capacities_bits_per_sec']:.2e} bits/sec (advantage: {row['cascade_advantage']:.0e}x)")


if __name__ == "__main__":
    main()
