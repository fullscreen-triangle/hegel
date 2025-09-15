#!/usr/bin/env python3
"""
Test the cascade NetworkX positioning fixes
"""

import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

def test_cascade_network_creation():
    """Test that cascade network creation works correctly"""
    print("🔬 Testing Cascade Network Creation...")
    
    try:
        from hegel_demo.electron_cascade import CascadeSimulator
        
        # Create simulator
        simulator = CascadeSimulator()
        
        # Check network properties
        network = simulator.network
        G = network.network
        pos = network.node_positions
        
        print(f"   Network size: {network.network_size}")
        print(f"   Graph nodes: {G.number_of_nodes()}")
        print(f"   Graph edges: {G.number_of_edges()}")
        print(f"   Position entries: {len(pos)}")
        
        # Check consistency
        graph_nodes = set(G.nodes())
        pos_nodes = set(pos.keys())
        
        print(f"   Graph node range: {min(graph_nodes)} to {max(graph_nodes)}")
        print(f"   Position node range: {min(pos_nodes)} to {max(pos_nodes)}")
        print(f"   Nodes match positions: {graph_nodes == pos_nodes}")
        
        if not graph_nodes.issubset(pos_nodes):
            missing = graph_nodes - pos_nodes
            print(f"   ❌ Missing positions for: {missing}")
            return False
        else:
            print(f"   ✅ All nodes have positions")
            return True
            
    except Exception as e:
        print(f"   ❌ Network creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cascade_visualization():
    """Test that cascade visualization works without errors"""
    print("\n📊 Testing Cascade Visualization...")
    
    try:
        from hegel_demo.electron_cascade import CascadeSimulator
        
        # Create simulator
        simulator = CascadeSimulator()
        
        # Test basic speed advantage demo (should work)
        print("   Testing speed advantage demonstration...")
        simulator.demonstrate_speed_advantage()
        print("   ✅ Speed advantage demo completed")
        
        # Test the problematic network propagation demo
        print("   Testing network propagation demonstration...")
        simulator.demonstrate_network_propagation()
        print("   ✅ Network propagation demo completed")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Visualization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cascade_data_summary():
    """Test cascade data summary generation"""
    print("\n💾 Testing Cascade Data Summary...")
    
    try:
        from hegel_demo.electron_cascade import CascadeSimulator
        
        # Create simulator
        simulator = CascadeSimulator()
        
        # Test data summary
        print("   Testing data summary generation...")
        simulator.save_data_summary()
        print("   ✅ Data summary generated: electron_cascade_data.json")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Data summary test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_cascade_simulation():
    """Test a simple cascade simulation"""
    print("\n⚡ Testing Simple Cascade Simulation...")
    
    try:
        from hegel_demo.electron_cascade import CascadeSimulator
        
        # Create simulator
        simulator = CascadeSimulator()
        
        # Get valid source node
        network = simulator.network
        all_nodes = list(network.network.nodes())
        if all_nodes:
            source_node = all_nodes[0]  # Use first node
            print(f"   Using source node: {source_node}")
            
            # Run short simulation
            print("   Running cascade simulation...")
            results = network.simulate_cascade_propagation(source_node, duration=1e-7)  # 0.1 μs
            
            print(f"   ✅ Simulation completed with {len(results)} result keys")
            print(f"   Result keys: {list(results.keys())}")
            
            return True
        else:
            print("   ❌ No nodes found in network")
            return False
            
    except Exception as e:
        print(f"   ❌ Simulation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 TESTING CASCADE NETWORKX FIXES")
    print("=" * 50)
    
    test_results = []
    
    # Run tests
    test_results.append(("Network Creation", test_cascade_network_creation()))
    test_results.append(("Simple Simulation", test_simple_cascade_simulation()))
    test_results.append(("Data Summary", test_cascade_data_summary()))
    test_results.append(("Visualization", test_cascade_visualization()))
    
    # Summary
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"\n{'='*50}")
    print(f"🏆 CASCADE FIX RESULTS: {passed}/{total} tests passed")
    print(f"{'='*50}")
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    if passed == total:
        print(f"\n🎉 ALL CASCADE FIXES WORKING!")
        print(f"   Ready to run: hegel-demo cascade")
    else:
        print(f"\n⚠️  Some tests still failing")
        
    print(f"\nGenerated files:")
    print(f"   • cascade_speed_advantage.png")
    print(f"   • cascade_network_propagation.png") 
    print(f"   • electron_cascade_data.json")
        
    sys.exit(0 if passed == total else 1)
