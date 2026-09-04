import React, { useState } from 'react';
import { VERDICTS, BLOCKERS } from './theme';

// The explanatory half of the page, read off the publication rather than
// paraphrased: part1-setting.tex for the defects and the two principles,
// part3-verdicts.tex for the independence argument, part5-execution.tex for
// the interpolation observation, part6-realisation.tex for the pipeline.
//
// It comes BEFORE the cells because the six verdicts are the vocabulary every
// cell reports in, and a reader who meets `starved` in a result strip without
// having met prop:independence has been shown a label, not an argument.

/* ---------------------------------------------------------------- */

export const Section = ({ n, title, lede, children }) => (
  <section className="mb-10">
    <h2 className="font-mono text-sm font-bold flex items-baseline gap-2">
      {n && <span className="opacity-35 text-xs">{n}</span>}
      {title}
    </h2>
    {lede && (
      <p className="text-sm opacity-70 mt-1.5 max-w-3xl leading-relaxed">{lede}</p>
    )}
    <div className="mt-3">{children}</div>
  </section>
);

const Code = ({ children, caption }) => (
  <figure className="my-3">
    <pre className="p-3 rounded text-[11px] leading-relaxed overflow-x-auto
                    bg-dark/[0.04] dark:bg-light/[0.06] font-mono
                    border border-dark/10 dark:border-light/10">
      {children}
    </pre>
    {caption && (
      <figcaption className="text-[11px] opacity-55 mt-1 font-mono">{caption}</figcaption>
    )}
  </figure>
);

/** A figure panel from the validation suite, with its measured caption. */
export const Panel = ({ src, title, children }) => {
  const [open, setOpen] = useState(false);
  return (
    <figure className="my-4 border border-dark/10 dark:border-light/10 rounded overflow-hidden">
      <img src={src} alt={title} className="w-full block bg-white" loading="lazy" />
      <figcaption className="p-2.5 text-[11px] leading-relaxed
                             bg-dark/[0.03] dark:bg-light/[0.05]">
        <button onClick={() => setOpen((v) => !v)}
                className="font-mono font-semibold text-left hover:underline">
          {title} <span className="opacity-40">{open ? '−' : '+'}</span>
        </button>
        {open && <div className="mt-1.5 opacity-70">{children}</div>}
      </figcaption>
    </figure>
  );
};

/* ---------------------------------------------------------------- */

const DEFECTS = [
  ['D1', 'The interpolation is textual',
   'Line 5 builds a query by string concatenation. Whether the result means '
   + 'what the author intended depends on the target language’s parse of a '
   + 'string the author never sees in full.'],
  ['D2', 'Failure is one bit wide',
   'If `compounds` comes back empty, the script cannot distinguish: the class '
   + 'has no members; the endpoint timed out and returned empty rather than an '
   + 'error; the query used a construct the endpoint does not support and it '
   + 'degraded silently; the identifier was misspelled. Each demands a '
   + 'different repair, and the script sees one empty list.'],
  ['D3', 'The failure of step n is attributed to step n',
   'If `pathways` is empty, the proximate cause is very often that `kegg_ids` '
   + 'was short, because `xref` is partial and silently dropped two-fifths of '
   + 'its input. The script reports a pathway problem and the analyst debugs '
   + 'the wrong stage.'],
  ['D4', 'The budget is unstated and unallocated',
   'There is a rate limit on one endpoint and a timeout on another, and no '
   + 'representation of either anywhere in the program. The script discovers '
   + 'them by failing.'],
  ['D5', 'The control flow is invisible to the data layer',
   'The loop over batches exists because a query language has no way to say '
   + '“and then”. The constant 50 is a magic number encoding an '
   + 'unstated belief about request-size limits at a service the script does '
   + 'not name.'],
];

