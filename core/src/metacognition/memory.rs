//! Memory System Module
//! 
//! This module provides a memory system for storing and retrieving contextual information
//! about molecules, their processing history, and decisions made by the system.

use anyhow::Result;
use log::{debug, info};
use serde::{Serialize, Deserialize};
use std::collections::{HashMap, VecDeque};
use std::sync::{Arc, Mutex};
use std::time::{Duration, SystemTime};

/// Initialize the memory module
pub fn initialize() -> Result<()> {
    info!("Initializing memory system module");
    info!("Memory system module initialized successfully");
    Ok(())
}

/// Main memory system for the Hegel platform
#[derive(Debug, Clone)]
pub struct MemorySystem {
    /// In-memory cache for fast retrieval of recent contexts
    context_cache: Arc<Mutex<LruCache<String, context::Context>>>,
    
    /// Storage directory for persistent memory
    storage_dir: String,
    
    /// Maximum number of contexts to keep in memory
    cache_size: usize,
}

impl MemorySystem {
    /// Create a new memory system
    pub fn new() -> Result<Self> {
        let storage_dir = std::env::var("HEGEL_MEMORY_STORAGE_DIR")
            .unwrap_or_else(|_| "./data/memory".to_string());
        
        let cache_size = std::env::var("HEGEL_MEMORY_CACHE_SIZE")
            .unwrap_or_else(|_| "100".to_string())
            .parse()
            .unwrap_or(100);
        
        // Ensure the storage directory exists
        std::fs::create_dir_all(&storage_dir)?;
        
        Ok(Self {
            context_cache: Arc::new(Mutex::new(LruCache::new(cache_size))),
            storage_dir,
            cache_size,
        })
    }
    
    /// Store a processing context
    pub fn store_context(&self, context: context::Context) -> Result<()> {
        let context_id = context.id.clone();
        debug!("Storing context: {}", context_id);
        
        // Add to in-memory cache
        self.context_cache.lock().unwrap().put(context_id.clone(), context.clone());
        
        // Persist to disk
        self.persist_context(&context)?;
        
        Ok(())
    }
    
    /// Retrieve a context by ID
    pub fn retrieve_context(&self, context_id: &str) -> Result<Option<context::Context>> {
        debug!("Retrieving context: {}", context_id);
        
        // Check in-memory cache first
        {
            let mut cache = self.context_cache.lock().unwrap();
            if let Some(context) = cache.get(context_id) {
                return Ok(Some(context.clone()));
            }
        }
        
        // If not in cache, try to load from disk
        match self.load_context(context_id) {
            Ok(context) => {
                // Add to cache
                self.context_cache.lock().unwrap().put(context_id.to_string(), context.clone());
                Ok(Some(context))
            }
            Err(_) => Ok(None),
        }
    }
    
    /// Find contexts related to a molecule
    pub fn find_contexts_by_molecule(&self, molecule_id: &str) -> Result<Vec<context::Context>> {
        debug!("Finding contexts for molecule: {}", molecule_id);
        
        let mut related_contexts = Vec::new();
        
        // Check persistent storage for related contexts
        let paths = std::fs::read_dir(&self.storage_dir)?;
        
        for path in paths {
            let path = path?.path();
            if let Some(filename) = path.file_name() {
                if let Some(filename_str) = filename.to_str() {
                    if filename_str.ends_with(".json") {
                        // Load the context and check if it's related to the molecule
                        if let Ok(context) = self.load_context_from_path(&path) {
                            if context.is_related_to_molecule(molecule_id) {
                                related_contexts.push(context);
                            }
                        }
                    }
                }
            }
        }
        
        // Sort by timestamp, most recent first
        related_contexts.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));
        
        Ok(related_contexts)
    }
    
    /// Persist a context to disk
    fn persist_context(&self, context: &context::Context) -> Result<()> {
        let json = serde_json::to_string_pretty(context)?;
        let path = format!("{}/{}.json", self.storage_dir, context.id);
        std::fs::write(path, json)?;
        Ok(())
    }
    
    /// Load a context from disk
    fn load_context(&self, context_id: &str) -> Result<context::Context> {
        let path = format!("{}/{}.json", self.storage_dir, context_id);
        self.load_context_from_path(&std::path::PathBuf::from(path))
    }
    
    /// Load a context from a specific path
    fn load_context_from_path(&self, path: &std::path::Path) -> Result<context::Context> {
        let json = std::fs::read_to_string(path)?;
        let context = serde_json::from_str(&json)?;
        Ok(context)
    }
}

/// Simple LRU cache implementation
#[derive(Debug)]
struct LruCache<K, V> {
    map: HashMap<K, V>,
    queue: VecDeque<K>,
    capacity: usize,
}

