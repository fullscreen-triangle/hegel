/* ============================================================================
 * Parameter sweeps, run in the browser.
 *
 * A single execution settles one proposition at one point. A chart needs a
 * curve, so this module varies a parameter and MEASURES, calling the same
 * functions the notebook calls. Nothing here fits a model or draws a
 * schematic: every value comes back from `check` or from a real `Executor`
 * run against a fixture registry.
 *
 * That is the whole reason these sweeps live here rather than in a JSON file
 * beside the page. A chart drawn from a dump is a picture of a run that
 * happened somewhere else, and the reader has to take the axis on trust. A
 * chart drawn from these functions recomputes when the reader moves a
 * control, which is the only way the claim "the count is exactly 2m−1" can be
 * checked rather than believed.
 *
 * The Python in ckg/validation-federated/sweeps.py computes the same
 * quantities for the manuscript figures. Neither is the source of truth: the
 * operational definitions in the paper are, and these are two readings of
 * them.
 *
 * Cost. The heaviest sweep here is `verdictGrid`, which executes one plan per
 * cell -- 100 plans at the default resolution, a few tens of milliseconds.
 * Callers memoise on the parameters rather than on a timer.
 * ========================================================================== */

import { parse } from './parser.js';
import { Executor } from './execute.js';
import { check } from './check.js';
import { Verdict } from './model.js';
import { PREDICATE_FEATURES } from './adapters.js';
import { buildRegistry, buildMaps, cardinalityPair } from './fixtures/build.js';
import { byId } from './plans.js';

/** A fresh registry per execution, as the validation suite does. */
const world = () => [buildRegistry(), buildMaps()];

const runSource = (text) => {
  const [reg, maps] = world();
  return new Executor(reg, maps).run(parse(text));
};

/* ------------------------------------------------------------------ *
 * 1. The verdict plane.
 *
 * cor:onebit collapses five of six verdicts onto one observable value.
 * Sweeping the two parameters that move a plan between verdicts shows the
 * regions a boolean interface merges -- and shows that they are regions, not
 * scattered points, which is what makes the collapse systematic rather than
 * incidental.
 * ------------------------------------------------------------------ */

export const DEFAULT_BUDGETS = [1, 2, 3, 4, 5, 6, 8, 10, 14, 20];

const verdictPlan = (budget, expect, within) => `plan sweep {
  budget ${budget} requests

  let acids = from chebi
      ask descendants_of("CHEBI:1")
      within 10

  let kegg  = map acids via chebi2kegg
      expect partial ${expect}

  let rxns  = from rhea
      ask reactions_consuming(?c)
      with ?c in kegg
      within ${within}

  emit rxns
}`;

/**
 * Execute the same plan across a budget × expectation grid.
 *
 * @param {object}   opts
 * @param {number[]} opts.budgets - request budgets, one per column
 * @param {number}   opts.nExpect - expectation levels, i/nExpect for i=1..n
 * @param {number}   opts.within  - the last step's time bound; lowering it is
 *   what moves cells into `timeout`, so it is a control and not a constant
 * @returns {{cells, budgets, expects, counts, oneBitTrue, oneBitFalse}}
 */
export function verdictGrid({
  budgets = DEFAULT_BUDGETS, nExpect = 10, within = 60,
} = {}) {
  const expects = Array.from({ length: nExpect }, (_, i) => (i + 1) / nExpect);
  const cells = [];
  for (const b of budgets) {
    for (const e of expects) {
      const ex = runSource(verdictPlan(b, e.toFixed(2), within));
      const last = ex.steps.length ? ex.steps[ex.steps.length - 1] : null;
      cells.push({
        budget: b,
        expect: e,
        verdict: last ? last.verdict : Verdict.SURFACE,
        requests: ex.steps.reduce((a, s) => a + s.spent, 0),
        // The one bit a caller reading success-or-failure actually sees.
        one_bit: Boolean(last && last.verdict === Verdict.ANSWER),
        n_steps_run: ex.steps.length,
      });
    }
  }
  const counts = {};
  cells.forEach((c) => { counts[c.verdict] = (counts[c.verdict] || 0) + 1; });
  return {
    cells, budgets, expects, counts,
    oneBitTrue: cells.filter((c) => c.one_bit).length,
    oneBitFalse: cells.filter((c) => !c.one_bit).length,
  };
}

