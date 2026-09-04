// Core model: features, result sets, verdicts, blockers.
//
// Definitions implemented here, with the paper's labels:
//
//   def:result    result set = finite set of (identifier, partial attribute
//                 map), no identifier occurring twice
//   def:verdicts  V = {answer, empty, surface, timeout, refused, starved}
//   def:blocker   partial map from non-answer verdicts to blockers; `empty`
//                 deliberately has no blocker
//   def:map       translation map = relation, with retention and amplification
//
// Nothing in this module performs I/O.

// ---------------------------------------------------------------------------
// Features (Feat). The capability vocabulary of the paper.
// ---------------------------------------------------------------------------

export const FEAT = new Set([
  'pattern', // conjunctive graph pattern
  'path',    // transitive / property path
  'filter',  // value filtering
  'bind',    // supply a bound set as input
  'agg',     // aggregation
  'neg',     // negation
  'order',   // ordering
  'regex',   // regular-expression matching
  'lookup',  // single-key record retrieval
  'link',    // cross-reference listing
  'batch',   // multiple keys in one request
]);

/** A capability symbol, validated against FEAT. */
export function feature(value) {
  if (!FEAT.has(value)) {
    throw new Error(
      `unknown feature ${repr(value)}; Feat = ${sortedList(FEAT)}`,
    );
  }
  return value;
}

export function featureset(...names) {
  return new Set(names.map(feature));
}

// ---------------------------------------------------------------------------
// Small helpers the port needs that Python gets from the language
// ---------------------------------------------------------------------------

/** Python `repr` of a string: single quotes unless the value contains one. */
export function repr(v) {
  if (typeof v !== 'string') return String(v);
  return v.includes("'") && !v.includes('"') ? `"${v}"` : `'${v}'`;
}

/** Python's `sorted(...)` rendered as a list literal: "['a', 'b']". */
export function sortedList(xs) {
  return `[${sorted(xs).map(repr).join(', ')}]`;
}

/**
 * Python `sorted()` over strings. JS's default sort compares by UTF-16 code
 * unit after string conversion, which agrees with Python for the ASCII
 * identifiers used throughout — but only if the comparator is explicit. A bare
 * .sort() on a mixed array would compare "10" and 9 by their string forms.
 */
export function sorted(xs) {
  return [...xs].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
}

/** Set operations. JS has no built-ins for these at the versions we target. */
export const setOps = {
  intersect: (a, b) => new Set([...a].filter((x) => b.has(x))),
  difference: (a, b) => new Set([...a].filter((x) => !b.has(x))),
  union: (a, b) => new Set([...a, ...b]),
  symmetric: (a, b) =>
    new Set([...[...a].filter((x) => !b.has(x)), ...[...b].filter((x) => !a.has(x))]),
  subset: (a, b) => [...a].every((x) => b.has(x)),
};

// ---------------------------------------------------------------------------
// Result sets (def:result)
// ---------------------------------------------------------------------------

/**
 * A finite set of (identifier, partial attribute map) pairs.
 *
 * The no-duplicate-identifier condition of def:result is enforced by
 * construction: the payload is a Map keyed by identifier. Identifiers are
 * namespace-tagged strings ("CHEBI:15377"), which is how rem:disjoint
 * discharges the disjointness assumption -- by prefixing at extraction time.
 *
 * `rows` is a Map and not a plain object. Attribute VALUES reach the join
 * index in execute.js, where a plain object would coerce null, 12 and "12" to
 * one key; keeping the row container a Map throughout avoids two conventions.
 */
export class ResultSet {
  constructor(namespace, rows = new Map()) {
    this.namespace = namespace;
    this.rows = rows;
  }

  static of(namespace, pairs) {
    const rows = new Map();
    for (const [ident, attrs] of pairs) {
      if (rows.has(ident)) {
        // def:result forbids a repeated identifier: merge attribute maps,
        // which is exactly the collapse prop:common-result performs.
        Object.assign(rows.get(ident), attrs);
      } else {
        rows.set(ident, { ...attrs });
      }
    }
    return new ResultSet(namespace, rows);
  }

  static empty(namespace) {
    return new ResultSet(namespace, new Map());
  }

  /** idm(Res): the projection onto identifiers. */
  identifiers() {
    return new Set(this.rows.keys());
  }

