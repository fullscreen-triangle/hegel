//! # Mzekezeke - ML Workhorse for Biological Systems
//!
//! Mzekezeke serves as the primary machine learning engine for the Hegel biological computer
//! architecture, providing sophisticated pattern recognition and predictive modeling capabilities
//! specifically optimized for biological molecular data.
//!
//! ## Core Capabilities
//!
//! The Mzekezeke ML system provides:
//!
//! - **Advanced Pattern Recognition**: Deep learning models for molecular pattern detection
//! - **Predictive Modeling**: Time-series forecasting and molecular behavior prediction  
//! - **Feature Engineering**: Automated biological feature extraction and selection
//! - **Online Learning**: Continuous model adaptation with new biological data
//! - **Biological Constraint Integration**: ML models aware of biological feasibility
//!
//! ## Architecture
//!
//! The system consists of:
//! - **Neural Network Engine**: Deep learning models for complex pattern recognition
//! - **Traditional ML Engine**: Classical algorithms for structured biological data
//! - **Feature Engineering Pipeline**: Automated biological feature extraction
//! - **Model Management System**: Training, validation, and deployment management
//! - **Prediction Services**: Real-time inference for biological queries
//!
//! ## Usage
//!
//! ```rust
//! use mzekezeke::{MzekezekeEngine, BiologicalDataset, PredictionRequest};
//!
//! #[tokio::main]
//! async fn main() -> Result<(), Box<dyn std::error::Error>> {
//!     let mut ml_engine = MzekezekeEngine::new().await?;
//!     
//!     // Train on biological dataset
//!     let dataset = BiologicalDataset::from_molecular_data(molecular_data);
//!     let training_result = ml_engine.train_model(dataset).await?;
//!     
//!     // Make predictions
//!     let prediction_request = PredictionRequest::new("C6H12O6", features);
//!     let prediction = ml_engine.predict(prediction_request).await?;
//!     
//!     println!("Prediction confidence: {:.3}", prediction.confidence);
//!     Ok(())
//! }
//! ```

use std::sync::Arc;
use tokio::sync::RwLock;
use serde::{Deserialize, Serialize};
use tracing::{debug, info, warn, error};
use uuid::Uuid;
use nalgebra::{DMatrix, DVector};
use ndarray::{Array1, Array2, Array3};

pub mod neural_networks;
pub mod traditional_ml;
pub mod feature_engineering;
pub mod model_management;
pub mod prediction_services;
pub mod online_learning;
pub mod biological_constraints;
pub mod error;

// Re-exports for convenience
pub use neural_networks::{NeuralNetworkEngine, DeepLearningModel, NetworkArchitecture};
pub use traditional_ml::{TraditionalMLEngine, ClassificationModel, RegressionModel};
pub use feature_engineering::{FeatureEngineer, BiologicalFeatureExtractor, FeatureSelection};
pub use model_management::{ModelManager, ModelMetadata, ModelRegistry};
pub use prediction_services::{PredictionService, PredictionRequest, PredictionResult};
pub use online_learning::{OnlineLearningEngine, IncrementalModel, AdaptationStrategy};
pub use biological_constraints::{BiologicalConstraintIntegrator, ConstraintValidator};
pub use error::{MzekezekeError, Result};

/// ML system constants
pub mod constants {
    /// Default learning rate
    pub const DEFAULT_LEARNING_RATE: f64 = 0.001;
    
    /// Maximum training epochs
    pub const MAX_TRAINING_EPOCHS: usize = 1000;
    
    /// Early stopping patience
    pub const EARLY_STOPPING_PATIENCE: usize = 50;
    
    /// Minimum validation accuracy
    pub const MIN_VALIDATION_ACCURACY: f64 = 0.8;
    
    /// Feature selection threshold
    pub const FEATURE_SELECTION_THRESHOLD: f64 = 0.05;
    
    /// Biological plausibility weight
    pub const BIOLOGICAL_PLAUSIBILITY_WEIGHT: f64 = 0.3;
    
    /// Model performance cache size
    pub const MODEL_CACHE_SIZE: usize = 100;
    
    /// Batch size for training
    pub const DEFAULT_BATCH_SIZE: usize = 64;
    
