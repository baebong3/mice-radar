// 정적 파일만 캐시한다. 화면(HTML)은 로그인 상태가 담겨 있어 캐시하지 않고, 끊겼을 때만 안내를 보여준다.
const CACHE = "radar-static-v2";
const ASSETS = ["/static/app.css", "/static/app.js", "/static/icon.svg"];
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  if (url.pathname.startsWith("/static/")) {
    e.respondWith(fetch(e.request).then((r) => {
      const copy = r.clone();
      caches.open(CACHE).then((c) => c.put(e.request, copy));
      return r;
    }).catch(() => caches.match(e.request)));
  } else if (e.request.mode === "navigate") {
    e.respondWith(fetch(e.request).catch(() => new Response(
      "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>" +
      "<body style='font-family:sans-serif;padding:40px 20px;text-align:center'>" +
      "<h1 style='font-size:20px'>인터넷 연결을 확인해 주십시오</h1><p>연결되면 다시 열어 주십시오.</p>",
      { headers: { "Content-Type": "text/html; charset=utf-8" } })));
  }
});
