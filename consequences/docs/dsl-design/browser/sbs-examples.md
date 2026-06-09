# SBS Browser Tool — Worked Examples

Each example below is a complete SBS program with the expected output, chart specifications, and API integration details. These are the built-in examples available from the playground's example dropdown.

---

## Example 1: Glycolysis — The Canonical Demo

### DSL Code

```sbs
// Glycolysis — 10 metabolites, 15 enzymatic reactions
// Source: Reactome R-HSA-70171

circuit glycolysis {
  node Glucose     { mu: -917.0, concentration: 5.0, compartment: "cytoplasm" }
  node G6P         { mu: -1760.0, concentration: 0.083 }
  node F6P         { mu: -1755.0, concentration: 0.014 }
  node FBP         { mu: -2600.0, concentration: 0.031 }
  node G3P         { mu: -1290.0, concentration: 0.14 }
  node BPG13       { mu: -2356.0, concentration: 0.001 }
  node PG3         { mu: -1515.0, concentration: 0.1 }
  node PG2         { mu: -1510.0, concentration: 0.03 }
  node PEP         { mu: -1263.0, concentration: 0.023 }
  node Pyruvate    { mu: -472.0, concentration: 0.051 }

  // Forward reactions
  edge Glucose  -> G6P      { rate: 230.0, conductance: 464.1 }
  edge G6P      -> F6P      { rate: 100.0, conductance: 3.35 }
  edge F6P      -> FBP      { rate: 150.0, conductance: 0.85 }
  edge FBP      -> G3P      { rate: 80.0, conductance: 1.0 }
  edge G3P      -> BPG13    { rate: 200.0, conductance: 11.3 }
  edge BPG13    -> PG3      { rate: 300.0, conductance: 0.12 }
  edge PG3      -> PG2      { rate: 180.0, conductance: 7.27 }
  edge PG2      -> PEP      { rate: 100.0, conductance: 1.21 }
  edge PEP      -> Pyruvate { rate: 500.0, conductance: 4.64 }

  // Reverse reactions (near-equilibrium steps)
  edge G6P  -> Glucose  { rate: 20.0, conductance: 0.67 }
  edge F6P  -> G6P      { rate: 80.0, conductance: 0.45 }
  edge G3P  -> FBP      { rate: 30.0, conductance: 1.69 }
  edge PG3  -> BPG13    { rate: 250.0, conductance: 10.1 }
  edge PG2  -> PG3      { rate: 150.0, conductance: 1.82 }
  edge PEP  -> PG2      { rate: 70.0, conductance: 0.65 }
}

// Observe healthy baseline
observe glycolysis

// Store healthy metrics
let healthy_R = R
let healthy_V = V

// Disease: hexokinase deficiency (90% reduction in Glucose->G6P)
perturb glycolysis { edge: "Glucose->G6P", factor: 0.1 }

// Observe diseased state
observe glycolysis

// Navigate backward from Pyruvate to find rate-limiting step
navigate from Pyruvate
```

### Expected Output

```
Healthy state:
  R = 0.705  (triple coherence)
  V = 1.000  (flux visibility — baseline is always 1.0)
  Backend: webgl2
  Render time: 0.3ms

After hexokinase perturbation (factor=0.1):
  R = 0.612  (coherence drops)
  V = 0.108  (visibility severely disrupted)

Backward navigation from Pyruvate:
  Pyruvate ← PEP ← PG2 ← PG3 ← BPG13 ← G3P ← FBP ← F6P ← G6P ← Glucose
```

### Charts

**Chart 1: S-entropy Scatter Plot**
- Type: `ScatterPlot` (from D3Chart.js)
- X-axis: Se (normalized chemical potential), range [0, 1]
- Y-axis: Sk (normalized flux), range [0, 1]
- Color: St (normalized degree) via `d3.interpolateViridis`
- Points: 10 (one per metabolite)
- Tooltip: node name, Se, Sk, St values
- Dimensions: 300×220px

