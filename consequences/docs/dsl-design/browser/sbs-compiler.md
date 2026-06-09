# SBS Browser Tool — Compiler Design

## 1. Design Philosophy

The SBS DSL is **declarative and evidence-based**, not imperative. It follows the same principles as the Kwasa-kwasa text processing DSL:

- **Circuits are declared, not constructed** — you state what exists, not how to build it
- **Observation is a single operation** — the shader runs once, no time-stepping
- **Perturbation is evidence** — you state what changed, the system computes the consequences
- **Catalysts compose multiplicatively** — `cascade(a, b)` is a declaration of composition, not a procedure
- **The triple (Se, Sk, St) is always available** — every circuit has these metrics after observation
- **No hidden state** — the circuit is the state, the shader result is the measurement

The DSL is closest to the "Points and Resolutions" pattern from Kwasa-kwasa: each observation is a measurement point, each perturbation is evidence, and the metrics (R, V) are the resolution.

---

## 2. Grammar Specification

### 2.1 Notation

```
UPPER_CASE  = terminal token type
'literal'   = literal string
[x]         = optional
{x}         = zero or more
x | y       = alternation
```

### 2.2 Top-Level

```
Program        = { Statement }

Statement      = CircuitDecl
               | NodeDecl
               | EdgeDecl
               | LetDecl
               | FnDecl
               | ObserveStmt
               | PerturbStmt
               | RestoreStmt
               | NavigateStmt
               | CatalystDecl
               | CascadeStmt
               | ConvertStmt
               | ForLoop
               | IfStatement
               | ImportStmt
               | ExportStmt
               | ExpressionStatement
```

### 2.3 Circuit Declaration

```
CircuitDecl    = 'circuit' IDENT '{' { Statement } '}'
```

Circuits are namespaces. Nodes and edges declared inside belong to that circuit. Multiple circuits can coexist.

```sbs
circuit glycolysis {
  node Glucose { mu: -917.0, concentration: 5.0, compartment: "cytoplasm" }
  node G6P     { mu: -1760.0, concentration: 0.083 }
  edge Glucose -> G6P { rate: 230.0, conductance: 464.1 }
}
```

### 2.4 Node Declaration

```
NodeDecl       = 'node' IDENT PropBlock
PropBlock      = '{' PropList '}'
PropList       = Prop { ',' Prop }
Prop           = IDENT ':' Expression
```

**Required properties**: `mu` (chemical potential in kJ/mol)

**Optional properties**:
| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `mu` | number | — | Chemical potential mu (kJ/mol) |
| `concentration` | number | 1.0 | Molar concentration [C] |
| `mu0` | number | `mu` | Standard chemical potential mu-zero |
| `compartment` | string | `"cytoplasm"` | GO compartment name |
| `boundary` | boolean | `false` | Boundary condition flag |

The actual chemical potential is computed as: `mu = mu0 + RT * ln(concentration)` where `RT = 2.478 kJ/mol` at 298K. If only `mu` is provided, it is used directly. If `mu0` and `concentration` are both provided, `mu` is computed from them.

### 2.5 Edge Declaration

```
EdgeDecl       = 'edge' IDENT '->' IDENT PropBlock
```

**Properties**:
| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `conductance` | number | — | Electrical conductance G |
| `rate` | number | — | Kinetic rate constant k |
| `deltaG` | number | computed | Driving force mu_src - mu_dst |

If `rate` is given and `conductance` is not, conductance is computed: `G = rate * concentration_src / RT`.

### 2.6 Observation

```
ObserveStmt    = 'observe' IDENT
```

Runs the observation shader on the named circuit. After this statement, the built-in variables `R`, `V`, `Se`, `Sk`, `St` are populated with the results.

This is the central operation. It corresponds to "the fragment shader evaluation IS the physical measurement." There is no time parameter, no iteration count, no convergence criterion. One pass.

### 2.7 Perturbation

