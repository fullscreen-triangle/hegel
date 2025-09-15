#!/usr/bin/env python3
"""
Test the simplified cascade approach that bypasses NetworkX visualization
"""

import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

def test_cascade_without_networkx():
    """Test cascade with simplified approach"""
    print("⚡ Testing Simplified Cascade Approach...")
    
    try:
        from hegel_demo.electron_cascade import CascadeSimulator
        
        # Create simulator
        print("   Creating cascade simulator...")
        simulator = CascadeSimulator()
        print("   ✅ Simulator created")
        
        # Test speed advantage (this should work)
        print("   Testing speed advantage demonstration...")
        simulator.demonstrate_speed_advantage()
        print("   ✅ Speed advantage completed")
        
        # Test the simplified network propagation
        print("   Testing simplified network propagation...")
        simulator.demonstrate_network_propagation()
        print("   ✅ Network propagation completed")
        
        # Check if JSON file was created
        import os
        if os.path.exists('cascade_network_propagation_data.json'):
            print("   ✅ JSON data file created")
            
            # Read and display summary
            import json
            with open('cascade_network_propagation_data.json', 'r') as f:
                data = json.load(f)
            
            print(f"   📊 Data summary:")
            print(f"      • Source node: {data['source_node']}")
            print(f"      • Network size: {data['network_size']}")
            print(f"      • Propagation speed: {data['propagation_speed_ms']:.0f} m/s")
            print(f"      • Final coverage: {data['final_coverage_percent']:.1f}%")
            print(f"      • Max electron density: {data['max_electron_density']:.3f}")
        else:
            print("   ❌ JSON data file not created")
            return False
        
        # Check if PNG was created
        if os.path.exists('cascade_network_propagation.png'):
            print("   ✅ Simple visualization created")
        else:
            print("   ❌ Simple visualization not created")
            return False
            
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cascade_data_completeness():
    """Test that cascade generates complete data without visualization issues"""
    print("\n📊 Testing Data Completeness...")
    
    try:
        from hegel_demo.electron_cascade import CascadeSimulator
        
        simulator = CascadeSimulator()
        
        # Test data summary generation
        print("   Generating data summary...")
        simulator.save_data_summary()
        
        # Check if file exists
        import os
        if os.path.exists('electron_cascade_data.json'):
            print("   ✅ Complete data summary created")
            
            import json
            with open('electron_cascade_data.json', 'r') as f:
                data = json.load(f)
            
            print(f"   📊 Summary includes:")
            for key in data.keys():
                print(f"      • {key}")
                
        else:
            print("   ❌ Data summary not created")
            return False
            
        return True
        
    except Exception as e:
        print(f"   ❌ Data completeness test failed: {e}")
        return False

def test_cascade_cli_command():
    """Test the CLI command with the fixed approach"""
    print("\n🔧 Testing CLI Command...")
    
    try:
        # Import and test the CLI function directly
        from hegel_demo.electron_cascade import run_cascade_demonstrations
        
        print("   Running cascade demonstrations...")
        run_cascade_demonstrations()
        print("   ✅ CLI cascade command completed successfully")
        
        return True
        
    except Exception as e:
        print(f"   ❌ CLI command test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 TESTING SIMPLIFIED CASCADE APPROACH")
    print("=" * 60)
    
    test_results = []
    
    # Run tests
    test_results.append(("Simplified Cascade", test_cascade_without_networkx()))
    test_results.append(("Data Completeness", test_cascade_data_completeness()))
    test_results.append(("CLI Command", test_cascade_cli_command()))
    
    # Summary
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"\n{'='*60}")
    print(f"🏆 SIMPLIFIED APPROACH RESULTS: {passed}/{total} tests passed")
    print(f"{'='*60}")
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    if passed == total:
        print(f"\n🎉 SIMPLIFIED APPROACH WORKING!")
        print(f"   • NetworkX visualization issues bypassed")
        print(f"   • Core cascade computations working")
        print(f"   • Data saved to JSON for analysis")
        print(f"   • Simple visualizations generated")
        print(f"\n   Ready to run: hegel-demo cascade")
    else:
        print(f"\n⚠️  Some tests still failing")
        
    print(f"\n📁 Generated files:")
    print(f"   • cascade_speed_advantage.png")
    print(f"   • cascade_network_propagation.png")
    print(f"   • cascade_network_propagation_data.json")
    print(f"   • electron_cascade_data.json")
        
    sys.exit(0 if passed == total else 1)
