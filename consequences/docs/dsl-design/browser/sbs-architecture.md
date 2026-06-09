# SBS Browser Tool — Architecture

## 1. System Overview

The SBS browser tool is a **single-page application** within the existing Next.js site that lets users:

1. **Define** a metabolic/signaling circuit (manually via DSL, or by fetching from Reactome/KEGG)
2. **Observe** it through the GPU shader in a single pass (no time-stepping)
3. **Perturb** edges and see the S-entropy response in real time
4. **Restore** flux visibility via l1-optimal perturbation suggestions
5. **Navigate** backward through the circuit to find rate-limiting steps
6. **Visualize** results as D3 charts, 3D cell geometry, and tabular data

The tool lives at `/sbs-playground` (the playground page) and `/sbs-tool` (the full guided tool). Both share the same core libraries.

---

## 2. Component Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Next.js Page                          │
│  /sbs-playground  or  /sbs-tool                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────┐    ┌────────────────────────┐   │
│  │  PlaygroundEditor   │    │  SBS Tool (3-step)     │   │
│  │  (DSL code editor)  │    │  ┌──────────────────┐  │   │
│  │  ┌───────────────┐  │    │  │ CircuitSearch    │  │   │
│  │  │ tokenizer.js  │  │    │  │ (Reactome/KEGG)  │  │   │
│  │  │ parser.js     │  │    │  └──────────────────┘  │   │
│  │  │ compiler.js   │  │    │  ┌──────────────────┐  │   │
│  │  └───────┬───────┘  │    │  │ CellViewer       │  │   │
│  │          │          │    │  │ (R3F + Three.js)  │  │   │
│  │          ▼          │    │  └──────────────────┘  │   │
│  │  ┌───────────────┐  │    │  ┌──────────────────┐  │   │
│  │  │ Circuit Object│◄─┼────┼──│ circuitBuilder   │  │   │
│  │  └───────┬───────┘  │    │  └──────────────────┘  │   │
│  │          │          │    │                        │   │
│  └──────────┼──────────┘    └────────────┬───────────┘   │
│             │                            │               │
│             ▼                            ▼               │
│  ┌──────────────────────────────────────────────────┐    │
│  │                Shared Core                        │    │
│  │  ┌──────────────┐  ┌────────────┐  ┌───────────┐ │    │
│  │  │shaderSolver  │  │metricsExtr │  │fluxPattern│ │    │
│  │  │  (WebGL2/CPU)│  │  (R, V)    │  │  compute  │ │    │
│  │  └──────┬───────┘  └─────┬──────┘  └─────┬─────┘ │    │
│  │         └────────────────┼────────────────┘       │    │
│  └──────────────────────────┼────────────────────────┘    │
│                             ▼                             │
│  ┌──────────────────────────────────────────────────┐    │
│  │              Visualization Layer                   │    │
│  │  ┌────────────┐ ┌───────────┐ ┌────────────────┐ │    │
│  │  │D3 Charts   │ │CircuitGraph│ │MetricsDashboard│ │    │
│  │  │(scatter,bar│ │(force sim) │ │(R,V,flux,path) │ │    │
│  │  │ gauge,line)│ │            │ │                │ │    │
│  │  └────────────┘ └───────────┘ └────────────────┘ │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │          External Data Integration                │    │
│  │  /api/sbs/search   → Reactome + KEGG             │    │
│  │  /api/sbs/pathway  → SBML XML fetch               │    │
│  │  /api/sbs/compounds → HMDB + KEGG thermodynamics  │    │
│  │  /api/sbs/models   → 3D cell model catalog        │    │
│  │  /api/sbs/hf-embed → HuggingFace inference proxy  │    │
│  │  /api/sbs/cell-image → Cell Atlas image proxy     │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow

### 3.1 DSL Path (Playground)

```
User types DSL code
       │
       ▼
tokenizer.js  →  token stream
       │
       ▼
parser.js     →  AST
       │
       ▼
compiler.js   →  { circuit, perturbations, observations, glsl, js }
       │
       ├──▶ shaderSolver.solveCircuit(circuit, perturbation)
       │         │
       │         ▼
       │    Float32Array texture  (Se, Sk, St per node)
       │         │
       │         ▼
       │    metricsExtractor.extractMetrics(...)
       │         │
       │         ▼
       │    { R, V, Se[], Sk[], St[], fluxHealthy[], fluxCurrent[], backwardPath }
       │
       ├──▶ Output Tabs: AST (JSON), GLSL, JS, Circuit, Metrics
       │
       └──▶ D3 Charts: S-entropy scatter, flux bar chart, gauge
```

