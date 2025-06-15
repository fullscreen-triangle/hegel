"""
API routes for the Diadochi intelligent domain LLM combination framework.

This module provides REST API endpoints for interacting with the various
architectural patterns implemented in Diadochi.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import asyncio

# Import Diadochi components
try:
    from ...diadochi import (
        ModelRegistry, Ensemble, MixtureOfExperts, Chain,
        EmbeddingRouter, KeywordRouter, SynthesisMixer,
        EmbeddingConfidence, KeywordConfidence
    )
    from ...diadochi.core.models import ModelConfig
    from ...diadochi.patterns.ensemble import EnsembleConfig
    from ...diadochi.patterns.moe import MoEConfig
except ImportError as e:
    logging.error(f"Failed to import Diadochi: {e}")
    # Create dummy classes for development
    class ModelRegistry: pass
    class Ensemble: pass
    class MixtureOfExperts: pass
    class Chain: pass
    class EmbeddingRouter: pass
    class KeywordRouter: pass
    class SynthesisMixer: pass
    class EmbeddingConfidence: pass
    class KeywordConfidence: pass
    class ModelConfig: pass
    class EnsembleConfig: pass
    class MoEConfig: pass

logger = logging.getLogger(__name__)

router = APIRouter()

# Global instances (in production, these would be managed more robustly)
_registry = None
_ensemble = None
_moe = None
_chains = {}


# Pydantic models for API requests/responses
class ModelRegistrationRequest(BaseModel):
    name: str = Field(..., description="Unique identifier for the model")
    engine: str = Field(..., description="Model engine (ollama, openai, anthropic, huggingface)")
    model_name: str = Field(..., description="Name of the model")
    api_key: Optional[str] = Field(None, description="API key for the model service")
    base_url: Optional[str] = Field(None, description="Base URL for the model service")
    temperature: float = Field(0.7, description="Temperature for generation")
    max_tokens: int = Field(1000, description="Maximum tokens to generate")
    timeout: int = Field(30, description="Request timeout in seconds")


class DomainDefinition(BaseModel):
    name: str = Field(..., description="Domain name")
    description: str = Field(..., description="Domain description")
    keywords: Optional[List[str]] = Field(None, description="Keywords associated with the domain")
    examples: Optional[List[str]] = Field(None, description="Example queries for the domain")


class EnsembleCreationRequest(BaseModel):
    router_type: str = Field("embedding", description="Type of router (embedding, keyword, llm)")
    router_config: Dict[str, Any] = Field(default_factory=dict, description="Router configuration")
    mixer_type: str = Field("synthesis", description="Type of mixer (default, concatenation, synthesis)")
    mixer_config: Dict[str, Any] = Field(default_factory=dict, description="Mixer configuration")
    ensemble_config: Dict[str, Any] = Field(default_factory=dict, description="Ensemble configuration")
    domains: List[DomainDefinition] = Field(..., description="Domain definitions")


class MoECreationRequest(BaseModel):
    confidence_estimator_type: str = Field("embedding", description="Type of confidence estimator")
    confidence_config: Dict[str, Any] = Field(default_factory=dict, description="Confidence estimator configuration")
    mixer_type: str = Field("synthesis", description="Type of mixer")
    mixer_config: Dict[str, Any] = Field(default_factory=dict, description="Mixer configuration")
    moe_config: Dict[str, Any] = Field(default_factory=dict, description="MoE configuration")
    domains: List[DomainDefinition] = Field(..., description="Domain definitions")


class ChainCreationRequest(BaseModel):
    model_sequence: List[str] = Field(..., description="Ordered list of model names to chain")
    chain_type: str = Field("basic", description="Type of chain (basic, summarizing, conditional)")
    prompt_templates: Optional[Dict[str, str]] = Field(None, description="Custom prompt templates")
    chain_config: Dict[str, Any] = Field(default_factory=dict, description="Chain configuration")


class QueryRequest(BaseModel):
    query: str = Field(..., description="Input query")
    include_metadata: bool = Field(False, description="Include routing/expert information in response")
    generation_params: Dict[str, Any] = Field(default_factory=dict, description="Additional generation parameters")


class QueryResponse(BaseModel):
    response: str = Field(..., description="Generated response")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata about the generation process")


class AnalysisRequest(BaseModel):
    query: str = Field(..., description="Query to analyze")


class AnalysisResponse(BaseModel):
    analysis: Dict[str, Any] = Field(..., description="Analysis results")


def get_registry() -> ModelRegistry:
    """Get or create the global model registry."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


@router.post("/models/register", summary="Register a new model")
async def register_model(request: ModelRegistrationRequest):
    """Register a new model in the Diadochi registry."""
    try:
        registry = get_registry()
        
        registry.add_model(
            name=request.name,
            engine=request.engine,
            model_name=request.model_name,
            api_key=request.api_key,
            base_url=request.base_url,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            timeout=request.timeout
        )
        
        return {
            "status": "success",
            "message": f"Model '{request.name}' registered successfully",
            "model_info": {
                "name": request.name,
                "engine": request.engine,
                "model_name": request.model_name
            }
        }
    
    except Exception as e:
        logger.error(f"Error registering model: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/models", summary="List registered models")
