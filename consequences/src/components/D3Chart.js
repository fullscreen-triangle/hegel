import React, { useRef, useEffect } from 'react';
import * as d3 from 'd3';

// Bar Chart
export const BarChart = ({ data, width = 500, height = 300, color = '#B63E96' }) => {
  const svgRef = useRef();

  useEffect(() => {
    if (!data || data.length === 0) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 20, right: 20, bottom: 60, left: 60 };
    const w = width - margin.left - margin.right;
    const h = height - margin.top - margin.bottom;

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand().domain(data.map(d => d.label)).range([0, w]).padding(0.3);
    const y = d3.scaleLinear().domain([0, d3.max(data, d => d.value) * 1.1]).range([h, 0]);

    g.append('g').attr('transform', `translate(0,${h})`).call(d3.axisBottom(x))
      .selectAll('text').attr('transform', 'rotate(-45)').style('text-anchor', 'end').style('font-size', '10px').style('fill', 'currentColor');
    g.append('g').call(d3.axisLeft(y).ticks(5)).selectAll('text').style('fill', 'currentColor');
    g.selectAll('.domain, .tick line').style('stroke', 'currentColor');

    g.selectAll('rect').data(data).join('rect')
      .attr('x', d => x(d.label))
      .attr('y', h)
      .attr('width', x.bandwidth())
      .attr('height', 0)
      .attr('fill', (d, i) => d.color || d3.interpolateViridis(i / data.length))
      .attr('rx', 3)
      .transition().duration(800).delay((d, i) => i * 100)
      .attr('y', d => y(d.value))
      .attr('height', d => h - y(d.value));
  }, [data, width, height, color]);

  return <svg ref={svgRef} width={width} height={height} className="text-dark dark:text-light" />;
};

// Line Chart
export const LineChart = ({ data, width = 500, height = 300, color = '#B63E96' }) => {
  const svgRef = useRef();

  useEffect(() => {
    if (!data || data.length === 0) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 20, right: 20, bottom: 40, left: 60 };
    const w = width - margin.left - margin.right;
    const h = height - margin.top - margin.bottom;

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const x = d3.scaleLinear().domain(d3.extent(data, d => d.x)).range([0, w]);
    const y = d3.scaleLinear().domain([0, d3.max(data, d => d.y) * 1.1]).range([h, 0]);

    g.append('g').attr('transform', `translate(0,${h})`).call(d3.axisBottom(x).ticks(5)).selectAll('text').style('fill', 'currentColor');
    g.append('g').call(d3.axisLeft(y).ticks(5)).selectAll('text').style('fill', 'currentColor');
    g.selectAll('.domain, .tick line').style('stroke', 'currentColor');

    const line = d3.line().x(d => x(d.x)).y(d => y(d.y)).curve(d3.curveMonotoneX);

    const path = g.append('path').datum(data).attr('fill', 'none').attr('stroke', color)
      .attr('stroke-width', 2.5).attr('d', line);

    const totalLength = path.node().getTotalLength();
    path.attr('stroke-dasharray', totalLength).attr('stroke-dashoffset', totalLength)
      .transition().duration(1500).attr('stroke-dashoffset', 0);

    g.selectAll('circle').data(data).join('circle')
      .attr('cx', d => x(d.x)).attr('cy', d => y(d.y)).attr('r', 3).attr('fill', color)
      .attr('opacity', 0).transition().duration(300).delay((d, i) => 1500 + i * 50).attr('opacity', 1);
  }, [data, width, height, color]);

  return <svg ref={svgRef} width={width} height={height} className="text-dark dark:text-light" />;
};

