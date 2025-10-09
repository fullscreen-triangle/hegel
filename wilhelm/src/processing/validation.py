# Cross-modal biological validation across multiple representation modes
import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Tuple, Any
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import silhouette_score
from sklearn.cluster import KMeans

def cross_modal_biological_validation(genomic_coordinates: Dict,
                                    protein_coordinates: Dict,
                                    metabolic_coordinates: Dict,
                                    circuit_coordinates: Dict,
                                    consistency_threshold: float = 0.95) -> Dict:
    """
    Validate results across multiple biological representation modes
    Ensures consistency between genomic, protein, metabolic, and circuit representations
    """
    print("Performing cross-modal biological validation...")
    
    # Initialize validator
    validator = CrossModalValidator(consistency_threshold)
    
    # Perform cross-modal consistency analysis
    consistency_analysis = validator.analyze_cross_modal_consistency(
        genomic_coordinates, protein_coordinates, metabolic_coordinates, circuit_coordinates
    )
    
    # Validate coordinate transformations
    transformation_validation = validator.validate_coordinate_transformations(
        genomic_coordinates, protein_coordinates, metabolic_coordinates, circuit_coordinates
    )
    
    # Perform statistical validation
    statistical_validation = validator.perform_statistical_validation(
        genomic_coordinates, protein_coordinates, metabolic_coordinates, circuit_coordinates
    )
    
    # Validate biological interpretability
    interpretability_validation = validator.validate_biological_interpretability(
        genomic_coordinates, protein_coordinates, metabolic_coordinates, circuit_coordinates
    )
    
    # Generate validation report
    validation_report = validator.generate_validation_report(
        consistency_analysis, transformation_validation, 
        statistical_validation, interpretability_validation
    )
    
    validation_results = {
        'validator': validator,
        'consistency_analysis': consistency_analysis,
        'transformation_validation': transformation_validation,
        'statistical_validation': statistical_validation,
        'interpretability_validation': interpretability_validation,
        'validation_report': validation_report,
        'overall_validity': validation_report['overall_validity_score'] >= consistency_threshold,
        'summary': {
            'consistency_score': consistency_analysis.get('overall_consistency', 0.0),
            'transformation_accuracy': transformation_validation.get('overall_accuracy', 0.0),
            'statistical_significance': statistical_validation.get('overall_significance', 0.0),
            'biological_interpretability': interpretability_validation.get('overall_interpretability', 0.0),
            'validation_passed': validation_report['overall_validity_score'] >= consistency_threshold
        }
    }
    
    print(f"Cross-modal validation complete:")
    print(f"  Overall validity score: {validation_report['overall_validity_score']:.3f}")
    print(f"  Consistency score: {consistency_analysis.get('overall_consistency', 0.0):.3f}")
    print(f"  Validation passed: {validation_results['overall_validity']}")
    
    return validation_results

