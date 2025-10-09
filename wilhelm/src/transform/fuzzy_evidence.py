# Complete Fuzzy Evidence Analysis with Windowing
import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Dict, List, Tuple, Any

class FuzzyWindowAnalyzer:
    """
    Complete Fuzzy Window Analyzer for S-entropy coordinates
    Applies tri-dimensional fuzzy windows for evidence processing
    """
    
    def __init__(self, window_centers: Tuple[float, float, float] = (0.5, 0.5, 0.5),
                 window_widths: Tuple[float, float, float] = (0.3, 0.3, 0.3)):
        self.centers = window_centers
        self.widths = window_widths
        self.evidence_cache = {}
        self.fuzzy_membership_functions = {}
        
    def fuzzy_aperture(self, x: float, center: float, width: float) -> float:
        """Gaussian fuzzy aperture function"""
        return np.exp(-((x - center) ** 2) / (2 * width ** 2))
    
    def triangular_membership(self, x: float, left: float, center: float, right: float) -> float:
        """Triangular membership function"""
        if x <= left or x >= right:
            return 0.0
        elif x <= center:
            return (x - left) / (center - left)
        else:
            return (right - x) / (right - center)
    
    def trapezoidal_membership(self, x: float, a: float, b: float, c: float, d: float) -> float:
        """Trapezoidal membership function"""
        if x <= a or x >= d:
            return 0.0
        elif a < x <= b:
            return (x - a) / (b - a)
        elif b < x <= c:
            return 1.0
        else:
            return (d - x) / (d - c)
    
    def apply_fuzzy_windows(self, s_coordinates: Dict) -> Dict:
        """Apply tri-dimensional fuzzy windows to S-coordinates"""
        windowed_data = {}
        
        for species_id, coord in s_coordinates.items():
            # Apply fuzzy windows to each dimension
            w_knowledge = self.fuzzy_aperture(coord[0], self.centers[0], self.widths[0])
            w_time = self.fuzzy_aperture(coord[1], self.centers[1], self.widths[1])  
            w_entropy = self.fuzzy_aperture(coord[2], self.centers[2], self.widths[2])
            
            # Combined weight
            combined_weight = w_knowledge * w_time * w_entropy
            
            windowed_data[species_id] = {
                'coordinates': coord,
                'weights': np.array([w_knowledge, w_time, w_entropy]),
                'combined_weight': combined_weight,
                'evidence_strength': self.calculate_evidence_strength(coord)
            }
            
        self.evidence_cache = windowed_data
        return windowed_data
    
    def calculate_evidence_strength(self, coordinate: np.array) -> float:
        """Calculate evidence strength based on coordinate properties"""
        # Distance from origin (information content)
        magnitude = np.linalg.norm(coordinate)
        
        # Balance across dimensions (coherence)
        if len(coordinate) >= 3:
            dimension_balance = 1.0 - np.std(coordinate) / (np.mean(np.abs(coordinate)) + 1e-6)
        else:
            dimension_balance = 1.0
        
        # Combined evidence strength
        evidence_strength = magnitude * dimension_balance
        
        return evidence_strength
    
    def create_fuzzy_evidence_network(self, windowed_data: Dict, 
                                    threshold: float = 0.1) -> Dict:
        """Create evidence network based on fuzzy similarity"""
        import networkx as nx
        
        G = nx.Graph()
        
        # Add nodes with evidence properties
        for species_id, evidence in windowed_data.items():
            G.add_node(species_id,
                      evidence_strength=evidence['evidence_strength'],
                      combined_weight=evidence['combined_weight'],
                      coordinates=evidence['coordinates'])
        
        # Add edges based on evidence similarity
        species_list = list(windowed_data.keys())
        
        for i, species1 in enumerate(species_list):
            for species2 in species_list[i+1:]:
                similarity = self.calculate_fuzzy_similarity(
                    windowed_data[species1], windowed_data[species2]
                )
                
                if similarity >= threshold:
                    G.add_edge(species1, species2, 
                              similarity=similarity,
                              evidence_coupling=similarity * windowed_data[species1]['evidence_strength'] *
                                              windowed_data[species2]['evidence_strength'])
        
        return {
            'evidence_network': G,
            'network_properties': {
                'num_nodes': G.number_of_nodes(),
                'num_edges': G.number_of_edges(),
                'density': nx.density(G),
                'is_connected': nx.is_connected(G),
                'avg_clustering': nx.average_clustering(G)
            }
        }
    
    def calculate_fuzzy_similarity(self, evidence1: Dict, evidence2: Dict) -> float:
        """Calculate fuzzy similarity between two evidence sets"""
        weights1 = evidence1['weights']
        weights2 = evidence2['weights']
        
        # Cosine similarity of weight vectors
        dot_product = np.dot(weights1, weights2)
        magnitude1 = np.linalg.norm(weights1)
        magnitude2 = np.linalg.norm(weights2)
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        cosine_similarity = dot_product / (magnitude1 * magnitude2)
        
        # Coordinate proximity
        coord1 = evidence1['coordinates']
        coord2 = evidence2['coordinates']
        coordinate_distance = np.linalg.norm(coord1 - coord2)
        proximity_similarity = np.exp(-coordinate_distance)
        
        # Combined similarity
        combined_similarity = 0.7 * cosine_similarity + 0.3 * proximity_similarity
        
        return max(0, combined_similarity)
    
    def perform_fuzzy_clustering(self, windowed_data: Dict, 
                                num_clusters: int = 3) -> Dict:
        """Perform fuzzy c-means clustering on evidence"""
        from sklearn.cluster import KMeans
        from scipy.spatial.distance import cdist
        
        # Prepare data for clustering
        species_ids = list(windowed_data.keys())
        evidence_features = []
        
        for species_id in species_ids:
            evidence = windowed_data[species_id]
            features = np.concatenate([
                evidence['coordinates'],
                evidence['weights'],
                [evidence['combined_weight'], evidence['evidence_strength']]
            ])
            evidence_features.append(features)
        
        evidence_array = np.array(evidence_features)
        
        # Perform K-means clustering (as approximation to fuzzy c-means)
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(evidence_array)
        
        # Calculate fuzzy membership (soft assignment)
        cluster_centers = kmeans.cluster_centers_
        distances = cdist(evidence_array, cluster_centers, metric='euclidean')
        
        # Convert distances to fuzzy memberships
        fuzzy_memberships = {}
        for i, species_id in enumerate(species_ids):
            species_distances = distances[i]
            # Inverse distance weighting for fuzzy membership
            inv_distances = 1.0 / (species_distances + 1e-6)
            memberships = inv_distances / np.sum(inv_distances)
            
            fuzzy_memberships[species_id] = {
                'hard_cluster': cluster_labels[i],
                'fuzzy_memberships': memberships,
                'primary_membership': np.max(memberships),
                'cluster_uncertainty': 1.0 - np.max(memberships)
            }
        
        return {
            'fuzzy_memberships': fuzzy_memberships,
            'cluster_centers': cluster_centers,
            'num_clusters': num_clusters,
            'clustering_quality': self.evaluate_clustering_quality(fuzzy_memberships)
        }
    
    def evaluate_clustering_quality(self, fuzzy_memberships: Dict) -> Dict:
        """Evaluate the quality of fuzzy clustering"""
        all_memberships = [fm['fuzzy_memberships'] for fm in fuzzy_memberships.values()]
        all_uncertainties = [fm['cluster_uncertainty'] for fm in fuzzy_memberships.values()]
        
        quality = {
            'avg_uncertainty': np.mean(all_uncertainties),
            'max_uncertainty': np.max(all_uncertainties),
            'min_uncertainty': np.min(all_uncertainties),
            'membership_entropy': np.mean([
                -np.sum(memberships * np.log2(memberships + 1e-6))
                for memberships in all_memberships
            ])
        }
        
        return quality
    
    def identify_evidence_patterns(self, windowed_data: Dict) -> Dict:
        """Identify patterns in fuzzy evidence"""
        patterns = {
            'high_evidence_species': [],
            'low_evidence_species': [],
            'balanced_evidence_species': [],
            'dominant_dimensions': {'knowledge': [], 'time': [], 'entropy': []},
            'evidence_distribution': {}
        }
        
        # Collect evidence statistics
        evidence_strengths = [e['evidence_strength'] for e in windowed_data.values()]
        combined_weights = [e['combined_weight'] for e in windowed_data.values()]
        
        if evidence_strengths:
            evidence_threshold_high = np.percentile(evidence_strengths, 75)
            evidence_threshold_low = np.percentile(evidence_strengths, 25)
            
            # Categorize species by evidence strength
            for species_id, evidence in windowed_data.items():
                strength = evidence['evidence_strength']
                
                if strength >= evidence_threshold_high:
                    patterns['high_evidence_species'].append((species_id, strength))
                elif strength <= evidence_threshold_low:
                    patterns['low_evidence_species'].append((species_id, strength))
                else:
                    patterns['balanced_evidence_species'].append((species_id, strength))
                
                # Check dominant dimensions
                weights = evidence['weights']
                dominant_dim = np.argmax(weights)
                
                if dominant_dim == 0:
                    patterns['dominant_dimensions']['knowledge'].append(species_id)
                elif dominant_dim == 1:
                    patterns['dominant_dimensions']['time'].append(species_id)
                elif dominant_dim == 2:
                    patterns['dominant_dimensions']['entropy'].append(species_id)
            
            # Evidence distribution statistics
            patterns['evidence_distribution'] = {
                'mean_strength': np.mean(evidence_strengths),
                'std_strength': np.std(evidence_strengths),
                'mean_weight': np.mean(combined_weights),
                'std_weight': np.std(combined_weights)
            }
        
        return patterns
    
    def calculate_evidence_confidence(self, windowed_data: Dict, 
                                    molecular_network: nx.Graph = None) -> Dict:
        """Calculate confidence scores for evidence"""
        confidence_scores = {}
        
        for species_id, evidence in windowed_data.items():
            # Base confidence from evidence strength
            base_confidence = evidence['evidence_strength']
            
            # Weight balance confidence
            weights = evidence['weights']
            weight_balance = 1.0 - np.std(weights) / (np.mean(weights) + 1e-6)
            
            # Network support confidence
            network_confidence = 1.0
            if molecular_network and species_id in molecular_network:
                degree = molecular_network.degree(species_id)
                network_confidence = np.log(degree + 1) / 10.0  # Normalized
            
            # Combined confidence
            total_confidence = (0.5 * base_confidence + 
                              0.3 * weight_balance + 
                              0.2 * network_confidence)
            
            confidence_scores[species_id] = {
                'total_confidence': total_confidence,
                'base_confidence': base_confidence,
                'weight_balance': weight_balance,
                'network_confidence': network_confidence,
                'confidence_category': self.categorize_confidence(total_confidence)
            }
        
        return confidence_scores
    
    def categorize_confidence(self, confidence: float) -> str:
        """Categorize confidence level"""
        if confidence >= 0.8:
            return 'high'
        elif confidence >= 0.5:
            return 'medium'
        elif confidence >= 0.2:
            return 'low'
        else:
            return 'very_low'
    
    def generate_evidence_report(self, windowed_data: Dict, 
                               confidence_scores: Dict,
                               evidence_patterns: Dict) -> Dict:
        """Generate comprehensive evidence analysis report"""
        report = {
            'summary': {
                'total_species_analyzed': len(windowed_data),
                'high_confidence_species': len([s for s, c in confidence_scores.items() 
                                              if c['confidence_category'] == 'high']),
                'evidence_coverage': len([s for s, e in windowed_data.items() 
                                        if e['combined_weight'] > 0.1]),
                'avg_evidence_strength': np.mean([e['evidence_strength'] 
                                                for e in windowed_data.values()])
            },
            'evidence_distribution': evidence_patterns['evidence_distribution'],
            'pattern_analysis': evidence_patterns,
            'confidence_analysis': {
                'confidence_distribution': {
                    category: len([s for s, c in confidence_scores.items() 
                                 if c['confidence_category'] == category])
                    for category in ['high', 'medium', 'low', 'very_low']
                }
            },
            'recommendations': self.generate_evidence_recommendations(
                windowed_data, confidence_scores, evidence_patterns
            )
        }
        
        return report
    
    def generate_evidence_recommendations(self, windowed_data: Dict,
                                        confidence_scores: Dict,
                                        evidence_patterns: Dict) -> List[str]:
        """Generate recommendations based on evidence analysis"""
        recommendations = []
        
        # Check evidence coverage
        low_evidence_count = len(evidence_patterns['low_evidence_species'])
        total_species = len(windowed_data)
        
        if low_evidence_count / total_species > 0.3:
            recommendations.append(
                f"Consider increasing evidence collection - {low_evidence_count}/{total_species} "
                "species have low evidence strength"
            )
        
        # Check dimension balance
        for dim, species_list in evidence_patterns['dominant_dimensions'].items():
            if len(species_list) / total_species > 0.5:
                recommendations.append(
                    f"Evidence is heavily skewed toward {dim} dimension - "
                    "consider balancing evidence collection"
                )
        
        # Check confidence distribution
        high_conf_count = len([s for s, c in confidence_scores.items() 
                              if c['confidence_category'] == 'high'])
        
        if high_conf_count / total_species < 0.2:
            recommendations.append(
                "Low overall confidence in evidence - consider additional validation"
            )
        
        return recommendations

