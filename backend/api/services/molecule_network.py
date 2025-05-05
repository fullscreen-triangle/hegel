"""
Molecular network graph builder and manager.
This module constructs and maintains the core molecular network graph
that represents the relationships between molecules across multiple data sources.
"""

import asyncio
import logging
from typing import Dict, List, Any, Set, Tuple, Optional
from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import ServiceUnavailable
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs
import networkx as nx

from .data_sources import data_source_manager

logger = logging.getLogger(__name__)

class MoleculeNetworkBuilder:
    """Builds and maintains the molecule network graph in Neo4j."""
    
    def __init__(self, uri: str, username: str, password: str):
        """
        Initialize connection to Neo4j database.
        
        Args:
            uri: Neo4j server URI
            username: Neo4j username
            password: Neo4j password
        """
        self.driver = AsyncGraphDatabase.driver(uri, auth=(username, password))
        
    async def __aenter__(self):
        """Context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the Neo4j driver connection."""
        await self.driver.close()
    
    async def check_connection(self) -> bool:
        """Check if the connection to Neo4j is working."""
        try:
            async with self.driver.session() as session:
                result = await session.run("RETURN 1")
                return await result.single() is not None
        except ServiceUnavailable:
            return False
    
    async def create_molecule_node(self, 
                                  molecule_data: Dict[str, Any],
                                  replace_existing: bool = False) -> str:
        """
        Create a molecule node in the graph database.
        
        Args:
            molecule_data: Molecule data from external sources
            replace_existing: Whether to replace existing node if found
            
        Returns:
            ID of the created or existing node
        """
        # Extract key identifiers
        identifiers = {}
        
        # Standard identifiers we try to extract
        id_keys = [
            ('inchikey', 'inchikey'),
            ('standard_inchikey', 'inchikey'),
            ('inchi', 'inchi'), 
            ('standard_inchi', 'inchi'),
            ('canonical_smiles', 'smiles'),
            ('smiles', 'smiles'),
            ('id', molecule_data.get('source', 'unknown') + '_id')
        ]
        
        for source_key, target_key in id_keys:
            if source_key in molecule_data and molecule_data[source_key]:
                identifiers[target_key] = molecule_data[source_key]
        
        if not identifiers:
            logger.warning("No identifiers found for molecule, skipping")
            return None
            
        # Check if molecule already exists
        node_id = await self._find_molecule_by_identifiers(identifiers)
        
        if node_id and not replace_existing:
            logger.info(f"Molecule already exists with ID {node_id}")
            return node_id
            
        # Prepare properties
        properties = {
            'name': molecule_data.get('name', 'Unknown'),
            'formula': molecule_data.get('formula'),
            'source': molecule_data.get('source', 'unknown'),
            'evidence_sources': molecule_data.get('evidence_sources', [molecule_data.get('source', 'unknown')]),
            'last_updated': 'timestamp()',  # Neo4j will replace this with current timestamp
        }
        
        # Add all identifiers
        properties.update(identifiers)
        
        # Add all other properties, excluding certain keys
        excluded_keys = ['id', 'name', 'formula', 'source', 'evidence_sources'] + list(identifiers.keys())
        for key, value in molecule_data.items():
            if key not in excluded_keys and value is not None:
                # Convert lists to string to ensure compatibility with Neo4j
                if isinstance(value, list):
                    properties[key] = str(value)
                else:
                    properties[key] = value
        
        # Create or update the node
        async with self.driver.session() as session:
            if node_id and replace_existing:
                # Update existing node
                query = """
                MATCH (m:Molecule {id: $id})
                SET m += $properties
                RETURN m.id
                """
                result = await session.run(query, id=node_id, properties=properties)
            else:
                # Create new node
                properties['created'] = 'timestamp()'  # Neo4j will replace this with current timestamp
                query = """
                CREATE (m:Molecule)
                SET m = $properties, m.id = randomUUID()
                RETURN m.id
                """
                result = await session.run(query, properties=properties)
            
            record = await result.single()
            return record['m.id'] if record else None
    
    async def _find_molecule_by_identifiers(self, identifiers: Dict[str, str]) -> Optional[str]:
        """
        Find a molecule node by its identifiers.
        
        Args:
            identifiers: Dictionary of identifier types to values
            
        Returns:
            ID of found node or None
        """
        conditions = []
        params = {}
        
        # Build query conditions for each identifier
        for i, (key, value) in enumerate(identifiers.items()):
            param_name = f"value{i}"
            conditions.append(f"m.{key} = ${param_name}")
            params[param_name] = value
        
        if not conditions:
            return None
            
        # Build the query
        query = f"""
        MATCH (m:Molecule)
        WHERE {' OR '.join(conditions)}
        RETURN m.id
        LIMIT 1
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, **params)
            record = await result.single()
            return record['m.id'] if record else None
    
    async def build_molecule_network(self, 
                                    molecules: List[Dict[str, Any]],
                                    similarity_threshold: float = 0.7) -> None:
        """
        Build a network of molecules with similarity and other relationships.
        
        Args:
            molecules: List of molecule data dictionaries
            similarity_threshold: Tanimoto similarity threshold for creating edges
        """
        # First create all molecule nodes
        molecule_ids = []
        for molecule in molecules:
            molecule_id = await self.create_molecule_node(molecule)
            if molecule_id:
                molecule_ids.append((molecule_id, molecule))
        
        if len(molecule_ids) < 2:
            return
            
        # Compute molecule similarities and create edges
        await self._create_similarity_edges(molecule_ids, similarity_threshold)
        
        # Create relationship edges based on external data
        await self._create_relationship_edges(molecule_ids)
    
    async def _create_similarity_edges(self, 
                                     molecule_ids: List[Tuple[str, Dict[str, Any]]], 
                                     similarity_threshold: float) -> None:
        """
        Create similarity edges between molecules based on structural similarity.
        
        Args:
            molecule_ids: List of molecule IDs and their data
            similarity_threshold: Tanimoto similarity threshold for creating edges
        """
        # Extract SMILES
        smiles_data = []
        for node_id, molecule in molecule_ids:
            smiles = molecule.get('canonical_smiles') or molecule.get('smiles')
            if smiles:
                smiles_data.append((node_id, smiles))
        
        # Compute fingerprints
        fingerprints = []
        valid_ids = []
        for node_id, smiles in smiles_data:
            mol = Chem.MolFromSmiles(smiles)
            if mol:
                fingerprint = AllChem.GetMorganFingerprintAsBitVect(mol, 2)
                fingerprints.append(fingerprint)
                valid_ids.append(node_id)
        
        # Compute similarities
        edges = []
        for i in range(len(fingerprints)):
            for j in range(i+1, len(fingerprints)):
                similarity = DataStructs.TanimotoSimilarity(fingerprints[i], fingerprints[j])
                if similarity >= similarity_threshold:
                    edges.append((valid_ids[i], valid_ids[j], similarity))
        
        # Create edges in batches
        batch_size = 100
        for i in range(0, len(edges), batch_size):
            batch = edges[i:i+batch_size]
            await self._create_similarity_edges_batch(batch)
    
    async def _create_similarity_edges_batch(self, edges: List[Tuple[str, str, float]]) -> None:
        """
        Create a batch of similarity edges.
        
        Args:
            edges: List of (source_id, target_id, similarity) tuples
        """
        if not edges:
            return
            
        query = """
        UNWIND $edges AS edge
        MATCH (a:Molecule {id: edge.source}), (b:Molecule {id: edge.target})
        MERGE (a)-[r:SIMILAR_TO]->(b)
        SET r.similarity = edge.similarity, 
            r.last_updated = timestamp()
        RETURN count(r)
        """
        
        edge_params = [
            {"source": source, "target": target, "similarity": similarity}
            for source, target, similarity in edges
        ]
        
        async with self.driver.session() as session:
            await session.run(query, edges=edge_params)
    
    async def _create_relationship_edges(self, molecule_ids: List[Tuple[str, Dict[str, Any]]]) -> None:
        """
        Create relationship edges based on external database information.
        
        Args:
            molecule_ids: List of molecule IDs and their data
        """
        # Create pathway relationships
        for node_id, molecule in molecule_ids:
            # Extract pathway information
            pathways = []
            
            # Direct pathway data
            if 'pathways' in molecule and isinstance(molecule['pathways'], list):
                for pathway in molecule['pathways']:
                    if isinstance(pathway, dict):
                        pathways.append(pathway)
                    else:
                        # String pathway - likely from KEGG
                        parts = pathway.split()
                        if parts:
                            pathways.append({
                                'id': parts[0],
                                'name': ' '.join(parts[1:]) if len(parts) > 1 else parts[0],
                                'source': molecule.get('source', 'unknown')
                            })
            
            # Create pathway nodes and edges
            for pathway in pathways:
                await self._create_pathway_relationship(node_id, pathway)
            
            # Process interaction data if available
            if 'interactions' in molecule and isinstance(molecule['interactions'], list):
                for interaction in molecule['interactions']:
                    if isinstance(interaction, dict) and 'target_id' in interaction:
                        await self._create_interaction_relationship(node_id, interaction)
    
    async def _create_pathway_relationship(self, 
                                         molecule_id: str, 
                                         pathway: Dict[str, Any]) -> None:
        """
        Create a pathway node and relationship to a molecule.
        
        Args:
            molecule_id: Molecule node ID
            pathway: Pathway information
        """
        if not pathway.get('id'):
            return
            
        # Create the pathway node if it doesn't exist
        query = """
        MERGE (p:Pathway {id: $pathway_id})
        ON CREATE SET p.name = $name, 
                      p.source = $source,
                      p.created = timestamp()
        SET p.last_updated = timestamp()
        
        WITH p
        MATCH (m:Molecule {id: $molecule_id})
        MERGE (m)-[r:PARTICIPATES_IN]->(p)
        SET r.last_updated = timestamp()
        RETURN p.id
        """
        
        params = {
            'pathway_id': pathway.get('id'),
            'name': pathway.get('name', pathway.get('id')),
            'source': pathway.get('source', 'unknown'),
            'molecule_id': molecule_id
        }
        
        async with self.driver.session() as session:
            await session.run(query, **params)
    
    async def _create_interaction_relationship(self, 
                                             molecule_id: str, 
                                             interaction: Dict[str, Any]) -> None:
        """
        Create an interaction relationship between molecules.
        
        Args:
            molecule_id: Source molecule node ID
            interaction: Interaction information including target
        """
        # Find the target molecule
        target_id = await self._find_molecule_by_identifiers(
            {interaction.get('id_type', 'id'): interaction['target_id']}
        )
        
        if not target_id:
            # Target molecule doesn't exist in our database yet
            # Could retrieve it from external sources, but for now we'll skip
            return
            
        # Create the interaction relationship
        query = """
        MATCH (a:Molecule {id: $source_id}), (b:Molecule {id: $target_id})
        MERGE (a)-[r:INTERACTS_WITH]->(b)
        SET r.interaction_type = $interaction_type,
            r.mechanism = $mechanism,
            r.source = $source,
            r.last_updated = timestamp()
        RETURN r
        """
        
        params = {
            'source_id': molecule_id,
            'target_id': target_id,
            'interaction_type': interaction.get('type', 'unknown'),
            'mechanism': interaction.get('mechanism', ''),
            'source': interaction.get('source', 'unknown')
        }
        
        async with self.driver.session() as session:
            await session.run(query, **params)
    
    async def get_molecule_by_id(self, molecule_id: str) -> Dict[str, Any]:
        """
        Get molecule data from the database by ID.
        
        Args:
            molecule_id: Database ID of the molecule
            
        Returns:
            Dictionary with molecule data
        """
        query = """
        MATCH (m:Molecule {id: $id})
        RETURN m
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, id=molecule_id)
            record = await result.single()
            if record:
                return dict(record['m'])
            return None
    
    async def get_molecule_neighborhood(self, 
                                      molecule_id: str, 
                                      relationship_types: List[str] = None,
                                      max_depth: int = 2,
                                      limit: int = 100) -> Dict[str, Any]:
        """
        Get the neighborhood of a molecule in the graph.
        
        Args:
            molecule_id: Database ID of the molecule
            relationship_types: Types of relationships to traverse
            max_depth: Maximum traversal depth
            limit: Maximum number of nodes to return
            
        Returns:
            Dictionary with nodes and edges forming the neighborhood
        """
        # Default relationship types if not specified
        if relationship_types is None:
            relationship_types = ["SIMILAR_TO", "PARTICIPATES_IN", "INTERACTS_WITH"]
        
        # Build the relationship filter
        rel_filter = " | ".join([f":{rel_type}" for rel_type in relationship_types])
        
        query = f"""
        MATCH path = (m:Molecule {{id: $id}})-[{rel_filter}*1..{max_depth}]-(related)
        WITH m, path, related
        LIMIT $limit
        RETURN 
            collect(distinct m) + collect(distinct related) as nodes,
            collect(distinct relationships(path)) as edges
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, id=molecule_id, limit=limit)
            record = await result.single()
            
            if not record:
                return {"nodes": [], "edges": []}
                
            # Process nodes
            nodes = []
            for node in record['nodes']:
                node_data = dict(node)
                node_data['labels'] = list(node.labels)
                nodes.append(node_data)
                
            # Process edges (flatten the list of lists)
            all_edges = [edge for edge_list in record['edges'] for edge in edge_list]
            edges = []
            for edge in all_edges:
                edge_data = {
                    'id': edge.id,
                    'source': edge.start_node.id,
                    'target': edge.end_node.id,
                    'type': edge.type,
                    **dict(edge)
                }
                edges.append(edge_data)
                
            return {
                "nodes": nodes,
                "edges": edges
            }
    
    async def get_molecules_by_property(self, 
                                       property_name: str, 
                                       property_value: Any,
                                       limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get molecules that have a specific property value.
        
        Args:
            property_name: Name of the property
            property_value: Value to match
            limit: Maximum number of results
            
        Returns:
            List of molecule data dictionaries
        """
        query = """
        MATCH (m:Molecule)
        WHERE m[$property_name] = $property_value
        RETURN m
        LIMIT $limit
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, 
                                      property_name=property_name,
                                      property_value=property_value,
                                      limit=limit)
            
            molecules = []
            async for record in result:
                molecule = dict(record['m'])
                molecules.append(molecule)
                
            return molecules
    
    async def search_molecules(self, 
                             query: str, 
                             limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for molecules by name, formula, or identifier.
        
        Args:
            query: Search string
            limit: Maximum number of results
            
        Returns:
            List of molecule data dictionaries
        """
        cypher_query = """
        MATCH (m:Molecule)
        WHERE 
            toLower(m.name) CONTAINS toLower($query)
            OR m.formula = $query
            OR m.inchikey = $query
            OR m.smiles = $query
            OR m.inchi CONTAINS $query
        RETURN m
        ORDER BY 
            CASE 
                WHEN toLower(m.name) = toLower($query) THEN 0
                WHEN toLower(m.name) STARTS WITH toLower($query) THEN 1
                WHEN m.formula = $query THEN 2
                WHEN m.inchikey = $query THEN 3
                ELSE 4
            END
        LIMIT $limit
        """
        
        async with self.driver.session() as session:
            result = await session.run(cypher_query, query=query, limit=limit)
            
            molecules = []
            async for record in result:
                molecule = dict(record['m'])
                molecules.append(molecule)
                
            return molecules
    
    async def get_evidence_summary(self, molecule_id: str) -> Dict[str, Any]:
        """
        Get a summary of evidence for a molecule's identity.
        
        Args:
            molecule_id: Database ID of the molecule
            
        Returns:
            Dictionary with evidence summary
        """
        # Get molecule base data
        molecule = await self.get_molecule_by_id(molecule_id)
        if not molecule:
            return None
            
        # Get evidence sources referenced in the database
        query = """
        MATCH (m:Molecule {id: $id})
        RETURN m.evidence_sources as sources
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, id=molecule_id)
            record = await result.single()
            
            if not record or not record['sources']:
                return {'molecule': molecule, 'evidence': []}
                
            # Parse evidence sources
            sources = record['sources']
            if isinstance(sources, str):
                try:
                    sources = eval(sources)  # Convert string representation of list back to list
                except:
                    sources = [sources]
            
            # Get evidence from each source
            evidence = []
            for source in sources:
                if source in molecule_id:
                    continue  # Skip if it's the same as the ID (to avoid recursion)
                    
                evidence_item = {
                    'source': source,
                    'identifiers': {},
                    'properties': {},
                    'confidence': 0.0
                }
                
                # Extract source-specific identifiers and properties
                for key, value in molecule.items():
                    if key.startswith(f"{source}_"):
                        prop_name = key[len(source)+1:]
                        if prop_name.endswith('id') or prop_name in ['inchikey', 'inchi', 'smiles']:
                            evidence_item['identifiers'][prop_name] = value
                        else:
                            evidence_item['properties'][prop_name] = value
                
                # Calculate confidence based on number of matched identifiers and properties
                id_count = len(evidence_item['identifiers'])
                prop_count = len(evidence_item['properties'])
                
                # Simple confidence score formula
                evidence_item['confidence'] = min(1.0, (id_count * 0.3 + prop_count * 0.1))
                
                evidence.append(evidence_item)
            
            return {
                'molecule': molecule,
                'evidence': evidence
            }

# Create a global instance that will be initialized with connection details later
molecule_network = None  # Type: MoleculeNetworkBuilder 