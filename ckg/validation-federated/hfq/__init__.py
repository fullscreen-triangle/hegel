"""hfq -- a compiler and executor for the Hegel Federated Query language.

Six stages, in the order fixed by sec:proto:

    parser.py     (1) Parse     plan text -> steps (x, Src, rho, beta, b)
    adapters.py   (2) Resolve   source names -> adapters declaring Capset(Src)
    check.py      (3) Check     Req(rho) subseteq Capset(Src), before contact
    allocate.py   (4) Allocate  water-filling on a single shadow price
    execute.py    (5) Execute   rules (R1)--(R6) of def:verdicts
    emit.py       (6) Emit      serialise to the schema of lst:json

Every adapter resolves against a local fixture or a local engine. No request
leaves the machine, by construction rather than by configuration.
"""

from .model import (FEAT, Blocker, Feature, Ident, ResultSet, TranslationMap,
                    Verdict, blocker_of, featureset)
from .parser import (AbstractRequest, Emit, ParseError, Plan, Step, parse)
from .adapters import (Adapter, GraphPatternAdapter, LookupAdapter, MapAdapter,
                       OntologyAdapter, Refusal, Registry, Timeout,
                       required_features)
from .check import CapabilityFailure, CheckReport, check, refusal_document
from .allocate import Allocation, YieldSpec, kkt_residuals, solve
from .execute import Execution, Executor, StepResult, yield_specs

__all__ = [
    "FEAT", "Feature", "featureset", "Ident", "ResultSet", "TranslationMap",
    "Verdict", "Blocker", "blocker_of",
    "parse", "Plan", "Step", "Emit", "AbstractRequest", "ParseError",
    "Adapter", "GraphPatternAdapter", "LookupAdapter", "OntologyAdapter",
    "MapAdapter", "Registry", "Refusal", "Timeout", "required_features",
    "check", "refusal_document", "CheckReport", "CapabilityFailure",
    "solve", "kkt_residuals", "YieldSpec", "Allocation",
    "Executor", "Execution", "StepResult", "yield_specs",
]
