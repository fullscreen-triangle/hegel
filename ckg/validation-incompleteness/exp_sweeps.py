"""
Experiments 18-23: the same claims, measured across a RANGE.

The seventeen experiments above establish their propositions at single points:
a verdict is or is not what the paper says, a boolean is or is not true. That
is what a proposition needs, and it is all a proposition needs. It is not
enough to see the SHAPE of any of it -- whether a cost grows linearly or
quadratically, where a budget stops being sufficient, how a scoring deficit
scales with the benchmark it is computed over.

These six sweep the parameters the constructions already carry (corpus size,
budget, bound, recursion shape, distinctness/closure, refusal fraction) and
record the measurement at every setting. Nothing new is claimed. Each sweep is
a magnifying glass held over a proposition already proved, and each records the
point the corresponding fixed-parameter experiment tested so the two can be
checked against each other.

  18 -- cost of closure vs corpus size, both recursion shapes, both topologies
        (Propositions 8.6/8.8: same least model, different cost)
  19 -- verdict as a function of the budget tau (Theorem 3.7's third witness,
        swept: the ONLY predicate with a clock)
  20 -- bounded cost as a surface over (k, n)  (Prop 8.6 + Cor 8.7 inversion)
  21 -- counting derivability over (distinctness, closure) x mode, both UNA
        regimes (Prop 3.4 + Prop 8.3 inheritance)
  22 -- score separation vs refusal fraction over a synthetic BENCHMARK MIX
        (Prop 4.9: the deficit is proportional to what is refused)
  23 -- blocker attribution as the model, corpus and engine are each varied
        (Section 9's trichotomy, swept over a grid)

Every number written here comes from running `evaluate`, `solve` or
`counting_derivable` -- the same functions the seventeen use. No curve is
fitted, no cost is estimated from a complexity argument, and where a run
exceeds its budget the exception is recorded as the measurement rather than
being replaced by a number.
"""

from __future__ import annotations

from common import (
    ANSWERED,
    BOUNDED_PATH,
    BudgetExceeded,
    CANNOT_EXPRESS,
    COUNTING,
    NOT_DERIVABLE,
    NO_QUERY_SURFACE,
    OpenWorldEngine,
    RuleEngine,
    TIMEOUT,
    TRANSITIVE_QUERY,
    blocker_of,
    chain_corpus,
    chain_model,
    counting_derivable,
    evaluate,
    fixture_corpus,
    fixture_model,
    ground_truth_exactly_four,
    lattice_corpus,
    naive_score,
    q_count,
    q_instances,
    q_reach,
    q_reach_bounded,
    utc_stamp,
    verdict,
    verdict_aware_score,
)

# The sweeps are deterministic; this only fixes the order in which a mix is
# assembled in 22, and is recorded in the payload so the mix can be rebuilt.
SEED = 20260815

SIZES = (4, 6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32)
BUDGETS = (1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 48, 64)
BOUNDS = (1, 2, 3, 4, 5, 6, 7, 8)


def _steps_or_exceeded(engine, program, model, corpus, budget):
    """
    Run and report. A budget overrun is a MEASUREMENT -- the number of steps
    reached before the clock stopped -- not a missing value. Returning None for
    the step count and a separate flag would lose exactly the quantity the
    sweep is after, which is where the overrun happens.
    """
    try:
        answers, certified, steps = engine.solve(program, model, corpus, budget)
        return {"completed": True, "steps": steps, "answers": len(answers),
                "certified": bool(certified)}
    except BudgetExceeded as exc:
        return {"completed": False, "steps": exc.steps, "budget": exc.budget,
                "answers": None, "certified": None}


# ---------------------------------------------------------------------------
# 18 -- closure cost vs corpus size, by recursion shape and topology.
# ---------------------------------------------------------------------------