    /// Validation split ratio
    pub const VALIDATION_SPLIT: f64 = 0.2;
}

/// High-level ML engine for biological pattern recognition and prediction
///
/// Mzekezeke integrates multiple ML approaches optimized for biological data,
/// providing a unified interface for pattern recognition, prediction, and
/// continuous learning in biological computing systems.
pub struct MzekezekeEngine {
    /// Neural network engine for deep learning
    neural_engine: Arc<NeuralNetworkEngine>,
    
    /// Traditional ML engine for structured data
    traditional_engine: Arc<TraditionalMLEngine>,
    
    /// Feature engineering pipeline
    feature_engineer: Arc<FeatureEngineer>,
    
    /// Model management system
    model_manager: Arc<RwLock<ModelManager>>,
    
    /// Prediction service
    prediction_service: Arc<PredictionService>,
    
    /// Online learning engine
    online_learning: Arc<RwLock<OnlineLearningEngine>>,
    
    /// Biological constraint integrator
    constraint_integrator: Arc<BiologicalConstraintIntegrator>,
    
    /// Performance statistics
    statistics: Arc<RwLock<MLStatistics>>,
    
    /// Configuration
    config: Arc<RwLock<MLConfiguration>>,
}

impl MzekezekeEngine {
    /// Create new Mzekezeke ML engine
    pub async fn new() -> Result<Self> {
        let neural_engine = NeuralNetworkEngine::new().await?;
        let traditional_engine = TraditionalMLEngine::new();
        let feature_engineer = FeatureEngineer::new();
        let model_manager = ModelManager::new();
        let prediction_service = PredictionService::new();
        let online_learning = OnlineLearningEngine::new();
        let constraint_integrator = BiologicalConstraintIntegrator::new();
        
        Ok(Self {
            neural_engine: Arc::new(neural_engine),
            traditional_engine: Arc::new(traditional_engine),
            feature_engineer: Arc::new(feature_engineer),
            model_manager: Arc::new(RwLock::new(model_manager)),
            prediction_service: Arc::new(prediction_service),
            online_learning: Arc::new(RwLock::new(online_learning)),
            constraint_integrator: Arc::new(constraint_integrator),
            statistics: Arc::new(RwLock::new(MLStatistics::new())),
            config: Arc::new(RwLock::new(MLConfiguration::default())),
        })
    }
    
    /// Create engine with custom configuration
    pub async fn with_config(config: MLConfiguration) -> Result<Self> {
        let mut engine = Self::new().await?;
        engine.update_configuration(config).await?;
        Ok(engine)
    }
    
