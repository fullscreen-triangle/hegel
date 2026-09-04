/* ============================================================================
 * The four figures.
 *
 * These replace the pre-rendered PNGs that used to sit in these positions. A
 * PNG is a picture of a run that happened on someone else's machine, and the
 * reader has to take its axis on trust. Each figure here holds a control, and
 * moving the control re-executes the interpreter in the reader's own tab: the
 * numbers under the caption are recomputed, not recalled.
 *
 * That is the difference the page is actually claiming. "The count is exactly
 * 2m-1" is a proposition; a reader who can drag m and watch the two series stay
 * parallel has checked it, and a reader looking at a bitmap has not.
 *
 * Each figure keeps the layout of the manuscript panel it replaces -- the same
 * four sub-panels in the same order, lettered the same way -- so the caption
 * prose on the page still refers to the right thing.
 *
 * Drawing is ./Charts (hand-rolled SVG, no charting library). Colour is
 * ./theme. Data is @/lib/hfq/sweeps, which calls the same parser, checker and
 * executor the notebook above calls.
 * ========================================================================== */

import React, { useMemo, useState } from 'react';
import {
  verdictGrid, checkCost, capabilityMatrix, blameChains, blamePropagation,
  cardinalityPlane, retentionCounterexample, chainFactorisation,
  DEFAULT_BUDGETS,
} from '@/lib/hfq/sweeps';
import { VERDICTS, verdictOf, fmt } from './theme';
import {
  LineChart, BarChart, Heatmap, ScatterChart, Slider, Controls,
  Quad, Sub, Readout,
} from './Charts';

/* Three neutral series colours, borrowed from the manuscript's palette so the
 * page and the paper's figures read as the same document. */
const C_LEFT = '#7f8fa6';
const C_RIGHT = '#1f7a8c';
const C_THIRD = '#b4654a';
const GREY = '#9aa0a6';

const ORDER = ['answer', 'empty', 'surface', 'timeout', 'refused', 'starved'];

/* ------------------------------------------------------------------ *
 * The frame every figure sits in: title, controls, panels, caption.
 * The caption is passed as children by the page, verbatim from the
 * manuscript, and stays collapsed by default as it did under the PNG.
 * ------------------------------------------------------------------ */

export function Figure({ title, controls, children, caption }) {
  const [open, setOpen] = useState(false);
  return (
    <figure className="my-5 border border-dark/15 dark:border-light/15 rounded-md overflow-hidden">
      <header className="px-3 py-2 bg-dark/[0.03] dark:bg-light/[0.05]
                         border-b border-dark/10 dark:border-light/10">
        <h3 className="font-mono text-[12px] font-semibold">{title}</h3>
      </header>
      <div className="p-3">
        {controls}
        {children}
      </div>
      <figcaption className="px-3 py-2 text-[11px] leading-relaxed
                             bg-dark/[0.03] dark:bg-light/[0.05]
                             border-t border-dark/10 dark:border-light/10">
        <button onClick={() => setOpen((v) => !v)} type="button"
                className="font-mono font-semibold text-left hover:underline opacity-80">
          what this shows <span className="opacity-40">{open ? '−' : '+'}</span>
        </button>
        {open && <div className="mt-1.5 opacity-70">{caption}</div>}
      </figcaption>
    </figure>
  );
}

/* ================================================================== *
 * Figure 1 — the verdict layer (replaces panel_2_verdicts.png).
 * ================================================================== */

