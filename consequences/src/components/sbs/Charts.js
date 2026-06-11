import React, { useRef, useEffect } from "react";

function getD3() {
  try { return require("d3"); } catch { return null; }
}

function clearSvg(ref) {
  if (!ref.current) return null;
  const d3 = getD3();
  if (!d3) return null;
  const svg = d3.select(ref.current);
  svg.selectAll("*").remove();
  return { d3, svg };
}

const AXIS_COLOR = "#888";
const GRID_COLOR = "#333";
const DOMAIN_COLOR = "#333";
const LABEL_SIZE = "10px";
const TICK_SIZE = "9px";

function axisStyle(g) {
  g.selectAll("text").style("fill", AXIS_COLOR).style("font-size", TICK_SIZE);
  g.selectAll("line").style("stroke", GRID_COLOR);
  g.selectAll("path.domain").style("stroke", DOMAIN_COLOR);
}

/* ─── 1. S-entropy Scatter (Se vs Sk, color=St) ─── */
function ScatterChart({ metrics, circuit }) {
  const ref = useRef(null);
  useEffect(() => {
    const r = clearSvg({ current: ref.current });
    if (!r || !metrics) return;
    const { d3, svg } = r;
    const margin = { top: 20, right: 20, bottom: 40, left: 50 };
    const w = 300 - margin.left - margin.right, h = 200 - margin.top - margin.bottom;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
    const x = d3.scaleLinear().domain([0, 1]).range([0, w]);
    const y = d3.scaleLinear().domain([0, 1]).range([h, 0]);
    const color = d3.scaleSequential(d3.interpolateViridis).domain([0, 1]);
    axisStyle(g.append("g").attr("transform", `translate(0,${h})`).call(d3.axisBottom(x).ticks(5)));
    axisStyle(g.append("g").call(d3.axisLeft(y).ticks(5)));
    g.append("text").attr("x", w / 2).attr("y", h + 35).style("fill", AXIS_COLOR).style("font-size", LABEL_SIZE).style("text-anchor", "middle").text("Se");
    g.append("text").attr("transform", "rotate(-90)").attr("x", -h / 2).attr("y", -38).style("fill", AXIS_COLOR).style("font-size", LABEL_SIZE).style("text-anchor", "middle").text("Sk");
    const names = circuit?.nodes?.map(n => n.name) || [];
    (metrics.Se || []).forEach((se, i) => {
      g.append("circle").attr("cx", x(se)).attr("cy", y(metrics.Sk?.[i] || 0)).attr("r", 5)
        .attr("fill", color(metrics.St?.[i] || 0)).attr("stroke", "#fff").attr("stroke-width", 0.5).attr("opacity", 0.9)
        .append("title").text(`${names[i] || i}: Se=${se.toFixed(3)}, Sk=${(metrics.Sk?.[i] || 0).toFixed(3)}, St=${(metrics.St?.[i] || 0).toFixed(3)}`);
    });
  }, [metrics, circuit]);
  return <svg ref={ref} width={300} height={200} />;
}

/* ─── 2. Flux Comparison Bar ─── */
function FluxBarChart({ metrics, circuit }) {
  const ref = useRef(null);
  useEffect(() => {
    const r = clearSvg({ current: ref.current });
    if (!r || !metrics) return;
    const { d3, svg } = r;
    const margin = { top: 16, right: 16, bottom: 50, left: 48 };
    const w = 340 - margin.left - margin.right, h = 180 - margin.top - margin.bottom;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
    const healthy = metrics.fluxHealthy || [], current = metrics.fluxCurrent || [];
    const edgeNames = circuit?.edges?.map(e => e.name.length > 8 ? e.name.slice(0, 8) : e.name) || [];
    if (healthy.length === 0) return;
    const maxFlux = Math.max(1e-10, ...healthy, ...current);
    const x = d3.scaleBand().domain(edgeNames).range([0, w]).padding(0.2);
    const y = d3.scaleLog().domain([Math.max(1e-6, maxFlux * 1e-6), maxFlux * 1.2]).range([h, 0]).clamp(true);
    axisStyle(g.append("g").attr("transform", `translate(0,${h})`).call(d3.axisBottom(x)).selectAll("text").attr("transform", "rotate(-40)").style("text-anchor", "end"));
    axisStyle(g.append("g").call(d3.axisLeft(y).ticks(3, ".0e")));
    const bw = x.bandwidth() / 2;
    healthy.forEach((hv, i) => {
      const name = edgeNames[i] || `e${i}`;
      g.append("rect").attr("x", x(name)).attr("y", y(Math.max(1e-10, hv))).attr("width", bw).attr("height", h - y(Math.max(1e-10, hv))).attr("fill", "#4a9eff").attr("opacity", 0.7);
      const cv = current[i] || 0;
      g.append("rect").attr("x", x(name) + bw).attr("y", y(Math.max(1e-10, cv))).attr("width", bw).attr("height", h - y(Math.max(1e-10, cv))).attr("fill", "#ff6b6b").attr("opacity", 0.7);
    });
    g.append("rect").attr("x", w - 80).attr("y", 0).attr("width", 8).attr("height", 8).attr("fill", "#4a9eff");
    g.append("text").attr("x", w - 68).attr("y", 8).style("fill", "#888").style("font-size", "9px").text("Healthy");
    g.append("rect").attr("x", w - 80).attr("y", 14).attr("width", 8).attr("height", 8).attr("fill", "#ff6b6b");
    g.append("text").attr("x", w - 68).attr("y", 22).style("fill", "#888").style("font-size", "9px").text("Perturbed");
  }, [metrics, circuit]);
  return <svg ref={ref} width={340} height={180} />;
}

