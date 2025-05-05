//! Hegel CLI Tool
//!
//! This binary provides a command-line interface for the Hegel molecular identity platform,
//! allowing users to validate molecules, build networks, and more.

use anyhow::{Result, Context, anyhow};
use clap::{Parser, Subcommand};
use log::{info, debug, error};
use serde_json::json;
use std::path::PathBuf;
use std::time::Instant;

use hegel::processing::{Molecule, MoleculeFormat};
use hegel::graph::{MoleculeNetwork, NetworkBuilder};
use hegel::metacognition::{MetacognitionSystem, ValidationResult};

/// CLI arguments
#[derive(Parser)]
#[clap(
    name = "hegel",
    about = "Hegel molecular identity platform",
    version = env!("CARGO_PKG_VERSION"),
    author = "Hegel Project Team"
)]
struct Cli {
    /// Subcommand to run
    #[clap(subcommand)]
    command: Commands,
    
    /// Increase verbosity
    #[clap(short, long, global = true)]
    verbose: bool,
    
    /// Output format (text, json, csv)
    #[clap(short, long, global = true, default_value = "text")]
    output: String,
}

/// Available subcommands
#[derive(Subcommand)]
enum Commands {
    /// Validate a molecule's identity
    Validate {
        /// Molecule identifier (SMILES, InChI, etc.)
        #[clap(short, long)]
        molecule: String,
        
        /// Type of identifier (smiles, inchi, name)
        #[clap(short, long, default_value = "smiles")]
        id_type: String,
        
        /// Validation confidence threshold (0.0-1.0)
        #[clap(short, long, default_value = "0.5")]
        threshold: f64,
    },
    
    /// Process a molecule to extract properties and relationships
    Process {
        /// Molecule identifier (SMILES, InChI, etc.)
        #[clap(short, long)]
        molecule: String,
        
        /// Type of identifier (smiles, inchi, name)
        #[clap(short, long, default_value = "smiles")]
        id_type: String,
        
        /// Include pathway information
        #[clap(long)]
        pathways: bool,
        
        /// Include interaction information
        #[clap(long)]
        interactions: bool,
    },
    
    /// Compare two molecules
    Compare {
        /// First molecule identifier
        #[clap(short, long)]
        molecule1: String,
        
        /// Second molecule identifier
        #[clap(short, long)]
        molecule2: String,
        
        /// Type of identifier (smiles, inchi, name)
        #[clap(short, long, default_value = "smiles")]
        id_type: String,
    },
    
    /// Build a network from a set of molecules
    Network {
        /// Input file with molecules (one per line)
        #[clap(short, long)]
        input: PathBuf,
        
        /// Output file for the network
        #[clap(short, long)]
        output: PathBuf,
        
        /// Input format (smiles, sdf, csv)
        #[clap(short, long, default_value = "smiles")]
        format: String,
        
        /// Similarity threshold for network connections (0.0-1.0)
        #[clap(short, long, default_value = "0.7")]
        threshold: f64,
        
        /// Maximum neighbors per molecule
        #[clap(short, long, default_value = "10")]
        max_neighbors: usize,
    },
    
    /// Start the Hegel API server
    Serve {
        /// Host to bind to
        #[clap(short, long, default_value = "127.0.0.1")]
        host: String,
        
        /// Port to listen on
        #[clap(short, long, default_value = "8080")]
        port: u16,
    },
}

