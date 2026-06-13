// WC Yayın Merkezi — PWA service worker
// HTML + status.json: network-first (online'da hep taze, offline'da cache).
// Statik varlıklar (ikon vb): cache-first. Cache sürümü değişince eski içerik temizlenir.
const CACHE = "wc-dash-v2";
const SHELL = [
  "./", "./index.html", "./manifest.webmanifest",
  "./icon-192.png", "./icon-512.png", "./apple-touch-icon.png",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  const isHTML = e.request.mode === "navigate" || url.pathname.endsWith("/") || url.pathname.endsWith(".html");
  const isLive = url.pathname.endsWith("status.json");
  if (isHTML || isLive) {
    // önce ağ → taze içerik; başarısızsa cache (offline)
    e.respondWith(
      fetch(e.request)
        .then((r) => { const c = r.clone(); caches.open(CACHE).then((ca) => ca.put(e.request, c)); return r; })
        .catch(() => caches.match(e.request).then((r) => r || caches.match("./index.html")))
    );
    return;
  }
  // statik varlıklar: önce cache
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});
