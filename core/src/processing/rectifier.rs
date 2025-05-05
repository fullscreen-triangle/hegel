//! Evidence Rectifier Module
//! 
//! This module handles the rectification of evidence from multiple sources using
//! AI-guided methods to improve confidence in molecular identities.

use anyhow::{Result, Context};
use log::{info, debug, warn, error};
use serde::{Serialize, Deserialize};
use std::collections::HashMap;
use std::sync::Arc;

use crate::graph::neo4j::Neo4jClient;
use crate::metacognition::llm::LLMClient;
use crate::processing::evidence::{Evidence, IntegratedEvidence, EvidenceType};

/// Initialize the evidence rectifier module
pub fn initialize() -> Result<()> {
    info!("Initializing evidence rectifier module");
    info!("Evidence rectifier module initialized successfully");
    Ok(())
}

/// Rectification strategy
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum RectificationStrategy {
    /// Use consensus from multiple sources
    Consensus,
    
    /// Use AI-guided reasoning
    AIGuided,
    
    /// Use pathway-based contextualization
    PathwayBased,
    
    /// Use literature-based evidence
    LiteratureBased,
    
    /// Use expert rules
    ExpertRules,
}

/// Result of evidence rectification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RectificationResult {
    /// Original evidence
    pub original_evidence: IntegratedEvidence,
    
    /// Rectified evidence items
    pub rectified_evidence: Vec<RectifiedEvidence>,
    
    /// Overall confidence improvement
    pub confidence_improvement: f64,
    
    /// Reasoning for rectification
    pub reasoning: Vec<String>,
    
    /// Strategies used for rectification
    pub strategies_used: Vec<RectificationStrategy>,
    
    /// Timestamp of rectification
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

/// Rectified evidence item
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RectifiedEvidence {
    /// Original evidence ID
    pub original_id: String,
    
    /// Type of evidence
    pub evidence_type: EvidenceType,
    
    /// Original confidence
    pub original_confidence: f64,
    
    /// Rectified confidence
    pub rectified_confidence: f64,
    
    /// Reason for confidence adjustment
    pub adjustment_reason: String,
    
    /// Raw evidence data
    pub data: serde_json::Value,
}

/// Options for evidence rectification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RectificationOptions {
    /// Strategies to use for rectification
    pub strategies: Vec<RectificationStrategy>,
    
    /// Maximum confidence improvement allowed
    pub max_confidence_improvement: f64,
    
    /// Minimum original confidence to consider for rectification
    pub min_original_confidence: f64,
    
    /// Whether to use pathway analysis
    pub use_pathway_analysis: bool,
    
    /// Whether to use interactome analysis
    pub use_interactome_analysis: bool,
}

impl Default for RectificationOptions {
    fn default() -> Self {
        Self {
            strategies: vec![
                RectificationStrategy::Consensus,
                RectificationStrategy::AIGuided,
                RectificationStrategy::PathwayBased,
            ],
            max_confidence_improvement: 0.3,
            min_original_confidence: 0.2,
            use_pathway_analysis: true,
            use_interactome_analysis: true,
        }
    }
}

/// Evidence rectifier for improving confidence in molecular evidence
pub struct EvidenceRectifier {
    /// Options for rectification
    options: RectificationOptions,
    
    /// Neo4j client for graph database operations
    neo4j_client: Option<Arc<Neo4jClient>>,
    
    /// LLM client for AI-guided rectification
    llm_client: Option<Arc<LLMClient>>,
}

impl EvidenceRectifier {
    /// Create a new evidence rectifier with the given options
    pub fn new(options: RectificationOptions) -> Self {
        Self {
            options,
            neo4j_client: None,
            llm_client: None,
        }
    }
    
    /// Create a new evidence rectifier with default options
    pub fn default() -> Self {
        Self::new(RectificationOptions::default())
    }
    
    /// Set the Neo4j client for database operations
    pub fn with_neo4j_client(mut self, client: Arc<Neo4jClient>) -> Self {
        self.neo4j_client = Some(client);
        self
    }
    
    /// Set the LLM client for AI-guided rectification
    pub fn with_llm_client(mut self, client: Arc<LLMClient>) -> Self {
        self.llm_client = Some(client);
        self
    }
    