### 3.2 Search Path (Guided Tool)

```
User searches "glycolysis"
       │
       ▼
/api/sbs/search  →  Reactome + KEGG results
       │
       ▼
User selects pathway (e.g., R-HSA-70171)
       │
       ▼
/api/sbs/pathway  →  SBML XML
       │
       ▼
circuitBuilder.buildCircuitFromSBML(xml, compoundData)
       │
       ▼
Circuit object { nodes[], edges[], numNodes, numEdges }
       │
       ├──▶ Same solver + metrics pipeline as DSL path
       └──▶ CellViewer projects nodes onto 3D organelle geometry
```

---

## 4. State Management

All shared state is managed via React context + `useReducer` in `SBSContext.js`.

### State Shape

```js
{
  // Step tracking (guided tool only)
  step: 'search' | 'geometry' | 'observe',

  // Circuit data (shared by playground and tool)
  circuit: {
    nodes: [{ id, name, speciesId, compartment, compartmentName,
              concentration, mu0, mu, boundary }],
    edges: [{ id, reactionId, name, src, dst, rate,
              conductance, deltaG }],
    numNodes: number,
    numEdges: number,
  },

  // Search state
  searchQuery: string,
  searchResults: [{ id, name, source, species, description }],
  searchLoading: boolean,
  selectedPathway: { id, name, source },

  // Geometry state
  cellModel: string,         // model ID

  // Observation state
  shaderResult: {
    texture: Float32Array,   // N*4 RGBA32F
    renderTimeMs: number,
    numNodes: number,
    backend: 'webgl2' | 'cpu',
  },
  healthyBaseline: { ... },  // same shape, stored for V computation
  metrics: {
    R: number,               // coherence [0,1]
    V: number,               // visibility (0,1]
    Se: number[],
    Sk: number[],
    St: number[],
    fluxHealthy: number[],
    fluxCurrent: number[],
    fluxWeights: number[],
    backwardPath: [{ nodeId, name, mu }],
    renderTimeMs: number,
    backend: string,
  },
  perturbation: [{ idx, factor }],

  // SBML raw text (for display/export)
  sbml: string,

  // Errors
  errors: [],
}
```

### Dispatch Actions

| Action | Payload | Effect |
|--------|---------|--------|
| `SET_SEARCH_QUERY` | `string` | Update search text |
| `SET_SEARCH_LOADING` | `boolean` | Toggle loading spinner |
| `SET_SEARCH_RESULTS` | `[...]` | Populate result list |
| `SELECT_PATHWAY` | `{id, name, source}` | Store selection |
| `SET_SBML` | `string` | Store raw SBML |
| `SET_CIRCUIT` | `{nodes, edges, ...}` | Replace circuit, reset metrics |
| `SET_CELL_MODEL` | `string` | Switch 3D model |
| `SET_SHADER_RESULT` | `{texture, ...}` | Store shader output |
| `SET_METRICS` | `{R, V, ...}` | Store computed metrics |
| `SET_PERTURBATION` | `[{idx, factor}]` | Set edge perturbations |
| `CLEAR_PERTURBATION` | — | Reset to healthy state |
| `CLEAR_ERROR` | — | Clear error messages |

---

## 5. External API Integration

### 5.1 Reactome (Pathway Database)

**Search**: `GET https://reactome.org/ContentService/search/query?query={q}&types=Pathway&cluster=true`
- Returns JSON with `results[].entries[]` containing `stId`, `name`, `summation`
- Proxied through `/api/sbs/search` to avoid CORS

**Pathway SBML**: `GET https://reactome.org/ContentService/exporter/sbml/{stId}.xml`
- Returns SBML XML string
- Proxied through `/api/sbs/pathway`

**Diagram**: `GET https://reactome.org/ContentService/exporter/diagram/{stId}.svg`
- Returns SVG of the pathway diagram (for reference overlay)

**Participants**: `GET https://reactome.org/ContentService/data/participants/{stId}`
- Returns species list with compartment annotations

### 5.2 KEGG (Pathway Maps)

**Search**: `GET https://rest.kegg.jp/find/pathway/{query}`
- Tab-separated text: `path:map00010\tGlycolysis / Gluconeogenesis`

**KGML**: `GET https://rest.kegg.jp/get/{pathId}/kgml`
- XML format with `<entry>` (species) and `<reaction>` (edges)

**Compound info**: `GET https://rest.kegg.jp/get/{compoundId}`
- Plain text with NAME, FORMULA, EXACT_MASS fields

### 5.3 HMDB (Metabolome Database)

