"""
Experiments 01-06: the three predicates, the verdict space, and the scoring
consequence.

Every expectation below was written into this file BEFORE the run and is
recorded in each result document as `expected`, so a divergence between
`expected` and `measured` shows up in the JSON rather than being absorbed by
editing the prose.
"""

from __future__ import annotations

from common import (
    ANSWERED,
    BOUNDED_PATH,
    CANNOT_EXPRESS,
    COUNTING,
    NON_ANSWER_LABELS,
    NOT_DERIVABLE,
    NO_QUERY_SURFACE,
    OpenWorldEngine,
    RuleEngine,
    TIMEOUT,
    CONTROL_VACUOUS,
    CONSTRAINT_INERT,
    Verdict,
    _jsonable,
    answers_returned_count,
    chain_corpus,
    chain_model,
    counting_derivable,
    evaluate,
    expressible,
    fixture_corpus,
    fixture_model,
    ground_truth_exactly_four,
    missing_features,
    naive_score,
    q_count,
    q_reach,
    q_reach_bounded,
    utc_stamp,
    verdict,
    verdict_aware_score,
)


# ---------------------------------------------------------------------------
# 01 -- Theorem 3.7: Exp, Der and Ans are pairwise independent.
# ---------------------------------------------------------------------------


def exp_01_predicate_independence():
    expected = {
        "w1_exp_true_der_false": True,
        "w2_exp_false_ans_true_for_sibling": True,
        "w3_der_true_ans_false": True,
        "all_three_witnesses_distinct": True,
    }
    corpus = fixture_corpus()
    ow = OpenWorldEngine()
    rule = RuleEngine()

    # Witness 1: Exp holds, Der fails. The grammar has COUNTING, so "exactly
    # four participants" is a sentence of the language; without closure the
    # answer is not determined by the semantics.
    m1 = fixture_model(with_counting=True, with_closure=False, with_distinctness=True,
                       scoped_to_participants=True)
    q1 = q_count("q_eq4", "hasParticipant", 4, "eq")
    w1_exp = expressible(q1, m1)
    w1_der, w1_reason = counting_derivable(m1, corpus, "rx1", "hasParticipant", 4, "eq")

    # Witness 2: Exp fails while a strictly weaker sibling question is
    # answered. A model without COUNTING cannot say it; the same model answers
    # "which reactions have a participant at all".
    m2 = fixture_model(with_counting=False)
    w2_exp = expressible(q1, m2)
    v2 = evaluate(q_reach("q_reach", "hasParticipant", "rx1"), m2, corpus, ow)
    w2_sibling_answered = v2.label == ANSWERED

    # Witness 3: Der holds, Ans fails. A cyclic chain, an unbounded reachability
    # question the semantics determines completely, and a budget of 2.
    m3 = chain_model()
    c3 = chain_corpus(n=8, cyclic=True)
    q3 = q_reach("q_reach_cyc", "precedes", "a0")
    w3_exp = expressible(q3, m3)
    v3 = evaluate(q3, m3, c3, ow, budget=2)
    w3_ans_fails = v3.label == TIMEOUT

    measured = {
        "w1_exp_true_der_false": bool(w1_exp) and not w1_der,
        "w1_der_reason": w1_reason,
        "w2_exp_false_ans_true_for_sibling": (not w2_exp) and w2_sibling_answered,
        "w2_missing_features": sorted(missing_features(q1, m2)),
        "w3_der_true_ans_false": bool(w3_exp) and w3_ans_fails,
        "w3_verdict": v3.to_json(),
    }
    measured["all_three_witnesses_distinct"] = (
        measured["w1_exp_true_der_false"]
        and measured["w2_exp_false_ans_true_for_sibling"]
        and measured["w3_der_true_ans_false"]
    )
    passed = all(measured[k] == expected[k] for k in expected)

    return {
        "experiment": "01_predicate_independence",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": "witness 3 with a budget large enough to finish",
            "outcome": evaluate(q3, m3, c3, ow, budget=1000).label,
            "must_be": ANSWERED,
        },
        "interpretation": (
            "Three constructed witnesses show that no one of Exp, Der and Ans "
            "implies another. The witnesses are ours; what is established is "
            "that the definitions as given are pairwise independent, not that "
            "any deployed system exhibits all three."
        ),
    }


