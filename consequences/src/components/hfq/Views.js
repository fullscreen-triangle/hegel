import React from 'react';
import { VERDICTS, verdictOf, kindOf, BLOCKERS, fmt } from './theme';

// Every view here reads fields that Execution.to_json() actually returns. A
// view with no data says so rather than drawing an empty frame, because an
// empty axis and an absent measurement look identical once drawn.

const Empty = ({ children }) => (
  <div className="text-xs italic opacity-50 py-3">{children}</div>
);

export const Panel = ({ title, sub, children, right }) => (
  <section className="border border-dark/15 dark:border-light/15 rounded-md overflow-hidden">
    <header className="flex items-baseline justify-between gap-3 px-3 py-2
                       bg-dark/[0.03] dark:bg-light/[0.04]
                       border-b border-dark/10 dark:border-light/10">
      <div>
        <h3 className="font-mono text-xs font-semibold tracking-wide">{title}</h3>
        {sub && <p className="text-[11px] opacity-60 mt-0.5">{sub}</p>}
      </div>
      {right}
    </header>
    <div className="p-3">{children}</div>
  </section>
);

/* ------------------------------------------------------------------ *
 * Plan DAG. Steps are laid out by dependency depth, so the horizontal
 * axis is the earliest position at which a step could run.
 * ------------------------------------------------------------------ */
