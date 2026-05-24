export default async function handler(req, res) {
  const { ids } = req.query;
  if (!ids) return res.status(400).json({ error: 'Missing compound ids' });

  const idList = ids.split(',').map(s => s.trim());
  const compounds = [];

  const fetchers = idList.map(async (id) => {
    if (id.startsWith('HMDB')) {
      try {
        const r = await fetch(`https://hmdb.ca/metabolites/${id}.json`);
        if (r.ok) {
          const data = await r.json();
          compounds.push({
            id,
            name: data.name || id,
            deltaG: data.standard_gibbs_free_energy || null,
            concentration: data.normal_concentrations?.[0]?.concentration_value
              ? parseFloat(data.normal_concentrations[0].concentration_value)
              : null,
            source: 'hmdb',
          });
        }
      } catch {}
    } else if (id.startsWith('C')) {
      try {
        const r = await fetch(`https://rest.kegg.jp/get/${id}`);
        if (r.ok) {
          const text = await r.text();
          const nameLine = text.split('\n').find(l => l.startsWith('NAME'));
          compounds.push({
            id,
            name: nameLine ? nameLine.replace('NAME', '').trim().replace(/;$/, '') : id,
            deltaG: null,
            concentration: null,
            source: 'kegg',
          });
        }
      } catch {}
    }
  });

  await Promise.all(fetchers);
  res.status(200).json({ compounds });
}
