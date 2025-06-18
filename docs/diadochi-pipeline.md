# Diadochi Complete Pipeline Documentation

## Overview

The Diadochi Complete Pipeline represents the culmination of the "Combine Harvester" architectural patterns - a fully integrated, metacognitive orchestrator that coordinates multiple domain-expert LLMs to handle complex, interdisciplinary queries with unprecedented intelligence and efficiency.

## Architecture

### Metacognitive Orchestrator

The `MetacognitiveOrchestrator` is the central brain of the Diadochi system, implementing sophisticated reasoning to:

1. **Query Analysis**: Automatically analyzes incoming queries for complexity, domain requirements, and synthesis needs
2. **Strategy Selection**: Intelligently selects the optimal processing strategy based on query characteristics
3. **Expert Coordination**: Manages multiple domain experts and their interactions
4. **Result Synthesis**: Combines and enhances results from multiple processing strategies
5. **Explanation Generation**: Provides comprehensive explanations of the reasoning process

### Pipeline Strategies

The orchestrator can execute five distinct strategies:

#### 1. AUTO (Recommended)
- **Description**: The orchestrator analyzes the query and automatically selects the optimal strategy
- **Use Case**: General-purpose processing for all query types
- **Benefits**: Optimal balance of performance and accuracy without manual configuration

#### 2. ENSEMBLE
- **Description**: Router-based ensemble that directs queries to the most appropriate single expert
- **Use Case**: Straightforward, single-domain questions requiring fast responses
- **Benefits**: Fastest execution time, minimal resource usage

#### 3. MOE (Mixture of Experts)
- **Description**: Processes queries through multiple experts in parallel and synthesizes responses
- **Use Case**: Complex queries requiring multiple perspectives and domain synthesis
- **Benefits**: Comprehensive analysis, high-quality synthesis

#### 4. CHAIN
- **Description**: Sequential processing through experts with context building
- **Use Case**: Queries requiring deep, iterative analysis where each expert builds upon previous insights
- **Benefits**: Deep expertise, contextual understanding

#### 5. HYBRID
- **Description**: Intelligent combination of multiple strategies based on confidence thresholds
- **Use Case**: Expert-level queries requiring maximum accuracy and reliability
- **Benefits**: Highest accuracy, fallback mechanisms, comprehensive validation

### Strategy Selection Logic

The orchestrator uses sophisticated heuristics to select strategies:

```python
def select_strategy(query_analysis):
    complexity = query_analysis['complexity']
    requires_synthesis = query_analysis['requires_synthesis']
    requires_expertise = query_analysis['requires_expertise']
    
    if complexity == 'simple' and not requires_synthesis:
        return 'ENSEMBLE'  # Fast, targeted response
    
    elif requires_synthesis or complexity == 'complex':
        return 'MOE'  # Multi-perspective synthesis
    
    elif requires_expertise and complexity in ['moderate', 'complex']:
        return 'CHAIN'  # Deep, iterative analysis
    
    elif complexity == 'expert':
        return 'HYBRID'  # Maximum accuracy
    
    else:
        return 'ENSEMBLE'  # Default fallback
```

## Query Analysis Framework

### Complexity Classification

Queries are automatically classified into four complexity levels:

1. **SIMPLE**: Short, straightforward questions (≤20 words)
   - Example: "What is VO2 max?"
   - Strategy: ENSEMBLE

2. **MODERATE**: Medium-length questions requiring some expertise (21-50 words)
   - Example: "How does lactate threshold training improve endurance performance?"
   - Strategy: ENSEMBLE or MOE

3. **COMPLEX**: Long questions requiring synthesis or multiple domains (>50 words)
   - Example: "How do biomechanics, physiology, and nutrition interact to determine marathon performance?"
   - Strategy: MOE or CHAIN

4. **EXPERT**: Highly technical questions requiring deep expertise
   - Example: "Provide a comprehensive analysis of the molecular mechanisms underlying exercise-induced mitochondrial biogenesis and their implications for training periodization"
   - Strategy: HYBRID

### Domain Synthesis Detection

The system detects when queries require synthesis across multiple domains by identifying keywords:

