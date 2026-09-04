// Stage 2 of the pipeline: Resolve. Adapters and the source registry.
//
// Four adapter kinds, exercising the four source kinds of obs:kind:
//
//   GraphPatternAdapter  local RDF store, {pattern, path, bind, filter, agg}
//   LookupAdapter        local key-value fixture, {lookup, link} -- NOT pattern
//   OntologyAdapter      local class hierarchy, {path, lookup}
//   MapAdapter           translation steps; the only kind reporting retention
//
// A source is the quadruple (eta, cap, ext, c) of def:source. `namespace` is
// eta, `capabilities` is Capset(Src), `extract` is ext, `cost` is c. The
// capability declaration is *data written by the adapter author* -- it is the
// locus of the honesty assumption of rem:honesty-assumption, and nothing here
// verifies it.
//
// Every adapter resolves against a local fixture. No adapter performs network
// I/O, and none may be added that does: the claims are properties of the
// compiler, and a live service can neither confirm nor refute them (sec:proto).

import { ResultSet, featureset, repr, sorted, sortedList, setOps } from './model.js';

/**
 * Raised by an adapter asked for something outside its declared set.
 *
 * This should never fire in a well-capability plan: thm:static decides
 * containment before contact. It exists so that a bug in the checker is loud.
 */
export class Refusal extends Error {
  constructor(message) {
    super(message);
    this.name = 'Refusal';
  }
}

/** Raised when a lowered request exceeds the step's effort allocation. */
export class Timeout extends Error {
  constructor(message) {
    super(message);
    this.name = 'Timeout';
  }
}

// ---------------------------------------------------------------------------
// The required-capability function Req(rho)
// ---------------------------------------------------------------------------

/**
 * Which features each abstract predicate requires. This is the structural
 * recursion of the Check stage: Req is a function of phi, not an annotation the
 * plan author supplies.
 */
export const PREDICATE_FEATURES = new Map([
  ['descendants_of', featureset('path')],
  ['ancestors_of', featureset('path')],
  ['record', featureset('lookup')],
  ['link', featureset('lookup', 'link')],
  ['reactions_consuming', featureset('pattern', 'bind')],
  ['reactions_producing', featureset('pattern', 'bind')],
  ['enzyme_of', featureset('pattern', 'bind')],
  ['participants_of', featureset('pattern', 'bind')],
  ['count_of', featureset('pattern', 'agg')],
  ['matching', featureset('pattern', 'regex')],
  ['excluding', featureset('pattern', 'neg')],
  ['ranked_by', featureset('pattern', 'order')],
  ['restricted', featureset('pattern', 'filter')],
]);

/**
 * Req for this request AT this source.
 *
 * The check and the executor must compute Req identically -- if they differ, a
 * plan can pass the static check and then be refused at R2, which inverts
 * cor:refuse-before-contact and is strictly worse than either component being
 * wrong on its own. So both call this, and only this.
 *
 * An adapter may override by defining `requiredFeatures`. That override is a
 * declaration by the adapter author with the same standing as the capability
 * set: nothing here verifies it (rem:honesty-assumption).
 */
export function resolveFeatures(adapter, request) {
  if (typeof adapter.requiredFeatures === 'function') {
    return adapter.requiredFeatures(request);
  }
  return requiredFeatures(request);
}

/**
 * Req(rho), by structural recursion over the abstract request.
 *
 * The predicate contributes its own features; a non-empty `with` clause
 * contributes `bind`, because supplying a bound set is itself a capability a
 * source may lack.
 */
export function requiredFeatures(request) {
  const base = PREDICATE_FEATURES.get(request.predicate);
  if (base === undefined) {
    throw new Refusal(`unknown abstract predicate ${repr(request.predicate)}`);
  }
  const req = new Set(base);
  if (request.bindings.length) req.add('bind');
  return req;
}

// ---------------------------------------------------------------------------
// Base adapter
// ---------------------------------------------------------------------------

/** A source Src = (eta, cap, ext, c). */
export class Adapter {
  constructor({ name, namespace, capabilities = new Set(), snapshot = 'fixture-v1' }) {
    this.name = name;
    this.namespace = namespace;
    this.capabilities = capabilities;
    this.snapshot = snapshot;
    // Counts concrete requests issued. (V1) asserts this stays zero when the
    // static check refuses, which is cor:refuse-before-contact made checkable.
    this.requests_issued = 0;
    // The last concrete form emitted by lowering, kept for (V14).
    this.last_lowered = null;
  }