def exp_18_closure_cost_sweep():
    """
    Proposition 8.8 says the two recursion shapes have the SAME least model.
    Proposition 8.6's neighbourhood says they do not have the same cost. Both
    are single-point facts in experiment 17; here they are swept over n so the
    separation between the two shapes can be seen to grow rather than merely
    to exist at one size.

    Two topologies, and the difference between them is the finding. On a CHAIN
    the two shapes cost exactly the same at every size: each node has one
    successor, so the left-recursive agenda holds one path at a time and never
    re-derives anything. That is not a refutation of the cost claim, it is the
    degenerate case of it, and it is swept here rather than omitted because a
    reader who tested the claim on a chain would see a flat ratio of 1 and
    conclude the shapes are interchangeable. On a LATTICE, where a node is
    reachable by several prefixes, the separation appears and grows.
    """
    expected = {
        "least_models_agree_everywhere": True,
        "left_never_cheaper": True,
        "chain_right_is_linear": True,
        # The two halves of Prop 8.8, each on the topology that can show it.
        "chain_shapes_cost_the_same": True,
        "lattice_separation_grows": True,
    }

    model = chain_model()
    right = RuleEngine(left_recursive=False)
    left = RuleEngine(left_recursive=True)
    q = q_reach("q_reach", "precedes", "a0")

    # Generous: the point is to measure cost, not to trip the clock. 19 is the
    # experiment about the clock.
    BIG = 10 ** 7

    # The lattice is swept over DEPTH, and its left-recursive cost is
    # exponential in depth, so it gets its own (short) range. Reusing SIZES
    # would spend the run on a number no reader needs to see.
    LATTICE_DEPTHS = (2, 3, 4, 5, 6, 7)

    series = {}
    disagreements = []
    left_cheaper_at = []

    def sweep(key, build, xs, xname):
        rows = []
        for x in xs:
            corpus = build(x)
            a_ans, _, a_steps = right.solve(right.lower(model, q), model, corpus, BIG)
            b_ans, _, b_steps = left.solve(left.lower(model, q), model, corpus, BIG)
            if a_ans != b_ans:
                disagreements.append({xname: x, "topology": key})
            if b_steps < a_steps:
                left_cheaper_at.append({xname: x, "topology": key})
            rows.append({
                xname: x,
                "n": x,
                "reached": len(a_ans),
                "steps_right": a_steps,
                "steps_left": b_steps,
                "ratio": b_steps / a_steps if a_steps else None,
            })
        series[key] = rows

    for cyclic in (False, True):
        key = "chain-cyclic" if cyclic else "chain-acyclic"
        sweep(key, lambda n, c=cyclic: chain_corpus(n, cyclic=c), SIZES, "n")
    for cyclic in (False, True):
        key = "lattice-cyclic" if cyclic else "lattice-acyclic"
        sweep(key, lambda d, c=cyclic: lattice_corpus(d, cyclic=c, width=2),
              LATTICE_DEPTHS, "depth")

    # On a path a0->...->a{n-1} the right-recursive frontier advances one level
    # per step and stops when the frontier empties: n-1 reachable nodes, n
    # steps (the last one finding nothing). Checked, not assumed.
    chain_linear = all(
        r["steps_right"] == r["n"] for r in series["chain-acyclic"]
    )
    chain_flat = all(
        r["ratio"] == 1.0
        for k in ("chain-acyclic", "chain-cyclic")
        for r in series[k]
    )
    lat = series["lattice-cyclic"]
    lattice_grows = all(
        lat[i]["ratio"] < lat[i + 1]["ratio"] for i in range(len(lat) - 1)
    )

    ratios = {k: [r["ratio"] for r in v] for k, v in series.items()}
    measured = {
        "series": series,
        "sizes": list(SIZES),
        "lattice_depths": list(LATTICE_DEPTHS),
        "least_models_agree_everywhere": not disagreements,
        "disagreements": disagreements,
        "left_never_cheaper": not left_cheaper_at,
        "left_cheaper_at": left_cheaper_at,
        "chain_right_is_linear": bool(chain_linear),
        "chain_shapes_cost_the_same": bool(chain_flat),
        "lattice_separation_grows": bool(lattice_grows),
        "max_ratio": {k: max(v) for k, v in ratios.items()},
    }
    passed = all(measured[k] == expected[k] for k in expected)

    return {
        "experiment": "18_closure_cost_sweep",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "the two shapes must return the same answer set at every size "
                "and topology; if they ever disagreed the cost comparison "
                "would be between two different computations and Prop 8.8 "
                "would be the thing refuted, not illustrated. The chain is "
                "the second control: a topology on which the cost claim is "
                "TRUE but invisible, so a flat ratio there is the expected "
                "reading and not a negative result"
            ),
            "outcome": {"disagreements": disagreements,
                        "chain_ratio_is_flat_at_one": bool(chain_flat)},
            "must_be_empty": True,
        },
        "interpretation": (
            "Both shapes compute the same least model at every size and "
            "topology measured, so the divergence between the two curves is "
            "cost and nothing else. On the chain there is no divergence at "
            "all: one successor per node means the left-recursive agenda "
            "never re-derives a prefix, and the ratio is exactly 1 at every "
            "size. The separation requires a node reachable by more than one "
            "prefix, and on the lattice it appears immediately and grows with "
            "depth, the left-recursive shape re-exploring each node once per "
            "path that reaches it while the right-recursive shape visits it "
            "once per level. The practical reading is that recursion shape is "
            "free on corpora shaped like paths and expensive on corpora "
            "shaped like real ones, and that a benchmark built from chains "
            "cannot tell the two apart. Neither curve is a complexity "
            "estimate: each point is a step count returned by the solver."
        ),
    }


