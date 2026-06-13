// WC Yayın Merkezi — PWA service worker
// Kabuk (shell) cache-first; status.json network-first (canlı veri taze kalsın, offline'da cache).
const CACHE = "wc-dash-v1";
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
  // canlı veri: önce ağ, başarısızsa cache
  if (url.pathname.endsWith("status.json")) {
    e.respondWith(
      fetch(e.request)
        .then((r) => { const c = r.clone(); caches.open(CACHE).then((ca) => ca.put(e.request, c)); return r; })
        .catch(() => caches.match(e.request))
    );
    return;
  }
  // kabuk: önce cache, yoksa ağ
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});