/* ------------------------------------------------------------------ *
 * 2. The static check.
 *
 * thm:static bounds the check at m|Feat| operations; the measured count is
 * what this sweep reports against it. cor:refuse-before-contact fixes the
 * request counter at zero on refusal, and the requests the refused plan WOULD
 * have issued are the saving -- so the ill variant is executed at every plan
 * length rather than asserted once and extrapolated.
 * ------------------------------------------------------------------ */

const chainPlan = (m, source = 'chebi') => {
  const body = [
    `plan p${m} {`, '  budget 400 requests',
    `  let s0 = from ${source}`,
    '      ask descendants_of("CHEBI:1")', '      within 10',
  ];
  for (let i = 1; i < m; i += 1) {
    body.push(`  let s${i} = from rhea`,
      '      ask reactions_consuming(?c)',
      `      with ?c in s${i - 1}`,
      '      within 20');
  }
  body.push(`  emit s${m - 1}`, '}');
  return body.join('\n');
};

/**
 * Check cost and refusal saving against plan length.
 *
 * @param {number} maxM - longest plan to measure (the x axis runs 1..maxM)
 * @returns {{rows, featureCount}} one row per length, each carrying the
 *   measured operation count, the m|Feat| bound, the requests a well-capable
 *   plan issues, and the requests the ill-capable variant issues (zero, or
 *   the claim is false).
 */
export function checkCost(maxM = 12) {
  const rows = [];
  let featureCount = 0;
  for (let m = 1; m <= maxM; m += 1) {
    const text = chainPlan(m);
    const plan = parse(text);
    const [reg, maps] = world();
    const rep = check(plan, reg);
    featureCount = rep.n_steps ? rep.bound / rep.n_steps : featureCount;

    const wouldIssue = new Executor(reg, maps).run(plan).requests_issued;

    // The same plan with its first step pointed at a source that cannot
    // answer it. enzdb declares neither the hierarchy nor the pattern
    // features `descendants_of` requires, so thm:static must reject it.
    const ill = parse(text.replace('from chebi', 'from enzdb'));
    const [reg2, maps2] = world();
    const illRep = check(ill, reg2);
    const illEx = new Executor(reg2, maps2).run(ill);

    rows.push({
      m,
      operations: rep.operations,
      bound: rep.bound,
      would_issue: wouldIssue,
      issued_after_refusal: illEx.requests_issued,
      refused: illEx.requests_issued === 0 && !illRep.well_capability,
    });
  }
  return { rows, featureCount };
}

/**
 * What each source declares, against what each predicate requires.
 *
 * The asymmetry this table exposes is the one the prototype cannot test away:
 * an under-declaration shows here as a predicate the source cannot serve, and
 * an over-declaration shows as nothing at all (rem:honesty-assumption).
 */
export function capabilityMatrix() {
  const [reg] = world();
  const sources = [...reg.adapters.keys()].sort();
  const predicates = [...PREDICATE_FEATURES.keys()].sort();
  const cells = [];
  for (const s of sources) {
    const ad = reg.adapters.get(s);
    for (const p of predicates) {
      const feats = PREDICATE_FEATURES.get(p);
      const missing = [...feats].filter((f) => !ad.capabilities.has(f));
      cells.push({
        source: s,
        predicate: p,
        n_required: feats.size ?? feats.length,
        n_declared: ad.capabilities.size,
        n_missing: missing.length,
        admitted: missing.length === 0,
      });
    }
  }
  return { sources, predicates, cells };
}

/* ------------------------------------------------------------------ *
 * 3. Blame.
 *
 * prop:blame: every bound variable is bound by an EARLIER step, so a blame
 * chain strictly decreases in position and terminates within m hops. That
 * makes termination an arithmetic fact rather than a budget, and the measured
 * maximum should sit strictly under the bound at every length.
 * ------------------------------------------------------------------ */

const blamePlan = (m, expect) => {
  const body = [
    `plan b${m} {`, '  budget 400 requests',
    '  let s0 = from chebi',
    '      ask descendants_of("CHEBI:1")', '      within 10',
    '  let s1 = map s0 via chebi2kegg',
    `      expect partial ${expect}`,
  ];
  let prev = 's1';
  for (let i = 2; i < m; i += 1) {
    body.push(`  let s${i} = map ${prev} via kegg2rhea`,
      `      expect partial ${expect}`);
    prev = `s${i}`;
  }
  body.push(`  emit ${prev}`, '}');
  return body.join('\n');
};

