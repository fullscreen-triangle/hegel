# Complete Oscillatory Bayesian Network Implementation  
import networkx as nx
import numpy as np
from typing import Dict, List, Tuple
from scipy.stats import norm
import pandas as pd

class SEntropyNetworkAnalyzer:
    """
    S-Entropy Network Analyzer for oscillatory Bayesian networks
    Integrates with finite and transcendent observers for multi-scale analysis
    """
    
    def __init__(self, network: nx.Graph, s_coordinates: Dict):
        self.network = network
        self.s_coordinates = s_coordinates
        self.oscillatory_frequencies = {}
        self.bayesian_posterior = {}
    
    def calculate_s_distance(self, species1: str, species2: str) -> float:
        """Calculate S-entropy distance between species"""
        if species1 not in self.s_coordinates or species2 not in self.s_coordinates:
            return float('inf')
            
        coord1 = self.s_coordinates[species1]
        coord2 = self.s_coordinates[species2] 
        
        return np.linalg.norm(coord1 - coord2)
    
    def find_s_entropy_clusters(self, threshold: float = 1.0) -> List[List[str]]:
        """Find clusters of species with similar S-coordinates"""
        species_list = list(self.s_coordinates.keys())
        clusters = []
        visited = set()
        
        for species in species_list:
            if species in visited:
                continue
                
            cluster = [species]
            visited.add(species)
            
            for other_species in species_list:
                if other_species not in visited:
                    distance = self.calculate_s_distance(species, other_species)
                    if distance <= threshold:
                        cluster.append(other_species)
                        visited.add(other_species)
            
            if len(cluster) > 1:
                clusters.append(cluster)
                
        return clusters
    
    def analyze_pathway_coherence(self) -> float:
        """Calculate pathway coherence based on S-entropy coordinates"""
        total_coherence = 0.0
        edge_count = 0
        
        for edge in self.network.edges():
            node1, node2 = edge
            # Skip reaction nodes, only analyze species-species connections
            if node1 in self.s_coordinates and node2 in self.s_coordinates:
                distance = self.calculate_s_distance(node1, node2)
                coherence = 1.0 / (1.0 + distance)  # Higher coherence for smaller distances
                total_coherence += coherence
                edge_count += 1
        
        return total_coherence / edge_count if edge_count > 0 else 0.0
    
    def calculate_oscillatory_frequencies(self, sbml_components: Dict) -> Dict:
        """Calculate characteristic oscillatory frequencies for network components"""
        frequencies = {}
        
        for species_id, species_data in sbml_components['species'].items():
            if species_id in self.s_coordinates:
                # Extract frequency from S-entropy coordinates
                s_coord = self.s_coordinates[species_id]
                
                # Frequency based on S-entropy magnitude and kinetic properties
                s_magnitude = np.linalg.norm(s_coord)
                concentration = species_data.get('initial_concentration', 1.0)
                
                # Characteristic frequency calculation
                base_frequency = s_magnitude * concentration
                
                # Scale based on network connectivity
                degree = self.network.degree(species_id) if species_id in self.network else 1
                frequency = base_frequency * np.log(degree + 1)
                
                frequencies[species_id] = frequency
        
        self.oscillatory_frequencies = frequencies
        return frequencies
    
    def construct_bayesian_network_structure(self) -> nx.DiGraph:
        """Construct directed Bayesian network structure from oscillatory relationships"""
        bayesian_network = nx.DiGraph()
        
        # Add nodes
        for species_id in self.s_coordinates:
            bayesian_network.add_node(species_id, 
                                    s_coordinate=self.s_coordinates[species_id],
                                    frequency=self.oscillatory_frequencies.get(species_id, 1.0))
        
        # Add edges based on oscillatory coupling
        species_list = list(self.s_coordinates.keys())
        
        for i, species1 in enumerate(species_list):
            for species2 in species_list[i+1:]:
                # Calculate coupling strength based on frequency resonance
                freq1 = self.oscillatory_frequencies.get(species1, 1.0)
                freq2 = self.oscillatory_frequencies.get(species2, 1.0)
                
                # Resonance occurs when frequencies are in integer ratios
                freq_ratio = freq2 / freq1 if freq1 != 0 else 1.0
                closest_integer = round(freq_ratio)
                resonance_strength = np.exp(-abs(freq_ratio - closest_integer))
                
                # Add edge if resonance is strong enough
                if resonance_strength > 0.5:  # Threshold for significant coupling
                    s_distance = self.calculate_s_distance(species1, species2)
                    coupling_strength = resonance_strength / (1.0 + s_distance)
                    
                    # Determine direction based on frequency (higher freq influences lower)
                    if freq1 > freq2:
                        bayesian_network.add_edge(species1, species2, 
                                                weight=coupling_strength,
                                                coupling_type='oscillatory_resonance')
                    else:
                        bayesian_network.add_edge(species2, species1,
                                                weight=coupling_strength, 
                                                coupling_type='oscillatory_resonance')
        
        return bayesian_network
    
    def calculate_bayesian_posterior(self, evidence: Dict[str, float], 
                                   bayesian_network: nx.DiGraph) -> Dict[str, float]:
        """Calculate Bayesian posterior probabilities given evidence"""
        posterior = {}
        
        # Simple message passing algorithm for tree-like structures
        # For more complex networks, would need junction tree or variational methods
        
        for node in bayesian_network.nodes():
            if node in evidence:
                # Evidence node - use observed value
                posterior[node] = evidence[node]
            else:
                # Calculate posterior based on parent nodes
                parents = list(bayesian_network.predecessors(node))
                
                if not parents:
                    # Root node - use prior
                    posterior[node] = 0.5  # Uniform prior
                else:
                    # Weighted combination of parent posteriors
                    weighted_sum = 0.0
                    total_weight = 0.0
                    
                    for parent in parents:
                        if parent in posterior:
                            weight = bayesian_network[parent][node]['weight']
                            weighted_sum += posterior[parent] * weight
                            total_weight += weight
                    
                    if total_weight > 0:
                        posterior[node] = weighted_sum / total_weight
                    else:
                        posterior[node] = 0.5
        
        self.bayesian_posterior = posterior
        return posterior
    
    def predict_oscillatory_response(self, perturbation: Dict[str, float], 
                                   bayesian_network: nx.DiGraph) -> Dict[str, float]:
        """Predict oscillatory response to perturbations using Bayesian inference"""
        # Calculate posterior given perturbation as evidence
        posterior = self.calculate_bayesian_posterior(perturbation, bayesian_network)
        
        response = {}
        
        for species_id in self.s_coordinates:
            if species_id not in perturbation:
                # Calculate response based on posterior and oscillatory properties
                base_response = posterior.get(species_id, 0.0)
                
                # Amplify response based on oscillatory frequency
                frequency = self.oscillatory_frequencies.get(species_id, 1.0)
                frequency_amplification = np.log(frequency + 1)
                
                # Modulate based on S-entropy coordinate
                s_coord = self.s_coordinates[species_id]
                s_modulation = np.tanh(np.linalg.norm(s_coord))
                
                predicted_response = base_response * frequency_amplification * s_modulation
                response[species_id] = predicted_response
        
        return response
    
    def identify_oscillatory_holes(self, target_frequency: float, 
                                 tolerance: float = 0.1) -> List[Dict]:
        """Identify oscillatory holes that match target frequency"""
        holes = []
        
        for species_id, frequency in self.oscillatory_frequencies.items():
            frequency_diff = abs(frequency - target_frequency)
            
            if frequency_diff <= tolerance:
                # This could be an oscillatory hole for the target frequency
                s_coord = self.s_coordinates[species_id]
                
                hole_info = {
                    'species': species_id,
                    'frequency': frequency,
                    'frequency_match': 1.0 - (frequency_diff / tolerance),
                    's_coordinate': s_coord,
                    'hole_strength': np.linalg.norm(s_coord),
                    'network_connectivity': self.network.degree(species_id) if species_id in self.network else 0
                }
                holes.append(hole_info)
        
        # Sort by frequency match and hole strength
        holes.sort(key=lambda x: x['frequency_match'] * x['hole_strength'], reverse=True)
        
        return holes
    
    def calculate_therapeutic_potential(self, pharmaceutical_frequency: float,
                                      oscillatory_holes: List[Dict]) -> Dict:
        """Calculate therapeutic potential for pharmaceutical with given frequency"""
        therapeutic_analysis = {
            'pharmaceutical_frequency': pharmaceutical_frequency,
            'matching_holes': 0,
            'total_therapeutic_potential': 0.0,
            'hole_matches': []
        }
        
        for hole in oscillatory_holes:
            frequency_match = 1.0 - abs(hole['frequency'] - pharmaceutical_frequency) / pharmaceutical_frequency
            
            if frequency_match > 0.5:  # Significant match
                therapeutic_potential = frequency_match * hole['hole_strength']
                
                hole_match = {
                    'species': hole['species'],
                    'frequency_match': frequency_match,
                    'therapeutic_potential': therapeutic_potential,
                    's_distance_to_hole': np.linalg.norm(hole['s_coordinate'])
                }
                
                therapeutic_analysis['hole_matches'].append(hole_match)
                therapeutic_analysis['total_therapeutic_potential'] += therapeutic_potential
                therapeutic_analysis['matching_holes'] += 1
        
        return therapeutic_analysis

