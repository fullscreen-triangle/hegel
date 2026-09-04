// Stage 5 of the pipeline: Execute. Rules (R1)--(R6) of def:verdicts.
//
// The rules are applied IN ORDER, which is what makes verdicts attributive: a
// step that is both starved and over-budget reports starvation, because (R1)
// precedes (R3) and the earlier obstruction is the one that actually stopped it.
//
//   (R1) some y in beta has a non-answer verdict, or an answer whose retention
//        fell below the step's declared expectation             -> starved
//   (R2) Req(rho) not subseteq Capset(Src)                      -> surface
//   (R3) remaining budget below cost_Src at input cardinality   -> refused
//   (R4) the request does not complete within b                 -> timeout
//   (R5) the extracted result set is empty                      -> empty
//   (R6) otherwise                                              -> answer
//
// Per prin:verdict a payload accompanies only `answer`. An implementation
// returning a partial payload alongside a failure verdict would reintroduce
// exactly the ambiguity cor:onebit identifies, so every non-answer verdict here
// carries payload null and the successors see the absence.

import {
  MapAdapter, Refusal, Timeout, resolveFeatures,
} from './adapters.js';
import { YieldSpec, solve } from './allocate.js';
import { check, refusalDocument } from './check.js';
import {
  ResultSet, Verdict, blockerOf, repr, sorted, setOps,
} from './model.js';

// ---------------------------------------------------------------------------
// Number formatting
// ---------------------------------------------------------------------------

/**
 * Python's "{:g}": six significant digits, exponential outside
 * [1e-4, 1e6), and trailing zeros stripped. JS has no equivalent, and a bare
 * template interpolation gives 17 digits where Python gives "0.3".
 */
export function formatG(x) {
  if (!Number.isFinite(x)) return String(x);
  if (x === 0) return '0';
  const exp = Math.floor(Math.log10(Math.abs(x)));
  if (exp < -4 || exp >= 6) {
    const s = x.toExponential(5);
    const [mant, e] = s.split('e');
    const trimmed = mant.includes('.') ? mant.replace(/\.?0+$/, '') : mant;
    const sign = e[0] === '-' ? '-' : '+';
    const digits = e.slice(1).padStart(2, '0');
    return `${trimmed}e${sign}${digits}`;
  }
  const s = x.toPrecision(6);
  return s.includes('.') ? s.replace(/\.?0+$/, '') : s;
}

/**
 * Python's "{:.2f}"/"{:.4f}". Python rounds half to even on the exact binary
 * value; JS toFixed rounds half away from zero, so (0.125).toFixed(2) is "0.13"
 * where Python gives "0.12". Retentions here are ratios of small integers and
 * 1/8 is reachable, so the tie case is not hypothetical.
 */
export function formatFixed(x, digits) {
  if (!Number.isFinite(x)) return String(x);
  const scale = 10 ** digits;
  const scaled = x * scale;
  const floor = Math.floor(scaled);
  const frac = scaled - floor;
  let n;
  if (Math.abs(frac - 0.5) < Number.EPSILON * Math.abs(scaled)) {
    n = floor % 2 === 0 ? floor : floor + 1; // half to even
  } else {
    n = Math.round(scaled);
  }
  return (n / scale).toFixed(digits);
}

/** Python renders a float 1.0 as "1.0"; JS String(1) gives "1". */
export function formatNum(x) {
  if (x === null || x === undefined) return String(x);
  if (typeof x === 'number' && Number.isInteger(x) && Number.isFinite(x)) {
    return `${x}.0`;
  }
  return String(x);
}

// ---------------------------------------------------------------------------
// Step results
// ---------------------------------------------------------------------------

/** One entry of the emitted JSON, in the shape fixed by lst:json. */
export class StepResult {
  constructor(init) {
    this.step = init.step;
    this.source = init.source;
    this.verdict = init.verdict;
    this.diagnosis = init.diagnosis ?? null;
    this.composite_power = init.composite_power ?? null;
    this.retention = init.retention ?? null;
    this.amplification = init.amplification ?? null;
    this.expected = init.expected ?? null;
    this.allocated = init.allocated ?? 0.0;
    this.spent = init.spent ?? 0.0;
    this.shadow_price = init.shadow_price ?? 0.0;
    this.payload = init.payload ?? null;
    this.snapshot = init.snapshot ?? null;
    this.lowered_form = init.lowered_form ?? null;
    this.stages = init.stages ?? null;
  }

