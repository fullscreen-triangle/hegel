import Head from 'next/head';
import dynamic from 'next/dynamic';
import Layout from '@/components/Layout';
import TransitionEffect from '@/components/TransitionEffect';
import {
  Section, Panel, TheScript, WhyRepairsFail, Principles, WhySix, TwoSpellings,
  Pipeline,
} from '@/components/hfq/Exposition';
import { SemMan4Cat } from '@/components/hfq/SemMan4Cat';

// The notebook holds mutable cell state and a textarea, so it has no meaningful
// server render; ssr is off rather than guarded. The interpreter it runs is a
// plain ES module with no server dependency at all — see src/lib/hfq/.
const Notebook = dynamic(() => import('@/components/hfq/Notebook'), {
  ssr: false,
  loading: () => (
    <p className="font-mono text-sm opacity-50 py-8">loading the interpreter…</p>
  ),
});

export default function HFQNotebook() {
  return (
    <>
      <Head>
        <title>Hegel Federated Query — Consequences</title>
        <meta
          name="description"
          content="A plan language for federated biological retrieval. Capability-indexed
                   lowering, six-valued verdicts, and the arithmetic of partial identifier
                   translation — with a live interpreter running entirely in the browser."
        />
      </Head>
      <TransitionEffect />
      <main className="w-full min-h-screen bg-light dark:bg-dark text-dark dark:text-light">
        <Layout className="!pt-4 !pb-8">

          <header className="mb-10 max-w-3xl">
            <h1 className="font-mono text-xl font-bold">hegel federated query</h1>
            <p className="text-sm opacity-70 mt-2 leading-relaxed">
              A biological question spanning more than one public database is
              today answered by a script: a host-language program that
              interpolates identifiers into query strings, sends them, parses
              what returns, and interpolates again. The host language knows
              nothing about the data and the query language knows nothing about
              control flow, and every failure mode of federated retrieval lives
              in the seam between them.
            </p>
            <p className="text-sm opacity-70 mt-2 leading-relaxed">
              This is a language that closes the seam by refusing to be a query
              language at all — and an interpreter for it, running here, in this
              tab.
            </p>
            <p className="text-[11px] opacity-50 mt-3 font-mono leading-relaxed">
              Every source resolves against a local fixture. No request leaves
              the machine, by construction rather than by configuration: the
              interpreter is an ES module in this page and there is no server to
              call.
            </p>
          </header>

          {/* ---------------- I. the problem ---------------- */}

          <Section n="1" title="The script everybody writes"
            lede="Which enzymes catalyse reactions consuming any member of a given
                  chemical class, and of those, which occur in pathways containing a
                  second class? No single public resource answers it. Hover a defect
                  to see the line that exhibits it.">
            <TheScript />
          </Section>

          <Section n="2" title="Why the obvious repairs fail"
            lede="Both standard answers leave most of the defects in place, and neither
                  failure is an implementation defect that better engineering removes.">
            <WhyRepairsFail />
          </Section>

          {/* ---------------- II. the language ---------------- */}

          <Section n="3" title="What a plan is instead"
            lede="A plan is a sequence of steps; a step names a source, an abstract
                  pattern to send it, and a binding to receive the result. The plan
                  language supplies the control flow and the source adapters supply the
                  concrete requests.">
            <Principles />
            <div className="mt-4">
              <h3 className="font-mono text-[12px] font-semibold mb-2">The pipeline</h3>
              <Pipeline />
            </div>
          </Section>

          <Section n="4" title="Why six verdicts"
            lede="Not a design taste. Fix a step executed against a source holding some
                  dataset, with its inputs already computed. Three predicates apply.">
            <WhySix />
            <Panel src="/hfq/panel_2_verdicts.png"
                   title="Figure — the verdict layer: six outcomes, one observable bit">
              A 10×10 sweep executes the same plan across ten budgets and ten
              declared-honesty levels, giving 100 executed plans. Of those, 21
              answer, 49 refuse and 30 starve. Panel D is the collapse of
              cor:onebit: 21 executions carry the true bit and 79 the false one,
              and the five non-answer kinds are distinct verdicts with distinct
              blockers and identical payload size 0 — so a caller reading only
              success or failure cannot separate them.
            </Panel>
          </Section>

          <Section n="5" title="Two spellings, two answers"
            lede="D1 with a number attached. This is a documented observation, restated
                  in full because the argument depends on the details rather than the
                  headline.">
            <TwoSpellings />
          </Section>

          <Section n="6" title="Refusal precedes contact"
            lede="The static check is decided entirely by what each source declares, so a
                  plan asking for a capability its source lacks is refused by name before
                  any request is issued — and the request counter proves it.">
            <Panel src="/hfq/panel_1_capability.png"
                   title="Figure — the static layer: checking is cheap, and refusal precedes contact">
              The measured operation count is exactly 2m−1 against a declared
              bound of 11m, one per feature. Panel B pins the ill-capability
              series at exactly 0 requests for all twelve plan lengths. Panel D
              records what each source <em>declares</em>: chebi admits 3 of 13
              predicates, enzdb 2, rhea 8 — and it is that inequality, not the
              checker, that decides which plans can be written at all. An
              over-declaration would be invisible here, which is the asymmetry
              the prototype cannot test away.
            </Panel>
          </Section>

          <Section n="7" title="Translation is where the losses are"
            lede="Cross-namespace maps are partial, non-injective and non-confluent.
                  Retention and amplification are recorded separately, because their
                  product — all the output cardinality reveals — determines neither.">
            <Panel src="/hfq/panel_4_retention.png"
                   title="Figure — retention and amplification are independent">
              At output size 12 the retention ranges over 0.083–0.5 while the
              amplification ranges over 1–6: equal output size is compatible
              with a sixfold difference in how much of the input survived. Panel
              C is the measured counterexample — two maps over the same
              8-element input both emit 8 identifiers, one with retention 1.00
              and one with 0.25.
            </Panel>
            <Panel src="/hfq/panel_3_blame.png"
                   title="Figure — blame terminates, and only ever runs downstream">
              Plans of length 2–9 executed with a starving first step. The
              measured maximum chain is exactly m−2 and the mean (m−2)/2, both
              strictly under the bound at every length: positions strictly
              decrease along a chain, so termination is an arithmetic fact and
              not a budget. Panel D&rsquo;s filled cells lie on or below the
              diagonal only — nothing upstream of a perturbation is ever
              touched, a null that could have failed.
            </Panel>
          </Section>

          {/* ---------------- III. the interpreter ---------------- */}

          <Section n="8" title="The interpreter"
            lede="Write a plan and run it. Ctrl+Enter runs a cell; the plans of the
                  validation suite are grouped by what each one demonstrates. Every
                  verdict below is computed here, by the same rules the sections above
                  describe.">
            <Notebook />
          </Section>

          {/* ---------------- IV. the questions ---------------- */}

          <SemMan4Cat />

          <footer className="mt-12 pt-4 border-t border-dark/10 dark:border-light/10
                             text-[11px] opacity-55 max-w-3xl leading-relaxed font-mono">
            <p>
              The interpreter on this page is one of three. A Python
              implementation in the repository is the validation artifact — it
              exercises sixteen checks against these same fixtures and is not a
              benchmark. A Rust CLI is the final form: a user runs it locally,
              generates a token, and pairs this page with it, at which point the
              plans execute against whatever that machine can reach. This page
              is what you get before either.
            </p>
            <p className="mt-2">
              What has not been established: the interpreter has not been run
              against any live public endpoint, no claim is made about answer
              correctness against biology, and the capability declarations are
              asserted by each source adapter rather than verified against the
              service.
            </p>
          </footer>

        </Layout>
      </main>
    </>
  );
}
