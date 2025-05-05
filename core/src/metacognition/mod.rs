//! Metacognition Module
//!
//! This module provides advanced reasoning, decision-making, and machine learning
//! capabilities for the Hegel system, allowing it to make informed decisions about
//! molecular identity and validation.

use anyhow::Result;
use log::{info, debug};

pub mod molecule_processor;
pub mod decision;
pub mod llm;
pub mod memory;

/// Initialize the metacognition module
pub fn initialize() -> Result<()> {
    info!("Initializing metacognition module");
    
    // Initialize submodules
    decision::initialize()?;
    llm::initialize()?;
    memory::initialize()?;
    
    info!("Metacognition module initialized successfully");
    Ok(())
}

/// Metacognition system for making high-level decisions about molecular identity
pub struct MetacognitionSystem {
    /// Decision engine for making molecule-related decisions
    decision_engine: decision::DecisionEngine,
    
    /// LLM interface for natural language reasoning
    llm_interface: llm::LLMInterface,
    
    /// Memory system for storing and retrieving context
    memory_system: memory::MemorySystem,
    
    /// Molecule processor for data retrieval and integration
    molecule_processor: molecule_processor::MoleculeProcessor,
}

impl MetacognitionSystem {
    /// Create a new metacognition system
    pub fn new() -> Result<Self> {
        let decision_engine = decision::DecisionEngine::new()?;
        let llm_interface = llm::LLMInterface::new()?;
        let memory_system = memory::MemorySystem::new()?;
        
        let python_api_endpoint = std::env::var("HEGEL_PYTHON_API_ENDPOINT")
            .unwrap_or_else(|_| "http://localhost:8000".to_string());
        
        let molecule_processor = molecule_processor::MoleculeProcessor::new(
            decision_engine.clone(),
            llm_interface.clone(),
            python_api_endpoint,
        );
        
        Ok(Self {
            decision_engine,
            llm_interface,
            memory_system,
            molecule_processor,
        })
    }
    
    /// Process a molecule and make decisions about its identity
    pub async fn process_molecule(
        &self,
        identifier: &str,
        id_type: molecule_processor::MoleculeIdType,
    ) -> Result<molecule_processor::MoleculeResponse> {
        // Create a new context for this processing session
        let mut context = memory::context::Context::new();
        
        // Set up the molecule request
        let request = molecule_processor::MoleculeRequest {
            identifier: identifier.to_string(),
            id_type,
            primary_source: molecule_processor::DataSource::PubChem,
            additional_sources: vec![],
            include_pathways: true,
            include_interactions: true,
            include_targets: true,
        };
        
        // Process the molecule
        let response = self.molecule_processor.process_molecule(request, &mut context).await?;
        
        // Store the context for future reference
        self.memory_system.store_context(context)?;
        
        Ok(response)
    }
    
    /// Validate a molecule's identity with confidence scoring
    pub async fn validate_molecule_identity(
        &self,
        molecule_id: &str,
    ) -> Result<ValidationResult> {
        debug!("Validating molecule identity for {}", molecule_id);
        
        // Retrieve molecule data
        let evidence = self.molecule_processor.get_evidence_summary(molecule_id).await?;
        
        // Extract molecule properties
        let properties = if let Some(props) = evidence.get("properties") {
            props.clone()
        } else {
            serde_json::Value::Object(serde_json::Map::new())
        };
        
        // Get sources that validate this molecule
        let sources = if let Some(sources_array) = evidence.get("sources") {
            sources_array.as_array()
                .map(|arr| arr.len())
                .unwrap_or(0)
        } else {
            0
        };
        
        // Calculate confidence based on number of confirming sources and properties
        let confidence = calculate_confidence(sources, &properties);
        
        // Determine if the molecule is valid
        let is_valid = confidence > 0.5;
        
        Ok(ValidationResult {
            molecule_id: molecule_id.to_string(),
            is_valid,
            confidence,
            evidence: evidence.clone(),
            explanation: format!(
                "Molecule validated with {:.1}% confidence based on {} sources",
                confidence * 100.0,
                sources
            ),
        })
    }
}

/// Result of validating a molecule's identity
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ValidationResult {
    /// ID of the molecule being validated
    pub molecule_id: String,
    
    /// Whether the molecule is considered valid
    pub is_valid: bool,
    
    /// Confidence score (0.0 - 1.0)
    pub confidence: f64,
    
    /// Evidence used for validation
    pub evidence: serde_json::Value,
    
    /// Human-readable explanation of the validation result
    pub explanation: String,
}

/// Calculate confidence in a molecule's identity based on evidence
fn calculate_confidence(sources: usize, properties: &serde_json::Value) -> f64 {
    // Base confidence from number of sources
    let source_confidence = match sources {
        0 => 0.0,
        1 => 0.3,
        2 => 0.5,
        3 => 0.7,
        4..=5 => 0.8,
        _ => 0.9,
    };
    
    // Additional confidence from properties
    let property_confidence = if let Some(props) = properties.as_object() {
        let property_count = props.len();
        match property_count {
            0 => 0.0,
            1..=3 => 0.1,
            4..=10 => 0.2,
            11..=20 => 0.3,
            _ => 0.4,
        }
    } else {
        0.0
    };
    
    // Combine confidence scores, capping at 1.0
    f64::min(source_confidence + property_confidence, 1.0)
}
