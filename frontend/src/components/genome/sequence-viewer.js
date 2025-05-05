import React, { useEffect, useRef, useState } from "react";

/**
 * SequenceViewer component for visualizing DNA/RNA sequences
 */
export default function SequenceViewer({ sequenceData, options }) {
  const containerRef = useRef(null);
  const [selectedRange, setSelectedRange] = useState({ start: 0, end: 0 });
  const [currentView, setCurrentView] = useState({
    start: 0,
    end: 100,
    sequence: ""
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [annotations, setAnnotations] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [highlightIndex, setHighlightIndex] = useState(0);
  
  // Default options
  const defaultOptions = {
    viewportSize: 100,           // Number of bases to show at once
    fontSize: 14,                // Font size for sequence
    colorScheme: "nucleotide",   // Color scheme: nucleotide, codon, conservation
    showLineNumbers: true,       // Show position numbers
    showAnnotations: true,       // Show gene/feature annotations
    allowSelection: true,        // Allow selecting regions
    showComplementary: false,    // Show complementary strand
    lineLength: 50,              // Bases per line
    highlightColor: "#FFEB3B"    // Color for highlighting search matches
  };
  
  // Merge options
  const mergedOptions = { ...defaultOptions, ...options };
  
  // Initialize the viewer
  useEffect(() => {
    if (!sequenceData || !sequenceData.sequence) {
      setError("No sequence data provided");
      setIsLoading(false);
      return;
    }
    
    setIsLoading(true);
    
    try {
      // Process incoming sequence data
      const sequence = sequenceData.sequence.toUpperCase().replace(/\s/g, "");
      
      // Get sequence annotations if available
      if (sequenceData.annotations) {
        setAnnotations(sequenceData.annotations.map(ann => ({
          ...ann,
          start: parseInt(ann.start),
          end: parseInt(ann.end)
        })));
      }
      
      // Initialize with the first viewportSize bases
      updateView(0, Math.min(mergedOptions.viewportSize, sequence.length));
      
      setIsLoading(false);
    } catch (err) {
      console.error("Error initializing sequence viewer:", err);
      setError("Failed to initialize sequence viewer");
      setIsLoading(false);
    }
  }, [sequenceData]);
  
  // Update the sequence view
  const updateView = (start, end) => {
    if (!sequenceData || !sequenceData.sequence) return;
    
    const sequence = sequenceData.sequence.toUpperCase().replace(/\s/g, "");
    
    // Ensure start and end are within bounds
    start = Math.max(0, start);
    end = Math.min(sequence.length, end);
    
    // Update the current view
    setCurrentView({
      start,
      end,
      sequence: sequence.substring(start, end)
    });
    
    // Clear any selection
    setSelectedRange({ start: 0, end: 0 });
  };
  
  // Navigate to next section
  const navigateNext = () => {
    const newStart = currentView.end;
    const newEnd = Math.min(
      newStart + mergedOptions.viewportSize,
      sequenceData.sequence.length
    );
    
    if (newStart < sequenceData.sequence.length) {
      updateView(newStart, newEnd);
    }
  };
  
  // Navigate to previous section
  const navigatePrevious = () => {
    const newEnd = currentView.start;
    const newStart = Math.max(0, newEnd - mergedOptions.viewportSize);
    
    if (newStart >= 0) {
      updateView(newStart, newEnd);
    }
  };
  
  // Navigate to a specific position
  const navigateToPosition = (position) => {
    const pos = parseInt(position);
    if (isNaN(pos)) return;
    
    const start = Math.max(0, pos - Math.floor(mergedOptions.viewportSize / 2));
    const end = Math.min(
      sequenceData.sequence.length,
      start + mergedOptions.viewportSize
    );
    
    updateView(start, end);
  };
  
  // Handle search
  const handleSearch = () => {
    if (!searchTerm || !currentView.sequence) {
      setSearchResults([]);
      return;
    }
    
    const fullSequence = sequenceData.sequence.toUpperCase();
    const term = searchTerm.toUpperCase();
    
    // Find all occurrences
    const results = [];
    let idx = fullSequence.indexOf(term);
    while (idx !== -1) {
      results.push({
        start: idx,
        end: idx + term.length,
        sequence: fullSequence.substring(idx, idx + term.length)
      });
      idx = fullSequence.indexOf(term, idx + 1);
    }
    
    setSearchResults(results);
    
    // Highlight and navigate to the first result if available
    if (results.length > 0) {
      setHighlightIndex(0);
      navigateToPosition(results[0].start);
    }
  };
  
  // Navigate between search results
  const navigateSearchResults = (direction) => {
    if (searchResults.length === 0) return;
    
    let newIndex;
    if (direction === "next") {
      newIndex = (highlightIndex + 1) % searchResults.length;
    } else {
      newIndex = (highlightIndex - 1 + searchResults.length) % searchResults.length;
    }
    
    setHighlightIndex(newIndex);
    navigateToPosition(searchResults[newIndex].start);
  };
  
  // Get complementary sequence
  const getComplementary = (sequence) => {
    return sequence
      .split("")
      .map(base => {
        switch (base) {
          case "A": return "T";
          case "T": return "A";
          case "G": return "C";
          case "C": return "G";
          case "U": return "A";
          default: return base;
        }
      })
      .join("");
  };
  
  // Get nucleotide color
  const getNucleotideColor = (base) => {
    switch (base) {
      case "A": return "#4CAF50"; // Green
      case "T":
      case "U": return "#F44336"; // Red
      case "G": return "#FFC107"; // Amber
      case "C": return "#2196F3"; // Blue
      default: return "#9E9E9E"; // Grey
    }
  };
  
  // Render the sequence with appropriate markup
  const renderSequence = () => {
    if (!currentView.sequence) return null;
    
    const { lineLength } = mergedOptions;
    const lines = [];
    
    // Split the sequence into lines
    for (let i = 0; i < currentView.sequence.length; i += lineLength) {
      const lineStart = currentView.start + i;
      const lineEnd = Math.min(lineStart + lineLength, currentView.start + currentView.sequence.length);
      const lineSequence = currentView.sequence.substring(i, i + lineLength);
      
      // Generate line content with base-by-base styling
      const lineContent = lineSequence.split("").map((base, index) => {
        const pos = lineStart + index;
        const isHighlighted = searchResults.length > 0 && 
          searchResults[highlightIndex].start <= pos && 
          pos < searchResults[highlightIndex].end;
        
        // Determine if this base is annotated
        const baseAnnotations = annotations.filter(
          ann => ann.start <= pos && pos <= ann.end
        );
        
        return (
          <span 
            key={index} 
            style={{ 
              color: mergedOptions.colorScheme === "nucleotide" ? getNucleotideColor(base) : "inherit",
              backgroundColor: isHighlighted ? mergedOptions.highlightColor : 
                baseAnnotations.length > 0 ? baseAnnotations[0].color || "#F5F5F5" : "transparent",
              padding: "0 1px",
              fontFamily: "monospace"
            }}
            title={baseAnnotations.length > 0 ? baseAnnotations[0].name : `Position ${pos + 1}`}
          >
            {base}
          </span>
        );
      });
      
      // Add line numbers if enabled
      const lineNumber = mergedOptions.showLineNumbers ? (
        <span className="line-number">
          {(lineStart + 1).toString().padStart(6, " ")}
        </span>
      ) : null;
      
      lines.push(
        <div key={lineStart} className="sequence-line">
          {lineNumber}
          <span className="sequence-text">{lineContent}</span>
        </div>
      );
      
      // Add complementary strand if enabled
      if (mergedOptions.showComplementary) {
        const compSequence = getComplementary(lineSequence);
        const compContent = compSequence.split("").map((base, index) => (
          <span 
            key={index} 
            style={{ 
              color: mergedOptions.colorScheme === "nucleotide" ? getNucleotideColor(base) : "inherit",
              padding: "0 1px",
              fontFamily: "monospace"
            }}
          >
            {base}
          </span>
        ));
        
        lines.push(
          <div key={`comp-${lineStart}`} className="complementary-line">
            {lineNumber && <span className="line-number"></span>}
            <span className="sequence-text">{compContent}</span>
          </div>
        );
      }
    }
    
    return <div className="sequence-display">{lines}</div>;
  };
  
  // Render annotations as a track above the sequence
  const renderAnnotationTrack = () => {
    if (!mergedOptions.showAnnotations || annotations.length === 0) return null;
    
    // Filter annotations visible in the current view
    const visibleAnnotations = annotations.filter(
      ann => ann.end >= currentView.start && ann.start <= currentView.end
    );
    
    if (visibleAnnotations.length === 0) return null;
    
    return (
      <div className="annotation-track">
        <h4>Annotations</h4>
        <div className="annotation-list">
          {visibleAnnotations.map((ann, index) => (
            <div key={index} className="annotation-item">
              <div 
                className="annotation-color"
                style={{ backgroundColor: ann.color || "#CFD8DC" }}
              ></div>
              <div className="annotation-details">
                <div className="annotation-name">{ann.name}</div>
                <div className="annotation-position">
                  {ann.start + 1}-{ann.end + 1}
                </div>
                {ann.type && (
                  <div className="annotation-type">{ann.type}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };
  
  // Get basic sequence stats
  const getSequenceStats = () => {
    if (!sequenceData || !sequenceData.sequence) return null;
    
    const sequence = sequenceData.sequence.toUpperCase();
    
    // Count bases
    const baseCounts = {
      A: 0, T: 0, G: 0, C: 0, U: 0, N: 0, Other: 0
    };
    
    for (const base of sequence) {
      if (base in baseCounts) {
        baseCounts[base]++;
      } else {
        baseCounts.Other++;
      }
    }
    
    // Calculate GC content
    const gcContent = ((baseCounts.G + baseCounts.C) / sequence.length) * 100;
    
    return (
      <div className="sequence-stats">
        <h4>Sequence Statistics</h4>
        <div className="stats-grid">
          <div className="stat-item">
            <div className="stat-label">Length</div>
            <div className="stat-value">{sequence.length} bp</div>
          </div>
          <div className="stat-item">
            <div className="stat-label">GC Content</div>
            <div className="stat-value">{gcContent.toFixed(1)}%</div>
          </div>
          <div className="stat-item">
            <div className="stat-label">Current Region</div>
            <div className="stat-value">
              {currentView.start + 1}-{currentView.end} of {sequence.length}
            </div>
          </div>
        </div>
      </div>
    );
  };
  
  return (
    <div className="sequence-viewer-container" ref={containerRef}>
      {isLoading ? (
        <div className="sequence-loading">
          <div className="loading-spinner"></div>
          <span>Loading sequence data...</span>
        </div>
      ) : error ? (
        <div className="sequence-error">
          <span>{error}</span>
        </div>
      ) : (
        <>
          <div className="sequence-toolbar">
            <div className="navigation-controls">
              <button 
                onClick={navigatePrevious}
                disabled={currentView.start === 0}
                className="sequence-nav-btn"
              >
                ← Previous
              </button>
              
              <div className="position-input">
                <label>Go to position:</label>
                <input 
                  type="number" 
                  min="1" 
                  max={sequenceData?.sequence?.length || 1}
                  onChange={(e) => navigateToPosition(parseInt(e.target.value) - 1)}
                  className="position-field"
                />
              </div>
              
              <button 
                onClick={navigateNext}
                disabled={currentView.end >= (sequenceData?.sequence?.length || 0)}
                className="sequence-nav-btn"
              >
                Next →
              </button>
            </div>
            
            <div className="search-controls">
              <input 
                type="text"
                placeholder="Search sequence..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="search-field"
              />
              <button 
                onClick={handleSearch}
                className="search-btn"
              >
                Search
              </button>
              
              {searchResults.length > 0 && (
                <div className="search-results-nav">
                  <button 
                    onClick={() => navigateSearchResults("previous")}
                    className="search-nav-btn"
                  >
                    ←
                  </button>
                  <span>
                    {highlightIndex + 1} of {searchResults.length}
                  </span>
                  <button 
                    onClick={() => navigateSearchResults("next")}
                    className="search-nav-btn"
                  >
                    →
                  </button>
                </div>
              )}
            </div>
            
            <div className="view-controls">
              <div className="view-control">
                <input 
                  type="checkbox"
                  id="show-annotations"
                  checked={mergedOptions.showAnnotations}
                  onChange={(e) => {
                    mergedOptions.showAnnotations = e.target.checked;
                    // Force re-render
                    setCurrentView({...currentView});
                  }}
                />
                <label htmlFor="show-annotations">Annotations</label>
              </div>
              
              <div className="view-control">
                <input 
                  type="checkbox"
                  id="show-complementary"
                  checked={mergedOptions.showComplementary}
                  onChange={(e) => {
                    mergedOptions.showComplementary = e.target.checked;
                    // Force re-render
                    setCurrentView({...currentView});
                  }}
                />
                <label htmlFor="show-complementary">Complementary</label>
              </div>
            </div>
          </div>
          
          <div className="sequence-content">
            {getSequenceStats()}
            {renderAnnotationTrack()}
            <div className="sequence-viewer">
              {renderSequence()}
            </div>
          </div>
          
          <div className="sequence-footer">
            <div className="position-indicator">
              Viewing {currentView.start + 1} to {currentView.end} of {sequenceData?.sequence?.length || 0} bp
            </div>
            
            {sequenceData?.metadata && (
              <div className="sequence-metadata">
                {sequenceData.metadata.name && (
                  <span className="metadata-item">
                    <strong>Name:</strong> {sequenceData.metadata.name}
                  </span>
                )}
                {sequenceData.metadata.source && (
                  <span className="metadata-item">
                    <strong>Source:</strong> {sequenceData.metadata.source}
                  </span>
                )}
                {sequenceData.metadata.type && (
                  <span className="metadata-item">
                    <strong>Type:</strong> {sequenceData.metadata.type}
                  </span>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
} 