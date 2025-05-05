use std::path::PathBuf;
use std::process;
use anyhow::{Result, Context};
use hegel::{self, api};

fn main() -> Result<()> {
    // Initialize the core engine
    hegel::initialize()
        .context("Failed to initialize Hegel core engine")?;
    
    // Parse command line arguments
    let args: Vec<String> = std::env::args().collect();
    
    if args.len() < 2 {
        print_usage();
        return Ok(());
    }
    
    match args[1].as_str() {
        "validate" => {
            if args.len() < 3 {
                eprintln!("Error: Missing SMILES string for validation");
                process::exit(1);
            }
            
            let smiles = &args[2];
            validate_molecule(smiles)?;
        },
        "compare" => {
            if args.len() < 4 {
                eprintln!("Error: Need two SMILES strings for comparison");
                process::exit(1);
            }
            
            let smiles1 = &args[2];
            let smiles2 = &args[3];
            compare_molecules(smiles1, smiles2)?;
        },
        "network" => {
            if args.len() < 3 {
                eprintln!("Error: Need file with SMILES strings");
                process::exit(1);
            }
            
            let filepath = &args[2];
            build_network(filepath)?;
        },
        "serve" => {
            let port = if args.len() >= 3 {
                args[2].parse().unwrap_or(8080)
            } else {
                8080
            };
            
            serve_api(port)?;
        },
        "help" | "--help" | "-h" => {
            print_usage();
        },
        cmd => {
            eprintln!("Error: Unknown command '{}'", cmd);
            print_usage();
            process::exit(1);
        }
    }
    
    Ok(())
}

fn print_usage() {
    println!("Hegel Molecular Identity Platform CLI");
    println!("Usage:");
    println!("  hegel-cli validate <SMILES>              - Validate a molecule");
    println!("  hegel-cli compare <SMILES1> <SMILES2>    - Compare two molecules");
    println!("  hegel-cli network <FILE>                 - Build a similarity network");
    println!("  hegel-cli serve [PORT]                   - Start the API server");
    println!("  hegel-cli help                           - Show this help message");
}

fn validate_molecule(smiles: &str) -> Result<()> {
    println!("Validating molecule: {}", smiles);
    
    match api::validate_molecule(smiles) {
        Ok(result) => {
            println!("Validation result:");
            println!("  Valid: {}", result.is_valid);
            println!("  Confidence: {:.2}%", result.confidence * 100.0);
            
            if !result.errors.is_empty() {
                println!("  Errors:");
                for error in &result.errors {
                    println!("    - {}", error);
                }
            }
            
            if !result.properties.is_empty() {
                println!("  Properties:");
                for (key, value) in &result.properties {
                    println!("    {}: {}", key, value);
                }
            }
            
            Ok(())
        },
        Err(e) => {
            eprintln!("Error validating molecule: {}", e);
            process::exit(1);
        }
    }
}

fn compare_molecules(smiles1: &str, smiles2: &str) -> Result<()> {
    println!("Comparing molecules:");
    println!("  Molecule 1: {}", smiles1);
    println!("  Molecule 2: {}", smiles2);
    
    match api::compare_molecules(smiles1, smiles2) {
        Ok(similarity) => {
            println!("Similarity: {:.2}%", similarity * 100.0);
            Ok(())
        },
        Err(e) => {
            eprintln!("Error comparing molecules: {}", e);
            process::exit(1);
        }
    }
}

fn build_network(filepath: &str) -> Result<()> {
    println!("Building molecular similarity network from: {}", filepath);
    
    // Read the file with SMILES strings
    let file_content = std::fs::read_to_string(filepath)
        .context(format!("Failed to read file: {}", filepath))?;
    
    // Parse SMILES strings from the file
    let smiles_list: Vec<&str> = file_content.lines()
        .filter(|line| !line.trim().is_empty() && !line.trim().starts_with('#'))
        .collect();
    
    println!("Found {} molecules", smiles_list.len());
    
    // Build the network
    match api::build_similarity_network(&smiles_list) {
        Ok(network) => {
            println!("Network built successfully:");
            println!("  Nodes: {}", network.nodes.len());
            println!("  Edges: {}", network.edges.len());
            
            // Save network to JSON file
            let output_path = PathBuf::from(filepath).with_extension("json");
            let json = serde_json::to_string_pretty(&network)
                .context("Failed to serialize network to JSON")?;
            
            std::fs::write(&output_path, json)
                .context(format!("Failed to write network to: {:?}", output_path))?;
            
            println!("Network saved to: {:?}", output_path);
            
            Ok(())
        },
        Err(e) => {
            eprintln!("Error building network: {}", e);
            process::exit(1);
        }
    }
}

fn serve_api(port: u16) -> Result<()> {
    println!("Starting API server on port {}...", port);
    println!("Press Ctrl+C to stop");
    
    // This would call into an actual API server implementation
    // For now, we'll just sleep to simulate a running server
    loop {
        std::thread::sleep(std::time::Duration::from_secs(1));
    }
}
