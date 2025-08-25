//! Oxygen-enhanced molecular data processor

use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{debug, info, warn};
use uuid::Uuid;

use crate::{
    molecular_data::MolecularData,
    evidence::{ProcessedEvidence, MolecularEvidence, EnhancedMolecularFeatures},
    error::{ProcessingError, Result},
    constants,
};

/// Oxygen-enhanced molecular information processor
///
/// Implements the core processing logic that applies paramagnetic oscillatory
/// enhancement to molecular data, creating biologically-validated evidence.
pub struct OxygenProcessor {
    processing_queue: Arc<RwLock<Vec<ProcessingTask>>>,
    active_processes: Arc<RwLock<std::collections::HashMap<Uuid, ProcessingContext>>>,
}

impl OxygenProcessor {
    /// Create new oxygen processor
    pub fn new() -> Self {
        Self {
            processing_queue: Arc::new(RwLock::new(Vec::new())),
            active_processes: Arc::new(RwLock::new(std::collections::HashMap::new())),
        }
    }

    /// Process molecular data with oxygen enhancement
    pub async fn process_with_oxygen_enhancement(
        &self,
        molecular_data: MolecularData,
        oscillation_pattern: Vec<f64>,
        processing_id: Uuid,
    ) -> Result<ProcessedEvidence> {
        info!(
            processing_id = %processing_id,
            molecule_count = molecular_data.molecules.len(),
            pattern_length = oscillation_pattern.len(),
            "Starting oxygen-enhanced molecular processing"
        );

        // Create processing context
        let context = ProcessingContext::new(processing_id, molecular_data.clone());
        
        {
            let mut active = self.active_processes.write().await;
            active.insert(processing_id, context);
        }

        // Apply paramagnetic oscillatory processing
        let processed_evidence = self.paramagnetic_processing(
            molecular_data,
            oscillation_pattern,
            processing_id,
        ).await?;

        // Remove from active processes
        {
            let mut active = self.active_processes.write().await;
            active.remove(&processing_id);
        }

        Ok(processed_evidence)
    }

    /// Core paramagnetic oscillation-based molecular processing
    async fn paramagnetic_processing(
        &self,
        data: MolecularData,
        pattern: Vec<f64>,
        processing_id: Uuid,
    ) -> Result<ProcessedEvidence> {
        debug!(
            processing_id = %processing_id,
            "Applying paramagnetic oscillatory enhancement"
        );

        let mut evidence = ProcessedEvidence::new();
        evidence.processing_metadata.processing_id = Some(processing_id);

        // Process each molecule with paramagnetic enhancement
        for (i, molecule) in data.molecules.iter().enumerate() {
            let oscillation_factor = if pattern.is_empty() {
                1.0
            } else {
                pattern[i % pattern.len()]
            };

            debug!(
                processing_id = %processing_id,
                molecule_id = %molecule.id,
                oscillation_factor = oscillation_factor,
                "Processing molecule with paramagnetic enhancement"
            );

            // Apply paramagnetic enhancement to molecular features
            let enhanced_features = self.apply_paramagnetic_enhancement(
                molecule,
                oscillation_factor,
            )?;

            // Calculate confidence score based on enhancement quality
            let confidence_score = self.calculate_enhancement_confidence(
                molecule,
                &enhanced_features,
                oscillation_factor,
            );

            // Add to evidence collection
            evidence.add_molecular_evidence(MolecularEvidence {
                molecule_id: molecule.id.clone(),
                enhanced_features,
                confidence_score,
                processing_metadata: EvidenceProcessingMetadata {
                    oscillation_factor,
                    enhancement_quality: confidence_score,
                    biological_compatibility: 1.0, // Will be calculated later
                    quantum_coherence_maintained: true,
                },
            });
        }

        // Calculate overall processing metrics
        evidence.processing_metadata.processing_time = Some(
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs_f64()
        );
        evidence.processing_metadata.oxygen_utilization = Some(
            self.calculate_oxygen_utilization(&data, &pattern)
        );
        evidence.processing_metadata.quantum_coherence_maintained = Some(true);

        info!(
            processing_id = %processing_id,
            evidence_count = evidence.molecular_evidence.len(),
            "Completed paramagnetic processing"
        );

        Ok(evidence)
    }

