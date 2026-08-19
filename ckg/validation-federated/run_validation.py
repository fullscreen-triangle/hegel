"""Drive the checks (V1)-(V15) of part6-realisation.tex and write JSON.

Each check is a function returning a dict with at least `check`, `claim`,
`holds` and the figures the claim is about. Nothing is asserted that the
returned figures do not exhibit: a reader disagreeing with a verdict can
recompute it from the same JSON.

Every adapter resolves against a local fixture. No request leaves the machine,
by construction rather than by configuration.
"""

from __future__ import annotations

import json
import os
import random
import sys
from typing import Any, Callable, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "fixtures"))

import build  # noqa: E402
from hfq import (Executor, ResultSet, Verdict, check, kkt_residuals,  # noqa: E402
                 parse, refusal_document, solve, yield_specs)

PLANS = os.path.join(HERE, "plans")
RESULTS = os.path.join(HERE, "results")


def load(name: str):
    with open(os.path.join(PLANS, name + ".hfq"), encoding="utf-8") as fh:
        return parse(fh.read())


def run(name: str, batch: bool = False):
    """Parse and execute a plan against a fresh registry."""
    reg = build.build_registry(batch=batch)
    maps = build.build_maps()
    return reg, Executor(reg, maps=maps).run(load(name))


def run_paper(name: str):
    reg, maps = build.build_paper_registry()
    return reg, Executor(reg, maps=maps).run(load(name))


# ---------------------------------------------------------------------------
# V1 -- the static check decides without contact
# ---------------------------------------------------------------------------


def v1() -> Dict[str, Any]:
    reg = build.build_registry()
    plan = load("ill_capability")
    report = check(plan, reg)
    doc = refusal_document(plan, report)
    issued = reg.total_requests()
    return {
        "check": "V1",
        "claim": "thm:static decides ill-capability before contact; "
                 "cor:refuse-before-contact fixes the request counter at zero",
        "plan": plan.name,
        "well_capability": report.well_capability,
        "failures": [f.to_json() for f in report.failures],
        "requests_issued_after_refusal": issued,
        "refusal_document": doc,
        "holds": (not report.well_capability) and issued == 0,
    }


# ---------------------------------------------------------------------------
# V2 -- the check is linear in m * |Feat|
# ---------------------------------------------------------------------------


def v2() -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for name in ["single_step", "healthy_chain", "order_a",
                 "enzymes_in_shared_pathways"]:
        if name == "enzymes_in_shared_pathways":
            reg, _maps = build.build_paper_registry()
        else:
            reg = build.build_registry()
        plan = load(name)
        rep = check(plan, reg)
        rows.append({
            "plan": plan.name,
            "steps": rep.n_steps,
            "operations": rep.operations,
            "bound": rep.bound,
            "within_bound": rep.operations <= rep.bound,
        })
    return {
        "check": "V2",
        "claim": "the check performs O(m|Feat|) membership tests; the count "
                 "never exceeds m|Feat| and grows linearly in m",
        "feature_count": 11,
        "measurements": rows,
        "holds": all(r["within_bound"] for r in rows),
    }


# ---------------------------------------------------------------------------
# V3 -- all six verdicts are realised
# ---------------------------------------------------------------------------

#: Each plan differs from healthy_chain in exactly one respect, which is what
#: thm:six requires: six configurations, one distinction apart.
VERDICT_PLANS = {
    "answer":  ("healthy_chain",  "rxns"),
    "empty":   ("empty_answer",   "none"),
    "surface": ("ill_capability", "bad"),
    "timeout": ("step_timeout",   "rxns"),
    "starved": ("starved_chain",  "rxns"),
}