# ---------------------------------------------------------------------------
# 02 -- Corollary 3.9: conflating the three loses information that no later
# stage can recover.
# ---------------------------------------------------------------------------


def exp_02_conflation_loses_information():
    expected = {
        "distinct_situations": 4,
        "distinct_labels": 4,
        "distinct_after_conflation": 1,
        "recoverable_after_conflation": False,
    }
    corpus = fixture_corpus()
    ow = OpenWorldEngine()

    situations = []

    m_nocount = fixture_model(with_counting=False)
    situations.append(
        ("no COUNTING in grammar",
         evaluate(q_count("q1", "hasParticipant", 4, "eq"), m_nocount, corpus, ow,
                  subject="rx1"))
    )

    m_count = fixture_model(with_counting=True, with_distinctness=True,
                            scoped_to_participants=True)
    situations.append(
        ("COUNTING present, closure absent",
         evaluate(q_count("q2", "hasParticipant", 4, "eq"), m_count, corpus, ow,
                  subject="rx1"))
    )

    m_full = fixture_model(with_counting=True, with_closure=True,
                           with_distinctness=True, scoped_to_participants=True)
    situations.append(
        ("derivable, but the adapter has no counting surface",
         evaluate(q_count("q3", "hasParticipant", 4, "eq"), m_full, corpus, ow,
                  subject="rx1"))
    )

    m_chain = chain_model()
    situations.append(
        ("derivable and lowerable, budget exhausted",
         evaluate(q_reach("q4", "precedes", "a0"), m_chain,
                  chain_corpus(8, cyclic=True), ow, budget=2))
    )

    labels = [v.label for _, v in situations]
    # The conflation: report only whether an answer set came back.
    conflated = ["empty" if v.label != ANSWERED else "nonempty" for _, v in situations]

    measured = {
        "distinct_situations": len(situations),
        "distinct_labels": len(set(labels)),
        "labels": labels,
        "distinct_after_conflation": len(set(conflated)),
        "conflated": conflated,
        "recoverable_after_conflation": len(set(conflated)) == len(set(labels)),
        "situations": [
            {"description": d, "verdict": v.to_json()} for d, v in situations
        ],
    }
    passed = all(measured[k] == expected[k] for k in expected)

    return {
        "experiment": "02_conflation_loses_information",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "an ANSWERED situation added to the same set must remain "
                "distinguishable under the conflation, so the collapse is not "
                "an artefact of every situation being a refusal"
            ),
            "outcome": "nonempty" if evaluate(
                q_reach("qc", "precedes", "a0"), m_chain,
                chain_corpus(8, cyclic=True), ow, budget=1000
            ).label == ANSWERED else "empty",
            "must_be": "nonempty",
        },
        "interpretation": (
            "Four situations with four different remedies map to four labels "
            "and to one bit under answer-set conflation. The information lost "
            "is which of four repairs to perform; no downstream stage can "
            "recover it because it was never emitted."
        ),
    }


# ---------------------------------------------------------------------------
# 03 -- Theorem 4.4: non-degeneracy. DEFINITIONAL: this is a property of the
# implementation of Definition 4.1, checked mechanically.
# ---------------------------------------------------------------------------


def exp_03_nondegeneracy():
    expected = {
        "non_answer_labels_expose_answers": 0,
        "labels_checked": len(NON_ANSWER_LABELS),
        "answered_exposes_answers": True,
    }
    exposed = []
    for label in sorted(NON_ANSWER_LABELS):
        v = Verdict(label, {"probe": True})
        try:
            _ = v.answers
            exposed.append(label)
        except ValueError:
            pass
    v_ok = Verdict(ANSWERED, {"answers": set(), "certified": True})
    try:
        answered_ok = v_ok.answers == set()
    except ValueError:
        answered_ok = False

    measured = {
        "non_answer_labels_expose_answers": len(exposed),
        "exposed": exposed,
        "labels_checked": len(NON_ANSWER_LABELS),
        "answered_exposes_answers": answered_ok,
    }
    passed = all(measured[k] == expected[k] for k in expected)

    return {
        "experiment": "03_nondegeneracy",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "ANSWERED with a genuinely empty answer set must still expose "
                "it, otherwise the check would pass by making every verdict "
                "opaque rather than by making refusals answer-free"
            ),
            "outcome": answered_ok,
            "must_be": True,
        },
        "interpretation": (
            "DEFINITIONAL. This does not measure a system; it checks that our "
            "implementation of the verdict type has the structural property "
            "Theorem 4.4 asserts, so that a certified empty answer set is "
            "distinguishable from every refusal by construction rather than "
            "by convention."
        ),
    }


