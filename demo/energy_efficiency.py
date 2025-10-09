import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import json


def main():
    # Load data using pandas
    with open('electron_cascade_data.json', 'r') as f:
        data = json.load(f)

    # Convert energy efficiency data to DataFrame
    energy_df = pd.DataFrame(data['energy_efficiency'])

    # Create figure
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

    # Plot 1: Energy consumption comparison
    ax1.loglog(energy_df['information_loads'], energy_df['cascade_energy_joules'],
               'b-', linewidth=2, label='Cascade System', marker='o', markersize=6)
    ax1.loglog(energy_df['information_loads'], energy_df['molecular_energy_joules'],
               'r-', linewidth=2, label='Molecular System', marker='s', markersize=6)
    ax1.set_xlabel('Information Load (bits)')
    ax1.set_ylabel('Energy Consumption (J)')
    ax1.set_title('Energy Consumption vs Information Load')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Energy efficiency ratio
    energy_df['energy_ratio'] = energy_df['molecular_energy_joules'] / energy_df['cascade_energy_joules']
    ax2.semilogx(energy_df['information_loads'], energy_df['energy_ratio'],
                 'g-', linewidth=2, marker='^', markersize=6)
    ax2.set_xlabel('Information Load (bits)')
    ax2.set_ylabel('Energy Efficiency Ratio (Molecular/Cascade)')
    ax2.set_title('Relative Energy Efficiency')
    ax2.grid(True, alpha=0.3)

    # Plot 3: Energy per bit
    energy_df['energy_per_bit_cascade'] = energy_df['cascade_energy_joules'] / energy_df['information_loads']
    energy_df['energy_per_bit_molecular'] = energy_df['molecular_energy_joules'] / energy_df['information_loads']

    ax3.loglog(energy_df['information_loads'], energy_df['energy_per_bit_cascade'],
               'b-', linewidth=2, label='Cascade', marker='o', markersize=6)
    ax3.loglog(energy_df['information_loads'], energy_df['energy_per_bit_molecular'],
               'r-', linewidth=2, label='Molecular', marker='s', markersize=6)
    ax3.set_xlabel('Information Load (bits)')
    ax3.set_ylabel('Energy per Bit (J/bit)')
    ax3.set_title('Energy Efficiency: Energy per Bit')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4: Efficiency advantage over load range
    ax4.semilogx(energy_df['information_loads'], energy_df['efficiency_advantage'],
                 'purple', linewidth=2, marker='d', markersize=6)
    ax4.set_xlabel('Information Load (bits)')
    ax4.set_ylabel('Efficiency Advantage Factor')
    ax4.set_title('Cascade Efficiency Advantage')
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('energy_efficiency_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Calculate and print statistics
    print("Energy Efficiency Analysis:")
    print(f"Average efficiency advantage: {energy_df['efficiency_advantage'].mean():.6f}")
    print(
        f"Energy advantage range: {energy_df['efficiency_advantage'].min():.6f} - {energy_df['efficiency_advantage'].max():.6f}")
    print(
        f"Cascade energy range: {energy_df['cascade_energy_joules'].min():.2e} - {energy_df['cascade_energy_joules'].max():.2e} J")
    print(
        f"Molecular energy range: {energy_df['molecular_energy_joules'].min():.2e} - {energy_df['molecular_energy_joules'].max():.2e} J")


if __name__ == "__main__":
    main()
