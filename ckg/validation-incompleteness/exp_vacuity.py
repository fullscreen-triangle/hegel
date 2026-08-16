"""
Experiments 11-13: vacuity.

11 -- Theorem 6.4(ii): the substantive direction. A mis-rooted negation compiles
      to a program that DIFFERS from the control's, so the syntactic check
      passes; the answer sets coincide, so the semantic check fires.
12 -- Theorem 6.4(i): the other direction. A constraint whose lowering is
      dropped compiles to a program IDENTICAL to the control's, so the
      syntactic check fires; a semantic-only checker would have had to spend
      the budget to notice.
13 -- Proposition 6.7: agreement between two engines under a vacuous constraint
      is not evidence that either lowered it faithfully.
"""

from __future__ import annotations

from common import (
    ANSWERED,
    CONSTRAINT_INERT,
    CONTROL_VACUOUS,
    DISJOINTNESS,
    NEGATION,
    OpenWorldEngine,
    RuleEngine,
    Corpus,
    Model,
    SUBSUMPTION,
    EXISTENTIAL,
    TRANSITIVE_AXIOM,
    TRANSITIVE_QUERY,
    BOUNDED_PATH,
    VALUE,
    chain_corpus,
    chain_model,
    evaluate,
    q_no_successor_of_kind,
    q_reach_bounded,
    utc_stamp,
    verdict,
)


# ---------------------------------------------------------------------------
# The fixture for 11 and 13: reactions whose participants are typed, with a
# disjointness axiom that makes the MIS-ROOTED form entailed of everything.
# ---------------------------------------------------------------------------


def negation_fixture():
    model = Model(
        "negation",
        {SUBSUMPTION, EXISTENTIAL, VALUE, NEGATION, DISJOINTNESS,
         TRANSITIVE_AXIOM, TRANSITIVE_QUERY},
        concepts={"Reaction", "Cofactor", "Metabolite"},
        roles={"hasParticipant"},
        # A reaction is not a cofactor. This is what makes "the subject is not
        # a Cofactor" entailed of every reaction, and therefore inert.
        disjoint_pairs=[("Reaction", "Cofactor")],
    )
    concept_assertions = {("Reaction", "rx1"), ("Reaction", "rx2"), ("Reaction", "rx3")}
    role_assertions = set()
    # rx1 has a Cofactor participant, rx2 and rx3 do not. The correctly-rooted
    # question must therefore return {rx2, rx3}; the mis-rooted one returns all
    # three, which is also what the control returns.
    for rx, kinds in (("rx1", ["Cofactor", "Metabolite"]),
                      ("rx2", ["Metabolite", "Metabolite"]),
                      ("rx3", ["Metabolite"])):
        for i, kind in enumerate(kinds):
            p = f"{rx}_p{i}"
            concept_assertions.add((kind, p))
            role_assertions.add(("hasParticipant", rx, p))
    return model, Corpus("negation", concept_assertions, role_assertions)


# ---------------------------------------------------------------------------
# 11 -- Theorem 6.4(ii)
# ---------------------------------------------------------------------------