  supports(features) {
    return setOps.subset(new Set(features), this.capabilities);
  }

  missing(features) {
    return setOps.difference(new Set(features), this.capabilities);
  }

  /**
   * Low_Src: abstract request to canonical concrete form.
   *
   * Per cons:longhand this is the ONLY producer of concrete requests, and it
   * emits one canonical spelling per abstract request.
   */
  lower() {
    throw new Error('not implemented');
  }

  /** ext: run the concrete request against the local fixture. */
  extract() {
    throw new Error('not implemented');
  }

  /** c(rho): the cost in requests of issuing rho with these inputs. */
  cost() {
    throw new Error('not implemented');
  }

  /**
   * The statement order here is load-bearing and must not be rearranged:
   * `requests_issued` increments AFTER the timeout check and AFTER lowering, so
   * a step that times out issues no request. (V1) asserts the counter is zero
   * on a static refusal, and (V14) reads `last_lowered`.
   */
  evaluate(request, inputs, effort) {
    const req = resolveFeatures(this, request);
    if (!this.supports(req)) {
      throw new Refusal(
        `${this.name} lacks ${sortedList(this.missing(req))} for ${repr(request.predicate)}`,
      );
    }
    const c = this.cost(request, inputs);
    if (c > effort) {
      throw new Timeout(`${this.name}: cost ${c} exceeds allocated effort ${effort}`);
    }
    const concrete = this.lower(request, inputs);
    this.last_lowered = concrete;
    this.requests_issued += 1;
    return this.extract(concrete, request, inputs);
  }
}

/** Literal (non-variable) arguments of a request, as strings. */
export function literalArgs(request) {
  return request.args.filter((a) => !String(a).startsWith('?')).map(String);
}

// ---------------------------------------------------------------------------
// (1) Graph-pattern adapter over a local RDF store
// ---------------------------------------------------------------------------

/**
 * A conjunctive-pattern source backed by a local triple fixture.
 *
 * Triples are (subject, predicate, object) strings. The lowering emits longhand
 * SPARQL: every predicate-object list expanded to separate patterns, every
 * bound set supplied through VALUES, never by concatenation into the pattern
 * text. That is cons:longhand (i) and (ii), and it is what makes
 * thm:interpolation applicable.
 */
export class GraphPatternAdapter extends Adapter {
  constructor(init) {
    super(init);
    this.triples = init.triples ?? [];
    this.prefixes = init.prefixes ?? {};
    // Abstract predicate -> the concrete predicate path it lowers to.
    this.paths = init.paths ?? {};
    if (!this.capabilities.size) {
      this.capabilities = featureset('pattern', 'path', 'bind', 'filter', 'agg');
    }
  }

  pathFor(request) {
    return this.paths[request.predicate] ?? request.predicate;
  }

  lower(request, inputs) {
    const path = this.pathFor(request);
    const lines = sorted(Object.keys(this.prefixes))
      .map((p) => `PREFIX ${p}: <${this.prefixes[p]}>`);
    lines.push('SELECT DISTINCT ?s ?o WHERE {');

    let boundVar = null;
    for (const [v, planVar] of request.bindings) {
      boundVar = v;
      const members = sorted(inputs[planVar].identifiers());
      // (ii): the bound set enters through VALUES. The identifiers are emitted
      // as a value list, not spliced into the pattern text.
      lines.push(`  VALUES ${v} { ${members.map((m) => `<${m}>`).join(' ')} }`);
    }

    // (i): longhand. One triple pattern per line, no predicate-object list, no
    // comma-separated object list -- the construct of obs:2-397.
    lines.push(`  ${boundVar || '?s'} <${path}> ?o .`);
    for (const arg of request.args) {
      if (typeof arg === 'string' && !arg.startsWith('?')) {
        lines.push(`  ?s <${path}> <${arg}> .`);
      }
    }
    lines.push('}');
    return lines.join('\n');
  }

  extract(concrete, request, inputs) {
    const path = this.pathFor(request);
    let seeds = null;
    for (const [, planVar] of request.bindings) {
      const ids = inputs[planVar].identifiers();
      seeds = seeds === null ? new Set(ids) : setOps.intersect(seeds, ids);
    }

    const pairs = [];
    for (const [s, p, o] of this.triples) {
      if (p !== path) continue;
      if (seeds !== null && !seeds.has(s)) continue;
      if (seeds === null) {
        const literals = literalArgs(request);
        if (literals.length && !literals.includes(s)) continue;
      }
      pairs.push([o, { _from: s, _via: path }]);
    }
    return ResultSet.of(this.namespace, pairs);
  }

