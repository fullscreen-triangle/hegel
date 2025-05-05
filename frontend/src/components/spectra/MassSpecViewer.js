import React, { useState, useEffect, useRef } from 'react';
import * as d3 from 'd3';
import axios from 'axios';

const MassSpecViewer = ({ moleculeId, width = 800, height = 400 }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const svgRef = useRef(null);

  // Fetch mass spec data for the molecule
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Replace with your actual API endpoint
        const response = await axios.get(`/api/molecule/${moleculeId}/mass-spec`);
        setData(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching mass spec data:', err);
        setError('Failed to load mass spectrometry data');
      } finally {
        setLoading(false);
      }
    };

    if (moleculeId) {
      fetchData();
    }
  }, [moleculeId]);

  // Render the spectrum visualization
  useEffect(() => {
    if (!data || !svgRef.current) return;

    // Parse the data for visualization
    const spectrumData = processDataForVisualization(data);
    renderSpectrum(spectrumData, svgRef.current, width, height);
  }, [data, width, height]);

  // Process the data into a format suitable for D3 visualization
  const processDataForVisualization = (rawData) => {
    // This will depend on your data format
    // For a typical mass spec, we'd have m/z values and intensities
    if (rawData.format === 'peaks') {
      return rawData.content.mz_values.map((mz, index) => ({
        mz,
        intensity: rawData.content.intensities[index] || 0,
      }));
    } else if (rawData.format === 'msms') {
      return rawData.content.fragment_mz.map((mz, index) => ({
        mz,
        intensity: rawData.content.fragment_intensities[index] || 0,
      }));
    }
    
    // Fallback for unknown formats
    return [];
  };

  // Render the spectrum using D3
  const renderSpectrum = (spectrumData, svgElement, width, height) => {
    // Clear any existing visualization
    d3.select(svgElement).selectAll('*').remove();

    // Set up the SVG and margins
    const margin = { top: 20, right: 30, bottom: 40, left: 50 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create the SVG group with margins
    const svg = d3
      .select(svgElement)
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Create scales
    const xScale = d3
      .scaleLinear()
      .domain([
        d3.min(spectrumData, d => d.mz) * 0.95,
        d3.max(spectrumData, d => d.mz) * 1.05
      ])
      .range([0, innerWidth]);

    const yScale = d3
      .scaleLinear()
      .domain([0, d3.max(spectrumData, d => d.intensity) * 1.1])
      .range([innerHeight, 0]);

    // Create axes
    const xAxis = d3.axisBottom(xScale);
    const yAxis = d3.axisLeft(yScale);

    // Add the X axis
    svg
      .append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(xAxis);

    // Add the Y axis
    svg.append('g').attr('class', 'y-axis').call(yAxis);

    // Add X axis label
    svg
      .append('text')
      .attr('class', 'x-axis-label')
      .attr('x', innerWidth / 2)
      .attr('y', innerHeight + margin.bottom - 5)
      .style('text-anchor', 'middle')
      .text('m/z');

    // Add Y axis label
    svg
      .append('text')
      .attr('class', 'y-axis-label')
      .attr('transform', 'rotate(-90)')
      .attr('x', -innerHeight / 2)
      .attr('y', -margin.left + 15)
      .style('text-anchor', 'middle')
      .text('Intensity');

    // Draw the spectrum lines
    svg
      .selectAll('.peak-line')
      .data(spectrumData)
      .enter()
      .append('line')
      .attr('class', 'peak-line')
      .attr('x1', d => xScale(d.mz))
      .attr('x2', d => xScale(d.mz))
      .attr('y1', d => yScale(0))
      .attr('y2', d => yScale(d.intensity))
      .attr('stroke', 'steelblue')
      .attr('stroke-width', 1.5);
  };

  // Show loading state
  if (loading) {
    return <div>Loading mass spectrometry data...</div>;
  }

  // Show error state
  if (error) {
    return <div className="error-message">{error}</div>;
  }

  // Show empty state
  if (!data) {
    return <div>No mass spectrometry data available for this molecule.</div>;
  }

  return (
    <div className="mass-spec-viewer">
      <h3>Mass Spectrometry Data</h3>
      <div className="spectrum-container">
        <svg ref={svgRef} />
      </div>
      <div className="metadata">
        {data.metadata && (
          <>
            <h4>Metadata</h4>
            <ul>
              {Object.entries(data.metadata).map(([key, value]) => (
                <li key={key}>
                  <strong>{key}:</strong> {JSON.stringify(value)}
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  );
};

export default MassSpecViewer; 