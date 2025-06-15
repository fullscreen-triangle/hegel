# Diadochi: Intelligent Domain LLM Combination Framework

<p align="center">
  <em>When you mix coffee, red bull and jetfuel</em>
</p>

Diadochi is a comprehensive framework for combining domain-expert Large Language Models (LLMs) to create superior, integrated AI systems capable of handling interdisciplinary queries. Named after Alexander the Great's successors who divided his empire among specialized domains, this framework intelligently combines the expertise of multiple domain-specific models.

## 🚀 Features

- **Multiple Architectural Patterns**: Implements five proven patterns for combining domain expertise
- **Flexible Model Support**: Works with Ollama, OpenAI, Anthropic, and HuggingFace models
- **Intelligent Routing**: Smart query routing based on embedding similarity, keywords, or LLM analysis
- **Advanced Mixing**: Sophisticated response synthesis and combination strategies
- **Performance Monitoring**: Built-in statistics and health monitoring
- **Async Support**: Fully asynchronous for high-performance applications

## 🏗️ Architecture

Diadochi implements five core architectural patterns from the "Combine Harvester" framework:

### 1. Router-Based Ensembles
Direct queries to the most appropriate domain expert based on query analysis.

```python
from diadochi import ModelRegistry, Ensemble, EmbeddingRouter

# Create registry and register models
registry = ModelRegistry()
registry.add_model("biomechanics", engine="ollama", model_name="biomech-expert")
registry.add_model("nutrition", engine="openai", model_name="gpt-4")

# Create router and add domain descriptions
router = EmbeddingRouter(threshold=0.6)
router.add_domain("biomechanics", "Expert in movement mechanics and force analysis")
router.add_domain("nutrition", "Expert in dietary strategies for athletic performance")

# Create ensemble
ensemble = Ensemble(router=router, models=registry)
response = await ensemble.generate("How does stride frequency affect performance?")
```

### 2. Sequential Chaining
Pass queries through multiple experts sequentially, building on previous insights.

```python
from diadochi import Chain

# Create chain with custom prompt templates
chain = Chain(
    models=[biomechanics_model, physiology_model, nutrition_model],
    prompt_templates={
        "physiology_model": "Building on this biomechanical analysis: {responses[0]}\nQuery: {query}"
    }
)

response = await chain.generate("How can sprint athletes optimize recovery?")
```

### 3. Mixture of Experts
Process queries through multiple experts in parallel and intelligently combine responses.

```python
from diadochi import MixtureOfExperts, EmbeddingConfidence

# Create confidence estimator
confidence = EmbeddingConfidence(temperature=0.8)
confidence.add_domain("biomechanics", "Movement mechanics expert")

# Create MoE
moe = MixtureOfExperts(
    confidence_estimator=confidence,
    models=registry,
    config=MoEConfig(confidence_threshold=0.2, max_experts=3)
)

response = await moe.generate("What factors determine jumping performance?")
```

### 4. Specialized System Prompts
Use carefully crafted prompts to create multi-domain expertise in a single model.

```python
from diadochi import SystemPromptExpert

expert = SystemPromptExpert(
    model=base_model,
    domains={
        "biomechanics": "You are an expert in movement mechanics...",
        "physiology": "You are an expert in exercise physiology..."
    }
)
```

### 5. Knowledge Distillation
Train integrated models that combine expertise from multiple domain experts.

```python
from diadochi import Distiller

distiller = Distiller(
    student_model=student,
    teacher_models={"bio": bio_model, "phys": phys_model},
    data_generators=[synthetic_generator, adversarial_generator]
)

integrated_model = await distiller.distill()
```

## 🔧 Components

### Core Components

- **ModelRegistry**: Centralized management of domain expert models
- **Routers**: Direct queries to appropriate experts (Embedding, Keyword, Classifier, LLM)
- **Chains**: Sequential processing through multiple models
- **Mixers**: Combine responses from multiple experts (Synthesis, Weighted, Consensus)

### Pipeline Orchestration (NEW)

- **MetacognitiveOrchestrator**: Central coordinator implementing metacognitive reasoning
  - Analyzes query complexity and requirements
  - Selects optimal processing strategies automatically
  - Coordinates multiple experts intelligently
  - Provides comprehensive explanations and metadata

