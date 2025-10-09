# Extract pathway structure from SBML components
import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Set, Any
from collections import defaultdict, deque

def extract_pathway_structure(sbml_components: Dict) -> Dict:
    """
    Extract pathway structure and topology from SBML components
    Identifies linear pathways, branching points, cycles, and pathway modules
    """
    print("Extracting pathway topology...")
    
    # Create directed reaction network
    reaction_network = create_directed_reaction_network(sbml_components)
    
    # Identify pathway components
    linear_pathways = identify_linear_pathways(reaction_network, sbml_components)
    branching_points = identify_branching_points(reaction_network, sbml_components)
    pathway_cycles = identify_pathway_cycles(reaction_network, sbml_components)
    pathway_modules = identify_pathway_modules(reaction_network, sbml_components)
    
    # Analyze pathway connectivity
    connectivity_analysis = analyze_pathway_connectivity(reaction_network, sbml_components)
    
    # Calculate pathway metrics
    pathway_metrics = calculate_pathway_metrics(reaction_network, sbml_components)
    
    pathway_topology = {
        'reaction_network': reaction_network,
        'linear_pathways': linear_pathways,
        'branching_points': branching_points,
        'pathway_cycles': pathway_cycles,
        'pathway_modules': pathway_modules,
        'connectivity_analysis': connectivity_analysis,
        'pathway_metrics': pathway_metrics,
        'summary': {
            'num_linear_pathways': len(linear_pathways),
            'num_branching_points': len(branching_points),
            'num_cycles': len(pathway_cycles),
            'num_modules': len(pathway_modules),
            'network_complexity': pathway_metrics.get('complexity_score', 0.0)
        }
    }
    
    print(f"Pathway topology extraction complete:")
    print(f"  Linear pathways: {len(linear_pathways)}")
    print(f"  Branching points: {len(branching_points)}")
    print(f"  Cycles: {len(pathway_cycles)}")
    print(f"  Modules: {len(pathway_modules)}")
    
    return pathway_topology

def create_directed_reaction_network(sbml_components: Dict) -> nx.DiGraph:
    """Create directed network showing flow from reactants to products"""
    G = nx.DiGraph()
    
    # Add species nodes
    for species_id, species_data in sbml_components['species'].items():
        G.add_node(species_id,
                  node_type='species',
                  name=species_data['name'],
                  compartment=species_data['compartment'],
                  initial_concentration=species_data['initial_concentration'])
    
    # Add directed edges based on reactions
    for reaction_id, reaction_data in sbml_components['reactions'].items():
        reactants = [r['species'] for r in reaction_data['reactants']]
        products = [p['species'] for p in reaction_data['products']]
        
        # Create edges from each reactant to each product
        for reactant in reactants:
            for product in products:
                if G.has_edge(reactant, product):
                    # Multiple reactions between same species
                    G[reactant][product]['reactions'].append(reaction_id)
                    G[reactant][product]['weight'] += 1
                else:
                    G.add_edge(reactant, product,
                              reactions=[reaction_id],
                              weight=1,
                              reaction_data=reaction_data)
        
        # Handle reversible reactions
        if reaction_data.get('reversible', False):
            for product in products:
                for reactant in reactants:
                    if G.has_edge(product, reactant):
                        G[product][reactant]['reactions'].append(f"{reaction_id}_reverse")
                        G[product][reactant]['weight'] += 0.5  # Lower weight for reverse
                    else:
                        G.add_edge(product, reactant,
                                  reactions=[f"{reaction_id}_reverse"],
                                  weight=0.5,
                                  reaction_data=reaction_data)
    
    return G

