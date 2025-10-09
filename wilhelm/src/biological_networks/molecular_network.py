# Construct molecular interaction graph from SBML components
import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Any, Optional

def construct_interaction_graph(sbml_components: Dict) -> nx.Graph:
    """
    Construct molecular interaction graph from SBML components
    Creates a bipartite graph with species and reactions as nodes
    """
    G = nx.Graph()
    
    # Add species nodes
    for species_id, species_data in sbml_components['species'].items():
        G.add_node(species_id, 
                  node_type='species',
                  name=species_data['name'],
                  compartment=species_data['compartment'],
                  initial_concentration=species_data['initial_concentration'],
                  boundary_condition=species_data['boundary_condition'])
    
    # Add reaction nodes and edges
    for reaction_id, reaction_data in sbml_components['reactions'].items():
        G.add_node(reaction_id,
                  node_type='reaction', 
                  name=reaction_data['name'],
                  reversible=reaction_data['reversible'],
                  compartment=reaction_data.get('compartment'))
        
        # Add edges from reactants to reaction
        for reactant in reaction_data['reactants']:
            species_id = reactant['species']
            G.add_edge(species_id, reaction_id,
                      edge_type='reactant',
                      stoichiometry=reactant['stoichiometry'])
        
        # Add edges from reaction to products
        for product in reaction_data['products']:
            species_id = product['species']
            G.add_edge(reaction_id, species_id,
                      edge_type='product',
                      stoichiometry=product['stoichiometry'])
        
        # Add modifier edges (bidirectional)
        for modifier in reaction_data['modifiers']:
            species_id = modifier['species']
            G.add_edge(species_id, reaction_id,
                      edge_type='modifier',
                      stoichiometry=1.0)
    
    return G

def create_species_interaction_graph(sbml_components: Dict) -> nx.Graph:
    """
    Create species-species interaction graph (reactions are edges, not nodes)
    This is more suitable for some types of analysis
    """
    G = nx.Graph()
    
    # Add species nodes
    for species_id, species_data in sbml_components['species'].items():
        G.add_node(species_id,
                  name=species_data['name'],
                  compartment=species_data['compartment'], 
                  initial_concentration=species_data['initial_concentration'])
    
    # Connect species through reactions
    for reaction_id, reaction_data in sbml_components['reactions'].items():
        reactant_species = [r['species'] for r in reaction_data['reactants']]
        product_species = [p['species'] for p in reaction_data['products']]
        modifier_species = [m['species'] for m in reaction_data['modifiers']]
        
        # Connect all species involved in the same reaction
        all_species = reactant_species + product_species + modifier_species
        
        for i, species1 in enumerate(all_species):
            for species2 in all_species[i+1:]:
                if G.has_edge(species1, species2):
                    # Multiple reactions connect these species - increase weight
                    G[species1][species2]['weight'] += 1
                    G[species1][species2]['reactions'].append(reaction_id)
                else:
                    G.add_edge(species1, species2,
                              weight=1,
                              reactions=[reaction_id])
    
    return G

