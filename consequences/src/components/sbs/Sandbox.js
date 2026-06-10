import React, { useState, useRef, useCallback, useMemo, useEffect } from "react";
import {
  Files, ChevronRight, ChevronDown,
  X, Circle, FileCode2, Folder, FolderOpen,
  Terminal as TerminalIcon, AlertCircle,
  PanelBottomClose, Check,
  Eye, Code2, Trash2, RefreshCw, BarChart3, Play,
} from "lucide-react";
import { compileSBS } from "@/lib/sbs/dsl/compiler";
import { SCRIPTS, DEFAULT_SCRIPT } from "@/lib/sbs/dsl/scripts";
import { solveCircuit, computeFluxPattern } from "@/lib/sbs/shaderSolver";
import { extractMetrics } from "@/lib/sbs/metricsExtractor";

const theme = {
  titlebar: "#1a1a2e", activitybar: "#16213e", activitybarFg: "#858585",
  activitybarFgActive: "#ffffff", sidebar: "#1a1a2e", sidebarFg: "#cccccc",
  sidebarHeader: "#bbbbbb", editor: "#0f0f1a", editorFg: "#d4d4d4",
  tabBar: "#16213e", tabActive: "#0f0f1a", tabInactive: "#1a1a2e",
  tabFg: "#969696", tabFgActive: "#ffffff", border: "#2a2a4a",
  accent: "#0e639c", accentBright: "#007acc", statusBar: "#0e639c",
  statusFg: "#ffffff", panel: "#0f0f1a", gutter: "#4a4a6a",
  lineActive: "#1a1a3e", selection: "#264f78",
};

/* ── Helpers ── */
const getScript = (name) => SCRIPTS[name] || null;

/* ── File Tree ── */
function Tree({ scripts, activePath, openFile }) {
  const entries = Object.entries(scripts).sort((a, b) => a[0].localeCompare(b[0]));
  return (
    <>
      {entries.map(([name, script]) => {
        const isActive = activePath === name;
        return (
          <button
            key={name}
            onClick={() => openFile(name)}
            className="flex w-full items-center gap-1.5 py-1 pr-2 text-left text-[13px] leading-relaxed transition-colors"
            style={{
              paddingLeft: 20,
              color: theme.sidebarFg,
              background: isActive ? theme.lineActive : "transparent",
            }}
            onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.background = theme.lineActive; }}
            onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.background = "transparent"; }}
          >
            <FileCode2 size={15} className="shrink-0" style={{ color: "#4ec9b0" }} />
            <span className="truncate">{name}</span>
          </button>
        );
      })}
    </>
  );
}

/* ── Editor with line numbers ── */
function Editor({ value, onChange, onCursor }) {
  const gutterRef = useRef(null);
  const lines = value.split("\n");
  const syncScroll = (e) => { if (gutterRef.current) gutterRef.current.scrollTop = e.target.scrollTop; };
  const handleCursor = (e) => {
    const upto = e.target.value.slice(0, e.target.selectionStart);
    onCursor({ ln: upto.split("\n").length, col: upto.length - upto.lastIndexOf("\n") });
  };
  const handleKeyDown = (e) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const { selectionStart, selectionEnd } = e.target;
      const next = value.slice(0, selectionStart) + "  " + value.slice(selectionEnd);
      onChange(next);
      requestAnimationFrame(() => {
        e.target.selectionStart = e.target.selectionEnd = selectionStart + 2;
      });
    }
  };
  return (
    <div className="flex min-h-0 flex-1" style={{ background: theme.editor }}>
      <div
        ref={gutterRef}
        className="select-none overflow-hidden py-3 text-right font-mono text-[13px] leading-[1.5]"
        style={{ color: theme.gutter, minWidth: 52, paddingRight: 16 }}
      >
        {lines.map((_, i) => <div key={i}>{i + 1}</div>)}
      </div>
      <textarea
        value={value} onChange={(e) => onChange(e.target.value)} onScroll={syncScroll}
        onKeyUp={handleCursor} onClick={handleCursor} onKeyDown={handleKeyDown}
        spellCheck={false}
        className="min-h-0 flex-1 resize-none border-0 bg-transparent py-3 pr-4 font-mono text-[13px] leading-[1.5] outline-none"
        style={{ color: theme.editorFg, tabSize: 2, caretColor: "#4ec9b0" }}
      />
    </div>
  );
}

