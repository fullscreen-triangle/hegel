# S-Entropy Coordinate Transformer - Complete Implementation
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any

class SEntropyCoordinateMapper:
    """
    Complete S-Entropy Coordinate Mapping System
    Transforms molecular data into navigable S-entropy coordinate space
    """
    
    def __init__(self):
        # Cardinal directions mapping from molecular-language theory
        self.base_mapping = {
            'A': np.array([0, 1]),   # North
            'T': np.array([0, -1]),  # South  
            'G': np.array([1, 0]),   # East
            'C': np.array([-1, 0])   # West
        }
        
        # Extended mapping for other molecular types
        self.extended_mapping = {
            # Amino acids
            'ALA': np.array([0.5, 0.5]),    # Alanine
            'VAL': np.array([0.5, -0.5]),   # Valine  
            'LEU': np.array([-0.5, 0.5]),   # Leucine
            'ILE': np.array([-0.5, -0.5]),  # Isoleucine
            'PHE': np.array([1, 1]),        # Phenylalanine
            'TRP': np.array([1, -1]),       # Tryptophan
            'TYR': np.array([-1, 1]),       # Tyrosine
            'PRO': np.array([-1, -1]),      # Proline
            
            # Common metabolites
            'GLC': np.array([0.7, 0.7]),    # Glucose
            'ATP': np.array([1.5, 0]),      # ATP
            'ADP': np.array([1, 0]),        # ADP
            'AMP': np.array([0.5, 0]),      # AMP
            'NAD': np.array([0, 1.5]),      # NAD+
            'NADH': np.array([0, 1]),       # NADH
            
            # Default patterns
            'UNKNOWN': np.array([0, 0])     # Unknown molecules
        }
        
        self.coordinate_cache = {}
    
    def calculate_knowledge_weight(self, species_data: Dict) -> float:
        """Calculate information content measure based on molecular complexity"""
        # Base calculation from name length
        name_length = len(species_data.get('name', ''))
        base_weight = -np.log2(max(name_length / 20.0, 0.01))
        
        # Enhance based on molecular properties
        concentration = species_data.get('initial_concentration', 0)
        if concentration > 0:
            concentration_weight = -np.log2(concentration / 100.0) if concentration < 100 else 0
        else:
            concentration_weight = 0
        
        # Boundary condition enhancement
        boundary_enhancement = 0.5 if species_data.get('boundary_condition', False) else 0
        
        # Compartment complexity
        compartment = species_data.get('compartment', '')
        compartment_weight = len(compartment) / 20.0 if compartment else 0
        
        total_weight = base_weight + 0.3 * concentration_weight + boundary_enhancement + compartment_weight
        
        # Normalize to [0, 2] range
        return max(0, min(2, total_weight))
    
    def calculate_time_weight(self, species_data: Dict, position: int, 
                            reaction_context: List[Dict] = None) -> float:
        """Calculate temporal dynamics coordinate with reaction context"""
        # Base calculation
        concentration = species_data.get('initial_concentration', 0)
        base_time = concentration * position / 100.0
        
        # Reaction kinetics enhancement
        kinetic_enhancement = 0
        if reaction_context:
            for reaction in reaction_context:
                # Look for this species in reaction
                species_id = species_data.get('id', '')
                
                # Check if species is involved
                is_reactant = any(r['species'] == species_id for r in reaction.get('reactants', []))
                is_product = any(p['species'] == species_id for p in reaction.get('products', []))
                is_modifier = any(m['species'] == species_id for m in reaction.get('modifiers', []))
                
                if is_reactant:
                    kinetic_enhancement += 0.3  # Consumed over time
                elif is_product:
                    kinetic_enhancement += 0.5  # Produced over time
                elif is_modifier:
                    kinetic_enhancement += 0.2  # Catalytic role
        
        # Reversible reaction enhancement
        if reaction_context:
            reversible_count = sum(1 for r in reaction_context if r.get('reversible', False))
            reversible_enhancement = reversible_count * 0.1
        else:
            reversible_enhancement = 0
        
        total_time_weight = base_time + kinetic_enhancement + reversible_enhancement
        
        # Normalize to [0, 2] range
        return max(0, min(2, total_time_weight))
    
    def calculate_entropy_weight(self, species_data: Dict, context_window: List[Dict],
                               network_connectivity: int = 0) -> float:
        """Calculate disorder measure with network topology"""
        if not context_window:
            return 0.5
        
        # Concentration entropy
        concentrations = [s.get('initial_concentration', 0) for s in context_window]
        if concentrations and max(concentrations) > 0:
            # Shannon entropy of concentration distribution
            probs = np.array(concentrations) / sum(concentrations)
            probs = probs[probs > 0]  # Remove zeros
            concentration_entropy = -np.sum(probs * np.log2(probs)) if len(probs) > 1 else 0
        else:
            concentration_entropy = 0
        
        # Compartment diversity entropy
        compartments = [s.get('compartment', '') for s in context_window]
        unique_compartments = len(set(compartments))
        compartment_entropy = np.log2(unique_compartments) if unique_compartments > 1 else 0
        
        # Network connectivity entropy
        connectivity_entropy = np.log2(network_connectivity + 1) / 10.0  # Normalized
        
        # Boundary condition disorder
        boundary_species = sum(1 for s in context_window if s.get('boundary_condition', False))
        boundary_entropy = boundary_species / len(context_window) if context_window else 0
        
        total_entropy = (concentration_entropy + compartment_entropy + 
                        connectivity_entropy + boundary_entropy) / 4.0
        
        # Normalize to [0, 2] range
        return max(0, min(2, total_entropy))
    
    def get_molecular_base_coordinate(self, species_data: Dict) -> np.array:
        """Get base coordinate from molecular type recognition"""
        species_id = species_data.get('id', '').upper()
        species_name = species_data.get('name', '').upper()
        
        # Try exact matches first
        for pattern, coord in self.extended_mapping.items():
            if pattern in species_id or pattern in species_name:
                return coord.copy()
        
        # Try base nucleotide mapping
        for nucleotide, coord in self.base_mapping.items():
            if nucleotide in species_id[:3] or nucleotide in species_name[:3]:
                return coord.copy()
        
        # Try pattern matching for common molecular types
        if any(pattern in species_id for pattern in ['ATP', 'GTP', 'CTP', 'UTP']):
            return np.array([1.2, 0.3])  # Nucleotide triphosphates
        elif any(pattern in species_id for pattern in ['ADP', 'GDP', 'CDP', 'UDP']):
            return np.array([0.8, 0.2])  # Nucleotide diphosphates
        elif any(pattern in species_id for pattern in ['AMP', 'GMP', 'CMP', 'UMP']):
            return np.array([0.4, 0.1])  # Nucleotide monophosphates
        elif 'COA' in species_id or 'COENZYME' in species_name:
            return np.array([0.6, 0.8])  # Coenzymes
        elif any(pattern in species_id for pattern in ['NADH', 'NADPH', 'FADH']):
            return np.array([0, 1.2])    # Reduced cofactors
        elif any(pattern in species_id for pattern in ['NAD', 'NADP', 'FAD']):
            return np.array([0, 0.9])    # Oxidized cofactors
        
        # Default coordinate based on molecular properties
        concentration = species_data.get('initial_concentration', 1.0)
        compartment_hash = hash(species_data.get('compartment', '')) % 100
        
        default_coord = np.array([
            (concentration % 10) / 10.0 - 0.5,
            (compartment_hash % 10) / 10.0 - 0.5
        ])
        
        return default_coord
    
    def transform_to_s_coordinates(self, species_df: pd.DataFrame, 
                                 reactions_data: Dict = None,
                                 network_connectivity: Dict = None) -> Dict:
        """Transform species data to S-entropy coordinates with full context"""
        s_coordinates = {}
        
        # Convert to list of dictionaries for easier processing
        species_list = species_df.to_dict('records') if isinstance(species_df, pd.DataFrame) else list(species_df.values())
        
        for idx, species_data in enumerate(species_list):
            species_id = species_data.get('id', f'species_{idx}')
            
            # Get context window (neighboring species)
            start_idx = max(0, idx - 2)
            end_idx = min(len(species_list), idx + 3)
            context_window = species_list[start_idx:end_idx]
            
            # Get reaction context
            reaction_context = []
            if reactions_data:
                for reaction_id, reaction_data in reactions_data.items():
                    # Check if this species is involved in reaction
                    involved = False
                    for reactant in reaction_data.get('reactants', []):
                        if reactant['species'] == species_id:
                            involved = True
                            break
                    if not involved:
                        for product in reaction_data.get('products', []):
                            if product['species'] == species_id:
                                involved = True
                                break
                    if not involved:
                        for modifier in reaction_data.get('modifiers', []):
                            if modifier['species'] == species_id:
                                involved = True
                                break
                    
                    if involved:
                        reaction_context.append(reaction_data)
            
            # Get network connectivity
            connectivity = network_connectivity.get(species_id, 0) if network_connectivity else 0
            
            # Calculate S-entropy coordinates
            w_k = self.calculate_knowledge_weight(species_data)
            w_t = self.calculate_time_weight(species_data, idx, reaction_context)
            w_e = self.calculate_entropy_weight(species_data, context_window, connectivity)
            
            # Get base coordinate
            base_coord = self.get_molecular_base_coordinate(species_data)
            
            # Full S-entropy coordinate (3D)
            s_coord = np.array([
                w_k * base_coord[0],  # S_knowledge
                w_t * base_coord[1],  # S_time  
                w_e * np.linalg.norm(base_coord)  # S_entropy
            ])
            
            s_coordinates[species_id] = s_coord
            
        self.coordinate_cache = s_coordinates
        return s_coordinates
    
    def calculate_coordinate_distances(self, s_coordinates: Dict = None) -> Dict:
        """Calculate all pairwise distances in S-entropy space"""
        coords = s_coordinates or self.coordinate_cache
        distances = {}
        
        species_list = list(coords.keys())
        
        for i, species1 in enumerate(species_list):
            for species2 in species_list[i+1:]:
                coord1 = coords[species1]
                coord2 = coords[species2]
                
                distance = np.linalg.norm(coord1 - coord2)
                distances[f"{species1}-{species2}"] = distance
        
        return distances
    
    def find_coordinate_neighbors(self, target_species: str, 
                                s_coordinates: Dict = None, 
                                max_neighbors: int = 5) -> List[Tuple[str, float]]:
        """Find nearest neighbors in S-entropy space"""
        coords = s_coordinates or self.coordinate_cache
        
        if target_species not in coords:
            return []
        
        target_coord = coords[target_species]
        neighbors = []
        
        for species_id, coord in coords.items():
            if species_id != target_species:
                distance = np.linalg.norm(target_coord - coord)
                neighbors.append((species_id, distance))
        
        # Sort by distance and return top neighbors
        neighbors.sort(key=lambda x: x[1])
        return neighbors[:max_neighbors]
    
    def analyze_coordinate_distribution(self, s_coordinates: Dict = None) -> Dict:
        """Analyze the distribution of species in S-entropy space"""
        coords = s_coordinates or self.coordinate_cache
        
        if not coords:
            return {}
        
        # Convert to array for analysis
        coord_array = np.array(list(coords.values()))
        
        analysis = {
            'num_species': len(coords),
            'coordinate_stats': {
                'mean': np.mean(coord_array, axis=0),
                'std': np.std(coord_array, axis=0),
                'min': np.min(coord_array, axis=0),
                'max': np.max(coord_array, axis=0)
            },
            'coordinate_ranges': {
                'knowledge_range': np.max(coord_array[:, 0]) - np.min(coord_array[:, 0]),
                'time_range': np.max(coord_array[:, 1]) - np.min(coord_array[:, 1]),
                'entropy_range': np.max(coord_array[:, 2]) - np.min(coord_array[:, 2])
            }
        }
        
        # Find extreme points
        analysis['extreme_points'] = {
            'max_knowledge': max(coords.items(), key=lambda x: x[1][0]),
            'min_knowledge': min(coords.items(), key=lambda x: x[1][0]),
            'max_time': max(coords.items(), key=lambda x: x[1][1]),
            'min_time': min(coords.items(), key=lambda x: x[1][1]),
            'max_entropy': max(coords.items(), key=lambda x: x[1][2]),
            'min_entropy': min(coords.items(), key=lambda x: x[1][2])
        }
        
        return analysis
    
    def create_molecular_navigation_map(self, s_coordinates: Dict = None) -> Dict:
        """Create navigation map for molecular coordinate space"""
        coords = s_coordinates or self.coordinate_cache
        
        navigation_map = {
            'coordinates': coords,
            'distances': self.calculate_coordinate_distances(coords),
            'distribution_analysis': self.analyze_coordinate_distribution(coords),
            'navigation_graph': self.build_navigation_graph(coords)
        }
        
        return navigation_map
    
    def build_navigation_graph(self, s_coordinates: Dict, 
                             connection_threshold: float = 1.0) -> Dict:
        """Build navigation graph connecting nearby species in S-entropy space"""
        import networkx as nx
        
        G = nx.Graph()
        
        # Add nodes
        for species_id, coord in s_coordinates.items():
            G.add_node(species_id, coordinate=coord)
        
        # Add edges between nearby species
        species_list = list(s_coordinates.keys())
        
        for i, species1 in enumerate(species_list):
            for species2 in species_list[i+1:]:
                coord1 = s_coordinates[species1]
                coord2 = s_coordinates[species2]
                
                distance = np.linalg.norm(coord1 - coord2)
                
                if distance <= connection_threshold:
                    G.add_edge(species1, species2, distance=distance)
        
        # Calculate graph properties
        graph_properties = {
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges(),
            'density': nx.density(G),
            'is_connected': nx.is_connected(G),
            'num_components': nx.number_connected_components(G),
            'avg_clustering': nx.average_clustering(G)
        }
        
        return {
            'navigation_graph': G,
            'properties': graph_properties
        }

