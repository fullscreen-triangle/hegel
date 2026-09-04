// Stage 1 of the pipeline: Parse.
//
// Plan text to a list of steps (x, Src, rho, beta, b) plus the plan budget,
// per def:step and def:plan. The grammar is deliberately small.
//
//     plan NAME {
//       budget INT requests
//
//       let x = from SOURCE
//               ask PRED(ARG, ...)
//               with ?v in y [, ?w in z]
//               within INT
//               [else fail unresolved | when starved emit partial]
//
//       let x = map y via MAP [then via MAP ...]
//               expect partial FLOAT
//
//       let x = ladder over y
//               power P [, power P ...]
//               [expect power E]
//
//       let x = union y z
//       let x = intersect y z
//       let x = join y z on ATTR
//       let x = filter y where ATTR OP VALUE
//
//       emit x [with provenance] [as extension of "TEXT" [because GAP]]
//                               GAP in {induction, vocabulary, conditions}
//       emit divergence(y, z) as NAME
//     }
//
// Tokenisation is line-oriented: a `let`/`emit`/`budget` keyword at the head of
// a line opens a clause, and subsequent more-indented lines continue it. This
// keeps the parser small enough to read while accepting the paper's listings
// verbatim.

import { repr } from './model.js';

/** Raised for malformed plan text. Carries the offending line number. */
export class ParseError extends Error {
  constructor(message, line = null) {
    super(line === null ? message : `line ${line}: ${message}`);
    this.name = 'ParseError';
    this.line = line;
  }
}

// ---------------------------------------------------------------------------
// Abstract requests (def:areq) and steps (def:step)
// ---------------------------------------------------------------------------

/**
 * rho = (phi, Req(rho), beta).
 *
 * `predicate` and `args` are phi. `required` (Req) is not stored here: it is
 * computed by structural recursion in check.js, because Req is a function of
 * phi and the source's declared vocabulary, not an author annotation.
 */
export class AbstractRequest {
  constructor(predicate, args = [], bindings = []) {
    this.predicate = predicate;
    this.args = args;
    this.bindings = bindings; // [[?var, planVariable], ...]
  }
}

/** A step of def:step, plus the surface annotations the grammar carries. */
export class Step {
  constructor(init) {
    this.var = init.var;
    this.kind = init.kind; // from|map|union|intersect|join|filter|ladder
    this.source = init.source ?? null;
    this.request = init.request ?? null;
    this.beta = init.beta ?? [];
    this.budget = init.budget ?? Infinity;
    this.maps = init.maps ?? [];
    this.expect_partial = init.expect_partial ?? null;
    this.on_starved = init.on_starved ?? null;
    this.on_unresolved = init.on_unresolved ?? null;
    this.operands = init.operands ?? [];
    this.join_on = init.join_on ?? null;
    this.where = init.where ?? null;
    this.rungs = init.rungs ?? [];
    this.expect_power = init.expect_power ?? null;
    this.line = init.line ?? 0;
  }
}

export class Emit {
  constructor(init) {
    this.target = init.target;
    this.provenance = init.provenance ?? false;
    this.divergence = init.divergence ?? null;
    this.alias = init.alias ?? null;
    // What the emitted set IS, when that differs from what the question asked
    // for. `emit x as extension of "substrate scope"` says: these rows are the
    // recorded extension, the question asked for an intension, and the gap
    // between them is not something any traversal of this corpus closes.
    //
    // This is a fourth answer shape alongside the verdict algebra, and it sits
    // at a different level. R1-R6 classify what happened to the REQUEST. A plan
    // can be `answer` at every step and still be answering a different question
    // than the one asked, because the mismatch is between the question's
    // logical form and the corpus's, not between a step and a source.
    this.intension = init.intension ?? null;
    // WHICH gap separates the emitted extension from the question, named by the
    // plan rather than assumed by the executor.
    this.gap = init.gap ?? null;
    this.line = init.line ?? 0;
  }
}

/** A plan of def:plan: a finite sequence of steps with a total budget. */
export class Plan {
  constructor(name, budget, steps = [], emits = []) {
    this.name = name;
    this.budget = budget;
    this.steps = steps;
    this.emits = emits;
  }

  stepByVar(v) {
    return this.steps.find((s) => s.var === v) || null;
  }

  /** G(Plan): edges Step_j -> Step_i whenever y in beta_i is bound by j. */
  dependencyGraph() {
    const g = {};
    for (const s of this.steps) g[s.var] = [...s.beta];
    return g;
  }
}