**Chart 2: Flux Comparison Bar Chart**
- Type: `BarChart` (grouped, from MetricsDashboard)
- X-axis: Edge names (truncated to 8 chars)
- Y-axis: Flux magnitude (log scale, `d3.scaleLog`)
- Bars: Blue = healthy flux, Red = perturbed flux
- 15 edge pairs side-by-side
- Dimensions: 400×200px

**Chart 3: Coherence Gauge**
- Type: `GaugeChart` (from D3Chart.js)
- Value: R = 0.612
- Max: 1.0
- Color: amber (degraded from healthy green)
- Label: "Triple Coherence R"
- Dimensions: 140×140px

**Chart 4: Visibility Gauge**
- Type: `GaugeChart`
- Value: V = 0.108
- Max: 1.0
- Color: red (severely disrupted)
- Label: "Flux Visibility V"
- Dimensions: 140×140px

**Chart 5: Circuit Force Graph**
- Type: Force-directed (from CircuitGraph.js)
- Nodes: 10 circles, radius 12px, colored by mu (Viridis)
- Edges: 15 lines, stroke width scaled by conductance
- Arrow markers for directionality
- Draggable, zoomable (0.3x–3x)
- Dimensions: 400×300px

### API Integration

**Reactome pathway reference**:
- Fetch: `GET /api/sbs/search?q=glycolysis`
- Select: R-HSA-70171 "Glycolysis"
- Load: `GET /api/sbs/pathway?id=R-HSA-70171&source=reactome`
- The SBML contains all 10 species and 9 reactions (some bidirectional)
- `buildCircuitFromSBML()` expands bidirectional reactions into forward + reverse edges

**Cell image reference**:
- Hexokinase HK1: `GET /api/sbs/cell-image?gene=HK1&tissue=liver`
- Returns immunofluorescence image from Human Protein Atlas
- Display alongside the circuit graph to show where hexokinase localizes

---

## Example 2: Catalyst Convergence

### DSL Code

```sbs
// Demonstrates Theorem 5.8: geometric convergence of catalysts
// Residual S-distance decays as (1 - kappa)^n

circuit minimal {
  node A { mu: 10.0, concentration: 1.0 }
  node B { mu: 5.0, concentration: 0.5 }
  node C { mu: 1.0, concentration: 0.1 }

  edge A -> B { conductance: 2.0 }
  edge B -> C { conductance: 1.5 }
  edge C -> A { conductance: 0.5 }
}

// Two catalysts with known powers
catalyst drug_mild   { power: 0.3 }
catalyst drug_strong { power: 0.7 }

// Cascade composition: kappa_12 = 1 - (1-0.3)(1-0.7) = 0.79
cascade(drug_mild, drug_strong)

// Show convergence at initial S-value 80
let s0 = 80.0

// Compute residual at each step
for n in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10] {
  let residual_mild = s0 * (1.0 - 0.3) ** n
  let residual_strong = s0 * (1.0 - 0.7) ** n
  let residual_combined = s0 * (1.0 - 0.79) ** n
}

observe minimal
```

### Expected Output

```
Catalyst composition:
  drug_mild:    kappa = 0.300
  drug_strong:  kappa = 0.700
  combined:     kappa = 0.790

Convergence table (S₀ = 80.0):
  n   mild(0.3)   strong(0.7)   combined(0.79)
  0   80.000      80.000        80.000
  1   56.000      24.000        16.800
  2   39.200       7.200         3.528
  3   27.440       2.160         0.741
  4   19.208       0.648         0.156
  5   13.446       0.194         0.033
  ...
  10   2.264       0.000         0.000

S_floor = 1.50 (bounded receiver guarantee)
```

### Charts

**Chart 1: Convergence Decay Curves**
- Type: `LineChart` (from D3Chart.js)
- X-axis: Application count n (0 to 20)
- Y-axis: Residual S-value
- Lines:
  - Blue dashed: `(1 - 0.3)^n * 80` — mild catalyst
  - Red dashed: `(1 - 0.7)^n * 80` — strong catalyst
  - Green solid: `(1 - 0.79)^n * 80` — combined cascade
- Horizontal dashed line at S_floor = 1.5
- Legend in top-right
- Dimensions: 400×250px
- Animation: Lines draw left-to-right (1500ms, curveMonotoneX)

