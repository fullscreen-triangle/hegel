# LLM Conversion and Comparison for Biological Networks
import os
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import torch
from transformers import (
    AutoTokenizer, AutoModel, AutoModelForCausalLM,
    TrainingArguments, Trainer, DataCollatorForLanguageModeling,
    pipeline, BertTokenizer, BertModel
)
from datasets import Dataset
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import classification_report
import requests
from sentence_transformers import SentenceTransformer
import matplotlib.pyplot as plt
import seaborn as sns

class BiologicalNetworkLLM:
    """
    Convert biological network analysis results to LLM format and compare with existing models
    """
    
    def __init__(self, huggingface_api_key: str = None):
        self.hf_api_key = huggingface_api_key
        self.network_texts = []
        self.qa_pairs = []
        self.embeddings_cache = {}
        
        # Available molecular/biological LLMs for comparison
        self.reference_models = {
            'chemberta': 'DeepChem/ChemBERTa-77M-MLM',
            'biobert': 'dmis-lab/biobert-base-cased-v1.1',
            'scibert': 'allenai/scibert_scivocab_uncased',
            'pubmedbert': 'microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext',
            'molbert': 'allenai/molbert-uncased',
            'bioclinicalbert': 'emilyalsentzer/Bio_ClinicalBERT'
        }
        
        # Initialize sentence transformer for embeddings
        try:
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        except:
            print("Warning: Could not load sentence transformer model")
            self.sentence_model = None
    
    def convert_network_to_text(self, analysis_results: Dict) -> List[str]:
        """Convert network analysis results to natural language descriptions"""
        
        network_descriptions = []
        
        # Convert SBML components to text
        if 'sbml_components' in analysis_results:
            sbml = analysis_results['sbml_components']
            desc = self._describe_sbml_components(sbml)
            network_descriptions.extend(desc)
        
        # Convert molecular networks to text
        if 'molecular_network' in analysis_results:
            network = analysis_results['molecular_network']
            desc = self._describe_molecular_network(network)
            network_descriptions.extend(desc)
        
        # Convert S-entropy coordinates to text  
        if 'molecular_language_system' in analysis_results:
            s_system = analysis_results['molecular_language_system']
            desc = self._describe_s_entropy_system(s_system)
            network_descriptions.extend(desc)
        
        # Convert oscillatory Bayesian networks to text
        if 'oscillatory_bayesian_network' in analysis_results:
            obn = analysis_results['oscillatory_bayesian_network']
            desc = self._describe_oscillatory_network(obn)
            network_descriptions.extend(desc)
        
        # Convert circuit analysis to text
        if 'circuit_analysis' in analysis_results:
            circuit = analysis_results['circuit_analysis']
            desc = self._describe_circuit_analysis(circuit)
            network_descriptions.extend(desc)
        
        self.network_texts = network_descriptions
        return network_descriptions
    
    def _describe_sbml_components(self, sbml: Dict) -> List[str]:
        """Convert SBML components to text descriptions"""
        descriptions = []
        
        summary = sbml.get('summary', {})
        descriptions.append(
            f"This biological system contains {summary.get('num_species', 0)} molecular species "
            f"and {summary.get('num_reactions', 0)} biochemical reactions. "
            f"The system includes {summary.get('num_compartments', 0)} cellular compartments."
        )
        
        # Describe species
        species = sbml.get('species', {})
        for species_id, species_data in list(species.items())[:5]:  # Limit for brevity
            name = species_data.get('name', species_id)
            compartment = species_data.get('compartment', 'unknown')
            concentration = species_data.get('initial_concentration', 0)
            
            descriptions.append(
                f"The molecule {name} is located in the {compartment} compartment "
                f"with an initial concentration of {concentration:.3f} units."
            )
        
        # Describe reactions
        reactions = sbml.get('reactions', {})
        for reaction_id, reaction_data in list(reactions.items())[:3]:  # Limit for brevity
            name = reaction_data.get('name', reaction_id)
            reversible = "reversible" if reaction_data.get('reversible', False) else "irreversible"
            num_reactants = len(reaction_data.get('reactants', []))
            num_products = len(reaction_data.get('products', []))
            
            descriptions.append(
                f"The {reversible} reaction {name} converts {num_reactants} reactant(s) "
                f"into {num_products} product(s)."
            )
        
        return descriptions
    
    def _describe_molecular_network(self, network: Dict) -> List[str]:
        """Convert molecular network analysis to text descriptions"""
        descriptions = []
        
        summary = network.get('summary', {})
        analysis = network.get('species_analysis', {})
        
        descriptions.append(
            f"The molecular interaction network has a density of {summary.get('network_density', 0):.3f}, "
            f"indicating {'high' if summary.get('network_density', 0) > 0.5 else 'low'} connectivity between molecules."
        )
        
        if 'avg_degree' in analysis:
            descriptions.append(
                f"On average, each molecule interacts with {analysis['avg_degree']:.1f} other molecules, "
                f"with the most connected molecule having {analysis.get('max_degree', 0)} interactions."
            )
        
        # Describe network motifs
        if 'network_motifs' in network:
            motifs = network['network_motifs']
            triangles = motifs.get('triangles', 0)
            descriptions.append(
                f"The network contains {triangles} triangular motifs, "
                "which represent stable interaction patterns between three molecules."
            )
        
        return descriptions
    
    def _describe_s_entropy_system(self, s_system: Dict) -> List[str]:
        """Convert S-entropy coordinate system to text descriptions"""
        descriptions = []
        
        summary = s_system.get('summary', {})
        descriptions.append(
            f"The molecular coordinate system maps {summary.get('species_mapped', 0)} molecules "
            f"into a {summary.get('coordinate_dimensionality', 3)}-dimensional space representing "
            "knowledge, time, and entropy dimensions."
        )
        
        if 'distribution_analysis' in s_system:
            dist = s_system['distribution_analysis']
            if 'extreme_points' in dist:
                extremes = dist['extreme_points']
                
                max_knowledge = extremes.get('max_knowledge', [None, None])
                if max_knowledge[0]:
                    descriptions.append(
                        f"The molecule {max_knowledge[0]} has the highest knowledge coordinate "
                        f"value of {max_knowledge[1][0]:.3f}, indicating high information content."
                    )
                
                max_entropy = extremes.get('max_entropy', [None, None])
                if max_entropy[0]:
                    descriptions.append(
                        f"The molecule {max_entropy[0]} shows the highest entropy coordinate "
                        f"value of {max_entropy[1][2]:.3f}, indicating high disorder."
                    )
        
        return descriptions
    
    def _describe_oscillatory_network(self, obn: Dict) -> List[str]:
        """Convert oscillatory Bayesian network to text descriptions"""
        descriptions = []
        
        summary = obn.get('summary', {})
        properties = obn.get('network_properties', {})
        
        descriptions.append(
            f"The oscillatory Bayesian network contains {properties.get('num_edges', 0)} "
            f"probabilistic connections between molecules, with an average oscillatory frequency "
            f"of {properties.get('avg_frequency', 0):.3f} Hz."
        )
        
        coherence = obn.get('pathway_coherence', 0)
        descriptions.append(
            f"The pathway coherence score is {coherence:.3f}, indicating "
            f"{'high' if coherence > 0.7 else 'moderate' if coherence > 0.4 else 'low'} "
            "synchronization between molecular oscillations."
        )
        
        # Describe oscillatory holes
        holes = obn.get('oscillatory_holes', [])
        if holes:
            top_hole = max(holes, key=lambda x: x.get('hole_strength', 0))
            descriptions.append(
                f"The strongest oscillatory hole is found in molecule {top_hole['species']} "
                f"at frequency {top_hole['frequency']:.3f} Hz, representing a therapeutic target "
                "for molecular intervention."
            )
        
        return descriptions
    
    def _describe_circuit_analysis(self, circuit: Dict) -> List[str]:
        """Convert biological circuit analysis to text descriptions"""
        descriptions = []
        
        summary = circuit.get('summary', {})
        descriptions.append(
            f"The biological semiconductor circuit contains {summary.get('pn_junctions', 0)} "
            f"P-N junctions and {summary.get('therapeutic_transistors', 0)} therapeutic transistors, "
            f"enabling directional therapeutic current flow."
        )
        
        if 'therapeutic_conductivity' in circuit:
            conductivity = circuit['therapeutic_conductivity']
            avg_conductivity = np.mean([c.get('total_conductivity', 0) 
                                      for c in conductivity.values()])
            descriptions.append(
                f"The average therapeutic conductivity is {avg_conductivity:.3f} units, "
                "representing the system's ability to conduct therapeutic effects through "
                "both molecular components and oscillatory holes."
            )
        
        return descriptions
    
    def create_qa_pairs(self, analysis_results: Dict) -> List[Dict]:
        """Create question-answer pairs for training/evaluation"""
        
        qa_pairs = []
        
        # Q&A about network structure
        if 'molecular_network' in analysis_results:
            network = analysis_results['molecular_network']
            summary = network.get('summary', {})
            
            qa_pairs.append({
                'question': 'What is the network density of this biological system?',
                'answer': f"The network density is {summary.get('network_density', 0):.3f}",
                'context': 'molecular_network_topology'
            })
            
            qa_pairs.append({
                'question': 'How many molecular species are in this network?',
                'answer': f"There are {summary.get('total_species', 0)} molecular species",
                'context': 'network_composition'
            })
        
        # Q&A about S-entropy coordinates
        if 'molecular_language_system' in analysis_results:
            s_system = analysis_results['molecular_language_system']
            summary = s_system.get('summary', {})
            
            qa_pairs.append({
                'question': 'How many dimensions does the molecular coordinate system have?',
                'answer': f"The coordinate system has {summary.get('coordinate_dimensionality', 3)} dimensions",
                'context': 's_entropy_coordinates'
            })
        
        # Q&A about oscillatory properties
        if 'oscillatory_bayesian_network' in analysis_results:
            obn = analysis_results['oscillatory_bayesian_network']
            coherence = obn.get('pathway_coherence', 0)
            
            qa_pairs.append({
                'question': 'What is the pathway coherence score?',
                'answer': f"The pathway coherence score is {coherence:.3f}",
                'context': 'oscillatory_analysis'
            })
        
        # Q&A about circuit properties
        if 'circuit_analysis' in analysis_results:
            circuit = analysis_results['circuit_analysis']
            summary = circuit.get('summary', {})
            
            qa_pairs.append({
                'question': 'How many therapeutic transistors are in the biological circuit?',
                'answer': f"There are {summary.get('therapeutic_transistors', 0)} therapeutic transistors",
                'context': 'circuit_analysis'
            })
        
        self.qa_pairs = qa_pairs
        return qa_pairs
    
    def create_training_data(self, analysis_results: Dict) -> Dataset:
        """Create training dataset from network analysis"""
        
        # Convert to text descriptions
        texts = self.convert_network_to_text(analysis_results)
        
        # Create Q&A pairs
        qa_pairs = self.create_qa_pairs(analysis_results)
        
        # Combine all text data
        all_texts = texts.copy()
        
        # Add Q&A as text
        for qa in qa_pairs:
            combined_text = f"Question: {qa['question']} Answer: {qa['answer']}"
            all_texts.append(combined_text)
        
        # Create dataset
        dataset_dict = {
            'text': all_texts,
            'labels': list(range(len(all_texts)))  # Simple labels for classification
        }
        
        dataset = Dataset.from_dict(dataset_dict)
        return dataset
    
    def load_reference_models(self) -> Dict[str, Any]:
        """Load reference molecular/biological LLMs"""
        
        loaded_models = {}
        
        for model_name, model_path in self.reference_models.items():
            try:
                print(f"Loading reference model: {model_name}")
                
                # Load tokenizer and model
                tokenizer = AutoTokenizer.from_pretrained(model_path)
                
                # Try different model types
                try:
                    model = AutoModelForCausalLM.from_pretrained(model_path)
                    model_type = 'causal_lm'
                except:
                    try:
                        model = AutoModel.from_pretrained(model_path)
                        model_type = 'encoder'
                    except Exception as e:
                        print(f"Could not load {model_name}: {e}")
                        continue
                
                loaded_models[model_name] = {
                    'tokenizer': tokenizer,
                    'model': model,
                    'type': model_type,
                    'path': model_path
                }
                
                print(f"✓ Loaded {model_name}")
                
            except Exception as e:
                print(f"Failed to load {model_name}: {e}")
        
        return loaded_models
    
    def create_embeddings(self, texts: List[str], model_name: str = None) -> np.ndarray:
        """Create embeddings for text using specified model or sentence transformer"""
        
        if model_name and model_name in self.embeddings_cache:
            return self.embeddings_cache[model_name]
        
        embeddings = None
        
        if self.sentence_model:
            print(f"Creating embeddings using sentence transformer...")
            embeddings = self.sentence_model.encode(texts)
        else:
            print("Creating simple embeddings using word averaging...")
            # Fallback: simple word averaging
            from sklearn.feature_extraction.text import TfidfVectorizer
            vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            embeddings = vectorizer.fit_transform(texts).toarray()
        
        if model_name:
            self.embeddings_cache[model_name] = embeddings
        
        return embeddings
    
    def compare_with_reference_models(self, analysis_results: Dict) -> Dict[str, Any]:
        """Compare network-derived LLM with reference molecular models"""
        
        print("Starting comparison with reference molecular LLMs...")
        
        # Create our network text
        network_texts = self.convert_network_to_text(analysis_results)
        
        # Load reference models (limit to available ones for demo)
        reference_models = {}
        
        # Try to load at least one reference model
        for model_name in ['biobert', 'scibert', 'pubmedbert']:
            try:
                print(f"Attempting to load {model_name}...")
                tokenizer = AutoTokenizer.from_pretrained(self.reference_models[model_name])
                model = AutoModel.from_pretrained(self.reference_models[model_name])
                
                reference_models[model_name] = {
                    'tokenizer': tokenizer,
                    'model': model,
                    'type': 'encoder'
                }
                print(f"✓ Successfully loaded {model_name}")
                break  # Use first successful model
                
            except Exception as e:
                print(f"Could not load {model_name}: {e}")
                continue
        
        comparison_results = {
            'network_texts_count': len(network_texts),
            'reference_models_loaded': len(reference_models),
            'embeddings_comparison': {},
            'semantic_similarity': {},
            'perplexity_scores': {},
            'benchmark_results': {}
        }
        
        # Create embeddings for our network texts
        network_embeddings = self.create_embeddings(network_texts, 'network_model')
        
        # Compare with each reference model
        for ref_name, ref_model in reference_models.items():
            print(f"Comparing with {ref_name}...")
            
            try:
                # Create reference embeddings
                ref_embeddings = self._create_model_embeddings(
                    network_texts, ref_model['tokenizer'], ref_model['model']
                )
                
                # Calculate similarity
                similarity_matrix = cosine_similarity(network_embeddings, ref_embeddings)
                avg_similarity = np.mean(similarity_matrix)
                
                comparison_results['semantic_similarity'][ref_name] = {
                    'average_similarity': float(avg_similarity),
                    'max_similarity': float(np.max(similarity_matrix)),
                    'min_similarity': float(np.min(similarity_matrix)),
                    'std_similarity': float(np.std(similarity_matrix))
                }
                
                print(f"Average similarity with {ref_name}: {avg_similarity:.3f}")
                
            except Exception as e:
                print(f"Error comparing with {ref_name}: {e}")
        
        # Benchmark tasks
        comparison_results['benchmark_results'] = self._run_benchmark_tasks(
            network_texts, reference_models
        )
        
        # Overall assessment
        comparison_results['assessment'] = self._assess_model_performance(comparison_results)
        
        return comparison_results
    
    def _create_model_embeddings(self, texts: List[str], tokenizer, model) -> np.ndarray:
        """Create embeddings using a specific model"""
        
        embeddings = []
        
        for text in texts:
            try:
                # Tokenize
                inputs = tokenizer(text, return_tensors='pt', truncation=True, 
                                 padding=True, max_length=512)
                
                # Get embeddings
                with torch.no_grad():
                    outputs = model(**inputs)
                    
                    # Use last hidden state mean as embedding
                    if hasattr(outputs, 'last_hidden_state'):
                        embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
                    else:
                        embedding = outputs.pooler_output.squeeze().numpy()
                    
                    embeddings.append(embedding)
                    
            except Exception as e:
                print(f"Error creating embedding for text: {e}")
                # Fallback: zero embedding
                embeddings.append(np.zeros(768))  # Standard BERT size
        
        return np.array(embeddings)
    
    def _run_benchmark_tasks(self, texts: List[str], reference_models: Dict) -> Dict:
        """Run benchmark tasks to compare model performance"""
        
        benchmark_results = {}
        
        # Task 1: Molecular entity recognition
        molecular_entities = [
            'glucose', 'atp', 'pyruvate', 'enzyme', 'protein', 'metabolite',
            'reaction', 'pathway', 'membrane', 'cytoplasm'
        ]
        
        entity_recognition_scores = {}
        for ref_name in reference_models.keys():
            score = self._evaluate_entity_recognition(texts, molecular_entities)
            entity_recognition_scores[ref_name] = score
        
        benchmark_results['entity_recognition'] = entity_recognition_scores
        
        # Task 2: Biological relationship extraction
        relationship_scores = {}
        for ref_name in reference_models.keys():
            score = self._evaluate_relationship_extraction(texts)
            relationship_scores[ref_name] = score
        
        benchmark_results['relationship_extraction'] = relationship_scores
        
        # Task 3: Pathway coherence prediction
        coherence_scores = {}
        for ref_name in reference_models.keys():
            score = self._evaluate_coherence_prediction(texts)
            coherence_scores[ref_name] = score
        
        benchmark_results['coherence_prediction'] = coherence_scores
        
        return benchmark_results
    
    def _evaluate_entity_recognition(self, texts: List[str], entities: List[str]) -> float:
        """Evaluate molecular entity recognition performance"""
        
        total_entities = 0
        found_entities = 0
        
        for text in texts:
            text_lower = text.lower()
            for entity in entities:
                total_entities += 1
                if entity.lower() in text_lower:
                    found_entities += 1
        
        return found_entities / total_entities if total_entities > 0 else 0.0
    
    def _evaluate_relationship_extraction(self, texts: List[str]) -> float:
        """Evaluate biological relationship extraction performance"""
        
        # Simple heuristic: look for relationship keywords
        relationship_keywords = [
            'interacts with', 'converts', 'produces', 'catalyzes', 'regulates',
            'activates', 'inhibits', 'binds to', 'located in'
        ]
        
        total_relationships = 0
        found_relationships = 0
        
        for text in texts:
            text_lower = text.lower()
            for keyword in relationship_keywords:
                total_relationships += 1
                if keyword in text_lower:
                    found_relationships += 1
        
        return found_relationships / total_relationships if total_relationships > 0 else 0.0
    
    def _evaluate_coherence_prediction(self, texts: List[str]) -> float:
        """Evaluate pathway coherence prediction performance"""
        
        # Simple heuristic: texts with quantitative values tend to be more coherent
        coherent_indicators = [
            'score', 'value', 'concentration', 'frequency', 'density',
            'coefficient', 'factor', 'ratio'
        ]
        
        coherent_texts = 0
        
        for text in texts:
            text_lower = text.lower()
            if any(indicator in text_lower for indicator in coherent_indicators):
                coherent_texts += 1
        
        return coherent_texts / len(texts) if texts else 0.0
    
    def _assess_model_performance(self, comparison_results: Dict) -> Dict:
        """Assess overall model performance"""
        
        assessment = {
            'overall_score': 0.0,
            'strengths': [],
            'weaknesses': [],
            'recommendations': []
        }
        
        # Calculate overall score
        similarity_scores = []
        for model_results in comparison_results.get('semantic_similarity', {}).values():
            similarity_scores.append(model_results.get('average_similarity', 0))
        
        if similarity_scores:
            avg_similarity = np.mean(similarity_scores)
            assessment['overall_score'] = avg_similarity
            
            # Assess performance
            if avg_similarity > 0.7:
                assessment['strengths'].append("High semantic similarity with reference models")
            elif avg_similarity > 0.5:
                assessment['strengths'].append("Moderate semantic similarity with reference models")
            else:
                assessment['weaknesses'].append("Low semantic similarity with reference models")
        
        # Assess text quality
        text_count = comparison_results.get('network_texts_count', 0)
        if text_count > 50:
            assessment['strengths'].append("Rich textual representation of biological networks")
        elif text_count > 20:
            assessment['strengths'].append("Adequate textual representation")
        else:
            assessment['weaknesses'].append("Limited textual representation")
        
        # Recommendations
        if assessment['overall_score'] < 0.6:
            assessment['recommendations'].append("Consider enriching network descriptions with more biological context")
            assessment['recommendations'].append("Add more domain-specific terminology")
        
        if text_count < 30:
            assessment['recommendations'].append("Generate more diverse textual descriptions")
        
        return assessment
    
    def visualize_comparison_results(self, comparison_results: Dict) -> None:
        """Visualize comparison results"""
        
        # Similarity comparison plot
        similarity_data = comparison_results.get('semantic_similarity', {})
        
        if similarity_data:
            models = list(similarity_data.keys())
            avg_similarities = [similarity_data[model]['average_similarity'] for model in models]
            
            plt.figure(figsize=(10, 6))
            
            # Bar plot of similarities
            plt.subplot(1, 2, 1)
            bars = plt.bar(models, avg_similarities, color='skyblue', alpha=0.7)
            plt.ylabel('Average Cosine Similarity')
            plt.title('Semantic Similarity with Reference Models')
            plt.xticks(rotation=45)
            plt.ylim(0, 1)
            
            # Add value labels on bars
            for bar, similarity in zip(bars, avg_similarities):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f'{similarity:.3f}', ha='center', va='bottom')
            
            # Overall assessment radar chart
            plt.subplot(1, 2, 2)
            assessment = comparison_results.get('assessment', {})
            overall_score = assessment.get('overall_score', 0)
            
            # Simple performance indicator
            colors = ['red' if overall_score < 0.4 else 'orange' if overall_score < 0.7 else 'green']
            plt.pie([overall_score, 1-overall_score], labels=['Performance', 'Room for Improvement'],
                   colors=colors + ['lightgray'], startangle=90)
            plt.title(f'Overall Performance Score: {overall_score:.3f}')
            
            plt.tight_layout()
            plt.show()
    
    def generate_model_summary(self, analysis_results: Dict, comparison_results: Dict) -> str:
        """Generate a comprehensive model summary"""
        
        summary = []
        summary.append("# Biological Network LLM Analysis Summary\n")
        
        # Network characteristics
        network_texts = self.convert_network_to_text(analysis_results)
        summary.append(f"## Network-to-Text Conversion")
        summary.append(f"- Generated {len(network_texts)} textual descriptions")
        summary.append(f"- Created {len(self.qa_pairs)} question-answer pairs")
        summary.append("")
        
        # Comparison results
        summary.append("## Comparison with Reference Models")
        similarity_data = comparison_results.get('semantic_similarity', {})
        
        for model_name, sim_data in similarity_data.items():
            avg_sim = sim_data.get('average_similarity', 0)
            summary.append(f"- {model_name}: {avg_sim:.3f} average similarity")
        
        summary.append("")
        
        # Assessment
        assessment = comparison_results.get('assessment', {})
        summary.append("## Performance Assessment")
        summary.append(f"- Overall Score: {assessment.get('overall_score', 0):.3f}")
        
        strengths = assessment.get('strengths', [])
        if strengths:
            summary.append("- Strengths:")
            for strength in strengths:
                summary.append(f"  * {strength}")
        
        weaknesses = assessment.get('weaknesses', [])
        if weaknesses:
            summary.append("- Areas for Improvement:")
            for weakness in weaknesses:
                summary.append(f"  * {weakness}")
        
        recommendations = assessment.get('recommendations', [])
        if recommendations:
            summary.append("- Recommendations:")
            for rec in recommendations:
                summary.append(f"  * {rec}")
        
        return "\n".join(summary)