```
PerturbStmt    = 'perturb' IDENT PropBlock
```

Modifies edge conductances by a multiplicative factor. The `factor` property applies to all edges, or specific edges can be targeted:

```sbs
// Perturb all edges in glycolysis by 10%
perturb glycolysis { factor: 0.1 }

// Perturb specific edge
perturb glycolysis { edge: "Hexokinase", factor: 0.1 }
```

### 2.8 Restore

```
RestoreStmt    = 'restore' IDENT
```

Computes the l1-optimal perturbation that restores flux visibility V > 0.9. Uses `findOptimalPerturbation()` from metricsExtractor.

### 2.9 Navigate

```
NavigateStmt   = 'navigate' 'from' IDENT
```

Traces backward from the named node through the circuit, following highest-conductance incoming edges. Uses `computeBackwardNavigation()`.

### 2.10 Catalyst Declaration

```
CatalystDecl   = 'catalyst' IDENT PropBlock
```

**Properties**:
| Property | Type | Range | Description |
|----------|------|-------|-------------|
| `power` | number | [0, 1] | Catalytic power kappa |

### 2.11 Cascade

```
CascadeStmt    = 'cascade' '(' IDENT { ',' IDENT } ')'
```

Composes catalysts multiplicatively: `kappa_12 = 1 - (1 - kappa_1)(1 - kappa_2)`.

The cascade also computes the convergence series `(1 - kappa)^n` for `n = 0..20` and makes it available for charting.

### 2.12 Convert (Triple Equivalence)

```
ConvertStmt    = 'convert' IDENT 'from' RepType 'to' RepType
RepType        = 'osc' | 'cat' | 'part'
```

Converts between the three representations from the Triple Equivalence theorem:
- `osc` — Oscillatory (default)
- `cat` — Categorical
- `part` — Partition

The S-entropy triple (Se, Sk, St) is invariant under conversion (Corollary 2.3).

### 2.13 Let Binding

```
LetDecl        = 'let' IDENT '=' Expression
```

Binds a name to a value. The value is computed at compile time if possible, otherwise deferred to runtime.

### 2.14 Function Declaration

```
FnDecl         = 'fn' IDENT '(' [ParamList] ')' '{' { Statement } '}'
ParamList      = IDENT { ',' IDENT }
```

### 2.15 Control Flow

```
ForLoop        = 'for' IDENT 'in' Expression '{' { Statement } '}'
IfStatement    = 'if' Expression '{' { Statement } '}' ['else' '{' { Statement } '}']
```

### 2.16 Import / Export

```
ImportStmt     = 'import' IDENT ['as' IDENT] 'from' STRING
ExportStmt     = 'export' IDENT
```

Import loads a circuit definition from a URL or pathway ID:

```sbs
import glycolysis from "reactome:R-HSA-70171"
import tca from "kegg:path:hsa00020"
```

### 2.17 Expressions

```
Expression     = PipeExpr
PipeExpr       = CompareExpr { '|>' CallExpr }
CompareExpr    = AddExpr { ('==' | '!=' | '<' | '>' | '<=' | '>=') AddExpr }
AddExpr        = MulExpr { ('+' | '-') MulExpr }
MulExpr        = UnaryExpr { ('*' | '/' | '%') UnaryExpr }
UnaryExpr      = ['-' | '!'] PostfixExpr
PostfixExpr    = Primary { '.' IDENT | '(' [ArgList] ')' | '[' Expression ']' }
Primary        = NumberLiteral
               | StringLiteral
               | BooleanLiteral
               | Identifier
               | TripleLiteral
               | SEntropyLiteral
               | ArrayLiteral
               | '(' Expression ')'

TripleLiteral  = 'triple' '(' Expression ',' Expression ',' Expression ')'
SEntropyLiteral = '#' '(' Expression ',' Expression ',' Expression ')'
ArrayLiteral   = '[' [Expression { ',' Expression }] ']'
```

