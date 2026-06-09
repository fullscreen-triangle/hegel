"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.emitGLSL = emitGLSL;
exports.emitJS = emitJS;
function emitGLSL(circuit) {
    const { nodes, edges, numNodes, numEdges } = circuit;
    const muValues = nodes.map(n => n.mu.toFixed(4)).join(', ');
    const edgeData = edges.map(e => `vec3(${e.src}.0, ${e.dst}.0, ${e.conductance.toFixed(4)})`).join(',\n    ');
    const muMin = Math.min(...nodes.map(n => n.mu));
    const muMax = Math.max(...nodes.map(n => n.mu));
    const muRange = muMax - muMin;
    return `#version 300 es
precision highp float;

// Auto-generated from SBS DSL
// ${numNodes} nodes, ${numEdges} edges

uniform sampler2D u_nodes;
uniform sampler2D u_edges;
uniform sampler2D u_perturbation;
uniform int u_numNodes;
uniform int u_numEdges;

in vec2 v_uv;
out vec4 fragColor;

// Hardcoded circuit data (for inspection)
const int NUM_NODES = ${numNodes};
const int NUM_EDGES = ${numEdges};
const float MU_MIN = ${muMin.toFixed(4)};
const float MU_RANGE = ${muRange.toFixed(4)};

const float mu[${numNodes}] = float[${numNodes}](${muValues});

const vec3 edgeData[${numEdges}] = vec3[${numEdges}](
    ${edgeData}
);

vec4 getNode(int idx) {
    return texture(u_nodes, vec2((float(idx) + 0.5) / float(u_numNodes), 0.5));
}

vec4 getEdge(int idx) {
    return texture(u_edges, vec2((float(idx) + 0.5) / float(u_numEdges), 0.5));
}

float getPerturbation(int idx) {
    return texture(u_perturbation, vec2((float(idx) + 0.5) / float(u_numEdges), 0.5)).r;
}

void main() {
    int nodeIdx = int(floor(v_uv.x * float(u_numNodes)));
    if (nodeIdx >= u_numNodes) { fragColor = vec4(0.0); return; }

    vec4 nd = getNode(nodeIdx);
    float nodeMu = nd.r;

    // Compute global normalization bounds
    float globalMuMin = 1e20, globalMuMax = -1e20;
    for (int n = 0; n < ${Math.min(numNodes, 256)}; n++) {
        if (n >= u_numNodes) break;
        float m = getNode(n).r;
        globalMuMin = min(globalMuMin, m);
        globalMuMax = max(globalMuMax, m);
    }

    // Compute per-node flux and degree
    float totalFlux = 0.0, weightedDegree = 0.0;
    float globalFluxMax = 0.0, globalDegreeMax = 0.0;

    for (int e = 0; e < ${Math.min(numEdges, 256)}; e++) {
        if (e >= u_numEdges) break;
        vec4 ed = getEdge(e);
        float G = ed.b * getPerturbation(e);
        float flux = G * abs(getNode(int(ed.r)).r - getNode(int(ed.g)).r);
        if (int(ed.r) == nodeIdx || int(ed.g) == nodeIdx) {
            totalFlux += flux;
            weightedDegree += G;
        }
    }

    // Global max pass
    for (int n = 0; n < ${Math.min(numNodes, 256)}; n++) {
        if (n >= u_numNodes) break;
        float nF = 0.0, nD = 0.0;
        for (int e = 0; e < ${Math.min(numEdges, 256)}; e++) {
            if (e >= u_numEdges) break;
            vec4 ed = getEdge(e);
            float G = ed.b * getPerturbation(e);
            float flux = G * abs(getNode(int(ed.r)).r - getNode(int(ed.g)).r);
            if (int(ed.r) == n || int(ed.g) == n) { nF += flux; nD += G; }
        }
        globalFluxMax = max(globalFluxMax, nF);
        globalDegreeMax = max(globalDegreeMax, nD);
    }

    // Normalize to S-entropy triple
    float muRng = globalMuMax - globalMuMin;
    float Se = muRng > 0.0 ? (nodeMu - globalMuMin) / muRng : 0.0;
    float Sk = globalFluxMax > 0.0 ? totalFlux / globalFluxMax : 0.0;
    float St = globalDegreeMax > 0.0 ? weightedDegree / globalDegreeMax : 0.0;

    fragColor = vec4(Se, Sk, St, 1.0);
}
`;
}
function emitJS(circuit, perturbations) {
    const lines = [];
    lines.push('// Auto-generated from SBS DSL');
    lines.push('');
    lines.push(`const circuit = ${JSON.stringify(circuit, null, 2)};`);
    lines.push('');
    if (perturbations.length > 0) {
        lines.push(`const perturbations = ${JSON.stringify(perturbations, null, 2)};`);
        lines.push('');
    }
    lines.push('// Solve');
    lines.push('import { solveCircuit } from "@/lib/sbs/shaderSolver";');
    lines.push('import { extractMetrics } from "@/lib/sbs/metricsExtractor";');
    lines.push('');
    lines.push(`const perturbation = ${perturbations.length > 0 ? 'perturbations' : 'null'};`);
    lines.push('const healthy = solveCircuit(circuit, null);');
    lines.push('const result = solveCircuit(circuit, perturbation);');
    lines.push('const metrics = extractMetrics(result, circuit, healthy, perturbation);');
    lines.push('');
    lines.push('console.log("R:", metrics.R.toFixed(4));');
    lines.push('console.log("V:", metrics.V.toFixed(4));');
    return lines.join('\n');
}
//# sourceMappingURL=codegen.js.map