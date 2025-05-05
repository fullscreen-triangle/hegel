use actix_cors::Cors;
use actix_web::{get, post, web, App, HttpResponse, HttpServer, Responder};
use hegel::{
    graph::{schema::MoleculeNode, neo4j::Neo4jClient},
    metacognition::{llm::LLMClient, memory::MemorySystem},
    processing::{evidence::{EvidenceProcessor, Evidence, EvidenceType}, 
                rectifier::EvidenceRectifier,
                genomics::{GenomicsData, GenomicsProcessor},
                mass_spec::{MassSpecData, MassSpecProcessor}},
};
use serde::{Deserialize, Serialize};
use std::{collections::HashMap, sync::Arc};
use tokio::sync::Mutex;

// Data structures for API requests and responses
#[derive(Debug, Serialize, Deserialize)]
struct AnalysisRequest {
    molecule_ids: Vec<String>,
    evidence_type: String,
    confidence_threshold: Option<f64>,
}

#[derive(Debug, Serialize, Deserialize)]
struct RectificationRequest {
    evidence_data: HashMap<String, Vec<Evidence>>,
    rectification_options: RectificationOptions,
}

#[derive(Debug, Serialize, Deserialize)]
struct RectificationOptions {
    use_ai_guidance: bool,
    confidence_threshold: f64,
    include_pathway_analysis: bool,
    include_interactome_analysis: bool,
}

#[derive(Debug, Serialize, Deserialize)]
struct Evidence {
    source: String,
    data: serde_json::Value,
    confidence: f64,
}

#[derive(Debug, Serialize, Deserialize)]
struct AnalysisResponse {
    results: HashMap<String, MoleculeAnalysis>,
    meta: AnalysisMeta,
}

#[derive(Debug, Serialize, Deserialize)]
struct MoleculeAnalysis {
    molecule_id: String,
    evidence_count: usize,
    rectified_evidence: Vec<RectifiedEvidence>,
    pathways: Vec<PathwayData>,
    interactions: Vec<InteractionData>,
    confidence_score: f64,
}

#[derive(Debug, Serialize, Deserialize)]
struct RectifiedEvidence {
    source: String,
    original_confidence: f64,
    rectified_confidence: f64,
    data: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
struct PathwayData {
    pathway_id: String,
    name: String,
    molecules: Vec<String>,
    confidence: f64,
}

#[derive(Debug, Serialize, Deserialize)]
struct InteractionData {
    source_molecule: String,
    target_molecule: String,
    interaction_type: String,
    evidence_count: usize,
    confidence: f64,
}

#[derive(Debug, Serialize, Deserialize)]
struct AnalysisMeta {
    timestamp: String,
    version: String,
    execution_time_ms: u64,
}

// New request structures for genomics and mass spec data
#[derive(Debug, Serialize, Deserialize)]
struct GenomicsRequest {
    /// Molecule ID this data relates to
    molecule_id: String,
    
    /// The genomics data to process
    data: GenomicsData,
}

#[derive(Debug, Serialize, Deserialize)]
struct MassSpecRequest {
    /// Molecule ID this data relates to
    molecule_id: String,
    
    /// The mass spec data to process
    data: MassSpecData,
}

#[derive(Debug, Serialize, Deserialize)]
struct ProcessedDataResponse {
    /// Molecule ID the results relate to
    molecule_id: String,
    
    /// Evidence generated from the data
    evidence: Vec<Evidence>,
    
    /// Overall confidence score
    confidence_score: f64,
    