/* ─── 3. Phase Coherence Circular Plot ─── */
function PhaseCoherence({ metrics, circuit }) {
  const ref = useRef(null);
  useEffect(() => {
    const r = clearSvg({ current: ref.current });
    if (!r || !metrics || !circuit) return;
    const { d3, svg } = r;
    const size = 260, cx = size / 2, cy = size / 2, radius = size / 2 - 40;
    const g = svg.append("g").attr("transform", `translate(${cx},${cy})`);
    const Se = metrics.Se || [], Sk = metrics.Sk || [], names = circuit.nodes?.map(n => n.name) || [];
    const n = Se.length;
    if (n === 0) return;
    for (let i = 1; i <= 4; i++) {
      const rad = (radius / 4) * i;
      g.append("circle").attr("r", rad).attr("fill", "none").attr("stroke", "#2a2a4a");
    }
    for (let a = 0; a < 360; a += 45) {
      const rad = (a * Math.PI) / 180;
      g.append("line").attr("x1", 0).attr("y1", 0).attr("x2", radius * Math.cos(rad - Math.PI / 2)).attr("y2", radius * Math.sin(rad - Math.PI / 2)).attr("stroke", "#2a2a4a");
    }
    const color = d3.scaleOrdinal(d3.schemeTableau10);
    let sumX = 0, sumY = 0;
    Se.forEach((se, i) => {
      const phase = se * 2 * Math.PI, amp = Math.max(0.1, Sk[i] || 0.5);
      const px = radius * amp * Math.cos(phase - Math.PI / 2), py = radius * amp * Math.sin(phase - Math.PI / 2);
      g.append("line").attr("x1", 0).attr("y1", 0).attr("x2", px).attr("y2", py).attr("stroke", color(i)).attr("stroke-width", 1.5).attr("opacity", 0.7);
      g.append("circle").attr("cx", px).attr("cy", py).attr("r", 4).attr("fill", color(i));
      g.append("text").attr("x", px * 1.2).attr("y", py * 1.2).attr("text-anchor", "middle").style("fill", "#888").style("font-size", "8px").text(names[i]?.slice(0, 6) || "");
      sumX += Math.cos(phase); sumY += Math.sin(phase);
    });
    const rVal = Math.sqrt(sumX * sumX + sumY * sumY) / n;
    const avgPh = Math.atan2(sumY, sumX);
    g.append("line").attr("x1", 0).attr("y1", 0).attr("x2", radius * rVal * Math.cos(avgPh - Math.PI / 2)).attr("y2", radius * rVal * Math.sin(avgPh - Math.PI / 2))
      .attr("stroke", "#ff4444").attr("stroke-width", 3);
    g.append("text").attr("x", 0).attr("y", -radius - 14).attr("text-anchor", "middle").style("fill", "#ccc").style("font-size", "11px").style("font-weight", "bold").text(`r = ${rVal.toFixed(3)}`);
  }, [metrics, circuit]);
  return <svg ref={ref} width={260} height={260} />;
}

/* ─── 4. Coupling Heatmap ─── */
function CouplingHeatmap({ circuit }) {
  const ref = useRef(null);
  useEffect(() => {
    const r = clearSvg({ current: ref.current });
    if (!r || !circuit) return;
    const { d3, svg } = r;
    const nodes = circuit.nodes || [], edges = circuit.edges || [], n = nodes.length;
    if (n === 0) return;
    const margin = { top: 55, right: 30, bottom: 10, left: 65 };
    const cellSize = Math.min(22, (280 - margin.left - margin.right) / n);
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
    const matrix = Array.from({ length: n }, () => Array(n).fill(0));
    edges.forEach(e => { matrix[e.src][e.dst] = e.conductance; matrix[e.dst][e.src] = e.conductance * 0.3; });
    const maxVal = Math.max(1e-10, ...matrix.flat());
    const color = d3.scaleSequential(d3.interpolatePlasma).domain([0, maxVal]);
    const names = nodes.map(nd => nd.name.length > 6 ? nd.name.slice(0, 5) + "…" : nd.name);
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
      g.append("rect").attr("x", j * cellSize).attr("y", i * cellSize).attr("width", cellSize - 1).attr("height", cellSize - 1)
        .attr("fill", matrix[i][j] > 0 ? color(matrix[i][j]) : "#0a0a14").attr("rx", 1)
        .append("title").text(`${nodes[i].name} → ${nodes[j].name}: ${matrix[i][j].toFixed(2)}`);
    }
    names.forEach((nm, i) => {
      g.append("text").attr("x", -4).attr("y", i * cellSize + cellSize / 2).attr("text-anchor", "end").attr("dominant-baseline", "middle").style("fill", "#888").style("font-size", "8px").text(nm);
      g.append("text").attr("x", i * cellSize + cellSize / 2).attr("y", -4).attr("text-anchor", "end").attr("transform", `rotate(-45, ${i * cellSize + cellSize / 2}, -4)`).style("fill", "#888").style("font-size", "8px").text(nm);
    });
  }, [circuit]);
  return <svg ref={ref} width={320} height={300} />;
}