async def list_models():
    """List all registered models."""
    try:
        registry = get_registry()
        models_info = registry.get_registry_info()
        
        return {
            "status": "success",
            "models": models_info
        }
    
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/models/{model_name}", summary="Remove a model")
async def remove_model(model_name: str):
    """Remove a model from the registry."""
    try:
        registry = get_registry()
        registry.remove_model(model_name)
        
        return {
            "status": "success",
            "message": f"Model '{model_name}' removed successfully"
        }
    
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
    except Exception as e:
        logger.error(f"Error removing model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ensemble/create", summary="Create a router-based ensemble")
async def create_ensemble(request: EnsembleCreationRequest):
    """Create a router-based ensemble."""
    try:
        registry = get_registry()
        
        # Create router
        if request.router_type == "embedding":
            router = EmbeddingRouter(**request.router_config)
        elif request.router_type == "keyword":
            router = KeywordRouter(**request.router_config)
        else:
            raise ValueError(f"Unsupported router type: {request.router_type}")
        
        # Add domain definitions to router
        for domain in request.domains:
            router.add_domain(
                domain.name,
                domain.description,
                domain.keywords,
                domain.examples
            )
        
        # Create mixer
        if request.mixer_type == "synthesis":
            # Use first available model for synthesis
            models = registry.get_available_models()
            if not models:
                raise ValueError("No models available for synthesis mixer")
            synthesis_model = registry.get(models[0])
            mixer = SynthesisMixer(synthesis_model, **request.mixer_config)
        else:
            raise ValueError(f"Unsupported mixer type: {request.mixer_type}")
        
        # Create ensemble config
        ensemble_config = EnsembleConfig(**request.ensemble_config)
        
        # Create ensemble
        global _ensemble
        _ensemble = Ensemble(
            router=router,
            models=registry,
            mixer=mixer,
            config=ensemble_config
        )
        
        return {
            "status": "success",
            "message": "Ensemble created successfully",
            "ensemble_info": {
                "router_type": request.router_type,
                "mixer_type": request.mixer_type,
                "domains": [d.name for d in request.domains],
                "available_models": len(registry.get_available_models())
            }
        }
    
    except Exception as e:
        logger.error(f"Error creating ensemble: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/moe/create", summary="Create a mixture of experts")
async def create_moe(request: MoECreationRequest):
    """Create a mixture of experts."""
    try:
        registry = get_registry()
        
        # Create confidence estimator
        if request.confidence_estimator_type == "embedding":
            confidence_estimator = EmbeddingConfidence(**request.confidence_config)
        elif request.confidence_estimator_type == "keyword":
            confidence_estimator = KeywordConfidence(**request.confidence_config)
        else:
            raise ValueError(f"Unsupported confidence estimator type: {request.confidence_estimator_type}")
        
        # Add domain definitions
        for domain in request.domains:
            confidence_estimator.add_domain(
                domain.name,
                domain.description,
                domain.keywords,
                domain.examples
            )
        
        # Create mixer
        if request.mixer_type == "synthesis":
            models = registry.get_available_models()
            if not models:
                raise ValueError("No models available for synthesis mixer")
            synthesis_model = registry.get(models[0])
            mixer = SynthesisMixer(synthesis_model, **request.mixer_config)
        else:
            raise ValueError(f"Unsupported mixer type: {request.mixer_type}")
        
        # Create MoE config
        moe_config = MoEConfig(**request.moe_config)
        
        # Create MoE
        global _moe
        _moe = MixtureOfExperts(
            confidence_estimator=confidence_estimator,
            models=registry,
            mixer=mixer,
            config=moe_config
        )
        
        return {
            "status": "success",
            "message": "Mixture of Experts created successfully",
            "moe_info": {
                "confidence_estimator_type": request.confidence_estimator_type,
                "mixer_type": request.mixer_type,
                "domains": [d.name for d in request.domains],
                "available_models": len(registry.get_available_models()),
                "config": {
                    "confidence_threshold": moe_config.confidence_threshold,
                    "max_experts": moe_config.max_experts
                }
            }
        }
    
    except Exception as e:
        logger.error(f"Error creating MoE: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/chain/create", summary="Create a sequential chain")
async def create_chain(request: ChainCreationRequest):
    """Create a sequential chain."""
    try:
        registry = get_registry()
        
        # Get models for the chain
        models = []
        for model_name in request.model_sequence:
            if model_name not in registry:
                raise ValueError(f"Model '{model_name}' not found in registry")
            models.append(registry.get(model_name))
        
        # Create chain
        if request.chain_type == "basic":
            chain = Chain(
                models=models,
                prompt_templates=request.prompt_templates,
                **request.chain_config
            )
        else:
            raise ValueError(f"Unsupported chain type: {request.chain_type}")
        
        # Store chain with a unique ID
        chain_id = f"chain_{len(_chains)}"
        _chains[chain_id] = chain
        
        return {
            "status": "success",
            "message": "Chain created successfully",
            "chain_info": {
                "chain_id": chain_id,
                "chain_type": request.chain_type,
                "model_sequence": request.model_sequence,
                "num_models": len(models)
            }
        }
    
    except Exception as e:
        logger.error(f"Error creating chain: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ensemble/query", response_model=QueryResponse, summary="Query the ensemble")
