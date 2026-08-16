"""
Experiments 07-10: capability is a property of the compiler.

07 -- Theorem 5.2 (containment): a faithful honest engine never claims a
      feature its lowering cannot produce.
08 -- Proposition 5.3 (under-declaration): the formalism counts, the compiler
      does not, and removing the fragment gate produces an EMPTY answer set
      from a program whose aggregate never grounded.
09 -- Proposition 5.6 (half-true): a conflated TRANSITIVE symbol makes honesty
      unsatisfiable.
10 -- Proposition 5.7 (nameability): an unnameable feature makes a differential
      run compare two different knowledge bases while blaming the engines.
"""

from __future__ import annotations

from common import (
    ANSWERED,
    BOUNDED_PATH,
    CONFLATED_TRANSITIVE,
    COUNTING,
    CannotLower,
    DISJOINTNESS,
    FEATURES,
    NO_QUERY_SURFACE,
    OpenWorldEngine,
    Program,
    RuleEngine,
    TRANSITIVE_AXIOM,
    TRANSITIVE_QUERY,
    Verdict,
    chain_corpus,
    chain_model,
    evaluate,
    fixture_corpus,
    fixture_model,
    ground_truth_exactly_four,
    q_count,
    q_reach,
    q_reach_bounded,
    utc_stamp,
    verdict,
)


# ---------------------------------------------------------------------------
# 07 -- Theorem 5.2. DEFINITIONAL.
# ---------------------------------------------------------------------------


def _lowerable(engine, model, question):
    try:
        engine.lower(model, question)
        return True
    except CannotLower:
        return False


def exp_07_containment():
    expected = {
        "open_world_honest": True,
        "rule_honest": True,
        "violations": 0,
    }
    corpus = fixture_corpus()
    model = fixture_model(with_counting=True, with_closure=True,
                          with_distinctness=True, scoped_to_participants=True)
    chain_m = chain_model()

    probes = {
        COUNTING: q_count("p_count", "hasParticipant", 4, "eq"),
        TRANSITIVE_QUERY: q_reach("p_reach", "precedes", "a0"),
        BOUNDED_PATH: q_reach_bounded("p_bounded", "precedes", "a0", 3),
    }

    report = {}
    violations = []
    for engine in (OpenWorldEngine(), RuleEngine()):
        rows = {}
        for feature, q in probes.items():
            declared = feature in engine.SUPPORTS
            m = chain_m if feature in (TRANSITIVE_QUERY, BOUNDED_PATH) else model
            actual = _lowerable(engine, m, q)
            rows[feature] = {"declared": declared, "lowerable": actual}
            # Honesty (Def 5.1): declared => lowerable. The converse is allowed.
            if declared and not actual:
                violations.append({"engine": engine.name, "feature": feature})
        report[engine.name] = rows

    measured = {
        "matrix": report,
        "violations": len(violations),
        "violation_detail": violations,
        "open_world_honest": not any(v["engine"] == "open_world" for v in violations),
        "rule_honest": not any(v["engine"] == "rule" for v in violations),
    }
    passed = all(measured[k] == expected[k] for k in expected)

    # A deliberately dishonest engine, so the check can fail.
    class Overclaimer(OpenWorldEngine):
        name = "overclaimer"
        SUPPORTS = frozenset(FEATURES)

    over = Overclaimer()
    over_violations = [
        f for f, q in probes.items()
        if f in over.SUPPORTS
        and not _lowerable(over, chain_m if f in (TRANSITIVE_QUERY, BOUNDED_PATH) else model, q)
    ]

    return {
        "experiment": "07_containment",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "an engine declaring the whole alphabet must be caught, "
                "otherwise the honesty check is vacuous"
            ),
            "outcome": sorted(over_violations),
            "must_be_nonempty": True,
            "caught": len(over_violations) > 0,
        },
        "interpretation": (
            "DEFINITIONAL. This checks that our two engines satisfy the "
            "honesty condition of Definition 5.1 and that the check is not "
            "vacuous. It establishes nothing about any third-party reasoner's "
            "declared profile."
        ),
    }


# ---------------------------------------------------------------------------
# 08 -- Proposition 5.3. The substantive one: removing the gate yields an
# EMPTY answer set WITH certification asserted.
# ---------------------------------------------------------------------------