    /// Train ML models on biological dataset
    pub async fn train_model(
        &self,
        dataset: BiologicalDataset,
    ) -> Result<TrainingResult> {
        let training_id = Uuid::new_v4();
        let start_time = std::time::Instant::now();
        
        info!(
            training_id = %training_id,
            dataset_size = dataset.samples.len(),
            features = dataset.feature_count(),
            "Starting ML model training"
        );

        // Step 1: Feature engineering and selection
        let engineered_features = self.feature_engineer
            .extract_biological_features(&dataset)
            .await?;
        
        let selected_features = self.feature_engineer
            .select_optimal_features(&engineered_features, &dataset.targets)
            .await?;

        info!(
            training_id = %training_id,
            original_features = dataset.feature_count(),
            engineered_features = engineered_features.feature_count(),
            selected_features = selected_features.len(),
            "Completed feature engineering"
        );

        // Step 2: Split dataset for training and validation
        let (train_data, val_data) = dataset.train_validation_split(constants::VALIDATION_SPLIT)?;

        // Step 3: Train neural network models
        let neural_training_result = self.neural_engine
            .train_model(&train_data, &val_data, &selected_features)
            .await?;

        // Step 4: Train traditional ML models
        let traditional_training_result = self.traditional_engine
            .train_ensemble(&train_data, &val_data, &selected_features)
            .await?;

        // Step 5: Integrate biological constraints
        let constraint_integration_result = self.constraint_integrator
            .integrate_constraints(&neural_training_result, &traditional_training_result)
            .await?;

        // Step 6: Model validation and selection
        let mut model_manager = self.model_manager.write().await;
        let best_model = model_manager.select_best_model(vec![
            neural_training_result.clone(),
            traditional_training_result.clone(),
        ]).await?;

        // Step 7: Register trained models
        let model_metadata = ModelMetadata {
            model_id: Uuid::new_v4(),
            model_type: best_model.model_type.clone(),
            training_dataset_id: dataset.id.clone(),
            features: selected_features.clone(),
            performance_metrics: best_model.performance_metrics.clone(),
            biological_constraints: constraint_integration_result.constraints,
            created_at: chrono::Utc::now(),
        };
        
        model_manager.register_model(model_metadata.clone()).await?;

        let training_duration = start_time.elapsed();

        let training_result = TrainingResult {
            training_id,
            best_model_id: model_metadata.model_id,
            neural_model_performance: neural_training_result.performance_metrics,
            traditional_model_performance: traditional_training_result.performance_metrics,
            selected_features,
            biological_constraint_satisfaction: constraint_integration_result.satisfaction_score,
            training_duration,
        };

        // Update statistics
        let mut stats = self.statistics.write().await;
        stats.record_training(
            training_duration,
            best_model.performance_metrics.accuracy,
            constraint_integration_result.satisfaction_score,
        );

        info!(
            training_id = %training_id,
            best_model_id = %training_result.best_model_id,
            accuracy = best_model.performance_metrics.accuracy,
            constraint_satisfaction = constraint_integration_result.satisfaction_score,
            duration_ms = training_duration.as_millis(),
            "Completed ML model training"
        );

        Ok(training_result)
    }
    
    /// Make prediction using trained models
    pub async fn predict(
        &self,
        request: PredictionRequest,
    ) -> Result<PredictionResult> {
        let prediction_id = Uuid::new_v4();
        let start_time = std::time::Instant::now();
        
        debug!(
            prediction_id = %prediction_id,
            input_features = request.features.len(),
            "Starting ML prediction"
        );

        // Step 1: Feature engineering for prediction
        let engineered_features = self.feature_engineer
            .engineer_features_for_prediction(&request.features)
            .await?;

        // Step 2: Get best available model
        let model_manager = self.model_manager.read().await;
        let best_model = model_manager.get_best_model().await?;

        // Step 3: Make prediction using neural networks
        let neural_prediction = self.neural_engine
            .predict(&engineered_features, &best_model.neural_model)
            .await?;

        // Step 4: Make prediction using traditional ML
        let traditional_prediction = self.traditional_engine
            .predict(&engineered_features, &best_model.traditional_model)
            .await?;

        // Step 5: Ensemble predictions
        let ensemble_prediction = self.prediction_service
            .ensemble_predictions(vec![neural_prediction, traditional_prediction])
            .await?;

        // Step 6: Validate biological constraints
        let constraint_validation = self.constraint_integrator
            .validate_prediction(&ensemble_prediction, &request)
            .await?;

        let prediction_duration = start_time.elapsed();

        let result = PredictionResult {
            prediction_id,
            request: request.clone(),
            prediction: ensemble_prediction.value,
            confidence: ensemble_prediction.confidence * constraint_validation.plausibility,
            biological_plausibility: constraint_validation.plausibility,
            model_contributions: vec![
                ModelContribution {
                    model_type: "neural".to_string(),
                    contribution: neural_prediction.confidence,
                },
                ModelContribution {
                    model_type: "traditional".to_string(),
                    contribution: traditional_prediction.confidence,
                },
            ],
            prediction_duration,
        };

        // Update statistics
        let mut stats = self.statistics.write().await;
        stats.record_prediction(prediction_duration, result.confidence);

        debug!(
            prediction_id = %prediction_id,
            prediction = result.prediction,
            confidence = result.confidence,
            duration_ms = prediction_duration.as_millis(),
            "Completed ML prediction"
        );

        Ok(result)
    }
    
