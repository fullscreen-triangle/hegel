import React, { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { compileSBS, validateSBS } from '@/lib/sbs/dsl/compiler';
import { EXAMPLES, DEFAULT_EXAMPLE } from '@/lib/sbs/dsl/examples';
import { KEYWORDS } from '@/lib/sbs/dsl/tokenizer';
import { solveCircuit, computeFluxPattern } from '@/lib/sbs/shaderSolver';
import { extractMetrics } from '@/lib/sbs/metricsExtractor';

const TABS = ['output', 'ast', 'glsl', 'js', 'circuit'];

function LineNumbers({ count }) {
  return (
    <div className="select-none text-right pr-3 pt-3 text-xs font-mono text-dark/30 dark:text-light/30 leading-[1.5rem]"
         style={{ minWidth: 40 }}>
      {Array.from({ length: count }, (_, i) => (
        <div key={i}>{i + 1}</div>
      ))}
    </div>
  );
}

function ErrorPanel({ errors, warnings }) {
  if (errors.length === 0 && warnings.length === 0) return null;
  return (
    <div className="border-t border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-900/20 p-3 max-h-32 overflow-auto">
      {errors.map((e, i) => (
        <div key={`e${i}`} className="text-red-600 dark:text-red-400 text-xs font-mono">
          Error{e.line ? ` (line ${e.line})` : ''}: {e.message}
        </div>
      ))}
      {warnings.map((w, i) => (
        <div key={`w${i}`} className="text-yellow-600 dark:text-yellow-400 text-xs font-mono">
          Warning: {w.message}
        </div>
      ))}
    </div>
  );
}

function MetricsBar({ metrics }) {
  if (!metrics) return null;
  const items = [
    { label: 'R (Coherence)', value: metrics.R?.toFixed(4) || '—', color: metrics.R > 0.5 ? 'text-green-500' : 'text-red-500' },
    { label: 'V (Visibility)', value: metrics.V?.toFixed(4) || '—', color: metrics.V > 0.5 ? 'text-green-500' : 'text-red-500' },
    { label: 'Nodes', value: metrics.numNodes || '—' },
    { label: 'Edges', value: metrics.numEdges || '—' },
    { label: 'Backend', value: metrics.backend || '—' },
    { label: 'Time', value: metrics.renderTimeMs ? `${metrics.renderTimeMs.toFixed(1)}ms` : '—' },
  ];

  return (
    <div className="flex flex-wrap gap-4 p-3 bg-dark/5 dark:bg-light/5 border-t border-dark/10 dark:border-light/10">
      {items.map(({ label, value, color }) => (
        <div key={label} className="text-xs">
          <span className="text-dark/50 dark:text-light/50">{label}: </span>
          <span className={`font-mono font-bold ${color || ''}`}>{value}</span>
        </div>
      ))}
    </div>
  );
}

export default function PlaygroundEditor() {
  const [source, setSource] = useState(EXAMPLES[DEFAULT_EXAMPLE].code);
  const [activeTab, setActiveTab] = useState('output');
  const [compileResult, setCompileResult] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [autoCompile, setAutoCompile] = useState(true);
  const [selectedExample, setSelectedExample] = useState(DEFAULT_EXAMPLE);
  const textareaRef = useRef(null);
  const compileTimerRef = useRef(null);

  const doCompile = useCallback((code) => {
    const result = compileSBS(code);
    setCompileResult(result);

    if (result.success && result.circuit) {
      try {
        const shaderResult = solveCircuit(result.circuit, result.perturbations);
        const healthyResult = solveCircuit(result.circuit, null);
        const healthyFluxes = computeFluxPattern(result.circuit, null);
        const currentFluxes = computeFluxPattern(result.circuit, result.perturbations);
        const m = extractMetrics(result.circuit, shaderResult, healthyResult, result.perturbations);
        setMetrics({
          ...m,
          numNodes: result.circuit.numNodes,
          numEdges: result.circuit.numEdges,
          backend: shaderResult.backend || 'cpu',
          renderTimeMs: shaderResult.renderTimeMs,
        });
      } catch (e) {
        setMetrics(null);
      }
    } else {
      setMetrics(null);
    }
  }, []);

  const handleChange = useCallback((e) => {
    const code = e.target.value;
    setSource(code);

    if (autoCompile) {
      clearTimeout(compileTimerRef.current);
      compileTimerRef.current = setTimeout(() => doCompile(code), 300);
    }
  }, [autoCompile, doCompile]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const { selectionStart, selectionEnd } = e.target;
      const newSource = source.slice(0, selectionStart) + '  ' + source.slice(selectionEnd);
      setSource(newSource);
      requestAnimationFrame(() => {
        e.target.selectionStart = e.target.selectionEnd = selectionStart + 2;
      });
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      doCompile(source);
    }
  }, [source, doCompile]);

  useEffect(() => {
    doCompile(source);
  }, []);

  const lineCount = source.split('\n').length;

  const renderOutput = () => {
    if (!compileResult) return <div className="p-4 text-dark/50 dark:text-light/50 text-sm">Press Ctrl+Enter or enable auto-compile</div>;

    if (!compileResult.success) {
      return <ErrorPanel errors={compileResult.errors} warnings={compileResult.warnings || []} />;
    }

    switch (activeTab) {
      case 'output':
        return (
          <div className="p-4 space-y-2">
            <div className="text-green-600 dark:text-green-400 text-sm font-mono">Compilation successful</div>
            {compileResult.circuit && (
              <div className="text-xs font-mono space-y-1">
                <div>Circuit: {compileResult.circuit.numNodes} nodes, {compileResult.circuit.numEdges} edges</div>
                <div>Compartments: {compileResult.circuit.compartments?.join(', ')}</div>
                {compileResult.perturbations?.length > 0 && (
                  <div>Perturbations: {compileResult.perturbations.length} active</div>
                )}
                {compileResult.observations?.length > 0 && (
                  <div>Observations: {compileResult.observations.length} queued</div>
                )}
              </div>
            )}
            {compileResult.warnings?.length > 0 && (
              <ErrorPanel errors={[]} warnings={compileResult.warnings} />
            )}
          </div>
        );

      case 'ast':
        return (
          <pre className="p-4 text-xs font-mono overflow-auto max-h-[500px] text-dark/80 dark:text-light/80">
            {JSON.stringify(compileResult.ast, null, 2)}
          </pre>
        );

      case 'glsl':
        return (
          <pre className="p-4 text-xs font-mono overflow-auto max-h-[500px] text-dark/80 dark:text-light/80 whitespace-pre">
            {compileResult.glsl || '// No GLSL output — define a circuit first'}
          </pre>
        );

      case 'js':
        return (
          <pre className="p-4 text-xs font-mono overflow-auto max-h-[500px] text-dark/80 dark:text-light/80 whitespace-pre">
            {compileResult.js || '// No JS output — define a circuit first'}
          </pre>
        );

      case 'circuit':
        return (
          <pre className="p-4 text-xs font-mono overflow-auto max-h-[500px] text-dark/80 dark:text-light/80">
            {compileResult.circuit
              ? JSON.stringify(compileResult.circuit, null, 2)
              : '// No circuit defined'}
          </pre>
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-120px)]">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-dark/10 dark:border-light/10">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold">SBS Playground</h1>
          <select
            value={selectedExample}
            onChange={(e) => {
              setSelectedExample(e.target.value);
              setSource(EXAMPLES[e.target.value].code);
              doCompile(EXAMPLES[e.target.value].code);
            }}
            className="text-sm bg-transparent border border-dark/20 dark:border-light/20 rounded px-2 py-1 text-dark dark:text-light"
          >
            {Object.entries(EXAMPLES).map(([key, ex]) => (
              <option key={key} value={key} className="bg-light dark:bg-dark">
                {ex.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-1 text-xs">
            <input
              type="checkbox"
              checked={autoCompile}
              onChange={(e) => setAutoCompile(e.target.checked)}
              className="rounded"
            />
            Auto-compile
          </label>
          <button
            onClick={() => doCompile(source)}
            className="px-3 py-1 text-xs font-medium bg-dark text-light dark:bg-light dark:text-dark rounded hover:opacity-80 transition"
          >
            Run (Ctrl+Enter)
          </button>
        </div>
      </div>

      {/* Main split */}
      <div className="flex flex-1 overflow-hidden lg:flex-col">
        {/* Editor */}
        <div className="flex-1 flex overflow-hidden border-r border-dark/10 dark:border-light/10 lg:border-r-0 lg:border-b">
          <LineNumbers count={lineCount} />
          <textarea
            ref={textareaRef}
            value={source}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            spellCheck={false}
            className="flex-1 p-3 bg-transparent resize-none outline-none font-mono text-sm leading-[1.5rem] text-dark dark:text-light overflow-auto"
            style={{ tabSize: 2 }}
          />
        </div>

        {/* Output */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Output tabs */}
          <div className="flex border-b border-dark/10 dark:border-light/10 bg-dark/3 dark:bg-light/3">
            {TABS.map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 text-xs font-medium uppercase tracking-wide transition
                  ${activeTab === tab
                    ? 'border-b-2 border-dark dark:border-light text-dark dark:text-light'
                    : 'text-dark/40 dark:text-light/40 hover:text-dark/70 dark:hover:text-light/70'
                  }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Output content */}
          <div className="flex-1 overflow-auto">
            {renderOutput()}
          </div>

          {/* Metrics bar */}
          <MetricsBar metrics={metrics} />

          {/* Errors */}
          {compileResult && !compileResult.success && (
            <ErrorPanel errors={compileResult.errors} warnings={compileResult.warnings || []} />
          )}
        </div>
      </div>

      {/* DSL reference */}
      <div className="border-t border-dark/10 dark:border-light/10 px-4 py-2 text-xs text-dark/40 dark:text-light/40 flex gap-4 flex-wrap">
        <span className="font-medium">Keywords:</span>
        {Array.from(KEYWORDS).slice(0, 20).map(kw => (
          <code key={kw} className="text-dark/60 dark:text-light/60">{kw}</code>
        ))}
        <span>...</span>
        <span className="ml-auto">S-entropy: <code>#(Se, Sk, St)</code> | Triple: <code>triple(k, t, e)</code> | Pipe: <code>|&gt;</code></span>
      </div>
    </div>
  );
}
