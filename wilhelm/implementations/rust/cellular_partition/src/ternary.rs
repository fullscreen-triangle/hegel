//! Ternary Encoding System
//!
//! The fundamental data structure for categorical partitioning.
//!
//! ## Key Insight: Position-Trajectory Duality
//!
//! The ternary address IS the path. A TritString simultaneously encodes:
//! - Position in S-entropy space (the address)
//! - History of how that position was reached (the trajectory)
//!
//! This duality is why observation = computation = process.
//! There is no separate "state" and "dynamics" - they are identical.

use crate::s_entropy::SEntropyCoordinate;
use serde::{Deserialize, Serialize};

/// A string of trits (ternary digits: 0, 1, 2)
///
/// The trit values encode categorical axes:
/// - 0: Knowledge axis (S_k)
/// - 1: Temporal axis (S_t)
/// - 2: Evolution axis (S_e)
///
/// The sequence of trits IS the trajectory through S-entropy space.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct TritString {
    trits: Vec<u8>,
}

impl TritString {
    /// Create a new TritString from a string of '0', '1', '2' characters
    pub fn new(s: &str) -> Result<Self, TritStringError> {
        let trits: Result<Vec<u8>, _> = s
            .chars()
            .map(|c| match c {
                '0' => Ok(0),
                '1' => Ok(1),
                '2' => Ok(2),
                _ => Err(TritStringError::InvalidCharacter(c)),
            })
            .collect();

        Ok(Self { trits: trits? })
    }

    /// Create from a vector of u8 values (must be 0, 1, or 2)
    pub fn from_vec(v: Vec<u8>) -> Result<Self, TritStringError> {
        for &t in &v {
            if t > 2 {
                return Err(TritStringError::InvalidTrit(t));
            }
        }
        Ok(Self { trits: v })
    }

    /// Create an empty TritString
    pub fn empty() -> Self {
        Self { trits: Vec::new() }
    }

    /// Create a TritString of given length filled with a specific trit
    pub fn filled(trit: u8, length: usize) -> Result<Self, TritStringError> {
        if trit > 2 {
            return Err(TritStringError::InvalidTrit(trit));
        }
        Ok(Self {
            trits: vec![trit; length],
        })
    }

    /// Get the length of the trit string
    pub fn len(&self) -> usize {
        self.trits.len()
    }

    /// Check if empty
    pub fn is_empty(&self) -> bool {
        self.trits.is_empty()
    }

    /// Get a specific trit by index
    pub fn get(&self, index: usize) -> Option<u8> {
        self.trits.get(index).copied()
    }

    /// Get the underlying trits as a slice
    pub fn as_slice(&self) -> &[u8] {
        &self.trits
    }

    /// Convert to string representation
    pub fn to_string_repr(&self) -> String {
        self.trits
            .iter()
            .map(|&t| char::from_digit(t as u32, 10).unwrap())
            .collect()
    }

    /// Append a trit
    pub fn push(&mut self, trit: u8) -> Result<(), TritStringError> {
        if trit > 2 {
            return Err(TritStringError::InvalidTrit(trit));
        }
        self.trits.push(trit);
        Ok(())
    }

    /// Concatenate two TritStrings
    pub fn concat(&self, other: &TritString) -> Self {
        let mut result = self.trits.clone();
        result.extend_from_slice(&other.trits);
        Self { trits: result }
    }

    /// Get a substring
    pub fn substring(&self, start: usize, end: usize) -> Self {
        let end = end.min(self.trits.len());
        let start = start.min(end);
        Self {
            trits: self.trits[start..end].to_vec(),
        }
    }

    /// Calculate categorical distance to another TritString
    ///
    /// This is the Hamming distance weighted by trit difference.
    pub fn categorical_distance(&self, other: &TritString) -> usize {
        let len = self.len().max(other.len());
        let mut distance = 0;

        for i in 0..len {
            let t1 = self.get(i).unwrap_or(0);
            let t2 = other.get(i).unwrap_or(0);
            distance += (t1 as i32 - t2 as i32).unsigned_abs() as usize;
        }

        distance
    }

