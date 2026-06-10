export const SCRIPTS = {
  "glycolysis.sbs": {
    name: "Glycolysis — Reactome Import",
    description: "Reactome R-HSA-70171 pathway with hexokinase deficiency perturbation",
    code: `// Glycolysis — imported from Reactome pathway database
// Source: https://reactome.org/content/detail/R-HSA-70171
// All species and kinetic parameters fetched from Reactome + BRENDA

import glycolysis from "reactome/R-HSA-70171"
import hk1 from "uniprot/P19367"
import glucose from "hmdb/HMDB0000122"
import pyruvate from "hmdb/HMDB0000243"

// Build circuit from Reactome pathway data
// Species concentrations from HMDB, kinetics from BRENDA via UniProt
circuit glycolysis_pathway {
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

  // Reaction conductances from BRENDA kcat values
  // G = kcat * [S] / RT (RT = 2.478 kJ/mol at 310K)
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

// Observe healthy baseline
observe glycolysis_pathway

// Disease: hexokinase (HK1 EC:2.7.1.1) deficiency — 90% loss
perturb glycolysis_pathway { factor: 0.1 }

navigate from Pyruvate
`,
  },
  "tca.sbs": {
    name: "TCA Cycle — Reactome Import",
    description: "Reactome R-HSA-71403 citric acid cycle with IDH2 glioma mutation",
    code: `// TCA Cycle — imported from Reactome pathway database
// Source: https://reactome.org/content/detail/R-HSA-71403
// IDH2 mutation is common in low-grade gliomas (WHO grade II-III)

import tca from "reactome/R-HSA-71403"
import citrate from "hmdb/HMDB0001341"
import oaa from "hmdb/HMDB0000208"

circuit tca_cycle {
  node Acetyl_CoA   { mu: -31.4, concentration: 0.1, compartment: "mitochondria" }
  node Citrate      { mu: -1166.0, concentration: 0.3, compartment: "mitochondria" }
  node Isocitrate   { mu: -1160.0, concentration: 0.02, compartment: "mitochondria" }
  node AlphaKG      { mu: -798.0, concentration: 0.05, compartment: "mitochondria" }
  node Succinyl_CoA { mu: -690.0, concentration: 0.04, compartment: "mitochondria" }
  node Succinate    { mu: -690.0, concentration: 0.3, compartment: "mitochondria" }
  node Fumarate     { mu: -604.0, concentration: 0.1, compartment: "mitochondria" }
  node Malate       { mu: -845.0, concentration: 0.2, compartment: "mitochondria" }
  node OAA          { mu: -797.0, concentration: 0.01, compartment: "mitochondria" }

  // EC numbers from KEGG enzyme database
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

// IDH2 R172K mutation — neomorphic: 85% loss of native activity
// Produces 2-hydroxyglutarate (oncometabolite)
perturb tca_cycle { edge: "Isocitrate->AlphaKG", factor: 0.15 }

observe tca_cycle
restore tca_cycle
`,
  },
  "egfr.sbs": {
    name: "EGFR/MAPK — KEGG Import",
    description: "KEGG hsa04010 MAPK cascade with oncogenic KRAS G12V mutation",
    code: `// EGFR/MAPK Signaling — imported from KEGG pathway database
// Source: https://www.kegg.jp/pathway/hsa04010
// KRAS G12V is the most common oncogenic driver in pancreatic cancer

import mapk from "kegg/hsa04010"

circuit egfr_mapk {
  node EGF      { mu: 0.0, concentration: 0.001, compartment: "extracellular" }
  node EGFR     { mu: -5.0, concentration: 0.1, compartment: "membrane" }
  node GRB2     { mu: -7.0, concentration: 0.2, compartment: "membrane" }
  node SOS      { mu: -8.0, concentration: 0.15, compartment: "cytoplasm" }
  node RAS      { mu: -10.0, concentration: 0.5, compartment: "membrane" }
  node RAF      { mu: -12.0, concentration: 0.3, compartment: "cytoplasm" }
  node MEK      { mu: -15.0, concentration: 0.4, compartment: "cytoplasm" }
  node ERK      { mu: -18.0, concentration: 0.6, compartment: "cytoplasm" }
  node MYC      { mu: -22.0, concentration: 0.05, compartment: "nucleus" }
  node CyclinD  { mu: -25.0, concentration: 0.08, compartment: "nucleus" }

  edge EGF   -> EGFR    { conductance: 15.0 }
  edge EGFR  -> GRB2    { conductance: 12.0 }
  edge GRB2  -> SOS     { conductance: 10.0 }
  edge SOS   -> RAS     { conductance: 9.0 }
  edge RAS   -> RAF     { conductance: 8.0 }
  edge RAF   -> MEK     { conductance: 7.0 }
  edge MEK   -> ERK     { conductance: 9.0 }
  edge ERK   -> MYC     { conductance: 5.0 }
  edge MYC   -> CyclinD { conductance: 3.0 }

  // Negative feedback loops (KEGG map edges)
  edge ERK    -> EGFR   { conductance: 2.0 }
  edge CyclinD -> EGF   { conductance: 0.5 }
}

observe egfr_mapk

// KRAS G12V — constitutive activation, 5x gain
perturb egfr_mapk { edge: "SOS->RAS", factor: 5.0 }

observe egfr_mapk
restore egfr_mapk
navigate from CyclinD
`,
  },
  "oxphos.sbs": {
    name: "Oxidative Phosphorylation — KEGG Import",
    description: "KEGG hsa00190 electron transport chain with Complex I inhibition",
    code: `// Oxidative Phosphorylation — KEGG pathway hsa00190
// Source: https://www.kegg.jp/pathway/hsa00190
// Models the electron transport chain + ATP synthase

import oxphos from "kegg/hsa00190"
import atp from "hmdb/HMDB0000538"

circuit electron_transport {
  node NADH  { mu: -320.0, concentration: 0.1, compartment: "mitochondria_matrix" }
  node CoQ   { mu: -50.0, concentration: 0.05, compartment: "inner_membrane" }
  node CytC  { mu: 250.0, concentration: 0.03, compartment: "ims" }
  node O2    { mu: 815.0, concentration: 0.26, compartment: "mitochondria_matrix" }
  node H2O   { mu: -237.0, concentration: 55.5, compartment: "mitochondria_matrix" }
  node ADP   { mu: -1906.0, concentration: 1.3, compartment: "mitochondria_matrix" }
  node ATP   { mu: -2292.0, concentration: 3.2, compartment: "mitochondria_matrix" }
  node Pi    { mu: -1018.0, concentration: 5.0, compartment: "mitochondria_matrix" }

  // Electron transport complexes
  edge NADH -> CoQ   { conductance: 12.0 }
  edge CoQ  -> CytC  { conductance: 10.0 }
  edge CytC -> O2    { conductance: 8.0 }
  edge O2   -> H2O   { conductance: 15.0 }

  // ATP synthase (F1-Fo)
  edge ADP  -> ATP   { conductance: 20.0 }
  edge ATP  -> ADP   { conductance: 0.5 }

  // Proton motive force coupling
  edge NADH -> ADP   { conductance: 3.0 }
  edge Pi   -> ATP   { conductance: 18.0 }
}

observe electron_transport

// Rotenone inhibition — Complex I block (70% reduction)
// Common model for Parkinson's disease mitochondrial dysfunction
perturb electron_transport { edge: "NADH->CoQ", factor: 0.3 }

observe electron_transport
navigate from ATP
`,
  },
  "catalyst.sbs": {
    name: "Catalyst Composition — HuggingFace Models",
    description: "ESM-2 + AlphaFold2 cascade with geometric convergence (Theorem 5.8)",
    code: `// Catalyst Composition — using HuggingFace ML models
// Demonstrates the unconstrained subtask theorem:
// Multiple ML models compose as catalysts with geometric convergence

import esm2 from "huggingface/esm2_t33_650M"
import alphafold from "huggingface/alphafold2"
import cellpose from "huggingface/cellpose_cyto2"

// Simple circuit to demonstrate catalyst composition
circuit protein_analysis {
  node Sequence     { mu: 10.0, concentration: 1.0 }
  node Embedding    { mu: 5.0, concentration: 0.5 }
  node Structure    { mu: 1.0, concentration: 0.1 }

  edge Sequence  -> Embedding { conductance: 2.0 }
  edge Embedding -> Structure { conductance: 1.5 }
  edge Structure -> Sequence  { conductance: 0.5 }
}

// ESM-2: kappa = 0.82 (strong protein language model)
catalyst esm2_catalyst { power: 0.82 }

// AlphaFold2: kappa = 0.91 (structure prediction)
catalyst af2_catalyst { power: 0.91 }

// Cascade: kappa_12 = 1 - (1-0.82)(1-0.91) = 0.9838
// Two HuggingFace models compose to near-perfect catalysis
cascade(esm2_catalyst, af2_catalyst)

observe protein_analysis
`,
  },
  "drug-design.sbs": {
    name: "Drug Design — Multi-Database",
    description: "l1-optimal perturbation using Reactome + UniProt + HMDB data",
    code: `// l1-Optimal Drug Design — integrating multiple databases
// Reactome topology + UniProt kinetics + HMDB thermodynamics
// Finds the sparsest drug target set to restore flux visibility

import pathway from "reactome/R-HSA-70171"
import pk from "uniprot/P14618"
import pgk from "uniprot/P00558"

circuit drug_target {
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

observe drug_target

// Receptor desensitization — 95% reduction
perturb drug_target { factor: 0.05 }

// l1-optimal restore: find sparsest perturbation set
restore drug_target

navigate from CREB
`,
  },
  "atp-synthase.sbs": {
    name: "ATP Synthase — GLB Structure",
    description: "GLB 3D model + KEGG oxphos pathway + AllenCell morphology",
    code: `// ATP Synthase — 3D structural context from GLB model
// Combines: GLB geometry (PDB 5ARA) + KEGG pathway + AllenCell morphology
// The GLB provides spatial anchoring for the circuit nodes

import structure from "glb/atp_synthase"
import oxphos from "kegg/hsa00190"
import cell from "allencell/AICS-12"
import af2 from "huggingface/alphafold2"

// Circuit for ATP synthase rotary mechanism
// Spatial positions from the GLB scene graph
circuit atp_synthase_rotor {
  node H_intermembrane { mu: 0.0, concentration: 0.0001, compartment: "ims" }
  node H_matrix        { mu: -18.0, concentration: 0.00001, compartment: "mitochondria_matrix" }
  node ADP             { mu: -1906.0, concentration: 1.3, compartment: "mitochondria_matrix" }
  node Pi              { mu: -1018.0, concentration: 5.0, compartment: "mitochondria_matrix" }
  node ATP             { mu: -2292.0, concentration: 3.2, compartment: "mitochondria_matrix" }
  node Fo_rotor        { mu: -5.0, concentration: 1.0, compartment: "inner_membrane" }
  node F1_alpha        { mu: -8.0, concentration: 1.0, compartment: "mitochondria_matrix" }
  node F1_beta         { mu: -12.0, concentration: 1.0, compartment: "mitochondria_matrix" }

  // Proton translocation through Fo
  edge H_intermembrane -> Fo_rotor { conductance: 25.0 }
  edge Fo_rotor -> H_matrix        { conductance: 20.0 }

  // Mechanical coupling (rotation drives conformational change)
  edge Fo_rotor  -> F1_alpha { conductance: 15.0 }
  edge F1_alpha  -> F1_beta  { conductance: 12.0 }

  // Catalytic cycle in F1 beta subunit
  edge ADP -> F1_beta { conductance: 10.0 }
  edge Pi  -> F1_beta { conductance: 8.0 }
  edge F1_beta -> ATP  { conductance: 18.0 }

  // ATP release + ADP rebinding
  edge ATP -> ADP { conductance: 0.3 }
}

observe atp_synthase_rotor

// Oligomycin — blocks Fo proton channel (90% reduction)
perturb atp_synthase_rotor { edge: "H_intermembrane->Fo_rotor", factor: 0.1 }

observe atp_synthase_rotor
navigate from ATP
`,
  },
};

export const DEFAULT_SCRIPT = "glycolysis.sbs";
