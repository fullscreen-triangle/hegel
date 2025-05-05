//! Molecular Schema Processing
//!
//! This module provides schema validation and processing for molecular data.

use anyhow::{Result, Context};
use log::{info, warn, debug};
use serde::{Serialize, Deserialize};
use std::collections::HashMap;

/// Initialize the schema module
pub fn initialize() -> Result<()> {
    info!("Initializing molecular schema module");
    
    // Load default schemas
    load_default_schemas()?;
    
    info!("Molecular schema module initialized successfully");
    Ok(())
}

/// Load default molecule schemas
fn load_default_schemas() -> Result<()> {
    debug!("Loading default molecule schemas");
    
    // Register common schemas in the registry
    let registry = SchemaRegistry::global();
    
    // Add default schema for small molecules
    registry.register_schema(
        "small_molecule",
        MoleculeSchema {
            name: "Small Molecule".to_string(),
            description: "Schema for small organic molecules".to_string(),
            constraints: vec![
                SchemaConstraint::MaxAtoms(100),
                SchemaConstraint::RequiredElements(vec!["C".to_string()]),
                SchemaConstraint::AllowedElements(vec![
                    "C".to_string(), "H".to_string(), "O".to_string(), 
                    "N".to_string(), "P".to_string(), "S".to_string(),
                    "F".to_string(), "Cl".to_string(), "Br".to_string(), 
                    "I".to_string()
                ]),
            ],
            properties: HashMap::new(),
        }
    );
    
    // Add default schema for proteins
    registry.register_schema(
        "protein",
        MoleculeSchema {
            name: "Protein".to_string(),
            description: "Schema for protein molecules".to_string(),
            constraints: vec![
                SchemaConstraint::MinAtoms(50),
                SchemaConstraint::RequiredElements(vec![
                    "C".to_string(), "H".to_string(), "O".to_string(), 
                    "N".to_string(), "S".to_string()
                ]),
            ],
            properties: HashMap::new(),
        }
    );
    
    debug!("Default molecule schemas loaded");
    Ok(())
}

/// Schema for validating molecules
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MoleculeSchema {
    /// Name of the schema
    pub name: String,
    
    /// Description of the schema
    pub description: String,
    
    /// Constraints that molecules must satisfy
    pub constraints: Vec<SchemaConstraint>,
    
    /// Additional properties and metadata
    pub properties: HashMap<String, serde_json::Value>,
}

impl MoleculeSchema {
    /// Validate a molecule against this schema
    pub fn validate(&self, molecule: &super::Molecule) -> ValidationResult {
        let mut result = ValidationResult {
            is_valid: true,
            issues: Vec::new(),
        };
        
        // Validate each constraint
        for constraint in &self.constraints {
            if let Err(issue) = constraint.validate(molecule) {
                result.is_valid = false;
                result.issues.push(issue);
            }
        }
        
        result
    }
}

/// Constraint for validating molecules
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SchemaConstraint {
    /// Minimum number of atoms
    MinAtoms(usize),
    
    /// Maximum number of atoms
    MaxAtoms(usize),
    
    /// Required elements that must be present
    RequiredElements(Vec<String>),
    
    /// Allowed elements (any elements not in this list are disallowed)
    AllowedElements(Vec<String>),
    
    /// Forbidden elements (elements in this list are disallowed)
    ForbiddenElements(Vec<String>),
    
    /// Minimum molecular weight
    MinMolecularWeight(f64),
    
    /// Maximum molecular weight
    MaxMolecularWeight(f64),
    
    /// Custom constraint with validation logic
    Custom {
        name: String,
        description: String,
    },
}

