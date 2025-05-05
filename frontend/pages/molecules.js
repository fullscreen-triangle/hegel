import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import Link from 'next/link';
import axios from 'axios';
import Layout from '../src/layout/Layout';

const MoleculesPage = () => {
  const router = useRouter();
  const [molecules, setMolecules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  
  // Fetch molecules data
  useEffect(() => {
    const fetchMolecules = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/api/molecules');
        setMolecules(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching molecules:', err);
        setError('Failed to load molecules');
      } finally {
        setLoading(false);
      }
    };

    fetchMolecules();
  }, []);

  // Filter and search molecules
  const filteredMolecules = molecules.filter(molecule => {
    // Apply search term filter
    const matchesSearch = 
      searchTerm === '' || 
      (molecule.name && molecule.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (molecule.id && molecule.id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (molecule.formula && molecule.formula.toLowerCase().includes(searchTerm.toLowerCase()));

    // Apply type filter
    if (filterType === 'all') {
      return matchesSearch;
    } else if (filterType === 'has_genomics' && molecule.has_genomics_data) {
      return matchesSearch;
    } else if (filterType === 'has_mass_spec' && molecule.has_mass_spec_data) {
      return matchesSearch;
    } else if (filterType === 'high_confidence' && molecule.confidence_score >= 0.8) {
      return matchesSearch;
    }

    return false;
  });

  // Handle search input change
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  // Handle filter type change
  const handleFilterChange = (e) => {
    setFilterType(e.target.value);
  };

  // Navigate to molecule detail page
  const handleMoleculeClick = (moleculeId) => {
    router.push(`/molecule/${moleculeId}`);
  };

  return (
    <Layout>
      <Head>
        <title>Molecules | Hegel</title>
      </Head>

      <div className="container pt-100 pb-100">
        <div className="molecules-header">
          <h1>Molecules</h1>
          <p>View and analyze molecular data from genomics and mass spectrometry experiments.</p>
        </div>

        <div className="filters-container">
          <div className="search-box">
            <input
              type="text"
              placeholder="Search by name, ID, or formula..."
              value={searchTerm}
              onChange={handleSearchChange}
            />
          </div>

          <div className="filter-options">
            <label htmlFor="filter-type">Filter by:</label>
            <select
              id="filter-type"
              value={filterType}
              onChange={handleFilterChange}
            >
              <option value="all">All Molecules</option>
              <option value="has_genomics">Has Genomics Data</option>
              <option value="has_mass_spec">Has Mass Spec Data</option>
              <option value="high_confidence">High Confidence (&gt;80%)</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="loading-spinner">Loading molecules...</div>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : (
          <div className="molecules-grid">
            {filteredMolecules.length > 0 ? (
              filteredMolecules.map((molecule) => (
                <div
                  key={molecule.id}
                  className="molecule-card"
                  onClick={() => handleMoleculeClick(molecule.id)}
                >
                  <div className="molecule-structure">
                    {molecule.smiles ? (
                      <img
                        src={`https://cactus.nci.nih.gov/chemical/structure/${encodeURIComponent(molecule.smiles)}/image`}
                        alt={`Structure of ${molecule.name || molecule.id}`}
                        onError={(e) => {
                          e.target.onerror = null;
                          e.target.src = '/placeholder-structure.png';
                        }}
                      />
                    ) : (
                      <div className="no-structure">No structure available</div>
                    )}
                  </div>
                  <div className="molecule-info">
                    <h3 className="molecule-name">{molecule.name || `Molecule ${molecule.id}`}</h3>
                    <div className="molecule-properties">
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
                    <div className="molecule-data-indicators">
                      {molecule.has_genomics_data && (
                        <span className="data-indicator genomics">Genomics</span>
                      )}
                      {molecule.has_mass_spec_data && (
                        <span className="data-indicator mass-spec">Mass Spec</span>
                      )}
                      {molecule.confidence_score && (
                        <span 
                          className={`confidence-indicator ${
                            molecule.confidence_score >= 0.8 ? 'high' : 
                            molecule.confidence_score >= 0.5 ? 'medium' : 'low'
                          }`}
                        >
                          Confidence: {(molecule.confidence_score * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="no-results">No molecules found matching your criteria.</div>
            )}
          </div>
        )}
      </div>

      <style jsx>{`
        .molecules-header {
          margin-bottom: 30px;
        }

        .filters-container {
          display: flex;
          justify-content: space-between;
          margin-bottom: 30px;
          padding: 15px;
          background-color: #f5f5f5;
          border-radius: 5px;
          align-items: center;
        }

        .search-box input {
          width: 300px;
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 16px;
        }

        .filter-options {
          display: flex;
          align-items: center;
        }

        .filter-options label {
          margin-right: 10px;
        }

        .filter-options select {
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 16px;
        }

        .molecules-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 20px;
        }

        .molecule-card {
          border: 1px solid #ddd;
          border-radius: 5px;
          overflow: hidden;
          background-color: white;
          cursor: pointer;
          transition: transform 0.2s, box-shadow 0.2s;
        }

        .molecule-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }

        .molecule-structure {
          height: 200px;
          display: flex;
          align-items: center;
          justify-content: center;
          background-color: #f9f9f9;
          padding: 15px;
        }

        .molecule-structure img {
          max-width: 100%;
          max-height: 100%;
        }

        .no-structure {
          color: #999;
          font-style: italic;
        }

        .molecule-info {
          padding: 15px;
        }

        .molecule-name {
          margin-top: 0;
          margin-bottom: 10px;
          font-size: 18px;
        }

        .molecule-properties {
          display: flex;
          flex-direction: column;
          gap: 5px;
          font-size: 14px;
          color: #666;
          margin-bottom: 15px;
        }

        .molecule-data-indicators {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }

        .data-indicator {
          font-size: 12px;
          padding: 3px 8px;
          border-radius: 12px;
          background-color: #f0f0f0;
          color: #666;
        }

        .data-indicator.genomics {
          background-color: #e3f2fd;
          color: #1976d2;
        }

        .data-indicator.mass-spec {
          background-color: #e8f5e9;
          color: #388e3c;
        }

        .confidence-indicator {
          font-size: 12px;
          padding: 3px 8px;
          border-radius: 12px;
          font-weight: bold;
        }

        .confidence-indicator.high {
          background-color: #e8f5e9;
          color: #388e3c;
        }

        .confidence-indicator.medium {
          background-color: #fff3e0;
          color: #f57c00;
        }

        .confidence-indicator.low {
          background-color: #ffebee;
          color: #d32f2f;
        }

        .no-results {
          grid-column: 1 / -1;
          text-align: center;
          padding: 30px;
          background-color: #f5f5f5;
          border-radius: 5px;
          font-style: italic;
          color: #666;
        }

        .loading-spinner, .error-message {
          text-align: center;
          padding: 30px;
        }
      `}</style>
    </Layout>
  );
};

export default MoleculesPage; 