**Compound JSON**: `GET https://hmdb.ca/metabolites/{HMDBID}.json`
- Returns `standard_gibbs_free_energy`, `concentration_value`, `name`
- Used to populate `mu0` and `concentration` on circuit nodes

### 5.4 HuggingFace Inference API

**Purpose**: Semantic search over pathway descriptions, protein function prediction

**Endpoint**: `POST https://api-inference.huggingface.co/models/{model_id}`
- Requires `Authorization: Bearer {HF_TOKEN}` header
- Proxied through `/api/sbs/hf-embed` to keep token server-side

**Use cases**:
1. **Pathway similarity search**: Embed user query and pathway descriptions with `sentence-transformers/all-MiniLM-L6-v2`, rank by cosine similarity
2. **Protein function classification**: Use `facebook/esm2_t6_8M_UR50D` for sequence-to-function when user provides a protein sequence
3. **Drug-target prediction**: Use `DeepChem/ChemBERTa-77M-MTR` for molecule embedding when user provides SMILES strings

**API route** `/api/sbs/hf-embed`:
```
POST /api/sbs/hf-embed
Body: { model: "sentence-transformers/all-MiniLM-L6-v2",
        inputs: ["glycolysis pathway", "TCA cycle"] }
Response: { embeddings: [[0.1, 0.2, ...], [0.3, 0.4, ...]] }
```

### 5.5 Cell Atlas Images

**Human Protein Atlas** (proteinatlas.org):
- Cell images: `GET https://images.proteinatlas.org/{gene}/{tissue}_{antibody}_blue_red_green.jpg`
- Used to show immunofluorescence images of proteins in the pathway

**API route** `/api/sbs/cell-image`:
```
GET /api/sbs/cell-image?gene=HK1&tissue=liver
Response: { url: "https://images.proteinatlas.org/...", gene, tissue, antibody }
```

This is a proxy that resolves the correct image URL from the Protein Atlas API and returns it for `<img>` rendering.

### 5.6 UniProt (Protein Data)

**Protein info**: `GET https://rest.uniprot.org/uniprotkb/search?query={gene}&format=json&size=1`
- Returns function annotation, subcellular location, GO terms
- Used to validate compartment assignments

---

## 6. Shader Pipeline (WebGL2)

### 6.1 Architecture

```
┌──────────────────────────────────────────────┐
│           Offscreen Canvas (WebGL2)          │
│                                              │
│  Uniforms:                                   │
│    u_nodes      ← RGBA32F texture (N×1)      │
│      .r = mu                                 │
│      .g = concentration                      │
│      .b = 0 (reserved)                       │
│      .a = node index                         │
│                                              │
│    u_edges      ← RGBA32F texture (M×1)      │
│      .r = src node index                     │
│      .g = dst node index                     │
│      .b = conductance                        │
│      .a = deltaG                             │
│                                              │
│    u_perturbation ← R32F texture (M×1)       │
│      .r = perturbation factor (default 1.0)  │
│                                              │
│    u_numNodes   ← int                        │
│    u_numEdges   ← int                        │
│                                              │
│  Render: full-screen quad (2 triangles)      │
│  Fragment shader: observation.frag.js        │
│  Output: framebuffer → readPixels            │
│                                              │
│  Result texture (N×1 RGBA32F):               │
│    .r = Se (normalized chemical potential)   │
│    .g = Sk (normalized flux magnitude)       │
│    .b = St (normalized weighted degree)      │
│    .a = 1.0                                  │
└──────────────────────────────────────────────┘
```

### 6.2 CPU Fallback

When `EXT_color_buffer_float` is unavailable, `solveCPU()` runs the same algorithm:

1. Build perturbation map from `[{idx, factor}]`
2. For each edge: `G = conductance * pertFactor`, `I = G * |mu_src - mu_dst|`
3. Accumulate flux and degree at each node endpoint
4. Normalize all three channels by global max
5. Pack into Float32Array with same layout as GPU output

### 6.3 Performance Budget

| Circuit size | GPU time | CPU time | Notes |
|-------------|----------|----------|-------|
| 10 nodes, 15 edges | < 1ms | < 1ms | Glycolysis demo |
| 100 nodes, 300 edges | < 2ms | ~5ms | Typical Reactome pathway |
| 1000 nodes, 5000 edges | < 5ms | ~50ms | Large metabolic network |

Single-pass: no iteration, no convergence check, no time-stepping.

---

## 7. Metrics Computation

All metrics are computed in JavaScript from the shader output texture.

### 7.1 Triple Coherence R