  toJSON(includePayload = true) {
    const out = {
      step: this.step,
      source: this.source,
      verdict: this.verdict,
    };
    // def:blocker is partial: the field is ABSENT, not null, exactly when the
    // verdict is `answer` or `empty`.
    const blk = blockerOf(this.verdict);
    if (blk !== undefined) out.blocker = blk;
    out.diagnosis = this.diagnosis;
    out.composite_power = this.composite_power;
    out.retention = this.retention;
    out.amplification = this.amplification;
    out.budget = {
      allocated: this.allocated,
      spent: this.spent,
      shadow_price: this.shadow_price,
    };
    // prin:verdict: a payload accompanies only `answer`.
    if (this.verdict === Verdict.ANSWER && includePayload && this.payload !== null) {
      out.payload = this.payload.toJSON();
    } else {
      out.payload = null;
    }
    const prov = {
      snapshot: this.snapshot,
      lowered_form: this.lowered_form ? 'canonical' : null,
    };
    // Python tests `if self.stages:` -- an empty list is falsy there and truthy
    // here, so the length must be tested explicitly.
    if (this.stages && this.stages.length) prov.stages = this.stages;
    if (this.lowered_form) prov.concrete = this.lowered_form;
    out.provenance = prov;
    return out;
  }
}

export class Execution {
  constructor(planName) {
    this.plan_name = planName;
    this.steps = [];
    this.allocation = null;
    this.check_report = null;
    this.emitted = {};
    this.requests_issued = 0;
    this.halted_early = false;
  }

  byVar(v) {
    return this.steps.find((s) => s.step === v) || null;
  }

  verdicts() {
    const out = {};
    for (const s of this.steps) out[s.step] = s.verdict;
    return out;
  }

  /**
   * Follow the diagnosis chain of prop:blame.
   *
   * Terminates at a non-starved step within m hops, because def:plan requires
   * every beta variable to be bound by an EARLIER step, so the chain is
   * strictly decreasing in sequence position and cannot cycle.
   */
  blameChain(v) {
    const chain = [v];
    const seen = new Set([v]);
    let cur = v;
    for (;;) {
      const r = this.byVar(cur);
      if (r === null || r.verdict !== Verdict.STARVED) return chain;
      const nxt = (r.diagnosis || {}).named_predecessor;
      if (nxt === null || nxt === undefined || seen.has(nxt)) return chain;
      chain.push(nxt);
      seen.add(nxt);
      cur = nxt;
    }
  }

  toJSON(includePayload = true) {
    return {
      plan: this.plan_name,
      outcome: 'executed',
      check: this.check_report ? this.check_report.toJSON() : null,
      allocation: this.allocation ? this.allocation.toJSON() : null,
      requests_issued: this.requests_issued,
      halted_early: this.halted_early,
      steps: this.steps.map((s) => s.toJSON(includePayload)),
      emitted: this.emitted,
    };
  }
}

// ---------------------------------------------------------------------------
// Yield specification
// ---------------------------------------------------------------------------

/**
 * Attach a yield to each step.
 *
 * A step against a source declaring `lookup` but not `pattern` is
 * all-or-nothing (rem:concavity-fails): one request retrieves the record and
 * further requests retrieve nothing. Such steps are charged first rather than
 * optimised, so the shadow price governs only a subset of the plan.
 *
 * The weights are configuration. sec:limits records that we have estimated a
 * yield function for no real source.
 */
export function yieldSpecs(plan, registry, weights = {}) {
  const specs = [];
  for (const s of plan.steps) {
    const w = weights[s.var] ?? 1.0;
    if (s.kind !== 'from') {
      // map and set operations consume no requests; they are charged a nominal
      // fixed unit so the allocator sees them.
      specs.push(new YieldSpec(s.var, { weight: w, allOrNothing: true, fixedCost: 1.0 }));
      continue;
    }
    const cap = registry.get(s.source).capabilities;
    const aon = cap.has('lookup') && !cap.has('pattern');
    specs.push(new YieldSpec(s.var, { weight: w, allOrNothing: aon, fixedCost: 1.0 }));
  }
  return specs;
}

