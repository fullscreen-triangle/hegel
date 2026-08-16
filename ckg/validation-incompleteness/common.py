"""
Shared machinery for the graph-incompleteness validation suite.

Implements, once, every construction the paper defines, so that the experiment
modules test the definitions rather than re-implementing them:

  * Model / Corpus / Engine     -- Definitions 2.2, 2.3, 2.7
  * Feature alphabet            -- Definition 2.6
  * Exp / Der / Ans             -- Definitions 3.1, 3.2, 3.3
  * Verdict + evaluation order  -- Definitions 4.1, 4.2
  * Controls and vacuity        -- Definitions 6.1, 6.2, 6.3
  * Blockers                    -- Definition 7.1

Two engines are implemented here rather than imported:

  OpenWorldEngine  -- certain-answer semantics, no unique-name assumption,
                      no closure. Refuses where the entailment does not hold.
  RuleEngine       -- least-model semantics over a Herbrand universe, so the
                      unique-name assumption is INHERITED (Prop 8.3) rather
                      than lowered.

They are ours, so nothing here tests a third-party reasoner's conformance.
What they do test is that the paper's definitions, implemented faithfully,
have the consequences the paper claims -- including the ones that read as
defects and are not (Cor 8.4).

Deterministic throughout: every stochastic experiment seeds explicitly.
"""

from __future__ import annotations

import itertools
import json
import os
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return OUTPUT_DIR


def save_result(result, filename):
    ensure_output_dir()
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    return path


def utc_stamp():
    return datetime.now(timezone.utc).isoformat()


def verdict(passed):
    return "PASS" if passed else "FAIL"


# ---------------------------------------------------------------------------
# Feature alphabet -- Definition 2.6
#
# TRANSITIVE is deliberately absent and appears only as the two split symbols
# (Remark 2.5). DISJOINTNESS and UNIQUE_NAMES are model features and are listed
# here for the reason Remark 2.6 gives: a construct absent from the alphabet is
# a construct whose omission by a compiler is undetectable (Prop 5.7).
# ---------------------------------------------------------------------------

SUBSUMPTION = "SUBSUMPTION"
EXISTENTIAL = "EXISTENTIAL"
VALUE = "VALUE"
NEGATION = "NEGATION"
COUNTING = "COUNTING"
TRANSITIVE_AXIOM = "TRANSITIVE_AXIOM"
TRANSITIVE_QUERY = "TRANSITIVE_QUERY"
BOUNDED_PATH = "BOUNDED_PATH"
DISJOINTNESS = "DISJOINTNESS"
UNIQUE_NAMES = "UNIQUE_NAMES"

FEATURES = frozenset(
    {
        SUBSUMPTION,
        EXISTENTIAL,
        VALUE,
        NEGATION,
        COUNTING,
        TRANSITIVE_AXIOM,
        TRANSITIVE_QUERY,
        BOUNDED_PATH,
        DISJOINTNESS,
        UNIQUE_NAMES,
    }
)

# The conflated alphabet of Proposition 5.6, kept so experiment 09 can run the
# comparison rather than assert it.
CONFLATED_TRANSITIVE = "TRANSITIVE"


# ---------------------------------------------------------------------------
# Verdict labels -- Definition 4.1
# ---------------------------------------------------------------------------

ANSWERED = "answered"
CANNOT_EXPRESS = "cannot-express"
NOT_DERIVABLE = "not-derivable"
NO_QUERY_SURFACE = "no-query-surface"
TIMEOUT = "timeout"
CONTROL_VACUOUS = "control-vacuous"
CONSTRAINT_INERT = "constraint-inert"

NON_ANSWER_LABELS = frozenset(
    {
        CANNOT_EXPRESS,
        NOT_DERIVABLE,
        NO_QUERY_SURFACE,
        TIMEOUT,
        CONTROL_VACUOUS,
        CONSTRAINT_INERT,
    }
)


class Verdict:
    """
    A label with a label-specific payload.

    `answers` is a property rather than a field, and it raises for every label
    but ANSWERED. That is Theorem 4.4 made mechanical: a consumer that tries to
    read an answer set off a refusal gets an exception rather than an empty
    list, so the conflation of section 1.1 cannot be reintroduced by a caller
    who forgets to check the label.

    CONSTRAINT_INERT carries the two coinciding answer sets in `payload` as
    EVIDENCE of inertness -- deliberately not through `answers`, since they are
    not an answer to the question.
    """

    __slots__ = ("label", "payload")

    def __init__(self, label, payload=None):
        self.label = label
        self.payload = payload

    @property
    def answers(self):
        if self.label != ANSWERED:
            raise ValueError(
                f"verdict {self.label!r} carries no answer set; "
                "read .payload and handle the label"
            )
        return self.payload["answers"]

    @property
    def certified(self):
        if self.label != ANSWERED:
            raise ValueError(f"verdict {self.label!r} carries no certification")
        return self.payload["certified"]

    def to_json(self):
        return {"label": self.label, "payload": _jsonable(self.payload)}

    def __repr__(self):
        return f"Verdict({self.label!r})"


