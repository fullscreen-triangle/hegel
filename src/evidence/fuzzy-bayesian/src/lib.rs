//! # Fuzzy-Bayesian Evidence Networks
//!
//! This module implements hybrid fuzzy-Bayesian evidence networks that treat biological
//! evidence as continuous rather than binary, enabling sophisticated uncertainty propagation
//! and relationship learning for molecular evidence processing.
//!
//! ## Core Innovation
//!
//! The fuzzy-Bayesian system provides:
//!
//! - **Continuous Evidence Processing**: Treats biological evidence as fuzzy sets rather than binary
//! - **Uncertainty Propagation**: Advanced Bayesian networks with uncertainty bounds
//! - **Relationship Discovery**: Automated learning of evidence relationships
//! - **Biological Constraint Integration**: Incorporates biological plausibility constraints
//!
//! ## Architecture
//!
//! The evidence network consists of:
//! - **Evidence Nodes**: Individual pieces of biological evidence with fuzzy membership
//! - **Relationship Edges**: Probabilistic connections between evidence types
//! - **Inference Engine**: Bayesian reasoning with fuzzy logic integration
//! - **Learning System**: Continuous improvement of network structure and parameters
//!
//! ## Usage
//!
//! ```rust
//! use fuzzy_bayesian::{EvidenceNetwork, Evidence, FuzzyMembership};
//!
//! #[tokio::main]
//! async fn main() -> Result<(), Box<dyn std::error::Error>> {
//!     let mut network = EvidenceNetwork::new();
//!     
//!     // Add evidence to the network
//!     let spectral_evidence = Evidence::new(
//!         "spectral_match".to_string(),
//!         0.85,
//!         FuzzyMembership::high(),
//!     );
//!     
//!     network.add_evidence(spectral_evidence).await?;
//!     
//!     // Perform inference
//!     let posterior = network.infer_molecular_identity("target_molecule").await?;
//!     
//!     println!("Molecular identity confidence: {:.2}", posterior.confidence);
//!     Ok(())
//! }
//! ```

use std::sync::Arc;
use tokio::sync::RwLock;
use serde::{Deserialize, Serialize};
use tracing::{debug, info, warn, error};
use uuid::Uuid;
use nalgebra::DMatrix;
use ndarray::{Array1, Array2};
use petgraph::{Graph, Directed, graph::NodeIndex};
use indexmap::IndexMap;

pub mod evidence;
pub mod fuzzy_logic;
pub mod bayesian;
pub mod network;
pub mod learning;
pub mod inference;
pub mod uncertainty;
pub mod biological_constraints;
pub mod error;

// Re-exports for convenience
pub use evidence::{Evidence, EvidenceType, EvidenceSource, BiologicalEvidence};
pub use fuzzy_logic::{FuzzyMembership, FuzzySet, FuzzyOperations, LinguisticVariable};
pub use bayesian::{BayesianNetwork, ConditionalProbability, PriorProbability};
pub use network::{EvidenceNetwork, NetworkTopology, EvidenceNode, EvidenceEdge};
pub use learning::{NetworkLearning, StructureLearning, ParameterLearning};
pub use inference::{InferenceEngine, InferenceResult, PosteriorDistribution};
pub use uncertainty::{UncertaintyPropagation, UncertaintyBounds, ConfidenceInterval};
pub use biological_constraints::{BiologicalConstraintValidator, ConstraintViolation};
pub use error::{EvidenceError, Result};

/// Evidence network constants
pub mod constants {
    /// Default evidence confidence threshold
    pub const EVIDENCE_CONFIDENCE_THRESHOLD: f64 = 0.85;
    
    /// Fuzzy membership tolerance
    pub const FUZZY_MEMBERSHIP_TOLERANCE: f64 = 0.1;
    
    /// Bayesian prior weight
    pub const BAYESIAN_PRIOR_WEIGHT: f64 = 0.3;
    