**Definition**: Mean pairwise Spearman rank correlation of (Se, Sk, St) vectors.

```
rhoEK = spearmanRho(Se, Sk)
rhoET = spearmanRho(Se, St)
rhoKT = spearmanRho(Sk, St)
meanRho = (rhoEK + rhoET + rhoKT) / 3
R = (meanRho + 1) / 2     // map [-1,1] → [0,1]
```

**Interpretation**: R = 1 means perfect agreement among the three axes (healthy). R → 0.5 means disorder. R < 0.5 means anti-correlation (severe disruption).

### 7.2 Flux Visibility V

**Definition**: Weighted geometric mean of per-edge flux preservation ratios.

```
For each edge k:
  w_k = |flux_healthy[k]| / sum(|flux_healthy|)     // importance weight
  ratio_k = min(flux_h, flux_c) / max(flux_h, flux_c)  // similarity
  
logV = sum(w_k * log(ratio_k))
V = exp(logV)
```

**Interpretation**: V = 1 means identical flux pattern. V < 0.1 means severe disruption. The l1-optimal restoration target is V > 0.9.

### 7.3 Backward Navigation

Greedy traversal from highest-mu node, following the incoming edge with maximum conductance at each step. Returns a path `[{nodeId, name, mu}]`.

### 7.4 Optimal Perturbation

Sort edges by flux weight descending. For each of the top-N perturbed edges, suggest `factor = 1/currentFactor` as the restoration.

---

## 8. Visualization Layer

### 8.1 D3 Charts (existing in D3Chart.js + MetricsDashboard.js)

| Chart | Data | Component |
|-------|------|-----------|
| S-entropy scatter | Se vs Sk, color=St (Viridis) | MetricsDashboard |
| Flux bar chart | fluxHealthy[] vs fluxCurrent[] (log scale) | MetricsDashboard |
| Backward path | Node names with arrows | MetricsDashboard |
| Coherence gauge | R value [0,1] | D3Chart (GaugeChart) |
| Visibility gauge | V value [0,1] | D3Chart (GaugeChart) |
| Catalyst convergence | (1-kappa)^n decay curve | D3Chart (LineChart) |
| Perturbation heatmap | Edge × perturbation factor | D3Chart (Heatmap) |

### 8.2 Charts to Add for Playground

| Chart | Purpose | Data Source | D3 Type |
|-------|---------|-------------|---------|
| **Flux comparison bar** | Side-by-side healthy/perturbed flux per edge | `fluxHealthy[]`, `fluxCurrent[]` | Grouped bar (log-y) |
| **Se-Sk-St radar** | Triangle showing triple balance per node | `Se[]`, `Sk[]`, `St[]` | Custom radial |
| **Catalyst decay line** | Plot `(1-κ)^n` for n=0..20 | Cascade parameters | LineChart |
| **Circuit topology** | Force-directed graph with mu-colored nodes | `circuit.nodes`, `circuit.edges` | Force simulation |
| **Perturbation response curve** | V as function of perturbation factor | Sweep from 0.01 to 10 | LineChart |
| **Backward path overlay** | Highlight nodes/edges on circuit graph | `backwardPath[]` | SVG overlay |
| **Reactome pathway image** | Reference diagram from Reactome | `/api/sbs/pathway?format=svg` | SVG embed |

### 8.3 3D Cell Viewer (R3F)

Existing `CellViewer.js` provides:
- Procedural organelle meshes (membrane, nucleus, mitochondria, ER, Golgi, vesicles)
- OrbitControls with auto-rotate
- Circuit nodes as glowing spheres positioned by compartment
- HTML overlay labels via drei

### 8.4 Playground Output Tabs

The playground editor renders 5 tabs:

| Tab | Content | Format |
|-----|---------|--------|
| **Output** | Metrics summary + chart area | HTML + D3 |
| **AST** | Parsed AST as formatted JSON | `<pre>` |
| **GLSL** | Generated fragment shader code | Syntax-highlighted |
| **JS** | Generated JavaScript equivalent | Syntax-highlighted |
| **Circuit** | Circuit object as JSON | `<pre>` |

---

## 9. File Map

### Core Libraries (`src/lib/sbs/`)

