"""Single-entry runner for the notebook: source text on stdin, cell JSON on stdout.

The notebook executes the SAME interpreter the validation suite runs. Nothing
here reimplements parse, check, allocate or execute; this module only selects a
fixture registry and flattens `Execution.to_json()` into the shape the browser
renders.

Every adapter resolves against a local fixture. No request leaves the machine,
by construction rather than by configuration.
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "fixtures"))

import build  # noqa: E402
from hfq import Executor, parse  # noqa: E402
from hfq.parser import ParseError  # noqa: E402
from hfq.adapters import Refusal  # noqa: E402


# --------------------------------------------------------------------------
# Registry selection
# --------------------------------------------------------------------------
#
# The three fixture worlds declare disjoint source names, so the sources a plan
# names determine which world it belongs to. This is inference over declared
# names and not a guess: a plan naming a source no world declares is reported
# as an unknown source rather than silently run against the wrong fixture.

WORLDS = {
    "main":  {"chebi", "rhea", "enzdb"},
    "paper": {"CHEBI", "RHEA", "KEGG"},
    "tiny":  {"tiny_onto", "tiny_graph"},
}


def _build(world: str):
    if world == "paper":
        return build.build_paper_registry()
    if world == "tiny":
        return build.budget_trap(), build.build_maps()
    return build.build_registry(), build.build_maps()


def select_world(plan) -> str:
    """Name the fixture world a parsed plan belongs to, by its declared sources."""
    named = {s.source for s in plan.steps if getattr(s, "source", None)}
    named = {s for s in named if not s.startswith("map:")}
    best, score = "main", -1
    for world, decl in WORLDS.items():
        hit = len(named & decl)
        if hit > score:
            best, score = world, hit
    unknown = sorted(named - WORLDS[best])
    return best, unknown


# --------------------------------------------------------------------------
# Cell assembly
# --------------------------------------------------------------------------


def _dag(plan) -> Dict[str, Any]:
    """Nodes and edges of def:plan's dependency graph, for the DAG view."""
    return {
        "nodes": [
            {"id": s.var, "kind": s.kind, "source": getattr(s, "source", None),
             "position": i}
            for i, s in enumerate(plan.steps)
        ],
        "edges": [
            {"from": b, "to": s.var}
            for s in plan.steps for b in (s.beta or ())
        ],
        "emits": [
            {"target": e.target, "provenance": e.provenance,
             "divergence": list(e.divergence) if e.divergence else None,
             "alias": e.alias}
            for e in plan.emits
        ],
    }


def run_source(text: str) -> Dict[str, Any]:
    """Parse, check, allocate and execute one cell. Never raises."""
    try:
        plan = parse(text)
    except ParseError as exc:
        return {"ok": False, "stage": "parse", "error": str(exc),
                "line": getattr(exc, "line", None)}
    except Exception as exc:                      # malformed beyond ParseError
        return {"ok": False, "stage": "parse", "error": str(exc)}

    world, unknown = select_world(plan)
    if unknown:
        return {"ok": False, "stage": "resolve", "world": world,
                "error": "unknown source(s): " + ", ".join(unknown),
                "declared": sorted(set().union(*WORLDS.values()))}

    reg, maps = _build(world)
    try:
        ex = Executor(reg, maps=maps).run(plan)
    except Refusal as exc:
        return {"ok": False, "stage": "resolve", "world": world,
                "error": str(exc)}
    except Exception as exc:
        return {"ok": False, "stage": "execute", "world": world,
                "error": f"{type(exc).__name__}: {exc}"}

    out = ex.to_json()
    out["ok"] = True
    out["world"] = world
    out["dag"] = _dag(plan)
    out["declared_budget"] = plan.budget

    # prop:blame -- the chain is walked for every starved step, so the reader
    # sees the root cause rather than only the symptom.
    blame = {}
    for s in ex.steps:
        if s.verdict.value == "starved":
            blame[s.step] = ex.blame_chain(s.step)
    out["blame"] = blame

    return out


def main() -> None:
    text = sys.stdin.read()
    try:
        result = run_source(text)
    except Exception as exc:                       # last resort: never 500
        result = {"ok": False, "stage": "internal",
                  "error": f"{type(exc).__name__}: {exc}"}
    sys.stdout.write(json.dumps(result))


if __name__ == "__main__":
    main()
