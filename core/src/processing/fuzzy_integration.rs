use crate::fuzzy_evidence::{
    FuzzyBayesianNetwork, FuzzyEvidence, EvidenceNode, EvidenceEdge, 
    EvidenceRelationship, EvidencePrediction
};
use crate::processing::evidence::{Evidence, IntegratedEvidence, EvidenceProcessor};
use anyhow::{Result, Context};
use std::collections::HashMap;
use log::{debug, info, warn};

/// Fuzzy Evidence Integration System
/// Bridges traditional evidence processing with fuzzy-Bayesian networks
pub struct FuzzyEvidenceIntegrator {
    network: FuzzyBayesianNetwork,
    evidence_processor: EvidenceProcessor,
    integration_config: IntegrationConfig,
}

#[derive(Debug, Clone)]
pub struct IntegrationConfig {
    pub confidence_threshold: f64,
    pub prediction_threshold: f64,
    pub max_prediction_iterations: usize,
    pub enable_temporal_decay: bool,
    pub enable_network_learning: bool,
}

impl Default for IntegrationConfig {
    fn default() -> Self {
        IntegrationConfig {
            confidence_threshold: 0.5,
            prediction_threshold: 0.7,
            max_prediction_iterations: 10,
            enable_temporal_decay: true,
            enable_network_learning: true,
        }
    }
}

impl FuzzyEvidenceIntegrator {
    /// Create a new fuzzy evidence integrator
    pub fn new(evidence_processor: EvidenceProcessor, config: IntegrationConfig) -> Self {
        FuzzyEvidenceIntegrator {
            network: FuzzyBayesianNetwork::new(),
            evidence_processor,
            integration_config: config,
        }
    }
    
    /// Convert traditional evidence to fuzzy evidence
    pub fn convert_to_fuzzy_evidence(&self, evidence: &Evidence) -> Result<FuzzyEvidence> {
        let timestamp = chrono::Utc::now(); // In practice, would use evidence timestamp
        
        let fuzzy_evidence = FuzzyEvidence::from_raw_evidence(
            evidence.id.clone(),
            evidence.source.clone(),
            evidence.evidence_type.to_string(),
            evidence.confidence,
            timestamp,
        );
        
        Ok(fuzzy_evidence)
    }
    
    /// Integrate traditional evidence into the fuzzy network
    pub async fn integrate_evidence(&mut self, evidences: Vec<Evidence>) -> Result<FuzzyIntegrationResult> {
        info!("Integrating {} evidence items into fuzzy network", evidences.len());
        
        let mut fuzzy_evidences = Vec::new();
        let mut integration_errors = Vec::new();
        
        // Convert traditional evidence to fuzzy evidence
        for evidence in &evidences {
            match self.convert_to_fuzzy_evidence(evidence) {
                Ok(fuzzy_evidence) => {
                    fuzzy_evidences.push(fuzzy_evidence);
                }
                Err(e) => {
                    warn!("Failed to convert evidence {}: {}", evidence.id, e);
                    integration_errors.push(format!("Evidence {}: {}", evidence.id, e));
                }
            }
        }
        
        // Add fuzzy evidence to network
        for fuzzy_evidence in fuzzy_evidences {
            if let Err(e) = self.network.add_evidence(fuzzy_evidence.clone()) {
                warn!("Failed to add evidence {} to network: {}", fuzzy_evidence.id, e);
                integration_errors.push(format!("Network addition {}: {}", fuzzy_evidence.id, e));
            }
        }
        
        // Build evidence relationships
        self.build_evidence_relationships(&evidences)?;
        
        // Update network using fuzzy-Bayesian inference
        if let Err(e) = self.network.update_network() {
            warn!("Failed to update fuzzy network: {}", e);
            integration_errors.push(format!("Network update: {}", e));
        }
        
        // Generate predictions for missing evidence
        let predictions = if self.integration_config.enable_network_learning {
            self.generate_evidence_predictions(&evidences).await?
        } else {
            Vec::new()
        };
        
        // Calculate enhanced confidence scores
        let enhanced_confidences = self.calculate_enhanced_confidences(&evidences)?;
        
        Ok(FuzzyIntegrationResult {
            original_evidence_count: evidences.len(),
            integrated_evidence_count: self.network.nodes.len(),
            predictions,
            enhanced_confidences,
            integration_errors,
            network_coherence_score: self.calculate_network_coherence()?,
        })
    }
    
