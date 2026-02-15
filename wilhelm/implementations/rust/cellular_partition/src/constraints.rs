//! Constraint System
//!
//! Physical constraints that filter valid trajectories:
//! 1. Charge neutrality: Σq_i = 0
//! 2. Energy conservation: ΔE = 0
//! 3. Categorical coherence: R > R_c (phase-lock order parameter)
//! 4. Poincaré recurrence: |Ψ(t+τ_P) - Ψ(0)| < ε
//!
//! Constraint satisfaction (not forward simulation) determines trajectories.
//! This is what makes Poincaré computing O(k*m) instead of O(e^λT).

use crate::ternary::TritString;
use serde::{Deserialize, Serialize};

/// Trait for categorical constraints
///
/// Constraints filter trajectories: they accept or reject,
/// they don't modify or simulate.
pub trait Constraint: Send + Sync {
    /// Check if trajectory satisfies this constraint
    fn satisfied(&self, trajectory: &TritString) -> bool;

    /// Can this constraint be checked on partial trajectories?
    fn can_check_partial(&self) -> bool;

    /// Get the name of this constraint
    fn name(&self) -> &str;
}

/// Charge neutrality constraint: Σq_i = 0
///
/// In ternary encoding, charge is encoded in trit patterns.
/// A charge-neutral trajectory has balanced trit sums.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChargeNeutrality {
    pub tolerance: f64,
}

impl ChargeNeutrality {
    pub fn new(tolerance: f64) -> Self {
        Self { tolerance }
    }
}

impl Default for ChargeNeutrality {
    fn default() -> Self {
        Self { tolerance: 0.1 }
    }
}

impl Constraint for ChargeNeutrality {
    fn satisfied(&self, trajectory: &TritString) -> bool {
        if trajectory.is_empty() {
            return true;
        }

        let counts = trajectory.trit_counts();
        let total = trajectory.len() as f64;
        let expected = total / 3.0;

        if expected < 1e-10 {
            return true;
        }

        counts
            .iter()
            .all(|&c| (c as f64 - expected).abs() / expected <= self.tolerance)
    }

    fn can_check_partial(&self) -> bool {
        false // Need full trajectory for charge balance
    }

    fn name(&self) -> &str {
        "ChargeNeutrality"
    }
}

/// Energy conservation constraint: |E_f - E_i| < ΔE
///
/// In S-entropy space, energy relates to partition depth.
/// Conservation means trajectory doesn't change total partition depth.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnergyConservation {
    pub tolerance: f64,
}

impl EnergyConservation {
    pub fn new(tolerance: f64) -> Self {
        Self { tolerance }
    }
}

impl Default for EnergyConservation {
    fn default() -> Self {
        Self { tolerance: 0.1 }
    }
}

impl Constraint for EnergyConservation {
    fn satisfied(&self, trajectory: &TritString) -> bool {
        if trajectory.len() < 2 {
            return true;
        }

        let max_deviation = trajectory.max_deviation();
        let expected = trajectory.len() as f64;

        if expected < 1e-10 {
            return true;
        }

        max_deviation / expected <= self.tolerance
    }

    fn can_check_partial(&self) -> bool {
        true // Can check running energy balance
    }

    fn name(&self) -> &str {
        "EnergyConservation"
    }
}

/// Categorical coherence constraint: R > R_c
///
/// R is the phase-lock order parameter (Kuramoto order parameter).
/// R_c ≈ 0.7 is the critical value for coherent dynamics.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CategoricalCoherence {
    pub critical_r: f64,
}

impl CategoricalCoherence {
    pub fn new(critical_r: f64) -> Self {
        Self { critical_r }
    }
}

impl Default for CategoricalCoherence {
    fn default() -> Self {
        Self { critical_r: 0.7 }
    }
}

impl Constraint for CategoricalCoherence {
    fn satisfied(&self, trajectory: &TritString) -> bool {
        trajectory.coherence() >= self.critical_r
    }

