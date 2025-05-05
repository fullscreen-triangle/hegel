"""
LLM service for evidence rectification in biomolecular analysis
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn
import httpx
from transformers import pipeline
import numpy as np

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Hegel LLM Service", version="0.1.0")

# Load LLM for evidence analysis
try:
    model_name = os.environ.get("LLM_MODEL", "distilbert-base-uncased")
    classifier = pipeline("text-classification", model=model_name)
    logger.info(f"Successfully loaded LLM model: {model_name}")
except Exception as e:
    logger.error(f"Error loading LLM model: {str(e)}")
    classifier = None

# Define request/response models
class Evidence(BaseModel):
    source: str
    data: Dict[str, Any]
    confidence: float


class RectificationOptions(BaseModel):
    use_ai_guidance: bool = True
    confidence_threshold: float = 0.6
    include_pathway_analysis: bool = True
    include_interactome_analysis: bool = True


class RectificationRequest(BaseModel):
    molecule_id: str
    evidences: List[Evidence]
    rectification_options: RectificationOptions


class RectifiedEvidence(BaseModel):
    source: str
    original_confidence: float
    rectified_confidence: float
    data: Dict[str, Any]
    explanation: Optional[str] = None


class RectificationResponse(BaseModel):
    molecule_id: str
    rectified_evidences: List[RectifiedEvidence]
    confidence_score: float
    reasoning: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Hegel LLM Service for evidence rectification"}


async def fetch_pathway_data(molecule_id: str):
    """Fetch pathway analysis data for contextual evidence"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{os.environ.get('PATHWAY_API', 'http://pathway-service:8000')}/pathways/{molecule_id}"
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch pathway data for {molecule_id}: {response.status_code}")
                return {}
    except Exception as e:
        logger.error(f"Error fetching pathway data: {str(e)}")
        return {}


async def fetch_interactome_data(molecule_id: str):
    """Fetch interactome analysis data for additional context"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{os.environ.get('INTERACTOME_API', 'http://interactome-service:8000')}/interactions/{molecule_id}"
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch interactome data for {molecule_id}: {response.status_code}")
                return {}
    except Exception as e:
        logger.error(f"Error fetching interactome data: {str(e)}")
        return {}


def analyze_evidence_with_llm(evidence: Evidence, context_data: Dict):
    """Analyze evidence using LLM to determine reliability"""
    if not classifier:
        logger.warning("LLM model not available, using fallback analysis")
        return 0.0, "LLM analysis unavailable"
    
    # Prepare input for the model
    evidence_str = json.dumps(evidence.data)
    context_str = json.dumps(context_data)
    
    prompt = f"""
    Analyzing molecular evidence from {evidence.source}:
    Evidence: {evidence_str}
    Context: {context_str}
    
    Rate the reliability of this evidence on a scale of 0-1.
    """
    
    try:
        # Get model prediction
        result = classifier(prompt)
        # Interpret results - in a real implementation you'd use a model 
        # fine-tuned specifically for this task
        llm_confidence = float(result[0]['score'])
        
        explanation = f"LLM analyzed the evidence from {evidence.source} considering pathway and interactome context."
        return llm_confidence, explanation
    except Exception as e:
        logger.error(f"Error in LLM analysis: {str(e)}")
        return 0.0, f"Error in LLM analysis: {str(e)}"


@app.post("/rectify", response_model=RectificationResponse)
async def rectify_evidence(request: RectificationRequest):
    """
    Rectify evidence using AI-guidance and contextual biological data
    """
    logger.info(f"Received rectification request for molecule: {request.molecule_id}")
    
    try:
        # Gather contextual data for better evidence analysis
        context_data = {}
        
        if request.rectification_options.include_pathway_analysis:
            pathway_data = await fetch_pathway_data(request.molecule_id)
            context_data["pathway"] = pathway_data
            
        if request.rectification_options.include_interactome_analysis:
            interactome_data = await fetch_interactome_data(request.molecule_id)
            context_data["interactome"] = interactome_data
        
        rectified_evidences = []
        total_confidence = 0.0
        all_explanations = []
        
        # Process each evidence with LLM guidance if enabled
        for evidence in request.evidences:
            if request.rectification_options.use_ai_guidance and classifier:
                # Use LLM to analyze evidence reliability
                llm_factor, explanation = analyze_evidence_with_llm(evidence, context_data)
                
                # Blend original confidence with LLM assessment
                weight_original = 0.3
                weight_llm = 0.7
                
                rectified_confidence = (
                    weight_original * evidence.confidence + 
                    weight_llm * llm_factor
                )
                
                all_explanations.append(explanation)
            else:
                # Fallback to rule-based rectification if AI guidance disabled
                source_factors = {
                    "genomics": 1.25,
                    "proteomics": 1.2,
                    "mass_spec": 1.15,
                    "literature": 1.1,
                    "clinical_trials": 1.3
                }
                
                factor = source_factors.get(evidence.source.lower(), 1.0)
                
                # Check if evidence is below threshold and should be adjusted
                if evidence.confidence < request.rectification_options.confidence_threshold:
                    factor *= 0.9  # Reduce confidence for low-confidence evidence
                
                rectified_confidence = min(evidence.confidence * factor, 0.99)
                explanation = f"Confidence adjusted based on {evidence.source} reliability factor of {factor:.2f}"
                all_explanations.append(explanation)
            
            # Create rectified evidence object
            rectified_evidences.append(
                RectifiedEvidence(
                    source=evidence.source,
                    original_confidence=evidence.confidence,
                    rectified_confidence=rectified_confidence,
                    data=evidence.data,
                    explanation=explanation,
                )
            )
            
            total_confidence += rectified_confidence
        
        # Apply cross-evidence analysis and correlation
        if len(rectified_evidences) > 1:
            # Adjust confidences based on agreement between evidences
            confidences = np.array([e.rectified_confidence for e in rectified_evidences])
            std_dev = np.std(confidences)
            
            # High agreement = lower std dev = confidence boost
            agreement_factor = 1.0 - (std_dev * 0.5)  # Boost for consensus
            
            for i, evidence in enumerate(rectified_evidences):
                rectified_evidences[i].rectified_confidence = min(
                    evidence.rectified_confidence * agreement_factor, 0.99
                )
                rectified_evidences[i].explanation += f" Further adjusted by {agreement_factor:.2f} based on cross-evidence analysis."
        
        # Calculate overall confidence score
        if rectified_evidences:
            confidence_score = sum(e.rectified_confidence for e in rectified_evidences) / len(rectified_evidences)
        else:
            confidence_score = 0.0
        
        # Generate overall reasoning
        reasoning = "Evidence rectified using molecular LLM analysis integrating "
        if request.rectification_options.include_pathway_analysis:
            reasoning += "pathway data, "
        if request.rectification_options.include_interactome_analysis:
            reasoning += "interactome analysis, "
        reasoning += "and cross-evidence correlation."
        
        return RectificationResponse(
            molecule_id=request.molecule_id,
            rectified_evidences=rectified_evidences,
            confidence_score=confidence_score,
            reasoning=reasoning,
        )
        
    except Exception as e:
        logger.error(f"Error rectifying evidence: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error rectifying evidence: {str(e)}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True) 