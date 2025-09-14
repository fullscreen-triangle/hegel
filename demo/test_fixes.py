#!/usr/bin/env python3
"""
Test the validation and NetworkX fixes
"""

import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

def test_validation_fixes():
    """Test that validation logic now works correctly"""
    print("🧪 Testing Validation Fixes...")
    
    try:
        from hegel_demo.utils import PerformanceMetrics, VALIDATION_DATASETS
        
        metrics = PerformanceMetrics()
        
        # Test oxygen supremacy validation
        print("   Testing oxygen supremacy validation...")
        oid_result = metrics.validate_oxygen_supremacy(VALIDATION_DATASETS['molecules_oid'])
        print(f"   Oxygen supremacy: {'✅ PASS' if oid_result['target_met'] else '❌ FAIL'}")
        print(f"   Min advantage: {oid_result['min_advantage']:.1f}×")
        print(f"   Avg advantage: {oid_result['avg_advantage']:.1f}×")
        
        # Test cascade speed validation
        print("   Testing cascade speed validation...")
        cascade_result = metrics.validate_cascade_speed(VALIDATION_DATASETS['cascade_speeds'])
        print(f"   Cascade speed: {'✅ PASS' if cascade_result['target_met'] else '❌ FAIL'}")
        print(f"   Average speed: {cascade_result['average_speed']:.2e} m/s")
        
        # Test quantum resolution validation
        print("   Testing quantum resolution validation...")
        quantum_result = metrics.validate_quantum_resolution(VALIDATION_DATASETS['quantum_accuracies'])
        print(f"   Quantum resolution: {'✅ PASS' if quantum_result['target_met'] else '❌ FAIL'}")
        print(f"   Success rate: {quantum_result['success_rate']:.1%}")
        print(f"   Average accuracy: {quantum_result['average_accuracy']:.3f}")
        
        # Test overall score
        metrics.metrics = {
            'oxygen_supremacy': oid_result,
            'cascade_speed': cascade_result,
            'quantum_resolution': quantum_result
        }
        overall_score = metrics.calculate_overall_score()
        print(f"   Overall score: {overall_score:.2f}")
        
        return (oid_result['target_met'] and 
                cascade_result['target_met'] and 
                quantum_result['target_met'])
        
    except Exception as e:
        print(f"   ❌ Validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cascade_network():
    """Test that cascade network visualization works"""
    print("\n⚡ Testing Cascade Network Fixes...")
    
    try:
        from hegel_demo.electron_cascade import CascadeSimulator
        
        simulator = CascadeSimulator()
        
        # Test basic properties
        network = simulator.network
        print(f"   Network size: {network.network_size}")
        print(f"   Number of nodes: {network.network.number_of_nodes()}")
        print(f"   Number of edges: {network.network.number_of_edges()}")
        
        # Test that positions are available
        pos = network.node_positions
        print(f"   Position dictionary size: {len(pos)}")
        
        # Check if positions match nodes
        all_nodes = list(network.network.nodes())
        print(f"   All nodes: {all_nodes[:5]}..." if len(all_nodes) > 5 else f"   All nodes: {all_nodes}")
        
        # Test selecting a valid central node
        if all_nodes:
            central_node = all_nodes[len(all_nodes) // 2]
            print(f"   Selected central node: {central_node}")
            print(f"   Central node in positions: {central_node in pos}")
        
        # Test a short cascade simulation
        print("   Testing short cascade simulation...")
        if all_nodes:
            central_node = all_nodes[0]  # Use first node as safe choice
            cascade_data = network.simulate_cascade_propagation(central_node, duration=1e-7)  # 0.1 μs
            print(f"   Cascade simulation completed: {len(cascade_data)} data keys")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Cascade network test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_test_plot():
    """Create a test plot to verify matplotlib works"""
    print("\n📊 Testing Matplotlib...")
    
    try:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # Test plot 1: OID supremacy
        molecules = ['O₂', 'N₂', 'H₂O', 'CO₂', 'ATP']
        oid_values = [3.2e15, 1.1e12, 4.7e13, 2.8e13, 8.3e13]
        colors = ['red' if mol == 'O₂' else 'blue' for mol in molecules]
        
        ax1.bar(molecules, oid_values, color=colors, alpha=0.7)
        ax1.set_yscale('log')
        ax1.set_title('OID Supremacy Validation')
        ax1.set_ylabel('OID (bits/mol/s)')
        
        # Test plot 2: Cascade speeds
        speeds = np.array([1.1e6, 0.98e6, 1.05e6, 1.02e6, 0.99e6])
        ax2.hist(speeds, bins=10, alpha=0.7, color='green')
        ax2.axvline(1e6, color='red', linestyle='--', label='Target')
        ax2.set_title('Cascade Speed Distribution')
        ax2.set_xlabel('Speed (m/s)')
        ax2.legend()
        
        # Test plot 3: Quantum accuracies
        accuracies = np.array([0.991, 0.994, 0.992, 0.996, 0.993])
        ax3.plot(accuracies, 'bo-', alpha=0.7)
        ax3.axhline(0.99, color='red', linestyle='--', label='99% Target')
        ax3.set_title('Quantum Resolution Accuracy')
        ax3.set_ylabel('Accuracy')
        ax3.legend()
        
        # Test plot 4: Network representation
        x = np.linspace(0, 10, 50)
        y = np.sin(x) * np.exp(-x/5)
        ax4.plot(x, y, 'g-', linewidth=2, label='Signal Propagation')
        ax4.set_title('Network Signal Example')
        ax4.set_xlabel('Time (μs)')
        ax4.set_ylabel('Signal')
        ax4.legend()
        
        plt.tight_layout()
        plt.savefig('validation_fixes_test.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        print("   ✅ Test plot saved as 'validation_fixes_test.png'")
        return True
        
    except Exception as e:
        print(f"   ❌ Matplotlib test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 TESTING VALIDATION AND NETWORK FIXES")
    print("=" * 60)
    
    test_results = []
    
    # Run tests
    test_results.append(("Validation Logic", test_validation_fixes()))
    test_results.append(("Cascade Network", test_cascade_network()))
    test_results.append(("Matplotlib", create_test_plot()))
    
    # Summary
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"\n{'='*60}")
    print(f"🏆 FIXING TEST RESULTS: {passed}/{total} tests passed")
    print(f"{'='*60}")
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    if passed == total:
        print(f"\n🎉 ALL FIXES WORKING!")
        print(f"   Ready to run:")
        print(f"   • hegel-demo validate")
        print(f"   • hegel-demo cascade")
        print(f"   • hegel-demo run-all")
    else:
        print(f"\n⚠️  Some tests still failing - need additional fixes")
    
    sys.exit(0 if passed == total else 1)