    /// Perform batch predictions
    pub async fn batch_predict(
        &self,
        requests: Vec<PredictionRequest>,
    ) -> Result<Vec<PredictionResult>> {
        info!(
            request_count = requests.len(),
            "Starting batch ML predictions"
        );

        let batch_id = Uuid::new_v4();
        let mut results = Vec::new();

        // Process predictions in parallel batches
        let batch_size = 32; // Configurable batch size
        for (i, batch) in requests.chunks(batch_size).enumerate() {
            debug!(
                batch_id = %batch_id,
                batch_index = i,
                batch_size = batch.len(),
                "Processing prediction batch"
            );

            let batch_futures: Vec<_> = batch.iter()
                .map(|request| self.predict(request.clone()))
                .collect();

            let batch_results = futures::future::try_join_all(batch_futures).await?;
            results.extend(batch_results);
        }

        info!(
            batch_id = %batch_id,
            total_predictions = results.len(),
            "Completed batch ML predictions"
        );

        Ok(results)
    }
    
    /// Retrain models with new data (online learning)
    pub async fn online_update(
        &self,
        new_data: Vec<BiologicalSample>,
    ) -> Result<OnlineUpdateResult> {
        info!(
            new_samples = new_data.len(),
            "Starting online model update"
        );

        let mut online_learning = self.online_learning.write().await;
        let update_result = online_learning
            .update_models_incremental(new_data)
            .await?;

        // Update model registry with new performance metrics
        let mut model_manager = self.model_manager.write().await;
        model_manager.update_model_performance(update_result.updated_models).await?;

        info!(
            models_updated = update_result.updated_model_count,
            performance_improvement = update_result.performance_delta,
            "Completed online model update"
        );

        Ok(update_result)
    }
    
    /// Get ML performance statistics
    pub async fn get_statistics(&self) -> MLStatistics {
        self.statistics.read().await.clone()
    }
    
    /// Reset statistics
    pub async fn reset_statistics(&self) {
        let mut stats = self.statistics.write().await;
        *stats = MLStatistics::new();
        info!("Reset ML statistics");
    }

    /// Update configuration
    pub async fn update_configuration(&self, config: MLConfiguration) -> Result<()> {
        config.validate()?;
        
        let mut current_config = self.config.write().await;
        *current_config = config;
        
        info!("Updated ML configuration");
        Ok(())
    }

    /// Get model information
    pub async fn get_model_info(&self, model_id: Uuid) -> Result<ModelMetadata> {
        let model_manager = self.model_manager.read().await;
        model_manager.get_model_metadata(model_id).await
    }

    /// List all trained models
    pub async fn list_models(&self) -> Result<Vec<ModelMetadata>> {
        let model_manager = self.model_manager.read().await;
        model_manager.list_all_models().await
    }
}

/// ML performance statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MLStatistics {
    pub total_trainings: u64,
    pub successful_trainings: u64,
    pub total_predictions: u64,
    pub average_training_time: std::time::Duration,
    pub average_prediction_time: std::time::Duration,
    pub average_model_accuracy: f64,
    pub average_prediction_confidence: f64,
    pub average_biological_constraint_satisfaction: f64,
    pub models_trained: u64,
    pub online_updates: u64,
    pub feature_engineering_time: std::time::Duration,
    pub created_at: chrono::DateTime<chrono::Utc>,
    pub last_updated: chrono::DateTime<chrono::Utc>,
}

impl MLStatistics {
    pub fn new() -> Self {
        let now = chrono::Utc::now();
        Self {
            total_trainings: 0,
            successful_trainings: 0,
            total_predictions: 0,
            average_training_time: std::time::Duration::from_millis(0),
            average_prediction_time: std::time::Duration::from_millis(0),
            average_model_accuracy: 0.0,
            average_prediction_confidence: 0.0,
            average_biological_constraint_satisfaction: 0.0,
            models_trained: 0,
            online_updates: 0,
            feature_engineering_time: std::time::Duration::from_millis(0),
            created_at: now,
            last_updated: now,
        }
    }

