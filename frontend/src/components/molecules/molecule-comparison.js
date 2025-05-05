import React, { useState, useEffect } from "react";
import MoleculeViewer from "./molecule-viewer";
import { compareMolecules } from "../../services/api";

/**
 * MoleculeComparison component for comparing two molecules side by side
 */
export default function MoleculeComparison({ molecules }) {
  const [molecule1, setMolecule1] = useState(null);
  const [molecule2, setMolecule2] = useState(null);
  const [comparisonResult, setComparisonResult] = useState(null);
  const [isComparing, setIsComparing] = useState(false);
  const [error, setError] = useState(null);
  const [viewerOptions, setViewerOptions] = useState({
    style: "stick",
    backgroundColor: "white",
    width: 400,
    height: 300
  });
  
  // Function to compare molecules
  const handleCompareMolecules = async () => {
    if (!molecule1 || !molecule2) {
      setError("Please select two molecules to compare");
      return;
    }
    
    setIsComparing(true);
    setError(null);
    
    try {
      // In a real implementation, this would call the API
      // const result = await compareMolecules({
      //   molecule1: molecule1.smiles,
      //   molecule2: molecule2.smiles,
      //   idType: 'smiles'
      // });
      
      // For now, simulate API call with a delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Calculate mock similarity based on molecule properties
      const propertyComp = compareProperties(molecule1, molecule2);
      
      setComparisonResult({
        similarity: propertyComp.overallSimilarity,
        same_entity: propertyComp.overallSimilarity > 0.8,
        analysis: generateAnalysis(molecule1, molecule2, propertyComp),
        propertyComparisons: propertyComp.comparisons
      });
    } catch (err) {
      console.error("Error comparing molecules:", err);
      setError("Failed to compare molecules: " + (err.message || "Unknown error"));
    } finally {
      setIsComparing(false);
    }
  };
  
  // Compare molecule properties and return a similarity score
  const compareProperties = (mol1, mol2) => {
    const comparisons = [];
    let totalWeight = 0;
    let weightedSum = 0;
    
    // Compare molecular weight
    if (mol1.molecular_weight && mol2.molecular_weight) {
      const mwDiff = Math.abs(mol1.molecular_weight - mol2.molecular_weight);
      const mwSimilarity = Math.max(0, 1 - (mwDiff / Math.max(mol1.molecular_weight, mol2.molecular_weight)));
      comparisons.push({
        property: "Molecular Weight",
        value1: mol1.molecular_weight + " g/mol",
        value2: mol2.molecular_weight + " g/mol",
        similarity: mwSimilarity,
        weight: 0.3
      });
      totalWeight += 0.3;
      weightedSum += mwSimilarity * 0.3;
    }
    
    // Compare LogP if available
    if (mol1.properties?.logP !== undefined && mol2.properties?.logP !== undefined) {
      const logPDiff = Math.abs(mol1.properties.logP - mol2.properties.logP);
      const logPSimilarity = Math.max(0, 1 - (logPDiff / 10)); // Assuming LogP ranges roughly ±5
      comparisons.push({
        property: "LogP",
        value1: mol1.properties.logP,
        value2: mol2.properties.logP,
        similarity: logPSimilarity,
        weight: 0.15
      });
      totalWeight += 0.15;
      weightedSum += logPSimilarity * 0.15;
    }
    
    // Compare hydrogen bond donors
    if (mol1.properties?.hydrogen_bond_donors !== undefined && 
        mol2.properties?.hydrogen_bond_donors !== undefined) {
      const hbdDiff = Math.abs(mol1.properties.hydrogen_bond_donors - mol2.properties.hydrogen_bond_donors);
      const hbdSimilarity = Math.max(0, 1 - (hbdDiff / 5)); // Assuming donors range 0-5
      comparisons.push({
        property: "H-Bond Donors",
        value1: mol1.properties.hydrogen_bond_donors,
        value2: mol2.properties.hydrogen_bond_donors,
        similarity: hbdSimilarity,
        weight: 0.15
      });
      totalWeight += 0.15;
      weightedSum += hbdSimilarity * 0.15;
    }
    
    // Compare hydrogen bond acceptors
    if (mol1.properties?.hydrogen_bond_acceptors !== undefined && 
        mol2.properties?.hydrogen_bond_acceptors !== undefined) {
      const hbaDiff = Math.abs(mol1.properties.hydrogen_bond_acceptors - mol2.properties.hydrogen_bond_acceptors);
      const hbaSimilarity = Math.max(0, 1 - (hbaDiff / 10)); // Assuming acceptors range 0-10
      comparisons.push({
        property: "H-Bond Acceptors",
        value1: mol1.properties.hydrogen_bond_acceptors,
        value2: mol2.properties.hydrogen_bond_acceptors,
        similarity: hbaSimilarity,
        weight: 0.15
      });
      totalWeight += 0.15;
      weightedSum += hbaSimilarity * 0.15;
    }
    
    // Compare rotatable bonds
    if (mol1.properties?.rotatable_bonds !== undefined && 
        mol2.properties?.rotatable_bonds !== undefined) {
      const rbDiff = Math.abs(mol1.properties.rotatable_bonds - mol2.properties.rotatable_bonds);
      const rbSimilarity = Math.max(0, 1 - (rbDiff / 10)); // Assuming rotatable bonds range 0-10
      comparisons.push({
        property: "Rotatable Bonds",
        value1: mol1.properties.rotatable_bonds,
        value2: mol2.properties.rotatable_bonds,
        similarity: rbSimilarity,
        weight: 0.15
      });
      totalWeight += 0.15;
      weightedSum += rbSimilarity * 0.15;
    }
    
    // Compare heavy atoms
    if (mol1.properties?.heavy_atoms !== undefined && 
        mol2.properties?.heavy_atoms !== undefined) {
      const haDiff = Math.abs(mol1.properties.heavy_atoms - mol2.properties.heavy_atoms);
      const haSimilarity = Math.max(0, 1 - (haDiff / 20)); // Assuming heavy atoms range 0-20+
      comparisons.push({
        property: "Heavy Atoms",
        value1: mol1.properties.heavy_atoms,
        value2: mol2.properties.heavy_atoms,
        similarity: haSimilarity,
        weight: 0.1
      });
      totalWeight += 0.1;
      weightedSum += haSimilarity * 0.1;
    }
    
    // Calculate overall similarity with weighting
    const overallSimilarity = totalWeight > 0 ? weightedSum / totalWeight : 0;
    
    return {
      comparisons,
      overallSimilarity
    };
  };
  
  // Generate analysis text based on comparison
  const generateAnalysis = (mol1, mol2, propertyComp) => {
    // This would be much more sophisticated in a real implementation
    // and might leverage LLM capabilities for natural language generation
    
    const { overallSimilarity, comparisons } = propertyComp;
    let analysis = "";
    
    if (overallSimilarity > 0.9) {
      analysis = `${mol1.name} and ${mol2.name} are highly similar molecules with nearly identical physicochemical properties.`;
    } else if (overallSimilarity > 0.7) {
      analysis = `${mol1.name} and ${mol2.name} share substantial similarity in their key properties, suggesting related biological activity.`;
    } else if (overallSimilarity > 0.5) {
      analysis = `${mol1.name} and ${mol2.name} show moderate similarity, with some shared characteristics but notable differences.`;
    } else {
      analysis = `${mol1.name} and ${mol2.name} appear to be quite distinct molecules with different physicochemical profiles.`;
    }
    
    // Add specific property differences
    let significantDifferences = comparisons
      .filter(comp => comp.similarity < 0.7)
      .map(comp => comp.property);
    
    if (significantDifferences.length > 0) {
      analysis += ` The most significant differences are in ${significantDifferences.join(", ")}.`;
    }
    
    return analysis;
  };
  
  // Handle selecting the first molecule
  const handleSelectMolecule1 = (event) => {
    const selected = molecules.find(m => m.id === event.target.value);
    setMolecule1(selected || null);
    setComparisonResult(null);
  };
  
  // Handle selecting the second molecule
  const handleSelectMolecule2 = (event) => {
    const selected = molecules.find(m => m.id === event.target.value);
    setMolecule2(selected || null);
    setComparisonResult(null);
  };
  
  // Handle viewer style change
  const handleStyleChange = (style) => {
    setViewerOptions(prev => ({
      ...prev,
      style
    }));
  };
  
  useEffect(() => {
    // Reset comparison when molecules change
    setComparisonResult(null);
  }, [molecule1, molecule2]);
  
  return (
    <div className="molecule_comparison">
      <div className="molecule_comparison_selectors">
        <div className="molecule_selector">
          <h4>First Molecule</h4>
          <select 
            value={molecule1?.id || ""} 
            onChange={handleSelectMolecule1}
          >
            <option value="">Select a molecule</option>
            {molecules.map(molecule => (
              <option key={molecule.id} value={molecule.id}>
                {molecule.name || molecule.id}
              </option>
            ))}
          </select>
        </div>
        
        <div className="molecule_selector">
          <h4>Second Molecule</h4>
          <select 
            value={molecule2?.id || ""} 
            onChange={handleSelectMolecule2}
          >
            <option value="">Select a molecule</option>
            {molecules.map(molecule => (
              <option key={molecule.id} value={molecule.id}>
                {molecule.name || molecule.id}
              </option>
            ))}
          </select>
        </div>
      </div>
      
      <div className="view_controls">
        <h4>Visualization Style</h4>
        <div className="style_buttons">
          <button 
            className={`style_btn ${viewerOptions.style === 'stick' ? 'active' : ''}`}
            onClick={() => handleStyleChange('stick')}
          >
            Stick
          </button>
          <button 
            className={`style_btn ${viewerOptions.style === 'ball_and_stick' ? 'active' : ''}`}
            onClick={() => handleStyleChange('ball_and_stick')}
          >
            Ball & Stick
          </button>
          <button 
            className={`style_btn ${viewerOptions.style === 'sphere' ? 'active' : ''}`}
            onClick={() => handleStyleChange('sphere')}
          >
            Sphere
          </button>
        </div>
      </div>
      
      <div className="molecule_viewers">
        <div className="molecule_viewer_wrapper">
          {molecule1 ? (
            <MoleculeViewer 
              moleculeData={molecule1}
              viewerOptions={{
                ...viewerOptions,
                width: 400,
                height: 300
              }}
            />
          ) : (
            <div className="empty_viewer">Select first molecule</div>
          )}
        </div>
        
        <div className="molecule_viewer_wrapper">
          {molecule2 ? (
            <MoleculeViewer 
              moleculeData={molecule2}
              viewerOptions={{
                ...viewerOptions,
                width: 400,
                height: 300
              }}
            />
          ) : (
            <div className="empty_viewer">Select second molecule</div>
          )}
        </div>
      </div>
      
      <div className="comparison_actions">
        <button 
          className="compare_btn" 
          onClick={handleCompareMolecules}
          disabled={!molecule1 || !molecule2 || isComparing}
        >
          {isComparing ? "Analyzing..." : "Compare Molecules"}
        </button>
        
        {error && (
          <div className="comparison_error">
            {error}
          </div>
        )}
      </div>
      
      {comparisonResult && (
        <div className="comparison_results">
          <h3>Comparison Results</h3>
          
          <div className="similarity_score">
            <h4>Overall Similarity</h4>
            <div className="score_bar">
              <div 
                className="score_fill" 
                style={{width: `${comparisonResult.similarity * 100}%`}}
              ></div>
              <span className="score_value">
                {(comparisonResult.similarity * 100).toFixed(1)}%
              </span>
            </div>
          </div>
          
          <div className="same_entity">
            <h4>Same Molecular Entity?</h4>
            <div className={`entity_result ${comparisonResult.same_entity ? 'same' : 'different'}`}>
              {comparisonResult.same_entity ? 'Yes' : 'No'}
            </div>
          </div>
          
          {comparisonResult.analysis && (
            <div className="analysis_results">
              <h4>Analysis</h4>
              <p>{comparisonResult.analysis}</p>
            </div>
          )}
          
          {comparisonResult.propertyComparisons && comparisonResult.propertyComparisons.length > 0 && (
            <div className="property_comparisons">
              <h4>Property Comparison</h4>
              <table className="property_table">
                <thead>
                  <tr>
                    <th>Property</th>
                    <th>{molecule1?.name || "Molecule 1"}</th>
                    <th>{molecule2?.name || "Molecule 2"}</th>
                    <th>Similarity</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonResult.propertyComparisons.map((comp, index) => (
                    <tr key={index}>
                      <td>{comp.property}</td>
                      <td>{comp.value1}</td>
                      <td>{comp.value2}</td>
                      <td>
                        <div className="mini_score_bar">
                          <div 
                            className="mini_score_fill" 
                            style={{width: `${comp.similarity * 100}%`}}
                          ></div>
                          <span className="mini_score_value">
                            {(comp.similarity * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
} 