**Chart 2: Catalyst Power Comparison Bar**
- Type: `BarChart`
- X-axis: Catalyst names
- Y-axis: Power kappa [0, 1]
- 3 bars: mild (0.3), strong (0.7), combined (0.79)
- Color: gradient from cool (low power) to warm (high power)
- Dimensions: 250×180px

---

## Example 3: Reactome Import — TCA Cycle

### DSL Code

```sbs
// Import a real pathway from Reactome
// The import resolves to an API call at compile time
import tca from "reactome:R-HSA-71403"

// Observe the imported circuit
observe tca

// Check coherence
let tca_coherence = R
let tca_visibility = V

// Perturb isocitrate dehydrogenase (common in gliomas)
perturb tca { edge: "Isocitrate->AlphaKG", factor: 0.15 }

observe tca

// Find optimal drug targets
restore tca
```

### Import Resolution

When the playground encounters `import tca from "reactome:R-HSA-71403"`:

1. Parse source: database = `reactome`, id = `R-HSA-71403`
2. Call: `GET /api/sbs/pathway?id=R-HSA-71403&source=reactome`
3. Receive: SBML XML (~50KB for TCA cycle)
4. Call: `GET /api/sbs/compounds?ids=HMDB0000094,HMDB0000134,...` (extracted species)
5. Build circuit: `buildCircuitFromSBML(sbmlXml, compoundData)`
6. Result: circuit with ~20 nodes, ~25 edges (TCA cycle reactions)
7. Inject as `circuit tca { ... }` before compilation

### Expected Output

```
TCA Cycle (R-HSA-71403):
  Nodes: 20 (Acetyl-CoA, Citrate, Isocitrate, α-KG, Succinyl-CoA, ...)
  Edges: 25 (8 forward, 8 reverse, 9 regulatory)

Healthy state:
  R = 0.73
  V = 1.00

After IDH perturbation (factor=0.15):
  R = 0.58
  V = 0.22

Restoration suggestions (l1-optimal, max 3 edges):
  1. Isocitrate->AlphaKG: restore factor = 6.67 (= 1/0.15)
  2. Citrate->Isocitrate: restore factor = 1.3 (compensatory)
  3. AlphaKG->Succinyl_CoA: restore factor = 1.1 (downstream relief)
```

### Charts

**Chart 1: Reactome Pathway Diagram (Reference)**
- Type: SVG embed
- Source: `GET https://reactome.org/ContentService/exporter/diagram/R-HSA-71403.svg`
- Displayed as reference alongside the SBS force graph
- Scrollable, zoomable container
- Dimensions: 500×400px (scrollable)

**Chart 2: S-entropy Scatter (Healthy vs Diseased overlay)**
- Type: `ScatterPlot`
- Two point sets: hollow circles = healthy, filled circles = perturbed
- Same axes as Example 1
- Points shift position between states, showing disruption visually
- Dimensions: 350×250px

**Chart 3: Restoration Impact**
- Type: `BarChart` (horizontal)
- X-axis: Suggested restoration factor
- Y-axis: Edge name
- 3 bars showing the top-3 restoration targets
- Color: green (restores V)
- Dimensions: 300×150px

### Cell Image Integration

```
IDH1 localization:
  GET /api/sbs/cell-image?gene=IDH1&tissue=brain
  → immunofluorescence showing mitochondrial matrix localization
  → displayed in a 200×200px thumbnail next to the circuit graph

IDH2 (mitochondrial isoform):
  GET /api/sbs/cell-image?gene=IDH2&tissue=liver
  → shows co-localization with other TCA enzymes
```

---

## Example 4: Drug Target Discovery with HuggingFace

### DSL Code