# ---------------------------------------------------------------------------
# 19 -- the verdict as a function of the budget.
# ---------------------------------------------------------------------------


def exp_19_budget_sweep():
    """
    Theorem 3.7 gives three independent predicates and notes that Ans_tau is
    the only one carrying a clock. Sweeping tau exhibits that directly: over a
    fixed model, corpus and engine, with Exp and Der held constant and TRUE,
    the verdict still changes with tau alone.
    """
    expected = {
        "expressible_throughout": True,
        "verdict_changes_with_budget_alone": True,
        "monotone_in_budget": True,
        "labels_seen_subset_of_two": True,
    }

    model = chain_model()
    corpus = chain_corpus(16, cyclic=True)
    q = q_reach("q_reach", "precedes", "a0")

    rows = []
    for tau in BUDGETS:
        v = evaluate(q, model, corpus, RuleEngine(), budget=tau)
        rows.append({
            "budget": tau,
            "label": v.label,
            "answered": v.label == ANSWERED,
            "steps": (v.payload.get("steps") if v.label == ANSWERED
                      else v.payload.get("steps")),
        })

    labels = {r["label"] for r in rows}
    answered_flags = [r["answered"] for r in rows]
    # Monotone: once answered, answered for every larger budget. A budget that
    # helped and then stopped helping would mean the cost is not a function of
    # the input alone, and every step count in 18 would be suspect.
    monotone = all(
        answered_flags[i] <= answered_flags[i + 1]
        for i in range(len(answered_flags) - 1)
    )
    first_ok = next((r["budget"] for r in rows if r["answered"]), None)

    measured = {
        "series": rows,
        "budgets": list(BUDGETS),
        "expressible_throughout": bool(q.requires <= model.features()),
        "labels_seen": sorted(labels),
        "labels_seen_subset_of_two": labels <= {ANSWERED, TIMEOUT},
        "verdict_changes_with_budget_alone": len(labels) > 1,
        "monotone_in_budget": bool(monotone),
        "threshold_budget": first_ok,
        "corpus_size": 16,
    }
    passed = all(measured[k] == expected[k] for k in expected)

    # Control: the same question on the SAME corpus at the largest budget must
    # answer, so the timeouts are the clock and not an engine that cannot do
    # the work at all.
    ctrl = evaluate(q, model, corpus, RuleEngine(), budget=10 ** 6)

    return {
        "experiment": "19_budget_sweep",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "at an unbounded budget the question must be ANSWERED, so the "
                "TIMEOUT verdicts below are attributable to tau and not to a "
                "missing capability -- otherwise the sweep would be measuring "
                "E3 and reporting it as E5"
            ),
            "outcome": ctrl.to_json(),
            "must_be": ANSWERED,
            "correct": ctrl.label == ANSWERED,
        },
        "interpretation": (
            "Exp holds at every point of this sweep and Der holds at every "
            "point; the model, the corpus and the engine are fixed. The only "
            "quantity varying is tau, and the verdict changes with it. That "
            "is the third witness of Theorem 3.7 exhibited as a curve rather "
            "than as a pair of cases: the threshold budget is a property of "
            "the run, and reporting a TIMEOUT as a capability finding would "
            "attribute it to the engine."
        ),
    }


# ---------------------------------------------------------------------------
# 20 -- bounded cost as a surface over (k, n).
# ---------------------------------------------------------------------------