def create_oscillatory_bayesian_network(sbml_components: Dict, 
                                       s_coordinates: Dict,
                                       molecular_network: Dict) -> Dict:
    """
    Main function to create complete oscillatory Bayesian network
    Integrates S-entropy coordinates, molecular networks, and Bayesian inference
    """
    print("Creating oscillatory Bayesian network...")
    
    # Create S-entropy network analyzer
    species_graph = molecular_network.get('species_graph', nx.Graph())
    analyzer = SEntropyNetworkAnalyzer(species_graph, s_coordinates)
    
    # Calculate oscillatory frequencies
    frequencies = analyzer.calculate_oscillatory_frequencies(sbml_components)
    
    # Construct Bayesian network structure
    bayesian_network = analyzer.construct_bayesian_network_structure()
    
    # Analyze network properties
    pathway_coherence = analyzer.analyze_pathway_coherence()
    s_entropy_clusters = analyzer.find_s_entropy_clusters()
    
    # Identify oscillatory holes across frequency spectrum
    frequency_range = np.linspace(0.1, 10.0, 50)  # Sample frequency range
    all_oscillatory_holes = []
    
    for target_freq in frequency_range:
        holes = analyzer.identify_oscillatory_holes(target_freq)
        all_oscillatory_holes.extend(holes)
    
    oscillatory_bayesian_network = {
        'analyzer': analyzer,
        'bayesian_network': bayesian_network,
        'oscillatory_frequencies': frequencies,
        'pathway_coherence': pathway_coherence,
        's_entropy_clusters': s_entropy_clusters,
        'oscillatory_holes': all_oscillatory_holes,
        'network_properties': {
            'num_nodes': bayesian_network.number_of_nodes(),
            'num_edges': bayesian_network.number_of_edges(),
            'network_density': nx.density(bayesian_network),
            'is_connected': nx.is_weakly_connected(bayesian_network),
            'avg_frequency': np.mean(list(frequencies.values())) if frequencies else 0.0,
            'frequency_std': np.std(list(frequencies.values())) if frequencies else 0.0
        },
        'summary': {
            'species_analyzed': len(s_coordinates),
            'oscillatory_frequencies_calculated': len(frequencies),
            'pathway_coherence_score': pathway_coherence,
            'num_s_entropy_clusters': len(s_entropy_clusters),
            'total_oscillatory_holes': len(all_oscillatory_holes)
        }
    }
    
    print(f"Oscillatory Bayesian network complete:")
    print(f"  Species analyzed: {len(s_coordinates)}")
    print(f"  Bayesian network edges: {bayesian_network.number_of_edges()}")
    print(f"  Pathway coherence: {pathway_coherence:.3f}")
    print(f"  S-entropy clusters: {len(s_entropy_clusters)}")
    print(f"  Oscillatory holes identified: {len(all_oscillatory_holes)}")
    
    return oscillatory_bayesian_network