impl<K, V> LruCache<K, V>
where
    K: Clone + std::cmp::Eq + std::hash::Hash,
    V: Clone,
{
    /// Create a new LRU cache with the given capacity
    fn new(capacity: usize) -> Self {
        Self {
            map: HashMap::with_capacity(capacity),
            queue: VecDeque::with_capacity(capacity),
            capacity,
        }
    }
    
    /// Get a value from the cache
    fn get(&mut self, key: &K) -> Option<&V> {
        if self.map.contains_key(key) {
            // Move the key to the end of the queue (most recently used)
            let pos = self.queue.iter().position(|k| k == key).unwrap();
            let k = self.queue.remove(pos).unwrap();
            self.queue.push_back(k);
            
            return self.map.get(key);
        }
        
        None
    }
    
    /// Put a value in the cache
    fn put(&mut self, key: K, value: V) {
        if self.map.contains_key(&key) {
            // Update existing value
            self.map.insert(key.clone(), value);
            
            // Move the key to the end of the queue (most recently used)
            let pos = self.queue.iter().position(|k| k == &key).unwrap();
            let k = self.queue.remove(pos).unwrap();
            self.queue.push_back(k);
        } else {
            // If at capacity, remove the least recently used item
            if self.queue.len() >= self.capacity {
                if let Some(old_key) = self.queue.pop_front() {
                    self.map.remove(&old_key);
                }
            }
            
            // Insert new item
            self.map.insert(key.clone(), value);
            self.queue.push_back(key);
        }
    }
}

/// Context module for processing contexts
pub mod context {
    use super::*;
    use std::collections::HashSet;
    
    /// Processing context for a single session
    #[derive(Debug, Clone, Serialize, Deserialize)]
    pub struct Context {
        /// Unique ID for this context
        pub id: String,
        
        /// Unix timestamp when the context was created
        pub timestamp: u64,
        
        /// Molecules involved in this context
        pub molecules: HashSet<String>,
        
        /// Processing steps performed
        pub steps: Vec<ProcessingStep>,
        
        /// Additional metadata
        pub metadata: HashMap<String, serde_json::Value>,
    }
    
    impl Context {
        /// Create a new context
        pub fn new() -> Self {
            let now = SystemTime::now().duration_since(SystemTime::UNIX_EPOCH)
                .unwrap_or(Duration::from_secs(0))
                .as_secs();
                
            Self {
                id: generate_context_id(),
                timestamp: now,
                molecules: HashSet::new(),
                steps: Vec::new(),
                metadata: HashMap::new(),
            }
        }
        
        /// Add a molecule to the context
        pub fn add_molecule(&mut self, molecule_id: &str) {
            self.molecules.insert(molecule_id.to_string());
        }
        
        /// Add a processing step to the context
        pub fn add_step(&mut self, step: ProcessingStep) {
            self.steps.push(step);
        }
        
        /// Check if this context is related to a specific molecule
        pub fn is_related_to_molecule(&self, molecule_id: &str) -> bool {
            self.molecules.contains(molecule_id)
        }
        
        /// Add metadata to the context
        pub fn add_metadata(&mut self, key: &str, value: serde_json::Value) {
            self.metadata.insert(key.to_string(), value);
        }
    }
    
    /// A processing step in a context
    #[derive(Debug, Clone, Serialize, Deserialize)]
    pub struct ProcessingStep {
        /// Type of processing step
        pub step_type: StepType,
        
        /// Description of the step
        pub description: String,
        
        /// Timestamp when the step was performed
        pub timestamp: u64,
        
        /// Result of the step
        pub result: StepResult,
    }
    
    /// Type of processing step
    #[derive(Debug, Clone, Serialize, Deserialize)]
    pub enum StepType {
        /// Molecule validation step
        Validation,
        
        /// Data retrieval step
        DataRetrieval,
        
        /// Comparison step
        Comparison,
        
        /// Decision step
        Decision,
        
        /// LLM query step
        LLMQuery,
        
        /// Custom step
        Custom(String),
    }
    
    /// Result of a processing step
    #[derive(Debug, Clone, Serialize, Deserialize)]
    pub enum StepResult {
        /// Success with a value
        Success(serde_json::Value),
        
        /// Failure with an error message
        Failure(String),
        
        /// Decision with a confidence score
        Decision {
            decision: String,
            confidence: f64,
            explanation: String,
        },
    }
    
    /// Generate a unique context ID
    fn generate_context_id() -> String {
        use std::hash::{Hash, Hasher};
        use std::collections::hash_map::DefaultHasher;
        
        let now = SystemTime::now().duration_since(SystemTime::UNIX_EPOCH)
            .unwrap_or(Duration::from_secs(0))
            .as_nanos();
            
        let rand = rand::random::<u64>();
        
        let mut hasher = DefaultHasher::new();
        now.hash(&mut hasher);
        rand.hash(&mut hasher);
        
        format!("ctx_{:016x}", hasher.finish())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_initialization() {
        assert!(initialize().is_ok());
    }
    
    #[test]
    fn test_memory_system_creation() {
        let memory = MemorySystem::new();
        assert!(memory.is_ok());
    }
    
    #[test]
    fn test_context_creation() {
        let context = context::Context::new();
        assert!(!context.id.is_empty());
    }
}
