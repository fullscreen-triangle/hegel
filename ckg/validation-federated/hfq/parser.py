"""Stage 1 of the pipeline: Parse.

Plan text to a list of steps (x, Src, rho, beta, b) plus the plan budget,
per def:step and def:plan. The grammar is deliberately small.

    plan NAME {
      budget INT requests

      let x = from SOURCE
              ask PRED(ARG, ...)
              with ?v in y [, ?w in z]
              within INT
              [else fail unresolved | when starved emit partial]

      let x = map y via MAP [then via MAP ...]
              expect partial FLOAT

      let x = union y z
      let x = intersect y z
      let x = join y z on ATTR
      let x = filter y where ATTR OP VALUE

      emit x [with provenance]
      emit divergence(y, z) as NAME
    }

Tokenisation is line-oriented: a `let`/`emit`/`budget` keyword at the head of a
line opens a clause, and subsequent more-indented lines continue it. This keeps
the parser small enough to read while accepting the paper's listings verbatim.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple


class ParseError(Exception):
    """Raised for malformed plan text. Carries the offending line number."""

    def __init__(self, message: str, line: Optional[int] = None) -> None:
        self.line = line
        super().__init__(message if line is None else f"line {line}: {message}")


# ---------------------------------------------------------------------------
# Abstract requests (def:areq) and steps (def:step)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AbstractRequest:
    """rho = (phi, Req(rho), beta).

    `predicate` and `args` are phi. `required` (Req) is not stored here: it is
    computed by structural recursion in check.py, because Req is a function of
    phi and the source's declared vocabulary, not an author annotation.
    """

    predicate: str
    args: Tuple[Any, ...] = ()
    bindings: Tuple[Tuple[str, str], ...] = ()  # (?var, plan variable)


@dataclass
class Step:
    """A step of def:step, plus the surface annotations the grammar carries."""

    var: str                       # x, the variable bound
    kind: str                      # from | map | union | intersect | join | filter
    source: Optional[str] = None   # Src, for kind == "from"
    request: Optional[AbstractRequest] = None  # rho
    beta: Tuple[str, ...] = ()     # plan variables supplied as input
    budget: float = float("inf")   # b, the step budget annotation
    maps: Tuple[str, ...] = ()     # translation maps, for kind == "map"
    expect_partial: Optional[float] = None  # epsilon of def:retention-check
    on_starved: Optional[str] = None        # "emit partial"
    on_unresolved: Optional[str] = None     # "fail"
    operands: Tuple[str, ...] = ()          # for set operations
    join_on: Optional[str] = None
    where: Optional[Tuple[str, str, Any]] = None
    line: int = 0


@dataclass
class Emit:
    target: str
    provenance: bool = False
    divergence: Optional[Tuple[str, str]] = None
    alias: Optional[str] = None
    line: int = 0


@dataclass
class Plan:
    """A plan of def:plan: a finite sequence of steps with a total budget."""

    name: str
    budget: float
    steps: List[Step] = field(default_factory=list)
    emits: List[Emit] = field(default_factory=list)

    def step_by_var(self, var: str) -> Optional[Step]:
        for s in self.steps:
            if s.var == var:
                return s
        return None

    def dependency_graph(self) -> Dict[str, Tuple[str, ...]]:
        """G(Plan): edges Step_j -> Step_i whenever y in beta_i is bound by j."""
        return {s.var: tuple(s.beta) for s in self.steps}


# ---------------------------------------------------------------------------
# Lexing helpers
# ---------------------------------------------------------------------------

_CLAUSE_HEAD = re.compile(r"^\s*(let|emit|budget|assert|plan|\})")
_ARG = re.compile(r'"([^"]*)"|\?([A-Za-z_]\w*)|([-+]?\d+(?:\.\d+)?)|([A-Za-z_][\w:.\-]*)')


def _strip_comment(line: str) -> str:
    # A '#' outside a quoted string starts a comment.
    out, quoted = [], False
    for ch in line:
        if ch == '"':
            quoted = not quoted
        if ch == "#" and not quoted:
            break
        out.append(ch)
    return "".join(out)


def _clauses(text: str) -> List[Tuple[int, str]]:
    """Group physical lines into logical clauses, keeping the opening line no."""
    clauses: List[Tuple[int, str]] = []
    current: Optional[List[str]] = None
    start = 0
    for n, raw in enumerate(text.splitlines(), start=1):
        line = _strip_comment(raw).rstrip()
        if not line.strip():
            continue
        if _CLAUSE_HEAD.match(line):
            if current is not None:
                clauses.append((start, " ".join(current)))
            current, start = [line.strip()], n
        else:
            if current is None:
                raise ParseError(f"continuation with no clause: {line.strip()!r}", n)
            current.append(line.strip())
    if current is not None:
        clauses.append((start, " ".join(current)))
    return clauses


def _parse_args(blob: str) -> Tuple[Any, ...]:
    args: List[Any] = []
    for m in _ARG.finditer(blob):
        s, var, num, bare = m.groups()
        if s is not None:
            args.append(s)
        elif var is not None:
            args.append("?" + var)
        elif num is not None:
            args.append(float(num) if "." in num else int(num))
        else:
            args.append(bare)
    return tuple(args)


# ---------------------------------------------------------------------------
# Clause parsers
# ---------------------------------------------------------------------------


def _parse_let(body: str, line: int) -> Step:
    m = re.match(r"let\s+([A-Za-z_]\w*)\s*=\s*(.*)$", body)
    if not m:
        raise ParseError("malformed let", line)
    var, rhs = m.group(1), m.group(2).strip()

    if rhs.startswith("from "):
        return _parse_from(var, rhs, line)
    if rhs.startswith("map "):
        return _parse_map(var, rhs, line)
    for op in ("union", "intersect"):
        if rhs.startswith(op + " "):
            operands = tuple(rhs[len(op):].split())
            if len(operands) < 2:
                raise ParseError(f"{op} needs at least two operands", line)
            return Step(var=var, kind=op, operands=operands,
                        beta=operands, line=line)
    if rhs.startswith("join "):
        mm = re.match(r"join\s+(\w+)\s+(\w+)\s+on\s+([\w:.\-]+)$", rhs)
        if not mm:
            raise ParseError("malformed join (expected: join A B on ATTR)", line)
        a, b, on = mm.groups()
        return Step(var=var, kind="join", operands=(a, b), beta=(a, b),
                    join_on=on, line=line)
    if rhs.startswith("filter "):
        mm = re.match(r'filter\s+(\w+)\s+where\s+([\w:.\-]+)\s*(==|!=|<=|>=|<|>)\s*(.+)$', rhs)
        if not mm:
            raise ParseError("malformed filter", line)
        a, attr, op, val = mm.groups()
        val = val.strip()
        if val.startswith('"') and val.endswith('"'):
            parsed: Any = val[1:-1]
        elif re.search(r"(and|or|not)", val, re.IGNORECASE):
            # The grammar admits one comparison per filter. Without this
            # check a conjunction parses as a single unquoted literal that
            # matches nothing, so the filter silently passes its whole input
            # and the plan looks cheaper than it is. A plan language whose
            # failures are invisible is the thing the verdict rules exist to
            # prevent, so this is a parse error rather than a warning.
            raise ParseError(
                "filter admits one comparison; chain filter steps instead "
                "of writing a boolean connective", line)
        else:
            try:
                parsed = float(val) if "." in val else int(val)
            except ValueError:
                parsed = val
        return Step(var=var, kind="filter", operands=(a,), beta=(a,),
                    where=(attr, op, parsed), line=line)
    raise ParseError(f"unknown right-hand side {rhs.split()[0]!r}", line)


def _parse_from(var: str, rhs: str, line: int) -> Step:
    m = re.match(r"from\s+([A-Za-z_][\w\-]*)\s*(.*)$", rhs)
    if not m:
        raise ParseError("malformed from", line)
    source, rest = m.group(1), m.group(2)

    am = re.search(r"\bask\s+([A-Za-z_]\w*)\s*\(([^)]*)\)", rest)
    if not am:
        raise ParseError("a `from` step requires an `ask`", line)
    predicate, argblob = am.group(1), am.group(2)

    bindings: List[Tuple[str, str]] = []
    beta: List[str] = []
    for bm in re.finditer(r"\bwith\s+\?(\w+)\s+in\s+(\w+)", rest):
        bindings.append(("?" + bm.group(1), bm.group(2)))
        beta.append(bm.group(2))

    wm = re.search(r"\bwithin\s+(\d+(?:\.\d+)?)", rest)
    budget = float(wm.group(1)) if wm else float("inf")

    on_unresolved = "fail" if re.search(r"\belse\s+fail\s+unresolved\b", rest) else None
    on_starved = ("emit partial"
                  if re.search(r"\bwhen\s+starved\s+emit\s+partial\b", rest) else None)

    return Step(
        var=var, kind="from", source=source,
        request=AbstractRequest(predicate, _parse_args(argblob), tuple(bindings)),
        beta=tuple(beta), budget=budget,
        on_starved=on_starved, on_unresolved=on_unresolved, line=line,
    )


def _parse_map(var: str, rhs: str, line: int) -> Step:
    m = re.match(r"map\s+(\w+)\s+via\s+(.*)$", rhs)
    if not m:
        raise ParseError("malformed map", line)
    operand, rest = m.group(1), m.group(2)
    maps = [rest.split()[0]]
    for tm in re.finditer(r"\bthen\s+via\s+([A-Za-z_]\w*)", rest):
        maps.append(tm.group(1))
    em = re.search(r"\bexpect\s+partial\s+(\d+(?:\.\d+)?)", rest)
    wm = re.search(r"\bwithin\s+(\d+(?:\.\d+)?)", rest)
    return Step(
        var=var, kind="map", maps=tuple(maps), operands=(operand,),
        beta=(operand,), expect_partial=float(em.group(1)) if em else None,
        budget=float(wm.group(1)) if wm else float("inf"), line=line,
    )


def _parse_emit(body: str, line: int) -> Emit:
    dm = re.match(r"emit\s+divergence\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)(?:\s+as\s+(\w+))?", body)
    if dm:
        return Emit(target=dm.group(1), divergence=(dm.group(1), dm.group(2)),
                    alias=dm.group(3), line=line)
    m = re.match(r"emit\s+(\w+)(.*)$", body)
    if not m:
        raise ParseError("malformed emit", line)
    return Emit(target=m.group(1),
                provenance=bool(re.search(r"\bwith\s+provenance\b", m.group(2))),
                line=line)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def parse(text: str) -> Plan:
    """Parse plan text into the intermediate representation of def:plan."""
    name: Optional[str] = None
    budget: Optional[float] = None
    steps: List[Step] = []
    emits: List[Emit] = []

    for line, body in _clauses(text):
        if body.startswith("plan"):
            m = re.match(r"plan\s+([A-Za-z_]\w*)\s*\{?", body)
            if not m:
                raise ParseError("malformed plan header", line)
            name = m.group(1)
        elif body.startswith("budget"):
            m = re.match(r"budget\s+(\d+(?:\.\d+)?)\s*(requests?)?", body)
            if not m:
                raise ParseError("malformed budget", line)
            budget = float(m.group(1))
        elif body.startswith("let"):
            steps.append(_parse_let(body, line))
        elif body.startswith("emit"):
            emits.append(_parse_emit(body, line))
        elif body.startswith("assert"):
            continue  # soundness assertions are declarative; nothing to execute
        elif body.startswith("}"):
            continue
        else:  # pragma: no cover - _CLAUSE_HEAD admits nothing else
            raise ParseError(f"unexpected clause {body!r}", line)

    if name is None:
        raise ParseError("plan has no name")
    if budget is None:
        raise ParseError("plan has no budget declaration")

    _check_wellformed(steps, line=0)
    return Plan(name=name, budget=budget, steps=steps, emits=emits)


def _check_wellformed(steps: Sequence[Step], line: int) -> None:
    """Enforce the two conditions of def:plan.

    (i) distinct bound variables; (ii) every variable in beta_i bound by some
    Step_j with j < i. Condition (ii) is what makes prop:blame terminate, so it
    is checked here rather than discovered at run time.
    """
    seen: set = set()
    for s in steps:
        for y in s.beta:
            if y not in seen:
                raise ParseError(
                    f"step {s.var!r} reads {y!r}, which is not bound by an earlier step",
                    s.line,
                )
        if s.var in seen:
            raise ParseError(f"variable {s.var!r} is bound twice", s.line)
        seen.add(s.var)
