//! Graph Schema Module
//! 
//! This module defines the schema for molecular graphs and networks, providing
//! strongly-typed representations of nodes, edges, and their properties.

use anyhow::Result;
use log::{debug, info};
use serde::{Serialize, Deserialize};
use std::collections::HashMap;

/// Node types in the molecular knowledge graph
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum NodeType {
    /// A chemical compound or molecule
    Molecule,
    
    /// A biological organism
    Organism,
    
    /// A protein or enzyme
    Protein,
    
    /// A genetic element
    Gene,
    
    /// A metabolic or signaling pathway
    Pathway,
    
    /// A disease or condition
    Disease,
    
    /// A publication or reference
    Publication,
    
    /// A data source or database
    Source,
}

impl std::fmt::Display for NodeType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            NodeType::Molecule => write!(f, "Molecule"),
            NodeType::Organism => write!(f, "Organism"),
            NodeType::Protein => write!(f, "Protein"),
            NodeType::Gene => write!(f, "Gene"),
            NodeType::Pathway => write!(f, "Pathway"),
            NodeType::Disease => write!(f, "Disease"),
            NodeType::Publication => write!(f, "Publication"),
            NodeType::Source => write!(f, "Source"),
        }
    }
}

/// Edge types in the molecular knowledge graph
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EdgeType {
    /// Similar to another entity
    SimilarTo,
    
    /// Part of a larger entity
    PartOf,
    
    /// Interacts with another entity
    InteractsWith,
    
    /// Inhibits another entity
    Inhibits,
    
    /// Activates another entity
    Activates,
    
    /// Treats a disease or condition
    Treats,
    
    /// Causes a disease or condition
    Causes,
    
    /// Referenced by a publication
    ReferencedBy,
    
    /// Sourced from a database
    SourcedFrom,
    
    /// Transforms into another entity
    TransformsTo,
    
    /// Metabolized by an organism
    MetabolizedBy,
}

impl std::fmt::Display for EdgeType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            EdgeType::SimilarTo => write!(f, "SIMILAR_TO"),
            EdgeType::PartOf => write!(f, "PART_OF"),
            EdgeType::InteractsWith => write!(f, "INTERACTS_WITH"),
            EdgeType::Inhibits => write!(f, "INHIBITS"),
            EdgeType::Activates => write!(f, "ACTIVATES"),
            EdgeType::Treats => write!(f, "TREATS"),
            EdgeType::Causes => write!(f, "CAUSES"),
            EdgeType::ReferencedBy => write!(f, "REFERENCED_BY"),
            EdgeType::SourcedFrom => write!(f, "SOURCED_FROM"),
            EdgeType::TransformsTo => write!(f, "TRANSFORMS_TO"),
            EdgeType::MetabolizedBy => write!(f, "METABOLIZED_BY"),
        }
    }
}

/// A node in the molecular knowledge graph
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Node {
    /// Unique identifier for the node
    pub id: String,
    
    /// Type of node
    pub node_type: NodeType,
    
    /// Primary name or label
    pub name: String,
    
    /// Additional properties
    pub properties: HashMap<String, serde_json::Value>,
    
    /// External identifiers
    pub external_ids: HashMap<String, String>,
}

impl Node {
    /// Create a new node
    pub fn new(id: String, node_type: NodeType, name: String) -> Self {
        Self {
            id,
            node_type,
            name,
            properties: HashMap::new(),
            external_ids: HashMap::new(),
        }
    }
    
    /// Add a property to the node
    pub fn add_property(&mut self, key: &str, value: serde_json::Value) -> &mut Self {
        self.properties.insert(key.to_string(), value);
        self
    }
    
    /// Add an external identifier to the node
    pub fn add_external_id(&mut self, system: &str, id: &str) -> &mut Self {
        self.external_ids.insert(system.to_string(), id.to_string());
        self
    }
    
    /// Get a property value
    pub fn get_property(&self, key: &str) -> Option<&serde_json::Value> {
        self.properties.get(key)
    }
    
    /// Get an external identifier
    pub fn get_external_id(&self, system: &str) -> Option<&str> {
        self.external_ids.get(system).map(|s| s.as_str())
    }
}

/// An edge in the molecular knowledge graph
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Edge {
    /// Unique identifier for the edge
    pub id: String,
    
    /// Source node ID
    pub source_id: String,
    
    /// Target node ID
    pub target_id: String,
    
    /// Type of edge
    pub edge_type: EdgeType,
    
    /// Additional properties
    pub properties: HashMap<String, serde_json::Value>,
}

impl Edge {
    /// Create a new edge
    pub fn new(
        source_id: String,
        target_id: String,
        edge_type: EdgeType,
    ) -> Self {
        Self {
            id: format!("e_{}_{}", source_id, target_id),
            source_id,
            target_id,
            edge_type,
            properties: HashMap::new(),
        }
    }
    
    /// Add a property to the edge
    pub fn add_property(&mut self, key: &str, value: serde_json::Value) -> &mut Self {
        self.properties.insert(key.to_string(), value);
        self
    }
    
    /// Get a property value
    pub fn get_property(&self, key: &str) -> Option<&serde_json::Value> {
        self.properties.get(key)
    }
}

/// A complete molecular knowledge graph
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MolecularGraph {
    /// Unique identifier for the graph
    pub id: String,
    
    /// Name of the graph
    pub name: String,
    
    /// Nodes in the graph
    pub nodes: Vec<Node>,
    
    /// Edges in the graph
    pub edges: Vec<Edge>,
    
    /// Additional metadata
    pub metadata: HashMap<String, serde_json::Value>,
}

