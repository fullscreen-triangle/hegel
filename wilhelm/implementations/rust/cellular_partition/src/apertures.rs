//! Categorical Apertures
//!
//! An aperture is a geometric constraint in S-entropy space.
//! Enzymes provide apertures - they don't "accelerate" reactions,
//! they provide geometric pathways that constrain valid trajectories.
//!
//! The active site IS the aperture. Catalysis IS aperture traversal.

use crate::s_entropy::SEntropyCoordinate;
use crate::ternary::TritString;
use serde::{Deserialize, Serialize};

/// A categorical aperture in S-entropy space
///
/// Apertures constrain trajectories by requiring passage through
/// a specific region of categorical space. This is how enzymes
/// catalyze reactions: they provide aperture geometry, not energy.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CategoricalAperture {
    /// Identifier (e.g., "carbonic_anhydrase_II")
    pub name: String,
    /// S-entropy coordinates of aperture center
    pub center: SEntropyCoordinate,
    /// Aperture width (selectivity)
    pub width: f64,
    /// Ternary pattern encoding aperture traversal
    pub pattern: String,
    /// Spatial arrangement (tetrahedral, octahedral, etc.)
    pub geometry: ApertureGeometry,
}

/// Geometry types for apertures
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ApertureGeometry {
    Tetrahedral,
    Octahedral,
    Cylindrical,
    Rotary,
    Planar,
    Generic,
}

impl CategoricalAperture {
    /// Create a new categorical aperture
    pub fn new(
        name: &str,
        center: SEntropyCoordinate,
        width: f64,
        pattern: &str,
        geometry: ApertureGeometry,
    ) -> Self {
        Self {
            name: name.to_string(),
            center,
            width,
            pattern: pattern.to_string(),
            geometry,
        }
    }

    /// Get the ternary pattern for aperture traversal
    pub fn traversal_pattern(&self) -> TritString {
        TritString::new(&self.pattern).unwrap_or_else(|_| TritString::empty())
    }

    /// Check if coordinate is within aperture
    pub fn contains(&self, coord: &SEntropyCoordinate) -> bool {
        self.center.categorical_distance(coord) <= self.width
    }

    /// Calculate distance reduction through aperture
    ///
    /// Apertures reduce categorical distance by providing
    /// intermediate states with smaller jumps.
    pub fn distance_reduction(&self, direct_distance: f64) -> f64 {
        let aperture_distance = direct_distance * self.width;
        (direct_distance - aperture_distance).max(0.0)
    }

    /// Aperture selectivity: narrower = more selective
    ///
    /// S = 1 / width
    ///
    /// K+ channels have S ~ 10^3 (very selective)
    /// Water channels have S ~ 10 (less selective)
    pub fn selectivity(&self) -> f64 {
        if self.width == 0.0 {
            f64::INFINITY
        } else {
            1.0 / self.width
        }
    }
}

// Predefined apertures for common enzymes

/// Carbonic Anhydrase II (CA II) aperture
///
/// Active site: Tetrahedral Zn2+ coordination
/// Reaction: CO2 + H2O <-> HCO3- + H+
/// Turnover: ~10^6 s^-1
///
/// Categorical distance d_C = 1 (single categorical transition)
pub fn carbonic_anhydrase_ii() -> CategoricalAperture {
    CategoricalAperture::new(
        "carbonic_anhydrase_II",
        SEntropyCoordinate::new(0.5, 0.5, 0.5),
        0.01, // Very narrow - high selectivity
        "012", // Tetrahedral traversal pattern
        ApertureGeometry::Tetrahedral,
    )
}

/// ATP Synthase aperture
///
/// Rotary motor converting proton gradient to ATP.
/// F0: proton channel
/// F1: catalytic domain
///
/// Pattern encodes the three-step rotary mechanism.
pub fn atp_synthase() -> CategoricalAperture {
    CategoricalAperture::new(
        "atp_synthase",
        SEntropyCoordinate::new(0.33, 0.33, 0.33),
        0.02,
        "012120201", // Three 120-degree rotations
        ApertureGeometry::Rotary,
    )
}

/// K+ ion channel aperture
///
/// Selectivity filter: TVGYG motif
/// Selectivity: ~10^4 K+ over Na+
///
/// Frequency matching, not size exclusion.
pub fn k_channel() -> CategoricalAperture {
    CategoricalAperture::new(
        "k_channel",
        SEntropyCoordinate::new(0.7, 0.3, 0.5),
        0.001, // Extremely narrow - high selectivity
        "111", // Temporal axis traversal (frequency match)
        ApertureGeometry::Cylindrical,
    )
}

/// Create a generic enzyme aperture
pub fn generic_enzyme(name: &str, pattern: &str, selectivity: f64) -> CategoricalAperture {
    CategoricalAperture::new(
        name,
        SEntropyCoordinate::center(),
        1.0 / selectivity,
        pattern,
        ApertureGeometry::Generic,
    )
}

