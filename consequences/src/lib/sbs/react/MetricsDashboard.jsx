/* ============================================================================
 * MetricsDashboard — S-entropy scatter, flux pattern, backward navigation.
 *
 * Props-only port of hegel's src/components/sbs/MetricsDashboard.js. The chart
 * internals (d3) are verbatim so the output is identical across hosts; the
 * only changes are: (1) data comes from props, not SBSContext; (2) the outer
 * container styling is neutral (host-agnostic) rather than hegel's Tailwind
 * theme; (3) the backward path binds to runSBS's top-level `navigation`.
 *
 * Consumes runSBS(source) output directly:
 *   <MetricsDashboard metrics={result.metrics}
 *                     circuit={result.circuit}
 *                     navigation={result.navigation} />
 * ========================================================================== */

import React, { useRef, useEffect } from 'react';
import * as d3 from 'd3';

export default function MetricsDashboard({ metrics, circuit, navigation }) {
  if (!metrics || !circuit) {
    return (
      <div style={dashStyle.empty}>
        <span style={dashStyle.emptyText}>Run observation to see metrics</span>
      </div>
    );
  }

  return (
    <div style={dashStyle.root}>
      <div style={dashStyle.title}>Observation Metrics</div>
      <div style={dashStyle.scalars}>
        <Scalar label="R (coherence)" value={metrics.R} />
        <Scalar label="V (visibility)" value={metrics.V} />
        <Scalar label="backend" value={metrics.backend} raw />
        <Scalar
          label="render"
          value={metrics.renderTimeMs != null ? `${metrics.renderTimeMs.toFixed(1)} ms` : '—'}
          raw
        />
      </div>
      <SEntropyScatter Se={metrics.Se} Sk={metrics.Sk} St={metrics.St} nodes={circuit.nodes} />
      <FluxChart fluxHealthy={metrics.fluxHealthy} fluxCurrent={metrics.fluxCurrent} edges={circuit.edges} />
      <BackwardPath path={navigation} />
    </div>
  );
}

function Scalar({ label, value, raw }) {
  const shown = raw ? value : typeof value === 'number' ? value.toFixed(3) : '—';
  return (
    <div style={dashStyle.scalar}>
      <div style={dashStyle.scalarLabel}>{label}</div>
      <div style={dashStyle.scalarValue}>{shown}</div>
    </div>
  );
}

function SEntropyScatter({ Se, Sk, St, nodes }) {
  const svgRef = useRef();

  useEffect(() => {
    if (!Se || !nodes) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = 280, height = 200;
    const margin = { top: 20, right: 20, bottom: 35, left: 40 };
    const w = width - margin.left - margin.right;
    const h = height - margin.top - margin.bottom;

    svg.attr('width', width).attr('height', height);
    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const x = d3.scaleLinear().domain([0, 1]).range([0, w]);
    const y = d3.scaleLinear().domain([0, 1]).range([h, 0]);
    const color = d3.scaleSequential(d3.interpolateViridis).domain([0, 1]);

    g.append('g').attr('transform', `translate(0,${h})`).call(d3.axisBottom(x).ticks(5))
      .selectAll('text').style('fill', 'currentColor').style('font-size', '8px');
    g.append('g').call(d3.axisLeft(y).ticks(5))
      .selectAll('text').style('fill', 'currentColor').style('font-size', '8px');
    g.selectAll('.domain, .tick line').style('stroke', 'currentColor');

    g.append('text').attr('x', w / 2).attr('y', h + 30).attr('text-anchor', 'middle')
      .style('fill', 'currentColor').style('font-size', '9px').text('Se (electrical)');
    g.append('text').attr('transform', 'rotate(-90)').attr('x', -h / 2).attr('y', -30)
      .attr('text-anchor', 'middle').style('fill', 'currentColor').style('font-size', '9px').text('Sk (kinetic)');

    g.selectAll('circle').data(Se.map((s, i) => ({ se: s, sk: Sk[i], st: St[i], name: nodes[i].name })))
      .join('circle')
      .attr('cx', d => x(d.se))
      .attr('cy', d => y(d.sk))
      .attr('r', 5)
      .attr('fill', d => color(d.st))
      .attr('stroke', 'currentColor')
      .attr('stroke-width', 0.5)
      .attr('opacity', 0.8)
      .append('title')
      .text(d => `${d.name}\nSe=${d.se.toFixed(3)}, Sk=${d.sk.toFixed(3)}, St=${d.st.toFixed(3)}`);
  }, [Se, Sk, St, nodes]);

  return (
    <div>
      <div style={dashStyle.chartLabel}>S-entropy Scatter (Se vs Sk, color = St)</div>
      <svg ref={svgRef} style={dashStyle.svg} />
    </div>
  );
}