/* ─── 5. S-entropy 3D Landscape (isometric canvas) ─── */
function SEntropyLandscape({ metrics, circuit }) {
  const ref = useRef(null);
  useEffect(() => {
    if (!metrics || !ref.current || !circuit) return;
    const canvas = ref.current, ctx = canvas.getContext("2d");
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const Se = metrics.Se || [], Sk = metrics.Sk || [], St = metrics.St || [];
    const names = circuit.nodes?.map(n => n.name) || [];
    if (Se.length === 0) return;
    const scale = Math.min(w, h) * 0.32, ox = w / 2, oy = h / 2 + 20;
    const iX = (se, sk) => ox + scale * (se - sk) * Math.cos(Math.PI / 6);
    const iY = (se, sk, st) => oy - scale * st * 0.8 + scale * (se + sk) * Math.sin(Math.PI / 6) * 0.5;
    ctx.strokeStyle = "#3a3a5a"; ctx.lineWidth = 1; ctx.setLineDash([3, 3]);
    [[1, 0, 0, "Se"], [0, 1, 0, "Sk"], [0, 0, 1, "St"]].forEach(([se, sk, st, lbl]) => {
      ctx.beginPath(); ctx.moveTo(iX(0, 0), iY(0, 0, 0)); ctx.lineTo(iX(se, sk), iY(se, sk, st)); ctx.stroke();
      ctx.fillStyle = "#888"; ctx.font = "9px monospace"; ctx.fillText(lbl, iX(se * 1.08, sk * 1.08), iY(se * 1.08, sk * 1.08, st * 1.08));
    });
    ctx.setLineDash([]); ctx.strokeStyle = "#1a1a3e"; ctx.lineWidth = 0.5;
    for (let i = 0; i <= 4; i++) { const t = i / 4; ctx.beginPath(); ctx.moveTo(iX(t, 0), iY(t, 0, 0)); ctx.lineTo(iX(t, 1), iY(t, 1, 0)); ctx.stroke(); ctx.beginPath(); ctx.moveTo(iX(0, t), iY(0, t, 0)); ctx.lineTo(iX(1, t), iY(1, t, 0)); ctx.stroke(); }
    ctx.setLineDash([2, 2]); ctx.strokeStyle = "#2a2a4a";
    Se.forEach((se, i) => { ctx.beginPath(); ctx.moveTo(iX(se, Sk[i] || 0), iY(se, Sk[i] || 0, St[i] || 0)); ctx.lineTo(iX(se, Sk[i] || 0), iY(se, Sk[i] || 0, 0)); ctx.stroke(); });
    ctx.setLineDash([]);
    const viridis = (t) => { const r = Math.round(255 * Math.max(0, Math.min(1, 0.267 + 2.82 * t * t - 5.77 * t ** 3 + 2.68 * t ** 4))); const g = Math.round(255 * Math.max(0, Math.min(1, 0.005 + 1.4 * t - 2.8 * t * t + 4.4 * t ** 3 - 2 * t ** 4))); const b = Math.round(255 * Math.max(0, Math.min(1, 0.329 + 1.07 * t - 0.73 * t * t + 0.33 * t ** 3))); return `rgb(${r},${g},${b})`; };
    const sorted = Se.map((se, i) => ({ se, sk: Sk[i] || 0, st: St[i] || 0, name: names[i] || "", i })).sort((a, b) => (a.se + a.sk) - (b.se + b.sk));
    sorted.forEach(({ se, sk, st, name }) => {
      const px = iX(se, sk), py = iY(se, sk, st);
      ctx.beginPath(); ctx.arc(px, py, 5, 0, 2 * Math.PI); ctx.fillStyle = viridis(st); ctx.fill(); ctx.strokeStyle = "#fff"; ctx.lineWidth = 0.6; ctx.stroke();
      ctx.fillStyle = "#aaa"; ctx.font = "8px monospace"; ctx.textAlign = "center"; ctx.fillText(name.slice(0, 7), px, py - 8);
    });
  }, [metrics, circuit]);
  return <canvas ref={ref} width={340} height={240} style={{ background: "#0a0a14", borderRadius: 4 }} />;
}

