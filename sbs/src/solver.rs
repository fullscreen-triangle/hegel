use crate::circuit::{Circuit, Perturbation};
use crate::entropy::{compute_s_entropy, SEntropy};
use crate::metrics::{extract_metrics, Metrics};

pub struct Solver {
    circuit: Circuit,
    perturbations: Vec<Perturbation>,
}

impl Solver {
    pub fn new(circuit: Circuit) -> Self {
        Self {
            circuit,
            perturbations: Vec::new(),
        }
    }

    pub fn with_perturbations(mut self, perturbations: Vec<Perturbation>) -> Self {
        self.perturbations = perturbations;
        self
    }

    pub fn add_perturbation(&mut self, edge_idx: usize, factor: f64) {
        self.perturbations.push(Perturbation::new(edge_idx, factor));
    }

    pub fn clear_perturbations(&mut self) {
        self.perturbations.clear();
    }

    pub fn solve(&self) -> SolverResult {
        let start = std::time::Instant::now();
        let s_entropy = compute_s_entropy(&self.circuit, &self.perturbations);
        let metrics = extract_metrics(&self.circuit, &self.perturbations);
        let elapsed = start.elapsed();

        SolverResult {
            s_entropy,
            metrics,
            compute_time_us: elapsed.as_micros() as u64,
            backend: "cpu".to_string(),
        }
    }

    pub fn circuit(&self) -> &Circuit {
        &self.circuit
    }

    pub fn perturbations(&self) -> &[Perturbation] {
        &self.perturbations
    }
}

#[derive(Debug, Clone)]
pub struct SolverResult {
    pub s_entropy: Vec<SEntropy>,
    pub metrics: Metrics,
    pub compute_time_us: u64,
    pub backend: String,
}

impl SolverResult {
    pub fn coherence(&self) -> f64 {
        self.metrics.r.value
    }

    pub fn visibility(&self) -> f64 {
        self.metrics.v.value
    }

    pub fn summary(&self) -> String {
        format!(
            "R={:.4} V={:.4} nodes={} time={}μs backend={}",
            self.coherence(),
            self.visibility(),
            self.s_entropy.len(),
            self.compute_time_us,
            self.backend,
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::circuit::Circuit;

    #[test]
    fn test_solver_healthy() {
        let solver = Solver::new(Circuit::demo_glycolysis());
        let result = solver.solve();
        assert_eq!(result.s_entropy.len(), 10);
        assert!(result.coherence() > 0.0);
        assert!((result.visibility() - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_solver_perturbed() {
        let mut solver = Solver::new(Circuit::demo_glycolysis());
        solver.add_perturbation(0, 0.1);
        let result = solver.solve();
        assert!(result.visibility() < 1.0);
    }
}
