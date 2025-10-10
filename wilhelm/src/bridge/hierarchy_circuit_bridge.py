#!/usr/bin/env python3
"""
Hierarchy-Circuit Bridge Implementation
=====================================

This module implements the bridge mechanism that connects oscillatory hierarchy nodes 
to circuit network elements, enabling seamless navigation between tree structures 
and network graphs based on frequency matching.

Key Innovation: Tree → Graph conversion through resonance frequency matching
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import json
import os
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import pickle

@dataclass
class HierarchyNode:
    """Represents a node in the oscillatory hierarchy tree"""
    id: str
    level: int
    oscillation_frequency: float  # Hz
    observer_type: str  # 'finite' or 'transcendent'
    information_capacity: float
    spatial_scale: float  # meters
    temporal_scale: float  # seconds
    parent_id: Optional[str] = None
    children_ids: List[str] = None
    
    def __post_init__(self):
        if self.children_ids is None:
            self.children_ids = []

@dataclass
class CircuitElement:
    """Represents an element in the biological circuit network"""
    id: str
    element_type: str  # 'resistor', 'capacitor', 'inductor', 'oscillator'
    resonance_frequency: float  # Hz
    impedance: complex
    biological_function: str
    molecular_basis: str
    conductivity: float = 0.0
    hole_density: float = 0.0
    
@dataclass
class BridgeConnection:
    """Represents a connection between hierarchy and circuit"""
    id: str
    hierarchy_node_id: str
    circuit_element_id: str
    frequency_match_score: float
    bridge_strength: float
    created_timestamp: str

class HierarchyCircuitBridge:
    """
    Main bridge class that connects oscillatory hierarchies to circuit networks
    """
    
    def __init__(self, frequency_tolerance: float = 1e-3):
        """
        Initialize the bridge system
        
        Args:
            frequency_tolerance: Maximum relative frequency difference for creating bridges
        """
        self.frequency_tolerance = frequency_tolerance
        self.hierarchy_nodes = {}
        self.circuit_elements = {}
        self.bridge_connections = {}
        self.bridge_graph = nx.Graph()
        
        # Results storage
        self.results = {
            'bridge_connections': [],
            'frequency_matches': [],
            'navigation_paths': [],
            'validation_metrics': {}
        }
    
    def add_hierarchy_node(self, node: HierarchyNode):
        """Add a node to the oscillatory hierarchy"""
        self.hierarchy_nodes[node.id] = node
        self.bridge_graph.add_node(node.id, 
                                  node_type='hierarchy',
                                  frequency=node.oscillation_frequency,
                                  level=node.level)
    
    def add_circuit_element(self, element: CircuitElement):
        """Add an element to the circuit network"""
        self.circuit_elements[element.id] = element
        self.bridge_graph.add_node(element.id,
                                  node_type='circuit',
                                  frequency=element.resonance_frequency,
                                  element_type=element.element_type)
    
    def find_frequency_matches(self) -> List[Tuple[str, str, float]]:
        """
        Find frequency matches between hierarchy nodes and circuit elements
        
        Returns:
            List of (hierarchy_id, circuit_id, match_score) tuples
        """
        matches = []
        
        for h_id, h_node in self.hierarchy_nodes.items():
            for c_id, c_element in self.circuit_elements.items():
                
                # Calculate relative frequency difference
                freq_diff = abs(h_node.oscillation_frequency - c_element.resonance_frequency)
                rel_diff = freq_diff / max(h_node.oscillation_frequency, c_element.resonance_frequency)
                
                if rel_diff < self.frequency_tolerance:
                    match_score = 1.0 - rel_diff  # Higher score for closer matches
                    matches.append((h_id, c_id, match_score))
        
        # Sort by match score (best matches first)
        matches.sort(key=lambda x: x[2], reverse=True)
        self.results['frequency_matches'] = matches
        
        return matches
    
    def create_bridge(self, hierarchy_id: str, circuit_id: str, match_score: float) -> BridgeConnection:
        """Create a bidirectional bridge between hierarchy node and circuit element"""
        
        bridge_id = f"bridge_{hierarchy_id}_{circuit_id}"
        
        # Calculate bridge strength based on match score and node properties
        h_node = self.hierarchy_nodes[hierarchy_id]
        c_element = self.circuit_elements[circuit_id]
        
        # Bridge strength considers frequency match and information capacity
        bridge_strength = match_score * np.sqrt(h_node.information_capacity)
        
        bridge = BridgeConnection(
            id=bridge_id,
            hierarchy_node_id=hierarchy_id,
            circuit_element_id=circuit_id,
            frequency_match_score=match_score,
            bridge_strength=bridge_strength,
            created_timestamp=datetime.now().isoformat()
        )
        
        self.bridge_connections[bridge_id] = bridge
        
        # Add edge to bridge graph
        self.bridge_graph.add_edge(hierarchy_id, circuit_id,
                                  bridge_id=bridge_id,
                                  weight=bridge_strength,
                                  match_score=match_score)
        
        return bridge
    
    def build_all_bridges(self) -> Dict[str, Any]:
        """Build all possible bridges based on frequency matching"""
        
        print("Building hierarchy-circuit bridges...")
        matches = self.find_frequency_matches()
        
        bridges_created = []
        for h_id, c_id, match_score in matches:
            bridge = self.create_bridge(h_id, c_id, match_score)
            bridges_created.append({
                'bridge_id': bridge.id,
                'hierarchy_node': h_id,
                'circuit_element': c_id,
                'match_score': match_score,
                'bridge_strength': bridge.bridge_strength
            })
        
        self.results['bridge_connections'] = bridges_created
        
        print(f"Created {len(bridges_created)} bridges")
        return {
            'total_bridges': len(bridges_created),
            'bridges': bridges_created,
            'average_match_score': np.mean([b['match_score'] for b in bridges_created]) if bridges_created else 0,
            'average_bridge_strength': np.mean([b['bridge_strength'] for b in bridges_created]) if bridges_created else 0
        }
    
    def navigate_hybrid_path(self, start_node: str, target_node: str) -> List[str]:
        """
        Navigate from any node to any other node using both hierarchy and circuit paths
        """
        try:
            # Use NetworkX shortest path on the bridge graph
            path = nx.shortest_path(self.bridge_graph, start_node, target_node, weight='weight')
            
            self.results['navigation_paths'].append({
                'start': start_node,
                'target': target_node,
                'path': path,
                'path_length': len(path),
                'crosses_structures': self._path_crosses_structures(path)
            })
            
            return path
        except nx.NetworkXNoPath:
            print(f"No path found between {start_node} and {target_node}")
            return []
    
    def _path_crosses_structures(self, path: List[str]) -> bool:
        """Check if path crosses between hierarchy and circuit structures"""
        node_types = []
        for node_id in path:
            if node_id in self.hierarchy_nodes:
                node_types.append('hierarchy')
            elif node_id in self.circuit_elements:
                node_types.append('circuit')
        
        # Path crosses structures if it contains both types
        return 'hierarchy' in node_types and 'circuit' in node_types
    
    def analyze_bridge_topology(self) -> Dict[str, Any]:
        """Analyze the topology of the bridge network"""
        
        analysis = {
            'total_nodes': self.bridge_graph.number_of_nodes(),
            'total_edges': self.bridge_graph.number_of_edges(),
            'hierarchy_nodes': len(self.hierarchy_nodes),
            'circuit_nodes': len(self.circuit_elements),
            'bridge_connections': len(self.bridge_connections),
            'connectivity': {}
        }
        
        if self.bridge_graph.number_of_nodes() > 0:
            # Network connectivity metrics
            analysis['connectivity'] = {
                'is_connected': nx.is_connected(self.bridge_graph),
                'number_of_components': nx.number_connected_components(self.bridge_graph),
                'average_clustering': nx.average_clustering(self.bridge_graph),
                'density': nx.density(self.bridge_graph)
            }
            
            # Degree analysis
            degrees = dict(self.bridge_graph.degree())
            analysis['degree_stats'] = {
                'mean_degree': np.mean(list(degrees.values())),
                'max_degree': max(degrees.values()) if degrees else 0,
                'min_degree': min(degrees.values()) if degrees else 0
            }
        
        self.results['validation_metrics']['topology_analysis'] = analysis
        return analysis
    
    def validate_bridge_system(self) -> Dict[str, Any]:
        """Comprehensive validation of the bridge system"""
        
        validation = {
            'bridge_creation_success_rate': 0.0,
            'frequency_matching_accuracy': 0.0,
            'navigation_success_rate': 0.0,
            'cross_structure_navigation_rate': 0.0
        }
        
        # Bridge creation success rate
        total_possible_bridges = len(self.hierarchy_nodes) * len(self.circuit_elements)
        if total_possible_bridges > 0:
            validation['bridge_creation_success_rate'] = len(self.bridge_connections) / total_possible_bridges
        
        # Frequency matching accuracy
        if self.results['frequency_matches']:
            match_scores = [match[2] for match in self.results['frequency_matches']]
            validation['frequency_matching_accuracy'] = np.mean(match_scores)
        
        # Navigation success rate
        if self.results['navigation_paths']:
            successful_paths = [p for p in self.results['navigation_paths'] if len(p['path']) > 0]
            validation['navigation_success_rate'] = len(successful_paths) / len(self.results['navigation_paths'])
            
            # Cross-structure navigation rate
            cross_structure_paths = [p for p in successful_paths if p['crosses_structures']]
            if successful_paths:
                validation['cross_structure_navigation_rate'] = len(cross_structure_paths) / len(successful_paths)
        
        self.results['validation_metrics']['bridge_validation'] = validation
        return validation
    
    def visualize_bridge_network(self, output_dir: str = "results"):
        """Create comprehensive visualizations of the bridge network"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up the plotting style
        plt.style.use('default')
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Hierarchy-Circuit Bridge Network Analysis', fontsize=16, fontweight='bold')
        
        # 1. Network topology visualization
        ax1 = axes[0, 0]
        pos = nx.spring_layout(self.bridge_graph, k=1, iterations=50)
        
        # Color nodes by type
        node_colors = []
        for node in self.bridge_graph.nodes():
            if node in self.hierarchy_nodes:
                node_colors.append('red')
            else:
                node_colors.append('blue')
        
        nx.draw(self.bridge_graph, pos, ax=ax1, 
                node_color=node_colors, node_size=100, 
                with_labels=False, edge_color='gray', alpha=0.7)
        ax1.set_title('Bridge Network Topology\n(Red: Hierarchy, Blue: Circuit)')
        
        # 2. Frequency matching distribution
        ax2 = axes[0, 1]
        if self.results['frequency_matches']:
            match_scores = [match[2] for match in self.results['frequency_matches']]
            ax2.hist(match_scores, bins=20, alpha=0.7, color='green')
            ax2.set_xlabel('Frequency Match Score')
            ax2.set_ylabel('Count')
            ax2.set_title('Frequency Match Score Distribution')
        else:
            ax2.text(0.5, 0.5, 'No frequency matches found', 
                    ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Frequency Match Scores')
        
        # 3. Bridge strength vs match score
        ax3 = axes[0, 2]
        if self.results['bridge_connections']:
            match_scores = [b['match_score'] for b in self.results['bridge_connections']]
            bridge_strengths = [b['bridge_strength'] for b in self.results['bridge_connections']]
            ax3.scatter(match_scores, bridge_strengths, alpha=0.6, color='purple')
            ax3.set_xlabel('Match Score')
            ax3.set_ylabel('Bridge Strength')
            ax3.set_title('Bridge Strength vs Match Score')
        else:
            ax3.text(0.5, 0.5, 'No bridges created', 
                    ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Bridge Strength Analysis')
        
        # 4. Hierarchy levels vs circuit types
        ax4 = axes[1, 0]
        hierarchy_levels = [node.level for node in self.hierarchy_nodes.values()]
        circuit_types = [elem.element_type for elem in self.circuit_elements.values()]
        
        if hierarchy_levels:
            ax4.hist(hierarchy_levels, bins=max(10, len(set(hierarchy_levels))), 
                    alpha=0.7, color='red', label='Hierarchy Levels')
            ax4.set_xlabel('Hierarchy Level')
            ax4.set_ylabel('Count')
            ax4.set_title('Hierarchy Level Distribution')
        else:
            ax4.text(0.5, 0.5, 'No hierarchy nodes', 
                    ha='center', va='center', transform=ax4.transAxes)
        
        # 5. Validation metrics radar chart
        ax5 = axes[1, 1]
        validation = self.results.get('validation_metrics', {}).get('bridge_validation', {})
        if validation:
            metrics = list(validation.keys())
            values = list(validation.values())
            
            angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False)
            values += values[:1]  # Complete the circle
            angles = np.concatenate([angles, [angles[0]]])
            
            ax5 = fig.add_subplot(2, 3, 5, projection='polar')
            ax5.plot(angles, values, 'o-', linewidth=2, color='orange')
            ax5.fill(angles, values, alpha=0.25, color='orange')
            ax5.set_xticks(angles[:-1])
            ax5.set_xticklabels([m.replace('_', '\n') for m in metrics])
            ax5.set_title('Validation Metrics')
        else:
            ax5.text(0.5, 0.5, 'No validation metrics', 
                    ha='center', va='center', transform=ax5.transAxes)
            ax5.set_title('Validation Metrics')
        
        # 6. Network statistics summary
        ax6 = axes[1, 2]
        topology = self.results.get('validation_metrics', {}).get('topology_analysis', {})
        if topology:
            stats_text = f"""Network Statistics:
            
Total Nodes: {topology.get('total_nodes', 0)}
Total Edges: {topology.get('total_edges', 0)}
Hierarchy Nodes: {topology.get('hierarchy_nodes', 0)}
Circuit Nodes: {topology.get('circuit_nodes', 0)}
Bridges: {topology.get('bridge_connections', 0)}

Connectivity:
Connected: {topology.get('connectivity', {}).get('is_connected', False)}
Components: {topology.get('connectivity', {}).get('number_of_components', 0)}
Density: {topology.get('connectivity', {}).get('density', 0):.3f}
            """
            ax6.text(0.1, 0.9, stats_text, transform=ax6.transAxes, 
                    verticalalignment='top', fontfamily='monospace')
        else:
            ax6.text(0.5, 0.5, 'No topology analysis', 
                    ha='center', va='center', transform=ax6.transAxes)
        
        ax6.set_title('Network Statistics')
        ax6.axis('off')
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/bridge_network_analysis.png", dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Bridge network visualization saved to {output_dir}/bridge_network_analysis.png")
    
    def save_results(self, output_dir: str = "results"):
        """Save all results to files"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON results
        with open(f"{output_dir}/bridge_results.json", 'w') as f:
            json.dump(self.results, f, indent=4, default=str)
        
        # Save bridge connections as CSV
        if self.results['bridge_connections']:
            bridge_df = pd.DataFrame(self.results['bridge_connections'])
            bridge_df.to_csv(f"{output_dir}/bridge_connections.csv", index=False)
        
        # Save network data
        with open(f"{output_dir}/bridge_network.pickle", 'wb') as f:
            pickle.dump(self.bridge_graph, f)
        
        # Save node and element data
        nodes_data = {
            'hierarchy_nodes': {k: {
                'id': v.id, 'level': v.level, 'frequency': v.oscillation_frequency,
                'observer_type': v.observer_type, 'information_capacity': v.information_capacity
            } for k, v in self.hierarchy_nodes.items()},
            'circuit_elements': {k: {
                'id': v.id, 'element_type': v.element_type, 'frequency': v.resonance_frequency,
                'biological_function': v.biological_function, 'molecular_basis': v.molecular_basis
            } for k, v in self.circuit_elements.items()}
        }
        
        with open(f"{output_dir}/network_nodes.json", 'w') as f:
            json.dump(nodes_data, f, indent=4)
        
        print(f"Bridge system results saved to {output_dir}/")


def create_example_hierarchy_nodes() -> List[HierarchyNode]:
    """Create example hierarchy nodes for testing"""
    
    nodes = [
        # Transcendent observer
        HierarchyNode(
            id="transcendent_01",
            level=0,
            oscillation_frequency=1e12,  # 1 THz
            observer_type="transcendent",
            information_capacity=1e6,
            spatial_scale=1e-3,  # 1 mm
            temporal_scale=1e-12  # 1 ps
        ),
        
        # Finite observers at different scales
        HierarchyNode(
            id="finite_molecular",
            level=1,
            oscillation_frequency=7.07e13,  # N2 vibrational frequency
            observer_type="finite",
            information_capacity=1e4,
            spatial_scale=1e-9,  # 1 nm
            temporal_scale=1e-14,  # 10 fs
            parent_id="transcendent_01"
        ),
        
        HierarchyNode(
            id="finite_cellular",
            level=1,
            oscillation_frequency=1e6,  # 1 MHz (cellular oscillations)
            observer_type="finite",
            information_capacity=1e5,
            spatial_scale=1e-6,  # 1 µm
            temporal_scale=1e-6,  # 1 µs
            parent_id="transcendent_01"
        ),
        
        HierarchyNode(
            id="finite_tissue",
            level=2,
            oscillation_frequency=1e3,  # 1 kHz (tissue dynamics)
            observer_type="finite",
            information_capacity=1e3,
            spatial_scale=1e-3,  # 1 mm
            temporal_scale=1e-3,  # 1 ms
            parent_id="finite_cellular"
        )
    ]
    
    return nodes


def create_example_circuit_elements() -> List[CircuitElement]:
    """Create example circuit elements for testing"""
    
    elements = [
        # Oscillatory hole semiconductor elements
        CircuitElement(
            id="oxygen_oscillator",
            element_type="oscillator",
            resonance_frequency=4.46e3,  # From oxygen paramagnetic resonance
            impedance=complex(1000, 500),
            biological_function="oxygen_information_processing",
            molecular_basis="O2_paramagnetic_resonance",
            conductivity=3.21e15,  # OID from paper
            hole_density=1e22
        ),
        
        CircuitElement(
            id="molecular_capacitor",
            element_type="capacitor",
            resonance_frequency=7.07e13,  # N2 molecular vibration
            impedance=complex(0, -1e6),
            biological_function="molecular_energy_storage",
            molecular_basis="N2_vibrational_modes",
            conductivity=1e10,
            hole_density=1e20
        ),
        
        CircuitElement(
            id="membrane_resistor",
            element_type="resistor",
            resonance_frequency=1e6,  # Membrane transport frequency
            impedance=complex(1e4, 0),
            biological_function="selective_transport",
            molecular_basis="lipid_bilayer_dynamics",
            conductivity=9.25e11,  # From electron cascade
            hole_density=1e18
        ),
        
        CircuitElement(
            id="cascade_inductor",
            element_type="inductor",
            resonance_frequency=1e12,  # Electron cascade frequency
            impedance=complex(0, 1e8),
            biological_function="electron_cascade_communication",
            molecular_basis="protein_electron_transfer",
            conductivity=1e6,  # Cascade velocity
            hole_density=1e21
        )
    ]
    
    return elements


def main():
    """Main function for testing the bridge system"""
    
    print("="*70)
    print("HIERARCHY-CIRCUIT BRIDGE SYSTEM TEST")
    print("="*70)
    
    # Initialize bridge system
    bridge = HierarchyCircuitBridge(frequency_tolerance=0.1)  # 10% tolerance
    
    # Create example nodes and elements
    hierarchy_nodes = create_example_hierarchy_nodes()
    circuit_elements = create_example_circuit_elements()
    
    # Add nodes to bridge system
    print("Adding hierarchy nodes and circuit elements...")
    for node in hierarchy_nodes:
        bridge.add_hierarchy_node(node)
    
    for element in circuit_elements:
        bridge.add_circuit_element(element)
    
    print(f"Added {len(hierarchy_nodes)} hierarchy nodes")
    print(f"Added {len(circuit_elements)} circuit elements")
    
    # Build bridges
    bridge_stats = bridge.build_all_bridges()
    print(f"\nBridge Creation Results:")
    print(f"Total bridges created: {bridge_stats['total_bridges']}")
    print(f"Average match score: {bridge_stats['average_match_score']:.3f}")
    print(f"Average bridge strength: {bridge_stats['average_bridge_strength']:.3f}")
    
    # Test navigation
    print("\nTesting hybrid navigation...")
    test_paths = [
        ("transcendent_01", "oxygen_oscillator"),
        ("finite_molecular", "molecular_capacitor"),
        ("finite_cellular", "membrane_resistor")
    ]
    
    for start, target in test_paths:
        path = bridge.navigate_hybrid_path(start, target)
        if path:
            crosses = bridge._path_crosses_structures(path)
            print(f"Path {start} → {target}: {len(path)} steps, crosses structures: {crosses}")
        else:
            print(f"No path found: {start} → {target}")
    
    # Analyze topology
    print("\nAnalyzing bridge network topology...")
    topology = bridge.analyze_bridge_topology()
    print(f"Network connectivity: {topology['connectivity']['is_connected']}")
    print(f"Number of components: {topology['connectivity']['number_of_components']}")
    print(f"Network density: {topology['connectivity']['density']:.3f}")
    
    # Validate system
    print("\nValidating bridge system...")
    validation = bridge.validate_bridge_system()
    print(f"Bridge creation success rate: {validation['bridge_creation_success_rate']:.3f}")
    print(f"Frequency matching accuracy: {validation['frequency_matching_accuracy']:.3f}")
    print(f"Navigation success rate: {validation['navigation_success_rate']:.3f}")
    
    # Create visualizations
    print("\nGenerating visualizations...")
    bridge.visualize_bridge_network("bridge_results")
    
    # Save results
    print("Saving results...")
    bridge.save_results("bridge_results")
    
    print("\n" + "="*70)
    print("BRIDGE SYSTEM TEST COMPLETE")
    print("="*70)
    print("Results saved to: bridge_results/")
    print("Key insight: Successfully linked oscillatory hierarchy to circuit networks!")


if __name__ == "__main__":
    main()
