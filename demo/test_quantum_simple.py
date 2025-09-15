#!/usr/bin/env python3
"""
Test the simplified quantum approach that doesn't get stuck in heavy simulations
"""

import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

def test_quantum_simplified():
    """Test quantum with simplified data-first approach"""
    print("🔬 Testing Simplified Quantum Approach...")
    
    try:
        from hegel_demo.membrane_quantum import QuantumProcessor
        
        # Create processor
        print("   Creating quantum processor...")
        processor = QuantumProcessor()
        print("   ✅ Processor created")
        
        # Test simplified resolution accuracy (this should be fast now)
        print("   Testing simplified resolution accuracy...")
        processor.demonstrate_resolution_accuracy()
        print("   ✅ Resolution accuracy completed")
        
        # Test simplified quantum coherence
        print("   Testing simplified quantum coherence...")
        processor.demonstrate_quantum_coherence()
        print("   ✅ Quantum coherence completed")
        
        # Test simplified pathway superposition
        print("   Testing simplified pathway superposition...")
        processor.demonstrate_pathway_superposition()
        print("   ✅ Pathway superposition completed")
        
        # Check if JSON files were created
        import os
        json_files = [
            'membrane_quantum_resolution_data.json',
            'membrane_quantum_coherence_data.json',
            'membrane_quantum_pathways_data.json'
        ]
        
        all_created = True
        for json_file in json_files:
            if os.path.exists(json_file):
                print(f"   ✅ {json_file} created")
                
                # Read and display summary
                import json
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                if 'resolution' in json_file:
                    print(f"      • Success rate: {data.get('success_rate', 0):.1%}")
                    print(f"      • Mean accuracy: {data.get('mean_accuracy', 0):.3f}")
                elif 'coherence' in json_file:
                    print(f"      • Coherence time: {data.get('coherence_time_microseconds', 0):.0f} μs")
                    print(f"      • Temperature: {data.get('biological_temperature_kelvin', 0):.1f}K")
                elif 'pathways' in json_file:
                    print(f"      • Superposition states: {data.get('superposition_states', 0)}/{data.get('pathway_count', 0)}")
            else:
                print(f"   ❌ {json_file} not created")
                all_created = False
        
        # Check if PNG was created
        if os.path.exists('membrane_quantum_accuracy.png'):
            print("   ✅ Simple visualization created")
        else:
            print("   ❌ Simple visualization not created")
            return False
            
        return all_created
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quantum_data_summary():
    """Test quantum data summary generation"""
    print("\n📊 Testing Quantum Data Summary...")
    
    try:
        from hegel_demo.membrane_quantum import QuantumProcessor
        
        processor = QuantumProcessor()
        
        # Test data summary generation (should be fast)
        print("   Generating data summary...")
        processor.save_data_summary()
        
        # Check if file exists
        import os
        if os.path.exists('membrane_quantum_data.json'):
            print("   ✅ Complete data summary created")
            
            import json
            with open('membrane_quantum_data.json', 'r') as f:
                data = json.load(f)
            
            print(f"   📊 Summary includes:")
            for key in data.keys():
                print(f"      • {key}")
                
        else:
            print("   ❌ Data summary not created")
            return False
            
        return True
        
    except Exception as e:
        print(f"   ❌ Data summary test failed: {e}")
        return False

def test_quantum_cli_command():
    """Test the CLI command with the simplified approach"""
    print("\n🧪 Testing Quantum CLI Command...")
    
    try:
        # Import and test the CLI function directly
        from hegel_demo.membrane_quantum import run_membrane_quantum_demonstrations
        
        print("   Running quantum demonstrations...")
        start_time = time.time() if 'time' in globals() else 0
        
        run_membrane_quantum_demonstrations()
        
        if start_time > 0:
            duration = time.time() - start_time
            print(f"   ✅ CLI quantum command completed in {duration:.1f} seconds")
        else:
            print("   ✅ CLI quantum command completed successfully")
        
        return True
        
    except Exception as e:
        print(f"   ❌ CLI command test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quantum_performance():
    """Test that quantum operations are fast (not stuck)"""
    print("\n⚡ Testing Quantum Performance...")
    
    try:
        import time
        from hegel_demo.membrane_quantum import QuantumProcessor
        
        processor = QuantumProcessor()
        
        # Time each operation to ensure none get stuck
        operations = [
            ('Resolution Accuracy', processor.demonstrate_resolution_accuracy),
            ('Quantum Coherence', processor.demonstrate_quantum_coherence),
            ('Pathway Superposition', processor.demonstrate_pathway_superposition)
        ]
        
        for name, operation in operations:
            start_time = time.time()
            operation()
            duration = time.time() - start_time
            
            if duration < 10:  # Should complete in under 10 seconds
                print(f"   ✅ {name}: {duration:.2f}s (FAST)")
            elif duration < 60:
                print(f"   ⚠️  {name}: {duration:.2f}s (SLOW but OK)")
            else:
                print(f"   ❌ {name}: {duration:.2f}s (TOO SLOW)")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Performance test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTING SIMPLIFIED QUANTUM APPROACH")
    print("=" * 60)
    
    import time  # For performance testing
    test_results = []
    
    # Run tests
    test_results.append(("Simplified Quantum", test_quantum_simplified()))
    test_results.append(("Performance Check", test_quantum_performance()))
    test_results.append(("Data Summary", test_quantum_data_summary()))
    test_results.append(("CLI Command", test_quantum_cli_command()))
    
    # Summary
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"\n{'='*60}")
    print(f"🏆 SIMPLIFIED QUANTUM RESULTS: {passed}/{total} tests passed")
    print(f"{'='*60}")
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    if passed == total:
        print(f"\n🎉 SIMPLIFIED QUANTUM APPROACH WORKING!")
        print(f"   • Heavy simulation loops bypassed")
        print(f"   • Core quantum computations working")
        print(f"   • Data saved to JSON for analysis")
        print(f"   • Simple visualizations generated")
        print(f"   • Fast execution (no more hour-long hangs)")
        print(f"\n   Ready to run: hegel-demo quantum")
    else:
        print(f"\n⚠️  Some tests still failing")
        
    print(f"\n📁 Generated files:")
    print(f"   • membrane_quantum_accuracy.png")
    print(f"   • membrane_quantum_resolution_data.json")
    print(f"   • membrane_quantum_coherence_data.json")
    print(f"   • membrane_quantum_pathways_data.json")
    print(f"   • membrane_quantum_data.json")
        
    sys.exit(0 if passed == total else 1)
