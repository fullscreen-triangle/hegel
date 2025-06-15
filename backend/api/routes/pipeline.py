"""
API routes for Diadochi Pipeline orchestration.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import asyncio

from backend.diadochi import (
    DiadochiPipeline,
    PipelineFactory,
    MetacognitiveOrchestrator,
    PipelineStrategy,
    quick_query,
    quick_comparison
)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

# Global pipeline instance (in production, this would be properly managed)
_pipeline_instance: Optional[DiadochiPipeline] = None


def get_pipeline() -> DiadochiPipeline:
    """Get or create pipeline instance"""
    global _pipeline_instance
    if _pipeline_instance is None:
        # Create default sports science pipeline
        orchestrator = PipelineFactory.create_sports_science_orchestrator()
        _pipeline_instance = DiadochiPipeline(orchestrator)
    return _pipeline_instance


class QueryRequest(BaseModel):
    """Request model for pipeline queries"""
    question: str = Field(..., description="The question to process")
    domain: Optional[str] = Field(None, description="Optional domain context")
    strategy: str = Field("auto", description="Processing strategy")
    max_experts: int = Field(3, ge=1, le=10, description="Maximum number of experts")
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Confidence threshold")
    include_explanation: bool = Field(True, description="Include processing explanation")


class BatchQueryRequest(BaseModel):
    """Request model for batch queries"""
    questions: List[str] = Field(..., description="List of questions to process")
    domain: Optional[str] = Field(None, description="Optional domain context")
    strategy: str = Field("auto", description="Processing strategy")
    max_experts: int = Field(3, ge=1, le=10, description="Maximum number of experts")
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Confidence threshold")
    include_explanation: bool = Field(True, description="Include processing explanation")


class StrategyAnalysisRequest(BaseModel):
    """Request model for strategy analysis"""
    question: str = Field(..., description="The question to analyze")
    domain: Optional[str] = Field(None, description="Optional domain context")


class ComparisonRequest(BaseModel):
    """Request model for strategy comparison"""
    question: str = Field(..., description="The question to process")
    strategies: Optional[List[str]] = Field(None, description="Strategies to compare")


@router.post("/query", response_model=Dict[str, Any])
async def process_query(request: QueryRequest):
    """
    Process a single query through the complete Diadochi pipeline.
    
    This endpoint analyzes the query, selects the optimal processing strategy,
    and returns a comprehensive response with explanations and metadata.
    """
    try:
        pipeline = get_pipeline()
        
        result = await pipeline.query(
            question=request.question,
            domain=request.domain,
            strategy=request.strategy,
            max_experts=request.max_experts,
            confidence_threshold=request.confidence_threshold,
            include_explanation=request.include_explanation
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {str(e)}")


@router.post("/batch", response_model=Dict[str, Any])
async def process_batch_queries(request: BatchQueryRequest):
    """
    Process multiple queries in parallel through the pipeline.
    
    This endpoint processes multiple questions simultaneously and returns
    results for each query.
    """
    try:
        pipeline = get_pipeline()
        
        results = await pipeline.batch_query(
            questions=request.questions,
            domain=request.domain,
            strategy=request.strategy,
            max_experts=request.max_experts,
            confidence_threshold=request.confidence_threshold,
            include_explanation=request.include_explanation
        )
        
        return {
            "success": True,
            "data": {
                "results": results,
                "total_processed": len(results),
                "batch_summary": {
                    "average_confidence": sum(r.get("confidence", 0) for r in results) / len(results),
                    "strategies_used": list(set(r.get("strategy_used", "unknown") for r in results)),
                    "total_execution_time": sum(r.get("execution_time", 0) for r in results)
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")


@router.post("/analyze-strategy", response_model=Dict[str, Any])
async def analyze_strategy(request: StrategyAnalysisRequest):
    """
    Analyze what strategy would be used for a query without executing it.
    
    This endpoint provides insights into how the pipeline would process
    a query, including complexity analysis and strategy recommendations.
    """
    try:
        pipeline = get_pipeline()
        
        analysis = await pipeline.explain_strategy(
            question=request.question,
            domain=request.domain
        )
        
        return {
            "success": True,
            "data": analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy analysis failed: {str(e)}")


@router.post("/compare-strategies", response_model=Dict[str, Any])
async def compare_strategies(request: ComparisonRequest):
    """
    Compare results across different processing strategies.
    
    This endpoint processes the same query using different strategies
    and provides a comparison of results, performance, and confidence.
    """
    try:
        results = await quick_comparison(
            question=request.question,
            strategies=request.strategies
        )
        
        # Calculate comparison metrics
        comparison_metrics = {}
        if results:
            strategies = list(results.keys())
            valid_results = {k: v for k, v in results.items() if not isinstance(v, dict) or "error" not in v}
            
            if valid_results:
                comparison_metrics = {
                    "best_confidence": max((r.get("confidence", 0) for r in valid_results.values())),
                    "fastest_execution": min((r.get("execution_time", float('inf')) for r in valid_results.values())),
                    "average_confidence": sum(r.get("confidence", 0) for r in valid_results.values()) / len(valid_results),
                    "strategies_compared": len(strategies),
                    "successful_strategies": len(valid_results),
                    "failed_strategies": len(strategies) - len(valid_results)
                }
        
        return {
            "success": True,
            "data": {
                "results": results,
                "comparison_metrics": comparison_metrics
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy comparison failed: {str(e)}")


@router.get("/health", response_model=Dict[str, Any])
async def pipeline_health():
    """
    Check the health status of the pipeline and all its components.
    
    This endpoint provides detailed health information about the orchestrator,
    registered models, and component status.
    """
    try:
        pipeline = get_pipeline()
        health_status = await pipeline.health_check()
        
        return {
            "success": True,
            "data": health_status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/stats", response_model=Dict[str, Any])
async def pipeline_stats():
    """
    Get pipeline execution statistics and performance metrics.
    
    This endpoint provides statistics about pipeline usage, performance,
    and strategy effectiveness.
    """
    try:
        pipeline = get_pipeline()
        stats = pipeline.get_pipeline_stats()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.get("/experts", response_model=Dict[str, Any])
async def list_experts():
    """
    List all registered expert models in the pipeline.
    
    This endpoint provides information about available domain experts
    and their capabilities.
    """
    try:
        pipeline = get_pipeline()
        experts = pipeline.list_experts()
        
        # Get additional info about each expert
        expert_info = {}
        for expert_name in experts:
            try:
                # This would ideally get more detailed info from the model
                expert_info[expert_name] = {
                    "name": expert_name,
                    "status": "available",
                    "capabilities": ["text_generation", "domain_expertise"]
                }
            except Exception:
                expert_info[expert_name] = {
                    "name": expert_name,
                    "status": "unknown",
                    "capabilities": []
                }
        
        return {
            "success": True,
            "data": {
                "total_experts": len(experts),
                "expert_names": experts,
                "expert_details": expert_info
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Expert listing failed: {str(e)}")


@router.post("/quick-query", response_model=Dict[str, Any])
async def quick_query_endpoint(request: QueryRequest):
    """
    Quick query processing using the convenience function.
    
    This endpoint provides a simplified interface for processing queries
    without requiring pipeline setup.
    """
    try:
        result = await quick_query(
            question=request.question,
            domain=request.domain,
            strategy=request.strategy,
            max_experts=request.max_experts,
            confidence_threshold=request.confidence_threshold,
            include_explanation=request.include_explanation
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick query failed: {str(e)}")


@router.get("/strategies", response_model=Dict[str, Any])
async def list_strategies():
    """
    List available processing strategies and their descriptions.
    
    This endpoint provides information about different processing strategies
    and when to use each one.
    """
    strategies = {
        "auto": {
            "name": "Automatic Strategy Selection",
            "description": "Pipeline automatically selects the optimal strategy based on query analysis",
            "use_case": "General purpose - recommended for most queries",
            "complexity": "Variable"
        },
        "ensemble": {
            "name": "Router-Based Ensemble",
            "description": "Routes query to most appropriate expert using intelligent routing",
            "use_case": "Fast processing of straightforward queries",
            "complexity": "Simple to Moderate"
        },
        "moe": {
            "name": "Mixture of Experts",
            "description": "Processes query through multiple experts and synthesizes responses",
            "use_case": "Complex queries requiring multiple perspectives",
            "complexity": "Moderate to Complex"
        },
        "chain": {
            "name": "Sequential Chain",
            "description": "Processes query through experts sequentially with context building",
            "use_case": "Queries requiring deep, iterative analysis",
            "complexity": "Complex"
        },
        "hybrid": {
            "name": "Hybrid Approach",
            "description": "Combines multiple strategies intelligently based on confidence thresholds",
            "use_case": "Expert-level queries with high accuracy requirements",
            "complexity": "Expert"
        }
    }
    
    return {
        "success": True,
        "data": {
            "available_strategies": list(strategies.keys()),
            "strategy_details": strategies,
            "default_strategy": "auto"
        }
    } 