```sbs
// Signal transduction cascade with drug target analysis
// Combines SBS observation with ML-based target prediction

circuit egfr_signaling {
  node EGF        { mu: 0.0, concentration: 0.001, compartment: "extracellular" }
  node EGFR       { mu: -5.0, concentration: 0.1, compartment: "membrane" }
  node RAS        { mu: -8.0, concentration: 0.5, compartment: "membrane" }
  node RAF        { mu: -12.0, concentration: 0.3, compartment: "cytoplasm" }
  node MEK        { mu: -15.0, concentration: 0.4, compartment: "cytoplasm" }
  node ERK        { mu: -18.0, concentration: 0.6, compartment: "cytoplasm" }
  node MYC        { mu: -22.0, concentration: 0.05, compartment: "nucleus" }
  node CyclinD    { mu: -25.0, concentration: 0.08, compartment: "nucleus" }

  edge EGF   -> EGFR    { conductance: 15.0 }
  edge EGFR  -> RAS     { conductance: 12.0 }
  edge RAS   -> RAF     { conductance: 10.0 }
  edge RAF   -> MEK     { conductance: 8.0 }
  edge MEK   -> ERK     { conductance: 9.0 }
  edge ERK   -> MYC     { conductance: 5.0 }
  edge MYC   -> CyclinD { conductance: 3.0 }

  // Negative feedback
  edge ERK   -> EGFR    { conductance: 2.0 }
  edge CyclinD -> EGF   { conductance: 0.5 }
}

observe egfr_signaling

// Oncogenic RAS mutation — constitutive activation
perturb egfr_signaling { edge: "EGFR->RAS", factor: 5.0 }

observe egfr_signaling

// Find sparse drug targets
restore egfr_signaling

// Navigate the rate-limiting path
navigate from CyclinD
```

### HuggingFace API Integration

**Pathway similarity search** — when the user types "EGFR signaling" in the search bar:

```
POST /api/sbs/hf-embed
Body: {
  model: "sentence-transformers/all-MiniLM-L6-v2",
  inputs: [
    "EGFR signaling pathway in cancer",
    "Glycolysis",
    "TCA cycle",
    "MAPK/ERK signaling cascade",
    "PI3K/AKT signaling",
    "Wnt signaling pathway"
  ]
}
Response: {
  embeddings: [[0.12, 0.34, ...], ...]  // 384-dim vectors
}
```

The playground computes cosine similarity between the query embedding and each pathway description embedding, ranking results by relevance. This supplements Reactome keyword search with semantic matching.

**Drug-target prediction** — when the user clicks "Suggest drug targets":

```
POST /api/sbs/hf-embed
Body: {
  model: "DeepChem/ChemBERTa-77M-MTR",
  inputs: ["c1ccc2c(c1)cc1ccccc1[nH]2"]  // example SMILES for erlotinib
}
Response: {
  embeddings: [[0.45, 0.67, ...]]  // molecular fingerprint
}
```

Combined with the SBS l1-optimal restoration, this identifies which edges in the circuit are most likely to respond to known drugs.

### Expected Output

```
EGFR Signaling (8 nodes, 9 edges):

Healthy:
  R = 0.81
  V = 1.00

After RAS oncogenic mutation (EGFR->RAS factor=5.0):
  R = 0.54  (coherence severely disrupted)
  V = 0.31  (flux pattern distorted)

Restoration targets:
  1. EGFR->RAS:  factor = 0.20 (direct reversal)
  2. RAF->MEK:   factor = 0.60 (downstream dampening)
  3. ERK->EGFR:  factor = 3.00 (enhance negative feedback)

Backward path from CyclinD:
  CyclinD ← MYC ← ERK ← MEK ← RAF ← RAS ← EGFR ← EGF

Known drugs for these targets:
  - EGFR->RAS: Erlotinib, Gefitinib (EGFR inhibitors)
  - RAF->MEK:  Trametinib (MEK inhibitor)
  - ERK->EGFR: Sorafenib (multi-kinase, enhances feedback)
```

### Charts

**Chart 1: Signaling Cascade Force Graph**
- Type: Force-directed (CircuitGraph)
- Layout: Left-to-right (extracellular → membrane → cytoplasm → nucleus)
- Nodes colored by compartment (4 colors)
- Perturbed edge (EGFR→RAS) highlighted in red, thick stroke
- Restoration targets highlighted in green
- Dimensions: 450×350px

