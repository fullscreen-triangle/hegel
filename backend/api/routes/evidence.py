"""
Evidence API routes for Hegel
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import uuid
from datetime import datetime
from ..models.database import Database, get_db
from ..models.schemas import Evidence, EvidenceCreate, EvidenceUpdate
from ..routes.auth import get_current_active_user, UserResponse

router = APIRouter()

@router.post("/", response_model=Evidence)
async def create_evidence(
    evidence: EvidenceCreate,
    db: Database = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Create a new piece of evidence for a molecule"""
    # Verify molecule exists
    molecule_query = """
    MATCH (m:Molecule {id: $molecule_id})
    RETURN m
    """
    
    molecule_result = await db.run_query(molecule_query, {"molecule_id": evidence.molecule_id})
    if not molecule_result:
        raise HTTPException(status_code=404, detail="Molecule not found")
    
    # Create evidence
    evidence_id = f"ev-{uuid.uuid4()}"
    now = datetime.utcnow().isoformat()
    
    # Create evidence node
    create_query = """
    MATCH (m:Molecule {id: $molecule_id})
    CREATE (e:Evidence {
        id: $id,
        source: $source,
        confidence: $confidence,
        evidence_type: $evidence_type,
        value: $value,
        metadata: $metadata,
        created_at: $created_at,
        updated_at: $created_at,
        created_by: $created_by
    })
    CREATE (m)-[r:HAS_EVIDENCE]->(e)
    RETURN e
    """
    
    params = {
        "id": evidence_id,
        "molecule_id": evidence.molecule_id,
        "source": evidence.source,
        "confidence": evidence.confidence,
        "evidence_type": evidence.evidence_type,
        "value": evidence.value,
        "metadata": evidence.metadata or {},
        "created_at": now,
        "created_by": current_user.id
    }
    
    await db.run_query(create_query, params)
    
    # Update molecule confidence score
    update_confidence_query = """
    MATCH (m:Molecule {id: $molecule_id})-[:HAS_EVIDENCE]->(e:Evidence)
    WITH m, AVG(e.confidence) as avg_confidence
    SET m.confidence_score = avg_confidence
    RETURN m
    """
    
    await db.run_query(update_confidence_query, {"molecule_id": evidence.molecule_id})
    
    # Return created evidence
    return Evidence(
        id=evidence_id,
        molecule_id=evidence.molecule_id,
        source=evidence.source,
        confidence=evidence.confidence,
        evidence_type=evidence.evidence_type,
        value=evidence.value,
        metadata=evidence.metadata,
        created_at=datetime.fromisoformat(now)
    )