### 2.18 Built-in References

After an `observe` statement, these names are bound:

| Name | Type | Description |
|------|------|-------------|
| `R` | number | Triple coherence [0, 1] |
| `V` | number | Flux visibility (0, 1] |
| `Se` | number[] | Normalized chemical potentials |
| `Sk` | number[] | Normalized flux magnitudes |
| `St` | number[] | Normalized weighted degrees |
| `floor` | number | S_floor > 0 (bounded receiver theorem) |

### 2.19 Pipe Operator

The `|>` operator threads the left-hand value as the first argument to the right-hand function:

```sbs
observe glycolysis |> perturb { factor: 0.1 } |> restore
```

---

## 3. Token Types

| Type | Examples | Regex/Pattern |
|------|----------|---------------|
| `KEYWORD` | `circuit`, `node`, `edge`, `observe`, ... | See keyword set |
| `IDENT` | `Glucose`, `myVar`, `alpha_kg` | `[a-zA-Z_][a-zA-Z0-9_]*` |
| `NUMBER` | `3.14`, `1e-5`, `0.001` | `[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?` |
| `STRING` | `"cytoplasm"`, `'membrane'` | `"..."` or `'...'` |
| `OP` | `+`, `-`, `*`, `/`, `==`, `!=`, `<=`, `>=` | Single/double char |
| `PUNC` | `(`, `)`, `{`, `}`, `[`, `]`, `:`, `;`, `,`, `.`, `@`, `#` | Single char |
| `ARROW` | `->`, `<-` | Two char |
| `PIPE` | `\|>` | Two char |
| `EOF` | — | End of input |

### Keyword Set (23 core + 9 type/representation)

```
circuit  node  edge  let  fn  return
observe  perturb  restore  navigate
Se  Sk  St  R  V
triple  catalyst  compose  cascade
floor  coherence  visibility
for  in  if  else  true  false
import  export  as
osc  cat  part
convert  from  to
```

### Comments

```sbs
// Single-line comment
/* Multi-line
   comment */
```

---

## 4. AST Node Types

### 4.1 Statements

```typescript
// (Types shown for documentation only — implementation is plain JS objects)

CircuitDecl     { type: "CircuitDecl", name: string, body: Statement[] }
NodeDecl        { type: "NodeDecl", name: string, props: Prop[] }
EdgeDecl        { type: "EdgeDecl", src: string, dst: string, props: Prop[] }
LetDecl         { type: "LetDecl", name: string, value: Expression }
FnDecl          { type: "FnDecl", name: string, params: string[], body: Statement[] }
ObserveStmt     { type: "Observe", target: string }
PerturbStmt     { type: "Perturb", target: string, props: Prop[] }
RestoreStmt     { type: "Restore", target: string }
NavigateStmt    { type: "Navigate", target: string }
CatalystDecl    { type: "CatalystDecl", name: string, props: Prop[] }
CascadeStmt     { type: "Cascade", catalysts: string[] }
ConvertStmt     { type: "Convert", target: string, from: string, to: string }
ForLoop         { type: "ForLoop", variable: string, iterable: Expression, body: Statement[] }
IfStatement     { type: "IfStatement", condition: Expression, consequent: Statement[], alternate: Statement[] | null }
ImportStmt      { type: "Import", name: string, alias: string | null, source: string }
ExportStmt      { type: "Export", name: string }
ExprStmt        { type: "ExpressionStatement", expression: Expression }
```

### 4.2 Expressions

