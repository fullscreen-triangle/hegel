//! Molecular Graph Module
//!
//! This module provides functionality for working with molecular graphs and networks,
//! including similarity calculations, substructure matching, and network analysis.

use anyhow::Result;
use log::{info, debug};
use petgraph::graph::{Graph, NodeIndex};
use petgraph::Undirected;
use serde::{Serialize, Deserialize};
use std::collections::{HashMap, HashSet};

use crate::processing::Molecule;

/// Initialize the graph module
pub fn initialize() -> Result<()> {
    info!("Initializing molecular graph module");
    info!("Molecular graph module initialized successfully");
    Ok(())
}

/// Molecular network representation
#[derive(Debug, Clone)]
pub struct MoleculeNetwork {
    /// The underlying graph
    graph: Graph<MoleculeNode, EdgeWeight, Undirected>,
    
    /// Mapping from molecule IDs to node indices
    id_to_node: HashMap<String, NodeIndex>,
}

impl MoleculeNetwork {
    /// Create a new, empty molecular network
    pub fn new() -> Self {
        Self {
            graph: Graph::new_undirected(),
            id_to_node: HashMap::new(),
        }
    }
    
    /// Add a molecule to the network
    pub fn add_molecule(&mut self, molecule: &Molecule) -> NodeIndex {
        // Check if the molecule is already in the network
        if let Some(&node_idx) = self.id_to_node.get(&molecule.id) {
            return node_idx;
        }
        
        // Create a new node for the molecule
        let node = MoleculeNode {
            id: molecule.id.clone(),
            smiles: molecule.smiles.clone(),
            name: molecule.name.clone(),
            formula: molecule.formula.clone(),
            properties: molecule.properties.clone(),
        };
        
        // Add the node to the graph
        let node_idx = self.graph.add_node(node);
        
        // Add the mapping
        self.id_to_node.insert(molecule.id.clone(), node_idx);
        
        node_idx
    }
    
    /// Add a similarity edge between two molecules
    pub fn add_similarity(&mut self, mol1_id: &str, mol2_id: &str, similarity: f64) -> Option<usize> {
        // Get the node indices for the molecules
        let node1 = self.id_to_node.get(mol1_id)?;
        let node2 = self.id_to_node.get(mol2_id)?;
        
        // Add an edge between the nodes
        let edge_idx = self.graph.add_edge(
            *node1,
            *node2,
            EdgeWeight::Similarity(similarity)
        );
        
        Some(edge_idx.index())
    }
    
    /// Get all molecules in the network
    pub fn get_molecules(&self) -> Vec<&MoleculeNode> {
        self.graph.node_weights().collect()
    }
    
    /// Get a molecule by ID
    pub fn get_molecule(&self, id: &str) -> Option<&MoleculeNode> {
        let node_idx = self.id_to_node.get(id)?;
        self.graph.node_weight(*node_idx)
    }
    
    /// Get similar molecules to a given molecule
    pub fn get_similar_molecules(&self, id: &str, min_similarity: f64) -> Vec<(MoleculeNode, f64)> {
        let mut similar_molecules = Vec::new();
        
        // Get the node index for the molecule
        if let Some(&node_idx) = self.id_to_node.get(id) {
            // Iterate through neighbors
            for edge in self.graph.edges(node_idx) {
                let neighbor_idx = edge.target();
                
                // Skip self-loops
                if neighbor_idx == node_idx {
                    continue;
                }
                
                // Check the similarity
                if let EdgeWeight::Similarity(similarity) = edge.weight() {
                    if *similarity >= min_similarity {
                        // Get the neighbor molecule
                        if let Some(molecule) = self.graph.node_weight(neighbor_idx) {
                            similar_molecules.push((molecule.clone(), *similarity));
                        }
                    }
                }
            }
        }
        
        similar_molecules
    }
    
    /// Calculate network metrics for the molecular network
    pub fn calculate_metrics(&self) -> NetworkMetrics {
        let mut metrics = NetworkMetrics {
            node_count: self.graph.node_count(),
            edge_count: self.graph.edge_count(),
            density: 0.0,
            avg_degree: 0.0,
            max_degree: 0,
            clusters: Vec::new(),
            centrality: HashMap::new(),
        };
        
        // Calculate density
        if metrics.node_count > 1 {
            let max_edges = (metrics.node_count * (metrics.node_count - 1)) / 2;
            metrics.density = metrics.edge_count as f64 / max_edges as f64;
        }
        
        // Calculate degree metrics
        let mut sum_degree = 0;
        
        for node_idx in self.graph.node_indices() {
            let degree = self.graph.neighbors(node_idx).count();
            sum_degree += degree;
            
            if degree > metrics.max_degree {
                metrics.max_degree = degree;
            }
            
            // Store centrality value
            if let Some(molecule) = self.graph.node_weight(node_idx) {
                metrics.centrality.insert(molecule.id.clone(), degree as f64);
            }
        }
        
        if metrics.node_count > 0 {
            metrics.avg_degree = sum_degree as f64 / metrics.node_count as f64;
        }
        
        // Find clusters (connected components)
        let components = petgraph::algo::connected_components(&self.graph);
        metrics.clusters = vec![0; components as usize];
        
        for node_idx in self.graph.node_indices() {
            if let Some(component) = petgraph::algo::connected_component(&self.graph, node_idx) {
                if component < metrics.clusters.len() {
                    metrics.clusters[component] += 1;
                }
            }
        }
        
        metrics
    }
    
