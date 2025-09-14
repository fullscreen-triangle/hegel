#!/usr/bin/env python3
"""
Test the computational algorithms to ensure they work without data type errors
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

def test_oxygen_substrate_computation():
    """Test oxygen substrate space generation computation"""
    print("\n🧬 Testing Oxygen Substrate Computation...")
    
    try:
        from hegel_demo.oxygen_substrate import OxygenProcessor
        
        processor = OxygenProcessor()
        
        # Test OID calculation
        oid = processor.calculate_oscillatory_information_density(310, 101325, 1.73)
        print(f"   ✅ OID calculation: {oid:.2e} bits/mol/s")
        
        # Test space generation simulation
        print("   🔬 Testing space generation simulation...")
        density_evolution = processor.substrate.simulate_cytoplasmic_space_generation()
        
        print(f"   ✅ Space generation simulation completed")
        print(f"   📊 Density evolution shape: {density_evolution.shape}")
        print(f"   📈 Density range: {np.min(density_evolution):.1f} to {np.max(density_evolution):.1f} kg/m³")
        
        # Test OID supremacy demonstration
        print("   🔬 Testing OID supremacy demonstration...")
        processor.demonstrate_oid_supremacy()
        print("   ✅ OID supremacy demonstration completed")
        
        # Test space generation demonstration  
        print("   🔬 Testing space generation demonstration...")
        processor.demonstrate_space_generation()
        print("   ✅ Space generation demonstration completed")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Oxygen substrate test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_electron_cascade_computation():
    """Test electron cascade communication computation"""
    print("\n⚡ Testing Electron Cascade Computation...")
    
    try:
        from hegel_demo.electron_cascade import CascadeSimulator
        
        simulator = CascadeSimulator()
        
        # Test cascade simulation
        print("   🔬 Testing cascade simulation...")
        results = simulator.simulate_cascade_propagation(0, 5e-6)  # source 0, 5μs duration
        
        print(f"   ✅ Cascade simulation completed")
        print(f"   📊 Results keys: {list(results.keys())}")
        print(f"   📈 Max electron density: {np.max(results['electron_density']):.3f}")
        
        # Test speed advantage demonstration
        print("   🔬 Testing speed advantage demonstration...")  
        simulator.demonstrate_speed_advantage()
        print("   ✅ Speed advantage demonstration completed")
        
        # Test network synchronization
        print("   🔬 Testing network synchronization...")
        simulator.demonstrate_network_synchronization()
        print("   ✅ Network synchronization demonstration completed")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Electron cascade test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_membrane_quantum_computation():
    """Test membrane quantum computer computation"""
    print("\n🔬 Testing Membrane Quantum Computation...")
    
    try:
        from hegel_demo.membrane_quantum import QuantumProcessor
        
        processor = QuantumProcessor()
        
        # Test molecular resolution simulation
        print("   🔬 Testing molecular resolution simulation...")
        molecules = ['glucose', 'caffeine', 'dopamine', 'ATP']
        results = processor.quantum_computer.simulate_molecular_resolution(molecules)
        
        print(f"   ✅ Molecular resolution simulation completed")
        print(f"   📊 Results shape: {len(results)}")
        print(f"   📈 Resolution accuracy: {[r['resolution_accuracy'] for r in results[:2]]}")
        
        # Test resolution accuracy demonstration
        print("   🔬 Testing resolution accuracy demonstration...")
        processor.demonstrate_resolution_accuracy()
        print("   ✅ Resolution accuracy demonstration completed")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Membrane quantum test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_arrays():
    """Test basic numpy array operations to verify type safety"""
    print("\n🔢 Testing Basic Array Operations...")
    
    try:
        # Test float64 arrays
        arr1 = np.zeros(10, dtype=np.float64)
        arr2 = np.full(10, 1000.0, dtype=np.float64)
        
        # Test arithmetic operations
        result1 = arr2 - arr1 * 2.5
        print(f"   ✅ Float64 subtraction: shape={result1.shape}, dtype={result1.dtype}")
        
        # Test array assignment
        arr1[0] = 3.14
        arr1[1:3] = 2.71
        print(f"   ✅ Array assignment: first 3 elements = {arr1[:3]}")
        
        # Test broadcasting
        arr3 = np.ones((5, 5), dtype=np.float64)
        arr4 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result2 = arr3 * arr4
        print(f"   ✅ Broadcasting: shape={result2.shape}, dtype={result2.dtype}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Basic array test failed: {e}")
        return False

def test_visualization_save():
    """Test that visualizations save properly"""
    print("\n📊 Testing Visualization Save...")
    
    try:
        # Create a simple test plot
        x = np.linspace(0, 10, 100)
        y = np.sin(x) * np.exp(-x/10)
        
        plt.figure(figsize=(8, 6))
        plt.plot(x, y, 'b-', linewidth=2)
        plt.title('Test Plot - Computational Algorithm Validation')
        plt.xlabel('Time (μs)')
        plt.ylabel('Signal Amplitude')
        plt.grid(True, alpha=0.3)
        
        # Save plot
        plt.savefig('computation_test_plot.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"   ✅ Test plot saved as 'computation_test_plot.png'")
        return True
        
    except Exception as e:
        print(f"   ❌ Visualization test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTING COMPUTATIONAL ALGORITHMS")
    print("=" * 60)
    
    test_results = []
    
    # Run tests
    test_results.append(("Basic Arrays", test_basic_arrays()))
    test_results.append(("Visualization", test_visualization_save()))
    test_results.append(("Oxygen Substrate", test_oxygen_substrate_computation()))
    test_results.append(("Electron Cascade", test_electron_cascade_computation()))
    test_results.append(("Membrane Quantum", test_membrane_quantum_computation()))
    
    # Summary
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"\n{'='*60}")
    print(f"🏆 COMPUTATIONAL TEST RESULTS: {passed}/{total} tests passed")
    print(f"{'='*60}")
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    if passed == total:
        print(f"\n🎉 ALL COMPUTATIONAL ALGORITHMS WORKING!")
        print(f"   Ready to run: hegel-demo run-all")
    else:
        print(f"\n⚠️  Some computational algorithms need additional fixes")
        
    print(f"\n📁 Generated files:")
    print(f"   • computation_test_plot.png")
    if passed >= 3:  # If most core tests passed
        print(f"   • oxygen_oid_supremacy.png")
        print(f"   • cascade_speed_advantage.png") 
        print(f"   • membrane_quantum_accuracy.png")
