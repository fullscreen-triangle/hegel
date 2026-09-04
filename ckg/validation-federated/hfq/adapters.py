"""Stage 2 of the pipeline: Resolve. Adapters and the source registry.

Four adapter kinds, exercising the four source kinds of obs:kind:

  GraphPatternAdapter  local RDF store, {pattern, path, bind, filter, agg}
  LookupAdapter        local key-value fixture, {lookup, link} -- NOT pattern
  OntologyAdapter      local class hierarchy, {path, lookup}
  MapAdapter           translation steps; the only kind reporting retention

A source is the quadruple (eta, cap, ext, c) of def:source. `namespace` is eta,
`capabilities` is Capset(Src), `extract` is ext, `cost` is c. The capability
declaration is *data written by the adapter author* -- it is the locus of the
honesty assumption of rem:honesty-assumption, and nothing here verifies it.

Every adapter resolves against a local fixture or a local engine. No adapter
performs network I/O, and none may be added that does: the prototype's claims
are properties of the compiler, and a live service can neither confirm nor
refute them (sec:proto).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

from .model import Ident, ResultSet, TranslationMap, featureset


class Refusal(Exception):
    """Raised by an adapter asked for something outside its declared set.

    This should never fire in a well-capability plan: thm:static decides
    containment before contact. It exists so that a bug in the checker is loud.
    """


class Timeout(Exception):
    """Raised when a lowered request exceeds the step's effort allocation."""


# ---------------------------------------------------------------------------
# The required-capability function Req(rho)
# ---------------------------------------------------------------------------

#: Which features each abstract predicate requires. This is the structural
#: recursion of the Check stage: Req is a function of phi, not an annotation
#: the plan author supplies.
PREDICATE_FEATURES: Dict[str, FrozenSet[str]] = {
    "descendants_of":       featureset("path"),
    "ancestors_of":         featureset("path"),
    "record":               featureset("lookup"),
    "link":                 featureset("lookup", "link"),
    "reactions_consuming":  featureset("pattern", "bind"),
    "reactions_producing":  featureset("pattern", "bind"),
    "enzyme_of":            featureset("pattern", "bind"),
    "participants_of":      featureset("pattern", "bind"),
    "count_of":             featureset("pattern", "agg"),
    "matching":             featureset("pattern", "regex"),
    "excluding":            featureset("pattern", "neg"),
    "ranked_by":            featureset("pattern", "order"),
    "restricted":           featureset("pattern", "filter"),
}


def resolve_features(adapter, request) -> FrozenSet[str]:
    """Req for this request AT this source.

    The check and the executor must compute Req identically -- if they differ,
    a plan can pass the static check and then be refused at R2, which inverts
    cor:refuse-before-contact and is strictly worse than either component
    being wrong on its own. So both call this, and only this.

    An adapter may override by defining `required_features`. That override is
    a declaration by the adapter author with the same standing as the
    capability set: nothing here verifies it (rem:honesty-assumption).
    """
    own = getattr(adapter, "required_features", None)
    return own(request) if own is not None else required_features(request)


def required_features(request) -> FrozenSet[str]:
    """Req(rho), by structural recursion over the abstract request.

    The predicate contributes its own features; a non-empty `with` clause
    contributes `bind`, because supplying a bound set is itself a capability
    a source may lack.
    """
    base = PREDICATE_FEATURES.get(request.predicate)
    if base is None:
        raise Refusal(f"unknown abstract predicate {request.predicate!r}")
    req = set(base)
    if request.bindings:
        req.add("bind")
    return frozenset(req)


# ---------------------------------------------------------------------------
# Base adapter
# ---------------------------------------------------------------------------


