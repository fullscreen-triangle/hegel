# Complete SBML Analysis Pipeline - Hierarchical Observer System Integration
import sys
import os
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import all modules
from processing.parse_sbml import parse_sbml_file
from biological_networks.molecular_network import create_molecular_network
from biological_networks.pathway_topology import extract_pathway_structure
from biological_networks.regulatory_networks import build_regulatory_graph
from biological_networks.network_model import create_network_llm_comparison
from transform.molecular_language import create_molecular_language_system
from transform.fuzzy_evidence import create_fuzzy_evidence_system
from transform.circuit_analysis import create_biological_circuit_analysis
from optimisation.finite_observer import FiniteObserver
from optimisation.transcendent_observer import TranscendentObserver
from optimisation.oscillatory_bayesian_network import create_oscillatory_bayesian_network
from optimisation.pathway_optimisation import optimize_biological_pathways
from processing.validation import cross_modal_biological_validation
from processing.visualisations import generate_biological_report
from data_sources.online_databases import get_online_model, BiologicalDatabaseClient

def run_complete_sbml_analysis(sbml_file_path: str = None,
                              model_source: str = None,
                              model_id: str = None,
                              optimization_targets: list = None,
                              consistency_threshold: float = 0.95,
                              output_dir: str = "results",
                              huggingface_api_key: str = None,
                              enable_llm_comparison: bool = True) -> Dict[str, Any]:
    """
    Complete SBML analysis pipeline using hierarchical observer system
    
    NEW FEATURES:
    - Online database integration (BiGG, BioModels, Reactome)
    - LLM conversion and comparison with Hugging Face models
    
    Integrates all theoretical frameworks:
    - Finite observers at each frequency scale
    - Transcendent observer for gear-based navigation  
    - S-entropy coordinate transformation
    - Oscillatory Bayesian networks
    - Biological circuit analysis (oscillatory hole semiconductor theory)
    - Fuzzy evidence processing
    - Cross-modal validation
    - Comprehensive visualization and reporting
    - Network-to-LLM conversion and model comparison
    
    Args:
        sbml_file_path: Local SBML file path (optional if using online models)
        model_source: Online database source ('bigg', 'biomodels', 'example')
        model_id: Specific model ID from online database
        optimization_targets: List of optimization targets
        consistency_threshold: Validation consistency threshold
        output_dir: Output directory for results
        huggingface_api_key: Hugging Face API key for LLM comparison
        enable_llm_comparison: Whether to perform LLM comparison
    """
    
    print("="*80)
    print("WILHELM HEGEL FRAMEWORK - COMPLETE SBML ANALYSIS PIPELINE")
    print("="*80)
    print("NEW FEATURES: Online Database Integration + LLM Comparison")
    print("="*80)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    analysis_results = {}
    
    try:
        # Step 0: Get SBML file (local or online)
        print("\n" + "="*50)
        print("STEP 0: SBML FILE ACQUISITION")
        print("="*50)
        
        if sbml_file_path is None:
            # Download from online database
            print("No local file provided - accessing online databases...")
            
            if model_source and model_id:
                print(f"Downloading {model_id} from {model_source}...")
                sbml_file_path = get_online_model(model_source, model_id)
            else:
                print("Auto-selecting model from online databases...")
                # Show available models
                client = BiologicalDatabaseClient()
                available_models = client.get_available_models(max_per_source=2)
                
                if available_models:
                    print(f"Available models ({len(available_models)}):")
                    for i, model in enumerate(available_models[:5]):
                        print(f"  {i+1}. [{model['source']}] {model['name']}")
                        print(f"     {model['description'][:80]}...")
                    
                    # Use first available model
                    selected_model = available_models[0]
                    print(f"\nAuto-selecting: {selected_model['name']}")
                    sbml_file_path = client.download_model(selected_model['source'], selected_model['id'])
                else:
                    print("No online models available, creating example...")
                    sbml_file_path = get_online_model('example', 'example_glycolysis')
        
        if not sbml_file_path or not os.path.exists(sbml_file_path):
            raise FileNotFoundError(f"Could not access SBML file: {sbml_file_path}")
        
        print(f"✓ SBML file ready: {sbml_file_path}")
        print(f"  Output directory: {output_dir}")
        
        # Step 1: Parse SBML file
        print("\n" + "="*50)
        print("STEP 1: SBML PARSING AND COMPONENT EXTRACTION")
        print("="*50)
        
        sbml_components = parse_sbml_file(sbml_file_path)
        analysis_results['sbml_components'] = sbml_components
        
        print(f"✓ SBML parsing complete")
        print(f"  Species: {sbml_components['summary']['num_species']}")
        print(f"  Reactions: {sbml_components['summary']['num_reactions']}")
        
        # Step 2: Create molecular networks
        print("\n" + "="*50)
        print("STEP 2: MOLECULAR NETWORK CONSTRUCTION")
        print("="*50)
        
        molecular_network = create_molecular_network(sbml_components)
        pathway_topology = extract_pathway_structure(sbml_components)
        regulatory_networks = build_regulatory_graph(sbml_components)
        
        analysis_results['molecular_network'] = molecular_network
        analysis_results['pathway_topology'] = pathway_topology
        analysis_results['regulatory_networks'] = regulatory_networks
        
        print(f"✓ Network construction complete")
        print(f"  Network density: {molecular_network['summary']['network_density']:.3f}")
        print(f"  Linear pathways: {pathway_topology['summary']['num_linear_pathways']}")
        print(f"  Regulatory interactions: {regulatory_networks['summary']['num_regulatory_interactions']}")
        
        # Step 3: Transform to S-entropy coordinates
        print("\n" + "="*50)
        print("STEP 3: S-ENTROPY COORDINATE TRANSFORMATION")
        print("="*50)
        
        molecular_language_system = create_molecular_language_system(
            sbml_components, molecular_network
        )
        s_coordinates = molecular_language_system['s_coordinates']
        
        analysis_results['molecular_language_system'] = molecular_language_system
        analysis_results['s_coordinates'] = s_coordinates
        
        print(f"✓ S-entropy transformation complete")
        print(f"  Species mapped: {molecular_language_system['summary']['species_mapped']}")
        print(f"  Coordinate dimensionality: {molecular_language_system['summary']['coordinate_dimensionality']}")
        
        # Step 4: Create hierarchical observer system
        print("\n" + "="*50)
        print("STEP 4: HIERARCHICAL OBSERVER SYSTEM")
        print("="*50)
        
        # Create finite observers for different scales
        molecular_observer = FiniteObserver(
            frequency_range=(1e12, 1e15),
            scale_name='molecular',
            temporal_window=1e-12
        )
        
        cellular_observer = FiniteObserver(
            frequency_range=(1e-3, 1e3),
            scale_name='cellular',
            temporal_window=1e-3
        )
        
        systemic_observer = FiniteObserver(
            frequency_range=(1e-2, 1e2),
            scale_name='systemic',
            temporal_window=1e2
        )
        
        # Create transcendent observer
        transcendent_navigator = TranscendentObserver([
            molecular_observer, cellular_observer, systemic_observer
        ])
        
        # Demonstrate gear-based navigation
        therapeutic_pathway = transcendent_navigator.navigate_therapeutic_pathway(
            sbml_components=sbml_components,
            target_scale='systemic',
            therapeutic_frequency=0.1  # Example target frequency
        )
        
        analysis_results['hierarchical_observers'] = {
            'molecular_observer': molecular_observer,
            'cellular_observer': cellular_observer,
            'systemic_observer': systemic_observer,
            'transcendent_navigator': transcendent_navigator,
            'therapeutic_pathway': therapeutic_pathway
        }
        
        print(f"✓ Hierarchical observer system created")
        print(f"  Finite observers: 3 (molecular, cellular, systemic)")
        print(f"  Transcendent navigation: {'successful' if 'error' not in therapeutic_pathway else 'failed'}")
        
        # Step 5: Create oscillatory Bayesian network
        print("\n" + "="*50)
        print("STEP 5: OSCILLATORY BAYESIAN NETWORK")
        print("="*50)
        
        oscillatory_bayesian_network = create_oscillatory_bayesian_network(
            sbml_components, s_coordinates, molecular_network
        )
        
        analysis_results['oscillatory_bayesian_network'] = oscillatory_bayesian_network
        
        print(f"✓ Oscillatory Bayesian network created")
        print(f"  Network edges: {oscillatory_bayesian_network['network_properties']['num_edges']}")
        print(f"  Pathway coherence: {oscillatory_bayesian_network['pathway_coherence']:.3f}")
        
        # Step 6: Apply fuzzy evidence processing
        print("\n" + "="*50)
        print("STEP 6: FUZZY EVIDENCE PROCESSING")
        print("="*50)
        
        fuzzy_evidence_system = create_fuzzy_evidence_system(
            s_coordinates, molecular_network
        )
        
        analysis_results['fuzzy_evidence_system'] = fuzzy_evidence_system
        
        print(f"✓ Fuzzy evidence processing complete")
        print(f"  Evidence network edges: {fuzzy_evidence_system['summary']['evidence_network_edges']}")
        print(f"  High confidence species: {fuzzy_evidence_system['summary']['high_confidence_species']}")
        
        # Step 7: Biological circuit analysis
        print("\n" + "="*50)
        print("STEP 7: BIOLOGICAL CIRCUIT ANALYSIS")
        print("="*50)
        
        circuit_analysis = create_biological_circuit_analysis(
            sbml_components, s_coordinates, regulatory_networks['regulatory_network']
        )
        
        analysis_results['circuit_analysis'] = circuit_analysis
        
        print(f"✓ Biological circuit analysis complete")
        print(f"  Circuit elements: {circuit_analysis['summary']['circuit_elements']}")
        print(f"  P-N junctions: {circuit_analysis['summary']['pn_junctions']}")
        print(f"  Therapeutic transistors: {circuit_analysis['summary']['therapeutic_transistors']}")
        
        # Step 8: Pathway optimization
        print("\n" + "="*50)
        print("STEP 8: PATHWAY OPTIMIZATION")
        print("="*50)
        
        if optimization_targets is None:
            optimization_targets = ['metabolic_efficiency', 'robustness', 'adaptability']
        
        # Extract constraints from S-entropy analysis
        s_entropy_constraints = extract_s_entropy_constraints(molecular_language_system)
        viability_thresholds = calculate_viability_thresholds(sbml_components)
        
        optimized_pathways = optimize_biological_pathways(
            regulatory_networks['regulatory_network'],
            optimization_targets,
            s_entropy_constraints,
            viability_thresholds
        )
        
        analysis_results['optimized_pathways'] = optimized_pathways
        
        print(f"✓ Pathway optimization complete")
        print(f"  Targets optimized: {optimized_pathways['optimization_summary']['targets_optimized']}")
        print(f"  Average improvement: {optimized_pathways['optimization_summary']['avg_optimization_score']:.3f}")
        
        # Step 9: Cross-modal validation
        print("\n" + "="*50)
        print("STEP 9: CROSS-MODAL VALIDATION")
        print("="*50)
        
        # Extract coordinates for validation
        genomic_coordinates = extract_genomic_coordinates(sbml_components)
        protein_coordinates = extract_protein_coordinates(sbml_components)  
        metabolic_coordinates = extract_metabolic_coordinates(sbml_components)
        circuit_coordinates = extract_circuit_coordinates(circuit_analysis)
        
        validation_results = cross_modal_biological_validation(
            genomic_coordinates, protein_coordinates, metabolic_coordinates,
            circuit_coordinates, consistency_threshold
        )
        
        analysis_results['validation_results'] = validation_results
        
        print(f"✓ Cross-modal validation complete")
        print(f"  Overall validity: {validation_results['summary']['consistency_score']:.3f}")
        print(f"  Validation status: {'PASSED' if validation_results['overall_validity'] else 'FAILED'}")
        
        # Step 10: Generate comprehensive report
        print("\n" + "="*50)
        print("STEP 10: COMPREHENSIVE REPORTING")
        print("="*50)
        
        coordinate_visualizations = create_coordinate_visualizations(
            genomic_coordinates, protein_coordinates, metabolic_coordinates, circuit_coordinates
        )
        
        biological_predictions = generate_biological_predictions(
            oscillatory_bayesian_network, circuit_analysis, optimized_pathways
        )
        
        comprehensive_report = generate_biological_report(
            oscillatory_bayesian_network,
            optimized_pathways,
            analysis_results,  # multi_scale_integration
            coordinate_visualizations,
            biological_predictions,
            validation_results
        )
        
        analysis_results['comprehensive_report'] = comprehensive_report
        
        print(f"✓ Comprehensive report generated")
        print(f"  Total visualizations: {comprehensive_report['report_metadata']['total_visualizations_created']}")
        print(f"  Report completeness: {comprehensive_report['report_metadata']['report_completeness_score']:.3f}")
        
        # Step 11: LLM Conversion and Comparison
        print("\n" + "="*50)
        print("STEP 11: LLM CONVERSION AND COMPARISON")
        print("="*50)
        
        if enable_llm_comparison:
            print("Converting network analysis to LLM format...")
            
            # Set up HF API key if provided
            if huggingface_api_key:
                os.environ['HUGGINGFACE_HUB_TOKEN'] = huggingface_api_key
                print("✓ Hugging Face API key configured")
            
            llm_analysis = create_network_llm_comparison(
                analysis_results, huggingface_api_key
            )
            
            analysis_results['llm_analysis'] = llm_analysis
            
            print(f"✓ LLM analysis complete")
            print(f"  Generated texts: {llm_analysis['metadata']['total_texts_generated']}")
            print(f"  Reference models compared: {llm_analysis['metadata']['reference_models_compared']}")
            print(f"  Overall performance score: {llm_analysis['metadata']['overall_performance_score']:.3f}")
            
            # Print summary
            if llm_analysis['metadata']['overall_performance_score'] > 0.7:
                print("  🎉 Excellent LLM performance - high similarity with reference models!")
            elif llm_analysis['metadata']['overall_performance_score'] > 0.5:
                print("  ✅ Good LLM performance - moderate similarity with reference models")
            else:
                print("  ⚠️  LLM performance needs improvement - consider enriching descriptions")
        else:
            print("LLM comparison disabled")
            analysis_results['llm_analysis'] = None
        
        # Step 12: Save results
        print("\n" + "="*50)
        print("STEP 12: SAVING RESULTS")
        print("="*50)
        
        save_analysis_results(analysis_results, output_dir)
        
        print(f"✓ Results saved to: {output_dir}")
        
        # Final summary
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE - SUMMARY")
        print("="*80)
        
        print_final_summary(analysis_results, enable_llm_comparison)
        
        return analysis_results
        
    except Exception as e:
        print(f"\n❌ Analysis failed with error: {str(e)}")
        print("Please check the SBML file and try again.")
        
        # Save partial results if any
        if analysis_results:
            save_analysis_results(analysis_results, output_dir, partial=True)
            print(f"Partial results saved to: {output_dir}")
        
        raise e

