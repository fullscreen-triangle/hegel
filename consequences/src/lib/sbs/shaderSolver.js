import { OBSERVATION_VERT } from './shaders/observation.vert';
import { OBSERVATION_FRAG } from './shaders/observation.frag';

function mkShader(gl, type, src) {
  const s = gl.createShader(type);
  gl.shaderSource(s, src);
  gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
    console.error('Shader compile error:', gl.getShaderInfoLog(s));
    gl.deleteShader(s);
    return null;
  }
  return s;
}

function mkProg(gl, vsSrc, fsSrc) {
  const vs = mkShader(gl, gl.VERTEX_SHADER, vsSrc);
  const fs = mkShader(gl, gl.FRAGMENT_SHADER, fsSrc);
  if (!vs || !fs) return null;

  const p = gl.createProgram();
  gl.attachShader(p, vs);
  gl.attachShader(p, fs);
  gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
    console.error('Program link error:', gl.getProgramInfoLog(p));
    gl.deleteProgram(p);
    return null;
  }
  gl.deleteShader(vs);
  gl.deleteShader(fs);
  return p;
}

function makeQuad(gl) {
  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER,
    new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]),
    gl.STATIC_DRAW);
  return buf;
}

function createDataTexture(gl, data, width) {
  const tex = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA32F, width, 1, 0, gl.RGBA, gl.FLOAT, data);
  return tex;
}

function packNodes(nodes) {
  const data = new Float32Array(nodes.length * 4);
  for (let i = 0; i < nodes.length; i++) {
    data[i * 4 + 0] = nodes[i].mu;
    data[i * 4 + 1] = nodes[i].concentration;
    data[i * 4 + 2] = 0; // placeholder
    data[i * 4 + 3] = i; // compartment index placeholder
  }
  return data;
}

function packEdges(edges) {
  const data = new Float32Array(edges.length * 4);
  for (let i = 0; i < edges.length; i++) {
    data[i * 4 + 0] = edges[i].src;
    data[i * 4 + 1] = edges[i].dst;
    data[i * 4 + 2] = edges[i].conductance;
    data[i * 4 + 3] = edges[i].deltaG;
  }
  return data;
}

function packPerturbation(numEdges, perturbation) {
  const data = new Float32Array(numEdges * 4);
  for (let i = 0; i < numEdges; i++) {
    data[i * 4 + 0] = 1.0; // default: no perturbation
    data[i * 4 + 1] = 0;
    data[i * 4 + 2] = 0;
    data[i * 4 + 3] = 0;
  }
  if (perturbation) {
    for (const p of perturbation) {
      if (p.idx >= 0 && p.idx < numEdges) {
        data[p.idx * 4 + 0] = p.factor;
      }
    }
  }
  return data;
}