def _jsonable(obj):
    if isinstance(obj, (set, frozenset)):
        return sorted(str(x) for x in obj)
    if isinstance(obj, tuple):
        return [_jsonable(x) for x in obj]
    if isinstance(obj, list):
        return [_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    return obj


# ---------------------------------------------------------------------------
# Model, Corpus -- Definitions 2.2, 2.3
# ---------------------------------------------------------------------------


class Model:
    """
    Schema plus axioms. `grammar` is the set of constructs the axiom and query
    languages admit; a construct outside it makes any question requiring it
    inexpressible (E1).

    `closed_roles` and `distinct_sets` are the two things Proposition 3.4 needs
    and are recorded SEPARATELY and SCOPED. `distinct_sets` is a list of sets
    of individuals known pairwise distinct, not a global boolean -- Remark 3.5
    is the whole reason for that shape.
    """

    def __init__(
        self,
        name,
        grammar,
        concepts=(),
        roles=(),
        individuals=(),
        subsumptions=(),
        disjoint_pairs=(),
        transitive_roles=(),
        closed_roles=(),
        distinct_sets=(),
    ):
        self.name = name
        self.grammar = frozenset(grammar)
        self.concepts = set(concepts)
        self.roles = set(roles)
        self.individuals = set(individuals)
        self.subsumptions = list(subsumptions)          # (sub, sup)
        self.disjoint_pairs = list(disjoint_pairs)      # (A, B)
        self.transitive_roles = set(transitive_roles)
        self.closed_roles = set(closed_roles)           # (individual, role) pairs
        self.distinct_sets = [frozenset(s) for s in distinct_sets]

    def features(self):
        """Feature(M) -- Definition 2.2. Only what the axioms actually use."""
        f = set()
        if self.subsumptions:
            f.add(SUBSUMPTION)
        if self.disjoint_pairs:
            f.add(DISJOINTNESS)
        if self.transitive_roles:
            f.add(TRANSITIVE_AXIOM)
        if self.distinct_sets:
            f.add(UNIQUE_NAMES)
        # Grammar-available constructs are expressible even where no axiom uses
        # them: Exp is a property of the language (Def 3.1).
        return frozenset(f | self.grammar)

    def known_distinct(self, individuals):
        """
        Proposition 3.4(i), scoped.

        Remark 3.5: `bool(self.distinct_sets)` would be the tempting check and
        it is wrong in the direction that HIDES the problem -- a distinctness
        assertion over an unrelated pair makes it true while saying nothing
        about the individuals being counted. This checks the counted set.
        """
        wanted = set(individuals)
        if len(wanted) < 2:
            return True
        return any(wanted <= s for s in self.distinct_sets)

    def tempting_global_distinctness_check(self):
        """The unsound check of Remark 3.5, implemented so experiment 05 can
        MEASURE the difference rather than assert it."""
        return bool(self.distinct_sets)

    def is_closed(self, individual, role):
        """Proposition 3.4(ii). False by construction when the grammar has no
        closure construct -- Remark 3.6."""
        if "CLOSURE" not in self.grammar:
            return False
        return (individual, role) in self.closed_roles

    def closure_basis(self):
        return "construction" if "CLOSURE" not in self.grammar else "inspection"


class Corpus:
    """Ground assertions only -- Definition 2.3."""

    def __init__(self, name, concept_assertions=(), role_assertions=()):
        self.name = name
        self.concept_assertions = set(concept_assertions)  # (Concept, ind)
        self.role_assertions = set(role_assertions)        # (role, a, b)

    def instances(self, concept):
        return {a for (c, a) in self.concept_assertions if c == concept}

    def successors(self, individual, role):
        return {b for (r, a, b) in self.role_assertions if r == role and a == individual}

    def individuals(self):
        out = {a for (_, a) in self.concept_assertions}
        for (_, a, b) in self.role_assertions:
            out.add(a)
            out.add(b)
        return out

    def edges(self, role):
        return {(a, b) for (r, a, b) in self.role_assertions if r == role}


# ---------------------------------------------------------------------------
# Questions -- Definition 2.4
# ---------------------------------------------------------------------------


class Question:
    """
    kind determines rho(q). The constraint-carrying kinds declare a `droppable`
    constraint, which is what triggers a control -- Remark 6.5 makes the
    trigger 'carries a droppable constraint', NOT 'is a negation'.
    """

    def __init__(self, qid, kind, params, requires, droppable=None):
        self.id = qid
        self.kind = kind
        self.params = dict(params)
        self.requires = frozenset(requires)
        self.droppable = droppable  # name of the constraint a control removes

    def control(self):
        """q-circle: q with the droppable constraint removed -- Def 6.1."""
        if self.droppable is None:
            return None
        params = dict(self.params)
        params[self.droppable] = None
        return Question(
            self.id + "^circ",
            self.kind,
            params,
            self.requires - {NEGATION, COUNTING, BOUNDED_PATH},
            droppable=None,
        )

    def __repr__(self):
        return f"Question({self.id!r}, {self.kind!r})"


def q_instances(qid, concept):
    return Question(qid, "instances", {"concept": concept}, {SUBSUMPTION})


def q_count(qid, role, n, mode):
    """mode in {'ge','le','eq'} -- the three of Proposition 3.4."""
    # The droppable key must be one the LOWERING reads. An earlier version
    # carried a separate `cardinality` key that mirrored `mode`; dropping it
    # left `mode` and `n` in place, so every compiler emitted a control program
    # identical to the question's and E4 fired on every counting question. A
    # control that the compiler cannot distinguish from its question tests the
    # bookkeeping, not the constraint -- Remark 6.5's point about triggering on
    # droppability rather than on a name, seen from the other side.
    return Question(
        qid,
        "count",
        {"role": role, "n": n, "mode": mode},
        {COUNTING},
        droppable="n",
    )


def q_no_successor_of_kind(qid, role, concept):
    """The mis-rootable negation of Theorem 6.4(ii): a constraint on a role
    FILLER, not on the subject."""
    return Question(
        qid,
        "negated_filler",
        {"role": role, "concept": concept, "negation": True},
        {NEGATION, EXISTENTIAL},
        droppable="negation",
    )


def q_reach(qid, role, source):
    return Question(qid, "reach", {"role": role, "source": source}, {TRANSITIVE_QUERY})


def q_reach_bounded(qid, role, source, k):
    return Question(
        qid,
        "reach_bounded",
        {"role": role, "source": source, "k": k, "bound": k},
        {BOUNDED_PATH},
        droppable="bound",
    )


def q_disjointness_violation(qid, a, b):
    return Question(qid, "violation", {"A": a, "B": b}, {DISJOINTNESS})


# ---------------------------------------------------------------------------
# Derivability -- Definition 3.2, Proposition 3.4
# ---------------------------------------------------------------------------


def counting_derivable(model, corpus, individual, role, n, mode, inherits_una=False):
    """
    Proposition 3.4. Returns (derivable, reason).

    inherits_una=True is the RuleEngine case (Prop 8.3): Herbrand semantics
    supply the distinctness unconditionally, which is exactly why the two
    engines legitimately disagree at 'ge' (Cor 8.4).
    """
    succ = corpus.successors(individual, role)
    have_distinct = inherits_una or model.known_distinct(succ)
    have_closure = model.is_closed(individual, role)

    if mode == "ge":
        if not have_distinct:
            return False, "successors not known pairwise distinct"
        return True, None
    if mode == "le":
        if not have_closure:
            return False, f"successor set not closed ({model.closure_basis()})"
        return True, None
    if mode == "eq":
        missing = []
        if not have_distinct:
            missing.append("distinctness")
        if not have_closure:
            missing.append(f"closure ({model.closure_basis()})")
        if missing:
            return False, "exactly-n requires both; missing " + " and ".join(missing)
        return True, None
    raise ValueError(mode)


# ---------------------------------------------------------------------------
# Programs -- the compiled form. A tuple, so `==` is exact syntactic identity,
# which is what Definition 6.2 needs.
# ---------------------------------------------------------------------------


class Program:
    __slots__ = ("engine", "ops")

    def __init__(self, engine, ops):
        self.engine = engine
        self.ops = tuple(ops)

    def __eq__(self, other):
        return isinstance(other, Program) and self.engine == other.engine and self.ops == other.ops

    def __hash__(self):
        return hash((self.engine, self.ops))

    def text(self):
        return "\n".join(str(o) for o in self.ops)

    def __repr__(self):
        return f"Program({self.engine!r}, {len(self.ops)} ops)"


class CannotLower(Exception):
    """The adapter has no surface for this construct. NOT a claim about the
    target language -- Remark 3.8."""

    def __init__(self, feature):
        super().__init__(feature)
        self.feature = feature


class BudgetExceeded(Exception):
    """An outcome, not a crash. Carries its cap, because TIMEOUT at 120 and
    TIMEOUT at 3600 are different claims (Remark 4.7)."""

    def __init__(self, budget, steps):
        super().__init__(budget)
        self.budget = budget
        self.steps = steps


# ---------------------------------------------------------------------------
# Engines -- Definition 2.7
# ---------------------------------------------------------------------------


class Engine:
    name = "abstract"
    SUPPORTS = frozenset()
    inherits_una = False

    def lower(self, model, question):
        raise NotImplementedError

    def solve(self, program, model, corpus, budget):
        raise NotImplementedError


class OpenWorldEngine(Engine):
    """
    Certain-answer semantics. No unique-name assumption, no closure.

    SUPPORTS omits COUNTING and BOUNDED_PATH. Neither omission is a statement
    about description logic: COUNTING is omitted because this compiler cannot
    produce a program whose count is ENTAILED (Prop 3.4), and BOUNDED_PATH
    because a transitive super-role closes completely and admits no step bound
    (Cor 8.7). Both are claims about the compiler (section 5).
    """

    name = "open_world"
    SUPPORTS = frozenset(
        {SUBSUMPTION, EXISTENTIAL, VALUE, NEGATION, TRANSITIVE_AXIOM,
         TRANSITIVE_QUERY, DISJOINTNESS}
    )
    inherits_una = False

    def __init__(self, mis_root_negation=False):
        # The defect of Theorem 6.4(ii), switchable so experiment 11 measures
        # it instead of describing it.
        self.mis_root_negation = mis_root_negation

    def lower(self, model, question):
        k = question.kind
        if k == "instances":
            return Program(self.name, [("instances", question.params["concept"])])
        if k == "count":
            raise CannotLower(COUNTING)
        if k == "reach_bounded":
            raise CannotLower(BOUNDED_PATH)
        if k == "reach":
            # Remark 5.5: a FRESH transitive super-role. Declaring the base role
            # transitive would change the model rather than query it.
            role = question.params["role"]
            return Program(
                self.name,
                [("super_role", role, role + "*"), ("transitive", role + "*"),
                 ("reach_via", role + "*", question.params["source"])],
            )
        if k == "violation":
            return Program(
                self.name,
                [("consistency_check", question.params["A"], question.params["B"])],
            )
        if k == "negated_filler":
            role = question.params["role"]
            concept = question.params["concept"]
            if question.params.get("negation") is None:
                return Program(self.name, [("all_subjects_with_role", role)])
            if self.mis_root_negation:
                # Rooted at the SUBJECT rather than at the filler: a different,
                # well-formed expression. P != P_circ, so the syntactic check
                # passes and only the answer sets betray it.
                return Program(
                    self.name,
                    [("all_subjects_with_role", role), ("not_self", concept)],
                )
            return Program(
                self.name,
                [("all_subjects_with_role", role), ("not_filler", role, concept)],
            )
        raise CannotLower(k)

    def solve(self, program, model, corpus, budget):
        steps = 0
        ops = dict()
        for op in program.ops:
            ops.setdefault(op[0], []).append(op)

        if "instances" in ops:
            concept = ops["instances"][0][1]
            answers = set(corpus.instances(concept))
            for (sub, sup) in model.subsumptions:
                if sup == concept:
                    answers |= corpus.instances(sub)
            steps = len(corpus.concept_assertions)
            return answers, True, steps

        if "consistency_check" in ops:
            _, a, b = ops["consistency_check"][0]
            both = corpus.instances(a) & corpus.instances(b)
            steps = len(corpus.concept_assertions)
            if both and (a, b) in model.disjoint_pairs or both and (b, a) in model.disjoint_pairs:
                # Proposition 8.1: inconsistency is GLOBAL. The engine reports
                # that something is wrong without reporting where.
                return "INCONSISTENT", True, steps
            return set(), True, steps

        if "reach_via" in ops:
            role = program.ops[0][1]
            source = ops["reach_via"][0][2]
            reached, frontier = set(), {source}
            while frontier:
                steps += 1
                if steps > budget:
                    raise BudgetExceeded(budget, steps)
                nxt = set()
                for x in frontier:
                    for y in corpus.successors(x, role):
                        if y not in reached:
                            reached.add(y)
                            nxt.add(y)
                frontier = nxt
            return reached, True, steps

        if "all_subjects_with_role" in ops:
            role = ops["all_subjects_with_role"][0][1]
            subjects = {a for (r, a, _) in corpus.role_assertions if r == role}
            steps = len(corpus.role_assertions)
            if "not_filler" in ops:
                _, r, concept = ops["not_filler"][0]
                subjects = {
                    s for s in subjects
                    if not (corpus.successors(s, r) & corpus.instances(concept))
                }
            elif "not_self" in ops:
                _, concept = ops["not_self"][0]
                # Disjointness makes this entailed of every subject: the
                # constraint is present and does no work.
                insts = corpus.instances(concept)
                subjects = {s for s in subjects if s not in insts}
            return subjects, True, steps

        return set(), True, steps


class RuleEngine(Engine):
    """
    Least-model semantics over a Herbrand universe.

    UNIQUE_NAMES is in SUPPORTS but is INHERITED, not lowered (Prop 8.3):
    distinct ground terms denote distinct elements by construction. Remark 8.5
    is why `term_map_injective` is checked before the inheritance is relied on.

    DISJOINTNESS is lowered as a DETECTOR (Prop 8.1) -- faithful only while the
    knowledge base is consistent, and diagnostic where the open-world engine is
    not (Cor 8.2).
    """

    name = "rule"
    SUPPORTS = frozenset(
        {SUBSUMPTION, EXISTENTIAL, VALUE, NEGATION, TRANSITIVE_QUERY,
         BOUNDED_PATH, DISJOINTNESS, UNIQUE_NAMES}
    )
    inherits_una = True

    def __init__(self, left_recursive=False, drop_bound=False):
        self.left_recursive = left_recursive
        self.drop_bound = drop_bound

    def lower(self, model, question):
        k = question.kind
        if k == "instances":
            return Program(self.name, [("instances", question.params["concept"])])
        if k == "count":
            # Proposition 5.3: the target language counts perfectly well; this
            # compiler cannot emit a count program the engine will certify.
            raise CannotLower(COUNTING)
        if k == "reach":
            role = question.params["role"]
            src = question.params["source"]
            shape = "left" if self.left_recursive else "right"
            return Program(self.name, [("closure", role, src, shape)])
        if k == "reach_bounded":
            role = question.params["role"]
            src = question.params["source"]
            kk = question.params.get("bound")
            if kk is None or self.drop_bound:
                # The control, or the defect: unrolling disappears and the
                # program is the unbounded one.
                return Program(self.name, [("closure", role, src, "right")])
            # Proposition 8.6: O(k) NON-recursive clauses, each depending only
            # on the one below. No fixpoint.
            ops = [("unroll", role, src, i) for i in range(1, kk + 1)]
            return Program(self.name, ops)
        if k == "violation":
            return Program(
                self.name,
                [("viol_rule", question.params["A"], question.params["B"])],
            )
        if k == "negated_filler":
            role = question.params["role"]
            concept = question.params["concept"]
            if question.params.get("negation") is None:
                return Program(self.name, [("subjects", role)])
            return Program(self.name, [("subjects", role), ("naf_filler", role, concept)])
        raise CannotLower(k)

    def solve(self, program, model, corpus, budget):
        steps = 0
        head = program.ops[0][0]

        if head == "instances":
            concept = program.ops[0][1]
            answers = set(corpus.instances(concept))
            for (sub, sup) in model.subsumptions:
                if sup == concept:
                    answers |= corpus.instances(sub)
            return answers, True, len(corpus.concept_assertions)

        if head == "viol_rule":
            _, a, b = program.ops[0]
            both = corpus.instances(a) & corpus.instances(b)
            # Proposition 8.1: exactly one additional fact per violating
            # individual. Everything else in the least model is unaffected.
            return {("viol", a, b, x) for x in both}, True, len(corpus.concept_assertions)

        if head == "closure":
            _, role, src, shape = program.ops[0]
            if shape == "right":
                reached, frontier = set(), {src}
                while frontier:
                    steps += 1
                    if steps > budget:
                        raise BudgetExceeded(budget, steps)
                    nxt = set()
                    for x in frontier:
                        for y in corpus.successors(x, role):
                            if y not in reached:
                                reached.add(y)
                                nxt.add(y)
                    frontier = nxt
                return reached, True, steps
            # Left recursion: re-derives every prefix before extending it.
            # Same least model (Prop 8.8), different cost.
            reached = set()
            agenda = [(src,)]
            while agenda:
                steps += 1
                if steps > budget:
                    raise BudgetExceeded(budget, steps)
                path = agenda.pop()
                tail = path[-1]
                for y in corpus.successors(tail, role):
                    reached.add(y)
                    if y not in path:  # keep it finite on cyclic graphs
                        agenda.append(path + (y,))
                    else:
                        # the re-derivation the shape costs: every rotation of
                        # the cycle is re-explored from its own prefix
                        for z in corpus.successors(y, role):
                            steps += 1
                            if steps > budget:
                                raise BudgetExceeded(budget, steps)
                            reached.add(z)
            return reached, True, steps

        if head == "unroll":
            role = program.ops[0][1]
            src = program.ops[0][2]
            k = len(program.ops)
            level = {src}
            reached = set()
            for _ in range(k):
                steps += 1
                if steps > budget:
                    raise BudgetExceeded(budget, steps)
                level = {y for x in level for y in corpus.successors(x, role)}
                reached |= level
            return reached, True, steps

        if head == "subjects":
            role = program.ops[0][1]
            subjects = {a for (r, a, _) in corpus.role_assertions if r == role}
            steps = len(corpus.role_assertions)
            for op in program.ops[1:]:
                if op[0] == "naf_filler":
                    _, r, concept = op
                    insts = corpus.instances(concept)
                    subjects = {s for s in subjects if not (corpus.successors(s, r) & insts)}
            return subjects, True, steps

        return set(), True, steps

    def term_map_injective(self, corpus, naming):
        """
        Remark 8.5. Herbrand distinctness is free but not unconditionally safe:
        if two individuals map to the same ground term the inherited assumption
        silently identifies them and Prop 3.4(i)'s bound is computed over a
        collapsed set.
        """
        seen = {}
        for ind in corpus.individuals():
            t = naming(ind)
            if t in seen and seen[t] != ind:
                return False, (seen[t], ind, t)
            seen[t] = ind
        return True, None


# ---------------------------------------------------------------------------
# Exp / Ans -- Definitions 3.1, 3.3
# ---------------------------------------------------------------------------


def expressible(question, model):
    """Definition 3.1. A property of the LANGUAGE: no corpus, no engine."""
    return question.requires <= model.features()


def missing_features(question, model):
    return question.requires - model.features()


# ---------------------------------------------------------------------------
# Evaluation -- Definition 4.2 (E1)-(E7)
#
# The order is the content. Each clause runs before any clause whose evidence
# it would corrupt: E1 before E3 so a limitation of the language is never
# reported as a limitation of the adapter; E4 before E5 so a vacuous control is
# caught before a budget is spent proving it agrees.
# ---------------------------------------------------------------------------


def evaluate(question, model, corpus, engine, budget=10_000, subject=None):
    # (E1) expressible in the model?
    missing = missing_features(question, model)
    if missing:
        return Verdict(CANNOT_EXPRESS, {"missing": sorted(missing), "model": model.name})

    # (E2) derivable?
    if question.kind == "count":
        subj = subject if subject is not None else question.params.get("subject")
        ok, reason = counting_derivable(
            model, corpus, subj, question.params["role"],
            question.params["n"], question.params["mode"],
            inherits_una=engine.inherits_una,
        )
        if not ok:
            return Verdict(
                NOT_DERIVABLE,
                {"clause": question.params["mode"], "reason": reason,
                 "una_inherited": engine.inherits_una},
            )

    # (E3) does the compiler have a surface?
    #
    # `question.requires` ONLY. Folding model.features() in here was a bug, and
    # instructively the exact one section 5 describes: it tested the model's
    # whole grammar rather than what this question asks for, so the presence of
    # a construct anywhere in the model produced NO-QUERY-SURFACE for every
    # question over it. A capability claim indexed by anything other than the
    # question is not a capability claim about the question.
    unsupported = question.requires - engine.SUPPORTS
    if unsupported:
        return Verdict(
            NO_QUERY_SURFACE,
            {"missing": sorted(unsupported), "engine": engine.name},
        )
    try:
        program = engine.lower(model, question)
    except CannotLower as exc:
        return Verdict(NO_QUERY_SURFACE, {"missing": [exc.feature], "engine": engine.name})

    control_q = question.control()
    control_program = None
    if control_q is not None:
        try:
            control_program = engine.lower(model, control_q)
        except CannotLower as exc:
            return Verdict(
                NO_QUERY_SURFACE,
                {"missing": [exc.feature], "engine": engine.name, "on": "control"},
            )
        # (E4) syntactic vacuity -- Definition 6.2
        if program == control_program:
            return Verdict(
                CONTROL_VACUOUS,
                {"program": program.text(), "control": control_program.text(),
                 "constraint": question.droppable},
            )

    # (E5) budget
    try:
        answers, certified, steps = engine.solve(program, model, corpus, budget)
    except BudgetExceeded as exc:
        return Verdict(TIMEOUT, {"budget": exc.budget, "steps": exc.steps})
    control_answers = None
    control_inconclusive = None
    if control_program is not None:
        try:
            control_answers, _, _ = engine.solve(control_program, model, corpus, budget)
        except BudgetExceeded as exc:
            # The CONTROL exceeded the budget; the question itself did not. E6
            # asks whether dropping the constraint changes the answer set, and
            # an unfinished control cannot answer that -- so the vacuity check
            # is inconclusive, not failed. Returning TIMEOUT here would report a
            # property of the control as a verdict on the question, which is the
            # conflation Corollary 4.3 warns about; it also mislabels precisely
            # the case Proposition 8.6 is about, where the constraint being
            # tested is the very thing that made the question affordable.
            control_inconclusive = {
                "reason": "control exceeded budget",
                "budget": exc.budget,
                "steps": exc.steps,
            }
        # (E6) semantic vacuity -- Definition 6.3.
        #
        # The coinciding set must be NON-EMPTY. Definition 6.3 infers inertness
        # from two differing programs agreeing on their answers, and that
        # inference needs the agreement to be about something: if neither
        # program grounds, both return the empty set and they agree vacuously,
        # for a reason having nothing to do with the constraint. Two empty sets
        # are consistent with the constraint doing all the work, none of it, or
        # the compiler having emitted nothing that runs -- which is exactly the
        # ungrounded-aggregate case of Proposition 5.3. Firing here would label
        # a broken lowering CONSTRAINT-INERT and let it past E7, converting a
        # capability defect into a vacuity report.
        if control_answers is not None and answers == control_answers and answers:
            return Verdict(
                CONSTRAINT_INERT,
                {"coinciding_answers": _jsonable(answers),
                 "constraint": question.droppable,
                 "programs_differed": program != control_program},
            )

    # (E7)
    payload = {"answers": answers, "certified": certified, "steps": steps,
               "engine": engine.name}
    if control_inconclusive is not None:
        # Carried in the payload so an ANSWERED verdict never silently implies
        # that the non-vacuity check was performed.
        payload["vacuity_check_inconclusive"] = control_inconclusive
    return Verdict(ANSWERED, payload)


# ---------------------------------------------------------------------------
# Blockers -- Definition 7.1
# ---------------------------------------------------------------------------

BLOCKED_BY_MODEL = "blocked-by-model"
BLOCKED_BY_CORPUS = "blocked-by-corpus"
BLOCKED_BY_ENGINE = "blocked-by-engine"

BLOCKERS = (BLOCKED_BY_MODEL, BLOCKED_BY_CORPUS, BLOCKED_BY_ENGINE)


def blocker_of(v, question, model, corpus):
    """Definition 7.1. Returns (blocker, unblockers) or None if answered."""
    if v.label == ANSWERED:
        return None
    if v.label == CANNOT_EXPRESS:
        return BLOCKED_BY_MODEL, [f"extend grammar with {f}" for f in v.payload["missing"]]
    if v.label == NOT_DERIVABLE:
        return BLOCKED_BY_MODEL, ["add closure axiom", "add distinctness over counted set"]
    if v.label in (NO_QUERY_SURFACE, TIMEOUT, CONTROL_VACUOUS, CONSTRAINT_INERT):
        return BLOCKED_BY_ENGINE, ["write the lowering", "raise the budget", "fix the control"]
    return BLOCKED_BY_CORPUS, ["import assertions populating the pattern"]


# ---------------------------------------------------------------------------
# The fixture: a synthetic knowledge base whose ground truth is known BY
# CONSTRUCTION. Section 9.5 records that this is a limitation, not a feature.
# ---------------------------------------------------------------------------

REACTIONS_WITH_FOUR = ("rx1", "rx2", "rx3")
REACTIONS_WITH_OTHER = ("rx4",)  # three participants -- the control reaction


def fixture_corpus():
    """
    Four reactions. Three have exactly four participants, one has three.
    Ground truth for 'exactly four participants' is therefore |{rx1,rx2,rx3}|=3
    and the control rx4 must NEVER appear in an answer.
    """
    concept_assertions = set()
    role_assertions = set()
    for rx in REACTIONS_WITH_FOUR:
        concept_assertions.add(("Reaction", rx))
        for i in range(4):
            p = f"{rx}_p{i}"
            concept_assertions.add(("Participant", p))
            role_assertions.add(("hasParticipant", rx, p))
    for rx in REACTIONS_WITH_OTHER:
        concept_assertions.add(("Reaction", rx))
        for i in range(3):
            p = f"{rx}_p{i}"
            concept_assertions.add(("Participant", p))
            role_assertions.add(("hasParticipant", rx, p))
    return Corpus("fixture", concept_assertions, role_assertions)


def fixture_model(with_counting=True, with_closure=False, with_distinctness=False,
                  scoped_to_participants=False):
    """
    Switchable so the three witnesses of Theorem 3.7 are CONSTRUCTED rather
    than described.

    scoped_to_participants distinguishes Remark 3.5's two checks: when False
    the distinctness is over two ROLE individuals, which makes the tempting
    global boolean true while the counted set remains unconstrained.
    """
    grammar = {SUBSUMPTION, EXISTENTIAL, VALUE, NEGATION, TRANSITIVE_AXIOM,
               TRANSITIVE_QUERY, DISJOINTNESS}
    if with_counting:
        grammar.add(COUNTING)
    if with_closure:
        grammar.add("CLOSURE")

    distinct_sets = []
    if with_distinctness:
        if scoped_to_participants:
            for rx in REACTIONS_WITH_FOUR + REACTIONS_WITH_OTHER:
                distinct_sets.append({f"{rx}_p{i}" for i in range(4)})
        else:
            # Remark 3.5: two ROLE individuals, unrelated to any counted set.
            distinct_sets.append({"Reactant", "Product"})

    closed = set()
    if with_closure:
        for rx in REACTIONS_WITH_FOUR + REACTIONS_WITH_OTHER:
            closed.add((rx, "hasParticipant"))

    return Model(
        "fixture" + ("+count" if with_counting else "")
        + ("+closure" if with_closure else "")
        + ("+distinct" if with_distinctness else ""),
        grammar,
        concepts={"Reaction", "Participant", "Transaminase", "Enzyme"},
        roles={"hasParticipant", "precedes"},
        individuals=set(),
        subsumptions=[("Transaminase", "Enzyme")],
        closed_roles=closed,
        distinct_sets=distinct_sets,
    )


def chain_corpus(n=6, cyclic=True):
    """A path a0 -> a1 -> ... -> a{n-1}, closed into a cycle if cyclic."""
    edges = {("precedes", f"a{i}", f"a{i+1}") for i in range(n - 1)}
    if cyclic:
        edges.add(("precedes", f"a{n-1}", "a0"))
    concepts = {("Node", f"a{i}") for i in range(n)}
    return Corpus(f"chain{n}{'-cyclic' if cyclic else ''}", concepts, edges)


def lattice_corpus(n=6, cyclic=False, width=2):
    """
    A DIAMOND lattice, not a chain: level i has `width` nodes and every node
    at level i points at every node at level i+1.

    A chain cannot separate the two recursion shapes. On a chain each node has
    exactly one successor, so the left-recursive agenda holds a single path at
    a time and never re-derives anything -- both shapes cost the same number of
    steps, and Proposition 8.8's cost claim is invisible. The separation the
    proposition describes needs a node reachable by SEVERAL prefixes, so that
    the left shape re-explores it once per prefix while the right shape visits
    it once per BFS level. That is what this corpus supplies.

    Uses the same role and node concept as `chain_corpus`, so `chain_model`
    covers it and no new grammar is needed.
    """
    edges = set()
    levels = [[f"L{i}_{j}" for j in range(width)] for i in range(n)]
    for i in range(n - 1):
        for x in levels[i]:
            for y in levels[i + 1]:
                edges.add(("precedes", x, y))
    # a single source so a reachability query has one subject
    for x in levels[0]:
        edges.add(("precedes", "a0", x))
    if cyclic:
        for x in levels[-1]:
            edges.add(("precedes", x, "a0"))
    nodes = {"a0"} | {x for lvl in levels for x in lvl}
    concepts = {("Node", x) for x in nodes}
    name = f"lattice{n}x{width}{'-cyclic' if cyclic else ''}"
    return Corpus(name, concepts, edges)


def chain_model(with_bounded=True, with_transitive_query=True):
    grammar = {SUBSUMPTION, EXISTENTIAL, TRANSITIVE_AXIOM}
    if with_transitive_query:
        grammar.add(TRANSITIVE_QUERY)
    if with_bounded:
        grammar.add(BOUNDED_PATH)
    return Model(
        "chain", grammar, concepts={"Node"}, roles={"precedes"},
        transitive_roles=set(),
    )


def disjoint_fixture():
    """
    An individual genuinely in both of two disjoint concepts -- the input on
    which Proposition 8.1's two engines diverge.
    """
    model = Model(
        "disjoint",
        {SUBSUMPTION, DISJOINTNESS},
        concepts={"TwoOxoAcid", "AminoAcid"},
        disjoint_pairs=[("TwoOxoAcid", "AminoAcid")],
    )
    corpus = Corpus(
        "disjoint",
        {("TwoOxoAcid", "chebi58556"), ("AminoAcid", "chebi58556"),
         ("TwoOxoAcid", "chebi16810"), ("AminoAcid", "chebi29985")},
    )
    return model, corpus


# ---------------------------------------------------------------------------
# Small helpers used by more than one experiment
# ---------------------------------------------------------------------------


def ground_truth_exactly_four(corpus, role="hasParticipant", n=4):
    """Computed from the corpus, not transcribed. The corpus is ours, so this
    is not independent evidence -- it is a consistency check on the fixture."""
    subjects = {a for (r, a, _) in corpus.role_assertions if r == role}
    return {s for s in subjects if len(corpus.successors(s, role)) == n}


def naive_score(v, truth):
    """Scores by ANSWERS RETURNED: the rule Proposition 4.9 says inverts."""
    if v.label != ANSWERED:
        return 0.0
    returned = v.payload["answers"]
    if not isinstance(returned, set):
        return 0.0
    return 1.0 if returned == truth else 0.0


def answers_returned_count(v):
    if v.label != ANSWERED:
        return None
    a = v.payload["answers"]
    return len(a) if isinstance(a, set) else None


def verdict_aware_score(v, truth):
    """
    Refusal scores as a correct report of a limitation; a wrong answer scores
    as wrong; a certified wrong emptiness scores as wrong and is FLAGGED.
    """
    if v.label in (CANNOT_EXPRESS, NOT_DERIVABLE, NO_QUERY_SURFACE):
        return 1.0
    if v.label == ANSWERED:
        return 1.0 if v.payload["answers"] == truth else 0.0
    return 0.0


EXPERIMENTS = []  # populated by the experiment modules, not here