    /// Rectify the evidence for a molecule
    pub async fn rectify(&self, evidence: IntegratedEvidence) -> Result<RectificationResult> {
        debug!("Rectifying evidence for molecule {}", evidence.molecule_id);
        
        // Skip rectification if no evidence items
        if evidence.evidence_items.is_empty() {
            return Ok(RectificationResult {
                original_evidence: evidence.clone(),
                rectified_evidence: Vec::new(),
                confidence_improvement: 0.0,
                reasoning: vec!["No evidence items to rectify".to_string()],
                strategies_used: Vec::new(),
                timestamp: chrono::Utc::now(),
            });
        }
        
        // Track strategies used
        let mut strategies_used = Vec::new();
        
        // Initial rectification using consensus strategy if enabled
        let mut rectified_evidence = if self.options.strategies.contains(&RectificationStrategy::Consensus) {
            strategies_used.push(RectificationStrategy::Consensus);
            self.apply_consensus_strategy(&evidence)?
        } else {
            // Start with original evidence and confidences
            evidence.evidence_items.iter()
                .map(|e| RectifiedEvidence {
                    original_id: e.id.clone(),
                    evidence_type: e.evidence_type,
                    original_confidence: e.confidence,
                    rectified_confidence: e.confidence,
                    adjustment_reason: "No rectification applied".to_string(),
                    data: e.data.clone(),
                })
                .collect()
        };
        
        // Apply AI-guided strategy if enabled
        if self.options.strategies.contains(&RectificationStrategy::AIGuided) {
            if let Some(llm_client) = &self.llm_client {
                strategies_used.push(RectificationStrategy::AIGuided);
                self.apply_ai_guided_strategy(llm_client, &evidence, &mut rectified_evidence).await?;
            } else {
                warn!("AI-guided strategy enabled but no LLM client provided");
            }
        }
        
        // Apply pathway-based strategy if enabled
        if self.options.strategies.contains(&RectificationStrategy::PathwayBased) && self.options.use_pathway_analysis {
            if let Some(neo4j_client) = &self.neo4j_client {
                strategies_used.push(RectificationStrategy::PathwayBased);
                self.apply_pathway_strategy(neo4j_client, &evidence, &mut rectified_evidence).await?;
            } else {
                warn!("Pathway-based strategy enabled but no Neo4j client provided");
            }
        }
        
        // Apply interactome-based adjustments if enabled
        if self.options.use_interactome_analysis {
            if let Some(neo4j_client) = &self.neo4j_client {
                self.apply_interactome_adjustments(neo4j_client, &evidence.molecule_id, &mut rectified_evidence).await?;
            }
        }
        
        // Calculate overall confidence improvement
        let original_avg_confidence = evidence.evidence_items.iter()
            .map(|e| e.confidence)
            .sum::<f64>() / evidence.evidence_items.len() as f64;
        
        let rectified_avg_confidence = rectified_evidence.iter()
            .map(|e| e.rectified_confidence)
            .sum::<f64>() / rectified_evidence.len() as f64;
        
        let confidence_improvement = rectified_avg_confidence - original_avg_confidence;
        
        // Generate reasoning for rectification
        let reasoning = self.generate_rectification_reasoning(&evidence, &rectified_evidence, &strategies_used)?;
        
        // Create result
        let result = RectificationResult {
            original_evidence: evidence,
            rectified_evidence,
            confidence_improvement,
            reasoning,
            strategies_used,
            timestamp: chrono::Utc::now(),
        };
        
        Ok(result)
    }
    
