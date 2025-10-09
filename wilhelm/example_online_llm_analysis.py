#!/usr/bin/env python3
"""
Wilhelm Hegel Framework - Online Database + LLM Analysis Example

This example demonstrates the new features:
1. Online database integration (automatic SBML download)
2. LLM conversion and comparison with Hugging Face models
"""

import os
from analysis_pipeline import run_complete_sbml_analysis
from src.data_sources.online_databases import BiologicalDatabaseClient

def main():
    print("Wilhelm Hegel Framework - Enhanced Example")
    print("="*50)
    
    # Example 1: List available online models
    print("\n1. Available Online Models:")
    client = BiologicalDatabaseClient()
    models = client.get_available_models(max_per_source=2)
    
    for i, model in enumerate(models[:5]):
        print(f"   {i+1}. [{model['source']}] {model['name']}")
        print(f"      {model['description'][:60]}...")
    
    # Example 2: Run analysis with online model (no local file needed)
    print("\n2. Running Analysis with Online Model:")
    print("   Using example glycolysis model...")
    
    try:
        # Run complete analysis with online model
        results = run_complete_sbml_analysis(
            sbml_file_path=None,  # No local file
            model_source='example',  # Use example database
            model_id='example_glycolysis',  # Specific model
            optimization_targets=['metabolic_efficiency', 'robustness'],
            output_dir="results_online_example",
            huggingface_api_key=os.environ.get('HUGGINGFACE_HUB_TOKEN'),  # Optional
            enable_llm_comparison=True
        )
        
        print("\n3. Analysis Results Summary:")
        print(f"   ✓ SBML Components: {results['sbml_components']['summary']['num_species']} species")
        print(f"   ✓ S-Entropy Coordinates: {results['molecular_language_system']['summary']['species_mapped']} mapped")
        print(f"   ✓ Bayesian Network: {results['oscillatory_bayesian_network']['network_properties']['num_edges']} edges")
        
        if results.get('llm_analysis'):
            llm = results['llm_analysis']['metadata']
            print(f"   ✓ LLM Analysis: {llm['total_texts_generated']} texts, score {llm['overall_performance_score']:.3f}")
        
        print(f"\n   Results saved to: results_online_example/")
        
    except Exception as e:
        print(f"   Error: {e}")
        print("   This is expected if dependencies are not installed")
    
    # Example 3: Manual model selection
    print("\n4. Manual Model Selection Example:")
    print("   You can also specify exact models:")
    print("   python analysis_pipeline.py --model-source biomodels --model-id BIOMD0000000001")
    print("   python analysis_pipeline.py --model-source bigg --model-id iIT341")
    print("   python analysis_pipeline.py --list-models  # See all available")
    
    # Example 4: LLM comparison only
    print("\n5. LLM Features:")
    print("   • Converts biological networks to natural language")
    print("   • Creates question-answer pairs for training")
    print("   • Compares with molecular LLMs (ChemBERTa, BioBERT, etc.)")
    print("   • Generates performance metrics and recommendations")
    
    print(f"\n{'='*50}")
    print("Example complete! Try running the analysis pipeline with online models.")

if __name__ == "__main__":
    main()
