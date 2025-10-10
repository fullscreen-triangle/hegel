#!/usr/bin/env python3
"""
Personal Pharmacology Theory Validation Script

This script validates your computational pharmacology theory using your personal:
1. Lithium blood level measurements 
2. Whole genome sequencing data

ENHANCED VERSION supports advanced theoretical components:
- Fuzzy Evidence Processing (your Dante Labs variants)
- Bayesian Molecular Networks (spectral + structural + pathway evidence)
- Oxygen-Enhanced Information Processing (paramagnetic oscillatory theory)
- Quantum Membrane Transport (lithium transport analysis)

Run this with your real data to test whether oscillatory hole semiconductor theory 
and BMD equivalence make better predictions than classical pharmacokinetics!
"""

import sys
import os
import json
import argparse
from typing import Dict, List

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from validation.pharmacology_validation import create_personal_pharmacology_validation

def load_personal_data() -> tuple:
    """Load personal lithium and genomic data"""
    
    print("="*60)
    print("PERSONAL PHARMACOLOGY THEORY VALIDATION")
    print("="*60)
    print("Testing oscillatory hole semiconductor theory with YOUR data!")
    print()
    
    # Try to load lithium data
    lithium_file = "personal_data_templates/lithium_data_template.json"
    genomic_file = "personal_data_templates/genomic_data_template.json"
    
    lithium_data = None
    genomic_data = None
    
    # Load lithium measurements
    if os.path.exists(lithium_file):
        try:
            with open(lithium_file, 'r') as f:
                data = json.load(f)
                lithium_data = data.get('lithium_measurements', [])
                print(f"✓ Loaded {len(lithium_data)} lithium measurements")
        except Exception as e:
            print(f"Error loading lithium data: {e}")
    else:
        print(f"❌ Lithium data file not found: {lithium_file}")
        print("Please edit the template with your real measurements!")
        return None, None
    
    # Load genomic data  
    if os.path.exists(genomic_file):
        try:
            with open(genomic_file, 'r') as f:
                data = json.load(f)
                genomic_data = data.get('genomic_variants', {})
                gene_count = len([g for g, variants in genomic_data.items() if variants])
                print(f"✓ Loaded genomic variants for {gene_count} genes")
        except Exception as e:
            print(f"Warning: Could not load genomic data: {e}")
            print("Continuing without genomic data...")
    else:
        print(f"⚠️ Genomic data file not found: {genomic_file}")
        print("Continuing without genomic data (reduced accuracy)")
    
    return lithium_data, genomic_data

def validate_data_quality(lithium_data: List[Dict]) -> bool:
    """Check if the data looks real (not template examples)"""
    
    if not lithium_data:
        return False
    
    # Check if data looks like template examples
    template_indicators = [
        all(m.get('dose_mg') == 600 for m in lithium_data),  # All same dose
        len(lithium_data) == 5,  # Exactly 5 measurements (template size)
        any('example' in str(m.get('notes', '')).lower() for m in lithium_data)
    ]
    
    if sum(template_indicators) >= 2:
        print("\n⚠️ WARNING: Data appears to be template examples!")
        print("Please replace the template data with your actual measurements.")
        print("The validation will run but results may not be meaningful.")
        
        response = input("\nContinue anyway? (y/n): ")
        return response.lower().startswith('y')
    
    return True