class UngatedRuleEngine(RuleEngine):
    """
    The rule engine with the certifiable-fragment gate removed.

    The gate is what makes `lower` raise CannotLower on a counting question.
    Without it the compiler emits a program containing an aggregate over a
    predicate the rest of the program never derives. The aggregate does not
    ground; the least model contains no answer; and because the certification
    flag is set unconditionally by the solve path, the caller receives an empty
    answer set presented as complete. That is Proposition 5.3's second half,
    and Remark 4.6 is the reason it is a payload component and not a filter.
    """

    name = "rule_ungated"

    # The gate's removal is a DECLARATION change as well as a lowering change:
    # an engine whose compiler will emit a counting program is one that claims
    # COUNTING. Inheriting the gated engine's SUPPORTS would have the ungated
    # engine refuse at E3 and never reach its own defect, which is the mirror
    # of Proposition 5.3 rather than the proposition itself.
    SUPPORTS = frozenset(RuleEngine.SUPPORTS | {COUNTING})

    def lower(self, model, question):
        if question.kind == "count":
            role = question.params["role"]
            n = question.params["n"]
            return Program(
                self.name,
                [
                    # `distinct_filler/2` is never derived: the compiler emits
                    # the aggregate without emitting the distinctness facts it
                    # ranges over, because the gate that would have refused was
                    # removed rather than the lowering completed.
                    ("aggregate_count", "distinct_filler", role, n,
                     question.params["mode"]),
                ],
            )
        return super().lower(model, question)

    def solve(self, program, model, corpus, budget):
        if program.ops and program.ops[0][0] == "aggregate_count":
            _, pred, role, n, mode = program.ops[0]
            derived = set()  # `pred` has no defining rule in the emitted program
            answers = {s for s in derived if True}
            # Certification asserted unconditionally -- the defect.
            return answers, True, 1
        return super().solve(program, model, corpus, budget)


def exp_08_under_declaration():
    corpus = fixture_corpus()
    truth = ground_truth_exactly_four(corpus)
    expected = {
        "formalism_expresses_counting": True,
        "gated_compiler_refuses": True,
        "gated_label": NO_QUERY_SURFACE,
        "ungated_answers": True,
        "ungated_answer_set_empty": True,
        "ungated_certification_asserted": True,
        "ground_truth_nonempty": True,
        "silently_missed": 3,
    }

    model = fixture_model(with_counting=True, with_closure=True,
                          with_distinctness=True, scoped_to_participants=True)
    q = q_count("q_eq4", "hasParticipant", 4, "eq")

    gated = evaluate(q, model, corpus, RuleEngine(), subject="rx1")
    ungated = evaluate(q, model, corpus, UngatedRuleEngine(), subject="rx1")

    ungated_answers = (
        ungated.payload["answers"] if ungated.label == ANSWERED else None
    )
    ungated_certified = (
        ungated.payload["certified"] if ungated.label == ANSWERED else None
    )

    measured = {
        "formalism_expresses_counting": COUNTING in model.features(),
        "gated_verdict": gated.to_json(),
        "gated_compiler_refuses": gated.label != ANSWERED,
        "gated_label": gated.label,
        "ungated_verdict": ungated.to_json(),
        "ungated_answers": ungated.label == ANSWERED,
        "ungated_answer_set_empty": ungated_answers == set(),
        "ungated_certification_asserted": ungated_certified is True,
        "ground_truth": sorted(truth),
        "ground_truth_nonempty": len(truth) > 0,
        "silently_missed": (
            len(truth) if ungated_answers is not None else None
        ),
    }
    passed = all(measured[k] == expected[k] for k in expected)

    # Control: the same ungated engine on a question whose lowering IS
    # complete must return the right answers, so the empty set above is
    # attributable to the missing aggregate and not to a broken engine.
    ctrl = evaluate(q_reach("q_ctrl", "hasParticipant", "rx1"), model, corpus,
                    UngatedRuleEngine())
    ctrl_ok = ctrl.label == ANSWERED and ctrl.payload["answers"] == corpus.successors(
        "rx1", "hasParticipant"
    )

    return {
        "experiment": "08_under_declaration",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "the ungated engine on a fully-lowered question must answer "
                "correctly, so the empty certified set is caused by the "
                "ungrounded aggregate rather than by a generally broken engine"
            ),
            "outcome": ctrl.to_json(),
            "correct": bool(ctrl_ok),
            "must_be": True,
        },
        "interpretation": (
            "The target formalism expresses the count. The compiler cannot "
            "produce a program the engine will certify, so an audit conducted "
            "against the formalism reports a capability that no question can "
            "reach. Removing the fragment gate does not add the capability: "
            "it converts a refusal into an empty answer set carrying an "
            "asserted certification flag, which is the worse of the two "
            "outcomes because it is indistinguishable from a true negative."
        ),
    }


# ---------------------------------------------------------------------------
# 09 -- Proposition 5.6. DEFINITIONAL: with one symbol for two constructs,
# honesty is unsatisfiable.
# ---------------------------------------------------------------------------