def identify_linear_pathways(reaction_network: nx.DiGraph, sbml_components: Dict) -> List[Dict]:
    """Identify linear pathway segments"""
    linear_pathways = []
    visited = set()
    
    # Find nodes with exactly one predecessor and one successor
    for node in reaction_network.nodes():
        if node in visited:
            continue
            
        in_degree = reaction_network.in_degree(node)
        out_degree = reaction_network.out_degree(node)
        
        # Start of potential linear pathway (source or low in-degree)
        if in_degree <= 1 and out_degree == 1:
            pathway = trace_linear_pathway(reaction_network, node, visited)
            if len(pathway) >= 3:  # At least 3 nodes to be considered a pathway
                pathway_info = {
                    'pathway': pathway,
                    'length': len(pathway),
                    'start_node': pathway[0],
                    'end_node': pathway[-1],
                    'reactions': get_pathway_reactions(reaction_network, pathway),
                    'compartments': get_pathway_compartments(sbml_components, pathway)
                }
                linear_pathways.append(pathway_info)
    
    return linear_pathways

def trace_linear_pathway(reaction_network: nx.DiGraph, start_node: str, visited: set) -> List[str]:
    """Trace a linear pathway from a starting node"""
    pathway = [start_node]
    visited.add(start_node)
    current_node = start_node
    
    while True:
        successors = list(reaction_network.successors(current_node))
        
        # Stop if no successors or multiple successors (branching)
        if len(successors) != 1:
            break
            
        next_node = successors[0]
        
        # Stop if next node has multiple predecessors (convergence)
        if reaction_network.in_degree(next_node) != 1:
            break
            
        # Stop if we've seen this node (cycle)
        if next_node in visited:
            break
            
        pathway.append(next_node)
        visited.add(next_node)
        current_node = next_node
    
    return pathway

def identify_branching_points(reaction_network: nx.DiGraph, sbml_components: Dict) -> List[Dict]:
    """Identify nodes where pathways branch (high out-degree)"""
    branching_points = []
    
    for node in reaction_network.nodes():
        out_degree = reaction_network.out_degree(node)
        
        if out_degree >= 2:  # Node has multiple outputs
            successors = list(reaction_network.successors(node))
            
            branching_info = {
                'node': node,
                'out_degree': out_degree,
                'branches': successors,
                'reactions': [],
                'compartment': sbml_components['species'][node]['compartment']
            }
            
            # Get reactions leading to each branch
            for successor in successors:
                edge_data = reaction_network[node][successor]
                branching_info['reactions'].extend(edge_data['reactions'])
            
            branching_points.append(branching_info)
    
    # Sort by out-degree (most connected first)
    branching_points.sort(key=lambda x: x['out_degree'], reverse=True)
    
    return branching_points

def identify_pathway_cycles(reaction_network: nx.DiGraph, sbml_components: Dict) -> List[Dict]:
    """Identify cycles in the reaction network"""
    cycles = []
    
    try:
        # Find all simple cycles
        simple_cycles = list(nx.simple_cycles(reaction_network))
        
        for cycle in simple_cycles:
            if len(cycle) >= 3:  # Minimum cycle size
                cycle_info = {
                    'cycle': cycle,
                    'length': len(cycle),
                    'reactions': get_pathway_reactions(reaction_network, cycle + [cycle[0]]),
                    'compartments': get_pathway_compartments(sbml_components, cycle),
                    'cycle_type': classify_cycle_type(reaction_network, cycle, sbml_components)
                }
                cycles.append(cycle_info)
        
    except Exception as e:
        print(f"Warning: Could not identify all cycles: {e}")
    
    # Sort by cycle length
    cycles.sort(key=lambda x: x['length'])
    
    return cycles

def classify_cycle_type(reaction_network: nx.DiGraph, cycle: List[str], sbml_components: Dict) -> str:
    """Classify the type of cycle (metabolic, regulatory, etc.)"""
    # Simple classification based on species types and compartments
    compartments = get_pathway_compartments(sbml_components, cycle)
    
    if len(compartments) == 1:
        return "local_cycle"
    elif len(compartments) > 1:
        return "transport_cycle"
    else:
        return "regulatory_cycle"

