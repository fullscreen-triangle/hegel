// Local fixtures. Nothing here touches the network.
//
// The datasets are small and hand-checkable on purpose: every figure the
// validation reports can be recomputed by reading the fixture, which is what
// makes a disagreement between the code and the paper visible rather than
// arguable.

import {
  GraphPatternAdapter, LookupAdapter, MapAdapter, OntologyAdapter, Registry,
} from '../adapters.js';
import { TranslationMap, featureset } from '../model.js';

export const SNAPSHOT = 'fixture-v3';

// ---------------------------------------------------------------------------
// A small chemistry-shaped world
// ---------------------------------------------------------------------------

/** A class hierarchy. CHEBI:1 is the root; two levels beneath it. */
export const PARENTS = {
  'CHEBI:2': ['CHEBI:1'],
  'CHEBI:3': ['CHEBI:1'],
  'CHEBI:4': ['CHEBI:1'],
  'CHEBI:5': ['CHEBI:2'],
  'CHEBI:6': ['CHEBI:2'],
  'CHEBI:7': ['CHEBI:3'],
  'CHEBI:8': ['CHEBI:4'],
  'CHEBI:9': ['CHEBI:4'],
  'CHEBI:10': ['CHEBI:9'],
};

export const LABELS = Object.fromEntries(
  Object.keys(PARENTS).map((k) => [k, `compound-${k.split(':')[1]}`]),
);

/** Reaction triples, keyed on KEGG identifiers. */
export const TRIPLES = [
  ['KEGG:C2', 'consumes', 'RHEA:100'],
  ['KEGG:C2', 'consumes', 'RHEA:101'],
  ['KEGG:C5', 'consumes', 'RHEA:102'],
  ['KEGG:C7', 'consumes', 'RHEA:103'],
  ['KEGG:C7', 'consumes', 'RHEA:104'],
  ['KEGG:C9', 'consumes', 'RHEA:105'],
  ['KEGG:C2', 'produces', 'RHEA:200'],
  ['KEGG:C5', 'produces', 'RHEA:201'],
  ['RHEA:100', 'catalysed_by', 'EC:1.1.1.1'],
  ['RHEA:101', 'catalysed_by', 'EC:1.1.1.2'],
  ['RHEA:102', 'catalysed_by', 'EC:2.7.1.1'],
  ['RHEA:103', 'catalysed_by', 'EC:1.1.1.1'],
  ['RHEA:104', 'catalysed_by', 'EC:3.1.3.1'],
  ['RHEA:105', 'catalysed_by', 'EC:2.7.1.1'],
];

export const PATHS = {
  reactions_consuming: 'consumes',
  reactions_producing: 'produces',
  enzyme_of: 'catalysed_by',
  participants_of: 'consumes',
};

/** Flat records for the lookup adapter. */
export const RECORDS = {
  'EC:1.1.1.1': { name: 'alcohol dehydrogenase', organisms: 12 },
  'EC:1.1.1.2': { name: 'alcohol dehydrogenase (NADP+)', organisms: 4 },
  'EC:2.7.1.1': { name: 'hexokinase', organisms: 31 },
  'EC:3.1.3.1': { name: 'alkaline phosphatase', organisms: 7 },
};

export const LINKS = {
  pathway: {
    'EC:1.1.1.1': ['MAP:00010'],
    'EC:2.7.1.1': ['MAP:00010', 'MAP:00051'],
    'EC:3.1.3.1': ['MAP:00790'],
  },
};

// ---------------------------------------------------------------------------
// Translation maps
// ---------------------------------------------------------------------------

/**
 * Partial, non-functional, non-injective -- all three, as def:map allows.
 * 7 of the 9 CHEBI descendants have a KEGG counterpart: retention 7/9.
 */
export const CHEBI_KEGG = new TranslationMap('chebi2kegg', 'CHEBI', 'KEGG', {
  'CHEBI:2': ['KEGG:C2'],
  'CHEBI:3': ['KEGG:C3'],
  'CHEBI:4': ['KEGG:C4'],
  'CHEBI:5': ['KEGG:C5'],
  'CHEBI:7': ['KEGG:C7'],
  'CHEBI:9': ['KEGG:C9'],
  'CHEBI:10': ['KEGG:C9', 'KEGG:C10'], // non-functional
  // CHEBI:6 and CHEBI:8 are outside the domain.
});

/** A lossy second stage, so a chain has something to lose. */
export const KEGG_RHEA = new TranslationMap('kegg2rhea', 'KEGG', 'RHEA', {
  'KEGG:C2': ['RHEA:100'],
  'KEGG:C5': ['RHEA:102'],
  'KEGG:C9': ['RHEA:105'],
  // C3, C4, C7, C10 are outside the domain.
});

