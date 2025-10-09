import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import json


def main():
    # Load data using pandas
    with open('membrane_quantum_resolution_data.json', 'r') as f:
        data = json.load(f)

    # Extract quantum parameters
    quantum_efficiency = data['quantum_efficiency']
    enhancement_factor = data['enaqt_enhancement_factor']
    coherence_time = data['coherence_time_microseconds']
    resolution_met = data['resolution_target_met']

    # Create results DataFrame
    results_df = pd.DataFrame({
        'accuracy': data['raw_accuracies'],
        'confidence': data['raw_confidences'],
        'molecule': data['test_molecules'],
        'processing_time': data['processing_times_microseconds']
    })

    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

    # Plot 1: Quantum efficiency visualization
    efficiency_data = pd.DataFrame({
        'Parameter': ['Quantum\nEfficiency', 'Enhancement\nFactor', 'Coherence Time\n(×10 μs)', 'Success\nRate'],
        'Value': [quantum_efficiency, enhancement_factor / 10, coherence_time / 10, data['success_rate']],
        'Raw_Value': [quantum_efficiency, enhancement_factor, coherence_time, data['success_rate']],
        'Color': ['blue', 'green', 'orange', 'red']
    })

    bars = ax1.bar(efficiency_data['Parameter'], efficiency_data['Value'],
                   color=efficiency_data['Color'], alpha=0.7, edgecolor='black')
    ax1.set_ylabel('Normalized Value')
    ax1.set_title('Quantum System Parameters')
    ax1.grid(True, alpha=0.3, axis='y')

    # Add value labels
    for bar, raw_val, param in zip(bars, efficiency_data['Raw_Value'], efficiency_data['Parameter']):
        height = bar.get_height()
        if 'Coherence' in param:
            label = f'{raw_val:.0f} μs'
        elif 'Enhancement' in param:
            label = f'{raw_val:.2f}x'
        else:
            label = f'{raw_val:.3f}'
        ax1.text(bar.get_x() + bar.get_width() / 2., height + 0.02,
                 label, ha='center', va='bottom', fontweight='bold')

    # Plot 2: Processing time vs accuracy with quantum efficiency coloring
    # Create efficiency bins based on accuracy
    results_df['efficiency_bin'] = pd.cut(results_df['accuracy'],
                                          bins=5, labels=['Low', 'Med-Low', 'Medium', 'Med-High', 'High'])

    colors = ['red', 'orange', 'yellow', 'lightgreen', 'darkgreen']
    for i, (bin_name, color) in enumerate(zip(['Low', 'Med-Low', 'Medium', 'Med-High', 'High'], colors)):
        mask = results_df['efficiency_bin'] == bin_name
        if mask.any():
            ax2.scatter(results_df[mask]['processing_time'], results_df[mask]['accuracy'],
                        c=color, label=f'{bin_name} Efficiency', alpha=0.7, s=50)

    ax2.set_xlabel('Processing Time (μs)')
    ax2.set_ylabel('Accuracy')
    ax2.set_title('Processing Time vs Accuracy (Efficiency Bins)')
    ax2.set_xscale('log')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Plot 3: Enhancement factor impact simulation
    # Simulate performance with different enhancement factors
    enhancement_range = np.linspace(1.0, 5.0, 20)
    base_accuracy = results_df['accuracy'].mean()
    base_processing_time = results_df['processing_time'].mean()

    # Simulate enhanced performance
    enhanced_accuracy = base_accuracy + (enhancement_range - 1) * 0.01  # Small accuracy boost
    enhanced_speed = base_processing_time / enhancement_range  # Speed improvement

    ax3_twin = ax3.twinx()

    line1 = ax3.plot(enhancement_range, enhanced_accuracy, 'b-', linewidth=2,
                     marker='o', label='Enhanced Accuracy')
    ax3.axvline(enhancement_factor, color='blue', linestyle='--', alpha=0.7,
                label=f'Current: {enhancement_factor:.2f}x')
    ax3.set_xlabel('Enhancement Factor')
    ax3.set_ylabel('Projected Accuracy', color='blue')
    ax3.tick_params(axis='y', labelcolor='blue')

    line2 = ax3_twin.plot(enhancement_range, enhanced_speed * 1e6, 'r-', linewidth=2,
                          marker='s', label='Enhanced Speed')
    ax3_twin.set_ylabel('Processing Time (ns)', color='red')
    ax3_twin.tick_params(axis='y', labelcolor='red')
    ax3_twin.set_yscale('log')

    ax3.set_title('Enhancement Factor Impact Analysis')
    ax3.grid(True, alpha=0.3)

    # Combine legends
    lines1, labels1 = ax3.get_legend_handles_labels()
    lines2, labels2 = ax3_twin.get_legend_handles_labels()
    ax3.legend(lines1 + lines2, labels1 + labels2, loc='center right')

    # Plot 4: Coherence time analysis
    # Simulate coherence time impact on performance
    coherence_range = np.linspace(50, 200, 100)
    optimal_coherence = 125  # Current value

    # Model performance degradation with suboptimal coherence
    coherence_factor = np.exp(-0.5 * ((coherence_range - optimal_coherence) / 30) ** 2)
    performance_impact = base_accuracy * coherence_factor

    ax4.plot(coherence_range, performance_impact, 'purple', linewidth=2)
    ax4.axvline(coherence_time, color='red', linestyle='--', linewidth=2,
                label=f'Current: {coherence_time:.0f} μs')
    ax4.axhline(base_accuracy, color='gray', linestyle=':', alpha=0.7,
                label=f'Base Accuracy: {base_accuracy:.3f}')
    ax4.set_xlabel('Coherence Time (μs)')
    ax4.set_ylabel('Projected Accuracy')
    ax4.set_title('Coherence Time Optimization')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('quantum_efficiency_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Print quantum system summary
    print("Quantum System Analysis:")
    print("=" * 50)
    print(f"Quantum Efficiency: {quantum_efficiency:.1%}")
    print(f"ENAQT Enhancement Factor: {enhancement_factor:.2f}x")
    print(f"Coherence Time: {coherence_time:.0f} μs")
    print(f"Resolution Target Met: {'✓ YES' if resolution_met else '✗ NO'}")
    print(f"Theoretical Speed Improvement: {enhancement_factor:.1f}x faster")
    print(f"Quantum Advantage: {(quantum_efficiency - 0.5) * 200:.1f}% above classical limit")


if __name__ == "__main__":
    main()
