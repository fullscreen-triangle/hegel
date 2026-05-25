import { parseSBML, extractDefaultRate } from './sbmlParser';

const RT = 2.478; // kJ/mol at 298K
const MU0_DEFAULT = -10.0; // default standard chemical potential (kJ/mol)

export function buildCircuitFromSBML(sbmlXml, compoundData = {}) {
  const parsed = parseSBML(sbmlXml);
  const { species, compartments, reactions } = parsed;

  const speciesMap = {};
  species.forEach(s => { speciesMap[s.id] = s; });

  const nodes = species.map((s, i) => {
    const ext = compoundData[s.id] || compoundData[s.name] || {};
    const conc = ext.concentration || s.initialConcentration || 0.1;
    const mu0 = ext.deltaG || MU0_DEFAULT;
    const mu = mu0 + RT * Math.log(Math.max(conc, 1e-10));
    return {
      id: i,
      speciesId: s.id,
      name: s.name,
      compartment: s.compartment,
      compartmentName: compartments[s.compartment]?.name || s.compartment,
      concentration: conc,
      mu0,
      mu,
      boundary: s.boundaryCondition,
    };
  });

  const nodeIndexMap = {};
  species.forEach((s, i) => { nodeIndexMap[s.id] = i; });

  const edges = [];
  let edgeIdx = 0;
  reactions.forEach(rxn => {
    const rate = extractDefaultRate(rxn);
    const srcSpecies = rxn.reactants.map(r => r.species);
    const dstSpecies = rxn.products.map(p => p.species);

    for (const srcId of srcSpecies) {
      for (const dstId of dstSpecies) {
        const srcIdx = nodeIndexMap[srcId];
        const dstIdx = nodeIndexMap[dstId];
        if (srcIdx === undefined || dstIdx === undefined) continue;

        const srcConc = nodes[srcIdx].concentration;
        const G = rate * srcConc / RT;

        edges.push({
          id: edgeIdx++,
          reactionId: rxn.id,
          name: rxn.name,
          src: srcIdx,
          dst: dstIdx,
          rate,
          conductance: G,
          deltaG: nodes[srcIdx].mu - nodes[dstIdx].mu,
        });
      }
    }
  });

  return {
    nodes,
    edges,
    compartments,
    modelId: parsed.modelId,
    numNodes: nodes.length,
    numEdges: edges.length,
  };
}

export function buildDemoGlycolysis() {
  const nodeData = [
    { name: 'Glucose',  conc: 5.0,    mu0: -917.0 },
    { name: 'G6P',      conc: 0.083,  mu0: -1760.0 },
    { name: 'F6P',      conc: 0.014,  mu0: -1760.0 },
    { name: 'FBP',      conc: 0.032,  mu0: -2600.0 },
    { name: 'DHAP',     conc: 0.16,   mu0: -1296.0 },
    { name: 'G3P',      conc: 0.019,  mu0: -1285.0 },
    { name: 'BPG',      conc: 0.001,  mu0: -2356.0 },
    { name: '3PG',      conc: 0.1,    mu0: -1502.0 },
    { name: 'PEP',      conc: 0.023,  mu0: -1269.0 },
    { name: 'Pyruvate', conc: 0.051,  mu0: -474.0 },
  ];

  const nodes = nodeData.map((n, i) => ({
    id: i,
    speciesId: n.name.toLowerCase(),
    name: n.name,
    compartment: 'cytoplasm',
    compartmentName: 'Cytoplasm',
    concentration: n.conc,
    mu0: n.mu0,
    mu: n.mu0 + RT * Math.log(Math.max(n.conc, 1e-10)),
    boundary: false,
  }));

  const edgeData = [
    { src: 0, dst: 1, name: 'Hexokinase',          k: 100.0 },
    { src: 1, dst: 2, name: 'PGI',                 k: 600.0 },
    { src: 2, dst: 3, name: 'PFK',                 k: 150.0 },
    { src: 3, dst: 4, name: 'Aldolase_DHAP',       k: 50.0 },
    { src: 3, dst: 5, name: 'Aldolase_G3P',        k: 50.0 },
    { src: 4, dst: 5, name: 'TPI',                 k: 2000.0 },
    { src: 5, dst: 6, name: 'GAPDH',               k: 250.0 },
    { src: 6, dst: 7, name: 'PGK',                 k: 800.0 },
    { src: 7, dst: 8, name: 'Enolase',             k: 100.0 },
    { src: 8, dst: 9, name: 'PyruvateKinase',      k: 300.0 },
    { src: 9, dst: 0, name: 'Gluconeogenesis',     k: 5.0 },
    { src: 1, dst: 5, name: 'PPP_branch',          k: 30.0 },
    { src: 7, dst: 2, name: '2PG_to_F6P',          k: 10.0 },
    { src: 4, dst: 9, name: 'DHAP_shunt',          k: 8.0 },
    { src: 6, dst: 8, name: 'BPG_mutase_shortcut', k: 15.0 },
  ];

  const edges = edgeData.map((e, i) => ({
    id: i,
    reactionId: e.name,
    name: e.name,
    src: e.src,
    dst: e.dst,
    rate: e.k,
    conductance: e.k * nodes[e.src].concentration / RT,
    deltaG: nodes[e.src].mu - nodes[e.dst].mu,
  }));

  return {
    nodes,
    edges,
    compartments: { cytoplasm: { id: 'cytoplasm', name: 'Cytoplasm', size: 1.0 } },
    modelId: 'demo_glycolysis',
    numNodes: nodes.length,
    numEdges: edges.length,
  };
}
