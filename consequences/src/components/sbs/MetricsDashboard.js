import React, { useRef, useEffect } from 'react';
import * as d3 from 'd3';
import { useSBS } from './SBSContext';

export default function MetricsDashboard() {
  const { metrics, circuit } = useSBS();

  if (!metrics || !circuit) {
    return (
      <div className="bg-light dark:bg-dark border border-dark/10 dark:border-light/10 rounded-xl p-6 shadow-sm
                      flex items-center justify-center min-h-[300px]">
        <p className="text-dark/40 dark:text-light/40 text-sm">
          Run observation to see metrics
        </p>
      </div>
    );
  }

  return (
    <div className="bg-light dark:bg-dark border border-dark/10 dark:border-light/10 rounded-xl p-6 shadow-sm space-y-6">
      <h3 className="font-bold text-sm text-dark dark:text-light">Observation Metrics</h3>
      <SEntropyScatter Se={metrics.Se} Sk={metrics.Sk} St={metrics.St} nodes={circuit.nodes} />
      <FluxChart fluxHealthy={metrics.fluxHealthy} fluxCurrent={metrics.fluxCurrent} edges={circuit.edges} />
      <BackwardPath path={metrics.backwardPath} />
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
      <div className="text-xs text-dark/60 dark:text-light/60 mb-2">S-entropy Scatter (Se vs Sk, color = St)</div>
      <svg ref={svgRef} className="text-dark dark:text-light" />
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
    const y = d3.scaleLog().domain([Math.max(0.01, Math.min(...fluxHealthy.filter(f => f > 0)) * 0.1), maxF]).range([h, 0]).clamp(true);

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
      <div className="text-xs text-dark/60 dark:text-light/60 mb-2">
        Flux Pattern (blue = healthy, red = current)
      </div>
      <svg ref={svgRef} className="text-dark dark:text-light" />
    </div>
  );
}

function BackwardPath({ path }) {
  if (!path || path.length === 0) return null;

  return (
    <div>
      <div className="text-xs text-dark/60 dark:text-light/60 mb-2">Backward Navigation (MAP trajectory)</div>
      <div className="flex flex-wrap items-center gap-1">
        {path.map((node, i) => (
          <React.Fragment key={node.nodeId}>
            <span className="text-xs px-2 py-1 rounded bg-primary/10 dark:bg-primaryDark/10
                             text-dark dark:text-light font-mono">
              {node.name}
            </span>
            {i < path.length - 1 && (
              <span className="text-dark/30 dark:text-light/30 text-xs">&larr;</span>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}
