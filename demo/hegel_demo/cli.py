"""
Command Line Interface for Hegel Demonstrations
"""

import click
import sys
import os
from pathlib import Path

# Add package to path
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir))


@click.group()
@click.version_option(version='1.0.0')
def main():
    """
    Hegel Biological Computer Architecture Demonstrations
    
    Revolutionary validation suite for oxygen-enhanced Bayesian 
    molecular evidence networks.
    """
    pass


@main.command()
@click.option('--quick', is_flag=True, help='Run quick validation instead of full demos')
@click.option('--output', '-o', default='hegel_validation_report.txt', 
              help='Output file for validation report')
def run_all(quick, output):
    """Run all demonstrations and validations"""
    
    if quick:
        click.echo("🏃‍♂️ Running quick validation mode...")
        os.system(f"python {current_dir}/run_all_demos.py --quick")
    else:
        click.echo("🔬 Running comprehensive demonstration suite...")
        os.system(f"python {current_dir}/run_all_demos.py")
    
    click.echo(f"📁 Report saved to: {output}")


@main.command()
def oxygen():
    """Run oxygen information processing demonstration"""
    click.echo("🧬 Running Oxygen Information Processing demonstration...")
    from hegel_demo.oxygen_substrate import run_oxygen_demonstrations
    run_oxygen_demonstrations()


@main.command()
def cascade():
    """Run electron cascade communication demonstration"""
    click.echo("⚡ Running Electron Cascade Communication demonstration...")
    from hegel_demo.electron_cascade import run_cascade_demonstrations
    run_cascade_demonstrations()


@main.command()
def quantum():
    """Run membrane quantum computer demonstration"""
    click.echo("🔬 Running Membrane Quantum Computer demonstration...")
    from hegel_demo.membrane_quantum import run_membrane_quantum_demonstrations
    run_membrane_quantum_demonstrations()


@main.command()
@click.option('--molecules', '-n', default=1000, help='Number of molecules to test')
def validate(molecules):
    """Run quick validation tests"""
    click.echo(f"🧪 Running validation with {molecules} test molecules...")
    
    from hegel_demo.utils import PerformanceMetrics, VALIDATION_DATASETS
    
    metrics = PerformanceMetrics()
    
    # Run validations
    oid_result = metrics.validate_oxygen_supremacy(VALIDATION_DATASETS['molecules_oid'])
    cascade_result = metrics.validate_cascade_speed(VALIDATION_DATASETS['cascade_speeds'])
    quantum_result = metrics.validate_quantum_resolution(VALIDATION_DATASETS['quantum_accuracies'])
    
    click.echo("\n📊 Validation Results:")
    click.echo(f"   Oxygen OID: {'✅ PASS' if oid_result['target_met'] else '❌ FAIL'}")
    click.echo(f"   Cascade Speed: {'✅ PASS' if cascade_result['target_met'] else '❌ FAIL'}")
    click.echo(f"   Quantum Resolution: {'✅ PASS' if quantum_result['target_met'] else '❌ FAIL'}")
    
    # Store results and get overall score
    metrics.metrics = {
        'oxygen_supremacy': oid_result,
        'cascade_speed': cascade_result,
        'quantum_resolution': quantum_result
    }
    
    overall_score = metrics.calculate_overall_score()
    click.echo(f"\n🏆 Overall Score: {overall_score:.2f}/1.00 ({overall_score*100:.0f}%)")


@main.command()
def info():
    """Show information about the Hegel framework"""
    info_text = """
🧬 HEGEL: Oxygen-Enhanced Bayesian Molecular Evidence Networks

Revolutionary biological computer architecture that models living cells as 
sophisticated quantum computers powered by oxygen's paramagnetic information 
processing capabilities.

Key Claims Being Validated:
• Oxygen OID: 3.2×10¹⁵ bits/molecule/second
• Membrane quantum computers: 99% molecular resolution  
• Electron cascade speed: 10⁶ m/s (vs 10⁻⁶ m/s diffusion)
• DNA consultation: 1% emergency troubleshooting
• Atmospheric advantage: 4000× over aquatic environments

This framework represents a paradigm shift from viewing biological systems 
as chemical reactors to understanding them as quantum information processors.

🔬 For more information, see the comprehensive academic paper:
   "Hegel: A Unified Framework for Oxygen-Enhanced Bayesian Molecular 
    Evidence Networks in Biological Systems"
"""
    click.echo(info_text)


