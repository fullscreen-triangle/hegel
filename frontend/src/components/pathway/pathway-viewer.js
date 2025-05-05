import React, { useRef, useEffect, useState } from "react";
import * as d3 from "d3";

/**
 * PathwayViewer component for visualizing biochemical pathways and reactomes
 */
export default function PathwayViewer({ pathwayData, options }) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [zoomState, setZoomState] = useState({ scale: 1, x: 0, y: 0 });
  
  // Default options
  const defaultOptions = {
    width: 800,
    height: 600,
    backgroundColor: "#ffffff",
    nodeRadius: 15,
    linkDistance: 100,
    chargeStrength: -200,
    showLabels: true,
    colorScheme: {
      metabolite: "#4CAF50",  // Green
      protein: "#2196F3",     // Blue
      gene: "#FF9800",        // Orange
      reaction: "#9C27B0",    // Purple
      pathway: "#F44336",     // Red
      default: "#757575"      // Grey
    },
    highlightColor: "#FFC107", // Amber
    zoomable: true
  };
  
  // Merge options
  const mergedOptions = { ...defaultOptions, ...options };
  
  // Initialize dimensions on mount and resize
  useEffect(() => {
    if (containerRef.current) {
      const resizeObserver = new ResizeObserver(entries => {
        const { width } = entries[0].contentRect;
        setDimensions({
          width: width,
          height: mergedOptions.height
        });
      });
      
      resizeObserver.observe(containerRef.current);
      
      return () => {
        resizeObserver.disconnect();
      };
    }
  }, [mergedOptions.height]);
  
  // Initialize and render the pathway visualization
  useEffect(() => {
    if (!svgRef.current || !dimensions.width || !pathwayData) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      createVisualization();
      setIsLoading(false);
    } catch (err) {
      console.error("Failed to render pathway:", err);
      setError("Error rendering pathway visualization");
      setIsLoading(false);
    }
  }, [pathwayData, dimensions, selectedNode]);
  
  // Create the pathway visualization
  const createVisualization = () => {
    // Clear previous content
    d3.select(svgRef.current).selectAll("*").remove();
    
    if (!pathwayData || !pathwayData.nodes || !pathwayData.links) {
      d3.select(svgRef.current)
        .append("text")
        .attr("x", dimensions.width / 2)
        .attr("y", dimensions.height / 2)
        .attr("text-anchor", "middle")
        .text("No pathway data available");
      return;
    }
    
    // Create the SVG canvas
    const svg = d3.select(svgRef.current)
      .attr("width", dimensions.width)
      .attr("height", dimensions.height)
      .style("background-color", mergedOptions.backgroundColor);
    
    // Create a group for the graph elements
    const g = svg.append("g");
    
    // Define arrowhead marker for directed edges
    svg.append("defs").append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", mergedOptions.nodeRadius + 10)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "#999");
    
    // Create the force simulation
    const simulation = d3.forceSimulation(pathwayData.nodes)
      .force("link", d3.forceLink(pathwayData.links)
        .id(d => d.id)
        .distance(mergedOptions.linkDistance))
      .force("charge", d3.forceManyBody().strength(mergedOptions.chargeStrength))
      .force("center", d3.forceCenter(dimensions.width / 2, dimensions.height / 2));
    
    // Create the links
    const links = g.append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(pathwayData.links)
      .enter().append("line")
      .attr("stroke", d => d.color || "#999")
      .attr("stroke-width", d => d.value || 1)
      .attr("stroke-dasharray", d => d.type === "indirect" ? "5,5" : null)
      .attr("marker-end", d => d.directed ? "url(#arrowhead)" : null);
    
    // Create the link labels if available
    if (mergedOptions.showLabels) {
      const linkLabels = g.append("g")
        .attr("class", "link-labels")
        .selectAll("text")
        .data(pathwayData.links.filter(link => link.label))
        .enter().append("text")
        .attr("font-size", 10)
        .attr("text-anchor", "middle")
        .attr("fill", "#666")
        .text(d => d.label);
    }
    
    // Create the nodes
    const nodes = g.append("g")
      .attr("class", "nodes")
      .selectAll("g")
      .data(pathwayData.nodes)
      .enter().append("g")
      .attr("class", "node")
      .call(d3.drag()
        .on("start", dragStarted)
        .on("drag", dragged)
        .on("end", dragEnded));
    
    // Add node circles
    nodes.append("circle")
      .attr("r", d => d.radius || mergedOptions.nodeRadius)
      .attr("fill", d => {
        if (selectedNode && selectedNode.id === d.id) {
          return mergedOptions.highlightColor;
        }
        return d.color || mergedOptions.colorScheme[d.type] || mergedOptions.colorScheme.default;
      })
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5);
    
    // Add node labels
    if (mergedOptions.showLabels) {
      nodes.append("text")
        .attr("dy", d => (d.radius || mergedOptions.nodeRadius) + 14)
        .attr("text-anchor", "middle")
        .attr("font-size", 12)
        .text(d => d.label || d.id);
    }
    
    // Add tooltips and click interactions
    nodes.append("title")
      .text(d => {
        let tooltip = d.label || d.id;
        if (d.type) tooltip += `\nType: ${d.type}`;
        if (d.description) tooltip += `\n${d.description}`;
        return tooltip;
      });
    
    nodes.on("click", (event, d) => {
      setSelectedNode(d);
      event.stopPropagation();
    });
    
    // Add background click handler to deselect
    svg.on("click", () => {
      setSelectedNode(null);
    });
    
    // Add zoom capability if enabled
    if (mergedOptions.zoomable) {
      const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on("zoom", (event) => {
          g.attr("transform", event.transform);
          setZoomState({
            scale: event.transform.k,
            x: event.transform.x,
            y: event.transform.y
          });
        });
      
      svg.call(zoom);
    }
    
    // Add legend for node types
    const uniqueTypes = [...new Set(pathwayData.nodes.map(n => n.type))];
    
    if (uniqueTypes.length > 0) {
      const legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(20, 20)`);
      
      legend.append("rect")
        .attr("width", 120)
        .attr("height", uniqueTypes.length * 25 + 10)
        .attr("rx", 5)
        .attr("ry", 5)
        .attr("fill", "#f5f5f5")
        .attr("opacity", 0.9);
      
      uniqueTypes.forEach((type, i) => {
        const legendItem = legend.append("g")
          .attr("transform", `translate(10, ${i * 25 + 20})`);
        
        legendItem.append("circle")
          .attr("r", 6)
          .attr("fill", mergedOptions.colorScheme[type] || mergedOptions.colorScheme.default);
        
        legendItem.append("text")
          .attr("x", 15)
          .attr("y", 4)
          .attr("font-size", 12)
          .text(capitalizeFirstLetter(type));
      });
    }
    
    // Function to update positions during simulation
    simulation.on("tick", () => {
      links
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);
      
      if (mergedOptions.showLabels) {
        g.selectAll(".link-labels text")
          .attr("x", d => (d.source.x + d.target.x) / 2)
          .attr("y", d => (d.source.y + d.target.y) / 2);
      }
      
      nodes.attr("transform", d => `translate(${d.x}, ${d.y})`);
    });
    
    // Drag functions
    function dragStarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }
    
    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }
    
    function dragEnded(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
  };
  
  // Helper to capitalize first letter
  const capitalizeFirstLetter = (string) => {
    return string.charAt(0).toUpperCase() + string.slice(1);
  };
  
  // Reset zoom and center the view
  const resetZoom = () => {
    const svg = d3.select(svgRef.current);
    const g = svg.select("g");
    
    svg.transition().duration(750).call(
      d3.zoom().transform,
      d3.zoomIdentity
    );
    
    setZoomState({ scale: 1, x: 0, y: 0 });
  };
  
  // Render pathway information panel
  const renderPathwayInfo = () => {
    if (!pathwayData || !pathwayData.metadata) return null;
    
    const { metadata } = pathwayData;
    
    return (
      <div className="pathway-info">
        <h3>{metadata.name || "Pathway"}</h3>
        {metadata.description && (
          <p className="pathway-description">{metadata.description}</p>
        )}
        <div className="pathway-metadata">
          {metadata.id && (
            <div className="metadata-item">
              <span className="metadata-label">ID:</span>
              <span className="metadata-value">{metadata.id}</span>
            </div>
          )}
          {metadata.organism && (
            <div className="metadata-item">
              <span className="metadata-label">Organism:</span>
              <span className="metadata-value">{metadata.organism}</span>
            </div>
          )}
          {metadata.source && (
            <div className="metadata-item">
              <span className="metadata-label">Source:</span>
              <span className="metadata-value">{metadata.source}</span>
            </div>
          )}
        </div>
      </div>
    );
  };
  
  // Render node details panel
  const renderNodeDetails = () => {
    if (!selectedNode) return null;
    
    return (
      <div className="node-details">
        <h4>
          {selectedNode.label || selectedNode.id}
          {selectedNode.type && (
            <span className="node-type" style={{
              backgroundColor: mergedOptions.colorScheme[selectedNode.type] || mergedOptions.colorScheme.default
            }}>
              {capitalizeFirstLetter(selectedNode.type)}
            </span>
          )}
        </h4>
        
        {selectedNode.description && (
          <p className="node-description">{selectedNode.description}</p>
        )}
        
        {selectedNode.attributes && Object.keys(selectedNode.attributes).length > 0 && (
          <div className="node-attributes">
            <h5>Properties</h5>
            <table className="attributes-table">
              <tbody>
                {Object.entries(selectedNode.attributes).map(([key, value]) => (
                  <tr key={key}>
                    <td>{capitalizeFirstLetter(key)}</td>
                    <td>{value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {/* Show connected nodes */}
        {pathwayData && pathwayData.links && (
          <div className="connected-nodes">
            <h5>Connected Entities</h5>
            <ul className="connections-list">
              {pathwayData.links
                .filter(link => link.source.id === selectedNode.id || link.target.id === selectedNode.id)
                .map((link, index) => {
                  const isSource = link.source.id === selectedNode.id;
                  const connectedNode = isSource ? link.target : link.source;
                  const direction = isSource ? "→" : "←";
                  
                  return (
                    <li key={index} className="connection-item">
                      <span className="connection-direction">{direction}</span>
                      <span className="connection-node">
                        {connectedNode.label || connectedNode.id}
                      </span>
                      {link.label && (
                        <span className="connection-label">({link.label})</span>
                      )}
                    </li>
                  );
                })}
            </ul>
          </div>
        )}
      </div>
    );
  };
  
  // Main render function
  return (
    <div className="pathway-viewer-container" ref={containerRef}>
      {renderPathwayInfo()}
      
      <div className="pathway-visualization">
        {isLoading && (
          <div className="pathway-loading">
            <div className="loading-spinner"></div>
            <span>Loading pathway data...</span>
          </div>
        )}
        
        {error && (
          <div className="pathway-error">
            <span>{error}</span>
          </div>
        )}
        
        <div className="pathway-controls">
          <button 
            onClick={resetZoom}
            className="pathway-control-btn"
          >
            Reset View
          </button>
          
          <div className="zoom-indicator">
            Zoom: {Math.round(zoomState.scale * 100)}%
          </div>
        </div>
        
        <svg 
          ref={svgRef} 
          className="pathway-svg"
          style={{ 
            width: "100%", 
            height: dimensions.height,
            maxWidth: "100%"
          }}
        ></svg>
      </div>
      
      {selectedNode && (
        <div className="details-panel">
          {renderNodeDetails()}
        </div>
      )}
    </div>
  );
} 