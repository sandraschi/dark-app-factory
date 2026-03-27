"""Generate PWA artifacts (manifest, service worker, icons) and inject into HTML."""

import json
import os

from src.utils.logger import logger


# Minimal SVG icon (gradient square, Dark App Factory style)
ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%%" style="stop-color:#00f3ff"/>
    <stop offset="100%%" style="stop-color:#bd00ff"/>
  </linearGradient></defs>
  <rect width="512" height="512" rx="64" fill="url(#g)"/>
  <text x="256" y="300" font-family="system-ui,sans-serif" font-size="180" font-weight="bold" fill="white" text-anchor="middle">A</text>
</svg>"""


def _write_manifest(base_dir: str, project_name: str) -> str:
    manifest = {
        "name": project_name,
        "short_name": project_name[:12],
        "description": f"{project_name} - Built with Dark App Factory",
        "start_url": "./",
        "display": "standalone",
        "background_color": "#09090b",
        "theme_color": "#09090b",
        "orientation": "portrait-primary",
        "icons": [
            {"src": "icons/icon-192.svg", "sizes": "192x192", "type": "image/svg+xml", "purpose": "any"},
            {"src": "icons/icon-512.svg", "sizes": "512x512", "type": "image/svg+xml", "purpose": "any maskable"},
        ],
    }
    path = os.path.join(base_dir, "manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return path


def _write_service_worker(base_dir: str) -> str:
    sw_content = """// Minimal service worker - cache first for offline
const CACHE = 'dark-app-v1';
self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(['./', './index.html'])));
  self.skipWaiting();
});
self.addEventListener('fetch', (e) => {
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});
"""
    path = os.path.join(base_dir, "sw.js")
    with open(path, "w", encoding="utf-8") as f:
        f.write(sw_content)
    return path


def _write_icons(base_dir: str) -> None:
    icons_dir = os.path.join(base_dir, "icons")
    os.makedirs(icons_dir, exist_ok=True)
    for size in (192, 512):
        svg = ICON_SVG.replace("512", str(size)).replace('width="512" height="512"', f'width="{size}" height="{size}"')
        path = os.path.join(icons_dir, f"icon-{size}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)


def _inject_pwa_meta(html: str) -> str:
    """Inject PWA meta/link tags and sw registration before </head>."""
    pwa_tags = """
  <meta name="theme-color" content="#09090b">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="App">
  <link rel="manifest" href="./manifest.json">
  <link rel="apple-touch-icon" href="./icons/icon-192.svg">
"""
    # Insert before </head>
    if "</head>" in html and "theme-color" not in html:
        html = html.replace("</head>", pwa_tags + "</head>")
    # Register service worker before </body>
    sw_script = """
  <script>
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('./sw.js').catch(() => {});
  }
  </script>
"""
    if "</body>" in html and "serviceWorker" not in html:
        html = html.replace("</body>", sw_script + "</body>")
    return html


def add_pwa_artifacts(output_dir: str, project_name: str = "Dark App") -> list[str]:
    """Add PWA artifacts to www/ and app root.

    Writes manifest.json, sw.js, icons/, and patches index.html with PWA meta + sw registration.
    Targets: output_dir/www/ (landing), output_dir/ (app root if index.html exists).

    Returns list of paths written.
    """
    written: list[str] = []

    for base in ["www", ""]:
        base_dir = os.path.join(output_dir, base) if base else output_dir
        if not os.path.isdir(base_dir) and base:
            continue
        index_path = os.path.join(base_dir, "index.html")
        if not os.path.isfile(index_path):
            continue

        try:
            _write_icons(base_dir)
            written.append(os.path.join(base_dir, "icons"))
            _write_manifest(base_dir, project_name)
            written.append(os.path.join(base_dir, "manifest.json"))
            _write_service_worker(base_dir)
            written.append(os.path.join(base_dir, "sw.js"))

            with open(index_path, "r", encoding="utf-8") as f:
                html = f.read()
            html = _inject_pwa_meta(html)
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(html)
            written.append(index_path)
        except OSError as e:
            logger.warning("PWA artifacts failed for %s: %s", base_dir, e)

    if written:
        logger.info("PWA artifacts added (manifest, sw, icons, meta injected)")
    return written
