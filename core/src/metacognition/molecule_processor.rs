use anyhow::{anyhow, Context, Result};
use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use tokio::process::Command;
use std::collections::HashMap;
use std::time::Duration;
use crate::memory::context::Context as HegelContext;
use crate::metacognition::decision::{Decision, DecisionEngine, DecisionFactor};
use crate::metacognition::llm::LLMInterface;

/// The set of data sources that can be queried
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DataSource {
    PubChem,
    ChEMBL,
    KEGG,
    HMDB,
    DrugBank,
    MetaCyc,
    ChEBI,
    UniProt,
    Reactome,
    WikiPathways,
    BioCyc,
    Custom(String),
}

impl DataSource {
    pub fn to_string(&self) -> String {
        match self {
            DataSource::PubChem => "pubchem".to_string(),
            DataSource::ChEMBL => "chembl".to_string(),
            DataSource::KEGG => "kegg".to_string(),
            DataSource::HMDB => "hmdb".to_string(),
            DataSource::DrugBank => "drugbank".to_string(),
            DataSource::MetaCyc => "metacyc".to_string(),
            DataSource::ChEBI => "chebi".to_string(),
            DataSource::UniProt => "uniprot".to_string(),
            DataSource::Reactome => "reactome".to_string(),
            DataSource::WikiPathways => "wikipathways".to_string(),
            DataSource::BioCyc => "biocyc".to_string(),
            DataSource::Custom(name) => name.clone(),
        }
    }
}

/// Molecule identifier types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MoleculeIdType {
    InChIKey,
    InChI,
    SMILES,
    Name,
    Formula,
    CAS,
    PubChemCID,
    ChEMBLID,
    KEGGID,
    HMDBID,
    DrugBankID,
    ChEBIID,
    Custom(String),
}

impl MoleculeIdType {
    pub fn to_string(&self) -> String {
        match self {
            MoleculeIdType::InChIKey => "inchikey".to_string(),
            MoleculeIdType::InChI => "inchi".to_string(),
            MoleculeIdType::SMILES => "smiles".to_string(),
            MoleculeIdType::Name => "name".to_string(),
            MoleculeIdType::Formula => "formula".to_string(),
            MoleculeIdType::CAS => "cas".to_string(),
            MoleculeIdType::PubChemCID => "pubchem_cid".to_string(),
            MoleculeIdType::ChEMBLID => "chembl_id".to_string(),
            MoleculeIdType::KEGGID => "kegg_id".to_string(),
            MoleculeIdType::HMDBID => "hmdb_id".to_string(),
            MoleculeIdType::DrugBankID => "drugbank_id".to_string(),
            MoleculeIdType::ChEBIID => "chebi_id".to_string(),
            MoleculeIdType::Custom(name) => name.clone(),
        }
    }
}

/// Molecule retrieval request
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MoleculeRequest {
    pub identifier: String,
    pub id_type: MoleculeIdType,
    pub primary_source: DataSource,
    pub additional_sources: Vec<DataSource>,
    pub include_pathways: bool,
    pub include_interactions: bool,
    pub include_targets: bool,
}

/// Molecule data response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MoleculeResponse {
    pub success: bool,
    pub molecule_id: Option<String>,
    pub data: Option<serde_json::Value>,
    pub error: Option<String>,
    pub sources_queried: Vec<String>,
    pub processing_time_ms: u64,
}

/// Molecule processor orchestrates the retrieval and integration of molecular data
pub struct MoleculeProcessor {
    decision_engine: DecisionEngine,
    llm_interface: LLMInterface,
    python_api_endpoint: String,
}

impl MoleculeProcessor {
    pub fn new(decision_engine: DecisionEngine, llm_interface: LLMInterface, api_endpoint: String) -> Self {
        Self {
            decision_engine,
            llm_interface,
            python_api_endpoint: api_endpoint,
        }
    }
    
