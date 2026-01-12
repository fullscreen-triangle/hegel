"""
Panel 22: Mechanical Modality - Stress, Strain, and Deformation

Validates:
1. Stress distribution in cellular colloid
2. Strain from membrane deformation
3. Mechanical wave propagation
4. Viscoelastic response coupled to O2 clock

Author: AI Assistant
Date: 2026-01-10
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import os

# Create output directory
os.makedirs('validation_results', exist_ok=True)

# Physical constants
E_modulus = 1e3  # Young's modulus (Pa) - soft biological material
nu = 0.5  # Poisson's ratio (incompressible)
G_shear = E_modulus / (2 * (1 + nu))  # Shear modulus (Pa)
eta = 1e-3  # Viscosity (Pa·s) - water-like
omega_O2 = 2 * np.pi * 1e3  # O2 clock frequency (rad/s)

print("Panel 22: Mechanical Modality - Stress, Strain, & Deformation")
print("=" * 70)

# Create figure with 4 subplots
fig = plt.figure(figsize=(16, 12))

#############################################################################
# Chart 1: Stress Distribution from Membrane Deformation (3D)
#############################################################################
print("\nChart 1: Stress Distribution from Membrane Deformation")

ax1 = fig.add_subplot(2, 2, 1, projection='3d')

# Spatial grid (cylindrical coordinates)
r = np.linspace(0, 5, 50)  # Radial distance (μm)
theta = np.linspace(0, 2*np.pi, 50)  # Angle
R, THETA = np.meshgrid(r, theta)

# Convert to Cartesian
X = R * np.cos(THETA)
Y = R * np.sin(THETA)

# Membrane deformation creates radial stress
# σ_r = P * (r_inner/r)² for thin-walled sphere
P_turgor = 100  # Turgor pressure (Pa)
r_inner = 0.5  # Inner radius (μm)

sigma_r = P_turgor * (r_inner / (R + 0.1))**2

# Plot surface
surf = ax1.plot_surface(X, Y, sigma_r, cmap='viridis', alpha=0.8,
                        edgecolor='none')

ax1.set_xlabel('X (μm)', fontsize=10)
ax1.set_ylabel('Y (μm)', fontsize=10)
ax1.set_zlabel('Radial Stress (Pa)', fontsize=10)
ax1.set_title('Stress Distribution from Membrane Deformation', fontsize=14, fontweight='bold')
ax1.view_init(elev=30, azim=45)
fig.colorbar(surf, ax=ax1, shrink=0.5, aspect=5)

print(f"  Young's modulus: {E_modulus} Pa")
print(f"  Shear modulus: {G_shear:.1f} Pa")
print(f"  Turgor pressure: {P_turgor} Pa")
print(f"  Max stress: {np.max(sigma_r):.1f} Pa")

#############################################################################
# Chart 2: Strain from Compartment Formation (2D)
#############################################################################
print("\nChart 2: Strain from Compartment Formation")

ax2 = fig.add_subplot(2, 2, 2)

# Position along membrane
x_membrane = np.linspace(0, 10, 1000)  # μm

# Strain from membrane deformation
# ε = ΔL/L = amplitude * sin(kx - ωt)
k_membrane = 2 * np.pi / 2  # Wave number (μm^-1)
epsilon_amplitude = 0.1  # 10% strain

# Multiple time snapshots
times = [0, 0.25, 0.5, 0.75]  # Fractions of O2 period
colors_time = ['blue', 'green', 'orange', 'red']
T_O2 = 2 * np.pi / omega_O2

for i, t_frac in enumerate(times):
    t = t_frac * T_O2
    epsilon = epsilon_amplitude * np.sin(k_membrane * x_membrane - omega_O2 * t)
    ax2.plot(x_membrane, epsilon * 100, color=colors_time[i], linewidth=2,
             label=f't = {t_frac:.2f}T', alpha=0.8)

ax2.axhline(0, color='black', linestyle='-', linewidth=0.5, alpha=0.5)
ax2.set_xlabel('Position along Membrane (μm)', fontsize=12)
ax2.set_ylabel('Strain (%)', fontsize=12)
ax2.set_title('Strain Wave Propagation (O2 Clock)', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=10)
ax2.set_xlim([0, 10])

wavelength = 2 * np.pi / k_membrane
print(f"  Strain amplitude: {epsilon_amplitude*100:.1f}%")
print(f"  Wavelength: {wavelength:.2f} μm")
print(f"  Period: {T_O2*1e3:.2f} ms")

#############################################################################
# Chart 3: Mechanical Wave Propagation (2D space-time)
#############################################################################
print("\nChart 3: Mechanical Wave Propagation")

ax3 = fig.add_subplot(2, 2, 3)

# Space-time grid
x_wave = np.linspace(0, 10, 100)  # μm
t_wave = np.linspace(0, 5e-3, 100)  # ms
X_wave, T_wave = np.meshgrid(x_wave, t_wave)

# Mechanical wave (shear wave)
c_shear = np.sqrt(G_shear / 1050)  # Shear wave speed (m/s)
k_wave = omega_O2 / c_shear  # Wave number (m^-1)

# Displacement wave
u = np.sin(k_wave * X_wave * 1e-6 - omega_O2 * T_wave)

# Plot
contour = ax3.contourf(X_wave, T_wave * 1e3, u, levels=20, cmap='RdBu_r')
fig.colorbar(contour, ax=ax3, label='Displacement (normalized)')

# Add wave fronts
ax3.contour(X_wave, T_wave * 1e3, u, levels=[0], colors='black', linewidths=2)

ax3.set_xlabel('Position (μm)', fontsize=12)
ax3.set_ylabel('Time (ms)', fontsize=12)
ax3.set_title(f'Shear Wave Propagation (c = {c_shear:.2f} m/s)', fontsize=14, fontweight='bold')

print(f"  Shear wave speed: {c_shear:.2f} m/s")
print(f"  Wave number: {k_wave:.2e} m^-1")
print(f"  Wavelength: {2*np.pi/k_wave*1e6:.2f} μm")

#############################################################################
# Chart 4: Viscoelastic Response (2D)
#############################################################################
print("\nChart 4: Viscoelastic Response to O2 Clock")

ax4 = fig.add_subplot(2, 2, 4)

# Frequency range
freq = np.logspace(1, 5, 1000)  # Hz
omega = 2 * np.pi * freq

# Maxwell model: G* = G * (iωτ) / (1 + iωτ)
# where τ = η/G is relaxation time
tau_relax = eta / G_shear

# Storage modulus (elastic)
G_storage = G_shear * (omega * tau_relax)**2 / (1 + (omega * tau_relax)**2)

# Loss modulus (viscous)
G_loss = G_shear * (omega * tau_relax) / (1 + (omega * tau_relax)**2)

# Loss tangent
tan_delta = G_loss / (G_storage + 1e-10)

# Plot
ax4.loglog(freq, G_storage, 'b-', linewidth=2.5, label="G' (storage)")
ax4.loglog(freq, G_loss, 'r-', linewidth=2.5, label='G" (loss)')

# Mark O2 clock frequency
f_O2 = omega_O2 / (2 * np.pi)
ax4.axvline(f_O2, color='green', linestyle='--', linewidth=2,
            label=f'O2 clock ({f_O2:.1f} Hz)')

# Mark crossover frequency
f_crossover = 1 / (2 * np.pi * tau_relax)
ax4.axvline(f_crossover, color='orange', linestyle=':', linewidth=2,
            label=f'Crossover ({f_crossover:.1f} Hz)')

ax4.set_xlabel('Frequency (Hz)', fontsize=12)
ax4.set_ylabel('Modulus (Pa)', fontsize=12)
ax4.set_title('Viscoelastic Response (Maxwell Model)', fontsize=14, fontweight='bold')
ax4.grid(True, alpha=0.3, which='both')
ax4.legend(fontsize=10)
ax4.set_xlim([10, 1e5])

print(f"  Relaxation time: {tau_relax*1e3:.2f} ms")
print(f"  Crossover frequency: {f_crossover:.1f} Hz")
print(f"  At O2 clock ({f_O2:.1f} Hz): {'Viscous' if f_O2 < f_crossover else 'Elastic'} regime")

#############################################################################
# Save figure
#############################################################################
plt.tight_layout()
output_path = 'validation_results/mechanical_modality_panel.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"\nPanel saved to: {output_path}")

plt.close()

#############################################################################
# Summary
#############################################################################
print("\n" + "=" * 70)
print("SUMMARY: Mechanical Modality in Cellular Colloid")
print("=" * 70)
print("1. Stress distribution:")
print(f"   - Turgor pressure: {P_turgor} Pa")
print(f"   - Max stress: {np.max(sigma_r):.1f} Pa")
print("   - Radial decay from membrane deformation")
print("\n2. Strain from compartment formation:")
print(f"   - Amplitude: {epsilon_amplitude*100:.1f}%")
print(f"   - Wavelength: {wavelength:.2f} μm")
print(f"   - Propagates at O2 clock frequency")
print("\n3. Mechanical wave propagation:")
print(f"   - Shear wave speed: {c_shear:.2f} m/s")
print(f"   - Wavelength: {2*np.pi/k_wave*1e6:.2f} μm")
print("   - Synchronized with O2 clock")
print("\n4. Viscoelastic response:")
print(f"   - Relaxation time: {tau_relax*1e3:.2f} ms")
print(f"   - Crossover: {f_crossover:.1f} Hz")
print(f"   - At O2 clock: {'Viscous' if f_O2 < f_crossover else 'Elastic'} regime")
print("\nKEY INSIGHT: Mechanical modality propagates through cellular colloid")
print("             as stress/strain waves synchronized with O2 clock.")
print("             Viscoelastic response shows viscous behavior at O2")
print("             frequency. Membrane deformation creates strain waves")
print("             that propagate as shear waves through cytoplasm.")
print("=" * 70)