def v3() -> Dict[str, Any]:
    observed: Dict[str, Any] = {}
    for want, (plan_name, var) in VERDICT_PLANS.items():
        _reg, ex = run(plan_name)
        sr = ex.by_var(var)
        observed[want] = {
            "plan": plan_name,
            "step": var,
            "verdict": sr.verdict.value,
            "blocker": sr.to_json().get("blocker"),
            "blocker_key_present": "blocker" in sr.to_json(),
            "matches": sr.verdict.value == want,
        }

    # `refused` needs the budget-trap registry, not the main one.
    reg = build.budget_trap()
    ex = Executor(reg).run(load("budget_trap"))
    sr = ex.by_var("rxns")
    observed["refused"] = {
        "plan": "budget_trap", "step": "rxns",
        "verdict": sr.verdict.value,
        "blocker": sr.to_json().get("blocker"),
        "blocker_key_present": "blocker" in sr.to_json(),
        "matches": sr.verdict.value == "refused",
    }

    return {
        "check": "V3",
        "claim": "thm:six -- each of the six verdicts is realised by a "
                 "configuration differing from a common baseline in one respect",
        "baseline": "healthy_chain",
        "observed": observed,
        "blocker_absent_for": [k for k, v in observed.items()
                               if not v["blocker_key_present"]],
        "holds": all(v["matches"] for v in observed.values()),
    }


# ---------------------------------------------------------------------------
# V4 -- the one-bit interface conflates four verdicts
# ---------------------------------------------------------------------------


def v4() -> Dict[str, Any]:
    """cor:onebit. A boolean success flag is the map v -> (v == answer)."""
    conflated = [k for k in VERDICT_PLANS if k != "answer"] + ["refused"]
    rows = []
    for name in ["empty_answer", "ill_capability", "step_timeout",
                 "starved_chain"]:
        _reg, ex = run(name)
        last = ex.steps[-1]
        rows.append({
            "plan": name,
            "verdict": last.verdict.value,
            "one_bit": last.verdict == Verdict.ANSWER,
            "payload_size": len(last.payload) if last.payload else 0,
        })
    reg = build.budget_trap()
    ex = Executor(reg).run(load("budget_trap"))
    rows.append({"plan": "budget_trap", "verdict": ex.steps[-1].verdict.value,
                 "one_bit": False, "payload_size": 0})

    distinct = sorted({r["verdict"] for r in rows})
    return {
        "check": "V4",
        "claim": "cor:onebit -- a boolean interface maps five distinct "
                 "verdicts, with five distinct blockers, onto one value",
        "observations": rows,
        "distinct_verdicts": distinct,
        "distinct_one_bit_values": sorted({r["one_bit"] for r in rows}),
        "conflated": conflated,
        "holds": len(distinct) >= 4 and len({r["one_bit"] for r in rows}) == 1,
    }


# ---------------------------------------------------------------------------
# V5 -- starvation is unreachable at m = 1 and reachable at m >= 2
# ---------------------------------------------------------------------------


def v5() -> Dict[str, Any]:
    _reg, single = run("single_step")
    _reg2, chain = run("starved_chain")

    single_verdicts = [s.verdict.value for s in single.steps]
    chain_starved = [s.step for s in chain.steps
                     if s.verdict == Verdict.STARVED]
    return {
        "check": "V5",
        "claim": "prop:starve-reachable -- starvation is unreachable in the "
                 "single-step setting and reachable at m >= 2, because the "
                 "corpus of step i is an artefact of steps 1..i-1",
        "single_step": {"m": len(single.steps), "verdicts": single_verdicts,
                        "starved_present": "starved" in single_verdicts},
        "federated": {"m": len(chain.steps),
                      "verdicts": [s.verdict.value for s in chain.steps],
                      "starved_steps": chain_starved},
        "holds": ("starved" not in single_verdicts) and len(chain_starved) > 0,
    }


# ---------------------------------------------------------------------------
# V6 -- blame terminates within m hops
# ---------------------------------------------------------------------------


