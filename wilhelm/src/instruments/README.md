# Virtual Categorical Spectrometry Suite

## Overview

This directory contains the virtual instrument suite for validating partition-based cellular state equations. The instruments exist as **categorical apertures** that only manifest during measurement, consistent with the principle that molecules occupy partition states without continuous instrumentation.

## Instruments

### 1. Virtual Categorical Spectrometer
**File:** `virtual_spectrometer.py`

Primary measurement instrument that:
- Measures partition coordinates (n, ℓ, m, s) from frequency/energy
- Transforms partition coordinates to S-entropy coordinates (S_k, S_t, S_e)
- Activates secondary instruments for sequential validation
- Reduces ambiguity from ~10⁶⁰ states to unique molecular identification

**Key Classes:**
- `PartitionCoordinates`: (n, ℓ, m, s) with 2n² capacity theorem
- `SEntropyCoordinates`: (S_k, S_t, S_e) ∈ [0,1]³
- `VirtualCategoricalSpectrometer`: Main measurement interface

### 2. Validation Suite
**File:** `validation_suite.py`

Comprehensive validation framework that generates:
- **Equations of State** (5 regimes): 4-panel plots for each regime
  - Neutral gas (ideal gas)
  - Plasma (Coulomb coupling)
  - Degenerate matter (Fermi pressure)
  - Relativistic gas
  - Bose-Einstein condensate
  
- **Categorical Dynamics** (3 analyses):
  - Categorical pendulum (∂²θ/∂p² dynamics)
  - S-entropy trajectories in [0,1]³
  - Memory reset at categorical boundaries
  
- **Phase Space Analysis** (3 analyses):
  - Eigenvalue structure and stability
  - Phase plane topology (nullclines, separatrix, fixed points)
  - Potential energy landscapes

**Key Class:**
- `ValidationSuite`: Main validation orchestrator

## Running Validation

### Quick Start

```bash
cd wilhelm/src/instruments
python run_validation.py
```

This generates 11 high-resolution plots in `validation_results/`:

**Equations of State:**
- `eos_neutral_gas.png`
- `eos_plasma.png`
- `eos_degenerate.png`
- `eos_relativistic.png`
- `eos_bose_einstein.png`

**Categorical Dynamics:**
- `categorical_pendulum.png`
- `sentropy_trajectory.png`
- `memory_reset.png`

**Phase Space Analysis:**
- `eigenvalue_analysis.png`
- `phase_plane.png`
- `potential_energy_3d.png`

### Programmatic Usage

```python
from instruments import ValidationSuite

# Create suite
suite = ValidationSuite(output_dir="my_results")

# Run all validations
suite.validate_all()

# Or run specific validations
suite.validate_equations_of_state()
suite.validate_categorical_dynamics()
suite.analyze_phase_space()
```

## Validation Results

See `validation_results/VALIDATION_REPORT.md` for detailed analysis of all validation plots.

**Summary:** All 11 validation tests passed successfully ✓

## Theoretical Foundation

### Foundational Axioms
1. **Bounded Phase Space**: All observables confined to finite intervals
2. **Categorical Observation**: Measurements occur in discrete categories

### Key Concepts

**Partition Coordinates (n, ℓ, m, s)**
- Derived from bounded phase space
- Correspond to quantum numbers
- Capacity theorem: 2n² states per shell

**S-Entropy Coordinates (S_k, S_t, S_e)**
- Knowledge entropy: S_k ∈ [0,1]
- Temporal entropy: S_t ∈ [0,1]
- Evolution entropy: S_e ∈ [0,1]
- Native 3D encoding space

**Categorical Dynamics**
- Derivatives with respect to categorical transitions: ∂/∂c
- Derivatives with respect to partition refinements: ∂/∂p
- Derivatives with respect to oscillation phases: ∂/∂φ
- Gyrometric derivatives: ∂/∂j (oxygen rotational quantum number)

**Categorical Memory Reset**
- State resets at each category boundary
- History-independent dynamics
- Analogous to Van Deemter plate theory
- Proof of hierarchical oxygen master clock

**Oxygen Master Clock**
- O₂ rotational states provide continuous, hierarchical clock
- Frequency partitioning: ω_n = (n/N) × ω_O₂
- Cellular processes synchronize to specific harmonics
- Enables efficient capacity and rapid state transitions

## Physical Constants

The validation suite uses CODATA 2018 values:
- Planck constant: h = 6.62607015×10⁻³⁴ J·s
- Boltzmann constant: k_B = 1.380649×10⁻²³ J/K
- Electron mass: m_e = 9.1093837015×10⁻³¹ kg
- Speed of light: c = 299792458 m/s

## Plot Specifications

All plots are generated at:
- **Resolution:** 300 DPI (publication quality)
- **Format:** PNG with tight bounding boxes
- **Size:** 14" × 10" (4200 × 3000 pixels)
- **Grid:** 2×2 panel layout for comprehensive analysis

## Dependencies

```
numpy >= 1.26
matplotlib >= 3.8
```

## Future Extensions

### Additional Instruments (planned)
- `vibration_analyzer.py`: Vibrational spectroscopy
- `dielectric_analyzer.py`: Capacitative dielectric analysis
- `em_field_mapper.py`: Electronic field mapping

### Additional Validations (planned)
- Protein folding dynamics (GroEL phase-locking)
- Membrane transport apertures (substrate selection)
- Categorical thermometry (zeptokelvin regime)
- Metabolic GPS (cellular triangulation)

## References

The validation suite implements equations derived in:
- `wilhelm/docs/cellular-state-equations/partition-based-cellular-state-equations.tex`

Key sections:
1. Partition Coordinates (Section 1)
2. Categorical Dynamics (Section 2)
3. Equations of State (Section 3)
4. Transport Phenomena (Section 4)

## License

Part of the Hegel framework for partition-based cellular state equations.

---

**Last Updated:** January 9, 2026  
**Version:** 1.0  
**Status:** All validations passing ✓
