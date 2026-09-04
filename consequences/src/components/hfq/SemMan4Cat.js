import React, { useCallback, useEffect, useState } from 'react';
import { runPlan } from '@/lib/hfq';
import { byId } from '@/lib/hfq/plans';
import { verdictOf, VERDICTS } from './theme';
import { Section } from './Exposition';
import { PayloadView, ConcreteQueries, CapabilityMatrix } from './Views';

// Mark Doerr's SemMan4Cat questions, each as a plan, executed live.
//
// The questions arrived as prose, in an email asking what a catalysis
// researcher would actually want to ask. They are here in the same words, with
// the plan beneath and the verdict the interpreter returns.
//
// The interesting answers are the refusals, and this section says so rather
// than burying them. A framework whose value is that it can distinguish "no
// such row" from "this corpus cannot express that question" has to show the
// second case working, not only the first.

const QUESTIONS = [
  {
    id: 'mark_q1',
    n: 'Q1',
    ask: 'Which biocatalyst / enzyme, originated from a bacterium (not '
      + 'eukaryote), catalyses the transamination of benzylethylamine and does '
      + 'not have a cysteine in its protein sequence?',
    reading:
      'One sentence, five steps, three sources, two namespaces. The residue '
      + 'clause cannot be a further conjunct of the graph pattern: SEQ holds the '
      + 'sequences and does not declare `pattern`, so it can only scan keys '
      + 'handed to it — which forces the enzyme set to be computed first and '
      + 'makes the dependency explicit rather than implicit in a join order the '
      + 'endpoint chooses. That is the whole reason this is a plan and not a query.',
    watch: 'The map from reaction accessions to sequence keys retains 4 of 5: '
      + 'one transaminase has no sequence entry, so it is neither included nor '
      + 'excluded by the scan. It is uncovered — a third outcome a one-bit '
      + 'answer has no room for. The `_uncovered` count rides on every row.',
  },
  {
    id: 'mark_q2',
    n: 'Q2',
    ask: 'Which buffer composition and pH was used in the biocatalytic methyl '
      + 'transfer using the methyl-transferase mt-X of Bacillus subtilis?',
    reading:
      'The question reads like a lookup and is not one. "Which buffer" '
      + 'presupposes a single answer; the store holds two runs of the same '
      + 'reaction with two different buffers, which is the ordinary condition of '
      + 'a laboratory record and not a defect in the data. A query language that '
      + 'returns a set and calls it the answer has silently reinterpreted the '
      + 'question.',
    watch: 'RXN types its enzymes by provenance — bacterial or eukaryotic — not '
      + 'by EC class. There is no methyltransferase kind to test against, so the '
      + 'phrase "methyl-transferase mt-X" does two different kinds of work: '
      + '"mt-X" is an identifier this store holds, and "methyl-transferase" is a '
      + 'classification it does not. The plan discharges the first and says so '
      + 'about the second.',
  },
  {
    id: 'mark_q3',
    n: 'Q3',
    ask: 'What is the substrate scope and product range of the '
      + 'Baeyer-Villiger monooxygenase BVMO-Y?',
    reading:
      'Every step answers. The plan still does not answer the question, and it '
      + 'says so in the emit: what comes back is the recorded extension — the '
      + 'two reactions someone ran — where the question asked for a scope, which '
      + 'is a claim about cases the corpus does not contain.',
    watch: 'The admissibility block sits beside the verdict rather than folded '
      + 'into it. Every step did answer, and `answers_question: false` records '
      + 'that the execution answered something else. Collapsing the two into a '
      + 'fabricated refusal would hide that the retrieval succeeded.',
  },
  {
    id: 'mark_q4',
    n: 'Q4',
    ask: 'What are the expected products of a biocatalytic kinetic resolution '
      + 'reaction with the enzyme PFE at pH 9 in HEPES buffer?',
    reading:
      '"Expected" is the word that decides this plan. PFE has been run once, at '
      + 'pH 7.0 in phosphate. HEPES appears nowhere in the corpus. pH 9 appears '
      + 'nowhere. The conditions the question names are not in the store at all.',
    watch: 'The filter on HEPES returns empty, and the pH filter downstream is '
      + 'starved by it. Both are honest: an empty extent and a step that never '
      + 'ran are different facts, and the blame chain names which. A system that '
      + 'returned the pH 7 phosphate products here would be answering a question '
      + 'nobody asked.',
  },
  {
    id: 'mark_q5',
    n: 'Q5',
    ask: 'With which device was the UV spectrum monitored during the '
      + 'biocatalytic transformation BT3 on March 23rd by Yuliia Dikova, and '
      + 'which wavelength was monitored?',
    reading:
      'The question the framework should find easy, and saying so matters as '
      + 'much as reporting the hard ones. One source, one hop, no translation, '
      + 'no negation — everything asked for is provenance of a single activity.',
    watch: 'What the plan adds over a lookup is that the three qualifiers are '
      + 'checked rather than trusted. BT4 also ran on 2026-03-23, and it was run '
      + 'by Doerr on a Bruker. A plan reaching BT3 by name alone would answer '
      + 'correctly and would also have answered correctly had the date been '
      + 'wrong — and a reader could not tell those apart.',
  },
];

