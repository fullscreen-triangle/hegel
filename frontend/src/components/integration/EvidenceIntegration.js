import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Radar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';

// Register required Chart.js components
ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

const EvidenceIntegration = ({ moleculeId }) => {
  const [integratedData, setIntegratedData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTab, setSelectedTab] = useState('overview');

  // Fetch integrated evidence for the molecule
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Replace with your actual API endpoint
        const response = await axios.get(`/api/evidence/${moleculeId}`);
        setIntegratedData(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching integrated evidence:', err);
        setError('Failed to load evidence integration data');
      } finally {
        setLoading(false);
      }
    };

    if (moleculeId) {
      fetchData();
    }
  }, [moleculeId]);

  // Show loading state
  if (loading) {
    return <div>Loading evidence integration data...</div>;
  }

  // Show error state
  if (error) {
    return <div className="error-message">{error}</div>;
  }

  // Show empty state
  if (!integratedData) {
    return <div>No integrated evidence available for this molecule.</div>;
  }

  // Prepare data for the radar chart
  const getRadarChartData = () => {
    if (!integratedData.evidence_items) {
      return null;
    }

    // Group evidence by type
    const evidenceByType = {};
    integratedData.evidence_items.forEach(item => {
      if (!evidenceByType[item.evidence_type]) {
        evidenceByType[item.evidence_type] = [];
      }
      evidenceByType[item.evidence_type].push(item);
    });

    // Calculate average confidence for each type
    const evidenceTypes = Object.keys(evidenceByType);
    const confidenceScores = evidenceTypes.map(type => {
      const items = evidenceByType[type];
      const avgConfidence = items.reduce((sum, item) => sum + item.confidence, 0) / items.length;
      return avgConfidence;
    });

    return {
      labels: evidenceTypes,
      datasets: [
        {
          label: 'Original Confidence',
          data: confidenceScores,
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          borderColor: 'rgb(54, 162, 235)',
          borderWidth: 1,
        },
        {
          label: 'Rectified Confidence',
          data: confidenceScores.map(score => Math.min(score * 1.2, 1.0)), // Simple simulation of rectification
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          borderColor: 'rgb(255, 99, 132)',
          borderWidth: 1,
        },
      ],
    };
  };

  // Radar chart options
  const radarOptions = {
    scales: {
      r: {
        angleLines: {
          display: true,
        },
        suggestedMin: 0,
        suggestedMax: 1,
      },
    },
  };

  // Render the overview tab
  const renderOverview = () => {
    const radarData = getRadarChartData();

    return (
      <div className="overview-tab">
        <div className="confidence-summary">
          <h4>Confidence Summary</h4>
          <div className="confidence-score">
            <div className="score-circle">
              <span className="score-value">
                {integratedData.aggregate_confidence
                  ? integratedData.aggregate_confidence.toFixed(2)
                  : 'N/A'}
              </span>
            </div>
            <div className="score-label">Aggregate Confidence</div>
          </div>
          
          <div className="confidence-details">
            <p>
              Based on {integratedData.evidence_count || 0} pieces of evidence
              across {integratedData.evidence_types?.length || 0} different sources.
            </p>
            <p>
              Last updated: {integratedData.last_updated || 'Unknown'}
            </p>
          </div>
        </div>

        {radarData && (
          <div className="radar-chart">
            <h4>Evidence Type Confidence</h4>
            <Radar data={radarData} options={radarOptions} />
          </div>
        )}
      </div>
    );
  };

  // Render the evidence details tab
  const renderEvidenceDetails = () => {
    if (!integratedData.evidence_items || integratedData.evidence_items.length === 0) {
      return <div>No detailed evidence items available.</div>;
    }

    return (
      <div className="evidence-details-tab">
        <h4>Evidence Items</h4>
        <table className="evidence-table">
          <thead>
            <tr>
              <th>Source</th>
              <th>Type</th>
              <th>Original Confidence</th>
              <th>Rectified Confidence</th>
              <th>Adjustment Reason</th>
            </tr>
          </thead>
          <tbody>
            {integratedData.evidence_items.map((item, index) => (
              <tr key={index}>
                <td>{item.source}</td>
                <td>{item.evidence_type}</td>
                <td>{item.original_confidence?.toFixed(2) || item.confidence?.toFixed(2)}</td>
                <td>{item.rectified_confidence?.toFixed(2) || 'N/A'}</td>
                <td>{item.adjustment_reason || 'No rectification applied'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // Render the conflicts tab
  const renderConflicts = () => {
    if (!integratedData.conflicts || integratedData.conflicts.length === 0) {
      return <div>No conflicts detected in the evidence.</div>;
    }

    return (
      <div className="conflicts-tab">
        <h4>Detected Conflicts</h4>
        <div className="conflicts-list">
          {integratedData.conflicts.map((conflict, index) => (
            <div key={index} className="conflict-item">
              <h5>Conflict #{index + 1}</h5>
              <p><strong>Description:</strong> {conflict.description}</p>
              <p><strong>Severity:</strong> {conflict.severity.toFixed(2)}</p>
              <p><strong>Involved Evidence:</strong> {conflict.evidence_ids.join(', ')}</p>
              
              {conflict.resolution_suggestions && conflict.resolution_suggestions.length > 0 && (
                <>
                  <p><strong>Resolution Suggestions:</strong></p>
                  <ul>
                    {conflict.resolution_suggestions.map((suggestion, idx) => (
                      <li key={idx}>{suggestion}</li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Main render function
  return (
    <div className="evidence-integration">
      <h3>Evidence Integration and Rectification</h3>
      
      <div className="tabs">
        <button 
          className={selectedTab === 'overview' ? 'active' : ''} 
          onClick={() => setSelectedTab('overview')}
        >
          Overview
        </button>
        <button 
          className={selectedTab === 'evidence' ? 'active' : ''} 
          onClick={() => setSelectedTab('evidence')}
        >
          Evidence Details
        </button>
        <button 
          className={selectedTab === 'conflicts' ? 'active' : ''} 
          onClick={() => setSelectedTab('conflicts')}
        >
          Conflicts
        </button>
      </div>
      
      <div className="tab-content">
        {selectedTab === 'overview' && renderOverview()}
        {selectedTab === 'evidence' && renderEvidenceDetails()}
        {selectedTab === 'conflicts' && renderConflicts()}
      </div>

      <style jsx>{`
        .evidence-integration {
          font-family: Arial, sans-serif;
          padding: 20px;
          background-color: #f9f9f9;
          border-radius: 5px;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .tabs {
          display: flex;
          margin-bottom: 20px;
          border-bottom: 1px solid #ddd;
        }

        .tabs button {
          padding: 10px 20px;
          background: none;
          border: none;
          border-bottom: 2px solid transparent;
          cursor: pointer;
          font-size: 16px;
          margin-right: 15px;
        }

        .tabs button.active {
          border-bottom: 2px solid #007bff;
          color: #007bff;
        }

        .tab-content {
          padding: 15px 0;
        }

        .confidence-summary {
          display: flex;
          margin-bottom: 30px;
          align-items: center;
        }

        .confidence-score {
          text-align: center;
          margin-right: 30px;
        }

        .score-circle {
          width: 100px;
          height: 100px;
          border-radius: 50%;
          background-color: #007bff;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 10px;
        }

        .score-value {
          color: white;
          font-size: 24px;
          font-weight: bold;
        }

        .radar-chart {
          margin-top: 20px;
          max-width: 500px;
        }

        .evidence-table {
          width: 100%;
          border-collapse: collapse;
        }

        .evidence-table th, .evidence-table td {
          padding: 10px;
          border: 1px solid #ddd;
          text-align: left;
        }

        .evidence-table th {
          background-color: #f2f2f2;
        }

        .conflict-item {
          background-color: #fff;
          padding: 15px;
          margin-bottom: 15px;
          border-radius: 5px;
          border-left: 4px solid #dc3545;
        }

        .conflict-item h5 {
          margin-top: 0;
          color: #dc3545;
        }
      `}</style>
    </div>
  );
};

export default EvidenceIntegration; 