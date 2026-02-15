//! Categorical Primitives
//!
//! The three fundamental operations of categorical computing:
//! - Project: Map continuous to categorical (replaces Boolean AND)
//! - Complete: Find valid trajectories (replaces Boolean OR)
//! - Compose: Chain morphisms (replaces Boolean NOT through complement)
//!
//! These primitives replace Boolean operations because categorical
//! structure preserves physics while Boolean logic destroys it.

use crate::constraints::ConstraintSet;
use crate::s_entropy::SEntropyCoordinate;
use crate::ternary::TritString;
use crate::completion::{BackwardCompletion, CompletionResult};

/// Project: Map continuous state to categorical representation
///
/// This is the fundamental operation that converts physical observables
/// to categorical structure. The projection preserves the essential
/// information while discarding irrelevant details.
///
/// S_k, S_t, S_e -> trit sequence
pub fn project(coord: &SEntropyCoordinate, depth: usize) -> TritString {
    let mut trits = Vec::with_capacity(depth);
    let mut current = *coord;

    for _ in 0..depth {
        // Determine dominant axis
        let trit = current.to_trit();
        trits.push(trit);

        // Refine for next level (subdivide the dominant partition)
        current = match trit {
            0 => SEntropyCoordinate::new(
                (current.s_k * 3.0) % 1.0,
                current.s_t,
                current.s_e,
            ),
            1 => SEntropyCoordinate::new(
                current.s_k,
                (current.s_t * 3.0) % 1.0,
                current.s_e,
            ),
            _ => SEntropyCoordinate::new(
                current.s_k,
                current.s_t,
                (current.s_e * 3.0) % 1.0,
            ),
        };
    }

    TritString::from_vec(trits).unwrap()
}

/// Complete: Find all valid trajectories between boundary conditions
///
/// This is the core operation of Poincaré computing. Given initial
/// and final states plus constraints, find all valid trajectories.
///
/// Complexity: O(k × m) where k = length, m = constraints
pub fn complete(
    initial: &TritString,
    final_state: &TritString,
    constraints: ConstraintSet,
    target_length: usize,
) -> Vec<CompletionResult> {
    let mut completer = BackwardCompletion::new(constraints, target_length);
    completer.complete(initial, final_state, Some(target_length))
}

/// Compose: Chain two categorical morphisms
///
/// Given trajectories A→B and B→C, produce trajectory A→C.
/// This preserves categorical structure through composition.
pub fn compose(first: &TritString, second: &TritString) -> TritString {
    // Find overlap region
    let first_len = first.len();
    let second_len = second.len();

    // Try to find matching suffix of first with prefix of second
    for overlap in (1..=first_len.min(second_len)).rev() {
        let first_suffix = first.substring(first_len - overlap, first_len);
        let second_prefix = second.substring(0, overlap);

        if first_suffix == second_prefix {
            // Found overlap - compose by concatenating without duplicate
            let second_remainder = second.substring(overlap, second_len);
            return first.concat(&second_remainder);
        }
    }

    // No overlap found - simple concatenation
    first.concat(second)
}

/// Invert: Find the categorical complement
///
/// For trajectory T with pattern P, find trajectories without P.
/// This replaces Boolean NOT with categorical complement.
pub fn complement_pattern(pattern: &str) -> String {
    // Generate the "opposite" pattern by flipping each trit
    pattern
        .chars()
        .map(|c| match c {
            '0' => '2',
            '2' => '0',
            _ => c, // '1' stays as '1'
        })
        .collect()
}

/// Intersection: Find trajectories satisfying both constraint sets
///
/// This is categorical AND - find trajectories valid under both sets.
pub fn intersect(
    initial: &TritString,
    final_state: &TritString,
    constraints1: ConstraintSet,
    constraints2: ConstraintSet,
    target_length: usize,
) -> Vec<TritString> {
    // Complete under first constraints
    let results1 = complete(initial, final_state, constraints1, target_length);

    // Filter by second constraints
    results1
        .into_iter()
        .filter(|r| constraints2.satisfied(&r.trajectory))
        .map(|r| r.trajectory)
        .collect()
}

/// Union: Find trajectories satisfying either constraint set
///
/// This is categorical OR - find trajectories valid under either set.
pub fn union(
    initial: &TritString,
    final_state: &TritString,
    constraints1: ConstraintSet,
    constraints2: ConstraintSet,
    target_length: usize,
) -> Vec<TritString> {
    let results1 = complete(initial, final_state, constraints1, target_length);
    let results2 = complete(initial, final_state, constraints2, target_length);

    // Combine and deduplicate
    let mut all: Vec<TritString> = results1.into_iter().map(|r| r.trajectory).collect();
    for r in results2 {
        if !all.contains(&r.trajectory) {
            all.push(r.trajectory);
        }
    }

    all
}

