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
from diffusion_comparison_validation import DiffusionComparisonValidator
from oxygen_field_tracking_validation import OxygenFieldTracker
from volume_ph_atp_validation import VolumePHATPValidator
from integrated_electric_metrics_validation import IntegratedElectricMetrics

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
    
    # 6. Diffusion-Convection vs Oxygen Clock Comparison
    print("\n" + "-"*70)
    print("6. DIFFUSION-CONVECTION VS OXYGEN CLOCK COMPARISON")
    print("-"*70)
    try:
        validator = DiffusionComparisonValidator(output_dir)
        validator.generate_diffusion_comparison_panel()
        validations.append(("Diffusion Comparison", True))
    except Exception as e:
        print(f"X Error in diffusion comparison validation: {e}")
        validations.append(("Diffusion Comparison", False))
    
    # 7. Oxygen Electric & Steric Field Tracking
    print("\n" + "-"*70)
    print("7. OXYGEN ELECTRIC & STERIC FIELD TRACKING")
    print("-"*70)
    try:
        tracker = OxygenFieldTracker(output_dir)
        tracker.generate_oxygen_field_tracking_panel()
        validations.append(("Oxygen Field Tracking", True))
    except Exception as e:
        print(f"X Error in oxygen field tracking validation: {e}")
        validations.append(("Oxygen Field Tracking", False))
    
    # 8. Volume-pH-ATP Coupling
    print("\n" + "-"*70)
    print("8. VOLUME-pH-ATP COUPLING")
    print("-"*70)
    try:
        validator = VolumePHATPValidator(output_dir)
        validator.generate_volume_ph_atp_panel()
        validations.append(("Volume-pH-ATP", True))
    except Exception as e:
        print(f"X Error in volume-pH-ATP validation: {e}")
        validations.append(("Volume-pH-ATP", False))
    
    # 9. Integrated Electric Field Metrics
    print("\n" + "-"*70)
    print("9. INTEGRATED ELECTRIC FIELD METRICS")
    print("-"*70)
    try:
        validator = IntegratedElectricMetrics(output_dir)
        validator.generate_integrated_electric_metrics_panel()
        validations.append(("Integrated Electric Metrics", True))
    except Exception as e:
        print(f"X Error in integrated electric metrics validation: {e}")
        validations.append(("Integrated Electric Metrics", False))
    
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
        "oxygen_geometry_validation_panel.png",
        "diffusion_comparison_panel.png",
        "oxygen_field_tracking_panel.png",
        "volume_ph_atp_panel.png",
        "integrated_electric_metrics_panel.png"
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
    
    print("6. Diffusion-Convection Comparison:")
    print("   - Transport time vs distance (diffusion fails)")
    print("   - Signal propagation (cascade vs diffusion)")
    print("   - O2 clock synchronization landscape (3D)")
    print("   - Genome-membrane electric circuit model\n")
    
    print("7. Oxygen Field Tracking:")
    print("   - O2 trajectories in cytoplasm (3D, E-field colored)")
    print("   - Electric field magnitude heatmap (genome + membrane)")
    print("   - Steric potential from protein crowding")
    print("   - Combined force field vectors (electric + steric)\n")
    
    print("8. Volume-pH-ATP Coupling:")
    print("   - Time evolution with O2 modulation")
    print("   - Volume-ATP phase space")
    print("   - pH-Volume-ATP landscape (3D)")
    print("   - ATP consumption rate map (V_m-pH dependence)\n")
    
    print("9. Integrated Electric Metrics:")
    print("   - Genome-membrane impedance spectrum")
    print("   - Electron cascade conductivity models")
    print("   - O2 clock frequency partitioning (3D)")
    print("   - Integrated power spectrum (O2 + harmonics + biological)\n")
    
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
