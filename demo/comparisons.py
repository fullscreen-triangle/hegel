import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import json


def main():
    # Load data using pandas
    with open('electron_cascade_data.json', 'r') as f:
        data = json.load(f)

    # Convert to pandas DataFrame for easier manipulation
    speed_df = pd.DataFrame(data['speed_comparison'])

    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

    # Plot 1: Time vs Distance comparison
    ax1.loglog(speed_df['distances_micrometers'], speed_df['cascade_times_microseconds'],
               'b-', linewidth=2, label='Cascade', marker='o')
    ax1.loglog(speed_df['distances_micrometers'], speed_df['diffusion_times_microseconds'],
               'r-', linewidth=2, label='Diffusion', marker='s')
    ax1.set_xlabel('Distance (μm)')
    ax1.set_ylabel('Time (μs)')
    ax1.set_title('Signal Propagation Time vs Distance')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Speed advantage
    ax2.loglog(speed_df['distances_micrometers'], speed_df['speed_advantage'],
               'g-', linewidth=2, marker='^')
    ax2.set_xlabel('Distance (μm)')
    ax2.set_ylabel('Speed Advantage Factor')
    ax2.set_title('Cascade Speed Advantage Over Diffusion')
    ax2.grid(True, alpha=0.3)

    # Plot 3: Normalized comparison
    cascade_norm = speed_df['cascade_times_microseconds'] / speed_df['cascade_times_microseconds'].iloc[0]
    diffusion_norm = speed_df['diffusion_times_microseconds'] / speed_df['diffusion_times_microseconds'].iloc[0]

    ax3.loglog(speed_df['distances_micrometers'], cascade_norm,
               'b-', linewidth=2, label='Cascade (normalized)', marker='o')
    ax3.loglog(speed_df['distances_micrometers'], diffusion_norm,
               'r-', linewidth=2, label='Diffusion (normalized)', marker='s')
    ax3.set_xlabel('Distance (μm)')
    ax3.set_ylabel('Normalized Time')
    ax3.set_title('Normalized Time Scaling')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4: Speed ratio trend
    ax4.semilogx(speed_df['distances_micrometers'], speed_df['speed_advantage'],
                 'purple', linewidth=2, marker='d')
    ax4.set_xlabel('Distance (μm)')
    ax4.set_ylabel('Speed Advantage (linear scale)')
    ax4.set_title('Speed Advantage Scaling Trend')
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('speed_comparison_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Print summary statistics
    print("Speed Analysis Summary:")
    print(f"Maximum speed advantage: {speed_df['speed_advantage'].max():.2e}")
    print(
        f"Distance range: {speed_df['distances_micrometers'].min():.1f} - {speed_df['distances_micrometers'].max():.1f} μm")
    print(
        f"Cascade time range: {speed_df['cascade_times_microseconds'].min():.2e} - {speed_df['cascade_times_microseconds'].max():.2e} μs")


if __name__ == "__main__":
    main()