function FluxChart({ fluxHealthy, fluxCurrent, edges }) {
  const svgRef = useRef();

  useEffect(() => {
    if (!fluxHealthy || !edges) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = 280, height = 180;
    const margin = { top: 10, right: 10, bottom: 50, left: 50 };
    const w = width - margin.left - margin.right;
    const h = height - margin.top - margin.bottom;

    svg.attr('width', width).attr('height', height);
    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const labels = edges.map(e => e.name.length > 6 ? e.name.slice(0, 5) + '..' : e.name);
    const x = d3.scaleBand().domain(labels).range([0, w]).padding(0.2);
    const maxF = Math.max(...fluxHealthy, ...fluxCurrent) * 1.1;
    const y = d3.scaleLog()
      .domain([Math.max(0.01, Math.min(...fluxHealthy.filter(f => f > 0)) * 0.1), maxF])
      .range([h, 0]).clamp(true);

    g.append('g').attr('transform', `translate(0,${h})`).call(d3.axisBottom(x))
      .selectAll('text').attr('transform', 'rotate(-50)').style('text-anchor', 'end')
      .style('fill', 'currentColor').style('font-size', '7px');
    g.append('g').call(d3.axisLeft(y).ticks(4, '.0e'))
      .selectAll('text').style('fill', 'currentColor').style('font-size', '7px');
    g.selectAll('.domain, .tick line').style('stroke', 'currentColor');

    const bw = x.bandwidth() / 2;
    g.selectAll('.bar-healthy').data(fluxHealthy).join('rect')
      .attr('x', (d, i) => x(labels[i]))
      .attr('width', bw)
      .attr('y', d => y(Math.max(d, 0.01)))
      .attr('height', d => h - y(Math.max(d, 0.01)))
      .attr('fill', '#4A90D9')
      .attr('opacity', 0.7);

    g.selectAll('.bar-current').data(fluxCurrent).join('rect')
      .attr('x', (d, i) => x(labels[i]) + bw)
      .attr('width', bw)
      .attr('y', d => y(Math.max(d, 0.01)))
      .attr('height', d => h - y(Math.max(d, 0.01)))
      .attr('fill', '#E74C3C')
      .attr('opacity', 0.7);
  }, [fluxHealthy, fluxCurrent, edges]);

  return (
    <div>
      <div style={dashStyle.chartLabel}>Flux Pattern (blue = healthy, red = current)</div>
      <svg ref={svgRef} style={dashStyle.svg} />
    </div>
  );
}

function BackwardPath({ path }) {
  if (!path || path.length === 0) return null;

  return (
    <div>
      <div style={dashStyle.chartLabel}>Backward Navigation (MAP trajectory)</div>
      <div style={dashStyle.pathRow}>
        {path.map((node, i) => (
          <React.Fragment key={node.nodeId}>
            <span style={dashStyle.pathNode}>{node.name}</span>
            {i < path.length - 1 && <span style={dashStyle.pathArrow}>&larr;</span>}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

// Host-agnostic inline styles. The charts themselves use `currentColor`, so
// they adapt to whatever text color the host sets on the container.
const dashStyle = {
  root: { display: 'flex', flexDirection: 'column', gap: '16px', color: 'inherit' },
  empty: {
    minHeight: 300, display: 'flex', alignItems: 'center', justifyContent: 'center',
    border: '1px solid rgba(128,128,128,0.2)', borderRadius: 12,
  },
  emptyText: { opacity: 0.4, fontSize: 13 },
  title: { fontWeight: 700, fontSize: 13 },
  scalars: { display: 'flex', flexWrap: 'wrap', gap: '10px' },
  scalar: {
    border: '1px solid rgba(128,128,128,0.25)', borderRadius: 8,
    padding: '4px 10px', minWidth: 84,
  },
  scalarLabel: { fontSize: 9, opacity: 0.6 },
  scalarValue: { fontSize: 14, fontFamily: 'monospace' },
  chartLabel: { fontSize: 11, opacity: 0.6, marginBottom: 6 },
  svg: { color: 'inherit' },
  pathRow: { display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 4 },
  pathNode: {
    fontSize: 11, padding: '2px 8px', borderRadius: 4, fontFamily: 'monospace',
    background: 'rgba(128,128,128,0.15)',
  },
  pathArrow: { opacity: 0.3, fontSize: 11 },
};