export function TheScript() {
  const [hi, setHi] = useState(null);
  const lines = [
    ['compounds = sparql(ENDPOINT_A, TEMPLATE_A % class_iri)', null],
    ['ids       = [row["c"] for row in compounds]', null],
    ['enzymes   = []', null],
    ['for chunk in batches(ids, 50):', 'D5'],
    ['    q = TEMPLATE_B % " ".join("<%s>" % i for i in chunk)', 'D1'],
    ['    enzymes += sparql(ENDPOINT_A, q)', 'D4'],
    ['kegg_ids  = [xref(e) for e in enzymes]', 'D3'],
    ['pathways  = [rest_get(ENDPOINT_C, "/link/pathway/%s" % k) for k in kegg_ids]', 'D2'],
  ];

  return (
    <>
      <figure className="my-3">
        <pre className="p-3 rounded text-[11px] leading-relaxed overflow-x-auto
                        bg-dark/[0.04] dark:bg-light/[0.06] font-mono
                        border border-dark/10 dark:border-light/10">
          {lines.map(([text, tag], i) => (
            <div key={i}
                 onMouseEnter={() => tag && setHi(tag)}
                 onMouseLeave={() => setHi(null)}
                 className="flex gap-2"
                 style={{ background: tag && hi === tag ? '#B63E9622' : 'transparent' }}>
              <span className="opacity-25 select-none w-4 text-right shrink-0">{i + 1}</span>
              <span className="whitespace-pre">{text}</span>
              {tag && (
                <span className="ml-auto pl-3 opacity-45 shrink-0"
                      style={{ color: hi === tag ? '#B63E96' : undefined }}>{tag}</span>
              )}
            </div>
          ))}
        </pre>
        <figcaption className="text-[11px] opacity-55 mt-1 font-mono">
          lst:script — &ldquo;the script everybody writes. Not a strawman.&rdquo;
          Eight lines, five independently serious defects.
        </figcaption>
      </figure>

      <dl className="grid sm:grid-cols-2 gap-x-5 gap-y-2 mt-4">
        {DEFECTS.map(([tag, title, body]) => (
          <div key={tag}
               onMouseEnter={() => setHi(tag)} onMouseLeave={() => setHi(null)}
               className="p-2 rounded transition-colors"
               style={{ background: hi === tag ? '#B63E9614' : 'transparent' }}>
            <dt className="font-mono text-[12px] font-semibold">
              <span style={{ color: '#B63E96' }}>{tag}</span> {title}
            </dt>
            <dd className="text-[12px] opacity-70 leading-relaxed mt-0.5">{body}</dd>
          </div>
        ))}
      </dl>

      <p className="text-sm opacity-70 mt-4 max-w-3xl leading-relaxed">
        These are not five instances of sloppiness. They are five consequences
        of one structural decision — that control flow lives in a host language
        and data access lives in a query language, and neither can see the
        other.
      </p>
    </>
  );
}

/* ---------------------------------------------------------------- */