// ---------------------------------------------------------------------------
// Why an emitted extension is not an answer
// ---------------------------------------------------------------------------

/**
 * Keyed by the gap the PLAN names, because the executor cannot tell these apart
 * by inspection: all three look identical from inside -- a step that answered,
 * holding rows nobody asked for. Only the plan author knows which sentence is
 * true, and requiring them to say it is the point. A default would be the
 * executor guessing, and a guess recorded in a provenance document is worse
 * than no document.
 */
export const GAPS = {
  induction:
    'The question asks for {asked}, a claim about cases the corpus does not '
    + 'contain. The emitted rows are the cases it does contain. No traversal, '
    + 'and no reasoner sound with respect to these axioms, closes that gap: '
    + 'the step from observed instances to a generalisation over them is '
    + 'chemistry, not inference, and asserting it in an ontology would launder '
    + 'an assumption into a derived fact.',
  vocabulary:
    'The question asks for {asked}. The corpus has no counterpart for that '
    + 'term -- not a missing value, an absent relation. The rows emitted '
    + 'satisfy every constraint that COULD be expressed and the unexpressible '
    + 'one was dropped, which is why they are reported as an extension rather '
    + 'than an answer. Adding the term as an asserted triple would make the '
    + 'constraint applicable and the answer unfounded, since the assertion '
    + 'would come from whoever wrote the mapping rather than from whoever ran '
    + 'the experiment.',
  conditions:
    'The question asks for {asked} under conditions the corpus never records. '
    + 'The emitted rows are what was run, not what was asked about, and the '
    + 'distance between them is not a retrieval failure that a better query '
    + 'closes -- it is an experiment nobody performed.',
};

// ---------------------------------------------------------------------------
// The executor
// ---------------------------------------------------------------------------

export class Executor {
  constructor(registry, maps = null, { replan = true, weights = {} } = {}) {
    this.registry = registry;
    this.maps = maps || new MapAdapter({ name: 'maps', namespace: 'map' });
    // rem:replanning: the prototype re-solves thm:allocation after each step
    // with the remaining budget and the realised cardinalities. sec:limits
    // records that we have not bounded its regret against the clairvoyant
    // allocation, which is the natural comparison we do not make.
    this.replan = replan;
    this.weights = weights;
  }

  // -- driver ---------------------------------------------------------------

  run(plan, budget = null) {
    const { registry } = this;
    registry.resetCounters();
    const totalBudget = budget === null ? plan.budget : budget;

    const ex = new Execution(plan.name);

    // --- Check: decided entirely by declarations, before any contact ---
    const report = check(plan, registry);
    ex.check_report = report;
    if (!report.well_capability) {
      // cor:refuse-before-contact. Halt here; requests_issued stays 0, which is
      // the quantity (V1) asserts.
      for (const step of plan.steps) {
        const fail = report.failures.find((f) => f.step === step.var);
        if (!fail) continue;
        ex.steps.push(new StepResult({
          step: step.var,
          source: step.source || '-',
          verdict: Verdict.SURFACE,
          diagnosis: {
            missing: fail.missing,
            reason: 'required capabilities not declared by the source; '
              + 'no request was issued',
          },
        }));
      }
      ex.requests_issued = registry.totalRequests();
      ex.halted_early = true;
      ex.emitted = { refusal: refusalDocument(plan, report) };
      return ex;
    }

    const specs = yieldSpecs(plan, registry, this.weights);
    const alloc = solve(specs, totalBudget);
    ex.allocation = alloc;

    const values = {};
    let remaining = totalBudget;
    const done = [];

    for (const step of plan.steps) {
      let allocated;
      let price;
      if (this.replan && done.length) {
        const sub = solve(specs.filter((s) => !done.includes(s.step_var)), remaining);
        allocated = sub.of(step.var);
        price = sub.shadow_price;
      } else {
        allocated = alloc.of(step.var);
        price = alloc.shadow_price;
      }

      const res = this.runStep(step, values, ex, allocated, price, remaining);
      ex.steps.push(res);
      remaining = Math.max(0.0, remaining - res.spent);
      done.push(step.var);

      if (res.verdict === Verdict.ANSWER && res.payload !== null) {
        values[step.var] = res.payload;
      } else {
        // prin:verdict: no payload for a non-answer verdict. Successors see the
        // absence and (R1) fires on them.
        values[step.var] = ResultSet.empty('-');
      }

      if (step.on_unresolved === 'fail' && res.verdict !== Verdict.ANSWER) {
        ex.halted_early = true;
        break;
      }
    }

    ex.requests_issued = registry.totalRequests();
    ex.emitted = this.emit(plan, ex, values);
    return ex;
  }

