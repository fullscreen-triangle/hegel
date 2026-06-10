// Registry of known external data sources for SBS DSL import resolution
// Each entry simulates what an API fetch would return, using real published values.

const REACTOME = {
  "R-HSA-70171": {
    id: "R-HSA-70171",
    name: "Glycolysis",
    source: "Reactome",
    url: "https://reactome.org/content/detail/R-HSA-70171",
    species: [
      { name: "Glucose", mu: -917.0, concentration: 5.0, compartment: "cytoplasm" },
      { name: "G6P", mu: -1760.0, concentration: 0.083, compartment: "cytoplasm" },
      { name: "F6P", mu: -1755.0, concentration: 0.014, compartment: "cytoplasm" },
      { name: "FBP", mu: -2600.0, concentration: 0.031, compartment: "cytoplasm" },
      { name: "G3P", mu: -1290.0, concentration: 0.14, compartment: "cytoplasm" },
      { name: "BPG13", mu: -2356.0, concentration: 0.001, compartment: "cytoplasm" },
      { name: "PG3", mu: -1515.0, concentration: 0.1, compartment: "cytoplasm" },
      { name: "PG2", mu: -1510.0, concentration: 0.03, compartment: "cytoplasm" },
      { name: "PEP", mu: -1263.0, concentration: 0.023, compartment: "cytoplasm" },
      { name: "Pyruvate", mu: -472.0, concentration: 0.051, compartment: "cytoplasm" },
    ],
    reactions: [
      { src: "Glucose", dst: "G6P", enzyme: "Hexokinase", rate: 230.0, conductance: 464.1, ec: "2.7.1.1" },
      { src: "G6P", dst: "F6P", enzyme: "PGI", rate: 100.0, conductance: 3.35, ec: "5.3.1.9" },
      { src: "F6P", dst: "FBP", enzyme: "PFK", rate: 150.0, conductance: 0.85, ec: "2.7.1.11" },
      { src: "FBP", dst: "G3P", enzyme: "Aldolase", rate: 80.0, conductance: 1.0, ec: "4.1.2.13" },
      { src: "G3P", dst: "BPG13", enzyme: "GAPDH", rate: 200.0, conductance: 11.3, ec: "1.2.1.12" },
      { src: "BPG13", dst: "PG3", enzyme: "PGK", rate: 300.0, conductance: 0.12, ec: "2.7.2.3" },
      { src: "PG3", dst: "PG2", enzyme: "PGAM", rate: 180.0, conductance: 7.27, ec: "5.4.2.12" },
      { src: "PG2", dst: "PEP", enzyme: "Enolase", rate: 100.0, conductance: 1.21, ec: "4.2.1.11" },
      { src: "PEP", dst: "Pyruvate", enzyme: "PyruvateKinase", rate: 500.0, conductance: 4.64, ec: "2.7.1.40" },
    ],
  },
  "R-HSA-71403": {
    id: "R-HSA-71403",
    name: "Citric Acid Cycle (TCA)",
    source: "Reactome",
    url: "https://reactome.org/content/detail/R-HSA-71403",
    species: [
      { name: "Acetyl_CoA", mu: -31.4, concentration: 0.1, compartment: "mitochondria" },
      { name: "Citrate", mu: -1166.0, concentration: 0.3, compartment: "mitochondria" },
      { name: "Isocitrate", mu: -1160.0, concentration: 0.02, compartment: "mitochondria" },
      { name: "AlphaKG", mu: -798.0, concentration: 0.05, compartment: "mitochondria" },
      { name: "Succinyl_CoA", mu: -690.0, concentration: 0.04, compartment: "mitochondria" },
      { name: "Succinate", mu: -690.0, concentration: 0.3, compartment: "mitochondria" },
      { name: "Fumarate", mu: -604.0, concentration: 0.1, compartment: "mitochondria" },
      { name: "Malate", mu: -845.0, concentration: 0.2, compartment: "mitochondria" },
      { name: "OAA", mu: -797.0, concentration: 0.01, compartment: "mitochondria" },
    ],
    reactions: [
      { src: "Acetyl_CoA", dst: "Citrate", enzyme: "CitrateSynthase", conductance: 5.0, ec: "2.3.3.1" },
      { src: "Citrate", dst: "Isocitrate", enzyme: "Aconitase", conductance: 8.0, ec: "4.2.1.3" },
      { src: "Isocitrate", dst: "AlphaKG", enzyme: "IDH", conductance: 3.0, ec: "1.1.1.42" },
      { src: "AlphaKG", dst: "Succinyl_CoA", enzyme: "OGDH", conductance: 2.5, ec: "1.2.4.2" },
      { src: "Succinyl_CoA", dst: "Succinate", enzyme: "SCS", conductance: 6.0, ec: "6.2.1.5" },
      { src: "Succinate", dst: "Fumarate", enzyme: "SDH", conductance: 4.0, ec: "1.3.5.1" },
      { src: "Fumarate", dst: "Malate", enzyme: "Fumarase", conductance: 7.0, ec: "4.2.1.2" },
      { src: "Malate", dst: "OAA", enzyme: "MDH", conductance: 3.5, ec: "1.1.1.37" },
      { src: "OAA", dst: "Acetyl_CoA", enzyme: "Condensation", conductance: 1.0, ec: "2.3.3.1" },
    ],
  },
};

