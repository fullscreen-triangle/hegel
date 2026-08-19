"""Parameter sweeps behind the manuscript panels.

The checks in run_validation.py each settle one proposition at one point. A
chart needs a curve, so this module varies a parameter and measures, calling
the same functions the checks call. Nothing here fits a model or draws a
schematic: every value is computed from the operational definitions in hfq/.

Results are cached to results/sweeps.json so the figures are reproducible from
the JSON alone.

Every adapter resolves against a local fixture. No request leaves the machine.
"""

from __future__ import annotations

import itertools
import json
import os
import random
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "fixtures"))

import build  # noqa: E402
from hfq import (Executor, ResultSet, TranslationMap, Verdict,  # noqa: E402
                 YieldSpec, check, kkt_residuals, parse, solve)

RESULTS = os.path.join(HERE, "results")


# ---------------------------------------------------------------------------
# 1. Retention: where thm:retention(b) holds and where it fails
# ---------------------------------------------------------------------------


def _random_chain(rng: random.Random, n: int, k: int, p_dom: float,
                  max_img: int):
    """A random k-stage chain over n elements. max_img=1 forces functionality."""
    layers = [["s%d:%d" % (i, j) for j in range(n)] for i in range(k + 1)]
    maps = []
    for i in range(k):
        pairs = {}
        for u in layers[i]:
            if rng.random() < p_dom:
                m = rng.randint(1, max_img)
                pairs[u] = tuple(rng.sample(layers[i + 1], m))
        maps.append(TranslationMap("m%d" % i, "n%d" % i, "n%d" % (i + 1), pairs))
    return layers[0], maps



def _injective_chain(rng: random.Random, n: int, k: int, p_dom: float):
    """A random k-stage chain that is injective on the realised sets.

    Built rather than rejected. Each stage draws a domain and assigns distinct
    images to its members, so no collision can arise; rejection sampling from
    the general generator would accept under 4% of draws and would bias the
    sample toward chains with small domains, which are exactly the ones where
    the bounds are loosest.
    """
    layers = [["s%d:%d" % (i, j) for j in range(n)] for i in range(k + 1)]
    maps = []
    for i in range(k):
        dom = [u for u in layers[i] if rng.random() < p_dom]
        imgs = rng.sample(layers[i + 1], len(dom))
        maps.append(TranslationMap("m%d" % i, "n%d" % i, "n%d" % (i + 1),
                                   {u: (v,) for u, v in zip(dom, imgs)}))
    return layers[0], maps


def _chain_stats(s0, maps) -> Dict[str, float]:
    sets = [set(s0)]
    rs, injective = [], True
    for mu in maps:
        cur = sets[-1]
        rs.append(mu.retention(cur))
        imgs = [mu.pairs[u] for u in cur if u in mu.pairs]
        flat = [x for t in imgs for x in t]
        if len(flat) != len(set(flat)):
            injective = False
        sets.append(mu.image(cur))
    survivors = 0
    for u in s0:
        frontier = {u}
        for mu in maps:
            frontier = mu.image(frontier)
            if not frontier:
                break
        if frontier:
            survivors += 1
    rho = survivors / len(s0)
    return {
        "rho": rho,
        "min_r": min(rs) if rs else 1.0,
        "r1": rs[0] if rs else 1.0,
        "lower": max(0.0, 1.0 - sum(1.0 - r for r in rs)),
        "injective": injective,
        "violates_min": rho > min(rs) + 1e-12 if rs else False,
    }


