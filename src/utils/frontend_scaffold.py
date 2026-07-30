"""Frontend scaffold — generates working React+Vite scaffold when missing from output."""

from __future__ import annotations

import json
import os
import shutil

_REACT = {"react": "^19.0.0", "react-dom": "^19.0.0", "react-router-dom": "^7.0.0", "lucide-react": "^0.400.0", "framer-motion": "^11.0.0"}
_DEV = {"@types/react": "^19.0.0", "@types/react-dom": "^19.0.0", "@vitejs/plugin-react": "^4.3.0",
        "autoprefixer": "^10.4.0", "postcss": "^8.4.0", "tailwindcss": "^3.4.0", "typescript": "^5.6.0", "vite": "^6.0.0"}


def _write_text(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _find_pages(output_dir: str) -> list[dict]:
    pages = []
    src_dir = os.path.join(output_dir, "src", "pages")
    if os.path.isdir(src_dir):
        for f in os.listdir(src_dir):
            if f.endswith(".tsx"):
                name = f.replace(".tsx", "")
                pages.append({"name": name, "file": f"src/pages/{f}", "route": "/" + name.lower().replace("page", "")})

    for f in os.listdir(output_dir):
        if f.startswith("pages_") and f.endswith(".tsx") and f not in os.listdir(os.path.join(output_dir, "src", "pages")):
            src = os.path.join(output_dir, f)
            name = f.replace(".tsx", "").replace("pages_", "")
            pascal = name.replace("_", " ").title().replace(" ", "")
            dest_name = pascal + ".tsx"
            dest = os.path.join(output_dir, "src", "pages", dest_name)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            content = open(src, encoding="utf-8", errors="replace").read()
            if "export default" not in content:
                content = content.rstrip() + f"\n\nexport default function {pascal}() {{\n  return <div className='p-4 text-zinc-400'>{pascal} page</div>;\n}}\n"
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(content)
            os.remove(src)
            pages.append({"name": pascal, "file": f"src/pages/{dest_name}", "route": "/" + name.lower().replace("_", "")})
    return pages


def _validate_pages(output_dir: str, pages: list[dict]) -> list[dict]:
    """Replace page files with likely compilation errors with stubs."""
    valid = []

    def _stub(name: str) -> str:
        return f"export default function {name}() {{\n  return <div className='p-8 text-center text-zinc-400'>{name} page</div>;\n}}\n"

    for p in pages:
        fpath = os.path.join(output_dir, p["file"])
        if not os.path.exists(fpath):
            valid.append(p)
            continue
        content = open(fpath, encoding="utf-8", errors="replace").read()
        # Check for common LLM generation errors
        broken = False
        if "export default" not in content:
            broken = True
        # Unclosed tags (more <div than </div)
        opens = content.count("<div") - content.count("// <div") - content.count("'<div")
        closes = content.count("</div")
        if opens > closes + 2:
            broken = True
        # Garbled imports
        if 'from "' in content and '";' not in content[:500]:
            broken = True
        if broken:
            _write_text(fpath, _stub(p["name"]))
        valid.append(p)
    return valid


def ensure_frontend_scaffold(output_dir: str, title: str = "App"):
    src_dir = os.path.join(output_dir, "src")
    os.makedirs(os.path.join(src_dir, "pages"), exist_ok=True)
    os.makedirs(os.path.join(src_dir, "components"), exist_ok=True)

    pages = _validate_pages(output_dir, _find_pages(output_dir))

    # package.json
    pkg_path = os.path.join(output_dir, "package.json")
    if not os.path.exists(pkg_path):
        pkg = {"name": title.lower().replace(" ", "-"), "private": True, "version": "0.1.0", "type": "module",
               "scripts": {"dev": "vite --port 5173 --host", "build": "tsc -b && vite build", "preview": "vite preview"},
               "dependencies": dict(_REACT), "devDependencies": dict(_DEV)}
        _write_text(pkg_path, json.dumps(pkg, indent=2) + "\n")

    # index.html
    html = '<!DOCTYPE html><html lang="en" class="dark"><head><meta charset="UTF-8"/>'
    html += '<meta name="viewport" content="width=device-width,initial-scale=1.0"/>'
    html += f"<title>{title}</title>"
    html += '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>'
    html += '</head><body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body></html>'
    _write_text(os.path.join(output_dir, "index.html"), html)

    # src/main.tsx
    _write_text(os.path.join(src_dir, "main.tsx"),
                'import React from "react";\nimport ReactDOM from "react-dom/client";\nimport App from "./App";\nimport "./index.css";\n'
                'ReactDOM.createRoot(document.getElementById("root")!).render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>\n);\n')

    # src/App.tsx with routes
    if pages:
        imports = "\n".join(f'import {p["name"]} from "./pages/{p["name"]}";' for p in pages)
        routes = "\n".join(f'          <Route path="{p["route"]}" element={{<{p["name"]} />}} />' for p in pages)
    else:
        imports = 'import { BrowserRouter, Routes, Route } from "react-router-dom";'
        routes = '          <Route path="/" element={<div className="p-8 text-center text-zinc-500">App ready</div>} />'

    app = f'import {{ BrowserRouter, Routes, Route }} from "react-router-dom";\n{imports}\n\nexport default function App() {{\n  return (\n    <BrowserRouter>\n      <div className="min-h-screen bg-zinc-950 text-zinc-100">\n        <Routes>\n{routes}\n        </Routes>\n      </div>\n    </BrowserRouter>\n  );\n}}\n'
    _write_text(os.path.join(src_dir, "App.tsx"), app)

    # src/index.css
    _write_text(os.path.join(src_dir, "index.css"),
                "@tailwind base;\n@tailwind components;\n@tailwind utilities;\nbody { color-scheme: dark; margin: 0; font-family: Inter, system-ui, sans-serif; background: #09090b; color: #e2e8f0; }\ninput, select, textarea { color-scheme: dark; }\n")

    # Config files
    _write_text(os.path.join(output_dir, "vite.config.ts"),
                'import { defineConfig } from "vite";\nimport react from "@vitejs/plugin-react";\n\nexport default defineConfig({\n  plugins: [react()],\n  server: { port: 5173, proxy: { "/api": { target: "http://127.0.0.1:8000", changeOrigin: true } } },\n});\n')

    _write_text(os.path.join(output_dir, "tailwind.config.js"),
                '/** @type {import("tailwindcss").Config} */\nexport default { content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"], theme: { extend: {} }, plugins: [] };\n')

    _write_text(os.path.join(output_dir, "postcss.config.js"), 'export default { plugins: { tailwindcss: {}, autoprefixer: {} } };\n')

    tsconfig = json.dumps({
        "compilerOptions": {
            "target": "ES2020", "useDefineForClassFields": True, "lib": ["ES2020", "DOM", "DOM.Iterable"],
            "module": "ESNext", "skipLibCheck": True, "moduleResolution": "bundler",
            "allowImportingTsExtensions": True, "isolatedModules": True, "moduleDetection": "force",
            "noEmit": True, "jsx": "react-jsx", "strict": True, "forceConsistentCasingInFileNames": True,
        },
        "include": ["src"],
    }, indent=2)
    _write_text(os.path.join(output_dir, "tsconfig.json"), tsconfig + "\n")
