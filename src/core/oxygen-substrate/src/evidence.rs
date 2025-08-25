//! Evidence structures for oxygen-enhanced molecular processing

use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Processed molecular evidence with oxygen enhancement
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessedEvidence {
    /// Collection of molecular evidence
    pub molecular_evidence: Vec<MolecularEvidence>,

    /// Overall biological plausibility score
    pub plausibility_score: Option<f64>,

    /// Processing metadata
    pub processing_metadata: ProcessingMetadata,

    /// Evidence creation timestamp
    pub created_at: chrono::DateTime<chrono::Utc>,

    /// Evidence validation results
    pub validation_results: Option<ValidationResults>,
}

impl ProcessedEvidence {
    /// Create new processed evidence container
    pub fn new() -> Self {
        Self {
            molecular_evidence: Vec::new(),
            plausibility_score: None,
            processing_metadata: ProcessingMetadata::default(),
            created_at: chrono::Utc::now(),
            validation_results: None,
        }
    }

    /// Add molecular evidence to the collection
    pub fn add_molecular_evidence(&mut self, evidence: MolecularEvidence) {
        self.molecular_evidence.push(evidence);
    }

    /// Set overall biological plausibility score
    pub fn set_plausibility_score(&mut self, score: f64) {
        self.plausibility_score = Some(score.clamp(0.0, 1.0));
    }

    /// Calculate thermodynamic feasibility of molecular processes
    pub fn calculate_thermodynamic_feasibility(&self) -> f64 {
        if self.molecular_evidence.is_empty() {
            return 0.0;
        }

        let feasibility_scores: Vec<f64> = self
            .molecular_evidence
            .iter()
            .map(|evidence| self.calculate_molecular_thermodynamic_feasibility(evidence))
            .collect();

        feasibility_scores.iter().sum::<f64>() / feasibility_scores.len() as f64
    }

    /// Calculate kinetic feasibility of molecular processes
    pub fn calculate_kinetic_feasibility(&self) -> f64 {
        if self.molecular_evidence.is_empty() {
            return 0.0;
        }

        let kinetic_scores: Vec<f64> = self
            .molecular_evidence
            .iter()
            .map(|evidence| self.calculate_molecular_kinetic_feasibility(evidence))
            .collect();

        kinetic_scores.iter().sum::<f64>() / kinetic_scores.len() as f64
    }

    /// Calculate cellular context compatibility
    pub fn calculate_cellular_compatibility(&self) -> f64 {
        if self.molecular_evidence.is_empty() {
            return 0.0;
        }

        let compatibility_scores: Vec<f64> = self
            .molecular_evidence
            .iter()
            .map(|evidence| {
                // Base compatibility on biological plausibility of enhanced features
                evidence
                    .enhanced_features
                    .features
                    .iter()
                    .map(|f| f.biological_plausibility)
                    .fold(1.0, |acc, x| acc * x)
            })
            .collect();

        compatibility_scores.iter().sum::<f64>() / compatibility_scores.len() as f64
    }

    /// Get evidence summary statistics
    pub fn get_summary_statistics(&self) -> EvidenceSummaryStatistics {
        let molecule_count = self.molecular_evidence.len();

        let average_confidence = if molecule_count > 0 {
            self.molecular_evidence
                .iter()
                .map(|e| e.confidence_score)
                .sum::<f64>()
                / molecule_count as f64
        } else {
            0.0
        };

        let total_features = self
            .molecular_evidence
            .iter()
            .map(|e| e.enhanced_features.features.len())
            .sum();

        let average_enhancement_factor = if total_features > 0 {
            self.molecular_evidence
                .iter()
                .flat_map(|e| e.enhanced_features.features.iter())
                .map(|f| f.enhancement_factor)
                .sum::<f64>()
                / total_features as f64
        } else {
            1.0
        };

        EvidenceSummaryStatistics {
            molecule_count,
            total_features,
            average_confidence,
            average_enhancement_factor,
            plausibility_score: self.plausibility_score.unwrap_or(0.0),
            thermodynamic_feasibility: self.calculate_thermodynamic_feasibility(),
            kinetic_feasibility: self.calculate_kinetic_feasibility(),
            cellular_compatibility: self.calculate_cellular_compatibility(),
        }
    }

    /// Calculate thermodynamic feasibility for a single molecular evidence
    fn calculate_molecular_thermodynamic_feasibility(&self, evidence: &MolecularEvidence) -> f64 {
        // Simplified thermodynamic feasibility based on enhancement factors
        let enhancement_factors: Vec<f64> = evidence
            .enhanced_features
            .features
            .iter()
            .map(|f| f.enhancement_factor)
            .collect();

        if enhancement_factors.is_empty() {
            return 0.5;
        }

        // Thermodynamically feasible enhancements should be moderate
        let feasible_enhancements = enhancement_factors
            .iter()
            .filter(|&&factor| factor >= 0.5 && factor <= 2.0)
            .count();

        feasible_enhancements as f64 / enhancement_factors.len() as f64
    }

