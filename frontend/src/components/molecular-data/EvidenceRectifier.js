import React, { useState, useEffect } from 'react';
import api from '../../services/api';

const EvidenceRectifier = () => {
  const [moleculeId, setMoleculeId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [pathways, setPathways] = useState([]);
  const [interactome, setInteractome] = useState([]);

  // Default configuration for evidence rectification
  const [rectificationOptions, setRectificationOptions] = useState({
    use_ai_guidance: true,
    confidence_threshold: 0.6,
    include_pathway_analysis: true,
    include_interactome_analysis: true,
  });

  const handleMoleculeIdChange = (e) => {
    setMoleculeId(e.target.value);
  };

  const handleOptionChange = (option, value) => {
    setRectificationOptions({
      ...rectificationOptions,
      [option]: value,
    });
  };

  const handleAnalyzeEvidence = async () => {
    if (!moleculeId) {
      setError('Please enter a molecule ID');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Analyze the evidence using the Rust backend
      const response = await api.analyzeEvidence({
        molecule_ids: [moleculeId],
        evidence_type: 'all',
        confidence_threshold: rectificationOptions.confidence_threshold,
      });

      setAnalysisResults(response.results[moleculeId]);

      // Fetch related pathways and interactions
      if (rectificationOptions.include_pathway_analysis) {
        const pathwaysResponse = await api.getReactomePathways(moleculeId);
        setPathways(pathwaysResponse);
      }

      if (rectificationOptions.include_interactome_analysis) {
        const interactomeResponse = await api.getInteractomeData(moleculeId);
        setInteractome(interactomeResponse);
      }

      setLoading(false);
    } catch (err) {
      setError(err.message || 'Failed to analyze evidence');
      setLoading(false);
    }
  };

  const handleRectifyEvidence = async () => {
    if (!moleculeId) {
      setError('Please enter a molecule ID');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Create dummy evidence for now (in a real app, this would come from selected sources)
      const evidenceData = {
        [moleculeId]: [
          {
            source: 'genomics',
            data: {
              variant: 'rs123456',
              effect: 'missense',
            },
            confidence: 0.65,
          },
          {
            source: 'mass_spec',
            data: {
              peak: 234.56,
              intensity: 45678,
            },
            confidence: 0.72,
          },
        ],
      };

      // Rectify the evidence using the AI-guided system
      const response = await api.rectifyEvidence({
        evidence_data: evidenceData,
        rectification_options: rectificationOptions,
      });

      setAnalysisResults(response.results[moleculeId]);
      setLoading(false);
    } catch (err) {
      setError(err.message || 'Failed to rectify evidence');
      setLoading(false);
    }
  };

  return (
    <div className="evidence-rectifier">
      <h2>Evidence Rectification Engine</h2>
      <p className="description">
        The evidence rectification engine analyzes molecular data from multiple sources,
        integrates it with reactome and interactome data, and uses AI-guided methods
        to improve confidence in molecular identity.
      </p>

      <div className="input-section">
        <div className="form-group">
          <label htmlFor="molecule-id">Molecule ID:</label>
          <input
            type="text"
            id="molecule-id"
            value={moleculeId}
            onChange={handleMoleculeIdChange}
            placeholder="Enter molecule ID (e.g., PROT1)"
          />
        </div>

        <div className="options-section">
          <h3>Rectification Options</h3>
          <div className="options-grid">
            <div className="option">
              <label>
                <input
                  type="checkbox"
                  checked={rectificationOptions.use_ai_guidance}
                  onChange={(e) => handleOptionChange('use_ai_guidance', e.target.checked)}
                />
                Use AI Guidance
              </label>
            </div>
            <div className="option">
              <label>
                <input
                  type="checkbox"
                  checked={rectificationOptions.include_pathway_analysis}
                  onChange={(e) => handleOptionChange('include_pathway_analysis', e.target.checked)}
                />
                Include Pathway Analysis
              </label>
            </div>
            <div className="option">
              <label>
                <input
                  type="checkbox"
                  checked={rectificationOptions.include_interactome_analysis}
                  onChange={(e) => handleOptionChange('include_interactome_analysis', e.target.checked)}
                />
                Include Interactome Analysis
              </label>
            </div>
            <div className="option">
              <label>
                Confidence Threshold:
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={rectificationOptions.confidence_threshold}
                  onChange={(e) => handleOptionChange('confidence_threshold', parseFloat(e.target.value))}
                />
                {rectificationOptions.confidence_threshold.toFixed(2)}
              </label>
            </div>
          </div>
        </div>

        <div className="action-buttons">
          <button
            className="btn-analyze"
            onClick={handleAnalyzeEvidence}
            disabled={loading}
          >
            {loading ? 'Analyzing...' : 'Analyze Evidence'}
          </button>
          <button
            className="btn-rectify"
            onClick={handleRectifyEvidence}
            disabled={loading}
          >
            {loading ? 'Rectifying...' : 'Rectify Evidence with AI'}
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}
      </div>

      {analysisResults && (
        <div className="results-section">
          <h3>Analysis Results</h3>
          <div className="results-grid">
            <div className="result-card">
              <h4>Evidence Summary</h4>
              <p>Molecule ID: {analysisResults.molecule_id}</p>
              <p>Evidence Count: {analysisResults.evidence_count}</p>
              <p>Confidence Score: {analysisResults.confidence_score.toFixed(2)}</p>
            </div>

            <div className="result-card">
              <h4>Rectified Evidence</h4>
              <table className="evidence-table">
                <thead>
                  <tr>
                    <th>Source</th>
                    <th>Original Confidence</th>
                    <th>Rectified Confidence</th>
                    <th>Improvement</th>
                  </tr>
                </thead>
                <tbody>
                  {analysisResults.rectified_evidence.map((evidence, index) => (
                    <tr key={index}>
                      <td>{evidence.source}</td>
                      <td>{evidence.original_confidence.toFixed(2)}</td>
                      <td>{evidence.rectified_confidence.toFixed(2)}</td>
                      <td>
                        {(
                          ((evidence.rectified_confidence - evidence.original_confidence) /
                            evidence.original_confidence) *
                          100
                        ).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {rectificationOptions.include_pathway_analysis && pathways.length > 0 && (
            <div className="pathways-section">
              <h4>Reactome Pathways</h4>
              <div className="pathways-grid">
                {pathways.map((pathway, index) => (
                  <div className="pathway-card" key={index}>
                    <h5>{pathway.name}</h5>
                    <p>ID: {pathway.pathway_id}</p>
                    <p>Confidence: {pathway.confidence.toFixed(2)}</p>
                    <p>Molecules: {pathway.molecules.join(', ')}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {rectificationOptions.include_interactome_analysis && interactome.length > 0 && (
            <div className="interactome-section">
              <h4>Interactome Analysis</h4>
              <table className="interactome-table">
                <thead>
                  <tr>
                    <th>Source</th>
                    <th>Target</th>
                    <th>Type</th>
                    <th>Evidence Count</th>
                    <th>Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {interactome.map((interaction, index) => (
                    <tr key={index}>
                      <td>{interaction.source_molecule}</td>
                      <td>{interaction.target_molecule}</td>
                      <td>{interaction.interaction_type}</td>
                      <td>{interaction.evidence_count}</td>
                      <td>{interaction.confidence.toFixed(2)}</td>
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
};

export default EvidenceRectifier; 