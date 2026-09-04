// Biocatalysis extension: the predicates a real question needs.
//
// Four abstract predicates were declared in `PREDICATE_FEATURES` and
// implemented by no adapter: `matching` (regex), `excluding` (neg), `ranked_by`
// (order) and `restricted` (filter). They were reachable by the static check --
// a plan naming them was correctly refused against a source that did not
// declare the feature -- but no plan could ever get an answer out of one,
// because no `extract` handled them. This module closes that gap, and adds the
// source kind they were missing.
//
// The gap is not an oversight to be tidied. It is exactly where the
// biocatalysis questions land. Doerr's Q1 asks for an enzyme
//
//   (a) originating from a bacterium and not a eukaryote   -- `neg`
//   (b) catalysing a named transamination                  -- `pattern`
//   (c) with no cysteine in its protein sequence           -- `regex`
//
// and (c) is not a graph question at all. A triple store holds the sequence as
// a literal; asking whether a character occurs in it is a string test the store
// may or may not perform faithfully, and `prop:under` says the honest response
// to "may or may not" is to withhold the declaration.

import {
  PREDICATE_FEATURES, Adapter, GraphPatternAdapter, Refusal, literalArgs,
} from './adapters.js';
import { ResultSet, featureset, repr, sorted, setOps } from './model.js';

// ---------------------------------------------------------------------------
// Req(rho) for the added predicates
// ---------------------------------------------------------------------------

/**
 * The delta. `sequence_of` is a lookup because a sequence is retrieved by key;
 * `typed_as` needs `neg` as well as `pattern` because the question that uses it
 * is a *negative* kind test ("bacterium, not eukaryote") and Req is a function
 * of the predicate, not of how a particular call happens to be phrased.
 */
export const BIOCAT_PREDICATE_FEATURES = new Map([
  ['sequence_of', featureset('lookup')],
  ['typed_as', featureset('pattern', 'neg')],
  ['measured_with', featureset('pattern', 'bind')],
  // An activity is reached FROM the thing it evaluated, which is the object
  // position of the stored triple. That is a `path` and not merely a `pattern`:
  // the source must traverse an edge backwards, and a deployment whose index is
  // one-directional can match the forward pattern and not the inverse.
  ['evaluations_of', featureset('pattern', 'path')],
  // The same shape on the reaction store: reach the subject from the object.
  ['producers_of', featureset('pattern', 'path')],
  ['consumers_of', featureset('pattern', 'path')],
  ['enzymes_from', featureset('pattern', 'path')],
  // Reaction from enzyme: the inverse of `catalysed_by`.
  ['catalysed_reactions', featureset('pattern', 'path')],
  // Identity. "Is this identifier in the set I hold?" -- no edge is walked, so
  // no `path`; the bound set is the extent, so `bind`.
  ['identified_as', featureset('pattern', 'bind')],
  // Forward: the device an activity used. Inverse: the activities that used a
  // device.
  ['measured_on', featureset('pattern', 'path')],
  // The recorded parameters of an activity: buffer, pH, operator, date.
  ['settings_of', featureset('pattern', 'bind')],
]);

for (const [k, v] of BIOCAT_PREDICATE_FEATURES) PREDICATE_FEATURES.set(k, v);

/**
 * Predicates whose extraction reaches the SUBJECT from the object, i.e. that
 * traverse a stored edge backwards. Named in one place so that a source cannot
 * implement the lowering for one direction and the extraction for the other.
 */
export const INVERSE_PREDICATES = new Set([
  'evaluations_of', 'producers_of', 'consumers_of', 'enzymes_from',
  'catalysed_reactions', 'measured_on',
]);

/**
 * `Req` corrected for the scan predicates.
 *
 * The base table gives `Req(matching) = {pattern, regex}` and likewise for
 * `excluding`. That conflates two separable things: how the source *reaches*
 * the literal, and what it *does* to the literal once it has it. A graph source
 * reaches it by matching a pattern, so for that source both features are
 * genuinely required. A lookup source reaches it by key -- there is no pattern
 * anywhere in the operation -- and demanding `pattern` of it makes the static
 * check refuse a plan for a capability the request never uses.
 *
 * The rule: a scan over a bound set requires `regex` (or `neg`) and `bind`. A
 * scan over an unbound extent requires `pattern` as well, because the source
 * must enumerate the extent to scan it. `bind` is therefore not merely additive
 * here -- its presence *removes* a requirement.
 */
