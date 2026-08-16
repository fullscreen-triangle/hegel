"""
Driver for the graph-incompleteness validation suite.

Runs every experiment, writes one JSON document per experiment plus a summary,
and attaches to each result the paper claim it tests. CLAIM_INDEX mirrors the
experiment table in the manuscript's validation section; the index is the one
place the correspondence is recorded, so a claim renamed in the paper and not
here shows up as an empty `paper_claim` rather than as a silently wrong one.

    python run_validation.py
"""

from __future__ import annotations

import sys
import traceback

import exp_capability
import exp_derivation
import exp_divergence
import exp_predicates
import exp_vacuity
from common import save_result, utc_stamp

MODULES = [
    ("predicates", exp_predicates),
    ("capability", exp_capability),
    ("vacuity", exp_vacuity),
    ("divergence", exp_divergence),
    ("derivation", exp_derivation),
]

CLAIM_INDEX = {
    "01_predicate_independence": "thm:independence -- Exp, Der, Ans pairwise independent",
    "02_conflation_loses_information": "cor:conflation -- conflation loses the repair",
    "03_nondegeneracy": "thm:nondegeneracy -- only ANSWERED carries an answer set",
    "04_counting_split": "prop:counting-split -- ge needs distinctness, le needs closure, eq needs both",
    "05_una_scope": "rem:una-scope -- the global distinctness check errs permissively",
    "06_compare_refusals": "prop:compare-refusals -- ranking reverses under a verdict-aware rule",
    "07_containment": "thm:containment -- declared capability contained in lowerable capability",
    "08_under_declaration": "prop:under -- the formalism counts, the compiler does not",
    "09_half_true_transitive": "prop:half-true -- a conflated TRANSITIVE makes honesty unsatisfiable",
    "10_nameable": "prop:nameable -- an unnameable feature misattributes the divergence",
    "11_semantic_vacuity_not_syntactic": "thm:irredundance(ii) -- semantic check catches what syntactic misses",
    "12_syntactic_vacuity_caught_early": "thm:irredundance(i) -- syntactic check fires before the budget",
    "13_agreement_under_vacuity": "prop:agreement -- agreement under vacuity is not evidence",
    "14_disjointness_detector": "prop:disjoint-detector + cor:localisation",
    "15_inherited_una": "prop:inherited-una + cor:disagree-result",
    "16_bounded_inversion": "prop:bounded-cheaper + cor:inversion",
    "17_single_derivation": "thm:single + prop:status-clock",
}

# Experiments whose PASS condition is a refusal or a disagreement rather than
# an answer. Recorded so the summary cannot be read as "17 things worked".
REFUSAL_OR_DISAGREEMENT = {
    "08_under_declaration",
    "11_semantic_vacuity_not_syntactic",
    "12_syntactic_vacuity_caught_early",
    "15_inherited_una",
}

DEFINITIONAL = {
    "03_nondegeneracy",
    "07_containment",
    "09_half_true_transitive",
}


def main():
    summary = {
        "suite": "graph-incompleteness-expectation",
        "timestamp": utc_stamp(),
        "python": sys.version.split()[0],
        "experiments": [],
        "counts": {"total": 0, "pass": 0, "fail": 0, "error": 0},
        "notes": {
            "refusal_or_disagreement_pass_condition": sorted(REFUSAL_OR_DISAGREEMENT),
            "definitional": sorted(DEFINITIONAL),
            "null_convention": (
                "result documents record null where nothing was measured, "
                "never a zero"
            ),
        },
    }

    for group, module in MODULES:
        for filename, fn in module.EXPERIMENTS:
            name = filename[:-5] if filename.endswith(".json") else filename
            row = {
                "name": name,
                "group": group,
                "file": filename,
                "paper_claim": CLAIM_INDEX.get(name, ""),
                "verdict": None,
                "error": None,
            }
            try:
                result = fn()
                result["paper_claim"] = CLAIM_INDEX.get(name, "")
                result["group"] = group
                result["pass_condition_is_refusal_or_disagreement"] = (
                    name in REFUSAL_OR_DISAGREEMENT
                )
                result["definitional"] = name in DEFINITIONAL
                save_result(result, filename)
                row["verdict"] = result.get("verdict")
                summary["counts"]["total"] += 1
                if row["verdict"] == "PASS":
                    summary["counts"]["pass"] += 1
                else:
                    summary["counts"]["fail"] += 1
                print(f"[{row['verdict']:4}] {name}")
            except Exception as exc:  # noqa: BLE001 -- an error is a result
                row["verdict"] = "ERROR"
                row["error"] = f"{type(exc).__name__}: {exc}"
                summary["counts"]["total"] += 1
                summary["counts"]["error"] += 1
                print(f"[ERR ] {name}: {row['error']}", file=sys.stderr)
                traceback.print_exc()
            summary["experiments"].append(row)

    if not CLAIM_INDEX.keys() >= {r["name"] for r in summary["experiments"]}:
        summary["claim_index_gaps"] = sorted(
            {r["name"] for r in summary["experiments"]} - set(CLAIM_INDEX)
        )

    save_result(summary, "00_summary.json")
    c = summary["counts"]
    print(f"\n{c['pass']}/{c['total']} pass, {c['fail']} fail, {c['error']} error")
    return 0 if c["fail"] == 0 and c["error"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
