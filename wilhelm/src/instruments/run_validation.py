"""
Run Validation Suite for Partition-Based Cellular State Equations

Generates all validation plots for equations of state and categorical dynamics.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from instruments.validation_suite import run_validation

if __name__ == "__main__":
    print("\n" + "="*70)
    print("VALIDATION SUITE: Partition-Based Cellular State Equations")
    print("="*70 + "\n")
    
    # Run validation
    output_dir = os.path.join(os.path.dirname(__file__), "validation_results")
    suite = run_validation(output_dir=output_dir)
    
    print("\n" + "="*70)
    print(f"[SUCCESS] Validation complete!")
    print(f"[SUCCESS] Results saved to: {output_dir}/")
    print("="*70 + "\n")
    
    print("Generated plots:")
    print("  Equations of State (5 regimes):")
    print("    - eos_neutral_gas.png")
    print("    - eos_plasma.png")
    print("    - eos_degenerate.png")
    print("    - eos_relativistic.png")
    print("    - eos_bose_einstein.png")
    print("\n  Categorical Dynamics:")
    print("    - categorical_pendulum.png")
    print("    - sentropy_trajectory.png")
    print("    - memory_reset.png")
    print("\n  Phase Space Analysis:")
    print("    - eigenvalue_analysis.png")
    print("    - phase_plane.png")
    print("    - potential_energy_3d.png")
    print("\n" + "="*70 + "\n")