export function biocatRequiredFeatures(request) {
  const base = PREDICATE_FEATURES.get(request.predicate);
  if (base === undefined) {
    throw new Refusal(`unknown abstract predicate ${repr(request.predicate)}`);
  }
  const req = new Set(base);
  if (request.bindings.length) {
    req.add('bind');
    if (['matching', 'excluding', 'sequence_of'].includes(request.predicate)) {
      req.delete('pattern');
    }
  }
  return req;
}

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

/** Bound-set identifiers for a request, sorted, unioned across bindings. */
function boundIdentifiers(request, inputs) {
  const out = new Set();
  for (const [, pv] of request.bindings) {
    for (const i of inputs[pv].identifiers()) out.add(i);
  }
  return out;
}

function valuesLine(v, members) {
  return `  VALUES ${v} { ${members.map((m) => `<${m}>`).join(' ')} }`;
}

/**
 * Python raises TypeError comparing a str with a number and the caller drops
 * the row. See the note in execute.js: ordering across types returns false, and
 * equality is strict so "12" == 12 does not become true.
 */
function compare(a, op, b) {
  const bothNumbers = typeof a === 'number' && typeof b === 'number';
  const bothStrings = typeof a === 'string' && typeof b === 'string';
  if (op === '==') return a === b;
  if (op === '!=') return a !== b;
  if (!bothNumbers && !bothStrings) return false;
  if (op === '<') return a < b;
  if (op === '>') return a > b;
  if (op === '<=') return a <= b;
  if (op === '>=') return a >= b;
  return false;
}

/**
 * Compile a plan-supplied pattern. A malformed pattern is a refusal, not an
 * empty answer. The difference is the whole of cor:onebit: "no enzyme lacks
 * cysteine" and "your regex did not compile" must not arrive as the same
 * result.
 *
 * Python `re` and JS `RegExp` are different languages -- `(?P<n>...)` and `\Z`
 * compile in Python and throw here, `\p{L}` the other way -- so a pattern that
 * one accepts may be refused by the other. The refusal is the honest outcome
 * either way; only the message text differs.
 */
function compilePattern(pred, pattern) {
  try {
    return new RegExp(pattern);
  } catch (e) {
    throw new Refusal(`${pred}: uncompilable pattern ${repr(pattern)}: ${e.message}`);
  }
}

// ---------------------------------------------------------------------------
// `identified_as`: is this named identifier in the set I already hold?
// ---------------------------------------------------------------------------
//
// Implemented as free functions rather than a mixin: JS has no multiple
// inheritance, and the Python mixin exists only because two source classes need
// this and share no ancestor below GraphPatternAdapter. Both classes below
// delegate here, which preserves the property the mixin was introduced for --
// one implementation, not two that can drift.
//
// Req is `pattern` + `bind` and deliberately NOT `path`: no edge is walked.

function lowerIdentity(request, inputs) {
  const names = sorted(new Set(literalArgs(request)));
  const lines = ['SELECT DISTINCT ?s WHERE {'];
  if (names.length) lines.push(valuesLine('?s', names));
  for (const [v, planVar] of request.bindings) {
    lines.push(valuesLine(v, sorted(inputs[planVar].identifiers())));
    lines.push(`  FILTER(?s = ${v})`);
  }
  lines.push('}');
  return lines.join('\n');
}

/**
 * The named identifiers, kept only if the bound set contains them.
 *
 * The intersection is the point: an identifier the plan names but the upstream
 * set does not hold is NOT returned, so a plan whose narrowing contradicts its
 * own earlier constraint yields the empty set rather than the name it asked
 * for. Naming a thing is not evidence the corpus has it.
 */