  /** One request per bound input, floor 1 -- no `batch` declared here. */
  cost(request, inputs) {
    let n = 0;
    for (const [, pv] of request.bindings) n += inputs[pv].size;
    return Math.max(1, n);
  }
}

// ---------------------------------------------------------------------------
// (2) Lookup adapter over a local key-value fixture
// ---------------------------------------------------------------------------

/**
 * A flat-file REST stand-in: {lookup, link} and deliberately NOT pattern.
 *
 * Its restricted declaration is what makes thm:static fire on a plan that asks
 * it for a join, and (V1) checks that the refusal happens with requests_issued
 * still zero.
 */
export class LookupAdapter extends Adapter {
  constructor(init) {
    super(init);
    this.records = init.records ?? {};
    this.links = init.links ?? {};
    if (!this.capabilities.size) this.capabilities = featureset('lookup', 'link');
  }

  lower(request, inputs) {
    const keys = [];
    for (const [, planVar] of request.bindings) {
      keys.push(...sorted(inputs[planVar].identifiers()));
    }
    keys.push(...literalArgs(request));
    const rel = request.args.length ? String(request.args[0]) : '';
    // Canonical form: one line per key. No string concatenation of keys into a
    // template -- each key is a separate structural field.
    const head = `GET ${this.name}/${request.predicate}`;
    const lines = [head, ...sorted(new Set(keys)).map((k) => `  key = ${k}`)];
    if (rel) lines.push(`  relation = ${rel}`);
    return lines.join('\n');
  }

  extract(concrete, request, inputs) {
    // Sorted, for the same reason TranslationMap.apply sorts: when two keys
    // reach one value -- KEGG:E1 and KEGG:E2 both link to MAP:00010 --
    // ResultSet.of merges on collision with the last write winning, so the
    // recorded `_from` depends on iteration order. The extent is identical
    // either way; only the provenance moves.
    const keys = [];
    for (const [, planVar] of request.bindings) {
      keys.push(...sorted(inputs[planVar].identifiers()));
    }

    const pairs = [];
    if (request.predicate === 'link') {
      const rel = request.args.length ? String(request.args[0]) : '';
      const table = this.links[rel] || {};
      for (const k of keys) {
        for (const v of table[k] || []) pairs.push([v, { _from: k, _relation: rel }]);
      }
    } else if (request.predicate === 'record') {
      for (const a of request.args) {
        if (typeof a === 'string' && !a.startsWith('?')) keys.push(a);
      }
      for (const k of keys) {
        if (Object.prototype.hasOwnProperty.call(this.records, k)) {
          pairs.push([k, { ...this.records[k] }]);
        }
      }
    }
    return ResultSet.of(this.namespace, pairs);
  }

  cost(request, inputs) {
    let n = 0;
    for (const [, pv] of request.bindings) n += inputs[pv].size;
    if (this.capabilities.has('batch')) return 1.0;
    return Math.max(1, n);
  }
}

// ---------------------------------------------------------------------------
// (3) Ontology adapter over a local class hierarchy
// ---------------------------------------------------------------------------

/** Transitive closure over subsumption: {path, lookup}. No filter, no agg. */
export class OntologyAdapter extends Adapter {
  constructor(init) {
    super(init);
    this.parents = init.parents ?? {};
    this.labels = init.labels ?? {};
    if (!this.capabilities.size) this.capabilities = featureset('path', 'lookup');
  }

  children() {
    const out = {};
    for (const [child, ps] of Object.entries(this.parents)) {
      for (const p of ps) {
        if (!out[p]) out[p] = [];
        out[p].push(child);
      }
    }
    return out;
  }

  lower(request, inputs) {
    const roots = literalArgs(request);
    for (const [, planVar] of request.bindings) {
      roots.push(...sorted(inputs[planVar].identifiers()));
    }
    const direction = request.predicate === 'ancestors_of' ? 'subClassOf*' : '^subClassOf*';
    const lines = ['SELECT DISTINCT ?c WHERE {'];
    if (roots.length) {
      const vals = sorted(new Set(roots)).map((r) => `<${r}>`).join(' ');
      lines.push(`  VALUES ?root { ${vals} }`);
    }
    lines.push(`  ?c ${direction} ?root .`);
    lines.push('}');
    return lines.join('\n');
  }

