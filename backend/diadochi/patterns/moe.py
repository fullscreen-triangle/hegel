"""
Mixture of Experts (MoE) pattern implementation for Diadochi.

This module implements the Mixture of Experts architectural pattern,
which processes queries through multiple domain experts in parallel and
combines their outputs based on relevance or confidence.
"""

import logging
import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass

from ..core.models import Model
from ..core.mixers import Mixer, SynthesisMixer
from ..core.registry import ModelRegistry
from ..utils.confidence import ConfidenceEstimator, EmbeddingConfidence

logger = logging.getLogger(__name__)


@dataclass
class MoEConfig:
    """Configuration for Mixture of Experts behavior."""
    confidence_threshold: float = 0.1
    max_experts: int = 5
    parallel_execution: bool = True
    timeout: int = 30
    temperature: float = 1.0
    aggregation_method: str = "weighted"  # "weighted", "top_k", "threshold"
    normalize_weights: bool = True
    use_meta_expert: bool = False


class MixtureOfExperts:
    """Mixture of Experts that processes queries through multiple domain experts in parallel."""
    
    def __init__(
        self,
        confidence_estimator: ConfidenceEstimator,
        models: Union[ModelRegistry, Dict[str, Model]],
        mixer: Optional[Mixer] = None,
        meta_expert: Optional[Model] = None,
        config: Optional[MoEConfig] = None
    ):
        """
        Initialize the Mixture of Experts.
        
        Args:
            confidence_estimator: Estimator for determining expert confidence/relevance
            models: Registry or dictionary of available models
            mixer: Mixer for combining expert responses
            meta_expert: Optional meta-expert for final synthesis
            config: Configuration for MoE behavior
        """
        self.confidence_estimator = confidence_estimator
        self.mixer = mixer
        self.meta_expert = meta_expert
        self.config = config or MoEConfig()
        
        # Handle different model input types
        if isinstance(models, ModelRegistry):
            self.registry = models
        elif isinstance(models, dict):
            self.registry = ModelRegistry()
            for name, model in models.items():
                self.registry.models[name] = model
        else:
            raise ValueError("models must be a ModelRegistry or dictionary of Model instances")
        
        # Set default mixer if none provided
        if self.mixer is None:
            if self.registry.models:
                # Use first available model as synthesis model
                synthesis_model = next(iter(self.registry.models.values()))
                self.mixer = SynthesisMixer(synthesis_model)
            else:
                raise ValueError("No mixer provided and no models available for default mixer")
        
        # Performance tracking
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "expert_usage": {},
            "average_confidence": 0.0,
            "average_response_time": 0.0,
            "average_experts_used": 0.0
        }
    
    async def generate(
        self, 
        query: str,
        top_k: Optional[int] = None,
        confidence_threshold: Optional[float] = None,
        include_expert_info: bool = False,
        **kwargs
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate a response using the mixture of experts.
        
        Args:
            query: Input query
            top_k: Maximum number of experts to use (overrides config)
            confidence_threshold: Minimum confidence threshold (overrides config)
            include_expert_info: Whether to include expert information in response
            **kwargs: Additional parameters for generation
            
        Returns:
            Generated response, optionally with expert information
        """
        import time
        start_time = time.time()
        
        try:
            self.stats["total_queries"] += 1
            
            # Get available models
            available_models = self.registry.get_available_models()
            
            if not available_models:
                logger.warning("No available models for MoE")
                return self._handle_no_available_models(include_expert_info)
            
            # Estimate confidence for each expert
            confidence_scores = await self.confidence_estimator.estimate_confidence(
                query, available_models
            )
            
            # Select experts based on confidence
            selected_experts = self._select_experts(
                confidence_scores, 
                top_k or self.config.max_experts,
                confidence_threshold or self.config.confidence_threshold
            )
            
            if not selected_experts:
                logger.warning("No experts selected for query")
                return self._handle_no_experts_selected(query, include_expert_info)
            
            # Generate responses from selected experts
            expert_responses = await self._generate_expert_responses(
                query, selected_experts, **kwargs
            )
            
            # Combine responses
            if len(expert_responses) == 1:
                final_response = next(iter(expert_responses.values()))
            else:
                # Prepare weights for mixing
                weights = {expert: confidence for expert, confidence in selected_experts if expert in expert_responses}
                
                # Normalize weights if configured
                if self.config.normalize_weights and weights:
                    total_weight = sum(weights.values())
                    if total_weight > 0:
                        weights = {k: v/total_weight for k, v in weights.items()}
                
                # Mix responses
                final_response = await self.mixer.mix(query, expert_responses, weights)
            
            # Optional meta-expert refinement
            if self.config.use_meta_expert and self.meta_expert:
                final_response = await self._apply_meta_expert(
                    query, final_response, expert_responses, selected_experts
                )
            
            # Update statistics
            self.stats["successful_queries"] += 1
            response_time = time.time() - start_time
            self._update_statistics(selected_experts, confidence_scores, response_time)
            
            # Return response with optional expert info
            if include_expert_info:
                return {
                    "response": final_response,
                    "expert_info": {
                        "selected_experts": selected_experts,
                        "expert_responses": expert_responses,
                        "confidence_scores": confidence_scores,
                        "response_time": response_time,
                        "meta_expert_used": self.config.use_meta_expert and self.meta_expert is not None
                    }
                }
            else:
                return final_response
        
        except Exception as e:
            logger.error(f"Error in MoE generation: {e}")
            self.stats["failed_queries"] += 1
            
            if include_expert_info:
                return {
                    "response": f"Error: {str(e)}",
                    "expert_info": {
                        "error": str(e)
                    }
                }
            else:
                return f"Error: {str(e)}"
    
    def _select_experts(
        self,
        confidence_scores: Dict[str, float],
        max_experts: int,
        threshold: float
    ) -> List[Tuple[str, float]]:
        """Select experts based on confidence scores."""
        # Filter by threshold
        qualified_experts = [
            (expert, confidence) for expert, confidence in confidence_scores.items()
            if confidence >= threshold
        ]
        
        if not qualified_experts:
            logger.warning(f"No experts meet confidence threshold {threshold}")
            return []
        
        # Apply aggregation method
        if self.config.aggregation_method == "weighted":
            # Use softmax to get better weight distribution
            confidences = np.array([conf for _, conf in qualified_experts])
            if self.config.temperature != 1.0:
                confidences = confidences / self.config.temperature
            
            # Apply softmax
            exp_confidences = np.exp(confidences - np.max(confidences))
            softmax_confidences = exp_confidences / np.sum(exp_confidences)
            
            # Create weighted list
            weighted_experts = [
                (qualified_experts[i][0], float(softmax_confidences[i]))
                for i in range(len(qualified_experts))
            ]
            
            # Sort by weight and take top_k
            weighted_experts.sort(key=lambda x: x[1], reverse=True)
            return weighted_experts[:max_experts]
        
        elif self.config.aggregation_method == "top_k":
            # Simply take top k by confidence
            qualified_experts.sort(key=lambda x: x[1], reverse=True)
            return qualified_experts[:max_experts]
        
        elif self.config.aggregation_method == "threshold":
            # Take all above threshold, but limit to max_experts
            qualified_experts.sort(key=lambda x: x[1], reverse=True)
            return qualified_experts[:max_experts]
        
        else:
            raise ValueError(f"Unknown aggregation method: {self.config.aggregation_method}")
    
    async def _generate_expert_responses(
        self,
        query: str,
        selected_experts: List[Tuple[str, float]],
        **kwargs
    ) -> Dict[str, str]:
        """Generate responses from selected experts."""
        expert_responses = {}
        
        if self.config.parallel_execution and len(selected_experts) > 1:
            # Execute in parallel
            tasks = []
            for expert_name, confidence in selected_experts:
                task = self._generate_single_expert_response(expert_name, query, **kwargs)
                tasks.append((expert_name, task))
            
            # Wait for all tasks to complete
            for expert_name, task in tasks:
                try:
                    response = await asyncio.wait_for(task, timeout=self.config.timeout)
                    expert_responses[expert_name] = response
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout for expert {expert_name}")
                except Exception as e:
                    logger.error(f"Error generating response from expert {expert_name}: {e}")
        else:
            # Execute sequentially
            for expert_name, confidence in selected_experts:
                try:
                    response = await asyncio.wait_for(
                        self._generate_single_expert_response(expert_name, query, **kwargs),
                        timeout=self.config.timeout
                    )
                    expert_responses[expert_name] = response
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout for expert {expert_name}")
                except Exception as e:
                    logger.error(f"Error generating response from expert {expert_name}: {e}")
        
        return expert_responses
    
    async def _generate_single_expert_response(self, expert_name: str, query: str, **kwargs) -> str:
        """Generate a response from a single expert."""
        model = self.registry.get(expert_name)
        return await model.generate(query, **kwargs)
    
    async def _apply_meta_expert(
        self,
        query: str,
        mixed_response: str,
        expert_responses: Dict[str, str],
        selected_experts: List[Tuple[str, float]]
    ) -> str:
        """Apply meta-expert to refine the mixed response."""
        if not self.meta_expert:
            return mixed_response
        
        try:
            # Create meta-expert prompt
            expert_info = []
            for expert_name, confidence in selected_experts:
                if expert_name in expert_responses:
                    expert_info.append(f"Expert: {expert_name} (confidence: {confidence:.2f})")
                    expert_info.append(f"Response: {expert_responses[expert_name]}")
                    expert_info.append("")
            
            meta_prompt = f"""
As a meta-expert, review and refine the following synthesized response based on the expert inputs.

Original Query: {query}

Expert Responses:
{chr(10).join(expert_info)}

Synthesized Response: {mixed_response}

Please provide a refined response that:
1. Incorporates the best insights from all experts
2. Resolves any contradictions
3. Provides a coherent and comprehensive answer
4. Maintains appropriate confidence levels

Refined Response:
"""
            
            refined_response = await self.meta_expert.generate(meta_prompt)
            return refined_response.strip()
        
        except Exception as e:
            logger.error(f"Error applying meta-expert: {e}")
            return mixed_response
    
    def _handle_no_available_models(self, include_expert_info: bool) -> Union[str, Dict[str, Any]]:
        """Handle case when no models are available."""
        error_msg = "No expert models are currently available"
        
        if include_expert_info:
            return {
                "response": error_msg,
                "expert_info": {
                    "error": error_msg,
                    "available_experts": []
                }
            }
        else:
            return error_msg
    
    def _handle_no_experts_selected(self, query: str, include_expert_info: bool) -> Union[str, Dict[str, Any]]:
        """Handle case when no experts are selected."""
        error_msg = "No experts were selected for this query"
        
        if include_expert_info:
            return {
                "response": error_msg,
                "expert_info": {
                    "error": error_msg,
                    "query": query,
                    "threshold": self.config.confidence_threshold
                }
            }
        else:
            return error_msg
    
    def _update_statistics(
        self,
        selected_experts: List[Tuple[str, float]],
        confidence_scores: Dict[str, float],
        response_time: float
    ):
        """Update performance statistics."""
        # Update expert usage
        for expert_name, confidence in selected_experts:
            self.stats["expert_usage"][expert_name] = self.stats["expert_usage"].get(expert_name, 0) + 1
        
        # Update average confidence
        if confidence_scores:
            avg_confidence = sum(confidence_scores.values()) / len(confidence_scores)
            current_avg = self.stats["average_confidence"]
            total_queries = self.stats["total_queries"]
            self.stats["average_confidence"] = (
                (current_avg * (total_queries - 1) + avg_confidence) / total_queries
            )
        
        # Update average response time
        current_avg = self.stats["average_response_time"]
        total_queries = self.stats["total_queries"]
        self.stats["average_response_time"] = (
            (current_avg * (total_queries - 1) + response_time) / total_queries
        )
        
        # Update average experts used
        experts_used = len(selected_experts)
        current_avg = self.stats["average_experts_used"]
        self.stats["average_experts_used"] = (
            (current_avg * (total_queries - 1) + experts_used) / total_queries
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get MoE performance statistics."""
        success_rate = (
            self.stats["successful_queries"] / self.stats["total_queries"]
            if self.stats["total_queries"] > 0 else 0.0
        )
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "available_experts": len(self.registry.get_available_models()),
            "total_experts": len(self.registry.models),
            "config": {
                "confidence_threshold": self.config.confidence_threshold,
                "max_experts": self.config.max_experts,
                "aggregation_method": self.config.aggregation_method,
                "use_meta_expert": self.config.use_meta_expert
            }
        }
    
    def reset_statistics(self):
        """Reset performance statistics."""
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "expert_usage": {},
            "average_confidence": 0.0,
            "average_response_time": 0.0,
            "average_experts_used": 0.0
        }
        logger.info("Reset MoE statistics")
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze a query to understand expert selection without generating responses."""
        available_models = self.registry.get_available_models()
        
        if not available_models:
            return {"error": "No available models"}
        
        # Estimate confidence for each expert
        confidence_scores = await self.confidence_estimator.estimate_confidence(
            query, available_models
        )
        
        # Select experts
        selected_experts = self._select_experts(
            confidence_scores,
            self.config.max_experts,
            self.config.confidence_threshold
        )
        
        return {
            "query": query,
            "available_experts": available_models,
            "confidence_scores": confidence_scores,
            "selected_experts": selected_experts,
            "selection_criteria": {
                "threshold": self.config.confidence_threshold,
                "max_experts": self.config.max_experts,
                "aggregation_method": self.config.aggregation_method
            }
        }
    
    def update_config(self, **kwargs):
        """Update MoE configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated MoE config: {key} = {value}")
            else:
                logger.warning(f"Unknown config parameter: {key}")
    
    def __repr__(self) -> str:
        """String representation of the MoE."""
        return f"MixtureOfExperts(experts={len(self.registry.models)}, threshold={self.config.confidence_threshold})" 