function extractIdentity(adapter, request, inputs) {
  const wanted = new Set(literalArgs(request));
  const held = boundIdentifiers(request, inputs);
  const pairs = [];
  for (const ident of sorted(setOps.intersect(wanted, held))) {
    const first = request.bindings.length ? request.bindings[0][1] : null;
    const row = first !== null ? { ...(inputs[first].get(ident) || {}) } : {};
    row._identified = true;
    pairs.push([ident, row]);
  }
  return ResultSet.of(adapter.namespace, pairs);
}

// ---------------------------------------------------------------------------
// The filtering graph source
// ---------------------------------------------------------------------------

/**
 * `GraphPatternAdapter` with `matching`/`excluding`/`restricted`/`ranked_by`.
 *
 * The base class lowers and extracts exactly one shape: subject --path-->
 * object. These four predicates are all *post-conditions on that shape*, so
 * each is implemented as the base extraction followed by one additional
 * operation, and each declares the feature that operation needs.
 *
 * Why they are predicates and not plan-level `filter` steps: a plan-level
 * filter runs after the result has crossed the wire. A `restricted` predicate
 * runs at the source. The distinction is invisible in the answer and decisive
 * in the cost.
 */
export class FilteringGraphAdapter extends GraphPatternAdapter {
  constructor(init) {
    super(init);
    // Attribute name carrying the literal that `matching`/`excluding` scan.
    this.literal_attr = init.literal_attr ?? '_literal';
    // Object -> literal, for sources that hold a scannable string per subject.
    this.literals = init.literals ?? {};
    // Object -> a numeric or comparable rank, for `ranked_by`.
    this.ranks = init.ranks ?? {};
    if (!init.capabilities || !init.capabilities.size) {
      this.capabilities = featureset(
        'pattern', 'path', 'bind', 'filter', 'agg', 'regex', 'neg', 'order',
      );
    }
  }

  // -- argument accessors ---------------------------------------------------
  //
  // Each predicate names its arguments positionally. A missing argument is a
  // Refusal rather than a silent default: a `matching` with no pattern would
  // otherwise match everything, which is the failure mode where a wrong answer
  // is indistinguishable from a right one.

  /**
   * The kind to require and, optionally, the kind to exclude.
   *
   * Shared by `lower` and `extract` so the audit record and the executed
   * semantics cannot diverge. They diverged once -- the lowering emitted a
   * conjunction where the extraction computed a difference.
   */
  static typeArgs(request) {
    const args = literalArgs(request);
    if (!args.length) throw new Refusal('typed_as requires a type argument');
    return [args[0], args.length > 1 ? args[1] : null];
  }

  static patternArg(request) {
    for (const a of request.args) {
      if (typeof a === 'string' && !a.startsWith('?')) return a;
    }
    throw new Refusal(`${repr(request.predicate)} requires a pattern argument`);
  }

  static rankArg(request) {
    for (const a of request.args) {
      if (typeof a === 'string' && !a.startsWith('?')) return a;
    }
    throw new Refusal('ranked_by requires a ranking key');
  }

  static restrictionArgs(request) {
    const args = request.args.filter((a) => !(typeof a === 'string' && a.startsWith('?')));
    if (args.length < 3) {
      throw new Refusal('restricted requires (attribute, operator, value)');
    }
    const [attr, op, val] = args;
    if (!['==', '!=', '<', '>', '<=', '>='].includes(op)) {
      throw new Refusal(`restricted: unknown operator ${repr(op)}`);
    }
    return [String(attr), op, val];
  }

  static literal(v) {
    return typeof v === 'string' ? `"${v}"` : String(v);
  }

  // -- lowering -------------------------------------------------------------