const GENERICS = [
  ['G1', 'all datasets D about a substance with compound C'],
  ['G2', 'all datasets D generated by Activity A of type T that evaluated a substance with compound C'],
  ['G3', '…the same, with a Bruker Spectrometer set to X'],
  ['G4', 'all datasets D about chemical reaction R that had product P'],
  ['G5', 'all datasets D about chemical reaction R that had a product with compound C'],
  ['G6', 'all datasets D measured with a UV-vis spectrometer containing a substance with compound C'],
  ['G7', 'all datasets D that had substance S as catalyst and were measured with a Bruker Spectrometer'],
  ['G8', 'all datasets D measured with any Bruker instrument'],
];

/* ---------------------------------------------------------------- */

function Verdicts({ steps }) {
  const counts = {};
  steps.forEach((s) => { counts[s.verdict] = (counts[s.verdict] || 0) + 1; });
  return (
    <div className="flex gap-1.5 flex-wrap">
      {Object.entries(counts).map(([v, n]) => {
        const vd = verdictOf(v);
        return (
          <span key={v} className="font-mono text-[10px] px-1.5 py-0.5 rounded"
                style={{ background: vd.bg, color: vd.color }} title={vd.note}>
            {n}× {vd.label}
          </span>
        );
      })}
    </div>
  );
}

