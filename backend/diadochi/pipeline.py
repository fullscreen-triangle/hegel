"""
Diadochi Pipeline Interface

Simplified interface for running complete Diadochi pipelines.
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict

from .orchestrator import (
    MetacognitiveOrchestrator, 
    PipelineConfig, 
    PipelineResult, 
    PipelineStrategy,
    PipelineFactory
)
from .core.models import BaseModel
from .core.registry import ModelRegistry


class DiadochiPipeline:
    """
    Simplified interface for running Diadochi pipelines.
    
    This class provides an easy-to-use interface for executing complete
    domain expert combination workflows.
    """
    
    def __init__(self, orchestrator: Optional[MetacognitiveOrchestrator] = None):
        """
        Initialize pipeline.
        
        Args:
            orchestrator: Pre-configured orchestrator, or None to create default
        """
        self.orchestrator = orchestrator or self._create_default_orchestrator()
    
    def _create_default_orchestrator(self) -> MetacognitiveOrchestrator:
        """Create default orchestrator with basic configuration"""
        registry = ModelRegistry()
        # Note: In production, you would register actual models here
        return MetacognitiveOrchestrator(registry)
    
    async def query(
        self,
        question: str,
        domain: Optional[str] = None,
        strategy: str = "auto",
        max_experts: int = 3,
        confidence_threshold: float = 0.7,
        include_explanation: bool = True
    ) -> Dict[str, Any]:
        """
        Process a query through the complete pipeline.
        
        Args:
            question: The question to ask
            domain: Optional domain context
            strategy: Processing strategy ("auto", "ensemble", "moe", "chain", "hybrid")
            max_experts: Maximum number of experts to use
            confidence_threshold: Minimum confidence threshold
            include_explanation: Whether to include processing explanation
            
        Returns:
            Dictionary containing response and metadata
        """
        
        # Convert string strategy to enum
        strategy_enum = PipelineStrategy.AUTO
        if strategy.lower() == "ensemble":
            strategy_enum = PipelineStrategy.ENSEMBLE
        elif strategy.lower() == "moe" or strategy.lower() == "mixture_of_experts":
            strategy_enum = PipelineStrategy.MOE
        elif strategy.lower() == "chain":
            strategy_enum = PipelineStrategy.CHAIN
        elif strategy.lower() == "hybrid":
            strategy_enum = PipelineStrategy.HYBRID
        
        # Create configuration
        config = PipelineConfig(
            strategy=strategy_enum,
            max_parallel_models=max_experts,
            confidence_threshold=confidence_threshold,
            enable_explanation=include_explanation,
            enable_metadata=True
        )
        
        # Execute pipeline
        result = await self.orchestrator.process_query(
            query=question,
            domain_context=domain,
            config=config
        )
        
        # Convert to dictionary for easy JSON serialization
        return {
            'response': result.response,
            'confidence': result.confidence,
            'strategy_used': result.strategy_used.value,
            'models_used': result.models_used,
            'execution_time': result.execution_time,
            'explanation': result.explanation,
            'metadata': result.metadata,
            'intermediate_results': result.intermediate_results
        }
    
    async def batch_query(
        self,
        questions: List[str],
        domain: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Process multiple queries in parallel.
        
        Args:
            questions: List of questions to process
            domain: Optional domain context for all questions
            **kwargs: Additional arguments passed to query()
            
        Returns:
            List of results for each question
        """
        tasks = [
            self.query(question, domain, **kwargs)
            for question in questions
        ]
        
        return await asyncio.gather(*tasks)
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline execution statistics"""
        return self.orchestrator.get_stats()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check pipeline health status"""
        return await self.orchestrator.health_check()
    
    def add_expert(self, name: str, model: BaseModel) -> None:
        """Add a new expert model to the registry"""
        self.orchestrator.registry.register_model(name, model)
    
    def list_experts(self) -> List[str]:
        """List all registered expert models"""
        return list(self.orchestrator.registry.get_all_models().keys())
    
    async def explain_strategy(self, question: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Explain what strategy would be used for a query without executing it.
        
        Args:
            question: The question to analyze
            domain: Optional domain context
            
        Returns:
            Analysis and strategy recommendation
        """
        # Analyze the query
        analysis = await self.orchestrator._analyze_query(question, domain)
        
        # Get strategy recommendation
        config = PipelineConfig()
        strategy = await self.orchestrator._select_strategy(analysis, config)
        
        return {
            'query': question,
            'domain': domain,
            'analysis': analysis,
            'recommended_strategy': strategy.value,
            'strategy_explanation': self._get_strategy_explanation(strategy, analysis)
        }
    
    def _get_strategy_explanation(self, strategy: PipelineStrategy, analysis: Dict[str, Any]) -> str:
        """Generate explanation for why a strategy was selected"""
        explanations = {
            PipelineStrategy.ENSEMBLE: "Router-based ensemble was selected for fast, parallel processing with intelligent routing to the most appropriate expert.",
            PipelineStrategy.MOE: "Mixture of Experts was selected because the query requires synthesis of multiple expert perspectives with confidence-weighted combination.",
            PipelineStrategy.CHAIN: "Sequential chain was selected for queries requiring deep, iterative analysis where each expert builds upon previous insights.",
            PipelineStrategy.HYBRID: "Hybrid approach was selected for complex queries that benefit from multiple processing strategies combined intelligently."
        }
        
        base_explanation = explanations.get(strategy, "Strategy selected based on query characteristics.")
        
        # Add analysis details
        complexity = analysis.get('complexity', 'unknown')
        requires_synthesis = analysis.get('requires_synthesis', False)
        requires_expertise = analysis.get('requires_expertise', False)
        
        details = f"\n\nQuery Analysis:\n- Complexity: {complexity}\n- Requires synthesis: {requires_synthesis}\n- Requires expertise: {requires_expertise}"
        
        return base_explanation + details


# Convenience functions for quick pipeline creation
async def quick_query(
    question: str,
    experts: Optional[List[BaseModel]] = None,
    domain: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Quick way to process a single query.
    
    Args:
        question: Question to process
        experts: Optional list of expert models
        domain: Optional domain context
        **kwargs: Additional query parameters
        
    Returns:
        Query result
    """
    if experts:
        orchestrator = PipelineFactory.create_general_orchestrator(experts)
        pipeline = DiadochiPipeline(orchestrator)
    else:
        # Use sports science example as default
        orchestrator = PipelineFactory.create_sports_science_orchestrator()
        pipeline = DiadochiPipeline(orchestrator)
    
    return await pipeline.query(question, domain, **kwargs)


async def quick_comparison(
    question: str,
    experts: Optional[List[BaseModel]] = None,
    strategies: Optional[List[str]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Compare results across different strategies.
    
    Args:
        question: Question to process
        experts: Optional list of expert models
        strategies: List of strategies to compare (default: all)
        
    Returns:
        Results for each strategy
    """
    if not strategies:
        strategies = ["ensemble", "moe", "chain", "hybrid"]
    
    if experts:
        orchestrator = PipelineFactory.create_general_orchestrator(experts)
        pipeline = DiadochiPipeline(orchestrator)
    else:
        orchestrator = PipelineFactory.create_sports_science_orchestrator()
        pipeline = DiadochiPipeline(orchestrator)
    
    results = {}
    for strategy in strategies:
        try:
            result = await pipeline.query(question, strategy=strategy)
            results[strategy] = result
        except Exception as e:
            results[strategy] = {"error": str(e)}
    
    return results


# Example usage functions
async def demo_pipeline():
    """Demonstrate pipeline capabilities"""
    print("=== Diadochi Pipeline Demo ===\n")
    
    # Create sports science pipeline
    orchestrator = PipelineFactory.create_sports_science_orchestrator()
    pipeline = DiadochiPipeline(orchestrator)
    
    # Health check
    print("1. Health Check:")
    health = await pipeline.health_check()
    print(f"   Status: {health['overall_status']}")
    print(f"   Models: {health['components'].get('registered_models', 0)}")
    print()
    
    # Example query
    question = "How can I improve my running performance through both training and nutrition?"
    
    print("2. Query Analysis:")
    explanation = await pipeline.explain_strategy(question)
    print(f"   Query: {explanation['query']}")
    print(f"   Recommended Strategy: {explanation['recommended_strategy']}")
    print(f"   Complexity: {explanation['analysis']['complexity']}")
    print()
    
    print("3. Processing Query:")
    result = await pipeline.query(question)
    print(f"   Strategy Used: {result['strategy_used']}")
    print(f"   Confidence: {result['confidence']:.2f}")
    print(f"   Execution Time: {result['execution_time']:.2f}s")
    print(f"   Models Used: {', '.join(result['models_used'])}")
    print()
    print("   Response:")
    print(f"   {result['response'][:200]}...")
    print()
    
    # Statistics
    print("4. Pipeline Statistics:")
    stats = pipeline.get_pipeline_stats()
    print(f"   Total Queries: {stats['total_queries']}")
    print(f"   Success Rate: {stats['success_rate']:.2%}")
    print(f"   Average Time: {stats['average_execution_time']:.2f}s")


if __name__ == "__main__":
    asyncio.run(demo_pipeline()) 