    /// Process a molecule request by retrieving data from multiple sources and building
    /// the molecule network
    pub async fn process_molecule(&self, request: MoleculeRequest, context: &mut HegelContext) -> Result<MoleculeResponse> {
        let start_time = std::time::Instant::now();
        
        // Determine optimal sources to query based on the molecule type and ID
        let sources = self.determine_data_sources(&request, context).await?;
        
        // Collect sources as strings for the response
        let sources_queried: Vec<String> = sources.iter().map(|s| s.to_string()).collect();
        
        // Call the Python API to retrieve molecule data
        let molecule_data = self.retrieve_molecule_data(&request, &sources).await
            .context("Failed to retrieve molecule data")?;
        
        // Check if we got valid data
        if molecule_data.is_null() || !molecule_data.is_object() {
            return Ok(MoleculeResponse {
                success: false,
                molecule_id: None,
                data: None,
                error: Some("No valid molecule data retrieved".to_string()),
                sources_queried,
                processing_time_ms: start_time.elapsed().as_millis() as u64,
            });
        }
        
        // Add molecule to the network
        let molecule_id = self.add_to_molecule_network(&molecule_data).await
            .context("Failed to add molecule to network")?;
        
        // Extract context information from the molecule data to update the context
        self.update_context_with_molecule(&molecule_data, context).await?;
        
        Ok(MoleculeResponse {
            success: true,
            molecule_id: Some(molecule_id),
            data: Some(molecule_data.clone()),
            error: None,
            sources_queried,
            processing_time_ms: start_time.elapsed().as_millis() as u64,
        })
    }
    
    /// Determine the most relevant data sources to query for a given molecule
    async fn determine_data_sources(&self, request: &MoleculeRequest, context: &HegelContext) -> Result<Vec<DataSource>> {
        // Always include the primary source
        let mut sources = vec![request.primary_source.clone()];
        
        // If additional sources are explicitly specified, use those
        if !request.additional_sources.is_empty() {
            sources.extend(request.additional_sources.clone());
            return Ok(sources);
        }
        
        // Otherwise, use the decision engine to determine additional sources
        // based on the molecule type and identifier
        
        // Create decision factors
        let mut factors = vec![
            DecisionFactor::new("identifier_type", request.id_type.to_string()),
            DecisionFactor::new("primary_source", request.primary_source.to_string()),
        ];
        
        // Add context factors if available
        if let Some(domain) = context.get_value("domain") {
            factors.push(DecisionFactor::new("domain", domain));
        }
        
        if let Some(molecule_type) = context.get_value("molecule_type") {
            factors.push(DecisionFactor::new("molecule_type", molecule_type));
        }
        
        // Ask the decision engine to determine additional sources
        let decision = self.decision_engine.make_decision(
            "select_data_sources",
            &factors,
            &context.get_history()
        ).await?;
        
        // Parse the decision result to get source names
        if let Some(sources_value) = decision.result.get("additional_sources") {
            if let Some(sources_arr) = sources_value.as_array() {
                for source in sources_arr {
                    if let Some(source_str) = source.as_str() {
                        match source_str {
                            "pubchem" => sources.push(DataSource::PubChem),
                            "chembl" => sources.push(DataSource::ChEMBL),
                            "kegg" => sources.push(DataSource::KEGG),
                            "hmdb" => sources.push(DataSource::HMDB),
                            "drugbank" => sources.push(DataSource::DrugBank),
                            "metacyc" => sources.push(DataSource::MetaCyc),
                            "chebi" => sources.push(DataSource::ChEBI),
                            "uniprot" => sources.push(DataSource::UniProt),
                            "reactome" => sources.push(DataSource::Reactome),
                            "wikipathways" => sources.push(DataSource::WikiPathways),
                            "biocyc" => sources.push(DataSource::BioCyc),
                            _ => sources.push(DataSource::Custom(source_str.to_string())),
                        }
                    }
                }
            }
        }
        
        // Deduplicate sources
        sources.sort_by_key(|s| s.to_string());
        sources.dedup();
        
        Ok(sources)
    }
    