def interpret_results(results: Dict) -> None:
    """Interpret and explain the validation results"""
    
    print("\n" + "="*60)
    print("THEORY VALIDATION RESULTS")
    print("="*60)
    
    summary = results['summary']
    
    # Overall performance
    theoretical_r2 = summary['overall_performance']['theoretical_r2']
    classical_r2 = summary['overall_performance']['classical_r2']
    improvement = summary['overall_performance']['improvement_percentage']
    
    print(f"\n📊 PREDICTION ACCURACY:")
    print(f"   Your Theory R²: {theoretical_r2:.3f}")
    print(f"   Classical PK R²: {classical_r2:.3f}")
    print(f"   Improvement: {improvement:+.1f}%")
    
    if improvement > 10:
        print("   🎉 EXCELLENT! Your theory significantly outperforms classical pharmacokinetics!")
    elif improvement > 0:
        print("   ✅ GOOD! Your theory shows improvement over classical models.")
    else:
        print("   ⚠️ Theory needs refinement - classical model performs better.")
    
    # Theory components
    theory_val = summary['theory_validation']
    components_passed = theory_val['components_passed']
    validation_rate = theory_val['validation_rate']
    
    print(f"\n🔬 THEORY COMPONENT VALIDATION:")
    print(f"   Components Passed: {components_passed}/3")
    print(f"   Validation Rate: {validation_rate:.1%}")
    
    if validation_rate >= 0.67:
        print("   ✅ STRONG theoretical support - multiple components validated!")
    elif validation_rate >= 0.33:
        print("   ⚠️ MODERATE theoretical support - some refinement needed.")
    else:
        print("   ❌ WEAK theoretical support - major revision required.")
    
    # Specific theory validations
    theory_validations = results['theory_validations']
    
    print(f"\n🔍 DETAILED COMPONENT ANALYSIS:")
    
    # Oscillatory holes
    if 'oscillatory_holes' in theory_validations:
        holes = theory_validations['oscillatory_holes']
        if holes.get('validation_passed', False):
            print("   ✅ Oscillatory Hole Theory: VALIDATED")
            print(f"      Hole strength: {holes['avg_hole_strength']:.3f}")
        else:
            print("   ❌ Oscillatory Hole Theory: NEEDS WORK")
    
    # Gear ratios
    if 'gear_ratios' in theory_validations:
        gears = theory_validations['gear_ratios']
        if gears.get('validation_passed', False):
            print("   ✅ Gear Ratio Theory: VALIDATED")
            print(f"      Average efficiency: {gears['avg_efficiency']:.3f}")
        else:
            print("   ❌ Gear Ratio Theory: NEEDS WORK")
    
    # BMD acceleration
    if 'bmd_acceleration' in theory_validations:
        bmd = theory_validations['bmd_acceleration']
        if bmd.get('validation_passed', False):
            print("   ✅ BMD Acceleration: VALIDATED")
            print(f"      Acceleration factor: {bmd['acceleration_factor']:.1f}x")
        else:
            print("   ❌ BMD Acceleration: OUTSIDE EXPECTED RANGE")
    
    # Clinical relevance
    clinical = summary['clinical_relevance']
    print(f"\n🏥 CLINICAL RELEVANCE:")
    print(f"   Prediction Accuracy: {clinical['prediction_accuracy'].upper()}")
    print(f"   Clinical Utility: {'YES' if clinical['clinical_utility'] else 'NEEDS IMPROVEMENT'}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    for rec in summary['recommendations']:
        print(f"   {rec}")
    
    print(f"\n" + "="*60)
    
    if validation_rate >= 0.67 and improvement > 5:
        print("🎉 CONGRATULATIONS! Your computational pharmacology theory shows")
        print("   strong validation against your personal clinical data!")
        print("   Consider submitting this as a proof-of-concept study.")
    elif validation_rate >= 0.33 and improvement > 0:
        print("✅ PROMISING RESULTS! Your theory shows merit but could benefit")
        print("   from parameter refinement and additional data collection.")
    else:
        print("🔬 INTERESTING! While not fully validated, this analysis provides")
        print("   valuable insights for theory development and refinement.")

def interpret_advanced_results(results: Dict, use_advanced: bool) -> None:
    """Enhanced results interpretation including advanced components"""
    
    print("\n" + "="*70)
    print("THEORY VALIDATION RESULTS")
    print("="*70)
    
    summary = results['summary']
    
    # Overall performance
    theoretical_r2 = summary['overall_performance']['theoretical_r2']
    classical_r2 = summary['overall_performance']['classical_r2']
    improvement = summary['overall_performance']['improvement_percentage']
    
    print(f"\n📊 PREDICTION ACCURACY:")
    print(f"   Your Theory R²: {theoretical_r2:.3f}")
    print(f"   Classical PK R²: {classical_r2:.3f}")
    print(f"   Improvement: {improvement:+.1f}%")
    
    if improvement > 10:
        print("   🎉 EXCELLENT! Your theory significantly outperforms classical pharmacokinetics!")
    elif improvement > 0:
        print("   ✅ GOOD! Your theory shows improvement over classical models.")
    else:
        print("   ⚠️ Theory needs refinement - classical model performs better.")
    
    # Advanced components results
    if use_advanced and 'advanced_validation' in results:
        advanced = results['advanced_validation']
        
        print(f"\n🚀 ADVANCED THEORETICAL COMPONENTS:")
        
        # Fuzzy Logic Processing
        if 'fuzzy_variants' in advanced:
            fuzzy_variants = advanced['fuzzy_variants']
            print(f"   🔬 Fuzzy Evidence Processing:")
            print(f"      Genomic variants processed: {len(fuzzy_variants)}")
            
            if fuzzy_variants:
                high_impact = sum(1 for fv in fuzzy_variants if fv['fuzzy_evidence']['dominant_membership'][1] > 0.5)
                print(f"      High-impact variants: {high_impact}/{len(fuzzy_variants)}")
                
                for fv in fuzzy_variants[:3]:  # Show top 3
                    fuzzy_set = fv['fuzzy_evidence']['fuzzy_set']
                    dominant = fv['fuzzy_evidence']['dominant_membership']
                    print(f"         {fv['gene']}: {dominant[0]} ({dominant[1]:.3f})")
        
        # Bayesian Network Analysis
        if 'bayesian_posterior' in advanced:
            bayesian = advanced['bayesian_posterior']
            responsive_prob = bayesian.get('lithium_responsive', 0)
            print(f"   🧠 Bayesian Molecular Network:")
            print(f"      Lithium responsiveness probability: {responsive_prob:.3f}")
            
            if responsive_prob > 0.8:
                print("      🎯 HIGH confidence in positive response")
            elif responsive_prob > 0.6:
                print("      ✅ MODERATE confidence in positive response")
            else:
                print("      ⚠️ LOW confidence - consider dosing adjustments")
        
        # Oxygen Enhancement
        if 'oxygen_enhancement' in advanced:
            oxygen = advanced['oxygen_enhancement']
            improvement_pct = oxygen.get('improvement_percent', 0)
            oid = oxygen.get('OID', 0)
            print(f"   💨 Oxygen-Enhanced Information Processing:")
            print(f"      Therapeutic enhancement: {improvement_pct:.1f}%")
            print(f"      Information density: {oid:.2e} bits/molecule/s")
            
            if improvement_pct > 15:
                print("      🌟 SIGNIFICANT atmospheric enhancement effect!")
            elif improvement_pct > 5:
                print("      ✅ MODERATE atmospheric enhancement")
            else:
                print("      ⚠️ MINIMAL atmospheric enhancement detected")
        
        # Quantum Transport
        if 'quantum_transport' in advanced:
            quantum = advanced['quantum_transport']
            transport = quantum.get('transport_efficiency', {})
            quantum_advantage = transport.get('quantum_advantage', 1)
            resolution = quantum.get('molecular_resolution', 0)
            print(f"   ⚛️ Quantum Membrane Transport:")
            print(f"      Quantum advantage: {quantum_advantage:.1f}×")
            print(f"      Molecular resolution: {resolution:.3f}")
            
            if quantum_advantage > 3:
                print("      🚀 STRONG quantum transport advantage!")
            elif quantum_advantage > 1.5:
                print("      ✅ MODERATE quantum advantage")
            else:
                print("      ⚠️ LIMITED quantum advantage - check parameters")
        
        # Combined Prediction Score
        if 'combined_prediction' in advanced:
            combined = advanced['combined_prediction']
            combined_score = combined.get('prediction_score', 0)
            print(f"\n🎯 COMBINED THEORETICAL PREDICTION: {combined_score:.3f}")
            
            if combined_score > 0.8:
                print("   🎉 EXCEPTIONAL - Advanced theory strongly validated!")
                print("   This could be groundbreaking for computational pharmacology!")
            elif combined_score > 0.6:
                print("   ✅ GOOD - Advanced components show promise!")
            elif combined_score > 0.4:
                print("   🔄 MODERATE - Theory shows potential but needs refinement")
            else:
                print("   ⚠️ LOW - Significant revision needed for advanced components")
    
    # Use enhanced summary if available
    if 'enhanced_summary' in results:
        summary_to_use = results['enhanced_summary']
    else:
        summary_to_use = summary
    
    # Theory components (standard)
    theory_val = summary_to_use['theory_validation']
    components_passed = theory_val['components_passed']
    validation_rate = theory_val['validation_rate']
    
    print(f"\n🔬 STANDARD THEORY COMPONENT VALIDATION:")
    print(f"   Components Passed: {components_passed}/3")
    print(f"   Validation Rate: {validation_rate:.1%}")
    
    if validation_rate >= 0.67:
        print("   ✅ STRONG theoretical support!")
    elif validation_rate >= 0.33:
        print("   ⚠️ MODERATE theoretical support")
    else:
        print("   ❌ WEAK theoretical support")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    for rec in summary_to_use.get('recommendations', []):
        print(f"   {rec}")
    
    print(f"\n" + "="*70)
    
    # Final assessment
    final_score = combined_score if use_advanced and 'combined_prediction' in advanced else theoretical_r2
    
    if use_advanced and final_score > 0.75 and improvement > 10:
        print("🎉 BREAKTHROUGH! Your advanced computational pharmacology framework")
        print("   shows exceptional validation against personal clinical data!")
        print("   This represents a paradigm shift in drug response prediction.")
        print("   Consider publishing this as a proof-of-concept study!")
    elif final_score > 0.6 and improvement > 5:
        print("🚀 PROMISING! Your theoretical framework shows strong merit.")
        print("   With additional data and refinement, this could be revolutionary.")
    elif final_score > 0.4:
        print("🔬 INTERESTING! While not fully validated, this provides valuable")
        print("   insights for computational pharmacology development.")
    else:
        print("🛠️ DEVELOPMENTAL STAGE: Theory needs significant refinement")
        print("   but the foundational approach shows potential.")

def main():
    """Enhanced main validation function with advanced component support"""
    
    parser = argparse.ArgumentParser(
        description="Validate computational pharmacology theory with personal clinical data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard validation (oscillatory holes + gear ratios)
  python validate_my_pharmacology_theory.py
  
  # Advanced validation (includes fuzzy logic, Bayesian networks, quantum transport)
  python validate_my_pharmacology_theory.py --advanced
  
  # Custom environmental conditions
  python validate_my_pharmacology_theory.py --advanced --temp 308 --oxygen 0.18
        """
    )
    
    parser.add_argument('--advanced', action='store_true',
                      help='Enable advanced theoretical components (fuzzy logic, Bayesian, quantum)')
    parser.add_argument('--temp', type=float, default=310,
                      help='Body temperature in Kelvin (default: 310)')
    parser.add_argument('--magnetic-field', type=float, default=1e-4,
                      help='Cellular magnetic field in Tesla (default: 1e-4)')
    parser.add_argument('--coherence-time', type=float, default=100e-6,
                      help='Quantum coherence time in seconds (default: 100e-6)')
    parser.add_argument('--oxygen', type=float, default=0.21,
                      help='Oxygen availability fraction (default: 0.21)')
    parser.add_argument('--interactive', action='store_true',
                      help='Run in interactive mode with data quality checks')
    
    args = parser.parse_args()
    
    # Check if data files exist
    if not os.path.exists("personal_data_templates/"):
        print("❌ Personal data templates directory not found!")
        print("Please make sure you're running this from the wilhelm/ directory.")
        return
    
    # Load personal data
    lithium_data, genomic_data = load_personal_data()
    
    if not lithium_data:
        print("\n❌ No lithium data available for validation.")
        print("Please edit personal_data_templates/lithium_data_template.json")
        return
    
    # Validate data quality (only in interactive mode)
    if args.interactive and not validate_data_quality(lithium_data):
        print("Validation cancelled.")
        return
    
    # Set up environmental conditions
    environmental_conditions = {
        'temperature': args.temp,
        'magnetic_field': args.magnetic_field,
        'coherence_time': args.coherence_time,
        'oxygen_availability': args.oxygen
    }
    
    # Print validation setup
    print(f"\n🚀 Running theoretical validation...")
    if args.advanced:
        print("🔬 ADVANCED MODE: Testing full theoretical framework")
        print("   • Fuzzy Evidence Processing")
        print("   • Bayesian Molecular Networks")
        print("   • Oxygen-Enhanced Information Processing")
        print("   • Quantum Membrane Transport")
    else:
        print("📊 STANDARD MODE: Testing core theoretical components")
        print("   • Oscillatory Hole Semiconductor Theory")
        print("   • Biological Gear Ratios")
        print("   • BMD Acceleration")
    
    print("This may take a moment...")
    
    try:
        # Run the validation
        results = create_personal_pharmacology_validation(
            lithium_data=lithium_data,
            genomic_data=genomic_data,
            use_advanced_components=args.advanced,
            environmental_conditions=environmental_conditions
        )
        
        # Interpret results
        interpret_advanced_results(results, args.advanced)
        
        # Save results
        filename_prefix = "advanced" if args.advanced else "standard"
        output_file = f'{filename_prefix}_pharmacology_validation_results.json'
        
        with open(output_file, 'w') as f:
            # Convert numpy arrays to lists for JSON serialization
            serializable_results = {}
            for key, value in results.items():
                if key in ['actual_levels', 'theoretical_predictions', 'classical_predictions', 'genomic_adjusted_predictions']:
                    if hasattr(value, 'tolist'):
                        serializable_results[key] = value.tolist()
                    else:
                        serializable_results[key] = value
                else:
                    serializable_results[key] = value
            
            json.dump(serializable_results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        if args.advanced:
            print(f"\n🎯 Summary of advanced validation:")
            if 'advanced_validation' in results and 'combined_prediction' in results['advanced_validation']:
                score = results['advanced_validation']['combined_prediction']['prediction_score']
                print(f"   Combined prediction score: {score:.3f}")
                print(f"   Theory sophistication: Advanced")
            print(f"   Environmental conditions: T={args.temp}K, O2={args.oxygen:.0%}")
        
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        if args.advanced:
            print("This might be due to missing advanced dependencies.")
            print("Try running in standard mode: python validate_my_pharmacology_theory.py")
        else:
            print("This might be due to missing dependencies or data formatting issues.")
        print("Please check your data format and try again.")

if __name__ == "__main__":
    main()