    /// Processing metadata
    metadata: HashMap<String, serde_json::Value>,
}

// Shared application state
struct AppState {
    neo4j_client: Arc<Mutex<Neo4jClient>>,
    llm_client: Arc<Mutex<LLMClient>>,
    memory_system: Arc<Mutex<MemorySystem>>,
    evidence_processor: Arc<Mutex<EvidenceProcessor>>,
    evidence_rectifier: Arc<Mutex<EvidenceRectifier>>,
    genomics_processor: Arc<Mutex<GenomicsProcessor>>,
    mass_spec_processor: Arc<Mutex<MassSpecProcessor>>,
}

// API routes
#[post("/api/analyze")]
async fn analyze_evidence(
    data: web::Json<AnalysisRequest>,
    state: web::Data<AppState>,
) -> impl Responder {
    println!("Received analysis request: {:?}", data);

    // Process the evidence using the Rust orchestrator
    let evidence_processor = state.evidence_processor.lock().await;
    let evidence_rectifier = state.evidence_rectifier.lock().await;
    let neo4j_client = state.neo4j_client.lock().await;

    // Process evidence with the full implementation
    let start_time = std::time::Instant::now();
    let mut results = HashMap::new();
    
    for molecule_id in &data.molecule_ids {
        info!("Processing evidence for molecule: {}", molecule_id);
        
        // Fetch evidence from Neo4j
        let evidence_fetch_query = format!(
            "MATCH (e:Evidence)-[:RELATED_TO]->(m:Molecule {{id: $molecule_id}}) 
             RETURN e.id as id, e.source as source, e.confidence as confidence, 
             e.data as data, e.type as type"
        );
        
        let params = serde_json::json!({
            "molecule_id": molecule_id,
        });
        
        let driver = neo4j_client.connect().await.map_err(|e| {
            error!("Failed to connect to Neo4j: {}", e);
            HttpResponse::InternalServerError().json(serde_json::json!({
                "error": format!("Database connection error: {}", e)
            }))
        })?;
        
        let evidence_results = driver.run_query(&evidence_fetch_query, params).await.map_err(|e| {
            error!("Failed to fetch evidence: {}", e);
            HttpResponse::InternalServerError().json(serde_json::json!({
                "error": format!("Evidence retrieval error: {}", e)
            }))
        })?;
        
        // Convert to Evidence objects
        let mut evidences = Vec::new();
        for result in evidence_results {
            let id = result.get("id").and_then(|v| v.as_str()).unwrap_or("unknown");
            let source = result.get("source").and_then(|v| v.as_str()).unwrap_or("unknown");
            let confidence = result.get("confidence").and_then(|v| v.as_f64()).unwrap_or(0.5);
            let data = result.get("data").unwrap_or(&serde_json::Value::Null);
            
            let evidence = Evidence {
                source: source.to_string(),
                data: data.clone(),
                confidence,
            };
            
            evidences.push(evidence);
        }
        
        // Filter evidence by type if specified
        if let Some(evidence_type) = data.evidence_type.strip_prefix("type:") {
            evidences.retain(|e| {
                e.source.to_lowercase().contains(&evidence_type.to_lowercase())
            });
        }
        
        // Apply confidence threshold if specified
        if let Some(threshold) = data.confidence_threshold {
            evidences.retain(|e| e.confidence >= threshold);
        }
        
        // Process evidences through the evidence processor
        let processor_config = evidence_processor.get_config().clone();
        let processed_evidences = evidences.iter()
            .map(|e| {
                let mut processed = e.clone();
                // Apply processing rules based on source
                match e.source.to_lowercase().as_str() {
                    "genomics" => processed.confidence *= processor_config.genomics_weight,
                    "mass_spec" => processed.confidence *= processor_config.mass_spec_weight,
                    "literature" => processed.confidence *= processor_config.literature_weight,
                    _ => {}
                }
                processed
            })
            .collect::<Vec<_>>();
        
        // Get pathway data
        let pathways = get_molecule_pathways(&driver, molecule_id).await?;
        
        // Get interaction data
        let interactions = get_molecule_interactions(&driver, molecule_id).await?;
        
        // Apply rectification if confidence_threshold was specified
        let rectified_evidences = if data.confidence_threshold.is_some() {
            let rectifier_options = evidence_rectifier.get_options().clone();
            
            // Use rectifier
            processed_evidences.iter()
                .map(|evidence| {
                    let mut rectified = RectifiedEvidence {
                        source: evidence.source.clone(),
                        original_confidence: evidence.confidence,
                        rectified_confidence: evidence.confidence,
                        data: evidence.data.clone(),
                    };
                    
                    // Apply rectification logic
                    if evidence.confidence < 0.5 {
                        // Lower confidence evidence gets a smaller boost
                        rectified.rectified_confidence = evidence.confidence * 1.1;
                    } else if evidence.confidence < 0.8 {
                        // Medium confidence evidence gets moderate boost
                        rectified.rectified_confidence = evidence.confidence * 1.2;
                    } else {
                        // High confidence evidence gets small adjustment to prevent overconfidence
                        rectified.rectified_confidence = 0.9 + evidence.confidence * 0.08;
                    }
                    
                    // Cap at 0.99
                    rectified.rectified_confidence = rectified.rectified_confidence.min(0.99);
                    
                    rectified
                })
                .collect()
        } else {
            // No rectification requested
            processed_evidences.iter()
                .map(|evidence| RectifiedEvidence {
                    source: evidence.source.clone(),
                    original_confidence: evidence.confidence,
                    rectified_confidence: evidence.confidence,
                    data: evidence.data.clone(),
                })
                .collect()
        };
        
        // Calculate average confidence
        let confidence_score = if rectified_evidences.is_empty() {
            0.0
        } else {
            rectified_evidences.iter()
                .map(|e| e.rectified_confidence)
                .sum::<f64>() / rectified_evidences.len() as f64
        };
        
        results.insert(
            molecule_id.clone(),
            MoleculeAnalysis {
                molecule_id: molecule_id.clone(),
                evidence_count: rectified_evidences.len(),
                rectified_evidence: rectified_evidences,
                pathways,
                interactions,
                confidence_score,
            },
        );
    }
    
    let elapsed = start_time.elapsed().as_millis() as u64;

    let response = AnalysisResponse {
        results,
        meta: AnalysisMeta {
            timestamp: chrono::Utc::now().to_rfc3339(),
            version: "0.1.0".to_string(),
            execution_time_ms: elapsed,
        },
    };

    HttpResponse::Ok().json(response)
}

// Helper function to get pathway data for a molecule
async fn get_molecule_pathways(driver: &Neo4jDriver, molecule_id: &str) -> Result<Vec<PathwayData>, HttpResponse> {
    let pathway_query = format!(
        "MATCH (m:Molecule {{id: $molecule_id}})-[:PART_OF]->(p:Pathway) 
         MATCH (other:Molecule)-[:PART_OF]->(p) 
         WITH p, COLLECT(other.id) as molecules 
         RETURN p.id as pathway_id, p.name as name, molecules, p.confidence as confidence"
    );
    
    let params = serde_json::json!({
        "molecule_id": molecule_id,
    });
    
    let pathway_results = driver.run_query(&pathway_query, params).await.map_err(|e| {
        error!("Failed to fetch pathway data: {}", e);
        HttpResponse::InternalServerError().json(serde_json::json!({
            "error": format!("Pathway data retrieval error: {}", e)
        }))
    })?;
    
    let mut pathways = Vec::new();
    for result in pathway_results {
        let pathway_id = result.get("pathway_id").and_then(|v| v.as_str()).unwrap_or("unknown");
        let name = result.get("name").and_then(|v| v.as_str()).unwrap_or("Unknown Pathway");
        let confidence = result.get("confidence").and_then(|v| v.as_f64()).unwrap_or(0.5);
        
        let molecules = if let Some(mol_arr) = result.get("molecules").and_then(|v| v.as_array()) {
            mol_arr.iter()
                .filter_map(|m| m.as_str().map(|s| s.to_string()))
                .collect()
        } else {
            Vec::new()
        };
        
        pathways.push(PathwayData {
            pathway_id: pathway_id.to_string(),
            name: name.to_string(),
            molecules,
            confidence,
        });
    }
    
    Ok(pathways)
}

// Helper function to get interaction data for a molecule
async fn get_molecule_interactions(driver: &Neo4jDriver, molecule_id: &str) -> Result<Vec<InteractionData>, HttpResponse> {
    let interaction_query = format!(
        "MATCH (m:Molecule {{id: $molecule_id}})-[r]->(target:Molecule) 
         RETURN target.id as target_id, type(r) as type, target.name as target_name, 
         r.evidence_count as evidence_count, r.confidence as confidence"
    );
    
    let params = serde_json::json!({
        "molecule_id": molecule_id,
    });
    
    let interaction_results = driver.run_query(&interaction_query, params).await.map_err(|e| {
        error!("Failed to fetch interaction data: {}", e);
        HttpResponse::InternalServerError().json(serde_json::json!({
            "error": format!("Interaction data retrieval error: {}", e)
        }))
    })?;
    
    let mut interactions = Vec::new();
    for result in interaction_results {
        let target_id = result.get("target_id").and_then(|v| v.as_str()).unwrap_or("unknown");
        let interaction_type = result.get("type").and_then(|v| v.as_str()).unwrap_or("interacts_with");
        let evidence_count = result.get("evidence_count").and_then(|v| v.as_u64()).unwrap_or(1) as usize;
        let confidence = result.get("confidence").and_then(|v| v.as_f64()).unwrap_or(0.5);
        
        interactions.push(InteractionData {
            source_molecule: molecule_id.to_string(),
            target_molecule: target_id.to_string(),
            interaction_type: interaction_type.to_string(),
            evidence_count,
            confidence,
        });
    }
    
    Ok(interactions)
}

#[post("/api/rectify")]
async fn rectify_evidence(
    data: web::Json<RectificationRequest>,
    state: web::Data<AppState>,
) -> impl Responder {
    println!("Received rectification request: {:?}", data);

    // Use the AI-guided evidence rectifier
    let evidence_rectifier = state.evidence_rectifier.lock().await;
    let llm_client = state.llm_client.lock().await;
    let memory_system = state.memory_system.lock().await;

    let start_time = std::time::Instant::now();
    let mut results = HashMap::new();
    
    for (molecule_id, evidences) in &data.evidence_data {
        info!("Rectifying evidence for molecule: {}", molecule_id);
        
        let mut rectified_evidences = Vec::new();
        let mut all_explanations = Vec::new();
        
        // Get contextual data if needed
        let context_data = if data.rectification_options.include_pathway_analysis || 
                            data.rectification_options.include_interactome_analysis {
            let mut context = serde_json::Map::new();
            
            // Connect to Neo4j
            let neo4j_client = state.neo4j_client.lock().await;
            if let Ok(driver) = neo4j_client.connect().await {
                // Get pathway data if requested
                if data.rectification_options.include_pathway_analysis {
                    if let Ok(pathways) = get_molecule_pathways(&driver, molecule_id).await {
                        context.insert("pathways".to_string(), serde_json::to_value(pathways).unwrap_or_default());
                    }
                }
                
                // Get interactome data if requested
                if data.rectification_options.include_interactome_analysis {
                    if let Ok(interactions) = get_molecule_interactions(&driver, molecule_id).await {
                        context.insert("interactions".to_string(), serde_json::to_value(interactions).unwrap_or_default());
                    }
                }
            }
            
            serde_json::Value::Object(context)
        } else {
            serde_json::Value::Null
        };
        
        // Process each evidence with or without AI guidance
        for evidence in evidences {
            let mut rectified_confidence = evidence.confidence;
            let mut explanation = String::new();
            
            if data.rectification_options.use_ai_guidance {
                // Use LLM for guidance on rectification
                let prompt = format!(
                    "Analyze the following molecular evidence for '{}' with original confidence {:.2}:\n\n{}\n\n",
                    molecule_id, evidence.confidence, serde_json::to_string_pretty(&evidence.data).unwrap_or_default()
                );
                
                let prompt = if !context_data.is_null() {
                    format!(
                        "{}Context information:\n\n{}\n\nGiven this evidence and context, provide a rectified confidence score between 0 and 1.",
                        prompt, serde_json::to_string_pretty(&context_data).unwrap_or_default()
                    )
                } else {
                    format!(
                        "{}Given this evidence, provide a rectified confidence score between 0 and 1.",
                        prompt
                    )
                };
                
                // Call LLM service for guidance
                if let Ok(llm_response) = llm_client.query(&prompt).await {
                    // Parse the response - in a real implementation this would be more robust
                    if let Some(score_str) = llm_response.response.split_whitespace()
                        .find(|s| s.parse::<f64>().is_ok()) {
                            
                        if let Ok(score) = score_str.parse::<f64>() {
                            if score >= 0.0 && score <= 1.0 {
                                rectified_confidence = score;
                                explanation = format!("AI analysis determined a confidence score of {:.2} based on evidence evaluation.", score);
                            }
                        }
                    }
                    
                    // If we couldn't parse a score, extract the reasoning as explanation
                    if explanation.is_empty() {
                        explanation = format!("AI analysis: {}", llm_response.response);
                        
                        // Apply a default rectification based on source reliability
                        let factor = match evidence.source.to_lowercase().as_str() {
                            "genomics" => 1.15,
                            "proteomics" => 1.1,
                            "mass_spec" => 1.05,
                            "literature" => 1.2,
                            _ => 1.0,
                        };
                        
                        rectified_confidence = (evidence.confidence * factor).min(0.99);
                    }
                    
                    // Record decision in memory system
                    let _ = memory_system.record_decision(
                        "evidence_rectification",
                        serde_json::json!({
                            "molecule_id": molecule_id,
                            "evidence_source": evidence.source,
                            "original_confidence": evidence.confidence,
                            "rectified_confidence": rectified_confidence,
                            "reasoning": explanation.clone(),
                        }),
                    ).await;
                } else {
                    // LLM call failed, fall back to rule-based rectification
                    let factor = match evidence.source.to_lowercase().as_str() {
                        "genomics" => 1.15,
                        "proteomics" => 1.1,
                        "mass_spec" => 1.05,
                        "literature" => 1.2,
                        _ => 1.0,
                    };
                    
                    rectified_confidence = (evidence.confidence * factor).min(0.99);
                    explanation = format!("Rule-based rectification applied (LLM unavailable). Factor: {:.2}", factor);
                }
            } else {
                // Rule-based rectification
                let factor = match evidence.source.to_lowercase().as_str() {
                    "genomics" => 1.15,
                    "proteomics" => 1.1,
                    "mass_spec" => 1.05,
                    "literature" => 1.2,
                    _ => 1.0,
                };
                
                // Apply confidence threshold adjustment
                let threshold_adjustment = if evidence.confidence < data.rectification_options.confidence_threshold {
                    0.9  // Reduce factor for evidence below threshold
                } else {
                    1.0  // Keep factor the same for evidence above threshold
                };
                
                rectified_confidence = (evidence.confidence * factor * threshold_adjustment).min(0.99);
                explanation = format!("Rule-based rectification applied. Factor: {:.2}, Threshold Adjustment: {:.2}", 
                    factor, threshold_adjustment);
            }
            
            rectified_evidences.push(RectifiedEvidence {
                source: evidence.source.clone(),
                original_confidence: evidence.confidence,
                rectified_confidence,
                data: evidence.data.clone(),
            });
            
            all_explanations.push(explanation);
        }
        
        // Apply cross-evidence analysis for consistency if we have multiple evidences
        if rectified_evidences.len() > 1 {
            // Calculate standard deviation of confidences
            let mean = rectified_evidences.iter()
                .map(|e| e.rectified_confidence)
                .sum::<f64>() / rectified_evidences.len() as f64;
                
            let variance = rectified_evidences.iter()
                .map(|e| (e.rectified_confidence - mean).powi(2))
                .sum::<f64>() / rectified_evidences.len() as f64;
                
            let std_dev = variance.sqrt();
            
            // High agreement = boost confidences
            let agreement_factor = if std_dev < 0.1 {
                1.1  // High agreement
            } else if std_dev < 0.2 {
                1.05  // Medium agreement
            } else if std_dev < 0.3 {
                1.0  // Low agreement
            } else {
                0.95  // Disagreement
            };
            
            for evidence in &mut rectified_evidences {
                evidence.rectified_confidence = (evidence.rectified_confidence * agreement_factor).min(0.99);
            }
        }
        
        // Calculate average confidence
        let confidence_score = if rectified_evidences.is_empty() {
            0.0
        } else {
            rectified_evidences.iter()
                .map(|e| e.rectified_confidence)
                .sum::<f64>() / rectified_evidences.len() as f64
        };
        
        results.insert(
            molecule_id.clone(),
            MoleculeAnalysis {
                molecule_id: molecule_id.clone(),
                evidence_count: rectified_evidences.len(),
                rectified_evidence: rectified_evidences,
                pathways: Vec::new(), // We don't return pathways in rectification response
                interactions: Vec::new(), // We don't return interactions in rectification response
                confidence_score,
            },
        );
    }
    
    let elapsed = start_time.elapsed().as_millis() as u64;
    
    let response = AnalysisResponse {
        results,
        meta: AnalysisMeta {
            timestamp: chrono::Utc::now().to_rfc3339(),
            version: "0.1.0".to_string(),
            execution_time_ms: elapsed,
        },
    };

    HttpResponse::Ok().json(response)
}

#[get("/api/reactome/pathways/{molecule_id}")]
async fn get_reactome_pathways(
    path: web::Path<String>,
    state: web::Data<AppState>,
) -> impl Responder {
    let molecule_id = path.into_inner();
    println!("Getting reactome pathways for molecule: {}", molecule_id);

    // Query Neo4j for reactome pathways
    let neo4j_client = state.neo4j_client.lock().await;
    
    // Connect to Neo4j
    let driver = match neo4j_client.connect().await {
        Ok(driver) => driver,
        Err(e) => {
            error!("Failed to connect to Neo4j: {}", e);
            return HttpResponse::InternalServerError().json(serde_json::json!({
                "error": format!("Database connection error: {}", e)
            }));
        }
    };
    
    // Query for Reactome pathways
    let query = format!(
        "MATCH (m:Molecule {{id: $molecule_id}})-[:PART_OF]->(p:Pathway) 
         WHERE p.database = 'reactome' 
         MATCH (other:Molecule)-[:PART_OF]->(p) 
         WITH p, COLLECT(other.id) as molecules 
         RETURN p.id as pathway_id, p.name as name, molecules, p.confidence as confidence"
    );
    
    let params = serde_json::json!({
        "molecule_id": molecule_id,
    });
    
    let results = match driver.run_query(&query, params).await {
        Ok(results) => results,
        Err(e) => {
            error!("Failed to fetch Reactome pathways: {}", e);
            return HttpResponse::InternalServerError().json(serde_json::json!({
                "error": format!("Pathway data retrieval error: {}", e)
            }));
        }
    };
    
    // Parse the results
    let pathways = results.iter().map(|row| {
        let pathway_id = row.get("pathway_id").and_then(|v| v.as_str()).unwrap_or("unknown");
        let name = row.get("name").and_then(|v| v.as_str()).unwrap_or("Unknown Pathway");
        let confidence = row.get("confidence").and_then(|v| v.as_f64()).unwrap_or(0.5);
        
        let molecules = if let Some(mol_arr) = row.get("molecules").and_then(|v| v.as_array()) {
            mol_arr.iter()
                .filter_map(|m| m.as_str().map(|s| s.to_string()))
                .collect()
        } else {
            Vec::new()
        };
        
        PathwayData {
            pathway_id: pathway_id.to_string(),
            name: name.to_string(),
            molecules,
            confidence,
        }
    }).collect::<Vec<_>>();

    HttpResponse::Ok().json(pathways)
}

#[get("/api/interactome/{molecule_id}")]
async fn get_interactome(path: web::Path<String>, state: web::Data<AppState>) -> impl Responder {
    let molecule_id = path.into_inner();
    println!("Getting interactome data for molecule: {}", molecule_id);

    // Query Neo4j for interactome data
    let neo4j_client = state.neo4j_client.lock().await;
    
    // Connect to Neo4j
    let driver = match neo4j_client.connect().await {
        Ok(driver) => driver,
        Err(e) => {
            error!("Failed to connect to Neo4j: {}", e);
            return HttpResponse::InternalServerError().json(serde_json::json!({
                "error": format!("Database connection error: {}", e)
            }));
        }
    };
    
    // Query for interactions - both outgoing and incoming
    let query = format!(
        "MATCH (m:Molecule {{id: $molecule_id}})-[r]->(target:Molecule) 
         RETURN target.id as target_id, type(r) as type, r.evidence_count as evidence_count, r.confidence as confidence
         UNION
         MATCH (source:Molecule)-[r]->(m:Molecule {{id: $molecule_id}}) 
         RETURN source.id as target_id, type(r) as type, r.evidence_count as evidence_count, r.confidence as confidence"
    );
    
    let params = serde_json::json!({
        "molecule_id": molecule_id,
    });
    
    let results = match driver.run_query(&query, params).await {
        Ok(results) => results,
        Err(e) => {
            error!("Failed to fetch interactome data: {}", e);
            return HttpResponse::InternalServerError().json(serde_json::json!({
                "error": format!("Interactome data retrieval error: {}", e)
            }));
        }
    };
    
    // Parse the results
    let interactions = results.iter().map(|row| {
        let target_id = row.get("target_id").and_then(|v| v.as_str()).unwrap_or("unknown");
        let interaction_type = row.get("type").and_then(|v| v.as_str()).unwrap_or("interacts_with");
        let evidence_count = row.get("evidence_count").and_then(|v| v.as_u64()).unwrap_or(1) as usize;
        let confidence = row.get("confidence").and_then(|v| v.as_f64()).unwrap_or(0.5);
        
        InteractionData {
            source_molecule: molecule_id.clone(),
            target_molecule: target_id.to_string(),
            interaction_type: interaction_type.to_string(),
            evidence_count,
            confidence,
        }
    }).collect::<Vec<_>>();

    HttpResponse::Ok().json(interactions)
}

#[get("/api/genomics/analysis")]
async fn get_genomics_analysis(state: web::Data<AppState>) -> impl Responder {
    println!("Getting genomics analysis results");

    // Get the genomics processor
    let genomics_processor = state.genomics_processor.lock().await;
    
    // Get the analysis summary
    let analysis_summary = match genomics_processor.get_analysis_summary().await {
        Ok(summary) => summary,
        Err(e) => {
            error!("Failed to get genomics analysis summary: {}", e);
            return HttpResponse::InternalServerError().json(serde_json::json!({
                "error": format!("Failed to retrieve genomics analysis: {}", e)
            }));
        }
    };
    
    // Query the Neo4j database for additional genomics insights
    let neo4j_client = state.neo4j_client.lock().await;
    
    let driver = match neo4j_client.connect().await {
        Ok(driver) => driver,
        Err(e) => {
            // We can still return the summary without the Neo4j data
            warn!("Failed to connect to Neo4j for genomics network analysis: {}", e);
            return HttpResponse::Ok().json(serde_json::json!({
                "genome_scoring": analysis_summary,
                "network_analysis": {
                    "status": "unavailable",
                    "error": format!("Database connection error: {}", e)
                }
            }));
        }
    };
    
    // Query for network analysis
    let network_query = format!(
        "MATCH (g:Gene)-[:ASSOCIATED_WITH]->(p:Phenotype) 
         WITH g, COUNT(p) as phenotype_count 
         ORDER BY phenotype_count DESC LIMIT 20 
         RETURN g.id as gene_id, g.name as gene_name, phenotype_count"
    );
    
    let network_results = match driver.run_query(&network_query, serde_json::json!({})).await {
        Ok(results) => {
            // Process network results
            let gene_phenotype_counts = results.iter().map(|row| {
                let gene_id = row.get("gene_id").and_then(|v| v.as_str()).unwrap_or("unknown");
                let gene_name = row.get("gene_name").and_then(|v| v.as_str()).unwrap_or("Unknown");
                let phenotype_count = row.get("phenotype_count").and_then(|v| v.as_u64()).unwrap_or(0);
                
                (gene_id.to_string(), gene_name.to_string(), phenotype_count)
            }).collect::<Vec<_>>();
            
            // Calculate centrality measures
            let mut centrality = serde_json::Map::new();
            for (gene_id, gene_name, count) in &gene_phenotype_counts {
                // Normalize the centrality score between 0 and 1
                let score = (*count as f64) / 100.0;  // Assuming 100 is the max possible connections
                centrality.insert(gene_id.clone(), serde_json::json!(score.min(0.99)));
            }
            
            // Generate community clusters (simplified)
            let mut communities = serde_json::Map::new();
            if !gene_phenotype_counts.is_empty() {
                let num_communities = std::cmp::min(5, gene_phenotype_counts.len() / 4 + 1);
                
                for i in 0..num_communities {
                    let community_genes = gene_phenotype_counts.iter()
                        .skip(i)
                        .step_by(num_communities)
                        .map(|(id, _, _)| serde_json::json!(id))
                        .collect::<Vec<_>>();
                    
                    communities.insert(format!("community{}", i+1), serde_json::json!(community_genes));
                }
            }
            
            serde_json::json!({
                "centrality": centrality,
                "communities": communities,
                "summary": {
                    "num_nodes": gene_phenotype_counts.len(),
                    "num_edges": gene_phenotype_counts.iter().map(|(_, _, c)| c).sum::<u64>(),
                    "num_communities": communities.len()
                }
            })
        },
        Err(e) => {
            warn!("Failed to fetch network analysis: {}", e);
            serde_json::json!({
                "status": "error",
                "error": format!("Network analysis error: {}", e)
            })
        }
    };
    
    // Combine the analysis summary with network data
    let combined_result = serde_json::json!({
        "genome_scoring": analysis_summary,
        "network_analysis": network_results
    });

    HttpResponse::Ok().json(combined_result)
}

#[get("/api/mass-spec/analysis")]
async fn get_mass_spec_analysis(state: web::Data<AppState>) -> impl Responder {
    println!("Getting mass spec analysis results");

    // Get the mass spec processor
    let mass_spec_processor = state.mass_spec_processor.lock().await;
    
    // Get the analysis summary
    let analysis_summary = match mass_spec_processor.get_analysis_summary().await {
        Ok(summary) => summary,
        Err(e) => {
            error!("Failed to get mass spec analysis summary: {}", e);
            return HttpResponse::InternalServerError().json(serde_json::json!({
                "error": format!("Failed to retrieve mass spec analysis: {}", e)
            }));
        }
    };
    
    // Get compounds with highest confidence
    let compounds = match mass_spec_processor.get_high_confidence_compounds(10).await {
        Ok(compounds) => compounds,
        Err(e) => {
            warn!("Failed to get high confidence compounds: {}", e);
            vec![]  // Return empty vector if we can't get compounds
        }
    };
    
    // Format the compound data for JSON return
    let compound_json = compounds.iter().map(|c| {
        serde_json::json!({
            "id": c.id,
            "name": c.name,
            "formula": c.formula,
            "mass": c.mass,
            "confidence": c.confidence
        })
    }).collect::<Vec<_>>();
    
    // Create full response
    let response = serde_json::json!({
        "summary": analysis_summary,
        "compounds": compound_json
    });

    HttpResponse::Ok().json(response)
}

#[get("/api/molecules/{id}")]
async fn get_molecule_data(path: web::Path<String>, state: web::Data<AppState>) -> impl Responder {
    let molecule_id = path.into_inner();
    println!("Getting molecule data for: {}", molecule_id);

    // Query Neo4j for molecule data
    let neo4j_client = state.neo4j_client.lock().await;
    
    let driver = match neo4j_client.connect().await {
        Ok(driver) => driver,
        Err(e) => {
            error!("Failed to connect to Neo4j: {}", e);
            return HttpResponse::InternalServerError().json(serde_json::json!({
                "error": format!("Database connection error: {}", e)
            }));
        }
    };
    
    // Query for molecule details
    let query = format!(
        "MATCH (m:Molecule {{id: $molecule_id}}) 
         OPTIONAL MATCH (m)-[:HAS_ALIAS]->(a:Alias) 
         WITH m, COLLECT(a.name) as aliases 
         RETURN m.id as id, m.name as name, m.type as type, m.description as description, 
                m.properties as properties, aliases"
    );
    
    let params = serde_json::json!({
        "molecule_id": molecule_id,
    });
    
    let results = match driver.run_query(&query, params).await {
        Ok(results) => results,
        Err(e) => {
            error!("Failed to fetch molecule data: {}", e);
            return HttpResponse::InternalServerError().json(serde_json::json!({
                "error": format!("Molecule data retrieval error: {}", e)
            }));
        }
    };
    
    // Check if molecule was found
    if results.is_empty() {
        return HttpResponse::NotFound().json(serde_json::json!({
            "error": format!("Molecule not found: {}", molecule_id)
        }));
    }
    
    // Parse the results
    let row = &results[0];
    let id = row.get("id").and_then(|v| v.as_str()).unwrap_or(&molecule_id);
    let name = row.get("name").and_then(|v| v.as_str()).unwrap_or("Unknown");
    let mol_type = row.get("type").and_then(|v| v.as_str()).unwrap_or("unknown");
    let description = row.get("description").and_then(|v| v.as_str()).unwrap_or("No description available");
    
    let properties = row.get("properties")
        .and_then(|v| v.as_object())
        .cloned()
        .unwrap_or_default();
    
    let aliases = match row.get("aliases") {
        Some(serde_json::Value::Array(arr)) => arr.clone(),
        _ => vec![],
    };
    
    // Create molecule data response
    let molecule_data = serde_json::json!({
        "id": id,
        "name": name,
        "type": mol_type,
        "description": description,
        "properties": properties,
        "aliases": aliases
    });

    HttpResponse::Ok().json(molecule_data)
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Initialize logger
    env_logger::init_from_env(env_logger::Env::default().default_filter_or("info"));
    
    info!("Starting Hegel API server");
    
    // Initialize the core engine
    match hegel::initialize() {
        Ok(_) => info!("Hegel core engine initialized successfully"),
        Err(e) => {
            error!("Failed to initialize Hegel core engine: {}", e);
            return Err(std::io::Error::new(std::io::ErrorKind::Other, e.to_string()));
        }
    }
    
    // Create shared application state
    let neo4j_client = Arc::new(Mutex::new(Neo4jClient::new("bolt://neo4j:7687", "neo4j", "password")));
    let llm_client = Arc::new(Mutex::new(LLMClient::new("http://llm-service:8000")));
    let memory_system = Arc::new(Mutex::new(MemorySystem::new()));
    let evidence_processor = Arc::new(Mutex::new(EvidenceProcessor::new(Default::default())));
    let evidence_rectifier = Arc::new(Mutex::new(EvidenceRectifier::default()));
    let genomics_processor = Arc::new(Mutex::new(GenomicsProcessor::new()));
    let mass_spec_processor = Arc::new(Mutex::new(MassSpecProcessor::new()));
    
    let app_state = web::Data::new(AppState {
        neo4j_client,
        llm_client,
        memory_system,
        evidence_processor,
        evidence_rectifier,
        genomics_processor,
        mass_spec_processor,
    });
    
    // Start HTTP server
    HttpServer::new(move || {
        // Configure CORS
        let cors = Cors::default()
            .allow_any_origin()
            .allow_any_method()
            .allow_any_header()
            .max_age(3600);
        
        App::new()
            .wrap(cors)
            .app_data(app_state.clone())
            // API routes
            .service(analyze_evidence)
            .service(rectify_evidence)
            .service(get_reactome_pathways)
            .service(get_interactome)
            .service(get_genomics_analysis)
            .service(get_mass_spec_analysis)
            .service(get_molecule_data)
    })
    .bind(("0.0.0.0", 8080))?
    .run()
    .await
} 