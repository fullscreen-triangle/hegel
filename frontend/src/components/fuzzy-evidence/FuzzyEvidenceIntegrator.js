import React, { useState, useEffect } from 'react';
import './FuzzyEvidenceIntegrator.css';

const FuzzyEvidenceIntegrator = ({ moleculeId, evidenceItems = [] }) => {
  const [integrationResult, setIntegrationResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [config, setConfig] = useState({
    enable_prediction: true,
    enable_network_learning: true,
    confidence_threshold: 0.5,
    prediction_threshold: 0.7
  });
  const [networkStats, setNetworkStats] = useState(null);
  const [linguisticVariables, setLinguisticVariables] = useState(null);

  useEffect(() => {
    // Load linguistic variables on component mount
    loadLinguisticVariables();
  }, []);

  const loadLinguisticVariables = async () => {
    try {
      const response = await fetch('/api/fuzzy-evidence/linguistic-variables');
      const data = await response.json();
      setLinguisticVariables(data);
    } catch (err) {
      console.error('Failed to load linguistic variables:', err);
    }
  };

  const integrateEvidence = async () => {
    if (!moleculeId || evidenceItems.length === 0) {
      setError('Molecule ID and evidence items are required');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/fuzzy-evidence/integrate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          molecule_id: moleculeId,
          evidence_items: evidenceItems,
          integration_config: config,
          enable_prediction: config.enable_prediction,
          enable_network_learning: config.enable_network_learning
        })
      });

      if (!response.ok) {
        throw new Error(`Integration failed: ${response.statusText}`);
      }

      const result = await response.json();
      setIntegrationResult(result);
      
      // Load network statistics
      await loadNetworkStatistics();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const loadNetworkStatistics = async () => {
    try {
      const response = await fetch(`/api/fuzzy-evidence/network-stats/${moleculeId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const stats = await response.json();
        setNetworkStats(stats);
      }
    } catch (err) {
      console.error('Failed to load network statistics:', err);
    }
  };

  const predictMissingEvidence = async () => {
    if (!moleculeId || !evidenceItems.length) return;

    setIsLoading(true);
    try {
      const partialEvidenceIds = evidenceItems.slice(0, Math.floor(evidenceItems.length / 2))
        .map(item => item.id);

      const response = await fetch(`/api/fuzzy-evidence/predict-evidence/${moleculeId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(partialEvidenceIds)
      });

      if (response.ok) {
        const predictions = await response.json();
        setIntegrationResult(prev => ({
          ...prev,
          predictions: predictions
        }));
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const renderFuzzyMemberships = (memberships) => {
    return (
      <div className="fuzzy-memberships">
        {Object.entries(memberships).map(([term, value]) => (
          <div key={term} className="membership-item">
            <span className="membership-term">{term}</span>
            <div className="membership-bar">
              <div 
                className="membership-fill" 
                style={{ width: `${value * 100}%` }}
              />
            </div>
            <span className="membership-value">{value.toFixed(3)}</span>
          </div>
        ))}
      </div>
    );
  };

  const renderEnhancedConfidence = (enhanced) => {
    return (
      <div className="enhanced-confidence">
        <div className="confidence-comparison">
          <div className="confidence-item">
            <label>Original:</label>
            <span className="confidence-value">{enhanced.original_confidence.toFixed(3)}</span>
          </div>
          <div className="confidence-item">
            <label>Fuzzy:</label>
            <span className="confidence-value">{enhanced.fuzzy_confidence.toFixed(3)}</span>
          </div>
          <div className="confidence-item">
            <label>Bayesian:</label>
            <span className="confidence-value">{enhanced.bayesian_posterior.toFixed(3)}</span>
          </div>
          <div className="confidence-item">
            <label>Network:</label>
            <span className="confidence-value">{enhanced.network_influence.toFixed(3)}</span>
          </div>
          <div className="confidence-item final">
            <label>Final:</label>
            <span className="confidence-value">{enhanced.final_confidence.toFixed(3)}</span>
          </div>
        </div>
        <div className="uncertainty-bounds">
          <label>Uncertainty Bounds:</label>
          <span>[{enhanced.uncertainty_bounds[0].toFixed(3)}, {enhanced.uncertainty_bounds[1].toFixed(3)}]</span>
        </div>
      </div>
    );
  };

  const renderNetworkVisualization = () => {
    if (!integrationResult) return null;

    return (
      <div className="network-visualization">
        <h4>Evidence Network</h4>
        <div className="network-stats">
          {networkStats && (
            <>
              <div className="stat-item">
                <label>Nodes:</label>
                <span>{networkStats.node_count}</span>
              </div>
              <div className="stat-item">
                <label>Edges:</label>
                <span>{networkStats.edge_count}</span>
              </div>
              <div className="stat-item">
                <label>Avg Confidence:</label>
                <span>{networkStats.avg_confidence.toFixed(3)}</span>
              </div>
              <div className="stat-item">
                <label>Conflicts:</label>
                <span>{networkStats.conflict_count}</span>
              </div>
              <div className="stat-item">
                <label>Coherence:</label>
                <span className={`coherence-score ${networkStats.coherence_score > 0.7 ? 'high' : networkStats.coherence_score > 0.4 ? 'medium' : 'low'}`}>
                  {networkStats.coherence_score.toFixed(3)}
                </span>
              </div>
            </>
          )}
        </div>
      </div>
    );
  };

  const renderLinguisticVariables = () => {
    if (!linguisticVariables) return null;

    return (
      <div className="linguistic-variables">
        <h4>Fuzzy Linguistic Variables</h4>
        {Object.entries(linguisticVariables).map(([varName, variable]) => (
          <div key={varName} className="linguistic-variable">
            <h5>{variable.name}</h5>
            <div className="universe">
              Universe: [{variable.universe[0]}, {variable.universe[1]}]
            </div>
            <div className="terms">
              {Object.entries(variable.terms).map(([termName, term]) => (
                <div key={termName} className="term">
                  <span className="term-name">{termName}</span>
                  <span className="term-type">({term.type})</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="fuzzy-evidence-integrator">
      <div className="integrator-header">
        <h3>Fuzzy-Bayesian Evidence Integration</h3>
        <p>Hybrid fuzzy logic and Bayesian inference for molecular evidence rectification</p>
      </div>

      <div className="integration-config">
        <h4>Integration Configuration</h4>
        <div className="config-options">
          <label>
            <input
              type="checkbox"
              checked={config.enable_prediction}
              onChange={(e) => setConfig(prev => ({ ...prev, enable_prediction: e.target.checked }))}
            />
            Enable Evidence Prediction
          </label>
          <label>
            <input
              type="checkbox"
              checked={config.enable_network_learning}
              onChange={(e) => setConfig(prev => ({ ...prev, enable_network_learning: e.target.checked }))}
            />
            Enable Network Learning
          </label>
          <label>
            Confidence Threshold:
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={config.confidence_threshold}
              onChange={(e) => setConfig(prev => ({ ...prev, confidence_threshold: parseFloat(e.target.value) }))}
            />
            <span>{config.confidence_threshold}</span>
          </label>
          <label>
            Prediction Threshold:
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={config.prediction_threshold}
              onChange={(e) => setConfig(prev => ({ ...prev, prediction_threshold: parseFloat(e.target.value) }))}
            />
            <span>{config.prediction_threshold}</span>
          </label>
        </div>
      </div>

      <div className="integration-controls">
        <button 
          onClick={integrateEvidence} 
          disabled={isLoading || !moleculeId || evidenceItems.length === 0}
          className="integrate-button"
        >
          {isLoading ? 'Integrating...' : 'Integrate Evidence'}
        </button>
        <button 
          onClick={predictMissingEvidence} 
          disabled={isLoading || !integrationResult}
          className="predict-button"
        >
          Predict Missing Evidence
        </button>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {integrationResult && (
        <div className="integration-results">
          <div className="results-summary">
            <h4>Integration Results</h4>
            <div className="summary-stats">
              <div className="stat">
                <label>Original Evidence:</label>
                <span>{integrationResult.original_evidence_count}</span>
              </div>
              <div className="stat">
                <label>Integrated Evidence:</label>
                <span>{integrationResult.integrated_evidence_count}</span>
              </div>
              <div className="stat">
                <label>Predictions:</label>
                <span>{integrationResult.predictions.length}</span>
              </div>
              <div className="stat">
                <label>Network Coherence:</label>
                <span className={`coherence ${integrationResult.network_coherence_score > 0.7 ? 'high' : integrationResult.network_coherence_score > 0.4 ? 'medium' : 'low'}`}>
                  {integrationResult.network_coherence_score.toFixed(3)}
                </span>
              </div>
            </div>
          </div>

          {renderNetworkVisualization()}

          <div className="enhanced-confidences">
            <h4>Enhanced Confidence Scores</h4>
            {Object.entries(integrationResult.enhanced_confidences).map(([evidenceId, enhanced]) => (
              <div key={evidenceId} className="evidence-confidence">
                <h5>Evidence: {evidenceId}</h5>
                {renderEnhancedConfidence(enhanced)}
              </div>
            ))}
          </div>

          {integrationResult.predictions.length > 0 && (
            <div className="evidence-predictions">
              <h4>Evidence Predictions</h4>
              {integrationResult.predictions.map((prediction, index) => (
                <div key={index} className="prediction">
                  <div className="prediction-header">
                    <span className="prediction-node">{prediction.node_id}</span>
                    <span className={`prediction-confidence ${prediction.confidence > 0.8 ? 'high' : prediction.confidence > 0.6 ? 'medium' : 'low'}`}>
                      {(prediction.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="prediction-value">
                    Predicted Value: {prediction.predicted_value.toFixed(3)}
                  </div>
                  <div className="prediction-reasoning">
                    {prediction.reasoning}
                  </div>
                  <div className="supporting-evidence">
                    Supporting Evidence: {prediction.supporting_evidence.join(', ')}
                  </div>
                </div>
              ))}
            </div>
          )}

          {integrationResult.integration_errors.length > 0 && (
            <div className="integration-errors">
              <h4>Integration Errors</h4>
              {integrationResult.integration_errors.map((error, index) => (
                <div key={index} className="error-item">
                  {error}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {renderLinguisticVariables()}

      <div className="methodology-explanation">
        <h4>Methodology</h4>
        <div className="explanation-content">
          <p>
            This fuzzy-Bayesian evidence integration system addresses the fundamental limitation 
            of treating biological evidence as binary. Instead, it:
          </p>
          <ul>
            <li><strong>Fuzzy Logic:</strong> Converts confidence scores to continuous membership degrees across linguistic terms (very_low, low, medium, high, very_high)</li>
            <li><strong>Bayesian Inference:</strong> Updates posterior probabilities based on evidence likelihood and prior knowledge</li>
            <li><strong>Network Learning:</strong> Builds evidence relationships and predicts missing evidence based on network structure</li>
            <li><strong>Granular Objectives:</strong> Optimizes evidence integration using multi-criteria objective functions</li>
            <li><strong>Temporal Decay:</strong> Accounts for evidence aging and reliability degradation over time</li>
            <li><strong>Uncertainty Quantification:</strong> Provides confidence intervals and uncertainty bounds for all evidence</li>
          </ul>
          <p>
            The system transforms Hegel from a binary evidence processor into a sophisticated 
            belief network that can reason about evidence uncertainty, predict missing data, 
            and optimize molecular identity validation through granular objective functions.
          </p>
        </div>
      </div>
    </div>
  );
};

export default FuzzyEvidenceIntegrator; 