    /// Apply consensus strategy for rectification
    fn apply_consensus_strategy(&self, evidence: &IntegratedEvidence) -> Result<Vec<RectifiedEvidence>> {
        debug!("Applying consensus strategy for rectification");
        
        let mut result = Vec::new();
        
        // Group evidence by type
        let mut evidence_by_type: HashMap<EvidenceType, Vec<&Evidence>> = HashMap::new();
        for ev in &evidence.evidence_items {
            evidence_by_type.entry(ev.evidence_type).or_default().push(ev);
        }
        
        // Process each evidence item
        for ev in &evidence.evidence_items {
            // Find corroborating evidence of different types
            let corroborating_types: Vec<EvidenceType> = evidence_by_type.keys()
                .filter(|&&t| t != ev.evidence_type)
                .copied()
                .collect();
            
            // Calculate confidence adjustment based on corroboration
            let mut adjustment = 0.0;
            let mut adjustment_reasons = Vec::new();
            
            for &corr_type in &corroborating_types {
                let corr_evidence = &evidence_by_type[&corr_type];
                
                // Simple heuristic: if there is corroborating evidence of another type,
                // increase confidence proportionally to that evidence's confidence
                if !corr_evidence.is_empty() {
                    let corr_confidence = corr_evidence.iter()
                        .map(|e| e.confidence)
                        .fold(0.0, f64::max);
                    
                    // Smaller boost for each corroborating type
                    let boost = 0.05 * corr_confidence;
                    adjustment += boost;
                    
                    adjustment_reasons.push(format!(
                        "Corroborated by {} evidence (confidence: {:.2})",
                        corr_type, corr_confidence
                    ));
                }
            }
            
            // Cap the adjustment
            adjustment = adjustment.min(self.options.max_confidence_improvement);
            
            // Apply the adjustment
            let new_confidence = (ev.confidence + adjustment).min(1.0);
            
            // Create a reason string
            let reason = if adjustment_reasons.is_empty() {
                "No corroborating evidence found".to_string()
            } else {
                adjustment_reasons.join("; ")
            };
            
            // Add to result
            result.push(RectifiedEvidence {
                original_id: ev.id.clone(),
                evidence_type: ev.evidence_type,
                original_confidence: ev.confidence,
                rectified_confidence: new_confidence,
                adjustment_reason: reason,
                data: ev.data.clone(),
            });
        }
        
        Ok(result)
    }
    
    /// Apply AI-guided strategy for rectification
    async fn apply_ai_guided_strategy(
        &self,
        llm_client: &LLMClient,
        evidence: &IntegratedEvidence,
        rectified_evidence: &mut Vec<RectifiedEvidence>,
    ) -> Result<()> {
        debug!("Applying AI-guided strategy for rectification");
        
        // Create a prompt for the LLM to analyze the evidence
        let prompt = self.create_llm_prompt(evidence)?;
        
        // Get LLM response
        let llm_response = llm_client.generate_completion(&prompt).await
            .context("Failed to get LLM response for evidence rectification")?;
        
        // Parse the LLM response to extract confidence adjustments
        let adjustments = self.parse_llm_response(&llm_response, evidence)
            .context("Failed to parse LLM response")?;
        
        debug!("LLM suggested {} confidence adjustments", adjustments.len());
        
        // Apply adjustments
        for (evidence_id, confidence_adjustment, reason) in adjustments {
            // Find the corresponding rectified evidence
            if let Some(rect_ev) = rectified_evidence.iter_mut()
                .find(|re| re.original_id == evidence_id) {
                
                // Apply the adjustment, respecting the maximum allowed improvement
                let capped_adjustment = confidence_adjustment.min(self.options.max_confidence_improvement);
                let new_confidence = (rect_ev.rectified_confidence + capped_adjustment).min(1.0).max(0.0);
                
                // Update the rectified evidence
                rect_ev.rectified_confidence = new_confidence;
                rect_ev.adjustment_reason = format!("{} + AI: {}", rect_ev.adjustment_reason, reason);
            }
        }
        
        Ok(())
    }
    
    /// Apply pathway-based strategy for rectification
    async fn apply_pathway_strategy(
        &self,
        neo4j_client: &Neo4jClient,
        evidence: &IntegratedEvidence,
        rectified_evidence: &mut Vec<RectifiedEvidence>,
    ) -> Result<()> {
        debug!("Applying pathway-based strategy for rectification");
        
        // Query Neo4j for pathway information about the molecule
        let molecule_id = &evidence.molecule_id;
        let pathway_query = format!(
            "MATCH (m:Molecule {{id: '{}'}})-[:PARTICIPATES_IN]->(p:Pathway)
             MATCH (p)<-[:PARTICIPATES_IN]-(other:Molecule)
             RETURN p.id AS pathway_id, p.name AS pathway_name, 
                    COUNT(other) AS molecule_count",
            molecule_id
        );
        
        let pathway_results = neo4j_client.execute_query(&pathway_query).await
            .context("Failed to query pathways from Neo4j")?;
        
        if pathway_results.is_empty() {
            debug!("No pathway information found for molecule {}", molecule_id);
            return Ok(());
        }
        
        // Apply confidence adjustments based on pathway participation
        for rect_ev in rectified_evidence.iter_mut() {
            // Higher confidence for molecules involved in multiple pathways
            let pathway_count = pathway_results.len();
            let pathway_boost = (0.01 * pathway_count as f64).min(0.1);
            
            // Apply the adjustment
            let new_confidence = (rect_ev.rectified_confidence + pathway_boost).min(1.0);
            
            // Update reason
            let pathway_names: Vec<String> = pathway_results.iter()
                .filter_map(|row| {
                    row.get::<String>("pathway_name").ok()
                })
                .take(3)
                .collect();
            
            let reason = if pathway_names.is_empty() {
                format!("Found in {} pathways", pathway_count)
            } else {
                format!("Found in {} pathways including: {}", 
                        pathway_count, pathway_names.join(", "))
            };
            
            rect_ev.rectified_confidence = new_confidence;
            rect_ev.adjustment_reason = format!("{} + Pathway: {}", rect_ev.adjustment_reason, reason);
        }
        
        Ok(())
    }
    