export function VerdictFigure({ caption }) {
  const [nExpect, setNExpect] = useState(10);
  const [nBudget, setNBudget] = useState(DEFAULT_BUDGETS.length);
  const [within, setWithin] = useState(60);
  const [hover, setHover] = useState(null);

  const budgets = useMemo(() => DEFAULT_BUDGETS.slice(0, nBudget), [nBudget]);
  const g = useMemo(
    () => verdictGrid({ budgets, nExpect, within }),
    [budgets, nExpect, within],
  );

  const present = ORDER.filter((n) => g.counts[n]);
  const nonAnswer = present.filter((n) => n !== 'answer');
  const total = g.cells.length;

  return (
    <Figure
      title="Figure — the verdict layer: six outcomes, one observable bit"
      caption={caption}
      controls={(
        <Controls note={`${total} plans executed`}>
          <Slider label="budgets" value={nBudget} min={3} max={DEFAULT_BUDGETS.length}
                  onChange={setNBudget} />
          <Slider label="honesty levels" value={nExpect} min={4} max={16}
                  onChange={setNExpect} />
          <Slider label="within" value={within} min={1} max={60} onChange={setWithin}
                  format={(v) => `${v}s`} />
        </Controls>
      )}
    >
      <Quad>
        <Sub letter="a" title="budget and honesty select the verdict">
          <Heatmap
            cols={budgets.map(String)}
            rows={g.expects.map((e) => e.toFixed(1))}
            colStride={nBudget > 8 ? 2 : 1}
            rowStride={nExpect > 10 ? 2 : 1}
            size={nBudget > 8 ? 18 : 22}
            xLabel="budget (requests)"
            yLabel="η declared retention"
            onHover={setHover}
            cell={(c, r, ci, ri) => {
              const cell = g.cells[ci * g.expects.length + ri];
              if (!cell) return null;
              const v = verdictOf(cell.verdict);
              return {
                fill: v.color, opacity: 0.82,
                title: `budget ${cell.budget}, η ${cell.expect.toFixed(2)} → `
                  + `${cell.verdict}, ${cell.requests} requests`,
                verdict: cell.verdict, requests: cell.requests, cell,
              };
            }}
          />
          <div className="flex gap-2 flex-wrap mt-1 text-[10px] font-mono">
            {present.map((n) => (
              <span key={n} className="flex items-center gap-1 opacity-75">
                <span className="inline-block w-2.5 h-2.5 rounded-sm"
                      style={{ background: VERDICTS[n].color }} />
                {n}
              </span>
            ))}
            <span className="ml-auto opacity-90">
              {hover ? `${hover.verdict} · ${hover.requests} requests` : ' '}
            </span>
          </div>
        </Sub>

        <Sub letter="b" title="spend before the verdict">
          <LineChart
            width={340} height={210}
            xDomain={[budgets[0], budgets[budgets.length - 1]]}
            yDomain={[0, Math.max(1, ...g.cells.map((c) => c.requests))]}
            xLabel="budget (requests)" yLabel="requests issued"
            series={[
              {
                name: 'max over η', color: C_RIGHT,
                points: budgets.map((b) => ({
                  x: b,
                  y: Math.max(...g.cells.filter((c) => c.budget === b).map((c) => c.requests)),
                })),
              },
              {
                name: 'mean over η', color: C_LEFT, dashed: true,
                points: budgets.map((b) => {
                  const col = g.cells.filter((c) => c.budget === b);
                  return { x: b, y: col.reduce((a, c) => a + c.requests, 0) / col.length };
                }),
              },
            ]}
          />
          <Readout>
            Spend rises with the budget and then stops: past the point where the
            plan can be served, a larger allowance buys nothing.
          </Readout>
        </Sub>

        <Sub letter="c" title="verdicts realised by the sweep">
          <BarChart
            width={340} height={200}
            groups={present}
            series={[{
              name: 'configurations', color: C_RIGHT,
              values: present.map((n) => g.counts[n]),
            }]}
            yLabel="configurations"
          />
          <div className="flex gap-2 flex-wrap mt-1 text-[10px] font-mono opacity-70">
            {present.map((n) => (
              <span key={n} style={{ color: VERDICTS[n].color }}>
                {n} {g.counts[n]}
              </span>
            ))}
          </div>
        </Sub>

        <Sub letter="d" title="six verdicts, one bit">
          {/* The collapse. Left: what the interpreter distinguishes -- one bar
              per verdict kind, stacked. Right: what a caller reading
              success-or-failure sees, which is two numbers. */}
          <div className="flex items-end gap-6">
            <BarChart
              width={150} height={200} stacked
              groups={['answer', `blocked (${nonAnswer.length} kinds)`]}
              yMax={total}
              series={ORDER.filter((n) => g.counts[n]).map((n) => ({
                name: n, color: VERDICTS[n].color,
                values: [n === 'answer' ? g.counts[n] : 0,
                         n === 'answer' ? 0 : g.counts[n]],
              }))}
              yLabel="configurations"
            />
            <BarChart
              width={130} height={200}
              groups={['true', 'false']}
              yMax={total}
              showValues
              series={[{
                name: 'one bit', color: C_RIGHT,
                values: [g.oneBitTrue, g.oneBitFalse],
              }]}
            />
          </div>
          <Readout>
            {g.oneBitTrue} carry the true bit and {g.oneBitFalse} the false one.
            The {nonAnswer.length} non-answer kinds are distinct verdicts with
            distinct blockers and identical payload size 0 — the right-hand pair
            is everything a boolean interface can report.
          </Readout>
        </Sub>
      </Quad>
    </Figure>
  );
}