def extract_s_entropy_constraints(molecular_language_system: Dict) -> Dict:
    """Extract S-entropy constraints from molecular language analysis"""
    constraints = {}
    
    if 'distribution_analysis' in molecular_language_system:
        dist_analysis = molecular_language_system['distribution_analysis']
        
        # Coordinate range constraints
        if 'coordinate_ranges' in dist_analysis:
            ranges = dist_analysis['coordinate_ranges']
            
            def knowledge_constraint(weights):
                return ranges.get('knowledge_range', 5.0) - np.sum(np.abs(weights[:len(weights)//3]))
            
            def time_constraint(weights):
                return ranges.get('time_range', 5.0) - np.sum(np.abs(weights[len(weights)//3:2*len(weights)//3]))
            
            def entropy_constraint(weights):
                return ranges.get('entropy_range', 5.0) - np.sum(np.abs(weights[2*len(weights)//3:]))
            
            constraints['knowledge_constraint'] = knowledge_constraint
            constraints['time_constraint'] = time_constraint
            constraints['entropy_constraint'] = entropy_constraint
    
    return constraints

def calculate_viability_thresholds(sbml_components: Dict) -> Dict:
    """Calculate viability thresholds from SBML components"""
    thresholds = {}
    
    # Calculate concentration-based thresholds
    concentrations = []
    for species_data in sbml_components['species'].values():
        conc = species_data.get('initial_concentration', 0)
        if conc > 0:
            concentrations.append(conc)
    
    if concentrations:
        thresholds['min_activity'] = np.percentile(concentrations, 10) / 10  # 10% of 10th percentile
        thresholds['max_activity'] = np.percentile(concentrations, 90) * 2    # 2x 90th percentile
    else:
        thresholds['min_activity'] = 0.01
        thresholds['max_activity'] = 2.0
    
    return thresholds

def extract_genomic_coordinates(sbml_components: Dict) -> Dict:
    """Extract genomic-level coordinates (simplified)"""
    genomic_coords = {}
    
    # Use species names and compartments as genomic-level features
    for species_id, species_data in sbml_components['species'].items():
        name = species_data.get('name', species_id)
        compartment = species_data.get('compartment', 'default')
        
        # Simple genomic coordinate based on name and compartment
        name_hash = hash(name) % 1000 / 1000.0
        comp_hash = hash(compartment) % 1000 / 1000.0
        
        genomic_coords[species_id] = np.array([name_hash, comp_hash])
    
    return genomic_coords

def extract_protein_coordinates(sbml_components: Dict) -> Dict:
    """Extract protein-level coordinates (simplified)"""
    protein_coords = {}
    
    # Use concentration and boundary conditions as protein-level features  
    for species_id, species_data in sbml_components['species'].items():
        concentration = species_data.get('initial_concentration', 0)
        boundary = 1.0 if species_data.get('boundary_condition', False) else 0.0
        
        protein_coords[species_id] = np.array([concentration / 100.0, boundary])
    
    return protein_coords

def extract_metabolic_coordinates(sbml_components: Dict) -> Dict:
    """Extract metabolic-level coordinates (simplified)"""
    metabolic_coords = {}
    
    # Count reaction involvement as metabolic activity
    species_reaction_counts = {}
    for reaction_data in sbml_components['reactions'].values():
        for reactant in reaction_data.get('reactants', []):
            species_id = reactant['species']
            species_reaction_counts[species_id] = species_reaction_counts.get(species_id, 0) + 1
        for product in reaction_data.get('products', []):
            species_id = product['species']
            species_reaction_counts[species_id] = species_reaction_counts.get(species_id, 0) + 1
    
    for species_id in sbml_components['species']:
        reaction_count = species_reaction_counts.get(species_id, 0)
        metabolic_activity = np.log(reaction_count + 1) / 5.0  # Normalized
        
        metabolic_coords[species_id] = np.array([metabolic_activity])
    
    return metabolic_coords

def extract_circuit_coordinates(circuit_analysis: Dict) -> Dict:
    """Extract circuit-level coordinates from circuit analysis"""
    circuit_coords = {}
    
    if 'therapeutic_conductivity' in circuit_analysis:
        conductivity = circuit_analysis['therapeutic_conductivity']
        
        for species_id, cond_data in conductivity.items():
            total_cond = cond_data.get('total_conductivity', 0)
            electron_contrib = cond_data.get('electron_contribution', 0)
            hole_contrib = cond_data.get('hole_contribution', 0)
            
            circuit_coords[species_id] = np.array([total_cond, electron_contrib, hole_contrib])
    
    return circuit_coords

def create_coordinate_visualizations(genomic_coords: Dict, protein_coords: Dict,
                                   metabolic_coords: Dict, circuit_coords: Dict) -> Dict:
    """Create coordinate visualizations for reporting"""
    return {
        'genomic_coordinates': genomic_coords,
        'protein_coordinates': protein_coords,
        'metabolic_coordinates': metabolic_coords,
        'circuit_coordinates': circuit_coords
    }

def generate_biological_predictions(oscillatory_network: Dict, circuit_analysis: Dict,
                                  optimized_pathways: Dict) -> Dict:
    """Generate biological predictions from analysis results"""
    predictions = {}
    
    # Therapeutic predictions from oscillatory holes
    if 'oscillatory_holes' in oscillatory_network:
        holes = oscillatory_network['oscillatory_holes']
        top_holes = sorted(holes, key=lambda x: x.get('hole_strength', 0), reverse=True)[:5]
        
        predictions['therapeutic_targets'] = [
            {
                'species': hole['species'],
                'frequency': hole['frequency'],
                'therapeutic_potential': hole['hole_strength']
            }
            for hole in top_holes
        ]
    
    # Circuit predictions
    if 'pn_junctions' in circuit_analysis:
        junctions = circuit_analysis['pn_junctions']
        predictions['therapeutic_junctions'] = len(junctions)
    
    # Optimization predictions
    if 'pathway_recommendations' in optimized_pathways:
        recommendations = optimized_pathways['pathway_recommendations']
        predictions['optimization_recommendations'] = len(recommendations)
    
    return predictions

def save_analysis_results(analysis_results: Dict, output_dir: str, partial: bool = False):
    """Save analysis results to files"""
    import json
    import pickle
    
    prefix = "partial_" if partial else ""
    
    # Save summary as JSON
    summary = extract_analysis_summary(analysis_results)
    with open(os.path.join(output_dir, f"{prefix}analysis_summary.json"), 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    # Save full results as pickle
    with open(os.path.join(output_dir, f"{prefix}analysis_results.pkl"), 'wb') as f:
        pickle.dump(analysis_results, f)
    
    # Save visualizations if present
    if 'comprehensive_report' in analysis_results:
        report = analysis_results['comprehensive_report']
        
        # Save matplotlib figures
        for category, visualizations in report.items():
            if isinstance(visualizations, dict) and 'visualizations' in category:
                viz_dir = os.path.join(output_dir, category)
                os.makedirs(viz_dir, exist_ok=True)
                
                for name, fig in visualizations.items():
                    if hasattr(fig, 'savefig'):
                        fig.savefig(os.path.join(viz_dir, f"{name}.png"), dpi=300, bbox_inches='tight')

def extract_analysis_summary(analysis_results: Dict) -> Dict:
    """Extract key summary information from analysis results"""
    summary = {
        'analysis_type': 'Wilhelm Hegel Framework - Complete SBML Analysis',
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    # SBML summary
    if 'sbml_components' in analysis_results:
        sbml = analysis_results['sbml_components']
        summary['sbml_summary'] = sbml.get('summary', {})
    
    # Network summary
    if 'molecular_network' in analysis_results:
        network = analysis_results['molecular_network']
        summary['network_summary'] = network.get('summary', {})
    
    # S-entropy summary
    if 'molecular_language_system' in analysis_results:
        s_entropy = analysis_results['molecular_language_system']
        summary['s_entropy_summary'] = s_entropy.get('summary', {})
    
    # Validation summary
    if 'validation_results' in analysis_results:
        validation = analysis_results['validation_results']
        summary['validation_summary'] = validation.get('summary', {})
    
    return summary

def print_final_summary(analysis_results: Dict, llm_enabled: bool = False):
    """Print final analysis summary"""
    print("Key Results:")
    
    if 'sbml_components' in analysis_results:
        sbml = analysis_results['sbml_components']['summary']
        print(f"  • Analyzed {sbml['num_species']} species and {sbml['num_reactions']} reactions")
    
    if 'molecular_language_system' in analysis_results:
        s_entropy = analysis_results['molecular_language_system']['summary']
        print(f"  • Mapped {s_entropy['species_mapped']} species to S-entropy coordinates")
    
    if 'oscillatory_bayesian_network' in analysis_results:
        obn = analysis_results['oscillatory_bayesian_network']['summary']
        print(f"  • Created Bayesian network with {obn['oscillatory_frequencies_calculated']} oscillatory frequencies")
    
    if 'circuit_analysis' in analysis_results:
        circuit = analysis_results['circuit_analysis']['summary']
        print(f"  • Identified {circuit['pn_junctions']} P-N junctions and {circuit['therapeutic_transistors']} therapeutic transistors")
    
    if 'validation_results' in analysis_results:
        validation = analysis_results['validation_results']['summary']
        status = "PASSED" if validation['validation_passed'] else "FAILED"
        print(f"  • Cross-modal validation: {status} (score: {validation['consistency_score']:.3f})")
    
    # NEW: LLM Analysis Results
    if llm_enabled and 'llm_analysis' in analysis_results and analysis_results['llm_analysis']:
        llm = analysis_results['llm_analysis']['metadata']
        performance = llm['overall_performance_score']
        status_emoji = "🎉" if performance > 0.7 else "✅" if performance > 0.5 else "⚠️"
        print(f"  • LLM Analysis: {status_emoji} Performance score {performance:.3f}")
        print(f"    - Generated {llm['total_texts_generated']} text descriptions")
        print(f"    - Compared with {llm['reference_models_compared']} reference models")
    
    print("\nHierarchical Observer System:")
    print("  • Finite observers: Molecular, Cellular, Systemic scales")
    print("  • Transcendent observer: Gear-based pathway navigation") 
    print("  • Oscillatory hole semiconductor theory: Applied to biological circuits")
    print("  • S-entropy coordinate system: Complete molecular language mapping")
    
    # NEW: Online Database Integration
    print("\nNEW FEATURES:")
    print("  • Online database integration: BiGG Models, BioModels, Reactome")
    print("  • Automatic SBML file download and caching")
    if llm_enabled:
        print("  • Network-to-LLM conversion and comparison")
        print("  • Hugging Face model benchmarking")
    
    print(f"\n{'='*80}")
    print("Analysis complete! Check the output directory for detailed results and visualizations.")
    if llm_enabled:
        print("LLM analysis results include model comparison and performance metrics.")
    print(f"{'='*80}")

# Main execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Wilhelm Hegel Framework - Complete SBML Analysis (Enhanced)")
    parser.add_argument("sbml_file", nargs='?', help="Path to SBML file (optional - can use online databases)")
    parser.add_argument("--output", "-o", default="results", help="Output directory")
    parser.add_argument("--targets", "-t", nargs="+", 
                       default=['metabolic_efficiency', 'robustness', 'adaptability'],
                       help="Optimization targets")
    parser.add_argument("--threshold", "-th", type=float, default=0.95,
                       help="Consistency threshold for validation")
    parser.add_argument("--model-source", "-ms", choices=['bigg', 'biomodels', 'example'],
                       help="Online database source")
    parser.add_argument("--model-id", "-mid", help="Specific model ID from online database")
    parser.add_argument("--hf-api-key", "-hf", help="Hugging Face API key for LLM comparison")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM comparison")
    parser.add_argument("--list-models", "-lm", action="store_true", 
                       help="List available online models and exit")
    
    args = parser.parse_args()
    
    # Handle list models request
    if args.list_models:
        print("Available online models:")
        client = BiologicalDatabaseClient()
        models = client.get_available_models()
        
        for i, model in enumerate(models):
            print(f"\n{i+1}. [{model['source']}] {model['id']}")
            print(f"   Name: {model['name']}")  
            print(f"   Description: {model['description']}")
        
        print(f"\nUsage examples:")
        print(f"  python {__file__} --model-source bigg --model-id {models[0]['id'] if models else 'model_id'}")
        print(f"  python {__file__} --model-source example --model-id example_glycolysis")
        return
    
    # Validate arguments
    if not args.sbml_file and not args.model_source:
        print("Either provide an SBML file or specify an online model source.")
        print("Use --list-models to see available online models.")
        print("Use --help for more information.")
        return
    
    # Run complete analysis
    results = run_complete_sbml_analysis(
        sbml_file_path=args.sbml_file,
        model_source=args.model_source,
        model_id=args.model_id,
        optimization_targets=args.targets,
        consistency_threshold=args.threshold,
        output_dir=args.output,
        huggingface_api_key=args.hf_api_key,
        enable_llm_comparison=not args.no_llm
    )
    
    print(f"\nAnalysis results available in: {args.output}")
    print("Check analysis_summary.json for key findings.")
    
    if not args.no_llm and results.get('llm_analysis'):
        print("\nLLM Analysis Summary:")
        print(results['llm_analysis']['model_summary'])