/* ─── 6. Radar Chart (per-node Se,Sk,St,mu_norm,conc_norm) ─── */
function RadarChart({ metrics, circuit }) {
  const ref = useRef(null);
  useEffect(() => {
    const r = clearSvg({ current: ref.current });
    if (!r || !metrics || !circuit) return;
    const { d3, svg } = r;
    const size = 260, cx = size / 2, cy = size / 2, radius = size / 2 - 40;
    const g = svg.append("g").attr("transform", `translate(${cx},${cy})`);
    const axes = ["Se", "Sk", "St", "mu_norm", "conc_norm"];
    const angleSlice = (2 * Math.PI) / axes.length;
    // Grid
    for (let i = 1; i <= 4; i++) {
      const pts = axes.map((_, j) => {
        const a = angleSlice * j - Math.PI / 2;
        const rad = (radius / 4) * i;
        return [rad * Math.cos(a), rad * Math.sin(a)];
      });
      g.append("polygon").attr("points", pts.map(p => p.join(",")).join(" ")).attr("fill", "none").attr("stroke", "#2a2a4a").attr("stroke-width", 0.5);
    }
    axes.forEach((ax, j) => {
      const a = angleSlice * j - Math.PI / 2;
      g.append("line").attr("x1", 0).attr("y1", 0).attr("x2", radius * Math.cos(a)).attr("y2", radius * Math.sin(a)).attr("stroke", "#2a2a4a");
      g.append("text").attr("x", (radius + 12) * Math.cos(a)).attr("y", (radius + 12) * Math.sin(a)).attr("text-anchor", "middle").attr("dominant-baseline", "middle").style("fill", "#888").style("font-size", "8px").text(ax);
    });
    const Se = metrics.Se || [], Sk = metrics.Sk || [], St = metrics.St || [];
    const nodes = circuit.nodes || [];
    const muMax = Math.max(1, ...nodes.map(n => Math.abs(n.mu)));
    const concMax = Math.max(1e-10, ...nodes.map(n => n.concentration));
    const color = d3.scaleOrdinal(d3.schemeTableau10);
    const maxNodes = Math.min(nodes.length, 8);
    for (let i = 0; i < maxNodes; i++) {
      const vals = [Se[i] || 0, Sk[i] || 0, St[i] || 0, Math.abs(nodes[i].mu) / muMax, nodes[i].concentration / concMax];
      const pts = vals.map((v, j) => {
        const a = angleSlice * j - Math.PI / 2;
        return [radius * v * Math.cos(a), radius * v * Math.sin(a)];
      });
      g.append("polygon").attr("points", pts.map(p => p.join(",")).join(" ")).attr("fill", color(i)).attr("fill-opacity", 0.08).attr("stroke", color(i)).attr("stroke-width", 1.5).attr("stroke-opacity", 0.7);
      pts.forEach(([px, py]) => g.append("circle").attr("cx", px).attr("cy", py).attr("r", 2.5).attr("fill", color(i)));
    }
    // Legend
    for (let i = 0; i < maxNodes; i++) {
      g.append("rect").attr("x", -radius).attr("y", radius + 6 + i * 12).attr("width", 8).attr("height", 8).attr("fill", color(i));
      g.append("text").attr("x", -radius + 12).attr("y", radius + 13 + i * 12).style("fill", "#888").style("font-size", "8px").text(nodes[i].name.slice(0, 10));
    }
  }, [metrics, circuit]);
  return <svg ref={ref} width={260} height={360} />;
}

/* ─── 7. Sankey / Flow Diagram ─── */
function SankeyFlow({ metrics, circuit }) {
  const ref = useRef(null);
  useEffect(() => {
    const r = clearSvg({ current: ref.current });
    if (!r || !circuit) return;
    const { d3, svg } = r;
    const margin = { top: 16, right: 16, bottom: 16, left: 16 };
    const w = 400 - margin.left - margin.right, h = 200 - margin.top - margin.bottom;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
    const nodes = circuit.nodes || [], edges = circuit.edges || [];
    if (nodes.length === 0) return;
    // Assign x positions based on topological order (simple: index)
    const nodeX = {}, nodeY = {};
    const layers = [];
    const visited = new Set();
    let queue = nodes.filter((_, i) => !edges.some(e => e.dst === i)).map((_, i) => i);
    if (queue.length === 0) queue = [0];
    let layer = 0;
    while (queue.length > 0 && layer < 20) {
      layers.push([...queue]);
      const next = new Set();
      queue.forEach(ni => { visited.add(ni); edges.filter(e => e.src === ni).forEach(e => { if (!visited.has(e.dst)) next.add(e.dst); }); });
      queue = [...next];
      layer++;
    }
    // Place remaining
    nodes.forEach((_, i) => { if (!visited.has(i)) { layers.push([i]); visited.add(i); } });
    const nLayers = layers.length;
    const layerW = w / Math.max(1, nLayers);
    layers.forEach((layer, li) => {
      const layerH = h / Math.max(1, layer.length);
      layer.forEach((ni, yi) => {
        nodeX[ni] = li * layerW + layerW / 2;
        nodeY[ni] = yi * layerH + layerH / 2;
      });
    });
    const fluxCurrent = metrics?.fluxCurrent || [];
    const maxFlux = Math.max(1e-10, ...fluxCurrent, ...edges.map(e => e.conductance));
    const color = d3.scaleSequential(d3.interpolateViridis).domain([0, 1]);
    // Edges as curved links
    edges.forEach((e, ei) => {
      const x1 = nodeX[e.src] || 0, y1 = nodeY[e.src] || 0;
      const x2 = nodeX[e.dst] || 0, y2 = nodeY[e.dst] || 0;
      const flux = fluxCurrent[ei] || e.conductance;
      const thick = Math.max(1, 8 * flux / maxFlux);
      const path = d3.line().curve(d3.curveBasis)([[x1, y1], [(x1 + x2) / 2, y1], [(x1 + x2) / 2, y2], [x2, y2]]);
      g.append("path").attr("d", path).attr("fill", "none").attr("stroke", color(flux / maxFlux)).attr("stroke-width", thick).attr("opacity", 0.5);
    });
    // Nodes
    const Se = metrics?.Se || [];
    nodes.forEach((n, i) => {
      g.append("circle").attr("cx", nodeX[i] || 0).attr("cy", nodeY[i] || 0).attr("r", 8)
        .attr("fill", color(Se[i] || 0)).attr("stroke", "#fff").attr("stroke-width", 1);
      g.append("text").attr("x", nodeX[i] || 0).attr("y", (nodeY[i] || 0) - 12).attr("text-anchor", "middle")
        .style("fill", "#aaa").style("font-size", "8px").text(n.name.slice(0, 8));
    });
  }, [metrics, circuit]);
  return <svg ref={ref} width={400} height={200} />;
}