    pub fn record_training(
        &mut self,
        duration: std::time::Duration,
        accuracy: f64,
        constraint_satisfaction: f64,
    ) {
        self.total_trainings += 1;
        self.successful_trainings += 1;
        self.models_trained += 1;

        // Update average training time
        let total_millis = self.average_training_time.as_millis() * (self.total_trainings - 1) as u128;
        let new_average_millis = (total_millis + duration.as_millis()) / self.total_trainings as u128;
        self.average_training_time = std::time::Duration::from_millis(new_average_millis as u64);

        // Update average accuracy
        self.average_model_accuracy = (self.average_model_accuracy * (self.total_trainings - 1) as f64 + accuracy) / self.total_trainings as f64;

        // Update average constraint satisfaction
        self.average_biological_constraint_satisfaction = (self.average_biological_constraint_satisfaction * (self.total_trainings - 1) as f64 + constraint_satisfaction) / self.total_trainings as f64;

        self.last_updated = chrono::Utc::now();
    }

    pub fn record_prediction(&mut self, duration: std::time::Duration, confidence: f64) {
        self.total_predictions += 1;

        // Update average prediction time
        let total_millis = self.average_prediction_time.as_millis() * (self.total_predictions - 1) as u128;
        let new_average_millis = (total_millis + duration.as_millis()) / self.total_predictions as u128;
        self.average_prediction_time = std::time::Duration::from_millis(new_average_millis as u64);

        // Update average confidence
        self.average_prediction_confidence = (self.average_prediction_confidence * (self.total_predictions - 1) as f64 + confidence) / self.total_predictions as f64;

        self.last_updated = chrono::Utc::now();
    }

    pub fn training_success_rate(&self) -> f64 {
        if self.total_trainings == 0 {
            return 0.0;
        }
        self.successful_trainings as f64 / self.total_trainings as f64
    }
}

/// ML system configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MLConfiguration {
    pub learning_rate: f64,
    pub max_epochs: usize,
    pub batch_size: usize,
    pub validation_split: f64,
    pub early_stopping_patience: usize,
    pub min_validation_accuracy: f64,
    pub biological_constraint_weight: f64,
    pub enable_online_learning: bool,
    pub enable_gpu_acceleration: bool,
    pub model_cache_size: usize,
}

impl Default for MLConfiguration {
    fn default() -> Self {
        Self {
            learning_rate: constants::DEFAULT_LEARNING_RATE,
            max_epochs: constants::MAX_TRAINING_EPOCHS,
            batch_size: constants::DEFAULT_BATCH_SIZE,
            validation_split: constants::VALIDATION_SPLIT,
            early_stopping_patience: constants::EARLY_STOPPING_PATIENCE,
            min_validation_accuracy: constants::MIN_VALIDATION_ACCURACY,
            biological_constraint_weight: constants::BIOLOGICAL_PLAUSIBILITY_WEIGHT,
            enable_online_learning: true,
            enable_gpu_acceleration: false,
            model_cache_size: constants::MODEL_CACHE_SIZE,
        }
    }
}

impl MLConfiguration {
    pub fn validate(&self) -> Result<()> {
        if self.learning_rate <= 0.0 || self.learning_rate > 1.0 {
            return Err(MzekezekeError::InvalidConfiguration {
                reason: "learning_rate must be between 0.0 and 1.0".to_string(),
            });
        }

        if self.validation_split <= 0.0 || self.validation_split >= 1.0 {
            return Err(MzekezekeError::InvalidConfiguration {
                reason: "validation_split must be between 0.0 and 1.0".to_string(),
            });
        }

        if self.batch_size == 0 {
            return Err(MzekezekeError::InvalidConfiguration {
                reason: "batch_size must be greater than 0".to_string(),
            });
        }

        Ok(())
    }
}

// Data structures
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BiologicalDataset {
    pub id: String,
    pub samples: Vec<BiologicalSample>,
    pub targets: Vec<f64>,
    pub feature_names: Vec<String>,
    pub metadata: DatasetMetadata,
}

impl BiologicalDataset {
    pub fn feature_count(&self) -> usize {
        self.feature_names.len()
    }