  /**
   * Longhand, extended with the construct each predicate needs.
   *
   * `cons:longhand` is preserved: one pattern per line, bound sets through
   * VALUES, and -- the point that matters for the added predicates -- the
   * regular expression enters as a *parameter of a FILTER call*, never spliced
   * into the pattern text.
   */
  lower(request, inputs) {
    const pred = request.predicate;

    if (INVERSE_PREDICATES.has(pred)) return this.lowerInverse(request, inputs);
    if (pred === 'identified_as') return lowerIdentity(request, inputs);

    if (pred === 'typed_as') {
      // `typed_as` cannot go through the base lowering. That lowering emits one
      // conjunct per literal argument, so a two-argument kind test would lower
      // to `?s a <want> . ?s a <forbid> .` -- a conjunction demanding BOTH
      // kinds, while `extract` computes the difference. The extraction is the
      // correct one; the lowering would have been wrong. A lowered form that
      // does not mean what the step means makes the record unreliable exactly
      // where cons:longhand asks it to be reliable.
      const [want, forbid] = FilteringGraphAdapter.typeArgs(request);
      const lines = ['SELECT DISTINCT ?s WHERE {'];
      for (const [v, planVar] of request.bindings) {
        lines.push(valuesLine(v, sorted(inputs[planVar].identifiers())));
      }
      lines.push(`  ?s <rdf:type> <${want}> .`);
      if (forbid !== null) lines.push(`  MINUS { ?s <rdf:type> <${forbid}> . }`);
      lines.push('}');
      return lines.join('\n');
    }

    const base = super.lower(request, inputs);
    if (!['matching', 'excluding', 'restricted', 'ranked_by'].includes(pred)) {
      return base;
    }

    const lines = base.replace(/\s+$/, '').split('\n');
    const body = lines.slice(0, -1);

    if (pred === 'matching' || pred === 'excluding') {
      const pattern = FilteringGraphAdapter.patternArg(request);
      // The pattern is a bound argument of REGEX, not text pasted into the
      // query. The value is emitted as a quoted literal in one place, which is
      // the whole of the exposure.
      const call = `REGEX(STR(?lit), "${pattern}")`;
      body.push(`  ?o <${this.literal_attr}> ?lit .`);
      body.push(pred === 'matching' ? `  FILTER(${call})` : `  FILTER(!${call})`);
    } else if (pred === 'restricted') {
      const [attr, op, val] = FilteringGraphAdapter.restrictionArgs(request);
      body.push(`  ?o <${attr}> ?v .`);
      body.push(`  FILTER(?v ${op} ${FilteringGraphAdapter.literal(val)})`);
    } else { // ranked_by
      body.push(`  ?o <${FilteringGraphAdapter.rankArg(request)}> ?rank .`);
    }

    body.push('}');
    if (pred === 'ranked_by') body.push('ORDER BY DESC(?rank)');
    return body.join('\n');
  }

  /**
   * The lowered form of an inverse traversal.
   *
   * Written separately rather than delegated, because the base lowering puts
   * each literal in the OBJECT position of a pattern whose subject is selected
   * and then filters subjects by it -- a forward walk. Emitting that string
   * here would leave an audit record describing an operation the step did not
   * perform.
   */
  lowerInverse(request, inputs) {
    const path = this.paths[request.predicate] ?? request.predicate;
    const targets = sorted(new Set(literalArgs(request)));
    const lines = ['SELECT DISTINCT ?s WHERE {'];
    if (targets.length) lines.push(valuesLine('?t', targets));
    for (const [v, planVar] of request.bindings) {
      lines.push(valuesLine(v, sorted(inputs[planVar].identifiers())));
    }
    lines.push(`  ?s <${path}> ?t .`);
    lines.push('}');
    return lines.join('\n');
  }

  // -- extraction -----------------------------------------------------------

  baseExtract(request, inputs) {
    return GraphPatternAdapter.prototype.extract.call(this, '', request, inputs);
  }

  /**
   * Reach the SUBJECT from the object.
   *
   * `baseExtract` walks subject --path--> object and returns the object. Three
   * of Doerr's questions run the other way. Expressing those with the forward
   * extraction does not fail loudly -- the literal filter applies to the
   * subject position, no subject is ever named `CHEBI:guaiacol`, and the step
   * returns nothing. An empty result meaning "you walked the edge backwards" is
   * indistinguishable at the emit boundary from one meaning "no reaction
   * produces this".
   */
  inverseExtract(request, inputs) {
    const path = this.paths[request.predicate] ?? request.predicate;
    const targets = new Set(literalArgs(request));
    for (const i of boundIdentifiers(request, inputs)) targets.add(i);
    const pairs = this.triples
      .filter(([, pr, o]) => pr === path && targets.has(o))
      .map(([s, , o]) => [s, { _reached: o, _via: path, _direction: 'inverse' }]);
    return ResultSet.of(this.namespace, pairs);
  }