/* ── Charts panel — D3 scatter + bar + phase coherence + heatmap + 3D surface ── */
function ChartsPanel({ metrics, circuit, imports }) {
  const scatterRef = useRef(null);
  const barRef = useRef(null);
  const phaseRef = useRef(null);
  const heatmapRef = useRef(null);
  const surfaceRef = useRef(null);

  // S-entropy scatter
  useEffect(() => {
    if (!metrics || !scatterRef.current) return;
    let d3;
    try { d3 = require("d3"); } catch { return; }

    const svg = d3.select(scatterRef.current);
    svg.selectAll("*").remove();
    const margin = { top: 20, right: 20, bottom: 40, left: 50 };
    const w = 320 - margin.left - margin.right;
    const h = 220 - margin.top - margin.bottom;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleLinear().domain([0, 1]).range([0, w]).nice();
    const y = d3.scaleLinear().domain([0, 1]).range([h, 0]).nice();
    const color = d3.scaleSequential(d3.interpolateViridis).domain([0, 1]);

    g.append("g").attr("transform", `translate(0,${h})`).call(d3.axisBottom(x).ticks(5))
      .selectAll("text").style("fill", "#888");
    g.append("g").call(d3.axisLeft(y).ticks(5))
      .selectAll("text").style("fill", "#888");
    g.selectAll("line").style("stroke", "#333");
    g.selectAll("path.domain").style("stroke", "#333");

    g.append("text").attr("x", w / 2).attr("y", h + 35).style("fill", "#888").style("font-size", "11px").style("text-anchor", "middle").text("Se (chemical potential)");
    g.append("text").attr("transform", "rotate(-90)").attr("x", -h / 2).attr("y", -40).style("fill", "#888").style("font-size", "11px").style("text-anchor", "middle").text("Sk (flux)");

    const Se = metrics.Se || [];
    const Sk = metrics.Sk || [];
    const St = metrics.St || [];
    const names = circuit?.nodes?.map(n => n.name) || [];

    Se.forEach((se, i) => {
      g.append("circle")
        .attr("cx", x(se)).attr("cy", y(Sk[i] || 0))
        .attr("r", 6).attr("fill", color(St[i] || 0))
        .attr("stroke", "#fff").attr("stroke-width", 0.5)
        .attr("opacity", 0.9)
        .append("title").text(`${names[i] || i}: Se=${se.toFixed(3)}, Sk=${(Sk[i] || 0).toFixed(3)}, St=${(St[i] || 0).toFixed(3)}`);
    });
  }, [metrics, circuit]);

  // Flux comparison bar chart
  useEffect(() => {
    if (!metrics || !barRef.current) return;
    let d3;
    try { d3 = require("d3"); } catch { return; }

    const svg = d3.select(barRef.current);
    svg.selectAll("*").remove();
    const margin = { top: 20, right: 20, bottom: 50, left: 50 };
    const w = 380 - margin.left - margin.right;
    const h = 200 - margin.top - margin.bottom;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const healthy = metrics.fluxHealthy || [];
    const current = metrics.fluxCurrent || [];
    const edgeNames = circuit?.edges?.map(e => e.name.length > 10 ? e.name.slice(0, 10) : e.name) || [];
    if (healthy.length === 0) return;

    const maxFlux = Math.max(1e-10, ...healthy, ...current);
    const x = d3.scaleBand().domain(edgeNames).range([0, w]).padding(0.2);
    const y = d3.scaleLog().domain([Math.max(1e-6, maxFlux * 1e-6), maxFlux * 1.2]).range([h, 0]).clamp(true);

    g.append("g").attr("transform", `translate(0,${h})`).call(d3.axisBottom(x))
      .selectAll("text").style("fill", "#888").style("font-size", "9px")
      .attr("transform", "rotate(-40)").style("text-anchor", "end");
    g.append("g").call(d3.axisLeft(y).ticks(4, ".0e"))
      .selectAll("text").style("fill", "#888");
    g.selectAll("line").style("stroke", "#333");
    g.selectAll("path.domain").style("stroke", "#333");

    const bw = x.bandwidth() / 2;
    healthy.forEach((h_val, i) => {
      const name = edgeNames[i] || `e${i}`;
      g.append("rect").attr("x", x(name)).attr("y", y(Math.max(1e-10, h_val)))
        .attr("width", bw).attr("height", h - y(Math.max(1e-10, h_val)))
        .attr("fill", "#4a9eff").attr("opacity", 0.7)
        .append("title").text(`Healthy: ${h_val.toFixed(4)}`);
      const c_val = current[i] || 0;
      g.append("rect").attr("x", x(name) + bw).attr("y", y(Math.max(1e-10, c_val)))
        .attr("width", bw).attr("height", h - y(Math.max(1e-10, c_val)))
        .attr("fill", "#ff6b6b").attr("opacity", 0.7)
        .append("title").text(`Current: ${c_val.toFixed(4)}`);
    });

    g.append("rect").attr("x", w - 90).attr("y", 0).attr("width", 10).attr("height", 10).attr("fill", "#4a9eff");
    g.append("text").attr("x", w - 76).attr("y", 9).style("fill", "#888").style("font-size", "10px").text("Healthy");
    g.append("rect").attr("x", w - 90).attr("y", 15).attr("width", 10).attr("height", 10).attr("fill", "#ff6b6b");
    g.append("text").attr("x", w - 76).attr("y", 24).style("fill", "#888").style("font-size", "10px").text("Perturbed");
  }, [metrics, circuit]);

  // Phase coherence circular plot
  useEffect(() => {
    if (!metrics || !phaseRef.current || !circuit) return;
    let d3;
    try { d3 = require("d3"); } catch { return; }

    const svg = d3.select(phaseRef.current);
    svg.selectAll("*").remove();
    const size = 280;
    const cx = size / 2;
    const cy = size / 2;
    const radius = size / 2 - 40;
    const g = svg.append("g").attr("transform", `translate(${cx},${cy})`);

    const Se = metrics.Se || [];
    const Sk = metrics.Sk || [];
    const names = circuit.nodes?.map(n => n.name) || [];
    const n = Se.length;
    if (n === 0) return;

    // Compute phase for each node: phi = 2*pi * Se (normalized position on unit circle)
    const phases = Se.map((se, i) => ({
      phase: se * 2 * Math.PI,
      amplitude: Sk[i] || 0.5,
      name: names[i] || `n${i}`,
    }));

    // Grid circles
    for (let i = 1; i <= 4; i++) {
      const r = (radius / 4) * i;
      g.append("circle").attr("cx", 0).attr("cy", 0).attr("r", r)
        .attr("fill", "none").attr("stroke", "#2a2a4a").attr("stroke-width", 1);
      g.append("text").attr("x", 4).attr("y", -r + 4)
        .style("fill", "#4a4a6a").style("font-size", "9px").text((i / 4).toFixed(1));
    }

    // Radial lines every 45 degrees
    for (let a = 0; a < 360; a += 45) {
      const rad = (a * Math.PI) / 180;
      g.append("line")
        .attr("x1", 0).attr("y1", 0)
        .attr("x2", radius * Math.cos(rad - Math.PI / 2))
        .attr("y2", radius * Math.sin(rad - Math.PI / 2))
        .attr("stroke", "#2a2a4a").attr("stroke-width", 1);
    }

    const color = d3.scaleOrdinal(d3.schemeTableau10);

    // Phase vectors
    let sumX = 0, sumY = 0;
    phases.forEach((p, i) => {
      const amp = Math.max(0.1, p.amplitude);
      const px = radius * amp * Math.cos(p.phase - Math.PI / 2);
      const py = radius * amp * Math.sin(p.phase - Math.PI / 2);

      g.append("line")
        .attr("x1", 0).attr("y1", 0).attr("x2", px).attr("y2", py)
        .attr("stroke", color(i)).attr("stroke-width", 1.5).attr("opacity", 0.7);

      g.append("circle").attr("cx", px).attr("cy", py).attr("r", 5)
        .attr("fill", color(i)).attr("stroke", "#fff").attr("stroke-width", 0.5)
        .append("title").text(`${p.name}: phase=${(p.phase * 180 / Math.PI).toFixed(1)}°, amp=${amp.toFixed(3)}`);

      g.append("text").attr("x", px * 1.18).attr("y", py * 1.18)
        .attr("text-anchor", "middle").attr("dominant-baseline", "middle")
        .style("fill", "#888").style("font-size", "9px")
        .text(p.name.length > 6 ? p.name.slice(0, 5) + "…" : p.name);

      sumX += Math.cos(p.phase);
      sumY += Math.sin(p.phase);
    });

    // Order parameter (red vector)
    const r = Math.sqrt(sumX * sumX + sumY * sumY) / n;
    const avgPhase = Math.atan2(sumY, sumX);
    const opx = radius * r * Math.cos(avgPhase - Math.PI / 2);
    const opy = radius * r * Math.sin(avgPhase - Math.PI / 2);

    g.append("line")
      .attr("x1", 0).attr("y1", 0).attr("x2", opx).attr("y2", opy)
      .attr("stroke", "#ff4444").attr("stroke-width", 3).attr("opacity", 0.9);
    g.append("circle").attr("cx", opx).attr("cy", opy).attr("r", 4)
      .attr("fill", "#ff4444");

    // Labels
    const status = r > 0.7 ? "Coherent" : r > 0.4 ? "Partial" : "Incoherent";
    const statusColor = r > 0.7 ? "#4ec9b0" : r > 0.4 ? "#dcdcaa" : "#ff6b6b";

    g.append("text").attr("x", 0).attr("y", -radius - 18)
      .attr("text-anchor", "middle").style("fill", "#ccc").style("font-size", "12px").style("font-weight", "bold")
      .text(`r = ${r.toFixed(3)}`);
    g.append("text").attr("x", 0).attr("y", -radius - 5)
      .attr("text-anchor", "middle").style("fill", statusColor).style("font-size", "10px")
      .text(status);
  }, [metrics, circuit]);

  // Coupling matrix heatmap
  useEffect(() => {
    if (!metrics || !heatmapRef.current || !circuit) return;
    let d3;
    try { d3 = require("d3"); } catch { return; }

    const svg = d3.select(heatmapRef.current);
    svg.selectAll("*").remove();
    const nodes = circuit.nodes || [];
    const edges = circuit.edges || [];
    const n = nodes.length;
    if (n === 0) return;

    const margin = { top: 60, right: 40, bottom: 20, left: 70 };
    const size = Math.min(320, 20 * n + margin.left + margin.right);
    const cellSize = (size - margin.left - margin.right) / n;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    // Build coupling matrix: K_ij = conductance of edge i->j (or j->i)
    const matrix = Array.from({ length: n }, () => Array(n).fill(0));
    edges.forEach(e => {
      matrix[e.src][e.dst] = e.conductance;
      matrix[e.dst][e.src] = e.conductance * 0.3;
    });

    const maxVal = Math.max(1e-10, ...matrix.flat());
    const color = d3.scaleSequential(d3.interpolatePlasma).domain([0, maxVal]);
    const names = nodes.map(nd => nd.name.length > 7 ? nd.name.slice(0, 6) + "…" : nd.name);

    // Cells
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        g.append("rect")
          .attr("x", j * cellSize).attr("y", i * cellSize)
          .attr("width", cellSize - 1).attr("height", cellSize - 1)
          .attr("fill", matrix[i][j] > 0 ? color(matrix[i][j]) : "#0a0a14")
          .attr("rx", 1)
          .append("title").text(`${nodes[i].name} → ${nodes[j].name}: ${matrix[i][j].toFixed(2)}`);
      }
    }

    // Row labels
    g.selectAll(".row-label").data(names).enter().append("text")
      .attr("x", -4).attr("y", (d, i) => i * cellSize + cellSize / 2)
      .attr("text-anchor", "end").attr("dominant-baseline", "middle")
      .style("fill", "#888").style("font-size", "9px").text(d => d);

    // Column labels
    g.selectAll(".col-label").data(names).enter().append("text")
      .attr("x", (d, i) => i * cellSize + cellSize / 2).attr("y", -4)
      .attr("text-anchor", "end").attr("dominant-baseline", "middle")
      .attr("transform", (d, i) => `rotate(-45, ${i * cellSize + cellSize / 2}, -4)`)
      .style("fill", "#888").style("font-size", "9px").text(d => d);

    // Color legend
    const legendW = 10;
    const legendH = n * cellSize;
    const legendX = n * cellSize + 10;
    const defs = svg.append("defs");
    const gradient = defs.append("linearGradient").attr("id", "hm-grad")
      .attr("x1", "0%").attr("y1", "100%").attr("x2", "0%").attr("y2", "0%");
    for (let i = 0; i <= 10; i++) {
      gradient.append("stop")
        .attr("offset", `${i * 10}%`)
        .attr("stop-color", color(maxVal * i / 10));
    }
    g.append("rect").attr("x", legendX).attr("y", 0)
      .attr("width", legendW).attr("height", legendH)
      .style("fill", "url(#hm-grad)");
    g.append("text").attr("x", legendX + legendW + 4).attr("y", 8)
      .style("fill", "#888").style("font-size", "9px").text(maxVal.toFixed(1));
    g.append("text").attr("x", legendX + legendW + 4).attr("y", legendH)
      .style("fill", "#888").style("font-size", "9px").text("0");
  }, [metrics, circuit]);

  // 3D S-entropy surface (pseudo-3D using D3 with isometric projection)
  useEffect(() => {
    if (!metrics || !surfaceRef.current || !circuit) return;
    let d3;
    try { d3 = require("d3"); } catch { return; }

    const canvas = surfaceRef.current;
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const Se = metrics.Se || [];
    const Sk = metrics.Sk || [];
    const St = metrics.St || [];
    const names = circuit.nodes?.map(n => n.name) || [];
    const n = Se.length;
    if (n === 0) return;

    // Isometric projection: (Se, Sk, St) -> (x, y)
    const scale = Math.min(w, h) * 0.35;
    const ox = w / 2;
    const oy = h / 2 + 20;
    const isoX = (se, sk) => ox + scale * (se - sk) * Math.cos(Math.PI / 6);
    const isoY = (se, sk, st) => oy - scale * st * 0.8 + scale * (se + sk) * Math.sin(Math.PI / 6) * 0.5;

    // Draw axes
    ctx.strokeStyle = "#3a3a5a";
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);

    // Se axis
    ctx.beginPath();
    ctx.moveTo(isoX(0, 0), isoY(0, 0, 0));
    ctx.lineTo(isoX(1, 0), isoY(1, 0, 0));
    ctx.stroke();
    ctx.fillStyle = "#888";
    ctx.font = "10px monospace";
    ctx.fillText("Se", isoX(1.05, 0), isoY(1.05, 0, 0) + 4);

    // Sk axis
    ctx.beginPath();
    ctx.moveTo(isoX(0, 0), isoY(0, 0, 0));
    ctx.lineTo(isoX(0, 1), isoY(0, 1, 0));
    ctx.stroke();
    ctx.fillText("Sk", isoX(0, 1.05), isoY(0, 1.05, 0) + 4);

    // St axis
    ctx.beginPath();
    ctx.moveTo(isoX(0, 0), isoY(0, 0, 0));
    ctx.lineTo(isoX(0, 0), isoY(0, 0, 1));
    ctx.stroke();
    ctx.fillText("St", isoX(0, 0) + 4, isoY(0, 0, 1) - 4);

    ctx.setLineDash([]);

    // Draw grid floor (Se-Sk plane at St=0)
    ctx.strokeStyle = "#1a1a3e";
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= 4; i++) {
      const t = i / 4;
      ctx.beginPath();
      ctx.moveTo(isoX(t, 0), isoY(t, 0, 0));
      ctx.lineTo(isoX(t, 1), isoY(t, 1, 0));
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(isoX(0, t), isoY(0, t, 0));
      ctx.lineTo(isoX(1, t), isoY(1, t, 0));
      ctx.stroke();
    }

    // Draw drop lines (from point to floor)
    ctx.strokeStyle = "#2a2a4a";
    ctx.lineWidth = 0.5;
    ctx.setLineDash([2, 2]);
    Se.forEach((se, i) => {
      const sk = Sk[i] || 0;
      const st = St[i] || 0;
      ctx.beginPath();
      ctx.moveTo(isoX(se, sk), isoY(se, sk, st));
      ctx.lineTo(isoX(se, sk), isoY(se, sk, 0));
      ctx.stroke();
    });
    ctx.setLineDash([]);

    // Draw shadow points on floor
    ctx.fillStyle = "rgba(78, 201, 176, 0.15)";
    Se.forEach((se, i) => {
      const sk = Sk[i] || 0;
      ctx.beginPath();
      ctx.arc(isoX(se, sk), isoY(se, sk, 0), 3, 0, 2 * Math.PI);
      ctx.fill();
    });

    // Sort by depth for proper overlap
    const sorted = Se.map((se, i) => ({ se, sk: Sk[i] || 0, st: St[i] || 0, name: names[i] || `n${i}`, i }));
    sorted.sort((a, b) => (a.se + a.sk) - (b.se + b.sk));

    // Draw data points
    const viridis = (t) => {
      const r = Math.round(255 * Math.max(0, Math.min(1, 0.267 + 0.005 * t + 2.817 * t * t - 5.765 * t * t * t + 2.676 * t * t * t * t)));
      const g = Math.round(255 * Math.max(0, Math.min(1, 0.005 + 1.404 * t - 2.799 * t * t + 4.390 * t * t * t - 2.000 * t * t * t * t)));
      const b = Math.round(255 * Math.max(0, Math.min(1, 0.329 + 1.074 * t - 0.734 * t * t + 0.331 * t * t * t)));
      return `rgb(${r},${g},${b})`;
    };

    sorted.forEach(({ se, sk, st, name }) => {
      const px = isoX(se, sk);
      const py = isoY(se, sk, st);

      // Glow
      ctx.beginPath();
      ctx.arc(px, py, 10, 0, 2 * Math.PI);
      ctx.fillStyle = viridis(st).replace("rgb", "rgba").replace(")", ",0.2)");
      ctx.fill();

      // Point
      ctx.beginPath();
      ctx.arc(px, py, 6, 0, 2 * Math.PI);
      ctx.fillStyle = viridis(st);
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 0.8;
      ctx.stroke();

      // Label
      ctx.fillStyle = "#aaa";
      ctx.font = "9px monospace";
      ctx.textAlign = "center";
      ctx.fillText(name.length > 8 ? name.slice(0, 7) + "…" : name, px, py - 10);
    });

    // Title
    ctx.fillStyle = "#6a6a8a";
    ctx.font = "10px monospace";
    ctx.textAlign = "left";
    ctx.fillText("S-entropy space [0,1]³", 8, 14);
  }, [metrics, circuit]);

  if (!metrics) {
    return <div className="flex h-full items-center justify-center text-sm" style={{ color: "#5a5a5a" }}>Run to generate charts</div>;
  }

  return (
    <div className="h-full overflow-auto p-4">
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

      <div className="flex flex-wrap gap-4">
        {/* Row 1: Scatter + Flux bars */}
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>S-entropy Scatter (Se vs Sk, color=St)</div>
          <svg ref={scatterRef} width={320} height={220} />
        </div>
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>Flux Comparison (log scale)</div>
          <svg ref={barRef} width={380} height={200} />
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-4">
        {/* Row 2: Phase coherence + Heatmap */}
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>Phase Coherence (Kuramoto order parameter)</div>
          <svg ref={phaseRef} width={280} height={280} />
        </div>
        <div>
          <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>Coupling Matrix (conductance heatmap)</div>
          <svg ref={heatmapRef} width={340} height={340} />
        </div>
      </div>

      <div className="mt-4">
        {/* Row 3: 3D S-entropy surface */}
        <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: "#6a6a8a" }}>S-Entropy Landscape (isometric 3D)</div>
        <canvas ref={surfaceRef} width={600} height={350} style={{ background: "#0a0a14", borderRadius: 4 }} />
      </div>

      {/* Backward path */}
      {metrics.backwardPath && metrics.backwardPath.length > 0 && (
        <div className="mt-4">
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

/* ── GLB 3D viewer ── */
function GLBViewer({ glbModel, circuit }) {
  const containerRef = useRef(null);
  const rendererRef = useRef(null);

  useEffect(() => {
    if (!glbModel?.file || !containerRef.current) return;
    let THREE, GLTFLoader, OrbitControls;
    try {
      THREE = require("three");
      GLTFLoader = require("three/examples/jsm/loaders/GLTFLoader").GLTFLoader;
      OrbitControls = require("three/examples/jsm/controls/OrbitControls").OrbitControls;
    } catch { return; }

    const el = containerRef.current;
    const w = el.clientWidth || 600;
    const h = el.clientHeight || 400;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a14);

    const camera = new THREE.PerspectiveCamera(50, w / h, 0.1, 100);
    camera.position.set(3, 2, 4);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    el.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;

    scene.add(new THREE.AmbientLight(0x404040, 2));
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.5);
    dirLight.position.set(3, 5, 3);
    scene.add(dirLight);

    const loader = new GLTFLoader();
    loader.load(glbModel.file, (gltf) => {
      const model = gltf.scene;
      const box = new THREE.Box3().setFromObject(model);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z);
      model.position.sub(center);
      model.scale.setScalar(2.5 / maxDim);
      scene.add(model);

      // Add node markers if species_map is present
      if (glbModel.species_map && circuit) {
        const markerGeom = new THREE.SphereGeometry(0.08, 16, 16);
        for (const [name, info] of Object.entries(glbModel.species_map)) {
          const mat = new THREE.MeshPhongMaterial({ color: info.color || "#4ec9b0", emissive: info.color || "#4ec9b0", emissiveIntensity: 0.3 });
          const marker = new THREE.Mesh(markerGeom, mat);
          marker.position.set(...(info.position || [0, 0, 0]));
          scene.add(marker);
        }
      }
    }, undefined, (err) => {
      console.warn("GLB load error:", err);
    });

    let animId;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animId);
      controls.dispose();
      renderer.dispose();
      if (el.contains(renderer.domElement)) el.removeChild(renderer.domElement);
    };
  }, [glbModel, circuit]);

  return (
    <div ref={containerRef} className="h-full w-full" style={{ background: "#0a0a14" }} />
  );
}

