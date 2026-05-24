import React, { useRef, useEffect } from 'react';
import * as d3 from 'd3';
import { useSBS } from './SBSContext';

export default function CircuitGraph() {
  const { circuit } = useSBS();
  const svgRef = useRef();
  const containerRef = useRef();

  useEffect(() => {
    if (!circuit || !svgRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth || 500;
    const height = 400;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();
    svg.attr('width', width).attr('height', height);

    const defs = svg.append('defs');
    defs.append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 20)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', 'currentColor')
      .attr('class', 'text-dark/40 dark:text-light/40');

    const simNodes = circuit.nodes.map(n => ({
      ...n,
      x: width / 2 + (Math.random() - 0.5) * 100,
      y: height / 2 + (Math.random() - 0.5) * 100,
    }));

    const simLinks = circuit.edges.map(e => ({
      ...e,
      source: e.src,
      target: e.dst,
    }));

    const simulation = d3.forceSimulation(simNodes)
      .force('link', d3.forceLink(simLinks).id((d, i) => i).distance(60))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(25));

    const g = svg.append('g');

    const zoom = d3.zoom()
      .scaleExtent([0.3, 3])
      .on('zoom', (event) => g.attr('transform', event.transform));
    svg.call(zoom);

    const link = g.append('g')
      .selectAll('line')
      .data(simLinks)
      .join('line')
      .attr('stroke', 'currentColor')
      .attr('class', 'text-dark/20 dark:text-light/20')
      .attr('stroke-width', d => Math.max(1, Math.log10(d.conductance + 1)))
      .attr('marker-end', 'url(#arrowhead)');

    const maxMu = d3.max(simNodes, d => d.mu);
    const minMu = d3.min(simNodes, d => d.mu);
    const colorScale = d3.scaleSequential(d3.interpolateViridis)
      .domain([minMu, maxMu]);

    const node = g.append('g')
      .selectAll('g')
      .data(simNodes)
      .join('g')
      .call(d3.drag()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x; d.fy = d.y;
        })
        .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null; d.fy = null;
        }));

    node.append('circle')
      .attr('r', 12)
      .attr('fill', d => colorScale(d.mu))
      .attr('stroke', 'currentColor')
      .attr('class', 'text-dark/40 dark:text-light/40')
      .attr('stroke-width', 1.5);

    node.append('text')
      .text(d => d.name.length > 8 ? d.name.slice(0, 7) + '...' : d.name)
      .attr('dy', -18)
      .attr('text-anchor', 'middle')
      .attr('font-size', '9px')
      .attr('fill', 'currentColor')
      .attr('class', 'text-dark dark:text-light');

    node.append('title')
      .text(d => `${d.name}\nmu: ${d.mu.toFixed(2)} kJ/mol\nconc: ${d.concentration}`);

    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    return () => simulation.stop();
  }, [circuit]);

  if (!circuit) {
    return (
      <div className="bg-light dark:bg-dark border border-dark/10 dark:border-light/10 rounded-xl p-6 shadow-sm
                      flex items-center justify-center min-h-[400px]">
        <p className="text-dark/40 dark:text-light/40 text-sm">
          Search for a pathway or load the demo to see the circuit graph
        </p>
      </div>
    );
  }

  return (
    <div ref={containerRef}
         className="bg-light dark:bg-dark border border-dark/10 dark:border-light/10 rounded-xl p-4 shadow-sm">
      <h3 className="font-bold text-sm mb-2 text-dark dark:text-light">
        Circuit Graph — {circuit.numNodes} nodes, {circuit.numEdges} edges
      </h3>
      <svg ref={svgRef} className="w-full text-dark dark:text-light" style={{ minHeight: 400 }} />
    </div>
  );
}