// ---------------------------------------------------------------------------
// Lexing helpers
// ---------------------------------------------------------------------------

const CLAUSE_HEAD = /^\s*(let|emit|budget|assert|plan|\})/;
const ARG = /"([^"]*)"|\?([A-Za-z_]\w*)|([-+]?\d+(?:\.\d+)?)|([A-Za-z_][\w:.\-]*)/g;

// Boolean connectives, as whole words and outside any quoted run. Matching
// `and|or|not` unanchored would fire on the `or` inside `chlorine` and reject a
// genuine one-comparison filter, so the boundaries are required rather than
// decorative. Written as a literal (not `new RegExp("...")`) so a `\b` cannot
// be resolved into a literal backspace byte, which is how the Python original
// once silently matched nothing at all.
const CONNECTIVE = /(?<![\w"])(?:and|or|not)(?![\w"])/i;

function stripComment(line) {
  // A '#' outside a quoted string starts a comment.
  const out = [];
  let quoted = false;
  for (const ch of line) {
    if (ch === '"') quoted = !quoted;
    if (ch === '#' && !quoted) break;
    out.push(ch);
  }
  return out.join('');
}

/** Group physical lines into logical clauses, keeping the opening line no. */
function clauses(text) {
  const out = [];
  let current = null;
  let start = 0;
  const lines = text.split(/\r\n|\r|\n/);
  for (let i = 0; i < lines.length; i += 1) {
    const n = i + 1;
    const line = stripComment(lines[i]).replace(/\s+$/, '');
    if (!line.trim()) continue;
    if (CLAUSE_HEAD.test(line)) {
      if (current !== null) out.push([start, current.join(' ')]);
      current = [line.trim()];
      start = n;
    } else {
      if (current === null) {
        throw new ParseError(`continuation with no clause: ${repr(line.trim())}`, n);
      }
      current.push(line.trim());
    }
  }
  if (current !== null) out.push([start, current.join(' ')]);
  return out;
}

/**
 * Python's int()/float() and JS's Number() disagree on enough inputs to matter:
 * Number("") is 0, Number("0x10") is 16, Number("1_000") is NaN, and
 * Number("Infinity") is Infinity -- where Python raises ValueError for all four
 * and the caller falls back to treating the text as a string. Decide by shape.
 */
function parseNumber(text) {
  if (/^[-+]?\d+$/.test(text)) return { ok: true, value: parseInt(text, 10) };
  if (/^[-+]?(?:\d+\.\d*|\.\d+|\d+)$/.test(text)) {
    const v = Number(text);
    if (Number.isFinite(v)) return { ok: true, value: v };
  }
  return { ok: false };
}

function parseArgs(blob) {
  const args = [];
  ARG.lastIndex = 0;
  for (const m of blob.matchAll(ARG)) {
    const [, s, v, num, bare] = m;
    // Each alternative is tested against undefined, not truthiness: `""` is a
    // legal quoted argument and is falsy, so `if (s)` would drop it.
    if (s !== undefined) args.push(s);
    else if (v !== undefined) args.push(`?${v}`);
    else if (num !== undefined) args.push(num.includes('.') ? parseFloat(num) : parseInt(num, 10));
    else args.push(bare);
  }
  return args;
}

// ---------------------------------------------------------------------------
// Clause parsers
// ---------------------------------------------------------------------------

