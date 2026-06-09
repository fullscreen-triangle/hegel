export const EXAMPLES = {
  glycolysis: {
    name: 'Glycolysis Pathway',
    description: 'Classic 10-step glycolysis circuit with disease perturbation',
    code: `// Glycolysis — the canonical SBS demo circuit
// Nodes are metabolites, edges are enzymatic reactions
// Conductance = rate * [substrate] / RT

circuit glycolysis {
  // Metabolites with chemical potentials (kJ/mol)
  node Glucose     { mu: -917.0, concentration: 5.0, compartment: "cytoplasm" }
  node G6P         { mu: -1760.0, concentration: 0.083, compartment: "cytoplasm" }
  node F6P         { mu: -1755.0, concentration: 0.014, compartment: "cytoplasm" }
  node FBP         { mu: -2600.0, concentration: 0.031, compartment: "cytoplasm" }
  node G3P         { mu: -1290.0, concentration: 0.14, compartment: "cytoplasm" }
  node BPG13       { mu: -2356.0, concentration: 0.001, compartment: "cytoplasm" }
  node PG3         { mu: -1515.0, concentration: 0.1, compartment: "cytoplasm" }
  node PG2         { mu: -1510.0, concentration: 0.03, compartment: "cytoplasm" }
  node PEP         { mu: -1263.0, concentration: 0.023, compartment: "cytoplasm" }
  node Pyruvate    { mu: -472.0, concentration: 0.051, compartment: "cytoplasm" }

  // Enzymatic reactions
  edge Glucose  -> G6P      { rate: 230.0, conductance: 464.1 }
  edge G6P      -> F6P      { rate: 100.0, conductance: 3.35 }
  edge F6P      -> FBP      { rate: 150.0, conductance: 0.85 }
  edge FBP      -> G3P      { rate: 80.0, conductance: 1.0 }
  edge G3P      -> BPG13    { rate: 200.0, conductance: 11.3 }
  edge BPG13    -> PG3      { rate: 300.0, conductance: 0.12 }
  edge PG3      -> PG2      { rate: 180.0, conductance: 7.27 }
  edge PG2      -> PEP      { rate: 100.0, conductance: 1.21 }
  edge PEP      -> Pyruvate  { rate: 500.0, conductance: 4.64 }

  // Reverse reactions (near-equilibrium steps)
  edge G6P  -> Glucose  { rate: 20.0, conductance: 0.67 }
  edge F6P  -> G6P      { rate: 80.0, conductance: 0.45 }
  edge G3P  -> FBP      { rate: 30.0, conductance: 1.69 }
  edge PG3  -> BPG13    { rate: 250.0, conductance: 10.1 }
  edge PG2  -> PG3      { rate: 150.0, conductance: 1.82 }
  edge PEP  -> PG2      { rate: 70.0, conductance: 0.65 }
}

// Observe the healthy baseline
observe glycolysis

// Disease: hexokinase deficiency — 90% reduction
perturb glycolysis { factor: 0.1 }

// Check metrics after perturbation
let disease_R = R
let disease_V = V
`,
  },

  catalyst_convergence: {
    name: 'Catalyst Convergence',
    description: 'Demonstrates geometric convergence via repeated catalyst application',
    code: `// Catalyst convergence — Theorem 5.8 of the S-entropy calculus
// Residual S-distance decays as (1 - kappa)^n

circuit simple {
  node A { mu: 10.0, concentration: 1.0 }
  node B { mu: 5.0, concentration: 0.5 }
  node C { mu: 1.0, concentration: 0.1 }

  edge A -> B { conductance: 2.0 }
  edge B -> C { conductance: 1.5 }
  edge C -> A { conductance: 0.5 }
}

// Define catalysts with known powers
catalyst drug_mild   { power: 0.3 }
catalyst drug_strong { power: 0.7 }

// Cascade composition: kappa_12 = 1 - (1-k1)(1-k2)
// Expected: 1 - (1-0.3)(1-0.7) = 1 - 0.21 = 0.79
cascade(drug_mild, drug_strong)

// Repeated application shows geometric decay
observe simple
`,
  },

  triple_equivalence: {
    name: 'Triple Equivalence',
    description: 'Conversion between Oscillatory, Categorical, and Partition representations',
    code: `// Triple Equivalence — Theorem 2.1
// O ≅ C ≅ P with free conversion functors
// F_OC: Osc -> Cat,  F_CP: Cat -> Part,  F_PO: Part -> Osc

circuit oscillator {
  // A simple oscillatory circuit
  node X { mu: 1.0, concentration: 1.0 }
  node Y { mu: -1.0, concentration: 1.0 }

  edge X -> Y { conductance: 3.14 }
  edge Y -> X { conductance: 3.14 }
}

// Observe in default (oscillatory) representation
observe oscillator

// Convert to categorical representation
convert oscillator from osc to cat

// Convert to partition representation
convert oscillator from cat to part

// Round-trip: should recover original
convert oscillator from part to osc

// The S-entropy triple (Se, Sk, St) is invariant
// under all conversions — this is the content of
// Corollary 2.3 (Free Conversion)
`,
  },

  unconstrained_subtask: {
    name: 'Unconstrained Subtask',
    description: 'Local infeasibility composing into global feasibility',
    code: `// Unconstrained Subtask Theorem (Theorem 3.3)
// Global S-value imposes NO constraint on subtask S-values
// "Miracle principle": locally impossible subtasks
// can compose into globally correct expressions

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

// The expression 3 = 1 + 1 + 1 has the same S-value
// as 3 = sin(3pi/2) + 4, despite the subtask
// sin(3pi/2) = -1 being "wrong direction"
//
// In circuit terms: a locally-impossible catalyst
// (Definition 4.4) can have positive catalytic power

catalyst impossible_route { power: 0.0 }
catalyst correction      { power: 0.8 }

// The cascade still converges — Theorem 4.3
cascade(impossible_route, correction)

observe metabolic
`,
  },

  drug_design: {
    name: 'l1-Optimal Drug Design',
    description: 'Sparse perturbation to restore flux visibility above 0.9',
    code: `// l1-Optimal Drug Design
// Find the sparsest set of edge perturbations
// that restores visibility V > 0.9

circuit signaling {
  node Receptor  { mu: 0.0, concentration: 1.0, compartment: "membrane" }
  node GProtein  { mu: -5.0, concentration: 0.8, compartment: "membrane" }
  node Adenylate { mu: -10.0, concentration: 0.5, compartment: "cytoplasm" }
  node cAMP      { mu: -15.0, concentration: 0.1, compartment: "cytoplasm" }
  node PKA       { mu: -20.0, concentration: 0.3, compartment: "cytoplasm" }
  node CREB      { mu: -25.0, concentration: 0.2, compartment: "nucleus" }

  edge Receptor  -> GProtein  { conductance: 10.0 }
  edge GProtein  -> Adenylate { conductance: 8.0 }
  edge Adenylate -> cAMP      { conductance: 12.0 }
  edge cAMP      -> PKA       { conductance: 6.0 }
  edge PKA       -> CREB      { conductance: 4.0 }
  edge CREB      -> Receptor  { conductance: 1.0 }
}

// Healthy baseline
observe signaling

// Disease state: receptor desensitization
perturb signaling { factor: 0.05 }

// The l1-optimal restore finds the minimum
// number of edges to perturb to recover V > 0.9
restore signaling

// Navigate backward from CREB to find
// the rate-limiting step
navigate from CREB
`,
  },

  recursive_triple: {
    name: 'Recursive Triple',
    description: 'S-entropy coordinates at multiple recursion depths',
    code: `// Recursive Triple Decomposition (Part V)
// Every S-value decomposes into (Sk, St, Se) at depth d
// yielding 3^d coordinate selections

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

// At depth 0: the circuit has a single S-value
observe tca_cycle

// The recursive triple decomposes this into
// triple(Sk, St, Se) — each itself an S-value
// of its sub-problem (Theorem 5.4: No Privileged Level)
//
// At depth d, there are 3^d coordinate selections
// Depth 1: 3 values  (k, t, e)
// Depth 2: 9 values  (kk, kt, ke, tk, tt, te, ek, et, ee)
// Depth 3: 27 values
//
// The scale operator sigma_{d->d+1} preserves S-value
// (Theorem 5.3: Scale Invariance)
`,
  },
};

export const DEFAULT_EXAMPLE = 'glycolysis';
