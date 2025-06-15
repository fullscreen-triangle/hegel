"""
Complete Diadochi Pipeline Demonstration

This example shows how to use the full Diadochi metacognitive orchestrator
to process complex queries through intelligent domain expert combination.
"""

import asyncio
import json
from typing import Dict, Any

from ..pipeline import DiadochiPipeline, quick_query, quick_comparison
from ..orchestrator import PipelineFactory, PipelineConfig, PipelineStrategy
from ..core.models import MockModel
from ..core.registry import ModelRegistry


class BiomechanicsExpert(MockModel):
    """Mock biomechanics expert for demonstration"""
    
    def __init__(self):
        super().__init__(name="biomechanics_expert")
    
    async def generate(self, prompt: str, **kwargs) -> str:
        return f"""
**Biomechanics Analysis:**

From a biomechanical perspective, your query involves:

1. **Movement Mechanics**: Analyzing the kinematic and kinetic factors
2. **Force Production**: Understanding how forces are generated and transmitted
3. **Efficiency Optimization**: Maximizing performance while minimizing injury risk

Key biomechanical principles relevant to your question:
- Force-velocity relationships
- Joint angle optimization
- Muscle activation patterns
- Energy transfer mechanisms

**Recommendation**: Focus on proper movement patterns and progressive loading.
        """.strip()


class PhysiologyExpert(MockModel):
    """Mock exercise physiology expert for demonstration"""
    
    def __init__(self):
        super().__init__(name="physiology_expert")
    
    async def generate(self, prompt: str, **kwargs) -> str:
        return f"""
**Exercise Physiology Analysis:**

From a physiological perspective, your query involves:

1. **Energy Systems**: Understanding aerobic and anaerobic pathways
2. **Adaptation Responses**: How the body adapts to training stimuli
3. **Recovery Processes**: Optimizing recovery for performance gains

Key physiological considerations:
- VO2 max and cardiovascular efficiency
- Metabolic flexibility
- Training load and recovery balance
- Hormonal responses to exercise

**Recommendation**: Implement periodized training with adequate recovery.
        """.strip()


class NutritionExpert(MockModel):
    """Mock sports nutrition expert for demonstration"""
    
    def __init__(self):
        super().__init__(name="nutrition_expert")
    
    async def generate(self, prompt: str, **kwargs) -> str:
        return f"""
**Sports Nutrition Analysis:**

From a nutritional perspective, your query involves:

1. **Fueling Strategies**: Optimizing energy availability for performance
2. **Recovery Nutrition**: Supporting adaptation and recovery processes
3. **Hydration Management**: Maintaining optimal fluid balance

Key nutritional considerations:
- Carbohydrate periodization
- Protein timing and quality
- Micronutrient adequacy
- Anti-inflammatory foods

**Recommendation**: Align nutrition timing with training demands.
        """.strip()


def create_demo_experts():
    """Create a set of demonstration experts"""
    return [
        {'name': 'biomechanics_expert', 'model': BiomechanicsExpert()},
        {'name': 'physiology_expert', 'model': PhysiologyExpert()},
        {'name': 'nutrition_expert', 'model': NutritionExpert()}
    ]


async def demo_basic_pipeline():
    """Demonstrate basic pipeline usage"""
    print("=== Basic Pipeline Demo ===\n")
    
    # Create pipeline with demo experts
    registry = ModelRegistry()
    experts = create_demo_experts()
    
    for expert in experts:
        registry.register_model(expert['name'], expert['model'])
    
    orchestrator = PipelineFactory.create_general_orchestrator([e['model'] for e in experts])
    pipeline = DiadochiPipeline(orchestrator)
    
    # Simple query
    query = "How can I improve my running performance?"
    
    print("Query:", query)
    print("\nProcessing...\n")
    
    result = await pipeline.query(query)
    
    print("=== Results ===")
    print(f"Strategy Used: {result['strategy_used']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Execution Time: {result['execution_time']:.2f}s")
    print(f"Models Used: {', '.join(result['models_used'])}")
    print(f"\nResponse:\n{result['response']}")
    
    if result.get('explanation'):
        print(f"\n=== Explanation ===\n{result['explanation']}")