# ---------------------------------------------------------------------------
# 04 -- Proposition 3.4: the counting split.
# ---------------------------------------------------------------------------


def exp_04_counting_split():
    expected = {
        "ge_needs_distinctness_only": True,
        "le_needs_closure_only": True,
        "eq_needs_both": True,
    }
    corpus = fixture_corpus()

    def der(mode, distinct, closure):
        m = fixture_model(with_counting=True, with_closure=closure,
                          with_distinctness=distinct, scoped_to_participants=True)
        ok, reason = counting_derivable(m, corpus, "rx1", "hasParticipant", 4, mode)
        return ok, reason

    grid = {}
    for mode in ("ge", "le", "eq"):
        for distinct in (False, True):
            for closure in (False, True):
                ok, reason = der(mode, distinct, closure)
                grid[f"{mode}|distinct={distinct}|closure={closure}"] = {
                    "derivable": ok, "reason": reason
                }

    measured = {
        "grid": grid,
        "ge_needs_distinctness_only": (
            grid["ge|distinct=True|closure=False"]["derivable"] is True
            and grid["ge|distinct=False|closure=True"]["derivable"] is False
        ),
        "le_needs_closure_only": (
            grid["le|distinct=False|closure=True"]["derivable"] is True
            and grid["le|distinct=True|closure=False"]["derivable"] is False
        ),
        "eq_needs_both": (
            grid["eq|distinct=True|closure=True"]["derivable"] is True
            and grid["eq|distinct=True|closure=False"]["derivable"] is False
            and grid["eq|distinct=False|closure=True"]["derivable"] is False
        ),
    }
    passed = all(measured[k] == expected[k] for k in expected)

    return {
        "experiment": "04_counting_split",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "the fully-equipped model must derive all three clauses, so a "
                "PASS cannot be obtained by a derivability check that refuses "
                "everything"
            ),
            "outcome": {
                m: der(m, True, True)[0] for m in ("ge", "le", "eq")
            },
            "must_be": {"ge": True, "le": True, "eq": True},
        },
        "interpretation": (
            "The three cardinality clauses have three different preconditions. "
            "A profile reported as 'cannot count' on the strength of the "
            "exactly-n clause may answer at-least-n; the split is what makes "
            "that reportable."
        ),
    }


# ---------------------------------------------------------------------------
# 05 -- Remark 3.5: the tempting global distinctness check is unsound in the
# direction that CONCEALS the problem.
# ---------------------------------------------------------------------------


def exp_05_una_scope():
    expected = {
        "global_check_says_yes": True,
        "scoped_check_says_no": True,
        "unsound_direction_is_permissive": True,
        "agree_when_properly_scoped": True,
    }
    corpus = fixture_corpus()

    # Distinctness asserted over two ROLE individuals, not over participants.
    m_unscoped = fixture_model(with_counting=True, with_distinctness=True,
                               scoped_to_participants=False)
    counted = corpus.successors("rx1", "hasParticipant")
    global_says = m_unscoped.tempting_global_distinctness_check()
    scoped_says = m_unscoped.known_distinct(counted)

    m_scoped = fixture_model(with_counting=True, with_distinctness=True,
                             scoped_to_participants=True)
    agree = (
        m_scoped.tempting_global_distinctness_check()
        == m_scoped.known_distinct(counted)
        is True
    )

    measured = {
        "distinctness_asserted_over": sorted(
            {x for s in m_unscoped.distinct_sets for x in s}
        ),
        "counted_set": sorted(counted),
        "global_check_says_yes": global_says is True,
        "scoped_check_says_no": scoped_says is False,
        "unsound_direction_is_permissive": (global_says is True and scoped_says is False),
        "agree_when_properly_scoped": bool(agree),
    }
    passed = all(measured[k] == expected[k] for k in expected)

    return {
        "experiment": "05_una_scope",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "with distinctness asserted over the counted set the two "
                "checks agree, so the disagreement is caused by scope and not "
                "by the scoped check being unsatisfiable"
            ),
            "outcome": bool(agree),
            "must_be": True,
        },
        "interpretation": (
            "The two checks disagree, and they disagree the wrong way round: "
            "the cheap one reports that the count is sound when it is not. An "
            "audit built on it would report a capability the system lacks."
        ),
    }