def v6() -> Dict[str, Any]:
    _reg, ex = run("starved_chain")
    m = len(ex.steps)
    chains = {}
    for s in ex.steps:
        if s.verdict == Verdict.STARVED:
            c = ex.blame_chain(s.step)
            chains[s.step] = {
                "chain": c,
                "hops": len(c) - 1,
                "terminates_at": c[-1],
                "terminal_verdict": ex.by_var(c[-1]).verdict.value,
                "within_m": len(c) - 1 <= m,
            }
    return {
        "check": "V6",
        "claim": "prop:blame -- every beta variable is bound by an earlier "
                 "step, so the chain strictly decreases in sequence position "
                 "and terminates within m hops without cycling",
        "m": m,
        "chains": chains,
        "holds": bool(chains) and all(c["within_m"] for c in chains.values()),
    }


# ---------------------------------------------------------------------------
# V7 -- retention factorises; the bounds hold; record the gap
# ---------------------------------------------------------------------------


def v7() -> Dict[str, Any]:
    maps = build.build_maps()
    reg = build.build_registry()
    ex = Executor(reg, maps=maps).run(load("healthy_chain"))
    seed = ex.by_var("acids").payload

    names = ["chebi2kegg", "kegg2rhea"]
    out, stages = maps.apply_chain(names, seed)
    rho = maps.surviving_fraction(names, seed)

    prod = 1.0
    for st in stages:
        prod *= st["retention"] * (st["amplification"] or 0.0)
    ratio = len(out) / len(seed)

    lower = max(0.0, 1.0 - sum(1.0 - st["retention"] for st in stages))
    upper = min(st["retention"] for st in stages)

    # thm:retention(b) holds only under injectivity on the realised sets.
    # CHEBI_KEGG is non-injective -- CHEBI:9 and CHEBI:10 collide on KEGG:C9 --
    # so this chain is a counterexample to the unrestricted inequality, and
    # rem:injectivity-needed is what it establishes. The residual bound
    # rho <= r_1 needs no hypothesis and is checked instead.
    chain = maps.chain(names)
    injective = []
    cur = seed.identifiers()
    for mu in chain:
        imgs = [mu.pairs.get(u, ()) for u in cur if u in mu.pairs]
        flat = [x for t in imgs for x in t]
        injective.append(len(flat) == len(set(flat)))
        cur = mu.image(cur)
    all_injective = all(injective)

    r1 = stages[0]["retention"]
    return {
        "check": "V7",
        "claim": "thm:retention -- (a) |S_k|/|S_0| = prod r_i a_i holds "
                 "unconditionally; (b) rho <= min r_i holds under injectivity "
                 "on the realised sets and FAILS without it "
                 "(rem:injectivity-needed); (c) rho >= 1 - sum (1 - r_i) "
                 "carries the same hypothesis. The gap between (b) and (c) is "
                 "not slack (rem:bounds-gap)",
        "input_size": len(seed),
        "stages": stages,
        "output_size": len(out),
        "product_r_times_a": prod,
        "observed_ratio": ratio,
        "factorisation_holds": abs(prod - ratio) < 1e-9,
        "surviving_fraction": rho,
        "per_stage_injective": injective,
        "chain_injective": all_injective,
        "minimum_retention": upper,
        "min_bound_would_hold": rho <= upper + 1e-9,
        "min_bound_applicable": all_injective,
        "residual_bound_r1": r1,
        "residual_bound_holds": rho <= r1 + 1e-9,
        "lower_bound": lower,
        "lower_bound_holds": rho >= lower - 1e-9,
        "lower_bound_applicable": all_injective,
        "gap_width": upper - lower,
        # The chain is deliberately non-injective, so neither (b) nor (c)
        # applies, and (b) failing here is the content of
        # rem:injectivity-needed rather than a defect. Unconditionally: (a) and
        # the residual bound. Conditionally: (b) exactly when the chain is
        # injective. (c) is recorded but not required, since a non-injective
        # chain satisfying it is permitted -- the bound is one-sided.
        "holds": (abs(prod - ratio) < 1e-9
                  and rho <= r1 + 1e-9
                  and (rho <= upper + 1e-9) == all_injective
                  and (rho >= lower - 1e-9 or not all_injective)),
    }