async def demo_strategy_analysis():
    """Demonstrate strategy analysis capabilities"""
    print("\n=== Strategy Analysis Demo ===\n")
    
    pipeline = DiadochiPipeline()
    
    queries = [
        "What is VO2 max?",  # Simple
        "How do biomechanics and nutrition interact to affect running performance?",  # Complex
        "Provide a comprehensive analysis of training periodization including biomechanical, physiological, and nutritional considerations."  # Expert
    ]
    
    for query in queries:
        analysis = await pipeline.explain_strategy(query)
        
        print(f"Query: {query[:50]}...")
        print(f"Complexity: {analysis['analysis']['complexity']}")
        print(f"Recommended Strategy: {analysis['recommended_strategy']}")
        print(f"Requires Synthesis: {analysis['analysis']['requires_synthesis']}")
        print(f"Requires Expertise: {analysis['analysis']['requires_expertise']}")
        print()


async def demo_strategy_comparison():
    """Demonstrate strategy comparison"""
    print("=== Strategy Comparison Demo ===\n")
    
    query = "How can biomechanics and nutrition work together to improve athletic performance?"
    
    print(f"Query: {query}\n")
    print("Comparing strategies...\n")
    
    results = await quick_comparison(query)
    
    print("=== Comparison Results ===")
    for strategy, result in results.items():
        if 'error' in result:
            print(f"{strategy.upper()}: ERROR - {result['error']}")
        else:
            print(f"{strategy.upper()}:")
            print(f"  Confidence: {result.get('confidence', 0):.2f}")
            print(f"  Execution Time: {result.get('execution_time', 0):.2f}s")
            print(f"  Response Length: {len(result.get('response', ''))}")
        print()


