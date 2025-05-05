//! Decision Engine Module
//!
//! This module provides a decision engine for making informed decisions about
//! molecules and validation processes based on various factors.

use anyhow::Result;
use log::{info, debug};
use serde::{Serialize, Deserialize};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

/// Initialize the decision engine module
pub fn initialize() -> Result<()> {
    info!("Initializing decision engine module");
    info!("Decision engine module initialized successfully");
    Ok(())
}

/// Decision engine for making molecule-related decisions
#[derive(Debug, Clone)]
pub struct DecisionEngine {
    /// Decision rules loaded from configuration
    rules: Arc<Mutex<HashMap<String, Vec<DecisionRule>>>>,
    
    /// Cache of previously made decisions
    decision_cache: Arc<Mutex<HashMap<String, Decision>>>,
}

impl DecisionEngine {
    /// Create a new decision engine
    pub fn new() -> Result<Self> {
        Ok(Self {
            rules: Arc::new(Mutex::new(HashMap::new())),
            decision_cache: Arc::new(Mutex::new(HashMap::new())),
        })
    }
    
    /// Load decision rules from a file
    pub fn load_rules(&self, path: &str) -> Result<()> {
        debug!("Loading decision rules from {}", path);
        
        // In a real implementation, this would load rules from a YAML/JSON file
        // For now, just create some default rules
        
        let mut rules = self.rules.lock().unwrap();
        
        // Rules for selecting data sources
        rules.insert(
            "select_data_sources".to_string(),
            vec![
                DecisionRule {
                    name: "drug_molecules".to_string(),
                    conditions: vec![
                        RuleCondition::Equals("molecule_type".to_string(), "drug".to_string()),
                    ],
                    action: DecisionAction::AddDataSources(vec![
                        "chembl".to_string(),
                        "drugbank".to_string(),
                    ]),
                    weight: 1.0,
                },
                DecisionRule {
                    name: "metabolites".to_string(),
                    conditions: vec![
                        RuleCondition::Equals("molecule_type".to_string(), "metabolite".to_string()),
                    ],
                    action: DecisionAction::AddDataSources(vec![
                        "hmdb".to_string(),
                        "kegg".to_string(),
                    ]),
                    weight: 1.0,
                },
                DecisionRule {
                    name: "natural_products".to_string(),
                    conditions: vec![
                        RuleCondition::Equals("molecule_type".to_string(), "natural_product".to_string()),
                    ],
                    action: DecisionAction::AddDataSources(vec![
                        "biocyc".to_string(),
                        "chebi".to_string(),
                    ]),
                    weight: 1.0,
                },
                DecisionRule {
                    name: "peptides".to_string(),
                    conditions: vec![
                        RuleCondition::Equals("molecule_type".to_string(), "peptide".to_string()),
                    ],
                    action: DecisionAction::AddDataSources(vec![
                        "uniprot".to_string(),
                    ]),
                    weight: 1.0,
                },
                DecisionRule {
                    name: "inchikey_identifier".to_string(),
                    conditions: vec![
                        RuleCondition::Equals("identifier_type".to_string(), "inchikey".to_string()),
                    ],
                    action: DecisionAction::AddDataSources(vec![
                        "pubchem".to_string(),
                        "chembl".to_string(),
                    ]),
                    weight: 0.8,
                },
                DecisionRule {
                    name: "name_identifier".to_string(),
                    conditions: vec![
                        RuleCondition::Equals("identifier_type".to_string(), "name".to_string()),
                    ],
                    action: DecisionAction::AddDataSources(vec![
                        "pubchem".to_string(),
                        "chembl".to_string(),
                        "chebi".to_string(),
                    ]),
                    weight: 0.6,
                },
            ],
        );
        
        // Rules for validation thresholds
        rules.insert(
            "validation_threshold".to_string(),
            vec![
                DecisionRule {
                    name: "high_confidence_drugs".to_string(),
                    conditions: vec![
                        RuleCondition::Equals("molecule_type".to_string(), "drug".to_string()),
                        RuleCondition::GreaterThan("source_count".to_string(), "3".to_string()),
                    ],
                    action: DecisionAction::SetThreshold(0.9),
                    weight: 1.0,
                },
                DecisionRule {
                    name: "standard_metabolites".to_string(),
                    conditions: vec![
                        RuleCondition::Equals("molecule_type".to_string(), "metabolite".to_string()),
                    ],
                    action: DecisionAction::SetThreshold(0.7),
                    weight: 1.0,
                },
                DecisionRule {
                    name: "unknown_molecules".to_string(),
                    conditions: vec![
                        RuleCondition::NotExists("molecule_type".to_string()),
                    ],
                    action: DecisionAction::SetThreshold(0.6),
                    weight: 0.5,
                },
            ],
        );
        
        debug!("Loaded {} rule sets", rules.len());
        Ok(())
    }
    