    /// Apply interactome-based adjustments
    async fn apply_interactome_adjustments(
        &self,
        neo4j_client: &Neo4jClient,
        molecule_id: &str,
        rectified_evidence: &mut Vec<RectifiedEvidence>,
    ) -> Result<()> {
        debug!("Applying interactome-based adjustments for molecule {}", molecule_id);
        
        // Query Neo4j for interaction information
        let interaction_query = format!(
            "MATCH (m:Molecule {{id: '{}'}})-[r:INTERACTS_WITH]-(other:Molecule)
             RETURN type(r) AS interaction_type, COUNT(other) AS interaction_count",
            molecule_id
        );
        
        let interaction_results = neo4j_client.execute_query(&interaction_query).await
            .context("Failed to query interactions from Neo4j")?;
        
        if interaction_results.is_empty() {
            debug!("No interaction information found for molecule {}", molecule_id);
            return Ok(());
        }
        
        // Apply confidence adjustments based on interaction network
        for rect_ev in rectified_evidence.iter_mut() {
            // Higher confidence for molecules with more interactions
            let total_interactions: i64 = interaction_results.iter()
                .filter_map(|row| row.get::<i64>("interaction_count").ok())
                .sum();
            
            // Apply boost based on interaction count
            let interaction_boost = (0.005 * total_interactions as f64).min(0.1);
            
            // Apply the adjustment
            let new_confidence = (rect_ev.rectified_confidence + interaction_boost).min(1.0);
            
            // Update reason
            rect_ev.rectified_confidence = new_confidence;
            rect_ev.adjustment_reason = format!("{} + Interactome: Found {} interactions", 
                                              rect_ev.adjustment_reason, total_interactions);
        }
        
        Ok(())
    }
    
    /// Create a prompt for the LLM to analyze evidence
    fn create_llm_prompt(&self, evidence: &IntegratedEvidence) -> Result<String> {
        let mut prompt = format!(
            "Analyze the molecular evidence for molecule ID '{}' and suggest confidence adjustments.\n\n",
            evidence.molecule_id
        );
        
        // Add evidence items to the prompt
        prompt.push_str("Evidence items:\n");
        
        for (i, ev) in evidence.evidence_items.iter().enumerate() {
            prompt.push_str(&format!(
                "{}. ID: {}, Type: {}, Source: {}, Confidence: {:.2}\n   Data: {}\n\n",
                i + 1, ev.id, ev.evidence_type, ev.source, ev.confidence, 
                serde_json::to_string_pretty(&ev.data).unwrap_or_default()
            ));
        }
        
        // Add conflicts if any
        if !evidence.conflicts.is_empty() {
            prompt.push_str("\nConflicts found:\n");
            
            for (i, conflict) in evidence.conflicts.iter().enumerate() {
                prompt.push_str(&format!(
                    "{}. {}\n   Severity: {:.2}\n   Involves evidence IDs: {}\n\n",
                    i + 1, conflict.description, conflict.severity,
                    conflict.evidence_ids.join(", ")
                ));
            }
        }
        
        // Add instructions for the LLM
        prompt.push_str("\nFor each evidence item, analyze its reliability and suggest:\n");
        prompt.push_str("1. A confidence adjustment (positive or negative number between -0.2 and 0.2)\n");
        prompt.push_str("2. A brief reason for the adjustment\n\n");
        prompt.push_str("Format your response as follows for each evidence item:\n");
        prompt.push_str("Evidence ID: <id>\nAdjustment: <value>\nReason: <reason>\n\n");
        
        Ok(prompt)
    }
    