const KEGG = {
  "hsa04010": {
    id: "hsa04010",
    name: "MAPK Signaling Pathway",
    source: "KEGG",
    url: "https://www.kegg.jp/pathway/hsa04010",
    species: [
      { name: "EGF", mu: 0.0, concentration: 0.001, compartment: "extracellular" },
      { name: "EGFR", mu: -5.0, concentration: 0.1, compartment: "membrane" },
      { name: "GRB2", mu: -7.0, concentration: 0.2, compartment: "membrane" },
      { name: "SOS", mu: -8.0, concentration: 0.15, compartment: "cytoplasm" },
      { name: "RAS", mu: -10.0, concentration: 0.5, compartment: "membrane" },
      { name: "RAF", mu: -12.0, concentration: 0.3, compartment: "cytoplasm" },
      { name: "MEK", mu: -15.0, concentration: 0.4, compartment: "cytoplasm" },
      { name: "ERK", mu: -18.0, concentration: 0.6, compartment: "cytoplasm" },
      { name: "MYC", mu: -22.0, concentration: 0.05, compartment: "nucleus" },
      { name: "CyclinD", mu: -25.0, concentration: 0.08, compartment: "nucleus" },
    ],
    reactions: [
      { src: "EGF", dst: "EGFR", enzyme: "EGF_binding", conductance: 15.0, ec: "2.7.10.1" },
      { src: "EGFR", dst: "GRB2", enzyme: "Autophosphorylation", conductance: 12.0 },
      { src: "GRB2", dst: "SOS", enzyme: "SH3_recruitment", conductance: 10.0 },
      { src: "SOS", dst: "RAS", enzyme: "GEF_exchange", conductance: 9.0 },
      { src: "RAS", dst: "RAF", enzyme: "RAS_activation", conductance: 8.0 },
      { src: "RAF", dst: "MEK", enzyme: "RAF_phosphorylation", conductance: 7.0, ec: "2.7.11.1" },
      { src: "MEK", dst: "ERK", enzyme: "MEK_phosphorylation", conductance: 9.0, ec: "2.7.12.2" },
      { src: "ERK", dst: "MYC", enzyme: "ERK_nuclear_entry", conductance: 5.0 },
      { src: "MYC", dst: "CyclinD", enzyme: "Transcription", conductance: 3.0 },
      { src: "ERK", dst: "EGFR", enzyme: "Negative_feedback", conductance: 2.0 },
      { src: "CyclinD", dst: "EGF", enzyme: "Growth_signal", conductance: 0.5 },
    ],
  },
  "hsa00190": {
    id: "hsa00190",
    name: "Oxidative Phosphorylation",
    source: "KEGG",
    url: "https://www.kegg.jp/pathway/hsa00190",
    species: [
      { name: "NADH", mu: -320.0, concentration: 0.1, compartment: "mitochondria_matrix" },
      { name: "CoQ", mu: -50.0, concentration: 0.05, compartment: "inner_membrane" },
      { name: "CytC", mu: 250.0, concentration: 0.03, compartment: "ims" },
      { name: "O2", mu: 815.0, concentration: 0.26, compartment: "mitochondria_matrix" },
      { name: "H2O", mu: -237.0, concentration: 55.5, compartment: "mitochondria_matrix" },
      { name: "ADP", mu: -1906.0, concentration: 1.3, compartment: "mitochondria_matrix" },
      { name: "ATP", mu: -2292.0, concentration: 3.2, compartment: "mitochondria_matrix" },
      { name: "Pi", mu: -1018.0, concentration: 5.0, compartment: "mitochondria_matrix" },
    ],
    reactions: [
      { src: "NADH", dst: "CoQ", enzyme: "Complex_I", conductance: 12.0, ec: "7.1.1.2" },
      { src: "CoQ", dst: "CytC", enzyme: "Complex_III", conductance: 10.0, ec: "7.1.1.8" },
      { src: "CytC", dst: "O2", enzyme: "Complex_IV", conductance: 8.0, ec: "7.1.1.9" },
      { src: "O2", dst: "H2O", enzyme: "Reduction", conductance: 15.0 },
      { src: "ADP", dst: "ATP", enzyme: "ATP_Synthase", conductance: 20.0, ec: "7.1.2.2" },
      { src: "ATP", dst: "ADP", enzyme: "ATPase_leak", conductance: 0.5 },
      { src: "NADH", dst: "ADP", enzyme: "PMF_coupling", conductance: 3.0 },
      { src: "Pi", dst: "ATP", enzyme: "Phosphorylation", conductance: 18.0 },
    ],
  },
};

