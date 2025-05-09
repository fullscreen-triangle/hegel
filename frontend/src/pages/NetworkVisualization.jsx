import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import NetworkGraph from '../components/pathway/NetworkGraph';
import MoleculeViewer from '../components/molecules/MoleculeViewer';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const NetworkVisualization = () => {
  const { moleculeId, pathwayId } = useParams();
  const navigate = useNavigate();
  
  const [molecule, setMolecule] = useState(null);
  const [pathway, setPathway] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [similarityThreshold, setSimilarityThreshold] = useState(0.6);
  
  // Fetch initial data based on route params
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // If moleculeId is provided, fetch molecule data
        if (moleculeId) {
          const moleculeResponse = await axios.get(`${API_URL}/molecules/${moleculeId}`);
          setMolecule(moleculeResponse.data);
          setSelectedNode(null);
        }
        
        // If pathwayId is provided, fetch pathway data
        if (pathwayId) {
          const pathwayResponse = await axios.get(`${API_URL}/pathways/${pathwayId}`);
          setPathway(pathwayResponse.data);
        }
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Failed to load data. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [moleculeId, pathwayId]);
  
  // Handle node click in network graph
  const handleNodeClick = (node) => {
    setSelectedNode(node);
    
    // If the node is a molecule, navigate to its details
    if (node.type === 'molecule' && node.id !== moleculeId) {
      navigate(`/molecules/${node.id}`);
    }
    
    // If the node is a pathway, navigate to its details
    if (node.type === 'pathway' && node.id !== pathwayId) {
      navigate(`/pathways/${node.id}`);
    }
  };
  
  // Handle similarity threshold change
  const handleThresholdChange = (event) => {
    setSimilarityThreshold(parseFloat(event.target.value));
  };
  
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">
          {molecule ? `Network for ${molecule.name}` : 
           pathway ? `Molecules in ${pathway.name} Pathway` : 
           'Network Visualization'}
        </h1>
        
        <div className="flex items-center">
          <label htmlFor="similarity" className="mr-2 text-sm">
            Similarity Threshold:
          </label>
          <input
            id="similarity"
            type="range"
            min="0.1"
            max="1.0"
            step="0.05"
            value={similarityThreshold}
            onChange={handleThresholdChange}
            className="w-32"
          />
          <span className="ml-2 text-sm">{(similarityThreshold * 100).toFixed(0)}%</span>
        </div>
      </div>
      
      {loading ? (
        <div className="flex justify-center items-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      ) : error ? (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Network Graph */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow-md overflow-hidden">
            <div className="p-4 bg-gray-50 border-b">
              <h2 className="text-lg font-semibold">Molecular Network</h2>
              <p className="text-sm text-gray-600">
                {moleculeId ? "Showing relationships between this molecule and others" : 
                 pathwayId ? "Showing molecules in this pathway" : 
                 "Explore molecular relationships"}
              </p>
            </div>
            
            <div className="h-[600px]">
              <NetworkGraph
                moleculeId={moleculeId}
                pathwayId={pathwayId}
                similarityThreshold={similarityThreshold}
                onNodeClick={handleNodeClick}
              />
            </div>
          </div>
          
          {/* Molecule Details or Selected Node */}
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="p-4 bg-gray-50 border-b">
              <h2 className="text-lg font-semibold">
                {selectedNode ? `Selected: ${selectedNode.name || selectedNode.label}` : 
                 molecule ? `${molecule.name}` : 
                 "Select a node to view details"}
              </h2>
            </div>
            
            <div className="p-4">
              {selectedNode ? (
                <div>
                  {selectedNode.type === 'molecule' && (
                    <>
                      <div className="mb-4">
                        <MoleculeViewer
                          moleculeId={selectedNode.id}
                          height="300px"
                        />
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div className="col-span-2">
                          <span className="font-semibold">Name:</span> {selectedNode.name}
                        </div>
                        {selectedNode.formula && (
                          <div>
                            <span className="font-semibold">Formula:</span> {selectedNode.formula}
                          </div>
                        )}
                        {selectedNode.confidence !== undefined && (
                          <div>
                            <span className="font-semibold">Confidence:</span>{' '}
                            <span 
                              className={
                                selectedNode.confidence >= 0.7 ? 'text-green-600' : 
                                selectedNode.confidence >= 0.4 ? 'text-yellow-600' : 
                                'text-red-600'
                              }
                            >
                              {(selectedNode.confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                        )}
                      </div>
                      
                      <div className="mt-4">
                        <button 
                          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded text-sm"
                          onClick={() => navigate(`/molecules/${selectedNode.id}`)}
                        >
                          View Full Details
                        </button>
                      </div>
                    </>
                  )}
                  
                  {selectedNode.type === 'pathway' && (
                    <>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div className="col-span-2">
                          <span className="font-semibold">Name:</span> {selectedNode.name}
                        </div>
                        {selectedNode.description && (
                          <div className="col-span-2">
                            <span className="font-semibold">Description:</span> {selectedNode.description}
                          </div>
                        )}
                      </div>
                      
                      <div className="mt-4">
                        <button 
                          className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded text-sm"
                          onClick={() => navigate(`/pathways/${selectedNode.id}`)}
                        >
                          Explore Pathway
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ) : molecule ? (
                <>
                  <div className="mb-4">
                    <MoleculeViewer
                      moleculeId={molecule.id}
                      height="300px"
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="col-span-2">
                      <span className="font-semibold">Name:</span> {molecule.name}
                    </div>
                    <div>
                      <span className="font-semibold">Formula:</span> {molecule.formula}
                    </div>
                    <div>
                      <span className="font-semibold">Confidence:</span>{' '}
                      <span 
                        className={
                          molecule.confidence_score >= 0.7 ? 'text-green-600' : 
                          molecule.confidence_score >= 0.4 ? 'text-yellow-600' : 
                          'text-red-600'
                        }
                      >
                        {(molecule.confidence_score * 100).toFixed(1)}%
                      </span>
                    </div>
                    {molecule.smiles && (
                      <div className="col-span-2">
                        <span className="font-semibold">SMILES:</span> 
                        <div className="text-xs bg-gray-100 p-2 mt-1 rounded overflow-x-auto">
                          {molecule.smiles}
                        </div>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="flex justify-center items-center h-64 text-gray-500">
                  Select a node from the network to view details
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NetworkVisualization; 