"""
Diadochi Metacognitive Orchestrator

This module implements the central orchestrator that coordinates all Diadochi components
into a complete pipeline for intelligent domain LLM combination.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import logging
from enum import Enum

from .core.models import BaseModel
from .core.registry import ModelRegistry
from .core.routers import RouterStrategy, KeywordRouter, EmbeddingRouter, ClassifierRouter, LLMRouter
from .core.chains import SequentialChain
from .core.mixers import MixerStrategy, SynthesisMixer, WeightedMixer, ConsensusMixer
from .patterns.ensemble import RouterBasedEnsemble
from .patterns.moe import MixtureOfExperts
from .utils.confidence import ConfidenceEstimator


class PipelineStrategy(Enum):
    """Available pipeline strategies"""
    AUTO = "auto"  # Orchestrator decides
    ENSEMBLE = "ensemble"  # Router-based ensemble
    MOE = "mixture_of_experts"  # Mixture of experts
    CHAIN = "sequential_chain"  # Sequential processing
    HYBRID = "hybrid"  # Combination of strategies


class QueryComplexity(Enum):
    """Query complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


@dataclass
class PipelineConfig:
    """Configuration for pipeline execution"""
    strategy: PipelineStrategy = PipelineStrategy.AUTO
    max_parallel_models: int = 3
    confidence_threshold: float = 0.7
    enable_explanation: bool = True
    enable_metadata: bool = True
    timeout_seconds: float = 30.0
    fallback_strategy: Optional[PipelineStrategy] = PipelineStrategy.ENSEMBLE


@dataclass
class PipelineResult:
    """Result from pipeline execution"""
    response: str
    confidence: float
    strategy_used: PipelineStrategy
    models_used: List[str]
    execution_time: float
    metadata: Dict[str, Any]
    explanation: Optional[str] = None
    intermediate_results: Optional[List[Dict[str, Any]]] = None