    /// Apply paramagnetic enhancement to a single molecule
    fn apply_paramagnetic_enhancement(
        &self,
        molecule: &crate::molecular_data::Molecule,
        oscillation_factor: f64,
    ) -> Result<EnhancedMolecularFeatures> {
        let mut enhanced = EnhancedMolecularFeatures::new(molecule.id.clone());

        for feature in &molecule.features {
            // Apply oscillatory enhancement based on paramagnetic resonance
            let enhancement_factor = 1.0 + oscillation_factor * constants::PARAMAGNETIC_ENHANCEMENT * 0.1;
            let enhanced_value = feature.value * enhancement_factor;

            // Boost confidence based on oscillation coherence
            let coherence_boost = oscillation_factor.abs() * 0.05;
            let enhanced_confidence = (feature.confidence + coherence_boost).clamp(0.0, 1.0);

            // Calculate biological plausibility factor
            let biological_factor = self.calculate_biological_plausibility_factor(
                &feature.name,
                enhanced_value,
                feature.value,
            );

            enhanced.add_feature(crate::evidence::EnhancedFeature {
                name: feature.name.clone(),
                original_value: feature.value,
                enhanced_value,
                confidence: enhanced_confidence,
                enhancement_factor,
                biological_plausibility: biological_factor,
                quantum_coherence_factor: oscillation_factor.abs(),
            });
        }

        Ok(enhanced)
    }

    /// Calculate confidence in the enhancement process
    fn calculate_enhancement_confidence(
        &self,
        molecule: &crate::molecular_data::Molecule,
        enhanced_features: &EnhancedMolecularFeatures,
        oscillation_factor: f64,
    ) -> f64 {
        let mut confidence_factors = Vec::new();

        // Factor 1: Oscillation quality
        let oscillation_quality = oscillation_factor.abs().min(1.0);
        confidence_factors.push(oscillation_quality);

        // Factor 2: Feature enhancement consistency
        if !enhanced_features.features.is_empty() {
            let enhancement_consistency = enhanced_features.features.iter()
                .map(|f| f.enhancement_factor)
                .collect::<Vec<_>>();
            
            let mean_enhancement = enhancement_consistency.iter().sum::<f64>() / enhancement_consistency.len() as f64;
            let variance = enhancement_consistency.iter()
                .map(|&e| (e - mean_enhancement).powi(2))
                .sum::<f64>() / enhancement_consistency.len() as f64;
            
            let consistency_score = 1.0 / (1.0 + variance);
            confidence_factors.push(consistency_score);
        }

        // Factor 3: Biological compatibility
        let biological_compatibility = enhanced_features.features.iter()
            .map(|f| f.biological_plausibility)
            .fold(1.0, |acc, x| acc * x);
        confidence_factors.push(biological_compatibility);

        // Factor 4: Molecular complexity adjustment
        let complexity_factor = if molecule.features.len() > 10 {
            0.9 // Reduce confidence for very complex molecules
        } else if molecule.features.len() < 3 {
            0.8 // Reduce confidence for very simple molecules
        } else {
            1.0
        };
        confidence_factors.push(complexity_factor);

        // Calculate weighted average confidence
        confidence_factors.iter().sum::<f64>() / confidence_factors.len() as f64
    }

    /// Calculate biological plausibility factor for a feature enhancement
    fn calculate_biological_plausibility_factor(
        &self,
        feature_name: &str,
        enhanced_value: f64,
        original_value: f64,
    ) -> f64 {
        let enhancement_ratio = enhanced_value / original_value.max(1e-10);
        
        // Biological systems have reasonable enhancement limits
        let plausibility = match feature_name {
            name if name.contains("mass") => {
                // Mass should not change significantly
                if (enhancement_ratio - 1.0).abs() < 0.01 { 1.0 } else { 0.5 }
            },
            name if name.contains("intensity") || name.contains("abundance") => {
                // Intensity can vary more but within biological limits
                if enhancement_ratio >= 0.5 && enhancement_ratio <= 3.0 { 1.0 } 
                else if enhancement_ratio >= 0.1 && enhancement_ratio <= 10.0 { 0.8 }
                else { 0.3 }
            },
            name if name.contains("energy") => {
                // Energy changes should be moderate
                if enhancement_ratio >= 0.8 && enhancement_ratio <= 1.5 { 1.0 }
                else if enhancement_ratio >= 0.5 && enhancement_ratio <= 2.0 { 0.7 }
                else { 0.4 }
            },
            _ => {
                // Default biological plausibility check
                if enhancement_ratio >= 0.7 && enhancement_ratio <= 2.0 { 1.0 }
                else if enhancement_ratio >= 0.3 && enhancement_ratio <= 5.0 { 0.6 }
                else { 0.2 }
            }
        };

        plausibility
    }

