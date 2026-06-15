// Název cache - při jakékoliv změně obsahu (např. úpravě textu písně) 
// bys měl číslo verze (v1) zvýšit, aby se uživatelům stáhla nová verze.
const CACHE_NAME = 'zpevnik-cache-v24';

// Zde definujeme, co se má stáhnout pro offline režim
const urlsToCache = [
  "/",
  "/2019/batalion/index.html",
  "/2019/bedna-od-whisky/index.html",
  "/2019/drnova-chajda/index.html",
  "/2019/hospoda-u-tri-bernardynu/index.html",
  "/2019/prodavac/index.html",
  "/2019/tri-krize/index.html",
  "/2020/kometa/index.html",
  "/2020/magdalena/index.html",
  "/2020/pisnicka/index.html",
  "/2020/space-oddity/index.html",
  "/2020/v-lese/index.html",
  "/2021/dabel-a-syn/index.html",
  "/2021/lemon-tree/index.html",
  "/2021/mam-doma-kocku/index.html",
  "/2021/pisnicka/index.html",
  "/2021/v-7:25/index.html",
  "/2021/wellerman/index.html",
  "/2021/wind-of-change/index.html",
  "/2022/jelen/index.html",
  "/2022/morituri/index.html",
  "/2022/snadne-je-zit/index.html",
  "/2022/stanky/index.html",
  "/2022/ved-me-dal-cesto-ma/index.html",
  "/2022/zafukane/index.html",
  "/2023/burlaci/index.html",
  "/2023/co-z-tebe-bude/index.html",
  "/2023/dej-mi-vic-sve-lasky/index.html",
  "/2023/dokud-se-zpiva/index.html",
  "/2023/kruty-krtek-joy/index.html",
  "/2023/tenhle-vitr-jsem-mel-rad/index.html",
  "/2023/velrybarska-vyprava/index.html",
  "/2024/505/index.html",
  "/2024/frankie-dlouhan/index.html",
  "/2024/jez/index.html",
  "/2024/mala-dama/index.html",
  "/2024/mezi-horami/index.html",
  "/2024/plachty/index.html",
  "/2024/tancici-polarnik/index.html",
  "/2025/kdo-vi-jestli/index.html",
  "/2025/kdyz-me-brali-za-vojaka/index.html",
  "/2025/kocabka/index.html",
  "/2025/kral-a-klaun/index.html",
  "/2025/na-hotelu-v-olomouci/index.html",
  "/2025/sila-starejch-vin/index.html",
  "/2025/slecna-zavist/index.html",
  "/2026/andel/index.html",
  "/2026/divka-s-perlami-ve-vlasech/index.html",
  "/2026/jasna-zprava/index.html",
  "/2026/mam-jizvu-na-rtu/index.html",
  "/2026/pohoda/index.html",
  "/2026/trh-ve-scarborough/index.html",
  "/2026/vodacka-holka/index.html",
  "/icon-192.png",
  "/icon-512.png",
  "/index.html",
  "/manifest.json",
  "/sw.js"
];


// Instalace Service Workeru a stažení souborů do mezipaměti
self.addEventListener('install', event => {
  // Nová verze se aktivuje hned, nečeká na zavření všech záložek aplikace
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Otevírám cache a stahuji soubory...');
        return cache.addAll(urlsToCache);
      })
  );
});

// Aktivace a smazání případné staré mezipaměti (když změníš CACHE_NAME)
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cache => {
          if (cache !== CACHE_NAME) {
            console.log('Mažu starou cache:', cache);
            return caches.delete(cache);
          }
        })
      );
    // Nový SW převezme i už otevřené stránky
    }).then(() => self.clients.claim())
  );
});

// Zpracování požadavků (když uživatel klikne na odkaz)
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Pokud je soubor v cache, vrátíme ho. Pokud ne, stáhneme ho z internetu.
        return response || fetch(event.request);
      })
  );
});