    /// Convert the network to a serializable format
    pub fn to_serializable(&self) -> SerializableNetwork {
        let mut nodes = Vec::new();
        let mut edges = Vec::new();
        
        // Convert nodes
        for node_idx in self.graph.node_indices() {
            if let Some(molecule) = self.graph.node_weight(node_idx) {
                nodes.push(molecule.clone());
            }
        }
        
        // Convert edges
        for edge in self.graph.edge_indices() {
            if let Some((source, target, weight)) = self.graph.edge_endpoints(edge).map(|(s, t)| {
                (s, t, self.graph.edge_weight(edge).unwrap())
            }) {
                if let (Some(source_mol), Some(target_mol)) = (
                    self.graph.node_weight(source),
                    self.graph.node_weight(target)
                ) {
                    match weight {
                        EdgeWeight::Similarity(similarity) => {
                            edges.push(SerializableEdge {
                                source: source_mol.id.clone(),
                                target: target_mol.id.clone(),
                                weight: *similarity,
                                edge_type: "similarity".to_string(),
                            });
                        }
                    }
                }
            }
        }
        
        SerializableNetwork { nodes, edges }
    }
}

/// Node in a molecular network
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MoleculeNode {
    /// Unique identifier for the molecule
    pub id: String,
    
    /// SMILES representation of the molecule
    pub smiles: String,
    
    /// Optional common name or identifier
    pub name: Option<String>,
    
    /// Optional molecular formula
    pub formula: Option<String>,
    
    /// Additional properties and metadata
    pub properties: HashMap<String, serde_json::Value>,
}

/// Edge weight in a molecular network
#[derive(Debug, Clone, Copy)]
pub enum EdgeWeight {
    /// Similarity between molecules (0.0 - 1.0)
    Similarity(f64),
}

/// Network metrics for a molecular network
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkMetrics {
    /// Number of nodes in the network
    pub node_count: usize,
    
    /// Number of edges in the network
    pub edge_count: usize,
    
    /// Density of the network (ratio of actual edges to possible edges)
    pub density: f64,
    
    /// Average degree of nodes in the network
    pub avg_degree: f64,
    
    /// Maximum degree of any node in the network
    pub max_degree: usize,
    
    /// Sizes of connected components (clusters) in the network
    pub clusters: Vec<usize>,
    
    /// Centrality values for each node (by molecule ID)
    pub centrality: HashMap<String, f64>,
}

/// Serializable representation of a molecular network
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SerializableNetwork {
    /// Nodes in the network
    pub nodes: Vec<MoleculeNode>,
    
    /// Edges in the network
    pub edges: Vec<SerializableEdge>,
}

/// Serializable edge in a molecular network
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SerializableEdge {
    /// Source molecule ID
    pub source: String,
    
    /// Target molecule ID
    pub target: String,
    
    /// Weight of the edge
    pub weight: f64,
    
    /// Type of the edge
    pub edge_type: String,
}

/// Builder for constructing a molecular network
pub struct NetworkBuilder {
    /// The network being built
    network: MoleculeNetwork,
    
    /// Minimum similarity threshold for adding edges
    similarity_threshold: f64,
    
    /// Maximum number of neighbors per molecule
    max_neighbors: usize,
}

impl NetworkBuilder {
    /// Create a new network builder
    pub fn new(similarity_threshold: f64, max_neighbors: usize) -> Self {
        Self {
            network: MoleculeNetwork::new(),
            similarity_threshold,
            max_neighbors,
        }
    }
    
    /// Add a molecule to the network
    pub fn add_molecule(&mut self, molecule: &Molecule) -> Result<()> {
        self.network.add_molecule(molecule);
        Ok(())
    }
    
    /// Add multiple molecules to the network
    pub fn add_molecules(&mut self, molecules: &[Molecule]) -> Result<()> {
        for molecule in molecules {
            self.add_molecule(molecule)?;
        }
        Ok(())
    }
    
    /// Calculate similarities and add edges
    pub fn build_similarities(&mut self) -> Result<()> {
        // Get all molecules in the network
        let molecules = self.network.get_molecules();
        
        // Calculate similarities between all pairs of molecules
        for (i, mol1) in molecules.iter().enumerate() {
            for mol2 in molecules.iter().skip(i + 1) {
                // Calculate similarity between the molecules
                // In a real implementation, this would use RDKit or another library
                // For now, just use a random value
                let similarity = rand::random::<f64>();
                
                // Add an edge if the similarity is above the threshold
                if similarity >= self.similarity_threshold {
                    self.network.add_similarity(&mol1.id, &mol2.id, similarity);
                }
            }
        }
        
        // Prune edges to keep only the top neighbors for each molecule
        self.prune_edges();
        
        Ok(())
    }
    
    /// Prune edges to keep only the top neighbors for each molecule
    fn prune_edges(&mut self) {
        // This would remove excess edges to keep only the top neighbors
        // For now, we'll skip this step
    }
    
    /// Build the network and return it
    pub fn build(self) -> MoleculeNetwork {
        self.network
    }
}
