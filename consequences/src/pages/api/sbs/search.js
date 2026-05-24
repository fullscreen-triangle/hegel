function stripHtml(str) {
  return (str || '').replace(/<[^>]*>/g, '');
}

export default async function handler(req, res) {
  const { q, db = 'reactome,kegg' } = req.query;
  if (!q) return res.status(400).json({ error: 'Missing query parameter q' });

  const sources = db.split(',').map(s => s.trim().toLowerCase());
  const results = [];

  const fetchers = [];

  if (sources.includes('reactome')) {
    fetchers.push(
      fetch(`https://reactome.org/ContentService/search/query?query=${encodeURIComponent(q)}&types=Pathway&cluster=true`)
        .then(r => r.ok ? r.json() : null)
        .then(data => {
          if (!data?.results) return;
          for (const group of data.results) {
            if (!group.entries) continue;
            for (const entry of group.entries.slice(0, 15)) {
              results.push({
                id: entry.stId || entry.dbId,
                name: stripHtml(entry.name),
                source: 'reactome',
                species: entry.species?.[0] || 'Homo sapiens',
                description: stripHtml(entry.summation?.[0] || ''),
              });
            }
          }
        })
        .catch(() => {})
    );
  }

  if (sources.includes('kegg')) {
    fetchers.push(
      fetch(`https://rest.kegg.jp/find/pathway/${encodeURIComponent(q)}`)
        .then(r => r.ok ? r.text() : '')
        .then(text => {
          if (!text) return;
          const lines = text.trim().split('\n');
          for (const line of lines.slice(0, 15)) {
            const [id, ...rest] = line.split('\t');
            const name = rest.join('\t');
            results.push({
              id: id.replace('path:', ''),
              name: name || id,
              source: 'kegg',
              species: id.startsWith('map') ? 'Reference' : 'Various',
              description: '',
            });
          }
        })
        .catch(() => {})
    );
  }

  await Promise.all(fetchers);
  res.status(200).json({ results, query: q });
}