  extract(concrete, request, inputs) {
    const pred = request.predicate;

    if (pred === 'count_of') {
      // `agg`. The aggregate is computed over the extent this adapter actually
      // holds. prop:under is the live hazard: a deployment whose server caps
      // materialisation returns a well-formed COUNT over a truncated extent,
      // and the caller cannot tell.
      const inner = this.baseExtract(request, inputs);
      return ResultSet.of(this.namespace, [
        [`${this.namespace}:count`, { count: inner.size, _over: pred }],
      ]);
    }

    if (pred === 'matching' || pred === 'excluding') {
      const pattern = FilteringGraphAdapter.patternArg(request);
      const rx = compilePattern(pred, pattern);
      const keep = (s) => (pred === 'matching' ? rx.test(s) : !rx.test(s));
      const pairs = [];
      for (const [ident, row] of this.baseExtract(request, inputs).rows) {
        const lit = row[this.literal_attr] ?? this.literals[ident];
        if (lit === undefined || lit === null) {
          // No literal to scan. Not a match and not a non-match -- the
          // predicate is undefined here, so the row is dropped rather than
          // being counted as a pass by a source that never looked.
          continue;
        }
        if (keep(String(lit))) {
          pairs.push([ident, { ...row, _scanned: true, _predicate: pred }]);
        }
      }
      return ResultSet.of(this.namespace, pairs);
    }

    if (pred === 'identified_as') return extractIdentity(this, request, inputs);

    if (pred === 'restricted') {
      const [attr, op, val] = FilteringGraphAdapter.restrictionArgs(request);
      const pairs = [];
      for (const [ident, row] of this.baseExtract(request, inputs).rows) {
        if (!Object.prototype.hasOwnProperty.call(row, attr)) continue;
        if (compare(row[attr], op, val)) pairs.push([ident, row]);
      }
      return ResultSet.of(this.namespace, pairs);
    }

    if (pred === 'ranked_by') {
      const key = FilteringGraphAdapter.rankArg(request);
      const rows = [...this.baseExtract(request, inputs).rows.entries()];
      const rank = ([k, r]) => r[key] ?? this.ranks[k] ?? 0.0;
      // Python's list.sort is stable and sorts descending via reverse=True,
      // which reverses the comparison and NOT the list, so ties keep their
      // original order. Array.prototype.sort is stable in modern engines, so a
      // descending comparator reproduces it exactly.
      rows.sort((a, b) => {
        const x = rank(a);
        const y = rank(b);
        if (x === y) return 0;
        return x > y ? -1 : 1;
      });
      return ResultSet.of(
        this.namespace,
        rows.map(([i, r], n) => [i, { ...r, _rank: n }]),
      );
    }

    if (pred === 'typed_as') {
      // The kind test. Two arguments: the type to require and, optionally, a
      // type to exclude -- which is why Req(typed_as) carries `neg`.
      const [want, forbid] = FilteringGraphAdapter.typeArgs(request);
      // A bound set restricts the extent tested, exactly as the VALUES block in
      // the lowered form says it does. Ignoring it here would make the kind
      // test range over the whole store while the audit record claimed
      // otherwise.
      const seeds = boundIdentifiers(request, inputs);
      const pairs = [];
      for (const [s, p, o] of this.triples) {
        if (p !== 'rdf:type') continue;
        if (o !== want) continue;
        if (seeds.size && !seeds.has(s)) continue;
        if (forbid !== null
            && this.triples.some(([s2, p2, o2]) => s2 === s && p2 === 'rdf:type' && o2 === forbid)) {
          continue;
        }
        pairs.push([s, { _type: want, _excluded: forbid }]);
      }
      return ResultSet.of(this.namespace, pairs);
    }

    if (INVERSE_PREDICATES.has(pred)) return this.inverseExtract(request, inputs);

    return this.baseExtract(request, inputs);
  }

