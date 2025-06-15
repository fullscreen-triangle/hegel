"""
Router-Based Ensemble pattern implementation for Diadochi.

This module implements the Router-Based Ensemble architectural pattern,
which directs queries to the most appropriate domain expert model based on query analysis.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass

from ..core.models import Model
from ..core.routers import Router
from ..core.mixers import Mixer, DefaultMixer
from ..core.registry import ModelRegistry

logger = logging.getLogger(__name__)


@dataclass
class EnsembleConfig:
    """Configuration for ensemble behavior."""
    default_model: Optional[str] = None
    fallback_strategy: str = "default"  # "default", "random", "all"
    timeout: int = 30
    parallel_execution: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0


class Ensemble:
    """Router-based ensemble that directs queries to appropriate domain experts."""
    
    def __init__(
        self,
        router: Router,
        models: Union[ModelRegistry, Dict[str, Model]],
        mixer: Optional[Mixer] = None,
        config: Optional[EnsembleConfig] = None
    ):
        """
        Initialize the ensemble.
        
        Args:
            router: Router for directing queries to appropriate models
            models: Registry or dictionary of available models
            mixer: Optional mixer for combining multiple responses
            config: Configuration for ensemble behavior
        """
        self.router = router
        self.mixer = mixer or DefaultMixer()
        self.config = config or EnsembleConfig()
        
        # Handle different model input types
        if isinstance(models, ModelRegistry):
            self.registry = models
        elif isinstance(models, dict):
            # Create a registry from dictionary
            self.registry = ModelRegistry()
            for name, model in models.items():
                # Add models directly to registry (bypass normal registration)
                self.registry.models[name] = model
                # Create a basic config for the model
                from ..core.models import ModelConfig
                self.registry.configs[name] = ModelConfig(
                    name=name,
                    engine="custom",
                    model_name=name
                )
        else:
            raise ValueError("models must be a ModelRegistry or dictionary of Model instances")
        
        # Performance tracking
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "model_usage": {},
            "average_response_time": 0.0
        }
    
    async def generate(
        self, 
        query: str, 
        top_k: int = 1,
        include_routing_info: bool = False,
        **kwargs
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate a response using the ensemble.
        
        Args:
            query: Input query
            top_k: Number of models to use (1 for single routing, >1 for multi-expert)
            include_routing_info: Whether to include routing information in response
            **kwargs: Additional parameters for generation
            
        Returns:
            Generated response, optionally with routing information
        """
        import time
        start_time = time.time()
        
        try:
            self.stats["total_queries"] += 1
            
            # Get available models
            available_models = self.registry.get_available_models()
            
            if not available_models:
                logger.warning("No available models for ensemble")
                return self._handle_no_available_models(query, include_routing_info)
            
            # Route the query
            if top_k == 1:
                selected_model = await self.router.route(query, available_models)
                if selected_model:
                    selected_models = [(selected_model, 1.0)]
                else:
                    selected_models = []
            else:
                selected_models = await self.router.route_multiple(query, available_models, k=top_k)
            
            # Handle no routing results
            if not selected_models:
                logger.warning(f"Router found no suitable models for query: {query[:100]}...")
                return await self._handle_fallback(query, available_models, include_routing_info, **kwargs)
            
            # Generate responses
            responses = await self._generate_responses(query, selected_models, **kwargs)
            
            # Mix responses if multiple
            if len(responses) == 1:
                final_response = next(iter(responses.values()))
            else:
                weights = {model: weight for model, weight in selected_models if model in responses}
                final_response = await self.mixer.mix(query, responses, weights)
            
            # Update statistics
            self.stats["successful_queries"] += 1
            response_time = time.time() - start_time
            self._update_response_time(response_time)
            
            # Update model usage stats
            for model_name in responses.keys():
                self.stats["model_usage"][model_name] = self.stats["model_usage"].get(model_name, 0) + 1
            
            # Return response with optional routing info
            if include_routing_info:
                return {
                    "response": final_response,
                    "routing_info": {
                        "selected_models": selected_models,
                        "responses": responses,
                        "response_time": response_time,
                        "fallback_used": False
                    }
                }
            else:
                return final_response
        
        except Exception as e:
            logger.error(f"Error in ensemble generation: {e}")
            self.stats["failed_queries"] += 1
            
            if include_routing_info:
                return {
                    "response": f"Error: {str(e)}",
                    "routing_info": {
                        "error": str(e),
                        "fallback_used": True
                    }
                }
            else:
                return f"Error: {str(e)}"
    
    async def _generate_responses(
        self, 
        query: str, 
        selected_models: List[Tuple[str, float]], 
        **kwargs
    ) -> Dict[str, str]:
        """Generate responses from selected models."""
        responses = {}
        
        if self.config.parallel_execution and len(selected_models) > 1:
            # Execute in parallel
            tasks = []
            for model_name, weight in selected_models:
                task = self._generate_single_response(model_name, query, **kwargs)
                tasks.append((model_name, task))
            
            # Wait for all tasks to complete
            for model_name, task in tasks:
                try:
                    response = await asyncio.wait_for(task, timeout=self.config.timeout)
                    responses[model_name] = response
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout for model {model_name}")
                except Exception as e:
                    logger.error(f"Error generating response from {model_name}: {e}")
        else:
            # Execute sequentially
            for model_name, weight in selected_models:
                try:
                    response = await asyncio.wait_for(
                        self._generate_single_response(model_name, query, **kwargs),
                        timeout=self.config.timeout
                    )
                    responses[model_name] = response
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout for model {model_name}")
                except Exception as e:
                    logger.error(f"Error generating response from {model_name}: {e}")
        
        return responses
    
    async def _generate_single_response(self, model_name: str, query: str, **kwargs) -> str:
        """Generate a response from a single model with retry logic."""
        model = self.registry.get(model_name)
        
        for attempt in range(self.config.max_retries):
            try:
                response = await model.generate(query, **kwargs)
                return response
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    raise e
                else:
                    logger.warning(f"Attempt {attempt + 1} failed for {model_name}: {e}")
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        
        raise RuntimeError(f"All attempts failed for model {model_name}")
    
    async def _handle_fallback(
        self, 
        query: str, 
        available_models: List[str],
        include_routing_info: bool,
        **kwargs
    ) -> Union[str, Dict[str, Any]]:
        """Handle fallback when routing fails."""
        if self.config.fallback_strategy == "default" and self.config.default_model:
            if self.config.default_model in available_models:
                logger.info(f"Using default model: {self.config.default_model}")
                try:
                    model = self.registry.get(self.config.default_model)
                    response = await model.generate(query, **kwargs)
                    
                    if include_routing_info:
                        return {
                            "response": response,
                            "routing_info": {
                                "selected_models": [(self.config.default_model, 1.0)],
                                "fallback_used": True,
                                "fallback_reason": "routing_failed"
                            }
                        }
                    else:
                        return response
                except Exception as e:
                    logger.error(f"Default model failed: {e}")
        
        elif self.config.fallback_strategy == "random" and available_models:
            import random
            random_model = random.choice(available_models)
            logger.info(f"Using random model: {random_model}")
            try:
                model = self.registry.get(random_model)
                response = await model.generate(query, **kwargs)
                
                if include_routing_info:
                    return {
                        "response": response,
                        "routing_info": {
                            "selected_models": [(random_model, 1.0)],
                            "fallback_used": True,
                            "fallback_reason": "routing_failed"
                        }
                    }
                else:
                    return response
            except Exception as e:
                logger.error(f"Random model failed: {e}")
        
        elif self.config.fallback_strategy == "all" and available_models:
            # Use all available models
            logger.info("Using all available models as fallback")
            try:
                responses = {}
                for model_name in available_models[:3]:  # Limit to 3 models
                    try:
                        model = self.registry.get(model_name)
                        response = await model.generate(query, **kwargs)
                        responses[model_name] = response
                    except Exception as e:
                        logger.error(f"Model {model_name} failed: {e}")
                
                if responses:
                    # Mix all responses with equal weights
                    weights = {model: 1.0/len(responses) for model in responses.keys()}
                    final_response = await self.mixer.mix(query, responses, weights)
                    
                    if include_routing_info:
                        return {
                            "response": final_response,
                            "routing_info": {
                                "selected_models": [(model, weights[model]) for model in responses.keys()],
                                "fallback_used": True,
                                "fallback_reason": "routing_failed"
                            }
                        }
                    else:
                        return final_response
            except Exception as e:
                logger.error(f"All models fallback failed: {e}")
        
        # Final fallback
        error_msg = "No suitable models available for this query"
        if include_routing_info:
            return {
                "response": error_msg,
                "routing_info": {
                    "error": error_msg,
                    "fallback_used": True,
                    "fallback_reason": "no_models_available"
                }
            }
        else:
            return error_msg
    
    def _handle_no_available_models(self, query: str, include_routing_info: bool) -> Union[str, Dict[str, Any]]:
        """Handle case when no models are available."""
        error_msg = "No models are currently available"
        
        if include_routing_info:
            return {
                "response": error_msg,
                "routing_info": {
                    "error": error_msg,
                    "available_models": []
                }
            }
        else:
            return error_msg
    
    def _update_response_time(self, response_time: float):
        """Update average response time statistics."""
        current_avg = self.stats["average_response_time"]
        total_queries = self.stats["total_queries"]
        
        # Calculate running average
        self.stats["average_response_time"] = (
            (current_avg * (total_queries - 1) + response_time) / total_queries
        )
    
    def add_model(self, name: str, model: Model):
        """Add a model to the ensemble."""
        self.registry.models[name] = model
        logger.info(f"Added model '{name}' to ensemble")
    
    def remove_model(self, name: str):
        """Remove a model from the ensemble."""
        if name in self.registry.models:
            del self.registry.models[name]
            logger.info(f"Removed model '{name}' from ensemble")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ensemble performance statistics."""
        success_rate = (
            self.stats["successful_queries"] / self.stats["total_queries"] 
            if self.stats["total_queries"] > 0 else 0.0
        )
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "available_models": len(self.registry.get_available_models()),
            "total_models": len(self.registry.models)
        }
    
    def reset_statistics(self):
        """Reset performance statistics."""
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "model_usage": {},
            "average_response_time": 0.0
        }
        logger.info("Reset ensemble statistics")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on all models."""
        health_status = {}
        
        for model_name in self.registry.list_models():
            try:
                model = self.registry.get(model_name)
                is_available = model.is_available()
                
                # Optional: perform a simple test query
                test_response = await asyncio.wait_for(
                    model.generate("Hello"), 
                    timeout=5.0
                )
                
                health_status[model_name] = {
                    "available": is_available,
                    "responding": True,
                    "test_response_length": len(test_response)
                }
            except asyncio.TimeoutError:
                health_status[model_name] = {
                    "available": False,
                    "responding": False,
                    "error": "timeout"
                }
            except Exception as e:
                health_status[model_name] = {
                    "available": False,
                    "responding": False,
                    "error": str(e)
                }
        
        return {
            "overall_health": all(status["available"] for status in health_status.values()),
            "models": health_status,
            "timestamp": __import__("time").time()
        }
    
    def __repr__(self) -> str:
        """String representation of the ensemble."""
        return f"Ensemble(models={len(self.registry.models)}, router={type(self.router).__name__})" 