def exp_20_bounded_surface():
    """
    Proposition 8.6: the bounded query costs O(k), independent of the corpus.
    Corollary 8.7: therefore for large enough corpora the bounded question is
    affordable where the unbounded one is not. Experiment 16 shows the
    inversion at one size; this measures the whole surface, which is what makes
    'independent of the corpus' a statement one can look at.
    """
    expected = {
        "bounded_cost_is_k": True,
        "bounded_independent_of_n": True,
        "unbounded_grows_with_n": True,
        "inversion_region_nonempty": True,
    }

    model = chain_model()
    engine = RuleEngine()
    BIG = 10 ** 7

    grid = []           # one row per (k, n)
    unbounded = []      # one row per n
    violations = []
    for n in SIZES:
        corpus = chain_corpus(n, cyclic=True)
        u = engine.solve(engine.lower(model, q_reach("qu", "precedes", "a0")),
                         model, corpus, BIG)
        unbounded.append({"n": n, "steps": u[2], "reached": len(u[0])})
        for k in BOUNDS:
            qb = q_reach_bounded(f"qb{k}", "precedes", "a0", k)
            a, _, s = engine.solve(engine.lower(model, qb), model, corpus, BIG)
            grid.append({"k": k, "n": n, "steps": s, "reached": len(a)})
            if s != k:
                violations.append({"k": k, "n": n, "steps": s})

    by_k = {}
    for row in grid:
        by_k.setdefault(row["k"], set()).add(row["steps"])
    independent = all(len(v) == 1 for v in by_k.values())

    u_steps = [r["steps"] for r in unbounded]
    grows = all(u_steps[i] <= u_steps[i + 1] for i in range(len(u_steps) - 1)) \
        and u_steps[-1] > u_steps[0]

    # The inversion region: settings where a budget exists that the bounded
    # question fits and the unbounded one does not.
    inversion = [
        {"n": u["n"], "k": k, "bounded_steps": k, "unbounded_steps": u["steps"]}
        for u in unbounded for k in BOUNDS if k < u["steps"]
    ]

    measured = {
        "grid": grid,
        "unbounded": unbounded,
        "bounds": list(BOUNDS),
        "sizes": list(SIZES),
        "bounded_cost_is_k": not violations,
        "violations": violations,
        "bounded_independent_of_n": bool(independent),
        "steps_by_k": {str(k): sorted(v)[0] for k, v in sorted(by_k.items())},
        "unbounded_grows_with_n": bool(grows),
        "inversion_region_nonempty": len(inversion) > 0,
        "inversion_cells": len(inversion),
        "total_cells": len(grid),
    }
    passed = all(measured[k] == expected[k] for k in expected)

    return {
        "experiment": "20_bounded_surface",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "the bounded and unbounded questions must return the SAME set "
                "wherever the bound exceeds the graph's depth; if the bounded "
                "form were cheaper because it answered a different question, "
                "the inversion would be an artefact of the comparison"
            ),
            "outcome": [
                {"n": u["n"],
                 "bounded_at_k8": next(g["reached"] for g in grid
                                       if g["n"] == u["n"] and g["k"] == 8),
                 "unbounded": u["reached"],
                 "agree": next(g["reached"] for g in grid
                               if g["n"] == u["n"] and g["k"] == 8) == u["reached"]}
                for u in unbounded if u["n"] <= 8
            ],
            "must_be": True,
        },
        "interpretation": (
            "The bounded cost is exactly k at every corpus size measured: the "
            "surface is a set of flat terraces, one per k, and it does not "
            "tilt as n grows. The unbounded cost rises with n on the same "
            "corpora. The inversion of Corollary 8.7 is therefore not a "
            "special case but a region, and it widens with the corpus."
        ),
    }


# ---------------------------------------------------------------------------
# 21 -- counting derivability over (distinctness, closure) x mode x UNA.
# ---------------------------------------------------------------------------


def exp_21_counting_surface():
    """
    Proposition 3.4 splits the counting quantifier into three clauses with
    different requirements. Proposition 8.3 says one engine inherits the
    distinctness half for free. Experiment 04 tabulates the twelve cells; this
    sweeps the same axes but records, for each cell, WHICH of the two
    prerequisites is missing, so the geometry of the split is visible rather
    than the pass/fail alone.
    """
    expected = {
        "ge_needs_distinctness_only": True,
        "le_needs_closure_only": True,
        "eq_needs_both": True,
        "una_inheritance_supplies_distinctness": True,
    }

    corpus = fixture_corpus()
    cells = []
    for una in (False, True):
        for distinct in (False, True):
            for closure in (False, True):
                model = fixture_model(with_counting=True, with_closure=closure,
                                      with_distinctness=distinct,
                                      scoped_to_participants=True)
                for mode in ("ge", "le", "eq"):
                    ok, reason = counting_derivable(
                        model, corpus, "rx1", "hasParticipant", 4, mode,
                        inherits_una=una,
                    )
                    cells.append({
                        "una": una, "distinct": distinct, "closure": closure,
                        "mode": mode, "derivable": bool(ok),
                        "reason": reason,
                        # The two prerequisites, separated. `have_distinct` is
                        # the disjunction Prop 8.3 makes: declared OR inherited.
                        "have_distinct": bool(distinct or una),
                        "have_closure": bool(closure),
                    })

    def sat(mode):
        return {(c["have_distinct"], c["have_closure"])
                for c in cells if c["mode"] == mode and c["derivable"]}

    ge, le, eq = sat("ge"), sat("le"), sat("eq")
    # ge is derivable exactly where distinctness holds, regardless of closure.
    ge_ok = ge == {(True, False), (True, True)}
    le_ok = le == {(False, True), (True, True)}
    eq_ok = eq == {(True, True)}

    # With UNA inherited, the `distinct` switch stops mattering for ge.
    una_cells = [c for c in cells if c["una"] and c["mode"] == "ge"]
    una_ok = all(c["derivable"] for c in una_cells)

    measured = {
        "cells": cells,
        "n_cells": len(cells),
        "ge_satisfying_corners": sorted(map(list, ge)),
        "le_satisfying_corners": sorted(map(list, le)),
        "eq_satisfying_corners": sorted(map(list, eq)),
        "ge_needs_distinctness_only": bool(ge_ok),
        "le_needs_closure_only": bool(le_ok),
        "eq_needs_both": bool(eq_ok),
        "una_inheritance_supplies_distinctness": bool(una_ok),
        "derivable_count": sum(1 for c in cells if c["derivable"]),
    }
    passed = all(measured[k] == expected[k] for k in expected)

    # Control: the ground truth is nonempty, so 'not derivable' is never
    # trivially right because there was nothing to derive.
    truth = ground_truth_exactly_four(corpus)

    return {
        "experiment": "21_counting_surface",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "the counted property must actually hold of something in the "
                "corpus, otherwise every 'not derivable' cell is vacuously "
                "unobjectionable and the surface says nothing"
            ),
            "outcome": {"ground_truth": sorted(truth), "size": len(truth)},
            "must_be_nonempty": True,
            "correct": len(truth) > 0,
        },
        "interpretation": (
            "The three clauses occupy three different regions of the same "
            "two-dimensional prerequisite space: at-least fills the "
            "distinctness half-plane, at-most the closure half-plane, and "
            "exactly-n only their intersection. Inheriting unique names moves "
            "an engine across the distinctness axis for free, which is why "
            "two engines can legitimately disagree on the same at-least "
            "question over the same corpus."
        ),
    }


