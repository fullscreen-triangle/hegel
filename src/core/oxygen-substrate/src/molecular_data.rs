//! Molecular data structures and processing utilities

use serde::{Deserialize, Serialize};
use crate::error::{ProcessingError, Result};

/// Molecular data container for oxygen-enhanced processing
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MolecularData {
    /// Collection of molecules to process
    pub molecules: Vec<Molecule>,
    
    /// Metadata about the molecular dataset
    pub metadata: MolecularMetadata,
    
    /// Data source information
    pub source_info: Option<SourceInformation>,
}

impl MolecularData {
    /// Create new molecular data container
    pub fn new(molecules: Vec<Molecule>, metadata: MolecularMetadata) -> Self {
        Self {
            molecules,
            metadata,
            source_info: None,
        }
    }

    /// Calculate complexity of molecular data for processing requirements
    pub fn calculate_complexity(&self) -> f64 {
        let base_complexity = self.molecules.len() as f64;
        
        let feature_complexity: f64 = self.molecules.iter()
            .map(|m| m.features.len() as f64)
            .sum();
        
        let mass_complexity: f64 = self.molecules.iter()
            .map(|m| m.mass.log10().max(1.0))
            .sum();
            
        let interaction_complexity = self.calculate_interaction_complexity();
        
        // Weight different complexity factors
        base_complexity * 1.0 + 
        feature_complexity * 0.5 + 
        mass_complexity * 0.2 + 
        interaction_complexity * 0.3
    }

    /// Get total number of molecules
    pub fn molecule_count(&self) -> u64 {
        self.molecules.len() as u64
    }

    /// Calculate molecular interaction complexity
    fn calculate_interaction_complexity(&self) -> f64 {
        let n = self.molecules.len();
        if n <= 1 { 
            return 0.0; 
        }

        // Pairwise interaction complexity, scaled logarithmically
        let pairwise_interactions = (n * (n - 1)) as f64 / 2.0;
        pairwise_interactions.log10().max(1.0)
    }

    /// Validate molecular data structure
    pub fn validate(&self) -> Result<()> {
        if self.molecules.is_empty() {
            return Err(ProcessingError::InsufficientData {
                minimum: 1,
                actual: 0,
            });
        }

        // Check for duplicate molecule IDs
        let mut ids = std::collections::HashSet::new();
        for molecule in &self.molecules {
            if !ids.insert(&molecule.id) {
                return Err(ProcessingError::ValidationFailure {
                    reason: format!("Duplicate molecule ID: {}", molecule.id),
                });
            }
        }

        // Validate each molecule
        for molecule in &self.molecules {
            molecule.validate()?;
        }

        Ok(())
    }

    /// Get molecules by formula
    pub fn get_molecules_by_formula(&self, formula: &str) -> Vec<&Molecule> {
        self.molecules.iter()
            .filter(|m| m.formula == formula)
            .collect()
    }

    /// Get molecules within mass range
    pub fn get_molecules_by_mass_range(&self, min_mass: f64, max_mass: f64) -> Vec<&Molecule> {
        self.molecules.iter()
            .filter(|m| m.mass >= min_mass && m.mass <= max_mass)
            .collect()
    }

    /// Get molecules with specific feature
    pub fn get_molecules_with_feature(&self, feature_name: &str) -> Vec<&Molecule> {
        self.molecules.iter()
            .filter(|m| m.has_feature(feature_name))
            .collect()
    }

    /// Calculate dataset statistics
    pub fn get_statistics(&self) -> MolecularDataStatistics {
        if self.molecules.is_empty() {
            return MolecularDataStatistics::default();
        }

        let masses: Vec<f64> = self.molecules.iter().map(|m| m.mass).collect();
        let min_mass = masses.iter().fold(f64::INFINITY, |a, &b| a.min(b));
        let max_mass = masses.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
        let mean_mass = masses.iter().sum::<f64>() / masses.len() as f64;

        let total_features = self.molecules.iter()
            .map(|m| m.features.len())
            .sum();

        let unique_formulas = self.molecules.iter()
            .map(|m| &m.formula)
            .collect::<std::collections::HashSet<_>>()
            .len();

        MolecularDataStatistics {
            molecule_count: self.molecules.len(),
            total_features,
            unique_formulas,
            min_mass,
            max_mass,
            mean_mass,
            complexity_score: self.calculate_complexity(),
        }
    }
}