/* ─── 8. Parallel Coordinates ─── */
function ParallelCoords({ metrics, circuit }) {
  const ref = useRef(null);
  useEffect(() => {
    const r = clearSvg({ current: ref.current });
    if (!r || !metrics || !circuit) return;
    const { d3, svg } = r;
    const margin = { top: 30, right: 16, bottom: 16, left: 16 };
    const w = 380 - margin.left - margin.right, h = 200 - margin.top - margin.bottom;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
    const dims = ["Se", "Sk", "St"];
    const nodes = circuit.nodes || [];
    const Se = metrics.Se || [], Sk = metrics.Sk || [], St = metrics.St || [];
    const n = Se.length;
    if (n === 0) return;
    const x = d3.scalePoint().domain(dims).range([0, w]).padding(0.2);
    const yScales = {};
    dims.forEach(d => { yScales[d] = d3.scaleLinear().domain([0, 1]).range([h, 0]); });
    // Axes
    dims.forEach(d => {
      const ax = g.append("g").attr("transform", `translate(${x(d)},0)`).call(d3.axisLeft(yScales[d]).ticks(4));
      axisStyle(ax);
      g.append("text").attr("x", x(d)).attr("y", -12).attr("text-anchor", "middle").style("fill", "#aaa").style("font-size", "10px").style("font-weight", "bold").text(d);
    });
    const color = d3.scaleOrdinal(d3.schemeTableau10);
    for (let i = 0; i < n; i++) {
      const vals = { Se: Se[i], Sk: Sk[i], St: St[i] };
      const line = d3.line().curve(d3.curveMonotoneX);
      const pts = dims.map(d => [x(d), yScales[d](vals[d] || 0)]);
      g.append("path").datum(pts).attr("d", line).attr("fill", "none").attr("stroke", color(i)).attr("stroke-width", 1.5).attr("opacity", 0.6);
      // Labels at end
      g.append("text").attr("x", x("St") + 8).attr("y", yScales["St"](St[i] || 0)).style("fill", color(i)).style("font-size", "8px").text(nodes[i]?.name?.slice(0, 6) || "");
    }
  }, [metrics, circuit]);
  return <svg ref={ref} width={380} height={200} />;
}

/* ─── 9. Waterfall Chart (cumulative deltaG along pathway) ─── */
function WaterfallChart({ circuit }) {
  const ref = useRef(null);
  useEffect(() => {
    const r = clearSvg({ current: ref.current });
    if (!r || !circuit) return;
    const { d3, svg } = r;
    const margin = { top: 20, right: 16, bottom: 50, left: 55 };
    const w = 380 - margin.left - margin.right, h = 180 - margin.top - margin.bottom;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
    const edges = circuit.edges || [];
    if (edges.length === 0) return;
    let cumulative = 0;
    const data = edges.map(e => {
      const start = cumulative;
      cumulative += e.deltaG;
      return { name: e.name.length > 8 ? e.name.slice(0, 8) : e.name, deltaG: e.deltaG, start, end: cumulative };
    });
    const x = d3.scaleBand().domain(data.map(d => d.name)).range([0, w]).padding(0.15);
    const extent = d3.extent(data.flatMap(d => [d.start, d.end]));
    const y = d3.scaleLinear().domain([extent[0] * 1.1, Math.max(0, extent[1] * 1.1)]).range([h, 0]);
    axisStyle(g.append("g").attr("transform", `translate(0,${h})`).call(d3.axisBottom(x)).selectAll("text").attr("transform", "rotate(-40)").style("text-anchor", "end"));
    axisStyle(g.append("g").call(d3.axisLeft(y).ticks(5)));
    g.append("text").attr("transform", "rotate(-90)").attr("x", -h / 2).attr("y", -42).style("fill", AXIS_COLOR).style("font-size", LABEL_SIZE).style("text-anchor", "middle").text("ΔG cumulative (kJ/mol)");
    // Zero line
    g.append("line").attr("x1", 0).attr("x2", w).attr("y1", y(0)).attr("y2", y(0)).attr("stroke", "#4a4a6a").attr("stroke-dasharray", "3,3");
    data.forEach(d => {
      const yTop = y(Math.max(d.start, d.end)), yBot = y(Math.min(d.start, d.end));
      g.append("rect").attr("x", x(d.name)).attr("y", yTop).attr("width", x.bandwidth()).attr("height", Math.max(1, yBot - yTop))
        .attr("fill", d.deltaG > 0 ? "#4ec9b0" : "#ff6b6b").attr("opacity", 0.8)
        .append("title").text(`${d.name}: ΔG = ${d.deltaG.toFixed(1)} kJ/mol`);
    });
    // Connector lines
    for (let i = 0; i < data.length - 1; i++) {
      g.append("line").attr("x1", x(data[i].name) + x.bandwidth()).attr("x2", x(data[i + 1].name))
        .attr("y1", y(data[i].end)).attr("y2", y(data[i].end)).attr("stroke", "#4a4a6a").attr("stroke-dasharray", "2,2");
    }
  }, [circuit]);
  return <svg ref={ref} width={380} height={180} />;
}

