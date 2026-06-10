import { tokenize } from './tokenizer';
import { parse } from './parser';
import { resolveImport } from './registry';

class Compiler {
  constructor() {
    this.errors = [];
    this.warnings = [];
    this.nodes = [];
    this.edges = [];
    this.variables = {};
    this.functions = {};
    this.perturbations = [];
    this.observations = [];
    this.catalysts = {};
    this.circuits = {};
    this.imports = {};
    this.glbModel = null;
  }

  compile(source) {
    this.errors = [];
    this.warnings = [];

    try {
      const tokens = tokenize(source);
      const ast = parse(tokens);
      const result = this.emit(ast);
      return {
        success: this.errors.length === 0,
        ast,
        result,
        circuit: this.buildCircuit(),
        perturbations: this.perturbations,
        observations: this.observations,
        imports: this.imports,
        glbModel: this.glbModel,
        errors: this.errors,
        warnings: this.warnings,
        glsl: this.emitGLSL(),
        js: this.emitJS(),
      };
    } catch (err) {
      this.errors.push({ message: err.message, line: err.line || 0 });
      return {
        success: false,
        errors: this.errors,
        warnings: this.warnings,
      };
    }
  }

  emit(node) {
    if (!node) return null;

    switch (node.type) {
      case 'Program':
        return node.body.map(s => this.emit(s));

      case 'CircuitDecl':
        const prevNodes = [...this.nodes];
        const prevEdges = [...this.edges];
        this.nodes = [];
        this.edges = [];
        node.body.forEach(s => this.emit(s));
        this.circuits[node.name] = {
          nodes: [...this.nodes],
          edges: [...this.edges],
        };
        if (prevNodes.length === 0 && prevEdges.length === 0) {
          return;
        }
        this.nodes = [...prevNodes, ...this.nodes];
        this.edges = [...prevEdges, ...this.edges];
        return;

      case 'NodeDecl':
        const nodeProps = this.evalProps(node.props);
        this.nodes.push({
          id: this.nodes.length,
          name: node.name,
          speciesId: node.name,
          compartment: nodeProps.compartment || 'cytoplasm',
          compartmentName: nodeProps.compartment || 'cytoplasm',
          concentration: nodeProps.concentration || 1.0,
          mu0: nodeProps.mu0 || nodeProps.potential || 0,
          mu: nodeProps.mu || nodeProps.potential || 0,
          boundary: nodeProps.boundary || false,
        });
        this.variables[node.name] = { type: 'node', index: this.nodes.length - 1 };
        return;

      case 'EdgeDecl':
        const edgeProps = this.evalProps(node.props);
        const srcIdx = this.findNode(node.src);
        const dstIdx = this.findNode(node.dst);
        if (srcIdx === -1) { this.errors.push({ message: `Unknown node '${node.src}'` }); return; }
        if (dstIdx === -1) { this.errors.push({ message: `Unknown node '${node.dst}'` }); return; }
        this.edges.push({
          id: this.edges.length,
          name: `${node.src}->${node.dst}`,
          reactionId: `${node.src}_${node.dst}`,
          src: srcIdx,
          dst: dstIdx,
          rate: edgeProps.rate || 1.0,
          conductance: edgeProps.conductance || edgeProps.rate || 1.0,
          deltaG: (this.nodes[srcIdx]?.mu || 0) - (this.nodes[dstIdx]?.mu || 0),
        });
        return;

      case 'LetDecl':
        this.variables[node.name] = { type: 'value', value: this.evalExpr(node.init) };
        return;

      case 'FnDecl':
        this.functions[node.name] = { params: node.params, body: node.body };
        return;

      case 'Observe':
        this.observations.push(this.evalExpr(node.target));
        return;

      case 'Perturb':
        const pertProps = this.evalProps(node.props);
        this.perturbations.push({
          target: this.evalExpr(node.target),
          factor: pertProps.factor || 0.1,
        });
        return;

      case 'Restore':
        this.perturbations = this.perturbations.filter(
          p => p.target !== this.evalExpr(node.target)
        );
        return;

      case 'Navigate':
        return { action: 'navigate', direction: node.direction, target: this.evalExpr(node.target) };

      case 'CatalystDecl':
        const catProps = this.evalProps(node.props);
        this.catalysts[node.name] = {
          power: catProps.power || 0.5,
          target: catProps.target || null,
        };
        return;

      case 'Cascade':
        const cascadePowers = node.catalysts.map(c => {
          const val = this.evalExpr(c);
          if (typeof val === 'string' && this.catalysts[val]) return this.catalysts[val].power;
          return typeof val === 'number' ? val : 0.5;
        });
        let composite = 1;
        for (const k of cascadePowers) composite *= (1 - k);
        return { catalyticPower: 1 - composite };

      case 'Convert':
        return { action: 'convert', expr: this.evalExpr(node.expr), from: node.from, to: node.to };

      case 'ForLoop':
        const iter = this.evalExpr(node.iterable);
        if (Array.isArray(iter)) {
          for (const item of iter) {
            this.variables[node.variable] = { type: 'value', value: item };
            node.body.forEach(s => this.emit(s));
          }
        }
        return;

      case 'IfStatement':
        if (this.evalExpr(node.condition)) {
          node.consequent.forEach(s => this.emit(s));
        } else if (node.alternate) {
          node.alternate.forEach(s => this.emit(s));
        }
        return;

      case 'ExpressionStatement':
        return this.evalExpr(node.expression);

      case 'Import':
        if (node.source) {
          const data = resolveImport(node.name, node.source);
          if (data) {
            this.imports[node.alias || node.name] = data;
            this.variables[node.alias || node.name] = { type: 'value', value: data };
            if (data.file) {
              this.glbModel = data;
            }
          } else {
            this.warnings.push({ message: `Unresolved import '${node.source}' — using as annotation`, line: 0 });
            this.variables[node.alias || node.name] = { type: 'value', value: { source: node.source, name: node.name } };
          }
        }
        return;

      case 'Export':
        return;

      default:
        return this.evalExpr(node);
    }
  }

