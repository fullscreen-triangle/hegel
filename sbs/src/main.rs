use std::path::PathBuf;

use anyhow::Result;
use clap::{Parser, Subcommand};
use sbs::circuit::{Circuit, Perturbation};
use sbs::metrics::find_optimal_perturbation;
use sbs::solver::Solver;

#[derive(Parser)]
#[command(name = "sbs")]
#[command(about = "Systems Biology Shaders — GPU-native observation calculus")]
#[command(version)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Run the demo glycolysis circuit
    Demo {
        /// Apply hexokinase deficiency perturbation (90% reduction)
        #[arg(long)]
        perturb: bool,

        /// Output format
        #[arg(long, default_value = "text")]
        format: OutputFormat,
    },

    /// Load and observe an SBML file
    Observe {
        /// Path to SBML XML file
        path: PathBuf,

        /// Edge perturbations as idx:factor pairs (e.g. "0:0.1,3:0.5")
        #[arg(long)]
        perturb: Option<String>,

        /// Output format
        #[arg(long, default_value = "text")]
        format: OutputFormat,
    },

    /// Find l1-optimal perturbation to restore visibility
    Restore {
        /// Path to SBML XML file
        path: PathBuf,

        /// Current perturbations as idx:factor pairs
        #[arg(long)]
        perturb: String,

        /// Maximum edges to restore
        #[arg(long, default_value = "5")]
        max_edges: usize,
    },

    /// Compute catalyst cascade convergence
    Cascade {
        /// Catalytic powers (comma-separated, e.g. "0.3,0.7,0.5")
        powers: String,

        /// Initial S-value
        #[arg(long, default_value = "80.0")]
        s0: f64,

        /// Floor value
        #[arg(long, default_value = "1.5")]
        floor: f64,
    },
}

#[derive(Clone, Debug)]
enum OutputFormat {
    Text,
    Json,
    Csv,
}

impl std::str::FromStr for OutputFormat {
    type Err = String;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "text" => Ok(OutputFormat::Text),
            "json" => Ok(OutputFormat::Json),
            "csv" => Ok(OutputFormat::Csv),
            _ => Err(format!("Unknown format: {}", s)),
        }
    }
}

fn parse_perturbations(s: &str) -> Vec<Perturbation> {
    s.split(',')
        .filter_map(|pair| {
            let parts: Vec<&str> = pair.trim().split(':').collect();
            if parts.len() == 2 {
                let idx = parts[0].parse().ok()?;
                let factor = parts[1].parse().ok()?;
                Some(Perturbation::new(idx, factor))
            } else {
                None
            }
        })
        .collect()
}