// Scatter Plot
export const ScatterPlot = ({ data, width = 500, height = 300 }) => {
  const svgRef = useRef();

  useEffect(() => {
    if (!data || data.length === 0) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 20, right: 20, bottom: 40, left: 60 };
    const w = width - margin.left - margin.right;
    const h = height - margin.top - margin.bottom;

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const x = d3.scaleLinear().domain(d3.extent(data, d => d.x)).nice().range([0, w]);
    const y = d3.scaleLinear().domain(d3.extent(data, d => d.y)).nice().range([h, 0]);

    g.append('g').attr('transform', `translate(0,${h})`).call(d3.axisBottom(x).ticks(5)).selectAll('text').style('fill', 'currentColor');
    g.append('g').call(d3.axisLeft(y).ticks(5)).selectAll('text').style('fill', 'currentColor');
    g.selectAll('.domain, .tick line').style('stroke', 'currentColor');

    // Reference line y=x
    const minVal = Math.min(d3.min(data, d => d.x), d3.min(data, d => d.y));
    const maxVal = Math.max(d3.max(data, d => d.x), d3.max(data, d => d.y));
    g.append('line').attr('x1', x(minVal)).attr('y1', y(minVal))
      .attr('x2', x(maxVal)).attr('y2', y(maxVal))
      .attr('stroke', '#999').attr('stroke-dasharray', '4,4').attr('stroke-width', 1);

    g.selectAll('circle').data(data).join('circle')
      .attr('cx', d => x(d.x)).attr('cy', d => y(d.y)).attr('r', 0)
      .attr('fill', (d, i) => d3.interpolateViridis(i / data.length))
      .attr('stroke', '#fff').attr('stroke-width', 1)
      .transition().duration(500).delay((d, i) => i * 80).attr('r', 6);
  }, [data, width, height]);

  return <svg ref={svgRef} width={width} height={height} className="text-dark dark:text-light" />;
};

// Heatmap
export const Heatmap = ({ data, labels, width = 400, height = 400 }) => {
  const svgRef = useRef();

  useEffect(() => {
    if (!data || data.length === 0) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 20, right: 20, bottom: 60, left: 80 };
    const w = width - margin.left - margin.right;
    const h = height - margin.top - margin.bottom;
    const n = labels.length;
    const cellW = w / n;
    const cellH = h / n;

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);
    const color = d3.scaleSequential(d3.interpolateViridis).domain([0, 1]);

    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        g.append('rect').attr('x', j * cellW).attr('y', i * cellH)
          .attr('width', cellW - 1).attr('height', cellH - 1)
          .attr('fill', color(data[i][j])).attr('rx', 2)
          .attr('opacity', 0).transition().duration(300).delay((i * n + j) * 20).attr('opacity', 1);
      }
    }

    g.selectAll('.labelX').data(labels).join('text').attr('class', 'labelX')
      .attr('x', (d, i) => i * cellW + cellW / 2).attr('y', h + 15)
      .attr('text-anchor', 'middle').style('font-size', '9px').style('fill', 'currentColor').text(d => d);
    g.selectAll('.labelY').data(labels).join('text').attr('class', 'labelY')
      .attr('x', -8).attr('y', (d, i) => i * cellH + cellH / 2 + 4)
      .attr('text-anchor', 'end').style('font-size', '9px').style('fill', 'currentColor').text(d => d);
  }, [data, labels, width, height]);

  return <svg ref={svgRef} width={width} height={height} className="text-dark dark:text-light" />;
};

// Radial/Gauge Chart
export const GaugeChart = ({ value, max = 1, label = '', width = 200, height = 200 }) => {
  const svgRef = useRef();

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const g = svg.append('g').attr('transform', `translate(${width/2},${height/2})`);
    const r = Math.min(width, height) / 2 - 20;

    const arc = d3.arc().innerRadius(r * 0.7).outerRadius(r).startAngle(0);

    g.append('path').datum({ endAngle: Math.PI * 2 })
      .attr('d', arc).attr('fill', '#e0e0e0').attr('opacity', 0.3);

    g.append('path').datum({ endAngle: 0 })
      .attr('d', arc).attr('fill', '#58E6D9')
      .transition().duration(1500)
      .attrTween('d', function() {
        const interpolate = d3.interpolate(0, (value / max) * Math.PI * 2);
        return function(t) { return arc({ endAngle: interpolate(t) }); };
      });

    g.append('text').attr('text-anchor', 'middle').attr('dy', '0.35em')
      .style('font-size', '24px').style('font-weight', 'bold').style('fill', 'currentColor')
      .text(typeof value === 'number' && value < 100 ? value.toFixed(2) : value);

    g.append('text').attr('text-anchor', 'middle').attr('dy', '2em')
      .style('font-size', '11px').style('fill', 'currentColor').attr('opacity', 0.7).text(label);
  }, [value, max, label, width, height]);

  return <svg ref={svgRef} width={width} height={height} className="text-dark dark:text-light" />;
};