- **Synthesis Indicators**: compare, versus, and, both, multiple, different, integrate, combine, synthesis, holistic
- **Expertise Indicators**: explain, analyze, detailed, comprehensive, in-depth, research, study, investigation, technical

### Confidence Requirements

Based on query analysis, the system determines confidence requirements:

- **Low**: Simple factual queries
- **Medium**: Standard analytical queries
- **High**: Complex synthesis queries
- **Critical**: Expert-level or high-stakes queries

## Pipeline Execution Flow

### 1. Query Reception and Analysis

```python
async def process_query(query, domain_context=None, config=None):
    # Step 1: Analyze query characteristics
    analysis = await self._analyze_query(query, domain_context)
    
    # Analysis includes:
    # - Word count and complexity classification
    # - Domain synthesis requirements
    # - Expertise level needed
    # - Confidence requirements
    # - Extracted keywords and potential domains
```

### 2. Strategy Selection

```python
    # Step 2: Select optimal strategy
    strategy = await self._select_strategy(analysis, config)
    
    # Selection considers:
    # - Query complexity level
    # - Synthesis requirements
    # - Expertise needs
    # - Performance vs. accuracy trade-offs
    # - User-specified preferences
```

### 3. Pipeline Execution

```python
    # Step 3: Execute selected strategy
    result = await self._execute_pipeline(query, strategy, analysis, config)
    
    # Execution paths:
    # - ENSEMBLE: Route to best expert
    # - MOE: Parallel expert processing + synthesis
    # - CHAIN: Sequential expert processing
    # - HYBRID: Multi-strategy combination
```

### 4. Result Enhancement

```python
    # Step 4: Enhance and explain results
    enhanced_result = await self._enhance_result(result, analysis, config)
    
    # Enhancement includes:
    # - Confidence assessment
    # - Explanation generation
    # - Metadata enrichment
    # - Quality validation
```

## Strategy Implementation Details

### Ensemble Execution

```python
async def _execute_ensemble(query, analysis, config):
    # Select appropriate router
    router = self._select_router(analysis)  # keyword, embedding, classifier, llm
    
    # Create ensemble with selected models
    ensemble = RouterBasedEnsemble(
        models=self.registry.get_models()[:config.max_parallel_models],
        router=router,
        mixer=self.mixers['weighted']
    )
    
    # Execute and return result
    return await ensemble.query(query)
```

### MoE Execution

```python
async def _execute_moe(query, analysis, config):
    # Create mixture of experts
    moe = MixtureOfExperts(
        experts=self.registry.get_models()[:config.max_parallel_models],
        confidence_estimator=self.confidence_estimator,
        mixer=self.mixers['synthesis']
    )
    
    # Execute with confidence-weighted synthesis
    return await moe.query(query)
```

### Chain Execution

```python
async def _execute_chain(query, analysis, config):
    # Create sequential chain
    chain = SequentialChain(
        models=self.registry.get_models()[:config.max_parallel_models]
    )
    
    # Execute with context building
    return await chain.process(query)
```

### Hybrid Execution

```python
async def _execute_hybrid(query, analysis, config):
    # Start with ensemble for quick response
    ensemble_result = await self._execute_ensemble(query, analysis, config)
    
    # If confidence below threshold, use MoE
    if ensemble_result['confidence'] < config.confidence_threshold:
        moe_result = await self._execute_moe(query, analysis, config)
        
        # Combine results using consensus
        return await self.mixers['consensus'].mix(
            [ensemble_result, moe_result]
        )
    
    return ensemble_result
```

## Configuration Options

### PipelineConfig

```python
@dataclass
class PipelineConfig:
    strategy: PipelineStrategy = PipelineStrategy.AUTO
    max_parallel_models: int = 3
    confidence_threshold: float = 0.7
    enable_explanation: bool = True
    enable_metadata: bool = True
    timeout_seconds: float = 30.0
    fallback_strategy: Optional[PipelineStrategy] = PipelineStrategy.ENSEMBLE
```

### Configuration Examples

