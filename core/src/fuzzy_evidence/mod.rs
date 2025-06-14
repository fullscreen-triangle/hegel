use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use anyhow::{Result, Context};

/// Fuzzy membership function types for evidence evaluation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum FuzzyMembershipFunction {
    /// Triangular membership function (low, peak, high)
    Triangular { low: f64, peak: f64, high: f64 },
    /// Trapezoidal membership function (low, low_peak, high_peak, high)
    Trapezoidal { low: f64, low_peak: f64, high_peak: f64, high: f64 },
    /// Gaussian membership function (center, sigma)
    Gaussian { center: f64, sigma: f64 },
    /// Sigmoid membership function (center, slope)
    Sigmoid { center: f64, slope: f64 },
}

impl FuzzyMembershipFunction {
    /// Calculate membership degree for a given value
    pub fn membership(&self, value: f64) -> f64 {
        match self {
            FuzzyMembershipFunction::Triangular { low, peak, high } => {
                if value <= *low || value >= *high {
                    0.0
                } else if value <= *peak {
                    (value - low) / (peak - low)
                } else {
                    (high - value) / (high - peak)
                }
            }
            FuzzyMembershipFunction::Trapezoidal { low, low_peak, high_peak, high } => {
                if value <= *low || value >= *high {
                    0.0
                } else if value <= *low_peak {
                    (value - low) / (low_peak - low)
                } else if value <= *high_peak {
                    1.0
                } else {
                    (high - value) / (high - high_peak)
                }
            }
            FuzzyMembershipFunction::Gaussian { center, sigma } => {
                let diff = value - center;
                (-0.5 * (diff / sigma).powi(2)).exp()
            }
            FuzzyMembershipFunction::Sigmoid { center, slope } => {
                1.0 / (1.0 + (-slope * (value - center)).exp())
            }
        }
    }
}

/// Fuzzy linguistic variables for evidence quality
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FuzzyLinguisticVariable {
    pub name: String,
    pub universe: (f64, f64), // (min, max) range
    pub terms: HashMap<String, FuzzyMembershipFunction>,
}

impl FuzzyLinguisticVariable {
    /// Create a new fuzzy linguistic variable for evidence confidence
    pub fn evidence_confidence() -> Self {
        let mut terms = HashMap::new();
        
        // Define linguistic terms for evidence confidence
        terms.insert("very_low".to_string(), 
            FuzzyMembershipFunction::Triangular { low: 0.0, peak: 0.0, high: 0.2 });
        terms.insert("low".to_string(), 
            FuzzyMembershipFunction::Triangular { low: 0.0, peak: 0.2, high: 0.4 });
        terms.insert("medium".to_string(), 
            FuzzyMembershipFunction::Triangular { low: 0.2, peak: 0.5, high: 0.8 });
        terms.insert("high".to_string(), 
            FuzzyMembershipFunction::Triangular { low: 0.6, peak: 0.8, high: 1.0 });
        terms.insert("very_high".to_string(), 
            FuzzyMembershipFunction::Triangular { low: 0.8, peak: 1.0, high: 1.0 });
        
        FuzzyLinguisticVariable {
            name: "evidence_confidence".to_string(),
            universe: (0.0, 1.0),
            terms,
        }
    }
    
    /// Create a fuzzy linguistic variable for evidence agreement
    pub fn evidence_agreement() -> Self {
        let mut terms = HashMap::new();
        
        terms.insert("conflicting".to_string(), 
            FuzzyMembershipFunction::Trapezoidal { low: 0.0, low_peak: 0.0, high_peak: 0.3, high: 0.5 });
        terms.insert("neutral".to_string(), 
            FuzzyMembershipFunction::Triangular { low: 0.3, peak: 0.5, high: 0.7 });
        terms.insert("supporting".to_string(), 
            FuzzyMembershipFunction::Trapezoidal { low: 0.5, low_peak: 0.7, high_peak: 1.0, high: 1.0 });
        
        FuzzyLinguisticVariable {
            name: "evidence_agreement".to_string(),
            universe: (0.0, 1.0),
            terms,
        }
    }
    
    /// Get membership degrees for all terms given a value
    pub fn fuzzify(&self, value: f64) -> HashMap<String, f64> {
        self.terms.iter()
            .map(|(term, func)| (term.clone(), func.membership(value)))
            .collect()
    }
}

