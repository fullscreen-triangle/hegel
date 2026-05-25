const RT = 2.478; // kJ/mol at 298K

export function parseSBML(sbmlXml) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(sbmlXml, 'application/xml');

  const parseError = doc.querySelector('parsererror');
  if (parseError) {
    throw new Error('Invalid SBML XML: ' + parseError.textContent.slice(0, 200));
  }

  const model = doc.querySelector('model');
  if (!model) throw new Error('No <model> element found in SBML');

  const species = parseSpecies(doc);
  const compartments = parseCompartments(doc);
  const reactions = parseReactions(doc);

  return { species, compartments, reactions, modelId: model.getAttribute('id') || 'unknown' };
}

function parseCompartments(doc) {
  const comps = {};
  const elements = doc.querySelectorAll('compartment');
  elements.forEach(el => {
    const id = el.getAttribute('id');
    comps[id] = {
      id,
      name: el.getAttribute('name') || id,
      size: parseFloat(el.getAttribute('size')) || 1.0,
      outside: el.getAttribute('outside') || null,
    };
  });
  return comps;
}

function parseSpecies(doc) {
  const speciesList = [];
  const elements = doc.querySelectorAll('species');
  elements.forEach((el, idx) => {
    const id = el.getAttribute('id');
    const initialConc = parseFloat(el.getAttribute('initialConcentration'))
      || parseFloat(el.getAttribute('initialAmount'))
      || 0.1;
    speciesList.push({
      id,
      name: el.getAttribute('name') || id,
      compartment: el.getAttribute('compartment') || 'default',
      initialConcentration: initialConc,
      boundaryCondition: el.getAttribute('boundaryCondition') === 'true',
      index: idx,
    });
  });
  return speciesList;
}

function parseReactions(doc) {
  const reactionsList = [];
  const elements = doc.querySelectorAll('reaction');
  elements.forEach((el, idx) => {
    const id = el.getAttribute('id');
    const reversible = el.getAttribute('reversible') !== 'false';

    const reactants = [];
    el.querySelectorAll('listOfReactants > speciesReference').forEach(sr => {
      reactants.push({
        species: sr.getAttribute('species'),
        stoichiometry: parseFloat(sr.getAttribute('stoichiometry')) || 1,
      });
    });

    const products = [];
    el.querySelectorAll('listOfProducts > speciesReference').forEach(sr => {
      products.push({
        species: sr.getAttribute('species'),
        stoichiometry: parseFloat(sr.getAttribute('stoichiometry')) || 1,
      });
    });

    const params = {};
    el.querySelectorAll('kineticLaw localParameter, kineticLaw parameter').forEach(p => {
      params[p.getAttribute('id')] = parseFloat(p.getAttribute('value')) || 0;
    });

    reactionsList.push({
      id,
      name: el.getAttribute('name') || id,
      reversible,
      reactants,
      products,
      kineticParams: params,
      index: idx,
    });
  });
  return reactionsList;
}

export function extractDefaultRate(reaction) {
  const params = reaction.kineticParams;
  if (params.Vmax) return params.Vmax;
  if (params.kcat) return params.kcat;
  if (params.k1) return params.k1;
  if (params.k) return params.k;
  const values = Object.values(params).filter(v => v > 0);
  if (values.length > 0) return Math.max(...values);
  return 10.0;
}