/**
 * Blame-chain length against plan length.
 *
 * @param {object} opts
 * @param {number} opts.maxM   - longest plan (x axis runs 2..maxM)
 * @param {number} opts.expect - declared honesty on every map step. At 0.95
 *   the maps cannot meet their declaration and starve downstream; raising it
 *   toward 0.1 is what empties the chains, and watching them empty is the
 *   point of making it a control.
 */
export function blameChains({ maxM = 9, expect = 0.95 } = {}) {
  const rows = [];
  for (let m = 2; m <= maxM; m += 1) {
    const ex = runSource(blamePlan(m, expect.toFixed(2)));
    const starved = ex.steps.filter((s) => s.verdict === Verdict.STARVED);
    const chains = starved.map((s) => ex.blameChain(s.step).length - 1);
    rows.push({
      m,
      n_steps: ex.steps.length,
      n_starved: starved.length,
      max_hops: chains.length ? Math.max(...chains) : 0,
      mean_hops: chains.length ? chains.reduce((a, b) => a + b, 0) / chains.length : 0,
      bound: ex.steps.length,
    });
  }
  return rows;
}

/**
 * How far a single perturbation reaches: cor:rerun confinement.
 *
 * The claim is that a step's outcome depends only on steps at earlier
 * positions, so perturbing position p can change positions >= p and nothing
 * before them. Drawing that as "which steps failed" would be measuring the
 * wrong thing: this chain STARVES ON ITS OWN after two translation hops --
 * chebi2kegg retains 0.78, kegg2rhea 0.43, and the third hop has nothing left
 * -- so a plain failure map is dominated by exhaustion the perturbation had no
 * part in.
 *
 * What is measured instead is the DIFFERENCE against an unperturbed baseline:
 * a cell is filled only where the verdict CHANGED. Steps that were already
 * starving stay unfilled, and the diagonal structure that survives is the
 * perturbation's own reach rather than the chain's decay.
 *
 * That makes the null meaningful. An upstream cell could light up here -- it
 * would mean a later step's expectation had reached backwards -- and none
 * does.
 */
export function blamePropagation({ nSteps = 5, bad = 0.95, good = 0.1 } = {}) {
  const build = (pos) => {
    const body = [
      'plan c {', '  budget 400 requests',
      '  let s0 = from chebi',
      '      ask descendants_of("CHEBI:1")', '      within 10',
    ];
    let prev = 's0';
    for (let i = 1; i <= nSteps; i += 1) {
      const e = i === pos + 1 ? bad : good;
      body.push(i === 1
        ? `  let s${i} = map ${prev} via chebi2kegg`
        : `  let s${i} = map ${prev} via kegg2rhea`);
      body.push(`      expect partial ${e.toFixed(2)}`);
      prev = `s${i}`;
    }
    body.push(`  emit ${prev}`, '}');
    return body.join('\n');
  };

  // pos = -1 perturbs nothing: the chain as it behaves when left alone.
  const baseline = runSource(build(-1)).steps.map((s) => s.verdict);

  const rows = [];
  for (let pos = 0; pos < nSteps; pos += 1) {
    const verdicts = runSource(build(pos)).steps.map((s) => s.verdict);
    const changed = [];
    verdicts.forEach((v, i) => { if (v !== baseline[i]) changed.push(i); });
    rows.push({
      perturbed_at: pos + 1,
      verdicts,
      changed,
      n_changed: changed.length,
      first_changed: changed.length ? changed[0] : null,
      // The property under test: no change strictly upstream of the
      // perturbed position.
      confined: changed.every((i) => i >= pos + 1),
    });
  }
  return { baseline, rows, nSteps, bad, good };
}

/* ------------------------------------------------------------------ *
 * 4. The (r, a) plane.
 *
 * prop:cardinality-uninformative: only the PRODUCT r·a is observable from
 * |mu(S)|. The level sets of the product are hyperbolae, and every point on
 * one is indistinguishable from the others by output size alone -- which is
 * why the two quantities are recorded separately in every step result.
 *
 * This one is arithmetic on the definitions rather than an execution: r and a
 * are defined as |S ∩ dom mu|/|S| and images-per-retained-element, and the
 * output cardinality is their product times the input. There is nothing to
 * run.
 * ------------------------------------------------------------------ */

/**
 * @param {object} opts
 * @param {number} opts.n     - input cardinality |S|
 * @param {number} opts.maxA  - largest amplification to plot
 * @param {number[]} opts.targets - output sizes to draw as iso-cardinality
 *   families; each is a level set of the product
 */