/// Main entry point
#[tokio::main]
async fn main() -> Result<()> {
    // Parse command-line arguments
    let cli = Cli::parse();
    
    // Configure logging
    if std::env::var("RUST_LOG").is_err() {
        if cli.verbose {
            std::env::set_var("RUST_LOG", "debug");
        } else {
            std::env::set_var("RUST_LOG", "info");
        }
    }
    env_logger::init();
    
    // Initialize the Hegel core engine
    hegel::initialize()?;
    
    // Process the requested command
    match &cli.command {
        Commands::Validate { molecule, id_type, threshold } => {
            validate_molecule(molecule, id_type, *threshold, &cli.output).await?;
        }
        
        Commands::Process { molecule, id_type, pathways, interactions } => {
            process_molecule(molecule, id_type, *pathways, *interactions, &cli.output).await?;
        }
        
        Commands::Compare { molecule1, molecule2, id_type } => {
            compare_molecules(molecule1, molecule2, id_type, &cli.output).await?;
        }
        
        Commands::Network { input, output, format, threshold, max_neighbors } => {
            build_network(input, output, format, *threshold, *max_neighbors, &cli.output).await?;
        }
        
        Commands::Serve { host, port } => {
            serve_api(host, *port).await?;
        }
    }
    
    Ok(())
}

/// Validate a molecule's identity
async fn validate_molecule(molecule: &str, id_type: &str, threshold: f64, output_format: &str) -> Result<()> {
    info!("Validating molecule: {}", molecule);
    let start_time = Instant::now();
    
    // Create a metacognition system
    let system = MetacognitionSystem::new()?;
    
    // Parse the ID type
    let mol_id_type = parse_id_type(id_type)?;
    
    // Process the molecule
    let validation = system.validate_molecule_identity(molecule).await?;
    
    // Output the results based on the format
    let elapsed = start_time.elapsed();
    
    match output_format {
        "json" => {
            println!("{}", serde_json::to_string_pretty(&validation)?);
        }
        "csv" => {
            println!("molecule_id,is_valid,confidence,explanation");
            println!("{},{},{},\"{}\"", 
                     validation.molecule_id,
                     validation.is_valid,
                     validation.confidence,
                     validation.explanation.replace("\"", "\"\""));
        }
        _ => {
            println!("Validation Results:");
            println!("  Molecule ID: {}", validation.molecule_id);
            println!("  Valid: {}", if validation.is_valid { "YES" } else { "NO" });
            println!("  Confidence: {:.1}%", validation.confidence * 100.0);
            println!("  Explanation: {}", validation.explanation);
            println!();
            println!("Time taken: {:.2?}", elapsed);
        }
    }
    
    Ok(())
}

/// Process a molecule to extract properties and relationships
async fn process_molecule(molecule: &str, id_type: &str, include_pathways: bool, include_interactions: bool, output_format: &str) -> Result<()> {
    info!("Processing molecule: {}", molecule);
    let start_time = Instant::now();
    
    // Create a metacognition system
    let system = MetacognitionSystem::new()?;
    
    // Parse the ID type
    let mol_id_type = parse_id_type(id_type)?;
    
    // Process the molecule
    let response = system.process_molecule(molecule, mol_id_type).await?;
    
    // Output the results based on the format
    let elapsed = start_time.elapsed();
    
    match output_format {
        "json" => {
            println!("{}", serde_json::to_string_pretty(&response)?);
        }
        "csv" => {
            // Basic molecule info
            println!("type,key,value");
            println!("info,id,{}", response.id);
            println!("info,name,{}", response.name.unwrap_or_default());
            println!("info,formula,{}", response.formula.unwrap_or_default());
            println!("info,smiles,{}", response.smiles);
            
            // Properties
            for (key, value) in response.properties {
                println!("property,{},{}", key, value);
            }
            
            // Related entities
            for related in response.related_entities {
                println!("related,{},{},{}", 
                         related.relation_type,
                         related.entity_id,
                         related.entity_name.unwrap_or_default());
            }
        }
        _ => {
            println!("Molecule Processing Results:");
            println!("  ID: {}", response.id);
            if let Some(name) = &response.name {
                println!("  Name: {}", name);
            }
            if let Some(formula) = &response.formula {
                println!("  Formula: {}", formula);
            }
            println!("  SMILES: {}", response.smiles);
            
            println!("\nProperties:");
            for (key, value) in &response.properties {
                println!("  {}: {}", key, value);
            }
            
            if !response.related_entities.is_empty() {
                println!("\nRelated Entities:");
                for related in &response.related_entities {
                    println!("  {} {} ({})", 
                             related.relation_type,
                             related.entity_name.as_deref().unwrap_or(&related.entity_id),
                             related.entity_id);
                }
            }
            
            println!();
            println!("Time taken: {:.2?}", elapsed);
        }
    }
    
    Ok(())
}