export function PlanDAG({ dag, verdicts }) {
  if (!dag || !dag.nodes || !dag.nodes.length) return <Empty>no plan graph</Empty>;

  const depth = {};
  const parents = {};
  dag.nodes.forEach((n) => { parents[n.id] = []; });
  (dag.edges || []).forEach((e) => {
    if (parents[e.to]) parents[e.to].push(e.from);
  });
  // def:plan requires every beta variable to be bound by an EARLIER step, so a
  // single pass in declaration order suffices; no fixpoint is needed here and
  // none is run.
  dag.nodes.forEach((n) => {
    const ps = parents[n.id];
    depth[n.id] = ps.length ? Math.max(...ps.map((p) => (depth[p] ?? 0) + 1)) : 0;
  });

  const cols = {};
  dag.nodes.forEach((n) => {
    const d = depth[n.id];
    (cols[d] = cols[d] || []).push(n);
  });
  const maxD = Math.max(...Object.keys(cols).map(Number));
  const maxRow = Math.max(...Object.values(cols).map((c) => c.length));

  const W = 150, H = 56, PX = 22, PY = 16;
  const pos = {};
  Object.entries(cols).forEach(([d, ns]) =>
    ns.forEach((n, i) => { pos[n.id] = { x: Number(d) * W + PX, y: i * H + PY }; }));
  const width = (maxD + 1) * W + PX;
  const height = maxRow * H + PY + 20;

  return (
    <div className="overflow-x-auto">
      <svg width={width} height={height}>
        <defs>
          <marker id="hfq-arrow" viewBox="0 0 8 8" refX="7" refY="4"
                  markerWidth="7" markerHeight="7" orient="auto">
            <path d="M0,0 L8,4 L0,8 z" fill="currentColor" opacity="0.45" />
          </marker>
        </defs>
        {(dag.edges || []).map((e, i) => {
          const a = pos[e.from];
          const b = pos[e.to];
          if (!a || !b) return null;
          const x1 = a.x + 108, y1 = a.y + 16, x2 = b.x, y2 = b.y + 16;
          const mx = (x1 + x2) / 2;
          return (
            <path key={i} d={`M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`}
                  fill="none" stroke="currentColor" strokeWidth="1.2"
                  opacity="0.35" markerEnd="url(#hfq-arrow)" />
          );
        })}
        {dag.nodes.map((n) => {
          const p = pos[n.id];
          const v = verdictOf((verdicts || {})[n.id]);
          const k = kindOf(n.kind);
          const known = Boolean(verdicts && n.id in verdicts);
          return (
            <g key={n.id} transform={`translate(${p.x},${p.y})`}>
              <rect width="108" height="32" rx="4"
                    fill={known ? v.bg : 'transparent'}
                    stroke={known ? v.color : 'currentColor'}
                    strokeOpacity={known ? 1 : 0.3} strokeWidth="1.2" />
              <text x="8" y="14" fontSize="11" fontFamily="ui-monospace, monospace"
                    fill="currentColor" fontWeight="600">{n.id}</text>
              <text x="8" y="26" fontSize="9" fontFamily="ui-monospace, monospace"
                    fill="currentColor" opacity="0.6">
                {k.glyph} {n.kind}{n.source ? ` ${n.source}` : ''}
              </text>
              {known && (
                <text x="100" y="14" fontSize="9" textAnchor="end"
                      fontFamily="ui-monospace, monospace" fill={v.color}
                      fontWeight="700">{v.label}</text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

/* ------------------------------------------------------------------ *
 * Capability matrix. check.requirements is what each step needs; the
 * failures list is what the source did not declare. The refusal that
 * precedes contact is legible here as a cross at zero requests issued.
 * ------------------------------------------------------------------ */
export function CapabilityMatrix({ check }) {
  if (!check) return <Empty>the plan did not reach the check</Empty>;
  const reqs = check.requirements || {};
  const steps = Object.keys(reqs);
  if (!steps.length) return <Empty>no step declared a capability requirement</Empty>;

  const feats = [...new Set(steps.flatMap((s) => reqs[s]))].sort();
  const missing = {};
  (check.failures || []).forEach((f) => {
    missing[f.step] = new Set(f.missing || []);
  });

  return (
    <div className="overflow-x-auto">
      <table className="text-[11px] font-mono border-collapse">
        <thead>
          <tr>
            <th className="text-left pr-3 pb-1 font-semibold">step</th>
            {feats.map((f) => (
              <th key={f} className="px-2 pb-1 font-normal opacity-70">{f}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {steps.map((s) => (
            <tr key={s}>
              <td className="pr-3 py-0.5 font-semibold">{s}</td>
              {feats.map((f) => {
                const need = reqs[s].includes(f);
                const gone = Boolean(missing[s] && missing[s].has(f));
                return (
                  <td key={f} className="px-1 py-0.5 text-center">
                    <span className="inline-block w-6 h-5 leading-5 rounded"
                      style={{
                        background: !need ? 'transparent'
                          : gone ? VERDICTS.surface.bg : VERDICTS.answer.bg,
                        color: !need ? 'inherit'
                          : gone ? VERDICTS.surface.color : VERDICTS.answer.color,
                        opacity: need ? 1 : 0.2,
                      }}>
                      {!need ? '·' : gone ? '✕' : '✓'}
                    </span>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-[11px] opacity-60 mt-2">
        {check.operations} operations against a declared bound of {check.bound}.{' '}
        {check.well_capability
          ? 'Every required feature is declared, so the plan may issue requests.'
          : 'A required feature is not declared, so the executor halted before issuing any request.'}
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ *
 * Allocation. Fixed costs are charged before the optimiser runs, so
 * both are drawn and the split between them is labelled.
 * ------------------------------------------------------------------ */
export function AllocationView({ allocation }) {
  if (!allocation) return <Empty>no allocation was solved; the plan halted first</Empty>;
  const effort = allocation.effort || {};
  const charged = allocation.charged_first || {};
  const support = new Set(allocation.support || []);
  const keys = Object.keys(effort);
  if (!keys.length) return <Empty>the allocator funded no step</Empty>;
  const max = Math.max(...keys.map((k) => effort[k]), 1);
  const chargedTotal = (allocation.budget ?? 0) -
    (allocation.optimised_budget ?? allocation.budget ?? 0);

  return (
    <div>
      <div className="space-y-1.5">
        {keys.map((k) => {
          const e = effort[k];
          const c = charged[k] || 0;
          const inSupport = support.has(k);
          return (
            <div key={k} className="flex items-center gap-2 text-[11px] font-mono">
              <span className="w-20 truncate" title={k}>{k}</span>
              <span className="flex-1 h-4 bg-dark/5 dark:bg-light/10 rounded-sm relative overflow-hidden">
                <span className="absolute inset-y-0 left-0 rounded-sm"
                      style={{ width: `${(e / max) * 100}%`,
                               background: inSupport ? '#B63E96' : '#B63E9655' }} />
                {c > 0 && (
                  <span className="absolute inset-y-0 left-0 border-r-2"
                        style={{ width: `${(c / max) * 100}%`,
                                 background: '#b4530933', borderColor: '#b45309' }} />
                )}
              </span>
              <span className="w-16 text-right tabular-nums">{fmt(e)}</span>
            </div>
          );
        })}
      </div>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-1 mt-3 text-[11px] font-mono">
        <dt className="opacity-60">budget</dt>
        <dd className="text-right">{fmt(allocation.budget)}</dd>
        <dt className="opacity-60">charged first</dt>
        <dd className="text-right">{fmt(chargedTotal)}</dd>
        <dt className="opacity-60">optimised over</dt>
        <dd className="text-right">{fmt(allocation.optimised_budget)}</dd>
        <dt className="opacity-60">shadow price</dt>
        <dd className="text-right">{fmt(allocation.shadow_price, 5)}</dd>
      </dl>
      <p className="text-[11px] opacity-60 mt-2">
        The amber band is the fixed cost charged before the optimiser runs. The
        price is what one further request would have been worth at the margin.
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ *
 * Retention. Populated on map steps only, so a plan with no map says
 * so rather than drawing zeros that would read as measurements.
 * ------------------------------------------------------------------ */
export function RetentionView({ steps }) {
  const maps = (steps || []).filter(
    (s) => s.retention !== null && s.retention !== undefined);
  if (!maps.length) {
    return <Empty>no map step ran, so retention was never defined</Empty>;
  }

  let running = 1;
  const rows = maps.map((s) => {
    running *= s.retention * (s.amplification ?? 1);
    return { ...s, running };
  });

  return (
    <div>
      <table className="w-full text-[11px] font-mono">
        <thead className="opacity-60">
          <tr>
            <th className="text-left font-normal">step</th>
            <th className="text-right font-normal">retention</th>
            <th className="text-right font-normal">amplification</th>
            <th className="text-right font-normal">running product</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((s) => (
            <tr key={s.step}>
              <td className="py-0.5">{s.step}</td>
              <td className="text-right tabular-nums">{fmt(s.retention)}</td>
              <td className="text-right tabular-nums">{fmt(s.amplification)}</td>
              <td className="text-right tabular-nums font-semibold">{fmt(s.running)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-[11px] opacity-60 mt-2">
        Output size sees only the product of the two, so two maps differing
        fourfold in retention can emit the same number of identifiers.
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ *
 * Verdict timeline: spend against verdict, in execution order.
 * ------------------------------------------------------------------ */
export function VerdictTimeline({ steps, requestsIssued, declaredBudget }) {
  if (!steps || !steps.length) return <Empty>nothing executed</Empty>;
  const spend = steps.map((s) => (s.budget && s.budget.spent) || 0);
  const max = Math.max(...spend, 1);
  let cum = 0;

  return (
    <div>
      <div className="space-y-1">
        {steps.map((s, i) => {
          const v = verdictOf(s.verdict);
          const sp = spend[i];
          cum += sp;
          return (
            <div key={s.step} className="flex items-center gap-2 text-[11px] font-mono">
              <span className="w-4 opacity-40 text-right">{i + 1}</span>
              <span className="w-20 truncate" title={s.step}>{s.step}</span>
              <span className="flex-1 h-4 bg-dark/5 dark:bg-light/10 rounded-sm relative">
                <span className="absolute inset-y-0 left-0 rounded-sm"
                      style={{ width: `${(sp / max) * 100}%`, background: v.color,
                               opacity: 0.75, minWidth: sp > 0 ? '2px' : 0 }} />
              </span>
              <span className="w-10 text-right tabular-nums opacity-70">{fmt(sp)}</span>
              <span className="w-16 text-right font-semibold" style={{ color: v.color }}>
                {v.label}
              </span>
            </div>
          );
        })}
      </div>
      <p className="text-[11px] opacity-60 mt-2 font-mono">
        {requestsIssued} request{requestsIssued === 1 ? '' : 's'} issued
        {declaredBudget !== undefined && declaredBudget !== null
          ? ` against a declared budget of ${fmt(declaredBudget)}`
          : ''}
        {' · '}total spend {fmt(cum)}
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ *
 * Blame, walked to the root for every starved step.
 * ------------------------------------------------------------------ */
export function BlameView({ blame, steps }) {
  const entries = Object.entries(blame || {});
  if (!entries.length) return <Empty>no step starved</Empty>;
  const byVar = Object.fromEntries((steps || []).map((s) => [s.step, s]));

  return (
    <div className="space-y-2">
      {entries.map(([victim, chain]) => {
        const root = byVar[chain[chain.length - 1]];
        const b = root && BLOCKERS[root.blocker];
        return (
          <div key={victim} className="text-[11px] font-mono">
            <div className="flex items-center gap-1 flex-wrap">
              {chain.map((v, i) => {
                const s = byVar[v];
                const vd = verdictOf(s && s.verdict);
                return (
                  <React.Fragment key={v + i}>
                    {i > 0 && <span className="opacity-40">{'←'}</span>}
                    <span className="px-1.5 py-0.5 rounded"
                          style={{ background: vd.bg, color: vd.color }}>{v}</span>
                  </React.Fragment>
                );
              })}
            </div>
            {b && (
              <p className="opacity-60 mt-0.5 pl-1">
                root blocker <span style={{ color: '#b45309' }}>{b.label}</span>
                {' — '}{b.note}
              </p>
            )}
          </div>
        );
      })}
      <p className="text-[11px] opacity-60">
        Positions strictly decrease along a chain, so the walk terminates by
        arithmetic rather than by a hop limit.
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ *
 * The lowered concrete query: the plan is abstract, and this is what a
 * source was actually asked.
 * ------------------------------------------------------------------ */
export function ConcreteQueries({ steps }) {
  const withQ = (steps || []).filter((s) => s.provenance && s.provenance.concrete);
  if (!withQ.length) {
    return <Empty>no step issued a request, so nothing was lowered</Empty>;
  }

  return (
    <div className="space-y-2">
      {withQ.map((s) => (
        <details key={s.step} open={withQ.length <= 2}>
          <summary className="cursor-pointer text-[11px] font-mono flex items-center gap-2">
            <span className="font-semibold">{s.step}</span>
            <span className="opacity-50">{s.source}</span>
            <span className="opacity-40">
              {s.provenance.snapshot}{' · '}{s.provenance.lowered_form}
            </span>
          </summary>
          <pre className="mt-1 p-2 rounded bg-dark/[0.04] dark:bg-light/[0.06]
                          text-[10.5px] leading-relaxed overflow-x-auto font-mono">
            {s.provenance.concrete}
          </pre>
        </details>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ *
 * Payload: the extent an `answer` carries. No other verdict has one.
 * ------------------------------------------------------------------ */
export function PayloadView({ steps }) {
  const withP = (steps || []).filter((s) => s.payload);
  if (!withP.length) {
    return <Empty>no step returned a payload, which is what the five non-answer verdicts have in common</Empty>;
  }
  return (
    <div className="space-y-2">
      {withP.map((s) => (
        <details key={s.step} open={withP.length === 1}>
          <summary className="cursor-pointer text-[11px] font-mono flex items-center gap-2">
            <span className="font-semibold">{s.step}</span>
            <span className="opacity-50">{s.payload.namespace}</span>
            <span className="opacity-40">{s.payload.size} identifiers</span>
          </summary>
          <div className="mt-1 flex flex-wrap gap-1">
            {(s.payload.identifiers || []).map((id) => (
              <span key={id}
                    className="px-1.5 py-0.5 rounded text-[10px] font-mono
                               bg-dark/[0.05] dark:bg-light/[0.08]"
                    title={JSON.stringify(
                      (s.payload.attributes || {})[id] || {}, null, 1)}>
                {id}
              </span>
            ))}
          </div>
        </details>
      ))}
    </div>
  );
}
