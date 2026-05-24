export default async function handler(req, res) {
  const { id, source = 'reactome' } = req.query;
  if (!id) return res.status(400).json({ error: 'Missing pathway id' });

  if (source === 'reactome') {
    const url = `https://reactome.org/ContentService/exporter/sbml/${encodeURIComponent(id)}.xml`;
    const response = await fetch(url);
    if (!response.ok) {
      return res.status(response.status).json({
        error: `Reactome SBML fetch failed: ${response.statusText}`,
      });
    }
    const sbml = await response.text();
    return res.status(200).json({ sbml, source, id });
  }

  if (source === 'kegg') {
    const url = `https://rest.kegg.jp/get/${encodeURIComponent(id)}/kgml`;
    const response = await fetch(url);
    if (!response.ok) {
      return res.status(response.status).json({
        error: `KEGG KGML fetch failed: ${response.statusText}`,
      });
    }
    const kgml = await response.text();
    return res.status(200).json({ sbml: kgml, source, id, format: 'kgml' });
  }

  return res.status(400).json({ error: `Unknown source: ${source}` });
}
