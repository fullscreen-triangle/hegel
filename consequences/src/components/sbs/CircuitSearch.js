import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useSBS, useSBSDispatch } from './SBSContext';
import { buildCircuitFromSBML, buildDemoGlycolysis } from '@/lib/sbs/circuitBuilder';

export default function CircuitSearch() {
  const { searchQuery, searchResults, searchLoading, selectedPathway, circuit } = useSBS();
  const dispatch = useSBSDispatch();
  const [loadingPathway, setLoadingPathway] = useState(false);

  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) return;
    dispatch({ type: 'SET_SEARCH_LOADING', loading: true });
    dispatch({ type: 'CLEAR_ERROR' });
    try {
      const res = await fetch(`/api/sbs/search?q=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      dispatch({ type: 'SET_SEARCH_RESULTS', results: data.results || [] });
    } catch (err) {
      dispatch({ type: 'SET_ERROR', error: 'Search failed: ' + err.message });
      dispatch({ type: 'SET_SEARCH_RESULTS', results: [] });
    }
  }, [searchQuery, dispatch]);

  const handleSelectPathway = useCallback(async (pathway) => {
    dispatch({ type: 'SELECT_PATHWAY', pathway });
    setLoadingPathway(true);
    try {
      const res = await fetch(`/api/sbs/pathway?id=${encodeURIComponent(pathway.id)}&source=${pathway.source}`);
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      dispatch({ type: 'SET_SBML', sbml: data.sbml });
      const circuit = buildCircuitFromSBML(data.sbml);
      dispatch({ type: 'SET_CIRCUIT', circuit });
    } catch (err) {
      dispatch({ type: 'SET_ERROR', error: 'Failed to load pathway: ' + err.message });
    } finally {
      setLoadingPathway(false);
    }
  }, [dispatch]);

  const handleDemo = useCallback(() => {
    const circuit = buildDemoGlycolysis();
    dispatch({ type: 'SELECT_PATHWAY', pathway: { id: 'demo', name: 'Glycolysis (Demo)', source: 'demo' } });
    dispatch({ type: 'SET_CIRCUIT', circuit });
  }, [dispatch]);

  return (
    <div className="bg-light dark:bg-dark border border-dark/10 dark:border-light/10 rounded-xl p-6 shadow-sm">
      <h3 className="font-bold text-lg mb-4 text-dark dark:text-light">
        1. Define Circuit
      </h3>

      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={searchQuery}
          onChange={e => dispatch({ type: 'SET_SEARCH_QUERY', query: e.target.value })}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
          placeholder="Search pathways (e.g. glycolysis, TCA cycle)"
          className="flex-1 px-4 py-2 rounded-lg border border-dark/20 dark:border-light/20
                     bg-transparent text-dark dark:text-light
                     focus:outline-none focus:border-primary dark:focus:border-primaryDark
                     placeholder:text-dark/30 dark:placeholder:text-light/30"
        />
        <button
          onClick={handleSearch}
          disabled={searchLoading}
          className="px-4 py-2 rounded-lg bg-primary dark:bg-primaryDark text-light
                     hover:opacity-90 transition-opacity disabled:opacity-50 font-medium"
        >
          {searchLoading ? 'Searching...' : 'Search'}
        </button>
      </div>

      <button
        onClick={handleDemo}
        className="text-sm text-primary dark:text-primaryDark hover:underline mb-4 block"
      >
        Or load demo glycolysis circuit
      </button>

      {searchResults.length > 0 && !circuit && (
        <div className="max-h-72 overflow-y-auto space-y-2 mb-4">
          {searchResults.map((r, i) => (
            <motion.button
              key={`${r.source}-${r.id}-${i}`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              onClick={() => handleSelectPathway(r)}
              disabled={loadingPathway}
              className={`w-full text-left p-3 rounded-lg border transition-colors
                ${selectedPathway?.id === r.id
                  ? 'border-primary dark:border-primaryDark bg-primary/5 dark:bg-primaryDark/5'
                  : 'border-dark/10 dark:border-light/10 hover:border-primary dark:hover:border-primaryDark'}
                disabled:opacity-50`}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-dark dark:text-light text-sm">
                  {r.name}
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-dark/5 dark:bg-light/5
                                 text-dark/60 dark:text-light/60 uppercase">
                  {r.source}
                </span>
              </div>
              {r.species && (
                <span className="text-xs text-dark/50 dark:text-light/50">{r.species}</span>
              )}
            </motion.button>
          ))}
        </div>
      )}

      {loadingPathway && (
        <div className="flex items-center gap-2 text-sm text-dark/60 dark:text-light/60">
          <div className="w-4 h-4 border-2 border-primary dark:border-primaryDark border-t-transparent rounded-full animate-spin" />
          Fetching SBML and building circuit...
        </div>
      )}

      {circuit && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4 p-3 rounded-lg bg-primary/5 dark:bg-primaryDark/5 border border-primary/20 dark:border-primaryDark/20"
        >
          <p className="text-sm font-medium text-dark dark:text-light">
            Circuit loaded: {circuit.numNodes} nodes, {circuit.numEdges} edges
          </p>
          <p className="text-xs text-dark/60 dark:text-light/60 mt-1">
            Model: {circuit.modelId}
          </p>
        </motion.div>
      )}
    </div>
  );
}