  /**
   * Scanning is charged, because scanning is work the source does.
   *
   * A `matching` over an unbound extent touches every literal the source holds,
   * and charging it as one request would make the allocator blind to the one
   * step in a plan that can actually be expensive.
   */
  cost(request, inputs) {
    const base = super.cost(request, inputs);
    if (['matching', 'excluding'].includes(request.predicate)) {
      return base + Math.max(1, Object.keys(this.literals).length);
    }
    return base;
  }
}

// ---------------------------------------------------------------------------
// The sequence source
// ---------------------------------------------------------------------------

/**
 * Protein sequences, retrieved by key and scanned as strings.
 *
 * Separate from the graph source on purpose. A sequence is a literal, and the
 * question "does this literal contain C" is answered by a string engine, not by
 * a graph engine. Keeping them apart lets a deployment declare `regex` for the
 * one and withhold it for the other -- which is the honest position for most
 * triple stores, whose `REGEX` is available but whose behaviour on a
 * multi-megabyte literal is not something the plan author can verify.
 */
export class SequenceAdapter extends Adapter {
  constructor(init) {
    super(init);
    this.sequences = init.sequences ?? {};
    // Sequence identifier -> the entity it belongs to, for joins back.
    this.owner = init.owner ?? {};
    if (!this.capabilities.size) {
      // Deliberately NOT `pattern`: this source cannot answer a graph question,
      // and declaring `pattern` here would let an ill-formed plan through the
      // static check and fail at the adapter, which is exactly the inversion
      // cor:refuse-before-contact rules out.
      this.capabilities = featureset('lookup', 'regex', 'neg', 'bind', 'batch');
    }
  }

  /**
   * This source resolves Req itself: it reaches literals by key, so a bound
   * scan demands no `pattern` of it. See `biocatRequiredFeatures`.
   */
  requiredFeatures(request) {
    return biocatRequiredFeatures(request);
  }

  /**
   * A retrieval, not a query. One structural field per key -- no concatenation
   * of keys into a template, matching `LookupAdapter` and `cons:longhand`(ii).
   */
  lower(request, inputs) {
    const lines = [`GET ${this.name}/${request.predicate}`];
    const [keys, residues] = this.splitArgs(request, inputs);
    for (const k of keys) lines.push(`  key = ${k}`);
    for (const r of residues) lines.push(`  residue = ${r}`);
    return lines.join('\n');
  }

  /**
   * Separate keys from residue patterns.
   *
   * A literal argument means different things to different predicates, and the
   * adapter cannot tell them apart by inspecting the string: `C` is a residue
   * to `excluding` and would be an identifier to `sequence_of`. Guessing -- by
   * testing membership in `this.sequences`, say -- would make the request's
   * meaning depend on the fixture's contents, so that adding a protein named
   * `C` would silently reinterpret every plan already written. The predicate
   * decides instead, statically, and the decision is visible in the lowered
   * form.
   */
  splitArgs(request, inputs) {
    const keys = [];
    for (const [, planVar] of request.bindings) {
      keys.push(...sorted(inputs[planVar].identifiers()));
    }
    const literals = literalArgs(request);
    if (request.predicate === 'sequence_of') {
      return [keys.concat(literals.filter((a) => !keys.includes(a))), []];
    }
    if (!literals.length) return [keys, []];
    // Scan predicates: the first literal is the pattern, any further literals
    // are keys, so `excluding(C, TA1, TA2)` scans two named proteins without a
    // binding step.
    return [keys.concat(literals.slice(1).filter((a) => !keys.includes(a))), [literals[0]]];
  }

