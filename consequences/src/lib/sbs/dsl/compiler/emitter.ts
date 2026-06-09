import {
  ASTNode, Expression, Program,
  CircuitNode, CircuitEdge, Circuit,
  Perturbation, CatalystInfo, CompileError,
} from './types';

const RT = 2.478; // kJ/mol at 298K

type RuntimePrimitive = number | string | boolean | null;
type RuntimeValue = RuntimePrimitive | RuntimeValue[] | { [key: string]: RuntimeValue };

interface VariableEntry {
  kind: 'node' | 'value';
  index?: number;
  value?: RuntimeValue;
}

interface FunctionEntry {
  params: string[];
  body: ASTNode[];
}

interface CircuitScope {
  nodes: CircuitNode[];
  edges: CircuitEdge[];
}

export class Emitter {
  private nodes: CircuitNode[] = [];
  private edges: CircuitEdge[] = [];
  private variables: Map<string, VariableEntry> = new Map();
  private functions: Map<string, FunctionEntry> = new Map();
  private catalysts: Map<string, CatalystInfo> = new Map();
  private circuits: Map<string, CircuitScope> = new Map();

  readonly perturbations: Perturbation[] = [];
  readonly observations: string[] = [];
  readonly errors: CompileError[] = [];
  readonly warnings: CompileError[] = [];

  emit(program: Program): void {
    for (const stmt of program.body) {
      this.emitNode(stmt);
    }
  }