/// Fuzzy evidence representation with continuous membership degrees
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FuzzyEvidence {
    pub id: String,
    pub source: String,
    pub evidence_type: String,
    pub raw_value: f64,
    pub confidence_memberships: HashMap<String, f64>, // Fuzzy memberships for confidence levels
    pub agreement_memberships: HashMap<String, f64>,  // Fuzzy memberships for agreement levels
    pub contextual_factors: HashMap<String, f64>,     // Additional fuzzy factors
    pub temporal_decay: f64,                          // Time-based confidence decay
    pub uncertainty_bounds: (f64, f64),               // Confidence interval bounds
}

impl FuzzyEvidence {
    /// Create new fuzzy evidence from raw evidence
    pub fn from_raw_evidence(
        id: String,
        source: String,
        evidence_type: String,
        raw_value: f64,
        timestamp: chrono::DateTime<chrono::Utc>,
    ) -> Self {
        let confidence_var = FuzzyLinguisticVariable::evidence_confidence();
        
        // Calculate temporal decay (evidence gets less reliable over time)
        let age_hours = chrono::Utc::now().signed_duration_since(timestamp).num_hours() as f64;
        let temporal_decay = (-age_hours / (24.0 * 30.0)).exp(); // Decay over ~30 days
        
        // Calculate uncertainty bounds based on evidence type
        let uncertainty_bounds = match evidence_type.as_str() {
            "mass_spec" => (raw_value * 0.95, raw_value * 1.05),
            "genomics" => (raw_value * 0.90, raw_value * 1.10),
            "literature" => (raw_value * 0.85, raw_value * 1.15),
            _ => (raw_value * 0.90, raw_value * 1.10),
        };
        
        FuzzyEvidence {
            id,
            source,
            evidence_type,
            raw_value,
            confidence_memberships: confidence_var.fuzzify(raw_value),
            agreement_memberships: HashMap::new(), // Will be calculated during integration
            contextual_factors: HashMap::new(),
            temporal_decay,
            uncertainty_bounds,
        }
    }
    
    /// Calculate defuzzified confidence score using centroid method
    pub fn defuzzified_confidence(&self) -> f64 {
        let mut numerator = 0.0;
        let mut denominator = 0.0;
        
        for (term, membership) in &self.confidence_memberships {
            let term_value = match term.as_str() {
                "very_low" => 0.1,
                "low" => 0.3,
                "medium" => 0.5,
                "high" => 0.8,
                "very_high" => 0.95,
                _ => 0.5,
            };
            
            numerator += term_value * membership * self.temporal_decay;
            denominator += membership;
        }
        
        if denominator > 0.0 {
            numerator / denominator
        } else {
            0.5 // Default neutral confidence
        }
    }
}