/* ================================================================== *
 * Figure 2 — the static layer (replaces panel_1_capability.png).
 * ================================================================== */

export function CapabilityFigure({ caption }) {
  const [maxM, setMaxM] = useState(12);
  const { rows, featureCount } = useMemo(() => checkCost(maxM), [maxM]);
  const mx = useMemo(() => capabilityMatrix(), []);

  const maxOps = Math.max(...rows.map((r) => r.bound));
  const maxReq = Math.max(...rows.map((r) => r.would_issue));
  const allRefused = rows.every((r) => r.refused && r.issued_after_refusal === 0);
  const admitted = mx.sources.map(
    (s) => mx.cells.filter((c) => c.source === s && c.admitted).length,
  );

  return (
    <Figure
      title="Figure — the static layer: checking is cheap, and refusal precedes contact"
      caption={caption}
      controls={(
        <Controls note={`${rows.length} plan lengths checked and executed`}>
          <Slider label="longest plan m" value={maxM} min={2} max={24} onChange={setMaxM} />
        </Controls>
      )}
    >
      <Quad>
        <Sub letter="a" title="checking is linear in the plan">
          <LineChart
            width={340} height={210} yLog
            xDomain={[1, maxM]} yDomain={[1, maxOps]}
            xLabel="steps in plan m" yLabel="capability tests"
            series={[
              { name: 'operations performed', color: C_RIGHT,
                points: rows.map((r) => ({ x: r.m, y: r.operations })) },
              { name: `m·|Feat| = ${featureCount}m`, color: GREY, dashed: true,
                points: rows.map((r) => ({ x: r.m, y: r.bound })) },
            ]}
          />
          <Readout>
            {rows.map((r) => `${r.m}:${r.operations}`).slice(0, 4).join('  ')} …
            — the measured count is exactly 2m−1 against a declared bound
            of {featureCount}m, one test per feature.
          </Readout>
        </Sub>

        <Sub letter="b" title="refusal happens before contact">
          <LineChart
            width={340} height={210}
            xDomain={[1, maxM]} yDomain={[-0.4, maxReq + 1]}
            xLabel="steps in plan m" yLabel="requests issued"
            series={[
              { name: 'issued by the admitted plan', color: C_LEFT,
                points: rows.map((r) => ({ x: r.m, y: r.would_issue })) },
              { name: 'issued after refusal', color: C_RIGHT,
                points: rows.map((r) => ({ x: r.m, y: r.issued_after_refusal })) },
            ]}
          />
          <Readout>
            Both series are executed counts, not a model. The gap between them is
            what the static check saves; {allRefused ? 'the lower one is pinned at exactly 0'
              : 'the lower one is NOT at 0'} for all {rows.length} plan lengths.
          </Readout>
        </Sub>

        <Sub letter="c" title="what each request would need">
          <Heatmap
            cols={mx.sources} rows={[...mx.predicates].reverse()}
            size={22} labelWidth={118}
            xLabel="source" yLabel="predicate"
            cell={(s, p) => {
              const c = mx.cells.find((x) => x.source === s && x.predicate === p);
              if (!c) return null;
              return {
                fill: c.n_missing === 0 ? C_RIGHT : (c.n_missing > 1 ? '#c0392b' : C_LEFT),
                opacity: c.n_missing === 0 ? 0.85 : 0.35 + 0.2 * c.n_missing,
                text: c.n_missing || '',
                textFill: '#ffffff',
                title: `${s} · ${p}: ${c.n_missing} of ${c.n_required} features missing`,
              };
            }}
          />
          <Readout>
            Integer counts over {mx.sources.length} sources are a discrete field.
            A cell is admitted only at zero: one missing feature is a refusal
            exactly as three are.
          </Readout>
        </Sub>

        <Sub letter="d" title="what each source can be asked">
          <BarChart
            width={340} height={200}
            groups={mx.sources}
            series={[
              { name: 'admitted', color: C_RIGHT, values: admitted },
              { name: 'rejected', color: C_LEFT,
                values: admitted.map((a) => mx.predicates.length - a) },
            ]}
            yLabel="predicates"
          />
          <Readout>
            {mx.sources.map((s, i) => `${s} ${admitted[i]}`).join(' · ')} of{' '}
            {mx.predicates.length}. It is that inequality, not the checker, that
            decides which plans can be written at all.
          </Readout>
        </Sub>
      </Quad>
    </Figure>
  );
}