# Main function to create S-entropy molecular language system
def create_molecular_language_system(sbml_components: Dict, 
                                   molecular_network: Dict = None) -> Dict:
    """
    Create complete molecular language system with S-entropy coordinates
    """
    print("Creating molecular language system...")
    
    # Initialize coordinate mapper
    mapper = SEntropyCoordinateMapper()
    
    # Prepare species data
    species_data = sbml_components['species']
    reactions_data = sbml_components.get('reactions', {})
    
    # Get network connectivity if available
    network_connectivity = {}
    if molecular_network and 'species_graph' in molecular_network:
        species_graph = molecular_network['species_graph']
        network_connectivity = {node: species_graph.degree(node) 
                              for node in species_graph.nodes()}
    
    # Transform to S-entropy coordinates
    s_coordinates = mapper.transform_to_s_coordinates(
        species_data, reactions_data, network_connectivity
    )
    
    # Create navigation map
    navigation_map = mapper.create_molecular_navigation_map(s_coordinates)
    
    # Analyze coordinate distribution
    distribution_analysis = mapper.analyze_coordinate_distribution(s_coordinates)
    
    molecular_language_system = {
        'mapper': mapper,
        's_coordinates': s_coordinates,
        'navigation_map': navigation_map,
        'distribution_analysis': distribution_analysis,
        'summary': {
            'species_mapped': len(s_coordinates),
            'coordinate_dimensionality': 3,
            'average_coordinate_magnitude': np.mean([np.linalg.norm(coord) 
                                                   for coord in s_coordinates.values()]),
            'navigation_graph_connectivity': navigation_map['navigation_graph']['properties']['is_connected']
        }
    }
    
    print(f"Molecular language system complete:")
    print(f"  Species mapped: {len(s_coordinates)}")
    print(f"  Navigation graph edges: {navigation_map['navigation_graph']['properties']['num_edges']}")
    print(f"  Graph connectivity: {navigation_map['navigation_graph']['properties']['is_connected']}")
    
    return molecular_language_system

# Usage example
if __name__ == "__main__":
    print("Molecular Language (S-Entropy) module ready for use")
    print("Use create_molecular_language_system(sbml_components) to create coordinate system")