    /// Evidence decay rate (30-day half-life)
    pub const EVIDENCE_DECAY_RATE: f64 = 0.023;
    
    /// Maximum network nodes
    pub const MAX_NETWORK_NODES: usize = 10000;
    
    /// Learning rate for parameter updates
    pub const LEARNING_RATE: f64 = 0.01;
    
    /// Minimum relationship strength
    pub const MIN_RELATIONSHIP_STRENGTH: f64 = 0.1;
    
    /// Biological plausibility threshold
    pub const BIOLOGICAL_PLAUSIBILITY_THRESHOLD: f64 = 0.7;
}

/// High-level evidence processing engine
///
/// Provides a simplified interface to the complex fuzzy-Bayesian evidence network
/// system, optimized for biological molecular evidence processing workflows.
pub struct EvidenceEngine {
    /// Core evidence network
    network: Arc<RwLock<EvidenceNetwork>>,
    
    /// Inference engine
    inference_engine: Arc<InferenceEngine>,
    
    /// Learning system
    learning_system: Arc<RwLock<NetworkLearning>>,
    
    /// Biological constraint validator
    constraint_validator: Arc<BiologicalConstraintValidator>,
    
    /// Performance statistics
    statistics: Arc<RwLock<EvidenceStatistics>>,
    
    /// Configuration
    config: Arc<RwLock<EvidenceConfiguration>>,
}

impl EvidenceEngine {
    /// Create new evidence processing engine
    pub async fn new() -> Result<Self> {
        let network = EvidenceNetwork::new();
        let inference_engine = InferenceEngine::new();
        let learning_system = NetworkLearning::new();
        let constraint_validator = BiologicalConstraintValidator::new();
        
        Ok(Self {
            network: Arc::new(RwLock::new(network)),
            inference_engine: Arc::new(inference_engine),
            learning_system: Arc::new(RwLock::new(learning_system)),
            constraint_validator: Arc::new(constraint_validator),
            statistics: Arc::new(RwLock::new(EvidenceStatistics::new())),
            config: Arc::new(RwLock::new(EvidenceConfiguration::default())),
        })
    }
    
    /// Create engine with custom configuration
    pub async fn with_config(config: EvidenceConfiguration) -> Result<Self> {
        let mut engine = Self::new().await?;
        engine.update_configuration(config).await?;
        Ok(engine)
    }
    
    /// Process molecular evidence and update network
    pub async fn process_molecular_evidence(
        &self,
        evidence_batch: Vec<BiologicalEvidence>,
    ) -> Result<EvidenceProcessingResult> {
        let processing_id = Uuid::new_v4();
        let start_time = std::time::Instant::now();
        
        info!(
            processing_id = %processing_id,
            evidence_count = evidence_batch.len(),
            "Starting molecular evidence processing"
        );

        let mut processing_result = EvidenceProcessingResult::new(processing_id);

        // Step 1: Validate biological constraints
        let validated_evidence = self.validate_biological_evidence(&evidence_batch).await?;
        processing_result.validated_evidence_count = validated_evidence.len();

        // Step 2: Convert to fuzzy evidence and add to network
        let mut network = self.network.write().await;
        for bio_evidence in validated_evidence {
            let fuzzy_evidence = self.convert_to_fuzzy_evidence(bio_evidence).await?;
            network.add_evidence(fuzzy_evidence).await?;
        }
        
        // Step 3: Update network structure through learning
        let mut learning = self.learning_system.write().await;
        let learning_result = learning.update_network_structure(&mut network).await?;
        processing_result.relationships_learned = learning_result.new_relationships;
        processing_result.parameters_updated = learning_result.updated_parameters;

        // Step 4: Propagate uncertainty through network
        let uncertainty_result = network.propagate_uncertainty().await?;
        processing_result.uncertainty_bounds = uncertainty_result.global_uncertainty_bounds;

        let processing_duration = start_time.elapsed();
        processing_result.processing_duration = processing_duration;

        // Update statistics
        let mut stats = self.statistics.write().await;
        stats.record_processing(
            evidence_batch.len(),
            processing_result.validated_evidence_count,
            processing_duration,
        );

        info!(
            processing_id = %processing_id,
            validated_count = processing_result.validated_evidence_count,
            relationships_learned = processing_result.relationships_learned,
            duration_ms = processing_duration.as_millis(),
            "Completed molecular evidence processing"
        );

        Ok(processing_result)
    }
    
