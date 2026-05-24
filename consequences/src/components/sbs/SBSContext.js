import React, { createContext, useContext, useReducer } from 'react';

const SBSContext = createContext(null);
const SBSDispatchContext = createContext(null);

const initialState = {
  step: 'search',
  searchQuery: '',
  searchResults: [],
  searchLoading: false,
  selectedPathway: null,
  sbmlData: null,
  circuit: null,
  cellModel: null,
  compartmentMap: null,
  shaderResult: null,
  healthyBaseline: null,
  perturbation: null,
  metrics: null,
  error: null,
};

function sbsReducer(state, action) {
  switch (action.type) {
    case 'SET_STEP':
      return { ...state, step: action.step };
    case 'SET_SEARCH_QUERY':
      return { ...state, searchQuery: action.query };
    case 'SET_SEARCH_LOADING':
      return { ...state, searchLoading: action.loading };
    case 'SET_SEARCH_RESULTS':
      return { ...state, searchResults: action.results, searchLoading: false };
    case 'SELECT_PATHWAY':
      return { ...state, selectedPathway: action.pathway };
    case 'SET_SBML':
      return { ...state, sbmlData: action.sbml };
    case 'SET_CIRCUIT':
      return { ...state, circuit: action.circuit, step: 'geometry' };
    case 'SET_CELL_MODEL':
      return { ...state, cellModel: action.model };
    case 'SET_COMPARTMENT_MAP':
      return { ...state, compartmentMap: action.map };
    case 'SET_SHADER_RESULT':
      return {
        ...state,
        shaderResult: action.result,
        healthyBaseline: state.healthyBaseline || action.result,
      };
    case 'SET_METRICS':
      return { ...state, metrics: action.metrics };
    case 'SET_PERTURBATION':
      return { ...state, perturbation: action.perturbation };
    case 'CLEAR_PERTURBATION':
      return { ...state, perturbation: null, shaderResult: state.healthyBaseline, metrics: null };
    case 'SET_ERROR':
      return { ...state, error: action.error };
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
}

export function SBSProvider({ children }) {
  const [state, dispatch] = useReducer(sbsReducer, initialState);
  return (
    <SBSContext.Provider value={state}>
      <SBSDispatchContext.Provider value={dispatch}>
        {children}
      </SBSDispatchContext.Provider>
    </SBSContext.Provider>
  );
}

export function useSBS() {
  return useContext(SBSContext);
}

export function useSBSDispatch() {
  return useContext(SBSDispatchContext);
}