/* ── Preview panel — circuit graph + optional GLB ── */
function PreviewPanel({ circuit, metrics, glbModel }) {
  const svgRef = useRef(null);
  const [showGLB, setShowGLB] = useState(false);

  useEffect(() => {
    if (glbModel?.file) setShowGLB(true);
    else setShowGLB(false);
  }, [glbModel]);

  useEffect(() => {
    if (!circuit || !svgRef.current || showGLB) return;
    let d3;
    try { d3 = require("d3"); } catch { return; }

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = svgRef.current.clientWidth || 600;
    const height = svgRef.current.clientHeight || 400;

    const defs = svg.append("defs");
    defs.append("marker").attr("id", "arrow").attr("viewBox", "0 -5 10 10")
      .attr("refX", 20).attr("refY", 0).attr("markerWidth", 6).attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path").attr("d", "M0,-5L10,0L0,5").attr("fill", "#4a4a6a");

    const muExtent = d3.extent(circuit.nodes, d => d.mu);
    const colorScale = d3.scaleSequential(d3.interpolateViridis).domain(muExtent);

    const nodes = circuit.nodes.map(n => ({ ...n }));
    const links = circuit.edges.map(e => ({ ...e, source: e.src, target: e.dst }));

    const sim = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((_, i) => i).distance(80))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide(30));

    const gLinks = svg.append("g");
    const gNodes = svg.append("g");
    const gLabels = svg.append("g");

    const maxG = Math.max(1, ...circuit.edges.map(e => e.conductance));

    const link = gLinks.selectAll("line").data(links).join("line")
      .attr("stroke", "#3a3a5a")
      .attr("stroke-width", d => Math.max(1, 3 * d.conductance / maxG))
      .attr("marker-end", "url(#arrow)");

    const node = gNodes.selectAll("circle").data(nodes).join("circle")
      .attr("r", 14)
      .attr("fill", d => colorScale(d.mu))
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .style("cursor", "grab")
      .call(d3.drag()
        .on("start", (e, d) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on("end", (e, d) => { if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; })
      );
    node.append("title").text(d => `${d.name}\nmu: ${d.mu.toFixed(1)} kJ/mol\nconc: ${d.concentration}`);

    const label = gLabels.selectAll("text").data(nodes).join("text")
      .text(d => d.name.length > 10 ? d.name.slice(0, 9) + "…" : d.name)
      .attr("text-anchor", "middle").attr("dy", -20)
      .style("fill", "#ccc").style("font-size", "11px").style("font-family", "monospace")
      .style("pointer-events", "none");

    sim.on("tick", () => {
      link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
      node.attr("cx", d => d.x).attr("cy", d => d.y);
      label.attr("x", d => d.x).attr("y", d => d.y);
    });

    const zoom = d3.zoom().scaleExtent([0.3, 4]).on("zoom", (e) => {
      gLinks.attr("transform", e.transform);
      gNodes.attr("transform", e.transform);
      gLabels.attr("transform", e.transform);
    });
    svg.call(zoom);

    return () => sim.stop();
  }, [circuit, showGLB]);

  if (!circuit) {
    return <div className="flex h-full items-center justify-center text-sm" style={{ color: "#5a5a5a" }}>Run a script to see the circuit</div>;
  }

  return (
    <div className="relative h-full w-full" style={{ background: "#0a0a14" }}>
      {showGLB && glbModel ? (
        <GLBViewer glbModel={glbModel} circuit={circuit} />
      ) : (
        <svg ref={svgRef} className="h-full w-full" />
      )}
      <div className="absolute left-3 top-3 flex items-center gap-2">
        <span className="rounded px-2 py-1 text-[11px] font-mono" style={{ background: "rgba(15,15,26,0.85)", color: "#4ec9b0" }}>
          {circuit.numNodes} nodes, {circuit.numEdges} edges
          {showGLB ? " — 3D model" : " — drag nodes, scroll to zoom"}
        </span>
        {glbModel?.file && (
          <button
            onClick={() => setShowGLB(s => !s)}
            className="rounded px-2 py-1 text-[11px] font-mono"
            style={{ background: "rgba(15,15,26,0.85)", color: showGLB ? "#dcdcaa" : "#4ec9b0", border: "1px solid #2a2a4a" }}
          >
            {showGLB ? "Show Graph" : "Show 3D"}
          </button>
        )}
      </div>
      {circuit.compartments && circuit.compartments.length > 1 && (
        <div className="absolute bottom-3 left-3 flex gap-2">
          {circuit.compartments.map(c => (
            <span key={c} className="rounded-full px-2 py-0.5 text-[10px]" style={{ background: "#1a1a3e", color: "#888" }}>{c}</span>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Output column ── */
function OutputColumn({ circuit, metrics, compiled, logs, onRun, onClear, errors, imports, glbModel }) {
  const [tab, setTab] = useState("preview");
  const tabs = [
    { id: "preview", label: "Preview", Icon: Eye },
    { id: "charts", label: "Charts", Icon: BarChart3 },
    { id: "console", label: "Console", Icon: TerminalIcon },
    { id: "compiled", label: "Compiled", Icon: Code2 },
  ];
  const levelColor = { log: "#d4d4d4", info: "#9cdcfe", warn: "#dcdcaa", error: "#f48771" };

  return (
    <div className="flex min-w-0 flex-1 flex-col" style={{ background: theme.editor, borderLeft: `1px solid ${theme.border}` }}>
      <div className="flex h-9 shrink-0 items-center justify-between pr-2" style={{ background: theme.tabInactive }}>
        <div className="flex h-full">
          {tabs.map(({ id, label, Icon }) => {
            const active = tab === id;
            return (
              <button key={id} onClick={() => setTab(id)}
                className="relative flex items-center gap-1.5 px-3 text-[12px] transition-colors"
                style={{ color: active ? theme.tabFgActive : theme.tabFg, background: active ? theme.tabActive : "transparent" }}>
                <Icon size={13} /> {label}
                {id === "console" && logs.length > 0 && (
                  <span className="rounded-full px-1.5 text-[10px]" style={{ background: theme.accent, color: "#fff" }}>{logs.length}</span>
                )}
                {active && <span className="absolute left-0 top-0 h-0.5 w-full" style={{ background: theme.accentBright }} />}
              </button>
            );
          })}
        </div>
        <div className="flex items-center gap-1">
          {tab === "console" && (
            <button onClick={onClear} title="Clear console" className="flex h-6 w-6 items-center justify-center rounded" style={{ color: theme.tabFg }}><Trash2 size={14} /></button>
          )}
          <button onClick={onRun} title="Run (Ctrl+Enter)" className="flex h-6 items-center gap-1 rounded px-2 text-[12px]" style={{ background: "#0e639c", color: "#fff" }}>
            <Play size={12} /> Run
          </button>
        </div>
      </div>

      <div className="min-h-0 flex-1">
        {tab === "preview" && <PreviewPanel circuit={circuit} metrics={metrics} glbModel={glbModel} />}
        {tab === "charts" && <ChartsPanel metrics={metrics} circuit={circuit} imports={imports} />}
        {tab === "console" && (
          <div className="h-full overflow-y-auto p-2 font-mono text-[12px] leading-relaxed">
            {errors.length > 0 && errors.map((e, i) => (
              <div key={`err${i}`} className="border-b px-1 py-1" style={{ color: "#f48771", borderColor: "#2a2a2a" }}>
                <span className="mr-2 opacity-50">error</span>{e.message}{e.line ? ` (line ${e.line})` : ""}
              </div>
            ))}
            {logs.length === 0 && errors.length === 0 ? (
              <div className="px-1 pt-1" style={{ color: "#5a5a5a" }}>Console output appears here.</div>
            ) : logs.map((l, i) => (
              <div key={i} className="border-b px-1 py-1" style={{ color: levelColor[l.level] || "#d4d4d4", borderColor: "#2a2a2a" }}>
                <span className="mr-2 opacity-50">{l.level}</span>{l.message}
              </div>
            ))}
          </div>
        )}
        {tab === "compiled" && (
          <div className="h-full overflow-auto">
            <div className="flex border-b" style={{ borderColor: theme.border }}>
              {["glsl", "js", "ast", "circuit"].map(sub => (
                <button key={sub} className="px-3 py-1.5 text-[11px] uppercase tracking-wider" style={{ color: theme.tabFg }}
                  onClick={(e) => {
                    e.currentTarget.parentElement.querySelectorAll("button").forEach(b => b.style.color = theme.tabFg);
                    e.currentTarget.style.color = theme.tabFgActive;
                    const panels = e.currentTarget.parentElement.nextElementSibling;
                    if (panels) {
                      panels.querySelectorAll("[data-panel]").forEach(p => p.style.display = "none");
                      const target = panels.querySelector(`[data-panel="${sub}"]`);
                      if (target) target.style.display = "block";
                    }
                  }}>
                  {sub}
                </button>
              ))}
            </div>
            <div>
              <pre data-panel="glsl" className="p-3 font-mono text-[12px] leading-[1.5]" style={{ color: theme.editorFg }}>
                {compiled.glsl || "// No GLSL output"}
              </pre>
              <pre data-panel="js" className="p-3 font-mono text-[12px] leading-[1.5]" style={{ color: theme.editorFg, display: "none" }}>
                {compiled.js || "// No JS output"}
              </pre>
              <pre data-panel="ast" className="p-3 font-mono text-[12px] leading-[1.5]" style={{ color: theme.editorFg, display: "none" }}>
                {compiled.ast || "// No AST"}
              </pre>
              <pre data-panel="circuit" className="p-3 font-mono text-[12px] leading-[1.5]" style={{ color: theme.editorFg, display: "none" }}>
                {compiled.circuit || "// No circuit"}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Main Sandbox ── */
export default function Sandbox() {
  const [activeFile, setActiveFile] = useState(DEFAULT_SCRIPT);
  const [sources, setSources] = useState(() => {
    const s = {};
    for (const [name, script] of Object.entries(SCRIPTS)) s[name] = script.code;
    return s;
  });
  const [openTabs, setOpenTabs] = useState([DEFAULT_SCRIPT]);
  const [dirty, setDirty] = useState(new Set());
  const [sidebar, setSidebar] = useState(true);
  const [cursor, setCursor] = useState({ ln: 1, col: 1 });
  const [panel, setPanel] = useState(false);
  const [panelTab, setPanelTab] = useState("problems");

  const [circuit, setCircuit] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [compiled, setCompiled] = useState({ glsl: null, js: null, ast: null, circuit: null });
  const [logs, setLogs] = useState([]);
  const [errors, setErrors] = useState([]);
  const [imports, setImports] = useState({});
  const [glbModel, setGlbModel] = useState(null);

  const [editorWidth, setEditorWidth] = useState(50);
  const splitRef = useRef(null);
  const dragging = useRef(false);

  const source = sources[activeFile] || "";

  const run = useCallback(() => {
    const code = sources[activeFile];
    if (!code) return;

    const t0 = performance.now();
    const result = compileSBS(code);
    const compileTime = performance.now() - t0;

    const newLogs = [];
    const newErrors = [];

    if (!result.success) {
      newErrors.push(...(result.errors || []));
      setErrors(newErrors);
      setLogs(newLogs);
      setCircuit(null);
      setMetrics(null);
      setImports({});
      setGlbModel(null);
      setCompiled({ glsl: null, js: null, ast: null, circuit: null });
      return;
    }

    // Track resolved imports
    if (result.imports && Object.keys(result.imports).length > 0) {
      setImports(result.imports);
      for (const [name, data] of Object.entries(result.imports)) {
        newLogs.push({ level: "info", message: `import ${name} from ${data.source || "registry"}: ${data.name || data.id || "resolved"}` });
      }
    } else {
      setImports({});
    }

    setGlbModel(result.glbModel || null);

    newLogs.push({ level: "info", message: `Compiled in ${compileTime.toFixed(1)}ms` });

    setCompiled({
      glsl: result.glsl || null,
      js: result.js || null,
      ast: result.ast ? JSON.stringify(result.ast, null, 2) : null,
      circuit: result.circuit ? JSON.stringify(result.circuit, null, 2) : null,
    });

    if (result.circuit) {
      newLogs.push({ level: "log", message: `Circuit: ${result.circuit.numNodes} nodes, ${result.circuit.numEdges} edges` });
      newLogs.push({ level: "log", message: `Compartments: ${result.circuit.compartments?.join(", ")}` });

      // Convert compiler perturbations ({target, factor, edge?}) to solver format ({idx, factor})
      const solverPerts = [];
      if (result.perturbations?.length > 0) {
        for (const p of result.perturbations) {
          if (p.edge) {
            const edgeIdx = result.circuit.edges.findIndex(e => e.name === p.edge);
            if (edgeIdx >= 0) solverPerts.push({ idx: edgeIdx, factor: p.factor });
          } else {
            // Apply to first edge (convention) or all edges
            for (let i = 0; i < result.circuit.numEdges; i++) {
              solverPerts.push({ idx: i, factor: p.factor });
            }
          }
        }
      }

      try {
        const shaderResult = solveCircuit(result.circuit, solverPerts.length > 0 ? solverPerts : null);
        const healthyResult = solveCircuit(result.circuit, null);
        const m = extractMetrics(shaderResult, result.circuit, healthyResult, solverPerts.length > 0 ? solverPerts : null);
        const mFull = {
          ...m,
          numNodes: result.circuit.numNodes,
          numEdges: result.circuit.numEdges,
          backend: shaderResult.backend || "cpu",
          renderTimeMs: shaderResult.renderTimeMs,
        };
        setMetrics(mFull);
        setCircuit(result.circuit);

        newLogs.push({ level: "log", message: `R (coherence): ${m.R?.toFixed(4)}` });
        newLogs.push({ level: "log", message: `V (visibility): ${m.V?.toFixed(4)}` });
        newLogs.push({ level: "info", message: `Solved on ${shaderResult.backend} in ${shaderResult.renderTimeMs?.toFixed(1)}ms` });

        if (result.perturbations?.length > 0) {
          newLogs.push({ level: "warn", message: `${result.perturbations.length} perturbation(s) active` });
        }
        if (result.observations?.length > 0) {
          newLogs.push({ level: "info", message: `${result.observations.length} observation(s)` });
        }
      } catch (e) {
        newErrors.push({ message: `Solver error: ${e.message}`, line: 0 });
        setMetrics(null);
        setCircuit(result.circuit);
      }
    } else {
      setCircuit(null);
      setMetrics(null);
    }

    setErrors(newErrors);
    setLogs(newLogs);
  }, [sources, activeFile]);

  // Auto-run on mount
  useEffect(() => { run(); }, []);

  // Debounced auto-run on edit
  useEffect(() => {
    const t = setTimeout(run, 500);
    return () => clearTimeout(t);
  }, [sources, activeFile]);

  // Ctrl+Enter to run
  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); run(); }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [run]);

  // Drag splitter
  useEffect(() => {
    const move = (e) => {
      if (!dragging.current || !splitRef.current) return;
      const r = splitRef.current.getBoundingClientRect();
      const pct = ((e.clientX - r.left) / r.width) * 100;
      setEditorWidth(Math.min(75, Math.max(25, pct)));
    };
    const up = () => { dragging.current = false; document.body.style.cursor = ""; };
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
    return () => { window.removeEventListener("mousemove", move); window.removeEventListener("mouseup", up); };
  }, []);

  const openFile = useCallback((name) => {
    if (!openTabs.includes(name)) setOpenTabs(prev => [...prev, name]);
    setActiveFile(name);
  }, [openTabs]);

  const closeTab = useCallback((name, e) => {
    e.stopPropagation();
    setOpenTabs(prev => {
      const next = prev.filter(t => t !== name);
      if (activeFile === name) setActiveFile(next.length ? next[next.length - 1] : null);
      return next;
    });
    setDirty(prev => { const n = new Set(prev); n.delete(name); return n; });
  }, [activeFile]);

  const updateContent = useCallback((val) => {
    setSources(prev => ({ ...prev, [activeFile]: val }));
    setDirty(prev => new Set(prev).add(activeFile));
  }, [activeFile]);

  const scriptInfo = SCRIPTS[activeFile];

  return (
    <div className="flex h-screen w-full flex-col overflow-hidden" style={{ background: theme.editor, color: theme.editorFg }}>
      {/* Title bar */}
      <div className="flex h-9 shrink-0 items-center justify-between px-4" style={{ background: theme.titlebar, borderBottom: `1px solid ${theme.border}` }}>
        <div className="flex items-center gap-3">
          <span className="font-mono text-[13px] font-bold" style={{ color: "#4ec9b0" }}>SBS</span>
          <span className="text-[12px]" style={{ color: "#888" }}>Systems Biology Shaders — Sandbox</span>
        </div>
        <div className="flex items-center gap-2 text-[11px]" style={{ color: "#888" }}>
          {scriptInfo && <span>{scriptInfo.name}</span>}
        </div>
      </div>

      <div className="flex min-h-0 flex-1">
        {/* Activity bar */}
        <div className="flex w-12 shrink-0 flex-col items-center py-2" style={{ background: theme.activitybar, borderRight: `1px solid ${theme.border}` }}>
          <button
            title="Explorer"
            onClick={() => setSidebar(s => !s)}
            className="flex h-11 w-12 items-center justify-center"
            style={{ color: sidebar ? theme.activitybarFgActive : theme.activitybarFg }}
          >
            <Files size={22} strokeWidth={1.5} />
          </button>
        </div>

        {/* Sidebar */}
        {sidebar && (
          <div className="flex w-56 shrink-0 flex-col overflow-hidden" style={{ background: theme.sidebar, borderRight: `1px solid ${theme.border}` }}>
            <div className="flex h-8 shrink-0 items-center px-4 text-[11px] font-medium uppercase tracking-wider" style={{ color: theme.sidebarHeader }}>
              Scripts
            </div>
            <div className="flex h-7 shrink-0 items-center gap-1 px-3 text-[12px]" style={{ color: theme.tabFg }}>
              <FolderOpen size={14} style={{ color: "#90a4ae" }} />
              <span>scripts</span>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto">
              <Tree scripts={SCRIPTS} activePath={activeFile} openFile={openFile} />
            </div>
          </div>
        )}

        {/* Editor + Output */}
        <div ref={splitRef} className="flex min-w-0 flex-1">
          {/* Editor column */}
          <div className="flex min-w-0 flex-col" style={{ width: `${editorWidth}%` }}>
            {/* Tabs */}
            <div className="flex h-9 shrink-0 items-stretch overflow-x-auto" style={{ background: theme.tabInactive }}>
              {openTabs.map(name => {
                const active = name === activeFile;
                const isDirty = dirty.has(name);
                return (
                  <div key={name} onClick={() => setActiveFile(name)}
                    className="group flex cursor-pointer items-center gap-2 border-r px-3 text-[13px]"
                    style={{
                      background: active ? theme.tabActive : theme.tabInactive,
                      color: active ? theme.tabFgActive : theme.tabFg,
                      borderColor: theme.border,
                      borderTop: active ? `1px solid ${theme.accentBright}` : "1px solid transparent",
                    }}>
                    <FileCode2 size={14} style={{ color: "#4ec9b0" }} />
                    <span className="whitespace-nowrap">{name}</span>
                    <button onClick={(e) => closeTab(name, e)} className="flex h-5 w-5 items-center justify-center rounded" style={{ color: active ? theme.tabFgActive : theme.tabFg }}>
                      {isDirty ? <Circle size={9} fill="currentColor" className="group-hover:hidden" /> : null}
                      <X size={14} className={isDirty ? "hidden group-hover:block" : "opacity-0 group-hover:opacity-100"} />
                    </button>
                  </div>
                );
              })}
            </div>

            {/* Breadcrumb */}
            {activeFile && (
              <div className="flex h-6 shrink-0 items-center gap-1 px-4 text-[12px]" style={{ background: theme.editor, color: theme.tabFg }}>
                <span className="flex items-center gap-1">
                  <Folder size={12} style={{ color: "#90a4ae" }} /> scripts
                  <ChevronRight size={12} className="opacity-60" />
                  {activeFile}
                </span>
                {scriptInfo && (
                  <span className="ml-3 text-[11px]" style={{ color: "#4a4a6a" }}>— {scriptInfo.description}</span>
                )}
              </div>
            )}

            {/* Editor */}
            {activeFile ? (
              <Editor value={source} onChange={updateContent} onCursor={setCursor} />
            ) : (
              <div className="flex min-h-0 flex-1 items-center justify-center text-sm" style={{ background: theme.editor, color: "#5a5a5a" }}>
                Select a script to start editing
              </div>
            )}

            {/* Bottom panel */}
            {panel && (
              <div className="flex h-32 shrink-0 flex-col" style={{ background: theme.panel, borderTop: `1px solid ${theme.border}` }}>
                <div className="flex h-8 items-center justify-between pr-2">
                  <div className="flex h-full items-center">
                    {[{ id: "problems", label: "Problems" }, { id: "terminal", label: "Terminal" }].map(({ id, label }) => {
                      const active = panelTab === id;
                      return (
                        <button key={id} onClick={() => setPanelTab(id)} className="relative h-full px-3 text-[11px] font-medium uppercase tracking-wider transition-colors" style={{ color: active ? theme.tabFgActive : theme.tabFg }}>
                          {label}
                          {active && <span className="absolute bottom-0 left-0 h-0.5 w-full" style={{ background: theme.accentBright }} />}
                        </button>
                      );
                    })}
                  </div>
                  <button onClick={() => setPanel(false)} style={{ color: theme.tabFg }}><PanelBottomClose size={14} /></button>
                </div>
                <div className="min-h-0 flex-1 overflow-y-auto px-3 pb-2 font-mono text-[12px] leading-relaxed">
                  {panelTab === "problems" ? (
                    errors.length === 0
                      ? <div className="flex items-center gap-2 pt-1" style={{ color: "#6a9955" }}><Check size={14} /> No problems detected.</div>
                      : errors.map((e, i) => (
                        <div key={i} className="flex items-center gap-2 py-0.5" style={{ color: "#f48771" }}>
                          <AlertCircle size={12} /> {e.message}
                        </div>
                      ))
                  ) : (
                    <div style={{ color: theme.editorFg }}>
                      <div><span style={{ color: "#4ec9b0" }}>sbs</span> <span style={{ color: "#888" }}>$</span> compile {activeFile}</div>
                      {logs.slice(0, 5).map((l, i) => (
                        <div key={i} style={{ color: l.level === "error" ? "#f48771" : l.level === "warn" ? "#dcdcaa" : "#9cdcfe" }}>{l.message}</div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Splitter */}
          <div
            onMouseDown={() => { dragging.current = true; document.body.style.cursor = "col-resize"; }}
            className="w-1 shrink-0 cursor-col-resize hover:opacity-100"
            style={{ background: theme.border }}
          />

          {/* Output */}
          <OutputColumn
            circuit={circuit} metrics={metrics} compiled={compiled}
            logs={logs} errors={errors}
            imports={imports} glbModel={glbModel}
            onRun={run} onClear={() => setLogs([])}
          />
        </div>
      </div>

      {/* Status bar */}
      <div className="flex h-6 shrink-0 items-center justify-between px-3 text-[12px]" style={{ background: theme.statusBar, color: theme.statusFg }}>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-1" onClick={() => setPanel(p => !p)}>
            <TerminalIcon size={13} /> {panel ? "Hide" : "Terminal"}
          </button>
          {errors.length > 0 && (
            <span className="flex items-center gap-1"><AlertCircle size={13} /> {errors.length}</span>
          )}
          {errors.length === 0 && (
            <span className="flex items-center gap-1"><Check size={13} /> 0 errors</span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span>Ln {cursor.ln}, Col {cursor.col}</span>
          <span>Spaces: 2</span>
          <span>SBS DSL</span>
        </div>
      </div>
    </div>
  );
}