function Question({ q }) {
  const [result, setResult] = useState(null);
  const [open, setOpen] = useState(false);
  const plan = byId(q.id);

  // Each question executes once on mount. They are cheap -- the whole suite
  // runs in a few milliseconds against local fixtures -- and a page about
  // verdicts that made the reader press a button to see one would be asking
  // them to take the interesting part on trust.
  useEffect(() => {
    if (plan) setResult(runPlan(plan.source));
  }, [plan]);

  if (!plan) return null;
  const ok = result && result.ok;
  const admissibility = ok && result.emitted
    ? Object.values(result.emitted).find((e) => e && e.admissibility)?.admissibility
    : null;

  return (
    <article className="border border-dark/15 dark:border-light/15 rounded-lg overflow-hidden mb-4">
      <header className="px-3 py-2 bg-dark/[0.03] dark:bg-light/[0.05]">
        <div className="flex items-baseline gap-2 flex-wrap">
          <span className="font-mono text-[12px] font-bold" style={{ color: '#B63E96' }}>
            {q.n}
          </span>
          <p className="text-[13px] flex-1 min-w-[16rem] leading-snug">
            &ldquo;{q.ask}&rdquo;
          </p>
          {ok && <Verdicts steps={result.steps} />}
        </div>
      </header>

      <div className="px-3 py-2.5 space-y-2">
        <p className="text-[12px] opacity-75 leading-relaxed">{q.reading}</p>
        <p className="text-[12px] leading-relaxed pl-2.5 border-l-2"
           style={{ borderColor: '#B63E96' }}>
          <span className="font-mono font-semibold opacity-70">what to watch </span>
          <span className="opacity-70">{q.watch}</span>
        </p>

        {ok && admissibility && (
          <div className="p-2.5 rounded text-[12px] leading-relaxed"
               style={{ background: VERDICTS.surface.bg }}>
            <span className="font-mono text-[11px] font-semibold"
                  style={{ color: VERDICTS.surface.color }}>
              answers_question: false — gap: {admissibility.gap}
            </span>
            <p className="opacity-75 mt-1">{admissibility.reason}</p>
          </div>
        )}

        {ok && result.requests_issued === 0 && (
          <div className="p-2.5 rounded text-[12px] font-mono"
               style={{ background: VERDICTS.surface.bg, color: VERDICTS.surface.color }}>
            0 requests issued. The refusal was decided by the declarations alone,
            before contact.
          </div>
        )}

        {result && !result.ok && (
          <div className="p-2.5 rounded text-[12px] font-mono"
               style={{ background: VERDICTS.refused.bg, color: VERDICTS.refused.color }}>
            {result.stage}: {result.error}
          </div>
        )}

        <button onClick={() => setOpen((v) => !v)}
          className="font-mono text-[11px] px-2 py-0.5 rounded border
                     border-dark/20 dark:border-light/20
                     hover:bg-dark/[0.05] dark:hover:bg-light/[0.08] transition-colors">
          {open ? 'hide' : 'show'} plan, payload and lowered query
        </button>

        {open && (
          <div className="space-y-3 pt-1">
            <pre className="p-2.5 rounded text-[11px] leading-relaxed overflow-x-auto
                            bg-dark/[0.04] dark:bg-light/[0.06] font-mono">
              {plan.source}
            </pre>
            {ok && (
              <>
                <div>
                  <h4 className="font-mono text-[11px] font-semibold opacity-70 mb-1">
                    capability — what each step required against what its source declares
                  </h4>
                  <CapabilityMatrix check={result.check} />
                </div>
                <div>
                  <h4 className="font-mono text-[11px] font-semibold opacity-70 mb-1">
                    payload
                  </h4>
                  <PayloadView steps={result.steps} />
                </div>
                <div>
                  <h4 className="font-mono text-[11px] font-semibold opacity-70 mb-1">
                    lowered query — the concrete request the abstract step became
                  </h4>
                  <ConcreteQueries steps={result.steps} />
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </article>
  );
}

/* ---------------------------------------------------------------- */

function Generic({ tag, text }) {
  const id = `dcat_g${tag.slice(1)}`;
  const plan = byId(id);
  const [result, setResult] = useState(null);
  useEffect(() => { if (plan) setResult(runPlan(plan.source)); }, [plan]);

  const refused = result && result.ok && result.requests_issued === 0;
  return (
    <div className="flex items-baseline gap-2 py-1.5 border-b border-dark/8 dark:border-light/8">
      <span className="font-mono text-[11px] font-semibold w-6 shrink-0 opacity-60">{tag}</span>
      <span className="text-[12px] flex-1 opacity-80">{text}</span>
      {result && result.ok && (
        <span className="font-mono text-[10px] px-1.5 py-0.5 rounded shrink-0"
              style={{
                background: verdictOf(result.steps[0]?.verdict).bg,
                color: verdictOf(result.steps[0]?.verdict).color,
              }}>
          {refused ? 'surface · 0 requests' : result.steps.map((s) => s.verdict).join(',')}
        </span>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------- */

export function SemMan4Cat() {
  return (
    <>
      <Section n="9" title="The questions, answered"
        lede="Five questions from the biocatalysis realm, sent by Mark Doerr to
              illustrate the challenges LARA faces, and eight generic dataset queries
              collected for Chem-DCAT-AP. Each is written as a plan and executed here.">
        <p className="text-sm opacity-70 mb-4 max-w-3xl leading-relaxed">
          Three of the thirteen cannot be answered by this corpus, and those are
          the ones worth reading first. A framework whose claim is that it
          distinguishes &ldquo;no such row&rdquo; from &ldquo;this corpus cannot
          express that question&rdquo; has to show the second case working —
          not merely assert that it would.
        </p>
        {QUESTIONS.map((q) => <Question key={q.id} q={q} />)}
      </Section>

      <Section n="10" title="Chem-DCAT-AP generic queries"
        lede="The eight generic dataset queries, run against the same fixture. Three are
              phrased as scans over an extent a keyed record service does not expose.">
        <div className="max-w-4xl">
          {GENERICS.map(([tag, text]) => <Generic key={tag} tag={tag} text={text} />)}
        </div>
        <div className="mt-4 p-3 rounded text-[12px] leading-relaxed max-w-3xl
                        bg-dark/[0.03] dark:bg-light/[0.05]">
          <p className="font-mono font-semibold mb-1">
            Why the Bruker queries are refused
          </p>
          <p className="opacity-75">
            &ldquo;With a Bruker Spectrometer&rdquo; does not name a device. It
            names a <em>class</em>, and asks the instrument service to enumerate
            its members — which devices, of all the devices you hold, are Bruker
            spectrometers. INST is a keyed record service: it answers
            &ldquo;tell me about DEV:UV1900i&rdquo;, and has no operation that
            ranges over its own extent, so it declares{' '}
            <span className="font-mono">lookup, link, bind, batch</span> and not{' '}
            <span className="font-mono">pattern</span>. The static check computes
            the requirement, finds it missing, and halts —{' '}
            <strong>zero requests issued</strong>. That is the result, not a
            failure to produce one. A system that answered by scanning whatever
            it happened to hold would be reporting a subset as though it were
            the extent.
          </p>
        </div>
      </Section>
    </>
  );
}

export default SemMan4Cat;