def sweep_retention() -> Dict[str, Any]:
    """rho against min_i r_i, for injective and non-injective chains.

    Under injectivity every point must sit on or below the diagonal
    (thm:retention(b)); without it, points above the diagonal appear, and their
    frequency is what rem:injectivity-needed reports.
    """
    rng = random.Random(20260818)
    pts = {"injective": [], "non_injective": []}
    for _ in range(1200):
        s0, maps = _injective_chain(rng, 8, 2, rng.uniform(0.4, 1.0))
        st = _chain_stats(s0, maps)
        assert st["injective"]
        pts["injective"].append(st)
    for _ in range(1200):
        s0, maps = _random_chain(rng, 8, 2, rng.uniform(0.4, 1.0), 3)
        st = _chain_stats(s0, maps)
        if not st["injective"]:
            pts["non_injective"].append(st)

    # violation rate against the maximum image size, i.e. how non-injective
    by_img = []
    for m in range(1, 7):
        viol = tot = 0
        for _ in range(600):
            s0, maps = _random_chain(rng, 8, 2, 0.8, m)
            st = _chain_stats(s0, maps)
            tot += 1
            viol += 1 if st["violates_min"] else 0
        by_img.append({"max_image": m, "rate": viol / tot, "trials": tot})

    # violation rate and bound gap against chain length
    by_len = []
    for k in range(1, 7):
        viol = tot = 0
        gaps = []
        for _ in range(400):
            s0, maps = _random_chain(rng, 8, k, 0.85, 3)
            st = _chain_stats(s0, maps)
            tot += 1
            viol += 1 if st["violates_min"] else 0
            gaps.append(st["min_r"] - st["lower"])
        by_len.append({"k": k, "rate": viol / tot,
                       "mean_gap": sum(gaps) / len(gaps)})
    return {"scatter": pts, "by_image_size": by_img, "by_length": by_len}


def sweep_bounds_surface() -> Dict[str, Any]:
    """The (b) and (c) bounds as surfaces over (r_1, r_2), with rho between.

    Two stages, retentions swept independently; rho is measured on a concrete
    chain realising each pair, so the surface is observed rather than plotted
    from the formula.
    """
    rng = random.Random(4242)
    n = 24
    grid = [i / 8.0 for i in range(1, 9)]
    out = []
    for r1 in grid:
        for r2 in grid:
            k1, k2 = max(1, round(r1 * n)), max(1, round(r2 * n))
            rhos = []
            for _ in range(40):
                a = ["a%d" % i for i in range(n)]
                b = ["b%d" % i for i in range(n)]
                c = ["c%d" % i for i in range(n)]
                d1 = rng.sample(a, k1)
                m1 = TranslationMap("m1", "A", "B",
                                    {u: (rng.choice(b),) for u in d1})
                d2 = rng.sample(b, k2)
                m2 = TranslationMap("m2", "B", "C",
                                    {u: (rng.choice(c),) for u in d2})
                rhos.append(_chain_stats(a, [m1, m2])["rho"])
            out.append({
                "r1": r1, "r2": r2,
                "rho": sum(rhos) / len(rhos),
                "upper": min(r1, r2),
                "lower": max(0.0, 1.0 - (1 - r1) - (1 - r2)),
            })
    return {"grid": grid, "cells": out}


# ---------------------------------------------------------------------------
# 2. Retention and amplification are independent
# ---------------------------------------------------------------------------


def sweep_cardinality() -> Dict[str, Any]:
    """The (r, a) plane with the output-cardinality ratio as the third axis.

    prop:cardinality-uninformative says only the product is observable from
    |mu(S)|. The level sets of the product are the hyperbolae r*a = const, and
    every point on one is indistinguishable from the others by output size.
    """
    n = 24
    cells = []
    for k in range(1, n + 1):            # |S ∩ dom mu| = k  ->  r = k/n
        for m in range(1, 7):            # images per retained element
            r = k / n
            a = float(m)
            cells.append({"r": r, "a": a, "ratio": r * a,
                          "output": k * m, "input": n})
    # explicit iso-cardinality families: same |mu(S)|, retention spread
    families = []
    for target in (12, 24, 48):
        fam = [c for c in cells if c["output"] == target]
        if len(fam) >= 2:
            families.append({
                "output": target,
                "retentions": [c["r"] for c in fam],
                "amplifications": [c["a"] for c in fam],
                "spread": max(c["r"] for c in fam) / min(c["r"] for c in fam),
            })
    return {"cells": cells, "iso_cardinality": families}


# ---------------------------------------------------------------------------
# 3. Allocation: the shadow price and the water-filling solution
# ---------------------------------------------------------------------------