- **DiadochiPipeline**: Simplified interface for complete workflow execution
  - One-line query processing with automatic strategy selection
  - Batch processing capabilities
  - Health monitoring and statistics
  - Strategy comparison and analysis

- **PipelineFactory**: Pre-configured pipeline creation
  - Domain-specific orchestrators (e.g., sports science)
  - General-purpose configurations
  - Easy setup for common use cases

### Utilities

- **Confidence Estimators**: Determine expert relevance (Embedding, Keyword, TF-IDF, LLM, Hybrid)
- **Data Generators**: Create training data (Synthetic, Adversarial)
- **Evaluators**: Assess multi-domain performance (Domain, Cross-Domain)

## 📚 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Complete Pipeline Usage (Recommended)

The easiest way to use Diadochi is through the complete pipeline interface:

```python
import asyncio
from diadochi import DiadochiPipeline, PipelineFactory

async def main():
    # Create a sports science pipeline (pre-configured)
    orchestrator = PipelineFactory.create_sports_science_orchestrator()
    pipeline = DiadochiPipeline(orchestrator)
    
    # Simple query processing
    result = await pipeline.query(
        "How can I improve my running performance through training and nutrition?",
        strategy="auto",  # Let the system decide the best approach
        max_experts=3,
        confidence_threshold=0.7,
        include_explanation=True
    )
    
    print(f"Strategy Used: {result['strategy_used']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Response: {result['response']}")
    print(f"Explanation: {result['explanation']}")

asyncio.run(main())
```

### Quick Query Interface

For even simpler usage:

```python
from diadochi import quick_query, quick_comparison

# Single query
result = await quick_query(
    "What factors determine athletic performance?",
    domain="sports_science"
)

# Compare different strategies
comparison = await quick_comparison(
    "How do biomechanics and nutrition interact?",
    strategies=["ensemble", "moe", "chain"]
)
```

### Advanced Pipeline Configuration

```python
from diadochi import DiadochiPipeline, PipelineConfig, PipelineStrategy

# Create custom pipeline
pipeline = DiadochiPipeline()

# Advanced configuration
config = PipelineConfig(
    strategy=PipelineStrategy.HYBRID,
    max_parallel_models=5,
    confidence_threshold=0.8,
    enable_explanation=True,
    timeout_seconds=60.0,
    fallback_strategy=PipelineStrategy.ENSEMBLE
)

result = await pipeline.query("Complex query", config=config)
```

### Component-Level Usage

For fine-grained control, you can use individual components:

```python
import asyncio
from diadochi import ModelRegistry, Ensemble, EmbeddingRouter

async def main():
    # Set up models
    registry = ModelRegistry()
    registry.add_model("expert1", engine="ollama", model_name="domain-expert-1")
    registry.add_model("expert2", engine="openai", model_name="gpt-4")
    
    # Create router
    router = EmbeddingRouter()
    router.add_domain("expert1", "Domain 1 expertise description")
    router.add_domain("expert2", "Domain 2 expertise description")
    
    # Create ensemble
    ensemble = Ensemble(router=router, models=registry)
    
    # Generate response
    response = await ensemble.generate("Your interdisciplinary query here")
    print(response)

asyncio.run(main())
```

## 🧠 Pipeline Strategies

The Diadochi orchestrator automatically selects the optimal strategy based on query analysis, or you can specify manually:

### Available Strategies

1. **AUTO** (Recommended): The orchestrator analyzes the query and selects the optimal strategy
   - Considers query complexity, domain requirements, and synthesis needs
   - Provides the best balance of performance and accuracy

2. **ENSEMBLE**: Router-based ensemble for fast, targeted responses
   - Routes queries to the most appropriate single expert
   - Optimal for straightforward, single-domain questions
   - Fastest execution time

3. **MOE** (Mixture of Experts): Parallel processing with intelligent synthesis
   - Processes queries through multiple experts simultaneously
   - Synthesizes responses using advanced mixing algorithms
   - Best for complex queries requiring multiple perspectives

4. **CHAIN**: Sequential processing with context building
   - Passes queries through experts sequentially
   - Each expert builds upon previous insights
   - Ideal for deep, iterative analysis