/* ================================================================== *
 * Figure 3 — retention (replaces panel_4_retention.png).
 * ================================================================== */

export function RetentionFigure({ caption }) {
  const [n, setN] = useState(24);
  const [maxA, setMaxA] = useState(6);
  const [target, setTarget] = useState(12);

  const plane = useMemo(
    () => cardinalityPlane({ n, maxA, targets: [target, n, n * 2] }),
    [n, maxA, target],
  );
  const ce = useMemo(() => retentionCounterexample(), []);
  const cf = useMemo(() => chainFactorisation(), []);

  const fam = plane.families.find((f) => f.output === target);
  const famColors = [C_RIGHT, C_THIRD, C_LEFT];

  return (
    <Figure
      title="Figure — retention and amplification are independent"
      caption={caption}
      controls={(
        <Controls note="(a,b) arithmetic on the definitions · (c,d) measured">
          <Slider label="input |S|" value={n} min={8} max={48} onChange={setN} />
          <Slider label="max a" value={maxA} min={2} max={12} onChange={setMaxA} />
          <Slider label="iso-output" value={target} min={4} max={48} step={2}
                  onChange={setTarget} />
        </Controls>
      )}
    >
      <Quad>
        <Sub letter="a" title="equal output cardinality is a hyperbola">
          <ScatterChart
            width={340} height={210}
            xDomain={[0, 1]} yDomain={[0, maxA + 0.5]}
            xLabel="retention r" yLabel="amplification a"
            points={plane.cells.map((c) => ({ x: c.r, y: c.a }))}
            families={plane.families.map((f, i) => ({
              name: `|μ(S)| = ${f.output}`,
              color: famColors[i % famColors.length],
              points: f.points.map((p) => ({ x: p.r, y: p.a })),
              title: (p) => `r ${p.x.toFixed(3)}, a ${p.y} → ${f.output}`,
            }))}
          />
          <div className="flex gap-3 flex-wrap mt-1 text-[10px] font-mono opacity-70">
            {plane.families.map((f, i) => (
              <span key={f.output} style={{ color: famColors[i % famColors.length] }}>
                |μ(S)| = {f.output} · spread ×{f.spread.toFixed(2)}
              </span>
            ))}
          </div>
        </Sub>

        <Sub letter="b" title="the level set, read off">
          {fam ? (
            <>
              <BarChart
                width={340} height={200}
                groups={fam.points.map((p) => `a=${p.a}`)}
                series={[{
                  name: 'retention', color: C_RIGHT,
                  values: fam.points.map((p) => p.r),
                }]}
                yLabel="retention r" valueFmt={(v) => v.toFixed(2)}
              />
              <Readout>
                {fam.points.length} distinct (r, a) pairs all emit exactly{' '}
                {target} identifiers from an input of {n}. Retention ranges over{' '}
                {Math.min(...fam.points.map((p) => p.r)).toFixed(3)}–
                {Math.max(...fam.points.map((p) => p.r)).toFixed(3)}, a spread of
                ×{fam.spread.toFixed(2)}. Output size distinguishes none of them.
              </Readout>
            </>
          ) : (
            <p className="text-[11px] font-mono opacity-55 py-8">
              No (r, a) pair with integer r·|S| gives output {target} at |S| = {n}.
              Move a slider.
            </p>
          )}
        </Sub>

        <Sub letter="c" title="the measured counterexample">
          <BarChart
            width={340} height={200}
            groups={ce.rows.map((r) => r.map)}
            series={[
              { name: 'retention r', color: C_RIGHT, values: ce.rows.map((r) => r.retention) },
              { name: 'amplification a', color: C_THIRD, values: ce.rows.map((r) => r.amplification) },
              { name: 'output / input', color: C_LEFT,
                values: ce.rows.map((r) => r.output_size / r.input_size) },
            ]}
            valueFmt={(v) => v.toFixed(2)}
          />
          <Readout>
            Two maps over the same {ce.rows[0].input_size}-element input, each
            emitting {ce.rows[0].output_size} identifiers
            {ce.equal_output ? '' : ' (NOT equal — the pair is wrong)'}, with
            retentions {fmt(ce.rows[0].retention, 2)} and {fmt(ce.rows[1].retention, 2)}
            {' '}— a ×{ce.retention_ratio.toFixed(0)} difference in how much of the
            input survived, invisible in the output size.
          </Readout>
        </Sub>

        <Sub letter="d" title="the factorisation along a real chain">
          <BarChart
            width={340} height={200}
            groups={cf.stages.map((s) => s.map)}
            series={[
              { name: 'retention rᵢ', color: C_RIGHT, values: cf.stages.map((s) => s.retention) },
              { name: 'amplification aᵢ', color: C_THIRD,
                values: cf.stages.map((s) => s.amplification || 0) },
              { name: 'cumulative ∏rⱼaⱼ', color: C_LEFT, values: cf.cumulative },
            ]}
            valueFmt={(v) => v.toFixed(3)}
          />
          <Readout>
            ∏rᵢaᵢ = {fmt(cf.product)} against the observed{' '}
            |S_k|/|S_0| = {fmt(cf.observed_ratio)} —{' '}
            {cf.factorisation_holds ? 'identical, as thm:retention(a) requires'
              : 'NOT equal, which would refute thm:retention(a)'}. The surviving
            fraction ρ = {fmt(cf.surviving_fraction)} is tracked separately and is
            not that product. It sits {cf.surviving_fraction > cf.upper_bound
              ? 'above' : 'below'} min rᵢ = {fmt(cf.upper_bound)}, which is
            admissible here: the chain is {cf.chain_injective ? '' : 'not '}
            injective on its realised sets, so thm:retention(b){' '}
            {cf.upper_applicable ? 'applies' : 'does not apply'} — rem:injectivity-needed,
            measured rather than asserted.
          </Readout>
        </Sub>
      </Quad>
    </Figure>
  );
}