@router.get("/{evidence_id}", response_model=Evidence)
async def get_evidence(
    evidence_id: str,
    db: Database = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get evidence by ID"""
    query = """
    MATCH (e:Evidence {id: $evidence_id})
    MATCH (m:Molecule)-[:HAS_EVIDENCE]->(e)
    RETURN e, m.id as molecule_id
    """
    
    result = await db.run_query(query, {"evidence_id": evidence_id})
    if not result:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    evidence_data = result[0][0]
    molecule_id = result[0][1]
    
    return Evidence(
        id=evidence_data["id"],
        molecule_id=molecule_id,
        source=evidence_data["source"],
        confidence=evidence_data["confidence"],
        evidence_type=evidence_data["evidence_type"],
        value=evidence_data["value"],
        metadata=evidence_data.get("metadata", {}),
        created_at=datetime.fromisoformat(evidence_data["created_at"]),
        updated_at=datetime.fromisoformat(evidence_data.get("updated_at", evidence_data["created_at"]))
    )

@router.get("/molecule/{molecule_id}", response_model=List[Evidence])
async def get_molecule_evidence(
    molecule_id: str,
    db: Database = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
    evidence_type: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None, ge=0, le=1)
):
    """Get all evidence for a molecule"""
    params = {"molecule_id": molecule_id}
    
    # Base query
    query = """
    MATCH (m:Molecule {id: $molecule_id})-[:HAS_EVIDENCE]->(e:Evidence)
    """
    
    # Add filters
    if evidence_type:
        query += "WHERE e.evidence_type = $evidence_type\n"
        params["evidence_type"] = evidence_type
        
    if min_confidence is not None:
        if 'WHERE' in query:
            query += "AND e.confidence >= $min_confidence\n"
        else:
            query += "WHERE e.confidence >= $min_confidence\n"
        params["min_confidence"] = min_confidence
    
    # Add return
    query += "RETURN e, m.id as molecule_id ORDER BY e.created_at DESC"
    
    results = await db.run_query(query, params)
    
    evidence_list = []
    for row in results:
        evidence_data = row[0]
        molecule_id = row[1]
        
        evidence_list.append(
            Evidence(
                id=evidence_data["id"],
                molecule_id=molecule_id,
                source=evidence_data["source"],
                confidence=evidence_data["confidence"],
                evidence_type=evidence_data["evidence_type"],
                value=evidence_data["value"],
                metadata=evidence_data.get("metadata", {}),
                created_at=datetime.fromisoformat(evidence_data["created_at"]),
                updated_at=datetime.fromisoformat(evidence_data.get("updated_at", evidence_data["created_at"]))
            )
        )
    
    return evidence_list

@router.put("/{evidence_id}", response_model=Evidence)
async def update_evidence(
    evidence_id: str,
    evidence_update: EvidenceUpdate,
    db: Database = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Update an evidence record"""
    # Check if evidence exists
    check_query = """
    MATCH (e:Evidence {id: $evidence_id})
    MATCH (m:Molecule)-[:HAS_EVIDENCE]->(e)
    RETURN e, m.id as molecule_id
    """
    
    result = await db.run_query(check_query, {"evidence_id": evidence_id})
    if not result:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    # Get existing data
    evidence_data = result[0][0]
    molecule_id = result[0][1]
    now = datetime.utcnow().isoformat()
    
    # Build update params
    update_params = {
        "evidence_id": evidence_id,
        "updated_at": now
    }
    
    # Build update query parts
    update_parts = []
    if evidence_update.source is not None:
        update_parts.append("e.source = $source")
        update_params["source"] = evidence_update.source
    
    if evidence_update.confidence is not None:
        update_parts.append("e.confidence = $confidence")
        update_params["confidence"] = evidence_update.confidence
    
    if evidence_update.evidence_type is not None:
        update_parts.append("e.evidence_type = $evidence_type")
        update_params["evidence_type"] = evidence_update.evidence_type
    
    if evidence_update.value is not None:
        update_parts.append("e.value = $value")
        update_params["value"] = evidence_update.value
    
    if evidence_update.metadata is not None:
        update_parts.append("e.metadata = $metadata")
        update_params["metadata"] = evidence_update.metadata
    
    update_parts.append("e.updated_at = $updated_at")
    
    # Update evidence
    update_query = f"""
    MATCH (e:Evidence {{id: $evidence_id}})
    SET {', '.join(update_parts)}
    RETURN e
    """
    
    await db.run_query(update_query, update_params)
    
    # Update molecule confidence score
    update_confidence_query = """
    MATCH (m:Molecule {id: $molecule_id})-[:HAS_EVIDENCE]->(e:Evidence)
    WITH m, AVG(e.confidence) as avg_confidence
    SET m.confidence_score = avg_confidence
    RETURN m
    """
    
    await db.run_query(update_confidence_query, {"molecule_id": molecule_id})
    
    # Get updated evidence
    return await get_evidence(evidence_id, db, current_user)

@router.delete("/{evidence_id}")
async def delete_evidence(
    evidence_id: str,
    db: Database = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Delete an evidence record"""
    # Check if evidence exists and get molecule ID
    check_query = """
    MATCH (e:Evidence {id: $evidence_id})
    MATCH (m:Molecule)-[:HAS_EVIDENCE]->(e)
    RETURN m.id as molecule_id
    """
    
    result = await db.run_query(check_query, {"evidence_id": evidence_id})
    if not result:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    molecule_id = result[0][0]
    
    # Delete evidence
    delete_query = """
    MATCH (e:Evidence {id: $evidence_id})
    DETACH DELETE e
    """
    
    await db.run_query(delete_query, {"evidence_id": evidence_id})
    
    # Update molecule confidence score
    update_confidence_query = """
    MATCH (m:Molecule {id: $molecule_id})-[:HAS_EVIDENCE]->(e:Evidence)
    WITH m, CASE WHEN COUNT(e) > 0 THEN AVG(e.confidence) ELSE 0 END as avg_confidence
    SET m.confidence_score = avg_confidence
    RETURN m
    """
    
    await db.run_query(update_confidence_query, {"molecule_id": molecule_id})
    
    return {"message": "Evidence deleted"} 