/* ============================================================================
 * @sachikonye/sbs — public entry point
 *
 * One high-level orchestrator, runSBS(source), that takes SBS DSL source text
 * and runs it end to end:
 *
 *     compile  (tokenize -> parse -> emit circuit + perturbations + GLSL)
 *       -> solve   (WebGL2 render; falls back to CPU; never throws)
 *       -> extract (R, V, S-entropy triple, flux pattern, backward path)
 *       -> honour the script's observe / perturb / navigate statements
 *
 * The return value is a plain, serialisable object. It carries no rendering
 * context, no typed arrays that a host cannot clone, and no functions — a host
 * (Buhera OS, the hegel playground, a test) maps it to whatever shape it needs.
 *
 * This is the ONLY surface a host should import. The compiler, solver, and
 * metrics extractor are implementation and may change; runSBS is the contract.
 * ========================================================================== */

import { compileSBS, validateSBS } from './dsl/compiler';
import { solveCircuit, solveCPU, computeFluxPattern } from './shaderSolver';
import {
  extractMetrics,
  computeBackwardNavigation,
  findOptimalPerturbation,
} from './metricsExtractor';

/**
 * Translate the DSL's circuit-level `perturb <circuit> { factor }` statements
 * into the edge-indexed `{ idx, factor }` shape the solver and metrics expect.
 *
 * The DSL targets a whole circuit; the solver perturbs individual edges. The
 * SBS disease model (paper §12.3, "enzyme deficiency") reduces the single
 * highest-flux-carrying edge — for glycolysis that is hexokinase. So a
 * circuit-level perturbation is realised by scaling the conductance of the
 * top-flux edge by `factor`. This is the one place the DSL's semantics and the
 * solver's API do not line up 1:1, and it is made explicit here rather than
 * hidden so a future edge-targeted `perturb` syntax can extend it cleanly.
 *
 * @param {object} circuit          built circuit (nodes, edges, numEdges)
 * @param {Array}  perturbations    compiler output: [{ target, factor }]
 * @returns {Array<{idx:number, factor:number}>} edge-indexed perturbation
 */
function resolvePerturbations(circuit, perturbations) {
  if (!circuit || !perturbations || perturbations.length === 0) return null;

  const flux = computeFluxPattern(circuit, null).map(Math.abs);
  let topEdge = 0;
  for (let i = 1; i < flux.length; i++) {
    if (flux[i] > flux[topEdge]) topEdge = i;
  }

  // Every circuit-level perturbation scales the current top-flux edge. Multiple
  // `perturb` statements compose multiplicatively on that edge.
  const factor = perturbations.reduce((f, p) => f * (p.factor ?? 0.1), 1.0);
  return [{ idx: topEdge, factor }];
}

/**
 * Solve a circuit, preferring the real WebGL2 render and falling back to the
 * CPU path on any failure (no DOM, no WebGL2, context lost, compile/link
 * failure). This function never throws.
 *
 * solveCircuit already falls back to solveCPU internally when the float-render
 * extension or program creation fails, but it still throws when there is no
 * document or no webgl2 context at all; this wrapper catches that.
 *
 * @param {object} circuit
 * @param {Array|null} perturbation  edge-indexed perturbation
 * @returns {object} { texture, renderTimeMs, numNodes, backend }
 */
function solveSafe(circuit, perturbation) {
  try {
    return solveCircuit(circuit, perturbation);
  } catch (_err) {
    return solveCPU(circuit, perturbation);
  }
}

