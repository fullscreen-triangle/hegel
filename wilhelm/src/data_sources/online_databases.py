# Online Database Integration for SBML and Pathway Data
import requests
import json
import os
import tempfile
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
import time

class BiologicalDatabaseClient:
    """
    Client for accessing online biological databases and SBML models
    """
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or tempfile.mkdtemp(prefix="wilhelm_cache_")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Database endpoints
        self.endpoints = {
            'bigg_models': 'http://bigg.ucsd.edu/api/v2/',
            'biomodels': 'https://www.ebi.ac.uk/biomodels/',
            'reactome': 'https://reactome.org/ContentService/',
            'kegg': 'https://rest.kegg.jp/',
            'chebi': 'https://www.ebi.ac.uk/webservices/chebi/2.0/webservice',
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Wilhelm-Hegel-Framework/1.0.0',
            'Accept': 'application/json'
        })
    
    def search_bigg_models(self, query: str = None, organism: str = None) -> List[Dict]:
        """Search BiGG Models database for SBML models"""
        print(f"Searching BiGG Models database...")
        
        url = urljoin(self.endpoints['bigg_models'], 'models')
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            models = response.json().get('results', [])
            
            # Filter by query or organism if specified
            if query or organism:
                filtered_models = []
                for model in models:
                    match = True
                    if query and query.lower() not in model.get('bigg_id', '').lower():
                        if query.lower() not in model.get('metabolite_count', ''):
                            match = False
                    if organism and organism.lower() not in model.get('organism', '').lower():
                        match = False
                    
                    if match:
                        filtered_models.append(model)
                
                models = filtered_models
            
            print(f"Found {len(models)} models in BiGG database")
            return models[:10]  # Limit to top 10 for performance
            
        except Exception as e:
            print(f"Error searching BiGG Models: {e}")
            return []
    
    def download_bigg_model(self, model_id: str) -> Optional[str]:
        """Download SBML model from BiGG Models"""
        print(f"Downloading BiGG model: {model_id}")
        
        # Check cache first
        cache_file = os.path.join(self.cache_dir, f"bigg_{model_id}.xml")
        if os.path.exists(cache_file):
            print(f"Using cached model: {cache_file}")
            return cache_file
        
        url = urljoin(self.endpoints['bigg_models'], f'models/{model_id}/download')
        
        try:
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            
            # Save to cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"Downloaded and cached: {cache_file}")
            return cache_file
            
        except Exception as e:
            print(f"Error downloading BiGG model {model_id}: {e}")
            return None
    
    def search_biomodels(self, query: str = None, max_results: int = 10) -> List[Dict]:
        """Search BioModels database"""
        print(f"Searching BioModels database...")
        
        # BioModels REST API
        base_url = "https://www.ebi.ac.uk/biomodels/search"
        
        params = {
            'query': query or '*',
            'format': 'json',
            'numResults': max_results
        }
        
        try:
            response = self.session.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            models = data.get('models', [])
            
            print(f"Found {len(models)} models in BioModels database")
            return models
            
        except Exception as e:
            print(f"Error searching BioModels: {e}")
            # Fallback to predefined list of popular models
            return self.get_popular_biomodels()
    
    def get_popular_biomodels(self) -> List[Dict]:
        """Get list of popular/example BioModels"""
        popular_models = [
            {'id': 'BIOMD0000000001', 'name': 'Edelstein1996 - EPSP ACh event'},
            {'id': 'BIOMD0000000010', 'name': 'Kholodenko1999 - EGF MAPK'},
            {'id': 'BIOMD0000000012', 'name': 'Elowitz2000 - Repressilator'},
            {'id': 'BIOMD0000000021', 'name': 'Tyson1991 - Cell Cycle'},
            {'id': 'BIOMD0000000028', 'name': 'Locke2005 - Circadian Clock'},
        ]
        return popular_models
    
    def download_biomodel(self, model_id: str) -> Optional[str]:
        """Download SBML model from BioModels"""
        print(f"Downloading BioModel: {model_id}")
        
        # Check cache first
        cache_file = os.path.join(self.cache_dir, f"biomodel_{model_id}.xml")
        if os.path.exists(cache_file):
            print(f"Using cached model: {cache_file}")
            return cache_file
        
        # BioModels download URL
        url = f"https://www.ebi.ac.uk/biomodels/model/download/{model_id}?filename={model_id}_url.xml"
        
        try:
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            
            # Validate it's XML content
            try:
                ET.fromstring(response.text)
            except ET.ParseError:
                print(f"Invalid XML content for model {model_id}")
                return None
            
            # Save to cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"Downloaded and cached: {cache_file}")
            return cache_file
            
        except Exception as e:
            print(f"Error downloading BioModel {model_id}: {e}")
            return None
    
    def search_reactome_pathways(self, species: str = "Homo sapiens", 
                                max_results: int = 5) -> List[Dict]:
        """Search Reactome pathways"""
        print(f"Searching Reactome pathways for {species}...")
        
        # Get top-level pathways for species
        url = urljoin(self.endpoints['reactome'], f'data/pathways/top/{species}')
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            pathways = response.json()[:max_results]
            
            print(f"Found {len(pathways)} top pathways in Reactome")
            return pathways
            
        except Exception as e:
            print(f"Error searching Reactome: {e}")
            return []
    
    def get_reactome_sbml(self, pathway_id: str) -> Optional[str]:
        """Get SBML representation of Reactome pathway"""
        print(f"Getting Reactome SBML for pathway: {pathway_id}")
        
        # Check cache first
        cache_file = os.path.join(self.cache_dir, f"reactome_{pathway_id}.xml")
        if os.path.exists(cache_file):
            print(f"Using cached pathway: {cache_file}")
            return cache_file
        
        # Reactome SBML export (if available)
        url = urljoin(self.endpoints['reactome'], f'exporter/sbml/{pathway_id}.xml')
        
        try:
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            
            # Validate XML
            try:
                ET.fromstring(response.text)
            except ET.ParseError:
                print(f"Invalid SBML content for pathway {pathway_id}")
                return None
            
            # Save to cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"Downloaded and cached: {cache_file}")
            return cache_file
            
        except Exception as e:
            print(f"Error getting Reactome SBML {pathway_id}: {e}")
            return None
    
    def create_example_sbml(self, model_name: str = "example_glycolysis") -> str:
        """Create a simple example SBML model for testing"""
        print(f"Creating example SBML model: {model_name}")
        
        cache_file = os.path.join(self.cache_dir, f"{model_name}.xml")
        
        # Simple glycolysis pathway SBML
        sbml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" level="3" version="1">
  <model id="glycolysis_example" name="Simple Glycolysis">
    
    <listOfCompartments>
      <compartment id="cytoplasm" name="Cytoplasm" size="1" constant="true"/>
    </listOfCompartments>
    
    <listOfSpecies>
      <species id="glucose" name="Glucose" compartment="cytoplasm" initialConcentration="10" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
      <species id="g6p" name="Glucose-6-phosphate" compartment="cytoplasm" initialConcentration="0" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
      <species id="f6p" name="Fructose-6-phosphate" compartment="cytoplasm" initialConcentration="0" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
      <species id="fbp" name="Fructose-1,6-bisphosphate" compartment="cytoplasm" initialConcentration="0" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
      <species id="pyruvate" name="Pyruvate" compartment="cytoplasm" initialConcentration="0" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
      <species id="atp" name="ATP" compartment="cytoplasm" initialConcentration="5" hasOnlySubstanceUnits="false" boundaryCondition="true" constant="false"/>
      <species id="adp" name="ADP" compartment="cytoplasm" initialConcentration="1" hasOnlySubstanceUnits="false" boundaryCondition="true" constant="false"/>
    </listOfSpecies>
    
    <listOfParameters>
      <parameter id="k1" name="Hexokinase rate" value="0.1" constant="true"/>
      <parameter id="k2" name="PGI rate" value="0.2" constant="true"/>
      <parameter id="k3" name="PFK rate" value="0.15" constant="true"/>
      <parameter id="k4" name="Aldolase rate" value="0.3" constant="true"/>
    </listOfParameters>
    
    <listOfReactions>
      <reaction id="hexokinase" name="Hexokinase" reversible="false">
        <listOfReactants>
          <speciesReference species="glucose" stoichiometry="1"/>
          <speciesReference species="atp" stoichiometry="1"/>
        </listOfReactants>
        <listOfProducts>
          <speciesReference species="g6p" stoichiometry="1"/>
          <speciesReference species="adp" stoichiometry="1"/>
        </listOfProducts>
        <kineticLaw>
          <math xmlns="http://www.w3.org/1998/Math/MathML">
            <apply>
              <times/>
              <ci>k1</ci>
              <ci>glucose</ci>
              <ci>atp</ci>
            </apply>
          </math>
        </kineticLaw>
      </reaction>
      
      <reaction id="pgi" name="Phosphoglucose isomerase" reversible="true">
        <listOfReactants>
          <speciesReference species="g6p" stoichiometry="1"/>
        </listOfReactants>
        <listOfProducts>
          <speciesReference species="f6p" stoichiometry="1"/>
        </listOfProducts>
        <kineticLaw>
          <math xmlns="http://www.w3.org/1998/Math/MathML">
            <apply>
              <times/>
              <ci>k2</ci>
              <ci>g6p</ci>
            </apply>
          </math>
        </kineticLaw>
      </reaction>
      
      <reaction id="pfk" name="Phosphofructokinase" reversible="false">
        <listOfReactants>
          <speciesReference species="f6p" stoichiometry="1"/>
          <speciesReference species="atp" stoichiometry="1"/>
        </listOfReactants>
        <listOfProducts>
          <speciesReference species="fbp" stoichiometry="1"/>
          <speciesReference species="adp" stoichiometry="1"/>
        </listOfProducts>
        <kineticLaw>
          <math xmlns="http://www.w3.org/1998/Math/MathML">
            <apply>
              <times/>
              <ci>k3</ci>
              <ci>f6p</ci>
              <ci>atp</ci>
            </apply>
          </math>
        </kineticLaw>
      </reaction>
      
      <reaction id="to_pyruvate" name="To Pyruvate" reversible="false">
        <listOfReactants>
          <speciesReference species="fbp" stoichiometry="1"/>
        </listOfReactants>
        <listOfProducts>
          <speciesReference species="pyruvate" stoichiometry="2"/>
        </listOfProducts>
        <kineticLaw>
          <math xmlns="http://www.w3.org/1998/Math/MathML">
            <apply>
              <times/>
              <ci>k4</ci>
              <ci>fbp</ci>
            </apply>
          </math>
        </kineticLaw>
      </reaction>
    </listOfReactions>
    
  </model>