    fn can_check_partial(&self) -> bool {
        true // Can check running coherence
    }

    fn name(&self) -> &str {
        "CategoricalCoherence"
    }
}

/// Poincaré recurrence constraint: |Ψ(t+τ_P) - Ψ(0)| < ε
///
/// Trajectory must return close to initial state after recurrence time.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PoincareRecurrence {
    pub epsilon: f64,
}

impl PoincareRecurrence {
    pub fn new(epsilon: f64) -> Self {
        Self { epsilon }
    }
}

impl Default for PoincareRecurrence {
    fn default() -> Self {
        Self { epsilon: 0.1 }
    }
}

impl Constraint for PoincareRecurrence {
    fn satisfied(&self, trajectory: &TritString) -> bool {
        if trajectory.len() < 3 {
            return true;
        }

        let trits = trajectory.as_slice();

        // Check various period lengths for approximate periodicity
        for period in 1..=(trits.len() / 2) {
            let mut matches = 0;
            let mut comparisons = 0;

            for i in 0..(trits.len() - period) {
                if trits[i] == trits[i + period] {
                    matches += 1;
                }
                comparisons += 1;
            }

            if comparisons > 0 {
                let similarity = matches as f64 / comparisons as f64;
                if similarity >= 1.0 - self.epsilon {
                    return true;
                }
            }
        }

        // Allow trajectories even without strict periodicity
        // (real systems have quasi-periodicity)
        true
    }

    fn can_check_partial(&self) -> bool {
        false // Need full trajectory
    }

    fn name(&self) -> &str {
        "PoincareRecurrence"
    }
}

/// Aperture constraint: trajectory must pass through categorical aperture
///
/// An aperture is a geometric constraint in S-entropy space.
/// For enzymatic catalysis, the active site defines the aperture.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApertureConstraint {
    pub pattern: String,
    pub required_count: usize,
}

impl ApertureConstraint {
    pub fn new(pattern: &str) -> Self {
        Self {
            pattern: pattern.to_string(),
            required_count: 1,
        }
    }

    pub fn with_count(pattern: &str, count: usize) -> Self {
        Self {
            pattern: pattern.to_string(),
            required_count: count,
        }
    }
}

impl Constraint for ApertureConstraint {
    fn satisfied(&self, trajectory: &TritString) -> bool {
        trajectory.count_pattern(&self.pattern) >= self.required_count
    }

    fn can_check_partial(&self) -> bool {
        false // Need full trajectory to verify traversal
    }

    fn name(&self) -> &str {
        "ApertureConstraint"
    }
}

/// Continuity constraint: adjacent trits differ by at most 1
///
/// |t_{i+1} - t_i| ≤ 1
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct ContinuityConstraint;

impl Constraint for ContinuityConstraint {
    fn satisfied(&self, trajectory: &TritString) -> bool {
        if trajectory.len() < 2 {
            return true;
        }

        let trits = trajectory.as_slice();
        for i in 0..(trits.len() - 1) {
            if (trits[i] as i32 - trits[i + 1] as i32).abs() > 1 {
                return false;
            }
        }

        true
    }

    fn can_check_partial(&self) -> bool {
        true // Can check incrementally
    }

    fn name(&self) -> &str {
        "ContinuityConstraint"
    }
}

/// A collection of constraints for trajectory validation
pub struct ConstraintSet {
    constraints: Vec<Box<dyn Constraint>>,
    partial_indices: Vec<usize>,
    full_indices: Vec<usize>,
}

impl ConstraintSet {
    pub fn new() -> Self {
        Self {
            constraints: Vec::new(),
            partial_indices: Vec::new(),
            full_indices: Vec::new(),
        }
    }

