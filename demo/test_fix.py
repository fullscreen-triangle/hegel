#!/usr/bin/env python3
"""
Quick test to verify the matplotlib backend fixes work
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

def test_basic_visualization():
    """Test basic matplotlib functionality"""
    print("Testing matplotlib with Agg backend...")
    
    # Create a simple plot
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    
    plt.figure(figsize=(8, 6))
    plt.plot(x, y, 'b-', linewidth=2, label='sin(x)')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title('Test Plot - Matplotlib with Agg Backend')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save plot (should work with Agg backend)
    plt.savefig('test_plot.png', dpi=150, bbox_inches='tight')
    plt.close()  # Close figure instead of show()
    
    print("✅ Basic matplotlib test passed!")
    print("   Generated: test_plot.png")

def test_oxygen_module_imports():
    """Test importing the fixed modules"""
    try:
        print("\nTesting module imports...")
        from hegel_demo.oxygen_substrate import OxygenProcessor
        print("✅ Oxygen substrate module imported successfully")
        
        from hegel_demo.electron_cascade import CascadeSimulator  
        print("✅ Electron cascade module imported successfully")
        
        from hegel_demo.membrane_quantum import QuantumProcessor
        print("✅ Membrane quantum module imported successfully")
        
        from hegel_demo.visualizations import BiologicalVisualizer
        print("✅ Visualizations module imported successfully")
        
        # Test creating instances
        oxygen_proc = OxygenProcessor()
        print("✅ OxygenProcessor instance created")
        
        cascade_sim = CascadeSimulator()
        print("✅ CascadeSimulator instance created")
        
        quantum_proc = QuantumProcessor()
        print("✅ QuantumProcessor instance created")
        
        visualizer = BiologicalVisualizer()
        print("✅ BiologicalVisualizer instance created")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_simple_demonstration():
    """Test a simple demonstration"""
    try:
        print("\nTesting simple oxygen demonstration...")
        from hegel_demo.oxygen_substrate import OxygenProcessor
        
        processor = OxygenProcessor()
        
        # Test OID calculation
        oid = processor.calculate_oscillatory_information_density(
            temperature=310,  # Body temperature
            pressure=101325,  # Standard pressure
            paramagnetic_enhancement=1.73
        )
        
        print(f"✅ OID calculated: {oid:.2e} bits/molecule/second")
        
        if oid > 1e15:
            print("✅ OID supremacy confirmed (>10¹⁵ bits/mol/s)")
            return True
        else:
            print("❌ OID below expected threshold")
            return False
            
    except Exception as e:
        print(f"❌ Simple demonstration failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 TESTING HEGEL DEMO FIXES")
    print("=" * 50)
    
    # Run tests
    success_count = 0
    total_tests = 3
    
    # Test 1: Basic matplotlib
    test_basic_visualization()
    success_count += 1
    
    # Test 2: Module imports
    if test_oxygen_module_imports():
        success_count += 1
    
    # Test 3: Simple demonstration
    if test_simple_demonstration():
        success_count += 1
    
    print(f"\n{'='*50}")
    print(f"🏆 TEST RESULTS: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("✅ ALL FIXES WORKING CORRECTLY!")
        print("   You can now run: hegel-demo run-all")
    else:
        print("❌ Some tests failed - additional fixes needed")