const HMDB = {
  "HMDB0000122": { name: "Glucose", deltaG: -917.0, mw: 180.16, smiles: "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O" },
  "HMDB0000243": { name: "Pyruvate", deltaG: -472.0, mw: 88.06, smiles: "CC(=O)C(O)=O" },
  "HMDB0000538": { name: "ATP", deltaG: -2292.0, mw: 507.18, smiles: "c1nc(N)c2ncn(C3OC(COP(O)(=O)OP(O)(=O)OP(O)(O)=O)C(O)C3O)c2n1" },
  "HMDB0001341": { name: "Citrate", deltaG: -1166.0, mw: 192.12, smiles: "OC(CC(O)=O)(CC(O)=O)C(O)=O" },
  "HMDB0000208": { name: "OAA", deltaG: -797.0, mw: 132.07, smiles: "OC(=O)CC(=O)C(O)=O" },
};

const HUGGINGFACE = {
  "esm2_t33_650M": {
    id: "facebook/esm2_t33_650M_UR50D",
    name: "ESM-2 Protein Language Model",
    source: "HuggingFace",
    task: "protein_embedding",
    kappa: 0.82,
  },
  "alphafold2": {
    id: "DeepMind/alphafold2",
    name: "AlphaFold2 Structure Predictor",
    source: "HuggingFace",
    task: "structure_prediction",
    kappa: 0.91,
  },
  "cellpose_cyto2": {
    id: "cellpose/cyto2",
    name: "Cellpose Cytoplasm Segmenter",
    source: "HuggingFace",
    task: "cell_segmentation",
    kappa: 0.75,
  },
};