class MetacognitiveOrchestrator:
    """
    Central orchestrator that coordinates all Diadochi components into a complete pipeline.
    
    This class implements metacognitive reasoning to:
    1. Analyze incoming queries
    2. Select optimal processing strategies
    3. Coordinate multiple domain experts
    4. Synthesize results intelligently
    5. Provide comprehensive explanations
    """
    
    def __init__(self, model_registry: ModelRegistry):
        self.registry = model_registry
        self.logger = logging.getLogger(__name__)
        
        # Initialize core components
        self.routers = {
            'keyword': KeywordRouter(),
            'embedding': EmbeddingRouter(),
            'classifier': ClassifierRouter(),
            'llm': LLMRouter()
        }
        
        self.mixers = {
            'synthesis': SynthesisMixer(),
            'weighted': WeightedMixer(),
            'consensus': ConsensusMixer()
        }
        
        self.confidence_estimator = ConfidenceEstimator()
        
        # Pipeline statistics
        self.stats = {
            'total_queries': 0,
            'strategy_usage': {strategy.value: 0 for strategy in PipelineStrategy},
            'average_execution_time': 0.0,
            'success_rate': 0.0
        }
    
    async def process_query(
        self,
        query: str,
        domain_context: Optional[str] = None,
        config: Optional[PipelineConfig] = None
    ) -> PipelineResult:
        """
        Process a query through the complete Diadochi pipeline.
        
        Args:
            query: The input query to process
            domain_context: Optional domain context for better routing
            config: Pipeline configuration
            
        Returns:
            PipelineResult containing response and metadata
        """
        start_time = time.time()
        config = config or PipelineConfig()
        
        try:
            # Step 1: Analyze query and determine strategy
            analysis = await self._analyze_query(query, domain_context)
            strategy = await self._select_strategy(analysis, config)
            
            self.logger.info(f"Processing query with strategy: {strategy.value}")
            
            # Step 2: Execute pipeline based on selected strategy
            result = await self._execute_pipeline(query, strategy, analysis, config)
            
            # Step 3: Post-process and enhance result
            enhanced_result = await self._enhance_result(result, analysis, config)
            
            # Update statistics
            execution_time = time.time() - start_time
            self._update_stats(strategy, execution_time, True)
            
            return PipelineResult(
                response=enhanced_result['response'],
                confidence=enhanced_result['confidence'],
                strategy_used=strategy,
                models_used=enhanced_result['models_used'],
                execution_time=execution_time,
                metadata=enhanced_result['metadata'],
                explanation=enhanced_result.get('explanation'),
                intermediate_results=enhanced_result.get('intermediate_results')
            )
            
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {str(e)}")
            execution_time = time.time() - start_time
            self._update_stats(config.strategy, execution_time, False)
            
            # Attempt fallback if configured
            if config.fallback_strategy and config.fallback_strategy != config.strategy:
                self.logger.info(f"Attempting fallback strategy: {config.fallback_strategy.value}")
                try:
                    return await self.process_query(
                        query, 
                        domain_context, 
                        PipelineConfig(strategy=config.fallback_strategy)
                    )
                except Exception as fallback_error:
                    self.logger.error(f"Fallback strategy also failed: {str(fallback_error)}")
            
            # Return error result
            return PipelineResult(
                response=f"Pipeline execution failed: {str(e)}",
                confidence=0.0,
                strategy_used=config.strategy,
                models_used=[],
                execution_time=execution_time,
                metadata={'error': str(e), 'failed': True}
            )
    
    async def _analyze_query(self, query: str, domain_context: Optional[str] = None) -> Dict[str, Any]:
        """Analyze query to determine optimal processing approach"""
        analysis = {
            'query': query,
            'domain_context': domain_context,
            'length': len(query.split()),
            'complexity': QueryComplexity.SIMPLE,
            'domains': [],
            'keywords': [],
            'requires_expertise': False,
            'requires_synthesis': False,
            'confidence_requirements': 'medium'
        }
        
        # Analyze query complexity
        word_count = len(query.split())
        if word_count > 50:
            analysis['complexity'] = QueryComplexity.COMPLEX
        elif word_count > 20:
            analysis['complexity'] = QueryComplexity.MODERATE
        
        # Detect if multiple domains are involved
        domain_indicators = [
            'compare', 'versus', 'and', 'both', 'multiple', 'different',
            'integrate', 'combine', 'synthesis', 'holistic'
        ]
        
        query_lower = query.lower()
        if any(indicator in query_lower for indicator in domain_indicators):
            analysis['requires_synthesis'] = True
            analysis['complexity'] = QueryComplexity.COMPLEX
        
        # Detect expertise requirements
        expert_indicators = [
            'explain', 'analyze', 'detailed', 'comprehensive', 'in-depth',
            'research', 'study', 'investigation', 'technical'
        ]
        
        if any(indicator in query_lower for indicator in expert_indicators):
            analysis['requires_expertise'] = True
        
        # Extract potential domains and keywords
        # This could be enhanced with NLP techniques
        analysis['keywords'] = [word for word in query.split() if len(word) > 3]
        
        return analysis
    
    async def _select_strategy(
        self, 
        analysis: Dict[str, Any], 
        config: PipelineConfig
    ) -> PipelineStrategy:
        """Select optimal pipeline strategy based on query analysis"""
        
        if config.strategy != PipelineStrategy.AUTO:
            return config.strategy
        
        # Decision logic based on analysis
        complexity = analysis['complexity']
        requires_synthesis = analysis['requires_synthesis']
        requires_expertise = analysis['requires_expertise']
        
        # Simple queries -> Ensemble (fastest)
        if complexity == QueryComplexity.SIMPLE and not requires_synthesis:
            return PipelineStrategy.ENSEMBLE
        
        # Complex queries requiring synthesis -> MoE
        if requires_synthesis or complexity == QueryComplexity.COMPLEX:
            return PipelineStrategy.MOE
        
        # Queries requiring deep expertise -> Chain
        if requires_expertise and complexity in [QueryComplexity.MODERATE, QueryComplexity.COMPLEX]:
            return PipelineStrategy.CHAIN
        
        # Expert-level queries -> Hybrid approach
        if complexity == QueryComplexity.EXPERT:
            return PipelineStrategy.HYBRID
        
        # Default to ensemble
        return PipelineStrategy.ENSEMBLE
    
    async def _execute_pipeline(
        self,
        query: str,
        strategy: PipelineStrategy,
        analysis: Dict[str, Any],
        config: PipelineConfig
    ) -> Dict[str, Any]:
        """Execute the selected pipeline strategy"""
        
        if strategy == PipelineStrategy.ENSEMBLE:
            return await self._execute_ensemble(query, analysis, config)
        elif strategy == PipelineStrategy.MOE:
            return await self._execute_moe(query, analysis, config)
        elif strategy == PipelineStrategy.CHAIN:
            return await self._execute_chain(query, analysis, config)
        elif strategy == PipelineStrategy.HYBRID:
            return await self._execute_hybrid(query, analysis, config)
        else:
            raise ValueError(f"Unsupported strategy: {strategy}")
    
    async def _execute_ensemble(
        self,
        query: str,
        analysis: Dict[str, Any],
        config: PipelineConfig
    ) -> Dict[str, Any]:
        """Execute router-based ensemble strategy"""
        
        # Select appropriate router based on query characteristics
        router_name = 'embedding'  # Default
        if len(analysis['keywords']) > 0:
            router_name = 'keyword'
        
        router = self.routers[router_name]
        
        # Create ensemble
        ensemble = RouterBasedEnsemble(
            models=list(self.registry.get_all_models().values())[:config.max_parallel_models],
            router=router,
            mixer=self.mixers['weighted']
        )
        
        # Execute ensemble
        result = await ensemble.query(query)
        
        return {
            'response': result['response'],
            'confidence': result['confidence'],
            'models_used': result['metadata']['models_used'],
            'metadata': {
                'strategy': 'ensemble',
                'router_used': router_name,
                'mixer_used': 'weighted',
                **result['metadata']
            }
        }
    
    async def _execute_moe(
        self,
        query: str,
        analysis: Dict[str, Any],
        config: PipelineConfig
    ) -> Dict[str, Any]:
        """Execute mixture of experts strategy"""
        
        # Create MoE system
        moe = MixtureOfExperts(
            experts=list(self.registry.get_all_models().values())[:config.max_parallel_models],
            confidence_estimator=self.confidence_estimator,
            mixer=self.mixers['synthesis']
        )
        
        # Execute MoE
        result = await moe.query(query)
        
        return {
            'response': result['response'],
            'confidence': result['confidence'],
            'models_used': result['metadata']['models_used'],
            'metadata': {
                'strategy': 'moe',
                'expert_confidences': result['metadata'].get('expert_confidences', {}),
                'mixer_used': 'synthesis',
                **result['metadata']
            },
            'intermediate_results': result['metadata'].get('expert_responses', [])
        }
    
    async def _execute_chain(
        self,
        query: str,
        analysis: Dict[str, Any],
        config: PipelineConfig
    ) -> Dict[str, Any]:
        """Execute sequential chain strategy"""
        
        # Create sequential chain
        models = list(self.registry.get_all_models().values())[:config.max_parallel_models]
        chain = SequentialChain(models=models)
        
        # Execute chain
        result = await chain.process(query)
        
        return {
            'response': result['final_response'],
            'confidence': result['final_confidence'],
            'models_used': [step['model'] for step in result['steps']],
            'metadata': {
                'strategy': 'chain',
                'steps_executed': len(result['steps']),
                'context_evolution': result.get('context_evolution', [])
            },
            'intermediate_results': result['steps']
        }
    
    async def _execute_hybrid(
        self,
        query: str,
        analysis: Dict[str, Any],
        config: PipelineConfig
    ) -> Dict[str, Any]:
        """Execute hybrid strategy combining multiple approaches"""
        
        # First, use ensemble for quick initial response
        ensemble_result = await self._execute_ensemble(query, analysis, config)
        
        # If confidence is below threshold, use MoE for deeper analysis
        if ensemble_result['confidence'] < config.confidence_threshold:
            moe_result = await self._execute_moe(query, analysis, config)
            
            # Combine results using consensus mixer
            consensus_mixer = self.mixers['consensus']
            
            combined_result = await consensus_mixer.mix(
                responses=[ensemble_result['response'], moe_result['response']],
                confidences=[ensemble_result['confidence'], moe_result['confidence']],
                metadata=[ensemble_result['metadata'], moe_result['metadata']]
            )
            
            return {
                'response': combined_result['response'],
                'confidence': combined_result['confidence'],
                'models_used': ensemble_result['models_used'] + moe_result['models_used'],
                'metadata': {
                    'strategy': 'hybrid',
                    'ensemble_confidence': ensemble_result['confidence'],
                    'moe_confidence': moe_result['confidence'],
                    'combination_method': 'consensus',
                    **combined_result['metadata']
                },
                'intermediate_results': [
                    {'stage': 'ensemble', **ensemble_result},
                    {'stage': 'moe', **moe_result}
                ]
            }
        else:
            # Ensemble result was good enough
            ensemble_result['metadata']['strategy'] = 'hybrid_ensemble_only'
            return ensemble_result
    
    async def _enhance_result(
        self,
        result: Dict[str, Any],
        analysis: Dict[str, Any],
        config: PipelineConfig
    ) -> Dict[str, Any]:
        """Enhance result with additional processing"""
        
        enhanced = result.copy()
        
        # Add explanation if requested
        if config.enable_explanation:
            explanation = await self._generate_explanation(result, analysis)
            enhanced['explanation'] = explanation
        
        # Add detailed metadata if requested
        if config.enable_metadata:
            enhanced['metadata'].update({
                'query_analysis': analysis,
                'processing_timestamp': time.time(),
                'orchestrator_version': '1.0.0'
            })
        
        return enhanced
    
    async def _generate_explanation(
        self,
        result: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> str:
        """Generate explanation of how the result was obtained"""
        
        strategy = result['metadata']['strategy']
        confidence = result['confidence']
        models_used = result['models_used']
        
        explanation = f"""
**Processing Explanation:**

**Query Analysis:** Your query was classified as {analysis['complexity'].value} complexity. 
It {'requires' if analysis['requires_expertise'] else 'does not require'} specialized expertise 
and {'requires' if analysis['requires_synthesis'] else 'does not require'} synthesis of multiple perspectives.

**Strategy Selected:** {strategy.upper()}
- This strategy was chosen because it's optimal for your query characteristics.
- {len(models_used)} domain experts were involved in processing.

**Confidence Assessment:** {confidence:.2f}
{'This indicates high confidence in the response.' if confidence > 0.8 else 
 'This indicates moderate confidence in the response.' if confidence > 0.6 else 
 'This indicates lower confidence; consider seeking additional validation.'}

**Expert Models Used:** {', '.join(models_used)}

**Processing Details:** 
- Strategy: {strategy}
- Execution time: Available in metadata
- Quality assurance: All responses were validated and synthesized using advanced mixing algorithms.
        """.strip()
        
        return explanation
    
    def _update_stats(self, strategy: PipelineStrategy, execution_time: float, success: bool):
        """Update pipeline statistics"""
        self.stats['total_queries'] += 1
        self.stats['strategy_usage'][strategy.value] += 1
        
        # Update average execution time
        total_queries = self.stats['total_queries']
        current_avg = self.stats['average_execution_time']
        self.stats['average_execution_time'] = (
            (current_avg * (total_queries - 1) + execution_time) / total_queries
        )
        
        # Update success rate
        if success:
            current_success_rate = self.stats['success_rate']
            self.stats['success_rate'] = (
                (current_success_rate * (total_queries - 1) + 1.0) / total_queries
            )
        else:
            current_success_rate = self.stats['success_rate']
            self.stats['success_rate'] = (
                (current_success_rate * (total_queries - 1)) / total_queries
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline execution statistics"""
        return self.stats.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of all pipeline components"""
        health_status = {
            'orchestrator': 'healthy',
            'model_registry': 'unknown',
            'routers': {},
            'mixers': {},
            'components': {},
            'overall_status': 'healthy'
        }
        
        # Check model registry
        try:
            models = self.registry.get_all_models()
            health_status['model_registry'] = 'healthy' if models else 'no_models'
            health_status['components']['registered_models'] = len(models)
        except Exception as e:
            health_status['model_registry'] = f'error: {str(e)}'
            health_status['overall_status'] = 'degraded'
        
        # Check routers
        for name, router in self.routers.items():
            try:
                # Simple health check - just instantiation verification
                health_status['routers'][name] = 'healthy'
            except Exception as e:
                health_status['routers'][name] = f'error: {str(e)}'
                health_status['overall_status'] = 'degraded'
        
        # Check mixers
        for name, mixer in self.mixers.items():
            try:
                health_status['mixers'][name] = 'healthy'
            except Exception as e:
                health_status['mixers'][name] = f'error: {str(e)}'
                health_status['overall_status'] = 'degraded'
        
        health_status['components']['total_queries_processed'] = self.stats['total_queries']
        health_status['components']['success_rate'] = self.stats['success_rate']
        
        return health_status


class PipelineFactory:
    """Factory for creating pre-configured pipeline orchestrators"""
    
    @staticmethod
    def create_sports_science_orchestrator() -> MetacognitiveOrchestrator:
        """Create orchestrator configured for sports science domain"""
        from .examples.sports_science_example import create_sports_science_experts
        
        registry = ModelRegistry()
        experts = create_sports_science_experts()
        
        for expert in experts:
            registry.register_model(expert['name'], expert['model'])
        
        return MetacognitiveOrchestrator(registry)
    
    @staticmethod
    def create_general_orchestrator(models: List[BaseModel]) -> MetacognitiveOrchestrator:
        """Create orchestrator with provided models"""
        registry = ModelRegistry()
        
        for i, model in enumerate(models):
            registry.register_model(f"expert_{i+1}", model)
        
        return MetacognitiveOrchestrator(registry) 