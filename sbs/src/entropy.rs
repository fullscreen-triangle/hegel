use serde::{Deserialize, Serialize};

use crate::circuit::{Circuit, Perturbation};

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct SEntropy {
    pub se: f64,
    pub sk: f64,
    pub st: f64,
}

impl SEntropy {
    pub fn new(se: f64, sk: f64, st: f64) -> Self {
        Self { se, sk, st }
    }

    pub fn as_array(&self) -> [f64; 3] {
        [self.se, self.sk, self.st]
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Triple {
    pub k: Box<TripleNode>,
    pub t: Box<TripleNode>,
    pub e: Box<TripleNode>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TripleNode {
    Leaf(SEntropy),
    Branch(Triple),
}

impl Triple {
    pub fn from_entropy(s: SEntropy) -> Self {
        Self {
            k: Box::new(TripleNode::Leaf(SEntropy::new(s.sk, 0.0, 0.0))),
            t: Box::new(TripleNode::Leaf(SEntropy::new(0.0, s.st, 0.0))),
            e: Box::new(TripleNode::Leaf(SEntropy::new(0.0, 0.0, s.se))),
        }
    }

    pub fn depth(&self) -> usize {
        let dk = match self.k.as_ref() {
            TripleNode::Leaf(_) => 0,
            TripleNode::Branch(t) => 1 + t.depth(),
        };
        let dt = match self.t.as_ref() {
            TripleNode::Leaf(_) => 0,
            TripleNode::Branch(t) => 1 + t.depth(),
        };
        let de = match self.e.as_ref() {
            TripleNode::Leaf(_) => 0,
            TripleNode::Branch(t) => 1 + t.depth(),
        };
        dk.max(dt).max(de)
    }

    pub fn coordinate_selections(&self, depth: usize) -> usize {
        3_usize.pow(depth as u32)
    }
}

pub fn compute_s_entropy(circuit: &Circuit, perturbations: &[Perturbation]) -> Vec<SEntropy> {
    let n = circuit.num_nodes();
    if n == 0 {
        return Vec::new();
    }

    let (mu_min, mu_max) = circuit.nodes.iter().fold((f64::MAX, f64::MIN), |(mn, mx), node| {
        (mn.min(node.mu), mx.max(node.mu))
    });
    let mu_range = mu_max - mu_min;

    let mut node_flux = vec![0.0_f64; n];
    let mut node_degree = vec![0.0_f64; n];

    for edge in &circuit.edges {
        let factor = perturbations
            .iter()
            .find(|p| p.edge_idx == edge.id)
            .map(|p| p.factor)
            .unwrap_or(1.0);

        let g = edge.conductance * factor;
        let flux = g * (circuit.nodes[edge.src].mu - circuit.nodes[edge.dst].mu).abs();

        node_flux[edge.src] += flux;
        node_flux[edge.dst] += flux;
        node_degree[edge.src] += g;
        node_degree[edge.dst] += g;
    }

    let flux_max = node_flux.iter().cloned().fold(0.0_f64, f64::max);
    let degree_max = node_degree.iter().cloned().fold(0.0_f64, f64::max);

    circuit
        .nodes
        .iter()
        .enumerate()
        .map(|(i, node)| {
            let se = if mu_range > 0.0 {
                (node.mu - mu_min) / mu_range
            } else {
                0.0
            };
            let sk = if flux_max > 0.0 {
                node_flux[i] / flux_max
            } else {
                0.0
            };
            let st = if degree_max > 0.0 {
                node_degree[i] / degree_max
            } else {
                0.0
            };
            SEntropy::new(se, sk, st)
        })
        .collect()
}

pub fn compute_flux_pattern(circuit: &Circuit, perturbations: &[Perturbation]) -> Vec<f64> {
    circuit
        .edges
        .iter()
        .map(|edge| {
            let factor = perturbations
                .iter()
                .find(|p| p.edge_idx == edge.id)
                .map(|p| p.factor)
                .unwrap_or(1.0);

            let g = edge.conductance * factor;
            g * (circuit.nodes[edge.src].mu - circuit.nodes[edge.dst].mu).abs()
        })
        .collect()
}