    /// Calculate oxygen utilization for the processing task
    fn calculate_oxygen_utilization(
        &self,
        data: &MolecularData,
        pattern: &[f64],
    ) -> f64 {
        let base_utilization = data.calculate_complexity() / constants::OXYGEN_INFORMATION_DENSITY;
        let pattern_intensity = if pattern.is_empty() {
            1.0
        } else {
            pattern.iter().map(|&x| x.abs()).sum::<f64>() / pattern.len() as f64
        };

        base_utilization * pattern_intensity
    }

    /// Get current processing queue status
    pub async fn get_queue_status(&self) -> ProcessingQueueStatus {
        let queue = self.processing_queue.read().await;
        let active = self.active_processes.read().await;

        ProcessingQueueStatus {
            queued_tasks: queue.len(),
            active_processes: active.len(),
            total_pending: queue.len() + active.len(),
        }
    }

    /// Add processing task to queue
    pub async fn queue_processing_task(&self, task: ProcessingTask) -> Result<()> {
        let mut queue = self.processing_queue.write().await;
        queue.push(task);
        Ok(())
    }
}

/// Processing task for queued molecular data processing
#[derive(Debug, Clone)]
pub struct ProcessingTask {
    pub id: Uuid,
    pub molecular_data: MolecularData,
    pub priority: TaskPriority,
    pub created_at: chrono::DateTime<chrono::Utc>,
    pub estimated_duration: Option<std::time::Duration>,
}

/// Task priority levels
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub enum TaskPriority {
    Low,
    Medium,
    High,
    Critical,
}

/// Processing context for active tasks
#[derive(Debug, Clone)]
struct ProcessingContext {
    pub processing_id: Uuid,
    pub molecular_data: MolecularData,
    pub start_time: std::time::Instant,
    pub status: ProcessingStatus,
}

impl ProcessingContext {
    fn new(processing_id: Uuid, molecular_data: MolecularData) -> Self {
        Self {
            processing_id,
            molecular_data,
            start_time: std::time::Instant::now(),
            status: ProcessingStatus::InProgress,
        }
    }
}

/// Processing status for tracking
#[derive(Debug, Clone)]
enum ProcessingStatus {
    InProgress,
    Completed,
    Failed,
}

/// Queue status information
#[derive(Debug, Clone)]
pub struct ProcessingQueueStatus {
    pub queued_tasks: usize,
    pub active_processes: usize,
    pub total_pending: usize,
}

/// Evidence processing metadata
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct EvidenceProcessingMetadata {
    pub oscillation_factor: f64,
    pub enhancement_quality: f64,
    pub biological_compatibility: f64,
    pub quantum_coherence_maintained: bool,
}

impl Default for OxygenProcessor {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::molecular_data::{Molecule, MolecularFeature};

    #[tokio::test]
    async fn test_processor_creation() {
        let processor = OxygenProcessor::new();
        let status = processor.get_queue_status().await;
        
        assert_eq!(status.queued_tasks, 0);
        assert_eq!(status.active_processes, 0);
    }

    #[test]
    fn test_paramagnetic_enhancement() {
        let processor = OxygenProcessor::new();
        
        let molecule = Molecule {
            id: "test-molecule".to_string(),
            formula: "C6H12O6".to_string(),
            mass: 180.156,
            features: vec![
                MolecularFeature {
                    name: "intensity".to_string(),
                    value: 1000.0,
                    confidence: 0.8,
                }
            ],
        };

        let enhanced = processor.apply_paramagnetic_enhancement(&molecule, 0.5)
            .expect("Enhancement should succeed");

        assert_eq!(enhanced.features.len(), 1);
        assert!(enhanced.features[0].enhanced_value > enhanced.features[0].original_value);
        assert!(enhanced.features[0].confidence >= 0.8);
    }

    #[test]
    fn test_biological_plausibility() {
        let processor = OxygenProcessor::new();
        
        // Test mass feature (should not change much)
        let mass_plausibility = processor.calculate_biological_plausibility_factor(
            "mass", 180.2, 180.0
        );
        assert!(mass_plausibility > 0.8);

        // Test intensity feature (can change more)
        let intensity_plausibility = processor.calculate_biological_plausibility_factor(
            "intensity", 1500.0, 1000.0
        );
        assert!(intensity_plausibility > 0.8);

        // Test extreme enhancement (should be penalized)
        let extreme_plausibility = processor.calculate_biological_plausibility_factor(
            "intensity", 10000.0, 100.0
        );
        assert!(extreme_plausibility < 0.8);
    }
}