  extract(concrete, request, inputs) {
    const roots = literalArgs(request);
    for (const [, planVar] of request.bindings) {
      roots.push(...inputs[planVar].identifiers());
    }

    let step;
    if (request.predicate === 'ancestors_of') step = this.parents;
    else if (request.predicate === 'descendants_of') step = this.children();
    else step = {};

    // LIFO frontier, matching Python's list.pop(). The final set is sorted, so
    // traversal order does not reach the output -- but keeping it identical
    // costs nothing and removes a question.
    const seen = new Set();
    const frontier = [...roots];
    while (frontier.length) {
      const u = frontier.pop();
      for (const v of step[u] || []) {
        if (!seen.has(v)) {
          seen.add(v);
          frontier.push(v);
        }
      }
    }
    const pairs = sorted(seen).map((v) => [v, { label: this.labels[v] ?? '' }]);
    return ResultSet.of(this.namespace, pairs);
  }

  /** A closure is one request: `path` is evaluated by the source. */
  cost() {
    return 1.0;
  }
}

// ---------------------------------------------------------------------------
// (4) Map adapter -- translation steps
// ---------------------------------------------------------------------------

/**
 * Translation steps of def:map. The only adapter reporting retention.
 *
 * Because def:retention separates retention from amplification and
 * prop:cardinality-uninformative shows their product is all the output
 * cardinality reveals, both are recorded, never just the output size.
 */
export class MapAdapter extends Adapter {
  constructor(init) {
    super(init);
    this.maps = init.maps instanceof Map ? init.maps : new Map(Object.entries(init.maps ?? {}));
    if (!this.capabilities.size) this.capabilities = featureset('lookup', 'link', 'batch');
  }

  chain(names) {
    return names.map((n) => {
      if (!this.maps.has(n)) throw new Refusal(`unknown translation map ${repr(n)}`);
      return this.maps.get(n);
    });
  }

  /**
   * Apply mu_1 .. mu_k, recording r and a at each stage.
   *
   * The per-stage record is what thm:retention(a) factorises over, and what
   * (V7) checks the multiplicative identity against.
   */
  applyChain(names, res) {
    const stages = [];
    let current = res;
    for (const mu of this.chain(names)) {
      const s = current.identifiers();
      const stage = {
        map: mu.name,
        input_size: s.size,
        retention: mu.retention(s),
        amplification: mu.amplification(s),
      };
      stages.push(stage);
      current = mu.apply(current);
      stage.output_size = current.size;
    }
    return [current, stages];
  }

  /**
   * rho_{1..k}(S_0): the fraction of S_0 with at least one image in S_k.
   *
   * Computed by tracking trajectories, not by multiplying retentions --
   * thm:retention(b),(c) bound it but do not determine it, which is the whole
   * content of rem:bounds-gap.
   */
  survivingFraction(names, res) {
    const s0 = res.identifiers();
    if (!s0.size) return 1.0;
    const chain = this.chain(names);
    let survivors = 0;
    for (const u of s0) {
      let frontier = new Set([u]);
      for (const mu of chain) {
        frontier = mu.image(frontier);
        if (!frontier.size) break;
      }
      if (frontier.size) survivors += 1;
    }
    return survivors / s0.size;
  }

  lower() {
    throw new Refusal('map steps do not lower to a concrete request');
  }

  extract() {
    throw new Refusal('map steps do not extract');
  }

  cost() {
    return 1.0;
  }
}

// ---------------------------------------------------------------------------
// Registry
// ---------------------------------------------------------------------------

/** Resolve stage: source name -> adapter. */
export class Registry {
  constructor(adapters = new Map()) {
    this.adapters = adapters;
  }

  register(adapter) {
    this.adapters.set(adapter.name, adapter);
    return adapter;
  }

  get(name) {
    if (!this.adapters.has(name)) throw new Refusal(`unknown source ${repr(name)}`);
    return this.adapters.get(name);
  }

  totalRequests() {
    let n = 0;
    for (const a of this.adapters.values()) n += a.requests_issued;
    return n;
  }

  resetCounters() {
    for (const a of this.adapters.values()) {
      a.requests_issued = 0;
      a.last_lowered = null;
    }
  }
}