  // -- the rules, in order --------------------------------------------------

  runStep(step, values, ex, allocated, price, remaining) {
    let source;
    if (step.kind === 'from') source = step.source || '-';
    else if (step.kind === 'map') source = `map:${step.maps.join('->')}`;
    else source = step.kind;

    const base = new StepResult({
      step: step.var, source, verdict: Verdict.ANSWER, allocated, shadow_price: price,
    });

    // (R1) a predecessor failed, or answered below its declared expectation.
    // Checked FIRST, so a step that is both starved and over-budget reports
    // starvation: the earlier obstruction is the one that stopped it.
    for (const y of step.beta) {
      const prev = ex.byVar(y);
      if (prev === null) continue;
      if (prev.verdict !== Verdict.ANSWER) {
        base.verdict = Verdict.STARVED;
        base.diagnosis = {
          named_predecessor: y,
          reason: `predecessor ${repr(y)} returned ${prev.verdict}`,
        };
        return base;
      }
      if (prev.retention !== null && prev.expected !== null
          && prev.retention < prev.expected) {
        base.verdict = Verdict.STARVED;
        base.diagnosis = {
          named_predecessor: y,
          reason: `predecessor retention ${formatFixed(prev.retention, 2)} below `
            + `declared expectation ${formatNum(prev.expected)}`,
        };
        return base;
      }
    }

    if (step.kind === 'map') return this.runMap(step, values, base);
    if (step.kind === 'ladder') return this.runLadder(step, values, base);
    if (['union', 'intersect', 'join', 'filter'].includes(step.kind)) {
      return this.runSetop(step, values, base);
    }
    return this.runFrom(step, values, base, allocated, remaining);
  }

  runFrom(step, values, base, allocated, remaining) {
    // Registry.get, resolveFeatures and the map helpers are OUTSIDE the try
    // below: only adapter.evaluate is guarded. A plan naming an unknown source
    // or predicate crashes the run rather than yielding `surface`, because it
    // has not been checked against anything.
    const adapter = this.registry.get(step.source);
    base.snapshot = adapter.snapshot;
    const inputs = {};
    for (const y of step.beta) inputs[y] = values[y];

    // (R2) capability containment. thm:static already decided this without
    // contact, so reaching it here means the checker and adapter disagree.
    const req = resolveFeatures(adapter, step.request);
    if (!adapter.supports(req)) {
      base.verdict = Verdict.SURFACE;
      base.diagnosis = {
        missing: sorted(adapter.missing(req)),
        required: sorted(req),
        reason: 'required capabilities not declared by the source',
      };
      return base;
    }

    // (R3) remaining PLAN budget below cost_Src at the realised input
    // cardinality. prop:necessary-not-sufficient lives here: the cost is a
    // function of an input no static quantity bounds.
    const cost = adapter.cost(step.request, inputs);
    if (remaining < cost) {
      base.verdict = Verdict.REFUSED;
      base.diagnosis = {
        reason: `remaining budget ${formatG(remaining)} below cost ${formatG(cost)} `
          + 'at input cardinality',
        remaining,
        required: cost,
        shortfall: cost - remaining,
      };
      return base;
    }

    // (R4) the step's own annotation b: does the request complete within it?
    const effort = allocated > 0 ? Math.min(step.budget, allocated) : step.budget;
    let payload;
    try {
      payload = adapter.evaluate(step.request, inputs, effort);
    } catch (e) {
      if (e instanceof Timeout) {
        base.verdict = Verdict.TIMEOUT;
        base.diagnosis = {
          reason: `cost ${formatG(cost)} exceeds the effort ${formatG(effort)} `
            + 'allocated to this step',
          step_budget: effort,
          elapsed_cost: cost,
        };
        return base;
      }
      if (e instanceof Refusal) {
        base.verdict = Verdict.SURFACE;
        base.diagnosis = { reason: e.message };
        return base;
      }
      throw e;
    }

    base.spent = cost;
    base.lowered_form = adapter.last_lowered;

    // (R5) empty denotation over this dataset -- a real answer, which is why
    // def:blocker assigns it no blocker.
    if (payload.size === 0) {
      base.verdict = Verdict.EMPTY;
      base.diagnosis = { reason: 'denotation is empty over this dataset' };
      return base;
    }

    // (R6)
    base.verdict = Verdict.ANSWER;
    base.payload = payload;
    return base;
  }