    /// Infer molecular identity from current evidence
    pub async fn infer_molecular_identity(
        &self,
        query: MolecularQuery,
    ) -> Result<MolecularInferenceResult> {
        let inference_id = Uuid::new_v4();
        let start_time = std::time::Instant::now();
        
        info!(
            inference_id = %inference_id,
            molecule_id = %query.molecule_id,
            "Starting molecular identity inference"
        );

        // Perform Bayesian inference with fuzzy evidence integration
        let inference_result = self.inference_engine
            .infer_with_uncertainty(&query, &*self.network.read().await)
            .await?;

        // Apply biological constraints to inference result
        let validated_result = self.constraint_validator
            .validate_inference_result(&inference_result)
            .await?;

        let inference_duration = start_time.elapsed();

        let result = MolecularInferenceResult {
            inference_id,
            query: query.clone(),
            posterior_distribution: inference_result.posterior,
            confidence: validated_result.confidence,
            uncertainty_bounds: inference_result.uncertainty_bounds,
            biological_plausibility: validated_result.plausibility_score,
            alternative_hypotheses: inference_result.alternatives,
            inference_duration,
        };

        // Update statistics
        let mut stats = self.statistics.write().await;
        stats.record_inference(inference_duration, result.confidence);

        info!(
            inference_id = %inference_id,
            confidence = result.confidence,
            plausibility = result.biological_plausibility,
            alternatives = result.alternative_hypotheses.len(),
            duration_ms = inference_duration.as_millis(),
            "Completed molecular identity inference"
        );

        Ok(result)
    }
    
    /// Get network topology information
    pub async fn get_network_topology(&self) -> NetworkTopologyInfo {
        let network = self.network.read().await;
        network.get_topology_info().await
    }
    
    /// Train network on historical data
    pub async fn train_network(
        &self,
        training_data: Vec<TrainingExample>,
    ) -> Result<TrainingResult> {
        info!(
            training_examples = training_data.len(),
            "Starting network training"
        );

        let mut learning = self.learning_system.write().await;
        let mut network = self.network.write().await;
        
        let training_result = learning.train_with_examples(
            &mut network,
            training_data,
        ).await?;

        info!(
            structure_changes = training_result.structure_changes,
            parameter_updates = training_result.parameter_updates,
            final_accuracy = training_result.final_accuracy,
            "Completed network training"
        );

        Ok(training_result)
    }
    
    /// Get evidence processing statistics
    pub async fn get_statistics(&self) -> EvidenceStatistics {
        self.statistics.read().await.clone()
    }
    
    /// Reset statistics
    pub async fn reset_statistics(&self) {
        let mut stats = self.statistics.write().await;
        *stats = EvidenceStatistics::new();
        info!("Reset evidence processing statistics");
    }

    /// Update configuration
    pub async fn update_configuration(&self, config: EvidenceConfiguration) -> Result<()> {
        config.validate()?;
        
        let mut current_config = self.config.write().await;
        *current_config = config;
        
        info!("Updated evidence processing configuration");
        Ok(())
    }

