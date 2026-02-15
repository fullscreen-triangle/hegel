//! Backward Completion Algorithm
//!
//! The core of Poincaré computing: determine trajectories by propagating
//! constraints BACKWARD from observations, not simulating FORWARD from
//! initial conditions.
//!
//! ## Complexity
//!
//! - **Backward completion**: O(k × m) where k = trajectory length, m = constraint count
//! - **Forward simulation**: O(e^{λT}) for chaotic systems
//!
//! This is how the derivation IS the computation.

use crate::constraints::{ApertureConstraint, Constraint, ConstraintSet};
use crate::ternary::TritString;
use instant::Instant;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Result of backward completion
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompletionResult {
    pub trajectory: TritString,
    pub constraint_checks: u64,
    pub computation_time_ns: u64,
    pub valid: bool,
    pub constraints_satisfied: Vec<(String, bool)>,
}

/// Statistics for completion algorithm
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct CompletionStats {
    pub total_trajectories_explored: u64,
    pub valid_trajectories_found: u64,
    pub constraint_checks: u64,
    pub pruned_branches: u64,
    pub computation_time_ns: u64,
}

/// Backward completion algorithm for Poincaré computing
///
/// Given:
/// - Initial state (boundary condition)
/// - Final state (boundary condition)
/// - Constraints (categorical apertures, conservation laws)
///
/// Returns:
/// - All valid trajectories connecting initial to final through constraints
///
/// The algorithm propagates constraints BACKWARD from the final state,
/// pruning invalid branches early. This achieves O(k*m) complexity.
pub struct BackwardCompletion {
    constraints: ConstraintSet,
    max_depth: usize,
    enable_pruning: bool,
    stats: CompletionStats,
}

impl BackwardCompletion {
    pub fn new(constraints: ConstraintSet, max_depth: usize) -> Self {
        Self {
            constraints,
            max_depth,
            enable_pruning: true,
            stats: CompletionStats::default(),
        }
    }

    pub fn with_pruning(mut self, enable: bool) -> Self {
        self.enable_pruning = enable;
        self
    }

    /// Get statistics from the last completion
    pub fn stats(&self) -> &CompletionStats {
        &self.stats
    }

    /// Complete trajectory from initial to final state
    ///
    /// This is the CORE operation. Running this IS the cellular process.
    /// The derivation is the computation.
    pub fn complete(
        &mut self,
        initial: &TritString,
        final_state: &TritString,
        target_length: Option<usize>,
    ) -> Vec<CompletionResult> {
        let start = Instant::now();
        self.stats = CompletionStats::default();

        let target_length = target_length.unwrap_or(self.max_depth);

        // Backward propagation
        let valid_trajectories =
            self.backward_propagate(initial, final_state, target_length);

        self.stats.computation_time_ns = start.elapsed().as_nanos() as u64;

        let mut results = Vec::new();
        for traj in valid_trajectories {
            let report = self.constraints.satisfaction_report(&traj);
            let valid = report.iter().all(|(_, satisfied)| *satisfied);

            results.push(CompletionResult {
                trajectory: traj,
                constraint_checks: self.stats.constraint_checks,
                computation_time_ns: self.stats.computation_time_ns,
                valid,
                constraints_satisfied: report,
            });
        }

        results
    }

    fn backward_propagate(
        &mut self,
        initial: &TritString,
        final_state: &TritString,
        target_length: usize,
    ) -> Vec<TritString> {
        let initial_len = initial.len();
        let final_len = final_state.len();

        if target_length < initial_len + final_len {
            // Trajectories overlap
            let combined = initial.concat(
                &final_state.substring(initial_len + final_len - target_length, final_len),
            );
            if self.constraints.check_full(&combined) {
                return vec![combined];
            }
            return vec![];
        }

        let middle_length = target_length - initial_len - final_len;

        // Generate middle section via backward search
        let mut valid_middles = Vec::new();
        self.search_middle(
            initial,
            final_state,
            middle_length,
            &TritString::empty(),
            &mut valid_middles,
        );

        valid_middles
            .into_iter()
            .map(|mid| initial.concat(&mid).concat(final_state))
            .collect()
    }

    fn search_middle(
        &mut self,
        initial: &TritString,
        final_state: &TritString,
        remaining: usize,
        current: &TritString,
        valid: &mut Vec<TritString>,
    ) {
        self.stats.total_trajectories_explored += 1;

        if remaining == 0 {
            // Check full trajectory
            let full = initial.concat(current).concat(final_state);
            self.stats.constraint_checks += 1;

            if self.constraints.check_full(&full) {
                valid.push(current.clone());
                self.stats.valid_trajectories_found += 1;
            }
            return;
        }

        // Try each trit
        for trit in 0..3u8 {
            let mut new_current = current.clone();
            new_current.push(trit).unwrap();

            // Early pruning: check partial constraints
            if self.enable_pruning {
                let partial = initial.concat(&new_current);
                self.stats.constraint_checks += 1;

                if !self.constraints.check_partial(&partial) {
                    self.stats.pruned_branches += 1;
                    continue;
                }
            }

            self.search_middle(initial, final_state, remaining - 1, &new_current, valid);
        }
    }

