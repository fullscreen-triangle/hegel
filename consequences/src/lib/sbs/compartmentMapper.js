const GO_TERM_MAP = {
  'cytoplasm': { go: 'GO:0005737', meshNames: ['cytoplasm', 'cytosol', 'cell_body', 'soma'] },
  'cytosol': { go: 'GO:0005829', meshNames: ['cytoplasm', 'cytosol'] },
  'nucleus': { go: 'GO:0005634', meshNames: ['nucleus', 'nuclear'] },
  'mitochondria': { go: 'GO:0005739', meshNames: ['mitochondria', 'mito', 'mitochondrion'] },
  'mitochondrial_matrix': { go: 'GO:0005759', meshNames: ['mito_matrix', 'mitochondria'] },
  'endoplasmic_reticulum': { go: 'GO:0005783', meshNames: ['er', 'endoplasmic', 'reticulum'] },
  'golgi': { go: 'GO:0005794', meshNames: ['golgi', 'golgi_apparatus'] },
  'cell_membrane': { go: 'GO:0005886', meshNames: ['membrane', 'cell_membrane', 'plasma_membrane'] },
  'extracellular': { go: 'GO:0005576', meshNames: ['extracellular', 'outside'] },
  'lysosome': { go: 'GO:0005764', meshNames: ['lysosome'] },
  'peroxisome': { go: 'GO:0005777', meshNames: ['peroxisome'] },
  'axon': { go: 'GO:0030424', meshNames: ['axon'] },
  'dendrite': { go: 'GO:0030425', meshNames: ['dendrite'] },
  'synapse': { go: 'GO:0045202', meshNames: ['synapse', 'synaptic'] },
  'default': { go: null, meshNames: ['cytoplasm', 'cytosol', 'cell_body'] },
};

export function mapCompartmentToMesh(compartmentId) {
  const key = compartmentId.toLowerCase().replace(/\s+/g, '_');

  if (GO_TERM_MAP[key]) return GO_TERM_MAP[key];

  for (const [mapKey, value] of Object.entries(GO_TERM_MAP)) {
    if (key.includes(mapKey) || mapKey.includes(key)) return value;
  }

  return GO_TERM_MAP['default'];
}

export function findMeshForCompartment(sceneChildren, compartmentId) {
  const mapping = mapCompartmentToMesh(compartmentId);
  const candidates = mapping.meshNames;

  for (const name of candidates) {
    const found = findMeshByName(sceneChildren, name);
    if (found) return found;
  }

  return null;
}

function findMeshByName(children, name) {
  const lower = name.toLowerCase();
  for (const child of children) {
    if (child.name && child.name.toLowerCase().includes(lower)) return child;
    if (child.children && child.children.length > 0) {
      const found = findMeshByName(child.children, name);
      if (found) return found;
    }
  }
  return null;
}

export function computeCompartmentCentroids(scene) {
  const centroids = {};

  scene.traverse(child => {
    if (!child.isMesh) return;
    const name = child.name.toLowerCase();
    if (!name) return;

    child.geometry.computeBoundingBox();
    const bb = child.geometry.boundingBox;
    const center = bb.getCenter(child.position.clone());
    child.localToWorld(center);

    centroids[child.name] = {
      x: center.x,
      y: center.y,
      z: center.z,
      mesh: child,
    };
  });

  return centroids;
}

export function projectNodesToCompartments(nodes, compartmentCentroids) {
  const jitter = 0.3;
  return nodes.map((node, i) => {
    const mapping = mapCompartmentToMesh(node.compartment);
    let position = { x: 0, y: 0, z: 0 };

    for (const meshName of mapping.meshNames) {
      for (const [key, centroid] of Object.entries(compartmentCentroids)) {
        if (key.toLowerCase().includes(meshName.toLowerCase())) {
          const angle = (i / nodes.length) * Math.PI * 2;
          const radius = jitter * (0.5 + Math.random() * 0.5);
          position = {
            x: centroid.x + Math.cos(angle) * radius,
            y: centroid.y + (Math.random() - 0.5) * jitter,
            z: centroid.z + Math.sin(angle) * radius,
          };
          return { ...node, position };
        }
      }
    }

    const angle = (i / nodes.length) * Math.PI * 2;
    position = {
      x: Math.cos(angle) * 1.5,
      y: (Math.random() - 0.5) * 0.5,
      z: Math.sin(angle) * 1.5,
    };
    return { ...node, position };
  });
}