    /// Calculate kinetic feasibility for a single molecular evidence
    fn calculate_molecular_kinetic_feasibility(&self, evidence: &MolecularEvidence) -> f64 {
        // Kinetic feasibility based on quantum coherence and biological plausibility
        let quantum_coherence = evidence.processing_metadata.quantum_coherence_maintained;
        let biological_compatibility = evidence.processing_metadata.biological_compatibility;

        if quantum_coherence {
            biological_compatibility * 0.9 + 0.1 // Bonus for maintained coherence
        } else {
            biological_compatibility * 0.7 // Penalty for lost coherence
        }
    }
}

/// Individual molecular evidence with enhancement data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MolecularEvidence {
    /// Unique identifier of the molecule
    pub molecule_id: String,

    /// Enhanced molecular features
    pub enhanced_features: EnhancedMolecularFeatures,

    /// Confidence score for this evidence
    pub confidence_score: f64,

    /// Processing metadata for this evidence
    pub processing_metadata: crate::processor::EvidenceProcessingMetadata,
}

/// Enhanced molecular features with paramagnetic processing results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnhancedMolecularFeatures {
    /// Molecule identifier
    pub molecule_id: String,

    /// Collection of enhanced features
    pub features: Vec<EnhancedFeature>,

    /// Overall enhancement quality score
    pub enhancement_quality: f64,

    /// Timestamp of enhancement
    pub enhanced_at: chrono::DateTime<chrono::Utc>,
}

impl EnhancedMolecularFeatures {
    /// Create new enhanced features container
    pub fn new(molecule_id: String) -> Self {
        Self {
            molecule_id,
            features: Vec::new(),
            enhancement_quality: 0.0,
            enhanced_at: chrono::Utc::now(),
        }
    }

    /// Add enhanced feature
    pub fn add_feature(&mut self, feature: EnhancedFeature) {
        self.features.push(feature);
        self.calculate_enhancement_quality();
    }

    /// Calculate overall enhancement quality
    fn calculate_enhancement_quality(&mut self) {
        if self.features.is_empty() {
            self.enhancement_quality = 0.0;
            return;
        }

        let quality_factors: Vec<f64> = self
            .features
            .iter()
            .map(|f| {
                // Quality based on confidence, biological plausibility, and coherence
                (f.confidence + f.biological_plausibility + f.quantum_coherence_factor) / 3.0
            })
            .collect();

        self.enhancement_quality =
            quality_factors.iter().sum::<f64>() / quality_factors.len() as f64;
    }

    /// Get feature by name
    pub fn get_feature(&self, name: &str) -> Option<&EnhancedFeature> {
        self.features.iter().find(|f| f.name == name)
    }

    /// Get enhancement statistics
    pub fn get_enhancement_statistics(&self) -> FeatureEnhancementStatistics {
        if self.features.is_empty() {
            return FeatureEnhancementStatistics::default();
        }

        let enhancement_factors: Vec<f64> =
            self.features.iter().map(|f| f.enhancement_factor).collect();

        let mean_enhancement =
            enhancement_factors.iter().sum::<f64>() / enhancement_factors.len() as f64;

        let variance = enhancement_factors
            .iter()
            .map(|&factor| (factor - mean_enhancement).powi(2))
            .sum::<f64>()
            / enhancement_factors.len() as f64;

        let std_deviation = variance.sqrt();

        let min_enhancement = enhancement_factors
            .iter()
            .fold(f64::INFINITY, |a, &b| a.min(b));
        let max_enhancement = enhancement_factors
            .iter()
            .fold(f64::NEG_INFINITY, |a, &b| a.max(b));

        FeatureEnhancementStatistics {
            feature_count: self.features.len(),
            mean_enhancement,
            std_deviation,
            min_enhancement,
            max_enhancement,
            enhancement_quality: self.enhancement_quality,
        }
    }
}

/// Individual enhanced molecular feature
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnhancedFeature {
    /// Feature name
    pub name: String,

    /// Original feature value
    pub original_value: f64,

    /// Enhanced feature value
    pub enhanced_value: f64,

    /// Confidence in the enhanced value
    pub confidence: f64,

    /// Enhancement factor applied
    pub enhancement_factor: f64,

    /// Biological plausibility score
    pub biological_plausibility: f64,

    /// Quantum coherence factor during enhancement
    pub quantum_coherence_factor: f64,
}

impl EnhancedFeature {
    /// Calculate enhancement improvement over original
    pub fn enhancement_improvement(&self) -> f64 {
        if self.original_value.abs() < 1e-10 {
            return 0.0;
        }

        (self.enhanced_value - self.original_value) / self.original_value
    }

    /// Calculate overall feature quality
    pub fn quality_score(&self) -> f64 {
        (self.confidence + self.biological_plausibility + self.quantum_coherence_factor) / 3.0
    }
}