| File | Purpose | Exports |
|------|---------|---------|
| `shaderSolver.js` | WebGL2 pipeline + CPU fallback | `solveCircuit`, `solveCPU`, `computeFluxPattern` |
| `metricsExtractor.js` | R, V, backward nav, optimal perturbation | `extractMetrics`, `tripleCoherence`, `fluxVisibility`, `computeBackwardNavigation`, `findOptimalPerturbation` |
| `circuitBuilder.js` | SBML → circuit, demo glycolysis | `buildCircuitFromSBML`, `buildDemoGlycolysis` |
| `dsl/tokenizer.js` | Lexer | `tokenize`, `TOKEN_TYPES`, `KEYWORDS` |
| `dsl/parser.js` | Recursive descent parser | `parse` |
| `dsl/compiler.js` | AST → circuit + GLSL + JS | `Compiler`, `compileSBS`, `validateSBS` |
| `dsl/examples.js` | 6 built-in examples | `EXAMPLES`, `DEFAULT_EXAMPLE` |
| `shaders/observation.frag.js` | GLSL fragment shader source | template literal |
| `shaders/observation.vert.js` | GLSL vertex shader source | template literal |

### Components (`src/components/sbs/`)

| File | Purpose | Key Props/Context |
|------|---------|-------------------|
| `SBSContext.js` | State management | Provider, `useSBS()` hook |
| `CircuitSearch.js` | Search + pathway loading | Dispatches `SET_CIRCUIT` |
| `CircuitGraph.js` | D3 force-directed network | Reads `circuit` from context |
| `CellViewer.js` | R3F 3D cell + nodes | Reads `circuit`, `shaderResult` |
| `ObservationPanel.js` | Run button + metric cards | Calls `solveCircuit` |
| `MetricsDashboard.js` | D3 charts (scatter, bars, path) | Reads `metrics` |
| `PerturbationEditor.js` | Edge sliders + disease presets | Dispatches `SET_PERTURBATION` |
| `PlaygroundEditor.js` | DSL code editor + output tabs | Self-contained with internal compile |

### Pages

| File | Route | Purpose |
|------|-------|---------|
| `pages/sbs-playground.js` | `/sbs-playground` | DSL playground |
| `pages/sbs-tool.js` | `/sbs-tool` | Guided 3-step tool |

### API Routes (`pages/api/sbs/`)

| File | Endpoint | External APIs |
|------|----------|---------------|
| `search.js` | `GET /api/sbs/search?q=` | Reactome, KEGG |
| `pathway.js` | `GET /api/sbs/pathway?id=&source=` | Reactome (SBML), KEGG (KGML) |
| `compounds.js` | `GET /api/sbs/compounds?ids=` | HMDB, KEGG |
| `models.js` | `GET /api/sbs/models` | Static catalog |
| `hf-embed.js` | `POST /api/sbs/hf-embed` | HuggingFace Inference |
| `cell-image.js` | `GET /api/sbs/cell-image?gene=&tissue=` | Human Protein Atlas |

---

## 10. Dependencies

**No new packages required.** Everything is already in `package.json`:

| Package | Version | Used For |
|---------|---------|----------|
| `next` | ^13.2.1 | Pages, API routes, SSR |
| `react` / `react-dom` | 18.2.0 | UI framework |
| `d3` | ^7.9.0 | All charts and force graphs |
| `three` | ^0.160.0 | 3D rendering |
| `@react-three/fiber` | ^8.15.19 | React bindings for Three.js |
| `@react-three/drei` | ^9.88.17 | Three.js helpers |
| `framer-motion` | ^10.0.1 | Animations and transitions |
| `tailwindcss` | ^3.2.7 | Styling |

SBML parsing uses browser-native `DOMParser`. No XML library needed.

---

## 11. Environment Variables

```env
# Optional — enables HuggingFace inference features
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxx

# Optional — enables Protein Atlas cell images
# No token needed (public API), but rate-limited
```

If `HF_TOKEN` is not set, the `/api/sbs/hf-embed` route returns a 501 with a message explaining the feature requires a HuggingFace token. The core SBS tool works fully without it.

---

## 12. Error Handling Strategy

| Layer | Strategy |
|-------|----------|
| DSL parsing | Collect errors with line/col, report all (don't stop at first) |
| API routes | Try-catch with `catch(() => {})` on each external API, merge available results |
| Shader | Attempt WebGL2, fall back to CPU, report backend in result |
| Metrics | Guard against division by zero (flux=0, empty arrays) |
| UI | Display errors in context-specific locations (editor gutter, metric cards, toast) |

---

## 13. Security Considerations

- All external API calls go through Next.js API routes (server-side proxy) — no CORS issues, no exposed tokens
- HuggingFace token stored in environment variable, never sent to client
- SBML XML parsed with DOMParser (sandboxed), not `eval` or `innerHTML`
- DSL compiler produces data structures, never executes arbitrary code
- Rate limiting on API routes recommended for production deployment