5. **HYBRID**: Intelligent combination of multiple strategies
   - Starts with ensemble for quick response
   - Falls back to MoE if confidence is below threshold
   - Optimal for expert-level queries requiring high accuracy

### Strategy Selection Logic

```python
# The orchestrator considers:
# - Query length and complexity
# - Presence of domain synthesis keywords
# - Expertise requirements
# - Performance vs. accuracy trade-offs

# Examples of automatic selection:
"What is VO2 max?" → ENSEMBLE (simple, single domain)
"How do nutrition and training interact?" → MOE (multi-domain synthesis)
"Provide a comprehensive analysis..." → CHAIN (deep expertise required)
"Critical medical diagnosis..." → HYBRID (high accuracy required)
```

### Query Analysis and Explanation

```python
# Analyze query without processing
analysis = await pipeline.explain_strategy(
    "How can biomechanics and nutrition work together to improve performance?"
)

print(f"Recommended Strategy: {analysis['recommended_strategy']}")
print(f"Query Complexity: {analysis['analysis']['complexity']}")
print(f"Requires Synthesis: {analysis['analysis']['requires_synthesis']}")
print(f"Strategy Explanation: {analysis['strategy_explanation']}")
```

## 📊 Monitoring and Analytics

### Health Monitoring

```python
# Check pipeline health
health = await pipeline.health_check()
print(f"Overall Status: {health['overall_status']}")
print(f"Registered Models: {health['components']['registered_models']}")
print(f"Success Rate: {health['components']['success_rate']:.2%}")
```

### Performance Statistics

```python
# Get detailed statistics
stats = pipeline.get_pipeline_stats()
print(f"Total Queries: {stats['total_queries']}")
print(f"Average Execution Time: {stats['average_execution_time']:.2f}s")
print(f"Strategy Usage: {stats['strategy_usage']}")
```

### Batch Processing and Analysis

```python
# Process multiple queries in parallel
questions = [
    "What is lactate threshold?",
    "How does strength training affect endurance?",
    "What are optimal recovery strategies?",
    "How can I prevent overtraining?"
]

results = await pipeline.batch_query(questions, domain="sports_science")

# Analyze batch results
print(f"Batch Summary:")
print(f"  Average Confidence: {results['batch_summary']['average_confidence']:.2f}")
print(f"  Strategies Used: {results['batch_summary']['strategies_used']}")
print(f"  Total Time: {results['batch_summary']['total_execution_time']:.2f}s")
```

## 🎯 Use Cases

### Sports Science
Combine biomechanics, exercise physiology, and nutrition experts:

```python
# Complete pipeline approach (recommended)
from diadochi import PipelineFactory, DiadochiPipeline

orchestrator = PipelineFactory.create_sports_science_orchestrator()
pipeline = DiadochiPipeline(orchestrator)

result = await pipeline.query(
    "I'm a marathon runner experiencing performance decline despite increased training. "
    "Could this be related to nutrition timing, biomechanics, or recovery strategies? "
    "Provide an integrated analysis across all domains."
)

print(f"Strategy: {result['strategy_used']}")  # Likely: 'moe' or 'hybrid'
print(f"Confidence: {result['confidence']:.2f}")
print(f"Integrated Response: {result['response']}")

# Component-level approach
# See examples/sports_science_example.py for implementation
demo = SportsScienceDemo()
await demo.run_demonstration_queries()
```

### Medical Diagnosis
Integrate radiology, pathology, and clinical experts:

```python
medical_moe = MixtureOfExperts(
    confidence_estimator=HybridConfidence([
        EmbeddingConfidence(),
        KeywordConfidence()
    ]),
    models=medical_experts_registry
)
```

### Research Analysis
Chain literature review, methodology, and statistical analysis experts:

```python
research_chain = Chain([
    literature_expert,
    methodology_expert,
    statistics_expert,
    synthesis_expert
])
```

## 🌐 REST API

Diadochi provides a comprehensive REST API for integration with web applications:

### Pipeline Endpoints

#### Process Query
```http
POST /api/pipeline/query
Content-Type: application/json

{
    "question": "How can I improve my running performance?",
    "domain": "sports_science",
    "strategy": "auto",
    "max_experts": 3,
    "confidence_threshold": 0.7,
    "include_explanation": true
}
```