  extract(concrete, request, inputs) {
    const pred = request.predicate;
    const [keys, residues] = this.splitArgs(request, inputs);

    if (pred === 'sequence_of') {
      const pairs = keys
        .filter((k) => k in this.sequences)
        .map((k) => [k, { sequence: this.sequences[k], length: this.sequences[k].length }]);
      return ResultSet.of(this.namespace, pairs);
    }

    if (pred === 'matching' || pred === 'excluding') {
      // `splitArgs` has already separated the residue pattern from the keys, so
      // nothing here inspects `request.args` again: the predicate decided the
      // split statically.
      if (!residues.length) {
        throw new Refusal(`${pred} requires a residue or pattern argument`);
      }
      const pattern = residues[0];
      const rx = compilePattern(pred, pattern);
      let pairs = [];
      let covered = 0;
      let uncovered = 0;
      for (const k of keys) {
        const seq = this.sequences[k];
        if (seq === undefined) {
          // The sequence is not held. This is the honest outcome of a partial
          // corpus: the entity is neither included nor excluded, and counting
          // it either way would be a claim the source cannot support. It is
          // dropped, and the count is carried on every surviving row so the
          // caller can see how much of its input was never examined.
          uncovered += 1;
          continue;
        }
        covered += 1;
        const hit = rx.test(seq);
        if ((pred === 'matching') === hit) {
          pairs.push([k, { sequence_length: seq.length, residue: pattern, _scanned: true }]);
        }
      }
      pairs = pairs.map(([k, r]) => [k, { ...r, _covered: covered, _uncovered: uncovered }]);
      return ResultSet.of(this.namespace, pairs);
    }

    throw new Refusal(`${this.name} does not implement ${repr(pred)}`);
  }

  cost(request, inputs) {
    let n = 0;
    for (const [, pv] of request.bindings) n += inputs[pv].size;
    if (this.capabilities.has('batch')) return 1.0;
    return Math.max(1, n);
  }
}

// ---------------------------------------------------------------------------
// Instrument / provenance source
// ---------------------------------------------------------------------------

/**
 * Activities, instruments, operators, dates, buffers.
 *
 * A `pattern` source like any other. It exists separately because the questions
 * that use it (Q2, Q5, and six of the eight generic queries) are provenance
 * questions, and a deployment that publishes reaction data need not publish
 * instrument settings -- so its capability set and its snapshot are properly
 * its own.
 */
export class ProvenanceAdapter extends GraphPatternAdapter {
  constructor(init) {
    super(init);
    if (!init.capabilities || !init.capabilities.size) {
      this.capabilities = featureset('pattern', 'bind', 'filter', 'path');
    }
  }

  lower(request, inputs) {
    const pred = request.predicate;

    if (pred === 'evaluations_of') {
      // The inverse traversal, written as one. The base lowering puts the
      // literal in the object position; emitting that form would describe a
      // forward walk the step does not perform.
      const targets = sorted(new Set(literalArgs(request)));
      const path = this.paths.evaluations_of ?? 'evaluated';
      const lines = ['SELECT DISTINCT ?a WHERE {'];
      if (targets.length) lines.push(valuesLine('?t', targets));
      for (const [v, planVar] of request.bindings) {
        lines.push(valuesLine(v, sorted(inputs[planVar].identifiers())));
      }
      lines.push(`  ?a <${path}> ?t .`);
      lines.push('}');
      return lines.join('\n');
    }

    if (pred === 'settings_of') {
      // One conjunct per setting, all optional: an activity that recorded no
      // wavelength is still an activity, and a pattern demanding all five would
      // silently drop it. cons:longhand (i) -- each on its own line.
      const lines = ['SELECT ?a ?p ?v WHERE {'];
      for (const [v, planVar] of request.bindings) {
        lines.push(valuesLine(v, sorted(inputs[planVar].identifiers())));
      }
      for (const s of ProvenanceAdapter.SETTING_PREDICATES) {
        lines.push(`  OPTIONAL { ?a <${s}> ?v_${s} . }`);
      }
      lines.push('}');
      return lines.join('\n');
    }

    if (pred === 'identified_as') return lowerIdentity(request, inputs);

    if (pred === 'measured_on') {
      // The inverse of `measured_with`. The extraction and the lowered form
      // have to agree about direction or the record is a lie that nobody reads,
      // which is the worst kind.
      const devices = sorted(new Set(literalArgs(request)));
      const path = this.paths.measured_on ?? 'measured_with';
      const lines = ['SELECT DISTINCT ?a WHERE {'];
      if (devices.length) lines.push(valuesLine('?d', devices));
      for (const [v, planVar] of request.bindings) {
        lines.push(valuesLine(v, sorted(inputs[planVar].identifiers())));
      }
      lines.push(`  ?a <${path}> ?d .`);
      lines.push('}');
      return lines.join('\n');
    }

    return super.lower(request, inputs);
  }