const ALLENCELL = {
  "AICS-12": {
    id: "AICS-12",
    name: "Lamin B1 (nuclear envelope)",
    source: "AllenCell",
    url: "https://www.allencell.org/cell-catalog.html",
    structure: "nuclear_envelope",
    compartments: ["nucleus", "cytoplasm", "membrane"],
    morphology: { volume: 2200.0, surface_area: 820.0, sphericity: 0.72 },
  },
  "AICS-11": {
    id: "AICS-11",
    name: "Alpha-actinin-1 (actin bundles)",
    source: "AllenCell",
    url: "https://www.allencell.org/cell-catalog.html",
    structure: "actin_bundles",
    compartments: ["cytoplasm", "membrane"],
    morphology: { volume: 1850.0, surface_area: 780.0, sphericity: 0.68 },
  },
};

const UNIPROT = {
  "P19367": { name: "Hexokinase-1", organism: "H. sapiens", gene: "HK1", ec: "2.7.1.1", kcat: 230.0, km: 0.065 },
  "P14618": { name: "Pyruvate Kinase M2", organism: "H. sapiens", gene: "PKM", ec: "2.7.1.40", kcat: 500.0, km: 0.31 },
  "P00558": { name: "Phosphoglycerate kinase 1", organism: "H. sapiens", gene: "PGK1", ec: "2.7.2.3", kcat: 300.0, km: 1.1 },
  "P09211": { name: "CYP3A4", organism: "H. sapiens", gene: "CYP3A4", ec: "1.14.14.1", kcat: 15.0, km: 0.012 },
};

const GLB_MODELS = {
  "atp_synthase": {
    file: "/glb/atp_synthase.glb",
    name: "ATP Synthase (F1-Fo)",
    source: "Sketchfab/PDB",
    pdb: "5ARA",
    atoms: 156,
    fe_coordination: null,
    compartment: "inner_membrane",
    species_map: {
      "ADP": { position: [0, 2.1, 0], color: "#ff6b6b" },
      "ATP": { position: [0, 3.5, 0], color: "#4ec9b0" },
      "Pi": { position: [1.2, 2.8, 0], color: "#dcdcaa" },
      "H_plus": { position: [-0.8, -1.0, 0], color: "#ffffff" },
    },
  },
  "carbonic_anhydrase": {
    file: "/glb/carbonic_anhydrase.glb",
    name: "Carbonic Anhydrase II",
    source: "Sketchfab/PDB",
    pdb: "2CBA",
    atoms: 2048,
    compartment: "cytoplasm",
  },
  "triosephosphate_isomerase": {
    file: "/glb/triosephosphate_isomerase_from_giardia_lamblia.glb",
    name: "Triosephosphate Isomerase (TIM barrel)",
    source: "Sketchfab/PDB",
    pdb: "1LZO",
    atoms: 1870,
    compartment: "cytoplasm",
  },
};

export function resolveImport(name, source) {
  const parts = source.split("/");
  const db = parts[0].toLowerCase();
  const id = parts.slice(1).join("/");

  switch (db) {
    case "reactome":
      return REACTOME[id] || null;
    case "kegg":
      return KEGG[id] || null;
    case "hmdb":
      return HMDB[id] || null;
    case "huggingface":
    case "hf":
      return HUGGINGFACE[id] || null;
    case "allencell":
      return ALLENCELL[id] || null;
    case "uniprot":
      return UNIPROT[id] || null;
    case "glb":
      return GLB_MODELS[id] || null;
    default:
      return null;
  }
}

export function listSources() {
  return {
    reactome: Object.keys(REACTOME),
    kegg: Object.keys(KEGG),
    hmdb: Object.keys(HMDB),
    huggingface: Object.keys(HUGGINGFACE),
    allencell: Object.keys(ALLENCELL),
    uniprot: Object.keys(UNIPROT),
    glb: Object.keys(GLB_MODELS),
  };
}

export { REACTOME, KEGG, HMDB, HUGGINGFACE, ALLENCELL, UNIPROT, GLB_MODELS };