    /// Validate biological evidence constraints
    async fn validate_biological_evidence(
        &self,
        evidence_batch: &[BiologicalEvidence],
    ) -> Result<Vec<BiologicalEvidence>> {
        let mut validated = Vec::new();
        
        for evidence in evidence_batch {
            match self.constraint_validator.validate_evidence(evidence).await {
                Ok(validation_result) => {
                    if validation_result.is_valid {
                        validated.push(evidence.clone());
                    } else {
                        warn!(
                            evidence_id = %evidence.id,
                            violations = ?validation_result.violations,
                            "Evidence failed biological validation"
                        );
                    }
                },
                Err(e) => {
                    warn!(
                        evidence_id = %evidence.id,
                        error = %e,
                        "Error validating evidence"
                    );
                }
            }
        }
        
        Ok(validated)
    }

    /// Convert biological evidence to fuzzy evidence
    async fn convert_to_fuzzy_evidence(
        &self,
        bio_evidence: BiologicalEvidence,
    ) -> Result<Evidence> {
        let fuzzy_membership = self.calculate_fuzzy_membership(&bio_evidence);
        
        Ok(Evidence {
            id: bio_evidence.id,
            evidence_type: bio_evidence.evidence_type,
            value: bio_evidence.value,
            confidence: bio_evidence.confidence,
            fuzzy_membership,
            source: bio_evidence.source,
            timestamp: bio_evidence.timestamp,
            biological_context: Some(bio_evidence.biological_context),
        })
    }

    /// Calculate fuzzy membership for biological evidence
    fn calculate_fuzzy_membership(&self, evidence: &BiologicalEvidence) -> FuzzyMembership {
        match evidence.evidence_type {
            EvidenceType::Spectral => {
                if evidence.value > 0.9 {
                    FuzzyMembership::very_high()
                } else if evidence.value > 0.7 {
                    FuzzyMembership::high()
                } else if evidence.value > 0.5 {
                    FuzzyMembership::medium()
                } else if evidence.value > 0.3 {
                    FuzzyMembership::low()
                } else {
                    FuzzyMembership::very_low()
                }
            },
            EvidenceType::Sequence => {
                // Sequence similarity often has different thresholds
                if evidence.value > 0.95 {
                    FuzzyMembership::very_high()
                } else if evidence.value > 0.8 {
                    FuzzyMembership::high()
                } else if evidence.value > 0.6 {
                    FuzzyMembership::medium()
                } else if evidence.value > 0.4 {
                    FuzzyMembership::low()
                } else {
                    FuzzyMembership::very_low()
                }
            },
            EvidenceType::Structural => {
                // Structural similarity thresholds
                if evidence.value > 0.85 {
                    FuzzyMembership::very_high()
                } else if evidence.value > 0.7 {
                    FuzzyMembership::high()
                } else if evidence.value > 0.5 {
                    FuzzyMembership::medium()
                } else if evidence.value > 0.3 {
                    FuzzyMembership::low()
                } else {
                    FuzzyMembership::very_low()
                }
            },
            EvidenceType::Pathway => {
                // Pathway membership is often binary but can be fuzzy
                if evidence.value > 0.8 {
                    FuzzyMembership::high()
                } else if evidence.value > 0.5 {
                    FuzzyMembership::medium()
                } else {
                    FuzzyMembership::low()
                }
            },
        }
    }
}

/// Evidence processing statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvidenceStatistics {
    pub total_evidence_processed: u64,
    pub validated_evidence_count: u64,
    pub rejected_evidence_count: u64,
    pub total_inferences: u64,
    pub successful_inferences: u64,
    pub average_processing_time: std::time::Duration,
    pub average_inference_time: std::time::Duration,
    pub average_confidence: f64,
    pub network_node_count: usize,
    pub network_edge_count: usize,
    pub relationships_learned: u64,
    pub parameters_updated: u64,
    pub created_at: chrono::DateTime<chrono::Utc>,
    pub last_updated: chrono::DateTime<chrono::Utc>,
}

