/* ============================================================================
 * hfq — the hegel federated query interpreter
 *
 * A plan names sources abstractly and declares a budget. This module parses the
 * plan, resolves each source against a local fixture registry, checks whether
 * the source can express what the step asks, allocates the budget across the
 * steps, executes, and returns the document the notebook renders.
 *
 * The pipeline is the one specified in part6-realisation.tex:
 *
 *   parse -> resolve -> check -> allocate -> execute -> emit
 *
 * Every adapter resolves against a local fixture. No request leaves the
 * machine, by construction rather than by configuration: nothing in this
 * module or the ones it imports performs network I/O, and the page it powers
 * ships no code that could.
 *
 * There are two other implementations of this interpreter and they are not
 * interchangeable. The Python in ckg/validation-federated/ is the VALIDATION
 * ARTIFACT -- it exercises (V1)-(V16) against the same fixtures and is not a
 * benchmark. The Rust CLI is the final form, which a user runs locally and
 * pairs with this page by token. This module is what a visitor gets before
 * either: the whole interpreter, in the browser, with no server.
 * ========================================================================== */

import { parse, ParseError } from './parser.js';
import { Executor } from './execute.js';
import { Refusal } from './adapters.js';
import { Verdict, sorted, setOps } from './model.js';
import { buildRegistry, buildMaps, buildPaperRegistry, budgetTrap } from './fixtures/build.js';
import { buildBiocatRegistry } from './fixtures/biocat.js';

export { parse, ParseError } from './parser.js';
export { Executor } from './execute.js';
export * from './model.js';

// ---------------------------------------------------------------------------
// Registry selection
// ---------------------------------------------------------------------------

/**
 * The four fixture worlds declare disjoint source names, so the sources a plan
 * names determine which world it belongs to. This is inference over declared
 * names and not a guess: a plan naming a source no world declares is reported
 * as an unknown source rather than silently run against the wrong fixture.
 */
export const WORLDS = {
  main: ['chebi', 'rhea', 'enzdb'],
  paper: ['CHEBI', 'RHEA', 'KEGG'],
  tiny: ['tiny_onto', 'tiny_graph'],
  biocat: ['TAX', 'RXN', 'SEQ', 'PROV', 'INST'],
};

function buildWorld(world) {
  if (world === 'biocat') return buildBiocatRegistry();
  if (world === 'paper') return buildPaperRegistry();
  if (world === 'tiny') return [budgetTrap(), buildMaps()];
  return [buildRegistry(), buildMaps()];
}

/** Name the fixture world a parsed plan belongs to, by its declared sources. */
export function selectWorld(plan) {
  const named = new Set(
    plan.steps.map((s) => s.source).filter((s) => s && !s.startsWith('map:')),
  );
  let best = 'main';
  let score = -1;
  for (const [world, decl] of Object.entries(WORLDS)) {
    const hit = decl.filter((d) => named.has(d)).length;
    if (hit > score) {
      best = world;
      score = hit;
    }
  }
  const unknown = sorted(setOps.difference(named, new Set(WORLDS[best])));
  return { world: best, unknown };
}

// ---------------------------------------------------------------------------
// Cell assembly
// ---------------------------------------------------------------------------

/** Nodes and edges of def:plan's dependency graph, for the DAG view. */
function dagOf(plan) {
  return {
    nodes: plan.steps.map((s, i) => ({
      id: s.var, kind: s.kind, source: s.source ?? null, position: i,
    })),
    edges: plan.steps.flatMap((s) => (s.beta || []).map((b) => ({ from: b, to: s.var }))),
    emits: plan.emits.map((e) => ({
      target: e.target,
      provenance: e.provenance,
      divergence: e.divergence ? [...e.divergence] : null,
      alias: e.alias,
    })),
  };
}

/**
 * Parse, check, allocate and execute one plan. **Never throws.**
 *
 * @param {string} source - plan text, as the notebook cell holds it.
 * @returns {object} result — always returned, never thrown. On success:
 *   {ok: true, plan, outcome, world, check, allocation, requests_issued,
 *    halted_early, steps[], emitted, dag, declared_budget, blame}
 *   On failure: {ok: false, stage, error, line?} where `stage` is one of
 *   'parse' | 'resolve' | 'execute' | 'internal'.
 *
 * The stages are the pipeline's own, so a failure names where it happened: a
 * plan that does not parse never reached the check, and a plan refused at the
 * check never reached a source. That distinction is the point of the framework
 * and it would be lost by returning a single error string.
 */
export function runPlan(source) {
  let plan;
  try {
    plan = parse(source);
  } catch (e) {
    if (e instanceof ParseError) {
      return { ok: false, stage: 'parse', error: e.message, line: e.line ?? null };
    }
    return { ok: false, stage: 'parse', error: String(e && e.message ? e.message : e) };
  }

  const { world, unknown } = selectWorld(plan);
  if (unknown.length) {
    return {
      ok: false,
      stage: 'resolve',
      world,
      error: `unknown source(s): ${unknown.join(', ')}`,
      declared: sorted(new Set(Object.values(WORLDS).flat())),
    };
  }

  let ex;
  try {
    const [reg, maps] = buildWorld(world);
    ex = new Executor(reg, maps).run(plan);
  } catch (e) {
    // Refusal reaching here is a registry or predicate error, not a verdict:
    // an unknown source name or abstract predicate propagates out of the
    // executor rather than being assigned `surface`, because a plan naming one
    // has not been checked against anything.
    if (e instanceof Refusal) {
      return { ok: false, stage: 'resolve', world, error: e.message };
    }
    return {
      ok: false,
      stage: 'execute',
      world,
      error: `${e && e.name ? e.name : 'Error'}: ${e && e.message ? e.message : e}`,
    };
  }

  const out = ex.toJSON();
  out.ok = true;
  out.world = world;
  out.dag = dagOf(plan);
  out.declared_budget = plan.budget;

  // prop:blame -- the chain is walked for every starved step, so the reader
  // sees the root cause rather than only the symptom.
  const blame = {};
  for (const s of ex.steps) {
    if (s.verdict === Verdict.STARVED) blame[s.step] = ex.blameChain(s.step);
  }
  out.blame = blame;

  return out;
}

export default runPlan;
