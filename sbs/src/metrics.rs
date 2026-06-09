use serde::{Deserialize, Serialize};

use crate::circuit::{Circuit, Perturbation};
use crate::entropy::{compute_flux_pattern, compute_s_entropy, SEntropy};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Metrics {
    pub r: Coherence,
    pub v: FluxVisibility,
    pub s_entropy: Vec<SEntropy>,
    pub flux_healthy: Vec<f64>,
    pub flux_current: Vec<f64>,
    pub backward_path: Vec<usize>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct Coherence {
    pub value: f64,
    pub rho_ek: f64,
    pub rho_et: f64,
    pub rho_kt: f64,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct FluxVisibility {
    pub value: f64,
}

pub fn extract_metrics(circuit: &Circuit, perturbations: &[Perturbation]) -> Metrics {
    let s_entropy = compute_s_entropy(circuit, perturbations);
    let flux_healthy = compute_flux_pattern(circuit, &[]);
    let flux_current = compute_flux_pattern(circuit, perturbations);

    let r = triple_coherence(&s_entropy);
    let v = flux_visibility(&flux_healthy, &flux_current);
    let backward_path = compute_backward_navigation(circuit, perturbations);

    Metrics {
        r,
        v,
        s_entropy,
        flux_healthy,
        flux_current,
        backward_path,
    }
}

pub fn triple_coherence(entropy: &[SEntropy]) -> Coherence {
    if entropy.len() < 2 {
        return Coherence {
            value: 1.0,
            rho_ek: 1.0,
            rho_et: 1.0,
            rho_kt: 1.0,
        };
    }

    let se: Vec<f64> = entropy.iter().map(|s| s.se).collect();
    let sk: Vec<f64> = entropy.iter().map(|s| s.sk).collect();
    let st: Vec<f64> = entropy.iter().map(|s| s.st).collect();

    let rho_ek = spearman_rho(&se, &sk);
    let rho_et = spearman_rho(&se, &st);
    let rho_kt = spearman_rho(&sk, &st);

    let mean_rho = (rho_ek + rho_et + rho_kt) / 3.0;
    let value = (mean_rho + 1.0) / 2.0;

    Coherence {
        value,
        rho_ek,
        rho_et,
        rho_kt,
    }
}

pub fn flux_visibility(flux_healthy: &[f64], flux_current: &[f64]) -> FluxVisibility {
    if flux_healthy.is_empty() || flux_current.is_empty() {
        return FluxVisibility { value: 1.0 };
    }

    let total_healthy: f64 = flux_healthy.iter().map(|f| f.abs()).sum();
    if total_healthy < 1e-15 {
        return FluxVisibility { value: 1.0 };
    }

    let mut log_v = 0.0;
    for (h, c) in flux_healthy.iter().zip(flux_current.iter()) {
        let ha = h.abs().max(1e-30);
        let ca = c.abs().max(1e-30);
        let w = ha / total_healthy;
        let ratio = ha.min(ca) / ha.max(ca);
        log_v += w * ratio.ln();
    }

    FluxVisibility {
        value: log_v.exp(),
    }
}

pub fn compute_backward_navigation(
    circuit: &Circuit,
    perturbations: &[Perturbation],
) -> Vec<usize> {
    if circuit.nodes.is_empty() {
        return Vec::new();
    }

    let start = circuit
        .nodes
        .iter()
        .enumerate()
        .max_by(|(_, a), (_, b)| a.mu.partial_cmp(&b.mu).unwrap())
        .map(|(i, _)| i)
        .unwrap_or(0);

    let mut path = vec![start];
    let mut visited = vec![false; circuit.num_nodes()];
    visited[start] = true;
    let mut current = start;

    for _ in 0..circuit.num_nodes() {
        let mut best_next = None;
        let mut best_conductance = 0.0_f64;

        for edge in &circuit.edges {
            let factor = perturbations
                .iter()
                .find(|p| p.edge_idx == edge.id)
                .map(|p| p.factor)
                .unwrap_or(1.0);

            let g = edge.conductance * factor;

            if edge.dst == current && !visited[edge.src] && g > best_conductance {
                best_conductance = g;
                best_next = Some(edge.src);
            }
        }

        match best_next {
            Some(next) => {
                visited[next] = true;
                path.push(next);
                current = next;
            }
            None => break,
        }
    }

    path
}

pub fn find_optimal_perturbation(
    circuit: &Circuit,
    perturbations: &[Perturbation],
    max_edges: usize,
) -> Vec<Perturbation> {
    let flux_healthy = compute_flux_pattern(circuit, &[]);
    let flux_current = compute_flux_pattern(circuit, perturbations);

    let mut edge_impact: Vec<(usize, f64)> = circuit
        .edges
        .iter()
        .enumerate()
        .map(|(i, _)| {
            let h = flux_healthy[i].abs().max(1e-30);
            let c = flux_current[i].abs().max(1e-30);
            let ratio = h.min(c) / h.max(c);
            (i, 1.0 - ratio)
        })
        .collect();

    edge_impact.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());

    edge_impact
        .into_iter()
        .take(max_edges)
        .filter(|(_, impact)| *impact > 0.01)
        .map(|(idx, _)| Perturbation::new(idx, 1.0))
        .collect()
}

fn spearman_rho(x: &[f64], y: &[f64]) -> f64 {
    let n = x.len();
    if n < 2 {
        return 1.0;
    }

    let rank_x = ranks(x);
    let rank_y = ranks(y);

    let mean_rx: f64 = rank_x.iter().sum::<f64>() / n as f64;
    let mean_ry: f64 = rank_y.iter().sum::<f64>() / n as f64;

    let mut cov = 0.0;
    let mut var_x = 0.0;
    let mut var_y = 0.0;

    for i in 0..n {
        let dx = rank_x[i] - mean_rx;
        let dy = rank_y[i] - mean_ry;
        cov += dx * dy;
        var_x += dx * dx;
        var_y += dy * dy;
    }

    if var_x < 1e-15 || var_y < 1e-15 {
        return 0.0;
    }

    cov / (var_x * var_y).sqrt()
}

fn ranks(values: &[f64]) -> Vec<f64> {
    let n = values.len();
    let mut indexed: Vec<(usize, f64)> = values.iter().copied().enumerate().collect();
    indexed.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap());

    let mut result = vec![0.0; n];
    let mut i = 0;
    while i < n {
        let mut j = i;
        while j < n - 1 && (indexed[j + 1].1 - indexed[j].1).abs() < 1e-15 {
            j += 1;
        }
        let rank = (i + j) as f64 / 2.0 + 1.0;
        for k in i..=j {
            result[indexed[k].0] = rank;
        }
        i = j + 1;
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::circuit::Circuit;

    #[test]
    fn test_glycolysis_coherence() {
        let circuit = Circuit::demo_glycolysis();
        let metrics = extract_metrics(&circuit, &[]);
        assert!(metrics.r.value > 0.0 && metrics.r.value <= 1.0);
        assert!((metrics.v.value - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_perturbation_reduces_visibility() {
        let circuit = Circuit::demo_glycolysis();
        let pert = vec![Perturbation::new(0, 0.1)];
        let metrics = extract_metrics(&circuit, &pert);
        assert!(metrics.v.value < 1.0);
    }

    #[test]
    fn test_backward_navigation() {
        let circuit = Circuit::demo_glycolysis();
        let path = compute_backward_navigation(&circuit, &[]);
        assert!(!path.is_empty());
    }
}
