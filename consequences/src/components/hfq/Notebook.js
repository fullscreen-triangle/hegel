import React, { useCallback, useEffect, useRef, useState } from 'react';
import { runPlan } from '@/lib/hfq';
import { PLANS, SECTIONS, byId } from '@/lib/hfq/plans';
import { verdictOf, VERDICTS, WORLDS, fmt } from './theme';
import {
  Panel, PlanDAG, CapabilityMatrix, AllocationView, RetentionView,
  VerdictTimeline, BlameView, ConcreteQueries, PayloadView,
} from './Views';

// A notebook of plans. Each cell holds one plan and, once run, the execution
// the interpreter returned for it.
//
// The cell is the unit because the plan is: a plan carries its own budget and
// is checked, allocated and executed as a whole, so there is no smaller thing
// to run. Cells do not share state -- running cell 3 does not depend on cell 2
// having run -- which matches the interpreter, where each plan is executed
// against a freshly built registry.

let SEQ = 0;
const uid = () => `c${++SEQ}`;

const newCell = (source = '') => ({
  id: uid(), source, result: null, running: false, ran: 0, elapsed: null,
});

const STAGES = ['parse', 'resolve', 'check', 'allocate', 'execute'];

/* ---------------------------------------------------------------- */

function StageTrail({ result }) {
  // Where the plan got to. A plan that halts at the check never reaches
  // allocation, and drawing an empty allocation panel would misreport that as
  // an allocation of nothing.
  let reached = STAGES.length;
  let failedAt = -1;
  if (result && !result.ok) {
    failedAt = STAGES.indexOf(result.stage);
    reached = failedAt < 0 ? 0 : failedAt;
  } else if (result && result.ok) {
    if (!result.check || result.check.well_capability === false) reached = 3;
    else if (!result.allocation) reached = 4;
  }

  return (
    <div className="flex items-center gap-1 flex-wrap">
      {STAGES.map((s, i) => {
        const failed = i === failedAt;
        const done = i < reached;
        return (
          <React.Fragment key={s}>
            {i > 0 && <span className="opacity-25 text-[10px]">{'›'}</span>}
            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono"
              style={{
                background: failed ? VERDICTS.refused.bg
                  : done ? VERDICTS.answer.bg : 'transparent',
                color: failed ? VERDICTS.refused.color
                  : done ? VERDICTS.answer.color : 'inherit',
                opacity: failed || done ? 1 : 0.35,
              }}>
              {s}
            </span>
          </React.Fragment>
        );
      })}
    </div>
  );
}