    /// Build relationships between evidence nodes based on molecular context
    fn build_evidence_relationships(&mut self, evidences: &[Evidence]) -> Result<()> {
        debug!("Building evidence relationships for {} evidence items", evidences.len());
        
        for i in 0..evidences.len() {
            for j in (i + 1)..evidences.len() {
                let evidence_a = &evidences[i];
                let evidence_b = &evidences[j];
                
                // Determine relationship type and strength
                let (relationship_type, strength) = self.determine_evidence_relationship(evidence_a, evidence_b)?;
                
                if strength > 0.1 { // Only add meaningful relationships
                    let edge = EvidenceEdge {
                        from_node: evidence_a.id.clone(),
                        to_node: evidence_b.id.clone(),
                        relationship_type,
                        strength,
                        fuzzy_strength: self.calculate_fuzzy_relationship_strength(evidence_a, evidence_b)?,
                    };
                    
                    self.network.edges.push(edge);
                }
            }
        }
        
        debug!("Built {} evidence relationships", self.network.edges.len());
        Ok(())
    }
    
    /// Determine the relationship type and strength between two pieces of evidence
    fn determine_evidence_relationship(&self, evidence_a: &Evidence, evidence_b: &Evidence) -> Result<(EvidenceRelationship, f64)> {
        // Same source type - likely corroborating
        if evidence_a.source == evidence_b.source {
            let confidence_diff = (evidence_a.confidence - evidence_b.confidence).abs();
            if confidence_diff < 0.2 {
                return Ok((EvidenceRelationship::Corroborates, 0.8 - confidence_diff));
            } else {
                return Ok((EvidenceRelationship::Contradicts, confidence_diff));
            }
        }
        
        // Different source types - analyze for support/contradiction
        let confidence_similarity = 1.0 - (evidence_a.confidence - evidence_b.confidence).abs();
        
        if confidence_similarity > 0.7 {
            Ok((EvidenceRelationship::Supports, confidence_similarity))
        } else if confidence_similarity < 0.3 {
            Ok((EvidenceRelationship::Contradicts, 1.0 - confidence_similarity))
        } else {
            // Check for implication relationships based on evidence types
            match (evidence_a.evidence_type.as_str(), evidence_b.evidence_type.as_str()) {
                ("genomics", "proteomics") => Ok((EvidenceRelationship::Implies, 0.6)),
                ("proteomics", "metabolomics") => Ok((EvidenceRelationship::Implies, 0.5)),
                ("literature", _) => Ok((EvidenceRelationship::Supports, 0.4)),
                _ => Ok((EvidenceRelationship::Supports, confidence_similarity)),
            }
        }
    }
    
    /// Calculate fuzzy representation of relationship strength
    fn calculate_fuzzy_relationship_strength(&self, evidence_a: &Evidence, evidence_b: &Evidence) -> Result<HashMap<String, f64>> {
        let mut fuzzy_strength = HashMap::new();
        
        let confidence_diff = (evidence_a.confidence - evidence_b.confidence).abs();
        let avg_confidence = (evidence_a.confidence + evidence_b.confidence) / 2.0;
        
        // Define fuzzy terms for relationship strength
        fuzzy_strength.insert("weak".to_string(), if confidence_diff > 0.5 { 1.0 } else { confidence_diff * 2.0 });
        fuzzy_strength.insert("moderate".to_string(), if confidence_diff < 0.3 && avg_confidence > 0.4 { 1.0 } else { 0.5 });
        fuzzy_strength.insert("strong".to_string(), if confidence_diff < 0.1 && avg_confidence > 0.7 { 1.0 } else { 0.0 });
        
        Ok(fuzzy_strength)
    }
    