/// Individual molecule representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Molecule {
    /// Unique molecule identifier
    pub id: String,
    
    /// Chemical formula
    pub formula: String,
    
    /// Molecular mass in Daltons
    pub mass: f64,
    
    /// Molecular features (spectral peaks, properties, etc.)
    pub features: Vec<MolecularFeature>,
    
    /// Optional SMILES string
    pub smiles: Option<String>,
    
    /// Optional InChI identifier
    pub inchi: Option<String>,
    
    /// Molecule classification
    pub classification: Option<MoleculeClassification>,
}

impl Molecule {
    /// Create new molecule
    pub fn new(id: String, formula: String, mass: f64) -> Self {
        Self {
            id,
            formula,
            mass,
            features: Vec::new(),
            smiles: None,
            inchi: None,
            classification: None,
        }
    }

    /// Add molecular feature
    pub fn add_feature(&mut self, feature: MolecularFeature) {
        self.features.push(feature);
    }

    /// Check if molecule has a specific feature
    pub fn has_feature(&self, feature_name: &str) -> bool {
        self.features.iter().any(|f| f.name == feature_name)
    }

    /// Get feature by name
    pub fn get_feature(&self, feature_name: &str) -> Option<&MolecularFeature> {
        self.features.iter().find(|f| f.name == feature_name)
    }

    /// Validate molecule structure
    pub fn validate(&self) -> Result<()> {
        if self.id.is_empty() {
            return Err(ProcessingError::ValidationFailure {
                reason: "Molecule ID cannot be empty".to_string(),
            });
        }

        if self.formula.is_empty() {
            return Err(ProcessingError::ValidationFailure {
                reason: format!("Molecule {} has empty formula", self.id),
            });
        }

        if self.mass <= 0.0 {
            return Err(ProcessingError::ValidationFailure {
                reason: format!("Molecule {} has invalid mass: {}", self.id, self.mass),
            });
        }

        // Validate features
        for feature in &self.features {
            feature.validate(&self.id)?;
        }

        Ok(())
    }

    /// Calculate molecular complexity score
    pub fn complexity_score(&self) -> f64 {
        let feature_count = self.features.len() as f64;
        let mass_factor = self.mass.log10().max(1.0);
        let formula_complexity = self.formula.len() as f64 * 0.1;
        
        feature_count + mass_factor + formula_complexity
    }

    /// Apply paramagnetic enhancement to molecular features (from implementation guide)
    pub fn apply_paramagnetic_enhancement(&self, oscillation_factor: f64) -> crate::evidence::EnhancedMolecularFeatures {
        let mut enhanced = crate::evidence::EnhancedMolecularFeatures::new(self.id.clone());

        for feature in &self.features {
            let enhanced_value = feature.value * (1.0 + oscillation_factor * 0.1);
            let confidence_boost = oscillation_factor.abs() * 0.05;

            enhanced.add_feature(crate::evidence::EnhancedFeature {
                name: feature.name.clone(),
                original_value: feature.value,
                enhanced_value,
                confidence: (feature.confidence + confidence_boost).clamp(0.0, 1.0),
                enhancement_factor: 1.0 + oscillation_factor * 0.1,
                biological_plausibility: 1.0, // Will be calculated by processor
                quantum_coherence_factor: oscillation_factor.abs(),
            });
        }

        enhanced
    }
}