/* ─── 10. Donut Chart (compartment distribution) ─── */
function CompartmentDonut({ circuit }) {
  const ref = useRef(null);
  useEffect(() => {
    const r = clearSvg({ current: ref.current });
    if (!r || !circuit) return;
    const { d3, svg } = r;
    const size = 200, cx = size / 2, cy = size / 2;
    const g = svg.append("g").attr("transform", `translate(${cx},${cy})`);
    const nodes = circuit.nodes || [];
    const compCounts = {};
    nodes.forEach(n => { const c = n.compartment || "cytoplasm"; compCounts[c] = (compCounts[c] || 0) + 1; });
    const entries = Object.entries(compCounts).sort((a, b) => b[1] - a[1]);
    if (entries.length === 0) return;
    const pie = d3.pie().value(d => d[1]).sort(null);
    const arc = d3.arc().innerRadius(35).outerRadius(70);
    const color = d3.scaleOrdinal(d3.schemeSet2);
    const arcs = pie(entries);
    arcs.forEach((a, i) => {
      g.append("path").attr("d", arc(a)).attr("fill", color(i)).attr("stroke", "#0a0a14").attr("stroke-width", 2)
        .append("title").text(`${entries[i][0]}: ${entries[i][1]} nodes`);
    });
    // Center label
    g.append("text").attr("text-anchor", "middle").attr("dominant-baseline", "middle").style("fill", "#ccc").style("font-size", "14px").style("font-weight", "bold").text(nodes.length);
    g.append("text").attr("text-anchor", "middle").attr("y", 16).style("fill", "#888").style("font-size", "8px").text("nodes");
    // Legend
    entries.forEach(([comp, count], i) => {
      g.append("rect").attr("x", -cx + 4).attr("y", 80 + i * 14).attr("width", 8).attr("height", 8).attr("fill", color(i));
      g.append("text").attr("x", -cx + 16).attr("y", 88 + i * 14).style("fill", "#888").style("font-size", "9px").text(`${comp} (${count})`);
    });
  }, [circuit]);
  return <svg ref={ref} width={200} height={220} />;
}

/* ─── 11. Gauge Charts (R and V) ─── */
function GaugeChart({ value, label, good }) {
  const ref = useRef(null);
  useEffect(() => {
    const r = clearSvg({ current: ref.current });
    if (!r || value == null) return;
    const { d3, svg } = r;
    const cx = 80, cy = 70, radius = 55;
    const g = svg.append("g").attr("transform", `translate(${cx},${cy})`);
    // Background arc
    const bgArc = d3.arc().innerRadius(radius - 12).outerRadius(radius).startAngle(-Math.PI * 0.75).endAngle(Math.PI * 0.75);
    g.append("path").attr("d", bgArc()).attr("fill", "#1a1a3e");
    // Value arc
    const valAngle = -Math.PI * 0.75 + Math.min(1, Math.max(0, value)) * Math.PI * 1.5;
    const valArc = d3.arc().innerRadius(radius - 12).outerRadius(radius).startAngle(-Math.PI * 0.75).endAngle(valAngle);
    const color = good ? "#4ec9b0" : "#ff6b6b";
    g.append("path").attr("d", valArc()).attr("fill", color);
    // Needle
    const needleAngle = valAngle - Math.PI / 2;
    g.append("line").attr("x1", 0).attr("y1", 0).attr("x2", (radius - 18) * Math.cos(needleAngle)).attr("y2", (radius - 18) * Math.sin(needleAngle))
      .attr("stroke", "#fff").attr("stroke-width", 2);
    g.append("circle").attr("r", 3).attr("fill", "#fff");
    // Value text
    g.append("text").attr("y", 18).attr("text-anchor", "middle").style("fill", color).style("font-size", "16px").style("font-weight", "bold").text(value.toFixed(3));
    g.append("text").attr("y", 32).attr("text-anchor", "middle").style("fill", "#888").style("font-size", "9px").text(label);
  }, [value, label, good]);
  return <svg ref={ref} width={160} height={110} />;
}

/* ─── 12. Correlation Matrix (Se,Sk,St pairwise) ─── */
function CorrelationMatrix({ metrics }) {
  const ref = useRef(null);
  useEffect(() => {
    const r = clearSvg({ current: ref.current });
    if (!r || !metrics) return;
    const { d3, svg } = r;
    const Se = metrics.Se || [], Sk = metrics.Sk || [], St = metrics.St || [];
    const n = Se.length;
    if (n < 2) return;
    const vars = [Se, Sk, St];
    const labels = ["Se", "Sk", "St"];
    // Compute Pearson correlations
    const corr = (a, b) => {
      const mA = a.reduce((s, v) => s + v, 0) / a.length, mB = b.reduce((s, v) => s + v, 0) / b.length;
      let num = 0, dA = 0, dB = 0;
      for (let i = 0; i < a.length; i++) { num += (a[i] - mA) * (b[i] - mB); dA += (a[i] - mA) ** 2; dB += (b[i] - mB) ** 2; }
      return dA && dB ? num / Math.sqrt(dA * dB) : 0;
    };
    const matrix = labels.map((_, i) => labels.map((_, j) => corr(vars[i], vars[j])));
    const margin = { top: 40, right: 10, bottom: 10, left: 40 };
    const cellSize = 50;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
    const color = d3.scaleSequential(d3.interpolateRdYlGn).domain([-1, 1]);
    matrix.forEach((row, i) => row.forEach((v, j) => {
      g.append("rect").attr("x", j * cellSize).attr("y", i * cellSize).attr("width", cellSize - 2).attr("height", cellSize - 2).attr("fill", color(v)).attr("rx", 3);
      g.append("text").attr("x", j * cellSize + cellSize / 2 - 1).attr("y", i * cellSize + cellSize / 2).attr("text-anchor", "middle").attr("dominant-baseline", "middle")
        .style("fill", Math.abs(v) > 0.5 ? "#fff" : "#000").style("font-size", "11px").style("font-weight", "bold").text(v.toFixed(2));
    }));
    labels.forEach((lbl, i) => {
      g.append("text").attr("x", i * cellSize + cellSize / 2 - 1).attr("y", -8).attr("text-anchor", "middle").style("fill", "#aaa").style("font-size", "10px").text(lbl);
      g.append("text").attr("x", -8).attr("y", i * cellSize + cellSize / 2).attr("text-anchor", "end").attr("dominant-baseline", "middle").style("fill", "#aaa").style("font-size", "10px").text(lbl);
    });
  }, [metrics]);
  return <svg ref={ref} width={210} height={210} />;
}