```python
# High-performance configuration
high_perf_config = PipelineConfig(
    strategy=PipelineStrategy.ENSEMBLE,
    max_parallel_models=1,
    confidence_threshold=0.5,
    enable_explanation=False,
    timeout_seconds=10.0
)

# High-accuracy configuration
high_accuracy_config = PipelineConfig(
    strategy=PipelineStrategy.HYBRID,
    max_parallel_models=5,
    confidence_threshold=0.9,
    enable_explanation=True,
    timeout_seconds=60.0,
    fallback_strategy=PipelineStrategy.MOE
)

# Balanced configuration (default)
balanced_config = PipelineConfig()  # Uses defaults
```

## Error Handling and Fallbacks

### Fallback Mechanisms

1. **Strategy Fallback**: If primary strategy fails, automatically try fallback strategy
2. **Model Fallback**: If specific models fail, use alternative models
3. **Timeout Handling**: Graceful degradation when operations exceed time limits
4. **Confidence Thresholds**: Automatic strategy escalation for low-confidence results

### Error Recovery

```python
try:
    result = await orchestrator.process_query(query, config=config)
except Exception as e:
    # Attempt fallback strategy
    if config.fallback_strategy:
        fallback_config = PipelineConfig(strategy=config.fallback_strategy)
        result = await orchestrator.process_query(query, config=fallback_config)
    else:
        # Return error result with diagnostic information
        result = PipelineResult(
            response=f"Processing failed: {str(e)}",
            confidence=0.0,
            strategy_used=config.strategy,
            models_used=[],
            execution_time=0.0,
            metadata={'error': str(e), 'failed': True}
        )
```

## Performance Monitoring

### Statistics Tracking

The orchestrator tracks comprehensive statistics:

```python
stats = {
    'total_queries': 0,
    'strategy_usage': {
        'auto': 0,
        'ensemble': 0,
        'moe': 0,
        'chain': 0,
        'hybrid': 0
    },
    'average_execution_time': 0.0,
    'success_rate': 0.0
}
```

### Health Monitoring

```python
async def health_check():
    return {
        'orchestrator': 'healthy',
        'model_registry': 'healthy',
        'routers': {'keyword': 'healthy', 'embedding': 'healthy'},
        'mixers': {'synthesis': 'healthy', 'weighted': 'healthy'},
        'components': {
            'registered_models': 3,
            'total_queries_processed': 150,
            'success_rate': 0.96
        },
        'overall_status': 'healthy'
    }
```

## API Integration

### REST Endpoints

The complete pipeline is exposed through comprehensive REST API:

#### Core Processing
- `POST /api/pipeline/query` - Process single query
- `POST /api/pipeline/batch` - Process multiple queries
- `POST /api/pipeline/quick-query` - Simplified query interface

#### Analysis and Comparison
- `POST /api/pipeline/analyze-strategy` - Analyze query without execution
- `POST /api/pipeline/compare-strategies` - Compare multiple strategies

#### Monitoring
- `GET /api/pipeline/health` - Health status
- `GET /api/pipeline/stats` - Performance statistics
- `GET /api/pipeline/experts` - List available experts
- `GET /api/pipeline/strategies` - List available strategies

### Example API Usage

```python
import requests

# Process a complex query
response = requests.post("http://localhost:8000/api/pipeline/query", json={
    "question": "How can biomechanics and nutrition work together to improve athletic performance?",
    "domain": "sports_science",
    "strategy": "auto",
    "max_experts": 3,
    "confidence_threshold": 0.7,
    "include_explanation": True
})

result = response.json()
print(f"Strategy: {result['data']['strategy_used']}")
print(f"Confidence: {result['data']['confidence']}")
print(f"Response: {result['data']['response']}")
```

## Usage Examples

### Basic Usage

```python
from diadochi import DiadochiPipeline, PipelineFactory

# Create pipeline
orchestrator = PipelineFactory.create_sports_science_orchestrator()
pipeline = DiadochiPipeline(orchestrator)

# Process query
result = await pipeline.query("How can I improve my running performance?")
print(result['response'])
```

### Advanced Configuration

```python
from diadochi import PipelineConfig, PipelineStrategy

# Custom configuration
config = PipelineConfig(
    strategy=PipelineStrategy.HYBRID,
    max_parallel_models=5,
    confidence_threshold=0.8,
    enable_explanation=True
)

# Process with custom config
result = await pipeline.query(
    "Provide a comprehensive analysis of training periodization",
    config=config
)
```

