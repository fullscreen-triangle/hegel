# Build regulatory graph from SBML components
import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Set, Any
import re

def build_regulatory_graph(sbml_components: Dict) -> Dict:
    """
    Build regulatory network from SBML components
    Identifies regulatory interactions, feedback loops, and control mechanisms
    """
    print("Building regulatory network...")
    
    # Create regulatory network
    regulatory_network = create_regulatory_network(sbml_components)
    
    # Identify regulatory patterns
    feedback_loops = identify_feedback_loops(regulatory_network)
    feed_forward_loops = identify_feed_forward_loops(regulatory_network)
    regulatory_hubs = identify_regulatory_hubs(regulatory_network)
    
    # Analyze regulatory control
    control_analysis = analyze_regulatory_control(regulatory_network, sbml_components)
    
    # Calculate regulatory metrics
    regulatory_metrics = calculate_regulatory_metrics(regulatory_network)
    
    regulatory_networks = {
        'regulatory_network': regulatory_network,
        'feedback_loops': feedback_loops,
        'feed_forward_loops': feed_forward_loops, 
        'regulatory_hubs': regulatory_hubs,
        'control_analysis': control_analysis,
        'regulatory_metrics': regulatory_metrics,
        'summary': {
            'num_regulatory_interactions': regulatory_network.number_of_edges(),
            'num_feedback_loops': len(feedback_loops),
            'num_feed_forward_loops': len(feed_forward_loops),
            'num_regulatory_hubs': len(regulatory_hubs),
            'network_density': nx.density(regulatory_network)
        }
    }
    
    print(f"Regulatory network construction complete:")
    print(f"  Regulatory interactions: {regulatory_network.number_of_edges()}")
    print(f"  Feedback loops: {len(feedback_loops)}")
    print(f"  Feed-forward loops: {len(feed_forward_loops)}")
    print(f"  Regulatory hubs: {len(regulatory_hubs)}")
    
    return regulatory_networks

def create_regulatory_network(sbml_components: Dict) -> nx.DiGraph:
    """Create directed regulatory network from SBML components"""
    G = nx.DiGraph()
    
    # Add species nodes
    for species_id, species_data in sbml_components['species'].items():
        G.add_node(species_id,
                  node_type='species',
                  name=species_data['name'],
                  compartment=species_data['compartment'])
    
    # Identify regulatory interactions from reactions
    regulatory_interactions = extract_regulatory_interactions(sbml_components)
    
    # Add regulatory edges
    for interaction in regulatory_interactions:
        regulator = interaction['regulator']
        target = interaction['target']
        regulation_type = interaction['type']
        
        G.add_edge(regulator, target,
                  regulation_type=regulation_type,
                  reaction_id=interaction['reaction_id'],
                  mechanism=interaction['mechanism'],
                  strength=interaction.get('strength', 1.0))
    
    # Add regulatory rules as edges
    regulatory_rules = extract_regulatory_rules(sbml_components)
    for rule in regulatory_rules:
        if rule['regulator'] and rule['target']:
            G.add_edge(rule['regulator'], rule['target'],
                      regulation_type=rule['type'],
                      rule_type=rule['rule_type'],
                      formula=rule['formula'])
    
    return G

def extract_regulatory_interactions(sbml_components: Dict) -> List[Dict]:
    """Extract regulatory interactions from reaction modifiers and kinetics"""
    interactions = []
    
    for reaction_id, reaction_data in sbml_components['reactions'].items():
        # Modifiers are potential regulators
        for modifier in reaction_data['modifiers']:
            regulator = modifier['species']
            
            # Targets are the products of the reaction
            for product in reaction_data['products']:
                target = product['species']
                
                # Determine regulation type from kinetic law if available
                regulation_type = determine_regulation_type(
                    reaction_data.get('kinetic_law'), regulator
                )
                
                interaction = {
                    'regulator': regulator,
                    'target': target,
                    'type': regulation_type,
                    'reaction_id': reaction_id,
                    'mechanism': 'modifier',
                    'strength': 1.0
                }
                interactions.append(interaction)
        
        # Also check for regulatory patterns in kinetic laws
        kinetic_interactions = extract_kinetic_regulatory_patterns(reaction_data, reaction_id)
        interactions.extend(kinetic_interactions)
    
    return interactions