def sweep_allocation() -> Dict[str, Any]:
    """Effort per step and the shadow price, as the budget grows.

    thm:allocation equalises marginal yields at one p*. Sweeping B traces
    p*(B) and the effort each step receives, and the KKT residual is recorded
    at every point rather than at one.
    """
    specs = [YieldSpec("a", weight=1.0), YieldSpec("b", weight=2.0),
             YieldSpec("c", weight=4.0), YieldSpec("d", weight=8.0)]
    curve = []
    for b in [2 ** (i / 4.0) for i in range(0, 45)]:
        alloc = solve(specs, b)
        resid = kkt_residuals(specs, alloc)
        curve.append({
            "budget": b,
            "shadow_price": alloc.shadow_price,
            "effort": dict(alloc.effort),
            "max_residual": resid["max_residual"],
            "support": len(alloc.support),
            "yield": sum(s.gamma(alloc.of(s.step_var)) for s in specs),
        })

    # yield surface over (budget, weight of one step) -- the third axis is the
    # total yield the solver achieves, measured not modelled
    surface = []
    budgets = [2 ** (i / 2.0) for i in range(1, 15)]
    weights = [0.5 * i for i in range(1, 13)]
    for b in budgets:
        for w in weights:
            sp = [YieldSpec("a", weight=1.0), YieldSpec("b", weight=2.0),
                  YieldSpec("c", weight=4.0), YieldSpec("d", weight=w)]
            al = solve(sp, b)
            surface.append({"budget": b, "weight": w,
                            "yield": sum(s.gamma(al.of(s.step_var)) for s in sp),
                            "shadow_price": al.shadow_price,
                            "effort_d": al.of("d")})

    # all-or-nothing steps are charged first: sweep how many there are
    stepwise = []
    for n_fixed in range(0, 5):
        sp = [YieldSpec("f%d" % i, weight=1.0, all_or_nothing=True,
                        fixed_cost=3.0) for i in range(n_fixed)]
        sp += [YieldSpec("o%d" % i, weight=2.0) for i in range(3)]
        al = solve(sp, 20.0)
        stepwise.append({
            "n_fixed": n_fixed,
            "charged_first": sum(al.charged_first.values()),
            "optimised_budget": al.optimised_budget,
            "shadow_price": al.shadow_price,
        })
    return {"curve": curve, "surface": surface, "budgets": budgets,
            "weights": weights, "stepwise": stepwise}


# ---------------------------------------------------------------------------
# 4. Cost of ordering: filter placement against selectivity
# ---------------------------------------------------------------------------


def sweep_ordering() -> Dict[str, Any]:
    """Requests spent by filter-before vs filter-after, over selectivity.

    The two plans compute the same extent whenever the discarded elements are
    barren. The request count differs, and the difference grows with the number
    of elements the filter removes -- which is the decision the plan language
    puts in the author's hands.
    """
    rows = []
    for n_drop in range(0, 9):
        # a source of 9 elements; n_drop of them consume nothing
        keep = 9 - n_drop
        before = 1 + 1 + keep      # closure + map + one request per kept element
        after = 1 + 1 + 9          # closure + map + one request per element
        rows.append({"dropped": n_drop, "before": before, "after": after,
                     "saving": after - before})

    # measured, not assumed: run the two plans at the fixture's own selectivity
    measured = []
    for name in ("order_a", "order_b"):
        reg = build.build_registry()
        ex = Executor(reg, maps=build.build_maps()).run(
            parse(open(os.path.join(HERE, "plans", name + ".hfq"),
                       encoding="utf-8").read()))
        measured.append({
            "plan": name,
            "requests": sum(s.spent for s in ex.steps),
            "coverage": len(ex.steps[-1].payload or []),
            "per_step": [{"step": s.step, "spent": s.spent} for s in ex.steps],
        })
    # A measured surface, not a model: for each subset of the KEGG identifiers
    # the filter removes, both orderings are generated as plan text and
    # executed, and the requests they spend are counted. The x-axis is how many
    # identifiers the filter names; the y-axis is the expansion's per-element
    # cost, varied through the rhea step's `within` allowance. Nothing here is
    # computed from a cost formula.
    drop_pool = ["KEGG:C%d" % i for i in (10, 9, 8, 7, 6, 5)]
    surface = []
    for n_drop in range(len(drop_pool) + 1):
        dropped = drop_pool[:n_drop]
        for within in (10, 20, 30, 40, 50, 60):
            row = {"dropped": n_drop, "within": within}
            for name in ("order_a", "order_b"):
                text = _ordering_plan(name, dropped, within)
                reg = build.build_registry()
                ex = Executor(reg, maps=build.build_maps()).run(parse(text))
                row[name + "_requests"] = sum(s.spent for s in ex.steps)
                row[name + "_coverage"] = len(ex.steps[-1].payload or [])
            row["saving"] = row["order_b_requests"] - row["order_a_requests"]
            row["same_extent"] = (row["order_a_coverage"]
                                  == row["order_b_coverage"])
            surface.append(row)

    return {"model": rows, "measured": measured, "surface": surface}


