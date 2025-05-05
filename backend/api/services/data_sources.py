"""
Data integration services for retrieving molecular information from external databases.
This module provides a unified interface for accessing multiple cheminformatics resources.
"""

import os
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional, Union
import logging
import json
from rdkit import Chem
from rdkit.Chem import Descriptors, AllChem
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DataSourceManager:
    """Manages connections to external biochemical and systems biology databases."""
    
    def __init__(self):
        """Initialize the data source manager with API keys from environment variables."""
        self.api_keys = {
            'pubchem': os.getenv('PUBCHEM_API_KEY', ''),
            'chembl': os.getenv('CHEMBL_API_KEY', ''),
            'kegg': os.getenv('KEGG_API_KEY', ''),
            'drugbank': os.getenv('DRUGBANK_API_KEY', ''),
            'hmdb': os.getenv('HMDB_API_KEY', ''),
            'uniprot': os.getenv('UNIPROT_API_KEY', ''),
            'reactome': os.getenv('REACTOME_API_KEY', '')
        }
        self.session = None
        
    async def __aenter__(self):
        """Set up an aiohttp session for async requests."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_molecule_by_id(self, 
                                identifier: str, 
                                source: str = 'pubchem',
                                include_sources: List[str] = None) -> Dict[str, Any]:
        """
        Retrieve molecule information from specified source database.
        
        Args:
            identifier: Molecule identifier (depends on source database)
            source: Primary database to query
            include_sources: Additional databases to query
            
        Returns:
            Dictionary with aggregated molecule information
        """
        if self.session is None:
            self.session = aiohttp.ClientSession()
            
        # Start with the primary source
        result = await self._get_from_source(identifier, source)
        
        # Add data from additional sources if specified
        if include_sources:
            for additional_source in include_sources:
                if additional_source != source:
                    try:
                        additional_data = await self._get_from_source(identifier, additional_source)
                        if additional_data:
                            # Add source name to the data
                            source_data = {f"{additional_source}_{k}": v for k, v in additional_data.items() 
                                           if k not in ['id', 'name', 'formula']}
                            result.update(source_data)
                            
                            # If primary source is missing basic info, use this source
                            if 'name' not in result and 'name' in additional_data:
                                result['name'] = additional_data['name']
                            if 'formula' not in result and 'formula' in additional_data:
                                result['formula'] = additional_data['formula']
                    except Exception as e:
                        logger.warning(f"Error retrieving data from {additional_source}: {str(e)}")
        
        # Add evidence source information
        if result:
            result['evidence_sources'] = [source] + (include_sources or [])
            
        return result
    
    async def _get_from_source(self, identifier: str, source: str) -> Dict[str, Any]:
        """Retrieve molecule data from a specific source."""
        handler = getattr(self, f"_get_from_{source}", None)
        
        if handler is None:
            logger.warning(f"No handler available for source: {source}")
            return {}
            
        try:
            return await handler(identifier)
        except Exception as e:
            logger.error(f"Error retrieving from {source}: {str(e)}")
            return {}
    
    async def _get_from_pubchem(self, identifier: str) -> Dict[str, Any]:
        """Retrieve molecule data from PubChem."""
        # Try to determine identifier type
        id_type = self._determine_pubchem_id_type(identifier)
        
        base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        url = f"{base_url}/{id_type}/{identifier}/JSON"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return self._parse_pubchem_response(data)
            else:
                logger.warning(f"PubChem returned status {response.status} for {identifier}")
                return {}
    
    def _determine_pubchem_id_type(self, identifier: str) -> str:
        """Determine the type of PubChem identifier."""
        if identifier.isdigit():
            return "compound/cid"
        elif identifier.startswith("CID:"):
            return "compound/cid"
        elif identifier.startswith("SID:"):
            return "substance/sid"
        else:
            # Assume it's a name/smiles/inchi
            return "compound/name"
    
    def _parse_pubchem_response(self, data: Dict) -> Dict[str, Any]:
        """Parse PubChem API response."""
        try:
            if 'PC_Compounds' in data:
                compound = data['PC_Compounds'][0]
                result = {
                    'id': str(compound['id']['id']['cid']),
                    'source': 'pubchem',
                    'name': self._extract_pubchem_name(compound),
                    'formula': self._extract_pubchem_property(compound, 'Molecular Formula'),
                    'molecular_weight': self._extract_pubchem_property(compound, 'Molecular Weight'),
                    'canonical_smiles': self._extract_pubchem_property(compound, 'SMILES', 'Canonical'),
                    'inchi': self._extract_pubchem_property(compound, 'InChI'),
                    'inchikey': self._extract_pubchem_property(compound, 'InChIKey'),
                    'xlogp': self._extract_pubchem_property(compound, 'XLogP'),
                    'charge': self._extract_pubchem_property(compound, 'Formal Charge'),
                    'complexity': self._extract_pubchem_property(compound, 'Complexity'),
                    'h_bond_donor_count': self._extract_pubchem_property(compound, 'Count', 'H-Bond Donor'),
                    'h_bond_acceptor_count': self._extract_pubchem_property(compound, 'Count', 'H-Bond Acceptor'),
                    'rotatable_bond_count': self._extract_pubchem_property(compound, 'Count', 'Rotatable Bond'),
                    'heavy_atom_count': self._extract_pubchem_property(compound, 'Count', 'Heavy Atom'),
                    'isotope_atom_count': self._extract_pubchem_property(compound, 'Count', 'Isotope Atom'),
                    'atom_stereo_count': self._extract_pubchem_property(compound, 'Count', 'Atom Stereo Center'),
                    'defined_atom_stereo_count': self._extract_pubchem_property(compound, 'Count', 'Defined Atom Stereo Center'),
                    'undefined_atom_stereo_count': self._extract_pubchem_property(compound, 'Count', 'Undefined Atom Stereo Center'),
                    'bond_stereo_count': self._extract_pubchem_property(compound, 'Count', 'Bond Stereo Center'),
                    'defined_bond_stereo_count': self._extract_pubchem_property(compound, 'Count', 'Defined Bond Stereo Center'),
                    'undefined_bond_stereo_count': self._extract_pubchem_property(compound, 'Count', 'Undefined Bond Stereo Center'),
                    'tautomer_count': self._extract_pubchem_property(compound, 'Count', 'Tautomers')
                }
                return {k: v for k, v in result.items() if v is not None}
            return {}
        except Exception as e:
            logger.error(f"Error parsing PubChem data: {str(e)}")
            return {}
    
    def _extract_pubchem_name(self, compound: Dict) -> Optional[str]:
        """Extract compound name from PubChem data."""
        if 'synonyms' in compound and compound['synonyms']:
            for syn_type in ['Preferred', 'Traditional', 'Systematic']:
                for syn in compound['synonyms']:
                    if syn_type in syn and syn[syn_type]:
                        return syn[syn_type][0]
            # If no preferred names found, return first synonym
            return compound['synonyms'][0][list(compound['synonyms'][0].keys())[0]][0]
        return None
    
    def _extract_pubchem_property(self, compound: Dict, prop_name: str, subtype: str = None) -> Any:
        """Extract a specific property from PubChem data."""
        if 'props' not in compound:
            return None
            
        for prop in compound['props']:
            if prop['urn']['label'] == prop_name:
                if subtype and 'urn' in prop and 'name' in prop['urn'] and prop['urn']['name'] != subtype:
                    continue
                
                if 'value' in prop:
                    if prop['value']['sval']:
                        return prop['value']['sval']
                    elif 'ival' in prop['value']:
                        return prop['value']['ival']
                    elif 'fval' in prop['value']:
                        return prop['value']['fval']
        return None
    
    async def _get_from_chembl(self, identifier: str) -> Dict[str, Any]:
        """Retrieve molecule data from ChEMBL."""
        # First, try to get ChEMBL ID if identifier is not already a ChEMBL ID
        chembl_id = identifier
        if not identifier.startswith("CHEMBL"):
            chembl_id = await self._resolve_chembl_id(identifier)
            if not chembl_id:
                return {}
        
        url = f"https://www.ebi.ac.uk/chembl/api/data/molecule/{chembl_id}.json"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return self._parse_chembl_response(data)
            else:
                logger.warning(f"ChEMBL returned status {response.status} for {identifier}")
                return {}
    
    async def _resolve_chembl_id(self, identifier: str) -> Optional[str]:
        """Resolve an identifier to a ChEMBL ID."""
        # Try different search strategies
        # 1. Try as a molecule name
        url = f"https://www.ebi.ac.uk/chembl/api/data/molecule.json?molecule_synonyms__synonym__iexact={identifier}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data['molecules'] and len(data['molecules']) > 0:
                    return data['molecules'][0]['molecule_chembl_id']
        
        # 2. Try as InChI or SMILES
        if identifier.startswith("InChI=") or "/" in identifier:
            search_type = "molecule_structures__standard_inchi__exact" 
        else:
            search_type = "molecule_structures__canonical_smiles__exact"
        
        url = f"https://www.ebi.ac.uk/chembl/api/data/molecule.json?{search_type}={identifier}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data['molecules'] and len(data['molecules']) > 0:
                    return data['molecules'][0]['molecule_chembl_id']
        
        return None
    
    def _parse_chembl_response(self, data: Dict) -> Dict[str, Any]:
        """Parse ChEMBL API response."""
        try:
            molecule = data
            
            result = {
                'id': molecule['molecule_chembl_id'],
                'source': 'chembl',
                'name': molecule.get('pref_name'),
                'formula': molecule.get('molecule_properties', {}).get('full_molformula'),
                'max_phase': molecule.get('max_phase'),
                'molecular_weight': molecule.get('molecule_properties', {}).get('full_mwt'),
                'alogp': molecule.get('molecule_properties', {}).get('alogp'),
                'psa': molecule.get('molecule_properties', {}).get('psa'),
                'hba': molecule.get('molecule_properties', {}).get('hba'),
                'hbd': molecule.get('molecule_properties', {}).get('hbd'),
                'ro5_violations': molecule.get('molecule_properties', {}).get('num_ro5_violations'),
                'canonical_smiles': molecule.get('molecule_structures', {}).get('canonical_smiles'),
                'standard_inchi': molecule.get('molecule_structures', {}).get('standard_inchi'),
                'standard_inchikey': molecule.get('molecule_structures', {}).get('standard_inchi_key'),
                'therapeutic_flag': molecule.get('therapeutic_flag', False),
                'oral': molecule.get('oral', False),
                'parenteral': molecule.get('parenteral', False),
                'topical': molecule.get('topical', False),
                'black_box_warning': molecule.get('black_box_warning', False),
                'natural_product': molecule.get('natural_product', False),
                'is_prodrug': molecule.get('molecule_properties', {}).get('is_prodrug', False)
            }
            
            # Add drug indications if available
            if 'indication_class' in molecule and molecule['indication_class']:
                result['indication_class'] = molecule['indication_class']

            return {k: v for k, v in result.items() if v is not None}
        except Exception as e:
            logger.error(f"Error parsing ChEMBL data: {str(e)}")
            return {}
    
    async def _get_from_kegg(self, identifier: str) -> Dict[str, Any]:
        """Retrieve molecule data from KEGG."""
        # KEGG API endpoints
        url = f"http://rest.kegg.jp/get/{identifier}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                text = await response.text()
                return self._parse_kegg_response(text)
            else:
                logger.warning(f"KEGG returned status {response.status} for {identifier}")
                return {}
                
    def _parse_kegg_response(self, text: str) -> Dict[str, Any]:
        """Parse KEGG flat file response."""
        try:
            result = {'source': 'kegg'}
            current_section = None
            
            lines = text.strip().split('\n')
            for line in lines:
                if not line.strip():
                    continue
                    
                if not line.startswith(' '):
                    # New section
                    parts = line.split(' ', 1)
                    current_section = parts[0]
                    value = parts[1].strip() if len(parts) > 1 else ""
                    
                    if current_section == 'ENTRY':
                        result['id'] = value.split()[0]
                    elif current_section == 'NAME':
                        result['name'] = value
                    elif current_section == 'FORMULA':
                        result['formula'] = value
                    elif current_section == 'EXACT_MASS':
                        result['exact_mass'] = float(value)
                    elif current_section == 'MOL_WEIGHT':
                        result['molecular_weight'] = float(value)
                    elif current_section == 'REMARK':
                        result['remark'] = value
                    elif current_section == 'PATHWAY':
                        result['pathways'] = [value]
                else:
                    # Continuation of previous section
                    value = line.strip()
                    if current_section == 'PATHWAY' and 'pathways' in result:
                        result['pathways'].append(value)
                        
            return result
        except Exception as e:
            logger.error(f"Error parsing KEGG data: {str(e)}")
            return {}
    
    async def _get_from_hmdb(self, identifier: str) -> Dict[str, Any]:
        """Retrieve molecule data from Human Metabolome Database."""
        # HMDB requires XML parsing, using the public API
        if not identifier.startswith("HMDB"):
            # Try to resolve to HMDB ID
            hmdb_id = await self._resolve_hmdb_id(identifier)
            if not hmdb_id:
                return {}
            identifier = hmdb_id
        
        url = f"http://www.hmdb.ca/metabolites/{identifier}.xml"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                text = await response.text()
                # Parse XML (simplified for example)
                return self._parse_hmdb_response(text)
            else:
                logger.warning(f"HMDB returned status {response.status} for {identifier}")
                return {}
    
    async def _resolve_hmdb_id(self, identifier: str) -> Optional[str]:
        """Resolve an identifier to an HMDB ID."""
        # Try to search HMDB
        url = f"http://www.hmdb.ca/unearth/q?utf8=%E2%9C%93&query={identifier}&searcher=metabolites"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                text = await response.text()
                # This is a simplification - in reality would need HTML parsing
                hmdb_match = text.find("/metabolites/HMDB")
                if hmdb_match > -1:
                    start = hmdb_match + 12  # len("/metabolites/")
                    end = text.find('"', start)
                    return text[start:end]
        return None
    
    def _parse_hmdb_response(self, text: str) -> Dict[str, Any]:
        """Parse HMDB XML response."""
        # This is a simplified version - would normally use XML parsing
        try:
            # Simple extraction of key elements
            result = {'source': 'hmdb'}
            
            # Extract key fields (simplified)
            result['id'] = self._extract_xml_value(text, 'accession')
            result['name'] = self._extract_xml_value(text, 'name')
            result['formula'] = self._extract_xml_value(text, 'chemical_formula')
            result['monisotopic_mass'] = self._extract_xml_value(text, 'monisotopic_molecular_weight')
            result['smiles'] = self._extract_xml_value(text, 'smiles')
            result['inchi'] = self._extract_xml_value(text, 'inchi')
            result['inchikey'] = self._extract_xml_value(text, 'inchikey')
            
            # Biological properties
            result['biofunction'] = self._extract_xml_value(text, 'biofunction')
            result['cellular_locations'] = self._extract_xml_value(text, 'cellular_locations')
            result['pathways'] = self._extract_xml_list(text, 'pathway')
            result['diseases'] = self._extract_xml_list(text, 'disease')
            
            return {k: v for k, v in result.items() if v}
        except Exception as e:
            logger.error(f"Error parsing HMDB data: {str(e)}")
            return {}
    
    def _extract_xml_value(self, text: str, tag: str) -> Optional[str]:
        """Extract a value from XML text."""
        start_tag = f"<{tag}>"
        end_tag = f"</{tag}>"
        start = text.find(start_tag)
        if start == -1:
            return None
        start += len(start_tag)
        end = text.find(end_tag, start)
        if end == -1:
            return None
        return text[start:end].strip()
    
    def _extract_xml_list(self, text: str, tag: str) -> List[str]:
        """Extract a list of values from XML text."""
        items = []
        start_pos = 0
        while True:
            start_tag = f"<{tag}>"
            end_tag = f"</{tag}>"
            start = text.find(start_tag, start_pos)
            if start == -1:
                break
            start += len(start_tag)
            end = text.find(end_tag, start)
            if end == -1:
                break
            items.append(text[start:end].strip())
            start_pos = end + len(end_tag)
        return items
    
    async def search_molecules(self, 
                              query: str, 
                              source: str = 'pubchem',
                              limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for molecules matching a query.
        
        Args:
            query: Search term
            source: Database to search
            limit: Maximum number of results
            
        Returns:
            List of matching molecules
        """
        if self.session is None:
            self.session = aiohttp.ClientSession()
            
        search_handler = getattr(self, f"_search_{source}", None)
        
        if search_handler is None:
            logger.warning(f"No search handler available for source: {source}")
            return []
            
        try:
            return await search_handler(query, limit)
        except Exception as e:
            logger.error(f"Error searching {source}: {str(e)}")
            return []
    
    async def _search_pubchem(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for molecules in PubChem."""
        base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name"
        url = f"{base_url}/{query}/cids/JSON"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if 'IdentifierList' in data and 'CID' in data['IdentifierList']:
                    cids = data['IdentifierList']['CID'][:limit]
                    results = []
                    
                    # Get details for each CID
                    for cid in cids:
                        molecule = await self._get_from_pubchem(str(cid))
                        if molecule:
                            results.append(molecule)
                    
                    return results
            return []
    
    async def _search_chembl(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for molecules in ChEMBL."""
        url = f"https://www.ebi.ac.uk/chembl/api/data/molecule/search.json?q={query}&limit={limit}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                results = []
                
                for molecule in data.get('molecules', [])[:limit]:
                    chembl_id = molecule.get('molecule_chembl_id')
                    if chembl_id:
                        molecule_data = await self._get_from_chembl(chembl_id)
                        if molecule_data:
                            results.append(molecule_data)
                
                return results
            return []
    
    async def get_molecule_interactions(self, identifier: str, source: str = 'drugbank') -> List[Dict[str, Any]]:
        """
        Get molecule interactions.
        
        Args:
            identifier: Molecule identifier
            source: Database to query
            
        Returns:
            List of interactions
        """
        if self.session is None:
            self.session = aiohttp.ClientSession()
            
        handler = getattr(self, f"_get_interactions_{source}", None)
        
        if handler is None:
            logger.warning(f"No interaction handler available for source: {source}")
            return []
            
        try:
            return await handler(identifier)
        except Exception as e:
            logger.error(f"Error getting interactions from {source}: {str(e)}")
            return []
    
    async def _get_interactions_drugbank(self, identifier: str) -> List[Dict[str, Any]]:
        """Get drug-drug interactions from DrugBank."""
        # NOTE: DrugBank requires registration and API key for access
        # This is a simplified version assuming credentials are available
        api_key = self.api_keys.get('drugbank')
        if not api_key:
            logger.warning("DrugBank API key not available")
            return []
        
        # Try to resolve DrugBank ID if not already provided
        drugbank_id = identifier
        if not identifier.startswith("DB"):
            # This would require subscription
            return []
        
        url = f"https://api.drugbank.com/v1/drug_interactions?drug_id={drugbank_id}"
        
        async with self.session.get(url, headers={"Authorization": f"Bearer {api_key}"}) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('interactions', [])
            else:
                logger.warning(f"DrugBank returned status {response.status} for {identifier}")
                return []
    
    async def get_molecule_pathways(self, identifier: str, source: str = 'kegg') -> List[Dict[str, Any]]:
        """
        Get pathways involving a molecule.
        
        Args:
            identifier: Molecule identifier
            source: Database to query
            
        Returns:
            List of pathways
        """
        if self.session is None:
            self.session = aiohttp.ClientSession()
            
        handler = getattr(self, f"_get_pathways_{source}", None)
        
        if handler is None:
            logger.warning(f"No pathway handler available for source: {source}")
            return []
            
        try:
            return await handler(identifier)
        except Exception as e:
            logger.error(f"Error getting pathways from {source}: {str(e)}")
            return []
    
    async def _get_pathways_kegg(self, identifier: str) -> List[Dict[str, Any]]:
        """Get pathways from KEGG."""
        # First, get compound information
        compound_data = await self._get_from_kegg(identifier)
        
        if not compound_data or 'pathways' not in compound_data:
            return []
        
        pathways = []
        for pathway_entry in compound_data['pathways']:
            # Extract pathway ID from entry
            parts = pathway_entry.split()
            if not parts:
                continue
            
            pathway_id = parts[0]
            
            # Get pathway details
            url = f"http://rest.kegg.jp/get/{pathway_id}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    
                    # Parse pathway information
                    name = None
                    description = None
                    
                    lines = text.strip().split('\n')
                    for line in lines:
                        if line.startswith('NAME'):
                            name = line.split(' ', 1)[1].strip()
                        elif line.startswith('DESCRIPTION'):
                            description = line.split(' ', 1)[1].strip()
                    
                    if name:
                        pathways.append({
                            'id': pathway_id,
                            'name': name,
                            'description': description,
                            'source': 'kegg'
                        })
        
        return pathways
    
    async def get_molecule_external_ids(self, identifier: str, source: str = 'pubchem') -> Dict[str, str]:
        """
        Get external database identifiers for a molecule.
        
        Args:
            identifier: Molecule identifier
            source: Source database
            
        Returns:
            Dictionary mapping database names to identifiers
        """
        if self.session is None:
            self.session = aiohttp.ClientSession()
            
        handler = getattr(self, f"_get_external_ids_{source}", None)
        
        if handler is None:
            logger.warning(f"No external ID handler available for source: {source}")
            return {}
            
        try:
            return await handler(identifier)
        except Exception as e:
            logger.error(f"Error getting external IDs from {source}: {str(e)}")
            return {}
    
    async def _get_external_ids_pubchem(self, identifier: str) -> Dict[str, str]:
        """Get external IDs from PubChem."""
        # First, ensure we have a CID
        if not identifier.isdigit() and not identifier.startswith("CID:"):
            # Resolve to CID
            url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{identifier}/cids/JSON"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'IdentifierList' in data and 'CID' in data['IdentifierList'] and data['IdentifierList']['CID']:
                        identifier = str(data['IdentifierList']['CID'][0])
                    else:
                        return {}
                else:
                    return {}
        
        # Strip "CID:" prefix if present
        if identifier.startswith("CID:"):
            identifier = identifier[4:]
        
        # Get external IDs
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{identifier}/xrefs/RegistryID,RN,HMDB,KEGG,ChEBI,ChEMBL,DrugBank/JSON"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                
                if 'InformationList' in data and 'Information' in data['InformationList']:
                    info = data['InformationList']['Information'][0]
                    
                    result = {
                        'pubchem_cid': identifier
                    }
                    
                    # Map the external IDs
                    if 'RegistryID' in info:
                        # CAS Registry Number typically
                        result['cas'] = info['RegistryID']
                    
                    if 'RN' in info:
                        # Another form of registry number
                        result['rn'] = info['RN']
                    
                    if 'HMDB' in info:
                        result['hmdb'] = info['HMDB']
                    
                    if 'KEGG' in info:
                        result['kegg'] = info['KEGG']
                    
                    if 'ChEBI' in info:
                        result['chebi'] = info['ChEBI']
                    
                    if 'ChEMBL' in info:
                        result['chembl'] = info['ChEMBL']
                    
                    if 'DrugBank' in info:
                        result['drugbank'] = info['DrugBank']
                    
                    return result
            
            return {}

# Create a global instance
data_source_manager = DataSourceManager() 