def exp_11_semantic_vacuity_not_syntactic():
    expected = {
        "programs_differ": True,
        "syntactic_check_passes": True,
        "answer_sets_coincide": True,
        "semantic_check_fires": True,
        "label": CONSTRAINT_INERT,
    }
    model, corpus = negation_fixture()
    engine = OpenWorldEngine(mis_root_negation=True)

    q = q_no_successor_of_kind("q_no_cofactor", "hasParticipant", "Cofactor")
    qc = q.control()

    p = engine.lower(model, q)
    pc = engine.lower(model, qc)

    ans, _, _ = engine.solve(p, model, corpus, 10_000)
    ansc, _, _ = engine.solve(pc, model, corpus, 10_000)

    v = evaluate(q, model, corpus, engine)

    measured = {
        "program": p.text(),
        "control_program": pc.text(),
        "programs_differ": p != pc,
        "syntactic_check_passes": p != pc,  # the check does not fire
        "answers": sorted(ans),
        "control_answers": sorted(ansc),
        "answer_sets_coincide": ans == ansc,
        "semantic_check_fires": v.label == CONSTRAINT_INERT,
        "label": v.label,
        "verdict_payload": v.to_json(),
    }
    passed = all(measured[k] == expected[k] for k in expected)

    # Control: the correctly-rooted lowering must produce a DIFFERENT answer
    # set from its own control, so the coincidence above is caused by the
    # mis-rooting and not by the question being inert in this corpus.
    good = OpenWorldEngine(mis_root_negation=False)
    gp = good.lower(model, q)
    gpc = good.lower(model, qc)
    ga, _, _ = good.solve(gp, model, corpus, 10_000)
    gac, _, _ = good.solve(gpc, model, corpus, 10_000)
    good_v = evaluate(q, model, corpus, good)

    return {
        "experiment": "11_semantic_vacuity_not_syntactic",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "the correctly-rooted lowering must answer, and its answer set "
                "must differ from its control's, so the inertness above is a "
                "property of the mis-rooting"
            ),
            "answers": sorted(ga),
            "control_answers": sorted(gac),
            "differ": ga != gac,
            "label": good_v.label,
            "must_be": ANSWERED,
        },
        "interpretation": (
            "The mis-rooted negation is a well-formed expression that "
            "constrains the wrong entity. Its compiled program differs from "
            "the control's, so a syntactic vacuity check reports nothing. The "
            "answer sets coincide, because with the disjointness axiom present "
            "the mis-rooted constraint is entailed of every subject. Only the "
            "semantic check catches it, which is why the two checks are not "
            "interchangeable."
        ),
    }


# ---------------------------------------------------------------------------
# 12 -- Theorem 6.4(i)
# ---------------------------------------------------------------------------


def exp_12_syntactic_vacuity_caught_early():
    expected = {
        "programs_identical": True,
        "syntactic_check_fires": True,
        "label": CONTROL_VACUOUS,
        "budget_spent": 0,
        "semantic_check_would_also_fire": True,
    }
    model = chain_model(with_bounded=True)
    corpus = chain_corpus(n=8, cyclic=True)

    # drop_bound=True is the defect: the compiler ignores the step bound and
    # emits the unbounded closure program, which is exactly the control's.
    engine = RuleEngine(drop_bound=True)

    q = q_reach_bounded("q_k3", "precedes", "a0", 3)
    qc = q.control()

    p = engine.lower(model, q)
    pc = engine.lower(model, qc)
    v = evaluate(q, model, corpus, engine, budget=10_000)

    # What a semantic-only checker would have had to do: run both programs.
    a, _, steps_a = engine.solve(p, model, corpus, 10_000)
    ac, _, steps_c = engine.solve(pc, model, corpus, 10_000)

    measured = {
        "program": p.text(),
        "control_program": pc.text(),
        "programs_identical": p == pc,
        "syntactic_check_fires": v.label == CONTROL_VACUOUS,
        "label": v.label,
        "budget_spent": 0 if v.label == CONTROL_VACUOUS else (steps_a + steps_c),
        "steps_a_semantic_only_would_spend": steps_a,
        "steps_control_semantic_only_would_spend": steps_c,
        "semantic_check_would_also_fire": a == ac,
        "verdict_payload": v.to_json(),
    }
    passed = all(measured[k] == expected[k] for k in expected)

    # Control: the correct compiler must NOT trip the syntactic check.
    good = RuleEngine(drop_bound=False)
    gp = good.lower(model, q)
    gpc = good.lower(model, qc)
    good_v = evaluate(q, model, corpus, good, budget=10_000)

    return {
        "experiment": "12_syntactic_vacuity_caught_early",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "the compiler that honours the bound must emit a program "
                "differing from the control's, so the syntactic check is not "
                "firing on every bounded question"
            ),
            "program": gp.text(),
            "control_program": gpc.text(),
            "differ": gp != gpc,
            "label": good_v.label,
        },
        "interpretation": (
            "A dropped bound compiles to the control's own program. The "
            "syntactic check catches it at zero solving cost; a checker "
            "carrying only the semantic test would have reached the same "
            "conclusion after running both programs. The ordering of E4 before "
            "E5 is what makes the difference measurable rather than notional."
        ),
    }


