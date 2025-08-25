//! Error handling for oxygen substrate processing

/// Result type for oxygen substrate operations
pub type Result<T> = std::result::Result<T, ProcessingError>;

/// Errors that can occur during oxygen-enhanced processing
#[derive(Debug, thiserror::Error)]
pub enum ProcessingError {
    #[error("Insufficient oxygen processing capacity: required {required}, available {available}")]
    InsufficientCapacity { required: f64, available: f64 },

    #[error("Invalid temperature for biological processing: {temperature}K")]
    InvalidTemperature { temperature: f64 },

    #[error("Quantum coherence lost during processing")]
    CoherenceLoss,

    #[error("Biological constraints violated: {constraint}")]
    BiologicalConstraintViolation { constraint: String },

    #[error("Paramagnetic oscillation failure: {reason}")]
    OscillationFailure { reason: String },

    #[error("Molecular data validation failed: {reason}")]
    ValidationFailure { reason: String },

    #[error("Enhancement processing failed: {reason}")]
    EnhancementFailure { reason: String },

    #[error("Substrate configuration invalid: {reason}")]
    InvalidConfiguration { reason: String },

    #[error("Processing timeout after {duration:?}")]
    ProcessingTimeout { duration: std::time::Duration },

    #[error("Insufficient molecular data: expected at least {minimum}, got {actual}")]
    InsufficientData { minimum: usize, actual: usize },

    #[error("Feature enhancement failed for molecule {molecule_id}: {reason}")]
    FeatureEnhancementFailure { molecule_id: String, reason: String },

    #[error("Oscillation pattern generation failed: {reason}")]
    OscillationPatternFailure { reason: String },

    #[error("Biological plausibility calculation failed: {reason}")]
    BiologicalPlausibilityFailure { reason: String },

    #[error("Quantum tunneling probability too low: {probability}")]
    QuantumTunnelingFailure { probability: f64 },

    #[error("Paramagnetic resonance not achieved: frequency {frequency} Hz")]
    ParametricResonanceFailure { frequency: f64 },

    #[error("Cellular compatibility check failed: {reason}")]
    CellularCompatibilityFailure { reason: String },

    #[error("Processing queue full: capacity {capacity}")]
    QueueCapacityExceeded { capacity: usize },

    #[error("Processing task not found: {task_id}")]
    ProcessingTaskNotFound { task_id: String },

    #[error("Concurrent processing limit exceeded: {limit}")]
    ConcurrentProcessingLimitExceeded { limit: usize },

    #[error("Memory allocation failed: requested {requested} bytes")]
    MemoryAllocationFailure { requested: usize },

    #[error("IO operation failed: {operation}")]
    IoFailure { operation: String },

    #[error("Serialization failed: {reason}")]
    SerializationFailure { reason: String },

    #[error("Deserialization failed: {reason}")]
    DeserializationFailure { reason: String },

    #[error("Network operation failed: {operation}")]
    NetworkFailure { operation: String },

    #[error("Authentication failed: {reason}")]
    AuthenticationFailure { reason: String },

    #[error("Authorization failed: insufficient permissions for {operation}")]
    AuthorizationFailure { operation: String },

    #[error("Rate limit exceeded: {limit} operations per {window:?}")]
    RateLimitExceeded { limit: u32, window: std::time::Duration },

    #[error("Internal error: {message}")]
    Internal { message: String },
}

impl ProcessingError {
    /// Check if the error is retryable
    pub fn is_retryable(&self) -> bool {
        match self {
            ProcessingError::ProcessingTimeout { .. } => true,
            ProcessingError::QueueCapacityExceeded { .. } => true,
            ProcessingError::ConcurrentProcessingLimitExceeded { .. } => true,
            ProcessingError::MemoryAllocationFailure { .. } => true,
            ProcessingError::NetworkFailure { .. } => true,
            ProcessingError::RateLimitExceeded { .. } => true,
            ProcessingError::CoherenceLoss => true,
            ProcessingError::OscillationFailure { .. } => true,
            _ => false,
        }
    }