def create_fuzzy_evidence_system(s_coordinates: Dict, 
                               molecular_network: Dict = None,
                               window_centers: Tuple[float, float, float] = (0.5, 0.5, 0.5),
                               window_widths: Tuple[float, float, float] = (0.3, 0.3, 0.3)) -> Dict:
    """
    Create complete fuzzy evidence analysis system
    """
    print("Creating fuzzy evidence system...")
    
    # Initialize fuzzy window analyzer
    analyzer = FuzzyWindowAnalyzer(window_centers, window_widths)
    
    # Apply fuzzy windows
    windowed_data = analyzer.apply_fuzzy_windows(s_coordinates)
    
    # Create evidence network
    evidence_network = analyzer.create_fuzzy_evidence_network(windowed_data)
    
    # Perform fuzzy clustering
    fuzzy_clustering = analyzer.perform_fuzzy_clustering(windowed_data)
    
    # Identify evidence patterns
    evidence_patterns = analyzer.identify_evidence_patterns(windowed_data)
    
    # Calculate confidence scores
    network_graph = molecular_network.get('species_graph') if molecular_network else None
    confidence_scores = analyzer.calculate_evidence_confidence(windowed_data, network_graph)
    
    # Generate comprehensive report
    evidence_report = analyzer.generate_evidence_report(
        windowed_data, confidence_scores, evidence_patterns
    )
    
    fuzzy_evidence_system = {
        'analyzer': analyzer,
        'windowed_data': windowed_data,
        'evidence_network': evidence_network,
        'fuzzy_clustering': fuzzy_clustering,
        'evidence_patterns': evidence_patterns,
        'confidence_scores': confidence_scores,
        'evidence_report': evidence_report,
        'summary': {
            'species_analyzed': len(windowed_data),
            'evidence_network_edges': evidence_network['network_properties']['num_edges'],
            'fuzzy_clusters': fuzzy_clustering['num_clusters'],
            'avg_evidence_strength': evidence_report['summary']['avg_evidence_strength'],
            'high_confidence_species': evidence_report['summary']['high_confidence_species']
        }
    }
    
    print(f"Fuzzy evidence system complete:")
    print(f"  Species analyzed: {len(windowed_data)}")
    print(f"  Evidence network edges: {evidence_network['network_properties']['num_edges']}")
    print(f"  Fuzzy clusters: {fuzzy_clustering['num_clusters']}")
    print(f"  High confidence species: {evidence_report['summary']['high_confidence_species']}")
    
    return fuzzy_evidence_system

# Usage example
if __name__ == "__main__":
    print("Fuzzy Evidence Analysis module ready for use")
    print("Use create_fuzzy_evidence_system(s_coordinates) to create evidence system")