/// Processing metadata for evidence
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ProcessingMetadata {
    /// Processing session identifier
    pub processing_id: Option<Uuid>,

    /// Total processing time in seconds
    pub processing_time: Option<f64>,

    /// Oxygen utilization during processing
    pub oxygen_utilization: Option<f64>,

    /// Whether quantum coherence was maintained
    pub quantum_coherence_maintained: Option<bool>,

    /// Whether biological constraints were satisfied
    pub biological_constraints_satisfied: Option<bool>,

    /// Processing algorithm version
    pub algorithm_version: String,

    /// Processing timestamp
    pub processed_at: chrono::DateTime<chrono::Utc>,
}

impl ProcessingMetadata {
    /// Create new processing metadata
    pub fn new() -> Self {
        Self {
            processing_id: None,
            processing_time: None,
            oxygen_utilization: None,
            quantum_coherence_maintained: None,
            biological_constraints_satisfied: None,
            algorithm_version: env!("CARGO_PKG_VERSION").to_string(),
            processed_at: chrono::Utc::now(),
        }
    }
}

/// Evidence validation results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationResults {
    /// Thermodynamic validation passed
    pub thermodynamic_valid: bool,

    /// Kinetic validation passed
    pub kinetic_valid: bool,

    /// Cellular context validation passed
    pub cellular_context_valid: bool,

    /// Overall validation score
    pub overall_validation_score: f64,

    /// Validation details and warnings
    pub validation_details: Vec<ValidationDetail>,

    /// Validation timestamp
    pub validated_at: chrono::DateTime<chrono::Utc>,
}

/// Individual validation detail
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationDetail {
    /// Validation category
    pub category: ValidationCategory,

    /// Validation message
    pub message: String,

    /// Severity level
    pub severity: ValidationSeverity,

    /// Associated molecule ID (if applicable)
    pub molecule_id: Option<String>,
}

/// Validation categories
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ValidationCategory {
    Thermodynamic,
    Kinetic,
    CellularContext,
    BiologicalPlausibility,
    QuantumCoherence,
}

/// Validation severity levels
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ValidationSeverity {
    Info,
    Warning,
    Error,
    Critical,
}

/// Summary statistics for processed evidence
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvidenceSummaryStatistics {
    pub molecule_count: usize,
    pub total_features: usize,
    pub average_confidence: f64,
    pub average_enhancement_factor: f64,
    pub plausibility_score: f64,
    pub thermodynamic_feasibility: f64,
    pub kinetic_feasibility: f64,
    pub cellular_compatibility: f64,
}

/// Feature enhancement statistics
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct FeatureEnhancementStatistics {
    pub feature_count: usize,
    pub mean_enhancement: f64,
    pub std_deviation: f64,
    pub min_enhancement: f64,
    pub max_enhancement: f64,
    pub enhancement_quality: f64,
}

impl Default for ProcessedEvidence {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_evidence_creation() {
        let evidence = ProcessedEvidence::new();

        assert!(evidence.molecular_evidence.is_empty());
        assert!(evidence.plausibility_score.is_none());
        assert!(evidence.validation_results.is_none());
    }

    #[test]
    fn test_enhanced_features() {
        let mut features = EnhancedMolecularFeatures::new("test-molecule".to_string());

        features.add_feature(EnhancedFeature {
            name: "intensity".to_string(),
            original_value: 1000.0,
            enhanced_value: 1150.0,
            confidence: 0.9,
            enhancement_factor: 1.15,
            biological_plausibility: 0.95,
            quantum_coherence_factor: 0.8,
        });

        assert_eq!(features.features.len(), 1);
        assert!(features.enhancement_quality > 0.0);

        let stats = features.get_enhancement_statistics();
        assert_eq!(stats.feature_count, 1);
        assert_eq!(stats.mean_enhancement, 1.15);
    }

    #[test]
    fn test_evidence_summary() {
        let mut evidence = ProcessedEvidence::new();

        let mut features = EnhancedMolecularFeatures::new("test-molecule".to_string());
        features.add_feature(EnhancedFeature {
            name: "intensity".to_string(),
            original_value: 1000.0,
            enhanced_value: 1150.0,
            confidence: 0.9,
            enhancement_factor: 1.15,
            biological_plausibility: 0.95,
            quantum_coherence_factor: 0.8,
        });

        evidence.add_molecular_evidence(MolecularEvidence {
            molecule_id: "test-molecule".to_string(),
            enhanced_features: features,
            confidence_score: 0.9,
            processing_metadata: crate::processor::EvidenceProcessingMetadata {
                oscillation_factor: 0.8,
                enhancement_quality: 0.9,
                biological_compatibility: 0.95,
                quantum_coherence_maintained: true,
            },
        });

        evidence.set_plausibility_score(0.92);

        let summary = evidence.get_summary_statistics();
        assert_eq!(summary.molecule_count, 1);
        assert_eq!(summary.total_features, 1);
        assert_eq!(summary.average_confidence, 0.9);
        assert_eq!(summary.plausibility_score, 0.92);
    }
}