/**
 * Run SBS DSL source end to end.
 *
 * @param {string} source          SBS DSL script
 * @param {object} [opts]
 * @param {boolean} [opts.preferCPU=false]  skip WebGL2, use the CPU solver
 *        directly (deterministic, headless; useful for tests)
 * @returns {object} result — always returned, never thrown:
 *   {
 *     ok: boolean,                 // compiled and solved without fatal error
 *     errors: [{message, line}],   // compile errors (fatal)
 *     warnings: [{message, line}], // non-fatal (e.g. unresolved import)
 *     circuit: { numNodes, numEdges, nodes, edges, compartments } | null,
 *     metrics: {                   // null if no circuit was declared
 *       R, V,                      // triple coherence, flux visibility
 *       Se, Sk, St,                // S-entropy triple, per node (arrays)
 *       fluxHealthy, fluxCurrent,  // per-edge flux (arrays)
 *       fluxWeights,               // per-edge normalised flux weight
 *       backend,                   // 'webgl2' | 'cpu'
 *       renderTimeMs,
 *     } | null,
 *     observations: [...],         // targets named by `observe` statements
 *     perturbations: [...],        // resolved edge-indexed perturbations
 *     navigation: [{nodeId,name,mu}] | null,  // if the script navigated
 *     glsl: string | null,         // emitted observation shader
 *   }
 */
export function runSBS(source, opts = {}) {
  const preferCPU = !!opts.preferCPU;

  // --- 1. Compile -----------------------------------------------------------
  const compiled = compileSBS(source);
  if (!compiled.success) {
    return {
      ok: false,
      errors: compiled.errors || [{ message: 'compile failed' }],
      warnings: compiled.warnings || [],
      circuit: null,
      metrics: null,
      observations: [],
      perturbations: [],
      navigation: null,
      glsl: null,
    };
  }

  const circuit = compiled.circuit;

  // A script with no `circuit` block is legal (it may only import or compute);
  // there is simply nothing to solve. Return the compile result cleanly.
  if (!circuit || circuit.numNodes === 0) {
    return {
      ok: true,
      errors: [],
      warnings: compiled.warnings || [],
      circuit: null,
      metrics: null,
      observations: compiled.observations || [],
      perturbations: [],
      navigation: null,
      glsl: compiled.glsl || null,
    };
  }

  // --- 2. Resolve perturbations (circuit-level -> edge-indexed) --------------
  const perturbation = resolvePerturbations(circuit, compiled.perturbations);

  // --- 3. Solve (WebGL2 render, or CPU) -------------------------------------
  const solved = preferCPU
    ? solveCPU(circuit, perturbation)
    : solveSafe(circuit, perturbation);

  // --- 4. Extract metrics ---------------------------------------------------
  const metrics = extractMetrics(solved, circuit, null, perturbation);

  // --- 5. Navigation --------------------------------------------------------
  // The compiler records `navigate` statements as observations of a Navigate
  // node; a backward MAP path is always meaningful once a circuit exists, so we
  // compute it whenever the script asked to navigate.
  const wantsNavigation = (source || '').includes('navigate');
  const navigation = wantsNavigation
    ? computeBackwardNavigation(circuit, perturbation)
    : null;

  return {
    ok: true,
    errors: [],
    warnings: compiled.warnings || [],
    circuit: {
      numNodes: circuit.numNodes,
      numEdges: circuit.numEdges,
      nodes: circuit.nodes,
      edges: circuit.edges,
      compartments: circuit.compartments,
    },
    metrics: {
      R: metrics.R,
      V: metrics.V,
      Se: metrics.Se,
      Sk: metrics.Sk,
      St: metrics.St,
      fluxHealthy: metrics.fluxHealthy,
      fluxCurrent: metrics.fluxCurrent,
      fluxWeights: metrics.fluxWeights,
      backend: metrics.backend,
      renderTimeMs: metrics.renderTimeMs,
    },
    observations: compiled.observations || [],
    perturbations: perturbation || [],
    navigation,
    glsl: compiled.glsl || null,
  };
}

/**
 * Check whether SBS source is syntactically valid without running it.
 * @param {string} source
 * @returns {{ valid: boolean, errors: Array }}
 */
export function checkSBS(source) {
  return validateSBS(source);
}

/**
 * Suggest an l1-sparse restorative perturbation for a diseased circuit — the
 * therapeutic-design step (paper Thm 10.6). Exposed for hosts that want the
 * "treat" operation without re-deriving it.
 * @param {object} circuit
 * @param {Array} perturbation  current (diseased) edge perturbation
 * @param {number} [maxEdges=3]
 */
export function suggestTherapy(circuit, perturbation, maxEdges = 3) {
  return findOptimalPerturbation(circuit, perturbation, maxEdges);
}

export { runSBS as default };
