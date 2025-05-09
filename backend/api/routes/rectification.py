"""
Rectification API routes for Hegel
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any
import os
import uuid
import httpx
import json
from datetime import datetime
from ..models.database import Database, get_db
from ..models.schemas import RectificationRequest, RectificationResult
from ..routes.auth import get_current_active_user, UserResponse

router = APIRouter()

# LLM Service configuration
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm-service:8000")

@router.post("/", response_model=RectificationResult)
async def rectify_molecule(
    request: RectificationRequest,
    background_tasks: BackgroundTasks,
    db: Database = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Rectify evidence for a molecule"""
    # Check if molecule exists
    molecule_query = """
    MATCH (m:Molecule {id: $molecule_id})
    RETURN m
    """
    
    molecule_result = await db.run_query(molecule_query, {"molecule_id": request.molecule_id})
    if not molecule_result:
        raise HTTPException(status_code=404, detail="Molecule not found")
    
    molecule_data = molecule_result[0][0]
    
    # Get evidence for the molecule
    evidence_query = """
    MATCH (m:Molecule {id: $molecule_id})-[:HAS_EVIDENCE]->(e:Evidence)
    RETURN e
    """
    
    evidence_result = await db.run_query(evidence_query, {"molecule_id": request.molecule_id})
    if not evidence_result:
        return RectificationResult(
            molecule_id=request.molecule_id,
            original_confidence=molecule_data.get("confidence_score", 0.0),
            rectified_confidence=molecule_data.get("confidence_score", 0.0),
            explanation="No evidence found for rectification",
            conflicts_detected=0,
            conflicts_resolved=0
        )
    
    # Convert evidence to list of dictionaries
    evidences = []
    for row in evidence_result:
        evidence_data = row[0]
        evidences.append({
            "id": evidence_data["id"],
            "source": evidence_data["source"],
            "confidence": evidence_data["confidence"],
            "evidence_type": evidence_data["evidence_type"],
            "value": evidence_data["value"],
            "metadata": evidence_data.get("metadata", {})
        })
    
    # Detect conflicts
    conflicts = detect_conflicts(evidences, threshold=0.3)
    
    # If no conflicts and confidence above threshold, no need to rectify
    original_confidence = molecule_data.get("confidence_score", 0.0)
    if not conflicts and original_confidence >= request.confidence_threshold:
        return RectificationResult(
            molecule_id=request.molecule_id,
            original_confidence=original_confidence,
            rectified_confidence=original_confidence,
            explanation="No conflicts detected and confidence is above threshold",
            conflicts_detected=0,
            conflicts_resolved=0
        )
    
    # If we need to generate explanation, use the LLM service
    explanation = None
    if request.explanation_required:
        explanation = await generate_explanation(evidences, molecule_data)
    
    # Apply rectification
    rectified_evidences, resolved_count = rectify_evidences(evidences, conflicts)
    
    # Calculate new confidence score
    rectified_confidence = calculate_confidence(rectified_evidences)
    
    # Update evidence confidence scores in background
    background_tasks.add_task(
        update_evidence_confidence,
        db, rectified_evidences
    )
    
    # Update molecule confidence score
    update_query = """
    MATCH (m:Molecule {id: $molecule_id})
    SET m.confidence_score = $confidence,
        m.last_rectified = $timestamp
    RETURN m
    """
    
    await db.run_query(update_query, {
        "molecule_id": request.molecule_id,
        "confidence": rectified_confidence,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Return result
    return RectificationResult(
        molecule_id=request.molecule_id,
        original_confidence=original_confidence,
        rectified_confidence=rectified_confidence,
        explanation=explanation,
        conflicts_detected=len(conflicts),
        conflicts_resolved=resolved_count
    )

def detect_conflicts(evidences: List[Dict[str, Any]], threshold: float = 0.3):
    """Detect conflicts between evidence sources"""
    conflicts = []
    
    for i in range(len(evidences)):
        for j in range(i+1, len(evidences)):
            # Check if evidences conflict
            confidence_diff = abs(evidences[i]["confidence"] - evidences[j]["confidence"])
            if confidence_diff > threshold:
                conflicts.append((i, j))
    
    return conflicts

def rectify_evidences(
    evidences: List[Dict[str, Any]], 
    conflicts: List[tuple]
) -> tuple:
    """Apply rectification to conflicting evidences"""
    if not conflicts:
        return evidences, 0
    
    # Make a copy to avoid modifying the original
    rectified = evidences.copy()
    resolved_count = 0
    
    for i, j in conflicts:
        # Simple rectification: reduce confidence of the lower confidence evidence
        if rectified[i]["confidence"] < rectified[j]["confidence"]:
            rectified[i]["confidence"] *= 0.8
        else:
            rectified[j]["confidence"] *= 0.8
        resolved_count += 1
    
    return rectified, resolved_count

def calculate_confidence(evidences: List[Dict[str, Any]]) -> float:
    """Calculate overall confidence score from evidences"""
    if not evidences:
        return 0.0
    
    total_confidence = sum(e["confidence"] for e in evidences)
    return total_confidence / len(evidences)

async def generate_explanation(
    evidences: List[Dict[str, Any]],
    molecule_data: Dict[str, Any]
) -> str:
    """Generate explanation for rectification using LLM service"""
    try:
        # Format prompt for LLM
        molecule_info = {
            "id": molecule_data["id"],
            "name": molecule_data["name"],
            "formula": molecule_data["formula"],
            "smiles": molecule_data.get("smiles"),
            "inchi": molecule_data.get("inchi")
        }
        
        prompt = f"""
        Analyze the evidence for molecule {molecule_info['name']} ({molecule_info['formula']}) and explain 
        any conflicts in the evidence and how they should be resolved:
        
        Evidence:
        """
        
        for idx, evidence in enumerate(evidences, 1):
            prompt += f"\n{idx}. {evidence['source']} ({evidence['evidence_type']}): {evidence['value']} (confidence: {evidence['confidence']:.2f})"
        
        # Call LLM service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LLM_SERVICE_URL}/api/explain",
                json={
                    "prompt": prompt,
                    "molecule": molecule_info,
                    "evidences": evidences
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("explanation", "No explanation generated")
            else:
                return "Failed to generate explanation"
    except Exception as e:
        return f"Error generating explanation: {str(e)}"

async def update_evidence_confidence(db: Database, evidences: List[Dict[str, Any]]):
    """Update evidence confidence scores in database"""
    for evidence in evidences:
        update_query = """
        MATCH (e:Evidence {id: $evidence_id})
        SET e.confidence = $confidence,
            e.updated_at = $timestamp
        RETURN e
        """
        
        await db.run_query(update_query, {
            "evidence_id": evidence["id"],
            "confidence": evidence["confidence"],
            "timestamp": datetime.utcnow().isoformat()
        }) 