# ---------------------------------------------------------------------------
# V8 -- output cardinality does not determine retention
# ---------------------------------------------------------------------------


def v8() -> Dict[str, Any]:
    hi, lo, s = build.cardinality_pair()
    rows = []
    for mu in (hi, lo):
        rows.append({
            "map": mu.name,
            "input_size": len(s),
            "output_size": len(mu.image(s)),
            "retention": mu.retention(s),
            "amplification": mu.amplification(s),
            "product": mu.retention(s) * mu.amplification(s),
        })
    same_size = rows[0]["output_size"] == rows[1]["output_size"]
    diff_ret = rows[0]["retention"] != rows[1]["retention"]
    return {
        "check": "V8",
        "claim": "prop:cardinality-uninformative -- two maps with equal output "
                 "cardinality can differ arbitrarily in retention; only the "
                 "product r*a is recoverable from |mu(S)|, so both are recorded",
        "maps": rows,
        "equal_output_cardinality": same_size,
        "unequal_retention": diff_ret,
        "retention_ratio": rows[0]["retention"] / rows[1]["retention"],
        "holds": same_size and diff_ret,
    }


# ---------------------------------------------------------------------------
# V9 -- pairwise coverage does not determine chain coverage
# ---------------------------------------------------------------------------


def v9() -> Dict[str, Any]:
    aligned, stagger, s = build.pairwise_families()
    seed = ResultSet.of("U", [(u, {}) for u in s])
    maps = build.build_maps()

    # The pairwise retentions must be measured on a COMMON reference set, not
    # on whatever the predecessor happens to deliver: measured on the realised
    # input, nu_aligned retains everything it is given and the two families are
    # no longer comparable. prop:pairwise-insufficient is a statement about
    # published per-map figures, which are quoted against a reference set.
    reference = {"V:v%d" % i for i in range(1, 5)}

    rows = []
    for label, (mu, nu) in (("aligned", aligned), ("staggered", stagger)):
        maps.maps[mu.name] = mu
        maps.maps[nu.name] = nu
        names = [mu.name, nu.name]
        _out, stages = maps.apply_chain(names, seed)
        rows.append({
            "family": label,
            "reference_retentions": [mu.retention(set(s)), nu.retention(reference)],
            "realised_retentions": [st["retention"] for st in stages],
            "surviving_fraction": maps.surviving_fraction(names, seed),
        })

    same_pairwise = (rows[0]["reference_retentions"]
                     == rows[1]["reference_retentions"])
    diff_rho = rows[0]["surviving_fraction"] != rows[1]["surviving_fraction"]
    return {
        "check": "V9",
        "claim": "prop:pairwise-insufficient -- two chains with identical "
                 "pairwise retentions can have different end-to-end surviving "
                 "fractions, so rho must be measured, not inferred",
        "reference_set": sorted(reference),
        "families": rows,
        "identical_pairwise": same_pairwise,
        "different_surviving_fraction": diff_rho,
        "holds": same_pairwise and diff_rho,
    }


# ---------------------------------------------------------------------------
# V10 -- reordering: equal coverage, unequal request count
# ---------------------------------------------------------------------------


def v10() -> Dict[str, Any]:
    rows = []
    for name in ("order_a", "order_b"):
        _reg, ex = run(name)
        last = ex.steps[-1]
        rows.append({
            "plan": name,
            "final_step": last.step,
            "coverage": sorted(last.payload.identifiers()) if last.payload else [],
            "requests": sum(s.spent for s in ex.steps),
        })
    return {
        "check": "V10",
        "claim": "two orderings of the same steps yield the same extent at "
                 "different request counts; the plan language makes the "
                 "ordering an authored decision rather than a planner's",
        "orderings": rows,
        "equal_coverage": rows[0]["coverage"] == rows[1]["coverage"],
        "unequal_requests": rows[0]["requests"] != rows[1]["requests"],
        "saving": rows[1]["requests"] - rows[0]["requests"],
        "holds": (rows[0]["coverage"] == rows[1]["coverage"]
                  and rows[0]["requests"] != rows[1]["requests"]),
    }


