"""
Validation suite for
  "A Circuit Model of the Cell as a Constructor of Causal Knowledge Graphs"

Runs every experiment, writes one JSON file per experiment into results/, and
emits 00_summary.json.

    python run_validation.py

Nothing here is a proof. The suite checks that the implementation obeys the
definitions the paper states, that the claimed invariances hold and that the
controls -- the tests designed to be able to fail -- do in fact discriminate.
Where a claim is definitional rather than empirical, the experiment's
"interpretation" field says so.
"""

import sys
import traceback

import exp_01_circuit
import exp_02_addressing
import exp_03_propagation
import exp_04_panel
from common import OUTPUT_DIR, ensure_output_dir, save_result, utc_stamp


MODULES = [
    ("circuit", exp_01_circuit),
    ("addressing", exp_02_addressing),
    ("propagation", exp_03_propagation),
    ("panel", exp_04_panel),
]

# Maps each experiment to the numbered claim it tests, for the summary table.
CLAIM_INDEX = {
    "01_kirchhoff_correspondence": "Theorem 2.1",
    "02_relabelling_invariance": "Proposition 2.6 (V2)",
    "03_coordinate_irreducibility": "V3, Definition 2.7",
    "04_prefix_ancestry": "Proposition 3.5 (V4)",
    "05_depth_capacity": "Proposition 3.10",
    "06_similarity_is_partition": "Proposition 3.7, Remark 3.8",
    "07_cache_free_queries": "Proposition 4.4 (V10), Corollary 4.3",
    "08_path_opacity": "Theorem 5.4",
    "09_direction_agnosticism": "Theorem 5.6",
    "10_ckg_is_propagation_at_rest": "Theorem 5.7",
    "11_virtual_substates_and_collapse": "Theorem 6.2, Corollary 6.3 (V5)",
    "12_forward_asymmetry": "Theorem 6.4",
    "13_discrimination_bound": "Theorem 7.2, Corollary 7.3 (V6)",
    "14_water_filling_allocation": "Theorem 7.7, Corollary 7.8 (V7)",
    "15_locking_threshold": "Theorem 7.11 (V8)",
    "16_localisation_of_R_drop": "Proposition 7.12 (V9)",
    "17_panel_identity": "Propositions 8.3, 8.4",
}


def main():
    ensure_output_dir()
    print(f"results -> {OUTPUT_DIR}\n")

    rows = []
    failures = []
    errors = []

    for group, module in MODULES:
        print(f"--- {group} " + "-" * (60 - len(group)))
        for filename, fn in module.EXPERIMENTS:
            name = filename.replace(".json", "")
            try:
                result = fn()
                result["paper_claim"] = CLAIM_INDEX.get(name, "")
                path = save_result(result, filename)
                status = result.get("status", "UNKNOWN")
                rows.append({
                    "experiment": name,
                    "group": group,
                    "claim": CLAIM_INDEX.get(name, ""),
                    "status": status,
                    "file": filename,
                })
                if status != "PASS":
                    failures.append(name)
                print(f"  [{status:4}] {name}  ({CLAIM_INDEX.get(name, '')})")
            except Exception as exc:                       # noqa: BLE001
                errors.append({
                    "experiment": name,
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                })
                rows.append({
                    "experiment": name,
                    "group": group,
                    "claim": CLAIM_INDEX.get(name, ""),
                    "status": "ERROR",
                    "file": filename,
                })
                print(f"  [ERR ] {name}: {type(exc).__name__}: {exc}")
        print()

    n_pass = sum(1 for r in rows if r["status"] == "PASS")
    summary = {
        "suite": "circuit-ckg-contact-propagation validation",
        "paper": "ckg/docs/circuit-ckg-contact-propagation/"
                 "circuit-ckg-contact-propagation.tex",
        "experiments_run": len(rows),
        "passed": n_pass,
        "failed": len(failures),
        "errored": len(errors),
        "results": rows,
        "failures": failures,
        "errors": errors,
        "data_provenance": {
            "thermodynamic": "eQuilibrator / Alberty 2003 / NIST standard values",
            "kinetic": "BRENDA kcat, human enzymes, pH 7.4, 37 C",
            "concentrations": "HMDB physiological reference ranges",
            "topology": "KEGG hsa00010 / hsa00020 / hsa00190 / hsa04010, Reactome",
            "spectroscopic": "published UV-Vis / EPR / Raman assignments for the "
                             "seven-state P450 cycle",
        },
        "determinism": {
            "seed": 20260813,
            "note": "every stochastic experiment seeds explicitly; reruns on the "
                    "same machine reproduce identical JSON apart from timestamps",
        },
        "scope": (
            "These experiments check that the implementation obeys the paper's "
            "definitions and that the stated invariances hold on four metabolic "
            "and signalling networks. They do not establish that the kinetic "
            "parameters are correct, that the asymptotic bounds hold beyond the "
            "sizes swept, or that the contact map predicts biological outcomes. "
            "Claims that are definitional rather than empirical are marked as "
            "such in each experiment's interpretation field."
        ),
        "timestamp": utc_stamp(),
    }
    save_result(summary, "00_summary.json")

    print("=" * 66)
    print(f"  {n_pass}/{len(rows)} passed, "
          f"{len(failures)} failed, {len(errors)} errored")
    if failures:
        print(f"  failures: {', '.join(failures)}")
    if errors:
        print(f"  errors:   {', '.join(e['experiment'] for e in errors)}")
    print("=" * 66)

    return 1 if (failures or errors) else 0


if __name__ == "__main__":
    sys.exit(main())