**Chart 2: Perturbation Response Curve**
- Type: `LineChart`
- X-axis: Perturbation factor for EGFR→RAS (0.01 to 10, log scale)
- Y-axis: Visibility V (0 to 1)
- Generated by sweeping the factor and solving at each point
- Vertical dashed line at factor=5.0 (current disease state)
- Horizontal dashed line at V=0.9 (restoration target)
- Intersection point labeled "therapeutic window"
- Dimensions: 400×250px

**Chart 3: Backward Path Overlay**
- Type: SVG overlay on Circuit Force Graph
- Highlighted edges: thick green lines following the backward path
- Node labels in bold along the path
- Non-path nodes/edges dimmed (opacity 0.3)

### Cell Image Integration

```
EGFR membrane localization:
  GET /api/sbs/cell-image?gene=EGFR&tissue=lung
  → shows membrane staining pattern
  → 200×200px thumbnail

ERK cytoplasm/nucleus shuttle:
  GET /api/sbs/cell-image?gene=MAPK1&tissue=skin
  → shows nuclear translocation upon activation
  → 200×200px thumbnail
```

---

## Example 5: Triple Equivalence — Representation Conversion

### DSL Code

```sbs
// Triple Equivalence Theorem (Theorem 2.1)
// O ≅ C ≅ P with free conversion functors
// S-entropy is invariant under conversion

circuit oscillator {
  node X { mu: 1.0, concentration: 1.0 }
  node Y { mu: -1.0, concentration: 1.0 }

  edge X -> Y { conductance: 3.14 }
  edge Y -> X { conductance: 3.14 }
}

// Observe in default (oscillatory) representation
observe oscillator
let osc_Se = Se
let osc_Sk = Sk
let osc_St = St
let osc_R = R

// Convert to categorical representation
convert oscillator from osc to cat
observe oscillator
let cat_R = R

// Convert to partition representation
convert oscillator from cat to part
observe oscillator
let part_R = R

// Round-trip back to oscillatory
convert oscillator from part to osc
observe oscillator
let roundtrip_R = R

// Verify invariance: all R values should be identical
// (within floating-point tolerance)
```

### Expected Output

```
Oscillatory representation:
  R = 0.667
  Se = [0.5, 0.5], Sk = [1.0, 1.0], St = [1.0, 1.0]

Categorical representation:
  R = 0.667  (invariant ✓)

Partition representation:
  R = 0.667  (invariant ✓)

Round-trip (Part → Osc):
  R = 0.667  (recovered original ✓)

The triple (Se, Sk, St) is invariant under all three conversions.
This is the content of Corollary 2.3 (Free Conversion).
```

### Charts

**Chart 1: Representation Triangle**
- Type: Custom D3 SVG
- Layout: Equilateral triangle with three vertices labeled O, C, P
- Edges labeled with functor names: F_OC, F_CP, F_PO
- Animated arrows showing the conversion cycle
- Central value: "R = 0.667" (invariant)
- Dimensions: 300×260px

**Chart 2: Se-Sk-St Invariance Scatter**
- Type: `ScatterPlot`
- Three overlaid point sets (different marker shapes): circle=Osc, square=Cat, triangle=Part
- All three should overlap perfectly (invariance)
- Dimensions: 280×220px

---

## Example 6: Unconstrained Subtask — Local Infeasibility

### DSL Code

```sbs
// Unconstrained Subtask Theorem (Theorem 3.3)
// Global S-value imposes NO constraint on subtask S-values
// Locally impossible subtasks compose into globally correct expressions

circuit metabolic {
  node ATP     { mu: -30.5, concentration: 3.0 }
  node ADP     { mu: -20.0, concentration: 0.25 }
  node Pi      { mu: -10.0, concentration: 1.65 }
  node Glucose { mu: -917.0, concentration: 5.0 }
  node CO2     { mu: -394.0, concentration: 0.01 }

  edge ATP     -> ADP     { conductance: 50.0 }
  edge ADP     -> ATP     { conductance: 45.0 }
  edge Glucose -> CO2     { conductance: 2.0 }
  edge CO2     -> Glucose { conductance: 0.01 }
  edge ATP     -> Glucose { conductance: 0.5 }
}

// A locally-impossible catalyst has zero power alone
catalyst impossible_route { power: 0.0 }

// But a correction catalyst compensates
catalyst correction      { power: 0.8 }

// The cascade STILL converges — Theorem 4.3
// kappa_12 = 1 - (1-0.0)(1-0.8) = 0.8
cascade(impossible_route, correction)

observe metabolic
```