/// Individual molecular feature (spectral peak, property measurement, etc.)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MolecularFeature {
    /// Feature name/identifier
    pub name: String,
    
    /// Feature value (intensity, m/z, property value, etc.)
    pub value: f64,
    
    /// Confidence in the measurement
    pub confidence: f64,
    
    /// Feature type classification
    pub feature_type: FeatureType,
    
    /// Units of measurement
    pub units: Option<String>,
    
    /// Measurement uncertainty
    pub uncertainty: Option<f64>,
}

impl MolecularFeature {
    /// Create new molecular feature
    pub fn new(name: String, value: f64, confidence: f64, feature_type: FeatureType) -> Self {
        Self {
            name,
            value,
            confidence: confidence.clamp(0.0, 1.0),
            feature_type,
            units: None,
            uncertainty: None,
        }
    }

    /// Validate feature data
    pub fn validate(&self, molecule_id: &str) -> Result<()> {
        if self.name.is_empty() {
            return Err(ProcessingError::ValidationFailure {
                reason: format!("Feature name cannot be empty for molecule {}", molecule_id),
            });
        }

        if !self.value.is_finite() {
            return Err(ProcessingError::ValidationFailure {
                reason: format!("Feature {} has invalid value: {} for molecule {}", 
                    self.name, self.value, molecule_id),
            });
        }

        if self.confidence < 0.0 || self.confidence > 1.0 {
            return Err(ProcessingError::ValidationFailure {
                reason: format!("Feature {} has invalid confidence: {} for molecule {}", 
                    self.name, self.confidence, molecule_id),
            });
        }

        Ok(())
    }

    /// Check if feature value is within expected biological range
    pub fn is_biologically_plausible(&self) -> bool {
        match self.feature_type {
            FeatureType::MassSpectrum => {
                // m/z values should be positive and reasonable
                self.value > 0.0 && self.value < 10000.0
            },
            FeatureType::Intensity => {
                // Intensities should be non-negative
                self.value >= 0.0
            },
            FeatureType::RetentionTime => {
                // Retention times should be positive and reasonable
                self.value > 0.0 && self.value < 1000.0 // seconds/minutes
            },
            FeatureType::Energy => {
                // Biological energy ranges (eV or similar units)
                self.value > -50.0 && self.value < 50.0
            },
            FeatureType::Property => {
                // Property values - context dependent, generally finite
                self.value.is_finite()
            },
        }
    }
}

/// Types of molecular features
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum FeatureType {
    /// Mass spectrum peak (m/z value)
    MassSpectrum,
    
    /// Signal intensity
    Intensity,
    
    /// Chromatographic retention time
    RetentionTime,
    
    /// Energy measurement
    Energy,
    
    /// General molecular property
    Property,
}

/// Molecule classification categories
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MoleculeClassification {
    Protein,
    Nucleotide,
    Lipid,
    Carbohydrate,
    Metabolite,
    Drug,
    Unknown,
}

/// Metadata about molecular dataset
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MolecularMetadata {
    /// Data source description
    pub source: String,
    
    /// Data acquisition timestamp
    pub acquisition_time: chrono::DateTime<chrono::Utc>,
    
    /// Instrument settings used
    pub instrument_settings: InstrumentSettings,
    
    /// Sample preparation information
    pub sample_preparation: Option<String>,
    
    /// Experimental conditions
    pub experimental_conditions: Option<ExperimentalConditions>,
}

/// Instrument configuration and settings
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InstrumentSettings {
    /// Mass accuracy in ppm
    pub mass_accuracy: f64,
    
    /// Mass resolution
    pub resolution: f64,
    
    /// Ionization mode (ESI+, ESI-, APCI, etc.)
    pub ionization_mode: String,
    
    /// Instrument type
    pub instrument_type: Option<String>,
    
    /// Additional settings
    pub additional_settings: std::collections::HashMap<String, String>,
}

/// Experimental conditions
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExperimentalConditions {
    /// Temperature in Kelvin
    pub temperature: Option<f64>,
    
    /// Pressure in Pa
    pub pressure: Option<f64>,
    
    /// pH value
    pub ph: Option<f64>,
    
    /// Solvent system
    pub solvent: Option<String>,
    
    /// Additional conditions
    pub additional_conditions: std::collections::HashMap<String, String>,
}

