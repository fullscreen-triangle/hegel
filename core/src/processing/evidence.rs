//! Evidence Processing Module
//! 
//! This module handles the processing, integration, and validation of evidence
//! from different sources (genomics, mass spectrometry, etc.) for molecular identification.

use anyhow::{Result, Context};
use log::{info, debug, warn, error};
use serde::{Serialize, Deserialize};
use std::collections::HashMap;
use std::sync::Arc;

use crate::processing::genomics::{GenomicsData, GenomicsProcessor};
use crate::processing::mass_spec::{MassSpecData, MassSpecProcessor};
use crate::graph::neo4j::Neo4jClient;

/// Initialize the evidence processing module
pub fn initialize() -> Result<()> {
    info!("Initializing evidence processing module");
    info!("Evidence processing module initialized successfully");
    Ok(())
}

/// Type of evidence source
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EvidenceType {
    /// Evidence from genomics data (sequencing, gene expression, etc.)
    Genomics,
    
    /// Evidence from mass spectrometry data
    MassSpec,
    
    /// Evidence from literature or databases
    Literature,
    
    /// Evidence from pathway analysis
    Pathway,
    
    /// Evidence from reactome analysis
    Reactome,
    
    /// Custom or other evidence source
    Other,
}

impl std::fmt::Display for EvidenceType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            EvidenceType::Genomics => write!(f, "genomics"),
            EvidenceType::MassSpec => write!(f, "mass_spec"),
            EvidenceType::Literature => write!(f, "literature"),
            EvidenceType::Pathway => write!(f, "pathway"),
            EvidenceType::Reactome => write!(f, "reactome"),
            EvidenceType::Other => write!(f, "other"),
        }
    }
}