impl EvidenceStatistics {
    pub fn new() -> Self {
        let now = chrono::Utc::now();
        Self {
            total_evidence_processed: 0,
            validated_evidence_count: 0,
            rejected_evidence_count: 0,
            total_inferences: 0,
            successful_inferences: 0,
            average_processing_time: std::time::Duration::from_millis(0),
            average_inference_time: std::time::Duration::from_millis(0),
            average_confidence: 0.0,
            network_node_count: 0,
            network_edge_count: 0,
            relationships_learned: 0,
            parameters_updated: 0,
            created_at: now,
            last_updated: now,
        }
    }

    pub fn record_processing(
        &mut self,
        total_evidence: usize,
        validated_evidence: usize,
        duration: std::time::Duration,
    ) {
        self.total_evidence_processed += total_evidence as u64;
        self.validated_evidence_count += validated_evidence as u64;
        self.rejected_evidence_count += (total_evidence - validated_evidence) as u64;

        // Update average processing time
        let total_millis = self.average_processing_time.as_millis() * self.total_evidence_processed as u128;
        let new_average_millis = (total_millis + duration.as_millis()) / (self.total_evidence_processed + 1) as u128;
        self.average_processing_time = std::time::Duration::from_millis(new_average_millis as u64);

        self.last_updated = chrono::Utc::now();
    }

    pub fn record_inference(&mut self, duration: std::time::Duration, confidence: f64) {
        self.total_inferences += 1;
        self.successful_inferences += 1;

        // Update average inference time
        let total_millis = self.average_inference_time.as_millis() * (self.total_inferences - 1) as u128;
        let new_average_millis = (total_millis + duration.as_millis()) / self.total_inferences as u128;
        self.average_inference_time = std::time::Duration::from_millis(new_average_millis as u64);

        // Update average confidence
        self.average_confidence = (self.average_confidence * (self.total_inferences - 1) as f64 + confidence) / self.total_inferences as f64;

        self.last_updated = chrono::Utc::now();
    }

    pub fn validation_rate(&self) -> f64 {
        if self.total_evidence_processed == 0 {
            return 0.0;
        }
        self.validated_evidence_count as f64 / self.total_evidence_processed as f64
    }

    pub fn inference_success_rate(&self) -> f64 {
        if self.total_inferences == 0 {
            return 0.0;
        }
        self.successful_inferences as f64 / self.total_inferences as f64
    }
}

/// Evidence processing configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvidenceConfiguration {
    pub confidence_threshold: f64,
    pub fuzzy_tolerance: f64,
    pub prior_weight: f64,
    pub decay_rate: f64,
    pub max_network_nodes: usize,
    pub learning_rate: f64,
    pub biological_plausibility_threshold: f64,
    pub enable_structure_learning: bool,
    pub enable_parameter_learning: bool,
    pub enable_uncertainty_propagation: bool,
}

impl Default for EvidenceConfiguration {
    fn default() -> Self {
        Self {
            confidence_threshold: constants::EVIDENCE_CONFIDENCE_THRESHOLD,
            fuzzy_tolerance: constants::FUZZY_MEMBERSHIP_TOLERANCE,
            prior_weight: constants::BAYESIAN_PRIOR_WEIGHT,
            decay_rate: constants::EVIDENCE_DECAY_RATE,
            max_network_nodes: constants::MAX_NETWORK_NODES,
            learning_rate: constants::LEARNING_RATE,
            biological_plausibility_threshold: constants::BIOLOGICAL_PLAUSIBILITY_THRESHOLD,
            enable_structure_learning: true,
            enable_parameter_learning: true,
            enable_uncertainty_propagation: true,
        }
    }
}

