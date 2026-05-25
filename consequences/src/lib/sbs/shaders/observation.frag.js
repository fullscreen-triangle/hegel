export const OBSERVATION_FRAG = `#version 300 es
precision highp float;

uniform sampler2D u_nodes;
uniform sampler2D u_edges;
uniform sampler2D u_perturbation;
uniform int u_numNodes;
uniform int u_numEdges;

in vec2 v_uv;
out vec4 fragColor;

// Fetch node data: RGBA = [mu, concentration, degree_placeholder, compartmentIdx]
vec4 getNode(int idx) {
    float u = (float(idx) + 0.5) / float(u_numNodes);
    return texture(u_nodes, vec2(u, 0.5));
}

// Fetch edge data: RGBA = [srcIdx, dstIdx, conductance, deltaG]
vec4 getEdge(int idx) {
    float u = (float(idx) + 0.5) / float(u_numEdges);
    return texture(u_edges, vec2(u, 0.5));
}

// Fetch perturbation multiplier for edge
float getPerturbation(int idx) {
    float u = (float(idx) + 0.5) / float(u_numEdges);
    return texture(u_perturbation, vec2(u, 0.5)).r;
}

void main() {
    int nodeIdx = int(floor(v_uv.x * float(u_numNodes)));
    if (nodeIdx >= u_numNodes) {
        fragColor = vec4(0.0);
        return;
    }

    vec4 nodeData = getNode(nodeIdx);
    float mu = nodeData.r;

    // Compute flux magnitude and weighted degree for this node
    float totalFlux = 0.0;
    float weightedDegree = 0.0;
    float globalMuMin = 1e20;
    float globalMuMax = -1e20;
    float globalFluxMax = 0.0;
    float globalDegreeMax = 0.0;

    // First pass: find global ranges across all nodes
    for (int n = 0; n < 256; n++) {
        if (n >= u_numNodes) break;
        vec4 nd = getNode(n);
        globalMuMin = min(globalMuMin, nd.r);
        globalMuMax = max(globalMuMax, nd.r);
    }

    // Compute per-node flux and degree
    for (int e = 0; e < 256; e++) {
        if (e >= u_numEdges) break;
        vec4 ed = getEdge(e);
        int src = int(ed.r);
        int dst = int(ed.g);
        float G = ed.b * getPerturbation(e);
        float srcMu = getNode(src).r;
        float dstMu = getNode(dst).r;
        float flux = G * abs(srcMu - dstMu);

        if (src == nodeIdx || dst == nodeIdx) {
            totalFlux += flux;
            weightedDegree += G;
        }
    }

    // Compute all-node flux and degree for normalization
    for (int n = 0; n < 256; n++) {
        if (n >= u_numNodes) break;
        float nFlux = 0.0;
        float nDeg = 0.0;
        for (int e = 0; e < 256; e++) {
            if (e >= u_numEdges) break;
            vec4 ed = getEdge(e);
            int src = int(ed.r);
            int dst = int(ed.g);
            float G = ed.b * getPerturbation(e);
            float srcMu = getNode(src).r;
            float dstMu = getNode(dst).r;
            float flux = G * abs(srcMu - dstMu);
            if (src == n || dst == n) {
                nFlux += flux;
                nDeg += G;
            }
        }
        globalFluxMax = max(globalFluxMax, nFlux);
        globalDegreeMax = max(globalDegreeMax, nDeg);
    }

    // S-entropy triple
    float muRange = globalMuMax - globalMuMin;
    float Se = muRange > 0.0 ? (mu - globalMuMin) / muRange : 0.0;
    float Sk = globalFluxMax > 0.0 ? totalFlux / globalFluxMax : 0.0;
    float St = globalDegreeMax > 0.0 ? weightedDegree / globalDegreeMax : 0.0;

    fragColor = vec4(Se, Sk, St, 1.0);
}
`;