async def demo_batch_processing():
    """Demonstrate batch query processing"""
    print("=== Batch Processing Demo ===\n")
    
    pipeline = DiadochiPipeline()
    
    questions = [
        "What is lactate threshold?",
        "How does strength training affect running economy?",
        "What are the best recovery nutrition strategies?",
        "How can I prevent running injuries?"
    ]
    
    print(f"Processing {len(questions)} questions in parallel...\n")
    
    results = await pipeline.batch_query(questions)
    
    print("=== Batch Results ===")
    for i, result in enumerate(results):
        print(f"Question {i+1}: {questions[i][:40]}...")
        print(f"  Strategy: {result['strategy_used']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print()


async def demo_health_monitoring():
    """Demonstrate health monitoring capabilities"""
    print("=== Health Monitoring Demo ===\n")
    
    pipeline = DiadochiPipeline()
    
    # Health check
    health = await pipeline.health_check()
    print("=== Health Status ===")
    print(f"Overall Status: {health['overall_status']}")
    print(f"Model Registry: {health['model_registry']}")
    print(f"Registered Models: {health['components'].get('registered_models', 0)}")
    print()
    
    # Process a few queries to generate stats
    await pipeline.query("Sample query 1")
    await pipeline.query("Sample query 2")
    
    # Get statistics
    stats = pipeline.get_pipeline_stats()
    print("=== Pipeline Statistics ===")
    print(f"Total Queries: {stats['total_queries']}")
    print(f"Success Rate: {stats['success_rate']:.2%}")
    print(f"Average Execution Time: {stats['average_execution_time']:.2f}s")
    print("Strategy Usage:")
    for strategy, count in stats['strategy_usage'].items():
        if count > 0:
            print(f"  {strategy}: {count}")


async def demo_advanced_configuration():
    """Demonstrate advanced pipeline configuration"""
    print("\n=== Advanced Configuration Demo ===\n")
    
    pipeline = DiadochiPipeline()
    
    query = "Analyze the complex interplay between biomechanics, physiology, and nutrition in endurance performance."
    
    # Test different configurations
    configs = [
        {"strategy": "auto", "max_experts": 2, "confidence_threshold": 0.5},
        {"strategy": "moe", "max_experts": 3, "confidence_threshold": 0.8},
        {"strategy": "hybrid", "max_experts": 3, "confidence_threshold": 0.7}
    ]
    
    for i, config in enumerate(configs):
        print(f"Configuration {i+1}: {config}")
        result = await pipeline.query(query, **config)
        print(f"  Result Strategy: {result['strategy_used']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Models Used: {len(result['models_used'])}")
        print()


async def demo_error_handling():
    """Demonstrate error handling and fallback mechanisms"""
    print("=== Error Handling Demo ===\n")
    
    # Create pipeline with minimal configuration to trigger fallbacks
    registry = ModelRegistry()
    # Don't register any models to simulate empty registry
    
    from ..orchestrator import MetacognitiveOrchestrator
    orchestrator = MetacognitiveOrchestrator(registry)
    pipeline = DiadochiPipeline(orchestrator)
    
    query = "Test query for error handling"
    
    print("Testing pipeline with no registered models...")
    result = await pipeline.query(query)
    
    print(f"Strategy Used: {result['strategy_used']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Error Handling: {'Success' if 'error' not in result['metadata'] else 'Fallback triggered'}")
    print(f"Response: {result['response'][:100]}...")


async def demo_real_world_scenario():
    """Demonstrate a realistic real-world scenario"""
    print("\n=== Real-World Scenario Demo ===\n")
    
    # Create comprehensive sports science pipeline
    orchestrator = PipelineFactory.create_sports_science_orchestrator()
    pipeline = DiadochiPipeline(orchestrator)
    
    # Complex real-world query
    query = """
    I'm a marathon runner who has been experiencing declining performance despite 
    increased training volume. I'm wondering if this could be related to my nutrition 
    timing, running biomechanics, or recovery strategies. Can you provide a 
    comprehensive analysis that integrates all these domains and suggest specific 
    actionable improvements?
    """
    
    print("Complex Query:", query[:100] + "...")
    print("\nAnalyzing query complexity and requirements...")
    
    # First, analyze what strategy would be used
    analysis = await pipeline.explain_strategy(query, domain="sports_science")
    print(f"\nRecommended Strategy: {analysis['recommended_strategy']}")
    print(f"Query Complexity: {analysis['analysis']['complexity']}")
    print(f"Requires Synthesis: {analysis['analysis']['requires_synthesis']}")
    print(f"Requires Expertise: {analysis['analysis']['requires_expertise']}")
    
    print("\nProcessing through pipeline...")
    
    # Process the query
    result = await pipeline.query(
        query, 
        domain="sports_science",
        strategy="auto",  # Let the orchestrator decide
        max_experts=3,
        confidence_threshold=0.7,
        include_explanation=True
    )
    
    print("\n=== Comprehensive Analysis Results ===")
    print(f"Strategy Used: {result['strategy_used']}")
    print(f"Confidence Level: {result['confidence']:.2f}")
    print(f"Processing Time: {result['execution_time']:.2f} seconds")
    print(f"Experts Consulted: {', '.join(result['models_used'])}")
    
    print(f"\n=== Integrated Response ===")
    print(result['response'])
    
    if result.get('explanation'):
        print(f"\n=== Processing Explanation ===")
        print(result['explanation'])
    
    if result.get('intermediate_results'):
        print(f"\n=== Expert Contributions ===")
        for i, intermediate in enumerate(result['intermediate_results']):
            print(f"Expert {i+1}: {intermediate.get('model', 'Unknown')}")
            # Only show first 100 chars of each expert response
            expert_response = str(intermediate).get('response', str(intermediate))
            print(f"  {expert_response[:100]}...")
            print()


async def main():
    """Run all demonstrations"""
    print("🚀 Diadochi Complete Pipeline Demonstration\n")
    print("=" * 60)
    
    demos = [
        demo_basic_pipeline,
        demo_strategy_analysis,
        demo_strategy_comparison,
        demo_batch_processing,
        demo_health_monitoring,
        demo_advanced_configuration,
        demo_error_handling,
        demo_real_world_scenario
    ]
    
    for demo in demos:
        try:
            await demo()
            print("\n" + "=" * 60)
        except Exception as e:
            print(f"Demo failed: {str(e)}")
            print("=" * 60)
    
    print("\n✅ All demonstrations completed!")


if __name__ == "__main__":
    asyncio.run(main()) 