/**
 * Total on the same source set, for the (V11) collapse: making every map total
 * drives the route divergence to zero.
 */
export const CHEBI_KEGG_TOTAL = new TranslationMap(
  'chebi2kegg_total', 'CHEBI', 'KEGG',
  {
    ...Object.fromEntries(CHEBI_KEGG.pairs),
    'CHEBI:6': ['KEGG:C6'],
    'CHEBI:8': ['KEGG:C8'],
  },
);

// ---------------------------------------------------------------------------
// prop:cardinality-uninformative
// ---------------------------------------------------------------------------

/**
 * Two maps with equal output cardinality and unequal retention.
 *
 * Over S = {a1..a8}:
 *   mu_hi keeps 8 of 8 and sends each to one image  -> r = 1.00, a = 1.0
 *   mu_lo keeps 2 of 8 and sends each to four       -> r = 0.25, a = 4.0
 * Both produce |mu(S)| = 8. The product r*a agrees; neither factor does.
 */
export function cardinalityPair() {
  const s = Array.from({ length: 8 }, (_, i) => `X:a${i + 1}`);
  const hi = {};
  for (const u of s) hi[u] = [`Y:${u.split(':')[1]}`];
  const lo = {};
  s.slice(0, 2).forEach((u, i) => {
    lo[u] = Array.from({ length: 4 }, (_, j) => `Y:b${i * 4 + j + 1}`);
  });
  return [
    new TranslationMap('mu_hi', 'X', 'Y', hi),
    new TranslationMap('mu_lo', 'X', 'Y', lo),
    s,
  ];
}

// ---------------------------------------------------------------------------
// Registry assembly
// ---------------------------------------------------------------------------

/**
 * Two steps, c_1 = c_2 = 1, Bud = 2, and a refusal all the same.
 *
 * Step 1 costs 1 and returns a payload of cardinality 3; step 2's cost is
 * linear in its input, so it needs 3 and only 1 remains. The obstruction is
 * that c_2 is a minimum over inputs and the realised input is not the
 * minimising one.
 */
export function budgetTrap() {
  const reg = new Registry();
  reg.register(new OntologyAdapter({
    name: 'tiny_onto',
    namespace: 'CHEBI',
    parents: { 'CHEBI:2': ['CHEBI:1'], 'CHEBI:3': ['CHEBI:1'], 'CHEBI:4': ['CHEBI:1'] },
    labels: {},
    snapshot: SNAPSHOT,
  }));
  reg.register(new GraphPatternAdapter({
    name: 'tiny_graph',
    namespace: 'RHEA',
    triples: [['CHEBI:2', 'consumes', 'RHEA:1']],
    paths: { reactions_consuming: 'consumes' },
    snapshot: SNAPSHOT,
  }));
  return reg;
}

/** The main registry: four adapter kinds over the world above. */
export function buildRegistry(batch = false) {
  const reg = new Registry();

  reg.register(new OntologyAdapter({
    name: 'chebi', namespace: 'CHEBI', parents: { ...PARENTS }, labels: { ...LABELS },
    snapshot: SNAPSHOT,
  }));

  reg.register(new GraphPatternAdapter({
    name: 'rhea', namespace: 'RHEA', triples: TRIPLES.map((t) => [...t]),
    paths: { ...PATHS }, prefixes: { rh: 'http://example.invalid/rhea/' },
    snapshot: SNAPSHOT,
  }));

  // Declares {lookup, link} and NOT pattern. That restriction is what makes
  // thm:static fire on a plan asking it for a join.
  reg.register(new LookupAdapter({
    name: 'enzdb',
    namespace: 'EC',
    capabilities: batch ? featureset('lookup', 'link', 'batch') : new Set(),
    records: { ...RECORDS },
    links: { pathway: { ...LINKS.pathway } },
    snapshot: SNAPSHOT,
  }));

  return reg;
}

export function buildMaps() {
  const m = new MapAdapter({
    name: 'maps',
    namespace: 'map',
    maps: {
      chebi2kegg: CHEBI_KEGG,
      kegg2rhea: KEGG_RHEA,
      chebi2kegg_total: CHEBI_KEGG_TOTAL,
    },
  });
  m.snapshot = SNAPSHOT;
  return m;
}

// ---------------------------------------------------------------------------
// The paper's two listings, run verbatim
// ---------------------------------------------------------------------------
//
// lst:plan and lst:routes name sources CHEBI/RHEA/KEGG and maps ec_to_kegg,
// chebi_to_kegg, chebi_to_inchikey, inchikey_to_kegg. Those names are part of
// the printed text, so the fixture supplies them rather than the plans being
// edited to match the fixture -- the point of running them is that the
// listings execute as written.