/* ─── 13. Ridge / Distribution Plot (Se, Sk, St histograms) ─── */
function RidgePlot({ metrics }) {
  const ref = useRef(null);
  useEffect(() => {
    const r = clearSvg({ current: ref.current });
    if (!r || !metrics) return;
    const { d3, svg } = r;
    const margin = { top: 16, right: 16, bottom: 30, left: 40 };
    const w = 280 - margin.left - margin.right, h = 180 - margin.top - margin.bottom;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
    const data = [
      { label: "Se", values: metrics.Se || [], color: "#ff6b6b" },
      { label: "Sk", values: metrics.Sk || [], color: "#4ec9b0" },
      { label: "St", values: metrics.St || [], color: "#dcdcaa" },
    ].filter(d => d.values.length > 0);
    if (data.length === 0) return;
    const x = d3.scaleLinear().domain([0, 1]).range([0, w]);
    const rowH = h / data.length;
    axisStyle(g.append("g").attr("transform", `translate(0,${h})`).call(d3.axisBottom(x).ticks(5)));
    data.forEach((d, ri) => {
      const bins = d3.bin().domain([0, 1]).thresholds(15)(d.values);
      const maxCount = Math.max(1, ...bins.map(b => b.length));
      const yScale = d3.scaleLinear().domain([0, maxCount]).range([rowH - 2, 0]);
      const area = d3.area().curve(d3.curveBasis).x(b => x((b.x0 + b.x1) / 2)).y0(rowH - 2).y1(b => yScale(b.length));
      const rg = g.append("g").attr("transform", `translate(0,${ri * rowH})`);
      rg.append("path").datum(bins).attr("d", area).attr("fill", d.color).attr("fill-opacity", 0.3).attr("stroke", d.color).attr("stroke-width", 1.5);
      rg.append("text").attr("x", -6).attr("y", rowH / 2).attr("text-anchor", "end").attr("dominant-baseline", "middle").style("fill", d.color).style("font-size", "10px").style("font-weight", "bold").text(d.label);
    });
  }, [metrics]);
  return <svg ref={ref} width={280} height={180} />;
}

/* ─── 14. Arc Diagram (linear circuit topology) ─── */
function ArcDiagram({ circuit }) {
  const ref = useRef(null);
  useEffect(() => {
    const r = clearSvg({ current: ref.current });
    if (!r || !circuit) return;
    const { d3, svg } = r;
    const margin = { top: 60, right: 20, bottom: 30, left: 20 };
    const w = 400 - margin.left - margin.right, h = 140 - margin.top - margin.bottom;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
    const nodes = circuit.nodes || [], edges = circuit.edges || [];
    if (nodes.length === 0) return;
    const x = d3.scalePoint().domain(nodes.map((_, i) => i)).range([0, w]).padding(0.1);
    const maxG = Math.max(1, ...edges.map(e => e.conductance));
    const color = d3.scaleSequential(d3.interpolateViridis).domain(d3.extent(nodes, d => d.mu));
    // Arcs
    edges.forEach(e => {
      const x1 = x(e.src), x2 = x(e.dst);
      const midX = (x1 + x2) / 2;
      const arcH = Math.abs(x2 - x1) * 0.5;
      const thick = Math.max(0.5, 3 * e.conductance / maxG);
      g.append("path").attr("d", `M ${x1} 0 A ${Math.abs(x2 - x1) / 2} ${arcH} 0 0 ${x2 > x1 ? 1 : 0} ${x2} 0`)
        .attr("fill", "none").attr("stroke", "#4a9eff").attr("stroke-width", thick).attr("opacity", 0.4);
    });
    // Nodes
    nodes.forEach((n, i) => {
      g.append("circle").attr("cx", x(i)).attr("cy", 0).attr("r", 6).attr("fill", color(n.mu)).attr("stroke", "#fff").attr("stroke-width", 1);
      g.append("text").attr("x", x(i)).attr("y", 16).attr("text-anchor", "middle").style("fill", "#888").style("font-size", "8px").text(n.name.slice(0, 6));
    });
  }, [circuit]);
  return <svg ref={ref} width={400} height={140} />;
}