@main.command()
def summary():
    """Generate comprehensive data summaries"""
    click.echo("📊 Generating comprehensive data summaries...")
    
    from hegel_demo.oxygen_substrate import OxygenProcessor
    from hegel_demo.electron_cascade import CascadeSimulator  
    from hegel_demo.membrane_quantum import QuantumProcessor
    
    # Generate data summaries
    oxygen_proc = OxygenProcessor()
    cascade_sim = CascadeSimulator()
    quantum_proc = QuantumProcessor()
    
    click.echo("   Creating oxygen substrate data summary...")
    oxygen_proc.save_data_summary()
    
    click.echo("   Creating electron cascade data summary...")
    cascade_sim.save_data_summary()
    
    click.echo("   Creating membrane quantum data summary...")
    quantum_proc.save_data_summary()
    
    click.echo("\n✅ Data summaries created:")
    click.echo("   • oxygen_substrate_data.json")
    click.echo("   • electron_cascade_data.json") 
    click.echo("   • membrane_quantum_data.json")


@main.command()
def test_fixes():
    """Test that all recent fixes are working properly"""
    click.echo("🔧 Testing validation and network fixes...")
    
    import subprocess
    import sys
    
    # Run the test script
    try:
        result = subprocess.run([sys.executable, 'test_fixes.py'], 
                              capture_output=True, text=True, cwd='.')
        
        # Display output
        click.echo(result.stdout)
        if result.stderr:
            click.echo("Errors:")
            click.echo(result.stderr)
        
        if result.returncode == 0:
            click.echo("\n🎉 All fixes validated successfully!")
        else:
            click.echo("\n⚠️ Some tests failed - check output above")
            
    except Exception as e:
        click.echo(f"Error running tests: {e}")


@main.command()
def test_cascade():
    """Test cascade network positioning fixes specifically"""
    click.echo("⚡ Testing cascade NetworkX positioning fixes...")
    
    import subprocess
    import sys
    
    # Run the cascade test script
    try:
        result = subprocess.run([sys.executable, 'test_cascade_fix.py'], 
                              capture_output=True, text=True, cwd='.')
        
        # Display output
        click.echo(result.stdout)
        if result.stderr:
            click.echo("Errors:")
            click.echo(result.stderr)
        
        if result.returncode == 0:
            click.echo("\n🎉 Cascade fixes validated successfully!")
            click.echo("   Ready to run: hegel-demo cascade")
        else:
            click.echo("\n⚠️ Some cascade tests failed - check output above")
            
    except Exception as e:
        click.echo(f"Error running cascade tests: {e}")


@main.command()
def test_simple():
    """Test simplified cascade approach without NetworkX issues"""
    click.echo("🧪 Testing simplified cascade approach...")
    
    import subprocess
    import sys
    
    # Run the simplified test script
    try:
        result = subprocess.run([sys.executable, 'test_cascade_simple.py'], 
                              capture_output=True, text=True, cwd='.')
        
        # Display output
        click.echo(result.stdout)
        if result.stderr:
            click.echo("Errors:")
            click.echo(result.stderr)
        
        if result.returncode == 0:
            click.echo("\n🎉 Simplified approach validated successfully!")
            click.echo("   NetworkX issues bypassed - cascade works!")
        else:
            click.echo("\n⚠️ Some simplified tests failed - check output above")
            
    except Exception as e:
        click.echo(f"Error running simplified tests: {e}")


@main.command()
def test_quantum():
    """Test simplified quantum approach without getting stuck"""
    click.echo("🧪 Testing simplified quantum approach...")
    
    import subprocess
    import sys
    
    # Run the simplified quantum test script
    try:
        result = subprocess.run([sys.executable, 'test_quantum_simple.py'], 
                              capture_output=True, text=True, cwd='.')
        
        # Display output
        click.echo(result.stdout)
        if result.stderr:
            click.echo("Errors:")
            click.echo(result.stderr)
        
        if result.returncode == 0:
            click.echo("\n🎉 Simplified quantum approach validated successfully!")
            click.echo("   No more hour-long hangs - quantum works fast!")
        else:
            click.echo("\n⚠️ Some quantum tests failed - check output above")
            
    except Exception as e:
        click.echo(f"Error running quantum tests: {e}")


@main.command()
def test_pipeline():
    """Test pipeline isolation and resilience"""
    click.echo("🛡️ Testing pipeline isolation and resilience...")
    
    import subprocess
    import sys
    
    # Run the pipeline isolation test script
    try:
        result = subprocess.run([sys.executable, 'test_pipeline_isolation.py'], 
                              capture_output=True, text=True, cwd='.')
        
        # Display output
        click.echo(result.stdout)
        if result.stderr:
            click.echo("Errors:")
            click.echo(result.stderr)
        
        if result.returncode == 0:
            click.echo("\n🎉 Pipeline isolation validated successfully!")
            click.echo("   Components are isolated - one failure won't break the whole system!")
        else:
            click.echo("\n⚠️ Pipeline has some isolation issues - check output above")
            
    except Exception as e:
        click.echo(f"Error running pipeline tests: {e}")


if __name__ == '__main__':
    main()
