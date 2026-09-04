// Stage 4 of the pipeline: Allocate.
//
// Solve def:alloc by bisection on the shadow price p, using the default yield
//
//     gamma_i(e) = w_i log(1 + e),   gamma_i'(e) = w_i / (1 + e),
//
// whose derivative inverts in closed form to e = w_i/p - 1. By thm:allocation
// the optimum is characterised by a single scalar p* with
//
//     e_i* > 0  =>  gamma_i'(e_i*) = p*
//     e_i* = 0  =>  gamma_i'(0)   <= p*
//
// and p* is the unique root of sum_i max(0, (gamma_i')^{-1}(p)) = B.
//
// Steps whose yield is all-or-nothing (a `lookup` against a REST interface: one
// request retrieves the record, further requests retrieve nothing) have a step
// function for a yield -- neither strictly concave nor differentiable -- so
// thm:allocation does not apply to them. Per rem:concavity-fails they are
// removed from the optimisation, their fixed cost charged to the budget first,
// and the remainder solved over the rest. The consequence, which the JSON
// records, is that the shadow price governs only a subset of the plan.

import { sorted } from './model.js';

/** gamma_i, as either a concave yield with weight w_i or a step function. */
export class YieldSpec {
  constructor(stepVar, { weight = 1.0, allOrNothing = false, fixedCost = 1.0 } = {}) {
    this.step_var = stepVar;
    this.weight = weight;
    // All-or-nothing steps are excluded from the optimisation and charged first.
    this.all_or_nothing = allOrNothing;
    this.fixed_cost = fixedCost;
  }

  gamma(e) {
    if (this.all_or_nothing) return e >= this.fixed_cost ? this.weight : 0.0;
    return this.weight * Math.log1p(Math.max(0.0, e));
  }

  /** gamma_i'(e). Undefined for step functions; they never reach here. */
  dgamma(e) {
    return this.weight / (1.0 + Math.max(0.0, e));
  }

  /** (gamma_i')^{-1}(p) = w_i/p - 1, clipped at 0. */
  invert(p) {
    if (p <= 0.0) return Infinity;
    return Math.max(0.0, this.weight / p - 1.0);
  }
}

export class Allocation {
  constructor(budget = 0.0) {
    // Maps, not plain objects: insertion order is the summation order in
    // kkt_residuals, and float addition is not associative.
    this.effort = new Map();
    this.shadow_price = 0.0;
    this.charged_first = new Map();
    this.budget = budget;
    this.optimised_budget = 0.0;
    this.support = [];
  }

  of(v) {
    return this.effort.has(v) ? this.effort.get(v) : 0.0;
  }

  toJSON() {
    const obj = (m) => {
      const o = {};
      for (const k of sorted(m.keys())) o[k] = m.get(k);
      return o;
    };
    return {
      budget: this.budget,
      shadow_price: this.shadow_price,
      effort: obj(this.effort),
      charged_first: obj(this.charged_first),
      optimised_budget: this.optimised_budget,
      support: sorted(this.support),
    };
  }
}

/** Water-filling by bisection on p. Returns e* and p*. */
export function solve(specs, budget, tol = 1e-12, maxIter = 400) {
  const alloc = new Allocation(budget);

  // rem:concavity-fails: charge the all-or-nothing steps first, IN ORDER,
  // while the budget lasts. Their effort is not a decision variable. The order
  // is the plan's step order and decides who gets paid when the budget runs
  // short, so it must not be sorted.
  let remaining = budget;
  const concave = [];
  for (const spec of specs) {
    if (spec.all_or_nothing) {
      const take = Math.min(spec.fixed_cost, Math.max(0.0, remaining));
      alloc.charged_first.set(spec.step_var, take);
      alloc.effort.set(spec.step_var, take);
      remaining -= take;
    } else {
      concave.push(spec);
    }
  }
  remaining = Math.max(0.0, remaining);
  alloc.optimised_budget = remaining;

  if (!concave.length || remaining <= 0.0) {
    alloc.shadow_price = 0.0;
    for (const spec of concave) alloc.effort.set(spec.step_var, 0.0);
    return alloc;
  }

  const total = (p) => concave.reduce((acc, s) => acc + s.invert(p), 0.0);

  // At p >= max w_i every e_i* is 0, so total(p) = 0 <= B: bracket above there.
  let hi = Math.max(...concave.map((s) => s.weight));
  let lo = 1e-15;
  // Grow hi until total(hi) <= budget (it is 0 at max w_i, so this holds).
  while (total(hi) > remaining) {
    hi *= 2.0;
    if (hi > 1e18) break; // unreachable for finite weights
  }
  // total is strictly DECREASING in p on the region where it is positive, so
  // the bracket update is inverted from the usual convention: t > remaining
  // means p is too small, and it is the LOWER bound that moves up.
  for (let i = 0; i < maxIter; i += 1) {
    const mid = 0.5 * (lo + hi);
    const t = total(mid);
    if (Math.abs(t - remaining) <= tol * Math.max(1.0, remaining)) {
      lo = mid;
      hi = mid;
      break;
    }
    if (t > remaining) lo = mid;
    else hi = mid;
  }
  const p = 0.5 * (lo + hi);
  alloc.shadow_price = p;

  for (const spec of concave) {
    const e = spec.invert(p);
    alloc.effort.set(spec.step_var, e);
    if (e > 0.0) alloc.support.push(spec.step_var);
  }
  return alloc;
}

/**
 * The quantities (V12) checks against thm:allocation.
 *
 * On the support all marginal yields must agree with p*; off the support
 * gamma_i'(0) <= p* must hold; and the budget must bind.
 */
export function kktResiduals(specs, alloc) {
  const p = alloc.shadow_price;
  const onSupport = [];
  const offSupport = [];
  for (const spec of specs) {
    if (spec.all_or_nothing) continue;
    const e = alloc.of(spec.step_var);
    if (e > 0.0) {
      onSupport.push({
        step: spec.step_var,
        marginal: spec.dgamma(e),
        residual: Math.abs(spec.dgamma(e) - p),
      });
    } else {
      offSupport.push({
        step: spec.step_var,
        marginal_at_zero: spec.dgamma(0.0),
        satisfies: spec.dgamma(0.0) <= p + 1e-9,
      });
    }
  }
  let spent = 0.0;
  for (const v of alloc.effort.values()) spent += v;
  return {
    shadow_price: p,
    on_support: onSupport,
    off_support: offSupport,
    // Python's max(..., default=0.0); JS's Math.max() of nothing is -Infinity.
    max_residual: onSupport.length
      ? Math.max(...onSupport.map((d) => d.residual))
      : 0.0,
    all_off_support_satisfy: offSupport.every((d) => d.satisfies),
    spent,
    budget: alloc.budget,
    budget_binds: Math.abs(spent - alloc.budget) <= 1e-6 * Math.max(1.0, alloc.budget),
  };
}
