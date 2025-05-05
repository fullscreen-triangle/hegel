import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import axios from 'axios';
import Layout from '../../src/layout/Layout';
import MassSpecViewer from '../../src/components/spectra/MassSpecViewer';
import GenomicsViewer from '../../src/components/genome/GenomicsViewer';
import EvidenceIntegration from '../../src/components/integration/EvidenceIntegration';

const MoleculeDetailPage = () => {
  const router = useRouter();
  const { id } = router.query;
  
  const [molecule, setMolecule] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    const fetchMoleculeData = async () => {
      if (!id) return;
      
      try {
        setLoading(true);
        const response = await axios.get(`/api/molecule/${id}`);
        setMolecule(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching molecule data:', err);
        setError('Failed to load molecule data');
      } finally {
        setLoading(false);
      }
    };

    fetchMoleculeData();
  }, [id]);

  if (loading) {
    return (
      <Layout>
        <div className="container pt-100 pb-100">
          <div className="loading-spinner">Loading molecule data...</div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="container pt-100 pb-100">
          <div className="error-message">{error}</div>
        </div>
      </Layout>
    );
  }

  if (!molecule) {
    return (
      <Layout>
        <div className="container pt-100 pb-100">
          <div>Molecule not found</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <Head>
        <title>{molecule.name || `Molecule ${id}`} | Hegel</title>
      </Head>

      <div className="container pt-100 pb-100">
        <div className="molecule-header">
          <h1 className="molecule-title">{molecule.name || `Molecule ${id}`}</h1>
          <div className="molecule-meta">
            <span className="molecule-id">ID: {molecule.id}</span>
            {molecule.formula && (
              <span className="molecule-formula">Formula: {molecule.formula}</span>
            )}
            {molecule.molecular_weight && (
              <span className="molecule-weight">
                MW: {molecule.molecular_weight.toFixed(2)} Da
              </span>
            )}
          </div>
        </div>

        <div className="tabs-container">
          <div className="tabs">
            <button
              className={activeTab === 'overview' ? 'active' : ''}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            <button
              className={activeTab === 'mass-spec' ? 'active' : ''}
              onClick={() => setActiveTab('mass-spec')}
            >
              Mass Spectrometry
            </button>
            <button
              className={activeTab === 'genomics' ? 'active' : ''}
              onClick={() => setActiveTab('genomics')}
            >
              Genomics
            </button>
            <button
              className={activeTab === 'evidence' ? 'active' : ''}
              onClick={() => setActiveTab('evidence')}
            >
              Evidence Integration
            </button>
          </div>

          <div className="tab-content">
            {activeTab === 'overview' && (
              <div className="overview-tab">
                <div className="molecule-structure">
                  {molecule.smiles && (
                    <div className="smiles-visualization">
                      <h3>Molecular Structure</h3>
                      <div className="smiles-container">
                        <img
                          src={`https://cactus.nci.nih.gov/chemical/structure/${encodeURIComponent(molecule.smiles)}/image`}
                          alt={`Structure of ${molecule.name || molecule.id}`}
                          onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = '/placeholder-structure.png';
                          }}
                        />
                      </div>
                      <div className="smiles-text">
                        <strong>SMILES:</strong> {molecule.smiles}
                      </div>
                    </div>
                  )}
                </div>

                <div className="molecule-properties">
                  <h3>Properties</h3>
                  <table className="properties-table">
                    <tbody>
                      {molecule.properties &&
                        Object.entries(molecule.properties).map(([key, value]) => (
                          <tr key={key}>
                            <th>{key}</th>
                            <td>{JSON.stringify(value)}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'mass-spec' && (
              <div className="mass-spec-tab">
                <MassSpecViewer moleculeId={id} />
              </div>
            )}

            {activeTab === 'genomics' && (
              <div className="genomics-tab">
                <GenomicsViewer moleculeId={id} />
              </div>
            )}

            {activeTab === 'evidence' && (
              <div className="evidence-tab">
                <EvidenceIntegration moleculeId={id} />
              </div>
            )}
          </div>
        </div>
      </div>

      <style jsx>{`
        .molecule-header {
          margin-bottom: 30px;
        }

        .molecule-title {
          font-size: 32px;
          margin-bottom: 10px;
        }

        .molecule-meta {
          display: flex;
          gap: 20px;
          font-size: 16px;
          color: #666;
        }

        .tabs-container {
          margin-top: 30px;
        }

        .tabs {
          display: flex;
          border-bottom: 1px solid #ddd;
          margin-bottom: 20px;
        }

        .tabs button {
          padding: 12px 20px;
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
          padding: 20px;
          background-color: #f9f9f9;
          border-radius: 5px;
        }

        .smiles-container {
          max-width: 400px;
          margin: 20px 0;
          background-color: white;
          padding: 15px;
          border-radius: 5px;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .smiles-container img {
          max-width: 100%;
        }

        .properties-table {
          width: 100%;
          border-collapse: collapse;
        }

        .properties-table th,
        .properties-table td {
          padding: 10px;
          border: 1px solid #ddd;
          text-align: left;
        }

        .properties-table th {
          width: 30%;
          background-color: #f2f2f2;
        }
      `}</style>
    </Layout>
  );
};

export default MoleculeDetailPage; 