# ---------------------------------------------------------------------------
# 22 -- score separation vs the composition of the benchmark.
# ---------------------------------------------------------------------------


def exp_22_scoring_sweep():
    """
    Proposition 4.9 compares an honest refuser with a confident wrong answerer
    on ONE question, where the naive rule scores both at zero and the
    verdict-aware rule separates them. On one question that is a fact about
    two numbers. Swept over a benchmark whose refusable fraction varies, it is
    a fact about a ranking: the naive rule's deficit is proportional to how
    much of the benchmark is unanswerable, so the ordering it induces is a
    function of the benchmark's composition rather than of the systems.
    """
    expected = {
        "naive_ranks_equal_everywhere": True,
        "aware_separates_whenever_refusable": True,
        "deficit_proportional_to_refusable": True,
        "orderings_disagree": True,
    }

    corpus = fixture_corpus()
    truth = ground_truth_exactly_four(corpus)
    model = fixture_model(with_counting=True, with_closure=True,
                          with_distinctness=True, scoped_to_participants=True)

    # The honest system refuses what it cannot lower; the confident one always
    # emits an answer set and asserts certification. Both are REAL runs: the
    # honest verdict is what `evaluate` returns for the gated rule engine, and
    # the confident one is the ungated engine from experiment 08.
    from exp_capability import UngatedRuleEngine

    q_refusable = q_count("q_eq4", "hasParticipant", 4, "eq")
    q_answerable = q_reach("q_ok", "hasParticipant", "rx1")
    answerable_truth = corpus.successors("rx1", "hasParticipant")

    honest_refuse = evaluate(q_refusable, model, corpus, RuleEngine(), subject="rx1")
    conf_refuse = evaluate(q_refusable, model, corpus, UngatedRuleEngine(), subject="rx1")
    honest_ok = evaluate(q_answerable, model, corpus, RuleEngine())
    conf_ok = evaluate(q_answerable, model, corpus, UngatedRuleEngine())

    TOTAL = 20
    rows = []
    disagreeing = 0
    for n_ref in range(0, TOTAL + 1):
        n_ans = TOTAL - n_ref
        # The mix: n_ref copies of the refusable question, n_ans of the
        # answerable one. Both systems face the identical benchmark.
        naive_h = (n_ref * naive_score(honest_refuse, truth)
                   + n_ans * naive_score(honest_ok, answerable_truth))
        naive_c = (n_ref * naive_score(conf_refuse, truth)
                   + n_ans * naive_score(conf_ok, answerable_truth))
        aware_h = (n_ref * verdict_aware_score(honest_refuse, truth)
                   + n_ans * verdict_aware_score(honest_ok, answerable_truth))
        aware_c = (n_ref * verdict_aware_score(conf_refuse, truth)
                   + n_ans * verdict_aware_score(conf_ok, answerable_truth))
        naive_order = (0 if naive_h == naive_c else (1 if naive_h > naive_c else -1))
        aware_order = (0 if aware_h == aware_c else (1 if aware_h > aware_c else -1))
        if naive_order != aware_order:
            disagreeing += 1
        rows.append({
            "refusable": n_ref, "answerable": n_ans,
            "refusable_fraction": n_ref / TOTAL,
            "naive_honest": naive_h, "naive_confident": naive_c,
            "aware_honest": aware_h, "aware_confident": aware_c,
            "naive_gap": naive_h - naive_c,
            "aware_gap": aware_h - aware_c,
            "naive_order": naive_order, "aware_order": aware_order,
            "orders_agree": naive_order == aware_order,
        })

    naive_equal = all(r["naive_gap"] == 0 for r in rows)
    # The aware gap must be exactly the refusable count: each refused question
    # scores 1 for the honest system and 0 for the confident one, and the two
    # systems score identically on the answerable ones.
    proportional = all(r["aware_gap"] == r["refusable"] for r in rows)
    separates = all(r["aware_gap"] > 0 for r in rows if r["refusable"] > 0)

    measured = {
        "series": rows,
        "total_questions": TOTAL,
        "seed": SEED,
        "naive_ranks_equal_everywhere": bool(naive_equal),
        "aware_separates_whenever_refusable": bool(separates),
        "deficit_proportional_to_refusable": bool(proportional),
        "orderings_disagree": disagreeing > 0,
        "disagreeing_mixes": disagreeing,
        "component_verdicts": {
            "honest_on_refusable": honest_refuse.to_json(),
            "confident_on_refusable": conf_refuse.to_json(),
            "honest_on_answerable": honest_ok.label,
            "confident_on_answerable": conf_ok.label,
        },
    }
    passed = all(measured[k] == expected[k] for k in expected)

    return {
        "experiment": "22_scoring_sweep",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "at zero refusable questions the two systems must be "
                "indistinguishable under BOTH rules; a separation there would "
                "mean the verdict-aware rule rewards refusal as such rather "
                "than rewarding a correct report of a limitation"
            ),
            "outcome": rows[0],
            "must_be": {"naive_gap": 0, "aware_gap": 0},
            "correct": rows[0]["naive_gap"] == 0 and rows[0]["aware_gap"] == 0,
        },
        "interpretation": (
            "On a benchmark with no unanswerable questions the two systems "
            "are ranked identically by both rules, as they should be. As the "
            "refusable fraction grows the verdict-aware gap grows exactly in "
            "step with it while the naive gap stays flat at zero, because the "
            "naive rule has no value to assign to a refusal and assigns the "
            "same zero to a refusal and to a certified wrong emptiness. The "
            "ordering a benchmark reports is therefore a function of the "
            "benchmark's composition, and a system tuned to it is tuned to "
            "the mix rather than to the task."
        ),
    }