  evalExpr(node) {
    if (!node) return null;

    switch (node.type) {
      case 'NumberLiteral': return node.value;
      case 'StringLiteral': return node.value;
      case 'BooleanLiteral': return node.value;

      case 'Identifier':
        if (this.variables[node.name]) {
          const v = this.variables[node.name];
          return v.type === 'node' ? node.name : v.value;
        }
        return node.name;

      case 'BuiltinRef':
        return `__builtin_${node.name}`;

      case 'TripleExpr':
        return { k: this.evalExpr(node.k), t: this.evalExpr(node.t), e: this.evalExpr(node.e) };

      case 'SEntropyLiteral':
        return { se: this.evalExpr(node.se), sk: this.evalExpr(node.sk), st: this.evalExpr(node.st) };

      case 'ArrayLiteral':
        return node.elements.map(e => this.evalExpr(e));

      case 'BinaryExpr': {
        const l = this.evalExpr(node.left);
        const r = this.evalExpr(node.right);
        switch (node.op) {
          case '+': return (typeof l === 'number' && typeof r === 'number') ? l + r : `${l} + ${r}`;
          case '-': return (typeof l === 'number' && typeof r === 'number') ? l - r : `${l} - ${r}`;
          case '*': return (typeof l === 'number' && typeof r === 'number') ? l * r : `${l} * ${r}`;
          case '/': return (typeof l === 'number' && typeof r === 'number') ? l / r : `${l} / ${r}`;
          case '%': return (typeof l === 'number' && typeof r === 'number') ? l % r : `${l} % ${r}`;
          case '**': return (typeof l === 'number' && typeof r === 'number') ? Math.pow(l, r) : `pow(${l}, ${r})`;
          case '==': return l === r;
          case '!=': return l !== r;
          case '<': return l < r;
          case '>': return l > r;
          case '<=': return l <= r;
          case '>=': return l >= r;
          case '&&': return l && r;
          case '||': return l || r;
          default: return `${l} ${node.op} ${r}`;
        }
      }

      case 'UnaryExpr': {
        const o = this.evalExpr(node.operand);
        if (node.op === '-') return typeof o === 'number' ? -o : `-${o}`;
        if (node.op === '!') return !o;
        return o;
      }

      case 'PipeExpr':
        return { type: 'pipe', input: this.evalExpr(node.left), fn: this.evalExpr(node.right) };

      case 'CallExpr': {
        const callee = this.evalExpr(node.callee);
        const args = node.args.map(a => this.evalExpr(a));
        if (typeof callee === 'string' && this.functions[callee]) {
          const fn = this.functions[callee];
          const prevVars = { ...this.variables };
          fn.params.forEach((p, i) => {
            this.variables[p] = { type: 'value', value: args[i] };
          });
          let result;
          for (const s of fn.body) {
            result = this.emit(s);
          }
          this.variables = prevVars;
          return result;
        }
        return { type: 'call', callee, args };
      }

      case 'MethodCall':
        return { type: 'method', object: this.evalExpr(node.object), method: node.method, args: node.args.map(a => this.evalExpr(a)) };

      case 'MemberExpr':
        return { type: 'member', object: this.evalExpr(node.object), property: node.property };

      case 'IndexExpr':
        return { type: 'index', object: this.evalExpr(node.object), index: this.evalExpr(node.index) };

      default:
        return null;
    }
  }

