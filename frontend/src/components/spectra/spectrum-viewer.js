import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";

/**
 * SpectrumViewer component for visualizing LC-MS/MS spectra
 */
export default function SpectrumViewer({ spectrumData, options }) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [zoomState, setZoomState] = useState({ k: 1, x: 0, y: 0 });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [highlightedPeaks, setHighlightedPeaks] = useState([]);
  const [annotationVisibility, setAnnotationVisibility] = useState(true);
  
  // Default options
  const defaultOptions = {
    width: 700,
    height: 400,
    margin: { top: 20, right: 30, bottom: 50, left: 60 },
    backgroundColor: "#ffffff",
    peakColor: "#4a90e2",
    highlightColor: "#ff7043",
    axisColor: "#333333",
    annotationColor: "#28a745",
    zoomable: true,
    showGrid: true,
    showAnnotations: true,
    minIntensityThreshold: 0.01, // Show peaks above 1% of max intensity
  };
  
  // Merge options
  const mergedOptions = { ...defaultOptions, ...options };
  
  // Update dimensions when container size changes
  useEffect(() => {
    if (containerRef.current) {
      const { width } = containerRef.current.getBoundingClientRect();
      setDimensions({ 
        width: width || mergedOptions.width, 
        height: mergedOptions.height 
      });
    }
  }, [mergedOptions.width, mergedOptions.height]);
  
  // Render spectrum when data or dimensions change
  useEffect(() => {
    if (!svgRef.current || !dimensions.width || !spectrumData) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      renderSpectrum();
      setIsLoading(false);
    } catch (err) {
      console.error("Failed to render spectrum:", err);
      setError("Error rendering spectrum visualization");
      setIsLoading(false);
    }
  }, [spectrumData, dimensions, zoomState, highlightedPeaks, annotationVisibility]);
  
  // Render the spectrum visualization
  const renderSpectrum = () => {
    // Clear previous content
    d3.select(svgRef.current).selectAll("*").remove();
    
    if (!spectrumData || !spectrumData.peaks || spectrumData.peaks.length === 0) {
      d3.select(svgRef.current)
        .append("text")
        .attr("x", dimensions.width / 2)
        .attr("y", dimensions.height / 2)
        .attr("text-anchor", "middle")
        .text("No spectrum data available");
      return;
    }
    
    const { margin } = mergedOptions;
    const width = dimensions.width - margin.left - margin.right;
    const height = dimensions.height - margin.top - margin.bottom;
    
    // Create the SVG canvas
    const svg = d3.select(svgRef.current)
      .attr("width", dimensions.width)
      .attr("height", dimensions.height)
      .style("background-color", mergedOptions.backgroundColor);
    
    // Create the chart area group
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // Extract peaks data
    const peaks = spectrumData.peaks.map(peak => ({
      mz: peak.mz || peak.mass_to_charge,
      intensity: peak.intensity,
      annotation: peak.annotation || "",
      highlighted: highlightedPeaks.includes(peak.mz || peak.mass_to_charge)
    }));
    
    // Find max intensity and normalize
    const maxIntensity = d3.max(peaks, d => d.intensity);
    const normalizedPeaks = peaks.map(peak => ({
      ...peak,
      normalizedIntensity: peak.intensity / maxIntensity
    }));
    
    // Filter peaks below threshold
    const filteredPeaks = normalizedPeaks.filter(
      peak => peak.normalizedIntensity >= mergedOptions.minIntensityThreshold
    );
    
    // Create scales
    const x = d3.scaleLinear()
      .domain([
        d3.min(filteredPeaks, d => d.mz) * 0.95,
        d3.max(filteredPeaks, d => d.mz) * 1.05
      ])
      .range([0, width]);
    
    const y = d3.scaleLinear()
      .domain([0, 1.05]) // Normalized intensity + 5% margin
      .range([height, 0]);
    
    // Apply zoom transform
    x.domain(x.domain().map(d => (d - zoomState.x) / zoomState.k));
    y.domain(y.domain().map(d => (d - zoomState.y) / zoomState.k));
    
    // Create axes
    const xAxis = g.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(x))
      .attr("color", mergedOptions.axisColor);
    
    const yAxis = g.append("g")
      .call(d3.axisLeft(y).ticks(5).tickFormat(d => `${Math.round(d * 100)}%`))
      .attr("color", mergedOptions.axisColor);
    
    // Add grid if enabled
    if (mergedOptions.showGrid) {
      g.append("g")
        .attr("class", "grid")
        .attr("transform", `translate(0,${height})`)
        .call(
          d3.axisBottom(x)
            .ticks(10)
            .tickSize(-height)
            .tickFormat("")
        )
        .attr("color", "#e0e0e0")
        .selectAll("line")
        .style("stroke-dasharray", "3,3");
      
      g.append("g")
        .attr("class", "grid")
        .call(
          d3.axisLeft(y)
            .ticks(5)
            .tickSize(-width)
            .tickFormat("")
        )
        .attr("color", "#e0e0e0")
        .selectAll("line")
        .style("stroke-dasharray", "3,3");
    }
    
    // Add axis labels
    g.append("text")
      .attr("transform", `translate(${width/2}, ${height + 40})`)
      .style("text-anchor", "middle")
      .style("fill", mergedOptions.axisColor)
      .text("m/z");
    
    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -40)
      .attr("x", -height / 2)
      .style("text-anchor", "middle")
      .style("fill", mergedOptions.axisColor)
      .text("Relative Intensity");
    
    // Draw peaks
    filteredPeaks.forEach(peak => {
      const peakX = x(peak.mz);
      const peakY = y(peak.normalizedIntensity);
      
      // Draw peak line
      g.append("line")
        .attr("x1", peakX)
        .attr("y1", height)
        .attr("x2", peakX)
        .attr("y2", peakY)
        .attr("stroke", peak.highlighted ? mergedOptions.highlightColor : mergedOptions.peakColor)
        .attr("stroke-width", peak.highlighted ? 2 : 1);
      
      // Add peak annotation if available and enabled
      if (peak.annotation && mergedOptions.showAnnotations && annotationVisibility) {
        g.append("text")
          .attr("x", peakX)
          .attr("y", peakY - 10)
          .attr("text-anchor", "middle")
          .attr("font-size", "10px")
          .style("fill", mergedOptions.annotationColor)
          .text(peak.annotation);
      }
      
      // Add interactive tooltip for peaks
      g.append("rect")
        .attr("x", peakX - 3)
        .attr("y", peakY)
        .attr("width", 6)
        .attr("height", height - peakY)
        .attr("fill", "transparent")
        .attr("data-mz", peak.mz)
        .attr("data-intensity", peak.intensity)
        .attr("class", "peak-hitbox")
        .on("mouseover", (event) => {
          const target = event.currentTarget;
          const mz = target.getAttribute("data-mz");
          const intensity = target.getAttribute("data-intensity");
          
          // Show tooltip
          const tooltip = svg.append("g")
            .attr("class", "tooltip")
            .attr("transform", `translate(${event.pageX - svgRef.current.getBoundingClientRect().left}, ${event.pageY - svgRef.current.getBoundingClientRect().top - 40})`);
          
          tooltip.append("rect")
            .attr("width", 120)
            .attr("height", 45)
            .attr("fill", "white")
            .attr("stroke", "#ccc")
            .attr("rx", 4);
          
          tooltip.append("text")
            .attr("x", 10)
            .attr("y", 15)
            .attr("fill", "#333")
            .text(`m/z: ${parseFloat(mz).toFixed(4)}`);
          
          tooltip.append("text")
            .attr("x", 10)
            .attr("y", 35)
            .attr("fill", "#333")
            .text(`Intensity: ${parseFloat(intensity).toFixed(2)}`);
        })
        .on("mouseout", () => {
          svg.select(".tooltip").remove();
        })
        .on("click", (event) => {
          const mz = parseFloat(event.currentTarget.getAttribute("data-mz"));
          togglePeakHighlight(mz);
        });
    });
    
    // Add spectrum metadata if available
    if (spectrumData.metadata) {
      const metadata = spectrumData.metadata;
      const metadataPanel = svg.append("g")
        .attr("transform", `translate(${margin.left + 10}, ${margin.top + 10})`);
      
      let yOffset = 0;
      
      if (metadata.precursorMz) {
        metadataPanel.append("text")
          .attr("y", yOffset)
          .attr("fill", "#333")
          .text(`Precursor m/z: ${metadata.precursorMz.toFixed(4)}`);
        yOffset += 15;
      }
      
      if (metadata.retentionTime) {
        metadataPanel.append("text")
          .attr("y", yOffset)
          .attr("fill", "#333")
          .text(`RT: ${metadata.retentionTime.toFixed(2)} min`);
        yOffset += 15;
      }
      
      if (metadata.scanNumber) {
        metadataPanel.append("text")
          .attr("y", yOffset)
          .attr("fill", "#333")
          .text(`Scan: ${metadata.scanNumber}`);
      }
    }
    
    // Add zoom behavior if enabled
    if (mergedOptions.zoomable) {
      const zoom = d3.zoom()
        .scaleExtent([1, 20])
        .on("zoom", (event) => {
          setZoomState({
            k: event.transform.k,
            x: event.transform.x,
            y: event.transform.y
          });
        });
      
      svg.call(zoom);
    }
  };
  
  // Toggle peak highlight
  const togglePeakHighlight = (mz) => {
    setHighlightedPeaks(prev => {
      if (prev.includes(mz)) {
        return prev.filter(m => m !== mz);
      } else {
        return [...prev, mz];
      }
    });
  };
  
  // Toggle annotation visibility
  const toggleAnnotations = () => {
    setAnnotationVisibility(prev => !prev);
  };
  
  // Reset zoom
  const resetZoom = () => {
    setZoomState({ k: 1, x: 0, y: 0 });
  };
  
  return (
    <div className="spectrum_viewer_container" ref={containerRef}>
      {isLoading && (
        <div className="spectrum_loading">
          <div className="loading_spinner"></div>
          <span>Loading spectrum data...</span>
        </div>
      )}
      
      {error && (
        <div className="spectrum_error">
          <span>{error}</span>
        </div>
      )}
      
      <svg 
        ref={svgRef} 
        className="spectrum_svg"
        style={{ 
          width: "100%", 
          height: mergedOptions.height,
          maxWidth: "100%"
        }}
      ></svg>
      
      <div className="spectrum_controls">
        <button onClick={resetZoom} className="spectrum_control_btn">
          Reset Zoom
        </button>
        <button 
          onClick={toggleAnnotations} 
          className={`spectrum_control_btn ${annotationVisibility ? 'active' : ''}`}
        >
          {annotationVisibility ? 'Hide' : 'Show'} Annotations
        </button>
        {spectrumData && spectrumData.metadata && (
          <div className="spectrum_metadata">
            {spectrumData.metadata.moleculeName && (
              <span className="metadata_item">
                <strong>Molecule:</strong> {spectrumData.metadata.moleculeName}
              </span>
            )}
            {spectrumData.metadata.msLevel && (
              <span className="metadata_item">
                <strong>MS Level:</strong> {spectrumData.metadata.msLevel}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
} 