  get size() {
    return this.rows.size;
  }

  /**
   * Python's ResultSet.__bool__ is `bool(self.rows)`. Every JS object is
   * truthy, so `if (res)` would be wrong wherever Python writes `if res`.
   * Call sites use this instead.
   */
  isEmpty() {
    return this.rows.size === 0;
  }

  get(ident) {
    return this.rows.get(ident);
  }

  has(ident) {
    return this.rows.has(ident);
  }

  toJSON() {
    const ids = sorted(this.rows.keys());
    const attributes = {};
    for (const k of ids) attributes[k] = this.rows.get(k);
    return {
      namespace: this.namespace,
      size: this.rows.size,
      identifiers: ids,
      attributes,
    };
  }
}

// ---------------------------------------------------------------------------
// Verdicts (def:verdicts) and blockers (def:blocker)
// ---------------------------------------------------------------------------

export const Verdict = Object.freeze({
  ANSWER: 'answer',
  EMPTY: 'empty',
  SURFACE: 'surface',
  TIMEOUT: 'timeout',
  REFUSED: 'refused',
  STARVED: 'starved',
});

export const Blocker = Object.freeze({
  MODEL: 'model',
  ENGINE: 'engine',
  BUDGET: 'budget',
  CORPUS: 'corpus',
});

/**
 * def:blocker. Deliberately partial: Verdict.EMPTY and Verdict.ANSWER are
 * absent, because (R6) fires exactly when nothing obstructed the step, and
 * assigning a blocker there would assert an obstruction that did not occur.
 */
export const BLOCKER = new Map([
  [Verdict.SURFACE, Blocker.MODEL],
  [Verdict.TIMEOUT, Blocker.ENGINE],
  [Verdict.REFUSED, Blocker.BUDGET],
  [Verdict.STARVED, Blocker.CORPUS],
]);

/** blk(v), partial. Returns undefined for ANSWER and EMPTY. */
export function blockerOf(v) {
  return BLOCKER.get(v);
}

// ---------------------------------------------------------------------------
// Translation maps (def:map, def:retention)
// ---------------------------------------------------------------------------

/** A relation mu subseteq n x n'. Partial, non-functional, non-injective. */
export class TranslationMap {
  constructor(name, sourceNs, targetNs, pairs) {
    this.name = name;
    this.source_ns = sourceNs;
    this.target_ns = targetNs;
    // Map<Ident, Ident[]>
    this.pairs = pairs instanceof Map ? pairs : new Map(Object.entries(pairs));
  }

  domain() {
    const out = new Set();
    for (const [k, v] of this.pairs) if (v && v.length) out.add(k);
    return out;
  }

  image(s) {
    const out = new Set();
    for (const u of s) for (const v of this.pairs.get(u) || []) out.add(v);
    return out;
  }

  /** r_mu(S) = |S cap dom mu| / |S|, with r_mu(empty) = 1 by convention. */
  retention(s) {
    const set = s instanceof Set ? s : new Set(s);
    if (set.size === 0) return 1.0;
    return setOps.intersect(set, this.domain()).size / set.size;
  }

  /** a_mu(S) = |mu(S)| / |S cap dom mu|; null when the denominator is 0. */
  amplification(s) {
    const set = s instanceof Set ? s : new Set(s);
    const kept = setOps.intersect(set, this.domain()).size;
    if (kept === 0) return null;
    return this.image(set).size / kept;
  }

  /**
   * Carry attributes forward, recording the preimage as provenance.
   *
   * The iteration is SORTED, where the Python iterates a frozenset. When mu is
   * non-injective -- CHEBI:9 and CHEBI:10 both reach KEGG:C9 -- the surviving
   * row's `_preimage` is whichever preimage was merged last, so an unordered
   * iteration makes that attribute vary between runs. Python's is genuinely
   * unstable across hash seeds; sorting here makes the provenance
   * reproducible. Verdicts and cardinalities are unaffected either way, since
   * the merge collapses to the same identifier set.
   */
  apply(res) {
    const pairs = [];
    for (const u of sorted(res.identifiers())) {
      for (const v of this.pairs.get(u) || []) {
        pairs.push([v, { ...res.get(u), _via: this.name, _preimage: u }]);
      }
    }
    return ResultSet.of(this.target_ns, pairs);
  }
}