function parseLet(body, line) {
  const m = /^let\s+([A-Za-z_]\w*)\s*=\s*([\s\S]*)$/.exec(body);
  if (!m) throw new ParseError('malformed let', line);
  const v = m[1];
  const rhs = m[2].trim();

  if (rhs.startsWith('from ')) return parseFrom(v, rhs, line);
  if (rhs.startsWith('map ')) return parseMap(v, rhs, line);
  if (rhs.startsWith('ladder ')) return parseLadder(v, rhs, line);

  for (const op of ['union', 'intersect']) {
    if (rhs.startsWith(`${op} `)) {
      const operands = rhs.slice(op.length).trim().split(/\s+/).filter(Boolean);
      if (operands.length < 2) {
        throw new ParseError(`${op} needs at least two operands`, line);
      }
      return new Step({ var: v, kind: op, operands, beta: operands, line });
    }
  }

  if (rhs.startsWith('join ')) {
    const mm = /^join\s+(\w+)\s+(\w+)\s+on\s+([\w:.\-]+)$/.exec(rhs);
    if (!mm) throw new ParseError('malformed join (expected: join A B on ATTR)', line);
    return new Step({
      var: v, kind: 'join', operands: [mm[1], mm[2]], beta: [mm[1], mm[2]],
      join_on: mm[3], line,
    });
  }

  if (rhs.startsWith('filter ')) {
    const mm = /^filter\s+(\w+)\s+where\s+([\w:.\-]+)\s*(==|!=|<=|>=|<|>)\s*([\s\S]+)$/.exec(rhs);
    if (!mm) throw new ParseError('malformed filter', line);
    const [, a, attr, op] = mm;
    const val = mm[4].trim();
    // Reject a boolean connective BEFORE deciding the value is a literal.
    // Without this check a conjunction parses as a single literal that matches
    // nothing, so the filter silently passes its whole input and the plan looks
    // cheaper than it is. A plan language whose failures are invisible is the
    // thing the verdict rules exist to prevent, so this is a parse error.
    if (CONNECTIVE.test(val)) {
      throw new ParseError(
        'filter admits one comparison; chain filter steps instead '
        + 'of writing a boolean connective', line,
      );
    }
    let parsed;
    if (val.length >= 2 && val.startsWith('"') && val.endsWith('"')) {
      parsed = val.slice(1, -1);
    } else {
      // Python tries float() when the text contains '.', else int(), and falls
      // back to the raw string on ValueError. Mirror that shape exactly.
      const n = parseNumber(val);
      parsed = n.ok ? n.value : val;
    }
    return new Step({
      var: v, kind: 'filter', operands: [a], beta: [a],
      where: [attr, op, parsed], line,
    });
  }

  throw new ParseError(`unknown right-hand side ${repr(rhs.split(/\s+/)[0])}`, line);
}

function parseFrom(v, rhs, line) {
  const m = /^from\s+([A-Za-z_][\w\-]*)\s*([\s\S]*)$/.exec(rhs);
  if (!m) throw new ParseError('malformed from', line);
  const source = m[1];
  const rest = m[2];

  const am = /\bask\s+([A-Za-z_]\w*)\s*\(([^)]*)\)/.exec(rest);
  if (!am) throw new ParseError('a `from` step requires an `ask`', line);

  const bindings = [];
  const beta = [];
  for (const bm of rest.matchAll(/\bwith\s+\?(\w+)\s+in\s+(\w+)/g)) {
    bindings.push([`?${bm[1]}`, bm[2]]);
    beta.push(bm[2]);
  }

  const wm = /\bwithin\s+(\d+(?:\.\d+)?)/.exec(rest);

  return new Step({
    var: v,
    kind: 'from',
    source,
    request: new AbstractRequest(am[1], parseArgs(am[2]), bindings),
    beta,
    budget: wm ? parseFloat(wm[1]) : Infinity,
    on_unresolved: /\belse\s+fail\s+unresolved\b/.test(rest) ? 'fail' : null,
    on_starved: /\bwhen\s+starved\s+emit\s+partial\b/.test(rest) ? 'emit partial' : null,
    line,
  });
}

function parseMap(v, rhs, line) {
  const m = /^map\s+(\w+)\s+via\s+([\s\S]*)$/.exec(rhs);
  if (!m) throw new ParseError('malformed map', line);
  const operand = m[1];
  const rest = m[2];
  const maps = [rest.trim().split(/\s+/)[0]];
  for (const tm of rest.matchAll(/\bthen\s+via\s+([A-Za-z_]\w*)/g)) maps.push(tm[1]);
  const em = /\bexpect\s+partial\s+(\d+(?:\.\d+)?)/.exec(rest);
  const wm = /\bwithin\s+(\d+(?:\.\d+)?)/.exec(rest);
  return new Step({
    var: v, kind: 'map', maps, operands: [operand], beta: [operand],
    expect_partial: em ? parseFloat(em[1]) : null,
    budget: wm ? parseFloat(wm[1]) : Infinity,
    line,
  });
}

/**
 * Parse: ladder over Y [power P, ...] [expect power E]
 *
 * A ladder step is local: it consumes no requests, reaches no source, and
 * demands no capability. It composes declared rung powers multiplicatively,
 * 1 - prod(1 - p_i), and may declare a target the composite must attain.
 */