    /// Parse the LLM response to extract confidence adjustments
    fn parse_llm_response(
        &self,
        response: &str,
        evidence: &IntegratedEvidence,
    ) -> Result<Vec<(String, f64, String)>> {
        let mut adjustments = Vec::new();
        
        // Simple parsing for the expected format
        let lines: Vec<&str> = response.lines().collect();
        let mut i = 0;
        
        while i < lines.len() {
            // Look for the evidence ID line
            if let Some(id_line) = lines.get(i) {
                if id_line.starts_with("Evidence ID:") {
                    let evidence_id = id_line
                        .trim_start_matches("Evidence ID:")
                        .trim()
                        .to_string();
                    
                    // Check if this is a valid evidence ID
                    if !evidence.evidence_items.iter().any(|e| e.id == evidence_id) {
                        i += 1;
                        continue;
                    }
                    
                    // Look for the adjustment line
                    if let Some(adj_line) = lines.get(i + 1) {
                        if adj_line.starts_with("Adjustment:") {
                            let adjustment_str = adj_line
                                .trim_start_matches("Adjustment:")
                                .trim();
                            
                            // Parse the adjustment as a f64
                            if let Ok(adjustment) = adjustment_str.parse::<f64>() {
                                // Look for the reason line
                                if let Some(reason_line) = lines.get(i + 2) {
                                    if reason_line.starts_with("Reason:") {
                                        let reason = reason_line
                                            .trim_start_matches("Reason:")
                                            .trim()
                                            .to_string();
                                        
                                        // Add to adjustments
                                        adjustments.push((evidence_id, adjustment, reason));
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            i += 1;
        }
        
        Ok(adjustments)
    }
    
    /// Generate reasoning for rectification
    fn generate_rectification_reasoning(
        &self,
        evidence: &IntegratedEvidence,
        rectified_evidence: &[RectifiedEvidence],
        strategies_used: &[RectificationStrategy],
    ) -> Result<Vec<String>> {
        let mut reasoning = Vec::new();
        
        // Overall reasoning
        reasoning.push(format!(
            "Rectification applied using strategies: {}",
            strategies_used.iter()
                .map(|s| format!("{:?}", s))
                .collect::<Vec<_>>()
                .join(", ")
        ));
        
        // Summarize confidence improvements
        let total_improvement = rectified_evidence.iter()
            .map(|re| re.rectified_confidence - re.original_confidence)
            .sum::<f64>();
        
        let avg_improvement = total_improvement / rectified_evidence.len() as f64;
        
        reasoning.push(format!(
            "Average confidence improvement: {:.2}",
            avg_improvement
        ));
        
        // Add reasoning for significant adjustments
        let significant_adjustments = rectified_evidence.iter()
            .filter(|re| (re.rectified_confidence - re.original_confidence).abs() > 0.05)
            .collect::<Vec<_>>();
        
        if !significant_adjustments.is_empty() {
            reasoning.push("Significant confidence adjustments:".to_string());
            
            for re in significant_adjustments {
                reasoning.push(format!(
                    "- {} evidence: {:.2} → {:.2} ({:+.2}) - {}",
                    re.evidence_type,
                    re.original_confidence,
                    re.rectified_confidence,
                    re.rectified_confidence - re.original_confidence,
                    re.adjustment_reason
                ));
            }
        }
        
        // Additional context if conflicts were present
        if !evidence.conflicts.is_empty() {
            reasoning.push(format!(
                "Rectification addressed {} evidence conflicts",
                evidence.conflicts.len()
            ));
        }
        
        Ok(reasoning)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_default_options() {
        let options = RectificationOptions::default();
        
        // Check default strategies
        assert!(options.strategies.contains(&RectificationStrategy::Consensus));
        assert!(options.strategies.contains(&RectificationStrategy::AIGuided));
        assert!(options.strategies.contains(&RectificationStrategy::PathwayBased));
        
        // Check other defaults
        assert!(options.max_confidence_improvement <= 0.5);
        assert!(options.use_pathway_analysis);
    }
} 