  extract(concrete, request, inputs) {
    const pred = request.predicate;

    if (pred === 'evaluations_of') {
      const targets = new Set(literalArgs(request));
      for (const i of boundIdentifiers(request, inputs)) targets.add(i);
      const path = this.paths.evaluations_of ?? 'evaluated';
      const pairs = this.triples
        .filter(([, pr, o]) => pr === path && targets.has(o))
        .map(([s, , o]) => [s, { _evaluated: o }]);
      return ResultSet.of(this.namespace, pairs);
    }

    if (pred === 'settings_of') {
      const seeds = boundIdentifiers(request, inputs);
      const pairs = [];
      for (const a of sorted(seeds)) {
        const attrs = {};
        for (const [s, pr, o] of this.triples) {
          if (s === a && ProvenanceAdapter.SETTING_PREDICATES.includes(pr)) attrs[pr] = o;
        }
        // An activity with no recorded settings is returned with none, not
        // dropped. "This run recorded no buffer" and "there is no such run" are
        // different answers to Q2 and must not collapse.
        attrs._recorded = sorted(Object.keys(attrs));
        pairs.push([a, attrs]);
      }
      return ResultSet.of(this.namespace, pairs);
    }

    if (pred === 'identified_as') return extractIdentity(this, request, inputs);

    if (pred === 'measured_on') {
      // The inverse: activities that used a named device. The generic
      // Chem-DCAT-AP queries ask this way round, and running it through the
      // forward extraction would filter ACTIVITY names by a DEVICE name and
      // return nothing -- an empty set that means "wrong direction" wearing the
      // costume of one that means "no such measurement".
      const devices = new Set(literalArgs(request));
      for (const i of boundIdentifiers(request, inputs)) devices.add(i);
      // No device named and nothing bound is not an empty question; it is
      // "which activities were monitored at all", and the extent of the edge is
      // the answer. Returning the empty set here would be a different claim.
      const restrict = devices.size > 0;
      const path = this.paths.measured_on ?? 'measured_with';
      const pairs = [];
      for (const [s, pr, o] of this.triples) {
        if (pr === path && (restrict ? devices.has(o) : true)) {
          const attrs = { _device: o };
          for (const [s2, p2, o2] of this.triples) {
            if (s2 === s && p2 !== path) attrs[p2] = o2;
          }
          pairs.push([s, attrs]);
        }
      }
      return ResultSet.of(this.namespace, pairs);
    }

    if (pred === 'measured_with') {
      const seeds = boundIdentifiers(request, inputs);
      const path = this.paths.measured_with ?? 'measured_with';
      const pairs = [];
      for (const [s, p, o] of this.triples) {
        if (p !== path) continue;
        if (seeds.size && !seeds.has(s)) continue;
        const attrs = { _activity: s };
        for (const [s2, p2, o2] of this.triples) {
          if (s2 === s && p2 !== path) attrs[p2] = o2;
        }
        pairs.push([o, attrs]);
      }
      return ResultSet.of(this.namespace, pairs);
    }

    return super.extract(concrete, request, inputs);
  }
}

/**
 * Predicates that record a setting of the activity rather than a link to
 * another entity. Kept explicit rather than inferred by "is the object a
 * literal", because whether a value is a literal is a fact about this fixture's
 * serialisation and not about what the question is asking.
 */
ProvenanceAdapter.SETTING_PREDICATES = ['buffer', 'pH', 'operator', 'date', 'wavelength'];
