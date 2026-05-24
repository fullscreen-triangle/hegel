import React, { useCallback, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useSBS, useSBSDispatch } from './SBSContext';
import { solveCircuit } from '@/lib/sbs/shaderSolver';
import { extractMetrics, findOptimalPerturbation } from '@/lib/sbs/metricsExtractor';

export default function PerturbationEditor() {
  const { circuit, perturbation, healthyBaseline } = useSBS();
  const dispatch = useSBSDispatch();

  const sortedEdges = useMemo(() => {
    if (!circuit) return [];
    return circuit.edges
      .map(e => ({ ...e }))
      .sort((a, b) => b.conductance - a.conductance);
  }, [circuit]);

  const handleSliderChange = useCallback((edgeIdx, value) => {
    const factor = parseFloat(value);
    const newPert = { ...(perturbation || {}) };
    if (Math.abs(factor - 1.0) < 0.01) {
      delete newPert[edgeIdx];
    } else {
      newPert[edgeIdx] = factor;
    }
    dispatch({ type: 'SET_PERTURBATION', perturbation: Object.keys(newPert).length > 0 ? newPert : null });
  }, [perturbation, dispatch]);

  const handleDisease = useCallback((severity) => {
    if (!circuit) return;
    const topEdges = sortedEdges.slice(0, 3);
    const newPert = {};
    for (const e of topEdges) {
      newPert[e.id] = severity;
    }
    dispatch({ type: 'SET_PERTURBATION', perturbation: newPert });

    requestAnimationFrame(() => {
      const pertList = Object.entries(newPert).map(([idx, factor]) => ({ idx: parseInt(idx), factor }));
      const result = solveCircuit(circuit, pertList);
      dispatch({ type: 'SET_SHADER_RESULT', result });
      const m = extractMetrics(result, circuit, healthyBaseline, pertList);
      dispatch({ type: 'SET_METRICS', metrics: m });
    });
  }, [circuit, sortedEdges, healthyBaseline, dispatch]);

  const handleRestore = useCallback(() => {
    if (!circuit || !perturbation) return;
    const pertList = Object.entries(perturbation).map(([idx, factor]) => ({ idx: parseInt(idx), factor }));
    const restoration = findOptimalPerturbation(circuit, pertList);

    const newPert = { ...(perturbation || {}) };
    for (const r of restoration) {
      const current = newPert[r.idx] || 1.0;
      newPert[r.idx] = current * r.factor;
    }
    dispatch({ type: 'SET_PERTURBATION', perturbation: newPert });

    requestAnimationFrame(() => {
      const pertListNew = Object.entries(newPert).map(([idx, factor]) => ({ idx: parseInt(idx), factor }));
      const result = solveCircuit(circuit, pertListNew);
      dispatch({ type: 'SET_SHADER_RESULT', result });
      const m = extractMetrics(result, circuit, healthyBaseline, pertListNew);
      dispatch({ type: 'SET_METRICS', metrics: m });
    });
  }, [circuit, perturbation, healthyBaseline, dispatch]);

  if (!circuit) return null;

  return (
    <div className="bg-light dark:bg-dark border border-dark/10 dark:border-light/10 rounded-xl p-6 shadow-sm">
      <h3 className="font-bold text-sm mb-4 text-dark dark:text-light">Edge Perturbations</h3>

      <div className="flex flex-wrap gap-2 mb-4">
        <button
          onClick={() => handleDisease(0.1)}
          className="px-3 py-1 rounded text-xs border border-red-500/30 text-red-600 dark:text-red-400
                     hover:bg-red-500/10 transition-colors"
        >
          Severe Disease (90%)
        </button>
        <button
          onClick={() => handleDisease(0.5)}
          className="px-3 py-1 rounded text-xs border border-yellow-500/30 text-yellow-600 dark:text-yellow-400
                     hover:bg-yellow-500/10 transition-colors"
        >
          Moderate Disease (50%)
        </button>
        {perturbation && (
          <button
            onClick={handleRestore}
            className="px-3 py-1 rounded text-xs border border-green-500/30 text-green-600 dark:text-green-400
                       hover:bg-green-500/10 transition-colors"
          >
            l1-Optimal Restore
          </button>
        )}
      </div>

      <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
        {sortedEdges.map((edge) => {
          const factor = perturbation?.[edge.id] ?? 1.0;
          const isPerturbed = Math.abs(factor - 1.0) > 0.01;

          return (
            <motion.div
              key={edge.id}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className={`p-2 rounded-lg text-xs ${
                isPerturbed
                  ? 'bg-red-500/5 border border-red-500/20'
                  : 'bg-dark/5 dark:bg-light/5'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-dark dark:text-light">
                  {edge.name}
                </span>
                <span className={`font-mono ${isPerturbed ? 'text-red-500' : 'text-dark/50 dark:text-light/50'}`}>
                  {(factor * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0.01"
                max="10"
                step="0.01"
                value={factor}
                onChange={(e) => handleSliderChange(edge.id, e.target.value)}
                className="w-full h-1 rounded-lg appearance-none cursor-pointer
                           bg-dark/20 dark:bg-light/20
                           accent-primary dark:accent-primaryDark"
              />
              <div className="flex justify-between text-dark/30 dark:text-light/30 mt-0.5">
                <span>1%</span>
                <span>100%</span>
                <span>1000%</span>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