#### Batch Processing
```http
POST /api/pipeline/batch
Content-Type: application/json

{
    "questions": [
        "What is lactate threshold?",
        "How does strength training affect endurance?"
    ],
    "domain": "sports_science",
    "strategy": "auto"
}
```

#### Strategy Analysis
```http
POST /api/pipeline/analyze-strategy
Content-Type: application/json

{
    "question": "Complex interdisciplinary query",
    "domain": "sports_science"
}
```

#### Strategy Comparison
```http
POST /api/pipeline/compare-strategies
Content-Type: application/json

{
    "question": "How do biomechanics and nutrition interact?",
    "strategies": ["ensemble", "moe", "chain", "hybrid"]
}
```

### Monitoring Endpoints

#### Health Check
```http
GET /api/pipeline/health
```

#### Statistics
```http
GET /api/pipeline/stats
```

#### List Experts
```http
GET /api/pipeline/experts
```

#### Available Strategies
```http
GET /api/pipeline/strategies
```

### Example API Usage

```python
import requests

# Process a query
response = requests.post("http://localhost:8000/api/pipeline/query", json={
    "question": "How can biomechanics and nutrition work together?",
    "strategy": "auto",
    "include_explanation": True
})

result = response.json()
print(f"Strategy Used: {result['data']['strategy_used']}")
print(f"Response: {result['data']['response']}")
```

## 🎮 Examples and Demos

### Complete Pipeline Demo

Run the comprehensive pipeline demonstration:

```bash
cd backend/diadochi/examples
python complete_pipeline_demo.py
```

This demo showcases:
- Basic pipeline usage
- Strategy analysis and selection
- Strategy comparison across different approaches
- Batch processing capabilities
- Health monitoring and statistics
- Advanced configuration options
- Error handling and fallback mechanisms
- Real-world scenario processing

### Sports Science Example

```bash
cd backend/diadochi/examples
python sports_science_example.py
```

### Pipeline in Jupyter Notebooks

```python
# Install in notebook
!pip install -r requirements.txt

# Run demonstration
from diadochi.examples.complete_pipeline_demo import main
await main()
```

### Quick Testing

```python
from diadochi import quick_query

# Simple test
result = await quick_query("What factors affect athletic performance?")
print(result['response'])
```

## 📊 Evaluation Metrics

Diadochi provides comprehensive evaluation metrics:

- **Domain-Specific Accuracy (DSA)**: Performance within individual domains
- **Cross-Domain Accuracy (CDA)**: Performance on interdisciplinary queries
- **Domain Expertise Retention (DER)**: Preservation of expert capabilities
- **Integration Coherence (IC)**: Logical consistency across domains

```python
# Get system statistics
stats = ensemble.get_statistics()
print(f"Success Rate: {stats['success_rate']:.2%}")
print(f"Average Response Time: {stats['average_response_time']:.2f}s")
print(f"Model Usage: {stats['model_usage']}")
```

## 🔍 API Integration

Diadochi provides a REST API for easy integration:

```bash
# Register a model
curl -X POST "http://localhost:8000/api/diadochi/models/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "biomechanics_expert",
    "engine": "ollama",
    "model_name": "biomech-expert"
  }'

# Create an ensemble
curl -X POST "http://localhost:8000/api/diadochi/ensemble/create" \
  -H "Content-Type: application/json" \
  -d '{
    "router_type": "embedding",
    "domains": [
      {
        "name": "biomechanics_expert",
        "description": "Expert in movement mechanics",
        "keywords": ["force", "velocity", "kinematics"]
      }
    ]
  }'

# Query the ensemble
curl -X POST "http://localhost:8000/api/diadochi/ensemble/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does stride frequency affect running performance?",
    "include_metadata": true
  }'
```

## 🧪 Advanced Configuration

### Custom Confidence Estimation

```python
# Hybrid confidence with custom weights
hybrid_confidence = HybridConfidence(
    estimators=[
        EmbeddingConfidence(temperature=0.6),
        KeywordConfidence(boost_exact_matches=True),
        TFIDFConfidence(max_features=5000)
    ],
    weights=[0.5, 0.3, 0.2],
    combination_method="weighted_average"
)
```

### Advanced Mixing Strategies