/* ================================================================== *
 * Figure 4 — blame (replaces panel_3_blame.png).
 * ================================================================== */

export function BlameFigure({ caption }) {
  const [maxM, setMaxM] = useState(9);
  const [expect, setExpect] = useState(0.95);
  const [nSteps, setNSteps] = useState(5);

  const chains = useMemo(() => blameChains({ maxM, expect }), [maxM, expect]);
  const prop = useMemo(() => blamePropagation({ nSteps }), [nSteps]);

  const underBound = chains.every((r) => r.max_hops < r.bound);
  const allConfined = prop.rows.every((r) => r.confined);
  const anyChange = prop.rows.some((r) => r.n_changed > 0);

  return (
    <Figure
      title="Figure — blame terminates, and only ever runs downstream"
      caption={caption}
      controls={(
        <Controls note={`${chains.length} plans + ${prop.rows.length + 1} perturbations`}>
          <Slider label="longest plan m" value={maxM} min={3} max={14} onChange={setMaxM} />
          <Slider label="declared η" value={expect} min={0.05} max={0.95} step={0.05}
                  onChange={setExpect} format={(v) => v.toFixed(2)} />
          <Slider label="chain length" value={nSteps} min={3} max={8} onChange={setNSteps} />
        </Controls>
      )}
    >
      <Quad>
        <Sub letter="a" title="blame terminates within m">
          <LineChart
            width={340} height={210}
            xDomain={[chains[0].m, maxM]}
            yDomain={[0, Math.max(...chains.map((r) => r.bound))]}
            xLabel="steps in plan m" yLabel="hops to the blamed step"
            series={[
              { name: 'longest chain', color: C_RIGHT,
                points: chains.map((r) => ({ x: r.m, y: r.max_hops })) },
              { name: 'mean chain', color: C_THIRD,
                points: chains.map((r) => ({ x: r.m, y: r.mean_hops })) },
              { name: 'bound m', color: GREY, dashed: true,
                points: chains.map((r) => ({ x: r.m, y: r.bound })) },
            ]}
          />
          <Readout>
            {underBound
              ? 'The longest chain sits strictly under the bound at every length'
              : 'A chain REACHED the bound — which would refute prop:blame'}
            : positions strictly decrease along a chain, so termination is an
            arithmetic fact and not a budget.
          </Readout>
        </Sub>

        <Sub letter="b" title="starvation spreads downstream">
          <BarChart
            width={340} height={200}
            groups={chains.map((r) => String(r.m))}
            series={[
              { name: 'steps starved', color: C_LEFT, values: chains.map((r) => r.n_starved) },
              { name: 'steps executed', color: GREY, values: chains.map((r) => r.n_steps) },
            ]}
            yLabel="steps"
          />
          <Readout>
            At η = {expect.toFixed(2)} the maps
            {chains[chains.length - 1].n_starved > 0
              ? ' cannot meet their declaration, and every step after the first failure starves'
              : ' meet their declaration and nothing starves'}. Lower the
            declared η and the bars empty.
          </Readout>
        </Sub>

        <Sub letter="c" title="the perturbation's reach, against a baseline">
          {/* Deliberately NOT a map of which steps failed. This chain starves on
              its own after two translation hops, so a failure map would be
              dominated by exhaustion the perturbation had no part in. What is
              plotted is the DIFFERENCE from the unperturbed run. */}
          <LineChart
            width={340} height={210} hover
            xDomain={[1, prop.nSteps]} yDomain={[0, prop.nSteps]}
            xTicks={prop.rows.map((r) => r.perturbed_at)}
            xLabel="position perturbed" yLabel="steps"
            series={[
              { name: 'verdicts changed', color: C_LEFT,
                points: prop.rows.map((r) => ({ x: r.perturbed_at, y: r.n_changed })) },
              { name: 'first changed position', color: C_RIGHT,
                points: prop.rows.map((r) => ({
                  x: r.perturbed_at,
                  y: r.first_changed === null ? 0 : r.first_changed + 1,
                })) },
            ]}
          />
          <Readout>
            Baseline (nothing perturbed):{' '}
            <span className="opacity-90">{prop.baseline.join(' ')}</span>. Only
            cells that differ from it are counted, so the chain&rsquo;s own decay
            is subtracted out rather than mistaken for the perturbation&rsquo;s
            effect.
          </Readout>
        </Sub>

        <Sub letter="d" title="the downstream cone">
          <Heatmap
            cols={Array.from({ length: prop.nSteps }, (_, i) => String(i + 1))}
            rows={prop.rows.map((r) => String(r.perturbed_at))}
            size={24}
            xLabel="step position" yLabel="position perturbed"
            cell={(c, r, ci, ri) => {
              const row = prop.rows[ri];
              const changed = row.changed.includes(ci);
              const upstream = ci < row.perturbed_at - 1;
              return {
                fill: changed ? (upstream ? '#c0392b' : C_LEFT) : 'currentColor',
                opacity: changed ? 0.85 : 0.07,
                title: `perturb ${row.perturbed_at}, step ${ci + 1}: `
                  + `${row.verdicts[ci]} (baseline ${prop.baseline[ci]})`
                  + `${changed ? ' — CHANGED' : ' — unchanged'}`,
              };
            }}
          />
          <Readout>
            Filled cells lie on or below the diagonal only
            {allConfined ? '' : ' — EXCEPT one, drawn in red, which would refute cor:rerun'}.
            {anyChange ? '' : ' No cell changed at all at this length; shorten the chain.'}
            {' '}Nothing upstream of a perturbation is ever touched — a null that
            could have failed, and the reason the baseline is subtracted rather
            than assumed.
          </Readout>
        </Sub>
      </Quad>
    </Figure>
  );
}