    /// Make a decision based on the provided factors
    pub fn make_decision(&self, decision_type: &str, factors: &[DecisionFactor]) -> Result<Decision> {
        debug!("Making decision of type {} with {} factors", decision_type, factors.len());
        
        // Create a cache key for this decision
        let cache_key = self.create_cache_key(decision_type, factors);
        
        // Check if this decision is cached
        {
            let cache = self.decision_cache.lock().unwrap();
            if let Some(decision) = cache.get(&cache_key) {
                debug!("Using cached decision for {}", cache_key);
                return Ok(decision.clone());
            }
        }
        
        // Get the rules for this decision type
        let rules = {
            let rules_map = self.rules.lock().unwrap();
            match rules_map.get(decision_type) {
                Some(rules) => rules.clone(),
                None => {
                    debug!("No rules found for decision type: {}", decision_type);
                    Vec::new()
                }
            }
        };
        
        // Create a decision result based on the applicable rules
        let mut decision = Decision {
            decision_type: decision_type.to_string(),
            data_sources: Vec::new(),
            threshold: 0.5,  // Default threshold
            confidence: 0.0,
            explanation: String::new(),
        };
        
        // Convert factors to a map for easier lookup
        let factor_map: HashMap<String, String> = factors.iter()
            .map(|f| (f.name.clone(), f.value.clone()))
            .collect();
        
        // Apply each applicable rule
        let mut applicable_rules = Vec::new();
        
        for rule in &rules {
            if self.rule_applies(&rule, &factor_map) {
                debug!("Rule '{}' applies", rule.name);
                applicable_rules.push(rule);
                
                // Apply the rule's action
                match &rule.action {
                    DecisionAction::AddDataSources(sources) => {
                        for source in sources {
                            if !decision.data_sources.contains(source) {
                                decision.data_sources.push(source.clone());
                            }
                        }
                    },
                    DecisionAction::SetThreshold(threshold) => {
                        decision.threshold = *threshold;
                    },
                    DecisionAction::Custom(_) => {
                        // Custom actions would be handled specifically
                    },
                }
            }
        }
        
        // Calculate confidence based on applicable rules
        if !applicable_rules.is_empty() {
            let total_weight: f64 = applicable_rules.iter().map(|r| r.weight).sum();
            decision.confidence = if total_weight > 0.0 { 
                total_weight / applicable_rules.len() as f64 
            } else { 
                0.0 
            };
        }
        
        // Generate explanation for the decision
        decision.explanation = self.generate_explanation(&decision, &applicable_rules);
        
        // Cache the decision
        {
            let mut cache = self.decision_cache.lock().unwrap();
            cache.insert(cache_key, decision.clone());
        }
        
        Ok(decision)
    }
    
