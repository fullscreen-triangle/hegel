import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const NetworkGraph = ({ 
  moleculeId,
  pathwayId,
  similarityThreshold = 0.6,
  maxNodes = 50,
  width = '100%',
  height = '600px',
  onNodeClick
}) => {
  const containerRef = useRef(null);
  const svgRef = useRef(null);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [networkData, setNetworkData] = useState(null);
  
  // Fetch network data
  useEffect(() => {
    if (!moleculeId && !pathwayId) return;
    
    const fetchNetworkData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch visualization data from API
        const response = await axios.post(`${API_URL}/visualization/network`, {
          central_molecule_id: moleculeId,
          pathway_id: pathwayId,
          similarity_threshold: similarityThreshold,
          max_nodes: maxNodes
        });
        
        setNetworkData(response.data.data);
      } catch (err) {
        console.error('Error fetching network data:', err);
        setError('Failed to load network visualization');
      } finally {
        setLoading(false);
      }
    };
    
    fetchNetworkData();
  }, [moleculeId, pathwayId, similarityThreshold, maxNodes]);
  
  // Render network graph
  useEffect(() => {
    if (!networkData || !containerRef.current) return;
    
    // Clear any existing SVG
    d3.select(containerRef.current).select('svg').remove();
    
    // Get container dimensions
    const containerWidth = containerRef.current.clientWidth;
    const containerHeight = containerRef.current.clientHeight;
    
    // Create SVG container
    const svg = d3.select(containerRef.current)
      .append('svg')
      .attr('width', containerWidth)
      .attr('height', containerHeight)
      .attr('viewBox', [0, 0, containerWidth, containerHeight])
      .call(d3.zoom().on('zoom', (event) => {
        g.attr('transform', event.transform);
      }));
    
    svgRef.current = svg;
    
    // Add a group for the graph
    const g = svg.append('g');
    
    // Add a marker for arrows
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 15)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#999');
    
    // Create a simulation for the graph
    const simulation = d3.forceSimulation(networkData.nodes)
      .force('link', d3.forceLink(networkData.links).id(d => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(containerWidth / 2, containerHeight / 2))
      .force('collision', d3.forceCollide().radius(d => (d.radius || 20) + 10));
    
    // Create links
    const link = g.selectAll('.link')
      .data(networkData.links)
      .enter().append('line')
      .attr('class', 'link')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', d => Math.sqrt(d.value || 1) * 2)
      .attr('marker-end', d => d.direction === 'forward' ? 'url(#arrowhead)' : null);
    
    // Create link labels
    const linkLabel = g.selectAll('.link-label')
      .data(networkData.links)
      .enter().append('text')
      .attr('class', 'link-label')
      .attr('dy', -5)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .text(d => d.label || '');
    
    // Create node groups
    const node = g.selectAll('.node')
      .data(networkData.nodes)
      .enter().append('g')
      .attr('class', 'node')
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended))
      .on('click', (event, d) => {
        if (onNodeClick) onNodeClick(d);
      });
    
    // Add circles for nodes
    node.append('circle')
      .attr('r', d => d.radius || 20)
      .attr('fill', d => getNodeColor(d))
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5);
    
    // Add labels to nodes
    node.append('text')
      .attr('dy', 5)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .text(d => d.label);
    
    // Add tooltips
    node.append('title')
      .text(d => {
        const parts = [];
        if (d.name) parts.push(`Name: ${d.name}`);
        if (d.formula) parts.push(`Formula: ${d.formula}`);
        if (d.confidence) parts.push(`Confidence: ${(d.confidence * 100).toFixed(1)}%`);
        return parts.join('\n');
      });
    
    // Update function for simulation
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      
      linkLabel
        .attr('x', d => (d.source.x + d.target.x) / 2)
        .attr('y', d => (d.source.y + d.target.y) / 2);
      
      node
        .attr('transform', d => `translate(${d.x},${d.y})`);
    });
    
    // Drag functions
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }
    
    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }
    
    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
    
    // Handle window resize
    const handleResize = () => {
      if (!containerRef.current || !svgRef.current) return;
      
      const newWidth = containerRef.current.clientWidth;
      const newHeight = containerRef.current.clientHeight;
      
      svgRef.current
        .attr('width', newWidth)
        .attr('height', newHeight)
        .attr('viewBox', [0, 0, newWidth, newHeight]);
      
      simulation.force('center', d3.forceCenter(newWidth / 2, newHeight / 2));
      simulation.alpha(0.3).restart();
    };
    
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      simulation.stop();
    };
  }, [networkData, onNodeClick]);
  
  // Get node color based on type and confidence
  const getNodeColor = (node) => {
    // Define color scale for confidence
    const confidenceScale = d3.scaleLinear()
      .domain([0, 0.5, 1])
      .range(['#ff4d4d', '#ffcc00', '#4CAF50'])
      .clamp(true);
    
    // If node is central, use a different color
    if (node.isCentral) {
      return '#6200ea'; // Purple for central node
    }
    
    // If node has confidence, use the confidence scale
    if (node.confidence !== undefined) {
      return confidenceScale(node.confidence);
    }
    
    // Default colors based on node type
    switch(node.type) {
      case 'molecule':
        return '#4285F4'; // Blue
      case 'reaction':
        return '#EA4335'; // Red
      case 'pathway':
        return '#34A853'; // Green
      default:
        return '#FBBC05'; // Yellow
    }
  };
  
  return (
    <div ref={containerRef} style={{ width, height, position: 'relative' }}>
      {loading && (
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}>
          Loading network graph...
        </div>
      )}
      
      {error && (
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', color: 'red' }}>
          {error}
        </div>
      )}
      
      {!loading && !error && (!networkData || networkData.nodes.length === 0) && (
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}>
          No network data available.
        </div>
      )}
    </div>
  );
};

export default NetworkGraph; 