  runMap(step, values, base) {
    const src = values[step.operands[0]];
    const [out, stages] = this.maps.applyChain(step.maps, src);
    base.stages = stages;
    base.spent = 1.0;
    base.snapshot = this.maps.snapshot;

    // Retention and amplification are recorded SEPARATELY, because by
    // prop:cardinality-uninformative their product -- all the output
    // cardinality reveals -- determines neither.
    base.retention = this.maps.survivingFraction(step.maps, src);
    base.amplification = stages.length ? stages[stages.length - 1].amplification : null;
    base.expected = step.expect_partial;

    // def:retention-check: below the declared expectation the step reports
    // starved to its successors, naming mu, epsilon and the observed r.
    if (step.expect_partial !== null && base.retention < step.expect_partial) {
      base.verdict = Verdict.STARVED;
      // The shortfall is in mu, not in the predecessor: the input arrived
      // intact and the translation lost it. Naming the predecessor here would
      // blame a step that answered correctly, so the chain of prop:blame
      // terminates AT this step.
      base.diagnosis = {
        named_predecessor: null,
        lossy_translation: [...step.maps],
        input_from: step.operands[0],
        reason: `retention ${formatFixed(base.retention, 2)} below declared `
          + `expectation ${formatNum(step.expect_partial)}`,
        expectation: step.expect_partial,
        observed: base.retention,
      };
      return base;
    }

    if (out.size === 0) {
      base.verdict = Verdict.EMPTY;
      base.diagnosis = { reason: 'translation image is empty' };
      return base;
    }
    base.verdict = Verdict.ANSWER;
    base.payload = out;
    return base;
  }

  /**
   * Compose declared rung powers multiplicatively: 1 - prod(1 - p_i).
   *
   * A ladder is local. It reaches no source, consumes no requests, and demands
   * no capability, so it is charged nothing. (R1) has already been applied by
   * the caller, so a ladder whose input starved never reaches here.
   */
  runLadder(step, values, base) {
    base.spent = 0.0;
    const src = values[step.operands[0]];

    let residual = 1.0;
    for (const p of step.rungs) residual *= (1.0 - p);
    const composite = 1.0 - residual;
    base.composite_power = composite;

    // def:refuse-climb -- a declared target the declared rungs cannot reach is
    // refused, and the refusal is tight: by the multiplicative law the
    // composite IS what executing the ladder would attain, so no ladder that
    // could have succeeded is rejected here.
    if (step.expect_power !== null && composite < step.expect_power) {
      base.verdict = Verdict.STARVED;
      base.diagnosis = {
        named_predecessor: null,
        declared_rungs: [...step.rungs],
        input_from: step.operands[0],
        reason: `composite power ${formatFixed(composite, 4)} below declared `
          + `expectation ${formatNum(step.expect_power)}`,
        expectation: step.expect_power,
        observed: composite,
        shortfall: step.expect_power - composite,
      };
      return base;
    }

    if (src.isEmpty()) {
      base.verdict = Verdict.EMPTY;
      base.diagnosis = {
        reason: 'ladder input is empty over this dataset',
        composite_power: composite,
      };
      return base;
    }

    base.verdict = Verdict.ANSWER;
    base.payload = src;
    return base;
  }

