{% load static %}
const CACHE_PREFIX = "swiftcart-";
const CACHE_NAME = "swiftcart-phase2-v6";
const OFFLINE_URL = "{% url 'offline' %}";
const APP_SHELL = [
    OFFLINE_URL,
    "{% static 'css/style.css' %}?v=20260731.6",
    "{% static 'css/catalogue-v2.css' %}?v=20260731.6",
    "{% static 'js/app.js' %}?v=20260731.6",
    "{% static 'images/pwa-icon.svg' %}?v=20260731.6",
    "{% static 'manifest.webmanifest' %}?v=20260731.6"
];

self.addEventListener("install", (event) => {
    event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)));
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(
                keys
                    .filter((key) => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME)
                    .map((key) => caches.delete(key))
            )
        )
    );
    self.clients.claim();
});

async function networkFirst(request, fallback) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        return (await caches.match(request)) || (fallback ? caches.match(fallback) : Response.error());
    }
}

async function cacheFirst(request) {
    const cached = await caches.match(request);
    if (cached) return cached;
    const response = await fetch(request);
    if (response.ok) {
        const cache = await caches.open(CACHE_NAME);
        cache.put(request, response.clone());
    }
    return response;
}

self.addEventListener("fetch", (event) => {
    if (event.request.method !== "GET") return;
    const url = new URL(event.request.url);
    if (url.origin !== self.location.origin) return;

    if (event.request.mode === "navigate") {
        event.respondWith(networkFirst(event.request, OFFLINE_URL));
        return;
    }

    const freshAsset =
        event.request.destination === "style" ||
        event.request.destination === "script" ||
        url.pathname.endsWith("manifest.webmanifest");
    event.respondWith(freshAsset ? networkFirst(event.request) : cacheFirst(event.request));
});