```python
# Consensus-based mixing
consensus_mixer = ConsensusBasedMixer(
    consensus_threshold=0.7,
    conflict_resolution="weight_based"
)

# Weighted segment mixing
weighted_mixer = WeightedMixer(
    combination_method="weighted_segments",
    segment_length=100,
    overlap_penalty=0.1
)
```

### Chain with Context Management

```python
# Summarizing chain for long contexts
summarizing_chain = SummarizingChain(
    models=expert_models,
    summarizer=synthesis_model,
    summary_threshold=2000,
    summary_target_length=500
)
```

## 🎛️ Configuration Options

### Router Configuration

```python
# Embedding router with custom model
router = EmbeddingRouter(
    threshold=0.6,
    embedding_model="all-MiniLM-L6-v2",
    temperature=1.0
)

# Keyword router with regex patterns
router = KeywordRouter(
    threshold=0.3,
    case_sensitive=False,
    boost_exact_matches=True
)
```

### Ensemble Configuration

```python
config = EnsembleConfig(
    default_model="general_expert",
    fallback_strategy="all",  # "default", "random", "all"
    parallel_execution=True,
    timeout=30,
    max_retries=3
)
```

### MoE Configuration

```python
config = MoEConfig(
    confidence_threshold=0.15,
    max_experts=5,
    temperature=0.8,
    aggregation_method="weighted",  # "weighted", "top_k", "threshold"
    normalize_weights=True,
    use_meta_expert=True
)
```

## 🔧 Extending Diadochi

### Custom Models

```python
from diadochi.core.models import Model

class CustomModel(Model):
    async def generate(self, prompt: str) -> str:
        # Your custom model implementation
        pass
    
    async def embed(self, text: str) -> List[float]:
        # Your embedding implementation
        pass
```

### Custom Routers

```python
from diadochi.core.routers import Router

class CustomRouter(Router):
    async def route(self, query: str, available_models: List[str]) -> Optional[str]:
        # Your custom routing logic
        pass
```

### Custom Mixers

```python
from diadochi.core.mixers import Mixer

class CustomMixer(Mixer):
    async def mix(self, query: str, responses: Dict[str, str], weights: Optional[Dict[str, float]] = None) -> str:
        # Your custom mixing logic
        pass
```

## 📈 Performance Optimization

### Parallel Execution

```python
# Enable parallel execution for faster responses
ensemble = Ensemble(
    router=router,
    models=registry,
    config=EnsembleConfig(parallel_execution=True)
)
```

### Caching

```python
# Implement caching for repeated queries
from functools import lru_cache

@lru_cache(maxsize=100)
async def cached_generate(query: str):
    return await ensemble.generate(query)
```

### Batch Processing

```python
# Process multiple queries efficiently
queries = ["Query 1", "Query 2", "Query 3"]
tasks = [ensemble.generate(query) for query in queries]
responses = await asyncio.gather(*tasks)
```

## 🏥 Health Monitoring

```python
# Comprehensive health check
health = await ensemble.health_check()
print(f"Overall Health: {health['overall_health']}")
print(f"Model Status: {health['models']}")

# Performance statistics
stats = ensemble.get_statistics()
print(f"Success Rate: {stats['success_rate']:.2%}")
print(f"Average Response Time: {stats['average_response_time']:.2f}s")
```

## 🔒 Error Handling

```python
try:
    response = await ensemble.generate(query)
except Exception as e:
    logger.error(f"Generation failed: {e}")
    # Implement fallback strategy
    response = await fallback_model.generate(query)
```

## 📝 Logging

```python
import logging

# Configure logging for Diadochi
logging.getLogger("diadochi").setLevel(logging.INFO)

# Enable debug logging for detailed information
logging.getLogger("diadochi.core.routers").setLevel(logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Based on the "Combine Harvester" architectural patterns
- Inspired by the need for interdisciplinary AI systems
- Built for the Hegel project's domain expertise requirements

## 📚 Citation

If you use Diadochi in your research, please cite:

```bibtex
@software{diadochi2024,
  title={Diadochi: Intelligent Domain LLM Combination Framework},
  author={Hegel Team},
  year={2024},
  url={https://github.com/hegel/diadochi}
}
```

---

<p align="center">
  <strong>Diadochi</strong> - Combining domain expertise for superior AI systems
</p> 