    pub fn train_validation_split(&self, validation_ratio: f64) -> Result<(Self, Self)> {
        if validation_ratio <= 0.0 || validation_ratio >= 1.0 {
            return Err(MzekezekeError::InvalidInput {
                message: "Validation ratio must be between 0 and 1".to_string(),
            });
        }

        let validation_size = (self.samples.len() as f64 * validation_ratio) as usize;
        let train_size = self.samples.len() - validation_size;

        let train_samples = self.samples[..train_size].to_vec();
        let val_samples = self.samples[train_size..].to_vec();
        let train_targets = self.targets[..train_size].to_vec();
        let val_targets = self.targets[train_size..].to_vec();

        let train_dataset = BiologicalDataset {
            id: format!("{}_train", self.id),
            samples: train_samples,
            targets: train_targets,
            feature_names: self.feature_names.clone(),
            metadata: self.metadata.clone(),
        };

        let val_dataset = BiologicalDataset {
            id: format!("{}_validation", self.id),
            samples: val_samples,
            targets: val_targets,
            feature_names: self.feature_names.clone(),
            metadata: self.metadata.clone(),
        };

        Ok((train_dataset, val_dataset))
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BiologicalSample {
    pub id: String,
    pub features: Vec<f64>,
    pub molecular_formula: Option<String>,
    pub biological_context: BiologicalContext,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BiologicalContext {
    pub organism: Option<String>,
    pub tissue_type: Option<String>,
    pub experimental_conditions: Option<String>,
    pub pathway: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatasetMetadata {
    pub source: String,
    pub creation_date: chrono::DateTime<chrono::Utc>,
    pub description: String,
    pub biological_domain: String,
}

// Result types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrainingResult {
    pub training_id: Uuid,
    pub best_model_id: Uuid,
    pub neural_model_performance: PerformanceMetrics,
    pub traditional_model_performance: PerformanceMetrics,
    pub selected_features: Vec<String>,
    pub biological_constraint_satisfaction: f64,
    pub training_duration: std::time::Duration,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceMetrics {
    pub accuracy: f64,
    pub precision: f64,
    pub recall: f64,
    pub f1_score: f64,
    pub auc_roc: f64,
    pub biological_plausibility_score: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelContribution {
    pub model_type: String,
    pub contribution: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OnlineUpdateResult {
    pub updated_model_count: usize,
    pub performance_delta: f64,
    pub updated_models: Vec<Uuid>,
}

impl Default for MLStatistics {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_mzekezeke_engine_creation() {
        let engine = MzekezekeEngine::new().await;
        assert!(engine.is_ok());
    }

    #[test]
    fn test_ml_configuration() {
        let config = MLConfiguration::default();
        assert!(config.validate().is_ok());
        
        let mut invalid_config = config;
        invalid_config.learning_rate = 2.0;
        assert!(invalid_config.validate().is_err());
    }

    #[test]
    fn test_dataset_split() {
        let dataset = BiologicalDataset {
            id: "test_dataset".to_string(),
            samples: vec![
                BiologicalSample {
                    id: "sample1".to_string(),
                    features: vec![1.0, 2.0, 3.0],
                    molecular_formula: None,
                    biological_context: BiologicalContext {
                        organism: None,
                        tissue_type: None,
                        experimental_conditions: None,
                        pathway: None,
                    },
                };
                100
            ],
            targets: vec![1.0; 100],
            feature_names: vec!["feature1".to_string(), "feature2".to_string(), "feature3".to_string()],
            metadata: DatasetMetadata {
                source: "test".to_string(),
                creation_date: chrono::Utc::now(),
                description: "Test dataset".to_string(),
                biological_domain: "test".to_string(),
            },
        };

        let result = dataset.train_validation_split(0.2);
        assert!(result.is_ok());
        
        let (train, val) = result.unwrap();
        assert_eq!(train.samples.len(), 80);
        assert_eq!(val.samples.len(), 20);
    }

    #[test]
    fn test_statistics_recording() {
        let mut stats = MLStatistics::new();
        
        stats.record_training(
            std::time::Duration::from_secs(120),
            0.95,
            0.88,
        );
        
        assert_eq!(stats.total_trainings, 1);
        assert_eq!(stats.average_model_accuracy, 0.95);
        assert_eq!(stats.training_success_rate(), 1.0);
        
        stats.record_prediction(std::time::Duration::from_millis(10), 0.92);
        assert_eq!(stats.total_predictions, 1);
        assert_eq!(stats.average_prediction_confidence, 0.92);
    }
}