def analyze_network_properties(molecular_graph: nx.Graph) -> Dict:
    """Analyze topological properties of the molecular network"""
    analysis = {}
    
    # Basic network properties
    analysis['num_nodes'] = molecular_graph.number_of_nodes()
    analysis['num_edges'] = molecular_graph.number_of_edges()
    analysis['density'] = nx.density(molecular_graph)
    
    # Separate species and reaction nodes
    species_nodes = [n for n, d in molecular_graph.nodes(data=True) 
                    if d.get('node_type') == 'species']
    reaction_nodes = [n for n, d in molecular_graph.nodes(data=True) 
                     if d.get('node_type') == 'reaction']
    
    analysis['num_species'] = len(species_nodes)
    analysis['num_reactions'] = len(reaction_nodes)
    
    # Degree analysis
    degrees = dict(molecular_graph.degree())
    analysis['avg_degree'] = np.mean(list(degrees.values()))
    analysis['max_degree'] = max(degrees.values()) if degrees else 0
    analysis['min_degree'] = min(degrees.values()) if degrees else 0
    
    # Species degree analysis
    species_degrees = {node: degrees[node] for node in species_nodes}
    if species_degrees:
        analysis['avg_species_degree'] = np.mean(list(species_degrees.values()))
        analysis['max_species_degree'] = max(species_degrees.values())
        analysis['hub_species'] = [node for node, degree in species_degrees.items() 
                                  if degree == analysis['max_species_degree']]
    
    # Connectivity analysis
    if nx.is_connected(molecular_graph):
        analysis['is_connected'] = True
        analysis['diameter'] = nx.diameter(molecular_graph)
        analysis['avg_shortest_path'] = nx.average_shortest_path_length(molecular_graph)
    else:
        analysis['is_connected'] = False
        analysis['num_components'] = nx.number_connected_components(molecular_graph)
        analysis['largest_component_size'] = len(max(nx.connected_components(molecular_graph), key=len))
    
    # Centrality measures (for species only)
    if species_nodes:
        subgraph = molecular_graph.subgraph(species_nodes)
        if len(subgraph.nodes()) > 0 and len(subgraph.edges()) > 0:
            betweenness = nx.betweenness_centrality(subgraph)
            closeness = nx.closeness_centrality(subgraph)
            eigenvector = nx.eigenvector_centrality(subgraph, max_iter=1000)
            
            analysis['top_betweenness'] = sorted(betweenness.items(), 
                                               key=lambda x: x[1], reverse=True)[:5]
            analysis['top_closeness'] = sorted(closeness.items(), 
                                             key=lambda x: x[1], reverse=True)[:5]
            analysis['top_eigenvector'] = sorted(eigenvector.items(), 
                                               key=lambda x: x[1], reverse=True)[:5]
    
    return analysis

def identify_network_motifs(molecular_graph: nx.Graph) -> Dict:
    """Identify common network motifs in the molecular interaction graph"""
    motifs = {
        'triangles': 0,
        'squares': 0,
        'feed_forward_loops': [],
        'feedback_loops': []
    }
    
    # Count triangles (3-cycles)
    if not molecular_graph.is_directed():
        motifs['triangles'] = sum(1 for _ in nx.enumerate_all_cliques(molecular_graph) 
                                 if len(list(_)) == 3)
    
    # Identify feedback loops (simple cycles)
    try:
        simple_cycles = list(nx.simple_cycles(molecular_graph.to_directed()))
        motifs['feedback_loops'] = simple_cycles[:10]  # Limit to first 10
    except:
        motifs['feedback_loops'] = []
    
    # Identify feed-forward loops (more complex pattern)
    # This is a simplified version - could be more sophisticated
    species_nodes = [n for n, d in molecular_graph.nodes(data=True) 
                    if d.get('node_type') == 'species']
    
    feed_forward_patterns = []
    for node in species_nodes[:20]:  # Limit search for performance
        neighbors = list(molecular_graph.neighbors(node))
        for neighbor1 in neighbors:
            for neighbor2 in neighbors:
                if neighbor1 != neighbor2:
                    if molecular_graph.has_edge(neighbor1, neighbor2):
                        feed_forward_patterns.append((node, neighbor1, neighbor2))
    
    motifs['feed_forward_loops'] = feed_forward_patterns[:10]
    
    return motifs

