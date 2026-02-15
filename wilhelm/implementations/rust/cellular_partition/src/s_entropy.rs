//! S-Entropy Coordinate System
//!
//! S-entropy (S = kB M ln n) provides a natural coordinate system for
//! describing cellular processes through categorical partitions.
//!
//! The three axes encode:
//! - S_k: Knowledge entropy (what we know about the system)
//! - S_t: Temporal entropy (when the state occurs)
//! - S_e: Evolution entropy (rate of change)
//!
//! Key insight: Categorical distance is INDEPENDENT of spatial distance
//! and optical opacity. This is why observation = computation = process.

use serde::{Deserialize, Serialize};
use std::f64::consts::E;

/// Boltzmann constant in J/K
pub const K_B: f64 = 1.380649e-23;

/// S-entropy coordinate in the unit cube [0,1]³
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct SEntropyCoordinate {
    /// Knowledge entropy: what we know about the system state
    pub s_k: f64,
    /// Temporal entropy: when the state occurs in the process
    pub s_t: f64,
    /// Evolution entropy: rate of categorical change
    pub s_e: f64,
}

impl SEntropyCoordinate {
    /// Create a new S-entropy coordinate.
    ///
    /// All values are clamped to [0, 1].
    pub fn new(s_k: f64, s_t: f64, s_e: f64) -> Self {
        Self {
            s_k: s_k.clamp(0.0, 1.0),
            s_t: s_t.clamp(0.0, 1.0),
            s_e: s_e.clamp(0.0, 1.0),
        }
    }

    /// Origin of S-entropy space
    pub fn origin() -> Self {
        Self::new(0.0, 0.0, 0.0)
    }

    /// Center of S-entropy space
    pub fn center() -> Self {
        Self::new(0.5, 0.5, 0.5)
    }

    /// Maximum entropy state
    pub fn max_entropy() -> Self {
        Self::new(1.0, 1.0, 1.0)
    }

    /// Calculate categorical distance to another coordinate.
    ///
    /// Key property: This distance is INDEPENDENT of:
    /// - Spatial distance
    /// - Optical opacity
    /// - Physical barriers
    ///
    /// The categorical metric depends only on partition structure.
    pub fn categorical_distance(&self, other: &SEntropyCoordinate) -> f64 {
        let dk = (self.s_k - other.s_k).abs();
        let dt = (self.s_t - other.s_t).abs();
        let de = (self.s_e - other.s_e).abs();

        // L1 norm (Manhattan distance) - natural for ternary partitions
        dk + dt + de
    }

    /// Euclidean distance (for visualization)
    pub fn euclidean_distance(&self, other: &SEntropyCoordinate) -> f64 {
        let dk = self.s_k - other.s_k;
        let dt = self.s_t - other.s_t;
        let de = self.s_e - other.s_e;

        (dk * dk + dt * dt + de * de).sqrt()
    }

    /// Calculate the S-entropy value: S = kB * M * ln(n)
    ///
    /// M is the multiplicity (partition count)
    /// n is the microstates per partition
    pub fn entropy_value(&self, m: f64, n: f64) -> f64 {
        K_B * m * n.ln()
    }

    /// Map to ternary trit (0, 1, 2) based on dominant axis
    pub fn to_trit(&self) -> u8 {
        if self.s_k >= self.s_t && self.s_k >= self.s_e {
            0 // Knowledge axis dominant
        } else if self.s_t >= self.s_k && self.s_t >= self.s_e {
            1 // Temporal axis dominant
        } else {
            2 // Evolution axis dominant
        }
    }

    /// Create from a trit value
    pub fn from_trit(trit: u8) -> Self {
        match trit {
            0 => Self::new(1.0, 0.0, 0.0), // Knowledge axis
            1 => Self::new(0.0, 1.0, 0.0), // Temporal axis
            2 => Self::new(0.0, 0.0, 1.0), // Evolution axis
            _ => Self::center(),
        }
    }

    /// Interpolate between two coordinates
    pub fn interpolate(&self, other: &SEntropyCoordinate, t: f64) -> Self {
        let t = t.clamp(0.0, 1.0);
        Self::new(
            self.s_k + t * (other.s_k - self.s_k),
            self.s_t + t * (other.s_t - self.s_t),
            self.s_e + t * (other.s_e - self.s_e),
        )
    }

