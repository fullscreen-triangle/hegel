import logging
from typing import Dict, List, Optional, Any
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs
import networkx as nx

# Configure logging
logger = logging.getLogger(__name__)

def generate_molecule_visualization(
    molecule_data: Dict[str, Any], 
    visualization_type: str = "3d"
) -> Dict[str, Any]:
    """
    Generate visualization data for a molecule.
    
    Args:
        molecule_data: Dictionary containing molecule data
        visualization_type: Type of visualization to generate (3d, 2d, etc.)
        
    Returns:
        Dictionary containing visualization data
    """
    # Extract molecule structure data
    smiles = molecule_data.get("smiles")
    if not smiles:
        logger.error("Cannot generate visualization: No SMILES data provided")
        return {"error": "No molecule structure data available"}
    
    try:
        # Create RDKit molecule from SMILES
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            logger.error(f"Failed to create RDKit molecule from SMILES: {smiles}")
            return {"error": "Invalid molecule structure"}
        
        # Generate 3D coordinates if needed
        if visualization_type == "3d":
            mol = Chem.AddHs(mol)
            AllChem.EmbedMolecule(mol, randomSeed=42)
            AllChem.MMFFOptimizeMolecule(mol)
            
            # Extract 3D coordinates
            conf = mol.GetConformer()
            atoms = []
            bonds = []
            
            # Get atom data
            for atom in mol.GetAtoms():
                idx = atom.GetIdx()
                pos = conf.GetAtomPosition(idx)
                atoms.append({
                    "id": idx,
                    "element": atom.GetSymbol(),
                    "position": [pos.x, pos.y, pos.z],
                    "charge": atom.GetFormalCharge(),
                    "is_aromatic": atom.GetIsAromatic()
                })
            
            # Get bond data
            for bond in mol.GetBonds():
                bonds.append({
                    "source": bond.GetBeginAtomIdx(),
                    "target": bond.GetEndAtomIdx(),
                    "type": str(bond.GetBondType()),
                    "is_aromatic": bond.GetIsAromatic(),
                    "is_conjugated": bond.GetIsConjugated()
                })
            
            return {
                "atoms": atoms,
                "bonds": bonds,
                "format": "3d"
            }
            
        elif visualization_type == "2d":
            # Generate 2D coordinates
            AllChem.Compute2DCoords(mol)
            
            # Extract 2D coordinates
            conf = mol.GetConformer()
            atoms = []
            bonds = []
            
            # Get atom data
            for atom in mol.GetAtoms():
                idx = atom.GetIdx()
                pos = conf.GetAtomPosition(idx)
                atoms.append({
                    "id": idx,
                    "element": atom.GetSymbol(),
                    "position": [pos.x, pos.y, 0],  # Use only x, y coordinates
                    "charge": atom.GetFormalCharge(),
                    "is_aromatic": atom.GetIsAromatic()
                })
            
            # Get bond data
            for bond in mol.GetBonds():
                bonds.append({
                    "source": bond.GetBeginAtomIdx(),
                    "target": bond.GetEndAtomIdx(),
                    "type": str(bond.GetBondType()),
                    "is_aromatic": bond.GetIsAromatic(),
                    "is_conjugated": bond.GetIsConjugated()
                })
            
            return {
                "atoms": atoms,
                "bonds": bonds,
                "format": "2d"
            }
        
        else:
            logger.error(f"Unsupported visualization type: {visualization_type}")
            return {"error": f"Unsupported visualization type: {visualization_type}"}
            
    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}")
        return {"error": f"Visualization generation failed: {str(e)}"}

def generate_similarity_network(
    molecules: List[Dict[str, Any]],
    similarity_threshold: float = 0.7,
    layout: str = "force-directed"
) -> Dict[str, Any]:
    """
    Generate a similarity network visualization for a set of molecules.
    
    Args:
        molecules: List of molecule data dictionaries
        similarity_threshold: Minimum similarity score to create an edge
        layout: Network layout algorithm to use
        
    Returns:
        Dictionary containing network visualization data
    """
    try:
        # Create graph
        G = nx.Graph()
        
        # Add nodes (molecules)
        for molecule in molecules:
            mol_id = molecule.get("id")
            G.add_node(
                mol_id,
                name=molecule.get("name", ""),
                formula=molecule.get("formula", ""),
                smiles=molecule.get("smiles", ""),
                type=molecule.get("type", "unknown")
            )
        
        # Add edges (similarities)
        for i, mol1 in enumerate(molecules):
            mol1_id = mol1.get("id")
            for j, mol2 in enumerate(molecules):
                if i >= j:  # Skip duplicate comparisons
                    continue
                    
                mol2_id = mol2.get("id")
                
                # Get similarity between molecules
                # Use existing similarity values if available, otherwise calculate
                similarity = None
                
                # Check if similarity is directly provided in the data
                if "similarities" in mol1 and mol2_id in mol1["similarities"]:
                    similarity = mol1["similarities"][mol2_id]
                elif "similarities" in mol2 and mol1_id in mol2["similarities"]:
                    similarity = mol2["similarities"][mol1_id]
                
                # If similarity not provided, calculate it if SMILES are available
                if similarity is None and "smiles" in mol1 and "smiles" in mol2:
                    mol1_smiles = mol1["smiles"]
                    mol2_smiles = mol2["smiles"]
                    
                    # Calculate Tanimoto similarity using RDKit
                    try:
                        rdkit_mol1 = Chem.MolFromSmiles(mol1_smiles)
                        rdkit_mol2 = Chem.MolFromSmiles(mol2_smiles)
                        
                        if rdkit_mol1 and rdkit_mol2:
                            fp1 = AllChem.GetMorganFingerprintAsBitVect(rdkit_mol1, 2)
                            fp2 = AllChem.GetMorganFingerprintAsBitVect(rdkit_mol2, 2)
                            similarity = round(float(DataStructs.TanimotoSimilarity(fp1, fp2)), 3)
                        else:
                            similarity = 0.0
                            
                    except Exception as e:
                        logger.warning(f"Error calculating similarity: {str(e)}")
                        similarity = 0.0
                
                # Add edge if similarity is above threshold
                if similarity is not None and similarity >= similarity_threshold:
                    G.add_edge(mol1_id, mol2_id, weight=similarity)
        
        # Apply layout algorithm
        if layout == "force-directed":
            pos = nx.spring_layout(G, seed=42)
        elif layout == "circular":
            pos = nx.circular_layout(G)
        elif layout == "spectral":
            pos = nx.spectral_layout(G)
        else:
            pos = nx.random_layout(G, seed=42)
        
        # Convert graph to visualization format
        nodes = []
        for node, data in G.nodes(data=True):
            pos_xy = pos[node]
            nodes.append({
                "id": node,
                "name": data.get("name", ""),
                "formula": data.get("formula", ""),
                "type": data.get("type", ""),
                "position": [float(pos_xy[0]), float(pos_xy[1])],
                "degree": G.degree(node)
            })
        
        edges = []
        for source, target, data in G.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "similarity": data.get("weight", 0.0)
            })
        
        return {
            "nodes": nodes,
            "edges": edges
        }
        
    except Exception as e:
        logger.error(f"Error generating similarity network: {str(e)}")
        return {"nodes": [], "edges": [], "error": str(e)} 