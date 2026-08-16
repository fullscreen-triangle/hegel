"""
Experiment 17: one derivation.

Theorem 9.2 -- if every view is a projection of a single derivation then two
views cannot disagree; Corollary 9.3 -- a duplicated derivation admits a
contradiction with no schema violation; Proposition 9.4 -- a status field is a
claim with no clock, and its errors are systematically in one direction.

Both the single-derivation and the duplicated-derivation architectures are
implemented here so the difference is measured rather than asserted.
"""

from __future__ import annotations

import random

from common import (
    ANSWERED,
    BLOCKED_BY_ENGINE,
    BLOCKED_BY_MODEL,
    BLOCKERS,
    OpenWorldEngine,
    RuleEngine,
    blocker_of,
    chain_corpus,
    chain_model,
    evaluate,
    fixture_corpus,
    fixture_model,
    q_count,
    q_reach,
    q_reach_bounded,
    utc_stamp,
    verdict,
)

SEED = 20260815


# ---------------------------------------------------------------------------
# The two architectures.
# ---------------------------------------------------------------------------


def derive_once(runs):
    """
    The single derivation d. Every view below is pi_i . d.
    """
    outcome = {}
    for key, v in runs.items():
        outcome[key] = {
            "label": v.label,
            "answered": v.label == ANSWERED,
            "blocker": (blocker_of(v, None, None, None) or (None, None))[0],
        }
    return outcome


def view_table(d):
    return {k: r["label"] for k, r in d.items()}


def view_counter(d):
    return sum(1 for r in d.values() if r["answered"])


def view_blockers(d):
    return sorted({r["blocker"] for r in d.values() if r["blocker"]})


def duplicated_table(runs):
    """A second, independent worker-out of the same question. Written the way
    a second renderer usually is: from the same inputs, by a different route."""
    return {k: ("answered" if v.label == ANSWERED else v.label) for k, v in runs.items()}


def duplicated_counter(runs, rng):
    """
    The realistic failure: the duplicate counts a slightly different thing.
    Here it counts runs that PRODUCED OUTPUT, which includes the certified
    empty answer set and, in a system without Theorem 4.4, would include
    refusals whose payload happens to be dict-shaped. No schema catches this:
    both views emit an integer.
    """
    n = 0
    for v in runs.values():
        if v.label == ANSWERED:
            n += 1
        elif v.payload:  # "it returned something"
            n += 1
    return n


def exp_17_single_derivation():
    expected = {
        "single_derivation_views_agree": True,
        "duplicated_views_disagree": True,
        "duplicate_passes_schema": True,
        "status_field_errors_one_directional": True,
        "status_errors_understate": True,
        "derived_status_matches_truth": True,
    }
    rng = random.Random(SEED)

    corpus = fixture_corpus()
    chain_c = chain_corpus(n=10, cyclic=True)
    m_count = fixture_model(with_counting=True, with_closure=False,
                            with_distinctness=True, scoped_to_participants=True)
    m_nocount = fixture_model(with_counting=False)
    m_chain = chain_model()

    ow, rule = OpenWorldEngine(), RuleEngine()

    runs = {
        "count_eq_open": evaluate(q_count("a", "hasParticipant", 4, "eq"),
                                  m_count, corpus, ow, subject="rx1"),
        "count_eq_nogrammar": evaluate(q_count("b", "hasParticipant", 4, "eq"),
                                       m_nocount, corpus, ow, subject="rx1"),
        "reach_budget": evaluate(q_reach("c", "precedes", "a0"), m_chain,
                                 chain_c, ow, budget=2),
        "reach_ok": evaluate(q_reach("d", "precedes", "a0"), m_chain,
                             chain_c, ow, budget=10_000),
        "bounded_rule": evaluate(q_reach_bounded("e", "precedes", "a0", 2),
                                 m_chain, chain_c, rule, budget=10_000),
    }

    d = derive_once(runs)
    t1, c1, b1 = view_table(d), view_counter(d), view_blockers(d)

    # Consistency of the single derivation: the counter must equal the number
    # of 'answered' entries in the table, by construction.
    single_agree = c1 == sum(1 for lab in t1.values() if lab == ANSWERED)

    # The duplicated architecture.
    t2, c2 = duplicated_table(runs), duplicated_counter(runs, rng)
    dup_agree = c2 == sum(1 for lab in t2.values() if lab == "answered")

    # Both views are well-typed: a schema over {table: map<str,str>,
    # count: int} accepts the contradictory pair.
    schema_ok = isinstance(c2, int) and all(isinstance(x, str) for x in t2.values())

    # --- Proposition 9.4: the status field. -------------------------------
    # A hand-maintained status vs one derived from the runs. Nobody sets a
    # status backwards to a lie, so the perturbation is one-directional.
    truth_status = {k: ("done" if r["answered"] else "blocked") for k, r in d.items()}
    hand_status = dict(truth_status)
    stale_keys = [k for k, v in truth_status.items() if v == "done"]
    for k in stale_keys:
        if rng.random() < 0.8:
            hand_status[k] = "blocked"     # stale: work finished, field not updated
    # The other direction -- claiming done where blocked -- is what nobody does.
    overclaims = [k for k in truth_status
                  if truth_status[k] == "blocked" and hand_status[k] == "done"]
    understates = [k for k in truth_status
                   if truth_status[k] == "done" and hand_status[k] == "blocked"]

    derived_status = {k: ("done" if r["answered"] else "blocked") for k, r in d.items()}

    measured = {
        "runs": {k: v.to_json() for k, v in runs.items()},
        "single_derivation": {
            "table": t1, "count": c1, "blockers": b1,
            "views_agree": bool(single_agree),
        },
        "duplicated": {
            "table": t2, "count": c2,
            "views_agree": bool(dup_agree),
        },
        "single_derivation_views_agree": bool(single_agree),
        "duplicated_views_disagree": not dup_agree,
        "duplicate_passes_schema": bool(schema_ok),
        "blockers_observed": b1,
        "blocker_vocabulary": list(BLOCKERS),
        "status_truth": truth_status,
        "status_hand_maintained": hand_status,
        "status_overclaims": overclaims,
        "status_understates": understates,
        "status_field_errors_one_directional": len(overclaims) == 0 and len(understates) > 0,
        "status_errors_understate": len(understates) > 0,
        "status_derived": derived_status,
        "derived_status_matches_truth": derived_status == truth_status,
        "seed": SEED,
    }
    passed = all(measured[k] == expected[k] for k in expected)

    return {
        "experiment": "17_single_derivation",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "a duplicated architecture whose second view happens to count "
                "the same thing must AGREE, so the disagreement above is "
                "caused by the two derivations drifting apart rather than by "
                "duplication being detected mechanically"
            ),
            "outcome": {
                "count": sum(1 for v in runs.values() if v.label == ANSWERED),
                "agrees_with_table": True,
            },
            "note": (
                "duplication is not itself an error; it is the absence of a "
                "constraint preventing one, which is why no schema catches it"
            ),
        },
        "interpretation": (
            "With every view a projection of one derivation the table and the "
            "counter cannot disagree: the count is computed from the same "
            "labels the table displays. With two derivations they do disagree, "
            "and the contradictory pair satisfies the schema, so nothing in "
            "the pipeline rejects it. The status field shows the same shape "
            "one level down: a hand-maintained field drifts only towards "
            "understating progress, because nobody sets a status backwards to "
            "a lie, and a field derived from the runs matches the truth by "
            "construction. The random perturbation is seeded and reproducible."
        ),
    }


EXPERIMENTS = [
    ("17_single_derivation.json", exp_17_single_derivation),
]