def determine_regulation_type(kinetic_law: Dict, regulator: str) -> str:
    """Determine if regulation is activation or inhibition from kinetic law"""
    if not kinetic_law or not kinetic_law.get('formula'):
        return 'unknown'
    
    formula = kinetic_law['formula'].lower()
    regulator_lower = regulator.lower()
    
    # Look for inhibition patterns
    inhibition_patterns = [
        f'/{regulator_lower}',  # Division suggests inhibition
        f'(1-{regulator_lower})',  # (1-x) suggests inhibition
        f'inhibition',
        f'competitive'
    ]
    
    for pattern in inhibition_patterns:
        if pattern in formula:
            return 'inhibition'
    
    # Look for activation patterns
    activation_patterns = [
        f'*{regulator_lower}',  # Multiplication suggests activation
        f'{regulator_lower}*',
        f'activation',
        f'catalysis'
    ]
    
    for pattern in activation_patterns:
        if pattern in formula:
            return 'activation'
    
    return 'unknown'

def extract_kinetic_regulatory_patterns(reaction_data: Dict, reaction_id: str) -> List[Dict]:
    """Extract regulatory patterns from kinetic law formulas"""
    interactions = []
    
    if not reaction_data.get('kinetic_law') or not reaction_data['kinetic_law'].get('formula'):
        return interactions
        
    formula = reaction_data['kinetic_law']['formula']
    
    # Simple pattern matching for regulatory interactions
    # This is a simplified approach - could be much more sophisticated
    
    # Look for Hill equation patterns (cooperative regulation)
    hill_pattern = r'(\w+)\^(\d+)'
    hill_matches = re.findall(hill_pattern, formula)
    
    for species, hill_coeff in hill_matches:
        # Check if this species is involved in the reaction
        all_species = []
        for reactant in reaction_data['reactants']:
            all_species.append(reactant['species'])
        for product in reaction_data['products']:
            all_species.append(product['species'])
        for modifier in reaction_data['modifiers']:
            all_species.append(modifier['species'])
        
        if species in all_species:
            for product in reaction_data['products']:
                target = product['species']
                if species != target:
                    interaction = {
                        'regulator': species,
                        'target': target,
                        'type': 'cooperative_activation',
                        'reaction_id': reaction_id,
                        'mechanism': 'hill_kinetics',
                        'strength': float(hill_coeff)
                    }
                    interactions.append(interaction)
    
    return interactions

def extract_regulatory_rules(sbml_components: Dict) -> List[Dict]:
    """Extract regulatory relationships from SBML rules"""
    rules = []
    
    # Process assignment rules
    for rule_id, rule_data in sbml_components['rules']['assignment_rules'].items():
        target = rule_data['variable']
        formula = rule_data.get('formula', '')
        
        # Extract species mentioned in the formula
        regulators = extract_species_from_formula(formula, sbml_components)
        
        for regulator in regulators:
            if regulator != target:
                rule_info = {
                    'regulator': regulator,
                    'target': target,
                    'type': 'assignment',
                    'rule_type': 'assignment_rule',
                    'formula': formula
                }
                rules.append(rule_info)
    
    # Process rate rules
    for rule_id, rule_data in sbml_components['rules']['rate_rules'].items():
        target = rule_data['variable']
        formula = rule_data.get('formula', '')
        
        regulators = extract_species_from_formula(formula, sbml_components)
        
        for regulator in regulators:
            if regulator != target:
                rule_info = {
                    'regulator': regulator,
                    'target': target,
                    'type': 'rate_control',
                    'rule_type': 'rate_rule',
                    'formula': formula
                }
                rules.append(rule_info)
    
    return rules

def extract_species_from_formula(formula: str, sbml_components: Dict) -> List[str]:
    """Extract species IDs mentioned in a mathematical formula"""
    if not formula:
        return []
    
    species_ids = list(sbml_components['species'].keys())
    mentioned_species = []
    
    # Simple approach: check if species ID appears in formula
    for species_id in species_ids:
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(species_id) + r'\b'
        if re.search(pattern, formula):
            mentioned_species.append(species_id)
    
    return mentioned_species

def identify_feedback_loops(regulatory_network: nx.DiGraph) -> List[Dict]:
    """Identify feedback loops in regulatory network"""
    feedback_loops = []
    
    try:
        # Find all simple cycles (feedback loops)
        cycles = list(nx.simple_cycles(regulatory_network))
        
        for cycle in cycles:
            if len(cycle) >= 2:  # At least 2 nodes for meaningful feedback
                # Classify feedback type
                feedback_type = classify_feedback_loop(regulatory_network, cycle)
                
                loop_info = {
                    'loop': cycle,
                    'length': len(cycle),
                    'type': feedback_type,
                    'regulation_types': get_loop_regulation_types(regulatory_network, cycle),
                    'strength': calculate_loop_strength(regulatory_network, cycle)
                }
                feedback_loops.append(loop_info)
        
    except Exception as e:
        print(f"Warning: Could not identify all feedback loops: {e}")
    
    # Sort by loop strength
    feedback_loops.sort(key=lambda x: x['strength'], reverse=True)
    
    return feedback_loops

