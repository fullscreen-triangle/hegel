export default function handler(req, res) {
  const models = [
    {
      id: 'eukaryotic_cell',
      name: 'Eukaryotic Cell',
      description: 'Generic animal cell with cytoplasm, nucleus, mitochondria, ER, and membrane',
      compartments: ['cytoplasm', 'nucleus', 'mitochondria', 'endoplasmic_reticulum', 'cell_membrane'],
      thumbnail: '/models/sbs/eukaryotic_cell_thumb.png',
      url: '/models/sbs/eukaryotic_cell.glb',
    },
    {
      id: 'neuron',
      name: 'Neuron',
      description: 'Neural cell with soma, axon, dendrites, and synaptic terminals',
      compartments: ['soma', 'axon', 'dendrite', 'synapse', 'cytoplasm'],
      thumbnail: '/models/sbs/neuron_thumb.png',
      url: '/models/sbs/neuron.glb',
    },
    {
      id: 'hepatocyte',
      name: 'Hepatocyte',
      description: 'Liver cell with extensive ER and mitochondrial networks',
      compartments: ['cytoplasm', 'nucleus', 'mitochondria', 'endoplasmic_reticulum', 'peroxisome'],
      thumbnail: '/models/sbs/hepatocyte_thumb.png',
      url: '/models/sbs/hepatocyte.glb',
    },
  ];

  res.status(200).json({ models });
}