```
PipeExpr        { type: "PipeExpr", left: Expression, right: Expression }
BinaryExpr      { type: "BinaryExpr", op: string, left: Expression, right: Expression }
UnaryExpr       { type: "UnaryExpr", op: string, operand: Expression }
CallExpr        { type: "CallExpr", callee: Expression, args: Expression[] }
MemberExpr      { type: "MemberExpr", object: Expression, property: string }
IndexExpr       { type: "IndexExpr", object: Expression, index: Expression }
TripleExpr      { type: "TripleExpr", k: Expression, t: Expression, e: Expression }
SEntropyLiteral { type: "SEntropyLiteral", se: Expression, sk: Expression, st: Expression }
ArrayLiteral    { type: "ArrayLiteral", elements: Expression[] }
Identifier      { type: "Identifier", name: string }
NumberLiteral   { type: "NumberLiteral", value: number }
StringLiteral   { type: "StringLiteral", value: string }
BooleanLiteral  { type: "BooleanLiteral", value: boolean }
```

### 4.3 Property

```
Prop            { key: string, value: Expression }
```

---

## 5. Compilation Targets

The compiler produces three outputs from a single AST:

### 5.1 Circuit Object

The primary output. A plain JavaScript object compatible with `shaderSolver.js`:

```js
{
  nodes: [{
    id: 0,
    name: "Glucose",
    speciesId: "Glucose",
    compartment: "cytoplasm",
    compartmentName: "cytoplasm",
    concentration: 5.0,
    mu0: -917.0,
    mu: -917.0 + 2.478 * Math.log(5.0),  // = -913.01
    boundary: false,
  }, ...],
  edges: [{
    id: 0,
    reactionId: "edge_0",
    name: "Glucose->G6P",
    src: 0,
    dst: 1,
    rate: 230.0,
    conductance: 464.1,
    deltaG: -913.01 - (-1766.1),  // mu_src - mu_dst
  }, ...],
  numNodes: 10,
  numEdges: 15,
}
```

**Node mu computation**: If `mu0` and `concentration` are both given, `mu = mu0 + RT * ln(concentration)`. If only `mu` is given, it is used directly with `mu0 = mu`.

**Edge conductance**: If `conductance` is given, use it. If only `rate` is given, compute `G = rate * concentration_src / RT`.

**Edge deltaG**: Always computed as `mu_src - mu_dst` from the resolved node potentials.

### 5.2 GLSL Output

Generates a fragment shader that hardcodes the circuit data as constants. This is for inspection/export only — the actual solver uses texture-packed data.

```glsl
#version 300 es
precision highp float;

// Auto-generated from SBS DSL
const int NUM_NODES = 10;
const int NUM_EDGES = 15;

// Node chemical potentials
const float mu[10] = float[10](-913.01, -1766.1, ...);

// Edge data: vec3(src, dst, conductance)
const vec3 edges[15] = vec3[15](vec3(0, 1, 464.1), ...);

in vec2 v_uv;
out vec4 fragColor;

void main() {
    int i = int(v_uv.x * float(NUM_NODES));
    if (i >= NUM_NODES) { fragColor = vec4(0.0); return; }

    float flux = 0.0;
    float degree = 0.0;
    for (int e = 0; e < NUM_EDGES; e++) {
        int src = int(edges[e].x);
        int dst = int(edges[e].y);
        float G = edges[e].z;
        if (src == i || dst == i) {
            flux += G * abs(mu[src] - mu[dst]);
            degree += G;
        }
    }

    // Normalize (global min/max would need a second pass or precomputation)
    float Se = (mu[i] - MU_MIN) / MU_RANGE;
    float Sk = flux / FLUX_MAX;
    float St = degree / DEG_MAX;
    fragColor = vec4(Se, Sk, St, 1.0);
}
```

### 5.3 JavaScript Output

Generates a standalone JS function that performs the same computation as the shader, for environments without WebGL:

```js
function computeSBS() {
  const RT = 2.478;
  const nodes = [
    { name: "Glucose", mu: -913.01, concentration: 5.0 },
    // ...
  ];
  const edges = [
    { src: 0, dst: 1, conductance: 464.1 },
    // ...
  ];

  const flux = new Float64Array(nodes.length);
  const degree = new Float64Array(nodes.length);

  for (const e of edges) {
    const I = e.conductance * Math.abs(nodes[e.src].mu - nodes[e.dst].mu);
    flux[e.src] += I;
    flux[e.dst] += I;
    degree[e.src] += e.conductance;
    degree[e.dst] += e.conductance;
  }

  const muMin = Math.min(...nodes.map(n => n.mu));
  const muRange = Math.max(...nodes.map(n => n.mu)) - muMin;
  const fluxMax = Math.max(...flux);
  const degMax = Math.max(...degree);

  return nodes.map((n, i) => ({
    Se: (n.mu - muMin) / muRange,
    Sk: flux[i] / fluxMax,
    St: degree[i] / degMax,
  }));
}
```

---

## 6. Compiler Pipeline

### 6.1 Overview

```
Source code (string)
       │
       ▼
  ┌──────────┐
  │ Tokenizer │  tokenize(source) → Token[]
  │           │  - Lexical analysis
  │           │  - Line/col tracking for error messages
  └─────┬────┘
        │
        ▼
  ┌──────────┐
  │  Parser   │  parse(tokens) → AST
  │           │  - Recursive descent
  │           │  - Operator precedence climbing
  │           │  - Error recovery (skip to next statement)
  └─────┬────┘
        │
        ▼
  ┌──────────┐
  │ Compiler  │  compile(ast) → CompileResult
  │           │  - Semantic analysis (name resolution, type checking)
  │           │  - Circuit building (nodes, edges, perturbations)
  │           │  - GLSL code generation
  │           │  - JS code generation
  └─────┬────┘
        │
        ▼
  CompileResult {
    success: boolean,
    ast: AST,
    circuit: Circuit,
    perturbations: [{idx, factor}],
    observations: [string],
    errors: [{message, line}],
    warnings: [{message, line}],
    glsl: string,
    js: string,
  }
```

### 6.2 Semantic Analysis

The compiler performs these checks during AST traversal:

| Check | Error Message |
|-------|---------------|
| Undefined node in edge | `Edge references undefined node '{name}'` |
| Undefined circuit in observe | `Cannot observe undefined circuit '{name}'` |
| Undefined catalyst in cascade | `Catalyst '{name}' not defined` |
| Duplicate node name | `Node '{name}' already declared` |
| Duplicate circuit name | `Circuit '{name}' already declared` |
| Invalid perturbation factor | `Perturbation factor must be > 0` |
| Invalid catalyst power | `Catalyst power must be in [0, 1]` |
| Missing mu on node | `Node '{name}' must have 'mu' property` |
| Edge missing conductance and rate | `Edge must have 'conductance' or 'rate'` |
| Invalid conversion type | `Unknown representation type '{type}'` |

### 6.3 Name Resolution

Names are resolved in this order:

1. Local variables (from `let` bindings)
2. Function parameters
3. Built-in references (`R`, `V`, `Se`, `Sk`, `St`, `floor`)
4. Node names in the current circuit scope
5. Circuit names (for `observe`, `perturb`, etc.)
6. Catalyst names

### 6.4 Property Evaluation

Property values (`{ key: expr }`) are evaluated at compile time when possible:

- Number literals → direct value
- String literals → direct value
- Boolean literals → direct value
- Arithmetic expressions on literals → computed value
- Variable references → deferred to runtime

---

## 7. Import Resolution

The `import` statement supports two source types:

### 7.1 Pathway Import

```sbs
import glycolysis from "reactome:R-HSA-70171"
import tca from "kegg:path:hsa00020"
```

These are resolved at compile time by the playground environment:

1. Parse the source string to extract `{database}:{id}`
2. Call `/api/sbs/pathway?id={id}&source={database}`
3. Parse the returned SBML with `buildCircuitFromSBML()`
4. Bind the resulting circuit to the import name

### 7.2 URL Import

```sbs
import custom from "https://example.com/my-circuit.sbs"
```

Fetches the URL, parses the content as SBS DSL, and merges the exported declarations.

