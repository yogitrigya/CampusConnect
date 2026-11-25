window.CampusConnect = {
  csrf: () => document.querySelector('meta[name="csrf-token"]')?.content || '',
  async request(url, options = {}) {
    const headers = { 'Content-Type': 'application/json', 'X-CSRF-Token': this.csrf(), ...(options.headers || {}) };
    const response = await fetch(url, { credentials: 'same-origin', ...options, headers });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.error?.message || 'Request failed.');
    return result.data;
  },
  notice(message, kind = 'success') {
    const el = document.getElementById('notice'); if (!el) return;
    el.className = `alert alert-${kind}`; el.textContent = message;
  }
};