    /// Retrieve molecule data from the Python API
    async fn retrieve_molecule_data(&self, request: &MoleculeRequest, sources: &[DataSource]) -> Result<serde_json::Value> {
        // Convert sources to strings
        let source_strings: Vec<String> = sources.iter().map(|s| s.to_string()).collect();
        
        // Prepare the HTTP client
        let client = reqwest::Client::new();
        
        // Prepare the request payload
        let payload = serde_json::json!({
            "identifier": request.identifier,
            "id_type": request.id_type.to_string(),
            "primary_source": request.primary_source.to_string(),
            "include_sources": source_strings,
            "include_pathways": request.include_pathways,
            "include_interactions": request.include_interactions,
            "include_targets": request.include_targets,
        });
        
        // Call the Python API
        let response = client.post(&format!("{}/api/molecules/retrieve", self.python_api_endpoint))
            .json(&payload)
            .timeout(Duration::from_secs(30))
            .send()
            .await
            .context("Failed to send request to Python API")?;
        
        // Check response status
        if !response.status().is_success() {
            let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
            return Err(anyhow!("API request failed with status {}: {}", response.status(), error_text));
        }
        
        // Parse response JSON
        let data = response.json::<serde_json::Value>().await
            .context("Failed to parse response JSON")?;
        
        Ok(data)
    }
    
    /// Add the molecule to the network database
    async fn add_to_molecule_network(&self, molecule_data: &serde_json::Value) -> Result<String> {
        // Prepare the HTTP client
        let client = reqwest::Client::new();
        
        // Call the Python API to add the molecule to the network
        let response = client.post(&format!("{}/api/molecules/network/add", self.python_api_endpoint))
            .json(molecule_data)
            .timeout(Duration::from_secs(30))
            .send()
            .await
            .context("Failed to send request to add molecule to network")?;
        
        // Check response status
        if !response.status().is_success() {
            let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
            return Err(anyhow!("API request failed with status {}: {}", response.status(), error_text));
        }
        
        // Parse response JSON
        let data = response.json::<serde_json::Value>().await
            .context("Failed to parse response JSON")?;
        
        // Extract the molecule ID
        let molecule_id = data.get("id")
            .and_then(|id| id.as_str())
            .ok_or_else(|| anyhow!("No molecule ID in response"))?
            .to_string();
        
        Ok(molecule_id)
    }
    
    /// Update the context with information from the molecule
    async fn update_context_with_molecule(&self, molecule_data: &serde_json::Value, context: &mut HegelContext) -> Result<()> {
        // Extract key properties from the molecule data to add to context
        if let Some(obj) = molecule_data.as_object() {
            // Add basic molecule information
            if let Some(name) = obj.get("name").and_then(|v| v.as_str()) {
                context.set_value("current_molecule_name", name.to_string());
            }
            
            if let Some(formula) = obj.get("formula").and_then(|v| v.as_str()) {
                context.set_value("current_molecule_formula", formula.to_string());
            }
            
            // Determine molecule type from the data
            let molecule_type = self.infer_molecule_type(obj).await?;
            context.set_value("current_molecule_type", molecule_type);
            
            // Extract source information
            if let Some(source) = obj.get("source").and_then(|v| v.as_str()) {
                context.set_value("current_molecule_source", source.to_string());
            }
            
            // Extract identifiers
            for (key, value) in obj.iter() {
                if key.ends_with("_id") || vec!["inchikey", "inchi", "smiles"].contains(&key.as_str()) {
                    if let Some(id_value) = value.as_str() {
                        context.set_value(&format!("current_molecule_{}", key), id_value.to_string());
                    }
                }
            }
        }
        
        Ok(())
    }
    