class CrossModalValidator:
    """
    Cross-modal validator for biological coordinate systems
    """
    
    def __init__(self, consistency_threshold: float = 0.95):
        self.consistency_threshold = consistency_threshold
        self.validation_cache = {}
        
    def analyze_cross_modal_consistency(self, genomic_coords: Dict, protein_coords: Dict,
                                      metabolic_coords: Dict, circuit_coords: Dict) -> Dict:
        """Analyze consistency across different coordinate representations"""
        
        # Find common entities across all coordinate systems
        common_entities = self.find_common_entities(
            genomic_coords, protein_coords, metabolic_coords, circuit_coords
        )
        
        if not common_entities:
            return {'overall_consistency': 0.0, 'error': 'No common entities found'}
        
        # Calculate pairwise consistency scores
        consistency_scores = {}
        
        # Genomic vs Protein
        consistency_scores['genomic_protein'] = self.calculate_pairwise_consistency(
            genomic_coords, protein_coords, common_entities
        )
        
        # Genomic vs Metabolic
        consistency_scores['genomic_metabolic'] = self.calculate_pairwise_consistency(
            genomic_coords, metabolic_coords, common_entities
        )
        
        # Genomic vs Circuit
        consistency_scores['genomic_circuit'] = self.calculate_pairwise_consistency(
            genomic_coords, circuit_coords, common_entities
        )
        
        # Protein vs Metabolic
        consistency_scores['protein_metabolic'] = self.calculate_pairwise_consistency(
            protein_coords, metabolic_coords, common_entities
        )
        
        # Protein vs Circuit
        consistency_scores['protein_circuit'] = self.calculate_pairwise_consistency(
            protein_coords, circuit_coords, common_entities
        )
        
        # Metabolic vs Circuit
        consistency_scores['metabolic_circuit'] = self.calculate_pairwise_consistency(
            metabolic_coords, circuit_coords, common_entities
        )
        
        # Calculate overall consistency
        all_scores = list(consistency_scores.values())
        overall_consistency = np.mean(all_scores) if all_scores else 0.0
        
        consistency_analysis = {
            'common_entities': common_entities,
            'pairwise_consistency': consistency_scores,
            'overall_consistency': overall_consistency,
            'consistency_distribution': {
                'mean': np.mean(all_scores),
                'std': np.std(all_scores),
                'min': np.min(all_scores),
                'max': np.max(all_scores)
            }
        }
        
        return consistency_analysis
    
    def find_common_entities(self, *coordinate_dicts) -> List[str]:
        """Find entities common to all coordinate systems"""
        if not coordinate_dicts:
            return []
        
        # Start with entities from first coordinate system
        common_entities = set(coordinate_dicts[0].keys())
        
        # Find intersection with all other systems
        for coord_dict in coordinate_dicts[1:]:
            common_entities = common_entities.intersection(set(coord_dict.keys()))
        
        return list(common_entities)
    
    def calculate_pairwise_consistency(self, coords1: Dict, coords2: Dict, 
                                     common_entities: List[str]) -> float:
        """Calculate consistency between two coordinate systems"""
        if not common_entities:
            return 0.0
        
        # Extract coordinate vectors for common entities
        vectors1 = []
        vectors2 = []
        
        for entity in common_entities:
            if entity in coords1 and entity in coords2:
                vec1 = np.array(coords1[entity])
                vec2 = np.array(coords2[entity])
                
                # Ensure same dimensionality (pad with zeros if needed)
                max_dim = max(len(vec1), len(vec2))
                if len(vec1) < max_dim:
                    vec1 = np.pad(vec1, (0, max_dim - len(vec1)))
                if len(vec2) < max_dim:
                    vec2 = np.pad(vec2, (0, max_dim - len(vec2)))
                
                vectors1.append(vec1)
                vectors2.append(vec2)
        
        if not vectors1:
            return 0.0
        
        vectors1 = np.array(vectors1)
        vectors2 = np.array(vectors2)
        
        # Calculate consistency measures
        consistency_measures = []
        
        # Correlation-based consistency
        for dim in range(min(vectors1.shape[1], vectors2.shape[1])):
            if np.std(vectors1[:, dim]) > 1e-6 and np.std(vectors2[:, dim]) > 1e-6:
                corr, _ = pearsonr(vectors1[:, dim], vectors2[:, dim])
                consistency_measures.append(abs(corr))
        
        # Distance-based consistency
        distances1 = self.calculate_pairwise_distances(vectors1)
        distances2 = self.calculate_pairwise_distances(vectors2)
        
        if len(distances1) > 0 and len(distances2) > 0:
            distance_corr, _ = spearmanr(distances1, distances2)
            consistency_measures.append(abs(distance_corr))
        
        # Ranking consistency
        ranking_consistency = self.calculate_ranking_consistency(vectors1, vectors2)
        consistency_measures.append(ranking_consistency)
        
        # Overall consistency
        overall_consistency = np.mean(consistency_measures) if consistency_measures else 0.0
        
        return overall_consistency
    
    def calculate_pairwise_distances(self, vectors: np.array) -> List[float]:
        """Calculate all pairwise distances in vector set"""
        distances = []
        n = len(vectors)
        
        for i in range(n):
            for j in range(i + 1, n):
                distance = np.linalg.norm(vectors[i] - vectors[j])
                distances.append(distance)
        
        return distances
    
    def calculate_ranking_consistency(self, vectors1: np.array, vectors2: np.array) -> float:
        """Calculate consistency of entity rankings between coordinate systems"""
        # Rank entities by magnitude in each system
        magnitudes1 = [np.linalg.norm(vec) for vec in vectors1]
        magnitudes2 = [np.linalg.norm(vec) for vec in vectors2]
        
        # Calculate Spearman rank correlation
        if len(magnitudes1) > 1 and len(magnitudes2) > 1:
            rank_corr, _ = spearmanr(magnitudes1, magnitudes2)
            return abs(rank_corr)
        
        return 0.0
    
    def validate_coordinate_transformations(self, genomic_coords: Dict, protein_coords: Dict,
                                          metabolic_coords: Dict, circuit_coords: Dict) -> Dict:
        """Validate coordinate transformation accuracy"""
        
        transformation_tests = {}
        
        # Test coordinate preservation under transformations
        all_coords = {
            'genomic': genomic_coords,
            'protein': protein_coords,
            'metabolic': metabolic_coords,
            'circuit': circuit_coords
        }
        
        for name1, coords1 in all_coords.items():
            for name2, coords2 in all_coords.items():
                if name1 != name2:
                    test_name = f"{name1}_to_{name2}"
                    accuracy = self.test_transformation_accuracy(coords1, coords2)
                    transformation_tests[test_name] = accuracy
        
        # Test coordinate space properties
        space_properties = self.validate_coordinate_space_properties(all_coords)
        
        # Test transformation invertibility
        invertibility_tests = self.test_transformation_invertibility(all_coords)
        
        transformation_validation = {
            'transformation_accuracy': transformation_tests,
            'space_properties': space_properties,
            'invertibility_tests': invertibility_tests,
            'overall_accuracy': np.mean(list(transformation_tests.values())) if transformation_tests else 0.0
        }
        
        return transformation_validation
    
    def test_transformation_accuracy(self, coords1: Dict, coords2: Dict) -> float:
        """Test accuracy of transformation between coordinate systems"""
        common_entities = set(coords1.keys()).intersection(set(coords2.keys()))
        
        if len(common_entities) < 2:
            return 0.0
        
        # Test preservation of relative distances
        entities = list(common_entities)[:50]  # Limit for performance
        
        distances1 = []
        distances2 = []
        
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                vec1_1 = np.array(coords1[entity1])
                vec1_2 = np.array(coords1[entity2])
                dist1 = np.linalg.norm(vec1_1 - vec1_2)
                
                vec2_1 = np.array(coords2[entity1])
                vec2_2 = np.array(coords2[entity2])
                dist2 = np.linalg.norm(vec2_1 - vec2_2)
                
                distances1.append(dist1)
                distances2.append(dist2)
        
        if len(distances1) > 1:
            # Correlation of distance preservation
            corr, _ = pearsonr(distances1, distances2)
            return abs(corr)
        
        return 0.0
    
    def validate_coordinate_space_properties(self, all_coords: Dict) -> Dict:
        """Validate mathematical properties of coordinate spaces"""
        properties = {}
        
        for name, coords in all_coords.items():
            if not coords:
                properties[name] = {'valid': False, 'error': 'Empty coordinate system'}
                continue
            
            vectors = [np.array(coord) for coord in coords.values()]
            
            # Test dimensional consistency
            dimensions = [len(vec) for vec in vectors]
            dim_consistent = len(set(dimensions)) <= 1
            
            # Test for NaN or infinite values
            has_invalid_values = any(np.any(np.isnan(vec)) or np.any(np.isinf(vec)) 
                                   for vec in vectors)
            
            # Test coordinate range
            all_values = np.concatenate(vectors) if vectors else np.array([])
            coord_range = np.max(all_values) - np.min(all_values) if len(all_values) > 0 else 0
            
            properties[name] = {
                'valid': dim_consistent and not has_invalid_values,
                'dimensional_consistency': dim_consistent,
                'has_invalid_values': has_invalid_values,
                'coordinate_range': coord_range,
                'num_entities': len(coords),
                'avg_dimension': np.mean(dimensions) if dimensions else 0
            }
        
        return properties
    
    def test_transformation_invertibility(self, all_coords: Dict) -> Dict:
        """Test if transformations are approximately invertible"""
        invertibility_tests = {}
        
        coord_names = list(all_coords.keys())
        
        for i, name1 in enumerate(coord_names):
            for name2 in coord_names[i+1:]:
                coords1 = all_coords[name1]
                coords2 = all_coords[name2]
                
                # Test round-trip accuracy (simplified)
                common_entities = set(coords1.keys()).intersection(set(coords2.keys()))
                
                if len(common_entities) >= 3:
                    # Sample entities for round-trip test
                    test_entities = list(common_entities)[:10]
                    
                    round_trip_errors = []
                    for entity in test_entities:
                        vec1 = np.array(coords1[entity])
                        vec2 = np.array(coords2[entity])
                        
                        # Simulate round-trip transformation (simplified)
                        # In practice, this would use actual transformation functions
                        reconstructed_vec1 = vec1 * (np.linalg.norm(vec2) / np.linalg.norm(vec1))
                        error = np.linalg.norm(vec1 - reconstructed_vec1) / np.linalg.norm(vec1)
                        round_trip_errors.append(error)
                    
                    avg_error = np.mean(round_trip_errors)
                    invertibility_score = max(0, 1 - avg_error)
                    
                    invertibility_tests[f"{name1}_{name2}"] = invertibility_score
        
        return invertibility_tests
    
    def perform_statistical_validation(self, genomic_coords: Dict, protein_coords: Dict,
                                     metabolic_coords: Dict, circuit_coords: Dict) -> Dict:
        """Perform statistical validation of coordinate systems"""
        
        all_coords = {
            'genomic': genomic_coords,
            'protein': protein_coords,
            'metabolic': metabolic_coords,
            'circuit': circuit_coords
        }
        
        statistical_tests = {}
        
        for name, coords in all_coords.items():
            if not coords:
                statistical_tests[name] = {'valid': False}
                continue
            
            vectors = [np.array(coord) for coord in coords.values()]
            
            # Normality tests (simplified)
            normality_scores = []
            for dim in range(min(len(vec) for vec in vectors) if vectors else 0):
                dim_values = [vec[dim] for vec in vectors if len(vec) > dim]
                if len(dim_values) > 3:
                    # Simplified normality test using skewness and kurtosis
                    from scipy.stats import skew, kurtosis
                    skewness = abs(skew(dim_values))
                    kurt = abs(kurtosis(dim_values))
                    normality_score = max(0, 1 - (skewness + kurt) / 10)
                    normality_scores.append(normality_score)
            
            # Clustering validation
            clustering_score = self.validate_clustering_quality(vectors)
            
            # Outlier detection
            outlier_analysis = self.detect_coordinate_outliers(vectors)
            
            statistical_tests[name] = {
                'valid': True,
                'normality_score': np.mean(normality_scores) if normality_scores else 0.0,
                'clustering_score': clustering_score,
                'outlier_analysis': outlier_analysis
            }
        
        # Calculate overall statistical significance
        valid_tests = [test for test in statistical_tests.values() if test.get('valid', False)]
        
        if valid_tests:
            overall_significance = np.mean([
                test.get('normality_score', 0) * 0.3 +
                test.get('clustering_score', 0) * 0.4 +
                (1 - test.get('outlier_analysis', {}).get('outlier_ratio', 1)) * 0.3
                for test in valid_tests
            ])
        else:
            overall_significance = 0.0
        
        return {
            'coordinate_tests': statistical_tests,
            'overall_significance': overall_significance
        }
    
    def validate_clustering_quality(self, vectors: List[np.array]) -> float:
        """Validate quality of natural clustering in coordinate space"""
        if len(vectors) < 3:
            return 0.0
        
        # Convert to array
        vector_array = np.array([vec for vec in vectors if len(vec) > 0])
        
        if vector_array.size == 0:
            return 0.0
        
        # Ensure consistent dimensions
        min_dim = min(vec.shape[0] for vec in vectors)
        vector_array = np.array([vec[:min_dim] for vec in vectors])
        
        # Test different numbers of clusters
        silhouette_scores = []
        
        for n_clusters in range(2, min(8, len(vectors))):
            try:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                cluster_labels = kmeans.fit_predict(vector_array)
                
                if len(set(cluster_labels)) > 1:
                    silhouette_avg = silhouette_score(vector_array, cluster_labels)
                    silhouette_scores.append(silhouette_avg)
            except:
                continue
        
        return max(silhouette_scores) if silhouette_scores else 0.0
    
    def detect_coordinate_outliers(self, vectors: List[np.array]) -> Dict:
        """Detect outliers in coordinate space"""
        if len(vectors) < 3:
            return {'outlier_ratio': 0.0, 'outlier_indices': []}
        
        # Calculate distances from centroid
        vector_array = np.array([vec for vec in vectors if len(vec) > 0])
        
        if vector_array.size == 0:
            return {'outlier_ratio': 0.0, 'outlier_indices': []}
        
        centroid = np.mean(vector_array, axis=0)
        distances = [np.linalg.norm(vec - centroid) for vec in vector_array]
        
        # Define outliers as points beyond 2 standard deviations
        mean_distance = np.mean(distances)
        std_distance = np.std(distances)
        outlier_threshold = mean_distance + 2 * std_distance
        
        outlier_indices = [i for i, dist in enumerate(distances) if dist > outlier_threshold]
        outlier_ratio = len(outlier_indices) / len(distances)
        
        return {
            'outlier_ratio': outlier_ratio,
            'outlier_indices': outlier_indices,
            'outlier_threshold': outlier_threshold,
            'distance_stats': {
                'mean': mean_distance,
                'std': std_distance,
                'max': max(distances),
                'min': min(distances)
            }
        }
    
    def validate_biological_interpretability(self, genomic_coords: Dict, protein_coords: Dict,
                                           metabolic_coords: Dict, circuit_coords: Dict) -> Dict:
        """Validate biological interpretability of coordinate systems"""
        
        interpretability_scores = {}
        
        # Test coordinate-function relationships
        all_coords = {
            'genomic': genomic_coords,
            'protein': protein_coords,
            'metabolic': metabolic_coords,
            'circuit': circuit_coords
        }
        
        for name, coords in all_coords.items():
            if not coords:
                interpretability_scores[name] = 0.0
                continue
            
            # Test biological relevance (simplified heuristics)
            bio_relevance_score = self.assess_biological_relevance(name, coords)
            
            # Test coordinate interpretability
            interpretability_score = self.assess_coordinate_interpretability(name, coords)
            
            # Combined score
            combined_score = 0.6 * bio_relevance_score + 0.4 * interpretability_score
            interpretability_scores[name] = combined_score
        
        overall_interpretability = np.mean(list(interpretability_scores.values())) if interpretability_scores else 0.0
        
        return {
            'interpretability_scores': interpretability_scores,
            'overall_interpretability': overall_interpretability
        }
    
    def assess_biological_relevance(self, coord_type: str, coords: Dict) -> float:
        """Assess biological relevance of coordinate system"""
        # Simplified biological relevance scoring
        relevance_score = 0.5  # Base score
        
        # Check coordinate magnitudes are reasonable for biological systems
        vectors = [np.array(coord) for coord in coords.values()]
        if vectors:
            all_values = np.concatenate(vectors)
            
            # Biological systems typically have coordinate values in reasonable ranges
            if np.all(all_values >= -100) and np.all(all_values <= 100):
                relevance_score += 0.2
            
            # Check for appropriate coordinate scaling
            value_range = np.max(all_values) - np.min(all_values)
            if 0.1 <= value_range <= 50:
                relevance_score += 0.2
            
            # Type-specific checks
            if coord_type == 'genomic' and len(coords) > 0:
                relevance_score += 0.1  # Bonus for having genomic data
            elif coord_type == 'protein' and len(coords) > 0:
                relevance_score += 0.1  # Bonus for having protein data
            elif coord_type == 'metabolic' and len(coords) > 0:
                relevance_score += 0.1  # Bonus for having metabolic data
            elif coord_type == 'circuit' and len(coords) > 0:
                relevance_score += 0.1  # Bonus for having circuit data
        
        return min(1.0, relevance_score)
    
    def assess_coordinate_interpretability(self, coord_type: str, coords: Dict) -> float:
        """Assess interpretability of coordinate values"""
        if not coords:
            return 0.0
        
        vectors = [np.array(coord) for coord in coords.values()]
        
        # Check for coordinate structure
        interpretability_score = 0.0
        
        # Dimensional consistency
        dimensions = [len(vec) for vec in vectors]
        if len(set(dimensions)) == 1:
            interpretability_score += 0.3
        
        # Value distribution
        all_values = np.concatenate(vectors) if vectors else np.array([])
        if len(all_values) > 0:
            # Check for reasonable distribution
            if not (np.all(all_values == 0) or np.any(np.isnan(all_values))):
                interpretability_score += 0.4
            
            # Check for structure in values
            if np.std(all_values) > 0.01:  # Not all the same value
                interpretability_score += 0.3
        
        return interpretability_score
    
    def generate_validation_report(self, consistency_analysis: Dict, transformation_validation: Dict,
                                 statistical_validation: Dict, interpretability_validation: Dict) -> Dict:
        """Generate comprehensive validation report"""
        
        # Calculate component scores
        consistency_score = consistency_analysis.get('overall_consistency', 0.0)
        transformation_score = transformation_validation.get('overall_accuracy', 0.0)
        statistical_score = statistical_validation.get('overall_significance', 0.0)
        interpretability_score = interpretability_validation.get('overall_interpretability', 0.0)
        
        # Weighted overall validity score
        overall_validity_score = (
            0.3 * consistency_score +
            0.25 * transformation_score +
            0.25 * statistical_score +
            0.2 * interpretability_score
        )
        
        # Generate recommendations
        recommendations = []
        
        if consistency_score < 0.8:
            recommendations.append("Low cross-modal consistency - review coordinate transformation methods")
        
        if transformation_score < 0.7:
            recommendations.append("Poor transformation accuracy - validate coordinate mapping functions")
        
        if statistical_score < 0.6:
            recommendations.append("Statistical validation concerns - check data quality and distributions")
        
        if interpretability_score < 0.5:
            recommendations.append("Low biological interpretability - review coordinate biological relevance")
        
        if overall_validity_score >= self.consistency_threshold:
            recommendations.append("Validation passed - coordinate systems are consistent and reliable")
        
        validation_report = {
            'overall_validity_score': overall_validity_score,
            'component_scores': {
                'consistency': consistency_score,
                'transformation': transformation_score,
                'statistical': statistical_score,
                'interpretability': interpretability_score
            },
            'validation_passed': overall_validity_score >= self.consistency_threshold,
            'recommendations': recommendations,
            'validation_summary': {
                'total_validations_performed': 4,
                'validations_passed': sum([
                    consistency_score >= 0.8,
                    transformation_score >= 0.7,
                    statistical_score >= 0.6,
                    interpretability_score >= 0.5
                ]),
                'critical_issues': len([score for score in [consistency_score, transformation_score, 
                                                           statistical_score, interpretability_score] 
                                      if score < 0.5])
            }
        }
        
        return validation_report

# Usage example
if __name__ == "__main__":
    print("Cross-modal Biological Validation module ready for use")
    print("Use cross_modal_biological_validation() to validate coordinate systems")