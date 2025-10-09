import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import json
from scipy.optimize import curve_fit
from scipy import stats


def main():
    # Load data using pandas
    with open('oxygen_substrate_data.json', 'r') as f:
        data = json.load(f)

    # Create temperature DataFrame
    temp_df = pd.DataFrame({
        'temperature': data['temperature_dependence']['temperatures_celsius'],
        'oid_values': data['temperature_dependence']['oid_values']
    })

    optimal_temp = data['temperature_dependence']['optimal_temperature']

    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: Temperature vs OID with optimal point highlighted
    ax1.plot(temp_df['temperature'], temp_df['oid_values'], 'b-', linewidth=2, alpha=0.8)
    ax1.scatter(temp_df['temperature'], temp_df['oid_values'], c='lightblue', s=20, alpha=0.6)

    # Fix: Find the closest temperature to optimal_temp
    closest_idx = (temp_df['temperature'] - optimal_temp).abs().idxmin()
    optimal_oid = temp_df.loc[closest_idx, 'oid_values']
    closest_temp = temp_df.loc[closest_idx, 'temperature']

    ax1.axvline(optimal_temp, color='red', linestyle='--', linewidth=2,
                label=f'Optimal Temp: {optimal_temp}°C')
    ax1.scatter(closest_temp, optimal_oid, color='red', s=100, zorder=5,
                label=f'Peak OID: {optimal_oid:.2e}')

    ax1.set_xlabel('Temperature (°C)')
    ax1.set_ylabel('OID Values (Oxygen Information Density)')
    ax1.set_title('Oxygen Paramagnetic Information Density vs Temperature')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')

    # Plot 2: Temperature efficiency zones
    # Define physiological temperature ranges
    temp_zones = {
        'Hypothermic': (0, 35),
        'Optimal': (35, 39),
        'Febrile': (39, 42),
        'Hyperthermia': (42, 100)
    }

    colors = ['lightblue', 'lightgreen', 'orange', 'red']
    zone_performance = []

    for i, (zone, (t_min, t_max)) in enumerate(temp_zones.items()):
        zone_mask = (temp_df['temperature'] >= t_min) & (temp_df['temperature'] <= t_max)
        zone_data = temp_df[zone_mask]

        if not zone_data.empty:
            mean_oid = zone_data['oid_values'].mean()
            zone_performance.append(mean_oid)

            ax2.fill_between(zone_data['temperature'], 0, zone_data['oid_values'],
                             alpha=0.3, color=colors[i], label=f'{zone} Zone')

    ax2.plot(temp_df['temperature'], temp_df['oid_values'], 'k-', linewidth=2, alpha=0.8)
    ax2.set_xlabel('Temperature (°C)')
    ax2.set_ylabel('OID Values')
    ax2.set_title('Physiological Temperature Zones and Oxygen Performance')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale('log')

    # Plot 3: Normalized performance around body temperature
    body_temp_range = temp_df[(temp_df['temperature'] >= 30) & (temp_df['temperature'] <= 45)]
    if not body_temp_range.empty:
        normalized_oid = body_temp_range['oid_values'] / body_temp_range['oid_values'].max()

        ax3.plot(body_temp_range['temperature'], normalized_oid, 'g-', linewidth=3, marker='o')
        ax3.axvline(37, color='red', linestyle='--', linewidth=2, label='Body Temperature')
        ax3.axhline(0.8, color='orange', linestyle=':', alpha=0.7, label='80% Efficiency Threshold')

        ax3.set_xlabel('Temperature (°C)')
        ax3.set_ylabel('Normalized OID Performance')
        ax3.set_title('Oxygen Efficiency in Physiological Range')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim(0, 1.1)
    else:
        ax3.text(0.5, 0.5, 'No data in physiological range',
                 transform=ax3.transAxes, ha='center', va='center')

    # Plot 4: Temperature sensitivity analysis
    # Calculate rate of change
    if len(temp_df) > 1:
        temp_diff = np.diff(temp_df['temperature'])
        oid_diff = np.diff(temp_df['oid_values'])
        sensitivity = oid_diff / temp_diff
        temp_mid = temp_df['temperature'][:-1].values + temp_diff / 2

        ax4.plot(temp_mid, sensitivity, 'purple', linewidth=2, alpha=0.8)
        ax4.axvline(optimal_temp, color='red', linestyle='--', alpha=0.7,
                    label=f'Optimal: {optimal_temp}°C')
        ax4.axhline(0, color='black', linestyle='-', alpha=0.3)

        ax4.set_xlabel('Temperature (°C)')
        ax4.set_ylabel('Temperature Sensitivity (dOID/dT)')
        ax4.set_title('Oxygen System Temperature Sensitivity')
        ax4.legend()
        ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('temperature_oid_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Print analysis summary
    print("Temperature-Dependent Oxygen Analysis:")
    print("=" * 50)
    print(f"Optimal Temperature: {optimal_temp}°C (Body Temperature)")
    print(f"Peak OID Value: {optimal_oid:.2e}")
    print(f"Temperature Range: {temp_df['temperature'].min():.1f}°C to {temp_df['temperature'].max():.1f}°C")

    # Calculate efficiency at key temperatures
    key_temps = [0, 20, 37, 42, 100]
    print("\nOID at Key Temperatures:")
    for temp in key_temps:
        closest_idx = (temp_df['temperature'] - temp).abs().idxmin()
        closest_temp = temp_df.loc[closest_idx, 'temperature']
        oid_val = temp_df.loc[closest_idx, 'oid_values']
        efficiency = (oid_val / optimal_oid) * 100
        print(f"{temp}°C (actual: {closest_temp:.1f}°C): {oid_val:.2e} ({efficiency:.1f}% of optimal)")

    # Temperature stability analysis
    body_temp_data = temp_df[(temp_df['temperature'] >= 36) & (temp_df['temperature'] <= 38)]
    if not body_temp_data.empty:
        stability = body_temp_data['oid_values'].std() / body_temp_data['oid_values'].mean()
        print(f"\nBody Temperature Stability (36-38°C): CV = {stability:.3f}")
    else:
        print(f"\nNo data points in exact body temperature range (36-38°C)")
        # Find closest range
        closest_to_37 = temp_df.iloc[(temp_df['temperature'] - 37).abs().argsort()[:3]]
        print(f"Closest temperatures to 37°C:")
        for idx, row in closest_to_37.iterrows():
            print(f"  {row['temperature']:.1f}°C: {row['oid_values']:.2e}")


if __name__ == "__main__":
    main()