/// Result of aperture traversal analysis
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApertureTraversalResult {
    pub aperture_name: String,
    pub trajectory: TritString,
    pub traversal_position: usize,
    pub categorical_distance: usize,
    pub direct_distance: usize,
    pub catalytic_efficiency: f64,
}

/// Analyze how a trajectory traverses an aperture
pub fn analyze_traversal(
    trajectory: &TritString,
    aperture: &CategoricalAperture,
) -> Option<ApertureTraversalResult> {
    let traj_str = trajectory.to_string_repr();
    let pattern = &aperture.pattern;

    // Find aperture traversal position
    let pos = traj_str.find(pattern)?;

    // Calculate categorical distances
    let len = trajectory.len();
    let pattern_len = pattern.len();

    let pre = if pos > 0 {
        trajectory.substring(0, pos)
    } else {
        TritString::empty()
    };

    let post = if pos + pattern_len < len {
        trajectory.substring(pos + pattern_len, len)
    } else {
        TritString::empty()
    };

    // Categorical distance through aperture
    let cat_dist = if !pre.is_empty() && !post.is_empty() {
        pre.categorical_distance(&post)
    } else {
        len
    };

    // Direct distance (without aperture)
    let initial = trajectory.substring(0, 3.min(len));
    let final_state = trajectory.substring(len.saturating_sub(3), len);
    let direct_dist = initial.categorical_distance(&final_state);

    // Catalytic efficiency
    let efficiency = direct_dist as f64 / cat_dist.max(1) as f64;

    Some(ApertureTraversalResult {
        aperture_name: aperture.name.clone(),
        trajectory: trajectory.clone(),
        traversal_position: pos,
        categorical_distance: cat_dist,
        direct_distance: direct_dist,
        catalytic_efficiency: efficiency,
    })
}

/// Collection of well-known enzyme apertures
pub struct EnzymeLibrary {
    apertures: Vec<CategoricalAperture>,
}

impl EnzymeLibrary {
    pub fn new() -> Self {
        Self {
            apertures: Vec::new(),
        }
    }

    /// Create library with standard enzymes
    pub fn standard() -> Self {
        let mut lib = Self::new();
        lib.add(carbonic_anhydrase_ii());
        lib.add(atp_synthase());
        lib.add(k_channel());
        lib
    }

    pub fn add(&mut self, aperture: CategoricalAperture) {
        self.apertures.push(aperture);
    }

    pub fn get(&self, name: &str) -> Option<&CategoricalAperture> {
        self.apertures.iter().find(|a| a.name == name)
    }

    pub fn len(&self) -> usize {
        self.apertures.len()
    }

    pub fn is_empty(&self) -> bool {
        self.apertures.is_empty()
    }

    pub fn iter(&self) -> impl Iterator<Item = &CategoricalAperture> {
        self.apertures.iter()
    }

    /// Find all apertures that can catalyze a given trajectory
    pub fn find_catalysts(&self, trajectory: &TritString) -> Vec<&CategoricalAperture> {
        self.apertures
            .iter()
            .filter(|a| trajectory.contains_pattern(&a.pattern))
            .collect()
    }
}

impl Default for EnzymeLibrary {
    fn default() -> Self {
        Self::standard()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_aperture_creation() {
        let ca2 = carbonic_anhydrase_ii();
        assert_eq!(ca2.name, "carbonic_anhydrase_II");
        assert_eq!(ca2.pattern, "012");
        assert_eq!(ca2.geometry, ApertureGeometry::Tetrahedral);
    }

    #[test]
    fn test_selectivity() {
        let ca2 = carbonic_anhydrase_ii();
        assert_eq!(ca2.selectivity(), 100.0); // 1/0.01

        let k_ch = k_channel();
        assert_eq!(k_ch.selectivity(), 1000.0); // 1/0.001
    }

    #[test]
    fn test_traversal_analysis() {
        let ca2 = carbonic_anhydrase_ii();
        let trajectory = TritString::new("000012222").unwrap();

        let result = analyze_traversal(&trajectory, &ca2);
        assert!(result.is_some());

        let result = result.unwrap();
        assert_eq!(result.traversal_position, 3);
    }

    #[test]
    fn test_enzyme_library() {
        let lib = EnzymeLibrary::standard();
        assert_eq!(lib.len(), 3);

        let ca2 = lib.get("carbonic_anhydrase_II");
        assert!(ca2.is_some());
    }

    #[test]
    fn test_find_catalysts() {
        let lib = EnzymeLibrary::standard();
        let trajectory = TritString::new("012012012").unwrap();

        let catalysts = lib.find_catalysts(&trajectory);
        // CA II has pattern "012", should match
        assert!(!catalysts.is_empty());
    }
}
