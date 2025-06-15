"""
Sports Science Domain Expert Example using Diadochi

This example demonstrates how to create and use domain expert combinations
for sports science queries, covering biomechanics, exercise physiology,
and sports nutrition domains.
"""

import asyncio
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Diadochi components
from ..core.registry import ModelRegistry
from ..core.routers import EmbeddingRouter, KeywordRouter
from ..core.mixers import SynthesisMixer, ConcatenationMixer
from ..patterns.ensemble import Ensemble, EnsembleConfig
from ..patterns.moe import MixtureOfExperts, MoEConfig
from ..core.chains import Chain, SummarizingChain
from ..utils.confidence import EmbeddingConfidence, KeywordConfidence, HybridConfidence


class SportsScienceDemo:
    """Demonstration of Diadochi with sports science domain experts."""
    
    def __init__(self):
        """Initialize the demo with domain expert models."""
        self.registry = ModelRegistry()
        self.setup_models()
        self.setup_domains()
    
    def setup_models(self):
        """Set up domain expert models."""
        # In a real scenario, these would be actual trained domain expert models
        # For this example, we'll use placeholder configurations
        
        try:
            # Biomechanics expert
            self.registry.add_model(
                name="biomechanics_expert",
                engine="ollama",
                model_name="llama3.2",  # Replace with actual biomechanics expert model
                temperature=0.3,
                max_tokens=500
            )
            
            # Exercise physiology expert
            self.registry.add_model(
                name="physiology_expert", 
                engine="ollama",
                model_name="llama3.2",  # Replace with actual physiology expert model
                temperature=0.4,
                max_tokens=500
            )
            
            # Sports nutrition expert
            self.registry.add_model(
                name="nutrition_expert",
                engine="ollama", 
                model_name="llama3.2",  # Replace with actual nutrition expert model
                temperature=0.4,
                max_tokens=500
            )
            
            # General sports science synthesizer
            self.registry.add_model(
                name="sports_synthesizer",
                engine="ollama",
                model_name="llama3.2",
                temperature=0.5,
                max_tokens=800
            )
            
            logger.info("Successfully registered all domain expert models")
            
        except Exception as e:
            logger.error(f"Error setting up models: {e}")
            # For demo purposes, continue even if models aren't available
    
    def setup_domains(self):
        """Define domain descriptions and characteristics."""
        self.domains = {
            "biomechanics_expert": {
                "description": (
                    "Biomechanics expert specializing in the mechanical laws relating to the movement "
                    "of living organisms. Focuses on force production, joint kinematics, muscle activation "
                    "patterns, and movement efficiency in athletic performance."
                ),
                "keywords": [
                    "force", "velocity", "acceleration", "torque", "power", "stride", "gait", 
                    "kinematics", "kinetics", "ground reaction", "joint angle", "muscle activation",
                    "mechanical advantage", "lever arm", "center of mass", "momentum", "technique"
                ],
                "examples": [
                    "What is the optimal stride frequency for elite sprinters?",
                    "How does ground reaction force affect running performance?",
                    "What joint angles maximize power output in jumping?"
                ]
            },
            
            "physiology_expert": {
                "description": (
                    "Exercise physiology expert focusing on the physiological responses and adaptations "
                    "to physical activity. Specializes in energy systems, cardiovascular responses, "
                    "muscular adaptations, and training-induced physiological changes."
                ),
                "keywords": [
                    "VO2 max", "lactate threshold", "aerobic", "anaerobic", "energy systems",
                    "ATP", "glycolysis", "oxidative", "heart rate", "cardiac output", "fatigue",
                    "adaptation", "training", "recovery", "muscle fiber", "mitochondria"
                ],
                "examples": [
                    "How does training affect mitochondrial density?",
                    "What are the physiological limiters of endurance performance?",
                    "How long does it take to adapt to altitude training?"
                ]
            },
            
            "nutrition_expert": {
                "description": (
                    "Sports nutrition expert specializing in dietary strategies to optimize athletic "
                    "performance and recovery. Focuses on macronutrient timing, hydration strategies, "
                    "supplementation, and nutrition for different training phases."
                ),
                "keywords": [
                    "carbohydrates", "protein", "fats", "hydration", "glycogen", "amino acids",
                    "supplements", "recovery nutrition", "pre-workout", "post-workout", "electrolytes",
                    "timing", "macronutrients", "micronutrients", "energy availability"
                ],
                "examples": [
                    "What's the optimal post-workout nutrition strategy?",
                    "How much protein do endurance athletes need?",
                    "What hydration strategy works best for marathon runners?"
                ]
            }
        }
    
    async def create_embedding_router_ensemble(self) -> Ensemble:
        """Create an ensemble using embedding-based routing."""
        logger.info("Creating embedding router ensemble...")
        
        # Create embedding router
        router = EmbeddingRouter(threshold=0.3, temperature=0.8)
        
        # Add domain descriptions
        for domain_name, domain_info in self.domains.items():
            router.add_domain(
                domain_name,
                domain_info["description"],
                domain_info["keywords"],
                domain_info["examples"]
            )
        
        # Create synthesis mixer
        synthesizer = self.registry.get("sports_synthesizer")
        mixer = SynthesisMixer(synthesizer)
        
        # Create ensemble configuration
        config = EnsembleConfig(
            default_model="sports_synthesizer",
            fallback_strategy="default",
            parallel_execution=True,
            timeout=30
        )
        
        # Create ensemble
        ensemble = Ensemble(
            router=router,
            models=self.registry,
            mixer=mixer,
            config=config
        )
        
        logger.info("Embedding router ensemble created successfully")
        return ensemble
    
    async def create_keyword_router_ensemble(self) -> Ensemble:
        """Create an ensemble using keyword-based routing."""
        logger.info("Creating keyword router ensemble...")
        
        # Create keyword router  
        router = KeywordRouter(threshold=0.2, case_sensitive=False)
        
        # Add domain descriptions
        for domain_name, domain_info in self.domains.items():
            router.add_domain(
                domain_name,
                domain_info["description"],
                domain_info["keywords"],
                domain_info["examples"]
            )
        
        # Create concatenation mixer for this example
        mixer = ConcatenationMixer(include_weights=True)
        
        # Create ensemble
        ensemble = Ensemble(
            router=router,
            models=self.registry,
            mixer=mixer
        )
        
        logger.info("Keyword router ensemble created successfully")
        return ensemble
    
    async def create_mixture_of_experts(self) -> MixtureOfExperts:
        """Create a mixture of experts system."""
        logger.info("Creating mixture of experts...")
        
        # Create embedding confidence estimator
        confidence_estimator = EmbeddingConfidence(temperature=0.6)
        
        # Add domain descriptions
        for domain_name, domain_info in self.domains.items():
            confidence_estimator.add_domain(
                domain_name,
                domain_info["description"],
                domain_info["keywords"],
                domain_info["examples"]
            )
        
        # Create synthesis mixer
        synthesizer = self.registry.get("sports_synthesizer")
        mixer = SynthesisMixer(synthesizer)
        
        # Create MoE configuration
        config = MoEConfig(
            confidence_threshold=0.15,
            max_experts=3,
            parallel_execution=True,
            temperature=0.8,
            aggregation_method="weighted",
            normalize_weights=True
        )
        
        # Create MoE
        moe = MixtureOfExperts(
            confidence_estimator=confidence_estimator,
            models=self.registry,
            mixer=mixer,
            config=config
        )
        
        logger.info("Mixture of experts created successfully")
        return moe
    
    async def create_sequential_chain(self) -> Chain:
        """Create a sequential chain of domain experts."""
        logger.info("Creating sequential chain...")
        
        # Define the sequence: biomechanics -> physiology -> nutrition -> synthesis
        models = [
            self.registry.get("biomechanics_expert"),
            self.registry.get("physiology_expert"), 
            self.registry.get("nutrition_expert"),
            self.registry.get("sports_synthesizer")
        ]
        
        # Define prompt templates for each step
        prompt_templates = {
            "biomechanics_expert": (
                "As a biomechanics expert, analyze this query from a mechanical perspective: {query}\n\n"
                "Focus on movement mechanics, forces, and biomechanical factors."
            ),
            
            "physiology_expert": (
                "As an exercise physiologist, build on this biomechanical analysis:\n\n"
                "Biomechanics Analysis: {responses[0]}\n\n"
                "Original Query: {query}\n\n"
                "Provide physiological insights that complement the biomechanical analysis."
            ),
            
            "nutrition_expert": (
                "As a sports nutrition expert, consider these previous analyses:\n\n"
                "Biomechanics: {responses[0]}\n\n"
                "Physiology: {responses[1]}\n\n"
                "Original Query: {query}\n\n"
                "Add nutritional strategies that support the biomechanical and physiological aspects discussed."
            ),
            
            "sports_synthesizer": (
                "Synthesize these expert analyses into a comprehensive response:\n\n"
                "Biomechanics Expert: {responses[0]}\n\n"
                "Physiology Expert: {responses[1]}\n\n"
                "Nutrition Expert: {responses[2]}\n\n"
                "Original Query: {query}\n\n"
                "Create an integrated response that combines insights from all three domains."
            )
        }
        
        # Create chain
        chain = Chain(
            models=models,
            prompt_templates=prompt_templates,
            max_context_length=4000,
            stop_on_error=False
        )
        
        logger.info("Sequential chain created successfully")
        return chain
    
    async def create_hybrid_confidence_moe(self) -> MixtureOfExperts:
        """Create MoE with hybrid confidence estimation."""
        logger.info("Creating MoE with hybrid confidence estimation...")
        
        # Create individual confidence estimators
        embedding_confidence = EmbeddingConfidence(temperature=0.6)
        keyword_confidence = KeywordConfidence(case_sensitive=False, boost_exact_matches=True)
        
        # Add domains to both estimators
        for domain_name, domain_info in self.domains.items():
            embedding_confidence.add_domain(
                domain_name,
                domain_info["description"],
                domain_info["keywords"],
                domain_info["examples"]
            )
            keyword_confidence.add_domain(
                domain_name,
                domain_info["description"],
                domain_info["keywords"],
                domain_info["examples"]
            )
        
        # Create hybrid confidence estimator
        hybrid_confidence = HybridConfidence(
            estimators=[embedding_confidence, keyword_confidence],
            weights=[0.7, 0.3],  # Weight embedding similarity more heavily
            combination_method="weighted_average"
        )
        
        # Create synthesis mixer
        synthesizer = self.registry.get("sports_synthesizer")
        mixer = SynthesisMixer(synthesizer)
        
        # Create MoE
        moe = MixtureOfExperts(
            confidence_estimator=hybrid_confidence,
            models=self.registry,
            mixer=mixer,
            config=MoEConfig(confidence_threshold=0.1, max_experts=3)
        )
        
        logger.info("Hybrid confidence MoE created successfully")
        return moe
    
    async def run_demonstration_queries(self):
        """Run a series of demonstration queries."""
        # Test queries covering different domain combinations
        test_queries = [
            # Single domain queries
            "What is the optimal stride frequency for elite sprinters?",
            "How does lactate threshold training improve endurance performance?",
            "What's the best post-workout nutrition for muscle recovery?",
            
            # Multi-domain queries
            "How can sprint athletes optimize their recovery between races?",
            "What factors determine jumping performance in basketball players?",
            "How should marathon runners adjust training and nutrition at altitude?",
            
            # Complex interdisciplinary query
            ("How can a 100m sprinter improve their performance through integrated "
             "biomechanical technique optimization, physiological conditioning, and "
             "nutritional strategies?")
        ]
        
        # Create different systems
        systems = {}
        
        try:
            systems["embedding_ensemble"] = await self.create_embedding_router_ensemble()
            systems["keyword_ensemble"] = await self.create_keyword_router_ensemble()
            systems["mixture_of_experts"] = await self.create_mixture_of_experts()
            systems["sequential_chain"] = await self.create_sequential_chain()
            systems["hybrid_moe"] = await self.create_hybrid_confidence_moe()
        except Exception as e:
            logger.error(f"Error creating systems: {e}")
            return
        
        # Run queries through each system
        for query in test_queries:
            print(f"\n{'='*80}")
            print(f"QUERY: {query}")
            print(f"{'='*80}\n")
            
            for system_name, system in systems.items():
                print(f"\n{'-'*60}")
                print(f"SYSTEM: {system_name.upper()}")
                print(f"{'-'*60}")
                
                try:
                    if isinstance(system, (Ensemble, MixtureOfExperts)):
                        response = await system.generate(query, include_metadata=True)
                        
                        if isinstance(response, dict):
                            print(f"RESPONSE: {response['response']}")
                            
                            # Print metadata if available
                            metadata_key = "routing_info" if "routing_info" in response else "expert_info"
                            if metadata_key in response:
                                metadata = response[metadata_key]
                                print(f"\nMETADATA:")
                                if "selected_models" in metadata:
                                    print(f"  Selected Models: {metadata['selected_models']}")
                                if "selected_experts" in metadata:
                                    print(f"  Selected Experts: {metadata['selected_experts']}")
                                if "confidence_scores" in metadata:
                                    print(f"  Confidence Scores: {metadata['confidence_scores']}")
                        else:
                            print(f"RESPONSE: {response}")
                    
                    elif isinstance(system, Chain):
                        response = await system.generate(query)
                        print(f"RESPONSE: {response}")
                    
                except Exception as e:
                    print(f"ERROR: {e}")
                    logger.error(f"Error with {system_name}: {e}")
        
        # Print system statistics
        print(f"\n{'='*80}")
        print("SYSTEM STATISTICS")
        print(f"{'='*80}")
        
        for system_name, system in systems.items():
            if hasattr(system, 'get_statistics'):
                try:
                    stats = system.get_statistics()
                    print(f"\n{system_name.upper()}:")
                    print(f"  Total Queries: {stats.get('total_queries', 0)}")
                    print(f"  Success Rate: {stats.get('success_rate', 0):.2%}")
                    print(f"  Average Response Time: {stats.get('average_response_time', 0):.2f}s")
                    
                    if 'model_usage' in stats:
                        print(f"  Model Usage: {stats['model_usage']}")
                    if 'expert_usage' in stats:
                        print(f"  Expert Usage: {stats['expert_usage']}")
                
                except Exception as e:
                    logger.error(f"Error getting stats for {system_name}: {e}")


async def main():
    """Main function to run the sports science demonstration."""
    print("Diadochi Sports Science Domain Expert Demonstration")
    print("=" * 60)
    
    # Create and run demonstration
    demo = SportsScienceDemo()
    await demo.run_demonstration_queries()
    
    print("\nDemonstration completed!")


if __name__ == "__main__":
    asyncio.run(main()) 