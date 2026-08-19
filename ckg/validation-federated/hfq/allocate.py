"""Stage 4 of the pipeline: Allocate.

Solve def:alloc by bisection on the shadow price p, using the default yield

    gamma_i(e) = w_i log(1 + e),   gamma_i'(e) = w_i / (1 + e),

whose derivative inverts in closed form to e = w_i/p - 1. By thm:allocation
the optimum is characterised by a single scalar p* with

    e_i* > 0  =>  gamma_i'(e_i*) = p*
    e_i* = 0  =>  gamma_i'(0)   <= p*

and p* is the unique root of sum_i max(0, (gamma_i')^{-1}(p)) = B.

Steps whose yield is all-or-nothing (a `lookup` against a REST interface: one
request retrieves the record, further requests retrieve nothing) have a step
function for a yield -- neither strictly concave nor differentiable -- so
thm:allocation does not apply to them. Per rem:concavity-fails they are removed
from the optimisation, their fixed cost charged to the budget first, and the
remainder solved over the rest. The consequence, which the JSON records, is
that the shadow price governs only a subset of the plan.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


@dataclass
class YieldSpec:
    """gamma_i, as either a concave yield with weight w_i or a step function."""

    step_var: str
    weight: float = 1.0
    #: All-or-nothing steps are excluded from the optimisation and charged first.
    all_or_nothing: bool = False
    fixed_cost: float = 1.0

    def gamma(self, e: float) -> float:
        if self.all_or_nothing:
            return self.weight if e >= self.fixed_cost else 0.0
        return self.weight * math.log1p(max(0.0, e))

    def dgamma(self, e: float) -> float:
        """gamma_i'(e). Undefined for step functions; they never reach here."""
        return self.weight / (1.0 + max(0.0, e))

    def invert(self, p: float) -> float:
        """(gamma_i')^{-1}(p) = w_i/p - 1, clipped at 0."""
        if p <= 0.0:
            return math.inf
        return max(0.0, self.weight / p - 1.0)


@dataclass
class Allocation:
    effort: Dict[str, float] = field(default_factory=dict)
    shadow_price: float = 0.0
    charged_first: Dict[str, float] = field(default_factory=dict)
    budget: float = 0.0
    optimised_budget: float = 0.0
    support: List[str] = field(default_factory=list)

    def of(self, var: str) -> float:
        return self.effort.get(var, 0.0)

    def to_json(self) -> Dict[str, Any]:
        return {
            "budget": self.budget,
            "shadow_price": self.shadow_price,
            "effort": {k: self.effort[k] for k in sorted(self.effort)},
            "charged_first": {k: self.charged_first[k] for k in sorted(self.charged_first)},
            "optimised_budget": self.optimised_budget,
            "support": sorted(self.support),
        }


def solve(specs: Sequence[YieldSpec], budget: float,
          tol: float = 1e-12, max_iter: int = 400) -> Allocation:
    """Water-filling by bisection on p. Returns e* and p*."""
    alloc = Allocation(budget=budget)

    # rem:concavity-fails: charge the all-or-nothing steps first, in order,
    # while the budget lasts. Their effort is not a decision variable.
    remaining = budget
    concave: List[YieldSpec] = []
    for spec in specs:
        if spec.all_or_nothing:
            take = min(spec.fixed_cost, max(0.0, remaining))
            alloc.charged_first[spec.step_var] = take
            alloc.effort[spec.step_var] = take
            remaining -= take
        else:
            concave.append(spec)
    remaining = max(0.0, remaining)
    alloc.optimised_budget = remaining

    if not concave or remaining <= 0.0:
        alloc.shadow_price = 0.0
        for spec in concave:
            alloc.effort[spec.step_var] = 0.0
        return alloc

    def total(p: float) -> float:
        return sum(s.invert(p) for s in concave)

    # At p >= max w_i every e_i* is 0, so total(p) = 0 <= B: bracket above there.
    hi = max(s.weight for s in concave)
    lo = 1e-15
    # Grow hi until total(hi) <= budget (it is 0 at max w_i, so this holds).
    while total(hi) > remaining:
        hi *= 2.0
        if hi > 1e18:  # pragma: no cover - unreachable for finite weights
            break
    # total is strictly decreasing in p on the region where it is positive.
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        t = total(mid)
        if abs(t - remaining) <= tol * max(1.0, remaining):
            lo = hi = mid
            break
        if t > remaining:
            lo = mid
        else:
            hi = mid
    p = 0.5 * (lo + hi)
    alloc.shadow_price = p

    for spec in concave:
        e = spec.invert(p)
        alloc.effort[spec.step_var] = e
        if e > 0.0:
            alloc.support.append(spec.step_var)
    return alloc


def kkt_residuals(specs: Sequence[YieldSpec], alloc: Allocation
                  ) -> Dict[str, Any]:
    """The quantities (V12) checks against thm:allocation.

    On the support all marginal yields must agree with p*; off the support
    gamma_i'(0) <= p* must hold; and the budget must bind.
    """
    p = alloc.shadow_price
    on_support, off_support = [], []
    for spec in specs:
        if spec.all_or_nothing:
            continue
        e = alloc.of(spec.step_var)
        if e > 0.0:
            on_support.append({"step": spec.step_var,
                               "marginal": spec.dgamma(e),
                               "residual": abs(spec.dgamma(e) - p)})
        else:
            off_support.append({"step": spec.step_var,
                                "marginal_at_zero": spec.dgamma(0.0),
                                "satisfies": spec.dgamma(0.0) <= p + 1e-9})
    spent = sum(alloc.effort.values())
    return {
        "shadow_price": p,
        "on_support": on_support,
        "off_support": off_support,
        "max_residual": max((d["residual"] for d in on_support), default=0.0),
        "all_off_support_satisfy": all(d["satisfies"] for d in off_support),
        "spent": spent,
        "budget": alloc.budget,
        "budget_binds": abs(spent - alloc.budget) <= 1e-6 * max(1.0, alloc.budget),
    }