    /// Check if coordinate is within an aperture (spherical region)
    pub fn within_aperture(&self, center: &SEntropyCoordinate, width: f64) -> bool {
        self.categorical_distance(center) <= width
    }

    /// Project onto a specific axis (0=k, 1=t, 2=e)
    pub fn project_axis(&self, axis: u8) -> f64 {
        match axis {
            0 => self.s_k,
            1 => self.s_t,
            2 => self.s_e,
            _ => 0.0,
        }
    }

    /// Calculate phase (angular position in S-entropy space)
    pub fn phase(&self) -> f64 {
        (self.s_t / (self.s_k + 1e-10)).atan()
    }

    /// Calculate magnitude (distance from origin)
    pub fn magnitude(&self) -> f64 {
        self.euclidean_distance(&Self::origin())
    }
}

impl Default for SEntropyCoordinate {
    fn default() -> Self {
        Self::center()
    }
}

impl std::fmt::Display for SEntropyCoordinate {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "S({:.3}, {:.3}, {:.3})", self.s_k, self.s_t, self.s_e)
    }
}

/// A trajectory through S-entropy space
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SEntropyTrajectory {
    pub points: Vec<SEntropyCoordinate>,
}

impl SEntropyTrajectory {
    pub fn new() -> Self {
        Self { points: Vec::new() }
    }

    pub fn with_capacity(capacity: usize) -> Self {
        Self {
            points: Vec::with_capacity(capacity),
        }
    }

    pub fn push(&mut self, coord: SEntropyCoordinate) {
        self.points.push(coord);
    }

    pub fn len(&self) -> usize {
        self.points.len()
    }

    pub fn is_empty(&self) -> bool {
        self.points.is_empty()
    }

    /// Total categorical path length
    pub fn categorical_length(&self) -> f64 {
        if self.points.len() < 2 {
            return 0.0;
        }

        self.points
            .windows(2)
            .map(|w| w[0].categorical_distance(&w[1]))
            .sum()
    }

    /// Direct distance from start to end
    pub fn direct_distance(&self) -> f64 {
        if self.points.len() < 2 {
            return 0.0;
        }

        self.points
            .first()
            .unwrap()
            .categorical_distance(self.points.last().unwrap())
    }

    /// Path efficiency: direct/actual (1.0 = straight line)
    pub fn efficiency(&self) -> f64 {
        let actual = self.categorical_length();
        if actual < 1e-10 {
            return 1.0;
        }
        self.direct_distance() / actual
    }
}

impl Default for SEntropyTrajectory {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_coordinate_creation() {
        let coord = SEntropyCoordinate::new(0.5, 0.3, 0.7);
        assert_eq!(coord.s_k, 0.5);
        assert_eq!(coord.s_t, 0.3);
        assert_eq!(coord.s_e, 0.7);
    }

    #[test]
    fn test_clamping() {
        let coord = SEntropyCoordinate::new(1.5, -0.2, 0.5);
        assert_eq!(coord.s_k, 1.0);
        assert_eq!(coord.s_t, 0.0);
        assert_eq!(coord.s_e, 0.5);
    }

    #[test]
    fn test_categorical_distance() {
        let a = SEntropyCoordinate::origin();
        let b = SEntropyCoordinate::new(1.0, 1.0, 1.0);
        assert_eq!(a.categorical_distance(&b), 3.0);
    }

    #[test]
    fn test_trit_conversion() {
        let k_dominant = SEntropyCoordinate::new(1.0, 0.2, 0.3);
        assert_eq!(k_dominant.to_trit(), 0);

        let t_dominant = SEntropyCoordinate::new(0.2, 1.0, 0.3);
        assert_eq!(t_dominant.to_trit(), 1);

        let e_dominant = SEntropyCoordinate::new(0.2, 0.3, 1.0);
        assert_eq!(e_dominant.to_trit(), 2);
    }

    #[test]
    fn test_trajectory_efficiency() {
        let mut traj = SEntropyTrajectory::new();
        traj.push(SEntropyCoordinate::origin());
        traj.push(SEntropyCoordinate::new(0.5, 0.5, 0.5));
        traj.push(SEntropyCoordinate::new(1.0, 1.0, 1.0));

        // Straight line should have efficiency 1.0
        assert!((traj.efficiency() - 1.0).abs() < 0.01);
    }
}