  buildCircuit(): Circuit | null {
    if (this.nodes.length === 0) return null;

    const nodes = this.nodes.map((n, i) => {
      const mu = n.mu !== 0
        ? n.mu
        : n.mu0 + RT * Math.log(Math.max(n.concentration, 1e-10));
      return { ...n, id: i, mu };
    });

    const edges = this.edges.map((e, i) => {
      const srcNode = nodes[e.src];
      const dstNode = nodes[e.dst];
      const conductance = e.conductance > 0
        ? e.conductance
        : e.rate * (srcNode?.concentration ?? 1) / RT;
      const deltaG = (srcNode?.mu ?? 0) - (dstNode?.mu ?? 0);
      return { ...e, id: i, conductance, deltaG };
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

  private emitNode(node: ASTNode): RuntimeValue {
    switch (node.type) {
      case 'Program':
        for (const s of node.body) this.emitNode(s);
        return null;

      case 'CircuitDecl': {
        const prevNodes = [...this.nodes];
        const prevEdges = [...this.edges];
        this.nodes = [];
        this.edges = [];
        for (const s of node.body) this.emitNode(s);
        this.circuits.set(node.name, {
          nodes: [...this.nodes],
          edges: [...this.edges],
        });
        if (prevNodes.length === 0 && prevEdges.length === 0) {
          return null;
        }
        this.nodes = [...prevNodes, ...this.nodes];
        this.edges = [...prevEdges, ...this.edges];
        return null;
      }

      case 'NodeDecl': {
        const props = this.evalProps(node.props);
        const mu0 = toNumber(props.mu0 ?? props.mu ?? 0);
        const concentration = toNumber(props.concentration ?? 1.0);
        const muDirect = toNumber(props.mu ?? 0);
        const mu = props.mu0 !== undefined
          ? mu0 + RT * Math.log(Math.max(concentration, 1e-10))
          : muDirect;

        const circuitNode: CircuitNode = {
          id: this.nodes.length,
          name: node.name,
          speciesId: node.name,
          compartment: toString(props.compartment ?? 'cytoplasm'),
          compartmentName: toString(props.compartment ?? 'cytoplasm'),
          concentration,
          mu0,
          mu,
          boundary: toBool(props.boundary ?? false),
        };
        this.nodes.push(circuitNode);
        this.variables.set(node.name, { kind: 'node', index: this.nodes.length - 1 });
        return null;
      }

      case 'EdgeDecl': {
        const props = this.evalProps(node.props);
        const srcIdx = this.findNode(node.src);
        const dstIdx = this.findNode(node.dst);
        if (srcIdx === -1) {
          this.errors.push({ message: `Edge references undefined node '${node.src}'`, line: 0 });
          return null;
        }
        if (dstIdx === -1) {
          this.errors.push({ message: `Edge references undefined node '${node.dst}'`, line: 0 });
          return null;
        }

        const rate = toNumber(props.rate ?? 1.0);
        const conductance = toNumber(props.conductance ?? 0);
        const srcNode = this.nodes[srcIdx];
        const dstNode = this.nodes[dstIdx];

        this.edges.push({
          id: this.edges.length,
          name: `${node.src}->${node.dst}`,
          reactionId: `${node.src}_${node.dst}`,
          src: srcIdx,
          dst: dstIdx,
          rate,
          conductance: conductance > 0 ? conductance : rate * (srcNode?.concentration ?? 1) / RT,
          deltaG: (srcNode?.mu ?? 0) - (dstNode?.mu ?? 0),
        });
        return null;
      }

      case 'LetDecl': {
        const value = this.evalExpr(node.init);
        this.variables.set(node.name, { kind: 'value', value });
        return null;
      }

      case 'FnDecl':
        this.functions.set(node.name, { params: node.params, body: node.body });
        return null;

      case 'Observe': {
        const target = this.evalExpr(node.target);
        this.observations.push(toString(target));
        return null;
      }

      case 'Perturb': {
        const target = this.evalExpr(node.target);
        const props = this.evalProps(node.props);
        this.perturbations.push({
          target: toString(target),
          factor: toNumber(props.factor ?? 0.1),
          edge: props.edge !== undefined ? toString(props.edge) : undefined,
        });
        return null;
      }

      case 'Restore': {
        const target = toString(this.evalExpr(node.target));
        const idx = this.perturbations.findIndex(p => p.target === target);
        if (idx !== -1) this.perturbations.splice(idx, 1);
        return null;
      }

      case 'Navigate':
        return {
          action: 'navigate',
          direction: node.direction,
          target: this.evalExpr(node.target),
        } as unknown as RuntimeValue;

      case 'CatalystDecl': {
        const props = this.evalProps(node.props);
        const power = toNumber(props.power ?? 0.5);
        if (power < 0 || power > 1) {
          this.errors.push({ message: `Catalyst power must be in [0, 1], got ${power}`, line: 0 });
        }
        this.catalysts.set(node.name, {
          power,
          target: props.target !== undefined ? toString(props.target) : null,
        });
        return null;
      }

      case 'Cascade': {
        const powers: number[] = node.catalysts.map(c => {
          const val = this.evalExpr(c);
          if (typeof val === 'string' && this.catalysts.has(val)) {
            return this.catalysts.get(val)!.power;
          }
          return typeof val === 'number' ? val : 0.5;
        });
        let residual = 1;
        for (const k of powers) residual *= (1 - k);
        return 1 - residual;
      }

      case 'Convert':
        return {
          action: 'convert',
          expr: this.evalExpr(node.expr),
          from: node.from,
          to: node.to,
        } as unknown as RuntimeValue;

      case 'ForLoop': {
        const iter = this.evalExpr(node.iterable);
        if (Array.isArray(iter)) {
          for (const item of iter) {
            this.variables.set(node.variable, { kind: 'value', value: item as RuntimeValue });
            for (const s of node.body) this.emitNode(s);
          }
        }
        return null;
      }

      case 'IfStatement': {
        const cond = this.evalExpr(node.condition);
        if (cond) {
          for (const s of node.consequent) this.emitNode(s);
        } else if (node.alternate) {
          for (const s of node.alternate) this.emitNode(s);
        }
        return null;
      }

      case 'ExpressionStatement':
        return this.evalExpr(node.expression);

      case 'Import':
      case 'Export':
        return null;

      default:
        return null;
    }
  }

  private evalExpr(node: Expression): RuntimeValue {
    switch (node.type) {
      case 'NumberLiteral': return node.value;
      case 'StringLiteral': return node.value;
      case 'BooleanLiteral': return node.value;

      case 'Identifier': {
        const entry = this.variables.get(node.name);
        if (entry) {
          return entry.kind === 'node' ? node.name : (entry.value ?? null);
        }
        return node.name;
      }

      case 'BuiltinRef':
        return `__builtin_${node.name}`;

      case 'TripleExpr':
        return {
          k: this.evalExpr(node.k),
          t: this.evalExpr(node.t),
          e: this.evalExpr(node.e),
        } as unknown as RuntimeValue;

      case 'SEntropyLiteral':
        return {
          se: this.evalExpr(node.se),
          sk: this.evalExpr(node.sk),
          st: this.evalExpr(node.st),
        } as unknown as RuntimeValue;

      case 'ArrayLiteral':
        return node.elements.map(e => this.evalExpr(e));

      case 'BinaryExpr': {
        const l = this.evalExpr(node.left);
        const r = this.evalExpr(node.right);
        if (typeof l === 'number' && typeof r === 'number') {
          switch (node.op) {
            case '+': return l + r;
            case '-': return l - r;
            case '*': return l * r;
            case '/': return r !== 0 ? l / r : (this.warnings.push({ message: 'Division by zero', line: 0 }), 0);
            case '%': return l % r;
            case '**': return Math.pow(l, r);
            case '==': return l === r;
            case '!=': return l !== r;
            case '<': return l < r;
            case '>': return l > r;
            case '<=': return l <= r;
            case '>=': return l >= r;
          }
        }
        switch (node.op) {
          case '&&': return l && r;
          case '||': return l || r;
          case '==': return l === r;
          case '!=': return l !== r;
          case '+': return `${l} + ${r}`;
        }
        return `${l} ${node.op} ${r}`;
      }

      case 'UnaryExpr': {
        const o = this.evalExpr(node.operand);
        if (node.op === '-') return typeof o === 'number' ? -o : `-${o}`;
        if (node.op === '!') return !o;
        return o;
      }

      case 'PipeExpr':
        return {
          type: 'pipe',
          input: this.evalExpr(node.left),
          fn: this.evalExpr(node.right),
        } as unknown as RuntimeValue;

      case 'CallExpr': {
        const callee = this.evalExpr(node.callee);
        const args = node.args.map(a => this.evalExpr(a));
        if (typeof callee === 'string' && this.functions.has(callee)) {
          const fn = this.functions.get(callee)!;
          const saved = new Map(this.variables);
          fn.params.forEach((p, i) => {
            this.variables.set(p, { kind: 'value', value: args[i] ?? null });
          });
          let result: RuntimeValue = null;
          for (const s of fn.body) {
            result = this.emitNode(s);
          }
          this.variables = saved;
          return result;
        }
        return { type: 'call', callee, args } as unknown as RuntimeValue;
      }

      case 'MethodCall':
        return {
          type: 'method',
          object: this.evalExpr(node.object),
          method: node.method,
          args: node.args.map(a => this.evalExpr(a)),
        } as unknown as RuntimeValue;

      case 'MemberExpr':
        return {
          type: 'member',
          object: this.evalExpr(node.object),
          property: node.property,
        } as unknown as RuntimeValue;

      case 'IndexExpr':
        return {
          type: 'index',
          object: this.evalExpr(node.object),
          index: this.evalExpr(node.index),
        } as unknown as RuntimeValue;

      default:
        return null;
    }
  }

  private evalProps(props: Record<string, Expression>): Record<string, RuntimeValue> {
    const result: Record<string, RuntimeValue> = {};
    for (const [key, val] of Object.entries(props)) {
      result[key] = this.evalExpr(val);
    }
    return result;
  }

  private findNode(name: string): number {
    return this.nodes.findIndex(n => n.name === name || n.speciesId === name);
  }
}

function toNumber(v: RuntimeValue): number {
  if (typeof v === 'number') return v;
  if (typeof v === 'string') return parseFloat(v) || 0;
  return 0;
}

function toString(v: RuntimeValue): string {
  if (typeof v === 'string') return v;
  if (v === null || v === undefined) return '';
  return String(v);
}

function toBool(v: RuntimeValue): boolean {
  return !!v;
}