  evalProps(props) {
    const result = {};
    for (const [key, val] of Object.entries(props)) {
      result[key] = this.evalExpr(val);
    }
    return result;
  }

  findNode(name) {
    return this.nodes.findIndex(n => n.name === name || n.speciesId === name);
  }

  buildCircuit() {
    if (this.nodes.length === 0) return null;

    const RT = 2.478;
    const nodes = this.nodes.map((n, i) => ({
      ...n,
      id: i,
      mu: n.mu || (n.mu0 + RT * Math.log(Math.max(n.concentration, 1e-10))),
    }));
    const edges = this.edges.map((e, i) => {
      const srcNode = nodes[e.src];
      return {
        ...e,
        id: i,
        conductance: e.conductance || (e.rate * (srcNode?.concentration || 1) / RT),
        deltaG: (srcNode?.mu || 0) - (nodes[e.dst]?.mu || 0),
      };
    });

    return {
      nodes,
      edges,
      compartments: [...new Set(nodes.map(n => n.compartment))],
      modelId: 'dsl-circuit',
      numNodes: nodes.length,
      numEdges: edges.length,
    };
  }

  emitGLSL() {
    if (this.nodes.length === 0) return null;

    let glsl = `#version 300 es
precision highp float;

uniform sampler2D u_nodes;
uniform sampler2D u_edges;
uniform sampler2D u_perturbation;
uniform int u_numNodes;
uniform int u_numEdges;

in vec2 v_uv;
out vec4 fragColor;

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
    float mu = nd.r;

    float globalMuMin = 1e20, globalMuMax = -1e20;
    for (int n = 0; n < 256; n++) {
        if (n >= u_numNodes) break;
        float m = getNode(n).r;
        globalMuMin = min(globalMuMin, m);
        globalMuMax = max(globalMuMax, m);
    }

    float totalFlux = 0.0, weightedDegree = 0.0;
    float globalFluxMax = 0.0, globalDegreeMax = 0.0;

    for (int e = 0; e < 256; e++) {
        if (e >= u_numEdges) break;
        vec4 ed = getEdge(e);
        float G = ed.b * getPerturbation(e);
        float flux = G * abs(getNode(int(ed.r)).r - getNode(int(ed.g)).r);
        if (int(ed.r) == nodeIdx || int(ed.g) == nodeIdx) {
            totalFlux += flux;
            weightedDegree += G;
        }
    }

    for (int n = 0; n < 256; n++) {
        if (n >= u_numNodes) break;
        float nF = 0.0, nD = 0.0;
        for (int e = 0; e < 256; e++) {
            if (e >= u_numEdges) break;
            vec4 ed = getEdge(e);
            float G = ed.b * getPerturbation(e);
            float flux = G * abs(getNode(int(ed.r)).r - getNode(int(ed.g)).r);
            if (int(ed.r) == n || int(ed.g) == n) { nF += flux; nD += G; }
        }
        globalFluxMax = max(globalFluxMax, nF);
        globalDegreeMax = max(globalDegreeMax, nD);
    }

    float muRange = globalMuMax - globalMuMin;
    float Se = muRange > 0.0 ? (mu - globalMuMin) / muRange : 0.0;
    float Sk = globalFluxMax > 0.0 ? totalFlux / globalFluxMax : 0.0;
    float St = globalDegreeMax > 0.0 ? weightedDegree / globalDegreeMax : 0.0;

    fragColor = vec4(Se, Sk, St, 1.0);
}
`;
    return glsl;
  }

  emitJS() {
    const lines = [];
    lines.push('// Auto-generated from SBS DSL');
    lines.push(`const circuit = ${JSON.stringify(this.buildCircuit(), null, 2)};`);

    if (this.perturbations.length > 0) {
      lines.push(`const perturbations = ${JSON.stringify(this.perturbations, null, 2)};`);
    }

    lines.push('');
    lines.push('// Solve circuit');
    lines.push('import { solveCircuit } from "@/lib/sbs/shaderSolver";');
    lines.push('import { extractMetrics } from "@/lib/sbs/metricsExtractor";');
    lines.push('');
    lines.push('const result = solveCircuit(circuit, perturbations);');
    lines.push('const metrics = extractMetrics(circuit, result, null, perturbations);');
    lines.push('console.log("R:", metrics.R, "V:", metrics.V);');

    return lines.join('\n');
  }
}

export function compileSBS(source) {
  const compiler = new Compiler();
  return compiler.compile(source);
}

export function validateSBS(source) {
  try {
    const tokens = tokenize(source);
    parse(tokens);
    return { valid: true, errors: [] };
  } catch (err) {
    return { valid: false, errors: [{ message: err.message }] };
  }
}
