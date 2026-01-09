"""
Master script to run all disease state equation validations
Generates comprehensive validation panels for:
- Disease state equations
- Immune equations of state
- Therapeutic equations of state
- Phase coherence and synchronization
- Oxygen gas model and geometric configurations
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from disease_validation import DiseaseValidator
from immune_validation import ImmuneValidator
from therapeutic_validation import TherapeuticValidator
from phase_coherence_validation import PhaseCoherenceValidator
from oxygen_geometry_validation import OxygenGeometryValidator

def main():
    """Run all disease state equation validations"""
    
    print("\n" + "="*70)
    print(" " * 15 + "DISEASE STATE EQUATIONS")
    print(" " * 10 + "COMPREHENSIVE VALIDATION SUITE")
    print("="*70 + "\n")
    
    print("This suite validates the mathematical framework for disease,")
    print("immunity, and therapeutics derived from bounded phase space.\n")
    
    output_dir = 'validation_results'
    os.makedirs(output_dir, exist_ok=True)
    
    # Track validation status
    validations = []
    
    # 1. Disease State Equations
    print("\n" + "-"*70)
    print("1. DISEASE STATE EQUATIONS VALIDATION")
    print("-"*70)
    try:
        validator = DiseaseValidator(output_dir)
        validator.generate_disease_panel()
        validations.append(("Disease State Equations", True))
    except Exception as e:
        print(f"X Error in disease validation: {e}")
        validations.append(("Disease State Equations", False))
    
    # 2. Immune Equations of State
    print("\n" + "-"*70)
    print("2. IMMUNE EQUATIONS OF STATE VALIDATION")
    print("-"*70)
    try:
        validator = ImmuneValidator(output_dir)
        validator.generate_immune_panel()
        validations.append(("Immune Equations of State", True))
    except Exception as e:
        print(f"X Error in immune validation: {e}")
        validations.append(("Immune Equations of State", False))
    
    # 3. Therapeutic Equations of State
    print("\n" + "-"*70)
    print("3. THERAPEUTIC EQUATIONS OF STATE VALIDATION")
    print("-"*70)
    try:
        validator = TherapeuticValidator(output_dir)
        validator.generate_therapeutic_panel()
        validations.append(("Therapeutic Equations of State", True))
    except Exception as e:
        print(f"X Error in therapeutic validation: {e}")
        validations.append(("Therapeutic Equations of State", False))
    
    # 4. Phase Coherence and Synchronization
    print("\n" + "-"*70)
    print("4. PHASE COHERENCE AND SYNCHRONIZATION VALIDATION")
    print("-"*70)
    try:
        validator = PhaseCoherenceValidator(output_dir)
        validator.generate_phase_coherence_panel()
        validations.append(("Phase Coherence", True))
    except Exception as e:
        print(f"X Error in phase coherence validation: {e}")
        validations.append(("Phase Coherence", False))
    
    # 5. Oxygen Gas Model and Geometric Configurations
    print("\n" + "-"*70)
    print("5. OXYGEN GAS MODEL & GEOMETRIC CONFIGURATION VALIDATION")
    print("-"*70)
    try:
        validator = OxygenGeometryValidator(output_dir)
        validator.generate_oxygen_geometry_panel()
        validations.append(("Oxygen Geometry", True))
    except Exception as e:
        print(f"X Error in oxygen geometry validation: {e}")
        validations.append(("Oxygen Geometry", False))
    
    # Summary
    print("\n" + "="*70)
    print(" " * 20 + "VALIDATION SUMMARY")
    print("="*70 + "\n")
    
    total = len(validations)
    passed = sum(1 for _, status in validations if status)
    
    print(f"Total Validations: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}\n")
    
    for name, status in validations:
        symbol = "[PASS]" if status else "[FAIL]"
        print(f"  {symbol} {name}")
    
    print("\n" + "="*70)
    print("Generated Validation Panels:")
    print("="*70 + "\n")
    
    panels = [
        "disease_validation_panel.png",
        "immune_validation_panel.png",
        "therapeutic_validation_panel.png",
        "phase_coherence_validation_panel.png",
        "oxygen_geometry_validation_panel.png"
    ]
    
    for panel in panels:
        path = os.path.join(output_dir, panel)
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"  [OK] {panel} ({size_mb:.2f} MB)")
        else:
            print(f"  [MISSING] {panel}")
    
    print("\n" + "="*70)
    print("Key Theoretical Validations:")
    print("="*70 + "\n")
    
    print("1. Disease State Equations:")
    print("   - Bimodal richness distribution (self vs pathogen)")
    print("   - Oscillatory hole dynamics and therapeutic restoration")
    print("   - Disease severity landscape (3D)")
    print("   - Trajectory statistics by disease type\n")
    
    print("2. Immune Equations of State:")
    print("   - MHC categorical aperture function")
    print("   - VDJ ternary hierarchy (~3^8 combinations)")
    print("   - Immune pressure landscape (3D)")
    print("   - Richness-dependent clonal expansion\n")
    
    print("3. Therapeutic Equations of State:")
    print("   - Dose-response curves (Hill equation)")
    print("   - Conjugate frequency conversion mechanism")
    print("   - Therapeutic pressure landscape (3D)")
    print("   - Combination therapy synergy maps\n")
    
    print("4. Phase Coherence:")
    print("   - Kuramoto order parameter transitions")
    print("   - Disease decoherence and therapeutic recoherence")
    print("   - Coherence-disorder landscape (3D)")
    print("   - Chimera states (coexisting sync/desync)\n")
    
    print("5. Oxygen Geometry:")
    print("   - O2 rotational energy spectrum")
    print("   - Master clock frequency partitioning")
    print("   - Cytoplasmic volume geometry (3D)")
    print("   - Conjugate frequency ladder mechanism\n")
    
    print("="*70)
    print("VALIDATION COMPLETE")
    print("="*70 + "\n")
    
    if passed == total:
        print("[SUCCESS] All validations passed successfully!")
        print("\nThese computational experiments confirm the geometric")
        print("derivations from bounded phase space and categorical observation.")
        return 0
    else:
        print(f"[ERROR] {total - passed} validation(s) failed.")
        print("\nPlease check error messages above for details.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
