"""
Experiments 14-16: divergent semantics as a result rather than a defect.

14 -- Proposition 8.1 + Corollary 8.2: the rule lowering of a disjointness
      axiom is a DETECTOR. It is faithful while the knowledge base is
      consistent and diagnostic when it is not, and only one of the two engines
      localises the violation.
15 -- Proposition 8.3 + Corollary 8.4: Herbrand semantics supply the
      unique-name assumption unconditionally, so the two engines answer the
      at-least-n question differently on identical input. The disagreement is
      the result.
16 -- Proposition 8.6 + Corollary 8.7: bounded reachability is certified where
      unbounded exceeds the budget on the same cyclic corpus, and the
      open-world engine answers the unbounded question while refusing the
      bounded one. One word in the question determines which engine can answer.
"""

from __future__ import annotations

from common import (
    ANSWERED,
    BOUNDED_PATH,
    CANNOT_EXPRESS,
    NOT_DERIVABLE,
    NO_QUERY_SURFACE,
    OpenWorldEngine,
    RuleEngine,
    TIMEOUT,
    chain_corpus,
    chain_model,
    counting_derivable,
    disjoint_fixture,
    evaluate,
    fixture_corpus,
    fixture_model,
    q_count,
    q_disjointness_violation,
    q_reach,
    q_reach_bounded,
    utc_stamp,
    verdict,
)


# ---------------------------------------------------------------------------
# 14 -- Proposition 8.1 + Corollary 8.2
# ---------------------------------------------------------------------------


def exp_14_disjointness_detector():
    expected = {
        "open_world_reports_global_inconsistency": True,
        "rule_localises": True,
        "rule_names_the_individual": True,
        "only_one_localises": True,
        "consistent_case_agrees": True,
    }
    model, corpus = disjoint_fixture()
    ow = OpenWorldEngine()
    rule = RuleEngine()

    q = q_disjointness_violation("q_viol", "TwoOxoAcid", "AminoAcid")

    ow_ans, _, _ = ow.solve(ow.lower(model, q), model, corpus, 10_000)
    rule_ans, _, _ = rule.solve(rule.lower(model, q), model, corpus, 10_000)

    localised = sorted({x for (_, _, _, x) in rule_ans}) if isinstance(rule_ans, set) else []

    # The consistent case: remove the offending assertion. Both engines must
    # then agree that nothing is wrong -- this is the sense in which the
    # detector is FAITHFUL while the knowledge base is consistent.
    from common import Corpus
    clean = Corpus(
        "disjoint-clean",
        {a for a in corpus.concept_assertions
         if a != ("AminoAcid", "chebi58556")},
    )
    ow_clean, _, _ = ow.solve(ow.lower(model, q), model, clean, 10_000)
    rule_clean, _, _ = rule.solve(rule.lower(model, q), model, clean, 10_000)

    measured = {
        "open_world_result": ow_ans if isinstance(ow_ans, str) else sorted(ow_ans),
        "rule_result": sorted(str(x) for x in rule_ans),
        "open_world_reports_global_inconsistency": ow_ans == "INCONSISTENT",
        "rule_localises": len(localised) > 0,
        "localised_individuals": localised,
        "rule_names_the_individual": localised == ["chebi58556"],
        "only_one_localises": (ow_ans == "INCONSISTENT" and len(localised) > 0),
        "consistent_case": {
            "open_world": ow_clean if isinstance(ow_clean, str) else sorted(ow_clean),
            "rule": sorted(str(x) for x in rule_clean),
        },
        "consistent_case_agrees": (
            ow_clean == set() and rule_clean == set()
        ),
    }
    passed = all(measured[k] == expected[k] for k in expected)

    return {
        "experiment": "14_disjointness_detector",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "on a consistent corpus both engines must report nothing, so "
                "the divergence is caused by the violation and not by the "
                "lowering being wrong in general"
            ),
            "outcome": measured["consistent_case"],
            "must_be_empty_both": measured["consistent_case_agrees"],
        },
        "interpretation": (
            "Both engines are correct and they answer different questions. "
            "The open-world engine reports that the knowledge base has no "
            "model, which is true and global: every entailment is now trivial "
            "and nothing can be localised. The rule lowering derives one extra "
            "fact per violating individual, leaving the rest of the least "
            "model intact. Only the second tells you where to look, which is "
            "why the divergence is worth recording rather than reconciling."
        ),
    }


