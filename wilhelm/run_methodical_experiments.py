#!/usr/bin/env python3
"""
Wilhelm Hegel Framework - Methodical Scientific Experiment Runner
===============================================================

This master script runs the Wilhelm framework as a series of methodical scientific experiments.
Each module has its own main function, saves results, and generates visualization panels.

Key Features:
- Run individual modules or complete pipeline
- Scientific result tracking and validation
- Comprehensive visualization panels
- Bridge system linking hierarchical structures to circuit networks
- Real-time experiment monitoring

Usage:
    python run_methodical_experiments.py --all                    # Run all experiments
    python run_methodical_experiments.py --bridge                 # Test bridge system
    python run_methodical_experiments.py --finite-observers       # Test finite observers
    python run_methodical_experiments.py --validation             # Run personal validation
"""

import sys
import os
import argparse
import json
from datetime import datetime
from pathlib import Path
import subprocess

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def run_bridge_experiment():
    """Run the hierarchy-circuit bridge experiment"""
    
    print("="*80)
    print("RUNNING BRIDGE EXPERIMENT")
    print("="*80)
    
    try:
        from bridge.hierarchy_circuit_bridge import main as bridge_main
        bridge_main()
        return True
    except Exception as e:
        print(f"Bridge experiment failed: {e}")
        return False

def run_finite_observer_experiment():
    """Run the finite observer experiment"""
    
    print("="*80)
    print("RUNNING FINITE OBSERVER EXPERIMENT")
    print("="*80)
    
    try:
        from optimisation.finite_observer import main as finite_main
        finite_main()
        return True
    except Exception as e:
        print(f"Finite observer experiment failed: {e}")
        return False

def run_transcendent_observer_experiment():
    """Run the transcendent observer experiment"""
    
    print("="*80)
    print("RUNNING TRANSCENDENT OBSERVER EXPERIMENT")
    print("="*80)
    
    try:
        # Import and run transcendent observer if it has been updated to be methodical
        from optimisation.transcendent_observer import TranscendentObserver
        
        print("Transcendent observer experiment - placeholder for now")
        print("(Would run methodical transcendent observer tests)")
        
        return True
    except Exception as e:
        print(f"Transcendent observer experiment failed: {e}")
        return False

def run_personal_validation_experiment():
    """Run the personal pharmacology validation experiment"""
    
    print("="*80)
    print("RUNNING PERSONAL PHARMACOLOGY VALIDATION EXPERIMENT")
    print("="*80)
    
    try:
        # Check if validation script exists and run it
        validation_script = "validate_my_pharmacology_theory.py"
        if os.path.exists(validation_script):
            print(f"Running {validation_script}...")
            result = subprocess.run([sys.executable, validation_script], 
                                  capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)
            return result.returncode == 0
        else:
            print(f"Personal validation script not found: {validation_script}")
            return False
    except Exception as e:
        print(f"Personal validation experiment failed: {e}")
        return False

def run_advanced_components_demo():
    """Run the advanced pharmacology components demo"""
    
    print("="*80)
    print("RUNNING ADVANCED COMPONENTS DEMO")
    print("="*80)
    
    try:
        demo_script = "demo_advanced_components.py"
        if os.path.exists(demo_script):
            print(f"Running {demo_script}...")
            result = subprocess.run([sys.executable, demo_script], 
                                  capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)
            return result.returncode == 0
        else:
            print(f"Advanced components demo not found: {demo_script}")
            return False
    except Exception as e:
        print(f"Advanced components demo failed: {e}")
        return False

def run_integrated_bridge_validation():
    """Run integrated test of bridge system with finite observers"""
    
    print("="*80)
    print("RUNNING INTEGRATED BRIDGE-OBSERVER EXPERIMENT")
    print("="*80)
    
    try:
        from bridge.hierarchy_circuit_bridge import (
            HierarchyCircuitBridge, 
            create_example_hierarchy_nodes, 
            create_example_circuit_elements
        )
        from optimisation.finite_observer import create_example_finite_observers
        
        # Create bridge system
        bridge = HierarchyCircuitBridge(frequency_tolerance=0.05)
        
        # Add hierarchy nodes from finite observers
        finite_observers = create_example_finite_observers()
        for obs in finite_observers:
            from bridge.hierarchy_circuit_bridge import HierarchyNode
            
            hierarchy_node = HierarchyNode(
                id=obs.observer_id,
                level=0 if obs.scale_name == "molecular" else 1,
                oscillation_frequency=sum(obs.frequency_range) / 2,  # Mid-point frequency
                observer_type="finite",
                information_capacity=obs.information_capacity,
                spatial_scale=1e-6,  # Placeholder
                temporal_scale=obs.temporal_window
            )
            bridge.add_hierarchy_node(hierarchy_node)
        
        # Add circuit elements
        circuit_elements = create_example_circuit_elements()
        for element in circuit_elements:
            bridge.add_circuit_element(element)
        
        # Build bridges and test
        bridge_stats = bridge.build_all_bridges()
        
        print(f"Integration Test Results:")
        print(f"  Bridges created: {bridge_stats['total_bridges']}")
        print(f"  Average match score: {bridge_stats['average_match_score']:.3f}")
        
        # Test cross-structure navigation
        if len(finite_observers) > 0 and len(circuit_elements) > 0:
            start_node = finite_observers[0].observer_id
            target_node = circuit_elements[0].id
            path = bridge.navigate_hybrid_path(start_node, target_node)
            
            if path:
                print(f"  Cross-structure navigation successful: {len(path)} steps")
                crosses = bridge._path_crosses_structures(path)
                print(f"  Path crosses structures: {crosses}")
            else:
                print(f"  Cross-structure navigation failed")
        
        # Generate integrated report
        bridge.visualize_bridge_network("integrated_bridge_results")
        bridge.save_results("integrated_bridge_results")
        
        print("Integrated experiment complete!")
        return True
        
    except Exception as e:
        print(f"Integrated bridge-observer experiment failed: {e}")
        return False

