"""
Diadochi - Intelligent Domain LLM Combination Framework

A comprehensive framework for combining domain-expert Large Language Models (LLMs)
to create superior, integrated AI systems capable of handling interdisciplinary queries.

Based on the "Combine Harvester" architectural patterns:
- Router-Based Ensembles
- Sequential Chaining  
- Mixture of Experts
- Specialized System Prompts
- Knowledge Distillation
- Multi-Domain RAG

Usage:
    from diadochi import ModelRegistry, Ensemble, Chain, MixtureOfExperts
    
    # Create a registry
    registry = ModelRegistry()
    registry.add_model("biomechanics", engine="ollama", model_name="biomech-expert")
    registry.add_model("nutrition", engine="openai", model_name="gpt-4")
    
    # Create an ensemble
    ensemble = Ensemble(router=EmbeddingRouter(), models=registry)
    response = ensemble.generate("How does stride frequency affect performance?")
"""

from .core.registry import ModelRegistry
from .core.models import Model, OllamaModel, OpenAIModel, AnthropicModel, HuggingFaceModel
from .core.routers import Router, KeywordRouter, EmbeddingRouter, ClassifierRouter, LLMRouter
from .core.chains import Chain, SummarizingChain
from .core.mixers import Mixer, DefaultMixer, ConcatenationMixer, SynthesisMixer, WeightedMixer
from .patterns.ensemble import Ensemble
from .patterns.moe import MixtureOfExperts
from .patterns.system_prompts import SystemPromptExpert
from .patterns.distillation import Distiller
from .patterns.rag import MultiDomainRAG
from .utils.confidence import ConfidenceEstimator, EmbeddingConfidence, KeywordConfidence
from .utils.evaluation import DomainEvaluator, CrossDomainEvaluator
from .utils.data_generation import SyntheticDataGenerator, AdversarialDataGenerator

# Pipeline and orchestration
from .orchestrator import (
    MetacognitiveOrchestrator, 
    PipelineConfig, 
    PipelineResult, 
    PipelineStrategy,
    PipelineFactory,
    QueryComplexity
)
from .pipeline import DiadochiPipeline, quick_query, quick_comparison

__version__ = "0.1.0"
__author__ = "Hegel Team"
__description__ = "Intelligent Domain LLM Combination Framework"

__all__ = [
    # Core components
    "ModelRegistry",
    "Model", "OllamaModel", "OpenAIModel", "AnthropicModel", "HuggingFaceModel",
    "Router", "KeywordRouter", "EmbeddingRouter", "ClassifierRouter", "LLMRouter", 
    "Chain", "SummarizingChain",
    "Mixer", "DefaultMixer", "ConcatenationMixer", "SynthesisMixer", "WeightedMixer",
    
    # Architectural patterns
    "Ensemble",
    "MixtureOfExperts", 
    "SystemPromptExpert",
    "Distiller",
    "MultiDomainRAG",
    
    # Pipeline and orchestration
    "MetacognitiveOrchestrator", "PipelineConfig", "PipelineResult", "PipelineStrategy",
    "PipelineFactory", "QueryComplexity", "DiadochiPipeline", "quick_query", "quick_comparison",
    
    # Utilities
    "ConfidenceEstimator", "EmbeddingConfidence", "KeywordConfidence",
    "DomainEvaluator", "CrossDomainEvaluator",
    "SyntheticDataGenerator", "AdversarialDataGenerator",
] 