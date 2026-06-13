# World Cup 2026 — Canlı Yayın Merkezi

GitHub Pages canlı dashboard. `tools/build_status.py` her ~15 dk GitHub Actions ile iki kanalın public izlenme/abone verisini çekip `docs/status.json` üretir, Pages deploy edilir.

- Panel: `docs/index.html`
- Yeni video → `videos.json`a ID ekle
- Sıradaki maç → `queue.json`
