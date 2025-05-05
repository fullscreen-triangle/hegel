from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, List, Optional
import logging
from pydantic import BaseModel

from ..services.molecule_network import molecule_network
from ..services.visualization import generate_molecule_visualization, generate_similarity_network

# Configure logging
logger = logging.getLogger(__name__)

# Define router
router = APIRouter(
    prefix="/visualizations",
    tags=["visualizations"],
    responses={404: {"description": "Not found"}},
)

# Visualization response models
class MoleculeVisualizationData(BaseModel):
    """Data for a 3D molecular visualization."""
    molecule_id: str
    structure_data: Dict
    visualization_type: str
    metadata: Optional[Dict] = None

class NetworkVisualizationData(BaseModel):
    """Data for a molecular network visualization."""
    nodes: List[Dict]
    edges: List[Dict]
    layout: str
    metadata: Optional[Dict] = None

@router.get("/{molecule_id}/3d", response_model=MoleculeVisualizationData)
async def get_molecule_visualization(
    molecule_id: str,
    visualization_type: str = Query("3d", description="Type of visualization (3d, 2d, etc.)"),
):
    """
    Generate a 3D visualization for a specific molecule.
    
    Args:
        molecule_id: The unique identifier for the molecule
        visualization_type: The type of visualization to generate
        
    Returns:
        Visualization data that can be rendered by the frontend
    """
    try:
        # Get molecule data from the database
        molecule_data = await molecule_network.get_molecule_by_id(molecule_id)
        
        if not molecule_data:
            raise HTTPException(status_code=404, detail=f"Molecule with ID {molecule_id} not found")
        
        # Generate visualization
        visualization = generate_molecule_visualization(
            molecule_data, 
            visualization_type=visualization_type
        )
        
        return MoleculeVisualizationData(
            molecule_id=molecule_id,
            structure_data=visualization,
            visualization_type=visualization_type,
            metadata={
                "name": molecule_data.get("name", ""),
                "formula": molecule_data.get("formula", ""),
                "inchi": molecule_data.get("inchi", "")
            }
        )
    
    except Exception as e:
        logger.error(f"Error generating visualization for molecule {molecule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating visualization")

@router.get("/similarity-network", response_model=NetworkVisualizationData)
async def get_similarity_network(
    molecule_ids: List[str] = Query(None, description="List of molecule IDs to include in network"),
    similarity_threshold: float = Query(0.7, description="Similarity threshold for connecting molecules"),
    max_molecules: int = Query(100, description="Maximum number of molecules to include"),
    layout: str = Query("force-directed", description="Network layout algorithm")
):
    """
    Generate a similarity network visualization for a set of molecules.
    
    Args:
        molecule_ids: Optional list of specific molecules to include
        similarity_threshold: Minimum similarity score to create an edge
        max_molecules: Maximum number of molecules to include in the visualization
        layout: Layout algorithm for the network
        
    Returns:
        Network visualization data that can be rendered by the frontend
    """
    try:
        # If no specific molecules requested, get most similar molecules
        if not molecule_ids:
            # Get most connected molecules from the database
            molecules = await molecule_network.get_most_connected_molecules(max_molecules)
        else:
            # Get the specified molecules and their connections
            molecules = await molecule_network.get_molecules_by_ids(molecule_ids, max_related=max_molecules)
        
        if not molecules:
            raise HTTPException(status_code=404, detail="No molecules found for network visualization")
        
        # Generate network visualization
        network = generate_similarity_network(
            molecules,
            similarity_threshold=similarity_threshold,
            layout=layout
        )
        
        return NetworkVisualizationData(
            nodes=network["nodes"],
            edges=network["edges"],
            layout=layout,
            metadata={
                "molecule_count": len(network["nodes"]),
                "connection_count": len(network["edges"]),
                "similarity_threshold": similarity_threshold
            }
        )
    
    except Exception as e:
        logger.error(f"Error generating similarity network: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating network visualization")