/**
 * EC -> KEGG. 3 of 4 enzymes have a counterpart: retention 0.75, above the 0.6
 * that lst:plan declares, so the plan runs to completion.
 */
export const EC_KEGG = new TranslationMap('ec_to_kegg', 'EC', 'KEGG', {
  'EC:1.1.1.1': ['KEGG:E1'],
  'EC:2.7.1.1': ['KEGG:E2'],
  'EC:3.1.3.1': ['KEGG:E3'],
  // EC:1.1.1.2 is outside the domain.
});

/**
 * The two routes of lst:routes. The direct route keeps 7 of 9; the indirect
 * route loses a different element at each of its two stages, so the routes
 * diverge without either being wrong -- thm:route-extent(b).
 */
export const CHEBI_INCHI = new TranslationMap(
  'chebi_to_inchikey', 'CHEBI', 'INCHI',
  Object.fromEntries(
    Object.keys(PARENTS)
      .filter((k) => k !== 'CHEBI:3')
      .map((k) => [k, [`INCHI:${k.split(':')[1]}`]]),
  ),
);

export const INCHI_KEGG = new TranslationMap('inchikey_to_kegg', 'INCHI', 'KEGG', {
  'INCHI:2': ['KEGG:C2'],
  'INCHI:4': ['KEGG:C4'],
  'INCHI:5': ['KEGG:C5'],
  'INCHI:6': ['KEGG:C6'], // the direct route misses this one
  'INCHI:7': ['KEGG:C7'],
  'INCHI:9': ['KEGG:C9'],
  // INCHI:8 and INCHI:10 are outside the domain.
});

/** The KEGG side of lst:plan: a lookup source keyed on the EC->KEGG images. */
export const KEGG_RECORDS = {
  'KEGG:E1': { name: 'adh' },
  'KEGG:E2': { name: 'hk' },
  'KEGG:E3': { name: 'alp' },
};

export const KEGG_LINKS = {
  pathway: {
    'KEGG:E1': ['MAP:00010'],
    'KEGG:E2': ['MAP:00010', 'MAP:00051'],
    'KEGG:E3': ['MAP:00790'],
  },
};

/** Sources and maps under the names the paper's listings use. */
export function buildPaperRegistry() {
  const reg = new Registry();

  // CHEBI:35238 is the root lst:plan asks for; it sits above the acids.
  const parents = { ...PARENTS, 'CHEBI:1': ['CHEBI:35238'] };

  reg.register(new OntologyAdapter({
    name: 'CHEBI', namespace: 'CHEBI', parents, labels: { ...LABELS },
    snapshot: SNAPSHOT,
  }));

  // lst:plan passes ChEBI identifiers straight to RHEA -- no translation step
  // intervenes -- so this fixture is keyed on ChEBI, as a real reaction store
  // cross-referencing ChEBI would be. TRIPLES above is keyed on KEGG and serves
  // the plans that translate first; both keyings are needed, and which one a
  // step meets is exactly what the plan's step order decides.
  const chebiTriples = [
    ...TRIPLES.filter(([s]) => s.startsWith('KEGG:C'))
      .map(([s, p, o]) => [s.replace('KEGG:C', 'CHEBI:'), p, o]),
    ...TRIPLES.filter(([s]) => s.startsWith('RHEA:')).map((t) => [...t]),
  ];
  reg.register(new GraphPatternAdapter({
    name: 'RHEA', namespace: 'RHEA', triples: chebiTriples, paths: { ...PATHS },
    snapshot: SNAPSHOT,
  }));

  // lst:plan supplies a bound set to this step, so def:wellcap requires both
  // `bind` and `batch`. A source that cannot accept a bound set cannot serve
  // that plan at all; declaring them here is the adapter author asserting the
  // REST endpoint takes a key list, which rem:honesty-assumption leaves
  // unverified.
  reg.register(new LookupAdapter({
    name: 'KEGG',
    namespace: 'KEGG',
    capabilities: featureset('lookup', 'link', 'bind', 'batch'),
    records: { ...KEGG_RECORDS },
    links: { pathway: { ...KEGG_LINKS.pathway } },
    snapshot: SNAPSHOT,
  }));

  const maps = new MapAdapter({
    name: 'maps',
    namespace: 'map',
    maps: {
      ec_to_kegg: EC_KEGG,
      chebi_to_kegg: CHEBI_KEGG,
      chebi_to_inchikey: CHEBI_INCHI,
      inchikey_to_kegg: INCHI_KEGG,
    },
  });
  maps.snapshot = SNAPSHOT;
  return [reg, maps];
}
