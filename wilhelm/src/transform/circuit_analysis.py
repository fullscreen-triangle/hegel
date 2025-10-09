# Circuit Analysis for Biological Systems - Oscillatory Hole Semiconductor Theory
import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Any
import pandas as pd

class BiologicalCircuitAnalyzer:
    """
    Analyze biological systems as oscillatory semiconductor circuits
    Implements the positive hole analogy from computational pharmacology theory
    """
    
    def __init__(self):
        self.circuit_network = None
        self.hole_populations = {}
        self.electron_populations = {}
        self.conductivity_matrix = {}
        self.junction_properties = {}
    
    def create_biological_circuit(self, sbml_components: Dict, 
                                s_coordinates: Dict,
                                regulatory_network: nx.DiGraph) -> nx.DiGraph:
        """Create biological circuit from SBML components and regulatory network"""
        print("Creating biological semiconductor circuit...")
        
        circuit = nx.DiGraph()
        
        # Add species nodes as circuit elements
        for species_id, species_data in sbml_components['species'].items():
            if species_id in s_coordinates:
                # Classify as n-type or p-type based on S-entropy coordinates
                circuit_type = self.classify_circuit_element_type(
                    s_coordinates[species_id], species_data
                )
                
                circuit.add_node(species_id,
                                element_type='species',
                                circuit_type=circuit_type,
                                concentration=species_data.get('initial_concentration', 0),
                                s_coordinate=s_coordinates[species_id],
                                doping_level=self.calculate_doping_level(species_data))
        
        # Add reaction nodes as circuit junctions
        for reaction_id, reaction_data in sbml_components['reactions'].items():
            junction_type = self.classify_junction_type(reaction_data)
            
            circuit.add_node(reaction_id,
                            element_type='junction',
                            junction_type=junction_type,
                            reversible=reaction_data.get('reversible', False))
        
        # Add circuit connections based on reactions
        for reaction_id, reaction_data in sbml_components['reactions'].items():
            reactants = [r['species'] for r in reaction_data['reactants']]
            products = [p['species'] for p in reaction_data['products']]
            
            # Connect reactants to junction (current flow in)
            for reactant in reactants:
                if reactant in circuit:
                    circuit.add_edge(reactant, reaction_id,
                                   connection_type='current_in',
                                   stoichiometry=self.get_stoichiometry(reactant, reaction_data))
            
            # Connect junction to products (current flow out)
            for product in products:
                if product in circuit:
                    circuit.add_edge(reaction_id, product,
                                   connection_type='current_out',
                                   stoichiometry=self.get_stoichiometry(product, reaction_data))
        
        # Add regulatory connections as control signals
        for regulator, target, edge_data in regulatory_network.edges(data=True):
            if regulator in circuit and target in circuit:
                regulation_type = edge_data.get('regulation_type', 'unknown')
                control_type = 'gate_voltage' if regulation_type == 'activation' else 'inhibition_signal'
                
                circuit.add_edge(regulator, target,
                                connection_type='regulatory',
                                control_type=control_type,
                                regulation_strength=edge_data.get('strength', 1.0))
        
        self.circuit_network = circuit
        return circuit
    
    def classify_circuit_element_type(self, s_coordinate: np.array, 
                                    species_data: Dict) -> str:
        """Classify species as n-type or p-type based on S-entropy coordinates"""
        # Use S-entropy coordinate to determine electron/hole dominance
        s_magnitude = np.linalg.norm(s_coordinate)
        s_balance = np.std(s_coordinate) / (np.mean(np.abs(s_coordinate)) + 1e-6)
        
        concentration = species_data.get('initial_concentration', 0)
        boundary_condition = species_data.get('boundary_condition', False)
        
        # N-type: high electron density (high concentration, low entropy)
        if concentration > 1.0 and s_balance < 0.5:
            return 'n_type'
        # P-type: high hole density (low concentration, high entropy)
        elif concentration < 1.0 and s_balance > 0.5:
            return 'p_type'
        # Intrinsic: balanced
        elif boundary_condition:
            return 'intrinsic_boundary'
        else:
            return 'intrinsic'
    
    def classify_junction_type(self, reaction_data: Dict) -> str:
        """Classify reaction as different types of semiconductor junctions"""
        num_reactants = len(reaction_data.get('reactants', []))
        num_products = len(reaction_data.get('products', []))
        is_reversible = reaction_data.get('reversible', False)
        has_modifiers = len(reaction_data.get('modifiers', [])) > 0
        
        if num_reactants == 1 and num_products == 1:
            return 'diode' if not is_reversible else 'bidirectional_diode'
        elif num_reactants >= 2 and num_products == 1:
            return 'and_gate' if not has_modifiers else 'controlled_and_gate'
        elif num_reactants == 1 and num_products >= 2:
            return 'splitter' if not has_modifiers else 'controlled_splitter'
        elif has_modifiers:
            return 'transistor'  # Modifiers act as gate control
        else:
            return 'complex_junction'
    
    def calculate_doping_level(self, species_data: Dict) -> float:
        """Calculate doping level based on species properties"""
        concentration = species_data.get('initial_concentration', 0)
        boundary_condition = species_data.get('boundary_condition', False)
        
        # Base doping from concentration
        base_doping = np.log(concentration + 1)
        
        # Boundary species have higher doping (constant supply)
        boundary_enhancement = 2.0 if boundary_condition else 1.0
        
        return base_doping * boundary_enhancement
    
    def get_stoichiometry(self, species_id: str, reaction_data: Dict) -> float:
        """Get stoichiometry coefficient for species in reaction"""
        # Check reactants
        for reactant in reaction_data.get('reactants', []):
            if reactant['species'] == species_id:
                return reactant.get('stoichiometry', 1.0)
        
        # Check products
        for product in reaction_data.get('products', []):
            if product['species'] == species_id:
                return product.get('stoichiometry', 1.0)
        
        return 1.0
    
    def calculate_hole_populations(self, circuit: nx.DiGraph) -> Dict:
        """Calculate oscillatory hole populations in circuit elements"""
        hole_populations = {}
        
        for node in circuit.nodes():
            node_data = circuit.nodes[node]
            
            if node_data.get('element_type') == 'species':
                circuit_type = node_data.get('circuit_type', 'intrinsic')
                concentration = node_data.get('concentration', 0)
                doping_level = node_data.get('doping_level', 1.0)
                
                if circuit_type == 'p_type':
                    # P-type: high hole concentration
                    hole_population = doping_level * np.exp(-concentration / 10.0)
                elif circuit_type == 'n_type':
                    # N-type: low hole concentration (minority carriers)
                    hole_population = 1.0 / (doping_level * concentration + 1.0)
                else:
                    # Intrinsic: moderate hole concentration
                    hole_population = 1.0 / (concentration + 1.0)
                
                hole_populations[node] = hole_population
        
        self.hole_populations = hole_populations
        return hole_populations
    
    def calculate_electron_populations(self, circuit: nx.DiGraph) -> Dict:
        """Calculate molecular component (electron) populations"""
        electron_populations = {}
        
        for node in circuit.nodes():
            node_data = circuit.nodes[node]
            
            if node_data.get('element_type') == 'species':
                circuit_type = node_data.get('circuit_type', 'intrinsic')
                concentration = node_data.get('concentration', 0)
                doping_level = node_data.get('doping_level', 1.0)
                
                if circuit_type == 'n_type':
                    # N-type: high electron concentration
                    electron_population = doping_level * concentration
                elif circuit_type == 'p_type':
                    # P-type: low electron concentration (minority carriers)
                    electron_population = 1.0 / (doping_level + 1.0)
                else:
                    # Intrinsic: moderate electron concentration
                    electron_population = concentration
                
                electron_populations[node] = electron_population
        
        self.electron_populations = electron_populations
        return electron_populations
    
    def calculate_therapeutic_conductivity(self, circuit: nx.DiGraph,
                                         hole_populations: Dict,
                                         electron_populations: Dict) -> Dict:
        """Calculate therapeutic conductivity: σ = n_m μ_m e + p_h μ_h e"""
        conductivity = {}
        
        # Constants (normalized units)
        elementary_charge = 1.0
        electron_mobility = 1.0  # Base mobility for molecular components
        hole_mobility = 0.8      # Slightly lower mobility for oscillatory holes
        
        for species_id in hole_populations:
            if species_id in electron_populations:
                n_m = electron_populations[species_id]  # Molecular component density
                p_h = hole_populations[species_id]      # Oscillatory hole density
                
                # Therapeutic conductivity equation from theory
                therapeutic_conductivity = (n_m * electron_mobility * elementary_charge + 
                                          p_h * hole_mobility * elementary_charge)
                
                conductivity[species_id] = {
                    'total_conductivity': therapeutic_conductivity,
                    'electron_contribution': n_m * electron_mobility * elementary_charge,
                    'hole_contribution': p_h * hole_mobility * elementary_charge,
                    'electron_density': n_m,
                    'hole_density': p_h
                }
        
        self.conductivity_matrix = conductivity
        return conductivity
    
    def identify_pn_junctions(self, circuit: nx.DiGraph) -> List[Dict]:
        """Identify P-N junctions in biological circuit"""
        pn_junctions = []
        
        for edge in circuit.edges():
            source, target = edge
            source_data = circuit.nodes.get(source, {})
            target_data = circuit.nodes.get(target, {})
            
            source_type = source_data.get('circuit_type', 'unknown')
            target_type = target_data.get('circuit_type', 'unknown')
            
            # Identify P-N junction
            if ((source_type == 'p_type' and target_type == 'n_type') or
                (source_type == 'n_type' and target_type == 'p_type')):
                
                junction_info = {
                    'p_node': source if source_type == 'p_type' else target,
                    'n_node': target if source_type == 'p_type' else source,
                    'junction_voltage': self.calculate_junction_voltage(source, target, circuit),
                    'junction_current': self.calculate_junction_current(source, target, circuit),
                    'junction_type': f"{source_type}_to_{target_type}",
                    'therapeutic_rectification': self.calculate_rectification_factor(source, target)
                }
                
                pn_junctions.append(junction_info)
        
        return pn_junctions
    
    def calculate_junction_voltage(self, node1: str, node2: str, circuit: nx.DiGraph) -> float:
        """Calculate junction voltage between two nodes"""
        if node1 in self.conductivity_matrix and node2 in self.conductivity_matrix:
            conductivity1 = self.conductivity_matrix[node1]['total_conductivity']
            conductivity2 = self.conductivity_matrix[node2]['total_conductivity']
            
            # Voltage difference based on conductivity difference
            voltage = np.log(conductivity1 / (conductivity2 + 1e-6))
            return voltage
        
        return 0.0
    
    def calculate_junction_current(self, node1: str, node2: str, circuit: nx.DiGraph) -> float:
        """Calculate therapeutic current through junction"""
        voltage = self.calculate_junction_voltage(node1, node2, circuit)
        
        # Diode equation: I = I0 * (exp(eV/kT) - 1)
        # Simplified with normalized units
        saturation_current = 0.1
        thermal_voltage = 1.0  # k_B * T / e normalized
        
        current = saturation_current * (np.exp(voltage / thermal_voltage) - 1)
        
        return current
    
    def calculate_rectification_factor(self, node1: str, node2: str) -> float:
        """Calculate therapeutic rectification factor"""
        # Simple rectification based on hole/electron population differences
        if node1 in self.hole_populations and node2 in self.hole_populations:
            hole_diff = abs(self.hole_populations[node1] - self.hole_populations[node2])
            rectification = hole_diff / (hole_diff + 1.0)
            return rectification
        
        return 0.0
    
    def identify_therapeutic_transistors(self, circuit: nx.DiGraph) -> List[Dict]:
        """Identify therapeutic transistor configurations"""
        transistors = []
        
        # Look for 3-node configurations with control signal
        for node in circuit.nodes():
            if circuit.nodes[node].get('element_type') == 'junction':
                # Get connected species
                predecessors = list(circuit.predecessors(node))
                successors = list(circuit.successors(node))
                
                # Look for regulatory connections (gate control)
                control_nodes = []
                for pred in predecessors:
                    edge_data = circuit.edges[pred, node]
                    if edge_data.get('connection_type') == 'regulatory':
                        control_nodes.append(pred)
                
                if len(control_nodes) >= 1 and len(predecessors) >= 2 and len(successors) >= 1:
                    # Potential transistor configuration
                    emitter = [n for n in predecessors if n not in control_nodes][0]
                    collector = successors[0]
                    base = control_nodes[0]
                    
                    transistor_info = {
                        'emitter': emitter,
                        'base': base,
                        'collector': collector,
                        'junction_node': node,
                        'transistor_type': self.classify_transistor_type(emitter, base, collector, circuit),
                        'current_gain': self.calculate_current_gain(emitter, base, collector),
                        'therapeutic_amplification': self.calculate_therapeutic_amplification(
                            emitter, base, collector
                        )
                    }
                    
                    transistors.append(transistor_info)
        
        return transistors
    
    def classify_transistor_type(self, emitter: str, base: str, collector: str, 
                               circuit: nx.DiGraph) -> str:
        """Classify transistor as NPN or PNP"""
        emitter_type = circuit.nodes[emitter].get('circuit_type', 'unknown')
        base_type = circuit.nodes[base].get('circuit_type', 'unknown')
        collector_type = circuit.nodes[collector].get('circuit_type', 'unknown')
        
        if emitter_type == 'n_type' and base_type == 'p_type' and collector_type == 'n_type':
            return 'npn'
        elif emitter_type == 'p_type' and base_type == 'n_type' and collector_type == 'p_type':
            return 'pnp'
        else:
            return 'hybrid'
    
    def calculate_current_gain(self, emitter: str, base: str, collector: str) -> float:
        """Calculate current gain β = I_collector / I_base"""
        if (emitter in self.conductivity_matrix and 
            base in self.conductivity_matrix and 
            collector in self.conductivity_matrix):
            
            emitter_conductivity = self.conductivity_matrix[emitter]['total_conductivity']
            base_conductivity = self.conductivity_matrix[base]['total_conductivity']
            collector_conductivity = self.conductivity_matrix[collector]['total_conductivity']
            
            # Simplified current gain calculation
            current_gain = (collector_conductivity * emitter_conductivity) / (base_conductivity + 1e-6)
            
            return current_gain
        
        return 1.0
    
    def calculate_therapeutic_amplification(self, emitter: str, base: str, collector: str) -> float:
        """Calculate therapeutic signal amplification"""
        current_gain = self.calculate_current_gain(emitter, base, collector)
        
        # Therapeutic amplification includes oscillatory hole effects
        if emitter in self.hole_populations:
            hole_amplification = np.log(self.hole_populations[emitter] + 1)
            therapeutic_amplification = current_gain * hole_amplification
            return therapeutic_amplification
        
        return current_gain
    
    def analyze_circuit_properties(self, circuit: nx.DiGraph) -> Dict:
        """Analyze overall circuit properties"""
        properties = {
            'circuit_elements': {
                'total_nodes': circuit.number_of_nodes(),
                'species_nodes': len([n for n in circuit.nodes() 
                                    if circuit.nodes[n].get('element_type') == 'species']),
                'junction_nodes': len([n for n in circuit.nodes() 
                                     if circuit.nodes[n].get('element_type') == 'junction']),
                'n_type_elements': len([n for n in circuit.nodes() 
                                      if circuit.nodes[n].get('circuit_type') == 'n_type']),
                'p_type_elements': len([n for n in circuit.nodes() 
                                      if circuit.nodes[n].get('circuit_type') == 'p_type']),
                'intrinsic_elements': len([n for n in circuit.nodes() 
                                         if 'intrinsic' in circuit.nodes[n].get('circuit_type', '')])
            },
            'circuit_connectivity': {
                'total_edges': circuit.number_of_edges(),
                'avg_degree': sum(dict(circuit.degree()).values()) / circuit.number_of_nodes(),
                'is_connected': nx.is_weakly_connected(circuit),
                'num_components': nx.number_weakly_connected_components(circuit)
            }
        }
        
        # Calculate average conductivities
        if self.conductivity_matrix:
            all_conductivities = [c['total_conductivity'] for c in self.conductivity_matrix.values()]
            properties['conductivity_stats'] = {
                'avg_conductivity': np.mean(all_conductivities),
                'max_conductivity': np.max(all_conductivities),
                'min_conductivity': np.min(all_conductivities),
                'conductivity_std': np.std(all_conductivities)
            }
        
        return properties