async def query_ensemble(request: QueryRequest):
    """Generate a response using the router-based ensemble."""
    try:
        if _ensemble is None:
            raise HTTPException(status_code=400, detail="No ensemble has been created")
        
        response = await _ensemble.generate(
            request.query,
            include_routing_info=request.include_metadata,
            **request.generation_params
        )
        
        if isinstance(response, dict):
            return QueryResponse(
                response=response["response"],
                metadata=response.get("routing_info")
            )
        else:
            return QueryResponse(response=response)
    
    except Exception as e:
        logger.error(f"Error querying ensemble: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/moe/query", response_model=QueryResponse, summary="Query the mixture of experts")
async def query_moe(request: QueryRequest):
    """Generate a response using the mixture of experts."""
    try:
        if _moe is None:
            raise HTTPException(status_code=400, detail="No MoE has been created")
        
        response = await _moe.generate(
            request.query,
            include_expert_info=request.include_metadata,
            **request.generation_params
        )
        
        if isinstance(response, dict):
            return QueryResponse(
                response=response["response"],
                metadata=response.get("expert_info")
            )
        else:
            return QueryResponse(response=response)
    
    except Exception as e:
        logger.error(f"Error querying MoE: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chain/{chain_id}/query", response_model=QueryResponse, summary="Query a sequential chain")
async def query_chain(chain_id: str, request: QueryRequest):
    """Generate a response using a sequential chain."""
    try:
        if chain_id not in _chains:
            raise HTTPException(status_code=404, detail=f"Chain '{chain_id}' not found")
        
        chain = _chains[chain_id]
        response = await chain.generate(request.query, **request.generation_params)
        
        return QueryResponse(
            response=response,
            metadata={"chain_id": chain_id} if request.include_metadata else None
        )
    
    except Exception as e:
        logger.error(f"Error querying chain: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/moe/analyze", response_model=AnalysisResponse, summary="Analyze query for MoE expert selection")
async def analyze_moe_query(request: AnalysisRequest):
    """Analyze a query to understand expert selection for MoE."""
    try:
        if _moe is None:
            raise HTTPException(status_code=400, detail="No MoE has been created")
        
        analysis = await _moe.analyze_query(request.query)
        
        return AnalysisResponse(analysis=analysis)
    
    except Exception as e:
        logger.error(f"Error analyzing MoE query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ensemble/stats", summary="Get ensemble statistics")
async def get_ensemble_stats():
    """Get performance statistics for the ensemble."""
    try:
        if _ensemble is None:
            raise HTTPException(status_code=400, detail="No ensemble has been created")
        
        stats = _ensemble.get_statistics()
        
        return {
            "status": "success",
            "statistics": stats
        }
    
    except Exception as e:
        logger.error(f"Error getting ensemble stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/moe/stats", summary="Get MoE statistics")
async def get_moe_stats():
    """Get performance statistics for the mixture of experts."""
    try:
        if _moe is None:
            raise HTTPException(status_code=400, detail="No MoE has been created")
        
        stats = _moe.get_statistics()
        
        return {
            "status": "success",
            "statistics": stats
        }
    
    except Exception as e:
        logger.error(f"Error getting MoE stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Health check for Diadochi system")
async def health_check():
    """Perform a comprehensive health check of the Diadochi system."""
    try:
        health_info = {
            "status": "healthy",
            "components": {},
            "registry": None,
            "ensemble": None,
            "moe": None,
            "chains": len(_chains)
        }
        
        # Check registry
        registry = get_registry()
        health_info["registry"] = {
            "total_models": len(registry.models),
            "available_models": len(registry.get_available_models()),
            "model_availability": registry.check_availability()
        }
        
        # Check ensemble
        if _ensemble:
            ensemble_health = await _ensemble.health_check()
            health_info["ensemble"] = ensemble_health
        
        # Check MoE (basic check)
        if _moe:
            health_info["moe"] = {
                "created": True,
                "expert_count": len(_moe.registry.models) if hasattr(_moe, 'registry') else 0
            }
        
        return health_info
    
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.post("/reset", summary="Reset all Diadochi components")
async def reset_system():
    """Reset all Diadochi components and statistics."""
    try:
        global _registry, _ensemble, _moe, _chains
        
        # Reset statistics if components exist
        if _ensemble:
            _ensemble.reset_statistics()
        if _moe:
            _moe.reset_statistics()
        
        # Clear global instances
        _registry = None
        _ensemble = None
        _moe = None
        _chains.clear()
        
        return {
            "status": "success",
            "message": "Diadochi system reset successfully"
        }
    
    except Exception as e:
        logger.error(f"Error resetting system: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 