    /// Generate predictions for missing evidence using the network
    async fn generate_evidence_predictions(&self, existing_evidence: &[Evidence]) -> Result<Vec<EvidencePrediction>> {
        let existing_ids: Vec<String> = existing_evidence.iter().map(|e| e.id.clone()).collect();
        
        let predictions = self.network.predict_missing_evidence(&existing_ids).await
            .context("Failed to generate evidence predictions")?;
        
        // Filter predictions by confidence threshold
        let filtered_predictions: Vec<EvidencePrediction> = predictions.into_iter()
            .filter(|p| p.confidence >= self.integration_config.prediction_threshold)
            .collect();
        
        info!("Generated {} high-confidence evidence predictions", filtered_predictions.len());
        Ok(filtered_predictions)
    }
    
    /// Calculate enhanced confidence scores using fuzzy network
    fn calculate_enhanced_confidences(&self, evidences: &[Evidence]) -> Result<HashMap<String, EnhancedConfidence>> {
        let mut enhanced_confidences = HashMap::new();
        
        for evidence in evidences {
            if let Some(node) = self.network.nodes.get(&evidence.id) {
                let enhanced = EnhancedConfidence {
                    original_confidence: evidence.confidence,
                    fuzzy_confidence: node.fuzzy_evidence.as_ref()
                        .map(|fe| fe.defuzzified_confidence())
                        .unwrap_or(evidence.confidence),
                    bayesian_posterior: node.posterior_probability,
                    network_influence: node.network_influence,
                    final_confidence: self.calculate_final_confidence(node)?,
                    uncertainty_bounds: node.fuzzy_evidence.as_ref()
                        .map(|fe| fe.uncertainty_bounds)
                        .unwrap_or((evidence.confidence * 0.9, evidence.confidence * 1.1)),
                };
                
                enhanced_confidences.insert(evidence.id.clone(), enhanced);
            }
        }
        
        Ok(enhanced_confidences)
    }
    
    /// Calculate final confidence score combining all factors
    fn calculate_final_confidence(&self, node: &EvidenceNode) -> Result<f64> {
        let fuzzy_weight = 0.4;
        let bayesian_weight = 0.4;
        let network_weight = 0.2;
        
        let fuzzy_confidence = node.fuzzy_evidence.as_ref()
            .map(|fe| fe.defuzzified_confidence())
            .unwrap_or(0.5);
        
        let final_confidence = fuzzy_confidence * fuzzy_weight +
                              node.posterior_probability * bayesian_weight +
                              node.network_influence.abs() * network_weight;
        
        Ok(final_confidence.clamp(0.0, 1.0))
    }
    
    /// Calculate overall network coherence score
    fn calculate_network_coherence(&self) -> Result<f64> {
        if self.network.nodes.is_empty() {
            return Ok(0.0);
        }
        
        // Calculate average confidence
        let avg_confidence: f64 = self.network.nodes.values()
            .filter_map(|node| node.fuzzy_evidence.as_ref())
            .map(|evidence| evidence.defuzzified_confidence())
            .sum::<f64>() / self.network.nodes.len() as f64;
        
        // Calculate relationship consistency
        let mut consistency_sum = 0.0;
        let mut relationship_count = 0;
        
        for edge in &self.network.edges {
            if let (Some(from_node), Some(to_node)) = (
                self.network.nodes.get(&edge.from_node),
                self.network.nodes.get(&edge.to_node)
            ) {
                let consistency = match edge.relationship_type {
                    EvidenceRelationship::Supports | EvidenceRelationship::Corroborates => {
                        1.0 - (from_node.posterior_probability - to_node.posterior_probability).abs()
                    }
                    EvidenceRelationship::Contradicts => {
                        (from_node.posterior_probability - to_node.posterior_probability).abs()
                    }
                    _ => 0.5,
                };
                
                consistency_sum += consistency * edge.strength;
                relationship_count += 1;
            }
        }
        
        let avg_consistency = if relationship_count > 0 {
            consistency_sum / relationship_count as f64
        } else {
            0.5
        };
        
        // Combine confidence and consistency
        let coherence = (avg_confidence * 0.6 + avg_consistency * 0.4).clamp(0.0, 1.0);
        
        Ok(coherence)
    }
    
