import React, { useState, useEffect } from "react";
import { Tabs, TabList, Tab, TabPanel } from "react-tabs";
import MoleculeList from "./molecule-list";
import MoleculeDetails from "./molecule-details";
import MoleculeViewer from "./molecule-viewer";
import MoleculeComparison from "./molecule-comparison";

// Mock data for testing
const mockMolecules = [
  {
    id: "mol_1",
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
      rotatable_bonds: 1,
      heavy_atoms: 12,
    },
    description: "A simple monosaccharide (simple sugar) with the formula C6H12O6. Glucose is the most abundant monosaccharide and an important source of energy for organisms.",
    atomCount: 24,
    format: "PDB"
  },
  {
    id: "mol_2",
    name: "Aspirin",
    smiles: "CC(=O)OC1=CC=CC=C1C(=O)O",
    formula: "C9H8O4",
    is_valid: true,
    confidence: 0.95,
    molecular_weight: 180.16,
    properties: {
      logP: 1.43,
      hydrogen_bond_donors: 1,
      hydrogen_bond_acceptors: 4,
      rotatable_bonds: 3,
      heavy_atoms: 13,
    },
    description: "Aspirin, also known as acetylsalicylic acid (ASA), is a medication used to reduce pain, fever, or inflammation.",
    atomCount: 21,
    format: "PDB"
  },
  {
    id: "mol_3",
    name: "Caffeine",
    smiles: "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
    formula: "C8H10N4O2",
    is_valid: true,
    confidence: 0.93,
    molecular_weight: 194.19,
    properties: {
      logP: -0.07,
      hydrogen_bond_donors: 0,
      hydrogen_bond_acceptors: 6,
      rotatable_bonds: 0,
      heavy_atoms: 14,
    },
    description: "Caffeine is a central nervous system stimulant of the methylxanthine class. It is the world's most widely consumed psychoactive drug.",
    atomCount: 24,
    format: "PDB"
  },
  {
    id: "mol_4",
    name: "Unknown Compound",
    smiles: "CCC(C)CC",
    formula: "C6H14",
    is_valid: false,
    confidence: 0.35,
    molecular_weight: 86.18,
    properties: {
      logP: 3.1,
      hydrogen_bond_donors: 0,
      hydrogen_bond_acceptors: 0,
      rotatable_bonds: 3,
      heavy_atoms: 6,
    },
    atomCount: 20,
    format: "PDB"
  }
];

/**
 * MoleculesDefault component integrates all molecule-related components
 */
export default function MoleculesDefault({ ActiveIndex }) {
  const [molecules, setMolecules] = useState([]);
  const [selectedMolecule, setSelectedMolecule] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Fetch molecules from the API
  useEffect(() => {
    // In a real implementation, this would fetch from the Hegel API
    // For now, use mock data with a simulated delay
    setLoading(true);
    
    const fetchMolecules = async () => {
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 800));
        setMolecules(mockMolecules);
        setLoading(false);
      } catch (err) {
        setError("Failed to load molecules");
        setLoading(false);
      }
    };
    
    fetchMolecules();
  }, []);
  
  // Handle molecule selection
  const handleSelectMolecule = (molecule) => {
    setSelectedMolecule(molecule);
  };
  
  return (
    <>
      <div
        className={
          ActiveIndex === 5
            ? "cavani_tm_section active animated fadeInUp"
            : "cavani_tm_section hidden animated"
        }
        id="molecules_"
      >
        <div className="section_inner">
          <div className="cavani_tm_molecules">
            <div className="molecules_title">
              <h3>Molecular Database</h3>
              <p>Validate, visualize, and compare molecular structures with the Hegel platform.</p>
            </div>
            
            <Tabs>
              <TabList>
                <Tab>Browse</Tab>
                <Tab>Compare</Tab>
              </TabList>
              
              <TabPanel>
                <div className="molecules_browse_container">
                  {loading ? (
                    <div className="loading_container">
                      <p>Loading molecular database...</p>
                    </div>
                  ) : error ? (
                    <div className="error_container">
                      <p>Error: {error}</p>
                    </div>
                  ) : (
                    <div className="molecules_browse_content">
                      <div className="molecules_list_panel">
                        <MoleculeList 
                          molecules={molecules} 
                          onSelectMolecule={handleSelectMolecule}
                          selectedMoleculeId={selectedMolecule?.id}
                        />
                      </div>
                      
                      <div className="molecules_details_panel">
                        {selectedMolecule ? (
                          <div className="molecule_details_content">
                            <div className="molecule_viewer_container">
                              <MoleculeViewer 
                                moleculeData={selectedMolecule}
                                viewerOptions={{ width: 500, height: 350 }}
                              />
                            </div>
                            
                            <div className="molecule_details_container">
                              <MoleculeDetails molecule={selectedMolecule} />
                            </div>
                          </div>
                        ) : (
                          <div className="no_molecule_selected">
                            <p>Select a molecule from the list to view details</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </TabPanel>
              
              <TabPanel>
                <div className="molecules_compare_container">
                  {loading ? (
                    <div className="loading_container">
                      <p>Loading molecular database...</p>
                    </div>
                  ) : error ? (
                    <div className="error_container">
                      <p>Error: {error}</p>
                    </div>
                  ) : (
                    <MoleculeComparison molecules={molecules} />
                  )}
                </div>
              </TabPanel>
            </Tabs>
          </div>
        </div>
      </div>
    </>
  );
} 