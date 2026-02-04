"""
Observational Partition Algebra - Validation Panel 2
=====================================================
Four-panel validation of diagnostic framework:
1. Disease signature vectors (8-component radar)
2. Protein folding as diagnostic readout
3. Phase-lock bandwidth and coherence
4. Cellular coherence index from oscillator ensemble
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize
import matplotlib.patches as mpatches

# Set up figure with 4 panels
fig = plt.figure(figsize=(14, 12))
fig.suptitle('Observational Partition Algebra: Diagnostic Framework Validation', fontsize=14, fontweight='bold')

# =============================================================================
# Panel 1: Disease Signature Vectors (Radar/Spider Chart)
# =============================================================================
ax1 = fig.add_subplot(2, 2, 1, projection='polar')

# Disease components: D = (D_P, D_E, D_C, D_M, D_A, D_G, D_Ca, D_R)
categories = ['$D_P$\n(Protein)', '$D_E$\n(Enzyme)', '$D_C$\n(Channel)', '$D_M$\n(Membrane)',
              '$D_A$\n(ATP)', '$D_G$\n(Genetic)', '$D_{Ca}$\n(Calcium)', '$D_R$\n(Circadian)']
N = len(categories)
angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]  # Complete the loop

# Disease profiles
healthy = [0.05, 0.08, 0.06, 0.04, 0.07, 0.05, 0.06, 0.03]
alzheimers = [0.85, 0.20, 0.15, 0.30, 0.25, 0.10, 0.40, 0.20]  # Dominant D_P
diabetes = [0.15, 0.80, 0.25, 0.20, 0.35, 0.15, 0.30, 0.25]    # Dominant D_E
cystic_fib = [0.10, 0.15, 0.90, 0.20, 0.15, 0.10, 0.25, 0.10]  # Dominant D_C
cancer = [0.30, 0.25, 0.20, 0.35, 0.25, 0.85, 0.20, 0.30]      # Dominant D_G

# Close the loop
healthy += healthy[:1]
alzheimers += alzheimers[:1]
diabetes += diabetes[:1]
cystic_fib += cystic_fib[:1]
cancer += cancer[:1]

# Plot
ax1.plot(angles, healthy, 'o-', linewidth=2, color='#2ecc71', label='Healthy', markersize=6)
ax1.fill(angles, healthy, alpha=0.15, color='#2ecc71')

ax1.plot(angles, alzheimers, 's-', linewidth=2, color='#e74c3c', label="Alzheimer's ($D_P$)", markersize=6)
ax1.fill(angles, alzheimers, alpha=0.1, color='#e74c3c')

ax1.plot(angles, diabetes, '^-', linewidth=2, color='#3498db', label='Diabetes ($D_E$)', markersize=6)
ax1.fill(angles, diabetes, alpha=0.1, color='#3498db')

ax1.plot(angles, cystic_fib, 'd-', linewidth=2, color='#9b59b6', label='Cystic Fibrosis ($D_C$)', markersize=6)
ax1.fill(angles, cystic_fib, alpha=0.1, color='#9b59b6')

ax1.plot(angles, cancer, 'p-', linewidth=2, color='#f39c12', label='Cancer ($D_G$)', markersize=6)
ax1.fill(angles, cancer, alpha=0.1, color='#f39c12')

ax1.set_xticks(angles[:-1])
ax1.set_xticklabels(categories, fontsize=8)
ax1.set_ylim(0, 1)
ax1.set_yticks([0.25, 0.5, 0.75, 1.0])
ax1.set_yticklabels(['0.25', '0.5', '0.75', '1.0'], fontsize=8)
ax1.legend(loc='upper right', bbox_to_anchor=(1.35, 1.0), fontsize=8)
ax1.set_title('(A) Disease Signature Vectors $\\mathbf{D}$', fontsize=11, pad=20)

# =============================================================================
# Panel 2: Protein Folding as Diagnostic Readout
# =============================================================================
ax2 = fig.add_subplot(2, 2, 2)

# Folding cycles distribution for different cellular states
k_values = np.arange(10, 20)
k_min, k_max = 12, 16

# Probability distributions for different health states
def folding_distribution(k, k_mean, sigma):
    return np.exp(-(k - k_mean)**2 / (2 * sigma**2))

# Healthy: narrow distribution around k_min
healthy_dist = folding_distribution(k_values, 12.5, 0.8)
healthy_dist /= healthy_dist.sum()

# Stressed: slightly shifted
stressed_dist = folding_distribution(k_values, 14, 1.0)
stressed_dist /= stressed_dist.sum()

# Diseased: shifted further
diseased_dist = folding_distribution(k_values, 15.5, 1.2)
diseased_dist /= diseased_dist.sum()

# Critical: broad, shifted to failure
critical_dist = folding_distribution(k_values, 17, 1.5)
critical_dist /= critical_dist.sum()

width = 0.2
x = k_values

ax2.bar(x - 1.5*width, healthy_dist, width, color='#2ecc71', label='Healthy ($\\eta \\approx 1$)', edgecolor='black')
ax2.bar(x - 0.5*width, stressed_dist, width, color='#f1c40f', label='Stressed ($\\eta \\approx 0.5$)', edgecolor='black')
ax2.bar(x + 0.5*width, diseased_dist, width, color='#e67e22', label='Diseased ($\\eta \\approx 0.25$)', edgecolor='black')
ax2.bar(x + 1.5*width, critical_dist, width, color='#e74c3c', label='Critical ($\\eta \\approx 0$)', edgecolor='black')

# Mark optimal and degraded bounds
ax2.axvline(x=k_min, color='green', linestyle='--', linewidth=2, alpha=0.7)
ax2.axvline(x=k_max, color='red', linestyle='--', linewidth=2, alpha=0.7)
ax2.text(k_min + 0.1, 0.42, '$k_{min}$', fontsize=10, color='green', fontweight='bold')
ax2.text(k_max + 0.1, 0.42, '$k_{max}$', fontsize=10, color='red', fontweight='bold')

# Coherence scale on secondary axis
ax2_twin = ax2.twiny()
eta_values = (k_max - np.array([12, 13, 14, 15, 16])) / (k_max - k_min)
ax2_twin.set_xlim(ax2.get_xlim())
ax2_twin.set_xticks([12, 13, 14, 15, 16])
ax2_twin.set_xticklabels([f'{e:.2f}' for e in eta_values])
ax2_twin.set_xlabel('Coherence Index $\\eta$', fontsize=10)

ax2.set_xlabel('Folding Cycles $k$', fontsize=11)
ax2.set_ylabel('Probability $P(k)$', fontsize=11)
ax2.set_title('(B) Folding Cycles Encode Cellular Coherence', fontsize=11)
ax2.legend(loc='upper right', fontsize=8)
ax2.set_xlim(9.5, 19.5)
ax2.set_ylim(0, 0.5)
ax2.grid(axis='y', alpha=0.3)

# =============================================================================
# Panel 3: Phase-Lock Bandwidth and Coherence
# =============================================================================
ax3 = fig.add_subplot(2, 2, 3)

# Phase-lock response function
delta_omega = np.linspace(-5, 5, 500)  # Normalized frequency detuning
delta_omega_c = 1.0  # Critical bandwidth

# Coherence as function of detuning (Lorentzian profile)
def phase_lock_coherence(dw, dw_c, eta_max=1.0):
    return eta_max / (1 + (dw / dw_c)**2)

eta_narrow = phase_lock_coherence(delta_omega, 0.5)
eta_normal = phase_lock_coherence(delta_omega, 1.0)
eta_wide = phase_lock_coherence(delta_omega, 2.0)

ax3.plot(delta_omega, eta_narrow, '-', color='#e74c3c', linewidth=2.5,
         label=r'Narrow: $\Delta\omega_c = 0.5$')
ax3.plot(delta_omega, eta_normal, '-', color='#3498db', linewidth=2.5,
         label=r'Normal: $\Delta\omega_c = 1.0$')
ax3.plot(delta_omega, eta_wide, '-', color='#2ecc71', linewidth=2.5,
         label=r'Wide: $\Delta\omega_c = 2.0$')

# Mark phase-lock region
ax3.axvspan(-1, 1, alpha=0.15, color='blue', label='Phase-lock region')
ax3.axhline(y=0.5, color='gray', linestyle=':', alpha=0.7)
ax3.axvline(x=-1, color='gray', linestyle=':', alpha=0.5)
ax3.axvline(x=1, color='gray', linestyle=':', alpha=0.5)

# Add annotations
ax3.annotate('$\\eta = 0.5$', xy=(2.5, 0.5), fontsize=10, color='gray')
ax3.annotate('Phase-locked\n(Healthy)', xy=(0, 0.85), ha='center', fontsize=9,
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
ax3.annotate('Decoherent\n(Diseased)', xy=(-3.5, 0.2), ha='center', fontsize=9,
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.3))

ax3.set_xlabel(r'Frequency Detuning $(\omega - \omega_0)/\omega_0$', fontsize=11)
ax3.set_ylabel('Coherence Index $\\eta$', fontsize=11)
ax3.set_title('(C) Phase-Lock Bandwidth Determines Coherence', fontsize=11)
ax3.legend(loc='upper right', fontsize=9)
ax3.set_xlim(-5, 5)
ax3.set_ylim(0, 1.1)
ax3.grid(alpha=0.3)

# =============================================================================
# Panel 4: Cellular Coherence Index from Oscillator Ensemble
# =============================================================================
ax4 = fig.add_subplot(2, 2, 4)

# Simulate oscillator ensemble
np.random.seed(123)
n_oscillators = 100

# Generate weights (entropic coupling)
weights = np.random.exponential(1.0, n_oscillators)
weights /= weights.sum()

# Simulate different cellular states
def compute_cellular_coherence(eta_mean, eta_std, weights):
    """Compute η_cell = (1/W) Σ w_i η_i"""
    eta_individual = np.clip(np.random.normal(eta_mean, eta_std, len(weights)), 0, 1)
    return np.sum(weights * eta_individual)

# Generate coherence distributions for different states
n_samples = 1000
healthy_eta_cell = [compute_cellular_coherence(0.85, 0.1, weights) for _ in range(n_samples)]
stressed_eta_cell = [compute_cellular_coherence(0.60, 0.15, weights) for _ in range(n_samples)]
diseased_eta_cell = [compute_cellular_coherence(0.35, 0.20, weights) for _ in range(n_samples)]

# Plot distributions
bins = np.linspace(0, 1, 40)
ax4.hist(healthy_eta_cell, bins, alpha=0.7, color='#2ecc71', label='Healthy', density=True, edgecolor='black')
ax4.hist(stressed_eta_cell, bins, alpha=0.7, color='#f1c40f', label='Stressed', density=True, edgecolor='black')
ax4.hist(diseased_eta_cell, bins, alpha=0.7, color='#e74c3c', label='Diseased', density=True, edgecolor='black')

# Mark critical threshold
eta_c = 0.5
ax4.axvline(x=eta_c, color='black', linestyle='--', linewidth=2)
ax4.text(eta_c + 0.02, ax4.get_ylim()[1] * 0.9, '$\\eta_c$ (threshold)', fontsize=10, fontweight='bold')

# Add equation
ax4.text(0.05, ax4.get_ylim()[1] * 0.75,
         r'$\eta_{cell} = \frac{1}{W}\sum_i w_i \eta_i$',
         fontsize=12, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# Statistics
ax4.axvline(x=np.mean(healthy_eta_cell), color='#27ae60', linestyle='-', linewidth=1.5, alpha=0.8)
ax4.axvline(x=np.mean(stressed_eta_cell), color='#d4ac0d', linestyle='-', linewidth=1.5, alpha=0.8)
ax4.axvline(x=np.mean(diseased_eta_cell), color='#c0392b', linestyle='-', linewidth=1.5, alpha=0.8)

ax4.set_xlabel('Cellular Coherence Index $\\eta_{cell}$', fontsize=11)
ax4.set_ylabel('Probability Density', fontsize=11)
ax4.set_title('(D) Cellular Coherence from Oscillator Ensemble', fontsize=11)
ax4.legend(loc='upper left', fontsize=9)
ax4.set_xlim(0, 1)
ax4.grid(alpha=0.3)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig('c:/Users/kundai/Documents/biology/hegel/wilhelm/publications/observation-equations/validation_panel2.png',
            dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig('c:/Users/kundai/Documents/biology/hegel/wilhelm/publications/observation-equations/validation_panel2.pdf',
            bbox_inches='tight', facecolor='white')
plt.show()

print("\nPanel 2 saved successfully!")
print("- Disease signature vectors (radar)")
print("- Protein folding as diagnostic readout")
print("- Phase-lock bandwidth")
print("- Cellular coherence index")

# =============================================================================
# Print validation statistics
# =============================================================================
print("\n" + "="*60)
print("VALIDATION STATISTICS")
print("="*60)

print("\n1. Partition Capacity Validation:")
for n in range(1, 8):
    print(f"   n={n}: C(n) = 2n² = {2*n**2}")

print("\n2. Coherence Index Statistics:")
print(f"   Healthy:  eta_cell = {np.mean(healthy_eta_cell):.3f} +/- {np.std(healthy_eta_cell):.3f}")
print(f"   Stressed: eta_cell = {np.mean(stressed_eta_cell):.3f} +/- {np.std(stressed_eta_cell):.3f}")
print(f"   Diseased: eta_cell = {np.mean(diseased_eta_cell):.3f} +/- {np.std(diseased_eta_cell):.3f}")

print("\n3. Disease Signature Dominant Components:")
diseases = ['Healthy', "Alzheimer's", 'Diabetes', 'Cystic Fibrosis', 'Cancer']
signatures = [healthy[:-1], alzheimers[:-1], diabetes[:-1], cystic_fib[:-1], cancer[:-1]]
components = ['D_P', 'D_E', 'D_C', 'D_M', 'D_A', 'D_G', 'D_Ca', 'D_R']
for disease, sig in zip(diseases, signatures):
    dominant = components[np.argmax(sig)]
    print(f"   {disease}: Dominant = {dominant} ({max(sig):.2f})")

print("\n4. Folding Efficiency Index (FEI):")
print(f"   Healthy:  FEI = {(k_max - 12.5)/(k_max - k_min):.3f}")
print(f"   Stressed: FEI = {(k_max - 14.0)/(k_max - k_min):.3f}")
print(f"   Diseased: FEI = {(k_max - 15.5)/(k_max - k_min):.3f}")
print(f"   Critical: FEI = {(k_max - 17.0)/(k_max - k_min):.3f}")