### 7.3 Import in Compiler vs. Runtime

The compiler itself does not perform network requests. Instead:

1. The compiler emits `Import` AST nodes
2. The playground environment resolves imports before compilation
3. Resolved imports are injected into the source as circuit declarations
4. The compiler processes the expanded source

---

## 8. Error Recovery

The parser uses **panic-mode recovery**: when a parse error occurs in a statement, it skips tokens until it finds a keyword that could start a new statement (`circuit`, `node`, `edge`, `let`, `fn`, `observe`, `perturb`, `restore`, `navigate`, `catalyst`, `cascade`, `for`, `if`, `import`, `export`).

This allows the compiler to report multiple errors per compilation, which is essential for the playground's auto-compile feature (300ms debounce).

---

## 9. Auto-Compile Behavior

The playground editor compiles on every keystroke (debounced 300ms):

1. **Tokenize** — always runs, populates error gutter with lexer errors
2. **Parse** — runs if tokenization succeeded, populates AST tab
3. **Compile** — runs if parsing succeeded, populates circuit/GLSL/JS tabs
4. **Solve** — runs if compilation succeeded AND auto-observe is enabled
5. **Metrics** — runs if solving succeeded, populates output tab with charts

Steps 4-5 are optional (toggled by the auto-compile checkbox) because the shader solve can be expensive for large circuits.

---

## 10. Integration with Existing Code

### 10.1 Circuit Compatibility

The compiler output circuit object has the exact same shape as `buildCircuitFromSBML()` output and `buildDemoGlycolysis()` output. This means:

- `solveCircuit(circuit, perturbation)` works directly
- `computeFluxPattern(circuit, perturbation)` works directly
- `extractMetrics(shaderResult, circuit, healthyBaseline, perturbation)` works directly
- `CircuitGraph` component renders it directly
- `CellViewer` component positions nodes correctly

### 10.2 Perturbation Format

The compiler collects `perturb` statements and produces `[{idx: edgeIndex, factor: number}]`, which is the exact format expected by `shaderSolver.js`.

### 10.3 Observation Sequence

When the compiler encounters `observe circuitName`:

1. Look up the circuit by name
2. Mark it as the active circuit for the playground
3. Record the observation in the `observations` array
4. Subsequent references to `R`, `V`, `Se`, `Sk`, `St` resolve to the observation results

Multiple `observe` statements are allowed — each replaces the previous observation baseline.

---

## 11. Future Extensions

### 11.1 Evidence-Based Perturbation (from Kwasa-kwasa Points & Resolutions)

Instead of just a multiplicative factor, perturbations could carry confidence:

```sbs
perturb glycolysis {
  edge: "Hexokinase",
  factor: 0.1,
  confidence: 0.85,       // how sure we are about this perturbation
  source: "PMID:12345678"  // evidence provenance
}
```

The confidence would weight the perturbation's contribution to V, implementing Bayesian updating over the flux pattern.

### 11.2 Goal-Based Observation (from Kwasa-kwasa Goals)

```sbs
goal restore_flux {
  target: V > 0.9,
  constraint: sparsity < 3,   // at most 3 edges
  method: "l1-optimal"
}
```

This would decompose into sub-goals (identify disrupted edges, compute restoration factors, verify V threshold) following the hierarchical goal pattern.

### 11.3 Fuzzy Membership (from Kwasa-kwasa Hybrid-Imperative)

```sbs
node Glucose {
  mu: -917.0,
  compartment: fuzzy("cytoplasm": 0.8, "membrane": 0.2)
}
```

Nodes could have fuzzy compartment membership, reflecting uncertainty in subcellular localization.

### 11.4 Circular Validation

```sbs
validate glycolysis {
  threshold: 0.5,
  // Checks mutual support among >=3 S-expressions
  // Reports cycle of validated/invalidated sub-circuits
}
```

Implements the circular validation theorem from Part VIII of the formalization.