@dataclass
class Adapter:
    """A source Src = (eta, cap, ext, c)."""

    name: str
    namespace: str
    capabilities: FrozenSet[str]
    snapshot: str = "fixture-v1"

    #: Counts concrete requests issued. (V1) asserts this stays zero when the
    #: static check refuses, which is cor:refuse-before-contact made checkable.
    requests_issued: int = 0
    #: The last concrete form emitted by lowering, kept for (V14).
    last_lowered: Optional[str] = None

    def supports(self, features: Iterable[str]) -> bool:
        return set(features) <= set(self.capabilities)

    def missing(self, features: Iterable[str]) -> FrozenSet[str]:
        return frozenset(set(features) - set(self.capabilities))

    def lower(self, request, inputs: Dict[str, ResultSet]) -> str:
        """Low_Src: abstract request to canonical concrete form.

        Per cons:longhand this is the ONLY producer of concrete requests, and
        it emits one canonical spelling per abstract request.
        """
        raise NotImplementedError

    def extract(self, concrete: str, request, inputs: Dict[str, ResultSet]) -> ResultSet:
        """ext: run the concrete request against the local fixture."""
        raise NotImplementedError

    def cost(self, request, inputs: Dict[str, ResultSet]) -> float:
        """c(rho): the cost in requests of issuing rho with these inputs."""
        raise NotImplementedError

    def evaluate(self, request, inputs: Dict[str, ResultSet], effort: float) -> ResultSet:
        req = resolve_features(self, request)
        if not self.supports(req):
            raise Refusal(
                f"{self.name} lacks {sorted(self.missing(req))} for "
                f"{request.predicate!r}"
            )
        c = self.cost(request, inputs)
        if c > effort:
            raise Timeout(f"{self.name}: cost {c} exceeds allocated effort {effort}")
        concrete = self.lower(request, inputs)
        self.last_lowered = concrete
        self.requests_issued += 1
        return self.extract(concrete, request, inputs)


# ---------------------------------------------------------------------------
# (1) Graph-pattern adapter over a local RDF store
# ---------------------------------------------------------------------------


@dataclass
class GraphPatternAdapter(Adapter):
    """A conjunctive-pattern source backed by a local triple fixture.

    Triples are (subject, predicate, object) strings. The lowering emits
    longhand SPARQL: every predicate-object list expanded to separate patterns,
    every bound set supplied through VALUES, never by concatenation into the
    pattern text. That is cons:longhand (i) and (ii), and it is what makes
    thm:interpolation applicable.
    """

    triples: List[Tuple[str, str, str]] = field(default_factory=list)
    prefixes: Dict[str, str] = field(default_factory=dict)

    #: Abstract predicate -> the concrete predicate path it lowers to.
    paths: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.capabilities:
            self.capabilities = featureset("pattern", "path", "bind", "filter", "agg")

    # -- lowering ----------------------------------------------------------

    def lower(self, request, inputs: Dict[str, ResultSet]) -> str:
        path = self.paths.get(request.predicate, request.predicate)
        lines = [f"PREFIX {p}: <{u}>" for p, u in sorted(self.prefixes.items())]
        lines.append("SELECT DISTINCT ?s ?o WHERE {")

        bound_var = None
        for var, plan_var in request.bindings:
            bound_var = var
            members = sorted(inputs[plan_var].identifiers())
            # (ii): the bound set enters through VALUES. The identifiers are
            # emitted as a value list, not spliced into the pattern text.
            values = " ".join(f"<{m}>" for m in members)
            lines.append(f"  VALUES {var} {{ {values} }}")

        # (i): longhand. One triple pattern per line, no predicate-object list,
        # no comma-separated object list -- the construct of obs:2-397.
        subject = bound_var if bound_var else "?s"
        lines.append(f"  {subject} <{path}> ?o .")
        for arg in request.args:
            if isinstance(arg, str) and not arg.startswith("?"):
                lines.append(f"  ?s <{path}> <{arg}> .")
        lines.append("}")
        return "\n".join(lines)

    # -- extraction --------------------------------------------------------

    def extract(self, concrete: str, request, inputs: Dict[str, ResultSet]) -> ResultSet:
        path = self.paths.get(request.predicate, request.predicate)
        seeds: Optional[set] = None
        for _var, plan_var in request.bindings:
            ids = inputs[plan_var].identifiers()
            seeds = set(ids) if seeds is None else (seeds & set(ids))

        pairs: List[Tuple[Ident, Dict[str, Any]]] = []
        for s, p, o in self.triples:
            if p != path:
                continue
            if seeds is not None and s not in seeds:
                continue
            if seeds is None:
                literals = [a for a in request.args
                            if isinstance(a, str) and not a.startswith("?")]
                if literals and s not in literals:
                    continue
            pairs.append((o, {"_from": s, "_via": path}))
        return ResultSet.of(self.namespace, pairs)

    def cost(self, request, inputs: Dict[str, ResultSet]) -> float:
        """One request per bound input, floor 1 -- no `batch` declared here."""
        n = sum(len(inputs[pv]) for _v, pv in request.bindings)
        return float(max(1, n))


