import { computeFluxPattern } from './shaderSolver';

export function extractMetrics(shaderResult, circuit, healthyBaseline, perturbation) {
  const texture = shaderResult.texture;
  const N = shaderResult.numNodes;

  const Se = [], Sk = [], St = [];
  for (let i = 0; i < N; i++) {
    Se.push(texture[i * 4 + 0]);
    Sk.push(texture[i * 4 + 1]);
    St.push(texture[i * 4 + 2]);
  }

  const R = tripleCoherence(Se, Sk, St);

  const fluxHealthy = computeFluxPattern(circuit, null);
  const fluxCurrent = computeFluxPattern(circuit, perturbation);
  const V = fluxVisibility(fluxHealthy, fluxCurrent);

  const fluxWeights = computeFluxWeights(fluxHealthy);
  const backwardPath = computeBackwardNavigation(circuit, perturbation);

  return {
    R,
    V,
    Se,
    Sk,
    St,
    fluxHealthy,
    fluxCurrent,
    fluxWeights,
    backwardPath,
    renderTimeMs: shaderResult.renderTimeMs,
    backend: shaderResult.backend,
  };
}

function spearmanRho(x, y) {
  const n = x.length;
  const rankX = computeRanks(x);
  const rankY = computeRanks(y);
  let dSq = 0;
  for (let i = 0; i < n; i++) {
    const d = rankX[i] - rankY[i];
    dSq += d * d;
  }
  return 1 - (6 * dSq) / (n * (n * n - 1));
}

function computeRanks(data) {
  const n = data.length;
  const indices = Array.from({ length: n }, (_, i) => i);
  indices.sort((a, b) => data[a] - data[b]);
  const ranks = new Array(n);
  for (let rank = 0; rank < n; rank++) {
    ranks[indices[rank]] = rank + 1;
  }
  return ranks;
}

export function tripleCoherence(Se, Sk, St) {
  const rhoEK = spearmanRho(Se, Sk);
  const rhoET = spearmanRho(Se, St);
  const rhoKT = spearmanRho(Sk, St);
  const meanRho = (rhoEK + rhoET + rhoKT) / 3;
  return (meanRho + 1) / 2; // map [-1,1] -> [0,1]
}

export function fluxVisibility(fluxHealthy, fluxTest) {
  const absH = fluxHealthy.map(Math.abs);
  const absT = fluxTest.map(Math.abs);
  const totalH = absH.reduce((a, b) => a + b, 0);
  if (totalH < 1e-20) return 0;

  let logV = 0;
  for (let k = 0; k < fluxHealthy.length; k++) {
    const wk = absH[k] / totalH;
    const a = absH[k], b = absT[k];
    let ratio;
    if (a > 1e-20 && b > 1e-20) {
      ratio = Math.min(a, b) / Math.max(a, b);
    } else if (a < 1e-20 && b < 1e-20) {
      ratio = 1.0;
    } else {
      ratio = 1e-10;
    }
    logV += wk * Math.log(Math.max(ratio, 1e-20));
  }
  return Math.exp(logV);
}

function computeFluxWeights(flux) {
  const abs = flux.map(Math.abs);
  const total = abs.reduce((a, b) => a + b, 0);
  if (total < 1e-20) return abs.map(() => 0);
  return abs.map(f => f / total);
}

export function computeBackwardNavigation(circuit, perturbation) {
  const { nodes, edges } = circuit;
  const pertMap = {};
  if (perturbation) {
    for (const p of perturbation) pertMap[p.idx] = p.factor;
  }

  const adj = {};
  for (const e of edges) {
    const G = e.conductance * (pertMap[e.id] ?? 1.0);
    if (!adj[e.dst]) adj[e.dst] = [];
    adj[e.dst].push({ from: e.src, conductance: G, edgeId: e.id });
  }

  const target = nodes.reduce((best, n) => n.mu > best.mu ? n : best, nodes[0]);

  const path = [target.id];
  const visited = new Set([target.id]);
  let current = target.id;

  for (let step = 0; step < nodes.length; step++) {
    const incoming = adj[current];
    if (!incoming || incoming.length === 0) break;

    const unvisited = incoming.filter(e => !visited.has(e.from));
    if (unvisited.length === 0) break;

    const best = unvisited.reduce((a, b) => a.conductance > b.conductance ? a : b);
    path.push(best.from);
    visited.add(best.from);
    current = best.from;
  }

  return path.map(id => ({
    nodeId: id,
    name: nodes[id].name,
    mu: nodes[id].mu,
  }));
}

export function findOptimalPerturbation(circuit, perturbation, maxEdges = 3) {
  const fluxHealthy = computeFluxPattern(circuit, null);
  const fluxWeights = computeFluxWeights(fluxHealthy);

  const sortedEdges = fluxWeights
    .map((w, i) => ({ idx: i, weight: w }))
    .sort((a, b) => b.weight - a.weight);

  const currentPert = perturbation ? [...perturbation] : [];
  const pertMap = {};
  for (const p of currentPert) pertMap[p.idx] = p.factor;

  const restoration = [];
  for (const edge of sortedEdges) {
    if (restoration.length >= maxEdges) break;
    const currentFactor = pertMap[edge.idx] ?? 1.0;
    if (Math.abs(currentFactor - 1.0) > 0.01) {
      restoration.push({ idx: edge.idx, factor: 1.0 / currentFactor });
    }
  }

  return restoration;
}