function parseLadder(v, rhs, line) {
  const m = /^ladder\s+over\s+(\w+)\s*([\s\S]*)$/.exec(rhs);
  if (!m) {
    throw new ParseError('malformed ladder (expected: ladder over Y power P, ...)', line);
  }
  const operand = m[1];
  const rest = m[2];

  // The expectation clause is removed BEFORE the rungs are read. Without this,
  // the "power" inside "expect power E" matches the rung pattern and the
  // declared target is silently appended as an extra rung: the plan would then
  // compose a ladder it did not write and report a composite nobody declared.
  const em = /\bexpect\s+power\s+(\d+(?:\.\d+)?)/.exec(rest);
  const rungText = em
    ? rest.slice(0, em.index) + rest.slice(em.index + em[0].length)
    : rest;

  const powers = [...rungText.matchAll(/\bpower\s+(\d+(?:\.\d+)?)/g)]
    .map((x) => parseFloat(x[1]));
  if (!powers.length) throw new ParseError('ladder declares no rungs', line);
  for (const p of powers) {
    if (!(p >= 0.0 && p <= 1.0)) {
      // A power outside [0,1] is not a weak rung, it is a malformed one.
      // Clamping would let a plan declare an impossible step and still run,
      // which is the class of silent failure the verdicts exist to prevent.
      throw new ParseError(`rung power ${formatRepr(p)} outside [0,1]`, line);
    }
  }

  return new Step({
    var: v, kind: 'ladder', operands: [operand], beta: [operand],
    rungs: powers,
    expect_power: em ? parseFloat(em[1]) : null,
    line,
  });
}

/** Python renders a float with a trailing ".0"; JS drops it. */
function formatRepr(x) {
  return Number.isInteger(x) ? `${x}.0` : String(x);
}

function parseEmit(body, line) {
  const dm = /^emit\s+divergence\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)(?:\s+as\s+(\w+))?/.exec(body);
  if (dm) {
    return new Emit({
      target: dm[1], divergence: [dm[1], dm[2]], alias: dm[3] ?? null, line,
    });
  }
  const m = /^emit\s+(\w+)([\s\S]*)$/.exec(body);
  if (!m) throw new ParseError('malformed emit', line);
  const tail = m[2];
  const im = /\bas\s+extension\s+of\s+"([^"]*)"/.exec(tail);
  const gm = /\bbecause\s+(induction|vocabulary|conditions)\b/.exec(tail);
  return new Emit({
    target: m[1],
    provenance: /\bwith\s+provenance\b/.test(tail),
    intension: im ? im[1] : null,
    gap: gm ? gm[1] : null,
    line,
  });
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

/** Parse plan text into the intermediate representation of def:plan. */
export function parse(text) {
  let name = null;
  let budget = null;
  const steps = [];
  const emits = [];

  for (const [line, body] of clauses(text)) {
    if (body.startsWith('plan')) {
      const m = /^plan\s+([A-Za-z_]\w*)\s*\{?/.exec(body);
      if (!m) throw new ParseError('malformed plan header', line);
      [, name] = m;
    } else if (body.startsWith('budget')) {
      const m = /^budget\s+(\d+(?:\.\d+)?)\s*(requests?)?/.exec(body);
      if (!m) throw new ParseError('malformed budget', line);
      budget = parseFloat(m[1]);
    } else if (body.startsWith('let')) {
      steps.push(parseLet(body, line));
    } else if (body.startsWith('emit')) {
      emits.push(parseEmit(body, line));
    } else if (body.startsWith('assert')) {
      continue; // soundness assertions are declarative; nothing to execute
    } else if (body.startsWith('}')) {
      continue;
    } else {
      throw new ParseError(`unexpected clause ${repr(body)}`, line);
    }
  }

  if (name === null) throw new ParseError('plan has no name');
  if (budget === null) throw new ParseError('plan has no budget declaration');

  checkWellformed(steps);
  return new Plan(name, budget, steps, emits);
}

/**
 * Enforce the two conditions of def:plan.
 *
 * (i) distinct bound variables; (ii) every variable in beta_i bound by some
 * Step_j with j < i. Condition (ii) is what makes prop:blame terminate, so it
 * is checked here rather than discovered at run time.
 */
function checkWellformed(steps) {
  const seen = new Set();
  for (const s of steps) {
    for (const y of s.beta) {
      if (!seen.has(y)) {
        throw new ParseError(
          `step ${repr(s.var)} reads ${repr(y)}, which is not bound by an earlier step`,
          s.line,
        );
      }
    }
    if (seen.has(s.var)) throw new ParseError(`variable ${repr(s.var)} is bound twice`, s.line);
    seen.add(s.var);
  }
}