# ---------------------------------------------------------------------------
# 15 -- Proposition 8.3 + Corollary 8.4
# ---------------------------------------------------------------------------


def exp_15_inherited_una():
    expected = {
        "open_world_refuses_ge": True,
        "rule_derives_ge": True,
        "engines_disagree": True,
        "disagreement_is_the_result": True,
        "term_map_injective": True,
        "scoped_distinctness_makes_them_agree": True,
    }
    corpus = fixture_corpus()
    # No distinctness asserted anywhere: the open-world engine has nothing to
    # work with, the rule engine has Herbrand.
    model = fixture_model(with_counting=True, with_closure=False,
                          with_distinctness=False)

    ow_der, ow_reason = counting_derivable(
        model, corpus, "rx1", "hasParticipant", 4, "ge", inherits_una=False
    )
    rule_der, rule_reason = counting_derivable(
        model, corpus, "rx1", "hasParticipant", 4, "ge", inherits_una=True
    )

    rule = RuleEngine()
    injective, collision = rule.term_map_injective(corpus, lambda x: x)

    # With distinctness scoped to the counted set, the open-world engine
    # derives it too: the disagreement is specifically about the assumption,
    # not about the arithmetic.
    model_scoped = fixture_model(with_counting=True, with_closure=False,
                                 with_distinctness=True,
                                 scoped_to_participants=True)
    ow_scoped, _ = counting_derivable(
        model_scoped, corpus, "rx1", "hasParticipant", 4, "ge", inherits_una=False
    )

    measured = {
        "open_world_derives_ge": ow_der,
        "open_world_reason": ow_reason,
        "rule_derives_ge": rule_der,
        "rule_reason": rule_reason,
        "open_world_refuses_ge": ow_der is False,
        "engines_disagree": ow_der != rule_der,
        "disagreement_is_the_result": ow_der is False and rule_der is True,
        "term_map_injective": bool(injective),
        "term_map_collision": collision,
        "scoped_distinctness_makes_them_agree": ow_scoped is True and rule_der is True,
    }
    passed = all(measured[k] == expected[k] for k in expected)

    # A non-injective term map: the guard of Remark 8.5.
    def collapsing(ind):
        return ind.split("_")[0] if "_p" in ind else ind

    injective_bad, collision_bad = rule.term_map_injective(corpus, collapsing)

    return {
        "experiment": "15_inherited_una",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "a term map that collapses two individuals must be caught, "
                "because the inherited assumption is only safe while the map "
                "is injective; if this control did not fire the inheritance "
                "would be being trusted unconditionally"
            ),
            "injective": bool(injective_bad),
            "collision": list(collision_bad) if collision_bad else None,
            "must_be_caught": injective_bad is False,
        },
        "interpretation": (
            "On identical input the two engines give different answers to the "
            "at-least-four question, and neither is wrong. The rule engine "
            "inherits distinctness from its Herbrand universe; the open-world "
            "engine has no such assumption and reports that the bound is not "
            "determined. Reconciling them would mean discarding one engine's "
            "semantics. The disagreement is the finding: it says the answer "
            "depends on an assumption the corpus never states. The control "
            "records the precondition -- inheritance is only sound while the "
            "term map is injective."
        ),
    }


# ---------------------------------------------------------------------------
# 16 -- Proposition 8.6 + Corollary 8.7: the inversion, on ONE corpus.
# ---------------------------------------------------------------------------


