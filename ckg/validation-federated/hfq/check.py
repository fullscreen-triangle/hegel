"""Stage 3 of the pipeline: Check.

Compute Req(rho_i) for every step by structural recursion over the abstract
request and test Req(rho_i) subseteq Capset(Src_i). On failure the executor
halts BEFORE issuing any request and emits a refusal document naming the
missing features and the step -- cor:refuse-before-contact made operational.

thm:static(a) says the check costs O(m |Feat|). `CheckReport.operations`
counts the containment tests actually performed so (V2) can measure it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .adapters import Refusal, Registry, required_features
from .model import FEAT
from .parser import Plan, Step


@dataclass
class CapabilityFailure:
    step: str
    source: str
    required: List[str]
    declared: List[str]
    missing: List[str]

    def to_json(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "source": self.source,
            "required": sorted(self.required),
            "declared": sorted(self.declared),
            "missing": sorted(self.missing),
        }


@dataclass
class CheckReport:
    """The outcome of the static check of thm:static."""

    well_capability: bool
    failures: List[CapabilityFailure] = field(default_factory=list)
    operations: int = 0
    requirements: Dict[str, List[str]] = field(default_factory=dict)
    #: number of steps, retained so `bound` can report the m|Feat| bound
    n_steps: int = 0

    def to_json(self) -> Dict[str, Any]:
        return {
            "well_capability": self.well_capability,
            "failures": [f.to_json() for f in self.failures],
            "operations": self.operations,
            "bound": self.bound,
            "requirements": self.requirements,
        }

    @property
    def bound(self) -> int:
        """The m|Feat| bound of thm:static(a), for comparison in (V2)."""
        return self.n_steps * len(FEAT)


def check(plan: Plan, registry: Registry) -> CheckReport:
    """Decide well-capability. Issues no request under any outcome."""
    report = CheckReport(well_capability=True)
    report.n_steps = len(plan.steps)

    for step in plan.steps:
        if step.kind != "from":
            continue  # map and set steps carry no source capability demand
        req = required_features(step.request)
        report.requirements[step.var] = sorted(req)
        adapter = registry.get(step.source)
        # One membership test per required feature: this is the count thm:static
        # bounds, and it is what (V2) measures.
        missing = []
        for f in sorted(req):
            report.operations += 1
            if f not in adapter.capabilities:
                missing.append(f)
        if missing:
            report.well_capability = False
            report.failures.append(
                CapabilityFailure(
                    step=step.var,
                    source=step.source,
                    required=sorted(req),
                    declared=sorted(adapter.capabilities),
                    missing=missing,
                )
            )
    return report


def refusal_document(plan: Plan, report: CheckReport) -> Dict[str, Any]:
    """The document emitted when the check fails.

    It names the missing features and the step. It is NOT an empty result:
    the distinction is the content of cor:onebit.
    """
    return {
        "plan": plan.name,
        "outcome": "refused_statically",
        "reason": "ill-capability plan; no request was issued",
        "failures": [f.to_json() for f in report.failures],
        "steps": [],
    }
