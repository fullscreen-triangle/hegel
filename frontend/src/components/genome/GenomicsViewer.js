import React, { useState, useEffect } from 'react';
import axios from 'axios';

const GenomicsViewer = ({ moleculeId }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedView, setSelectedView] = useState('expression'); // Options: expression, variants, reads

  // Fetch genomics data for the molecule
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Replace with your actual API endpoint
        const response = await axios.get(`/api/molecule/${moleculeId}/genomics`);
        setData(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching genomics data:', err);
        setError('Failed to load genomics data');
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
    return <div>Loading genomics data...</div>;
  }

  // Show error state
  if (error) {
    return <div className="error-message">{error}</div>;
  }

  // Show empty state
  if (!data) {
    return <div>No genomics data available for this molecule.</div>;
  }

  // Determine what content to show based on data type and selected view
  const renderContent = () => {
    if (!data.findings || data.findings.length === 0) {
      return <div>No findings available in the genomics data.</div>;
    }

    // Filter findings by view type
    const relevantFindings = data.findings.filter(
      finding => finding.finding_type.includes(selectedView)
    );

    if (relevantFindings.length === 0) {
      return <div>No {selectedView} data available.</div>;
    }

    // Render findings based on view type
    switch (selectedView) {
      case 'expression':
        return (
          <div className="expression-data">
            <h4>Gene Expression Results</h4>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Gene</th>
                  <th>Expression Score</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {relevantFindings.map((finding, index) => (
                  <tr key={index}>
                    <td>{finding.details.gene_id || 'N/A'}</td>
                    <td>{finding.score.toFixed(2)}</td>
                    <td>{finding.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );

      case 'variant':
        return (
          <div className="variant-data">
            <h4>Genomic Variants</h4>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Chromosome</th>
                  <th>Position</th>
                  <th>Reference</th>
                  <th>Alternate</th>
                  <th>Quality</th>
                </tr>
              </thead>
              <tbody>
                {relevantFindings.map((finding, index) => (
                  <tr key={index}>
                    <td>{finding.details.chromosome || 'N/A'}</td>
                    <td>{finding.details.position || 'N/A'}</td>
                    <td>{finding.details.reference || 'N/A'}</td>
                    <td>{finding.details.alternate || 'N/A'}</td>
                    <td>{finding.details.quality || 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );

      case 'read':
        return (
          <div className="read-data">
            <h4>Read Count Data</h4>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Region</th>
                  <th>Read Count</th>
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                {relevantFindings.map((finding, index) => (
                  <tr key={index}>
                    <td>{finding.details.region_id || 'N/A'}</td>
                    <td>{finding.details.read_count || 'N/A'}</td>
                    <td>{finding.score.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );

      default:
        return <div>Select a view to see genomics data.</div>;
    }
  };

  return (
    <div className="genomics-viewer">
      <h3>Genomics Data</h3>
      <div className="confidence-score">
        <strong>Confidence Score:</strong> {data.confidence.toFixed(2)}
      </div>

      <div className="view-selectors">
        <button
          className={selectedView === 'expression' ? 'active' : ''}
          onClick={() => setSelectedView('expression')}
        >
          Gene Expression
        </button>
        <button
          className={selectedView === 'variant' ? 'active' : ''}
          onClick={() => setSelectedView('variant')}
        >
          Variants
        </button>
        <button
          className={selectedView === 'read' ? 'active' : ''}
          onClick={() => setSelectedView('read')}
        >
          Read Counts
        </button>
      </div>

      <div className="content-container">{renderContent()}</div>

      <div className="metadata">
        {data.processing_metadata && (
          <>
            <h4>Metadata</h4>
            <ul>
              {Object.entries(data.processing_metadata).map(([key, value]) => (
                <li key={key}>
                  <strong>{key}:</strong> {JSON.stringify(value)}
                </li>
              ))}
            </ul>
          </>
        )}
      </div>

      <style jsx>{`
        .genomics-viewer {
          font-family: Arial, sans-serif;
          padding: 15px;
          background-color: #f9f9f9;
          border-radius: 5px;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .confidence-score {
          margin-bottom: 15px;
          font-size: 16px;
        }

        .view-selectors {
          display: flex;
          margin-bottom: 20px;
          gap: 10px;
        }

        .view-selectors button {
          padding: 8px 15px;
          background: #e0e0e0;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }

        .view-selectors button.active {
          background: #007bff;
          color: white;
        }

        .content-container {
          margin-bottom: 20px;
        }

        .data-table {
          width: 100%;
          border-collapse: collapse;
        }

        .data-table th, .data-table td {
          padding: 8px;
          border: 1px solid #ddd;
        }

        .data-table th {
          background-color: #f2f2f2;
          text-align: left;
        }

        .data-table tr:nth-child(even) {
          background-color: #f9f9f9;
        }

        .metadata {
          font-size: 14px;
        }

        .metadata ul {
          list-style-type: none;
          padding-left: 0;
        }

        .metadata li {
          margin-bottom: 5px;
        }
      `}</style>
    </div>
  );
};

export default GenomicsViewer; 