/**
 * Submission endpoint for label-annotator.html (optional, deploy gated).
 *
 * POST /?k=<SUBMIT_KEY> with the tool's export JSON as the body.
 * Stores each submission in KV under `<annotator>_<iso-ts>` — nothing is
 * overwritten, interim and final submissions all persist.
 *
 * Deploy (after maintainer approval): `wrangler deploy` with a KV namespace bound as
 * LABELS and a secret SUBMIT_KEY (`wrangler secret put SUBMIT_KEY`). Then
 * rebuild the tool with SUBMIT_URL set in build_external_package.py.
 */
const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return new Response(null, { headers: CORS });
    if (request.method !== 'POST')
      return new Response('POST only', { status: 405, headers: CORS });

    const key = new URL(request.url).searchParams.get('k');
    if (!key || key !== env.SUBMIT_KEY)
      return new Response('bad key', { status: 403, headers: CORS });

    const text = await request.text();
    if (text.length > 2_000_000)
      return new Response('too large', { status: 413, headers: CORS });

    let doc;
    try { doc = JSON.parse(text); } catch { return new Response('not JSON', { status: 400, headers: CORS }); }
    if (!Array.isArray(doc.labels))
      return new Response('missing labels[]', { status: 400, headers: CORS });

    const ann = String(doc.annotator || 'unknown').replace(/[^A-Za-z0-9_-]/g, '').toUpperCase() || 'UNKNOWN';
    const done = doc.labels.filter(l => l.verdict).length;
    const id = `${ann}_${new Date().toISOString().replace(/[:.]/g, '-')}`;
    await env.LABELS.put(id, text);

    return new Response(JSON.stringify({ ok: true, id, received: done }), {
      headers: { 'Content-Type': 'application/json', ...CORS },
    });
  },
};