/// Fuzzy rule for evidence integration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FuzzyRule {
    pub id: String,
    pub antecedent: Vec<FuzzyCondition>,
    pub consequent: FuzzyConsequent,
    pub weight: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FuzzyCondition {
    pub variable: String,
    pub term: String,
    pub operator: FuzzyOperator,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum FuzzyOperator {
    Is,
    IsNot,
    GreaterThan,
    LessThan,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FuzzyConsequent {
    pub variable: String,
    pub term: String,
    pub adjustment: f64,
}

/// Hybrid Fuzzy-Bayesian Evidence Network
#[derive(Debug)]
pub struct FuzzyBayesianNetwork {
    pub nodes: HashMap<String, EvidenceNode>,
    pub edges: Vec<EvidenceEdge>,
    pub fuzzy_rules: Vec<FuzzyRule>,
    pub linguistic_variables: HashMap<String, FuzzyLinguisticVariable>,
    pub objective_functions: HashMap<String, ObjectiveFunction>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvidenceNode {
    pub id: String,
    pub evidence_type: String,
    pub fuzzy_evidence: Option<FuzzyEvidence>,
    pub prior_probability: f64,
    pub posterior_probability: f64,
    pub network_influence: f64, // Influence from connected nodes
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvidenceEdge {
    pub from_node: String,
    pub to_node: String,
    pub relationship_type: EvidenceRelationship,
    pub strength: f64,
    pub fuzzy_strength: HashMap<String, f64>, // Fuzzy representation of relationship strength
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EvidenceRelationship {
    Supports,
    Contradicts,
    Corroborates,
    Implies,
    Requires,
}

/// Granular objective function for evidence optimization
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObjectiveFunction {
    pub name: String,
    pub components: Vec<ObjectiveComponent>,
    pub weights: HashMap<String, f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObjectiveComponent {
    pub name: String,
    pub function_type: ObjectiveFunctionType,
    pub parameters: HashMap<String, f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ObjectiveFunctionType {
    MaximizeConfidence,
    MinimizeUncertainty,
    MaximizeConsistency,
    MinimizeConflicts,
    MaximizeNetworkCoherence,
}

impl FuzzyBayesianNetwork {
    /// Create a new fuzzy-Bayesian evidence network
    pub fn new() -> Self {
        let mut linguistic_variables = HashMap::new();
        linguistic_variables.insert("confidence".to_string(), FuzzyLinguisticVariable::evidence_confidence());
        linguistic_variables.insert("agreement".to_string(), FuzzyLinguisticVariable::evidence_agreement());
        
        let mut objective_functions = HashMap::new();
        objective_functions.insert("default".to_string(), ObjectiveFunction::default_molecular_identity());
        
        FuzzyBayesianNetwork {
            nodes: HashMap::new(),
            edges: Vec::new(),
            fuzzy_rules: Self::default_fuzzy_rules(),
            linguistic_variables,
            objective_functions,
        }
    }
    
    /// Add evidence to the network
    pub fn add_evidence(&mut self, evidence: FuzzyEvidence) -> Result<()> {
        let node = EvidenceNode {
            id: evidence.id.clone(),
            evidence_type: evidence.evidence_type.clone(),
            fuzzy_evidence: Some(evidence),
            prior_probability: 0.5, // Neutral prior
            posterior_probability: 0.5,
            network_influence: 0.0,
        };
        
        self.nodes.insert(node.id.clone(), node);
        Ok(())
    }
    
    /// Predict missing evidence using network structure
    pub async fn predict_missing_evidence(&self, partial_evidence: &[String]) -> Result<Vec<EvidencePrediction>> {
        let mut predictions = Vec::new();
        
        // Find nodes that are not in the partial evidence set
        let missing_nodes: Vec<&EvidenceNode> = self.nodes.values()
            .filter(|node| !partial_evidence.contains(&node.id))
            .collect();
        
        for missing_node in missing_nodes {
            // Calculate prediction based on connected evidence
            let connected_evidence = self.get_connected_evidence(&missing_node.id);
            
            if !connected_evidence.is_empty() {
                let prediction = self.calculate_evidence_prediction(missing_node, &connected_evidence)?;
                predictions.push(prediction);
            }
        }
        
        // Sort predictions by confidence
        predictions.sort_by(|a, b| b.confidence.partial_cmp(&a.confidence).unwrap_or(std::cmp::Ordering::Equal));
        
        Ok(predictions)
    }
    
    /// Update network using fuzzy-Bayesian inference
    pub fn update_network(&mut self) -> Result<()> {
        // Step 1: Apply fuzzy rules to calculate fuzzy outputs
        self.apply_fuzzy_rules()?;
        
        // Step 2: Update Bayesian probabilities
        self.update_bayesian_probabilities()?;
        
        // Step 3: Calculate network influence
        self.calculate_network_influence()?;
        
        // Step 4: Optimize using objective functions
        self.optimize_with_objective_functions()?;
        
        Ok(())
    }
    
    /// Apply fuzzy rules to evidence
    fn apply_fuzzy_rules(&mut self) -> Result<()> {
        for rule in &self.fuzzy_rules.clone() {
            let activation_strength = self.calculate_rule_activation(rule)?;
            
            if activation_strength > 0.0 {
                self.apply_rule_consequent(rule, activation_strength)?;
            }
        }
        Ok(())
    }
    
    /// Update Bayesian probabilities based on evidence
    fn update_bayesian_probabilities(&mut self) -> Result<()> {
        for node in self.nodes.values_mut() {
            if let Some(evidence) = &node.fuzzy_evidence {
                // Bayesian update: P(H|E) = P(E|H) * P(H) / P(E)
                let likelihood = evidence.defuzzified_confidence();
                let prior = node.prior_probability;
                
                // Simplified Bayesian update (in practice, would need proper normalization)
                let posterior = (likelihood * prior) / (likelihood * prior + (1.0 - likelihood) * (1.0 - prior));
                node.posterior_probability = posterior;
            }
        }
        Ok(())
    }
    
    /// Calculate network influence between connected nodes
    fn calculate_network_influence(&mut self) -> Result<()> {
        for edge in &self.edges.clone() {
            let influence = self.calculate_edge_influence(edge)?;
            
            if let Some(to_node) = self.nodes.get_mut(&edge.to_node) {
                to_node.network_influence += influence * edge.strength;
            }
        }
        Ok(())
    }
    
    /// Optimize network using granular objective functions
    fn optimize_with_objective_functions(&mut self) -> Result<()> {
        for (name, objective) in &self.objective_functions.clone() {
            let optimization_result = self.evaluate_objective_function(objective)?;
            self.apply_optimization_adjustments(name, &optimization_result)?;
        }
        Ok(())
    }
    
    // Helper methods for network operations
    fn get_connected_evidence(&self, node_id: &str) -> Vec<&EvidenceNode> {
        self.edges.iter()
            .filter(|edge| edge.to_node == node_id || edge.from_node == node_id)
            .filter_map(|edge| {
                let connected_id = if edge.to_node == node_id { &edge.from_node } else { &edge.to_node };
                self.nodes.get(connected_id)
            })
            .collect()
    }
    
    fn calculate_evidence_prediction(&self, target_node: &EvidenceNode, connected_evidence: &[&EvidenceNode]) -> Result<EvidencePrediction> {
        let mut prediction_confidence = 0.0;
        let mut prediction_value = 0.0;
        let mut total_weight = 0.0;
        
        for evidence_node in connected_evidence {
            if let Some(evidence) = &evidence_node.fuzzy_evidence {
                let weight = evidence.defuzzified_confidence();
                prediction_confidence += evidence.defuzzified_confidence() * weight;
                prediction_value += evidence.raw_value * weight;
                total_weight += weight;
            }
        }
        
        if total_weight > 0.0 {
            prediction_confidence /= total_weight;
            prediction_value /= total_weight;
        }
        
        Ok(EvidencePrediction {
            node_id: target_node.id.clone(),
            predicted_value: prediction_value,
            confidence: prediction_confidence,
            supporting_evidence: connected_evidence.iter().map(|n| n.id.clone()).collect(),
            reasoning: format!("Predicted based on {} connected evidence nodes", connected_evidence.len()),
        })
    }
    
    fn calculate_rule_activation(&self, rule: &FuzzyRule) -> Result<f64> {
        let mut activation = 1.0;
        
        for condition in &rule.antecedent {
            // Find the relevant node and calculate condition satisfaction
            let condition_satisfaction = self.evaluate_fuzzy_condition(condition)?;
            activation = activation.min(condition_satisfaction); // AND operation (minimum)
        }
        
        Ok(activation * rule.weight)
    }
    
    fn evaluate_fuzzy_condition(&self, _condition: &FuzzyCondition) -> Result<f64> {
        // This would evaluate the fuzzy condition against the current network state
        // For now, return a placeholder
        Ok(0.5)
    }
    
    fn apply_rule_consequent(&mut self, _rule: &FuzzyRule, _activation: f64) -> Result<()> {
        // Apply the rule's consequent with the given activation strength
        // This would modify the network state based on the rule
        Ok(())
    }
    
    fn calculate_edge_influence(&self, edge: &EvidenceEdge) -> Result<f64> {
        if let (Some(from_node), Some(to_node)) = (self.nodes.get(&edge.from_node), self.nodes.get(&edge.to_node)) {
            let base_influence = match edge.relationship_type {
                EvidenceRelationship::Supports => from_node.posterior_probability,
                EvidenceRelationship::Contradicts => 1.0 - from_node.posterior_probability,
                EvidenceRelationship::Corroborates => from_node.posterior_probability * 0.8,
                EvidenceRelationship::Implies => from_node.posterior_probability * 0.9,
                EvidenceRelationship::Requires => if from_node.posterior_probability > 0.5 { 1.0 } else { 0.0 },
            };
            
            Ok(base_influence)
        } else {
            Ok(0.0)
        }
    }
    
    fn evaluate_objective_function(&self, objective: &ObjectiveFunction) -> Result<ObjectiveResult> {
        let mut total_score = 0.0;
        let mut component_scores = HashMap::new();
        
        for component in &objective.components {
            let score = self.evaluate_objective_component(component)?;
            let weight = objective.weights.get(&component.name).unwrap_or(&1.0);
            
            component_scores.insert(component.name.clone(), score);
            total_score += score * weight;
        }
        
        Ok(ObjectiveResult {
            total_score,
            component_scores,
            recommendations: self.generate_optimization_recommendations(objective, &component_scores)?,
        })
    }
    
    fn evaluate_objective_component(&self, component: &ObjectiveComponent) -> Result<f64> {
        match component.function_type {
            ObjectiveFunctionType::MaximizeConfidence => {
                let avg_confidence: f64 = self.nodes.values()
                    .filter_map(|node| node.fuzzy_evidence.as_ref())
                    .map(|evidence| evidence.defuzzified_confidence())
                    .sum::<f64>() / self.nodes.len() as f64;
                Ok(avg_confidence)
            }
            ObjectiveFunctionType::MinimizeUncertainty => {
                let avg_uncertainty: f64 = self.nodes.values()
                    .filter_map(|node| node.fuzzy_evidence.as_ref())
                    .map(|evidence| {
                        let (low, high) = evidence.uncertainty_bounds;
                        high - low
                    })
                    .sum::<f64>() / self.nodes.len() as f64;
                Ok(1.0 - avg_uncertainty) // Convert to maximization problem
            }
            ObjectiveFunctionType::MaximizeConsistency => {
                // Calculate consistency based on agreement between connected nodes
                let mut consistency_sum = 0.0;
                let mut edge_count = 0;
                
                for edge in &self.edges {
                    if let (Some(from_node), Some(to_node)) = (self.nodes.get(&edge.from_node), self.nodes.get(&edge.to_node)) {
                        let consistency = match edge.relationship_type {
                            EvidenceRelationship::Supports => {
                                1.0 - (from_node.posterior_probability - to_node.posterior_probability).abs()
                            }
                            EvidenceRelationship::Contradicts => {
                                (from_node.posterior_probability - to_node.posterior_probability).abs()
                            }
                            _ => 0.5, // Neutral for other relationships
                        };
                        consistency_sum += consistency;
                        edge_count += 1;
                    }
                }
                
                Ok(if edge_count > 0 { consistency_sum / edge_count as f64 } else { 0.5 })
            }
            ObjectiveFunctionType::MinimizeConflicts => {
                let conflict_count = self.edges.iter()
                    .filter(|edge| matches!(edge.relationship_type, EvidenceRelationship::Contradicts))
                    .count();
                Ok(1.0 - (conflict_count as f64 / self.edges.len().max(1) as f64))
            }
            ObjectiveFunctionType::MaximizeNetworkCoherence => {
                // Calculate network coherence based on connectivity and consistency
                let connectivity = self.edges.len() as f64 / (self.nodes.len().max(1) as f64).powi(2);
                let consistency = self.evaluate_objective_component(&ObjectiveComponent {
                    name: "consistency".to_string(),
                    function_type: ObjectiveFunctionType::MaximizeConsistency,
                    parameters: HashMap::new(),
                })?;
                Ok((connectivity + consistency) / 2.0)
            }
        }
    }
    
    fn apply_optimization_adjustments(&mut self, _objective_name: &str, result: &ObjectiveResult) -> Result<()> {
        // Apply adjustments based on optimization results
        for recommendation in &result.recommendations {
            self.apply_optimization_recommendation(recommendation)?;
        }
        Ok(())
    }
    
    fn apply_optimization_recommendation(&mut self, recommendation: &OptimizationRecommendation) -> Result<()> {
        match recommendation.action_type {
            OptimizationAction::AdjustConfidence => {
                if let Some(node) = self.nodes.get_mut(&recommendation.target_node) {
                    node.posterior_probability = (node.posterior_probability + recommendation.adjustment).clamp(0.0, 1.0);
                }
            }
            OptimizationAction::AddEdge => {
                // Add new edge based on recommendation
            }
            OptimizationAction::RemoveEdge => {
                // Remove edge based on recommendation
            }
            OptimizationAction::UpdateWeight => {
                // Update edge weight
            }
        }
        Ok(())
    }
    
    fn generate_optimization_recommendations(&self, _objective: &ObjectiveFunction, scores: &HashMap<String, f64>) -> Result<Vec<OptimizationRecommendation>> {
        let mut recommendations = Vec::new();
        
        // Generate recommendations based on objective function performance
        for (component_name, &score) in scores {
            if score < 0.5 { // Below threshold
                recommendations.push(OptimizationRecommendation {
                    target_node: "global".to_string(),
                    action_type: OptimizationAction::AdjustConfidence,
                    adjustment: 0.1,
                    reasoning: format!("Improve {} score from {:.2}", component_name, score),
                });
            }
        }
        
        Ok(recommendations)
    }
    
    /// Default fuzzy rules for molecular evidence
    fn default_fuzzy_rules() -> Vec<FuzzyRule> {
        vec![
            FuzzyRule {
                id: "high_confidence_support".to_string(),
                antecedent: vec![
                    FuzzyCondition {
                        variable: "confidence".to_string(),
                        term: "high".to_string(),
                        operator: FuzzyOperator::Is,
                    }
                ],
                consequent: FuzzyConsequent {
                    variable: "posterior".to_string(),
                    term: "increase".to_string(),
                    adjustment: 0.1,
                },
                weight: 1.0,
            },
            FuzzyRule {
                id: "conflicting_evidence_penalty".to_string(),
                antecedent: vec![
                    FuzzyCondition {
                        variable: "agreement".to_string(),
                        term: "conflicting".to_string(),
                        operator: FuzzyOperator::Is,
                    }
                ],
                consequent: FuzzyConsequent {
                    variable: "posterior".to_string(),
                    term: "decrease".to_string(),
                    adjustment: -0.2,
                },
                weight: 1.0,
            },
        ]
    }
}

impl ObjectiveFunction {
    /// Default objective function for molecular identity validation
    pub fn default_molecular_identity() -> Self {
        let mut weights = HashMap::new();
        weights.insert("confidence".to_string(), 0.3);
        weights.insert("uncertainty".to_string(), 0.2);
        weights.insert("consistency".to_string(), 0.25);
        weights.insert("conflicts".to_string(), 0.15);
        weights.insert("coherence".to_string(), 0.1);
        
        ObjectiveFunction {
            name: "molecular_identity_validation".to_string(),
            components: vec![
                ObjectiveComponent {
                    name: "confidence".to_string(),
                    function_type: ObjectiveFunctionType::MaximizeConfidence,
                    parameters: HashMap::new(),
                },
                ObjectiveComponent {
                    name: "uncertainty".to_string(),
                    function_type: ObjectiveFunctionType::MinimizeUncertainty,
                    parameters: HashMap::new(),
                },
                ObjectiveComponent {
                    name: "consistency".to_string(),
                    function_type: ObjectiveFunctionType::MaximizeConsistency,
                    parameters: HashMap::new(),
                },
                ObjectiveComponent {
                    name: "conflicts".to_string(),
                    function_type: ObjectiveFunctionType::MinimizeConflicts,
                    parameters: HashMap::new(),
                },
                ObjectiveComponent {
                    name: "coherence".to_string(),
                    function_type: ObjectiveFunctionType::MaximizeNetworkCoherence,
                    parameters: HashMap::new(),
                },
            ],
            weights,
        }
    }
}

/// Result of evidence prediction
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvidencePrediction {
    pub node_id: String,
    pub predicted_value: f64,
    pub confidence: f64,
    pub supporting_evidence: Vec<String>,
    pub reasoning: String,
}

/// Result of objective function evaluation
#[derive(Debug, Clone)]
pub struct ObjectiveResult {
    pub total_score: f64,
    pub component_scores: HashMap<String, f64>,
    pub recommendations: Vec<OptimizationRecommendation>,
}

/// Optimization recommendation
#[derive(Debug, Clone)]
pub struct OptimizationRecommendation {
    pub target_node: String,
    pub action_type: OptimizationAction,
    pub adjustment: f64,
    pub reasoning: String,
}

#[derive(Debug, Clone)]
pub enum OptimizationAction {
    AdjustConfidence,
    AddEdge,
    RemoveEdge,
    UpdateWeight,
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_fuzzy_membership_functions() {
        let triangular = FuzzyMembershipFunction::Triangular { low: 0.0, peak: 0.5, high: 1.0 };
        
        assert_eq!(triangular.membership(0.0), 0.0);
        assert_eq!(triangular.membership(0.5), 1.0);
        assert_eq!(triangular.membership(1.0), 0.0);
        assert_eq!(triangular.membership(0.25), 0.5);
    }
    
    #[test]
    fn test_fuzzy_linguistic_variable() {
        let confidence_var = FuzzyLinguisticVariable::evidence_confidence();
        let memberships = confidence_var.fuzzify(0.7);
        
        assert!(memberships.contains_key("medium"));
        assert!(memberships.contains_key("high"));
        assert!(memberships["high"] > 0.0);
    }
    
    #[test]
    fn test_fuzzy_bayesian_network() {
        let mut network = FuzzyBayesianNetwork::new();
        
        let evidence = FuzzyEvidence::from_raw_evidence(
            "test_evidence".to_string(),
            "mass_spec".to_string(),
            "spectral_match".to_string(),
            0.8,
            chrono::Utc::now(),
        );
        
        assert!(network.add_evidence(evidence).is_ok());
        assert!(network.nodes.contains_key("test_evidence"));
    }
} 