</sbml>'''
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(sbml_content)
        
        print(f"Created example SBML: {cache_file}")
        return cache_file
    
    def get_available_models(self, source: str = "all", max_per_source: int = 3) -> List[Dict]:
        """Get available models from all sources"""
        print("Fetching available models from online databases...")
        
        available_models = []
        
        if source in ["all", "bigg"]:
            try:
                bigg_models = self.search_bigg_models()[:max_per_source]
                for model in bigg_models:
                    available_models.append({
                        'source': 'bigg',
                        'id': model.get('bigg_id'),
                        'name': model.get('bigg_id'),
                        'organism': model.get('organism'),
                        'description': f"BiGG Model: {model.get('organism')} - {model.get('metabolite_count', 0)} metabolites"
                    })
            except Exception as e:
                print(f"Error fetching BiGG models: {e}")
        
        if source in ["all", "biomodels"]:
            try:
                biomodels = self.search_biomodels(max_results=max_per_source)
                for model in biomodels:
                    available_models.append({
                        'source': 'biomodels',
                        'id': model.get('id'),
                        'name': model.get('name', model.get('id')),
                        'description': f"BioModel: {model.get('name', 'Unknown')}"
                    })
            except Exception as e:
                print(f"Error fetching BioModels: {e}")
        
        # Always add example model as fallback
        available_models.append({
            'source': 'example',
            'id': 'example_glycolysis',
            'name': 'Example Glycolysis Pathway',
            'description': 'Simple glycolysis pathway for testing'
        })
        
        print(f"Found {len(available_models)} available models")
        return available_models
    
    def download_model(self, source: str, model_id: str) -> Optional[str]:
        """Download model from specified source"""
        print(f"Downloading model {model_id} from {source}...")
        
        if source == 'bigg':
            return self.download_bigg_model(model_id)
        elif source == 'biomodels':
            return self.download_biomodel(model_id)
        elif source == 'example':
            return self.create_example_sbml(model_id)
        else:
            print(f"Unknown source: {source}")
            return None
    
    def cleanup_cache(self):
        """Clean up cached files"""
        import shutil
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            print(f"Cleaned up cache directory: {self.cache_dir}")

def get_online_model(model_source: str = None, model_id: str = None) -> Optional[str]:
    """
    Convenience function to get an online model
    
    Args:
        model_source: 'bigg', 'biomodels', 'example', or None for auto-select
        model_id: Specific model ID, or None for auto-select
        
    Returns:
        Path to downloaded SBML file
    """
    
    client = BiologicalDatabaseClient()
    
    try:
        if model_source and model_id:
            # Download specific model
            return client.download_model(model_source, model_id)
        else:
            # Auto-select first available model
            available_models = client.get_available_models(max_per_source=1)
            
            if available_models:
                model = available_models[0]
                print(f"Auto-selecting model: {model['name']} from {model['source']}")
                return client.download_model(model['source'], model['id'])
            else:
                print("No models available, creating example")
                return client.create_example_sbml()
    
    except Exception as e:
        print(f"Error getting online model: {e}")
        print("Falling back to example model")
        return client.create_example_sbml()

# Usage example
if __name__ == "__main__":
    client = BiologicalDatabaseClient()
    
    # List available models
    models = client.get_available_models()
    print(f"\nAvailable models ({len(models)}):")
    for i, model in enumerate(models):
        print(f"  {i+1}. [{model['source']}] {model['name']}")
        print(f"     {model['description']}")
    
    # Download first model
    if models:
        first_model = models[0]
        sbml_file = client.download_model(first_model['source'], first_model['id'])
        print(f"\nDownloaded: {sbml_file}")
    
    # Cleanup
    client.cleanup_cache()