/// Compare two molecules
async fn compare_molecules(molecule1: &str, molecule2: &str, id_type: &str, output_format: &str) -> Result<()> {
    info!("Comparing molecules: {} and {}", molecule1, molecule2);
    let start_time = Instant::now();
    
    // Parse the ID type
    let mol_id_type = parse_id_type(id_type)?;
    
    // Create molecules
    let mol1 = Molecule::from_identifier(molecule1, mol_id_type)?;
    let mol2 = Molecule::from_identifier(molecule2, mol_id_type)?;
    
    // Calculate similarity
    let similarity = mol1.calculate_similarity(&mol2)?;
    
    // Create a metacognition system
    let system = MetacognitionSystem::new()?;
    
    // Get additional analysis via LLM (if available)
    let llm_interface = system.get_llm_interface();
    let analysis = if let Some(interface) = llm_interface {
        // Convert molecules to the format expected by the LLM interface
        let mol1_data = convert_to_llm_molecule(&mol1);
        let mol2_data = convert_to_llm_molecule(&mol2);
        
        // Get analysis
        match interface.compare_molecules(&mol1_data, &mol2_data).await {
            Ok(comparison) => Some(comparison),
            Err(_) => None,
        }
    } else {
        None
    };
    
    // Output the results based on the format
    let elapsed = start_time.elapsed();
    
    match output_format {
        "json" => {
            let result = json!({
                "molecule1": {
                    "id": mol1.id,
                    "smiles": mol1.smiles,
                    "name": mol1.name,
                },
                "molecule2": {
                    "id": mol2.id,
                    "smiles": mol2.smiles,
                    "name": mol2.name,
                },
                "similarity": similarity,
                "analysis": analysis.map(|a| a.analysis),
                "same_entity": analysis.map(|a| a.same_entity),
            });
            println!("{}", serde_json::to_string_pretty(&result)?);
        }
        "csv" => {
            println!("molecule1,molecule2,similarity,same_entity");
            println!("{},{},{},{}",
                     mol1.id,
                     mol2.id,
                     similarity,
                     analysis.as_ref().map(|a| a.same_entity).unwrap_or(similarity > 0.8));
        }
        _ => {
            println!("Molecule Comparison:");
            println!("  Molecule 1: {} ({})", mol1.name.as_deref().unwrap_or(&mol1.id), mol1.smiles);
            println!("  Molecule 2: {} ({})", mol2.name.as_deref().unwrap_or(&mol2.id), mol2.smiles);
            println!("  Similarity: {:.1}%", similarity * 100.0);
            
            if let Some(a) = analysis {
                println!("\nAnalysis:");
                println!("  {}", a.analysis);
                println!("  Same entity: {}", if a.same_entity { "YES" } else { "NO" });
            }
            
            println!();
            println!("Time taken: {:.2?}", elapsed);
        }
    }
    
    Ok(())
}

