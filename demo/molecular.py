import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import json


def main():
    # Load data using pandas
    with open('oxygen_substrate_data.json', 'r') as f:
        data = json.load(f)

    # Create molecular comparison DataFrame
    molecules = data['molecular_comparison']['molecules']
    oid_values = data['molecular_comparison']['oid_values']

    mol_df = pd.DataFrame({
        'molecule': molecules,
        'oid_value': oid_values
    })

    # Sort by OID value for better visualization
    mol_df = mol_df.sort_values('oid_value', ascending=False)

    # Extract oxygen advantages
    oxygen_advantages = data['molecular_comparison']['oxygen_advantage']

    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: OID values comparison (bar chart)
    colors = ['red' if 'O₂' in mol else 'lightblue' for mol in mol_df['molecule']]
    bars = ax1.bar(range(len(mol_df)), mol_df['oid_value'],
                   color=colors, alpha=0.8, edgecolor='black')

    ax1.set_xlabel('Molecules')
    ax1.set_ylabel('OID Values (Information Density)')
    ax1.set_title('Molecular Information Density Comparison')
    ax1.set_xticks(range(len(mol_df)))
    ax1.set_xticklabels(mol_df['molecule'], rotation=45, ha='right')
    ax1.set_yscale('log')
    ax1.grid(True, alpha=0.3, axis='y')

    # Add value labels on bars
    for bar, value in zip(bars, mol_df['oid_value']):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2., height * 1.1,
                 f'{value:.1e}', ha='center', va='bottom', rotation=45, fontsize=8)

    # Plot 2: Oxygen advantage factors
    advantage_molecules = list(oxygen_advantages.keys())
    advantage_values = list(oxygen_advantages.values())

    # Clean up molecule names for display
    clean_names = [name.split('(')[0].strip() for name in advantage_molecules]

    bars2 = ax2.bar(range(len(advantage_values)), advantage_values,
                    color=['lightcoral', 'lightgreen', 'lightyellow', 'lightpink', 'lightcyan', 'wheat'],
                    alpha=0.8, edgecolor='black')

    ax2.set_xlabel('Molecules')
    ax2.set_ylabel('Oxygen Advantage Factor')
    ax2.set_title('Oxygen Supremacy Over Other Molecules')
    ax2.set_xticks(range(len(clean_names)))
    ax2.set_xticklabels(clean_names, rotation=45, ha='right')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3, axis='y')

    # Add value labels
    for bar, value in zip(bars2, advantage_values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2., height * 1.1,
                 f'{value:.1f}x', ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Plot 3: Relative performance radar chart (simplified as line plot)
    # Normalize OID values for comparison
    normalized_oid = mol_df['oid_value'] / mol_df['oid_value'].max()

    ax3.plot(range(len(mol_df)), normalized_oid, 'bo-', linewidth=3, markersize=8)
    ax3.fill_between(range(len(mol_df)), 0, normalized_oid, alpha=0.3, color='blue')

    # Highlight oxygen
    oxygen_idx = mol_df[mol_df['molecule'].str.contains('O₂')].index[0]
    oxygen_pos = mol_df.index.get_loc(oxygen_idx)
    ax3.scatter(oxygen_pos, normalized_oid.iloc[oxygen_pos],
                color='red', s=200, zorder=5, label='Oxygen (O₂)')

    ax3.set_xlabel('Molecules (Ranked by Performance)')
    ax3.set_ylabel('Normalized Information Density')
    ax3.set_title('Relative Molecular Performance Profile')
    ax3.set_xticks(range(len(mol_df)))
    ax3.set_xticklabels(mol_df['molecule'], rotation=45, ha='right')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0, 1.1)

    # Plot 4: Biological significance analysis
    # Create categories based on biological function
    biological_categories = {
        'Respiratory': ['O₂ (Oxygen)', 'N₂ (Nitrogen)', 'CO₂ (Carbon Dioxide)'],
        'Metabolic': ['ATP', 'Glucose'],
        'Transport': ['Hemoglobin'],
        'Solvent': ['H₂O (Water)']
    }

    category_performance = {}
    for category, mols in biological_categories.items():
        category_oids = []
        for mol in mols:
            if mol in mol_df['molecule'].values:
                oid_val = mol_df[mol_df['molecule'] == mol]['oid_value'].iloc[0]
                category_oids.append(oid_val)
        if category_oids:
            category_performance[category] = np.mean(category_oids)

    categories = list(category_performance.keys())
    performances = list(category_performance.values())

    # Create pie chart showing relative importance
    colors_pie = ['red', 'blue', 'green', 'orange']
    wedges, texts, autotexts = ax4.pie(performances, labels=categories, autopct='%1.1f%%',
                                       colors=colors_pie, startangle=90)

    ax4.set_title('Biological Function Categories by Information Density')

    # Enhance text
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')

    plt.tight_layout()
    plt.savefig('molecular_comparison_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Print molecular analysis
    print("Molecular Comparison Analysis:")
    print("=" * 50)

    # Oxygen supremacy
    oxygen_oid = mol_df[mol_df['molecule'].str.contains('O₂')]['oid_value'].iloc[0]
    print(f"Oxygen OID Value: {oxygen_oid:.2e}")

    print("\nOxygen Advantages:")
    for molecule, advantage in oxygen_advantages.items():
        print(f"vs {molecule}: {advantage:.1f}x superior")

    # Statistical analysis
    print(f"\nStatistical Summary:")
    print(f"Highest OID: {mol_df['oid_value'].max():.2e} ({mol_df.iloc[0]['molecule']})")
    print(f"Lowest OID: {mol_df['oid_value'].min():.2e} ({mol_df.iloc[-1]['molecule']})")
    print(f"OID Range: {mol_df['oid_value'].max() / mol_df['oid_value'].min():.1f}x")

    # Biological significance
    print(f"\nBiological Significance:")
    for category, performance in category_performance.items():
        percentage = (performance / sum(performances)) * 100
        print(f"{category}: {performance:.2e} ({percentage:.1f}% of total)")

    # Oxygen's role in cellular processes
    print(f"\nOxygen's Cellular Role:")
    print(f"• Primary information substrate for cellular processes")
    print(f"• {oxygen_oid / 1e15:.0f} petabytes of information density")
    print(f"• Paramagnetic properties create reactive spaces")
    print(f"• Eliminates diffusion limitations in biochemical reactions")


if __name__ == "__main__":
    main()