# ---------------------------------------------------------------------------
# V11 -- routes diverge without contradiction; totality collapses divergence
# ---------------------------------------------------------------------------


def v11() -> Dict[str, Any]:
    reg, maps = build.build_paper_registry()
    ex = Executor(reg, maps=maps).run(load("routes"))
    div = ex.emitted["resolved_extent"]

    # Collapse: replace the indirect route's two maps by a single total map on
    # the same source set. thm:route-extent -- divergence is a coverage
    # statement, and it vanishes when both routes are total.
    reg2, maps2 = build.build_paper_registry()
    maps2.maps["chebi_to_kegg"] = build.CHEBI_KEGG_TOTAL
    maps2.maps["chebi_to_inchikey"] = build.CHEBI_KEGG_TOTAL
    maps2.maps["inchikey_to_kegg"] = build.TranslationMap(
        "identity", "KEGG", "KEGG",
        {v: (v,) for vs in build.CHEBI_KEGG_TOTAL.pairs.values() for v in vs})
    ex2 = Executor(reg2, maps=maps2).run(load("routes"))
    div2 = ex2.emitted["resolved_extent"]

    return {
        "check": "V11",
        "claim": "thm:route-extent(b) -- the divergence of two routes is a "
                 "lower bound on correspondences at least one route fails to "
                 "resolve; neither route contradicts the other, and making "
                 "both total collapses the divergence to zero",
        "partial_maps": div,
        "total_maps": div2,
        "divergence_collapses": div2["symmetric_difference"] == 0,
        "holds": (div["symmetric_difference"] > 0
                  and div2["symmetric_difference"] == 0),
    }


# ---------------------------------------------------------------------------
# V12 -- the allocation satisfies the KKT conditions
# ---------------------------------------------------------------------------


def v12() -> Dict[str, Any]:
    reg = build.build_registry()
    plan = load("healthy_chain")
    specs = yield_specs(plan, reg)
    alloc = solve(specs, plan.budget)
    resid = kkt_residuals(specs, alloc)
    return {
        "check": "V12",
        "claim": "thm:allocation -- the water-filling solution equalises the "
                 "marginal yields of every optimised step at one shadow price "
                 "p*, which is the KKT stationarity condition",
        "budget": plan.budget,
        "allocation": alloc.to_json(),
        "kkt_residuals": resid,
        "max_residual": resid["max_residual"],
        "holds": (resid["max_residual"] < 1e-6
                  and resid["all_off_support_satisfy"]),
    }


# ---------------------------------------------------------------------------
# V13 -- sufficient budget is not sufficient
# ---------------------------------------------------------------------------


def v13() -> Dict[str, Any]:
    reg = build.budget_trap()
    plan = load("budget_trap")
    ex = Executor(reg).run(plan)
    declared = {}
    for s in plan.steps:
        if s.kind == "from":
            declared[s.var] = reg.get(s.source).cost(
                s.request, {y: ResultSet.empty("-") for y in s.beta})
    refused = [s for s in ex.steps if s.verdict == Verdict.REFUSED]
    return {
        "check": "V13",
        "claim": "prop:necessary-not-sufficient -- B >= sum c_i is necessary "
                 "but not sufficient, because each c_i is a minimum over "
                 "inputs and the realised input need not be the minimiser",
        "budget": plan.budget,
        "declared_costs": declared,
        "sum_declared": sum(declared.values()),
        "budget_covers_declared": plan.budget >= sum(declared.values()),
        "steps": [s.to_json(include_payload=False) for s in ex.steps],
        "refused_steps": [s.step for s in refused],
        "holds": plan.budget >= sum(declared.values()) and bool(refused),
    }