/// Evidence item for a molecule
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Evidence {
    /// Unique identifier for the evidence
    pub id: String,
    
    /// Molecule ID this evidence relates to
    pub molecule_id: String,
    
    /// Type of evidence
    pub evidence_type: EvidenceType,
    
    /// Source of the evidence (e.g., specific experiment, database)
    pub source: String,
    
    /// Confidence score (0.0 - 1.0)
    pub confidence: f64,
    
    /// Raw data or evidence content
    pub data: serde_json::Value,
    
    /// Metadata and additional properties
    pub metadata: HashMap<String, serde_json::Value>,
    
    /// Timestamp when the evidence was created/recorded
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

/// Integrated evidence for a molecule from multiple sources
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IntegratedEvidence {
    /// Molecule ID this evidence relates to
    pub molecule_id: String,
    
    /// Individual evidence items
    pub evidence_items: Vec<Evidence>,
    
    /// Overall confidence score (calculated from individual evidence)
    pub aggregate_confidence: f64,
    
    /// Analysis of conflicting evidence
    pub conflicts: Vec<EvidenceConflict>,
    
    /// Timestamp of the integration
    pub integration_timestamp: chrono::DateTime<chrono::Utc>,
}

/// Conflict between evidence items
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvidenceConflict {
    /// Description of the conflict
    pub description: String,
    
    /// Evidence items involved in the conflict
    pub evidence_ids: Vec<String>,
    
    /// Severity of the conflict (0.0 - 1.0)
    pub severity: f64,
    
    /// Possible resolution suggestions
    pub resolution_suggestions: Vec<String>,
}

/// Options for evidence processing
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvidenceProcessingOptions {
    /// Minimum confidence threshold for accepting evidence
    pub confidence_threshold: f64,
    
    /// Whether to use AI-guided processing
    pub use_ai_guidance: bool,
    
    /// Maximum number of conflicts to report
    pub max_conflicts: usize,
    
    /// Sources to prioritize
    pub priority_sources: Vec<EvidenceType>,
}

impl Default for EvidenceProcessingOptions {
    fn default() -> Self {
        Self {
            confidence_threshold: 0.5,
            use_ai_guidance: true,
            max_conflicts: 10,
            priority_sources: vec![EvidenceType::Genomics, EvidenceType::MassSpec],
        }
    }
}

/// Evidence processor for handling and integrating molecular evidence
pub struct EvidenceProcessor {
    /// Options for evidence processing
    options: EvidenceProcessingOptions,
    
    /// Neo4j client for database operations
    neo4j_client: Option<Arc<Neo4jClient>>,
    
    /// Genomics data processor
    genomics_processor: GenomicsProcessor,
    
    /// Mass spectrometry data processor
    mass_spec_processor: MassSpecProcessor,
}

impl EvidenceProcessor {
    /// Create a new evidence processor with the given options
    pub fn new(options: EvidenceProcessingOptions) -> Self {
        Self {
            options,
            neo4j_client: None,
            genomics_processor: GenomicsProcessor::new(),
            mass_spec_processor: MassSpecProcessor::new(),
        }
    }
    
    /// Set the Neo4j client for database operations
    pub fn with_neo4j_client(mut self, client: Arc<Neo4jClient>) -> Self {
        self.neo4j_client = Some(client);
        self
    }
    
    /// Process and integrate evidence for a molecule
    pub async fn process_evidence(&self, molecule_id: &str, evidence: Vec<Evidence>) -> Result<IntegratedEvidence> {
        debug!("Processing {} evidence items for molecule {}", evidence.len(), molecule_id);
        
        // Filter evidence by confidence threshold
        let filtered_evidence: Vec<Evidence> = evidence.into_iter()
            .filter(|e| e.confidence >= self.options.confidence_threshold)
            .collect();
        
        debug!("{} evidence items passed confidence threshold", filtered_evidence.len());
        
        // Check for conflicting evidence
        let conflicts = self.detect_conflicts(&filtered_evidence)?;
        debug!("Detected {} conflicts in evidence", conflicts.len());
        
        // Calculate aggregate confidence
        let aggregate_confidence = self.calculate_aggregate_confidence(&filtered_evidence, &conflicts)?;
        debug!("Calculated aggregate confidence: {:.2}", aggregate_confidence);
        
        // Create integrated evidence
        let integrated = IntegratedEvidence {
            molecule_id: molecule_id.to_string(),
            evidence_items: filtered_evidence,
            aggregate_confidence,
            conflicts,
            integration_timestamp: chrono::Utc::now(),
        };
        
        Ok(integrated)
    }
    
    /// Process genomics data and convert to evidence
    pub fn process_genomics_data(&self, molecule_id: &str, data: &GenomicsData) -> Result<Vec<Evidence>> {
        self.genomics_processor.process(molecule_id, data)
            .map(|results| {
                results.into_iter()
                    .map(|result| Evidence {
                        id: format!("genomics-{}-{}", molecule_id, uuid::Uuid::new_v4()),
                        molecule_id: molecule_id.to_string(),
                        evidence_type: EvidenceType::Genomics,
                        source: "genomics_analysis".to_string(),
                        confidence: result.confidence,
                        data: serde_json::to_value(&result).unwrap_or_default(),
                        metadata: HashMap::new(),
                        timestamp: chrono::Utc::now(),
                    })
                    .collect()
            })
            .context("Failed to process genomics data")
    }
    
    /// Process mass spectrometry data and convert to evidence
    pub fn process_mass_spec_data(&self, molecule_id: &str, data: &MassSpecData) -> Result<Vec<Evidence>> {
        self.mass_spec_processor.process(molecule_id, data)
            .map(|results| {
                results.into_iter()
                    .map(|result| Evidence {
                        id: format!("mass_spec-{}-{}", molecule_id, uuid::Uuid::new_v4()),
                        molecule_id: molecule_id.to_string(),
                        evidence_type: EvidenceType::MassSpec,
                        source: "mass_spec_analysis".to_string(),
                        confidence: result.confidence,
                        data: serde_json::to_value(&result).unwrap_or_default(),
                        metadata: HashMap::new(),
                        timestamp: chrono::Utc::now(),
                    })
                    .collect()
            })
            .context("Failed to process mass spectrometry data")
    }
    
    /// Detect conflicts between evidence items
    fn detect_conflicts(&self, evidence: &[Evidence]) -> Result<Vec<EvidenceConflict>> {
        // For now, implement a simple conflict detection algorithm
        // In a real implementation, this would be more sophisticated
        
        let mut conflicts = Vec::new();
        
        // Group evidence by molecule property/attribute
        let mut evidence_by_property: HashMap<String, Vec<&Evidence>> = HashMap::new();
        
        for ev in evidence {
            if let Some(props) = ev.data.as_object() {
                for (key, _) in props {
                    evidence_by_property
                        .entry(key.clone())
                        .or_default()
                        .push(ev);
                }
            }
        }
        
        // Check for conflicts within each property group
        for (property, items) in evidence_by_property {
            if items.len() < 2 {
                continue;
            }
            
            // Simple heuristic: if confidence values vary by more than 0.3, consider it a conflict
            let max_confidence = items.iter().map(|e| e.confidence).fold(0.0, f64::max);
            let min_confidence = items.iter().map(|e| e.confidence).fold(1.0, f64::min);
            
            if max_confidence - min_confidence > 0.3 {
                conflicts.push(EvidenceConflict {
                    description: format!("Conflicting evidence for property '{}'", property),
                    evidence_ids: items.iter().map(|e| e.id.clone()).collect(),
                    severity: max_confidence - min_confidence,
                    resolution_suggestions: vec![
                        "Consider additional experiments".to_string(),
                        "Prioritize higher confidence evidence".to_string(),
                    ],
                });
            }
        }
        
        // Limit to max_conflicts
        if conflicts.len() > self.options.max_conflicts {
            conflicts.sort_by(|a, b| b.severity.partial_cmp(&a.severity).unwrap_or(std::cmp::Ordering::Equal));
            conflicts.truncate(self.options.max_conflicts);
        }
        
        Ok(conflicts)
    }
    
    /// Calculate aggregate confidence from individual evidence items
    fn calculate_aggregate_confidence(&self, evidence: &[Evidence], conflicts: &[EvidenceConflict]) -> Result<f64> {
        if evidence.is_empty() {
            return Ok(0.0);
        }
        
        // Start with weighted average of individual confidences
        let mut total_weight = 0.0;
        let mut weighted_sum = 0.0;
        
        for ev in evidence {
            // Prioritize evidence from priority sources
            let weight = if self.options.priority_sources.contains(&ev.evidence_type) {
                2.0
            } else {
                1.0
            };
            
            weighted_sum += ev.confidence * weight;
            total_weight += weight;
        }
        
        let mut aggregate = weighted_sum / total_weight;
        
        // Adjust for conflicts
        if !conflicts.is_empty() {
            let conflict_penalty = conflicts.iter()
                .map(|c| c.severity)
                .sum::<f64>() / conflicts.len() as f64;
            
            // Apply a penalty proportional to the severity of conflicts
            aggregate *= (1.0 - 0.5 * conflict_penalty);
        }
        
        // Ensure the result is within [0.0, 1.0]
        let aggregate = aggregate.max(0.0).min(1.0);
        
        Ok(aggregate)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_evidence_type_display() {
        assert_eq!(EvidenceType::Genomics.to_string(), "genomics");
        assert_eq!(EvidenceType::MassSpec.to_string(), "mass_spec");
    }
    
    #[test]
    fn test_default_options() {
        let options = EvidenceProcessingOptions::default();
        assert_eq!(options.confidence_threshold, 0.5);
        assert_eq!(options.max_conflicts, 10);
        assert!(options.use_ai_guidance);
    }
} 