/// Restrict: Filter trajectories to those passing through aperture
pub fn restrict(
    trajectories: &[TritString],
    aperture_pattern: &str,
) -> Vec<TritString> {
    trajectories
        .iter()
        .filter(|t| t.contains_pattern(aperture_pattern))
        .cloned()
        .collect()
}

/// Extend: Extend a trajectory by one trit in all valid directions
pub fn extend(trajectory: &TritString) -> Vec<TritString> {
    (0..3u8)
        .map(|trit| {
            let mut extended = trajectory.clone();
            extended.push(trit).unwrap();
            extended
        })
        .collect()
}

/// Truncate: Remove the last trit from a trajectory
pub fn truncate(trajectory: &TritString) -> Option<TritString> {
    if trajectory.is_empty() {
        return None;
    }
    Some(trajectory.substring(0, trajectory.len() - 1))
}

/// Reverse: Reverse a trajectory (for backward analysis)
pub fn reverse(trajectory: &TritString) -> TritString {
    let trits: Vec<u8> = trajectory.as_slice().iter().copied().rev().collect();
    TritString::from_vec(trits).unwrap()
}

/// Map: Apply a transformation to each trit
pub fn map_trits<F>(trajectory: &TritString, f: F) -> TritString
where
    F: Fn(u8) -> u8,
{
    let trits: Vec<u8> = trajectory.as_slice().iter().map(|&t| f(t) % 3).collect();
    TritString::from_vec(trits).unwrap()
}

/// Rotate: Cycle trit values (0→1→2→0)
pub fn rotate(trajectory: &TritString) -> TritString {
    map_trits(trajectory, |t| (t + 1) % 3)
}

/// Reflect: Reflect trit values (0↔2, 1→1)
pub fn reflect(trajectory: &TritString) -> TritString {
    map_trits(trajectory, |t| 2 - t)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constraints::ApertureConstraint;

    #[test]
    fn test_project() {
        let coord = SEntropyCoordinate::new(0.8, 0.1, 0.1);
        let projected = project(&coord, 3);

        // Knowledge axis dominant, should start with 0
        assert_eq!(projected.get(0), Some(0));
    }

    #[test]
    fn test_compose() {
        let first = TritString::new("012").unwrap();
        let second = TritString::new("120").unwrap();

        let composed = compose(&first, &second);
        // Should find overlap "12" and compose: "012" + "0" = "0120"
        assert_eq!(composed.to_string_repr(), "0120");
    }

    #[test]
    fn test_compose_no_overlap() {
        let first = TritString::new("000").unwrap();
        let second = TritString::new("111").unwrap();

        let composed = compose(&first, &second);
        assert_eq!(composed.to_string_repr(), "000111");
    }

    #[test]
    fn test_complement() {
        let pattern = "012";
        let complement = complement_pattern(pattern);
        assert_eq!(complement, "210");
    }

    #[test]
    fn test_reverse() {
        let traj = TritString::new("012").unwrap();
        let reversed = reverse(&traj);
        assert_eq!(reversed.to_string_repr(), "210");
    }

    #[test]
    fn test_rotate() {
        let traj = TritString::new("012").unwrap();
        let rotated = rotate(&traj);
        assert_eq!(rotated.to_string_repr(), "120");
    }

    #[test]
    fn test_reflect() {
        let traj = TritString::new("012").unwrap();
        let reflected = reflect(&traj);
        assert_eq!(reflected.to_string_repr(), "210");
    }

    #[test]
    fn test_extend() {
        let traj = TritString::new("01").unwrap();
        let extended = extend(&traj);

        assert_eq!(extended.len(), 3);
        assert_eq!(extended[0].to_string_repr(), "010");
        assert_eq!(extended[1].to_string_repr(), "011");
        assert_eq!(extended[2].to_string_repr(), "012");
    }

    #[test]
    fn test_truncate() {
        let traj = TritString::new("012").unwrap();
        let truncated = truncate(&traj).unwrap();
        assert_eq!(truncated.to_string_repr(), "01");
    }

    #[test]
    fn test_restrict() {
        let trajectories = vec![
            TritString::new("012012").unwrap(),
            TritString::new("000111").unwrap(),
            TritString::new("012000").unwrap(),
        ];

        let restricted = restrict(&trajectories, "012");
        assert_eq!(restricted.len(), 2);
    }
}