    /// Count occurrences of each trit
    pub fn trit_counts(&self) -> [usize; 3] {
        let mut counts = [0usize; 3];
        for &t in &self.trits {
            counts[t as usize] += 1;
        }
        counts
    }

    /// Check if the trit distribution is balanced
    pub fn is_balanced(&self, tolerance: f64) -> bool {
        if self.is_empty() {
            return true;
        }

        let counts = self.trit_counts();
        let expected = self.len() as f64 / 3.0;

        counts
            .iter()
            .all(|&c| (c as f64 - expected).abs() / expected <= tolerance)
    }

    /// Check if trajectory contains a specific pattern
    pub fn contains_pattern(&self, pattern: &str) -> bool {
        self.to_string_repr().contains(pattern)
    }

    /// Find all positions where a pattern occurs
    pub fn find_pattern(&self, pattern: &str) -> Vec<usize> {
        let s = self.to_string_repr();
        let mut positions = Vec::new();
        let mut start = 0;

        while let Some(pos) = s[start..].find(pattern) {
            positions.push(start + pos);
            start += pos + 1;
        }

        positions
    }

    /// Count non-overlapping occurrences of a pattern
    pub fn count_pattern(&self, pattern: &str) -> usize {
        let s = self.to_string_repr();
        let mut count = 0;
        let mut i = 0;

        while i <= s.len().saturating_sub(pattern.len()) {
            if &s[i..i + pattern.len()] == pattern {
                count += 1;
                i += pattern.len();
            } else {
                i += 1;
            }
        }

        count
    }

    /// Convert to S-entropy trajectory
    pub fn to_s_entropy_trajectory(&self) -> Vec<SEntropyCoordinate> {
        self.trits
            .iter()
            .map(|&t| SEntropyCoordinate::from_trit(t))
            .collect()
    }

    /// Check for abrupt transitions (|t[i+1] - t[i]| == 2)
    pub fn count_abrupt_transitions(&self) -> usize {
        if self.len() < 2 {
            return 0;
        }

        self.trits
            .windows(2)
            .filter(|w| (w[0] as i32 - w[1] as i32).abs() == 2)
            .count()
    }

    /// Calculate coherence parameter (Kuramoto order parameter analog)
    pub fn coherence(&self) -> f64 {
        if self.len() < 2 {
            return 1.0;
        }

        let abrupt = self.count_abrupt_transitions();
        let total = self.len() - 1;

        1.0 - (abrupt as f64 / total as f64)
    }

    /// Calculate cumulative trit sum (for energy-like quantities)
    pub fn cumulative_sum(&self) -> Vec<u32> {
        let mut sum = 0u32;
        self.trits
            .iter()
            .map(|&t| {
                sum += t as u32;
                sum
            })
            .collect()
    }

    /// Maximum deviation from expected cumulative sum
    pub fn max_deviation(&self) -> f64 {
        if self.is_empty() {
            return 0.0;
        }

        let cum_sum = self.cumulative_sum();
        let expected_per_step = 1.0; // Average trit value is 1

        cum_sum
            .iter()
            .enumerate()
            .map(|(i, &s)| (s as f64 - (i + 1) as f64 * expected_per_step).abs())
            .fold(0.0, f64::max)
    }
}

impl std::fmt::Display for TritString {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.to_string_repr())
    }
}

impl std::str::FromStr for TritString {
    type Err = TritStringError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        TritString::new(s)
    }
}

/// Errors that can occur when working with TritStrings
#[derive(Debug, Clone, PartialEq)]
pub enum TritStringError {
    InvalidCharacter(char),
    InvalidTrit(u8),
}