### Batch Processing

```python
questions = [
    "What is lactate threshold?",
    "How does strength training affect endurance?",
    "What are optimal recovery strategies?"
]

results = await pipeline.batch_query(questions)
for i, result in enumerate(results):
    print(f"Q{i+1}: {result['strategy_used']} - {result['confidence']:.2f}")
```

### Strategy Analysis

```python
# Analyze without execution
analysis = await pipeline.explain_strategy(
    "How do biomechanics and nutrition interact?"
)

print(f"Recommended: {analysis['recommended_strategy']}")
print(f"Complexity: {analysis['analysis']['complexity']}")
print(f"Explanation: {analysis['strategy_explanation']}")
```

### Strategy Comparison

```python
from diadochi import quick_comparison

# Compare all strategies
comparison = await quick_comparison(
    "How can I optimize athletic performance?",
    strategies=["ensemble", "moe", "chain", "hybrid"]
)

for strategy, result in comparison.items():
    if 'error' not in result:
        print(f"{strategy}: {result['confidence']:.2f} ({result['execution_time']:.2f}s)")
```

## Best Practices

### Strategy Selection Guidelines

1. **Use AUTO for most cases**: The orchestrator's automatic selection is optimized for best results
2. **Use ENSEMBLE for simple queries**: When you need fast responses to straightforward questions
3. **Use MOE for synthesis**: When queries require combining multiple domain perspectives
4. **Use CHAIN for deep analysis**: When queries need iterative, building analysis
5. **Use HYBRID for critical queries**: When maximum accuracy is required

### Configuration Recommendations

1. **Development**: Lower confidence thresholds, shorter timeouts, disable explanations
2. **Production**: Higher confidence thresholds, longer timeouts, enable monitoring
3. **High-throughput**: Limit parallel models, use ENSEMBLE strategy
4. **High-accuracy**: Increase parallel models, use HYBRID strategy

### Performance Optimization

1. **Model Selection**: Register only necessary domain experts
2. **Batch Processing**: Use batch queries for multiple related questions
3. **Caching**: Implement result caching for repeated queries
4. **Monitoring**: Use health checks and statistics for optimization

## Troubleshooting

### Common Issues

1. **Low Confidence Results**: Increase max_experts or use HYBRID strategy
2. **Slow Performance**: Reduce max_parallel_models or use ENSEMBLE
3. **Strategy Failures**: Ensure fallback_strategy is configured
4. **Model Errors**: Check model registry and health status

### Debugging

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check pipeline health
health = await pipeline.health_check()
print(f"Status: {health['overall_status']}")

# Get detailed statistics
stats = pipeline.get_pipeline_stats()
print(f"Success rate: {stats['success_rate']:.2%}")
```

## Future Enhancements

### Planned Features

1. **Adaptive Learning**: Pipeline learns from usage patterns to improve strategy selection
2. **Custom Strategies**: User-defined strategy combinations
3. **Model Fine-tuning**: Automatic fine-tuning based on domain-specific feedback
4. **Advanced Caching**: Intelligent result caching with similarity matching
5. **Distributed Processing**: Multi-node pipeline execution for large-scale deployments

### Research Directions

1. **Metacognitive Improvements**: Enhanced reasoning about reasoning
2. **Dynamic Expert Selection**: Real-time expert capability assessment
3. **Uncertainty Quantification**: Better confidence estimation methods
4. **Cross-domain Transfer**: Learning from one domain to improve others

## Conclusion

The Diadochi Complete Pipeline represents a significant advancement in domain-expert LLM combination, providing:

- **Intelligent Orchestration**: Automatic strategy selection and expert coordination
- **Comprehensive Coverage**: Five distinct strategies for different query types
- **Production Ready**: Full API integration, monitoring, and error handling
- **Extensible Architecture**: Easy addition of new strategies and experts
- **Research Foundation**: Platform for advancing multi-expert AI systems

The system transforms complex, interdisciplinary queries from a challenging coordination problem into a simple, one-line operation while maintaining the sophistication and accuracy of expert-level analysis. 