/// Information about data source
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SourceInformation {
    /// Source database or file
    pub source_name: String,
    
    /// Version or timestamp
    pub version: Option<String>,
    
    /// Access URL or path
    pub access_url: Option<String>,
    
    /// Citation information
    pub citation: Option<String>,
    
    /// License information
    pub license: Option<String>,
}

/// Statistical summary of molecular data
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct MolecularDataStatistics {
    pub molecule_count: usize,
    pub total_features: usize,
    pub unique_formulas: usize,
    pub min_mass: f64,
    pub max_mass: f64,
    pub mean_mass: f64,
    pub complexity_score: f64,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_molecule_creation() {
        let molecule = Molecule::new(
            "glucose".to_string(),
            "C6H12O6".to_string(),
            180.156,
        );

        assert_eq!(molecule.id, "glucose");
        assert_eq!(molecule.formula, "C6H12O6");
        assert_eq!(molecule.mass, 180.156);
        assert!(molecule.features.is_empty());
    }

    #[test]
    fn test_molecule_validation() {
        let mut molecule = Molecule::new(
            "test".to_string(),
            "C1H4".to_string(),
            16.04,
        );

        assert!(molecule.validate().is_ok());

        // Test invalid mass
        molecule.mass = -10.0;
        assert!(molecule.validate().is_err());
    }

    #[test]
    fn test_molecular_feature() {
        let feature = MolecularFeature::new(
            "base_peak".to_string(),
            100.0,
            0.95,
            FeatureType::Intensity,
        );

        assert!(feature.validate("test_molecule").is_ok());
        assert!(feature.is_biologically_plausible());
    }

    #[test]
    fn test_molecular_data_complexity() {
        let molecules = vec![
            Molecule::new("mol1".to_string(), "C6H12O6".to_string(), 180.156),
            Molecule::new("mol2".to_string(), "C12H24O12".to_string(), 360.312),
        ];

        let metadata = MolecularMetadata {
            source: "test".to_string(),
            acquisition_time: chrono::Utc::now(),
            instrument_settings: InstrumentSettings {
                mass_accuracy: 5.0,
                resolution: 30000.0,
                ionization_mode: "ESI+".to_string(),
                instrument_type: None,
                additional_settings: std::collections::HashMap::new(),
            },
            sample_preparation: None,
            experimental_conditions: None,
        };

        let data = MolecularData::new(molecules, metadata);
        let complexity = data.calculate_complexity();
        
        assert!(complexity > 0.0);
        assert_eq!(data.molecule_count(), 2);
    }

    #[test]
    fn test_molecular_data_statistics() {
        let mut molecules = vec![
            Molecule::new("mol1".to_string(), "C6H12O6".to_string(), 180.156),
            Molecule::new("mol2".to_string(), "C12H24O12".to_string(), 360.312),
        ];

        molecules[0].add_feature(MolecularFeature::new(
            "intensity".to_string(),
            1000.0,
            0.9,
            FeatureType::Intensity,
        ));

        let metadata = MolecularMetadata {
            source: "test".to_string(),
            acquisition_time: chrono::Utc::now(),
            instrument_settings: InstrumentSettings {
                mass_accuracy: 5.0,
                resolution: 30000.0,
                ionization_mode: "ESI+".to_string(),
                instrument_type: None,
                additional_settings: std::collections::HashMap::new(),
            },
            sample_preparation: None,
            experimental_conditions: None,
        };

        let data = MolecularData::new(molecules, metadata);
        let stats = data.get_statistics();
        
        assert_eq!(stats.molecule_count, 2);
        assert_eq!(stats.total_features, 1);
        assert_eq!(stats.unique_formulas, 2);
        assert!(stats.min_mass > 0.0);
        assert!(stats.max_mass > stats.min_mass);
    }
}
