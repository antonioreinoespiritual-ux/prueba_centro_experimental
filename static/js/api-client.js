(function(){
  const base = localStorage.getItem('ce_api_base') || window.location.origin || 'http://127.0.0.1:8000';

  async function request(path, init = {}) {
    const res = await fetch(base + path, init);
    const contentType = res.headers.get('content-type') || '';
    let payload;
    if (contentType.includes('application/json')) payload = await res.json();
    else payload = await res.text();
    if (!res.ok) {
      const msg = typeof payload === 'string' ? payload : (payload?.detail || JSON.stringify(payload));
      throw new Error(msg || `HTTP ${res.status}`);
    }
    return payload;
  }

  window.CEApi = {
    base,
    request,
    get: (path) => request(path),
    post: (path, body) => request(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
    patch: (path, body) => request(path, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
    del: (path) => request(path, { method: 'DELETE' }),
  };
})();