def identify_pathway_modules(reaction_network: nx.DiGraph, sbml_components: Dict) -> List[Dict]:
    """Identify functional modules using community detection"""
    modules = []
    
    try:
        # Convert to undirected for community detection
        undirected_network = reaction_network.to_undirected()
        
        # Use greedy modularity optimization
        communities = nx.community.greedy_modularity_communities(undirected_network)
        
        for i, community in enumerate(communities):
            if len(community) >= 3:  # Minimum module size
                module_nodes = list(community)
                
                # Calculate module properties
                subgraph = reaction_network.subgraph(module_nodes)
                
                module_info = {
                    'module_id': f"module_{i}",
                    'nodes': module_nodes,
                    'size': len(module_nodes),
                    'internal_edges': subgraph.number_of_edges(),
                    'external_connections': count_external_connections(reaction_network, module_nodes),
                    'compartments': get_pathway_compartments(sbml_components, module_nodes),
                    'density': nx.density(subgraph) if len(module_nodes) > 1 else 0.0
                }
                
                modules.append(module_info)
        
    except Exception as e:
        print(f"Warning: Could not identify modules: {e}")
    
    # Sort by module size
    modules.sort(key=lambda x: x['size'], reverse=True)
    
    return modules

def count_external_connections(reaction_network: nx.DiGraph, module_nodes: List[str]) -> int:
    """Count connections from module to external nodes"""
    external_connections = 0
    module_set = set(module_nodes)
    
    for node in module_nodes:
        for neighbor in reaction_network.neighbors(node):
            if neighbor not in module_set:
                external_connections += 1
    
    return external_connections

def analyze_pathway_connectivity(reaction_network: nx.DiGraph, sbml_components: Dict) -> Dict:
    """Analyze overall pathway connectivity patterns"""
    analysis = {}
    
    # Basic connectivity metrics
    analysis['is_strongly_connected'] = nx.is_strongly_connected(reaction_network)
    analysis['is_weakly_connected'] = nx.is_weakly_connected(reaction_network)
    analysis['num_strongly_connected_components'] = nx.number_strongly_connected_components(reaction_network)
    analysis['num_weakly_connected_components'] = nx.number_weakly_connected_components(reaction_network)
    
    # Identify source and sink nodes
    sources = [node for node in reaction_network.nodes() 
              if reaction_network.in_degree(node) == 0 and reaction_network.out_degree(node) > 0]
    sinks = [node for node in reaction_network.nodes() 
            if reaction_network.out_degree(node) == 0 and reaction_network.in_degree(node) > 0]
    
    analysis['source_nodes'] = sources
    analysis['sink_nodes'] = sinks
    analysis['num_sources'] = len(sources)
    analysis['num_sinks'] = len(sinks)
    
    # Calculate pathway lengths
    if analysis['is_weakly_connected']:
        try:
            # Convert to undirected for path length calculation
            undirected = reaction_network.to_undirected()
            analysis['avg_shortest_path'] = nx.average_shortest_path_length(undirected)
            analysis['diameter'] = nx.diameter(undirected)
        except:
            analysis['avg_shortest_path'] = None
            analysis['diameter'] = None
    
    # Analyze degree distributions
    in_degrees = [reaction_network.in_degree(node) for node in reaction_network.nodes()]
    out_degrees = [reaction_network.out_degree(node) for node in reaction_network.nodes()]
    
    analysis['in_degree_stats'] = {
        'mean': np.mean(in_degrees),
        'std': np.std(in_degrees),
        'max': np.max(in_degrees),
        'min': np.min(in_degrees)
    }
    
    analysis['out_degree_stats'] = {
        'mean': np.mean(out_degrees),
        'std': np.std(out_degrees),
        'max': np.max(out_degrees),
        'min': np.min(out_degrees)
    }
    
    return analysis