  runSetop(step, values, base) {
    const operands = step.operands.map((y) => values[y]);
    base.spent = 0.0;
    const ns = operands.length ? operands[0].namespace : '-';
    let out;

    if (step.kind === 'union') {
      const pairs = [];
      for (const a of operands) for (const [i, row] of a.rows) pairs.push([i, row]);
      out = ResultSet.of(ns, pairs);
    } else if (step.kind === 'intersect') {
      let keep = operands[0].identifiers();
      for (const a of operands.slice(1)) keep = setOps.intersect(keep, a.identifiers());
      const pairs = [];
      for (const a of operands) {
        for (const [i, row] of a.rows) if (keep.has(i)) pairs.push([i, row]);
      }
      out = ResultSet.of(ns, pairs);
    } else if (step.kind === 'join') {
      const [left, right] = operands;
      const attr = step.join_on;
      // A Map, not a plain object: the key is an attribute VALUE, which can be
      // undefined, a number or a string. A plain object would coerce all three
      // toward strings and merge rows that Python keeps apart.
      const index = new Map();
      for (const [j, row] of right.rows) {
        const k = row[attr];
        if (!index.has(k)) index.set(k, []);
        index.get(k).push([j, row]);
      }
      const pairs = [];
      for (const [i, row] of left.rows) {
        for (const [, other] of index.get(row[attr]) || []) {
          const merged = { ...row };
          for (const [k, v] of Object.entries(other)) merged[`_joined_${k}`] = v;
          pairs.push([i, merged]);
        }
      }
      out = ResultSet.of(ns, pairs);
    } else { // filter
      const [attr, op, val] = step.where;
      const pairs = [];
      for (const [i, row] of operands[0].rows) {
        // `_id` names the identifier itself. Every row in the common result
        // model has one, and attributes do not survive a non-injective map
        // intact -- when two sources collide on one identifier, ResultSet.of
        // merges their attribute maps and the later write wins. A filter that
        // must pick out a specific element therefore has to name it, not a
        // property it carries.
        if (attr === '_id') {
          if (compare(i, op, val)) pairs.push([i, row]);
          continue;
        }
        if (!Object.prototype.hasOwnProperty.call(row, attr)) continue;
        if (compare(row[attr], op, val)) pairs.push([i, row]);
      }
      out = ResultSet.of(ns, pairs);
    }

    if (out.size === 0) {
      base.verdict = Verdict.EMPTY;
      base.diagnosis = { reason: `${step.kind} produced an empty set` };
      return base;
    }
    base.verdict = Verdict.ANSWER;
    base.payload = out;
    return base;
  }

  // -- emit -----------------------------------------------------------------

  /**
   * The steps that contributed to `target`, in plan order.
   *
   * def:plan binds every input variable by a strictly earlier step, so the
   * reverse reachability closure is finite and acyclic.
   */
  static ancestry(plan, target) {
    const byVar = new Map(plan.steps.map((s) => [s.var, s]));
    const want = new Set();
    const frontier = [target];
    while (frontier.length) {
      const v = frontier.pop();
      const s = byVar.get(v);
      if (s === undefined || want.has(v)) continue;
      want.add(v);
      frontier.push(...s.beta, ...s.operands);
    }
    return plan.steps.filter((s) => want.has(s.var)).map((s) => s.var);
  }

