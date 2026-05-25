import React, { useCallback } from 'react';
import { motion } from 'framer-motion';
import { useSBS, useSBSDispatch } from './SBSContext';

const CELL_MODELS = [
  {
    id: 'eukaryotic_cell',
    name: 'Eukaryotic Cell',
    description: 'Full cell with membrane, nucleus, mitochondria, ER, Golgi, and vesicles',
    compartments: ['cytoplasm', 'nucleus', 'mitochondria', 'endoplasmic reticulum', 'golgi', 'membrane'],
    icon: '\u{1F9EC}',
  },
  {
    id: 'minimal',
    name: 'Minimal Cell',
    description: 'Simplified cell with membrane and nucleus only — cleaner view for small circuits',
    compartments: ['cytoplasm', 'nucleus', 'membrane'],
    icon: '\u{1F52C}',
  },
];

export default function CellModelPicker() {
  const { cellModel, circuit } = useSBS();
  const dispatch = useSBSDispatch();

  const handleSelect = useCallback((model) => {
    dispatch({ type: 'SET_CELL_MODEL', model });
  }, [dispatch]);

  const handleContinue = useCallback(() => {
    if (!cellModel) {
      dispatch({ type: 'SET_CELL_MODEL', model: CELL_MODELS[0] });
    }
    dispatch({ type: 'SET_STEP', step: 'observe' });
  }, [cellModel, dispatch]);

  if (!circuit) return null;

  return (
    <div className="bg-light dark:bg-dark border border-dark/10 dark:border-light/10 rounded-xl p-6 shadow-sm">
      <h3 className="font-bold text-lg mb-4 text-dark dark:text-light">
        2. Cell Geometry
      </h3>
      <p className="text-sm text-dark/60 dark:text-light/60 mb-4">
        Select a 3D cell model. Circuit nodes will be projected onto organelle compartments.
      </p>

      <div className="space-y-3">
        {CELL_MODELS.map((model, i) => (
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
            <div className="flex items-center gap-2">
              <span className="text-xl">{model.icon}</span>
              <div>
                <div className="font-medium text-dark dark:text-light text-sm">{model.name}</div>
                <div className="text-xs text-dark/50 dark:text-light/50 mt-0.5">{model.description}</div>
              </div>
            </div>
            <div className="flex flex-wrap gap-1 mt-2 ml-8">
              {model.compartments.map(c => (
                <span key={c} className="text-xs px-2 py-0.5 rounded-full bg-dark/5 dark:bg-light/5
                                         text-dark/60 dark:text-light/60">
                  {c}
                </span>
              ))}
            </div>
          </motion.button>
        ))}

        <button
          onClick={handleContinue}
          className="w-full px-4 py-2.5 rounded-lg bg-primary dark:bg-primaryDark text-light
                     hover:opacity-90 transition-opacity font-medium text-sm mt-4"
        >
          Continue to Observe
        </button>
      </div>
    </div>
  );
}
