import React, { useCallback, useState } from 'react';
import { motion } from 'framer-motion';
import { useSBS, useSBSDispatch } from './SBSContext';
import { solveCircuit } from '@/lib/sbs/shaderSolver';
import { extractMetrics } from '@/lib/sbs/metricsExtractor';

export default function ObservationPanel() {
  const { circuit, perturbation, shaderResult, healthyBaseline, metrics } = useSBS();
  const dispatch = useSBSDispatch();
  const [observing, setObserving] = useState(false);

  const handleObserve = useCallback(() => {
    if (!circuit) return;
    setObserving(true);
    dispatch({ type: 'CLEAR_ERROR' });

    requestAnimationFrame(() => {
      try {
        const pertList = perturbation
          ? Object.entries(perturbation).map(([idx, factor]) => ({ idx: parseInt(idx), factor }))
          : null;

        const result = solveCircuit(circuit, pertList);
        dispatch({ type: 'SET_SHADER_RESULT', result });

        const baselineResult = healthyBaseline || result;
        const m = extractMetrics(result, circuit, baselineResult, pertList);
        dispatch({ type: 'SET_METRICS', metrics: m });
      } catch (err) {
        dispatch({ type: 'SET_ERROR', error: 'Observation failed: ' + err.message });
      } finally {
        setObserving(false);
      }
    });
  }, [circuit, perturbation, healthyBaseline, dispatch]);

  const handleReset = useCallback(() => {
    dispatch({ type: 'CLEAR_PERTURBATION' });
  }, [dispatch]);

  if (!circuit) return null;

  return (
    <div className="bg-light dark:bg-dark border border-dark/10 dark:border-light/10 rounded-xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold text-lg text-dark dark:text-light">
          3. Observe
        </h3>
        <div className="flex gap-2">
          {perturbation && (
            <button
              onClick={handleReset}
              className="px-3 py-1.5 rounded-lg text-sm border border-dark/20 dark:border-light/20
                         text-dark/60 dark:text-light/60 hover:border-primary dark:hover:border-primaryDark
                         transition-colors"
            >
              Reset Healthy
            </button>
          )}
          <button
            onClick={handleObserve}
            disabled={observing}
            className="px-4 py-1.5 rounded-lg bg-primary dark:bg-primaryDark text-light
                       hover:opacity-90 transition-opacity font-medium text-sm disabled:opacity-50"
          >
            {observing ? 'Observing...' : shaderResult ? 'Re-observe' : 'Observe'}
          </button>
        </div>
      </div>

      {metrics && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-2 sm:grid-cols-4 gap-3"
        >
          <MetricCard
            label="Coherence R"
            value={metrics.R.toFixed(4)}
            status={metrics.R > 0.7 ? 'good' : metrics.R > 0.5 ? 'warn' : 'bad'}
          />
          <MetricCard
            label="Visibility V"
            value={metrics.V.toFixed(4)}
            status={metrics.V > 0.95 ? 'good' : metrics.V > 0.3 ? 'warn' : 'bad'}
          />
          <MetricCard
            label="Render Time"
            value={`${metrics.renderTimeMs.toFixed(1)} ms`}
            status={metrics.renderTimeMs < 100 ? 'good' : 'warn'}
          />
          <MetricCard
            label="Backend"
            value={metrics.backend.toUpperCase()}
            status="neutral"
          />
        </motion.div>
      )}

      {!shaderResult && (
        <p className="text-sm text-dark/50 dark:text-light/50">
          Click Observe to run the shader solver on the circuit. The observation computes
          S-entropy coordinates (Se, Sk, St) for each node in a single GPU pass.
        </p>
      )}
    </div>
  );
}

function MetricCard({ label, value, status }) {
  const colors = {
    good: 'border-green-500/30 bg-green-500/5',
    warn: 'border-yellow-500/30 bg-yellow-500/5',
    bad: 'border-red-500/30 bg-red-500/5',
    neutral: 'border-dark/10 dark:border-light/10 bg-dark/5 dark:bg-light/5',
  };

  return (
    <div className={`p-3 rounded-lg border ${colors[status]}`}>
      <div className="text-xs text-dark/50 dark:text-light/50 mb-1">{label}</div>
      <div className="text-lg font-bold text-dark dark:text-light">{value}</div>
    </div>
  );
}