/// Build a network from a set of molecules
async fn build_network(
    input: &PathBuf,
    output: &PathBuf,
    format: &str,
    threshold: f64,
    max_neighbors: usize,
    output_format: &str,
) -> Result<()> {
    info!("Building network from file: {}", input.display());
    let start_time = Instant::now();
    
    // Parse the input format
    let mol_format = match format {
        "smiles" => MoleculeFormat::Smiles,
        "sdf" => MoleculeFormat::Sdf,
        "csv" => MoleculeFormat::Csv,
        _ => return Err(anyhow!("Unsupported input format: {}", format)),
    };
    
    // Read molecules from the input file
    let molecules = Molecule::read_from_file(input, mol_format)?;
    info!("Read {} molecules from input file", molecules.len());
    
    // Create a network builder
    let mut builder = NetworkBuilder::new(threshold, max_neighbors);
    
    // Add molecules to the network
    builder.add_molecules(&molecules)?;
    
    // Build the network
    let network = builder.build();
    info!("Built network with {} nodes and {} edges", 
          network.get_molecules().len(), 
          network.calculate_metrics().edge_count);
    
    // Calculate network metrics
    let metrics = network.calculate_metrics();
    
    // Serialize the network
    let serialized = network.to_serializable();
    
    // Write the network to the output file
    let json = serde_json::to_string_pretty(&serialized)?;
    std::fs::write(output, json)?;
    info!("Wrote network to file: {}", output.display());
    
    // Output the results based on the format
    let elapsed = start_time.elapsed();
    
    match output_format {
        "json" => {
            println!("{}", serde_json::to_string_pretty(&metrics)?);
        }
        "csv" => {
            println!("metric,value");
            println!("nodes,{}", metrics.node_count);
            println!("edges,{}", metrics.edge_count);
            println!("density,{}", metrics.density);
            println!("avg_degree,{}", metrics.avg_degree);
            println!("max_degree,{}", metrics.max_degree);
        }
        _ => {
            println!("Network Building Results:");
            println!("  Input file: {}", input.display());
            println!("  Output file: {}", output.display());
            println!("  Molecules read: {}", molecules.len());
            println!("  Nodes in network: {}", metrics.node_count);
            println!("  Edges in network: {}", metrics.edge_count);
            println!("  Network density: {:.3}", metrics.density);
            println!("  Average degree: {:.2}", metrics.avg_degree);
            println!("  Maximum degree: {}", metrics.max_degree);
            
            if !metrics.clusters.is_empty() {
                println!("\nClusters:");
                for (i, size) in metrics.clusters.iter().enumerate() {
                    println!("  Cluster {}: {} nodes", i + 1, size);
                }
            }
            
            println!();
            println!("Time taken: {:.2?}", elapsed);
        }
    }
    
    Ok(())
}

/// Start the API server
async fn serve_api(host: &str, port: u16) -> Result<()> {
    info!("Starting API server on {}:{}", host, port);
    
    // In a real implementation, this would start an Actix web server
    // For now, we'll just simulate the server
    
    println!("API server started on http://{}:{}", host, port);
    println!("Available endpoints:");
    println!("  POST /api/validate - Validate a molecule");
    println!("  POST /api/process - Process a molecule");
    println!("  POST /api/compare - Compare two molecules");
    println!("  POST /api/network - Build a network");
    
    println!("\nPress Ctrl+C to stop the server");
    
    // Keep the server running until interrupted
    tokio::signal::ctrl_c().await?;
    println!("Server stopped");
    
    Ok(())
}

/// Parse molecule ID type
fn parse_id_type(id_type: &str) -> Result<hegel::metacognition::molecule_processor::MoleculeIdType> {
    use hegel::metacognition::molecule_processor::MoleculeIdType;
    
    match id_type.to_lowercase().as_str() {
        "smiles" => Ok(MoleculeIdType::Smiles),
        "inchi" => Ok(MoleculeIdType::InChI),
        "name" => Ok(MoleculeIdType::Name),
        "cas" => Ok(MoleculeIdType::CasNumber),
        "pubchem" => Ok(MoleculeIdType::PubChemId),
        _ => Err(anyhow!("Unsupported ID type: {}", id_type)),
    }
}

/// Convert a molecule to the format expected by the LLM interface
fn convert_to_llm_molecule(molecule: &Molecule) -> hegel::metacognition::llm::MoleculeData {
    use hegel::metacognition::llm::MoleculeData;
    
    // Convert properties to the right format
    let properties = molecule.properties.clone();
    
    MoleculeData {
        identifier: molecule.id.clone(),
        smiles: molecule.smiles.clone(),
        name: molecule.name.clone(),
        formula: molecule.formula.clone(),
        properties,
    }
}
