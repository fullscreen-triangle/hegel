/**
 * API Services for the Hegel platform
 * This module contains functions for communicating with the Hegel backend API
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080/api';

/**
 * Fetch molecules from the API
 * @returns {Promise<Array>} Array of molecule objects
 */
export async function fetchMolecules() {
  try {
    const response = await fetch(`${API_BASE_URL}/molecules`);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching molecules:', error);
    throw error;
  }
}

/**
 * Fetch details for a specific molecule
 * @param {string} id - Molecule ID
 * @returns {Promise<Object>} Molecule details
 */
export async function fetchMoleculeDetails(id) {
  try {
    const response = await fetch(`${API_BASE_URL}/molecules/${id}`);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`Error fetching molecule ${id}:`, error);
    throw error;
  }
}

/**
 * Validate a molecule
 * @param {Object} params - Validation parameters
 * @param {string} params.molecule - Molecule identifier (SMILES, InChI, etc.)
 * @param {string} params.idType - Type of identifier (smiles, inchi, name)
 * @param {number} params.threshold - Validation confidence threshold (0.0-1.0)
 * @returns {Promise<Object>} Validation results
 */
export async function validateMolecule({ molecule, idType = 'smiles', threshold = 0.5 }) {
  try {
    const response = await fetch(`${API_BASE_URL}/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        molecule,
        id_type: idType,
        threshold,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error validating molecule:', error);
    throw error;
  }
}

/**
 * Process a molecule to extract properties and relationships
 * @param {Object} params - Processing parameters
 * @param {string} params.molecule - Molecule identifier (SMILES, InChI, etc.)
 * @param {string} params.idType - Type of identifier (smiles, inchi, name)
 * @param {boolean} params.includePathways - Whether to include pathway information
 * @param {boolean} params.includeInteractions - Whether to include interaction information
 * @returns {Promise<Object>} Processing results
 */
export async function processMolecule({ 
  molecule, 
  idType = 'smiles', 
  includePathways = false, 
  includeInteractions = false 
}) {
  try {
    const response = await fetch(`${API_BASE_URL}/process`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        molecule,
        id_type: idType,
        pathways: includePathways,
        interactions: includeInteractions,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error processing molecule:', error);
    throw error;
  }
}

/**
 * Compare two molecules
 * @param {Object} params - Comparison parameters
 * @param {string} params.molecule1 - First molecule identifier
 * @param {string} params.molecule2 - Second molecule identifier
 * @param {string} params.idType - Type of identifier (smiles, inchi, name)
 * @returns {Promise<Object>} Comparison results
 */
export async function compareMolecules({ molecule1, molecule2, idType = 'smiles' }) {
  try {
    const response = await fetch(`${API_BASE_URL}/compare`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        molecule1,
        molecule2,
        id_type: idType,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error comparing molecules:', error);
    throw error;
  }
}

/**
 * Build a network from a set of molecules
 * @param {Object} params - Network building parameters
 * @param {Array<string>} params.molecules - Array of molecule identifiers
 * @param {string} params.idType - Type of identifier (smiles, inchi, name)
 * @param {number} params.threshold - Similarity threshold (0.0-1.0)
 * @param {number} params.maxNeighbors - Maximum neighbors per molecule
 * @returns {Promise<Object>} Network results
 */
export async function buildNetwork({ 
  molecules, 
  idType = 'smiles', 
  threshold = 0.7, 
  maxNeighbors = 10 
}) {
  try {
    const response = await fetch(`${API_BASE_URL}/network`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        molecules,
        id_type: idType,
        threshold,
        max_neighbors: maxNeighbors,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error building network:', error);
    throw error;
  }
}

/**
 * API service for connecting to the Rust backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080/api';

/**
 * Fetch data from the Rust backend
 * @param {string} endpoint - API endpoint
 * @param {Object} options - Fetch options
 * @returns {Promise<any>} - Response data
 */
async function fetchFromApi(endpoint, options = {}) {
  const url = `${API_URL}/${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || `API request failed with status ${response.status}`);
  }

  return response.json();
}

/**
 * API for interacting with the Rust backend
 */
const api = {
  /**
   * Analyze molecular evidence
   * @param {Object} data - Molecular data to analyze
   * @returns {Promise<Object>} - Analysis results
   */
  analyzeEvidence: (data) => {
    return fetchFromApi('analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get reactome pathways
   * @param {string} molecule - Molecule identifier
   * @returns {Promise<Object>} - Reactome pathways
   */
  getReactomePathways: (molecule) => {
    return fetchFromApi(`reactome/pathways/${molecule}`);
  },

  /**
   * Get interactome data
   * @param {string} molecule - Molecule identifier
   * @returns {Promise<Object>} - Interactome data
   */
  getInteractomeData: (molecule) => {
    return fetchFromApi(`interactome/${molecule}`);
  },

  /**
   * Run AI-guided evidence rectification
   * @param {Object} evidenceData - Evidence data
   * @returns {Promise<Object>} - Rectified evidence
   */
  rectifyEvidence: (evidenceData) => {
    return fetchFromApi('rectify', {
      method: 'POST',
      body: JSON.stringify(evidenceData),
    });
  },

  /**
   * Get genomics analysis results
   * @returns {Promise<Object>} - Genomics analysis
   */
  getGenomicsAnalysis: () => {
    return fetchFromApi('genomics/analysis');
  },

  /**
   * Get mass spectrometry analysis results
   * @returns {Promise<Object>} - Mass spec analysis
   */
  getMassSpecAnalysis: () => {
    return fetchFromApi('mass-spec/analysis');
  },

  /**
   * Submit genomics data for analysis
   * @param {Object} data - Genomics data
   * @returns {Promise<Object>} - Analysis job info
   */
  submitGenomicsAnalysis: (data) => {
    return fetchFromApi('genomics/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Submit mass spec data for analysis
   * @param {Object} data - Mass spec data
   * @returns {Promise<Object>} - Analysis job info
   */
  submitMassSpecAnalysis: (data) => {
    return fetchFromApi('mass-spec/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get molecule metadata
   * @param {string} id - Molecule ID
   * @returns {Promise<Object>} - Molecule data
   */
  getMoleculeData: (id) => {
    return fetchFromApi(`molecules/${id}`);
  },
};

export default api; 