    /// Get network statistics for analysis
    pub fn get_network_statistics(&self) -> NetworkStatistics {
        let node_count = self.network.nodes.len();
        let edge_count = self.network.edges.len();
        
        let avg_confidence = if node_count > 0 {
            self.network.nodes.values()
                .filter_map(|node| node.fuzzy_evidence.as_ref())
                .map(|evidence| evidence.defuzzified_confidence())
                .sum::<f64>() / node_count as f64
        } else {
            0.0
        };
        
        let conflict_count = self.network.edges.iter()
            .filter(|edge| matches!(edge.relationship_type, EvidenceRelationship::Contradicts))
            .count();
        
        NetworkStatistics {
            node_count,
            edge_count,
            avg_confidence,
            conflict_count,
            coherence_score: self.calculate_network_coherence().unwrap_or(0.0),
        }
    }
}

/// Result of fuzzy evidence integration
#[derive(Debug, Clone)]
pub struct FuzzyIntegrationResult {
    pub original_evidence_count: usize,
    pub integrated_evidence_count: usize,
    pub predictions: Vec<EvidencePrediction>,
    pub enhanced_confidences: HashMap<String, EnhancedConfidence>,
    pub integration_errors: Vec<String>,
    pub network_coherence_score: f64,
}

/// Enhanced confidence information combining multiple approaches
#[derive(Debug, Clone)]
pub struct EnhancedConfidence {
    pub original_confidence: f64,
    pub fuzzy_confidence: f64,
    pub bayesian_posterior: f64,
    pub network_influence: f64,
    pub final_confidence: f64,
    pub uncertainty_bounds: (f64, f64),
}

/// Network statistics for analysis
#[derive(Debug, Clone)]
pub struct NetworkStatistics {
    pub node_count: usize,
    pub edge_count: usize,
    pub avg_confidence: f64,
    pub conflict_count: usize,
    pub coherence_score: f64,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::processing::evidence::{Evidence, EvidenceProcessingOptions};
    
    #[tokio::test]
    async fn test_fuzzy_integration() {
        let evidence_processor = EvidenceProcessor::new(EvidenceProcessingOptions::default());
        let config = IntegrationConfig::default();
        let mut integrator = FuzzyEvidenceIntegrator::new(evidence_processor, config);
        
        let evidence = Evidence {
            id: "test_evidence".to_string(),
            source: "mass_spec".to_string(),
            evidence_type: "spectral_match".to_string(),
            confidence: 0.8,
            data: serde_json::json!({"peak_count": 15}),
        };
        
        let result = integrator.integrate_evidence(vec![evidence]).await;
        assert!(result.is_ok());
        
        let integration_result = result.unwrap();
        assert_eq!(integration_result.original_evidence_count, 1);
        assert_eq!(integration_result.integrated_evidence_count, 1);
    }
    
    #[test]
    fn test_evidence_relationship_determination() {
        let evidence_processor = EvidenceProcessor::new(EvidenceProcessingOptions::default());
        let config = IntegrationConfig::default();
        let integrator = FuzzyEvidenceIntegrator::new(evidence_processor, config);
        
        let evidence_a = Evidence {
            id: "evidence_a".to_string(),
            source: "mass_spec".to_string(),
            evidence_type: "spectral_match".to_string(),
            confidence: 0.8,
            data: serde_json::json!({}),
        };
        
        let evidence_b = Evidence {
            id: "evidence_b".to_string(),
            source: "mass_spec".to_string(),
            evidence_type: "spectral_match".to_string(),
            confidence: 0.75,
            data: serde_json::json!({}),
        };
        
        let result = integrator.determine_evidence_relationship(&evidence_a, &evidence_b);
        assert!(result.is_ok());
        
        let (relationship, strength) = result.unwrap();
        assert!(matches!(relationship, EvidenceRelationship::Corroborates));
        assert!(strength > 0.5);
    }
} 