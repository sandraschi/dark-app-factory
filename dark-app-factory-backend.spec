# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for dark-app-factory backend sidecar."""

from PyInstaller.utils.hooks import copy_metadata

pkg_name = "dark_app_factory_mcp"

datas = [("mcp-server/src/dark_app_factory_mcp", "dark_app_factory_mcp")]
for pkg in (
    "fastmcp",
    "fastapi",
    "uvicorn",
    "pydantic",
    "starlette",
    "httpx",
):
    datas += copy_metadata(pkg)

hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.httptools_impl",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "dark_app_factory_mcp.server",
    "dark_app_factory_mcp.api",
    "dark_app_factory_mcp.app",
    "dark_app_factory_mcp.main",
    "dark_app_factory_mcp.tools",
]

a = Analysis(
    ["run_server.py"],
    pathex=["mcp-server/src"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pandas", "scipy", "torch", "tensorflow"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="dark-app-factory-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)