fn main() -> Result<()> {
    tracing_subscriber::fmt::init();
    let cli = Cli::parse();

    match cli.command {
        Commands::Demo { perturb, format } => {
            let circuit = Circuit::demo_glycolysis();
            let mut solver = Solver::new(circuit);

            if perturb {
                solver.add_perturbation(0, 0.1);
                eprintln!("Applied hexokinase deficiency: edge 0 × 0.1");
            }

            let result = solver.solve();

            match format {
                OutputFormat::Text => {
                    println!("=== SBS Demo: Glycolysis ===");
                    println!("{}", result.summary());
                    println!();
                    println!("S-entropy per node:");
                    for (i, s) in result.s_entropy.iter().enumerate() {
                        let name = &solver.circuit().nodes[i].name;
                        println!(
                            "  {:12} Se={:.4} Sk={:.4} St={:.4}",
                            name, s.se, s.sk, s.st
                        );
                    }
                    println!();
                    println!("Backward navigation path:");
                    for &idx in &result.metrics.backward_path {
                        print!("{}", solver.circuit().nodes[idx].name);
                        if idx != *result.metrics.backward_path.last().unwrap() {
                            print!(" <- ");
                        }
                    }
                    println!();
                }
                OutputFormat::Json => {
                    let output = serde_json::json!({
                        "coherence": result.coherence(),
                        "visibility": result.visibility(),
                        "compute_time_us": result.compute_time_us,
                        "s_entropy": result.s_entropy,
                        "metrics": result.metrics,
                    });
                    println!("{}", serde_json::to_string_pretty(&output)?);
                }
                OutputFormat::Csv => {
                    println!("node,name,Se,Sk,St");
                    for (i, s) in result.s_entropy.iter().enumerate() {
                        println!(
                            "{},{},{:.6},{:.6},{:.6}",
                            i, solver.circuit().nodes[i].name, s.se, s.sk, s.st
                        );
                    }
                }
            }
        }

        Commands::Observe {
            path,
            perturb,
            format,
        } => {
            let xml = std::fs::read_to_string(&path)?;
            let circuit = sbs::sbml::parse_sbml(&xml)
                .map_err(|e| anyhow::anyhow!("SBML parse error: {}", e))?;

            let perturbations = perturb
                .map(|s| parse_perturbations(&s))
                .unwrap_or_default();

            let solver = Solver::new(circuit).with_perturbations(perturbations);
            let result = solver.solve();

            match format {
                OutputFormat::Text => {
                    println!("=== SBS Observe: {} ===", path.display());
                    println!("{}", result.summary());
                }
                OutputFormat::Json => {
                    let output = serde_json::json!({
                        "file": path.display().to_string(),
                        "coherence": result.coherence(),
                        "visibility": result.visibility(),
                        "s_entropy": result.s_entropy,
                    });
                    println!("{}", serde_json::to_string_pretty(&output)?);
                }
                OutputFormat::Csv => {
                    println!("node,name,Se,Sk,St");
                    for (i, s) in result.s_entropy.iter().enumerate() {
                        println!(
                            "{},{},{:.6},{:.6},{:.6}",
                            i, solver.circuit().nodes[i].name, s.se, s.sk, s.st
                        );
                    }
                }
            }
        }

        Commands::Restore {
            path,
            perturb,
            max_edges,
        } => {
            let xml = std::fs::read_to_string(&path)?;
            let circuit = sbs::sbml::parse_sbml(&xml)
                .map_err(|e| anyhow::anyhow!("SBML parse error: {}", e))?;

            let perturbations = parse_perturbations(&perturb);
            let optimal = find_optimal_perturbation(&circuit, &perturbations, max_edges);

            println!("=== l1-Optimal Restoration ===");
            println!("Current perturbations: {}", perturbations.len());
            println!("Recommended restorations ({} edges):", optimal.len());
            for p in &optimal {
                let edge = &circuit.edges[p.edge_idx];
                println!(
                    "  Edge {} ({}) -> factor {:.2}",
                    p.edge_idx, edge.name, p.factor
                );
            }

            let solver = Solver::new(circuit).with_perturbations(optimal);
            let result = solver.solve();
            println!();
            println!("After restoration: {}", result.summary());
        }

        Commands::Cascade { powers, s0, floor } => {
            let kappas: Vec<f64> = powers
                .split(',')
                .filter_map(|s| s.trim().parse().ok())
                .collect();

            println!("=== Catalyst Cascade ===");
            println!("S0={}, Floor={}", s0, floor);
            println!();

            let mut residual = s0 - floor;
            let mut composite = 0.0_f64;

            println!("{:>4}  {:>8}  {:>10}  {:>12}  {:>12}", "Step", "kappa", "Composite", "S-value", "Residual");
            println!("{}", "-".repeat(55));

            for (i, &k) in kappas.iter().enumerate() {
                composite = 1.0 - (1.0 - composite) * (1.0 - k);
                residual *= 1.0 - k;
                let s_value = floor + residual;

                println!(
                    "{:>4}  {:>8.4}  {:>10.6}  {:>12.6}  {:>12.6e}",
                    i + 1, k, composite, s_value, residual
                );
            }

            println!();
            println!("Final composite catalytic power: {:.6}", composite);
            println!(
                "Predicted by Theorem 7.3: 1 - {} = {:.6}",
                kappas
                    .iter()
                    .map(|k| format!("(1-{:.2})", k))
                    .collect::<Vec<_>>()
                    .join("·"),
                composite
            );
        }
    }

    Ok(())
}