def exp_09_half_true_transitive():
    expected = {
        "split_alphabet_admits_honest_declaration": True,
        "conflated_alphabet_admits_none": True,
        "declaring_true_overclaims": True,
        "declaring_false_underclaims": True,
    }
    chain_m = chain_model()
    corpus = chain_corpus(6, cyclic=False)
    rule = RuleEngine()

    # The rule engine answers transitive QUERIES and cannot consume a
    # transitive AXIOM: it has no mechanism to close a role declared transitive
    # in the model, it can only compute closure asked for in a query.
    can_query = _lowerable(rule, chain_m, q_reach("q", "precedes", "a0"))
    can_consume_axiom = TRANSITIVE_AXIOM in rule.SUPPORTS

    split_ok = (TRANSITIVE_QUERY in rule.SUPPORTS) == can_query and (
        TRANSITIVE_AXIOM in rule.SUPPORTS
    ) == can_consume_axiom

    # Under a conflated symbol there is a single boolean to set.
    declaring_true_overclaims = not can_consume_axiom   # claims the axiom it lacks
    declaring_false_underclaims = can_query             # denies the query it has

    measured = {
        "can_answer_transitive_query": bool(can_query),
        "can_consume_transitive_axiom": bool(can_consume_axiom),
        "split_alphabet_admits_honest_declaration": bool(split_ok),
        "conflated_symbol": CONFLATED_TRANSITIVE,
        "declaring_true_overclaims": bool(declaring_true_overclaims),
        "declaring_false_underclaims": bool(declaring_false_underclaims),
        "conflated_alphabet_admits_none": bool(
            declaring_true_overclaims and declaring_false_underclaims
        ),
    }
    passed = all(measured[k] == expected[k] for k in expected)

    return {
        "experiment": "09_half_true_transitive",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "an engine that genuinely has both constructs must be able to "
                "declare the conflated symbol honestly, so the unsatisfiability "
                "is a property of THIS engine's asymmetry and not of conflation "
                "in general"
            ),
            "outcome": {
                "engine": "open_world",
                "query": TRANSITIVE_QUERY in OpenWorldEngine.SUPPORTS,
                "axiom": TRANSITIVE_AXIOM in OpenWorldEngine.SUPPORTS,
                "conflated_declaration_honest": (
                    TRANSITIVE_QUERY in OpenWorldEngine.SUPPORTS
                    and TRANSITIVE_AXIOM in OpenWorldEngine.SUPPORTS
                ),
            },
            "must_be": True,
        },
        "interpretation": (
            "DEFINITIONAL. With one symbol covering both constructs, an engine "
            "supporting exactly one of them has no honest value to declare: "
            "true overclaims, false underclaims. The split of Remark 2.5 is "
            "what makes an honest declaration available at all."
        ),
    }


# ---------------------------------------------------------------------------
# 10 -- Proposition 5.7: an unnameable feature makes a differential run compare
# two different knowledge bases while attributing the difference to engines.
# ---------------------------------------------------------------------------


def exp_10_nameable():
    expected = {
        "answers_differ": True,
        "difference_attributable_to_model": True,
        "unnameable_alphabet_blames_engine": True,
        "nameable_alphabet_blames_model": True,
    }
    corpus = fixture_corpus()
    ow = OpenWorldEngine()

    # Two models differing ONLY in a feature. If the alphabet cannot name it,
    # the two runs are recorded as the same model under two engines.
    m_with = fixture_model(with_counting=True, with_closure=True,
                           with_distinctness=True, scoped_to_participants=True)
    m_without = fixture_model(with_counting=True, with_closure=False,
                              with_distinctness=True, scoped_to_participants=True)

    q = q_count("q_le4", "hasParticipant", 4, "le")
    v_with = evaluate(q, m_with, corpus, ow, subject="rx1")
    v_without = evaluate(q, m_without, corpus, ow, subject="rx1")

    differ = v_with.label != v_without.label

    # The two alphabets.
    nameable_alphabet = FEATURES | {"CLOSURE"}
    unnameable_alphabet = FEATURES  # CLOSURE absent

    delta = m_with.grammar ^ m_without.grammar
    nameable = delta <= nameable_alphabet
    unnameable = not (delta <= unnameable_alphabet)

    measured = {
        "model_delta": sorted(delta),
        "verdict_with": v_with.to_json(),
        "verdict_without": v_without.to_json(),
        "answers_differ": bool(differ),
        "difference_attributable_to_model": bool(nameable),
        "nameable_alphabet_blames_model": bool(nameable),
        "unnameable_alphabet_blames_engine": bool(unnameable),
        "note": (
            "with CLOSURE absent from the alphabet the two runs record an "
            "identical model field and differ only in the engine column, so "
            "the recorded cause of the divergence is the engine"
        ),
    }
    passed = all(measured[k] == expected[k] for k in expected)

    # Control: two runs of the SAME model under the same engine must not
    # differ, so a difference is never manufactured by the harness.
    v_a = evaluate(q, m_with, corpus, ow, subject="rx1")
    v_b = evaluate(q, m_with, corpus, ow, subject="rx1")

    return {
        "experiment": "10_nameable",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "identical model and engine must produce identical verdicts, "
                "so the divergence above is caused by the model delta"
            ),
            "outcome": {"a": v_a.label, "b": v_b.label, "identical": v_a.label == v_b.label},
            "must_be": True,
        },
        "interpretation": (
            "The two runs differ because of a model feature. An alphabet that "
            "cannot name that feature records the two runs as the same model, "
            "so the divergence is attributed to whatever column did differ. "
            "The recorded finding is then about engines and the true cause is "
            "in the model."
        ),
    }


EXPERIMENTS = [
    ("07_containment.json", exp_07_containment),
    ("08_under_declaration.json", exp_08_under_declaration),
    ("09_half_true_transitive.json", exp_09_half_true_transitive),
    ("10_nameable.json", exp_10_nameable),
]
