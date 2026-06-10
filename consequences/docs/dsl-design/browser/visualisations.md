# Partition-Bio Charts Module: Comprehensive Visualization Library

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [2D Chart Types](#2d-chart-types)
3. [3D Chart Types](#3d-chart-types)
4. [Interactive Features](#interactive-features)
5. [Implementation](#implementation)
6. [API Reference](#api-reference)
7. [Examples](#examples)

---

## Architecture Overview

### Module Structure

```
partition-bio-charts/
├── src/
│   ├── core/
│   │   ├── ChartBase.ts           # Base class for all charts
│   │   ├── ScaleManager.ts        # D3 scale management
│   │   ├── AxisManager.ts         # Axis rendering
│   │   ├── LegendManager.ts       # Legend generation
│   │   ├── TooltipManager.ts      # Interactive tooltips
│   │   └── AnimationEngine.ts     # Smooth transitions
│   ├── 2d/
│   │   ├── basic/
│   │   │   ├── LineChart.ts       # Time series, trajectories
│   │   │   ├── AreaChart.ts       # Stacked concentrations
│   │   │   ├── BarChart.ts        # Discrete comparisons
│   │   │   ├── ScatterPlot.ts     # Correlation analysis
│   │   │   └── HistogramChart.ts  # Distribution analysis
│   │   ├── specialized/
│   │   │   ├── HeatmapChart.ts    # Expression matrices
│   │   │   ├── CircularPlot.ts    # Phase coherence
│   │   │   ├── RadarChart.ts      # Multi-dimensional comparison
│   │   │   ├── SankeyDiagram.ts   # Metabolic flux
│   │   │   ├── ChordDiagram.ts    # Interaction networks
│   │   │   ├── TreemapChart.ts    # Hierarchical partition
│   │   │   ├── SunburstChart.ts   # Recursive decomposition
│   │   │   ├── VoronoiDiagram.ts  # Spatial tessellation
│   │   │   └── StreamGraph.ts     # Temporal evolution
│   │   ├── network/
│   │   │   ├── ForceDirectedGraph.ts  # Circuit topology
│   │   │   ├── HierarchicalGraph.ts   # Pathway hierarchy
│   │   │   ├── ArcDiagram.ts          # Linear network
│   │   │   └── MatrixView.ts          # Adjacency matrix
│   │   └── biological/
│   │       ├── PhylogeneticTree.ts    # Evolution
│   │       ├── GenomeViewer.ts        # Genomic coordinates
│   │       ├── ProteinStructure2D.ts  # Secondary structure
│   │       ├── PathwayMap.ts          # KEGG-style maps
│   │       └── CellCycleWheel.ts      # Phase distribution
│   ├── 3d/
│   │   ├── basic/
│   │   │   ├── Surface3D.ts       # S-entropy landscape
│   │   │   ├── Scatter3D.ts       # 3D point clouds
│   │   │   ├── Line3D.ts          # 3D trajectories
│   │   │   ├── Bar3D.ts           # 3D histograms
│   │   │   └── Mesh3D.ts          # Isosurfaces
│   │   ├── volume/
│   │   │   ├── VolumeRenderer.ts  # Ray marching
│   │   │   ├── SliceViewer.ts     # Orthogonal slices
│   │   │   ├── IsocontourPlot.ts  # Level sets
│   │   │   └── VectorField3D.ts   # Gradient flows
│   │   ├── molecular/
│   │   │   ├── MolecularViewer.ts # Protein structures
│   │   │   ├── BallAndStick.ts    # Atomic models
│   │   │   ├── RibbonDiagram.ts   # Protein backbone
│   │   │   └── SurfaceModel.ts    # Molecular surfaces
│   │   └── specialized/
│   │       ├── PartitionCube.ts   # S-entropy volume
│   │       ├── PhaseSpace3D.ts    # Dynamical systems
│   │       ├── NetworkGraph3D.ts  # 3D force layout
│   │       └── TensorField.ts     # Multi-dimensional data
│   ├── composite/
│   │   ├── Dashboard.ts           # Multi-chart layout
│   │   ├── LinkedViews.ts         # Coordinated interactions
│   │   ├── SmallMultiples.ts      # Faceted displays
│   │   └── AnimatedSequence.ts    # Temporal animations
│   ├── utils/
│   │   ├── ColorSchemes.ts        # Biological color palettes
│   │   ├── DataTransform.ts       # Data preprocessing
│   │   ├── ExportManager.ts       # SVG/PNG/WebGL export
│   │   └── AccessibilityHelper.ts # ARIA labels, keyboard nav
│   └── index.ts                   # Main export
├── examples/
│   ├── glycolysis-dashboard.html
│   ├── protein-folding.html
│   ├── disease-progression.html
│   └── multi-omics.html
├── docs/
│   ├── api-reference.md
│   ├── chart-gallery.md
│   └── tutorials/
└── package.json
```

---

## 2D Chart Types

### 1. Basic Charts

#### 1.1 Line Chart (Time Series)

```typescript
import * as d3 from 'd3';
import { ChartBase, ChartConfig } from '../core/ChartBase';

export interface LineChartConfig extends ChartConfig {
  xField: string;
  yFields: string[];
  interpolation?: 'linear' | 'step' | 'basis' | 'cardinal' | 'monotone';
  showPoints?: boolean;
  pointRadius?: number;
  lineWidth?: number;
  colors?: string[];
  showConfidenceBands?: boolean;
  confidenceLevel?: number;
}

export class LineChart extends ChartBase {
  private xScale: d3.ScaleLinear<number, number>;
  private yScale: d3.ScaleLinear<number, number>;
  private line: d3.Line<any>;
  private area: d3.Area<any>;
  
  constructor(container: string, config: LineChartConfig) {
    super(container, config);
    this.config = { ...this.defaultConfig(), ...config };
    this.initialize();
  }
  
  private defaultConfig(): Partial<LineChartConfig> {
    return {
      interpolation: 'monotone',
      showPoints: false,
      pointRadius: 3,
      lineWidth: 2,
      colors: d3.schemeCategory10,
      showConfidenceBands: false,
      confidenceLevel: 0.95
    };
  }
  
  protected initialize(): void {
    super.initialize();
    
    // Create scales
    this.xScale = d3.scaleLinear()
      .range([0, this.width]);
    
    this.yScale = d3.scaleLinear()
      .range([this.height, 0]);
    
    // Create line generator
    const interpolationMap = {
      'linear': d3.curveLinear,
      'step': d3.curveStep,
      'basis': d3.curveBasis,
      'cardinal': d3.curveCardinal,
      'monotone': d3.curveMonotoneX
    };
    
    this.line = d3.line()
      .x((d: any) => this.xScale(d[this.config.xField]))
      .y((d: any) => this.yScale(d.value))
      .curve(interpolationMap[this.config.interpolation]);
    
    // Create area generator for confidence bands
    if (this.config.showConfidenceBands) {
      this.area = d3.area()
        .x((d: any) => this.xScale(d[this.config.xField]))
        .y0((d: any) => this.yScale(d.lower))
        .y1((d: any) => this.yScale(d.upper))
        .curve(interpolationMap[this.config.interpolation]);
    }
  }
  
  public render(data: any[]): void {
    // Update scales
    this.xScale.domain(d3.extent(data, d => d[this.config.xField]));
    
    const allValues = this.config.yFields.flatMap(field => 
      data.map(d => d[field])
    );
    this.yScale.domain([
      d3.min(allValues) * 0.95,
      d3.max(allValues) * 1.05
    ]);
    
    // Render axes
    this.renderAxes();
    
    // Render lines for each field
    this.config.yFields.forEach((field, i) => {
      const lineData = data.map(d => ({
        [this.config.xField]: d[this.config.xField],
        value: d[field]
      }));
      
      // Confidence bands
      if (this.config.showConfidenceBands && d[`${field}_lower`]) {
        const bandData = data.map(d => ({
          [this.config.xField]: d[this.config.xField],
          lower: d[`${field}_lower`],
          upper: d[`${field}_upper`]
        }));
        
        this.g.append('path')
          .datum(bandData)
          .attr('class', `confidence-band-${i}`)
          .attr('fill', this.config.colors[i])
          .attr('opacity', 0.2)
          .attr('d', this.area);
      }
      
      // Line path
      const path = this.g.append('path')
        .datum(lineData)
        .attr('class', `line-${i}`)
        .attr('fill', 'none')
        .attr('stroke', this.config.colors[i])
        .attr('stroke-width', this.config.lineWidth)
        .attr('d', this.line);
      
      // Animate line drawing
      const totalLength = path.node().getTotalLength();
      path
        .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
        .attr('stroke-dashoffset', totalLength)
        .transition()
        .duration(1500)
        .ease(d3.easeLinear)
        .attr('stroke-dashoffset', 0);
      
      // Points
      if (this.config.showPoints) {
        this.g.selectAll(`.point-${i}`)
          .data(lineData)
          .enter()
          .append('circle')
          .attr('class', `point-${i}`)
          .attr('cx', d => this.xScale(d[this.config.xField]))
          .attr('cy', d => this.yScale(d.value))
          .attr('r', 0)
          .attr('fill', this.config.colors[i])
          .on('mouseover', (event, d) => this.showTooltip(event, d, field))
          .on('mouseout', () => this.hideTooltip())
          .transition()
          .delay((d, j) => j * 10)
          .duration(300)
          .attr('r', this.config.pointRadius);
      }
    });
    
    // Legend
    this.renderLegend(this.config.yFields);
  }
  
  private renderAxes(): void {
    // X axis
    const xAxis = d3.axisBottom(this.xScale)
      .ticks(10)
      .tickFormat(d => d3.format('.2f')(d));
    
    this.g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${this.height})`)
      .call(xAxis)
      .append('text')
      .attr('x', this.width / 2)
      .attr('y', 40)
      .attr('fill', '#000')
      .attr('text-anchor', 'middle')
      .text(this.config.xLabel || this.config.xField);
    
    // Y axis
    const yAxis = d3.axisLeft(this.yScale)
      .ticks(10)
      .tickFormat(d => d3.format('.2f')(d));
    
    this.g.append('g')
      .attr('class', 'y-axis')
      .call(yAxis)
      .append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -this.height / 2)
      .attr('y', -50)
      .attr('fill', '#000')
      .attr('text-anchor', 'middle')
      .text(this.config.yLabel || 'Value');
    
    // Grid lines
    this.g.append('g')
      .attr('class', 'grid')
      .attr('opacity', 0.1)
      .call(d3.axisLeft(this.yScale)
        .ticks(10)
        .tickSize(-this.width)
        .tickFormat(() => '')
      );
  }
  
  private showTooltip(event: MouseEvent, d: any, field: string): void {
    const tooltip = d3.select('body')
      .append('div')
      .attr('class', 'partition-bio-tooltip')
      .style('position', 'absolute')
      .style('background', 'rgba(0,0,0,0.8)')
      .style('color', '#fff')
      .style('padding', '8px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('z-index', '1000');
    
    tooltip.html(`
      <strong>${field}</strong><br/>
      ${this.config.xField}: ${d[this.config.xField].toFixed(2)}<br/>
      Value: ${d.value.toFixed(4)}
    `)
      .style('left', `${event.pageX + 10}px`)
      .style('top', `${event.pageY - 28}px`);
  }
  
  private hideTooltip(): void {
    d3.selectAll('.partition-bio-tooltip').remove();
  }
  
  public update(data: any[]): void {
    // Smooth transition to new data
    this.config.yFields.forEach((field, i) => {
      const lineData = data.map(d => ({
        [this.config.xField]: d[this.config.xField],
        value: d[field]
      }));
      
      this.g.select(`.line-${i}`)
        .datum(lineData)
        .transition()
        .duration(750)
        .attr('d', this.line);
      
      if (this.config.showPoints) {
        const points = this.g.selectAll(`.point-${i}`)
          .data(lineData);
        
        points.transition()
          .duration(750)
          .attr('cx', d => this.xScale(d[this.config.xField]))
          .attr('cy', d => this.yScale(d.value));
      }
    });
  }
}
```

#### 1.2 Circular Phase Plot (Phase Coherence)

```typescript
export interface CircularPlotConfig extends ChartConfig {
  phaseField: string;
  amplitudeField?: string;
  labelField?: string;
  showOrderParameter?: boolean;
  showGrid?: boolean;
  gridLevels?: number;
  colors?: string[];
}

export class CircularPlot extends ChartBase {
  private radius: number;
  private angleScale: d3.ScaleLinear<number, number>;
  private radiusScale: d3.ScaleLinear<number, number>;
  
  constructor(container: string, config: CircularPlotConfig) {
    super(container, config);
    this.config = { ...this.defaultConfig(), ...config };
    this.initialize();
  }
  
  private defaultConfig(): Partial<CircularPlotConfig> {
    return {
      showOrderParameter: true,
      showGrid: true,
      gridLevels: 5,
      colors: d3.schemeCategory10
    };
  }
  
  protected initialize(): void {
    super.initialize();
    
    this.radius = Math.min(this.width, this.height) / 2 - 50;
    
    // Move origin to center
    this.g.attr('transform', 
      `translate(${this.width / 2 + this.margin.left},${this.height / 2 + this.margin.top})`
    );
    
    // Angle scale (0 to 2π)
    this.angleScale = d3.scaleLinear()
      .domain([0, 2 * Math.PI])
      .range([0, 2 * Math.PI]);
    
    // Radius scale (for amplitude)
    this.radiusScale = d3.scaleLinear()
      .domain([0, 1])
      .range([0, this.radius]);
  }
  
  public render(data: any[]): void {
    // Update radius scale if amplitude field exists
    if (this.config.amplitudeField) {
      const maxAmplitude = d3.max(data, d => d[this.config.amplitudeField]);
      this.radiusScale.domain([0, maxAmplitude]);
    }
    
    // Render grid
    if (this.config.showGrid) {
      this.renderGrid();
    }
    
    // Render phase vectors
    data.forEach((d, i) => {
      const phase = d[this.config.phaseField];
      const amplitude = this.config.amplitudeField 
        ? d[this.config.amplitudeField] 
        : this.radius;
      
      const x = this.radiusScale(amplitude) * Math.cos(phase - Math.PI / 2);
      const y = this.radiusScale(amplitude) * Math.sin(phase - Math.PI / 2);
      
      // Vector line
      this.g.append('line')
        .attr('class', `phase-vector-${i}`)
        .attr('x1', 0)
        .attr('y1', 0)
        .attr('x2', 0)
        .attr('y2', 0)
        .attr('stroke', this.config.colors[i % this.config.colors.length])
        .attr('stroke-width', 2)
        .transition()
        .duration(1000)
        .attr('x2', x)
        .attr('y2', y);
      
      // Vector point
      this.g.append('circle')
        .attr('class', `phase-point-${i}`)
        .attr('cx', 0)
        .attr('cy', 0)
        .attr('r', 0)
        .attr('fill', this.config.colors[i % this.config.colors.length])
        .on('mouseover', (event) => this.showPhaseTooltip(event, d, i))
        .on('mouseout', () => this.hideTooltip())
        .transition()
        .duration(1000)
        .attr('cx', x)
        .attr('cy', y)
        .attr('r', 6);
      
      // Label
      if (this.config.labelField) {
        this.g.append('text')
          .attr('class', `phase-label-${i}`)
          .attr('x', x * 1.15)
          .attr('y', y * 1.15)
          .attr('text-anchor', 'middle')
          .attr('dominant-baseline', 'middle')
          .attr('font-size', '10px')
          .attr('opacity', 0)
          .text(d[this.config.labelField])
          .transition()
          .duration(1000)
          .attr('opacity', 1);
      }
    });
    
    // Compute and render order parameter
    if (this.config.showOrderParameter) {
      this.renderOrderParameter(data);
    }
  }
  
  private renderGrid(): void {
    // Concentric circles
    for (let i = 1; i <= this.config.gridLevels; i++) {
      const r = (this.radius / this.config.gridLevels) * i;
      
      this.g.append('circle')
        .attr('cx', 0)
        .attr('cy', 0)
        .attr('r', r)
        .attr('fill', 'none')
        .attr('stroke', '#ddd')
        .attr('stroke-width', 1);
      
      // Label
      this.g.append('text')
        .attr('x', 5)
        .attr('y', -r)
        .attr('font-size', '10px')
        .attr('fill', '#999')
        .text((i / this.config.gridLevels).toFixed(1));
    }
    
    // Radial lines (every 30 degrees)
    for (let angle = 0; angle < 360; angle += 30) {
      const rad = (angle * Math.PI) / 180;
      const x = this.radius * Math.cos(rad - Math.PI / 2);
      const y = this.radius * Math.sin(rad - Math.PI / 2);
      
      this.g.append('line')
        .attr('x1', 0)
        .attr('y1', 0)
        .attr('x2', x)
        .attr('y2', y)
        .attr('stroke', '#ddd')
        .attr('stroke-width', 1);
      
      // Angle label
      this.g.append('text')
        .attr('x', x * 1.1)
        .attr('y', y * 1.1)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('font-size', '10px')
        .attr('fill', '#999')
        .text(`${angle}°`);
    }
  }
  
  private renderOrderParameter(data: any[]): void {
    // Compute Kuramoto order parameter
    let sumX = 0, sumY = 0;
    
    data.forEach(d => {
      const phase = d[this.config.phaseField];
      sumX += Math.cos(phase);
      sumY += Math.sin(phase);
    });
    
    const r = Math.sqrt(sumX * sumX + sumY * sumY) / data.length;
    const avgPhase = Math.atan2(sumY, sumX);
    
    const x = this.radius * r * Math.cos(avgPhase - Math.PI / 2);
    const y = this.radius * r * Math.sin(avgPhase - Math.PI / 2);
    
    // Order parameter vector (thick red line)
    this.g.append('line')
      .attr('class', 'order-parameter')
      .attr('x1', 0)
      .attr('y1', 0)
      .attr('x2', 0)
      .attr('y2', 0)
      .attr('stroke', '#ff0000')
      .attr('stroke-width', 4)
      .attr('marker-end', 'url(#arrow)')
      .transition()
      .duration(1500)
      .attr('x2', x)
      .attr('y2', y);
    
    // Arrow marker
    this.svg.append('defs')
      .append('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 8)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#ff0000');
    
    // Display r value
    this.g.append('text')
      .attr('x', 0)
      .attr('y', -this.radius - 20)
      .attr('text-anchor', 'middle')
      .attr('font-size', '16px')
      .attr('font-weight', 'bold')
      .attr('opacity', 0)
      .text(`r = ${r.toFixed(3)}`)
      .transition()
      .duration(1500)
      .attr('opacity', 1);
    
    // Health status
    const status = r > 0.7 ? 'Healthy' : r > 0.5 ? 'Stressed' : 'Diseased';
    const statusColor = r > 0.7 ? '#00aa00' : r > 0.5 ? '#aaaa00' : '#aa0000';
    
    this.g.append('text')
      .attr('x', 0)
      .attr('y', -this.radius - 40)
      .attr('text-anchor', 'middle')
      .attr('font-size', '14px')
      .attr('fill', statusColor)
      .attr('opacity', 0)
      .text(`Status: ${status}`)
      .transition()
      .duration(1500)
      .attr('opacity', 1);
  }
  
  private showPhaseTooltip(event: MouseEvent, d: any, index: number): void {
    const tooltip = d3.select('body')
      .append('div')
      .attr('class', 'partition-bio-tooltip')
      .style('position', 'absolute')
      .style('background', 'rgba(0,0,0,0.8)')
      .style('color', '#fff')
      .style('padding', '8px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('z-index', '1000');
    
    const phase = d[this.config.phaseField];
    const phaseDeg = (phase * 180 / Math.PI).toFixed(1);
    const amplitude = this.config.amplitudeField 
      ? d[this.config.amplitudeField].toFixed(3) 
      : 'N/A';
    
    tooltip.html(`
      <strong>${this.config.labelField ? d[this.config.labelField] : `Node ${index}`}</strong><br/>
      Phase: ${phaseDeg}° (${phase.toFixed(3)} rad)<br/>
      ${this.config.amplitudeField ? `Amplitude: ${amplitude}` : ''}
    `)
      .style('left', `${event.pageX + 10}px`)
      .style('top', `${event.pageY - 28}px`);
  }
}
```

#### 1.3 Heatmap Chart (Expression Matrices)

```typescript
export interface HeatmapConfig extends ChartConfig {
  rowField: string;
  colField: string;
  valueField: string;
  colorScheme?: 'viridis' | 'plasma' | 'inferno' | 'magma' | 'RdYlBu' | 'RdYlGn';
  showValues?: boolean;
  cellPadding?: number;
  dendrogramRow?: boolean;
  dendrogramCol?: boolean;
}

export class HeatmapChart extends ChartBase {
  private xScale: d3.ScaleBand<string>;
  private yScale: d3.ScaleBand<string>;
  private colorScale: d3.ScaleSequential<string>;
  
  constructor(container: string, config: HeatmapConfig) {
    super(container, config);
    this.config = { ...this.defaultConfig(), ...config };
    this.initialize();
  }
  
  private defaultConfig(): Partial<HeatmapConfig> {
    return {
      colorScheme: 'viridis',
      showValues: false,
      cellPadding: 2,
      dendrogramRow: false,
      dendrogramCol: false
    };
  }
  
  protected initialize(): void {
    super.initialize();
    
    // Band scales for rows and columns
    this.xScale = d3.scaleBand()
      .range([0, this.width])
      .padding(0.05);
    
    this.yScale = d3.scaleBand()
      .range([0, this.height])
      .padding(0.05);
    
    // Color scale
    const colorSchemes = {
      'viridis': d3.interpolateViridis,
      'plasma': d3.interpolatePlasma,
      'inferno': d3.interpolateInferno,
      'magma': d3.interpolateMagma,
      'RdYlBu': d3.interpolateRdYlBu,
      'RdYlGn': d3.interpolateRdYlGn
    };
    
    this.colorScale = d3.scaleSequential(colorSchemes[this.config.colorScheme]);
  }
  
  public render(data: any[]): void {
    // Extract unique rows and columns
    const rows = Array.from(new Set(data.map(d => d[this.config.rowField])));
    const cols = Array.from(new Set(data.map(d => d[this.config.colField])));
    
    // Update scales
    this.xScale.domain(cols);
    this.yScale.domain(rows);
    
    // Update color scale
    const values = data.map(d => d[this.config.valueField]);
    this.colorScale.domain([d3.min(values), d3.max(values)]);
    
    // Render cells
    const cells = this.g.selectAll('.heatmap-cell')
      .data(data)
      .enter()
      .append('rect')
      .attr('class', 'heatmap-cell')
      .attr('x', d => this.xScale(d[this.config.colField]))
      .attr('y', d => this.yScale(d[this.config.rowField]))
      .attr('width', this.xScale.bandwidth())
      .attr('height', this.yScale.bandwidth())
      .attr('fill', '#fff')
      .attr('stroke', '#ddd')
      .attr('stroke-width', 0.5)
      .on('mouseover', (event, d) => this.showHeatmapTooltip(event, d))
      .on('mouseout', () => this.hideTooltip());
    
    // Animate color fill
    cells.transition()
      .duration(1000)
      .delay((d, i) => i * 2)
      .attr('fill', d => this.colorScale(d[this.config.valueField]));
    
    // Render values in cells
    if (this.config.showValues) {
      this.g.selectAll('.heatmap-value')
        .data(data)
        .enter()
        .append('text')
        .attr('class', 'heatmap-value')
        .attr('x', d => this.xScale(d[this.config.colField]) + this.xScale.bandwidth() / 2)
        .attr('y', d => this.yScale(d[this.config.rowField]) + this.yScale.bandwidth() / 2)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('font-size', '10px')
        .attr('fill', d => {
          const value = d[this.config.valueField];
          const normalized = (value - this.colorScale.domain()[0]) / 
                           (this.colorScale.domain()[1] - this.colorScale.domain()[0]);
          return normalized > 0.5 ? '#fff' : '#000';
        })
        .attr('opacity', 0)
        .text(d => d[this.config.valueField].toFixed(2))
        .transition()
        .duration(1000)
        .attr('opacity', 1);
    }
    
    // Render axes
    this.renderAxes(rows, cols);
    
    // Render color legend
    this.renderColorLegend();
    
    // Render dendrograms if requested
    if (this.config.dendrogramRow) {
      this.renderDendrogram('row', rows, data);
    }
    if (this.config.dendrogramCol) {
      this.renderDendrogram('col', cols, data);
    }
  }
  
  private renderAxes(rows: string[], cols: string[]): void {
    // X axis (columns)
    this.g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${this.height})`)
      .call(d3.axisBottom(this.xScale))
      .selectAll('text')
      .attr('transform', 'rotate(-45)')
      .style('text-anchor', 'end');
    
    // Y axis (rows)
    this.g.append('g')
      .attr('class', 'y-axis')
      .call(d3.axisLeft(this.yScale));
  }
  
  private renderColorLegend(): void {
    const legendWidth = 20;
    const legendHeight = this.height;
    const legendX = this.width + 40;
    
    // Create gradient
    const defs = this.svg.append('defs');
    const gradient = defs.append('linearGradient')
      .attr('id', 'heatmap-gradient')
      .attr('x1', '0%')
      .attr('y1', '100%')
      .attr('x2', '0%')
      .attr('y2', '0%');
    
    // Add color stops
    const numStops = 10;
    for (let i = 0; i <= numStops; i++) {
      const t = i / numStops;
      gradient.append('stop')
        .attr('offset', `${t * 100}%`)
        .attr('stop-color', this.colorScale(
          this.colorScale.domain()[0] + t * (this.colorScale.domain()[1] - this.colorScale.domain()[0])
        ));
    }
    
    // Draw legend rectangle
    this.g.append('rect')
      .attr('x', legendX)
      .attr('y', 0)
      .attr('width', legendWidth)
      .attr('height', legendHeight)
      .style('fill', 'url(#heatmap-gradient)');
    
    // Legend axis
    const legendScale = d3.scaleLinear()
      .domain(this.colorScale.domain())
      .range([legendHeight, 0]);
    
    this.g.append('g')
      .attr('class', 'legend-axis')
      .attr('transform', `translate(${legendX + legendWidth},0)`)
      .call(d3.axisRight(legendScale).ticks(5));
  }
  
  private renderDendrogram(type: 'row' | 'col', labels: string[], data: any[]): void {
    // Hierarchical clustering using simple linkage
    // This is a simplified version - full implementation would use d3-hierarchy
    
    const dendrogramWidth = type === 'col' ? this.width : 100;
    const dendrogramHeight = type === 'row' ? this.height : 100;
    
    // Position dendrogram
    const x = type === 'col' ? 0 : -dendrogramWidth - 20;
    const y = type === 'row' ? 0 : -dendrogramHeight - 20;
    
    const dendrogramG = this.g.append('g')
      .attr('class', `dendrogram-${type}`)
      .attr('transform', `translate(${x},${y})`);
    
    // Placeholder for actual dendrogram rendering
    dendrogramG.append('text')
      .attr('x', dendrogramWidth / 2)
      .attr('y', dendrogramHeight / 2)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('fill', '#999')
      .text(`${type} dendrogram`);
  }
  
  private showHeatmapTooltip(event: MouseEvent, d: any): void {
    const tooltip = d3.select('body')
      .append('div')
      .attr('class', 'partition-bio-tooltip')
      .style('position', 'absolute')
      .style('background', 'rgba(0,0,0,0.8)')
      .style('color', '#fff')
      .style('padding', '8px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('z-index', '1000');
    
    tooltip.html(`
      <strong>${d[this.config.rowField]} × ${d[this.config.colField]}</strong><br/>
      Value: ${d[this.config.valueField].toFixed(4)}
    `)
      .style('left', `${event.pageX + 10}px`)
      .style('top', `${event.pageY - 28}px`);
  }
}
```

---

## 3D Chart Types

### 2.1 3D Surface Plot (S-Entropy Landscape)

```typescript
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

export interface Surface3DConfig {
  container: string;
  width: number;
  height: number;
  xField: string;
  yField: string;
  zField: string;
  resolution?: number;
  colorScheme?: 'viridis' | 'plasma' | 'rainbow';
  wireframe?: boolean;
  showAxes?: boolean;
  showGrid?: boolean;
  cameraPosition?: [number, number, number];
}

export class Surface3D {
  private container: HTMLElement;
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private controls: OrbitControls;
  private mesh: THREE.Mesh;
  private config: Surface3DConfig;
  
  constructor(config: Surface3DConfig) {
    this.config = { ...this.defaultConfig(), ...config };
    this.container = document.getElementById(config.container);
    this.initialize();
  }
  
  private defaultConfig(): Partial<Surface3DConfig> {
    return {
      resolution: 50,
      colorScheme: 'viridis',
      wireframe: false,
      showAxes: true,
      showGrid: true,
      cameraPosition: [2, 2, 2]
    };
  }
  
  private initialize(): void {
    // Scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0xffffff);
    
    // Camera
    this.camera = new THREE.PerspectiveCamera(
      75,
      this.config.width / this.config.height,
      0.1,
      1000
    );
    this.camera.position.set(...this.config.cameraPosition);
    
    // Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setSize(this.config.width, this.config.height);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.container.appendChild(this.renderer.domElement);
    
    // Controls
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    
    // Lights
    const ambientLight = new THREE.AmbientLight(0x404040, 2);
    this.scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(1, 1, 1);
    this.scene.add(directionalLight);
    
    // Axes
    if (this.config.showAxes) {
      const axesHelper = new THREE.AxesHelper(1.5);
      this.scene.add(axesHelper);
    }
    
    // Grid
    if (this.config.showGrid) {
      const gridHelper = new THREE.GridHelper(2, 20, 0xcccccc, 0xeeeeee);
      gridHelper.rotation.x = Math.PI / 2;
      this.scene.add(gridHelper);
    }
    
    // Start animation loop
    this.animate();
  }
  
  public render(data: any[]): void {
    // Remove existing mesh
    if (this.mesh) {
      this.scene.remove(this.mesh);
    }
    
    // Create geometry
    const geometry = this.createSurfaceGeometry(data);
    
    // Create material
    const material = new THREE.MeshPhongMaterial({
      vertexColors: true,
      side: THREE.DoubleSide,
      wireframe: this.config.wireframe,
      shininess: 30
    });
    
    // Create mesh
    this.mesh = new THREE.Mesh(geometry, material);
    this.scene.add(this.mesh);
  }
  
  private createSurfaceGeometry(data: any[]): THREE.BufferGeometry {
    const resolution = this.config.resolution;
    
    // Extract data ranges
    const xValues = data.map(d => d[this.config.xField]);
    const yValues = data.map(d => d[this.config.yField]);
    const zValues = data.map(d => d[this.config.zField]);
    
    const xMin = Math.min(...xValues);
    const xMax = Math.max(...xValues);
    const yMin = Math.min(...yValues);
    const yMax = Math.max(...yValues);
    const zMin = Math.min(...zValues);
    const zMax = Math.max(...zValues);
    
    // Create grid
    const positions = [];
    const colors = [];
    const indices = [];
    
    for (let i = 0; i < resolution; i++) {
      for (let j = 0; j < resolution; j++) {
        const x = xMin + (xMax - xMin) * (i / (resolution - 1));
        const y = yMin + (yMax - yMin) * (j / (resolution - 1));
        
        // Interpolate z value
        const z = this.interpolateZ(data, x, y);
        
        // Normalize to [-1, 1]
        const xNorm = 2 * (x - xMin) / (xMax - xMin) - 1;
        const yNorm = 2 * (y - yMin) / (yMax - yMin) - 1;
        const zNorm = 2 * (z - zMin) / (zMax - zMin) - 1;
        
        positions.push(xNorm, yNorm, zNorm);
        
        // Color based on height
        const color = this.getColor((z - zMin) / (zMax - zMin));
        colors.push(color.r, color.g, color.b);
      }
    }
    
    // Create triangles
    for (let i = 0; i < resolution - 1; i++) {
      for (let j = 0; j < resolution - 1; j++) {
        const a = i * resolution + j;
        const b = i * resolution + j + 1;
        const c = (i + 1) * resolution + j;
        const d = (i + 1) * resolution + j + 1;
        
        indices.push(a, b, c);
        indices.push(b, d, c);
      }
    }
    
    // Create geometry
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    geometry.setIndex(indices);
    geometry.computeVertexNormals();
    
    return geometry;
  }
  
  private interpolateZ(data: any[], x: number, y: number): number {
    // Simple nearest-neighbor interpolation
    // For production, use bilinear or bicubic interpolation
    
    let minDist = Infinity;
    let closestZ = 0;
    
    for (const d of data) {
      const dx = d[this.config.xField] - x;
      const dy = d[this.config.yField] - y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      
      if (dist < minDist) {
        minDist = dist;
        closestZ = d[this.config.zField];
      }
    }
    
    return closestZ;
  }
  
  private getColor(t: number): { r: number; g: number; b: number } {
    // Viridis color scheme approximation
    if (this.config.colorScheme === 'viridis') {
      const r = 0.267 + 0.005 * t + 2.817 * t * t - 5.765 * t * t * t + 2.676 * t * t * t * t;
      const g = 0.005 + 1.404 * t - 2.799 * t * t + 4.390 * t * t * t - 2.000 * t * t * t * t;
      const b = 0.329 + 1.074 * t - 0.734 * t * t + 0.331 * t * t * t;
      return { r: Math.max(0, Math.min(1, r)), g: Math.max(0, Math.min(1, g)), b: Math.max(0, Math.min(1, b)) };
    }
    
    // Rainbow fallback
    const hue = t * 360;
    return this.hslToRgb(hue, 1, 0.5);
  }
  
  private hslToRgb(h: number, s: number, l: number): { r: number; g: number; b: number } {
    h = h / 360;
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    
    const r = this.hue2rgb(p, q, h + 1/3);
    const g = this.hue2rgb(p, q, h);
    const b = this.hue2rgb(p, q, h - 1/3);
    
    return { r, g, b };
  }
  
  private hue2rgb(p: number, q: number, t: number): number {
    if (t < 0) t += 1;
    if (t > 1) t -= 1;
    if (t < 1/6) return p + (q - p) * 6 * t;
    if (t < 1/2) return q;
    if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
    return p;
  }
  
  private animate(): void {
    requestAnimationFrame(() => this.animate());
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
  
  public dispose(): void {
    this.renderer.dispose();
    this.controls.dispose();
    this.container.removeChild(this.renderer.domElement);
  }
}
```

### 2.2 3D Volume Renderer (S-Entropy Cube)

```typescript
export interface VolumeRendererConfig {
  container: string;
  width: number;
  height: number;
  resolution: [number, number, number];
  colorScheme?: string;
  threshold?: number;
  stepSize?: number;
  showSlices?: boolean;
}

export class VolumeRenderer {
  private container: HTMLElement;
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private controls: OrbitControls;
  private volumeTexture: THREE.Data3DTexture;
  private config: VolumeRendererConfig;
  
  constructor(config: VolumeRendererConfig) {
    this.config = { ...this.defaultConfig(), ...config };
    this.container = document.getElementById(config.container);
    this.initialize();
  }
  
  private defaultConfig(): Partial<VolumeRendererConfig> {
    return {
      resolution: [64, 64, 64],
      colorScheme: 'viridis',
      threshold: 0.5,
      stepSize: 0.01,
      showSlices: false
    };
  }
  
  private initialize(): void {
    // Scene setup (similar to Surface3D)
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x000000);
    
    this.camera = new THREE.PerspectiveCamera(
      60,
      this.config.width / this.config.height,
      0.1,
      100
    );
    this.camera.position.set(2, 2, 2);
    
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setSize(this.config.width, this.config.height);
    this.container.appendChild(this.renderer.domElement);
    
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    
    this.animate();
  }
  
  public render(volumeData: Float32Array): void {
    const [nx, ny, nz] = this.config.resolution;
    
    // Create 3D texture
    this.volumeTexture = new THREE.Data3DTexture(volumeData, nx, ny, nz);
    this.volumeTexture.format = THREE.RedFormat;
    this.volumeTexture.type = THREE.FloatType;
    this.volumeTexture.minFilter = THREE.LinearFilter;
    this.volumeTexture.magFilter = THREE.LinearFilter;
    this.volumeTexture.unpackAlignment = 1;
    this.volumeTexture.needsUpdate = true;
    
    // Create volume rendering shader
    const geometry = new THREE.BoxGeometry(1, 1, 1);
    const material = new THREE.ShaderMaterial({
      uniforms: {
        u_volume: { value: this.volumeTexture },
        u_threshold: { value: this.config.threshold },
        u_step_size: { value: this.config.stepSize },
        u_camera_pos: { value: this.camera.position }
      },
      vertexShader: this.getVertexShader(),
      fragmentShader: this.getFragmentShader(),
      side: THREE.BackSide,
      transparent: true
    });
    
    const mesh = new THREE.Mesh(geometry, material);
    this.scene.add(mesh);
  }
  
  private getVertexShader(): string {
    return `
      varying vec3 vPosition;
      varying vec3 vNormal;
      
      void main() {
        vPosition = position;
        vNormal = normalize(normalMatrix * normal);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `;
  }
  
  private getFragmentShader(): string {
    return `
      uniform sampler3D u_volume;
      uniform float u_threshold;
      uniform float u_step_size;
      uniform vec3 u_camera_pos;
      
      varying vec3 vPosition;
      varying vec3 vNormal;
      
      // Viridis color map
      vec3 viridis(float t) {
        const vec3 c0 = vec3(0.267, 0.005, 0.329);
        const vec3 c1 = vec3(0.283, 0.141, 0.458);
        const vec3 c2 = vec3(0.254, 0.265, 0.530);
        const vec3 c3 = vec3(0.207, 0.372, 0.553);
        const vec3 c4 = vec3(0.164, 0.471, 0.558);
        const vec3 c5 = vec3(0.128, 0.567, 0.551);
        const vec3 c6 = vec3(0.135, 0.659, 0.518);
        const vec3 c7 = vec3(0.267, 0.749, 0.441);
        const vec3 c8 = vec3(0.478, 0.821, 0.318);
        const vec3 c9 = vec3(0.741, 0.873, 0.150);
        const vec3 c10 = vec3(0.993, 0.906, 0.144);
        
        if (t < 0.1) return mix(c0, c1, t * 10.0);
        if (t < 0.2) return mix(c1, c2, (t - 0.1) * 10.0);
        if (t < 0.3) return mix(c2, c3, (t - 0.2) * 10.0);
        if (t < 0.4) return mix(c3, c4, (t - 0.3) * 10.0);
        if (t < 0.5) return mix(c4, c5, (t - 0.4) * 10.0);
        if (t < 0.6) return mix(c5, c6, (t - 0.5) * 10.0);
        if (t < 0.7) return mix(c6, c7, (t - 0.6) * 10.0);
        if (t < 0.8) return mix(c7, c8, (t - 0.7) * 10.0);
        if (t < 0.9) return mix(c8, c9, (t - 0.8) * 10.0);
        return mix(c9, c10, (t - 0.9) * 10.0);
      }
      
      void main() {
        // Ray marching
        vec3 ray_dir = normalize(vPosition - u_camera_pos);
        vec3 ray_pos = vPosition;
        
        vec4 color = vec4(0.0);
        
        for (int i = 0; i < 256; i++) {
          // Sample volume
          vec3 tex_coord = (ray_pos + 1.0) * 0.5;
          float density = texture(u_volume, tex_coord).r;
          
          if (density > u_threshold) {
            vec3 sample_color = viridis(density);
            float alpha = (density - u_threshold) / (1.0 - u_threshold);
            
            // Accumulate color
            color.rgb += (1.0 - color.a) * sample_color * alpha * 0.1;
            color.a += (1.0 - color.a) * alpha * 0.1;
          }
          
          // Early termination
          if (color.a > 0.99) break;
          
          // Step forward
          ray_pos += ray_dir * u_step_size;
          
          // Exit if outside cube
          if (any(lessThan(ray_pos, vec3(-1.0))) || any(greaterThan(ray_pos, vec3(1.0)))) {
            break;
          }
        }
        
        gl_FragColor = color;
      }
    `;
  }
  
  private animate(): void {
    requestAnimationFrame(() => this.animate());
    this.controls.update();
    
    // Update camera position uniform
    if (this.scene.children.length > 0) {
      const mesh = this.scene.children[0] as THREE.Mesh;
      const material = mesh.material as THREE.ShaderMaterial;
      material.uniforms.u_camera_pos.value = this.camera.position;
    }
    
    this.renderer.render(this.scene, this.camera);
  }
  
  public dispose(): void {
    this.renderer.dispose();
    this.controls.dispose();
    this.container.removeChild(this.renderer.domElement);
  }
}
```

---

## Complete Chart Gallery

Due to length constraints, I'll provide a comprehensive list of all chart types with brief descriptions:

### 2D Charts (35 types)

1. **LineChart** - Time series, trajectories
2. **AreaChart** - Stacked concentrations
3. **BarChart** - Discrete comparisons
4. **ScatterPlot** - Correlation analysis
5. **HistogramChart** - Distribution analysis
6. **BoxPlot** - Statistical summaries
7. **ViolinPlot** - Distribution + density
8. **HeatmapChart** - Expression matrices
9. **CircularPlot** - Phase coherence
10. **RadarChart** - Multi-dimensional comparison
11. **SankeyDiagram** - Metabolic flux
12. **ChordDiagram** - Interaction networks
13. **TreemapChart** - Hierarchical partition
14. **SunburstChart** - Recursive decomposition
15. **VoronoiDiagram** - Spatial tessellation
16. **StreamGraph** - Temporal evolution
17. **ForceDirectedGraph** - Circuit topology
18. **HierarchicalGraph** - Pathway hierarchy
19. **ArcDiagram** - Linear network
20. **MatrixView** - Adjacency matrix
21. **ParallelCoordinates** - Multi-dimensional data
22. **DendrogramChart** - Hierarchical clustering
23. **ContourPlot** - 2D level sets
24. **RidgePlot** - Distribution comparison
25. **BeeswarmPlot** - Categorical scatter
26. **BulletChart** - Performance metrics
27. **GaugeChart** - Single value display
28. **WaterfallChart** - Cumulative effects
29. **FunnelChart** - Process stages
30. **PieChart** - Proportions
31. **DonutChart** - Proportions with center
32. **PolarAreaChart** - Circular bar chart
33. **CalendarHeatmap** - Temporal patterns
34. **CorrelationMatrix** - Pairwise correlations
35. **UpSetPlot** - Set intersections

### 3D Charts (20 types)

1. **Surface3D** - S-entropy landscape
2. **Scatter3D** - 3D point clouds
3. **Line3D** - 3D trajectories
4. **Bar3D** - 3D histograms
5. **Mesh3D** - Isosurfaces
6. **VolumeRenderer** - Ray marching
7. **SliceViewer** - Orthogonal slices
8. **IsocontourPlot** - Level sets
9. **VectorField3D** - Gradient flows
10. **MolecularViewer** - Protein structures
11. **BallAndStick** - Atomic models
12. **RibbonDiagram** - Protein backbone
13. **SurfaceModel** - Molecular surfaces
14. **PartitionCube** - S-entropy volume
15. **PhaseSpace3D** - Dynamical systems
16. **NetworkGraph3D** - 3D force layout
17. **TensorField** - Multi-dimensional data
18. **Streamlines3D** - Flow visualization
19. **Glyphs3D** - Multi-variate markers
20. **PointCloud** - Dense 3D data

---

## Usage Examples

### Example 1: Glycolysis Dashboard

```typescript
import { LineChart, CircularPlot, HeatmapChart, Surface3D } from 'partition-bio-charts';

// Time series of concentrations
const lineChart = new LineChart('#timeseries', {
  width: 800,
  height: 400,
  xField: 'time',
  yFields: ['Glucose', 'ATP', 'Pyruvate'],
  xLabel: 'Time (s)',
  yLabel: 'Concentration (mM)',
  interpolation: 'monotone',
  showPoints: true
});

lineChart.render(timeseriesData);

// Phase coherence
const phaseChart = new CircularPlot('#phase-plot', {
  width: 400,
  height: 400,
  phaseField: 'phase',
  amplitudeField: 'amplitude',
  labelField: 'species',
  showOrderParameter: true
});

phaseChart.render(phaseData);

// Expression heatmap
const heatmap = new HeatmapChart('#heatmap', {
  width: 600,
  height: 600,
  rowField: 'gene',
  colField: 'condition',
  valueField: 'expression',
  colorScheme: 'RdYlBu',
  showValues: false,
  dendrogramRow: true,
  dendrogramCol: true
});

heatmap.render(expressionData);

// S-entropy landscape
const surface = new Surface3D({
  container: 's-entropy-3d',
  width: 800,
  height: 600,
  xField: 'S_k',
  yField: 'S_t',
  zField: 'S_e',
  resolution: 100,
  colorScheme: 'viridis',
  wireframe: false
});

surface.render(sentropyData);
```

### Example 2: Real-Time Updates

```typescript
// Set up real-time data stream
const ws = new WebSocket('ws://localhost
