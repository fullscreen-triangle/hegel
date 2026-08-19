"""Stage 5 of the pipeline: Execute. Rules (R1)--(R6) of def:verdicts.

The rules are applied IN ORDER, which is what makes verdicts attributive: a step
that is both starved and over-budget reports starvation, because (R1) precedes
(R3) and the earlier obstruction is the one that actually stopped it.

  (R1) some y in beta has a non-answer verdict, or an answer whose retention
       fell below the step's declared expectation             -> starved
  (R2) Req(rho) not subseteq Capset(Src)                      -> surface
  (R3) remaining budget below cost_Src at input cardinality   -> refused
  (R4) the request does not complete within b                 -> timeout
  (R5) the extracted result set is empty                      -> empty
  (R6) otherwise                                              -> answer

Per prin:verdict a payload accompanies only `answer`. An implementation
returning a partial payload alongside a failure verdict would reintroduce
exactly the ambiguity cor:onebit identifies, so every non-answer verdict here
carries payload None and the successors see the absence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .adapters import (MapAdapter, Refusal, Registry, Timeout,
                       required_features)
from .allocate import Allocation, YieldSpec, solve
from .check import check, refusal_document
from .model import ResultSet, Verdict, blocker_of
from .parser import Plan, Step


@dataclass
class StepResult:
    """One entry of the emitted JSON, in the shape fixed by lst:json."""

    step: str
    source: str
    verdict: Verdict
    diagnosis: Optional[Dict[str, Any]] = None
    retention: Optional[float] = None
    amplification: Optional[float] = None
    expected: Optional[float] = None
    allocated: float = 0.0
    spent: float = 0.0
    shadow_price: float = 0.0
    payload: Optional[ResultSet] = None
    snapshot: Optional[str] = None
    lowered_form: Optional[str] = None
    stages: Optional[List[Dict[str, Any]]] = None

    def to_json(self, include_payload: bool = True) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "step": self.step,
            "source": self.source,
            "verdict": self.verdict.value,
        }
        # def:blocker is partial: the field is ABSENT, not null, exactly when
        # the verdict is `answer` or `empty`.
        blk = blocker_of(self.verdict)
        if blk is not None:
            out["blocker"] = blk.value
        out["diagnosis"] = self.diagnosis
        out["retention"] = self.retention
        out["amplification"] = self.amplification
        out["budget"] = {
            "allocated": self.allocated,
            "spent": self.spent,
            "shadow_price": self.shadow_price,
        }
        # prin:verdict: a payload accompanies only `answer`.
        if (self.verdict is Verdict.ANSWER and include_payload
                and self.payload is not None):
            out["payload"] = self.payload.to_json()
        else:
            out["payload"] = None
        prov: Dict[str, Any] = {
            "snapshot": self.snapshot,
            "lowered_form": "canonical" if self.lowered_form else None,
        }
        if self.stages:
            prov["stages"] = self.stages
        if self.lowered_form:
            prov["concrete"] = self.lowered_form
        out["provenance"] = prov
        return out


@dataclass
class Execution:
    plan_name: str
    steps: List[StepResult] = field(default_factory=list)
    allocation: Optional[Allocation] = None
    check_report: Optional[Any] = None
    emitted: Dict[str, Any] = field(default_factory=dict)
    requests_issued: int = 0
    halted_early: bool = False

    def by_var(self, var: str) -> Optional[StepResult]:
        for s in self.steps:
            if s.step == var:
                return s
        return None

    def verdicts(self) -> Dict[str, str]:
        return {s.step: s.verdict.value for s in self.steps}

    def blame_chain(self, var: str) -> List[str]:
        """Follow the diagnosis chain of prop:blame.

        Terminates at a non-starved step within m hops, because def:plan
        requires every beta variable to be bound by an EARLIER step, so the
        chain is strictly decreasing in sequence position and cannot cycle.
        """
        chain, seen = [var], {var}
        cur = var
        while True:
            r = self.by_var(cur)
            if r is None or r.verdict is not Verdict.STARVED:
                return chain
            nxt = (r.diagnosis or {}).get("named_predecessor")
            if nxt is None or nxt in seen:
                return chain
            chain.append(nxt)
            seen.add(nxt)
            cur = nxt

    def to_json(self, include_payload: bool = True) -> Dict[str, Any]:
        return {
            "plan": self.plan_name,
            "outcome": "executed",
            "check": (self.check_report.to_json()
                      if hasattr(self.check_report, "to_json") else None),
            "allocation": self.allocation.to_json() if self.allocation else None,
            "requests_issued": self.requests_issued,
            "halted_early": self.halted_early,
            "steps": [s.to_json(include_payload) for s in self.steps],
            "emitted": self.emitted,
        }


# ---------------------------------------------------------------------------
# Yield specification
# ---------------------------------------------------------------------------


def yield_specs(plan: Plan, registry: Registry,
                weights: Optional[Dict[str, float]] = None) -> List[YieldSpec]:
    """Attach a yield to each step.

    A step against a source declaring `lookup` but not `pattern` is
    all-or-nothing (rem:concavity-fails): one request retrieves the record and
    further requests retrieve nothing. Such steps are charged first rather than
    optimised, so the shadow price governs only a subset of the plan.

    The weights are configuration. sec:limits records that we have estimated a
    yield function for no real source.
    """
    weights = weights or {}
    specs: List[YieldSpec] = []
    for s in plan.steps:
        w = weights.get(s.var, 1.0)
        if s.kind != "from":
            # map and set operations consume no requests; they are charged a
            # nominal fixed unit so the allocator sees them.
            specs.append(YieldSpec(s.var, w, all_or_nothing=True, fixed_cost=1.0))
            continue
        cap = registry.get(s.source).capabilities
        aon = ("lookup" in cap) and ("pattern" not in cap)
        specs.append(YieldSpec(s.var, w, all_or_nothing=aon, fixed_cost=1.0))
    return specs


# ---------------------------------------------------------------------------
# The executor
# ---------------------------------------------------------------------------


class Executor:
    def __init__(self, registry: Registry, maps: Optional[MapAdapter] = None,
                 replan: bool = True,
                 weights: Optional[Dict[str, float]] = None) -> None:
        self.registry = registry
        self.maps = maps or MapAdapter(name="maps", namespace="map",
                                       capabilities=frozenset())
        # rem:replanning: the prototype re-solves thm:allocation after each step
        # with the remaining budget and the realised cardinalities. sec:limits
        # records that we have not bounded its regret against the clairvoyant
        # allocation, which is the natural comparison we do not make.
        self.replan = replan
        self.weights = weights or {}

    # -- driver ------------------------------------------------------------

    def run(self, plan: Plan, budget: Optional[float] = None) -> Execution:
        registry = self.registry
        registry.reset_counters()
        total_budget = plan.budget if budget is None else budget

        ex = Execution(plan_name=plan.name)

        # --- Check: decided entirely by declarations, before any contact ---
        report = check(plan, registry)
        ex.check_report = report
        if not report.well_capability:
            # cor:refuse-before-contact. Halt here; requests_issued stays 0,
            # which is the quantity (V1) asserts.
            for step in plan.steps:
                fail = next((f for f in report.failures if f.step == step.var),
                            None)
                if fail is None:
                    continue
                ex.steps.append(StepResult(
                    step=step.var, source=step.source or "-",
                    verdict=Verdict.SURFACE,
                    diagnosis={
                        "missing": fail.missing,
                        "reason": "required capabilities not declared by the "
                                  "source; no request was issued",
                    },
                ))
            ex.requests_issued = registry.total_requests()
            ex.halted_early = True
            ex.emitted = {"refusal": refusal_document(plan, report)}
            return ex

        specs = yield_specs(plan, registry, self.weights)
        alloc = solve(specs, total_budget)
        ex.allocation = alloc

        values: Dict[str, ResultSet] = {}
        remaining = total_budget
        done: List[str] = []

        for step in plan.steps:
            if self.replan and done:
                sub = solve([s for s in specs if s.step_var not in done],
                            remaining)
                allocated, price = sub.of(step.var), sub.shadow_price
            else:
                allocated, price = alloc.of(step.var), alloc.shadow_price

            res = self._run_step(step, values, ex, allocated, price, remaining)
            ex.steps.append(res)
            remaining = max(0.0, remaining - res.spent)
            done.append(step.var)

            if res.verdict is Verdict.ANSWER and res.payload is not None:
                values[step.var] = res.payload
            else:
                # prin:verdict: no payload for a non-answer verdict. Successors
                # see the absence and (R1) fires on them.
                values[step.var] = ResultSet.empty("-")

            if step.on_unresolved == "fail" and res.verdict is not Verdict.ANSWER:
                ex.halted_early = True
                break

        ex.requests_issued = registry.total_requests()
        ex.emitted = self._emit(plan, ex, values)
        return ex

    # -- the rules, in order ----------------------------------------------

    def _run_step(self, step: Step, values: Dict[str, ResultSet], ex: Execution,
                  allocated: float, price: float,
                  remaining: float) -> StepResult:
        if step.kind == "from":
            source = step.source or "-"
        elif step.kind == "map":
            source = "map:" + "->".join(step.maps)
        else:
            source = step.kind
        base = StepResult(step=step.var, source=source, verdict=Verdict.ANSWER,
                          allocated=allocated, shadow_price=price)

        # (R1) a predecessor failed, or answered below its declared expectation.
        # Checked FIRST, so a step that is both starved and over-budget reports
        # starvation: the earlier obstruction is the one that stopped it.
        for y in step.beta:
            prev = ex.by_var(y)
            if prev is None:
                continue
            if prev.verdict is not Verdict.ANSWER:
                base.verdict = Verdict.STARVED
                base.diagnosis = {
                    "named_predecessor": y,
                    "reason": "predecessor " + repr(y) + " returned "
                              + prev.verdict.value,
                }
                return base
            if (prev.retention is not None and prev.expected is not None
                    and prev.retention < prev.expected):
                base.verdict = Verdict.STARVED
                base.diagnosis = {
                    "named_predecessor": y,
                    "reason": "predecessor retention {:.2f} below declared "
                              "expectation {}".format(prev.retention,
                                                      prev.expected),
                }
                return base

        if step.kind == "map":
            return self._run_map(step, values, base)
        if step.kind in ("union", "intersect", "join", "filter"):
            return self._run_setop(step, values, base)
        return self._run_from(step, values, base, allocated, remaining)

    def _run_from(self, step: Step, values: Dict[str, ResultSet],
                  base: StepResult, allocated: float,
                  remaining: float) -> StepResult:
        adapter = self.registry.get(step.source)
        base.snapshot = adapter.snapshot
        inputs = {y: values[y] for y in step.beta}

        # (R2) capability containment. thm:static already decided this without
        # contact, so reaching it here means the checker and adapter disagree.
        req = required_features(step.request)
        if not adapter.supports(req):
            base.verdict = Verdict.SURFACE
            base.diagnosis = {
                "missing": sorted(adapter.missing(req)),
                "required": sorted(req),
                "reason": "required capabilities not declared by the source",
            }
            return base

        # (R3) remaining PLAN budget below cost_Src at the realised input
        # cardinality. prop:necessary-not-sufficient lives here: the cost is a
        # function of an input no static quantity bounds.
        cost = adapter.cost(step.request, inputs)
        if remaining < cost:
            base.verdict = Verdict.REFUSED
            base.diagnosis = {
                "reason": "remaining budget {:g} below cost {:g} at input "
                          "cardinality".format(remaining, cost),
                "remaining": remaining,
                "required": cost,
                "shortfall": cost - remaining,
            }
            return base

        # (R4) the step's own annotation b: does the request complete within it?
        effort = min(step.budget, allocated) if allocated > 0 else step.budget
        try:
            payload = adapter.evaluate(step.request, inputs, effort)
        except Timeout:
            base.verdict = Verdict.TIMEOUT
            base.diagnosis = {
                "reason": "cost {:g} exceeds the effort {:g} allocated to this "
                          "step".format(cost, effort),
                "step_budget": effort,
                "elapsed_cost": cost,
            }
            return base
        except Refusal as e:
            base.verdict = Verdict.SURFACE
            base.diagnosis = {"reason": str(e)}
            return base

        base.spent = cost
        base.lowered_form = adapter.last_lowered

        # (R5) empty denotation over this dataset -- a real answer, which is
        # why def:blocker assigns it no blocker.
        if len(payload) == 0:
            base.verdict = Verdict.EMPTY
            base.diagnosis = {"reason": "denotation is empty over this dataset"}
            return base

        # (R6)
        base.verdict = Verdict.ANSWER
        base.payload = payload
        return base

    def _run_map(self, step: Step, values: Dict[str, ResultSet],
                 base: StepResult) -> StepResult:
        src = values[step.operands[0]]
        out, stages = self.maps.apply_chain(step.maps, src)
        base.stages = stages
        base.spent = 1.0
        base.snapshot = self.maps.snapshot

        # Retention and amplification are recorded SEPARATELY, because by
        # prop:cardinality-uninformative their product -- all the output
        # cardinality reveals -- determines neither.
        base.retention = self.maps.surviving_fraction(step.maps, src)
        base.amplification = stages[-1]["amplification"] if stages else None
        base.expected = step.expect_partial

        # def:retention-check: below the declared expectation the step reports
        # starved to its successors, naming mu, epsilon and the observed r.
        if (step.expect_partial is not None
                and base.retention < step.expect_partial):
            base.verdict = Verdict.STARVED
            # The shortfall is in mu, not in the predecessor: the input
            # arrived intact and the translation lost it. Naming the
            # predecessor here would blame a step that answered correctly, so
            # the chain of prop:blame terminates AT this step.
            base.diagnosis = {
                "named_predecessor": None,
                "lossy_translation": list(step.maps),
                "input_from": step.operands[0],
                "reason": "retention {:.2f} below declared expectation "
                          "{}".format(base.retention, step.expect_partial),
                "expectation": step.expect_partial,
                "observed": base.retention,
            }
            return base

        if len(out) == 0:
            base.verdict = Verdict.EMPTY
            base.diagnosis = {"reason": "translation image is empty"}
            return base
        base.verdict = Verdict.ANSWER
        base.payload = out
        return base

    def _run_setop(self, step: Step, values: Dict[str, ResultSet],
                   base: StepResult) -> StepResult:
        operands = [values[y] for y in step.operands]
        base.spent = 0.0
        ns = operands[0].namespace if operands else "-"

        if step.kind == "union":
            pairs = [(i, a.rows[i]) for a in operands for i in a.rows]
            out = ResultSet.of(ns, pairs)
        elif step.kind == "intersect":
            keep = set(operands[0].identifiers())
            for a in operands[1:]:
                keep &= set(a.identifiers())
            pairs = [(i, a.rows[i]) for a in operands for i in a.rows
                     if i in keep]
            out = ResultSet.of(ns, pairs)
        elif step.kind == "join":
            left, right = operands
            attr = step.join_on
            index: Dict[Any, List[Any]] = {}
            for j, row in right.rows.items():
                index.setdefault(row.get(attr), []).append((j, row))
            pairs = []
            for i, row in left.rows.items():
                for _j, other in index.get(row.get(attr), []):
                    merged = dict(row)
                    merged.update({"_joined_" + k: v for k, v in other.items()})
                    pairs.append((i, merged))
            out = ResultSet.of(ns, pairs)
        else:  # filter
            attr, op, val = step.where
            ops = {"==": lambda x, y: x == y, "!=": lambda x, y: x != y,
                   "<": lambda x, y: x < y, ">": lambda x, y: x > y,
                   "<=": lambda x, y: x <= y, ">=": lambda x, y: x >= y}
            test = ops[op]
            pairs = []
            for i, row in operands[0].rows.items():
                # `_id` names the identifier itself. Every row in the common
                # result model has one, and attributes do not survive a
                # non-injective map intact -- when two sources collide on one
                # identifier, ResultSet.of merges their attribute maps and the
                # later write wins. A filter that must pick out a specific
                # element therefore has to name it, not a property it carries.
                if attr == "_id":
                    try:
                        if test(i, val):
                            pairs.append((i, row))
                    except TypeError:
                        pass
                    continue
                if attr not in row:
                    continue
                try:
                    if test(row[attr], val):
                        pairs.append((i, row))
                except TypeError:
                    continue
            out = ResultSet.of(ns, pairs)

        if len(out) == 0:
            base.verdict = Verdict.EMPTY
            base.diagnosis = {"reason": step.kind + " produced an empty set"}
            return base
        base.verdict = Verdict.ANSWER
        base.payload = out
        return base

    # -- emit --------------------------------------------------------------

    def _emit(self, plan: Plan, ex: Execution,
              values: Dict[str, ResultSet]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for e in plan.emits:
            if e.divergence:
                a, b = e.divergence
                sa = values.get(a, ResultSet.empty("-")).identifiers()
                sb = values.get(b, ResultSet.empty("-")).identifiers()
                # thm:route-extent(b): the symmetric difference is a LOWER
                # BOUND on correspondences at least one route fails to resolve.
                # It is a coverage statement, not an error count, and must not
                # be reported as one.
                key = e.alias or ("divergence_" + a + "_" + b)
                out[key] = {
                    "left": a,
                    "right": b,
                    "left_only": sorted(sa - sb),
                    "right_only": sorted(sb - sa),
                    "symmetric_difference": len(sa ^ sb),
                    "union_size": len(sa | sb),
                    "interpretation": "lower bound on correspondences at least "
                                      "one route fails to resolve; neither "
                                      "route contradicts the other",
                }
            else:
                r = ex.by_var(e.target)
                payload = values.get(e.target)
                answered = r is not None and r.verdict is Verdict.ANSWER
                out[e.target] = {
                    "verdict": r.verdict.value if r else None,
                    "payload": (payload.to_json()
                                if answered and payload else None),
                    "provenance": e.provenance,
                }
        return out
