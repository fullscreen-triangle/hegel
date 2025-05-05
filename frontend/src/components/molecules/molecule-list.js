import React, { useState, useEffect, useMemo } from "react";

/**
 * MoleculeList component displays a searchable list of molecules
 */
export default function MoleculeList({ molecules, onSelectMolecule, selectedMoleculeId }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredMolecules, setFilteredMolecules] = useState([]);
  const [sortField, setSortField] = useState("name");
  const [sortOrder, setSortOrder] = useState("asc");
  const [filters, setFilters] = useState({
    status: "all", // "all", "valid", "invalid"
    confidence: 0, // minimum confidence threshold (0-1)
    properties: {} // for advanced filtering
  });
  
  // Derived statistics
  const stats = useMemo(() => {
    if (!molecules || !Array.isArray(molecules)) {
      return {
        total: 0,
        valid: 0,
        invalid: 0,
        avgConfidence: 0
      };
    }
    
    const valid = molecules.filter(m => m.is_valid).length;
    const invalid = molecules.length - valid;
    const confidenceSum = molecules
      .filter(m => typeof m.confidence === 'number')
      .reduce((sum, m) => sum + m.confidence, 0);
    const confidenceCount = molecules.filter(m => typeof m.confidence === 'number').length;
    
    return {
      total: molecules.length,
      valid,
      invalid,
      avgConfidence: confidenceCount ? (confidenceSum / confidenceCount) : 0
    };
  }, [molecules]);

  // Filter and sort molecules when data, search term, or sort params change
  useEffect(() => {
    if (!molecules || !Array.isArray(molecules)) {
      setFilteredMolecules([]);
      return;
    }
    
    // Apply filters
    let filtered = molecules;
    
    // Filter by validation status
    if (filters.status !== "all") {
      const isValid = filters.status === "valid";
      filtered = filtered.filter(molecule => molecule.is_valid === isValid);
    }
    
    // Filter by confidence threshold
    if (filters.confidence > 0) {
      filtered = filtered.filter(
        molecule => typeof molecule.confidence === 'number' && molecule.confidence >= filters.confidence
      );
    }
    
    // Apply search term filter
    if (searchTerm) {
      const searchTermLower = searchTerm.toLowerCase();
      filtered = filtered.filter(
        molecule => 
          (molecule.name && molecule.name.toLowerCase().includes(searchTermLower)) ||
          (molecule.id && molecule.id.toLowerCase().includes(searchTermLower)) ||
          (molecule.smiles && molecule.smiles.toLowerCase().includes(searchTermLower)) ||
          (molecule.formula && molecule.formula.toLowerCase().includes(searchTermLower))
      );
    }
    
    // Sort molecules based on sort field and order
    const sorted = [...filtered].sort((a, b) => {
      let valA = a[sortField] || "";
      let valB = b[sortField] || "";
      
      // Special handling for confidence to sort numerically
      if (sortField === 'confidence') {
        valA = typeof valA === 'number' ? valA : 0;
        valB = typeof valB === 'number' ? valB : 0;
      }
      
      // Handle strings (case-insensitive) and numbers
      if (typeof valA === "string" && typeof valB === "string") {
        valA = valA.toLowerCase();
        valB = valB.toLowerCase();
      }
      
      // Null/undefined values should sort last regardless of order
      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;
      
      // Perform actual comparison
      if (valA < valB) return sortOrder === "asc" ? -1 : 1;
      if (valA > valB) return sortOrder === "asc" ? 1 : -1;
      return 0;
    });
    
    setFilteredMolecules(sorted);
  }, [molecules, searchTerm, sortField, sortOrder, filters]);

  // Handle sort toggle
  const handleSort = (field) => {
    if (field === sortField) {
      // Toggle order if same field
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      // Set new field and default to ascending
      setSortField(field);
      setSortOrder("asc");
    }
  };

  // Get sort indicator icon
  const getSortIndicator = (field) => {
    if (field !== sortField) return null;
    return sortOrder === "asc" ? "↑" : "↓";
  };

  // Handle search input change
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };
  
  // Handle filter changes
  const handleFilterChange = (filterType, value) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: value
    }));
  };
  
  // Handle clear filters
  const handleClearFilters = () => {
    setFilters({
      status: "all",
      confidence: 0,
      properties: {}
    });
    setSearchTerm("");
  };
  
  // Get the confidence level display
  const getConfidenceLevel = (confidence) => {
    if (typeof confidence !== 'number') return "Unknown";
    if (confidence >= 0.9) return "High";
    if (confidence >= 0.7) return "Medium";
    return "Low";
  };
  
  // Get the confidence color class
  const getConfidenceColorClass = (confidence) => {
    if (typeof confidence !== 'number') return "";
    if (confidence >= 0.9) return "high";
    if (confidence >= 0.7) return "medium";
    return "low";
  };

  return (
    <div className="molecule_list_container">
      <div className="molecule_list_toolbar">
        <div className="molecule_list_search">
          <input 
            type="text" 
            placeholder="Search molecules..." 
            value={searchTerm}
            onChange={handleSearchChange}
            className="search_input"
          />
        </div>
        
        <div className="molecule_list_filters">
          <div className="filter_group">
            <label>Status:</label>
            <select 
              value={filters.status}
              onChange={(e) => handleFilterChange("status", e.target.value)}
              className="filter_select"
            >
              <option value="all">All</option>
              <option value="valid">Valid only</option>
              <option value="invalid">Invalid only</option>
            </select>
          </div>
          
          <div className="filter_group">
            <label>Min Confidence:</label>
            <select 
              value={filters.confidence}
              onChange={(e) => handleFilterChange("confidence", parseFloat(e.target.value))}
              className="filter_select"
            >
              <option value="0">Any</option>
              <option value="0.5">50% or higher</option>
              <option value="0.7">70% or higher</option>
              <option value="0.9">90% or higher</option>
            </select>
          </div>
          
          <button 
            onClick={handleClearFilters}
            className="clear_filters_btn"
            disabled={filters.status === "all" && filters.confidence === 0 && !searchTerm}
          >
            Clear Filters
          </button>
        </div>
      </div>
      
      <div className="list_summary">
        <div className="list_stats">
          <span className="stat_item">
            Total: <strong>{stats.total}</strong>
          </span>
          <span className="stat_item stat_valid">
            Valid: <strong>{stats.valid}</strong>
          </span>
          <span className="stat_item stat_invalid">
            Invalid: <strong>{stats.invalid}</strong>
          </span>
          <span className="stat_item">
            Avg. Confidence: <strong>{(stats.avgConfidence * 100).toFixed(1)}%</strong>
          </span>
        </div>
        
        <div className="filtered_stats">
          Showing {filteredMolecules.length} of {molecules?.length || 0} molecules
        </div>
      </div>
      
      {filteredMolecules.length > 0 ? (
        <div className="molecule_list">
          <div className="molecule_list_header">
            <div 
              className={`molecule_list_column id ${sortField === "id" ? "sorted" : ""}`}
              onClick={() => handleSort("id")}
            >
              ID {getSortIndicator("id")}
            </div>
            <div 
              className={`molecule_list_column name ${sortField === "name" ? "sorted" : ""}`}
              onClick={() => handleSort("name")}
            >
              Name {getSortIndicator("name")}
            </div>
            <div 
              className={`molecule_list_column formula ${sortField === "formula" ? "sorted" : ""}`}
              onClick={() => handleSort("formula")}
            >
              Formula {getSortIndicator("formula")}
            </div>
            <div 
              className={`molecule_list_column status ${sortField === "is_valid" ? "sorted" : ""}`}
              onClick={() => handleSort("is_valid")}
            >
              Status {getSortIndicator("is_valid")}
            </div>
            <div 
              className={`molecule_list_column confidence ${sortField === "confidence" ? "sorted" : ""}`}
              onClick={() => handleSort("confidence")}
            >
              Confidence {getSortIndicator("confidence")}
            </div>
          </div>
          
          {filteredMolecules.map(molecule => (
            <div 
              key={molecule.id} 
              className={`molecule_list_item ${selectedMoleculeId === molecule.id ? "selected" : ""}`}
              onClick={() => onSelectMolecule(molecule)}
            >
              <div className="molecule_list_column id">{molecule.id}</div>
              <div className="molecule_list_column name">{molecule.name || "Unknown"}</div>
              <div className="molecule_list_column formula">{molecule.formula || "N/A"}</div>
              <div className="molecule_list_column status">
                <span className={`status_badge ${molecule.is_valid ? "valid" : "invalid"}`}>
                  {molecule.is_valid ? "Valid" : "Invalid"}
                </span>
              </div>
              <div className="molecule_list_column confidence">
                {typeof molecule.confidence === 'number' ? (
                  <div className="confidence_display">
                    <div className="confidence_bar">
                      <div 
                        className={`confidence_fill ${getConfidenceColorClass(molecule.confidence)}`}
                        style={{ width: `${molecule.confidence * 100}%` }}
                      ></div>
                    </div>
                    <span className="confidence_value">
                      {(molecule.confidence * 100).toFixed(0)}%
                    </span>
                    <span className="confidence_label">
                      {getConfidenceLevel(molecule.confidence)}
                    </span>
                  </div>
                ) : (
                  <span>N/A</span>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="molecule_list_empty">
          {molecules && molecules.length > 0 
            ? "No molecules match your search criteria"
            : "No molecules available"
          }
          {filters.status !== "all" || filters.confidence > 0 || searchTerm ? (
            <button onClick={handleClearFilters} className="empty_clear_btn">
              Clear Filters
            </button>
          ) : null}
        </div>
      )}
    </div>
  );
} 