def exp_16_bounded_inversion():
    expected = {
        "same_corpus": True,
        "rule_bounded_answered": True,
        "rule_unbounded_timeout": True,
        "open_world_unbounded_answered": True,
        "open_world_bounded_refused": True,
        "inversion": True,
        "bounded_steps_linear_in_k": True,
    }
    model = chain_model(with_bounded=True, with_transitive_query=True)
    corpus = chain_corpus(n=12, cyclic=True)

    BUDGET = 4  # small enough that the cyclic closure cannot finish

    rule = RuleEngine()
    ow = OpenWorldEngine()

    q_bounded = q_reach_bounded("q_k3", "precedes", "a0", 3)
    q_unbounded = q_reach("q_star", "precedes", "a0")

    v_rule_bounded = evaluate(q_bounded, model, corpus, rule, budget=BUDGET)
    v_rule_unbounded = evaluate(q_unbounded, model, corpus, rule, budget=BUDGET)
    v_ow_unbounded = evaluate(q_unbounded, model, corpus, ow, budget=10_000)
    v_ow_bounded = evaluate(q_bounded, model, corpus, ow, budget=10_000)

    # Proposition 8.6's cost claim: steps scale with k, not with the corpus.
    steps_by_k = {}
    for k in (1, 2, 3, 4, 5):
        vk = evaluate(
            q_reach_bounded(f"q_k{k}", "precedes", "a0", k), model, corpus,
            rule, budget=10_000,
        )
        steps_by_k[k] = vk.payload["steps"] if vk.label == ANSWERED else None
    linear = all(
        steps_by_k[k] == k for k in steps_by_k if steps_by_k[k] is not None
    )

    measured = {
        "corpus": corpus.name,
        "corpus_size": len(corpus.role_assertions),
        "cyclic": True,
        "budget": BUDGET,
        "same_corpus": True,
        "rule_bounded": v_rule_bounded.to_json(),
        "rule_unbounded": v_rule_unbounded.to_json(),
        "open_world_unbounded": v_ow_unbounded.to_json(),
        "open_world_bounded": v_ow_bounded.to_json(),
        "rule_bounded_answered": v_rule_bounded.label == ANSWERED,
        "rule_unbounded_timeout": v_rule_unbounded.label == TIMEOUT,
        "open_world_unbounded_answered": v_ow_unbounded.label == ANSWERED,
        "open_world_bounded_refused": v_ow_bounded.label in (
            NO_QUERY_SURFACE, CANNOT_EXPRESS
        ),
        "open_world_bounded_label": v_ow_bounded.label,
        "steps_by_k": steps_by_k,
        "bounded_steps_linear_in_k": bool(linear),
    }
    measured["inversion"] = (
        measured["rule_bounded_answered"]
        and measured["rule_unbounded_timeout"]
        and measured["open_world_unbounded_answered"]
        and measured["open_world_bounded_refused"]
    )
    passed = all(measured[k] == expected[k] for k in expected)

    # Control: on an ACYCLIC corpus the rule engine's unbounded closure must
    # finish within the same budget, so the timeout above is caused by the
    # cycle and not by the budget being set below any possible completion.
    acyclic = chain_corpus(n=4, cyclic=False)
    v_ctrl = evaluate(q_unbounded, model, acyclic, rule, budget=BUDGET)

    return {
        "experiment": "16_bounded_inversion",
        "timestamp": utc_stamp(),
        "expected": expected,
        "measured": measured,
        "verdict": verdict(passed),
        "control": {
            "description": (
                "the same unbounded question on an acyclic corpus at the same "
                "budget must complete, so the TIMEOUT is attributable to the "
                "cycle rather than to an unreachably small budget"
            ),
            "outcome": v_ctrl.to_json(),
            "answered": v_ctrl.label == ANSWERED,
            "must_be": True,
        },
        "interpretation": (
            "One corpus, one budget, two questions differing in a single word. "
            "The rule engine certifies the bounded question because unrolling "
            "is non-recursive and costs k steps, and exceeds the budget on the "
            "unbounded one because the cycle forces a fixpoint. The open-world "
            "engine is the mirror image: its transitive super-role closes "
            "completely and admits no step bound, so it answers the unbounded "
            "question and has no surface for the bounded one. Neither engine "
            "dominates. The timing figures are a property of our evaluation "
            "strategy and the stated budget, not of the formalisms."
        ),
    }


EXPERIMENTS = [
    ("14_disjointness_detector.json", exp_14_disjointness_detector),
    ("15_inherited_una.json", exp_15_inherited_una),
    ("16_bounded_inversion.json", exp_16_bounded_inversion),
]