def _ordering_plan(order: str, dropped, within: int) -> str:
    """Emit plan text for one ordering, one filter set, one expansion cost.

    Generating the source rather than editing a parsed tree keeps the sweep
    honest: the executor sees exactly the language the manuscript documents,
    parsed by the same parser, with no path that bypasses the checker.

    The filter grammar admits one comparison per step, so a set of identifiers
    is removed by a chain of filter steps rather than a conjunction. Filters
    issue no request, so chaining them does not disturb the quantity measured.
    """
    attr = "_id" if order == "order_a" else "_from"
    lines = [
        "plan %s {" % order,
        "  budget 400 requests",
        '  let acids = from chebi ask descendants_of("CHEBI:1") within 10',
        "  let kegg = map acids via chebi2kegg expect partial 0.1",
    ]

    def filter_chain(src):
        """Append one filter step per removed identifier; return the last var."""
        cur = src
        for i, d in enumerate(dropped):
            nxt = "narrow%d" % i
            lines.append('  let %s = filter %s where %s != "%s"'
                         % (nxt, cur, attr, d))
            cur = nxt
        return cur

    if order == "order_a":
        last = filter_chain("kegg")
        lines += [
            "  let rxns = from rhea ask reactions_consuming(?c) "
            "with ?c in %s within %d" % (last, within),
            "  emit rxns",
        ]
    else:
        lines.append("  let rxns = from rhea ask reactions_consuming(?c) "
                     "with ?c in kegg within %d" % within)
        last = filter_chain("rxns")
        lines.append("  emit %s" % last)
    lines.append("}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# 5. Route divergence against map partiality
# ---------------------------------------------------------------------------


def sweep_routes() -> Dict[str, Any]:
    """Symmetric difference of two routes as both become more total.

    thm:route-extent(b): the divergence is a lower bound on unresolved
    correspondences, and it collapses to zero when both routes are total.
    """
    rng = random.Random(99)
    n = 40
    src = ["x%d" % i for i in range(n)]
    tgt = ["y%d" % i for i in range(n)]
    rows = []
    for pct in range(0, 101, 5):
        p = pct / 100.0
        sym, uni = [], []
        for _ in range(60):
            d1 = [u for u in src if rng.random() < p]
            d2 = [u for u in src if rng.random() < p]
            m1 = TranslationMap("d", "X", "Y",
                                {u: (tgt[src.index(u)],) for u in d1})
            m2 = TranslationMap("i", "X", "Y",
                                {u: (tgt[src.index(u)],) for u in d2})
            a, b = m1.image(set(src)), m2.image(set(src))
            sym.append(len(a ^ b))
            uni.append(len(a | b))
        rows.append({"coverage": p,
                     "symmetric_difference": sum(sym) / len(sym),
                     "union": sum(uni) / len(uni)})

    # the two-dimensional version: independent coverage for each route
    surface = []
    grid = [i / 10.0 for i in range(0, 11)]
    for p1 in grid:
        for p2 in grid:
            sym = []
            for _ in range(30):
                d1 = [u for u in src if rng.random() < p1]
                d2 = [u for u in src if rng.random() < p2]
                a = {tgt[src.index(u)] for u in d1}
                b = {tgt[src.index(u)] for u in d2}
                sym.append(len(a ^ b))
            surface.append({"p1": p1, "p2": p2,
                            "symmetric_difference": sum(sym) / len(sym)})
    return {"curve": rows, "grid": grid, "surface": surface}


# ---------------------------------------------------------------------------
# 6. The static check: cost and what it refuses
# ---------------------------------------------------------------------------


def sweep_check() -> Dict[str, Any]:
    """Check operations against plan length, and requests saved by refusing.

    thm:static is linear in m|Feat|; cor:refuse-before-contact fixes the
    request counter at zero on refusal, so the requests a refused plan would
    have issued are the saving, and they grow with the plan.
    """
    rows = []
    for m in range(1, 13):
        body = ['plan p%d {' % m, '  budget 400 requests',
                '  let s0 = from chebi',
                '      ask descendants_of("CHEBI:1")', '      within 10']
        for i in range(1, m):
            body += ['  let s%d = from rhea' % i,
                     '      ask reactions_consuming(?c)',
                     '      with ?c in s%d' % (i - 1),
                     '      within 20']
        body += ['  emit s%d' % (m - 1), '}']
        plan = parse("\n".join(body))
        reg = build.build_registry()
        rep = check(plan, reg)

        # The requests the plan actually issues when it is well-capable.
        # Executed, not modelled: this is the quantity a refusal saves.
        ex = Executor(reg, maps=build.build_maps()).run(plan)
        would_issue = ex.requests_issued

        # The same plan with its first step pointed at a source that
        # cannot answer it. thm:static must reject it and
        # cor:refuse-before-contact fixes the request counter at zero, so
        # this is measured at every m rather than asserted once at one m
        # and extrapolated across the axis.
        ill = parse("\n".join(body).replace("from chebi", "from enzdb", 1))
        ill_rep = check(ill, reg)
        if ill_rep.well_capability:
            raise AssertionError("ill variant admitted at m=%d" % m)
        ill_doc = Executor(reg, maps=build.build_maps()).run(ill)
        issued_after_refusal = ill_doc.requests_issued

        rows.append({"m": m, "operations": rep.operations,
                     "bound": rep.bound, "feature_count": 11,
                     "would_issue": would_issue,
                     "issued_after_refusal": issued_after_refusal,
                     "refused": ill_doc.requests_issued == 0 and not ill_rep.well_capability})

    # capability coverage: which declared sets admit which predicates
    from hfq.adapters import PREDICATE_FEATURES
    reg = build.build_registry()
    matrix = []
    for src_name, ad in sorted(reg.adapters.items()):
        for pred, feats in sorted(PREDICATE_FEATURES.items()):
            matrix.append({
                "source": src_name, "predicate": pred,
                "n_required": len(feats),
                "n_declared": len(ad.capabilities),
                "n_missing": len(set(feats) - set(ad.capabilities)),
                "admitted": set(feats) <= set(ad.capabilities),
            })
    return {"linearity": rows, "matrix": matrix}


# ---------------------------------------------------------------------------
# 7. Verdicts: how much a one-bit interface discards
# ---------------------------------------------------------------------------


def sweep_verdicts() -> Dict[str, Any]:
    """Where each verdict arises as budget and expectation vary.

    cor:onebit collapses five of the six onto one value. Sweeping the two
    parameters that move a plan between verdicts shows the regions a boolean
    interface merges.
    """
    tmpl = """plan sweep {{
  budget {budget} requests

  let acids = from chebi
      ask descendants_of("CHEBI:1")
      within 10

  let kegg  = map acids via chebi2kegg
      expect partial {expect}

  let rxns  = from rhea
      ask reactions_consuming(?c)
      with ?c in kegg
      within {within}

  emit rxns
}}"""
    cells = []
    budgets = [1, 2, 3, 4, 5, 6, 8, 10, 14, 20]
    expects = [i / 10.0 for i in range(1, 11)]
    for b in budgets:
        for e in expects:
            reg = build.build_registry()
            plan = parse(tmpl.format(budget=b, expect=e, within=60))
            ex = Executor(reg, maps=build.build_maps()).run(plan)
            last = ex.steps[-1] if ex.steps else None
            cells.append({
                "budget": b, "expect": e,
                "verdict": last.verdict.value if last else "surface",
                "requests": sum(s.spent for s in ex.steps),
                "one_bit": bool(last and last.verdict is Verdict.ANSWER),
                "n_steps_run": len(ex.steps),
            })
    counts: Dict[str, int] = {}
    for c in cells:
        counts[c["verdict"]] = counts.get(c["verdict"], 0) + 1
    return {"cells": cells, "budgets": budgets, "expects": expects,
            "counts": counts,
            "one_bit_true": sum(1 for c in cells if c["one_bit"]),
            "one_bit_false": sum(1 for c in cells if not c["one_bit"])}


# ---------------------------------------------------------------------------
# 8. Blame: chain length and where diagnosis terminates
# ---------------------------------------------------------------------------


def sweep_blame() -> Dict[str, Any]:
    """Blame-chain length against plan length, with the m-hop bound.

    prop:blame: every beta variable is bound by an earlier step, so the chain
    strictly decreases in position and terminates within m hops.
    """
    rows = []
    for m in range(2, 10):
        body = ['plan b%d {' % m, '  budget 400 requests',
                '  let s0 = from chebi',
                '      ask descendants_of("CHEBI:1")', '      within 10',
                '  let s1 = map s0 via chebi2kegg',
                '      expect partial 0.95']
        prev = "s1"
        for i in range(2, m):
            body += ['  let s%d = map %s via kegg2rhea' % (i, prev),
                     '      expect partial 0.95']
            prev = "s%d" % i
        body += ['  emit %s' % prev, '}']
        reg = build.build_registry()
        ex = Executor(reg, maps=build.build_maps()).run(parse("\n".join(body)))
        starved = [s for s in ex.steps if s.verdict is Verdict.STARVED]
        chains = [len(ex.blame_chain(s.step)) - 1 for s in starved]
        rows.append({
            "m": m,
            "n_steps": len(ex.steps),
            "n_starved": len(starved),
            "max_hops": max(chains) if chains else 0,
            "mean_hops": (sum(chains) / len(chains)) if chains else 0.0,
            "bound": len(ex.steps),
        })

    # how far a single perturbation propagates: cor:rerun confinement
    prop = []
    for pos in range(0, 5):
        body = ['plan c {', '  budget 400 requests',
                '  let s0 = from chebi',
                '      ask descendants_of("CHEBI:1")', '      within 10']
        prev = "s0"
        for i in range(1, 6):
            exp = 0.95 if i == pos + 1 else 0.1
            body += ['  let s%d = map %s via chebi2kegg' % (i, prev)
                     if i == 1 else
                     '  let s%d = map %s via kegg2rhea' % (i, prev),
                     '      expect partial %.2f' % exp]
            prev = "s%d" % i
        body += ['  emit %s' % prev, '}']
        reg = build.build_registry()
        ex = Executor(reg, maps=build.build_maps()).run(parse("\n".join(body)))
        bad = [i for i, s in enumerate(ex.steps)
               if s.verdict is not Verdict.ANSWER]
        prop.append({"perturbed_at": pos + 1, "n_affected": len(bad),
                     "first_affected": bad[0] if bad else None,
                     "n_steps": len(ex.steps)})
    return {"by_length": rows, "propagation": prop}


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

SWEEPS = {
    "retention": sweep_retention,
    "bounds_surface": sweep_bounds_surface,
    "cardinality": sweep_cardinality,
    "allocation": sweep_allocation,
    "ordering": sweep_ordering,
    "routes": sweep_routes,
    "check": sweep_check,
    "verdicts": sweep_verdicts,
    "blame": sweep_blame,
}


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    out: Dict[str, Any] = {}
    for name, fn in SWEEPS.items():
        out[name] = fn()
        print("{:<16} ok".format(name))
    path = os.path.join(RESULTS, "sweeps.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    print("\nwrote {}".format(os.path.relpath(path, HERE)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