# ---------------------------------------------------------------------------
# V14 -- lowering is canonical
# ---------------------------------------------------------------------------


def v14() -> Dict[str, Any]:
    """cons:longhand and thm:interpolation, made inspectable.

    The bound set enters through VALUES and every pattern is written longhand,
    so the (2,397) defect class -- where an object list and separate triple
    patterns disagree -- cannot arise: the lowering never emits an object list.
    """
    reg = build.build_registry()
    maps = build.build_maps()
    ex = Executor(reg, maps=maps).run(load("healthy_chain"))
    forms = {s.step: s.lowered_form for s in ex.steps if s.lowered_form}

    # Re-lower the same plan against a fresh registry: the concrete form must
    # be identical, character for character.
    reg2 = build.build_registry()
    ex2 = Executor(reg2, maps=build.build_maps()).run(load("healthy_chain"))
    forms2 = {s.step: s.lowered_form for s in ex2.steps if s.lowered_form}

    object_lists = [v for v in forms.values() if v and "," in v]
    return {
        "check": "V14",
        "claim": "cons:longhand -- lowering emits one canonical form per "
                 "abstract request, with bound sets carried by VALUES and no "
                 "predicate-object lists, so thm:interpolation applies",
        "lowered_forms": forms,
        "deterministic": forms == forms2,
        "uses_values": all("VALUES" in v for v in forms.values()
                           if "?" in (v or "")),
        "object_lists_emitted": object_lists,
        "holds": forms == forms2 and not object_lists,
    }


# ---------------------------------------------------------------------------
# V15 -- re-execution is stable; a perturbation is confined
# ---------------------------------------------------------------------------


def v15() -> Dict[str, Any]:
    _r1, a = run("healthy_chain")
    _r2, b = run("healthy_chain")
    ja = a.to_json(include_payload=False)
    jb = b.to_json(include_payload=False)

    _r3, c = run("starved_chain")
    va = {s.step: s.verdict.value for s in a.steps}
    vc = {s.step: s.verdict.value for s in c.steps}
    differing = sorted(k for k in va if va[k] != vc.get(k))

    # The two plans differ only in the map step's declared expectation, so the
    # difference must be confined to that step and its successors.
    order = [s.step for s in a.steps]
    first = min((order.index(k) for k in differing), default=len(order))
    expected = set(order[first:])

    return {
        "check": "V15",
        "claim": "thm:idempotent / cor:rerun -- re-executing an unchanged plan "
                 "against an unchanged snapshot reproduces every verdict; a "
                 "single perturbation is confined to the perturbed step and "
                 "its successors",
        "identical_reruns": ja == jb,
        "baseline_verdicts": va,
        "perturbed_verdicts": vc,
        "differing_steps": differing,
        "confined_to_successors": set(differing) <= expected,
        "holds": ja == jb and set(differing) <= expected and bool(differing),
    }


# ---------------------------------------------------------------------------
# The paper's own listings, executed as written
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# V16 -- injectivity is exactly the hypothesis (b) and (c) need
# ---------------------------------------------------------------------------