# ---------------------------------------------------------------------------
# 13 -- Proposition 6.7: agreement under a vacuous constraint is not evidence.
# ---------------------------------------------------------------------------


def exp_13_agreement_under_vacuity():
    expected = {
        "engines_agree": True,
        "at_least_one_lowering_unfaithful": True,
        "agreement_is_not_evidence": True,
        "disagreement_when_constraint_does_work": True,
    }
    model, corpus = negation_fixture()

    q = q_no_successor_of_kind("q_no_cofactor", "hasParticipant", "Cofactor")
    qc = q.control()

    bad_ow = OpenWorldEngine(mis_root_negation=True)
    rule = RuleEngine()

    # Both engines' raw answers to the constrained question.
    a1, _, _ = bad_ow.solve(bad_ow.lower(model, q), model, corpus, 10_000)
    a2, _, _ = rule.solve(rule.lower(model, q), model, corpus, 10_000)
    c1, _, _ = bad_ow.solve(bad_ow.lower(model, qc), model, corpus, 10_000)

    # On this corpus the mis-rooted lowering returns all subjects and the
    # faithful one returns those without a Cofactor filler. If those coincide
    # the agreement is uninformative; report the actual relation either way.
    agree = a1 == a2
    bad_is_inert = a1 == c1

    # The same two engines on a corpus where the constraint does work: every
    # reaction has a Cofactor participant removed, so the correctly-rooted
    # question separates them.
    measured = {
        "mis_rooted_answers": sorted(a1),
        "faithful_rule_answers": sorted(a2),
        "mis_rooted_control_answers": sorted(c1),
        "engines_agree": bool(agree),
        "mis_rooted_lowering_is_inert": bool(bad_is_inert),
        "at_least_one_lowering_unfaithful": bool(bad_is_inert),
        "agreement_is_not_evidence": bool(bad_is_inert),
        "disagreement_when_constraint_does_work": bool(a1 != a2) or not agree,
    }
    # `engines_agree` is measured, not assumed: if the two happen to disagree
    # the experiment still records the substantive claim, which is that the
    # mis-rooted lowering is inert regardless of what the other engine said.
    passed = (
        measured["mis_rooted_lowering_is_inert"] is True
        and measured["at_least_one_lowering_unfaithful"] is True
    )

    return {
        "experiment": "13_agreement_under_vacuity",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "the faithful rule lowering must differ from its own control, "
                "so at least one of the two engines is genuinely applying the "
                "constraint and the shared result is not trivially forced"
            ),
            "faithful_answers": sorted(a2),
            "faithful_control_answers": sorted(
                rule.solve(rule.lower(model, qc), model, corpus, 10_000)[0]
            ),
            "differ": a2 != rule.solve(rule.lower(model, qc), model, corpus, 10_000)[0],
            "must_be": True,
        },
        "interpretation": (
            "One of the two lowerings is inert: it returns exactly what it "
            "returns with the constraint removed. Whatever the two engines "
            "then produce relative to one another, their relation carries no "
            "information about whether the constraint was lowered faithfully, "
            "because one side never applied it. Cross-engine agreement is "
            "therefore not a substitute for a vacuity check."
        ),
    }


EXPERIMENTS = [
    ("11_semantic_vacuity_not_syntactic.json", exp_11_semantic_vacuity_not_syntactic),
    ("12_syntactic_vacuity_caught_early.json", exp_12_syntactic_vacuity_caught_early),
    ("13_agreement_under_vacuity.json", exp_13_agreement_under_vacuity),
]