def calculate_network_resilience(molecular_graph: nx.Graph) -> Dict:
    """Calculate network resilience metrics"""
    resilience = {}
    
    # Node connectivity
    resilience['node_connectivity'] = nx.node_connectivity(molecular_graph)
    resilience['edge_connectivity'] = nx.edge_connectivity(molecular_graph)
    
    # Robustness to random node removal
    original_nodes = molecular_graph.number_of_nodes()
    nodes_to_remove = min(10, original_nodes // 10)  # Remove 10% or 10 nodes max
    
    if nodes_to_remove > 0:
        temp_graph = molecular_graph.copy()
        nodes_removed = 0
        
        while nodes_removed < nodes_to_remove and temp_graph.number_of_nodes() > 1:
            # Remove random node
            node_to_remove = np.random.choice(list(temp_graph.nodes()))
            temp_graph.remove_node(node_to_remove)
            nodes_removed += 1
        
        resilience['robustness_random'] = {
            'nodes_removed': nodes_removed,
            'remaining_nodes': temp_graph.number_of_nodes(),
            'remaining_connectivity': nx.is_connected(temp_graph) if temp_graph.number_of_nodes() > 0 else False
        }
    
    # Critical nodes (high degree nodes whose removal fragments network)
    critical_nodes = []
    species_nodes = [n for n, d in molecular_graph.nodes(data=True) 
                    if d.get('node_type') == 'species']
    
    for node in species_nodes[:10]:  # Check top nodes by degree
        temp_graph = molecular_graph.copy()
        temp_graph.remove_node(node)
        
        if not nx.is_connected(temp_graph):
            critical_nodes.append(node)
    
    resilience['critical_nodes'] = critical_nodes
    
    return resilience

def extract_compartment_networks(sbml_components: Dict) -> Dict[str, nx.Graph]:
    """Extract separate networks for each cellular compartment"""
    compartment_networks = {}
    
    # Group species by compartment
    compartment_species = {}
    for species_id, species_data in sbml_components['species'].items():
        compartment = species_data['compartment']
        if compartment not in compartment_species:
            compartment_species[compartment] = []
        compartment_species[compartment].append(species_id)
    
    # Create network for each compartment
    for compartment, species_list in compartment_species.items():
        G = nx.Graph()
        
        # Add species nodes for this compartment
        for species_id in species_list:
            species_data = sbml_components['species'][species_id]
            G.add_node(species_id,
                      name=species_data['name'],
                      initial_concentration=species_data['initial_concentration'])
        
        # Add reactions that involve species in this compartment
        for reaction_id, reaction_data in sbml_components['reactions'].items():
            reaction_species = set()
            
            # Collect all species in reaction
            for reactant in reaction_data['reactants']:
                reaction_species.add(reactant['species'])
            for product in reaction_data['products']:
                reaction_species.add(product['species'])
            for modifier in reaction_data['modifiers']:
                reaction_species.add(modifier['species'])
            
            # If reaction involves species in this compartment
            compartment_reaction_species = reaction_species.intersection(set(species_list))
            if len(compartment_reaction_species) >= 2:
                # Connect species through this reaction
                species_in_reaction = list(compartment_reaction_species)
                for i, species1 in enumerate(species_in_reaction):
                    for species2 in species_in_reaction[i+1:]:
                        if G.has_edge(species1, species2):
                            G[species1][species2]['weight'] += 1
                            G[species1][species2]['reactions'].append(reaction_id)
                        else:
                            G.add_edge(species1, species2,
                                      weight=1,
                                      reactions=[reaction_id])
        
        compartment_networks[compartment] = G
    
    return compartment_networks

# Main function that creates the molecular network
def create_molecular_network(sbml_components: Dict) -> Dict:
    """
    Main function to create comprehensive molecular network analysis
    Returns dictionary with all network representations and analyses
    """
    print("Constructing molecular interaction networks...")
    
    # Create different network representations
    bipartite_graph = construct_interaction_graph(sbml_components)
    species_graph = create_species_interaction_graph(sbml_components)
    compartment_networks = extract_compartment_networks(sbml_components)
    
    # Analyze network properties
    bipartite_analysis = analyze_network_properties(bipartite_graph)
    species_analysis = analyze_network_properties(species_graph)
    
    # Identify network motifs
    motifs = identify_network_motifs(bipartite_graph)
    
    # Calculate resilience
    resilience = calculate_network_resilience(species_graph)
    
    molecular_network = {
        'bipartite_graph': bipartite_graph,
        'species_graph': species_graph,
        'compartment_networks': compartment_networks,
        'bipartite_analysis': bipartite_analysis,
        'species_analysis': species_analysis,
        'network_motifs': motifs,
        'network_resilience': resilience,
        'summary': {
            'total_species': len(sbml_components['species']),
            'total_reactions': len(sbml_components['reactions']),
            'total_compartments': len(compartment_networks),
            'is_connected': species_analysis.get('is_connected', False),
            'network_density': species_analysis.get('density', 0.0)
        }
    }
    
    print(f"Molecular network construction complete:")
    print(f"  Species nodes: {len(sbml_components['species'])}")
    print(f"  Reaction nodes: {len(sbml_components['reactions'])}")  
    print(f"  Compartments: {len(compartment_networks)}")
    print(f"  Network density: {species_analysis.get('density', 0.0):.3f}")
    
    return molecular_network

# Usage example
if __name__ == "__main__":
    print("Molecular network module ready for use")
    print("Use create_molecular_network(sbml_components) to create network")