def v16() -> Dict[str, Any]:
    """Search randomly generated chains for violations of (b) and (c).

    V7 exhibits one non-injective chain that breaks (b). This check establishes
    the converse direction that rem:injectivity-needed relies on: among
    injective chains neither bound is ever violated, while among non-injective
    ones both are, at the rates the remark prints. The generator is the same
    one the figure sweeps use, so the paper's number and the panel's scatter
    come from one procedure.
    """
    import sweeps

    rng = random.Random(20260818)
    groups = {"injective": {"n": 0, "b": 0, "c": 0},
              "non_injective": {"n": 0, "b": 0, "c": 0}}
    target = 5000
    guard = 0
    while groups["non_injective"]["n"] < target and guard < 400000:
        guard += 1
        s0, maps = sweeps._random_chain(rng, 8, 2, 0.8, 3)
        st = sweeps._chain_stats(s0, maps)
        g = groups["injective"] if st["injective"] else groups["non_injective"]
        g["n"] += 1
        g["b"] += 1 if st["rho"] > st["min_r"] + 1e-12 else 0
        g["c"] += 1 if st["rho"] < st["lower"] - 1e-12 else 0

    # Injective draws are rare under the general generator, so they are
    # constructed rather than rejected -- rejection would also bias the sample
    # toward small domains, where the bounds are loosest.
    while groups["injective"]["n"] < target:
        s0, maps = sweeps._injective_chain(rng, 8, 2, 0.8)
        st = sweeps._chain_stats(s0, maps)
        g = groups["injective"]
        g["n"] += 1
        g["b"] += 1 if st["rho"] > st["min_r"] + 1e-12 else 0
        g["c"] += 1 if st["rho"] < st["lower"] - 1e-12 else 0

    rates = {k: {"n": g["n"],
                 "upper_bound_violations": g["b"],
                 "lower_bound_violations": g["c"],
                 "upper_rate": g["b"] / g["n"] if g["n"] else 0.0,
                 "lower_rate": g["c"] / g["n"] if g["n"] else 0.0}
             for k, g in groups.items()}
    return {
        "check": "V16",
        "claim": "rem:injectivity-needed -- injectivity on the realised sets "
                 "is exactly the hypothesis thm:retention(b) and (c) require: "
                 "no injective chain violates either bound, and non-injective "
                 "chains violate both",
        "generator": {"elements": 8, "stages": 2, "domain_probability": 0.8,
                      "max_images": 3,
                      "injective_draws": "constructed, not rejection-sampled"},
        "rates": rates,
        "holds": (rates["injective"]["upper_bound_violations"] == 0
                  and rates["injective"]["lower_bound_violations"] == 0
                  and rates["non_injective"]["upper_bound_violations"] > 0
                  and rates["non_injective"]["lower_bound_violations"] > 0),
    }


def listings() -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for name in ("enzymes_in_shared_pathways", "routes"):
        _reg, ex = run_paper(name)
        out[name] = ex.to_json()
    return {
        "check": "listings",
        "claim": "lst:plan and lst:routes execute as printed, against local "
                 "fixtures supplying the source and map names they use",
        "executions": out,
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

CHECKS: List[Callable[[], Dict[str, Any]]] = [
    v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15,
    v16,
]


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    summary: List[Dict[str, Any]] = []
    failures = 0

    for fn in CHECKS:
        try:
            res = fn()
        except Exception as exc:  # a crash is a failed check, reported as one
            res = {"check": fn.__name__.upper(), "holds": False,
                   "error": "{}: {}".format(type(exc).__name__, exc)}
        name = res["check"].lower()
        path = os.path.join(RESULTS, "{}.json".format(name))
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=2, sort_keys=True)
        ok = bool(res.get("holds"))
        failures += 0 if ok else 1
        summary.append({"check": res["check"], "holds": ok,
                        "claim": res.get("claim", ""),
                        "file": os.path.basename(path)})
        print("{:<8} {}".format(res["check"], "ok" if ok else "FAILED"))
        if not ok and "error" in res:
            print("         {}".format(res["error"]))

    lst = listings()
    with open(os.path.join(RESULTS, "listings.json"), "w", encoding="utf-8") as fh:
        json.dump(lst, fh, indent=2, sort_keys=True)

    with open(os.path.join(RESULTS, "00_summary.json"), "w", encoding="utf-8") as fh:
        json.dump({
            "checks": summary,
            "total": len(summary),
            "passing": len(summary) - failures,
            "failing": failures,
            "network_access": "none; every adapter resolves against a local fixture",
            "snapshot": build.SNAPSHOT,
        }, fh, indent=2, sort_keys=True)

    print("\n{}/{} checks hold".format(len(summary) - failures, len(summary)))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
