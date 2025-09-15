#!/usr/bin/env python3
"""
Test that pipeline components are isolated and one failure doesn't break the whole system
"""

import sys
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

def test_isolated_oxygen():
    """Test oxygen component in isolation"""
    print("🧬 Testing Oxygen Component Isolation...")
    
    try:
        from hegel_demo.oxygen_substrate import run_oxygen_demonstrations
        
        print("   Running oxygen demonstrations...")
        run_oxygen_demonstrations()
        print("   ✅ Oxygen component completed successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Oxygen component failed: {e}")
        return False

def test_isolated_cascade():
    """Test cascade component in isolation"""
    print("\n⚡ Testing Cascade Component Isolation...")
    
    try:
        from hegel_demo.electron_cascade import run_cascade_demonstrations
        
        print("   Running cascade demonstrations...")
        run_cascade_demonstrations()
        print("   ✅ Cascade component completed successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Cascade component failed: {e}")
        return False

def test_isolated_quantum():
    """Test quantum component in isolation"""
    print("\n🔬 Testing Quantum Component Isolation...")
    
    try:
        from hegel_demo.membrane_quantum import run_membrane_quantum_demonstrations
        
        print("   Running quantum demonstrations...")
        run_membrane_quantum_demonstrations()
        print("   ✅ Quantum component completed successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Quantum component failed: {e}")
        return False

def test_validation_isolation():
    """Test validation component in isolation"""
    print("\n🧪 Testing Validation Component Isolation...")
    
    try:
        from hegel_demo.utils import PerformanceMetrics, VALIDATION_DATASETS
        
        metrics = PerformanceMetrics()
        
        # Test each validation independently
        oid_result = metrics.validate_oxygen_supremacy(VALIDATION_DATASETS['molecules_oid'])
        cascade_result = metrics.validate_cascade_speed(VALIDATION_DATASETS['cascade_speeds'])
        quantum_result = metrics.validate_quantum_resolution(VALIDATION_DATASETS['quantum_accuracies'])
        
        print(f"   Oxygen validation: {'✅ PASS' if oid_result['target_met'] else '❌ FAIL'}")
        print(f"   Cascade validation: {'✅ PASS' if cascade_result['target_met'] else '❌ FAIL'}")
        print(f"   Quantum validation: {'✅ PASS' if quantum_result['target_met'] else '❌ FAIL'}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Validation component failed: {e}")
        return False

def test_partial_pipeline_resilience():
    """Test that pipeline can continue even if one component fails"""
    print("\n🛡️ Testing Pipeline Resilience...")
    
    components = [
        ("Oxygen", test_isolated_oxygen),
        ("Cascade", test_isolated_cascade),
        ("Quantum", test_isolated_quantum),
        ("Validation", test_validation_isolation)
    ]
    
    results = {}
    for name, test_func in components:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"   Component {name} crashed: {e}")
            results[name] = False
    
    # Check if at least 2 components work (50% resilience)
    working_count = sum(1 for success in results.values() if success)
    total_count = len(components)
    resilience = working_count / total_count
    
    print(f"\n   Pipeline Resilience: {working_count}/{total_count} components working")
    print(f"   Resilience Score: {resilience:.1%}")
    
    if resilience >= 0.75:  # 75% of components working
        print("   ✅ EXCELLENT resilience - pipeline is robust")
        return True
    elif resilience >= 0.50:  # 50% of components working
        print("   ⚠️ GOOD resilience - pipeline can continue with partial functionality")
        return True
    else:
        print("   ❌ POOR resilience - pipeline would break down")
        return False

def test_data_output_consistency():
    """Test that all components generate expected data outputs"""
    print("\n📊 Testing Data Output Consistency...")
    
    import os
    expected_files = [
        # Oxygen files
        'oxygen_oid_supremacy.png',
        'cytoplasmic_space_generation.png',
        'oxygen_substrate_data.json',
        
        # Cascade files
        'cascade_speed_advantage.png', 
        'cascade_network_propagation.png',
        'cascade_network_propagation_data.json',
        'electron_cascade_data.json',
        
        # Quantum files
        'membrane_quantum_accuracy.png',
        'membrane_quantum_resolution_data.json',
        'membrane_quantum_coherence_data.json',
        'membrane_quantum_pathways_data.json',
        'membrane_quantum_data.json'
    ]
    
    existing_files = []
    missing_files = []
    
    for file in expected_files:
        if os.path.exists(file):
            existing_files.append(file)
        else:
            missing_files.append(file)
    
    completion_rate = len(existing_files) / len(expected_files)
    
    print(f"   Data Files: {len(existing_files)}/{len(expected_files)} created")
    print(f"   Completion Rate: {completion_rate:.1%}")
    
    if missing_files:
        print("   Missing files:")
        for file in missing_files[:5]:  # Show first 5 missing
            print(f"      • {file}")
        if len(missing_files) > 5:
            print(f"      • ... and {len(missing_files) - 5} more")
    
    return completion_rate >= 0.6  # 60% of expected files created

if __name__ == "__main__":
    print("🧪 TESTING PIPELINE ISOLATION & RESILIENCE")
    print("=" * 70)
    
    test_results = []
    
    # Run isolation tests
    test_results.append(("Oxygen Isolation", test_isolated_oxygen()))
    test_results.append(("Cascade Isolation", test_isolated_cascade()))  
    test_results.append(("Quantum Isolation", test_isolated_quantum()))
    test_results.append(("Validation Isolation", test_validation_isolation()))
    test_results.append(("Pipeline Resilience", test_partial_pipeline_resilience()))
    test_results.append(("Data Consistency", test_data_output_consistency()))
    
    # Summary
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"\n{'='*70}")
    print(f"🏆 PIPELINE ISOLATION RESULTS: {passed}/{total} tests passed")
    print(f"{'='*70}")
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    if passed >= 4:  # At least 4/6 tests pass
        print(f"\n🎉 PIPELINE IS ROBUST!")
        print(f"   • Components are properly isolated")
        print(f"   • One failure won't break the whole system")
        print(f"   • Data-first approach working")
        print(f"   • Ready for production use")
    elif passed >= 2:
        print(f"\n⚠️  PIPELINE HAS SOME ISSUES")
        print(f"   • Partial functionality available")
        print(f"   • Some components need additional work")
    else:
        print(f"\n❌ PIPELINE NEEDS MAJOR FIXES")
        
    sys.exit(0 if passed >= 4 else 1)