def classify_feedback_loop(regulatory_network: nx.DiGraph, cycle: List[str]) -> str:
    """Classify feedback loop as positive or negative"""
    inhibition_count = 0
    
    for i in range(len(cycle)):
        current = cycle[i]
        next_node = cycle[(i + 1) % len(cycle)]
        
        if regulatory_network.has_edge(current, next_node):
            reg_type = regulatory_network[current][next_node].get('regulation_type', 'unknown')
            if reg_type == 'inhibition':
                inhibition_count += 1
    
    # Odd number of inhibitions = negative feedback
    # Even number of inhibitions = positive feedback
    if inhibition_count % 2 == 1:
        return 'negative_feedback'
    else:
        return 'positive_feedback'

def get_loop_regulation_types(regulatory_network: nx.DiGraph, cycle: List[str]) -> List[str]:
    """Get regulation types for all edges in a loop"""
    regulation_types = []
    
    for i in range(len(cycle)):
        current = cycle[i]
        next_node = cycle[(i + 1) % len(cycle)]
        
        if regulatory_network.has_edge(current, next_node):
            reg_type = regulatory_network[current][next_node].get('regulation_type', 'unknown')
            regulation_types.append(reg_type)
        else:
            regulation_types.append('unknown')
    
    return regulation_types

def calculate_loop_strength(regulatory_network: nx.DiGraph, cycle: List[str]) -> float:
    """Calculate the strength of a regulatory loop"""
    total_strength = 1.0
    
    for i in range(len(cycle)):
        current = cycle[i]
        next_node = cycle[(i + 1) % len(cycle)]
        
        if regulatory_network.has_edge(current, next_node):
            strength = regulatory_network[current][next_node].get('strength', 1.0)
            total_strength *= strength
    
    return total_strength

def identify_feed_forward_loops(regulatory_network: nx.DiGraph) -> List[Dict]:
    """Identify feed-forward loops (3-node motifs with direct and indirect paths)"""
    feed_forward_loops = []
    
    nodes = list(regulatory_network.nodes())
    
    # Check all combinations of 3 nodes
    for i, node_a in enumerate(nodes):
        for j, node_b in enumerate(nodes[i+1:], i+1):
            for k, node_c in enumerate(nodes[j+1:], j+1):
                # Check for feed-forward loop pattern: A->B, A->C, B->C
                if (regulatory_network.has_edge(node_a, node_b) and
                    regulatory_network.has_edge(node_a, node_c) and
                    regulatory_network.has_edge(node_b, node_c)):
                    
                    # Get regulation types
                    ab_type = regulatory_network[node_a][node_b].get('regulation_type', 'unknown')
                    ac_type = regulatory_network[node_a][node_c].get('regulation_type', 'unknown')
                    bc_type = regulatory_network[node_b][node_c].get('regulation_type', 'unknown')
                    
                    # Classify feed-forward loop type
                    ffl_type = classify_feed_forward_loop(ab_type, ac_type, bc_type)
                    
                    loop_info = {
                        'nodes': [node_a, node_b, node_c],
                        'regulator': node_a,
                        'intermediate': node_b,
                        'target': node_c,
                        'type': ffl_type,
                        'regulation_types': {
                            'regulator_to_intermediate': ab_type,
                            'regulator_to_target': ac_type,
                            'intermediate_to_target': bc_type
                        }
                    }
                    feed_forward_loops.append(loop_info)
    
    return feed_forward_loops

def classify_feed_forward_loop(ab_type: str, ac_type: str, bc_type: str) -> str:
    """Classify feed-forward loop based on regulation types"""
    # Count activations and inhibitions
    activations = sum(1 for reg_type in [ab_type, ac_type, bc_type] 
                     if reg_type == 'activation')
    inhibitions = sum(1 for reg_type in [ab_type, ac_type, bc_type] 
                     if reg_type == 'inhibition')
    
    if activations == 3:
        return 'coherent_type1'  # All activations
    elif inhibitions == 1:
        return 'incoherent_type1'  # One inhibition
    elif inhibitions == 2:
        return 'incoherent_type2'  # Two inhibitions
    elif inhibitions == 3:
        return 'coherent_type2'  # All inhibitions
    else:
        return 'mixed_type'