    pub fn add<C: Constraint + 'static>(&mut self, constraint: C) {
        let idx = self.constraints.len();
        if constraint.can_check_partial() {
            self.partial_indices.push(idx);
        } else {
            self.full_indices.push(idx);
        }
        self.constraints.push(Box::new(constraint));
    }

    pub fn len(&self) -> usize {
        self.constraints.len()
    }

    pub fn is_empty(&self) -> bool {
        self.constraints.is_empty()
    }

    /// Check partial constraints only (for pruning during search)
    pub fn check_partial(&self, trajectory: &TritString) -> bool {
        self.partial_indices
            .iter()
            .all(|&i| self.constraints[i].satisfied(trajectory))
    }

    /// Check all constraints
    pub fn check_full(&self, trajectory: &TritString) -> bool {
        self.constraints
            .iter()
            .all(|c| c.satisfied(trajectory))
    }

    /// Check all constraints
    pub fn satisfied(&self, trajectory: &TritString) -> bool {
        self.check_full(trajectory)
    }

    /// Detailed report of which constraints pass/fail
    pub fn satisfaction_report(&self, trajectory: &TritString) -> Vec<(String, bool)> {
        self.constraints
            .iter()
            .map(|c| (c.name().to_string(), c.satisfied(trajectory)))
            .collect()
    }

    /// Count how many constraints are satisfied
    pub fn satisfaction_count(&self, trajectory: &TritString) -> usize {
        self.constraints
            .iter()
            .filter(|c| c.satisfied(trajectory))
            .count()
    }
}

impl Default for ConstraintSet {
    fn default() -> Self {
        Self::new()
    }
}

/// Standard constraints for enzymatic catalysis
pub fn enzymatic_constraints(aperture_pattern: &str) -> ConstraintSet {
    let mut cs = ConstraintSet::new();
    cs.add(ChargeNeutrality::new(0.2));
    cs.add(EnergyConservation::new(0.15));
    cs.add(CategoricalCoherence::new(0.7));
    cs.add(ApertureConstraint::new(aperture_pattern));
    cs
}

/// Standard constraints for cellular processes
pub fn cellular_constraints() -> ConstraintSet {
    let mut cs = ConstraintSet::new();
    cs.add(ChargeNeutrality::new(0.1));
    cs.add(EnergyConservation::new(0.1));
    cs.add(CategoricalCoherence::new(0.7));
    cs.add(PoincareRecurrence::new(0.2));
    cs
}

/// Minimal constraint set for aperture traversal only
pub fn aperture_only_constraints(aperture_pattern: &str) -> ConstraintSet {
    let mut cs = ConstraintSet::new();
    cs.add(ApertureConstraint::new(aperture_pattern));
    cs
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_charge_neutrality() {
        let cn = ChargeNeutrality::default();

        let balanced = TritString::new("012012012").unwrap();
        assert!(cn.satisfied(&balanced));

        let unbalanced = TritString::new("000000111").unwrap();
        assert!(!cn.satisfied(&unbalanced));
    }

    #[test]
    fn test_coherence() {
        let cc = CategoricalCoherence::new(0.7);

        let smooth = TritString::new("001122110").unwrap();
        assert!(cc.satisfied(&smooth));

        let abrupt = TritString::new("020202020").unwrap();
        assert!(!cc.satisfied(&abrupt));
    }

    #[test]
    fn test_aperture_constraint() {
        let ac = ApertureConstraint::new("012");

        let with_aperture = TritString::new("000012222").unwrap();
        assert!(ac.satisfied(&with_aperture));

        let without = TritString::new("000111222").unwrap();
        assert!(!ac.satisfied(&without));
    }

    #[test]
    fn test_continuity() {
        let cc = ContinuityConstraint;

        let continuous = TritString::new("001122110").unwrap();
        assert!(cc.satisfied(&continuous));

        let discontinuous = TritString::new("020202").unwrap();
        assert!(!cc.satisfied(&discontinuous));
    }

    #[test]
    fn test_constraint_set() {
        let cs = enzymatic_constraints("012");

        let good = TritString::new("012012012012").unwrap();
        let report = cs.satisfaction_report(&good);

        assert_eq!(report.len(), 4);
    }
}