def demonstrate_therapeutic_prediction(oscillatory_network: Dict, 
                                     pharmaceutical_frequency: float) -> Dict:
    """Demonstrate therapeutic prediction using oscillatory Bayesian network"""
    analyzer = oscillatory_network['analyzer']
    bayesian_network = oscillatory_network['bayesian_network']
    
    print(f"\nPredicting therapeutic effects for frequency: {pharmaceutical_frequency:.2f}")
    
    # Find matching oscillatory holes
    oscillatory_holes = analyzer.identify_oscillatory_holes(pharmaceutical_frequency)
    
    # Calculate therapeutic potential
    therapeutic_analysis = analyzer.calculate_therapeutic_potential(
        pharmaceutical_frequency, oscillatory_holes
    )
    
    # Simulate perturbation
    if oscillatory_holes:
        best_match = oscillatory_holes[0]
        perturbation = {best_match['species']: pharmaceutical_frequency}
        
        # Predict network response
        response = analyzer.predict_oscillatory_response(perturbation, bayesian_network)
        
        therapeutic_analysis['predicted_response'] = response
        therapeutic_analysis['primary_target'] = best_match['species']
    
    print(f"  Matching holes: {therapeutic_analysis['matching_holes']}")
    print(f"  Therapeutic potential: {therapeutic_analysis['total_therapeutic_potential']:.3f}")
    
    return therapeutic_analysis

# Usage example
if __name__ == "__main__":
    print("Oscillatory Bayesian Network module ready for use")
    print("Use create_oscillatory_bayesian_network() to create network")
    print("Use demonstrate_therapeutic_prediction() for therapeutic analysis")