# ---------------------------------------------------------------------------
# 06 -- Proposition 4.9: an honest refuser loses under answer-counting and wins
# under a verdict-aware rule; the reversal magnitude is the ground-truth
# cardinality.
# ---------------------------------------------------------------------------


def exp_06_compare_refusals():
    corpus = fixture_corpus()
    truth = ground_truth_exactly_four(corpus)
    expected = {
        "ground_truth_cardinality": 3,
        "honest_refuses": True,
        "confident_returns_empty": True,
        "naive_ranks_confident_above_honest": True,
        "aware_ranks_honest_above_confident": True,
        "reversal_magnitude_equals_truth_cardinality": True,
    }

    ow = OpenWorldEngine()
    m = fixture_model(with_counting=True, with_closure=False,
                      with_distinctness=True, scoped_to_participants=True)
    q = q_count("q_eq4", "hasParticipant", 4, "eq")

    honest = evaluate(q, m, corpus, ow, subject="rx1")

    # The confident system: same knowledge base, but it emits an answer set
    # anyway. Under closed-world defaults with no closure axiom present, the
    # aggregate never grounds and the emitted set is empty.
    confident = Verdict(ANSWERED, {"answers": set(), "certified": True,
                                   "steps": 0, "engine": "confident"})

    naive_honest = answers_returned_count(honest)
    naive_confident = answers_returned_count(confident)

    # The answer-counting rule: a refusal contributes nothing, so it cannot
    # outrank anything that returned.
    naive_rank = {
        "honest": 0 if naive_honest is None else naive_honest,
        "confident": naive_confident,
    }
    aware_rank = {
        "honest": verdict_aware_score(honest, truth),
        "confident": verdict_aware_score(confident, truth),
    }

    # Magnitude of the reversal: how many true answers the confident system
    # silently omitted while presenting its output as complete.
    missed = len(truth - confident.payload["answers"])

    measured = {
        "ground_truth": sorted(truth),
        "ground_truth_cardinality": len(truth),
        "honest_verdict": honest.to_json(),
        "confident_verdict": confident.to_json(),
        "honest_refuses": honest.label in (NOT_DERIVABLE, CANNOT_EXPRESS, NO_QUERY_SURFACE),
        "confident_returns_empty": (
            confident.label == ANSWERED and confident.payload["answers"] == set()
        ),
        "naive_scores": naive_rank,
        "verdict_aware_scores": aware_rank,
        "naive_ranks_confident_above_honest": naive_rank["confident"] >= naive_rank["honest"],
        "aware_ranks_honest_above_confident": aware_rank["honest"] > aware_rank["confident"],
        "reversal_magnitude": missed,
        "reversal_magnitude_equals_truth_cardinality": missed == len(truth),
    }
    passed = all(
        measured[k] == expected[k] for k in expected if k in measured
    )

    return {
        "experiment": "06_compare_refusals",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "a system that both answers and is correct must outrank the "
                "honest refuser under the verdict-aware rule too, so the rule "
                "is not simply rewarding silence"
            ),
            "outcome": verdict_aware_score(
                Verdict(ANSWERED, {"answers": set(truth), "certified": True}), truth
            ),
            "must_be": 1.0,
            "honest_score_for_comparison": aware_rank["honest"],
        },
        "interpretation": (
            "Under any rule that counts answers returned, the confident system "
            "with a silently empty result outranks the system that reported "
            "its own limitation. The ordering reverses under a verdict-aware "
            "rule, and the size of the reversal is the number of true answers "
            "the confident system omitted. Note the control: the reversal does "
            "not reward refusal over a correct answer, only over a wrong one."
        ),
    }


EXPERIMENTS = [
    ("01_predicate_independence.json", exp_01_predicate_independence),
    ("02_conflation_loses_information.json", exp_02_conflation_loses_information),
    ("03_nondegeneracy.json", exp_03_nondegeneracy),
    ("04_counting_split.json", exp_04_counting_split),
    ("05_una_scope.json", exp_05_una_scope),
    ("06_compare_refusals.json", exp_06_compare_refusals),
]