def create_network_llm_comparison(analysis_results: Dict, 
                                huggingface_api_key: str = None) -> Dict:
    """
    Main function to create and compare biological network LLM
    
    Args:
        analysis_results: Results from Wilhelm analysis pipeline
        huggingface_api_key: Optional Hugging Face API key
        
    Returns:
        Dictionary containing LLM analysis and comparison results
    """
    
    print("Creating biological network LLM comparison...")
    
    # Initialize LLM system
    network_llm = BiologicalNetworkLLM(huggingface_api_key)
    
    # Convert network to text
    network_texts = network_llm.convert_network_to_text(analysis_results)
    
    # Create training data
    training_dataset = network_llm.create_training_data(analysis_results)
    
    # Compare with reference models
    comparison_results = network_llm.compare_with_reference_models(analysis_results)
    
    # Generate summary
    model_summary = network_llm.generate_model_summary(analysis_results, comparison_results)
    
    # Visualize results
    try:
        network_llm.visualize_comparison_results(comparison_results)
    except Exception as e:
        print(f"Could not create visualizations: {e}")
    
    llm_analysis = {
        'network_llm': network_llm,
        'network_texts': network_texts,
        'training_dataset': training_dataset,
        'comparison_results': comparison_results,
        'model_summary': model_summary,
        'qa_pairs': network_llm.qa_pairs,
        'assessment': comparison_results.get('assessment', {}),
        'metadata': {
            'total_texts_generated': len(network_texts),
            'reference_models_compared': len(comparison_results.get('semantic_similarity', {})),
            'overall_performance_score': comparison_results.get('assessment', {}).get('overall_score', 0)
        }
    }
    
    print(f"LLM comparison complete:")
    print(f"  Generated texts: {len(network_texts)}")
    print(f"  Reference models compared: {len(comparison_results.get('semantic_similarity', {}))}")
    print(f"  Overall performance: {llm_analysis['metadata']['overall_performance_score']:.3f}")
    
    return llm_analysis

# Usage example
if __name__ == "__main__":
    # Example usage (would normally get results from analysis pipeline)
    example_results = {
        'sbml_components': {
            'summary': {'num_species': 10, 'num_reactions': 8, 'num_compartments': 2}
        },
        'molecular_network': {
            'summary': {'network_density': 0.3, 'total_species': 10}
        }
    }
    
    llm_analysis = create_network_llm_comparison(example_results)
    print(llm_analysis['model_summary'])