export function solveCircuit(circuit, perturbation = null) {
  const t0 = performance.now();

  const canvas = document.createElement('canvas');
  canvas.width = circuit.numNodes;
  canvas.height = 1;
  const gl = canvas.getContext('webgl2');
  if (!gl) throw new Error('WebGL2 not supported');

  const ext = gl.getExtension('EXT_color_buffer_float');
  if (!ext) {
    return solveCPU(circuit, perturbation);
  }

  const prog = mkProg(gl, OBSERVATION_VERT, OBSERVATION_FRAG);
  if (!prog) {
    return solveCPU(circuit, perturbation);
  }

  const quad = makeQuad(gl);

  const nodesTex = createDataTexture(gl, packNodes(circuit.nodes), circuit.numNodes);
  const edgesTex = createDataTexture(gl, packEdges(circuit.edges), circuit.numEdges);
  const pertTex = createDataTexture(gl, packPerturbation(circuit.numEdges, perturbation), circuit.numEdges);

  const fb = gl.createFramebuffer();
  const outTex = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, outTex);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA32F, circuit.numNodes, 1, 0, gl.RGBA, gl.FLOAT, null);
  gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, outTex, 0);

  gl.viewport(0, 0, circuit.numNodes, 1);
  gl.useProgram(prog);

  gl.activeTexture(gl.TEXTURE0);
  gl.bindTexture(gl.TEXTURE_2D, nodesTex);
  gl.uniform1i(gl.getUniformLocation(prog, 'u_nodes'), 0);

  gl.activeTexture(gl.TEXTURE1);
  gl.bindTexture(gl.TEXTURE_2D, edgesTex);
  gl.uniform1i(gl.getUniformLocation(prog, 'u_edges'), 1);

  gl.activeTexture(gl.TEXTURE2);
  gl.bindTexture(gl.TEXTURE_2D, pertTex);
  gl.uniform1i(gl.getUniformLocation(prog, 'u_perturbation'), 2);

  gl.uniform1i(gl.getUniformLocation(prog, 'u_numNodes'), circuit.numNodes);
  gl.uniform1i(gl.getUniformLocation(prog, 'u_numEdges'), circuit.numEdges);

  gl.bindBuffer(gl.ARRAY_BUFFER, quad);
  const aPos = gl.getAttribLocation(prog, 'a_pos');
  gl.enableVertexAttribArray(aPos);
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

  gl.drawArrays(gl.TRIANGLES, 0, 6);

  const pixels = new Float32Array(circuit.numNodes * 4);
  gl.readPixels(0, 0, circuit.numNodes, 1, gl.RGBA, gl.FLOAT, pixels);

  gl.deleteTexture(nodesTex);
  gl.deleteTexture(edgesTex);
  gl.deleteTexture(pertTex);
  gl.deleteTexture(outTex);
  gl.deleteFramebuffer(fb);
  gl.deleteBuffer(quad);
  gl.deleteProgram(prog);

  const renderTimeMs = performance.now() - t0;

  return {
    texture: pixels,
    renderTimeMs,
    numNodes: circuit.numNodes,
    backend: 'webgl2',
  };
}

export function solveCPU(circuit, perturbation = null) {
  const t0 = performance.now();
  const { nodes, edges } = circuit;
  const N = nodes.length;

  const pertMap = {};
  if (perturbation) {
    for (const p of perturbation) pertMap[p.idx] = p.factor;
  }

  const muVals = nodes.map(n => n.mu);
  const muMin = Math.min(...muVals);
  const muMax = Math.max(...muVals);
  const muRange = muMax - muMin || 1;

  const flux = new Array(N).fill(0);
  const degree = new Array(N).fill(0);

  for (const e of edges) {
    const G = e.conductance * (pertMap[e.id] ?? 1.0);
    const I = G * Math.abs(nodes[e.src].mu - nodes[e.dst].mu);
    flux[e.src] += I;
    flux[e.dst] += I;
    degree[e.src] += G;
    degree[e.dst] += G;
  }

  const fluxMax = Math.max(...flux) || 1;
  const degMax = Math.max(...degree) || 1;

  const texture = new Float32Array(N * 4);
  for (let i = 0; i < N; i++) {
    texture[i * 4 + 0] = (nodes[i].mu - muMin) / muRange;       // Se
    texture[i * 4 + 1] = flux[i] / fluxMax;                      // Sk
    texture[i * 4 + 2] = degree[i] / degMax;                     // St
    texture[i * 4 + 3] = 1.0;
  }

  return {
    texture,
    renderTimeMs: performance.now() - t0,
    numNodes: N,
    backend: 'cpu',
  };
}

export function computeFluxPattern(circuit, perturbation = null) {
  const { nodes, edges } = circuit;
  const pertMap = {};
  if (perturbation) {
    for (const p of perturbation) pertMap[p.idx] = p.factor;
  }

  return edges.map(e => {
    const G = e.conductance * (pertMap[e.id] ?? 1.0);
    return G * Math.abs(nodes[e.src].mu - nodes[e.dst].mu);
  });
}