    /// Infer the type of molecule from its properties
    async fn infer_molecule_type(&self, molecule_data: &serde_json::Map<String, serde_json::Value>) -> Result<String> {
        // Use the LLM to infer the molecule type based on properties
        let properties_json = serde_json::to_string(molecule_data).unwrap_or_default();
        
        let prompt = format!(
            "Based on the following molecule properties, classify the molecule into one of these categories: \
            'small molecule', 'metabolite', 'drug', 'peptide', 'protein', 'lipid', 'nucleic acid', 'carbohydrate', 'unknown'. \
            Only respond with the category name, nothing else.\n\nProperties: {}", 
            properties_json
        );
        
        let response = self.llm_interface.complete(&prompt, None, None).await?;
        let molecule_type = response.trim().to_lowercase();
        
        // Validate the response
        let valid_types = [
            "small molecule", "metabolite", "drug", "peptide", "protein", 
            "lipid", "nucleic acid", "carbohydrate", "unknown"
        ];
        
        if valid_types.contains(&molecule_type.as_str()) {
            Ok(molecule_type)
        } else {
            // Default to "small molecule" if LLM returns something unexpected
            Ok("small molecule".to_string())
        }
    }
    
    /// Get a summary of evidence for a molecule's identity
    pub async fn get_evidence_summary(&self, molecule_id: &str) -> Result<serde_json::Value> {
        // Prepare the HTTP client
        let client = reqwest::Client::new();
        
        // Call the Python API to get evidence summary
        let response = client.get(&format!("{}/api/molecules/{}/evidence", self.python_api_endpoint, molecule_id))
            .timeout(Duration::from_secs(30))
            .send()
            .await
            .context("Failed to send request for evidence summary")?;
        
        // Check response status
        if !response.status().is_success() {
            let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
            return Err(anyhow!("API request failed with status {}: {}", response.status(), error_text));
        }
        
        // Parse response JSON
        let data = response.json::<serde_json::Value>().await
            .context("Failed to parse response JSON")?;
        
        Ok(data)
    }
    
    /// Get the molecule network neighborhood
    pub async fn get_molecule_neighborhood(&self, 
                                         molecule_id: &str, 
                                         relationship_types: Option<Vec<String>>,
                                         max_depth: Option<u32>,
                                         limit: Option<u32>) -> Result<serde_json::Value> {
        // Prepare the HTTP client
        let client = reqwest::Client::new();
        
        // Prepare query parameters
        let mut params = Vec::new();
        
        if let Some(rel_types) = &relationship_types {
            for rel_type in rel_types {
                params.push(("relationship_types", rel_type));
            }
        }
        
        if let Some(depth) = max_depth {
            params.push(("max_depth", &depth.to_string()));
        }
        
        if let Some(lim) = limit {
            params.push(("limit", &lim.to_string()));
        }
        
        // Call the Python API to get molecule neighborhood
        let response = client.get(&format!("{}/api/molecules/{}/neighborhood", self.python_api_endpoint, molecule_id))
            .query(&params)
            .timeout(Duration::from_secs(30))
            .send()
            .await
            .context("Failed to send request for molecule neighborhood")?;
        
        // Check response status
        if !response.status().is_success() {
            let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
            return Err(anyhow!("API request failed with status {}: {}", response.status(), error_text));
        }
        
        // Parse response JSON
        let data = response.json::<serde_json::Value>().await
            .context("Failed to parse response JSON")?;
        
        Ok(data)
    }
    
    /// Process a batch of molecules
    pub async fn process_molecule_batch(&self, 
                                      requests: Vec<MoleculeRequest>,
                                      context: &mut HegelContext) -> Result<Vec<MoleculeResponse>> {
        let mut responses = Vec::with_capacity(requests.len());
        
        // Process each molecule request
        for request in requests {
            match self.process_molecule(request, context).await {
                Ok(response) => responses.push(response),
                Err(e) => {
                    // Create an error response
                    responses.push(MoleculeResponse {
                        success: false,
                        molecule_id: None,
                        data: None,
                        error: Some(format!("Failed to process molecule: {}", e)),
                        sources_queried: vec![],
                        processing_time_ms: 0,
                    });
                }
            }
        }
        
        Ok(responses)
    }
} 