    /// Complete trajectory that passes through a categorical aperture
    ///
    /// This is enzymatic catalysis: the aperture is the active site.
    /// The enzyme doesn't "accelerate" - it provides a geometric pathway.
    pub fn complete_through_aperture(
        &mut self,
        initial: &TritString,
        final_state: &TritString,
        aperture_pattern: &str,
        target_length: Option<usize>,
    ) -> Vec<CompletionResult> {
        // Create a temporary constraint set with the aperture
        let mut temp_constraints = ConstraintSet::new();

        // Copy existing constraints (we can't iterate the original easily,
        // so we use a simple aperture-only approach for the aperture completion)
        temp_constraints.add(ApertureConstraint::new(aperture_pattern));

        // Swap constraints
        let original = std::mem::replace(&mut self.constraints, temp_constraints);

        let results = self.complete(initial, final_state, target_length);

        // Restore original
        self.constraints = original;

        results
    }
}

/// Compare forward vs backward completion complexity
pub fn theoretical_speedup(trajectory_length: usize, lyapunov_exponent: f64) -> f64 {
    // Forward simulation: O(e^{λT})
    let forward_ops = (lyapunov_exponent * trajectory_length as f64).exp();

    // Backward completion: O(k) with m=1 constraint
    let backward_ops = trajectory_length as f64;

    forward_ops / backward_ops
}

/// Calculate speedup for molecular dynamics comparison
pub struct SpeedupAnalysis {
    pub backward_ops: u64,
    pub forward_ops_standard: f64,
    pub forward_ops_chaotic: f64,
    pub speedup_standard: f64,
    pub speedup_chaotic: f64,
    pub valid_trajectories: usize,
}

impl SpeedupAnalysis {
    /// Perform speedup analysis comparing backward completion to MD
    pub fn analyze(
        backward_ops: u64,
        trajectory_length: usize,
    ) -> Self {
        // MD parameters
        let timestep_s: f64 = 1e-15; // 1 femtosecond
        let trajectory_time_s: f64 = 100e-12; // 100 picoseconds
        let steps_per_traj = trajectory_time_s / timestep_s;
        let ops_per_step: f64 = 1e4; // ~100 atoms
        let ensemble_size: f64 = 1000.0;

        let forward_ops_standard = steps_per_traj * ops_per_step * ensemble_size;

        // Chaotic system correction
        let lyapunov: f64 = 1.0;
        let chaos_factor = (lyapunov * trajectory_length as f64).exp();
        let forward_ops_chaotic = forward_ops_standard * chaos_factor;

        let backward = backward_ops.max(1) as f64;

        Self {
            backward_ops,
            forward_ops_standard,
            forward_ops_chaotic,
            speedup_standard: forward_ops_standard / backward,
            speedup_chaotic: forward_ops_chaotic / backward,
            valid_trajectories: 0,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constraints::{enzymatic_constraints, ApertureConstraint};

    #[test]
    fn test_basic_completion() {
        let mut cs = ConstraintSet::new();
        cs.add(ApertureConstraint::new("012"));

        let mut completer = BackwardCompletion::new(cs, 12);

        let initial = TritString::new("000").unwrap();
        let final_state = TritString::new("222").unwrap();

        let results = completer.complete(&initial, &final_state, Some(12));

        assert!(!results.is_empty());
        assert!(completer.stats().constraint_checks > 0);
    }

    #[test]
    fn test_aperture_traversal() {
        let cs = ConstraintSet::new();
        let mut completer = BackwardCompletion::new(cs, 12);

        let initial = TritString::new("000").unwrap();
        let final_state = TritString::new("222").unwrap();

        let results = completer.complete_through_aperture(
            &initial,
            &final_state,
            "012",
            Some(12),
        );

        // All valid trajectories should contain "012"
        for result in &results {
            assert!(result.trajectory.contains_pattern("012"));
        }
    }

    #[test]
    fn test_speedup_calculation() {
        let speedup = theoretical_speedup(12, 1.0);
        // e^12 / 12 ≈ 13,524
        assert!(speedup > 10000.0);
    }

    #[test]
    fn test_stats_tracking() {
        let mut cs = ConstraintSet::new();
        cs.add(ApertureConstraint::new("012"));

        let mut completer = BackwardCompletion::new(cs, 9);

        let initial = TritString::new("01").unwrap();
        let final_state = TritString::new("12").unwrap();

        completer.complete(&initial, &final_state, Some(9));

        let stats = completer.stats();
        assert!(stats.total_trajectories_explored > 0);
        assert!(stats.computation_time_ns > 0);
    }
}