impl std::fmt::Display for TritStringError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            TritStringError::InvalidCharacter(c) => {
                write!(f, "Invalid character '{}' in trit string (must be 0, 1, or 2)", c)
            }
            TritStringError::InvalidTrit(t) => {
                write!(f, "Invalid trit value {} (must be 0, 1, or 2)", t)
            }
        }
    }
}

impl std::error::Error for TritStringError {}

/// A node in the ternary tree structure
#[derive(Debug, Clone)]
pub struct TernaryNode {
    pub address: TritString,
    pub depth: usize,
    pub children: [Option<Box<TernaryNode>>; 3],
}

impl TernaryNode {
    pub fn new(address: TritString) -> Self {
        let depth = address.len();
        Self {
            address,
            depth,
            children: [None, None, None],
        }
    }

    pub fn root() -> Self {
        Self::new(TritString::empty())
    }

    pub fn is_leaf(&self) -> bool {
        self.children.iter().all(|c| c.is_none())
    }

    /// Add a child at the specified trit position
    pub fn add_child(&mut self, trit: u8) -> &mut TernaryNode {
        let mut new_address = self.address.clone();
        new_address.push(trit).unwrap();

        self.children[trit as usize] = Some(Box::new(TernaryNode::new(new_address)));
        self.children[trit as usize].as_mut().unwrap()
    }
}

/// Ternary tree for trajectory enumeration
pub struct TernaryTree {
    pub root: TernaryNode,
    pub max_depth: usize,
}

impl TernaryTree {
    pub fn new(max_depth: usize) -> Self {
        Self {
            root: TernaryNode::root(),
            max_depth,
        }
    }

    /// Generate all possible TritStrings of a given length
    pub fn enumerate_all(length: usize) -> Vec<TritString> {
        if length == 0 {
            return vec![TritString::empty()];
        }

        let count = 3usize.pow(length as u32);
        let mut results = Vec::with_capacity(count);

        for i in 0..count {
            let mut trits = Vec::with_capacity(length);
            let mut n = i;

            for _ in 0..length {
                trits.push((n % 3) as u8);
                n /= 3;
            }

            trits.reverse();
            results.push(TritString::from_vec(trits).unwrap());
        }

        results
    }

    /// Count of all possible trajectories of given length
    pub fn trajectory_count(length: usize) -> usize {
        3usize.pow(length as u32)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_trit_string_creation() {
        let ts = TritString::new("012").unwrap();
        assert_eq!(ts.len(), 3);
        assert_eq!(ts.get(0), Some(0));
        assert_eq!(ts.get(1), Some(1));
        assert_eq!(ts.get(2), Some(2));
    }

    #[test]
    fn test_invalid_character() {
        let result = TritString::new("013");
        assert!(result.is_err());
    }

    #[test]
    fn test_categorical_distance() {
        let a = TritString::new("000").unwrap();
        let b = TritString::new("222").unwrap();
        assert_eq!(a.categorical_distance(&b), 6);

        let c = TritString::new("012").unwrap();
        assert_eq!(a.categorical_distance(&c), 3);
    }

    #[test]
    fn test_balanced() {
        let balanced = TritString::new("012012012").unwrap();
        assert!(balanced.is_balanced(0.1));

        let unbalanced = TritString::new("000000111").unwrap();
        assert!(!unbalanced.is_balanced(0.1));
    }

    #[test]
    fn test_pattern_search() {
        let ts = TritString::new("012012012").unwrap();
        assert!(ts.contains_pattern("012"));
        assert_eq!(ts.count_pattern("012"), 3);
    }

    #[test]
    fn test_coherence() {
        let smooth = TritString::new("001122").unwrap();
        assert!(smooth.coherence() >= 0.9);

        let abrupt = TritString::new("020202").unwrap();
        assert!(abrupt.coherence() < 0.5);
    }

    #[test]
    fn test_enumerate_all() {
        let all_2 = TernaryTree::enumerate_all(2);
        assert_eq!(all_2.len(), 9);
    }
}
