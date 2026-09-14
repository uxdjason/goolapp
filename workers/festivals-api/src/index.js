const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Content-Type': 'application/json; charset=utf-8',
};

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    const url = new URL(request.url);

    // GET /festivals
    if (url.pathname === '/festivals') {
      const region = url.searchParams.get('region') || '';
      const q = url.searchParams.get('q') || '';
      const from = url.searchParams.get('from') || new Date().toISOString().slice(0, 10);

      let sql = `SELECT * FROM festivals WHERE end_date >= ?`;
      const params = [from];

      if (region) {
        sql += ` AND region = ?`;
        params.push(region);
      }
      if (q) {
        sql += ` AND (name LIKE ? OR city LIKE ? OR venue LIKE ?)`;
        const like = `%${q}%`;
        params.push(like, like, like);
      }

      sql += ` ORDER BY start_date ASC LIMIT 300`;

      try {
        const stmt = env.goolapp_festivals.prepare(sql);
        const { results } = await stmt.bind(...params).all();
        return new Response(JSON.stringify(results), { headers: CORS_HEADERS });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), {
          status: 500, headers: CORS_HEADERS,
        });
      }
    }

    // GET /regions
    if (url.pathname === '/regions') {
      try {
        const { results } = await env.goolapp_festivals
          .prepare(`SELECT DISTINCT region FROM festivals ORDER BY region`)
          .all();
        return new Response(JSON.stringify(results.map(r => r.region)), { headers: CORS_HEADERS });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), {
          status: 500, headers: CORS_HEADERS,
        });
      }
    }

    return new Response(JSON.stringify({ error: 'Not found' }), {
      status: 404, headers: CORS_HEADERS,
    });
  },
};
