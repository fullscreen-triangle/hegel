"""Core model: features, result sets, verdicts, blockers.

Definitions implemented here, with the paper's labels:

  def:result    result set = finite set of (identifier, partial attribute map),
                no identifier occurring twice
  def:verdicts  V = {answer, empty, surface, timeout, refused, starved}
  def:blocker   partial map from non-answer verdicts to blockers; `empty`
                deliberately has no blocker
  def:map       translation map = relation, with retention and amplification

Nothing in this module performs I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, Iterator, Mapping, Optional, Tuple

# ---------------------------------------------------------------------------
# Features (Feat). The capability vocabulary of the paper.
# ---------------------------------------------------------------------------

FEAT = frozenset(
    {
        "pattern",  # conjunctive graph pattern
        "path",     # transitive / property path
        "filter",   # value filtering
        "bind",     # supply a bound set as input
        "agg",      # aggregation
        "neg",      # negation
        "order",    # ordering
        "regex",    # regular-expression matching
        "lookup",   # single-key record retrieval
        "link",     # cross-reference listing
        "batch",    # multiple keys in one request
    }
)


class Feature(str):
    """A capability symbol, validated against FEAT."""

    __slots__ = ()

    def __new__(cls, value: str) -> "Feature":
        if value not in FEAT:
            raise ValueError(f"unknown feature {value!r}; Feat = {sorted(FEAT)}")
        return super().__new__(cls, value)


def featureset(*names: str) -> frozenset:
    return frozenset(Feature(n) for n in names)


# ---------------------------------------------------------------------------
# Result sets (def:result)
# ---------------------------------------------------------------------------

Ident = str
AttrMap = Mapping[str, Any]


@dataclass(frozen=True)
class ResultSet:
    """A finite set of (identifier, partial attribute map) pairs.

    The no-duplicate-identifier condition of def:result is enforced by
    construction: the payload is a dict keyed by identifier. Identifiers are
    namespace-tagged strings ("CHEBI:15377"), which is how rem:disjoint
    discharges the disjointness assumption -- by prefixing at extraction time.
    """

    namespace: str
    rows: Dict[Ident, Dict[str, Any]] = field(default_factory=dict)

    @staticmethod
    def of(namespace: str, pairs: Iterable[Tuple[Ident, AttrMap]]) -> "ResultSet":
        rows: Dict[Ident, Dict[str, Any]] = {}
        for ident, attrs in pairs:
            if ident in rows:
                # def:result forbids a repeated identifier: merge attribute maps,
                # which is exactly the collapse prop:common-result performs.
                rows[ident].update(dict(attrs))
            else:
                rows[ident] = dict(attrs)
        return ResultSet(namespace, rows)

    @staticmethod
    def empty(namespace: str) -> "ResultSet":
        return ResultSet(namespace, {})

    def identifiers(self) -> frozenset:
        """idm(Res): the projection onto identifiers."""
        return frozenset(self.rows)

    def __len__(self) -> int:
        return len(self.rows)

    def __iter__(self) -> Iterator[Ident]:
        return iter(self.rows)

    def __bool__(self) -> bool:
        return bool(self.rows)

    def to_json(self) -> Dict[str, Any]:
        return {
            "namespace": self.namespace,
            "size": len(self.rows),
            "identifiers": sorted(self.rows),
            "attributes": {k: self.rows[k] for k in sorted(self.rows)},
        }


# ---------------------------------------------------------------------------
# Verdicts (def:verdicts) and blockers (def:blocker)
# ---------------------------------------------------------------------------


class Verdict(str, Enum):
    ANSWER = "answer"
    EMPTY = "empty"
    SURFACE = "surface"
    TIMEOUT = "timeout"
    REFUSED = "refused"
    STARVED = "starved"

    def __str__(self) -> str:  # pragma: no cover - display only
        return self.value


class Blocker(str, Enum):
    MODEL = "model"
    ENGINE = "engine"
    BUDGET = "budget"
    CORPUS = "corpus"

    def __str__(self) -> str:  # pragma: no cover - display only
        return self.value


#: def:blocker. Deliberately partial: Verdict.EMPTY and Verdict.ANSWER are
#: absent, because (R6) fires exactly when nothing obstructed the step, and
#: assigning a blocker there would assert an obstruction that did not occur.
BLOCKER: Mapping[Verdict, Blocker] = {
    Verdict.SURFACE: Blocker.MODEL,
    Verdict.TIMEOUT: Blocker.ENGINE,
    Verdict.REFUSED: Blocker.BUDGET,
    Verdict.STARVED: Blocker.CORPUS,
}


def blocker_of(v: Verdict) -> Optional[Blocker]:
    """blk(v), partial. Returns None for ANSWER and EMPTY."""
    return BLOCKER.get(v)


# ---------------------------------------------------------------------------
# Translation maps (def:map, def:retention)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TranslationMap:
    """A relation mu subseteq n x n'. Partial, non-functional, non-injective."""

    name: str
    source_ns: str
    target_ns: str
    pairs: Mapping[Ident, Tuple[Ident, ...]]

    def domain(self) -> frozenset:
        return frozenset(k for k, v in self.pairs.items() if v)

    def image(self, s: Iterable[Ident]) -> frozenset:
        out = set()
        for u in s:
            out.update(self.pairs.get(u, ()))
        return frozenset(out)

    def retention(self, s: Iterable[Ident]) -> float:
        """r_mu(S) = |S cap dom mu| / |S|, with r_mu(empty) = 1 by convention."""
        s = frozenset(s)
        if not s:
            return 1.0
        return len(s & self.domain()) / len(s)

    def amplification(self, s: Iterable[Ident]) -> Optional[float]:
        """a_mu(S) = |mu(S)| / |S cap dom mu|; None when the denominator is 0."""
        s = frozenset(s)
        kept = len(s & self.domain())
        if kept == 0:
            return None
        return len(self.image(s)) / kept

    def apply(self, res: ResultSet) -> ResultSet:
        """Carry attributes forward, recording the preimage as provenance.

        The iteration is SORTED. identifiers() returns a frozenset, and
        ResultSet.of merges on collision with the last write winning, so when
        mu is non-injective -- CHEBI:9 and CHEBI:10 both reach KEGG:C9 -- the
        surviving row's `_preimage` is whichever preimage came last. Under an
        unordered iteration that is genuinely unstable across runs: with
        PYTHONHASHSEED varied over 0..7 this attribute alternates between the
        two preimages. Verdicts and cardinalities are unaffected either way,
        since the merge collapses to the same identifier set, but the recorded
        provenance is not reproducible. Sorting fixes the choice without
        changing any other quantity.
        """
        pairs = []
        for u in sorted(res.identifiers()):
            for v in self.pairs.get(u, ()):
                attrs = dict(res.rows[u])
                attrs["_via"] = self.name
                attrs["_preimage"] = u
                pairs.append((v, attrs))
        return ResultSet.of(self.target_ns, pairs)