def calculate_pathway_metrics(reaction_network: nx.DiGraph, sbml_components: Dict) -> Dict:
    """Calculate various pathway complexity and efficiency metrics"""
    metrics = {}
    
    # Network complexity
    num_nodes = reaction_network.number_of_nodes()
    num_edges = reaction_network.number_of_edges()
    
    metrics['complexity_score'] = num_edges / num_nodes if num_nodes > 0 else 0
    metrics['density'] = nx.density(reaction_network)
    
    # Pathway efficiency (inverse of average path length)
    if nx.is_weakly_connected(reaction_network):
        try:
            undirected = reaction_network.to_undirected()
            avg_path_length = nx.average_shortest_path_length(undirected)
            metrics['efficiency'] = 1.0 / avg_path_length if avg_path_length > 0 else 0
        except:
            metrics['efficiency'] = 0
    else:
        metrics['efficiency'] = 0
    
    # Robustness metrics
    metrics['node_connectivity'] = nx.node_connectivity(reaction_network.to_undirected())
    metrics['edge_connectivity'] = nx.edge_connectivity(reaction_network.to_undirected())
    
    # Centralization measures
    if num_nodes > 1:
        # Degree centralization
        degrees = [reaction_network.degree(node) for node in reaction_network.nodes()]
        max_degree = max(degrees)
        degree_centralization = sum(max_degree - degree for degree in degrees)
        max_possible_centralization = (num_nodes - 1) * (num_nodes - 2)
        
        metrics['degree_centralization'] = (degree_centralization / max_possible_centralization 
                                          if max_possible_centralization > 0 else 0)
    else:
        metrics['degree_centralization'] = 0
    
    return metrics

def get_pathway_reactions(reaction_network: nx.DiGraph, pathway: List[str]) -> List[str]:
    """Get all reactions involved in a pathway"""
    reactions = []
    
    for i in range(len(pathway) - 1):
        node1, node2 = pathway[i], pathway[i + 1]
        if reaction_network.has_edge(node1, node2):
            edge_data = reaction_network[node1][node2]
            reactions.extend(edge_data.get('reactions', []))
    
    return list(set(reactions))  # Remove duplicates

def get_pathway_compartments(sbml_components: Dict, pathway: List[str]) -> List[str]:
    """Get all compartments involved in a pathway"""
    compartments = []
    
    for node in pathway:
        if node in sbml_components['species']:
            compartment = sbml_components['species'][node]['compartment']
            if compartment not in compartments:
                compartments.append(compartment)
    
    return compartments

def find_shortest_paths_between_compartments(reaction_network: nx.DiGraph, 
                                           sbml_components: Dict) -> Dict:
    """Find shortest paths between different compartments"""
    # Group species by compartment
    compartment_species = defaultdict(list)
    for species_id, species_data in sbml_components['species'].items():
        compartment_species[species_data['compartment']].append(species_id)
    
    compartments = list(compartment_species.keys())
    inter_compartment_paths = {}
    
    # Find paths between each pair of compartments
    for i, comp1 in enumerate(compartments):
        for comp2 in compartments[i+1:]:
            shortest_paths = []
            
            # Try to find paths from any species in comp1 to any species in comp2
            for species1 in compartment_species[comp1][:5]:  # Limit for performance
                for species2 in compartment_species[comp2][:5]:
                    try:
                        if nx.has_path(reaction_network, species1, species2):
                            path = nx.shortest_path(reaction_network, species1, species2)
                            shortest_paths.append({
                                'path': path,
                                'length': len(path) - 1,
                                'start_species': species1,
                                'end_species': species2
                            })
                    except:
                        continue
            
            if shortest_paths:
                # Find the shortest among all paths
                shortest = min(shortest_paths, key=lambda x: x['length'])
                inter_compartment_paths[f"{comp1}->{comp2}"] = shortest
    
    return inter_compartment_paths

# Usage example
if __name__ == "__main__":
    print("Pathway topology module ready for use")
    print("Use extract_pathway_structure(sbml_components) to analyze pathway topology")