export function cardinalityPlane({ n = 24, maxA = 6, targets = [12, 24, 48] } = {}) {
  const cells = [];
  for (let k = 1; k <= n; k += 1) {
    for (let a = 1; a <= maxA; a += 1) {
      cells.push({ r: k / n, a, ratio: (k / n) * a, output: k * a, input: n });
    }
  }
  const families = [];
  for (const target of targets) {
    const fam = cells.filter((c) => c.output === target);
    if (fam.length >= 2) {
      const rs = fam.map((c) => c.r);
      families.push({
        output: target,
        points: fam.map((c) => ({ r: c.r, a: c.a })),
        spread: Math.max(...rs) / Math.min(...rs),
      });
    }
  }
  return { cells, families, n, maxA };
}

/**
 * The measured counterexample behind the plane.
 *
 * Two maps over the same 8-element input, each emitting 8 identifiers, with
 * retentions 1.00 and 0.25. This is (V8): the pair is constructed for the
 * purpose -- mu_hi keeps everything and sends each element to one image,
 * mu_lo keeps two of eight and sends each to four -- because the proposition
 * is that equal output cardinality is compatible with ANY retention, and a
 * pair taken from the corpus would only show that it is compatible with the
 * two retentions that corpus happens to hold.
 *
 * The numbers still come back from the map objects rather than from here:
 * `retention` and `amplification` are the same methods the executor calls on
 * every map step.
 */
export function retentionCounterexample() {
  const [hi, lo, s] = cardinalityPair();
  const set = new Set(s);
  const rows = [hi, lo].map((mu) => {
    const r = mu.retention(set);
    const a = mu.amplification(set);
    return {
      map: mu.name,
      input_size: set.size,
      output_size: mu.image(set).size,
      retention: r,
      amplification: a,
      product: r * a,
    };
  });
  return {
    rows,
    equal_output: rows[0].output_size === rows[1].output_size,
    unequal_retention: rows[0].retention !== rows[1].retention,
    retention_ratio: rows[0].retention / rows[1].retention,
  };
}

/**
 * The factorisation, stage by stage, along a real chain.
 *
 * thm:retention(a): |S_k|/|S_0| = prod r_i a_i, unconditionally. This is (V7).
 * The seed is whatever the healthy chain's first step actually returned, so
 * the identity is checked against a measurement rather than against a set
 * chosen to make it come out.
 *
 * The surviving fraction rho is tracked separately, by following each
 * identifier's trajectory. It is NOT the product: thm:retention(b),(c) bound
 * it from either side and the gap between those bounds is not slack
 * (rem:bounds-gap), which is the reason both are drawn.
 *
 * The chain is non-injective -- CHEBI:9 and CHEBI:10 collide on KEGG:C9 -- so
 * the upper bound rho <= min r_i does not apply here. That is the point of
 * rem:injectivity-needed, and the sweep reports applicability rather than
 * quietly drawing a bound that does not hold.
 */
export function chainFactorisation({ names = ['chebi2kegg', 'kegg2rhea'] } = {}) {
  const [reg, maps] = world();
  const ex = new Executor(reg, maps).run(parse(byId('healthy_chain').source));
  const seed = ex.byVar('acids').payload;

  const [out, stages] = maps.applyChain(names, seed);
  const rho = maps.survivingFraction(names, seed);

  let prod = 1;
  const cumulative = stages.map((st) => {
    prod *= st.retention * (st.amplification || 0);
    return prod;
  });
  const ratio = out.size / seed.size;

  // Injectivity ON THE REALISED SETS, which is the hypothesis thm:retention(b)
  // actually carries -- not injectivity of the map as declared.
  const chain = maps.chain(names);
  let cur = seed.identifiers();
  const injective = chain.map((mu) => {
    const flat = [];
    for (const u of cur) if (mu.pairs.has(u)) flat.push(...mu.pairs.get(u));
    cur = mu.image(cur);
    return flat.length === new Set(flat).size;
  });

  const upper = Math.min(...stages.map((st) => st.retention));
  const lower = Math.max(0, 1 - stages.reduce((a, st) => a + (1 - st.retention), 0));

  return {
    stages,
    cumulative,
    input_size: seed.size,
    output_size: out.size,
    observed_ratio: ratio,
    product: prod,
    factorisation_holds: Math.abs(prod - ratio) < 1e-9,
    surviving_fraction: rho,
    per_stage_injective: injective,
    chain_injective: injective.every(Boolean),
    upper_bound: upper,
    lower_bound: lower,
    upper_applicable: injective.every(Boolean),
    residual_bound_r1: stages[0].retention,
  };
}
