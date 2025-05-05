from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Dict, Any, Optional
import os
import logging
import asyncio
from pydantic import BaseModel, Field

from ..services.data_sources import data_source_manager
from ..services.molecule_network import molecule_network
from ..services.graph import graph_service
from ..services.auth import get_current_user

router = APIRouter(prefix="/molecules", tags=["molecules"])
logger = logging.getLogger(__name__)

# Models
class MoleculeRetrieveRequest(BaseModel):
    identifier: str = Field(..., description="Molecule identifier to look up")
    id_type: str = Field("name", description="Type of identifier (e.g., name, inchikey, smiles)")
    primary_source: str = Field("pubchem", description="Primary database to query")
    include_sources: List[str] = Field(default=[], description="Additional data sources to query")
    include_pathways: bool = Field(False, description="Whether to include pathway data")
    include_interactions: bool = Field(False, description="Whether to include interaction data")
    include_targets: bool = Field(False, description="Whether to include target data")

class MoleculeSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    source: str = Field("pubchem", description="Database to search")
    limit: int = Field(10, description="Maximum number of results", ge=1, le=100)

class MoleculeNetworkAddRequest(BaseModel):
    molecule_data: Dict[str, Any] = Field(..., description="Molecule data to add to network")
    build_connections: bool = Field(True, description="Whether to build connections to existing molecules")
    similarity_threshold: float = Field(0.7, description="Threshold for structural similarity", ge=0.0, le=1.0)

class MoleculeListResponse(BaseModel):
    count: int = Field(..., description="Number of molecules returned")
    molecules: List[Dict[str, Any]] = Field(..., description="List of molecule data")

class MoleculeResponse(BaseModel):
    id: Optional[str] = Field(None, description="Molecule ID in the graph database")
    success: bool = Field(..., description="Whether the operation was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Molecule data")
    error: Optional[str] = Field(None, description="Error message if operation failed")

class MoleculeNeighborhoodResponse(BaseModel):
    nodes: List[Dict[str, Any]] = Field(..., description="Network nodes")
    edges: List[Dict[str, Any]] = Field(..., description="Network edges")

class EvidenceResponse(BaseModel):
    molecule: Dict[str, Any] = Field(..., description="Base molecule data")
    evidence: List[Dict[str, Any]] = Field(..., description="Evidence data from multiple sources")
    
# Routes

@router.post("/retrieve", response_model=MoleculeResponse)
async def retrieve_molecule(request: MoleculeRetrieveRequest):
    """
    Retrieve molecule information from external databases.
    Aggregates data from multiple sources if specified.
    """
    try:
        async with data_source_manager:
            # Get molecule from primary source
            molecule_data = await data_source_manager.get_molecule_by_id(
                request.identifier,
                request.primary_source,
                request.include_sources
            )
            
            if not molecule_data:
                return MoleculeResponse(
                    success=False, 
                    error=f"Molecule not found in {request.primary_source}"
                )
            
            # Get additional data if requested
            if request.include_pathways and molecule_data:
                pathways = await data_source_manager.get_molecule_pathways(
                    molecule_data.get('id', request.identifier),
                    request.primary_source
                )
                if pathways:
                    molecule_data['pathways'] = pathways
            
            if request.include_interactions and molecule_data:
                interactions = await data_source_manager.get_molecule_interactions(
                    molecule_data.get('id', request.identifier), 
                    'drugbank' if 'drugbank' in request.include_sources else request.primary_source
                )
                if interactions:
                    molecule_data['interactions'] = interactions
            
            # Get cross-references from external IDs
            if molecule_data:
                external_ids = await data_source_manager.get_molecule_external_ids(
                    molecule_data.get('id', request.identifier),
                    request.primary_source
                )
                if external_ids:
                    molecule_data.update(external_ids)
            
            return MoleculeResponse(
                success=bool(molecule_data),
                data=molecule_data,
                id=molecule_data.get('id') if molecule_data else None
            )
    except Exception as e:
        logger.exception(f"Error retrieving molecule: {str(e)}")
        return MoleculeResponse(success=False, error=f"Error retrieving molecule: {str(e)}")