impl SchemaConstraint {
    /// Validate a molecule against this constraint
    pub fn validate(&self, molecule: &super::Molecule) -> Result<(), ValidationIssue> {
        // In a real implementation, this would use RDKit or another library to validate the constraint
        // For now, just return success for most constraints
        
        match self {
            Self::MinAtoms(min) => {
                // Check if the molecule has at least `min` atoms
                let num_atoms = molecule.properties.get("num_atoms")
                    .and_then(|v| v.as_u64())
                    .unwrap_or(0) as usize;
                
                if num_atoms < *min {
                    return Err(ValidationIssue {
                        constraint: self.clone(),
                        message: format!("Molecule has {} atoms, but at least {} are required", num_atoms, min),
                        severity: IssueSeverity::Error,
                    });
                }
            },
            Self::MaxAtoms(max) => {
                // Check if the molecule has at most `max` atoms
                let num_atoms = molecule.properties.get("num_atoms")
                    .and_then(|v| v.as_u64())
                    .unwrap_or(0) as usize;
                
                if num_atoms > *max {
                    return Err(ValidationIssue {
                        constraint: self.clone(),
                        message: format!("Molecule has {} atoms, but at most {} are allowed", num_atoms, max),
                        severity: IssueSeverity::Error,
                    });
                }
            },
            Self::RequiredElements(elements) => {
                // Check if the molecule contains all required elements
                // For now, just assume all required elements are present
                if elements.contains(&"X".to_string()) {
                    return Err(ValidationIssue {
                        constraint: self.clone(),
                        message: format!("Molecule is missing required element X"),
                        severity: IssueSeverity::Error,
                    });
                }
            },
            Self::AllowedElements(elements) => {
                // Check if the molecule contains only allowed elements
                // For now, just assume all elements are allowed
            },
            Self::ForbiddenElements(elements) => {
                // Check if the molecule contains any forbidden elements
                // For now, just assume no forbidden elements are present
            },
            Self::MinMolecularWeight(min) => {
                // Check if the molecule has at least the minimum molecular weight
                if let Some(mw) = molecule.molecular_weight {
                    if mw < *min {
                        return Err(ValidationIssue {
                            constraint: self.clone(),
                            message: format!("Molecule has molecular weight {}, but at least {} is required", mw, min),
                            severity: IssueSeverity::Error,
                        });
                    }
                } else {
                    return Err(ValidationIssue {
                        constraint: self.clone(),
                        message: "Molecule has no molecular weight information".to_string(),
                        severity: IssueSeverity::Warning,
                    });
                }
            },
            Self::MaxMolecularWeight(max) => {
                // Check if the molecule has at most the maximum molecular weight
                if let Some(mw) = molecule.molecular_weight {
                    if mw > *max {
                        return Err(ValidationIssue {
                            constraint: self.clone(),
                            message: format!("Molecule has molecular weight {}, but at most {} is allowed", mw, max),
                            severity: IssueSeverity::Error,
                        });
                    }
                } else {
                    return Err(ValidationIssue {
                        constraint: self.clone(),
                        message: "Molecule has no molecular weight information".to_string(),
                        severity: IssueSeverity::Warning,
                    });
                }
            },
            Self::Custom { name, description } => {
                // Custom constraint validation
                // For now, just assume all custom constraints pass
            },
        }
        
        Ok(())
    }
}

/// Result of validating a molecule against a schema
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationResult {
    /// Whether the molecule is valid according to the schema
    pub is_valid: bool,
    
    /// Issues found during validation
    pub issues: Vec<ValidationIssue>,
}

/// Issue found during schema validation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationIssue {
    /// Constraint that failed
    pub constraint: SchemaConstraint,
    
    /// Description of the issue
    pub message: String,
    
    /// Severity of the issue
    pub severity: IssueSeverity,
}

/// Severity of a validation issue
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum IssueSeverity {
    /// Informational message, not an error
    Info,
    
    /// Warning, may indicate a problem
    Warning,
    
    /// Error, indicates an invalid molecule
    Error,
}

/// Registry of molecule schemas
pub struct SchemaRegistry {
    schemas: HashMap<String, MoleculeSchema>,
}

impl SchemaRegistry {
    /// Create a new schema registry
    pub fn new() -> Self {
        Self {
            schemas: HashMap::new(),
        }
    }
    
    /// Get the global schema registry
    pub fn global() -> &'static Self {
        // In a real implementation, this would be a thread-safe singleton
        // For now, just return a new instance each time
        Box::leak(Box::new(Self::new()))
    }
    
    /// Register a new schema
    pub fn register_schema(&self, id: &str, schema: MoleculeSchema) -> &Self {
        unsafe {
            let self_mut = &mut *(self as *const Self as *mut Self);
            self_mut.schemas.insert(id.to_string(), schema);
        }
        self
    }
    
    /// Get a schema by ID
    pub fn get_schema(&self, id: &str) -> Option<&MoleculeSchema> {
        self.schemas.get(id)
    }
    
    /// Get all registered schemas
    pub fn get_all_schemas(&self) -> Vec<&MoleculeSchema> {
        self.schemas.values().collect()
    }
    
    /// Validate a molecule against a schema by ID
    pub fn validate(&self, id: &str, molecule: &super::Molecule) -> Option<ValidationResult> {
        self.get_schema(id).map(|schema| schema.validate(molecule))
    }
}