impl EvidenceConfiguration {
    pub fn validate(&self) -> Result<()> {
        if self.confidence_threshold <= 0.0 || self.confidence_threshold > 1.0 {
            return Err(EvidenceError::InvalidConfiguration {
                reason: "confidence_threshold must be between 0.0 and 1.0".to_string(),
            });
        }

        if self.learning_rate <= 0.0 || self.learning_rate > 1.0 {
            return Err(EvidenceError::InvalidConfiguration {
                reason: "learning_rate must be between 0.0 and 1.0".to_string(),
            });
        }

        if self.max_network_nodes == 0 {
            return Err(EvidenceError::InvalidConfiguration {
                reason: "max_network_nodes must be greater than 0".to_string(),
            });
        }

        Ok(())
    }
}

// Result types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvidenceProcessingResult {
    pub processing_id: Uuid,
    pub validated_evidence_count: usize,
    pub relationships_learned: usize,
    pub parameters_updated: usize,
    pub uncertainty_bounds: UncertaintyBounds,
    pub processing_duration: std::time::Duration,
}

impl EvidenceProcessingResult {
    pub fn new(processing_id: Uuid) -> Self {
        Self {
            processing_id,
            validated_evidence_count: 0,
            relationships_learned: 0,
            parameters_updated: 0,
            uncertainty_bounds: UncertaintyBounds::default(),
            processing_duration: std::time::Duration::from_millis(0),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MolecularInferenceResult {
    pub inference_id: Uuid,
    pub query: MolecularQuery,
    pub posterior_distribution: PosteriorDistribution,
    pub confidence: f64,
    pub uncertainty_bounds: UncertaintyBounds,
    pub biological_plausibility: f64,
    pub alternative_hypotheses: Vec<AlternativeHypothesis>,
    pub inference_duration: std::time::Duration,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MolecularQuery {
    pub molecule_id: String,
    pub query_type: QueryType,
    pub constraints: Vec<QueryConstraint>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum QueryType {
    Identity,
    Pathway,
    Interaction,
    Property,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QueryConstraint {
    pub constraint_type: String,
    pub value: f64,
    pub tolerance: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlternativeHypothesis {
    pub hypothesis: String,
    pub probability: f64,
    pub evidence_support: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrainingExample {
    pub input_evidence: Vec<BiologicalEvidence>,
    pub expected_output: String,
    pub confidence: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrainingResult {
    pub structure_changes: usize,
    pub parameter_updates: usize,
    pub final_accuracy: f64,
    pub training_duration: std::time::Duration,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkTopologyInfo {
    pub node_count: usize,
    pub edge_count: usize,
    pub average_degree: f64,
    pub clustering_coefficient: f64,
    pub network_density: f64,
}

impl Default for EvidenceStatistics {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_evidence_engine_creation() {
        let engine = EvidenceEngine::new().await;
        assert!(engine.is_ok());
    }

    #[test]
    fn test_evidence_configuration() {
        let config = EvidenceConfiguration::default();
        assert!(config.validate().is_ok());
        
        let mut invalid_config = config;
        invalid_config.confidence_threshold = 2.0;
        assert!(invalid_config.validate().is_err());
    }

    #[test]
    fn test_statistics_recording() {
        let mut stats = EvidenceStatistics::new();
        
        stats.record_processing(10, 8, std::time::Duration::from_millis(100));
        assert_eq!(stats.total_evidence_processed, 10);
        assert_eq!(stats.validated_evidence_count, 8);
        assert_eq!(stats.rejected_evidence_count, 2);
        assert_eq!(stats.validation_rate(), 0.8);
        
        stats.record_inference(std::time::Duration::from_millis(50), 0.9);
        assert_eq!(stats.total_inferences, 1);
        assert_eq!(stats.average_confidence, 0.9);
        assert_eq!(stats.inference_success_rate(), 1.0);
    }

    #[test]
    fn test_evidence_processing_result() {
        let processing_id = Uuid::new_v4();
        let mut result = EvidenceProcessingResult::new(processing_id);
        
        assert_eq!(result.processing_id, processing_id);
        assert_eq!(result.validated_evidence_count, 0);
        
        result.validated_evidence_count = 5;
        assert_eq!(result.validated_evidence_count, 5);
    }
}
