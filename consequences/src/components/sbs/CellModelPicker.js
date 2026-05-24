import React, { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useSBS, useSBSDispatch } from './SBSContext';

export default function CellModelPicker() {
  const { cellModel, circuit } = useSBS();
  const dispatch = useSBSDispatch();
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/sbs/models')
      .then(r => r.json())
      .then(data => setModels(data.models || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSelect = useCallback((model) => {
    dispatch({ type: 'SET_CELL_MODEL', model });
  }, [dispatch]);

  const handleSkip = useCallback(() => {
    dispatch({ type: 'SET_CELL_MODEL', model: { id: 'procedural', name: 'Procedural Layout', url: null } });
    dispatch({ type: 'SET_STEP', step: 'observe' });
  }, [dispatch]);

  const handleContinue = useCallback(() => {
    dispatch({ type: 'SET_STEP', step: 'observe' });
  }, [dispatch]);

  if (!circuit) return null;

  return (
    <div className="bg-light dark:bg-dark border border-dark/10 dark:border-light/10 rounded-xl p-6 shadow-sm">
      <h3 className="font-bold text-lg mb-4 text-dark dark:text-light">
        2. Select Cell Model
      </h3>
      <p className="text-sm text-dark/60 dark:text-light/60 mb-4">
        Choose a 3D cell model to project the circuit onto, or use procedural layout.
      </p>

      {loading ? (
        <div className="flex items-center gap-2 text-sm text-dark/60 dark:text-light/60">
          <div className="w-4 h-4 border-2 border-primary dark:border-primaryDark border-t-transparent rounded-full animate-spin" />
          Loading models...
        </div>
      ) : (
        <div className="space-y-3">
          {models.map((model, i) => (
            <motion.button
              key={model.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              onClick={() => handleSelect(model)}
              className={`w-full text-left p-4 rounded-lg border transition-colors
                ${cellModel?.id === model.id
                  ? 'border-primary dark:border-primaryDark bg-primary/5 dark:bg-primaryDark/5'
                  : 'border-dark/10 dark:border-light/10 hover:border-primary dark:hover:border-primaryDark'}`}
            >
              <div className="font-medium text-dark dark:text-light text-sm">{model.name}</div>
              <div className="text-xs text-dark/50 dark:text-light/50 mt-1">{model.description}</div>
              <div className="flex flex-wrap gap-1 mt-2">
                {model.compartments.map(c => (
                  <span key={c} className="text-xs px-2 py-0.5 rounded-full bg-dark/5 dark:bg-light/5
                                           text-dark/60 dark:text-light/60">
                    {c.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </motion.button>
          ))}

          <div className="flex gap-3 mt-4">
            <button
              onClick={handleSkip}
              className="flex-1 px-4 py-2 rounded-lg border border-dark/20 dark:border-light/20
                         text-dark/60 dark:text-light/60 hover:border-primary dark:hover:border-primaryDark
                         transition-colors text-sm"
            >
              Skip (Procedural Layout)
            </button>
            {cellModel && (
              <button
                onClick={handleContinue}
                className="flex-1 px-4 py-2 rounded-lg bg-primary dark:bg-primaryDark text-light
                           hover:opacity-90 transition-opacity font-medium text-sm"
              >
                Continue to Observe
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
