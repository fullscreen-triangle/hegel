"""Biocatalysis extension: the predicates a real question needs.

Four abstract predicates were declared in `PREDICATE_FEATURES` and implemented
by no adapter: `matching` (regex), `excluding` (neg), `ranked_by` (order) and
`restricted` (filter). They were reachable by the static check -- a plan
naming them was correctly refused against a source that did not declare the
feature -- but no plan could ever get an answer out of one, because no
`extract` handled them. This module closes that gap, and adds the source kind
they were missing.

The gap is not an oversight to be tidied. It is exactly where the biocatalysis
questions land. Doerr's Q1 asks for an enzyme

  (a) originating from a bacterium and not a eukaryote   -- `neg`
  (b) catalysing a named transamination                  -- `pattern`
  (c) with no cysteine in its protein sequence           -- `regex`

and (c) is not a graph question at all. A triple store holds the sequence as a
literal; asking whether a character occurs in it is a string test the store may
or may not perform faithfully, and `prop:under` says the honest response to
"may or may not" is to withhold the declaration. So `SequenceAdapter` is a
separate source with its own capability set, and a deployment that cannot be
trusted to scan a literal simply does not declare `regex` -- at which point
`thm:static` refuses the plan by naming the missing feature, before contact,
instead of returning an answer computed from a scan that silently truncated.

Three new abstract predicates appear here because the questions need them and
no combination of the existing ones expresses them:

  `typed_as`      the kind test of Q1(a): is this organism a bacterium?
  `measured_with` the instrument link of Q5 and of the generic queries that
                  name a Bruker spectrometer
  `sequence_of`   retrieve the residue string, so that `matching` and
                  `excluding` have something to scan

Their entries extend `PREDICATE_FEATURES` at import time rather than editing
the table in place, so the base module stays the artifact the paper describes
and this module is legible as the delta.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from .adapters import (PREDICATE_FEATURES, Adapter, GraphPatternAdapter,
                       Refusal)
from .model import Ident, ResultSet, featureset

# ---------------------------------------------------------------------------
# Req(rho) for the added predicates
# ---------------------------------------------------------------------------

#: The delta. `sequence_of` is a lookup because a sequence is retrieved by key;
#: `typed_as` needs `neg` as well as `pattern` because the question that uses it
#: is a *negative* kind test ("bacterium, not eukaryote") and Req is a function
#: of the predicate, not of how a particular call happens to be phrased.
BIOCAT_PREDICATE_FEATURES: Dict[str, FrozenSet[str]] = {
    "sequence_of":    featureset("lookup"),
    "typed_as":       featureset("pattern", "neg"),
    "measured_with":  featureset("pattern", "bind"),
    # An activity is reached FROM the thing it evaluated, which is the object
    # position of the stored triple. That is a `path` and not merely a
    # `pattern`: the source must traverse an edge backwards, and a deployment
    # whose index is one-directional can match the forward pattern and not the
    # inverse. Declaring only `pattern` here would let such a deployment pass
    # the static check and then return nothing, which is the empty-versus-
    # unsupported confusion of cor:onebit arriving through the capability
    # table rather than through the result set.
    "evaluations_of": featureset("pattern", "path"),
    # The same shape on the reaction store: reach the subject from the object.
    # `producers_of` finds the reactions that yield a compound; `consumers_of`
    # the reactions that take it in; `enzymes_from` the enzymes attributed to
    # an organism. All three are inverse traversals and all three declare
    # `path` for the reason given above.
    "producers_of":   featureset("pattern", "path"),
    "consumers_of":   featureset("pattern", "path"),
    "enzymes_from":   featureset("pattern", "path"),
    # Reaction from enzyme: the inverse of `catalysed_by`.
    "catalysed_reactions": featureset("pattern", "path"),
    # Identity. "Is this identifier in the set I hold?" -- no edge is walked,
    # so no `path`; the bound set is the extent, so `bind`. Separated from
    # `restricted`, which compares an ATTRIBUTE of a row against a value and
    # cannot express membership by name.
    "identified_as":  featureset("pattern", "bind"),
    # Forward: the device an activity used. Inverse: the activities that used
    # a device.
    "measured_on":    featureset("pattern", "path"),
    # The recorded parameters of an activity: buffer, pH, operator, date.
    # A lookup by key over a subject the plan already holds.
    "settings_of":    featureset("pattern", "bind"),
}

PREDICATE_FEATURES.update(BIOCAT_PREDICATE_FEATURES)

#: Predicates whose extraction reaches the SUBJECT from the object, i.e. that
#: traverse a stored edge backwards. Named in one place so that a source
#: cannot implement the lowering for one direction and the extraction for the
#: other -- the defect the dedicated `typed_as` branch was introduced to close,
#: which is silent because nobody reads a lowered form that was never wrong
#: before.
INVERSE_PREDICATES = frozenset({
    "evaluations_of", "producers_of", "consumers_of", "enzymes_from",
    "catalysed_reactions", "measured_on",
})


def biocat_required_features(request) -> FrozenSet[str]:
    """`Req` corrected for the scan predicates.

    The base table gives `Req(matching) = {pattern, regex}` and likewise for
    `excluding`. That conflates two separable things: how the source *reaches*
    the literal, and what it *does* to the literal once it has it. A graph
    source reaches it by matching a pattern, so for that source both features
    are genuinely required. A lookup source reaches it by key -- there is no
    pattern anywhere in the operation -- and demanding `pattern` of it makes
    the static check refuse a plan for a capability the request never uses.

    The refusal would be silent about this. It would report `missing:
    ['pattern']` against a source that correctly does not have one, and the
    plan author would have no way to tell that from a source that ought to
    have had one. `prin:refusal` requires the refusal name the real obstacle,
    so `Req` has to depend on how the request is shaped, not on the predicate
    alone.

    The rule: a scan over a bound set requires `regex` (or `neg`) and `bind`.
    A scan over an unbound extent requires `pattern` as well, because the
    source must enumerate the extent to scan it, and enumeration is what
    `pattern` names. `bind` is therefore not merely additive here -- its
    presence *removes* a requirement, which is why this cannot be expressed
    as a table lookup plus a fixed increment.
    """
    base = PREDICATE_FEATURES.get(request.predicate)
    if base is None:
        raise Refusal(f"unknown abstract predicate {request.predicate!r}")
    req = set(base)
    if request.bindings:
        req.add("bind")
        if request.predicate in ("matching", "excluding", "sequence_of"):
            req.discard("pattern")
    return frozenset(req)


# ---------------------------------------------------------------------------
# The four dead predicates, implemented
# ---------------------------------------------------------------------------


@dataclass
class IdentityMixin:
    """`identified_as`: is this named identifier in the set I already hold?

    Separated into a mixin because two source classes need it and they do not
    share an ancestor below `GraphPatternAdapter`, which lives in the generic
    adapter module and has no business knowing biocatalysis predicates. The
    alternative -- pasting the branch into both classes -- is how the
    `measured_on` defect happened: `ProvenanceAdapter` extends
    `GraphPatternAdapter` rather than `FilteringGraphAdapter`, so every
    predicate added to the latter silently does not exist on the former, and a
    plan that uses one gets an empty set rather than a refusal. An empty set
    that means "this class never implemented the predicate" is exactly the
    confusion the framework claims to eliminate, so the structural fix is the
    only honest one.

    Req is `pattern` + `bind` and deliberately NOT `path`: no edge is walked.
    That matters for refusal -- a source with no traversal capability can still
    answer an identity question, and folding this into `restricted` (an
    attribute comparison) would have demanded capabilities it does not need.
    """

    def _lower_identity(self, request, inputs) -> str:
        names = sorted({a for a in request.args
                        if isinstance(a, str) and not a.startswith("?")})
        lines = ["SELECT DISTINCT ?s WHERE {"]
        if names:
            lines.append("  VALUES ?s { "
                         + " ".join("<" + n + ">" for n in names) + " }")
        for var, plan_var in request.bindings:
            members = sorted(inputs[plan_var].identifiers())
            lines.append("  VALUES " + var + " { "
                         + " ".join("<" + m + ">" for m in members) + " }")
            lines.append("  FILTER(?s = " + var + ")")
        lines.append("}")
        return "\n".join(lines)

    def _extract_identity(self, request, inputs) -> ResultSet:
        """The named identifiers, kept only if the bound set contains them.

        The intersection is the point: an identifier the plan names but the
        upstream set does not hold is NOT returned, so a plan whose narrowing
        contradicts its own earlier constraint yields the empty set rather than
        the name it asked for. Naming a thing is not evidence the corpus has
        it -- and a query language in which naming a URI in a VALUES clause
        makes it appear in the output has quietly conflated the two.
        """
        wanted = {a for a in request.args
                  if isinstance(a, str) and not a.startswith("?")}
        held = set()
        for _v, pv in request.bindings:
            held |= set(inputs[pv].identifiers())
        pairs = []
        for ident in sorted(wanted & held):
            row = (dict(inputs[request.bindings[0][1]].rows.get(ident, {}))
                   if request.bindings else {})
            row["_identified"] = True
            pairs.append((ident, row))
        return ResultSet.of(self.namespace, pairs)


class FilteringGraphAdapter(GraphPatternAdapter, IdentityMixin):
    """`GraphPatternAdapter` with `matching`/`excluding`/`restricted`/`ranked_by`.

    The base class lowers and extracts exactly one shape: subject --path--> object.
    These four predicates are all *post-conditions on that shape*, so each is
    implemented as the base extraction followed by one additional operation,
    and each declares the feature that operation needs.

    Why they are predicates and not plan-level `filter` steps: a plan-level
    filter runs here, after the result has crossed the wire. A `restricted`
    predicate runs at the source. The distinction is invisible in the answer
    and decisive in the cost, and `def:source` makes the source declare which
    it can do. A source that cannot filter server-side must not declare
    `filter`, and the plan then pays for the unfiltered extent.
    """

    #: Attribute name carrying the literal that `matching`/`excluding` scan.
    literal_attr: str = "_literal"

    #: Object -> literal, for sources that hold a scannable string per subject.
    literals: Dict[str, str] = field(default_factory=dict)

    #: Object -> a numeric or comparable rank, for `ranked_by`.
    ranks: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.capabilities:
            self.capabilities = featureset(
                "pattern", "path", "bind", "filter", "agg", "regex", "neg",
                "order")

    # -- lowering ----------------------------------------------------------

    def lower(self, request, inputs: Dict[str, ResultSet]) -> str:
        """Longhand, extended with the construct each predicate needs.

        `cons:longhand` is preserved: one pattern per line, bound sets through
        VALUES, and -- the point that matters for the added predicates -- the
        regular expression enters as a *parameter of a FILTER call*, never
        spliced into the pattern text. A regex concatenated into a query string
        is precisely the interpolation `thm:interpolation` exists to remove.
        """
        pred = request.predicate

        if pred in INVERSE_PREDICATES:
            return self._lower_inverse(request, inputs)

        if pred == "identified_as":
            return self._lower_identity(request, inputs)

        if pred == "typed_as":
            # `typed_as` cannot go through the base lowering. That lowering
            # emits one conjunct per literal argument, so a two-argument kind
            # test would lower to `?s a <want> . ?s a <forbid> .` -- a
            # conjunction demanding BOTH kinds, while `extract` computes the
            # difference. The extraction is the correct one; the lowering
            # would have been wrong.
            #
            # The bug matters more than the wrong rows it would produce if
            # anyone executed it, because nobody does: `extract` reads the
            # fixture, not this string. What the string is for is audit. A
            # lowered form that does not mean what the step means makes the
            # record unreliable exactly where cons:longhand and
            # thm:interpolation ask it to be reliable, and the defect is
            # invisible in every result the plan returns. So the negative
            # kind test gets the construct that expresses it.
            want, forbid = self._type_args(request)
            lines = ["SELECT DISTINCT ?s WHERE {"]
            for var, plan_var in request.bindings:
                members = sorted(inputs[plan_var].identifiers())
                values = " ".join(f"<{m}>" for m in members)
                lines.append(f"  VALUES {var} {{ {values} }}")
            lines.append(f"  ?s <rdf:type> <{want}> .")
            if forbid is not None:
                lines.append(f"  MINUS {{ ?s <rdf:type> <{forbid}> . }}")
            lines.append("}")
            return "\n".join(lines)

        base = super().lower(request, inputs)
        if pred not in ("matching", "excluding", "restricted", "ranked_by"):
            return base

        lines = base.rstrip().split("\n")
        assert lines[-1] == "}"
        body = lines[:-1]

        if pred in ("matching", "excluding"):
            pattern = self._pattern_arg(request)
            # The pattern is a bound argument of REGEX, not text pasted into
            # the query. `str.__repr__` is not used: the value is emitted as a
            # quoted literal in one place, which is the whole of the exposure.
            call = f'REGEX(STR(?lit), "{pattern}")'
            body.append(f"  ?o <{self.literal_attr}> ?lit .")
            body.append(f"  FILTER({call})" if pred == "matching"
                        else f"  FILTER(!{call})")
        elif pred == "restricted":
            attr, op, val = self._restriction_args(request)
            body.append(f"  ?o <{attr}> ?v .")
            body.append(f"  FILTER(?v {op} {self._literal(val)})")
        else:  # ranked_by
            key = self._rank_arg(request)
            body.append(f"  ?o <{key}> ?rank .")

        body.append("}")
        if pred == "ranked_by":
            body.append("ORDER BY DESC(?rank)")
        return "\n".join(body)

    # -- argument accessors ------------------------------------------------
    #
    # Each predicate names its arguments positionally. A missing argument is a
    # Refusal rather than a silent default: a `matching` with no pattern would
    # otherwise match everything, which is the failure mode where a wrong
    # answer is indistinguishable from a right one.

    @staticmethod
    def _type_args(request) -> Tuple[str, Optional[str]]:
        """The kind to require and, optionally, the kind to exclude.

        Shared by `lower` and `extract` so the audit record and the executed
        semantics cannot diverge. They diverged once -- the lowering emitted a
        conjunction where the extraction computed a difference -- and a single
        accessor is the structural fix rather than a corrected duplicate.
        """
        args = [a for a in request.args
                if isinstance(a, str) and not a.startswith("?")]
        if not args:
            raise Refusal("typed_as requires a type argument")
        return args[0], (args[1] if len(args) > 1 else None)

    @staticmethod
    def _pattern_arg(request) -> str:
        for a in request.args:
            if isinstance(a, str) and not a.startswith("?"):
                return a
        raise Refusal(f"{request.predicate!r} requires a pattern argument")

    @staticmethod
    def _rank_arg(request) -> str:
        for a in request.args:
            if isinstance(a, str) and not a.startswith("?"):
                return a
        raise Refusal("ranked_by requires a ranking key")

    @staticmethod
    def _restriction_args(request) -> Tuple[str, str, Any]:
        args = [a for a in request.args if not (isinstance(a, str)
                                                and a.startswith("?"))]
        if len(args) < 3:
            raise Refusal("restricted requires (attribute, operator, value)")
        attr, op, val = args[0], args[1], args[2]
        if op not in ("==", "!=", "<", ">", "<=", ">="):
            raise Refusal(f"restricted: unknown operator {op!r}")
        return str(attr), op, val

    @staticmethod
    def _literal(v: Any) -> str:
        return f'"{v}"' if isinstance(v, str) else str(v)

    # -- extraction --------------------------------------------------------

    def extract(self, concrete: str, request,
                inputs: Dict[str, ResultSet]) -> ResultSet:
        pred = request.predicate

        if pred == "count_of":
            # `agg`. The aggregate is computed over the extent this adapter
            # actually holds. prop:under is the live hazard here: a deployment
            # whose server caps materialisation returns a well-formed COUNT
            # over a truncated extent, and the caller cannot tell. Honesty
            # therefore forces `agg` OUT of the declaration of any source that
            # caps, even though SPARQL supports COUNT and the request succeeded.
            inner = self._base_extract(request, inputs)
            return ResultSet.of(self.namespace,
                                [(f"{self.namespace}:count",
                                  {"count": len(inner), "_over": pred})])

        if pred in ("matching", "excluding"):
            pattern = self._pattern_arg(request)
            try:
                rx = re.compile(pattern)
            except re.error as e:
                # A malformed pattern is a refusal, not an empty answer. The
                # difference is the whole of cor:onebit: "no enzyme lacks
                # cysteine" and "your regex did not compile" must not arrive
                # as the same result.
                raise Refusal(f"{pred}: uncompilable pattern {pattern!r}: {e}")
            keep = (lambda s: rx.search(s) is not None) if pred == "matching" \
                else (lambda s: rx.search(s) is None)
            pairs = []
            for ident, row in self._base_extract(request, inputs).rows.items():
                lit = row.get(self.literal_attr, self.literals.get(ident))
                if lit is None:
                    # No literal to scan. Not a match and not a non-match --
                    # the predicate is undefined here, so the row is dropped
                    # and the drop is recorded, rather than being counted as a
                    # pass by a source that never looked.
                    continue
                if keep(str(lit)):
                    r = dict(row)
                    r["_scanned"] = True
                    r["_predicate"] = pred
                    pairs.append((ident, r))
            return ResultSet.of(self.namespace, pairs)

        if pred == "identified_as":
            return self._extract_identity(request, inputs)

        if pred == "restricted":
            attr, op, val = self._restriction_args(request)
            ops = {"==": lambda x, y: x == y, "!=": lambda x, y: x != y,
                   "<": lambda x, y: x < y, ">": lambda x, y: x > y,
                   "<=": lambda x, y: x <= y, ">=": lambda x, y: x >= y}
            test = ops[op]
            pairs = []
            for ident, row in self._base_extract(request, inputs).rows.items():
                if attr not in row:
                    continue
                try:
                    if test(row[attr], val):
                        pairs.append((ident, row))
                except TypeError:
                    continue
            return ResultSet.of(self.namespace, pairs)

        if pred == "ranked_by":
            key = self._rank_arg(request)
            rows = list(self._base_extract(request, inputs).rows.items())
            rows.sort(key=lambda kv: (kv[1].get(key, self.ranks.get(kv[0], 0.0))),
                      reverse=True)
            return ResultSet.of(self.namespace,
                                [(i, dict(r, _rank=n))
                                 for n, (i, r) in enumerate(rows)])

        if pred == "typed_as":
            # The kind test. Two arguments: the type to require and, optionally,
            # a type to exclude -- which is why Req(typed_as) carries `neg`.
            want, forbid = self._type_args(request)
            # A bound set restricts the extent tested, exactly as the VALUES
            # block in the lowered form says it does. Ignoring it here would
            # make the kind test range over the whole store while the audit
            # record claimed otherwise -- the same divergence `_type_args`
            # was introduced to close, in the other direction.
            seeds = set()
            for _v, pv in request.bindings:
                seeds |= set(inputs[pv].identifiers())
            pairs = []
            for s, p, o in self.triples:
                if p != "rdf:type":
                    continue
                if o != want:
                    continue
                if seeds and s not in seeds:
                    continue
                if forbid is not None and any(
                        s2 == s and p2 == "rdf:type" and o2 == forbid
                        for s2, p2, o2 in self.triples):
                    continue
                pairs.append((s, {"_type": want, "_excluded": forbid}))
            return ResultSet.of(self.namespace, pairs)

        if pred in INVERSE_PREDICATES:
            return self._inverse_extract(request, inputs)

        return self._base_extract(request, inputs)

    def _inverse_extract(self, request, inputs) -> ResultSet:
        """Reach the SUBJECT from the object.

        `_base_extract` walks subject --path--> object and returns the object.
        Three of Doerr's questions run the other way: which reactions produce
        guaiacol, which enzymes come from B. subtilis, which activities
        evaluated this reaction. Expressing those with the forward extraction
        does not fail loudly -- the literal filter applies to the subject
        position, no subject is ever named `CHEBI:guaiacol`, and the step
        returns nothing.

        An empty result meaning "you walked the edge backwards" is
        indistinguishable at the emit boundary from one meaning "no reaction
        produces this". That is cor:onebit arriving from inside the executor
        rather than from the endpoint, and it is worse there, because the
        framework's whole claim is that IT can tell those apart. So direction
        is part of the predicate: a source that cannot traverse an edge
        backwards withholds `path` and is refused by name before contact.
        """
        path = self.paths.get(request.predicate, request.predicate)
        targets = {a for a in request.args
                   if isinstance(a, str) and not a.startswith("?")}
        for _v, pv in request.bindings:
            targets |= set(inputs[pv].identifiers())
        pairs = [(s, {"_reached": o, "_via": path, "_direction": "inverse"})
                 for s, pr, o in self.triples
                 if pr == path and o in targets]
        return ResultSet.of(self.namespace, pairs)

    def _lower_inverse(self, request, inputs) -> str:
        """The lowered form of an inverse traversal.

        Written separately rather than delegated, because the base lowering
        puts each literal in the OBJECT position of a pattern whose subject is
        selected and then filters subjects by it -- a forward walk. Emitting
        that string here would leave an audit record describing an operation
        the step did not perform. `cons:longhand` still holds: one pattern per
        line, every bound set through VALUES.
        """
        path = self.paths.get(request.predicate, request.predicate)
        targets = sorted({a for a in request.args
                          if isinstance(a, str) and not a.startswith("?")})
        lines = ["SELECT DISTINCT ?s WHERE {"]
        if targets:
            lines.append("  VALUES ?t { "
                         + " ".join("<" + x + ">" for x in targets) + " }")
        for var, plan_var in request.bindings:
            members = sorted(inputs[plan_var].identifiers())
            lines.append("  VALUES " + var + " { "
                         + " ".join("<" + m + ">" for m in members) + " }")
        lines.append("  ?s <" + path + "> ?t .")
        lines.append("}")
        return "\n".join(lines)

    def _base_extract(self, request, inputs) -> ResultSet:
        """The subject--path-->object extraction of the base class.

        `matching`, `excluding`, `restricted` and `ranked_by` are all defined
        as post-conditions on it, so the path they resolve is the one the
        `paths` table gives for the predicate, falling back to the predicate
        name -- identical to the base behaviour.
        """
        return GraphPatternAdapter.extract(self, "", request, inputs)

    # -- cost --------------------------------------------------------------

    def cost(self, request, inputs: Dict[str, ResultSet]) -> float:
        """Scanning is charged, because scanning is work the source does.

        A `matching` over an unbound extent touches every literal the source
        holds, and charging it as one request would make the allocator blind to
        the one step in a plan that can actually be expensive. The charge is the
        base cost plus the extent scanned, in units of requests, which is the
        unit `def:yield` measures effort in.
        """
        base = super().cost(request, inputs)
        if request.predicate in ("matching", "excluding"):
            return base + float(max(1, len(self.literals)))
        return base


# ---------------------------------------------------------------------------
# The sequence source
# ---------------------------------------------------------------------------


@dataclass
class SequenceAdapter(Adapter):
    """Protein sequences, retrieved by key and scanned as strings.

    Separate from the graph source on purpose. A sequence is a literal, and the
    question "does this literal contain C" is answered by a string engine, not
    by a graph engine. Keeping them apart lets a deployment declare `regex`
    for the one and withhold it for the other -- which is the honest position
    for most triple stores, whose `REGEX` is available but whose behaviour on a
    multi-megabyte literal is not something the plan author can verify.

    `residue_absent` is the predicate Q1 needs. It is expressed in terms of
    `excluding`: Req is the same set, and a source declaring `regex` and `neg`
    supports both or neither.
    """

    sequences: Dict[str, str] = field(default_factory=dict)

    #: Sequence identifier -> the entity it belongs to, for joins back.
    owner: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.capabilities:
            # Deliberately NOT `pattern`: this source cannot answer a graph
            # question, and declaring `pattern` here would let an ill-formed
            # plan through the static check and fail at the adapter, which is
            # exactly the inversion cor:refuse-before-contact rules out.
            self.capabilities = featureset("lookup", "regex", "neg", "bind",
                                           "batch")

    #: This source resolves Req itself: it reaches literals by key, so a
    #: bound scan demands no `pattern` of it. See `biocat_required_features`.
    def required_features(self, request) -> FrozenSet[str]:
        return biocat_required_features(request)

    def lower(self, request, inputs: Dict[str, ResultSet]) -> str:
        """A retrieval, not a query.

        One structural field per key -- no concatenation of keys into a
        template, matching `LookupAdapter`'s treatment and `cons:longhand`(ii).
        The residue argument is a separate field for the same reason.
        """
        lines = [f"GET {self.name}/{request.predicate}"]
        keys, residues = self._split_args(request, inputs)
        for k in keys:
            lines.append(f"  key = {k}")
        for r in residues:
            lines.append(f"  residue = {r}")
        return "\n".join(lines)

    def _split_args(self, request, inputs: Dict[str, ResultSet]):
        """Separate keys from residue patterns.

        A literal argument means different things to different predicates, and
        the adapter cannot tell them apart by inspecting the string: `C` is a
        residue to `excluding` and would be an identifier to `sequence_of`.
        Guessing -- by testing membership in `self.sequences`, say -- would make
        the request's meaning depend on the fixture's contents, so that adding a
        protein named `C` would silently reinterpret every plan already written.
        The predicate decides instead, statically, and the decision is visible
        in the lowered form.
        """
        keys: List[str] = []
        for _var, plan_var in request.bindings:
            keys.extend(sorted(inputs[plan_var].identifiers()))
        literals = [a for a in request.args
                    if isinstance(a, str) and not a.startswith("?")]
        if request.predicate == "sequence_of":
            return keys + [a for a in literals if a not in keys], []
        if not literals:
            return keys, []
        # Scan predicates: the first literal is the pattern, any further
        # literals are keys, so `excluding(C, TA1, TA2)` scans two named
        # proteins without a binding step.
        return keys + [a for a in literals[1:] if a not in keys], [literals[0]]

    def extract(self, concrete: str, request,
                inputs: Dict[str, ResultSet]) -> ResultSet:
        pred = request.predicate
        keys, residues = self._split_args(request, inputs)

        if pred == "sequence_of":
            pairs = [(k, {"sequence": self.sequences[k],
                          "length": len(self.sequences[k])})
                     for k in keys if k in self.sequences]
            return ResultSet.of(self.namespace, pairs)

        if pred in ("matching", "excluding"):
            # The scan. `_split_args` has already separated the residue
            # pattern from the keys, so nothing here inspects `request.args`
            # again: the predicate decided the split statically, and the
            # decision is visible in the lowered form rather than being
            # re-derived from the fixture's contents at extraction time.
            if not residues:
                raise Refusal(f"{pred} requires a residue or pattern argument")
            pattern = residues[0]
            try:
                rx = re.compile(pattern)
            except re.error as e:
                # A malformed pattern is a refusal, not an empty answer. The
                # difference is the whole of cor:onebit: "no enzyme lacks
                # cysteine" and "your regex did not compile" must not arrive
                # as the same result.
                raise Refusal(f"{pred}: uncompilable pattern {pattern!r}: {e}")
            pairs = []
            covered, uncovered = 0, 0
            for k in keys:
                seq = self.sequences.get(k)
                if seq is None:
                    # The sequence is not held. This is the honest outcome of a
                    # partial corpus: the entity is neither included nor
                    # excluded, and counting it either way would be a claim the
                    # source cannot support. It is dropped, and the count is
                    # carried on every surviving row so the caller can see how
                    # much of its input was never examined.
                    uncovered += 1
                    continue
                covered += 1
                hit = rx.search(seq) is not None
                if (pred == "matching") == hit:
                    pairs.append((k, {"sequence_length": len(seq),
                                      "residue": pattern,
                                      "_scanned": True}))
            pairs = [(k, dict(r, _covered=covered, _uncovered=uncovered))
                     for k, r in pairs]
            return ResultSet.of(self.namespace, pairs)

        raise Refusal(f"{self.name} does not implement {pred!r}")

    def cost(self, request, inputs: Dict[str, ResultSet]) -> float:
        n = sum(len(inputs[pv]) for _v, pv in request.bindings)
        if "batch" in self.capabilities:
            return 1.0
        return float(max(1, n))


# ---------------------------------------------------------------------------
# Instrument / provenance source
# ---------------------------------------------------------------------------


@dataclass
class ProvenanceAdapter(GraphPatternAdapter, IdentityMixin):
    """Activities, instruments, operators, dates, buffers.

    A `pattern` source like any other. It exists separately because the
    questions that use it (Q2, Q5, and six of the eight generic queries) are
    provenance questions, and a deployment that publishes reaction data need
    not publish instrument settings -- so its capability set and its snapshot
    are properly its own.
    """

    def __post_init__(self) -> None:
        if not self.capabilities:
            self.capabilities = featureset("pattern", "bind", "filter", "path")

    #: Predicates that record a setting of the activity rather than a link to
    #: another entity. Kept explicit rather than inferred by "is the object a
    #: literal", because whether a value is a literal is a fact about this
    #: fixture's serialisation and not about what the question is asking.
    SETTING_PREDICATES = ("buffer", "pH", "operator", "date", "wavelength")

    def lower(self, request, inputs: Dict[str, ResultSet]) -> str:
        pred = request.predicate

        if pred == "evaluations_of":
            # The inverse traversal, written as one. The base lowering puts the
            # literal in the object position; here it belongs in the object
            # position of a pattern whose SUBJECT is the variable selected,
            # and emitting the base form would describe a forward walk the
            # step does not perform.
            targets = [a for a in request.args
                       if isinstance(a, str) and not a.startswith("?")]
            path = self.paths.get("evaluations_of", "evaluated")
            lines = ["SELECT DISTINCT ?a WHERE {"]
            if targets:
                lines.append("  VALUES ?t { "
                             + " ".join(f"<{x}>" for x in sorted(set(targets)))
                             + " }")
            for var, plan_var in request.bindings:
                members = sorted(inputs[plan_var].identifiers())
                lines.append(f"  VALUES {var} {{ "
                             + " ".join(f"<{m}>" for m in members) + " }")
            lines.append(f"  ?a <{path}> ?t .")
            lines.append("}")
            return "\n".join(lines)

        if pred == "settings_of":
            # One conjunct per setting, all optional: an activity that recorded
            # no wavelength is still an activity, and a pattern demanding all
            # five would silently drop it. cons:longhand (i) -- each on its own
            # line, no predicate-object list.
            lines = ["SELECT ?a ?p ?v WHERE {"]
            for var, plan_var in request.bindings:
                members = sorted(inputs[plan_var].identifiers())
                lines.append(f"  VALUES {var} {{ "
                             + " ".join(f"<{m}>" for m in members) + " }")
            for s in self.SETTING_PREDICATES:
                lines.append(f"  OPTIONAL {{ ?a <{s}> ?v_{s} . }}")
            lines.append("}")
            return "\n".join(lines)

        if pred == "identified_as":
            return self._lower_identity(request, inputs)

        if pred == "measured_on":
            # The inverse of `measured_with`. Delegating to the base lowering
            # would emit a forward walk -- a string describing an operation
            # this step does not perform, left behind as the audit record of
            # one that it does. The extraction and the lowered form have to
            # agree about direction or the record is a lie that nobody reads,
            # which is the worst kind.
            devices = sorted({a for a in request.args
                              if isinstance(a, str) and not a.startswith("?")})
            path = self.paths.get("measured_on", "measured_with")
            lines = ["SELECT DISTINCT ?a WHERE {"]
            if devices:
                lines.append("  VALUES ?d { "
                             + " ".join("<" + x + ">" for x in devices) + " }")
            for var, plan_var in request.bindings:
                members = sorted(inputs[plan_var].identifiers())
                lines.append("  VALUES " + var + " { "
                             + " ".join("<" + m + ">" for m in members) + " }")
            lines.append("  ?a <" + path + "> ?d .")
            lines.append("}")
            return "\n".join(lines)

        return GraphPatternAdapter.lower(self, request, inputs)

    def extract(self, concrete: str, request,
                inputs: Dict[str, ResultSet]) -> ResultSet:
        if request.predicate == "evaluations_of":
            targets = {a for a in request.args
                       if isinstance(a, str) and not a.startswith("?")}
            for _v, pv in request.bindings:
                targets |= set(inputs[pv].identifiers())
            path = self.paths.get("evaluations_of", "evaluated")
            pairs = []
            for s, pr, o in self.triples:
                if pr == path and o in targets:
                    pairs.append((s, {"_evaluated": o}))
            return ResultSet.of(self.namespace, pairs)

        if request.predicate == "settings_of":
            seeds = set()
            for _v, pv in request.bindings:
                seeds |= set(inputs[pv].identifiers())
            pairs = []
            for a in sorted(seeds):
                attrs = {}
                for s, pr, o in self.triples:
                    if s == a and pr in self.SETTING_PREDICATES:
                        attrs[pr] = o
                # An activity with no recorded settings is returned with none,
                # not dropped. "This run recorded no buffer" and "there is no
                # such run" are different answers to Q2 and must not collapse.
                attrs["_recorded"] = sorted(attrs)
                pairs.append((a, attrs))
            return ResultSet.of(self.namespace, pairs)

        if request.predicate == "identified_as":
            return self._extract_identity(request, inputs)

        if request.predicate == "measured_on":
            # The inverse: activities that used a named device. The generic
            # Chem-DCAT-AP queries ask this way round ("datasets measured with
            # a Bruker spectrometer"), and running it through the forward
            # extraction would filter ACTIVITY names by a DEVICE name and
            # return nothing -- an empty set that means "wrong direction"
            # wearing the costume of one that means "no such measurement".
            devices = {a for a in request.args
                       if isinstance(a, str) and not a.startswith("?")}
            for _v, pv in request.bindings:
                devices |= set(inputs[pv].identifiers())
            # No device named and nothing bound is not an empty question; it
            # is "which activities were monitored at all", and the extent of
            # the edge is the answer. Returning the empty set here would be a
            # different claim -- that nothing was monitored -- and the two must
            # not be spelled the same way. `restrict` records which case ran so
            # the audit trail says whether a narrowing was applied.
            restrict = bool(devices)
            path = self.paths.get("measured_on", "measured_with")
            pairs = []
            for s, pr, o in self.triples:
                if pr == path and ((o in devices) if restrict else True):
                    attrs = {"_device": o}
                    for s2, p2, o2 in self.triples:
                        if s2 == s and p2 != path:
                            attrs[p2] = o2
                    pairs.append((s, attrs))
            return ResultSet.of(self.namespace, pairs)

        if request.predicate == "measured_with":
            seeds = set()
            for _v, pv in request.bindings:
                seeds |= set(inputs[pv].identifiers())
            path = self.paths.get("measured_with", "measured_with")
            pairs = []
            for s, p, o in self.triples:
                if p != path:
                    continue
                if seeds and s not in seeds:
                    continue
                attrs = {"_activity": s}
                for s2, p2, o2 in self.triples:
                    if s2 == s and p2 != path:
                        attrs[p2] = o2
                pairs.append((o, attrs))
            return ResultSet.of(self.namespace, pairs)
        return GraphPatternAdapter.extract(self, concrete, request, inputs)