impl MolecularGraph {
    /// Create a new molecular graph
    pub fn new(id: String, name: String) -> Self {
        Self {
            id,
            name,
            nodes: Vec::new(),
            edges: Vec::new(),
            metadata: HashMap::new(),
        }
    }
    
    /// Add a node to the graph
    pub fn add_node(&mut self, node: Node) -> &mut Self {
        self.nodes.push(node);
        self
    }
    
    /// Add an edge to the graph
    pub fn add_edge(&mut self, edge: Edge) -> &mut Self {
        self.edges.push(edge);
        self
    }
    
    /// Find a node by ID
    pub fn find_node(&self, id: &str) -> Option<&Node> {
        self.nodes.iter().find(|node| node.id == id)
    }
    
    /// Find nodes by type
    pub fn find_nodes_by_type(&self, node_type: NodeType) -> Vec<&Node> {
        self.nodes.iter().filter(|node| node.node_type == node_type).collect()
    }
    
    /// Find edges connecting to a node
    pub fn find_edges_for_node(&self, node_id: &str) -> Vec<&Edge> {
        self.edges.iter().filter(|edge| {
            edge.source_id == node_id || edge.target_id == node_id
        }).collect()
    }
    
    /// Find edges of a specific type
    pub fn find_edges_by_type(&self, edge_type: EdgeType) -> Vec<&Edge> {
        self.edges.iter().filter(|edge| edge.edge_type == edge_type).collect()
    }
    
    /// Find connected nodes for a given node
    pub fn find_connected_nodes(&self, node_id: &str) -> Vec<(&Node, &Edge)> {
        let mut connected = Vec::new();
        
        for edge in self.edges.iter() {
            if edge.source_id == node_id {
                if let Some(target) = self.find_node(&edge.target_id) {
                    connected.push((target, edge));
                }
            } else if edge.target_id == node_id {
                if let Some(source) = self.find_node(&edge.source_id) {
                    connected.push((source, edge));
                }
            }
        }
        
        connected
    }
    
    /// Add metadata to the graph
    pub fn add_metadata(&mut self, key: &str, value: serde_json::Value) -> &mut Self {
        self.metadata.insert(key.to_string(), value);
        self
    }
}

/// A path in a molecular graph
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GraphPath {
    /// Nodes in the path
    pub nodes: Vec<Node>,
    
    /// Edges in the path
    pub edges: Vec<Edge>,
}

impl GraphPath {
    /// Create a new empty path
    pub fn new() -> Self {
        Self {
            nodes: Vec::new(),
            edges: Vec::new(),
        }
    }
    
    /// Add a node and edge to the path
    pub fn add_step(&mut self, node: Node, edge: Option<Edge>) -> &mut Self {
        self.nodes.push(node);
        if let Some(e) = edge {
            self.edges.push(e);
        }
        self
    }
    
    /// Get the length of the path (number of edges)
    pub fn length(&self) -> usize {
        self.edges.len()
    }
    
    /// Get the start node of the path
    pub fn start_node(&self) -> Option<&Node> {
        self.nodes.first()
    }
    
    /// Get the end node of the path
    pub fn end_node(&self) -> Option<&Node> {
        self.nodes.last()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_node_creation() {
        let mut node = Node::new(
            "mol_123".to_string(),
            NodeType::Molecule,
            "Glucose".to_string(),
        );
        
        node.add_property("formula", serde_json::json!("C6H12O6"))
            .add_external_id("pubchem", "5793");
            
        assert_eq!(node.id, "mol_123");
        assert_eq!(node.node_type, NodeType::Molecule);
        assert_eq!(node.name, "Glucose");
        assert_eq!(node.get_property("formula"), Some(&serde_json::json!("C6H12O6")));
        assert_eq!(node.get_external_id("pubchem"), Some("5793"));
    }
    
    #[test]
    fn test_edge_creation() {
        let mut edge = Edge::new(
            "mol_123".to_string(),
            "protein_456".to_string(),
            EdgeType::InteractsWith,
        );
        
        edge.add_property("affinity", serde_json::json!(0.89));
        
        assert_eq!(edge.source_id, "mol_123");
        assert_eq!(edge.target_id, "protein_456");
        assert_eq!(edge.edge_type, EdgeType::InteractsWith);
        assert_eq!(edge.get_property("affinity"), Some(&serde_json::json!(0.89)));
    }
    
    #[test]
    fn test_graph_operations() {
        let mut graph = MolecularGraph::new(
            "test_graph".to_string(),
            "Test Knowledge Graph".to_string(),
        );
        
        let node1 = Node::new(
            "mol_123".to_string(),
            NodeType::Molecule,
            "Glucose".to_string(),
        );
        
        let node2 = Node::new(
            "protein_456".to_string(),
            NodeType::Protein,
            "Insulin".to_string(),
        );
        
        let edge = Edge::new(
            "mol_123".to_string(),
            "protein_456".to_string(),
            EdgeType::InteractsWith,
        );
        
        graph.add_node(node1)
             .add_node(node2)
             .add_edge(edge);
             
        assert_eq!(graph.nodes.len(), 2);
        assert_eq!(graph.edges.len(), 1);
        
        let found_node = graph.find_node("mol_123");
        assert!(found_node.is_some());
        assert_eq!(found_node.unwrap().name, "Glucose");
        
        let connected = graph.find_connected_nodes("mol_123");
        assert_eq!(connected.len(), 1);
        assert_eq!(connected[0].0.name, "Insulin");
    }
}