export function WhyRepairsFail() {
  return (
    <div className="grid md:grid-cols-2 gap-4">
      <div className="p-3 rounded border border-dark/12 dark:border-light/12">
        <h3 className="font-mono text-[12px] font-semibold mb-1.5">
          Make the query language bigger
        </h3>
        <p className="text-[12px] opacity-70 leading-relaxed">
          One large query with unions, subselects and federated service
          clauses. It fails for two reasons that are not implementation
          defects. <strong>It is frequently not available</strong> — of the four
          sources in the motivating question, only two speak SPARQL at all, and
          a flat-file REST interface cannot be reached by a service clause
          because there is no endpoint to address. And where it is available,
          <strong> it concentrates the defects</strong>: a single query
          containing every stage still fails one bit wide (D2), its
          intermediates are still invisible (D3), and it is now large enough
          that D1 becomes very hard to see.
        </p>
      </div>
      <div className="p-3 rounded border border-dark/12 dark:border-light/12">
        <h3 className="font-mono text-[12px] font-semibold mb-1.5">
          Use a workflow system
        </h3>
        <p className="text-[12px] opacity-70 leading-relaxed">
          A workflow engine supplies exactly the control flow (D5) that the
          query language lacks. It leaves <strong>D1–D4 untouched</strong>,
          because a workflow node that issues a query issues a string its author
          assembled, and the engine does not know what the string means.
        </p>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- */

export function Principles() {
  return (
    <div className="space-y-3">
      {[
        ['prin:leaves', 'Queries are leaves',
         'No construct of the plan language denotes a graph pattern, a triple, '
         + 'a relational clause, or a URL. Every such object is produced by '
         + 'lowering, from an abstract step together with a source declaration, '
         + 'and is not addressable by the plan author. The user writes the plan. '
         + 'Nobody writes a query.'],
        ['prin:verdict', 'A step returns a verdict, not rows',
         'The value of a step is a pair (verdict, payload). The payload is a '
         + 'result set only when the verdict is answer. Every other verdict '
         + 'carries a diagnosis and no result set.'],
      ].map(([label, title, body]) => (
        <div key={label} className="pl-3 border-l-2" style={{ borderColor: '#B63E96' }}>
          <h3 className="font-mono text-[12px] font-semibold">
            {title} <span className="opacity-40 font-normal">{label}</span>
          </h3>
          <p className="text-[12px] opacity-70 leading-relaxed mt-0.5 max-w-3xl">{body}</p>
        </div>
      ))}
    </div>
  );
}

/* ---------------------------------------------------------------- */

/**
 * prop:independence, drawn. Three predicates, eight assignments, one bit.
 * The point the current footer omits: six verdicts is not a design taste, it
 * is the coarsening of an eight-element space that distinguishes the cases
 * calling for different repairs.
 */
export function WhySix() {
  const rows = [
    ['Exp', 'the request is expressible against the source', 'Req(ρ) ⊆ cap(Src)',
     'a property of the request and the declaration'],
    ['Der', 'the denotation is non-empty on the data held', '⟦ρ⟧_D ≠ ∅',
     'a property of the request and the dataset'],
    ['Ans', 'the request completes within the step budget', 'cost ≤ b',
     'the only one that mentions a clock'],
  ];
  return (
    <>
      <div className="overflow-x-auto">
        <table className="text-[12px] w-full border-collapse">
          <tbody>
            {rows.map(([k, what, formal, note]) => (
              <tr key={k} className="border-b border-dark/8 dark:border-light/8">
                <td className="py-1.5 pr-3 font-mono font-semibold align-top">{k}</td>
                <td className="py-1.5 pr-3 align-top">{what}</td>
                <td className="py-1.5 pr-3 font-mono opacity-60 align-top whitespace-nowrap">
                  {formal}
                </td>
                <td className="py-1.5 opacity-55 align-top">{note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-sm opacity-70 mt-3 max-w-3xl leading-relaxed">
        The three are <strong>logically independent</strong> — all eight truth
        assignments are realisable, and the paper exhibits the constructions
        (prop:independence). So a step&rsquo;s outcome is a point in an
        eight-element space, and <strong>one bit indexes two</strong>. The six
        verdicts are the coarsening of that space which distinguishes the cases
        calling for different repairs.
      </p>
      <p className="text-sm opacity-70 mt-2 max-w-3xl leading-relaxed">
        This is why a practitioner who reruns a failing step with more time is
        implicitly betting the failure was in the third predicate. The bet is
        unfounded two-thirds of the time, and the script provides no way to
        check it.
      </p>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-x-4 gap-y-2 mt-4">
        {Object.entries(VERDICTS).map(([k, v]) => (
          <div key={k} className="flex gap-2 text-[11px]">
            <dt className="font-mono font-semibold w-16 shrink-0" style={{ color: v.color }}>
              {v.label}
            </dt>
            <dd className="opacity-65">{v.note}</dd>
          </div>
        ))}
      </div>

      <p className="text-[12px] opacity-60 mt-4 max-w-3xl leading-relaxed">
        Four of the six carry a <em>blocker</em>, which answers the question the
        verdict alone does not: which layer failed.{' '}
        {Object.entries(BLOCKERS).map(([k, b], i) => (
          <span key={k}>
            {i > 0 && ' · '}
            <span className="font-mono font-semibold">{b.label}</span> {b.note}
          </span>
        ))}
        . <strong>empty</strong> and <strong>answer</strong> have none, because
        nothing obstructed them — def:blocker is partial, and the JSON omits the
        key rather than writing null.
      </p>
    </>
  );
}

/* ---------------------------------------------------------------- */

const FORM_A = `PREFIX rh:    <http://rdf.rhea-db.org/>
PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
PREFIX chebi: <http://purl.obolibrary.org/obo/CHEBI_>
SELECT (COUNT(DISTINCT ?r) AS ?n) WHERE {
  ?r rdfs:subClassOf rh:Reaction ; rh:status rh:Approved .
  ?r rh:side/rh:contains/rh:compound/rh:chebi ?a , ?o .
  VALUES ?aa { chebi:35238 chebi:37022 }
  VALUES ?ox { chebi:35179 chebi:36147 chebi:133294 }
  ?a rdfs:subClassOf* ?aa .
  ?o rdfs:subClassOf* ?ox .
}`;

const FORM_B = `  ?r rh:side/rh:contains/rh:compound/rh:chebi ?a .
  ?r rh:side/rh:contains/rh:compound/rh:chebi ?o .`;

export function TwoSpellings() {
  return (
    <>
      <div className="grid md:grid-cols-2 gap-3">
        <div>
          <div className="font-mono text-[12px] mb-1">
            Form A returns <span className="font-bold" style={{ color: '#b91c1c' }}>2</span>
          </div>
          <Code caption="The abbreviation is on line 6: a comma-separated object list.">
            {FORM_A}
          </Code>
        </div>
        <div>
          <div className="font-mono text-[12px] mb-1">
            Form B returns <span className="font-bold" style={{ color: '#15803d' }}>397</span>
          </div>
          <Code caption="Differs from Form A only in that line 6 is written as two patterns.">
            {FORM_B}
          </Code>
        </div>
      </div>
      <p className="text-sm opacity-70 mt-2 max-w-3xl leading-relaxed">
        On 10 August 2026, two requests were issued to a public SPARQL endpoint
        of a reaction knowledge base. They were byte-identical except for one
        line. The counts differ by a factor of <strong>198.5</strong>.
      </p>
      <p className="text-sm opacity-70 mt-2 max-w-3xl leading-relaxed">
        The two forms are semantically equivalent under the specification: an
        object list is syntax, expanded during translation to the abstract query
        before evaluation. A conforming implementation must return the same
        count for both. <strong>The difference is not a specification
        ambiguity.</strong>
      </p>
      <div className="mt-3 p-2.5 rounded text-[12px] leading-relaxed
                      bg-dark/[0.03] dark:bg-light/[0.05] max-w-3xl">
        <span className="font-mono font-semibold">The control is clean and the
        confound is named. </span>
        <span className="opacity-70">
          Both forms were evaluated locally against two independent engines over
          a hand-checkable dataset, and both engines returned the hand-computed
          answer for both spellings — so the equivalence is not merely a reading
          of the grammar. Separately, the endpoint&rsquo;s loaded ontology
          carried 204,585 classes against 237,672 in the published download, a
          difference of 13.9%, so any comparison <em>across</em> those two
          artefacts is confounded by snapshot skew. That confound does not touch
          this observation, in which both counts come from the same endpoint in
          the same session.
        </span>
      </div>
      <p className="text-sm opacity-70 mt-3 max-w-3xl leading-relaxed">
        This is D1 with a number attached. Under prin:leaves the plan author
        never writes either form: lowering emits one canonical spelling, bound
        sets enter through the value-binding construct rather than by
        concatenation, and the family of defects this observation belongs to is
        eliminated by construction rather than by care.
      </p>
    </>
  );
}

/* ---------------------------------------------------------------- */

const STAGES = [
  ['parse', 'Plan text to a list of steps (x, Src, ρ, β, b) plus the plan budget.'],
  ['resolve', 'Each source name resolves against a registry of adapters, each '
    + 'declaring its capability set as explicit feature symbols. The declaration '
    + 'is data written by the adapter author, and nothing verifies it.'],
  ['check', 'Compute Req(ρ) by structural recursion and test containment. On '
    + 'failure the executor halts before issuing any request and emits a refusal '
    + 'naming the missing features and the step.'],
  ['allocate', 'Solve the budget allocation by bisection on a single shadow '
    + 'price. Steps with step-function yields are charged first.'],
  ['execute', 'In sequence order, apply (R1)–(R6). A step reaching (R4) calls '
    + 'its adapter’s lowering, which emits the canonical concrete request.'],
  ['emit', 'Serialise to JSON — verdicts, payloads, retention, allocation, '
    + 'provenance.'],
];

export function Pipeline() {
  return (
    <ol className="space-y-1.5">
      {STAGES.map(([name, body], i) => (
        <li key={name} className="flex gap-2.5 items-baseline">
          <span className="font-mono text-[11px] px-1.5 py-0.5 rounded shrink-0
                           bg-dark/[0.06] dark:bg-light/[0.09]">
            {i + 1}. {name}
          </span>
          <span className="text-[12px] opacity-70 leading-relaxed">{body}</span>
        </li>
      ))}
    </ol>
  );
}
