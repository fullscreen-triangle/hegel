// Stage 3 of the pipeline: Check.
//
// Compute Req(rho_i) for every step by structural recursion over the abstract
// request and test Req(rho_i) subseteq Capset(Src_i). On failure the executor
// halts BEFORE issuing any request and emits a refusal document naming the
// missing features and the step -- cor:refuse-before-contact made operational.
//
// thm:static(a) says the check costs O(m |Feat|). `CheckReport.operations`
// counts the containment tests actually performed so (V2) can measure it.

import { FEAT, sorted } from './model.js';
import { resolveFeatures } from './adapters.js';

export class CapabilityFailure {
  constructor(step, source, required, declared, missing) {
    this.step = step;
    this.source = source;
    this.required = required;
    this.declared = declared;
    this.missing = missing;
  }

  toJSON() {
    return {
      step: this.step,
      source: this.source,
      required: sorted(this.required),
      declared: sorted(this.declared),
      missing: sorted(this.missing),
    };
  }
}

/** The outcome of the static check of thm:static. */
export class CheckReport {
  constructor(wellCapability = true) {
    this.well_capability = wellCapability;
    this.failures = [];
    this.operations = 0;
    this.requirements = {};
    // number of steps, retained so `bound` can report the m|Feat| bound
    this.n_steps = 0;
  }

  /** The m|Feat| bound of thm:static(a), for comparison in (V2). */
  get bound() {
    return this.n_steps * FEAT.size;
  }

  toJSON() {
    return {
      well_capability: this.well_capability,
      failures: this.failures.map((f) => f.toJSON()),
      operations: this.operations,
      bound: this.bound,
      requirements: this.requirements,
    };
  }
}

/** Decide well-capability. Issues no request under any outcome. */
export function check(plan, registry) {
  const report = new CheckReport(true);
  report.n_steps = plan.steps.length;

  for (const step of plan.steps) {
    if (step.kind !== 'from') continue; // map and set steps carry no source demand
    // Registry.get throws Refusal for an unknown source. That propagates out of
    // check() and out of the run -- it is not a `surface` verdict, because a
    // plan naming a source the registry does not hold has not been checked
    // against anything.
    const adapter = registry.get(step.source);
    // Req is asked of the adapter when the adapter has an opinion. A source
    // that reaches a literal by key and one that reaches it by pattern do not
    // demand the same features of the same request, and a table keyed on the
    // predicate alone cannot express that. The default remains the paper's
    // `required_features`; overriding is a declaration by the adapter author
    // and is as unverified as the capability set itself
    // (rem:honesty-assumption).
    const req = resolveFeatures(adapter, step.request);
    report.requirements[step.var] = sorted(req);
    // One membership test per required feature: this is the count thm:static
    // bounds, and it is what (V2) measures.
    const missing = [];
    for (const f of sorted(req)) {
      report.operations += 1;
      if (!adapter.capabilities.has(f)) missing.push(f);
    }
    if (missing.length) {
      report.well_capability = false;
      report.failures.push(new CapabilityFailure(
        step.var,
        step.source,
        sorted(req),
        sorted(adapter.capabilities),
        missing,
      ));
    }
  }
  return report;
}

/**
 * The document emitted when the check fails.
 *
 * It names the missing features and the step. It is NOT an empty result: the
 * distinction is the content of cor:onebit.
 */
export function refusalDocument(plan, report) {
  return {
    plan: plan.name,
    outcome: 'refused_statically',
    reason: 'ill-capability plan; no request was issued',
    failures: report.failures.map((f) => f.toJSON()),
    steps: [],
  };
}
