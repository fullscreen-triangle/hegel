export const SCRIPTS = {
  "glycolysis.sbs": {
    name: "Glycolysis Pathway",
    description: "10 metabolites, 9 enzymatic reactions with hexokinase perturbation",
    code: `// Glycolysis — 10 metabolites, 9 enzymatic reactions
// The canonical SBS demo circuit

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
}

// Observe the healthy baseline
observe glycolysis

// Disease: hexokinase deficiency — 90% reduction
perturb glycolysis { factor: 0.1 }

// Navigate backward from Pyruvate
navigate from Pyruvate
`,
  },
  "catalyst.sbs": {
    name: "Catalyst Convergence",
    description: "Geometric convergence via repeated catalyst application",
    code: `// Catalyst convergence — Theorem 5.8
// Residual S-distance decays as (1 - kappa)^n

circuit simple {
  node A { mu: 10.0, concentration: 1.0 }
  node B { mu: 5.0, concentration: 0.5 }
  node C { mu: 1.0, concentration: 0.1 }

  edge A -> B { conductance: 2.0 }
  edge B -> C { conductance: 1.5 }
  edge C -> A { conductance: 0.5 }
}

catalyst drug_mild   { power: 0.3 }
catalyst drug_strong { power: 0.7 }

// Cascade: kappa_12 = 1 - (1-0.3)(1-0.7) = 0.79
cascade(drug_mild, drug_strong)

observe simple
`,
  },
  "egfr.sbs": {
    name: "EGFR Signaling",
    description: "Signal transduction cascade with oncogenic RAS mutation",
    code: `// EGFR/MAPK signaling cascade
// Oncogenic RAS mutation — constitutive activation

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

// Oncogenic RAS mutation — 5x gain
perturb egfr_signaling { edge: "EGFR->RAS", factor: 5.0 }

observe egfr_signaling

// Find sparse drug targets
restore egfr_signaling

navigate from CyclinD
`,
  },
  "tca.sbs": {
    name: "TCA Cycle",
    description: "Citric acid cycle with IDH perturbation (glioma model)",
    code: `// TCA Cycle — 9 metabolites in circular topology
// IDH mutation model (common in gliomas)

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

// IDH mutation — 85% loss of activity
perturb tca_cycle { edge: "Isocitrate->AlphaKG", factor: 0.15 }

observe tca_cycle
restore tca_cycle
`,
  },
  "triple.sbs": {
    name: "Triple Equivalence",
    description: "O ≅ C ≅ P representation conversion invariance",
    code: `// Triple Equivalence — Theorem 2.1
// S-entropy is invariant under representation conversion

circuit oscillator {
  node X { mu: 1.0, concentration: 1.0 }
  node Y { mu: -1.0, concentration: 1.0 }

  edge X -> Y { conductance: 3.14 }
  edge Y -> X { conductance: 3.14 }
}

observe oscillator
let osc_R = R

convert oscillator from osc to cat
observe oscillator
let cat_R = R

convert oscillator from cat to part
observe oscillator
let part_R = R

// Round-trip: Part -> Osc
convert oscillator from part to osc
observe oscillator
let roundtrip_R = R
`,
  },
  "drug-design.sbs": {
    name: "l1-Optimal Drug Design",
    description: "Sparse perturbation to restore flux visibility above 0.9",
    code: `// l1-Optimal Drug Design
// Find sparsest edge set to restore V > 0.9

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

observe signaling

// Receptor desensitization
perturb signaling { factor: 0.05 }

// l1-optimal restore
restore signaling

navigate from CREB
`,
  },
};

export const DEFAULT_SCRIPT = "glycolysis.sbs";