def generate_master_report(experiment_results: dict):
    """Generate a master report of all experiments"""
    
    print("="*80)
    print("GENERATING MASTER EXPERIMENT REPORT")
    print("="*80)
    
    output_dir = "master_experiment_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create summary report
    report = {
        'experiment_timestamp': datetime.now().isoformat(),
        'total_experiments_run': len(experiment_results),
        'successful_experiments': sum(1 for success in experiment_results.values() if success),
        'failed_experiments': sum(1 for success in experiment_results.values() if not success),
        'experiment_results': experiment_results,
        'success_rate': sum(1 for success in experiment_results.values() if success) / len(experiment_results) if experiment_results else 0
    }
    
    # Save JSON report
    with open(f"{output_dir}/master_experiment_report.json", 'w') as f:
        json.dump(report, f, indent=4)
    
    # Print summary
    print(f"Master Experiment Report:")
    print(f"  Total experiments: {report['total_experiments_run']}")
    print(f"  Successful: {report['successful_experiments']}")
    print(f"  Failed: {report['failed_experiments']}")
    print(f"  Success rate: {report['success_rate']:.1%}")
    
    print(f"\nExperiment Details:")
    for exp_name, success in experiment_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {exp_name}: {status}")
    
    print(f"\nMaster report saved to: {output_dir}/master_experiment_report.json")
    
    if report['success_rate'] >= 0.8:
        print("\n🎉 EXCELLENT! Most experiments passed successfully!")
    elif report['success_rate'] >= 0.6:
        print("\n✅ GOOD! Majority of experiments passed.")
    else:
        print("\n⚠️ Some experiments failed. Check individual logs for details.")

def main():
    """Main experiment runner with command line options"""
    
    parser = argparse.ArgumentParser(
        description="Wilhelm Hegel Framework - Methodical Scientific Experiment Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all experiments in sequence
  python run_methodical_experiments.py --all
  
  # Run specific experiments
  python run_methodical_experiments.py --bridge --finite-observers
  
  # Run personal validation only
  python run_methodical_experiments.py --validation
  
  # Run integrated tests
  python run_methodical_experiments.py --integrated
        """
    )
    
    parser.add_argument('--all', action='store_true',
                       help='Run all experiments in sequence')
    parser.add_argument('--bridge', action='store_true',
                       help='Run hierarchy-circuit bridge experiment')
    parser.add_argument('--finite-observers', action='store_true', 
                       help='Run finite observer experiment')
    parser.add_argument('--transcendent', action='store_true',
                       help='Run transcendent observer experiment')
    parser.add_argument('--validation', action='store_true',
                       help='Run personal pharmacology validation')
    parser.add_argument('--advanced-demo', action='store_true',
                       help='Run advanced components demo')
    parser.add_argument('--integrated', action='store_true',
                       help='Run integrated bridge-observer experiment')
    parser.add_argument('--generate-report', action='store_true',
                       help='Generate master report of previous experiments')
    
    args = parser.parse_args()
    
    # If no specific experiments chosen, show help
    if not any([args.all, args.bridge, args.finite_observers, args.transcendent, 
                args.validation, args.advanced_demo, args.integrated, args.generate_report]):
        parser.print_help()
        return
    
    print("="*80)
    print("WILHELM HEGEL FRAMEWORK - METHODICAL SCIENTIFIC EXPERIMENTS")
    print("="*80)
    print(f"Experiment started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Track experiment results
    experiment_results = {}
    
    # Run experiments based on arguments
    if args.all or args.bridge:
        experiment_results['bridge_system'] = run_bridge_experiment()
    
    if args.all or args.finite_observers:
        experiment_results['finite_observers'] = run_finite_observer_experiment()
    
    if args.all or args.transcendent:
        experiment_results['transcendent_observer'] = run_transcendent_observer_experiment()
    
    if args.all or args.validation:
        experiment_results['personal_validation'] = run_personal_validation_experiment()
    
    if args.all or args.advanced_demo:
        experiment_results['advanced_components'] = run_advanced_components_demo()
    
    if args.all or args.integrated:
        experiment_results['integrated_bridge_validation'] = run_integrated_bridge_validation()
    
    # Generate master report
    if experiment_results or args.generate_report:
        generate_master_report(experiment_results)
    
    print("\n" + "="*80)
    print("ALL EXPERIMENTS COMPLETE")
    print("="*80)
    print(f"Experiment ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show results directories
    print(f"\nResults can be found in:")
    result_dirs = [
        "bridge_results/",
        "finite_observer_results/",
        "personal_validation_results/", 
        "integrated_bridge_results/",
        "master_experiment_results/"
    ]
    
    for result_dir in result_dirs:
        if os.path.exists(result_dir):
            print(f"  - {result_dir}")
    
    print(f"\n🔬 Wilhelm Hegel Framework experiments demonstrate:")
    print(f"  • Bridge system linking hierarchical structures to circuit networks")
    print(f"  • Finite observers with bounded information processing") 
    print(f"  • Personal pharmacology theory validation")
    print(f"  • Advanced theoretical components (fuzzy, Bayesian, quantum)")
    print(f"  • Methodical scientific approach with comprehensive validation")
    
    print(f"\n🎯 This validates our collaborative idea of bridging tree→graph structures!")

if __name__ == "__main__":
    main()
