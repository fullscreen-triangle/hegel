// Vocabulary shared by every view in the notebook.
//
// The six verdicts are the ordered rules (R1)-(R6) of thm:six, and the colours
// below encode the one distinction cor:onebit says a caller reading success or
// failure cannot make: `answer` is the only verdict that carries a payload, so
// it is the only one drawn in the affirmative colour. The other five are
// separated from each other by hue but share a weight, because they are five
// distinct diagnoses that collapse onto one observable bit.

export const VERDICTS = {
  answer:   { label: 'answer',   color: '#15803d', bg: '#15803d18', glyph: '=',
              note: 'a payload accompanies this verdict and no other' },
  empty:    { label: 'empty',    color: '#0369a1', bg: '#0369a118', glyph: '0',
              note: 'the request resolved and the extent was empty' },
  surface:  { label: 'surface',  color: '#b45309', bg: '#b4530918', glyph: '!',
              note: 'the source cannot express the request; no request issued' },
  timeout:  { label: 'timeout',  color: '#a16207', bg: '#a1620718', glyph: 'T',
              note: 'the engine did not return within the step budget' },
  refused:  { label: 'refused',  color: '#b91c1c', bg: '#b91c1c18', glyph: 'x',
              note: 'the budget could not fund the step' },
  starved:  { label: 'starved',  color: '#7c3aed', bg: '#7c3aed18', glyph: '~',
              note: 'an input this step depends on did not resolve' },
};

export const verdictOf = (v) => VERDICTS[v] || {
  label: v || 'unknown', color: '#6b7280', bg: '#6b728018', glyph: '?', note: '',
};

// prop:blame names four blockers. The blocker answers "which layer failed",
// which is the question the verdict alone does not answer.
export const BLOCKERS = {
  model:  { label: 'model',  note: 'the source does not declare the required feature' },
  engine: { label: 'engine', note: 'the engine did not return in time' },
  corpus: { label: 'corpus', note: 'the corpus does not contain the correspondence' },
  budget: { label: 'budget', note: 'the allocation could not fund the step' },
};

// Step kinds, from the grammar in hfq/parser.py.
export const KINDS = {
  from:      { glyph: '→', color: '#B63E96', note: 'issues a request to a source' },
  map:       { glyph: '⇝', color: '#7c3aed', note: 'translates identifiers across namespaces' },
  union:     { glyph: '∪', color: '#0369a1', note: 'set union of two bound variables' },
  intersect: { glyph: '∩', color: '#0369a1', note: 'set intersection' },
  join:      { glyph: '⋈', color: '#0f766e', note: 'join on a shared attribute' },
  filter:    { glyph: '⊙', color: '#b45309', note: 'one comparison; chain to conjoin' },
};

export const kindOf = (k) => KINDS[k] || { glyph: '○', color: '#6b7280', note: '' };

// The three fixture worlds. Their source names are disjoint, which is what lets
// hfq_serve.select_world infer the registry from the plan's declared sources.
export const WORLDS = {
  main:  { sources: ['chebi', 'rhea', 'enzdb'],
           note: 'the registry the bulk of the suite runs against' },
  paper: { sources: ['CHEBI', 'RHEA', 'KEGG'],
           note: 'the registry the worked example in the paper uses' },
  tiny:  { sources: ['tiny_onto', 'tiny_graph'],
           note: 'a two-source registry sized so the budget binds' },
};

export const fmt = (x, d = 3) =>
  x === null || x === undefined ? '—'
  : typeof x !== 'number' ? String(x)
  : Number.isInteger(x) ? String(x)
  : Math.abs(x) < 1e-3 ? x.toExponential(2)
  : x.toFixed(d).replace(/\.?0+$/, '');