# ---------------------------------------------------------------------------
# (2) Lookup adapter over a local key-value fixture
# ---------------------------------------------------------------------------


@dataclass
class LookupAdapter(Adapter):
    """A flat-file REST stand-in: {lookup, link} and deliberately NOT pattern.

    Its restricted declaration is what makes thm:static fire on a plan that
    asks it for a join, and (V1) checks that the refusal happens with
    requests_issued still zero.
    """

    records: Dict[Ident, Dict[str, Any]] = field(default_factory=dict)
    links: Dict[str, Dict[Ident, List[Ident]]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.capabilities:
            self.capabilities = featureset("lookup", "link")

    def lower(self, request, inputs: Dict[str, ResultSet]) -> str:
        keys: List[str] = []
        for _var, plan_var in request.bindings:
            keys.extend(sorted(inputs[plan_var].identifiers()))
        keys.extend(str(a) for a in request.args if not str(a).startswith("?"))
        rel = str(request.args[0]) if request.args else ""
        # Canonical form: one line per key. No string concatenation of keys
        # into a template -- each key is a separate structural field.
        head = f"GET {self.name}/{request.predicate}"
        return "\n".join([head] + [f"  key = {k}" for k in sorted(set(keys))]
                         + ([f"  relation = {rel}"] if rel else []))

    def extract(self, concrete: str, request, inputs: Dict[str, ResultSet]) -> ResultSet:
        # Sorted, for the same reason TranslationMap.apply sorts: identifiers()
        # is a frozenset, and when two keys reach one value -- KEGG:E1 and
        # KEGG:E2 both link to MAP:00010 -- ResultSet.of merges on collision
        # with the last write winning, so the recorded `_from` depends on
        # iteration order. Under PYTHONHASHSEED 0..5 it alternates between the
        # two. The extent is identical either way; only the provenance moves.
        keys: List[Ident] = []
        for _var, plan_var in request.bindings:
            keys.extend(sorted(inputs[plan_var].identifiers()))

        pairs: List[Tuple[Ident, Dict[str, Any]]] = []
        if request.predicate == "link":
            rel = str(request.args[0]) if request.args else ""
            table = self.links.get(rel, {})
            for k in keys:
                for v in table.get(k, ()):
                    pairs.append((v, {"_from": k, "_relation": rel}))
        elif request.predicate == "record":
            for a in request.args:
                if isinstance(a, str) and not a.startswith("?"):
                    keys.append(a)
            for k in keys:
                if k in self.records:
                    pairs.append((k, dict(self.records[k])))
        return ResultSet.of(self.namespace, pairs)

    def cost(self, request, inputs: Dict[str, ResultSet]) -> float:
        n = sum(len(inputs[pv]) for _v, pv in request.bindings)
        if "batch" in self.capabilities:
            return 1.0
        return float(max(1, n))


# ---------------------------------------------------------------------------
# (3) Ontology adapter over a local class hierarchy
# ---------------------------------------------------------------------------


@dataclass
class OntologyAdapter(Adapter):
    """Transitive closure over subsumption: {path, lookup}. No filter, no agg."""

    parents: Dict[Ident, List[Ident]] = field(default_factory=dict)
    labels: Dict[Ident, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.capabilities:
            self.capabilities = featureset("path", "lookup")

    def _children(self) -> Dict[Ident, List[Ident]]:
        out: Dict[Ident, List[Ident]] = {}
        for child, ps in self.parents.items():
            for p in ps:
                out.setdefault(p, []).append(child)
        return out

    def lower(self, request, inputs: Dict[str, ResultSet]) -> str:
        roots = [str(a) for a in request.args if not str(a).startswith("?")]
        for _var, plan_var in request.bindings:
            roots.extend(sorted(inputs[plan_var].identifiers()))
        direction = "subClassOf*" if request.predicate == "ancestors_of" else "^subClassOf*"
        lines = ["SELECT DISTINCT ?c WHERE {"]
        if roots:
            lines.append("  VALUES ?root { " + " ".join(f"<{r}>" for r in sorted(set(roots))) + " }")
        lines.append(f"  ?c {direction} ?root .")
        lines.append("}")
        return "\n".join(lines)

    def extract(self, concrete: str, request, inputs: Dict[str, ResultSet]) -> ResultSet:
        roots: List[Ident] = [str(a) for a in request.args if not str(a).startswith("?")]
        for _var, plan_var in request.bindings:
            roots.extend(inputs[plan_var].identifiers())

        if request.predicate == "ancestors_of":
            step = self.parents
        elif request.predicate == "descendants_of":
            step = self._children()
        else:
            step = {}

        seen: set = set()
        frontier = list(roots)
        while frontier:
            u = frontier.pop()
            for v in step.get(u, ()):
                if v not in seen:
                    seen.add(v)
                    frontier.append(v)
        pairs = [(v, {"label": self.labels.get(v, "")}) for v in sorted(seen)]
        return ResultSet.of(self.namespace, pairs)

    def cost(self, request, inputs: Dict[str, ResultSet]) -> float:
        """A closure is one request: `path` is evaluated by the source."""
        return 1.0


# ---------------------------------------------------------------------------
# (4) Map adapter -- translation steps
# ---------------------------------------------------------------------------


@dataclass
class MapAdapter(Adapter):
    """Translation steps of def:map. The only adapter reporting retention.

    Because def:retention separates retention from amplification and
    prop:cardinality-uninformative shows their product is all the output
    cardinality reveals, both are recorded, never just the output size.
    """

    maps: Dict[str, TranslationMap] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.capabilities:
            self.capabilities = featureset("lookup", "link", "batch")

    def chain(self, names: Sequence[str]) -> List[TranslationMap]:
        try:
            return [self.maps[n] for n in names]
        except KeyError as e:  # pragma: no cover - registry error, not a verdict
            raise Refusal(f"unknown translation map {e.args[0]!r}") from e

    def apply_chain(
        self, names: Sequence[str], res: ResultSet
    ) -> Tuple[ResultSet, List[Dict[str, Any]]]:
        """Apply mu_1 .. mu_k, recording r and a at each stage.

        The per-stage record is what thm:retention(a) factorises over, and what
        (V7) checks the multiplicative identity against.
        """
        stages: List[Dict[str, Any]] = []
        current = res
        for mu in self.chain(names):
            s = current.identifiers()
            stages.append({
                "map": mu.name,
                "input_size": len(s),
                "retention": mu.retention(s),
                "amplification": mu.amplification(s),
            })
            current = mu.apply(current)
            stages[-1]["output_size"] = len(current)
        return current, stages

    def surviving_fraction(self, names: Sequence[str], res: ResultSet) -> float:
        """rho_{1..k}(S_0): the fraction of S_0 with at least one image in S_k.

        Computed by tracking trajectories, not by multiplying retentions --
        thm:retention(b),(c) bound it but do not determine it, which is the
        whole content of rem:bounds-gap.
        """
        s0 = res.identifiers()
        if not s0:
            return 1.0
        chain = self.chain(names)
        survivors = 0
        for u in s0:
            frontier = {u}
            for mu in chain:
                frontier = mu.image(frontier)
                if not frontier:
                    break
            if frontier:
                survivors += 1
        return survivors / len(s0)

    def lower(self, request, inputs: Dict[str, ResultSet]) -> str:  # pragma: no cover
        raise Refusal("map steps do not lower to a concrete request")

    def extract(self, concrete, request, inputs):  # pragma: no cover
        raise Refusal("map steps do not extract")

    def cost(self, request, inputs: Dict[str, ResultSet]) -> float:
        return 1.0


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


@dataclass
class Registry:
    """Resolve stage: source name -> adapter."""

    adapters: Dict[str, Adapter] = field(default_factory=dict)

    def register(self, adapter: Adapter) -> Adapter:
        self.adapters[adapter.name] = adapter
        return adapter

    def get(self, name: str) -> Adapter:
        if name not in self.adapters:
            raise Refusal(f"unknown source {name!r}")
        return self.adapters[name]

    def total_requests(self) -> int:
        return sum(a.requests_issued for a in self.adapters.values())

    def reset_counters(self) -> None:
        for a in self.adapters.values():
            a.requests_issued = 0
            a.last_lowered = None