def identify_regulatory_hubs(regulatory_network: nx.DiGraph) -> List[Dict]:
    """Identify regulatory hubs (nodes with high regulatory degree)"""
    hubs = []
    
    # Calculate regulatory degrees
    for node in regulatory_network.nodes():
        in_degree = regulatory_network.in_degree(node)
        out_degree = regulatory_network.out_degree(node)
        total_degree = in_degree + out_degree
        
        # Consider nodes with high degree as hubs
        if total_degree >= 3:  # Threshold for hub classification
            hub_info = {
                'node': node,
                'in_degree': in_degree,
                'out_degree': out_degree,
                'total_degree': total_degree,
                'hub_type': classify_hub_type(in_degree, out_degree),
                'targets': list(regulatory_network.successors(node)),
                'regulators': list(regulatory_network.predecessors(node))
            }
            hubs.append(hub_info)
    
    # Sort by total degree
    hubs.sort(key=lambda x: x['total_degree'], reverse=True)
    
    return hubs

def classify_hub_type(in_degree: int, out_degree: int) -> str:
    """Classify hub type based on in/out degree"""
    if out_degree > in_degree * 2:
        return 'master_regulator'  # High out-degree
    elif in_degree > out_degree * 2:
        return 'integration_hub'  # High in-degree
    else:
        return 'bidirectional_hub'  # Balanced

def analyze_regulatory_control(regulatory_network: nx.DiGraph, sbml_components: Dict) -> Dict:
    """Analyze regulatory control patterns"""
    analysis = {}
    
    # Count regulation types
    regulation_counts = {'activation': 0, 'inhibition': 0, 'unknown': 0}
    
    for _, _, edge_data in regulatory_network.edges(data=True):
        reg_type = edge_data.get('regulation_type', 'unknown')
        regulation_counts[reg_type] = regulation_counts.get(reg_type, 0) + 1
    
    analysis['regulation_type_distribution'] = regulation_counts
    
    # Calculate regulatory balance
    total_regulatory = regulation_counts['activation'] + regulation_counts['inhibition']
    if total_regulatory > 0:
        analysis['activation_ratio'] = regulation_counts['activation'] / total_regulatory
        analysis['inhibition_ratio'] = regulation_counts['inhibition'] / total_regulatory
    else:
        analysis['activation_ratio'] = 0
        analysis['inhibition_ratio'] = 0
    
    # Identify most regulated species
    most_regulated = []
    for node in regulatory_network.nodes():
        in_degree = regulatory_network.in_degree(node)
        if in_degree > 0:
            most_regulated.append((node, in_degree))
    
    most_regulated.sort(key=lambda x: x[1], reverse=True)
    analysis['most_regulated_species'] = most_regulated[:10]
    
    # Identify top regulators
    top_regulators = []
    for node in regulatory_network.nodes():
        out_degree = regulatory_network.out_degree(node)
        if out_degree > 0:
            top_regulators.append((node, out_degree))
    
    top_regulators.sort(key=lambda x: x[1], reverse=True)
    analysis['top_regulators'] = top_regulators[:10]
    
    return analysis

def calculate_regulatory_metrics(regulatory_network: nx.DiGraph) -> Dict:
    """Calculate regulatory network metrics"""
    metrics = {}
    
    # Basic metrics
    metrics['num_nodes'] = regulatory_network.number_of_nodes()
    metrics['num_edges'] = regulatory_network.number_of_edges()
    metrics['density'] = nx.density(regulatory_network)
    
    # Degree metrics
    in_degrees = [regulatory_network.in_degree(node) for node in regulatory_network.nodes()]
    out_degrees = [regulatory_network.out_degree(node) for node in regulatory_network.nodes()]
    
    metrics['avg_in_degree'] = np.mean(in_degrees) if in_degrees else 0
    metrics['avg_out_degree'] = np.mean(out_degrees) if out_degrees else 0
    metrics['max_in_degree'] = max(in_degrees) if in_degrees else 0
    metrics['max_out_degree'] = max(out_degrees) if out_degrees else 0
    
    # Connectivity metrics
    if regulatory_network.number_of_nodes() > 0:
        metrics['is_strongly_connected'] = nx.is_strongly_connected(regulatory_network)
        metrics['is_weakly_connected'] = nx.is_weakly_connected(regulatory_network)
        metrics['num_strongly_connected_components'] = nx.number_strongly_connected_components(regulatory_network)
        
        # Calculate average path length for weakly connected network
        if nx.is_weakly_connected(regulatory_network):
            try:
                undirected = regulatory_network.to_undirected()
                metrics['avg_shortest_path'] = nx.average_shortest_path_length(undirected)
            except:
                metrics['avg_shortest_path'] = None
    
    return metrics

# Usage example
if __name__ == "__main__":
    print("Regulatory networks module ready for use")
    print("Use build_regulatory_graph(sbml_components) to build regulatory network")