  /**
   * What the emitted set does NOT account for.
   *
   * The motivating case is a partial translation. A map step drops an
   * identifier; every later step then reports honest full coverage of the
   * smaller set it was handed, and the emitted payload is a correct answer to a
   * question narrower than the one asked. Nothing local to the final step
   * records the difference -- the record lives upstream, in that map's
   * retention, and a reader who sees only the payload cannot recover it.
   *
   * That gap is cor:onebit reappearing INSIDE an honest pipeline.
   */
  attrition(plan, ex, target) {
    const losses = [];
    for (const v of Executor.ancestry(plan, target)) {
      const r = ex.byVar(v);
      if (r === null || r.retention === null || r.retention >= 1.0) continue;
      const before = r.stages && r.stages.length ? r.stages[0].input_size : null;
      const after = r.payload !== null ? r.payload.size : null;
      losses.push({
        step: v,
        source: r.source,
        retention: r.retention,
        expected: r.expected,
        input_size: before,
        output_size: after,
        dropped: before !== null && after !== null ? before - after : null,
      });
    }
    const final = ex.byVar(target);
    // Python's `final.payload` is falsy for an EMPTY result set; every JS
    // object is truthy, so the row count must be tested.
    const examined = final !== null && final.payload !== null && !final.payload.isEmpty()
      ? final.payload.size
      : 0;
    const totalDropped = losses.reduce((a, l) => a + (l.dropped || 0), 0);
    return {
      examined,
      unexamined_lower_bound: totalDropped,
      complete: losses.length === 0,
      losses,
      interpretation: losses.length === 0
        ? 'exhaustive over the identifiers that reached the final step, and no '
          + 'identifier was dropped on the way'
        : 'exhaustive over the identifiers that reached the final step; '
          + `${totalDropped} identifier(s) were dropped upstream and never `
          + "examined. Absence from the payload does not distinguish 'tested "
          + "and rejected' from 'never tested'.",
    };
  }

  /**
   * The statement that outranks the verdict.
   *
   * Recorded beside the verdict rather than folded into it. The verdict stays
   * honest about the execution -- every step did answer -- and
   * `answers_question: false` says the execution answered something else.
   */
  static admissibility(e) {
    const gap = e.gap || 'induction';
    return {
      asked_for: e.intension,
      returned: 'recorded extension',
      answers_question: false,
      gap,
      reason: GAPS[gap].replace('{asked}', e.intension),
    };
  }

  emit(plan, ex, values) {
    const out = {};
    for (const e of plan.emits) {
      if (e.divergence) {
        const [a, b] = e.divergence;
        const sa = (values[a] || ResultSet.empty('-')).identifiers();
        const sb = (values[b] || ResultSet.empty('-')).identifiers();
        // thm:route-extent(b): the symmetric difference is a LOWER BOUND on
        // correspondences at least one route fails to resolve. It is a coverage
        // statement, not an error count, and must not be reported as one.
        const key = e.alias || `divergence_${a}_${b}`;
        out[key] = {
          left: a,
          right: b,
          left_only: sorted(setOps.difference(sa, sb)),
          right_only: sorted(setOps.difference(sb, sa)),
          symmetric_difference: setOps.symmetric(sa, sb).size,
          union_size: setOps.union(sa, sb).size,
          interpretation: 'lower bound on correspondences at least one route '
            + 'fails to resolve; neither route contradicts the other',
        };
      } else {
        const r = ex.byVar(e.target);
        const payload = values[e.target];
        const answered = r !== null && r.verdict === Verdict.ANSWER;
        const rec = {
          verdict: r ? r.verdict : null,
          payload: answered && payload && !payload.isEmpty() ? payload.toJSON() : null,
          provenance: e.provenance,
        };
        // `with provenance` is the request for the record, so the coverage
        // statement belongs here rather than beside every payload.
        if (e.provenance) rec.coverage = this.attrition(plan, ex, e.target);
        // An admissibility statement outranks the verdict, so it is recorded
        // beside it rather than folded into it.
        if (e.intension !== null) rec.admissibility = Executor.admissibility(e);
        out[e.target] = rec;
      }
    }
    return out;
  }
}

/**
 * Python raises TypeError comparing a str with a number and the caller drops
 * the row; JS coerces and yields false, which drops it too for the ordering
 * operators. Equality must use === / !== so that "12" == 12 does not become
 * true here when Python says False. null is the one genuine divergence: Python
 * raises on `None < 5` where JS coerces null to 0, so it is rejected up front.
 */
function compare(a, op, b) {
  const bothNumbers = typeof a === 'number' && typeof b === 'number';
  const bothStrings = typeof a === 'string' && typeof b === 'string';
  switch (op) {
    case '==': return a === b;
    case '!=': return a !== b;
    default: break;
  }
  // Ordering across types is a TypeError in Python; the row is dropped.
  if (!bothNumbers && !bothStrings) return false;
  switch (op) {
    case '<': return a < b;
    case '>': return a > b;
    case '<=': return a <= b;
    case '>=': return a >= b;
    default: return false;
  }
}