function VerdictStrip({ result }) {
  if (!result || !result.ok || !result.steps) return null;
  const counts = {};
  result.steps.forEach((s) => { counts[s.verdict] = (counts[s.verdict] || 0) + 1; });
  const answers = counts.answer || 0;
  const total = result.steps.length;

  return (
    <div className="flex items-center gap-3 flex-wrap text-[11px] font-mono">
      {Object.entries(counts).map(([v, n]) => {
        const vd = verdictOf(v);
        return (
          <span key={v} className="px-1.5 py-0.5 rounded" title={vd.note}
                style={{ background: vd.bg, color: vd.color }}>
            {n}{'×'} {vd.label}
          </span>
        );
      })}
      {answers < total && (
        <span className="opacity-60">
          {total - answers} of {total} steps carry no payload, and a caller
          reading only success or failure cannot tell them apart.
        </span>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------- */

function Cell({ cell, index, onChange, onRun, onDelete, onInsertAfter }) {
  const ta = useRef(null);
  const r = cell.result;

  const keydown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      onRun(cell.id);
    }
    if (e.key === 'Tab') {
      e.preventDefault();
      const el = ta.current;
      const { selectionStart: a, selectionEnd: b } = el;
      const next = `${cell.source.slice(0, a)}  ${cell.source.slice(b)}`;
      onChange(cell.id, next);
      requestAnimationFrame(() => { el.selectionStart = el.selectionEnd = a + 2; });
    }
  };

  const lines = cell.source.split('\n').length;

  return (
    <article className="border border-dark/20 dark:border-light/20 rounded-lg overflow-hidden
                        bg-light dark:bg-dark">
      <header className="flex items-center gap-2 px-3 py-1.5 border-b
                         border-dark/10 dark:border-light/10
                         bg-dark/[0.02] dark:bg-light/[0.03]">
        <span className="font-mono text-[11px] opacity-40 w-10">
          [{cell.ran ? cell.ran : ' '}]
        </span>
        <StageTrail result={r} />
        <div className="flex-1" />
        {cell.elapsed !== null && (
          <span className="font-mono text-[10px] opacity-40">{cell.elapsed} ms</span>
        )}
        {r && r.world && (
          <span className="font-mono text-[10px] px-1.5 py-0.5 rounded
                           bg-dark/[0.05] dark:bg-light/[0.08]"
                title={(WORLDS[r.world] || {}).note}>
            {r.world}
          </span>
        )}
        <button onClick={() => onRun(cell.id)} disabled={cell.running}
          className="font-mono text-[11px] px-2 py-0.5 rounded
                     bg-primary text-light disabled:opacity-40
                     hover:bg-primary/85 transition-colors">
          {cell.running ? 'running' : 'run'}
        </button>
        <button onClick={() => onInsertAfter(cell.id)} title="insert a cell below"
          className="font-mono text-[11px] px-1.5 opacity-50 hover:opacity-100">+</button>
        <button onClick={() => onDelete(cell.id)} title="delete this cell"
          className="font-mono text-[11px] px-1.5 opacity-50 hover:opacity-100">{'×'}</button>
      </header>

      <div className="relative">
        <textarea
          ref={ta}
          value={cell.source}
          spellCheck={false}
          onChange={(e) => onChange(cell.id, e.target.value)}
          onKeyDown={keydown}
          rows={Math.max(6, Math.min(lines + 1, 28))}
          className="w-full resize-y px-3 py-2 font-mono text-[12px] leading-relaxed
                     bg-transparent outline-none
                     focus:bg-primary/[0.03] transition-colors"
          placeholder={'plan example {\n  budget 4 requests\n  let x = from chebi ask descendants_of("CHEBI:1") within 2\n  emit x with provenance\n}'}
        />
      </div>

      {r && <Output result={r} index={index} />}
    </article>
  );
}

/* ---------------------------------------------------------------- */

function Failure({ result }) {
  return (
    <div className="px-3 py-3 border-t border-dark/10 dark:border-light/10">
      <div className="flex items-baseline gap-2">
        <span className="font-mono text-[11px] px-1.5 py-0.5 rounded"
              style={{ background: VERDICTS.refused.bg, color: VERDICTS.refused.color }}>
          {result.stage}
        </span>
        <p className="font-mono text-[12px]">{result.error}</p>
      </div>
      {result.line && (
        <p className="font-mono text-[11px] opacity-50 mt-1">at line {result.line}</p>
      )}
      {result.declared && (
        <p className="font-mono text-[11px] opacity-60 mt-2">
          sources the fixture worlds declare: {result.declared.join(', ')}
        </p>
      )}
      {result.detail && (
        <pre className="mt-2 p-2 rounded text-[10px] overflow-x-auto
                        bg-dark/[0.04] dark:bg-light/[0.06]">{result.detail}</pre>
      )}
    </div>
  );
}

function Output({ result }) {
  const [tab, setTab] = useState('overview');
  if (!result.ok) return <Failure result={result} />;

  const verdicts = {};
  (result.steps || []).forEach((s) => { verdicts[s.step] = s.verdict; });
  const refusedStatically = result.emitted && result.emitted.refusal;

  const TABS = [
    ['overview', 'overview'],
    ['capability', 'capability'],
    ['allocation', 'allocation'],
    ['retention', 'retention'],
    ['lowered', 'lowered query'],
    ['payload', 'payload'],
    ['json', 'json'],
  ];

  return (
    <div className="border-t border-dark/10 dark:border-light/10">
      <div className="flex items-center gap-1 px-3 pt-2 flex-wrap">
        {TABS.map(([k, label]) => (
          <button key={k} onClick={() => setTab(k)}
            className={`font-mono text-[11px] px-2 py-0.5 rounded transition-colors ${
              tab === k ? 'bg-primary text-light'
                        : 'opacity-55 hover:opacity-100 hover:bg-dark/[0.05] dark:hover:bg-light/[0.08]'
            }`}>
            {label}
          </button>
        ))}
      </div>

      <div className="p-3 space-y-3">
        {refusedStatically && (
          <div className="px-3 py-2 rounded text-[11px] font-mono"
               style={{ background: VERDICTS.surface.bg, color: VERDICTS.surface.color }}>
            {result.emitted.refusal.reason} — {result.requests_issued} requests issued.
          </div>
        )}

        {tab === 'overview' && (
          <>
            <VerdictStrip result={result} />
            <Panel title="plan" sub="steps laid out by dependency depth; colour is the verdict each returned">
              <PlanDAG dag={result.dag} verdicts={verdicts} />
            </Panel>
            <div className="grid grid-cols-2 md:grid-cols-1 gap-3">
              <Panel title="verdicts" sub="spend per step, in execution order">
                <VerdictTimeline steps={result.steps}
                                 requestsIssued={result.requests_issued}
                                 declaredBudget={result.declared_budget} />
              </Panel>
              <Panel title="blame" sub="each starved step walked to its root cause">
                <BlameView blame={result.blame} steps={result.steps} />
              </Panel>
            </div>
          </>
        )}

        {tab === 'capability' && (
          <Panel title="capability"
                 sub="what each step requires against what its source declares">
            <CapabilityMatrix check={result.check} />
          </Panel>
        )}

        {tab === 'allocation' && (
          <Panel title="allocation" sub="effort per step, with fixed costs charged first">
            <AllocationView allocation={result.allocation} />
          </Panel>
        )}

        {tab === 'retention' && (
          <Panel title="retention" sub="defined on map steps only">
            <RetentionView steps={result.steps} />
          </Panel>
        )}

        {tab === 'lowered' && (
          <Panel title="lowered query"
                 sub="the concrete query the abstract request was lowered into">
            <ConcreteQueries steps={result.steps} />
          </Panel>
        )}

        {tab === 'payload' && (
          <Panel title="payload" sub="the extent an answer carries">
            <PayloadView steps={result.steps} />
          </Panel>
        )}

        {tab === 'json' && (
          <pre className="p-2 rounded text-[10px] leading-relaxed overflow-auto max-h-96
                          bg-dark/[0.04] dark:bg-light/[0.06] font-mono">
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- */

export default function Notebook({ initial = 'healthy_chain' }) {
  const [cells, setCells] = useState(() => [newCell(byId(initial)?.source || '')]);
  const [counter, setCounter] = useState(0);
  const [showPresets, setShowPresets] = useState(false);

  const update = useCallback((id, source) => {
    setCells((cs) => cs.map((c) => (c.id === id ? { ...c, source } : c)));
  }, []);

  // The interpreter runs HERE, in this tab. `runPlan` is the whole pipeline --
  // parse, resolve, check, allocate, execute -- and it reaches no server,
  // which is what makes "no request leaves the machine" a property of the page
  // rather than a claim about its configuration.
  //
  // It stays async because the engine boundary is where the Rust CLI attaches:
  // a paired session sends the plan to a local binary over its token and awaits
  // the same document shape. Nothing else in the component would change.
  const run = useCallback(async (id) => {
    setCells((cs) => cs.map((c) => (c.id === id ? { ...c, running: true } : c)));
    const cell = cells.find((c) => c.id === id);
    const t0 = performance.now();
    let result;
    try {
      result = runPlan((cell && cell.source) || '');
    } catch (e) {
      // runPlan documents that it never throws; if it does, that is a defect in
      // the interpreter and the cell says so rather than rendering blank.
      result = { ok: false, stage: 'internal', error: String(e && e.message ? e.message : e) };
    }
    const elapsed = Math.round(performance.now() - t0);
    setCounter((n) => {
      const next = n + 1;
      setCells((cs) => cs.map((c) =>
        c.id === id ? { ...c, running: false, result, elapsed, ran: next } : c));
      return next;
    });
  }, [cells]);

  const runAll = useCallback(async () => {
    for (const c of cells) await run(c.id);
  }, [cells, run]);

  const insertAfter = useCallback((id, source = '') => {
    setCells((cs) => {
      const i = cs.findIndex((c) => c.id === id);
      const next = [...cs];
      next.splice(i + 1, 0, newCell(source));
      return next;
    });
  }, []);

  const remove = useCallback((id) => {
    setCells((cs) => (cs.length === 1 ? [newCell()] : cs.filter((c) => c.id !== id)));
  }, []);

  const appendPreset = useCallback((preset) => {
    setCells((cs) => [...cs, newCell(preset.source)]);
    setShowPresets(false);
    requestAnimationFrame(() =>
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }));
  }, []);

  return (
    <div className="w-full">
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <button onClick={runAll}
          className="font-mono text-[12px] px-3 py-1 rounded bg-primary text-light
                     hover:bg-primary/85 transition-colors">
          run all
        </button>
        <button onClick={() => setShowPresets((v) => !v)}
          className="font-mono text-[12px] px-3 py-1 rounded border
                     border-dark/25 dark:border-light/25
                     hover:bg-dark/[0.05] dark:hover:bg-light/[0.08] transition-colors">
          plans from the validation suite ({PLANS.length})
        </button>
        <button onClick={() => setCells((cs) => [...cs, newCell()])}
          className="font-mono text-[12px] px-3 py-1 rounded border
                     border-dark/25 dark:border-light/25
                     hover:bg-dark/[0.05] dark:hover:bg-light/[0.08] transition-colors">
          new cell
        </button>
        <span className="font-mono text-[11px] opacity-40">ctrl+enter runs a cell</span>
      </div>

      {/* Grouped by what each plan demonstrates rather than presented as a flat
          list: a reader looking for the refusals should not have to know which
          of twenty-four names carries one. */}
      {showPresets && (
        <div className="mb-4 space-y-3">
          {Object.entries(SECTIONS).map(([key, meta]) => {
            const inSection = PLANS.filter((p) => p.section === key);
            if (!inSection.length) return null;
            return (
              <div key={key}>
                <h3 className="font-mono text-[11px] font-semibold opacity-70 mb-1.5">
                  {meta.title} <span className="opacity-50">({inSection.length})</span>
                </h3>
                <div className="grid grid-cols-3 lg:grid-cols-2 sm:grid-cols-1 gap-2">
                  {inSection.map((p) => (
                    <button key={p.id} onClick={() => appendPreset(p)}
                      className="text-left p-2 rounded border border-dark/15 dark:border-light/15
                                 hover:border-primary hover:bg-primary/[0.04] transition-colors">
                      <div className="font-mono text-[12px] font-semibold">{p.id}</div>
                      <div className="font-mono text-[10px] opacity-50 mt-1 line-clamp-2">
                        {p.blurb || `${p.source.split('\n').length} lines`}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="space-y-4">
        {cells.map((c, i) => (
          <Cell key={c.id} cell={c} index={i}
                onChange={update} onRun={run}
                onDelete={remove} onInsertAfter={insertAfter} />
        ))}
      </div>

    </div>
  );
}