# ---------------------------------------------------------------------------
# 23 -- blocker attribution over a grid.
# ---------------------------------------------------------------------------


def exp_23_blocker_grid():
    """
    Section 9's trichotomy assigns each non-answer to the model, the corpus or
    the engine. Sweeping the three independently over a grid checks that the
    attribution tracks the thing actually varied: changing the model must move
    the blocker to the model, and so on. That is what makes the trichotomy a
    diagnosis rather than a label.
    """
    expected = {
        "model_change_attributed_to_model": True,
        "engine_change_attributed_to_engine": True,
        "no_answered_case_has_a_blocker": True,
        # NOT "all three observed". Only two of the trichotomy's three values
        # are reachable through `evaluate`: Definition 7.1 sends every one of
        # the six non-answer labels to blocked-by-model or blocked-by-engine,
        # and blocked-by-corpus is the fallback for a label that no clause of
        # Definition 4.2 produces. A corpus that simply lacks the facts yields
        # ANSWERED with an empty set, which is a correct report and not a
        # block. This is recorded as a measurement below rather than asserted
        # away, because it is a property of the definitions and not of this
        # grid: the earlier draft of this experiment expected all three and
        # was wrong to.
        "blocked_by_corpus_reachable_from_evaluate": False,
        "empty_corpus_answers_rather_than_blocks": True,
        # Each of the three axes evaluate CAN move must be witnessed by a cell
        # whose verdict actually differs from its baseline. Without this, the
        # two checks above pass on a grid where nothing varied and every cell
        # was blocked for an unrelated reason.
        "model_axis_witnessed": True,
        "engine_axis_witnessed": True,
        "budget_axis_witnessed": True,
    }

    corpus = fixture_corpus()
    chain_c = chain_corpus(12, cyclic=True)

    # Model axis: does the grammar carry COUNTING?
    m_full = fixture_model(with_counting=True, with_closure=True,
                           with_distinctness=True, scoped_to_participants=True)
    m_nocount = fixture_model(with_counting=False, with_closure=True,
                              with_distinctness=True, scoped_to_participants=True)
    m_noclosure = fixture_model(with_counting=True, with_closure=False,
                                with_distinctness=True, scoped_to_participants=True)
    chain_m = chain_model()
    chain_m_nobound = chain_model(with_bounded=False)

    cells = []
    q_eq = q_count("q_eq4", "hasParticipant", 4, "eq")
    q_b = q_reach_bounded("q_b3", "precedes", "a0", 3)
    # The `ge` clause needs distinctness ONLY (Prop 3.4), which m_full has, so
    # this question passes E2 and the verdict is decided at E3 -- by the
    # compiler. `eq` would be refused at E2 for want of nothing the engine
    # controls, and an earlier version of this grid used it and mislabelled the
    # resulting blocked-by-model as an engine effect. The evaluation order of
    # Definition 4.2 is the reason: a question refused earlier never reaches
    # the clause one intends to vary.
    q_ge = q_count("q_ge4", "hasParticipant", 4, "ge")

    settings = [
        # (label, question, model, corpus, engine, budget, varied-axis)
        ("count-ge/full/open", q_ge, m_full, corpus, OpenWorldEngine(), 10 ** 6, "baseline"),
        ("count-ge/full/rule", q_ge, m_full, corpus, RuleEngine(), 10 ** 6, "engine"),
        ("count-eq/no-COUNTING/open", q_eq, m_nocount, corpus, OpenWorldEngine(), 10 ** 6, "model"),
        ("count-eq/no-closure/open", q_eq, m_noclosure, corpus, OpenWorldEngine(), 10 ** 6, "model"),
        ("bounded/full/rule", q_b, chain_m, chain_c, RuleEngine(), 10 ** 6, "baseline"),
        ("bounded/no-BOUNDED/rule", q_b, chain_m_nobound, chain_c, RuleEngine(), 10 ** 6, "model"),
        ("bounded/full/open", q_b, chain_m, chain_c, OpenWorldEngine(), 10 ** 6, "engine"),
        ("reach/full/rule/tau=2", q_reach("q_r", "precedes", "a0"), chain_m,
         chain_c, RuleEngine(), 2, "budget"),
        # The corpus axis: a concept the model declares and the engine lowers,
        # whose extension is empty. Everything the trichotomy could blame is
        # present and working.
        ("instances/empty-extension/rule", q_instances("q_i", "Transaminase"),
         m_full, corpus, RuleEngine(), 10 ** 6, "corpus"),
    ]

    for label, q, model, c, engine, budget, axis in settings:
        v = evaluate(q, model, c, engine, budget=budget)
        # blocker_of returns (blocker, unblockers) -- Definition 7.1 pairs the
        # attribution with the repair, and a sweep that kept only the first
        # half would record the diagnosis while discarding what to do about it.
        got = blocker_of(v, q, model, c)
        b, unblockers = (None, None) if got is None else got
        cells.append({
            "setting": label, "varied": axis, "label": v.label,
            "blocker": b, "unblockers": unblockers,
            "answered": v.label == ANSWERED,
            "engine": engine.name, "model": model.name, "corpus": c.name,
            "budget": budget,
        })

    seen = {c["blocker"] for c in cells if c["blocker"] is not None}
    model_cells = [c for c in cells if c["varied"] == "model"]
    engine_cells = [c for c in cells if c["varied"] == "engine"]

    model_ok = all(c["blocker"] == "blocked-by-model" for c in model_cells)
    engine_ok = all(c["blocker"] == "blocked-by-engine" for c in engine_cells)

    # Asserting the VALUE of a varied cell's blocker is weaker than it looks: a
    # cell can carry the expected blocker while the axis it names changed
    # nothing, if the baseline was already blocked there for another reason.
    # Each varied cell is therefore paired with its baseline (same question,
    # one axis moved) and the pair is recorded as differing or not. A pair that
    # does not differ is not a failure -- it is a cell that does not witness
    # its axis, and saying so is the point of recording it.
    baselines = {c["setting"]: c for c in cells if c["varied"] == "baseline"}
    pairs = [
        ("count-ge/full/rule", "count-ge/full/open", "engine"),
        ("count-eq/no-COUNTING/open", "count-ge/full/open", "model"),
        ("count-eq/no-closure/open", "count-ge/full/open", "model"),
        ("bounded/no-BOUNDED/rule", "bounded/full/rule", "model"),
        ("bounded/full/open", "bounded/full/rule", "engine"),
        ("reach/full/rule/tau=2", "bounded/full/rule", "budget"),
        ("instances/empty-extension/rule", "bounded/full/rule", "corpus"),
    ]
    by_setting = {c["setting"]: c for c in cells}
    contrasts = []
    for varied_name, base_name, axis in pairs:
        v_cell, b_cell = by_setting[varied_name], baselines[base_name]
        contrasts.append({
            "axis": axis,
            "varied": varied_name,
            "baseline": base_name,
            "varied_label": v_cell["label"],
            "baseline_label": b_cell["label"],
            "differs": v_cell["label"] != b_cell["label"],
            "blocker": v_cell["blocker"],
        })
    witnessing = {
        c["axis"] for c in contrasts if c["differs"]
    }
    # Every axis the grid varies must be witnessed by at least ONE cell whose
    # verdict actually moved. The corpus axis is expected not to appear here,
    # for the reason recorded in `expected`.
    axes_witnessed = sorted(witnessing)
    no_blocker_when_answered = all(
        c["blocker"] is None for c in cells if c["answered"]
    )

    # The budget axis is recorded separately because the trichotomy does NOT
    # separate it: Definition 7.1 sends TIMEOUT to blocked-by-engine, so a run
    # starved of budget is attributed to the same place as a missing lowering.
    # That is a coarseness of the trichotomy, not a defect of the sweep, and it
    # is measured here rather than left for a reader to discover.
    budget_cells = [c for c in cells if c["varied"] == "budget"]
    budget_collides = all(
        c["blocker"] == "blocked-by-engine" for c in budget_cells
    ) and any(c["blocker"] == "blocked-by-engine" for c in engine_cells)

    # The corpus axis. `blocker_of` reaches its corpus branch only as a
    # fallback, for a label no clause of Definition 4.2 emits, so the question
    # is not "does the grid contain a corpus block" but "what does a corpus
    # that lacks the facts actually produce". It produces ANSWERED with an
    # empty set: a correct report, and the paper's own position that an empty
    # answer under a working pipeline is a finding rather than a failure.
    corpus_cells = [c for c in cells if c["varied"] == "corpus"]
    empty_answers = all(
        c["answered"] and c["blocker"] is None for c in corpus_cells
    ) and bool(corpus_cells)

    measured = {
        "cells": cells,
        "blockers_observed": sorted(seen),
        "all_three_blockers_observed": len(seen) >= 3,
        "model_change_attributed_to_model": bool(model_ok),
        "engine_change_attributed_to_engine": bool(engine_ok),
        "no_answered_case_has_a_blocker": bool(no_blocker_when_answered),
        "answered_count": sum(1 for c in cells if c["answered"]),
        "budget_shares_blocker_with_engine": bool(budget_collides),
        "budget_cells": budget_cells,
        "blocked_by_corpus_reachable_from_evaluate": "blocked-by-corpus" in seen,
        "empty_corpus_answers_rather_than_blocks": bool(empty_answers),
        "corpus_cells": corpus_cells,
        "contrasts": contrasts,
        "axes_witnessed_by_a_changed_verdict": axes_witnessed,
        "model_axis_witnessed": "model" in witnessing,
        "engine_axis_witnessed": "engine" in witnessing,
        "budget_axis_witnessed": "budget" in witnessing,
    }
    passed = all(measured[k] == expected[k] for k in expected)

    return {
        "experiment": "23_blocker_grid",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "at least one setting must ANSWER and carry no blocker; a "
                "grid in which every cell is blocked would satisfy the "
                "attribution checks trivially and demonstrate nothing about "
                "the trichotomy's discrimination"
            ),
            "outcome": [c["setting"] for c in cells if c["answered"]],
            "must_be_nonempty": True,
            "correct": any(c["answered"] for c in cells),
        },
        "interpretation": (
            "Removing a construct from the grammar produces blocked-by-model; "
            "swapping the engine while holding the model and corpus fixed "
            "produces blocked-by-engine. On those two axes the trichotomy "
            "discriminates rather than merely labelling, which is what a "
            "reader needs before acting on a verdict. The budget axis is "
            "where it does not: a TIMEOUT is sent to blocked-by-engine, the "
            "same cell as a missing lowering, so 'blocked-by-engine' alone "
            "does not distinguish an engine that cannot compile the question "
            "from one that was not given time to run it. The two are "
            "separable only by the verdict label the payload carries "
            "alongside the blocker, and a report that keeps the blocker and "
            "discards the label loses the distinction. The corpus axis does "
            "not appear at all: a concept the model declares and the engine "
            "lowers, whose extension happens to be empty, is ANSWERED with an "
            "empty set and carries no blocker. blocked-by-corpus is therefore "
            "unreachable through the evaluation order -- it is a fallback for "
            "a label no clause of Definition 4.2 emits. This is the right "
            "behaviour and not a gap: an empty answer from a working pipeline "
            "is a report about the corpus, not a refusal to report. But it "
            "means the trichotomy's three values are not three outcomes of "
            "one procedure; two are verdict-driven and the third is reached "
            "only if the verdict space is later extended."
        ),
    }


EXPERIMENTS = [
    ("18_closure_cost_sweep.json", exp_18_closure_cost_sweep),
    ("19_budget_sweep.json", exp_19_budget_sweep),
    ("20_bounded_surface.json", exp_20_bounded_surface),
    ("21_counting_surface.json", exp_21_counting_surface),
    ("22_scoring_sweep.json", exp_22_scoring_sweep),
    ("23_blocker_grid.json", exp_23_blocker_grid),
]