    /// Get error severity level
    pub fn severity(&self) -> ErrorSeverity {
        match self {
            ProcessingError::Internal { .. } => ErrorSeverity::Critical,
            ProcessingError::AuthenticationFailure { .. } => ErrorSeverity::Critical,
            ProcessingError::AuthorizationFailure { .. } => ErrorSeverity::High,
            ProcessingError::BiologicalConstraintViolation { .. } => ErrorSeverity::High,
            ProcessingError::ValidationFailure { .. } => ErrorSeverity::High,
            ProcessingError::InvalidConfiguration { .. } => ErrorSeverity::High,
            ProcessingError::InvalidTemperature { .. } => ErrorSeverity::High,
            ProcessingError::InsufficientCapacity { .. } => ErrorSeverity::Medium,
            ProcessingError::InsufficientData { .. } => ErrorSeverity::Medium,
            ProcessingError::ProcessingTimeout { .. } => ErrorSeverity::Medium,
            ProcessingError::CoherenceLoss => ErrorSeverity::Medium,
            ProcessingError::QuantumTunnelingFailure { .. } => ErrorSeverity::Medium,
            ProcessingError::ParametricResonanceFailure { .. } => ErrorSeverity::Medium,
            ProcessingError::QueueCapacityExceeded { .. } => ErrorSeverity::Low,
            ProcessingError::RateLimitExceeded { .. } => ErrorSeverity::Low,
            _ => ErrorSeverity::Medium,
        }
    }

    /// Get error category
    pub fn category(&self) -> ErrorCategory {
        match self {
            ProcessingError::InsufficientCapacity { .. } => ErrorCategory::Resource,
            ProcessingError::InvalidTemperature { .. } => ErrorCategory::Configuration,
            ProcessingError::CoherenceLoss => ErrorCategory::Quantum,
            ProcessingError::BiologicalConstraintViolation { .. } => ErrorCategory::Biological,
            ProcessingError::OscillationFailure { .. } => ErrorCategory::Processing,
            ProcessingError::ValidationFailure { .. } => ErrorCategory::Validation,
            ProcessingError::EnhancementFailure { .. } => ErrorCategory::Processing,
            ProcessingError::InvalidConfiguration { .. } => ErrorCategory::Configuration,
            ProcessingError::ProcessingTimeout { .. } => ErrorCategory::Performance,
            ProcessingError::InsufficientData { .. } => ErrorCategory::Data,
            ProcessingError::FeatureEnhancementFailure { .. } => ErrorCategory::Processing,
            ProcessingError::OscillationPatternFailure { .. } => ErrorCategory::Processing,
            ProcessingError::BiologicalPlausibilityFailure { .. } => ErrorCategory::Biological,
            ProcessingError::QuantumTunnelingFailure { .. } => ErrorCategory::Quantum,
            ProcessingError::ParametricResonanceFailure { .. } => ErrorCategory::Quantum,
            ProcessingError::CellularCompatibilityFailure { .. } => ErrorCategory::Biological,
            ProcessingError::QueueCapacityExceeded { .. } => ErrorCategory::Resource,
            ProcessingError::ProcessingTaskNotFound { .. } => ErrorCategory::Data,
            ProcessingError::ConcurrentProcessingLimitExceeded { .. } => ErrorCategory::Resource,
            ProcessingError::MemoryAllocationFailure { .. } => ErrorCategory::Resource,
            ProcessingError::IoFailure { .. } => ErrorCategory::System,
            ProcessingError::SerializationFailure { .. } => ErrorCategory::Data,
            ProcessingError::DeserializationFailure { .. } => ErrorCategory::Data,
            ProcessingError::NetworkFailure { .. } => ErrorCategory::Network,
            ProcessingError::AuthenticationFailure { .. } => ErrorCategory::Security,
            ProcessingError::AuthorizationFailure { .. } => ErrorCategory::Security,
            ProcessingError::RateLimitExceeded { .. } => ErrorCategory::Performance,
            ProcessingError::Internal { .. } => ErrorCategory::System,
        }
    }

    /// Convert to a user-friendly error message
    pub fn user_message(&self) -> String {
        match self {
            ProcessingError::InsufficientCapacity { .. } => {
                "The system doesn't have enough processing capacity for this request. Please try with fewer molecules or wait for current processing to complete.".to_string()
            },
            ProcessingError::InvalidTemperature { temperature } => {
                format!("The specified temperature ({:.1}K) is outside the biological range (0°C to 50°C). Please adjust the temperature settings.", temperature)
            },
            ProcessingError::CoherenceLoss => {
                "Quantum coherence was lost during processing. This may be due to environmental interference or system instability.".to_string()
            },
            ProcessingError::BiologicalConstraintViolation { constraint } => {
                format!("The processing violated biological constraints: {}. Please review your input data.", constraint)
            },
            ProcessingError::ValidationFailure { reason } => {
                format!("Input validation failed: {}. Please check your molecular data format.", reason)
            },
            ProcessingError::ProcessingTimeout { .. } => {
                "Processing took longer than expected. The system may be under heavy load.".to_string()
            },
            _ => self.to_string(),
        }
    }
}