def create_biological_circuit_analysis(sbml_components: Dict,
                                     s_coordinates: Dict,
                                     regulatory_network: nx.DiGraph) -> Dict:
    """
    Create complete biological circuit analysis using oscillatory hole theory
    """
    print("Creating biological circuit analysis...")
    
    # Initialize circuit analyzer
    analyzer = BiologicalCircuitAnalyzer()
    
    # Create biological circuit
    circuit = analyzer.create_biological_circuit(sbml_components, s_coordinates, regulatory_network)
    
    # Calculate carrier populations
    hole_populations = analyzer.calculate_hole_populations(circuit)
    electron_populations = analyzer.calculate_electron_populations(circuit)
    
    # Calculate therapeutic conductivity
    conductivity = analyzer.calculate_therapeutic_conductivity(
        circuit, hole_populations, electron_populations
    )
    
    # Identify circuit elements
    pn_junctions = analyzer.identify_pn_junctions(circuit)
    transistors = analyzer.identify_therapeutic_transistors(circuit)
    
    # Analyze circuit properties
    circuit_properties = analyzer.analyze_circuit_properties(circuit)
    
    biological_circuit_analysis = {
        'analyzer': analyzer,
        'circuit': circuit,
        'hole_populations': hole_populations,
        'electron_populations': electron_populations,
        'therapeutic_conductivity': conductivity,
        'pn_junctions': pn_junctions,
        'therapeutic_transistors': transistors,
        'circuit_properties': circuit_properties,
        'summary': {
            'circuit_elements': circuit_properties['circuit_elements']['total_nodes'],
            'pn_junctions': len(pn_junctions),
            'therapeutic_transistors': len(transistors),
            'avg_conductivity': circuit_properties.get('conductivity_stats', {}).get('avg_conductivity', 0),
            'circuit_complexity': circuit.number_of_edges() / circuit.number_of_nodes()
        }
    }
    
    print(f"Biological circuit analysis complete:")
    print(f"  Circuit elements: {circuit.number_of_nodes()}")
    print(f"  P-N junctions: {len(pn_junctions)}")
    print(f"  Therapeutic transistors: {len(transistors)}")
    print(f"  Circuit connectivity: {circuit_properties['circuit_connectivity']['is_connected']}")
    
    return biological_circuit_analysis

# Usage example
if __name__ == "__main__":
    print("Biological Circuit Analysis module ready for use")
    print("Use create_biological_circuit_analysis() to analyze biological circuits")
