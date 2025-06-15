"""
Model Registry for centralized model management in Diadochi.

The registry provides a central repository for managing multiple model instances,
allowing easy registration, retrieval, and configuration of domain expert models.
"""

import logging
from typing import Dict, List, Optional, Any
from .models import Model, ModelConfig, create_model

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Registry for managing multiple models."""
    
    def __init__(self):
        """Initialize the registry."""
        self.models: Dict[str, Model] = {}
        self.configs: Dict[str, ModelConfig] = {}
    
    def add_model(
        self, 
        name: str, 
        engine: str, 
        model_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        timeout: int = 30,
        **kwargs
    ) -> None:
        """
        Register a new model.
        
        Args:
            name: Unique identifier for the model
            engine: Model engine ("ollama", "openai", "anthropic", "huggingface")
            model_name: Name of the model (e.g., "gpt-4", "llama2", "claude-3-sonnet")
            api_key: API key for the model service
            base_url: Base URL for the model service
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
            **kwargs: Additional parameters for the model
        """
        if name in self.models:
            logger.warning(f"Model '{name}' already exists, replacing...")
        
        config = ModelConfig(
            name=name,
            engine=engine,
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            extra_params=kwargs
        )
        
        try:
            model = create_model(config)
            self.models[name] = model
            self.configs[name] = config
            logger.info(f"Successfully registered model '{name}' ({engine}:{model_name})")
        except Exception as e:
            logger.error(f"Failed to register model '{name}': {e}")
            raise
    
    def get(self, name: str) -> Model:
        """
        Retrieve a registered model by name.
        
        Args:
            name: Name of the model to retrieve
            
        Returns:
            Model instance
            
        Raises:
            KeyError: If model is not found
        """
        if name not in self.models:
            raise KeyError(f"Model '{name}' not found in registry")
        return self.models[name]
    
    def get_config(self, name: str) -> ModelConfig:
        """
        Retrieve a model's configuration by name.
        
        Args:
            name: Name of the model
            
        Returns:
            ModelConfig instance
            
        Raises:
            KeyError: If model is not found
        """
        if name not in self.configs:
            raise KeyError(f"Model config '{name}' not found in registry")
        return self.configs[name]
    
    def list_models(self) -> List[str]:
        """
        List all registered models.
        
        Returns:
            List of model names
        """
        return list(self.models.keys())
    
    def remove_model(self, name: str) -> None:
        """
        Remove a model from the registry.
        
        Args:
            name: Name of the model to remove
            
        Raises:
            KeyError: If model is not found
        """
        if name not in self.models:
            raise KeyError(f"Model '{name}' not found in registry")
        
        del self.models[name]
        del self.configs[name]
        logger.info(f"Removed model '{name}' from registry")
    
    def check_availability(self) -> Dict[str, bool]:
        """
        Check the availability of all registered models.
        
        Returns:
            Dictionary mapping model names to availability status
        """
        availability = {}
        for name, model in self.models.items():
            try:
                availability[name] = model.is_available()
            except Exception as e:
                logger.error(f"Error checking availability of model '{name}': {e}")
                availability[name] = False
        
        return availability
    
    def get_models_by_engine(self, engine: str) -> List[str]:
        """
        Get all models using a specific engine.
        
        Args:
            engine: Engine name to filter by
            
        Returns:
            List of model names using the specified engine
        """
        return [
            name for name, config in self.configs.items() 
            if config.engine == engine
        ]
    
    def get_available_models(self) -> List[str]:
        """
        Get all currently available models.
        
        Returns:
            List of available model names
        """
        availability = self.check_availability()
        return [name for name, available in availability.items() if available]
    
    def update_model_config(
        self, 
        name: str, 
        **kwargs
    ) -> None:
        """
        Update configuration for an existing model.
        
        Args:
            name: Name of the model to update
            **kwargs: Configuration parameters to update
            
        Raises:
            KeyError: If model is not found
        """
        if name not in self.configs:
            raise KeyError(f"Model '{name}' not found in registry")
        
        config = self.configs[name]
        
        # Update configuration
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                config.extra_params[key] = value
        
        # Recreate the model with updated config
        try:
            model = create_model(config)
            self.models[name] = model
            logger.info(f"Updated configuration for model '{name}'")
        except Exception as e:
            logger.error(f"Failed to update model '{name}': {e}")
            raise
    
    def clear(self) -> None:
        """Clear all models from the registry."""
        self.models.clear()
        self.configs.clear()
        logger.info("Cleared all models from registry")
    
    def get_registry_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about the registry.
        
        Returns:
            Dictionary with registry statistics and model information
        """
        availability = self.check_availability()
        engines = {}
        for config in self.configs.values():
            engines[config.engine] = engines.get(config.engine, 0) + 1
        
        return {
            "total_models": len(self.models),
            "available_models": sum(availability.values()),
            "unavailable_models": len(self.models) - sum(availability.values()),
            "engines": engines,
            "models": {
                name: {
                    "engine": config.engine,
                    "model_name": config.model_name,
                    "available": availability.get(name, False)
                }
                for name, config in self.configs.items()
            }
        }
    
    def __len__(self) -> int:
        """Return the number of registered models."""
        return len(self.models)
    
    def __contains__(self, name: str) -> bool:
        """Check if a model is registered."""
        return name in self.models
    
    def __iter__(self):
        """Iterate over model names."""
        return iter(self.models.keys())
    
    def __repr__(self) -> str:
        """String representation of the registry."""
        return f"ModelRegistry({len(self.models)} models: {list(self.models.keys())})" 