    /// Check if a rule applies based on the given factors
    fn rule_applies(&self, rule: &DecisionRule, factors: &HashMap<String, String>) -> bool {
        for condition in &rule.conditions {
            match condition {
                RuleCondition::Equals(name, value) => {
                    if !factors.get(name).map_or(false, |v| v == value) {
                        return false;
                    }
                },
                RuleCondition::NotEquals(name, value) => {
                    if factors.get(name).map_or(false, |v| v == value) {
                        return false;
                    }
                },
                RuleCondition::GreaterThan(name, value) => {
                    let factor_value = factors.get(name).map(|v| v.parse::<f64>().ok()).flatten();
                    let condition_value = value.parse::<f64>().ok();
                    
                    if let (Some(fv), Some(cv)) = (factor_value, condition_value) {
                        if fv <= cv {
                            return false;
                        }
                    } else {
                        return false;
                    }
                },
                RuleCondition::LessThan(name, value) => {
                    let factor_value = factors.get(name).map(|v| v.parse::<f64>().ok()).flatten();
                    let condition_value = value.parse::<f64>().ok();
                    
                    if let (Some(fv), Some(cv)) = (factor_value, condition_value) {
                        if fv >= cv {
                            return false;
                        }
                    } else {
                        return false;
                    }
                },
                RuleCondition::Contains(name, value) => {
                    if !factors.get(name).map_or(false, |v| v.contains(value)) {
                        return false;
                    }
                },
                RuleCondition::Exists(name) => {
                    if !factors.contains_key(name) {
                        return false;
                    }
                },
                RuleCondition::NotExists(name) => {
                    if factors.contains_key(name) {
                        return false;
                    }
                },
            }
        }
        
        true
    }
    
    /// Generate an explanation for a decision
    fn generate_explanation(&self, decision: &Decision, rules: &[&DecisionRule]) -> String {
        if rules.is_empty() {
            return "No specific rules applied; using default settings.".to_string();
        }
        
        let rule_names: Vec<String> = rules.iter().map(|r| r.name.clone()).collect();
        format!(
            "Decision made with {:.0}% confidence based on {} rules: {}. {}",
            decision.confidence * 100.0,
            rules.len(),
            rule_names.join(", "),
            if !decision.data_sources.is_empty() {
                format!("Selected data sources: {}.", decision.data_sources.join(", "))
            } else {
                "".to_string()
            }
        )
    }
    
    /// Create a cache key for a decision
    fn create_cache_key(&self, decision_type: &str, factors: &[DecisionFactor]) -> String {
        let mut factor_strings: Vec<String> = factors.iter()
            .map(|f| format!("{}={}", f.name, f.value))
            .collect();
        
        factor_strings.sort();
        format!("{}-{}", decision_type, factor_strings.join("-"))
    }
}

/// Decision factor used for making decisions
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DecisionFactor {
    /// Name of the factor
    pub name: String,
    
    /// Value of the factor
    pub value: String,
}

impl DecisionFactor {
    /// Create a new decision factor
    pub fn new(name: &str, value: String) -> Self {
        Self {
            name: name.to_string(),
            value,
        }
    }
}

/// Result of a decision
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Decision {
    /// Type of decision
    pub decision_type: String,
    
    /// Data sources to use (for source selection decisions)
    pub data_sources: Vec<String>,
    
    /// Threshold value (for threshold decisions)
    pub threshold: f64,
    
    /// Confidence in the decision (0.0 - 1.0)
    pub confidence: f64,
    
    /// Explanation for the decision
    pub explanation: String,
}

/// Rule for making decisions
#[derive(Debug, Clone, Serialize, Deserialize)]
struct DecisionRule {
    /// Name of the rule
    name: String,
    
    /// Conditions for the rule to apply
    conditions: Vec<RuleCondition>,
    
    /// Action to take if the rule applies
    action: DecisionAction,
    
    /// Weight of the rule (used for confidence calculation)
    weight: f64,
}

/// Condition for a decision rule
#[derive(Debug, Clone, Serialize, Deserialize)]
enum RuleCondition {
    /// Factor value equals the specified value
    Equals(String, String),
    
    /// Factor value does not equal the specified value
    NotEquals(String, String),
    
    /// Factor value is greater than the specified value
    GreaterThan(String, String),
    
    /// Factor value is less than the specified value
    LessThan(String, String),
    
    /// Factor value contains the specified substring
    Contains(String, String),
    
    /// Factor exists
    Exists(String),
    
    /// Factor does not exist
    NotExists(String),
}

/// Action to take when a rule applies
#[derive(Debug, Clone, Serialize, Deserialize)]
enum DecisionAction {
    /// Add data sources to the decision
    AddDataSources(Vec<String>),
    
    /// Set a threshold value
    SetThreshold(f64),
    
    /// Custom action (for complex decisions)
    Custom(String),
}
