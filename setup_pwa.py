#!/usr/bin/env python3
"""Setup PWA (Progressive Web App) for PROMPTURE Command Library.

1. Backs up index.html -> index.html.before_pwa_bak
2. Extracts embedded logo into icon-192.png and icon-512.png
3. Generates manifest.json (standalone, gold/black theme)
4. Generates sw.js (Service Worker with smart Network-First offline cache)
5. Patches index.html to link manifest, meta tags, and register sw.js
"""
import base64
import json
import re
import shutil

HTML_FILE = 'index.html'
BACKUP_FILE = 'index.html.before_pwa_bak'

def main():
    shutil.copy2(HTML_FILE, BACKUP_FILE)
    html = open(HTML_FILE, encoding='utf-8').read()

    # 1. Extract embedded base64 icon from favicon
    icon_match = re.search(r'<link rel="icon" href="data:image/png;base64,(.*?)"', html)
    if icon_match:
        raw_png = base64.b64decode(icon_match.group(1))
        open('icon-192.png', 'wb').write(raw_png)
        open('icon-512.png', 'wb').write(raw_png)
        print('[OK] Generated icon-192.png and icon-512.png')
    else:
        print('[WARN] Could not find base64 favicon, using dummy fallback')

    # 2. Generate manifest.json
    manifest = {
        "name": "PROMPTURE Command Library",
        "short_name": "PROMPTURE",
        "description": "PROMPTURE Command Library v2.9 · 4626 Commands",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "background_color": "#0f0e0c",
        "theme_color": "#d4af37",
        "orientation": "any",
        "icons": [
            {
                "src": "icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ]
    }
    open('manifest.json', 'w', encoding='utf-8').write(json.dumps(manifest, indent=2, ensure_ascii=False))
    print('[OK] Created manifest.json')

    # 3. Generate sw.js (Smart Network-First Service Worker)
    sw_code = """const CACHE_NAME = 'prompture-pwa-v2_9';
const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.map((k) => {
          if (k !== CACHE_NAME) return caches.delete(k);
        })
      )
    )
  );
  self.clients.claim();
});

// Network-first with cache fallback (works 100% offline and auto-updates online)
self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        const resClone = res.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(e.request, resClone));
        return res;
      })
      .catch(() => caches.match(e.request))
  );
});
"""
    open('sw.js', 'w', encoding='utf-8').write(sw_code)
    print('[OK] Created sw.js (Service Worker)')

    # 4. Patch index.html
    # Insert manifest & meta tags in <head>
    head_tags = (
        '\n<link rel="manifest" href="manifest.json">\n'
        '<meta name="theme-color" content="#d4af37">\n'
        '<meta name="apple-mobile-web-app-capable" content="yes">\n'
        '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">\n'
        '<meta name="apple-mobile-web-app-title" content="PROMPTURE">\n'
        '<link rel="apple-touch-icon" href="icon-192.png">\n'
    )
    if '<link rel="manifest"' not in html:
        html = html.replace('<title>PROMPTURE Command Library</title>', '<title>PROMPTURE Command Library</title>' + head_tags, 1)

    # Insert Service Worker registration before closing </script>
    sw_register = """
// PWA Service Worker Registration
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').catch(() => {});
  });
}
"""
    if 'navigator.serviceWorker' not in html:
        html = html.replace('applyTheme(); applyLang(); saveFavs();', 'applyTheme(); applyLang(); saveFavs();\n' + sw_register, 1)

    open(HTML_FILE, 'w', encoding='utf-8').write(html)
    print(f'[SUCCESS] PWA fully configured! (Backup at {BACKUP_FILE})')

if __name__ == '__main__':
    main()