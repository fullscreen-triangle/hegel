import React from "react";

/**
 * MoleculeDetails component displays detailed information about a molecule
 */
export default function MoleculeDetails({ molecule }) {
  if (!molecule) {
    return <div className="molecule_details_empty">No molecule selected</div>;
  }

  return (
    <div className="molecule_details">
      <div className="molecule_details_header">
        <h3>{molecule.name || "Unknown Molecule"}</h3>
        {molecule.formula && (
          <div className="molecule_formula">{molecule.formula}</div>
        )}
      </div>

      <div className="molecule_details_grid">
        <div className="molecule_details_section">
          <h4>Basic Information</h4>
          <table className="molecule_properties_table">
            <tbody>
              <tr>
                <td>ID:</td>
                <td>{molecule.id || "Unknown"}</td>
              </tr>
              <tr>
                <td>SMILES:</td>
                <td className="molecule_smiles">{molecule.smiles || "N/A"}</td>
              </tr>
              <tr>
                <td>Molecular Weight:</td>
                <td>{molecule.molecular_weight ? `${molecule.molecular_weight} g/mol` : "N/A"}</td>
              </tr>
              <tr>
                <td>Validation Status:</td>
                <td>
                  <span className={`validation_status ${molecule.is_valid ? "valid" : "invalid"}`}>
                    {molecule.is_valid ? "Valid" : "Invalid"}
                  </span>
                  {molecule.confidence && (
                    <span className="confidence_score">
                      {" "}({(molecule.confidence * 100).toFixed(1)}% confidence)
                    </span>
                  )}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {molecule.properties && Object.keys(molecule.properties).length > 0 && (
          <div className="molecule_details_section">
            <h4>Properties</h4>
            <table className="molecule_properties_table">
              <tbody>
                {Object.entries(molecule.properties).map(([key, value]) => (
                  <tr key={key}>
                    <td>{key}:</td>
                    <td>{typeof value === "object" ? JSON.stringify(value) : value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {molecule.description && (
        <div className="molecule_details_section">
          <h4>Description</h4>
          <p>{molecule.description}</p>
        </div>
      )}

      {molecule.related_entities && molecule.related_entities.length > 0 && (
        <div className="molecule_details_section">
          <h4>Related Entities</h4>
          <ul className="related_entities_list">
            {molecule.related_entities.map((entity, index) => (
              <li key={entity.entity_id || index}>
                <span className="relation_type">{entity.relation_type}</span>
                <span className="entity_name">
                  {entity.entity_name || entity.entity_id}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {molecule.evidence && (
        <div className="molecule_details_section">
          <h4>Evidence</h4>
          <div className="evidence_content">
            {typeof molecule.evidence === "object" 
              ? Object.entries(molecule.evidence).map(([key, value]) => (
                  <div key={key} className="evidence_item">
                    <strong>{key}:</strong> {typeof value === "object" ? JSON.stringify(value) : value}
                  </div>
                ))
              : molecule.evidence
            }
          </div>
        </div>
      )}
      
      {molecule.explanation && (
        <div className="molecule_details_section">
          <h4>Explanation</h4>
          <p>{molecule.explanation}</p>
        </div>
      )}
    </div>
  );
} 