/// Error severity levels
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub enum ErrorSeverity {
    Low,
    Medium,
    High,
    Critical,
}

/// Error categories for classification
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ErrorCategory {
    Configuration,
    Resource,
    Quantum,
    Biological,
    Processing,
    Validation,
    Performance,
    Data,
    System,
    Network,
    Security,
}

/// Error context for detailed error reporting
#[derive(Debug, Clone)]
pub struct ErrorContext {
    pub error: ProcessingError,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub processing_id: Option<uuid::Uuid>,
    pub molecule_count: Option<usize>,
    pub processing_stage: Option<ProcessingStage>,
    pub system_state: Option<SystemState>,
}

impl ErrorContext {
    /// Create new error context
    pub fn new(error: ProcessingError) -> Self {
        Self {
            error,
            timestamp: chrono::Utc::now(),
            processing_id: None,
            molecule_count: None,
            processing_stage: None,
            system_state: None,
        }
    }

    /// Add processing context information
    pub fn with_processing_info(
        mut self,
        processing_id: uuid::Uuid,
        molecule_count: usize,
        stage: ProcessingStage,
    ) -> Self {
        self.processing_id = Some(processing_id);
        self.molecule_count = Some(molecule_count);
        self.processing_stage = Some(stage);
        self
    }

    /// Add system state information
    pub fn with_system_state(mut self, state: SystemState) -> Self {
        self.system_state = Some(state);
        self
    }
}

/// Processing stages for error context
#[derive(Debug, Clone)]
pub enum ProcessingStage {
    Validation,
    CapacityCheck,
    OscillationGeneration,
    ParametricEnhancement,
    BiologicalValidation,
    EvidenceGeneration,
    Finalization,
}

/// System state information for error context
#[derive(Debug, Clone)]
pub struct SystemState {
    pub cpu_usage: Option<f64>,
    pub memory_usage: Option<f64>,
    pub active_processes: Option<usize>,
    pub queue_length: Option<usize>,
    pub oxygen_utilization: Option<f64>,
    pub quantum_coherence_level: Option<f64>,
}

// Implement common conversions
impl From<std::io::Error> for ProcessingError {
    fn from(err: std::io::Error) -> Self {
        ProcessingError::IoFailure {
            operation: err.to_string(),
        }
    }
}

impl From<serde_json::Error> for ProcessingError {
    fn from(err: serde_json::Error) -> Self {
        ProcessingError::SerializationFailure {
            reason: err.to_string(),
        }
    }
}

impl From<tokio::time::error::Elapsed> for ProcessingError {
    fn from(err: tokio::time::error::Elapsed) -> Self {
        ProcessingError::ProcessingTimeout {
            duration: std::time::Duration::from_secs(30), // Default timeout
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_severity() {
        let error = ProcessingError::Internal { message: "Test".to_string() };
        assert_eq!(error.severity(), ErrorSeverity::Critical);

        let error = ProcessingError::InsufficientCapacity { required: 100.0, available: 50.0 };
        assert_eq!(error.severity(), ErrorSeverity::Medium);
    }

    #[test]
    fn test_error_category() {
        let error = ProcessingError::CoherenceLoss;
        assert_eq!(error.category(), ErrorCategory::Quantum);

        let error = ProcessingError::BiologicalConstraintViolation { 
            constraint: "temperature".to_string() 
        };
        assert_eq!(error.category(), ErrorCategory::Biological);
    }

    #[test]
    fn test_error_retryability() {
        let error = ProcessingError::ProcessingTimeout { 
            duration: std::time::Duration::from_secs(30) 
        };
        assert!(error.is_retryable());

        let error = ProcessingError::InvalidTemperature { temperature: 500.0 };
        assert!(!error.is_retryable());
    }

    #[test]
    fn test_error_context() {
        let error = ProcessingError::CoherenceLoss;
        let context = ErrorContext::new(error)
            .with_processing_info(
                uuid::Uuid::new_v4(),
                100,
                ProcessingStage::ParametricEnhancement,
            );

        assert!(context.processing_id.is_some());
        assert_eq!(context.molecule_count, Some(100));
    }

    #[test]
    fn test_user_message() {
        let error = ProcessingError::InvalidTemperature { temperature: 500.0 };
        let message = error.user_message();
        assert!(message.contains("biological range"));
        assert!(message.contains("500.0"));
    }
}