### Expected Output

```
Catalyst analysis:
  impossible_route: kappa = 0.000 (zero catalytic power alone)
  correction:       kappa = 0.800
  cascade:          kappa = 0.800 (correction fully compensates)

  Key insight: kappa_12 = 1 - (1-0)(1-0.8) = 1 - 0.2 = 0.8
  The zero-power catalyst contributes nothing, but does NOT block convergence.
  This is the "miracle principle" — local impossibility ≠ global impossibility.

Circuit observation:
  R = 0.69
  V = 1.00
```

### Charts

**Chart 1: Subtask Decomposition Diagram**
- Type: Custom D3 SVG (tree layout)
- Root node: "Global S = 3.0"
- Left child: "Subtask A: sin(3π/2) = -1" (red, locally infeasible)
- Right child: "Subtask B: 4" (green, overcompensates)
- Sum arrow pointing up: "-1 + 4 = 3 ✓"
- Dimensions: 400×200px

**Chart 2: Cascade Effect**
- Type: `BarChart`
- Two bars: "impossible_route (κ=0)" and "correction (κ=0.8)"
- Stacked representation showing cascade result κ=0.8
- Dimensions: 250×150px

---

## Example 7: Multi-Pathway Comparison (Reactome + KEGG)

### DSL Code

```sbs
// Compare glycolysis from two different databases
import glycolysis_reactome from "reactome:R-HSA-70171"
import glycolysis_kegg from "kegg:path:hsa00010"

// Observe both
observe glycolysis_reactome
let R_reactome = R
let V_reactome = V

observe glycolysis_kegg
let R_kegg = R
let V_kegg = V

// Apply same perturbation to both
perturb glycolysis_reactome { edge: 0, factor: 0.1 }
perturb glycolysis_kegg { edge: 0, factor: 0.1 }

observe glycolysis_reactome
let R_reactome_perturbed = R

observe glycolysis_kegg
let R_kegg_perturbed = R
```

### API Call Sequence

```
1. GET /api/sbs/search?q=glycolysis
   → Returns results from both Reactome and KEGG

2. GET /api/sbs/pathway?id=R-HSA-70171&source=reactome
   → SBML XML (Reactome format)

3. GET /api/sbs/pathway?id=hsa00010&source=kegg
   → KGML XML (KEGG format)

4. GET /api/sbs/compounds?ids=HMDB0000122,HMDB0000660,...
   → Thermodynamic data for both pathways

5. buildCircuitFromSBML() for each
   → Two circuit objects with potentially different node/edge counts
```

### Charts

**Chart 1: Side-by-Side Force Graphs**
- Type: Two `CircuitGraph` instances
- Left: Reactome glycolysis, Right: KEGG glycolysis
- Same layout forces for visual comparison
- Dimensions: 350×300px each

**Chart 2: Metric Comparison Table**
- Type: HTML table (styled with Tailwind)
- Columns: Metric | Reactome | KEGG
- Rows: R (healthy), V (healthy), R (perturbed), Node count, Edge count
- Highlighted cells where values differ significantly

**Chart 3: Heatmap of Se Differences**
- Type: `Heatmap` (from D3Chart.js)
- Rows: Common metabolite names
- Columns: [Reactome Se, KEGG Se, Difference]
- Color: Diverging scale (blue-white-red) for differences
- Dimensions: 350×250px

---

## Example 8: Recursive Triple Depth Analysis

### DSL Code