@router.post("/search", response_model=MoleculeListResponse)
async def search_molecules(request: MoleculeSearchRequest):
    """
    Search for molecules by name or other attributes.
    """
    try:
        async with data_source_manager:
            molecules = await data_source_manager.search_molecules(
                request.query,
                request.source,
                request.limit
            )
            
            return MoleculeListResponse(
                count=len(molecules),
                molecules=molecules
            )
    except Exception as e:
        logger.exception(f"Error searching molecules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching molecules: {str(e)}")

@router.post("/network/add", response_model=MoleculeResponse)
async def add_to_network(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Add a molecule to the molecular network.
    Can optionally build connections to other molecules.
    """
    try:
        if not molecule_network:
            raise HTTPException(status_code=500, detail="Molecule network not initialized")
            
        # Add molecule to network
        molecule_id = await molecule_network.create_molecule_node(request)
        
        if not molecule_id:
            return MoleculeResponse(
                success=False,
                error="Failed to add molecule to network"
            )
            
        # Build connections in the background to avoid blocking
        if request.get('build_connections', True):
            background_tasks.add_task(
                build_molecule_connections,
                molecule_id,
                request,
                request.get('similarity_threshold', 0.7)
            )
            
        return MoleculeResponse(
            success=True,
            id=molecule_id,
            data={"id": molecule_id}
        )
    except Exception as e:
        logger.exception(f"Error adding molecule to network: {str(e)}")
        return MoleculeResponse(
            success=False,
            error=f"Error adding molecule to network: {str(e)}"
        )

async def build_molecule_connections(molecule_id: str, molecule_data: Dict[str, Any], similarity_threshold: float = 0.7):
    """
    Background task to build connections between a molecule and existing molecules.
    """
    try:
        # We need to fetch similar molecules and build connections
        await molecule_network.build_molecule_network([molecule_data], similarity_threshold)
        logger.info(f"Successfully built connections for molecule {molecule_id}")
    except Exception as e:
        logger.exception(f"Error building connections for molecule {molecule_id}: {str(e)}")

@router.get("/{molecule_id}", response_model=MoleculeResponse)
async def get_molecule(molecule_id: str):
    """
    Get molecule data from the graph database by its ID.
    """
    try:
        if not molecule_network:
            raise HTTPException(status_code=500, detail="Molecule network not initialized")
            
        molecule_data = await molecule_network.get_molecule_by_id(molecule_id)
        
        if not molecule_data:
            return MoleculeResponse(
                success=False,
                error="Molecule not found"
            )
            
        return MoleculeResponse(
            success=True,
            id=molecule_id,
            data=molecule_data
        )
    except Exception as e:
        logger.exception(f"Error retrieving molecule {molecule_id}: {str(e)}")
        return MoleculeResponse(
            success=False,
            error=f"Error retrieving molecule: {str(e)}"
        )

@router.get("/{molecule_id}/neighborhood", response_model=MoleculeNeighborhoodResponse)
async def get_molecule_neighborhood(
    molecule_id: str,
    relationship_types: List[str] = Query(None),
    max_depth: int = Query(2, ge=1, le=5),
    limit: int = Query(100, ge=1, le=500)
):
    """
    Get the neighborhood of a molecule in the graph.
    """
    try:
        if not molecule_network:
            raise HTTPException(status_code=500, detail="Molecule network not initialized")
            
        # Default relationship types if not specified
        if not relationship_types:
            relationship_types = ["SIMILAR_TO", "PARTICIPATES_IN", "INTERACTS_WITH"]
            
        neighborhood = await molecule_network.get_molecule_neighborhood(
            molecule_id,
            relationship_types,
            max_depth,
            limit
        )
        
        return neighborhood
    except Exception as e:
        logger.exception(f"Error retrieving neighborhood for molecule {molecule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving molecule neighborhood: {str(e)}")

@router.get("/{molecule_id}/evidence", response_model=EvidenceResponse)
async def get_molecule_evidence(molecule_id: str):
    """
    Get evidence supporting a molecule's identity from multiple sources.
    """
    try:
        if not molecule_network:
            raise HTTPException(status_code=500, detail="Molecule network not initialized")
            
        evidence = await molecule_network.get_evidence_summary(molecule_id)
        
        if not evidence:
            raise HTTPException(status_code=404, detail="Molecule or evidence not found")
            
        return evidence
    except Exception as e:
        logger.exception(f"Error retrieving evidence for molecule {molecule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving molecule evidence: {str(e)}")

@router.get("/by-property/{property_name}/{property_value}", response_model=MoleculeListResponse)
async def get_molecules_by_property(
    property_name: str,
    property_value: str,
    limit: int = Query(100, ge=1, le=500)
):
    """
    Get molecules that have a specific property value.
    """
    try:
        if not molecule_network:
            raise HTTPException(status_code=500, detail="Molecule network not initialized")
            
        molecules = await molecule_network.get_molecules_by_property(
            property_name,
            property_value,
            limit
        )
        
        return MoleculeListResponse(
            count=len(molecules),
            molecules=molecules
        )
    except Exception as e:
        logger.exception(f"Error retrieving molecules by property: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving molecules: {str(e)}")

@router.post("/batch/retrieve", response_model=List[MoleculeResponse])
async def retrieve_molecule_batch(requests: List[MoleculeRetrieveRequest]):
    """
    Retrieve information for multiple molecules in a batch.
    """
    try:
        async with data_source_manager:
            results = []
            
            for request in requests:
                # Process each request
                result = await retrieve_molecule(request)
                results.append(result)
                
            return results
    except Exception as e:
        logger.exception(f"Error processing batch retrieval: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")

@router.post("/validate", response_model=MoleculeResponse)
async def validate_molecule(request: MoleculeRetrieveRequest):
    """
    Validate a molecule's identity by retrieving data from multiple sources
    and evaluating confidence based on consistency across sources.
    """
    try:
        async with data_source_manager:
            # First retrieve the molecule data
            molecule_data = await data_source_manager.get_molecule_by_id(
                request.identifier,
                request.primary_source,
                request.include_sources or ["pubchem", "chembl", "kegg", "hmdb"]
            )
            
            if not molecule_data:
                return MoleculeResponse(
                    success=False, 
                    error=f"Molecule not found in {request.primary_source}"
                )
            
            # Add to network to get an ID
            if molecule_network:
                molecule_id = await molecule_network.create_molecule_node(molecule_data)
                
                if molecule_id:
                    # Get evidence summary
                    evidence = await molecule_network.get_evidence_summary(molecule_id)
                    
                    if evidence:
                        # Add validation status based on evidence
                        confidence_scores = [e.get('confidence', 0) for e in evidence.get('evidence', [])]
                        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
                        
                        validation_result = {
                            "id": molecule_id,
                            "name": molecule_data.get('name', 'Unknown'),
                            "validated": avg_confidence > 0.5,
                            "confidence": avg_confidence,
                            "evidence_count": len(evidence.get('evidence', [])),
                            "evidence_summary": evidence
                        }
                        
                        return MoleculeResponse(
                            success=True,
                            id=molecule_id,
                            data=validation_result
                        )
            
            # Fallback if network isn't available or evidence couldn't be generated
            return MoleculeResponse(
                success=True,
                data=molecule_data,
                id=molecule_data.get('id')
            )
    except Exception as e:
        logger.exception(f"Error validating molecule: {str(e)}")
        return MoleculeResponse(success=False, error=f"Error validating molecule: {str(e)}") 