/* ─── Main Charts Panel ─── */
export default function ChartsPanel({ metrics, circuit, imports }) {
  if (!metrics) {
    return <div className="flex h-full items-center justify-center text-sm" style={{ color: "#5a5a5a" }}>Run to generate charts</div>;
  }

  const names = circuit?.nodes?.map(n => n.name) || [];

  return (
    <div className="h-full overflow-auto p-4" style={{ background: "#0f0f1a" }}>
      {/* Metric cards */}
      <div className="mb-4 flex flex-wrap gap-3">
        {[
          { label: "R (Coherence)", value: metrics.R?.toFixed(4), good: metrics.R > 0.5 },
          { label: "V (Visibility)", value: metrics.V?.toFixed(4), good: metrics.V > 0.5 },
          { label: "Nodes", value: circuit?.numNodes },
          { label: "Edges", value: circuit?.numEdges },
          { label: "Backend", value: metrics.backend },
          { label: "Time", value: metrics.renderTimeMs ? `${metrics.renderTimeMs.toFixed(1)}ms` : "—" },
        ].map(({ label, value, good }) => (
          <div key={label} className="rounded px-3 py-2" style={{ background: "#1a1a3e" }}>
            <div className="text-[10px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>{label}</div>
            <div className="font-mono text-sm font-bold" style={{ color: good === undefined ? "#d4d4d4" : good ? "#4ec9b0" : "#ff6b6b" }}>
              {value ?? "—"}
            </div>
          </div>
        ))}
      </div>

      {/* Import sources */}
      {imports && Object.keys(imports).length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {Object.entries(imports).map(([name, data]) => (
            <div key={name} className="flex items-center gap-1.5 rounded px-2 py-1" style={{ background: "#1a1a3e", border: "1px solid #2a2a4a" }}>
              <span className="text-[10px] uppercase tracking-wider" style={{ color: "#4ec9b0" }}>{data.source || "API"}</span>
              <span className="text-[11px]" style={{ color: "#888" }}>{data.name || name}</span>
            </div>
          ))}
        </div>
      )}

      {/* Row 1: Gauge + Correlation */}
      <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>System Health Gauges</div>
      <div className="mb-4 flex flex-wrap items-start gap-2">
        <GaugeChart value={metrics.R || 0} label="R (Coherence)" good={(metrics.R || 0) > 0.5} />
        <GaugeChart value={metrics.V || 0} label="V (Visibility)" good={(metrics.V || 0) > 0.5} />
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>Triple Correlation</div>
          <CorrelationMatrix metrics={metrics} />
        </div>
      </div>

      {/* Row 2: Scatter + Flux bars */}
      <div className="mb-4 flex flex-wrap gap-4">
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>S-entropy Scatter (Se vs Sk, color=St)</div>
          <ScatterChart metrics={metrics} circuit={circuit} />
        </div>
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>Flux Comparison (log scale)</div>
          <FluxBarChart metrics={metrics} circuit={circuit} />
        </div>
      </div>

      {/* Row 3: Phase coherence + Coupling heatmap */}
      <div className="mb-4 flex flex-wrap gap-4">
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>Phase Coherence (Kuramoto r)</div>
          <PhaseCoherence metrics={metrics} circuit={circuit} />
        </div>
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>Coupling Matrix (conductance)</div>
          <CouplingHeatmap circuit={circuit} />
        </div>
      </div>

      {/* Row 4: Radar + Compartment donut */}
      <div className="mb-4 flex flex-wrap gap-4">
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>Radar (Se, Sk, St, mu, conc)</div>
          <RadarChart metrics={metrics} circuit={circuit} />
        </div>
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>Compartments</div>
          <CompartmentDonut circuit={circuit} />
        </div>
      </div>

      {/* Row 5: Sankey + Waterfall */}
      <div className="mb-4 flex flex-wrap gap-4">
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>Metabolic Flow (flux-weighted)</div>
          <SankeyFlow metrics={metrics} circuit={circuit} />
        </div>
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>Cumulative ΔG Waterfall</div>
          <WaterfallChart circuit={circuit} />
        </div>
      </div>

      {/* Row 6: Parallel coords + Ridge */}
      <div className="mb-4 flex flex-wrap gap-4">
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>Parallel Coordinates (Se, Sk, St)</div>
          <ParallelCoords metrics={metrics} circuit={circuit} />
        </div>
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>S-entropy Distributions</div>
          <RidgePlot metrics={metrics} />
        </div>
      </div>

      {/* Row 7: Arc diagram + 3D landscape */}
      <div className="mb-4 flex flex-wrap gap-4">
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>Arc Diagram (linear topology)</div>
          <ArcDiagram circuit={circuit} />
        </div>
      </div>

      <div className="mb-4">
        <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>S-Entropy Landscape (isometric 3D)</div>
        <SEntropyLandscape metrics={metrics} circuit={circuit} />
      </div>

      {/* Backward path */}
      {metrics.backwardPath && metrics.backwardPath.length > 0 && (
        <div className="mb-4">
          <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>Backward Navigation Path</div>
          <div className="flex flex-wrap items-center gap-1">
            {metrics.backwardPath.map((node, i) => (
              <React.Fragment key={i}>
                {i > 0 && <span style={{ color: "#4a4a6a" }}>&larr;</span>}
                <span className="rounded px-2 py-0.5 font-mono text-xs" style={{ background: "#1a1a3e", color: "#4ec9b0" }}>
                  {node.name}
                </span>
              </React.Fragment>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