```sbs
// Recursive Triple Decomposition (Part V)
// At depth d, there are 3^d coordinate selections

circuit tca_cycle {
  node Acetyl_CoA   { mu: -31.4, concentration: 0.1 }
  node Citrate      { mu: -1166.0, concentration: 0.3 }
  node Isocitrate   { mu: -1160.0, concentration: 0.02 }
  node AlphaKG      { mu: -798.0, concentration: 0.05 }
  node Succinyl_CoA { mu: -690.0, concentration: 0.04 }
  node Succinate    { mu: -690.0, concentration: 0.3 }
  node Fumarate     { mu: -604.0, concentration: 0.1 }
  node Malate       { mu: -845.0, concentration: 0.2 }
  node OAA          { mu: -797.0, concentration: 0.01 }

  edge Acetyl_CoA   -> Citrate      { conductance: 5.0 }
  edge Citrate      -> Isocitrate   { conductance: 8.0 }
  edge Isocitrate   -> AlphaKG      { conductance: 3.0 }
  edge AlphaKG      -> Succinyl_CoA { conductance: 2.5 }
  edge Succinyl_CoA -> Succinate    { conductance: 6.0 }
  edge Succinate    -> Fumarate     { conductance: 4.0 }
  edge Fumarate     -> Malate       { conductance: 7.0 }
  edge Malate       -> OAA          { conductance: 3.5 }
  edge OAA          -> Acetyl_CoA   { conductance: 1.0 }
}

observe tca_cycle

// Depth 0: single S-value
let s_depth0 = R

// Depth 1: triple (k, t, e) — each itself an S-value
let s_k = triple(Sk, St, Se).k
let s_t = triple(Sk, St, Se).t
let s_e = triple(Sk, St, Se).e

// Depth 2: 9 values (kk, kt, ke, tk, tt, te, ek, et, ee)
// No privileged level — Theorem 5.4
```

### Charts

**Chart 1: Recursive Depth Tree**
- Type: Custom D3 SVG (tree layout, 3-ary)
- Depth 0: Root node with S-value
- Depth 1: 3 children (k, t, e) with sub-S-values
- Depth 2: 9 grandchildren (kk, kt, ke, ...) with sub-sub-S-values
- Node size proportional to S-value
- Color: Viridis scale
- Dimensions: 500×350px

**Chart 2: Scale Invariance Verification**
- Type: `ScatterPlot`
- X-axis: Depth
- Y-axis: Mean S-value at that depth
- Points at depth 0, 1, 2 showing scale invariance
- Error bars showing min/max at each depth
- Should be approximately constant (Theorem 5.3)
- Dimensions: 300×200px

---

## Implementation Notes for All Examples

### Chart Rendering Pipeline

All charts are rendered via D3 in React using this pattern:

```jsx
function ChartComponent({ data }) {
  const svgRef = useRef();

  useEffect(() => {
    if (!data || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();  // clear previous render

    const margin = { top: 20, right: 30, bottom: 40, left: 50 };
    const width = 400 - margin.left - margin.right;
    const height = 250 - margin.top - margin.bottom;

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // ... D3 rendering logic ...

  }, [data]);

  return <svg ref={svgRef} width={400} height={250} />;
}
```

### Auto-Compile Integration

When a user selects an example from the dropdown:
1. Code is loaded into the editor textarea
2. Auto-compile triggers after 300ms debounce
3. Compiler produces circuit + perturbations + observations
4. Shader solves the circuit
5. Metrics are extracted
6. Charts render with the metrics data
7. Output tab shows the summary

### Error Display

If an example fails (e.g., import resolution fails due to API timeout):
- Editor gutter shows red dots at error lines
- Output tab shows error messages with line numbers
- Metrics bar shows "Error" instead of values
- Charts remain blank with a "No data" message

### Performance Targets

| Example | Compile time | Solve time | Total render |
|---------|-------------|------------|-------------|
| Glycolysis (10 nodes) | < 5ms | < 1ms | < 50ms |
| TCA cycle (9 nodes) | < 5ms | < 1ms | < 50ms |
| Reactome import (~20 nodes) | < 10ms + API | < 2ms | < 100ms + API |
| EGFR signaling (8 nodes) | < 5ms | < 1ms | < 50ms |

API calls (Reactome, KEGG, HMDB, HuggingFace) add 200ms–2s depending on the service. The playground shows a loading spinner during API resolution.
