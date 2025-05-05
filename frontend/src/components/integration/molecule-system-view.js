import React, { useState, useEffect } from "react";
import MoleculeViewer from "../molecules/molecule-viewer";
import SpectrumViewer from "../spectra/spectrum-viewer";
import SequenceViewer from "../genome/sequence-viewer";
import PathwayViewer from "../pathway/pathway-viewer";
import { fetchMoleculeSystemData } from "../../services/api";

/**
 * MoleculeSystemView component that integrates various data viewers
 * into a comprehensive system view for a given molecule or entity
 */
export default function MoleculeSystemView({ entityId, options }) {
  const [activeTab, setActiveTab] = useState("overview");
  const [systemData, setSystemData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [connectionHighlights, setConnectionHighlights] = useState({});
  
  // Fetch system data on component mount
  useEffect(() => {
    if (!entityId) return;
    
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // In a real implementation, this would call the API
        // const data = await fetchMoleculeSystemData(entityId);
        
        // For now, simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // Use mock data
        const mockData = generateMockData(entityId);
        setSystemData(mockData);
      } catch (err) {
        console.error("Error fetching system data:", err);
        setError("Failed to fetch system data");
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, [entityId]);
  
  // Handle highlighting connected elements
  const handleElementHighlight = (elementId, elementType) => {
    // Find connections for this element
    if (!systemData || !systemData.connections) {
      return;
    }
    
    const relevantConnections = systemData.connections.filter(
      conn => conn.source.id === elementId || conn.target.id === elementId
    );
    
    const highlights = {};
    
    relevantConnections.forEach(conn => {
      const connectedElement = conn.source.id === elementId ? conn.target : conn.source;
      
      if (!highlights[connectedElement.type]) {
        highlights[connectedElement.type] = [];
      }
      
      highlights[connectedElement.type].push({
        id: connectedElement.id,
        relationship: conn.relationship
      });
    });
    
    setConnectionHighlights(highlights);
  };
  
  // Clear highlights
  const clearHighlights = () => {
    setConnectionHighlights({});
  };
  
  // Generate mock data for demonstration
  const generateMockData = (id) => {
    return {
      id: id,
      name: "Glucose",
      description: "A simple monosaccharide (sugar) with the molecular formula C₆H₁₂O₆",
      molecule: {
        id: "mol_glucose",
        name: "Glucose",
        smiles: "C1C(C(C(C(C1O)O)O)O)O",
        formula: "C6H12O6",
        is_valid: true,
        confidence: 0.98,
        molecular_weight: 180.156,
        properties: {
          logP: -3.24,
          hydrogen_bond_donors: 5,
          hydrogen_bond_acceptors: 6,
          rotatable_bonds: 1
        },
        description: "A simple monosaccharide (simple sugar) with the formula C6H12O6. Glucose is the most abundant monosaccharide and an important source of energy for organisms."
      },
      spectra: [
        {
          id: "spectrum_glucose_ms1",
          type: "MS1",
          description: "MS1 spectrum of glucose",
          peaks: [
            { mz: 180.0634, intensity: 1000000, annotation: "M" },
            { mz: 181.0667, intensity: 66000, annotation: "M+1" },
            { mz: 182.0701, intensity: 22000, annotation: "M+2" },
            { mz: 203.0532, intensity: 550000, annotation: "M+Na" },
            { mz: 219.0271, intensity: 125000, annotation: "M+K" },
            { mz: 225.0744, intensity: 80000, annotation: "M+HCOONa" }
          ],
          metadata: {
            moleculeName: "Glucose",
            msLevel: "MS1",
            precursorMz: null,
            retentionTime: 1.45,
            scanNumber: 120
          }
        },
        {
          id: "spectrum_glucose_ms2",
          type: "MS2",
          description: "MS2 spectrum of glucose",
          peaks: [
            { mz: 163.0606, intensity: 850000, annotation: "M-H2O" },
            { mz: 145.0501, intensity: 420000, annotation: "M-2H2O" },
            { mz: 127.0395, intensity: 310000, annotation: "M-3H2O" },
            { mz: 109.0290, intensity: 210000, annotation: "M-4H2O" },
            { mz: 97.0290, intensity: 180000, annotation: "C5H5O2" },
            { mz: 85.0290, intensity: 160000, annotation: "C4H5O2" }
          ],
          metadata: {
            moleculeName: "Glucose",
            msLevel: "MS2",
            precursorMz: 180.0634,
            retentionTime: 1.45,
            scanNumber: 125
          }
        }
      ],
      sequences: [
        {
          id: "sequence_glucose_transporter",
          name: "Glucose Transporter 1 (GLUT1)",
          type: "DNA",
          description: "DNA sequence encoding the glucose transporter protein GLUT1",
          sequence: "ATGGAGCCCAGCAGCAAGAAGCTGACGGGTCGCCTCATGCTGGCCGTGGGCATCAATTGCTCCATCGTGATCGGCATTTTCTTCACTGCTCGCCTGTTTGACCTGGGCTTCGTCAACACTGCCTTCTCGAAGGACTTCCAGTATCTCATCGCAGGCGCGTATGGTTCCTTCCAGACGAAAGAAGGAACTGTGCCCATCACGTTCTCGGACGGCTTCTCCAACTGGACCTCCAACTACTGCACGGATGAGATTGAAGAATATGACCTGAACCGCATCATGGGCATCGTTATTGGCCTTATTGCAGTTGAACTGTGCTCCAGTATCTTCGTCCAGCAGATAGGCTACAACCGCACCGCGGCCGACTCGGACTTCCTGCTGCTGGGCCTCTTCATTGTTGCTGCAGTGGGCGGCGTCCTTGTCTGATTCGGTTCCCAGCTGGCACCCATGCTCTCCGTAGCTGCTGGCACGTCGGAACTTCTCGTAAGCATCAGTTTTGTGAACGCTACTGGCGTTCTGTTTCCAGTATGCGGGGGACTTGAGCTTCCTGCTGGGACGTCCCTTGATCCTCAGTGGCCTGCTGCAGCTGGCCATTGCAGGCGCAACCATTTGGATGATTGTGGAATTTCGGGCTGGTCCCATGTATGCCCAGCAGAAGGGCATTCACCGCACTGAGGAGATCATCGGGGGCATGATTGGCTCCCTGCAGTTTGGCTACAACACTGGAGTCATCAATGCCCCCCAGAAGGTTATTGAGGAATTAATGCTTGCTTCTGTAACCATGGTGACTCCCATCACTGCCCAGGACACACTGACCACCACACTCACCACCCTGGGCGGCATCTTCATTGCCGTGGTGCTGCTGCCTGTGGTCTTCTCCAAGGGGCTGCCCGTGGTCATTGGCCTGGTCCCTGGACGCATGAACGTGTTTGAAAACCTAGGACCGCTGCGGGCCACGGAGGAGCTGGCCCCAGCAGATCGCTGTGGGCATCCTGCTCACTGGTGTCTTCTATTTCCTTCTCTTTGGCTGGGTGGGCATCAAGCCCAAGGGTGTGGAGCGAGTCCTCACTTTGGCCCTCTTCCTGTTCATCATTTCTGGACTGGTGGCCATTGTCTGAGTGTTCAAGGAGTTCACTGGTGTGGCCCCTGAGAACTCCCTGGTCACTGGGAAGAAGATCACTGTGCTGCTGCAGTTCGGCTCGGGCATCGTGAGGGGCCAGCCGGCCGTGCGCATTGTGCCCCAGCTGGTGCACCAGCGCCTGAGCTCGGTGGACCCAGGCAAGAATAATGGGACTCCAGACAGCTGCTCCTGCCGGAACCTCGCCATGGATATTCCCTCAAAGGGATCCCAAGCCTCCTGCATCCCAAGGAGGAACTCTTCCCACCTAACGAGGAGCTGCATCTGCTGGATCCACACCTCGGGTGCATGAGCTTTGCCACCTTGGACCGCACCCCTGCAGTTGCTGTGGTGAACAAGCTGCTGGGCATCGCCGTCGTGCTCATGGCCGGTGCCCAGGTGTTCGAAGAGCTGGACGAGGCTCCTGAGACGCTTGGCCCGGTGGAGCGAGCCCTTCCGGCCTCCTATCATGGCTCAGGAGCAGCTGGCGTTGCGCACCATCTTCGGCCTGGACTCCGTTGCTGGCGCCTTCATCATCACCCAAGGCGTGGTGCTGCAGTCCTTCGTCCTGGGCTTCTTCATCTCAGTGGGCGCCTGGATCCTGCAGGGCTGCCTTAGCAAAGCCCAGGAGGTGAGCAGTGAGATGAAGAAGAACGAGATGGAGATGACACGCGACAGCCTGGGCGGGTCCCCCGGGGGCAGCAGCAGCGTCAGCGACACTGAGGCCACGGCTGAGGCACTGCTGCAACAGGAGGAGCACGCTGGCACTCGACACCTGAACGAAGCGCAACCACCTGTGA",
          annotations: [
            {
              name: "Transmembrane Domain 1",
              start: 330,
              end: 399,
              type: "domain",
              color: "#4CAF50"
            },
            {
              name: "Glucose Binding Site",
              start: 650,
              end: 700,
              type: "functional_site",
              color: "#F44336"
            },
            {
              name: "Glycosylation Site",
              start: 850,
              end: 870,
              type: "modification",
              color: "#2196F3"
            }
          ],
          metadata: {
            name: "GLUT1",
            source: "Human",
            type: "Coding Sequence"
          }
        }
      ],
      pathways: [
        {
          id: "pathway_glycolysis",
          name: "Glycolysis Pathway",
          description: "The metabolic pathway that converts glucose into pyruvate, releasing energy in the form of ATP",
          nodes: [
            { id: "glucose", label: "Glucose", type: "metabolite", description: "C6H12O6" },
            { id: "g6p", label: "Glucose-6-P", type: "metabolite", description: "C6H13O9P" },
            { id: "f6p", label: "Fructose-6-P", type: "metabolite" },
            { id: "f16bp", label: "Fructose-1,6-BP", type: "metabolite" },
            { id: "dhap", label: "DHAP", type: "metabolite" },
            { id: "g3p", label: "Glyceraldehyde-3-P", type: "metabolite" },
            { id: "bpg", label: "1,3-BPG", type: "metabolite" },
            { id: "3pg", label: "3-PG", type: "metabolite" },
            { id: "2pg", label: "2-PG", type: "metabolite" },
            { id: "pep", label: "PEP", type: "metabolite" },
            { id: "pyruvate", label: "Pyruvate", type: "metabolite" },
            { id: "hk", label: "Hexokinase", type: "protein" },
            { id: "pgi", label: "Phosphoglucose Isomerase", type: "protein" },
            { id: "pfk", label: "Phosphofructokinase", type: "protein" },
            { id: "aldo", label: "Aldolase", type: "protein" },
            { id: "tpi", label: "Triose Phosphate Isomerase", type: "protein" },
            { id: "gapdh", label: "GAPDH", type: "protein" },
            { id: "pgk", label: "Phosphoglycerate Kinase", type: "protein" },
            { id: "pgm", label: "Phosphoglycerate Mutase", type: "protein" },
            { id: "eno", label: "Enolase", type: "protein" },
            { id: "pk", label: "Pyruvate Kinase", type: "protein" }
          ],
          links: [
            { source: "glucose", target: "hk", directed: true },
            { source: "hk", target: "g6p", directed: true },
            { source: "g6p", target: "pgi", directed: true },
            { source: "pgi", target: "f6p", directed: true },
            { source: "f6p", target: "pfk", directed: true },
            { source: "pfk", target: "f16bp", directed: true },
            { source: "f16bp", target: "aldo", directed: true },
            { source: "aldo", target: "dhap", directed: true },
            { source: "aldo", target: "g3p", directed: true },
            { source: "dhap", target: "tpi", directed: true },
            { source: "tpi", target: "g3p", directed: true },
            { source: "g3p", target: "gapdh", directed: true },
            { source: "gapdh", target: "bpg", directed: true },
            { source: "bpg", target: "pgk", directed: true },
            { source: "pgk", target: "3pg", directed: true },
            { source: "3pg", target: "pgm", directed: true },
            { source: "pgm", target: "2pg", directed: true },
            { source: "2pg", target: "eno", directed: true },
            { source: "eno", target: "pep", directed: true },
            { source: "pep", target: "pk", directed: true },
            { source: "pk", target: "pyruvate", directed: true }
          ],
          metadata: {
            id: "P00001",
            organism: "Human",
            source: "KEGG"
          }
        }
      ],
      connections: [
        {
          source: { id: "mol_glucose", type: "molecule" },
          target: { id: "spectrum_glucose_ms1", type: "spectrum" },
          relationship: "has_spectrum"
        },
        {
          source: { id: "mol_glucose", type: "molecule" },
          target: { id: "spectrum_glucose_ms2", type: "spectrum" },
          relationship: "has_spectrum"
        },
        {
          source: { id: "mol_glucose", type: "molecule" },
          target: { id: "pathway_glycolysis", type: "pathway" },
          relationship: "participates_in"
        },
        {
          source: { id: "sequence_glucose_transporter", type: "sequence" },
          target: { id: "mol_glucose", type: "molecule" },
          relationship: "transports"
        }
      ]
    };
  };
  
  // Render loading state
  if (isLoading) {
    return (
      <div className="molecule-system-loading">
        <div className="spinner"></div>
        <p>Loading system data...</p>
      </div>
    );
  }
  
  // Render error state
  if (error) {
    return (
      <div className="molecule-system-error">
        <h3>Error</h3>
        <p>{error}</p>
      </div>
    );
  }
  
  // Render empty state
  if (!systemData) {
    return (
      <div className="molecule-system-empty">
        <p>No system data available for this entity.</p>
      </div>
    );
  }
  
  return (
    <div className="molecule-system-container">
      <div className="molecule-system-header">
        <h2>{systemData.name}</h2>
        {systemData.description && (
          <p className="system-description">{systemData.description}</p>
        )}
      </div>
      
      <div className="molecule-system-tabs">
        <button 
          className={`system-tab ${activeTab === "overview" ? "active" : ""}`}
          onClick={() => setActiveTab("overview")}
        >
          Overview
        </button>
        <button 
          className={`system-tab ${activeTab === "molecule" ? "active" : ""}`}
          onClick={() => setActiveTab("molecule")}
          disabled={!systemData.molecule}
        >
          Molecule
        </button>
        <button 
          className={`system-tab ${activeTab === "spectra" ? "active" : ""}`}
          onClick={() => setActiveTab("spectra")}
          disabled={!systemData.spectra || systemData.spectra.length === 0}
        >
          Spectra
        </button>
        <button 
          className={`system-tab ${activeTab === "sequences" ? "active" : ""}`}
          onClick={() => setActiveTab("sequences")}
          disabled={!systemData.sequences || systemData.sequences.length === 0}
        >
          Sequences
        </button>
        <button 
          className={`system-tab ${activeTab === "pathways" ? "active" : ""}`}
          onClick={() => setActiveTab("pathways")}
          disabled={!systemData.pathways || systemData.pathways.length === 0}
        >
          Pathways
        </button>
      </div>
      
      <div className="molecule-system-content">
        {activeTab === "overview" && (
          <div className="system-overview">
            <div className="system-overview-grid">
              {systemData.molecule && (
                <div className="overview-card" onClick={() => setActiveTab("molecule")}>
                  <h3>Molecule</h3>
                  <div className="overview-preview molecule-preview">
                    <MoleculeViewer 
                      moleculeData={systemData.molecule}
                      viewerOptions={{ width: 300, height: 200 }}
                    />
                  </div>
                  <p className="overview-description">
                    {systemData.molecule.name} - {systemData.molecule.formula}
                  </p>
                </div>
              )}
              
              {systemData.spectra && systemData.spectra.length > 0 && (
                <div className="overview-card" onClick={() => setActiveTab("spectra")}>
                  <h3>Spectra</h3>
                  <div className="overview-preview spectra-preview">
                    <SpectrumViewer 
                      spectrumData={systemData.spectra[0]}
                      options={{ width: 300, height: 200, showGrid: false }}
                    />
                  </div>
                  <p className="overview-description">
                    {systemData.spectra.length} spectrum/spectra available
                  </p>
                </div>
              )}
              
              {systemData.sequences && systemData.sequences.length > 0 && (
                <div className="overview-card" onClick={() => setActiveTab("sequences")}>
                  <h3>Sequences</h3>
                  <div className="overview-preview sequence-preview">
                    <div className="sequence-snippet">
                      {systemData.sequences[0].sequence.substring(0, 50)}...
                    </div>
                  </div>
                  <p className="overview-description">
                    {systemData.sequences[0].name} - {systemData.sequences[0].metadata?.type || "Sequence"}
                  </p>
                </div>
              )}
              
              {systemData.pathways && systemData.pathways.length > 0 && (
                <div className="overview-card" onClick={() => setActiveTab("pathways")}>
                  <h3>Pathways</h3>
                  <div className="overview-preview pathway-preview">
                    <PathwayViewer 
                      pathwayData={systemData.pathways[0]}
                      options={{ width: 300, height: 200, showLabels: false }}
                    />
                  </div>
                  <p className="overview-description">
                    {systemData.pathways[0].name}
                  </p>
                </div>
              )}
            </div>
            
            <div className="system-connections">
              <h3>System Connections</h3>
              <div className="connections-diagram">
                {systemData.connections && systemData.connections.map((conn, index) => (
                  <div key={index} className="connection-item">
                    <div className={`connection-node source ${conn.source.type}`}>
                      {conn.source.id.split('_').pop()}
                    </div>
                    <div className="connection-arrow">
                      {conn.relationship.replace(/_/g, ' ')}
                    </div>
                    <div className={`connection-node target ${conn.target.type}`}>
                      {conn.target.id.split('_').pop()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        
        {activeTab === "molecule" && systemData.molecule && (
          <div className="system-molecule">
            <div className="molecule-details">
              <MoleculeViewer 
                moleculeData={systemData.molecule}
                viewerOptions={{ width: 500, height: 400 }}
              />
            </div>
            
            <div className="molecule-metadata">
              <table className="metadata-table">
                <tbody>
                  <tr>
                    <td>Name</td>
                    <td>{systemData.molecule.name}</td>
                  </tr>
                  <tr>
                    <td>Formula</td>
                    <td>{systemData.molecule.formula}</td>
                  </tr>
                  <tr>
                    <td>SMILES</td>
                    <td>{systemData.molecule.smiles}</td>
                  </tr>
                  <tr>
                    <td>Molecular Weight</td>
                    <td>{systemData.molecule.molecular_weight} g/mol</td>
                  </tr>
                  <tr>
                    <td>LogP</td>
                    <td>{systemData.molecule.properties?.logP}</td>
                  </tr>
                  <tr>
                    <td>H-Bond Donors</td>
                    <td>{systemData.molecule.properties?.hydrogen_bond_donors}</td>
                  </tr>
                  <tr>
                    <td>H-Bond Acceptors</td>
                    <td>{systemData.molecule.properties?.hydrogen_bond_acceptors}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}
        
        {activeTab === "spectra" && systemData.spectra && (
          <div className="system-spectra">
            <div className="spectra-tabs">
              {systemData.spectra.map((spectrum, index) => (
                <button 
                  key={spectrum.id}
                  className={`spectra-tab ${index === 0 ? "active" : ""}`}
                >
                  {spectrum.type} Spectrum
                </button>
              ))}
            </div>
            
            <div className="spectrum-display">
              <SpectrumViewer 
                spectrumData={systemData.spectra[0]}
                options={{ width: 800, height: 400 }}
              />
            </div>
          </div>
        )}
        
        {activeTab === "sequences" && systemData.sequences && (
          <div className="system-sequences">
            <div className="sequence-tabs">
              {systemData.sequences.map((sequence, index) => (
                <button 
                  key={sequence.id}
                  className={`sequence-tab ${index === 0 ? "active" : ""}`}
                >
                  {sequence.name}
                </button>
              ))}
            </div>
            
            <div className="sequence-display">
              <SequenceViewer 
                sequenceData={systemData.sequences[0]}
                options={{ viewportSize: 200, lineLength: 60 }}
              />
            </div>
          </div>
        )}
        
        {activeTab === "pathways" && systemData.pathways && (
          <div className="system-pathways">
            <div className="pathway-tabs">
              {systemData.pathways.map((pathway, index) => (
                <button 
                  key={pathway.id}
                  className={`pathway-tab ${index === 0 ? "active" : ""}`}
                >
                  {pathway.name}
                </button>
              ))}
            </div>
            
            <div className="pathway-display">
              <PathwayViewer pathwayData={systemData.pathways[0]} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 