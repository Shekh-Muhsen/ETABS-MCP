# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the ETABS MCP server.

Produces a single-file executable:
- etabs-mcp.exe: console executable for stdio MCP transport.

Bundles the Python runtime, all dependencies, and bundled ETABS skills content.

Build:
    pip install pyinstaller
    pyinstaller mcpb/etabs-mcp.spec --noconfirm
    # Output: dist/etabs-mcp.exe

Then pack as .mcpb (requires @anthropic-ai/mcpb):
    .\build.ps1 -SkipPyInstaller
"""

import os
from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata

block_cipher = None

ROOT = Path(SPECPATH).parent

# Collect bundled ETABS skills files (.md)
skills_data = []
skills_dir = ROOT / "src" / "etabs_mcp" / "etabs_skills"
if skills_dir.exists():
    for f in skills_dir.rglob("*"):
        if f.is_file() and f.suffix in (".md", ".py"):
            rel_parent = f.parent.relative_to(ROOT / "src")
            skills_data.append((str(f), str(rel_parent).replace("\\", "/")))

# Bundle API index JSON
api_index = ROOT / "src" / "etabs_mcp" / "etabs_api_index.json"
if api_index.exists():
    skills_data.append((str(api_index), "etabs_mcp"))

# Include fastmcp distribution metadata (needed at runtime for version resolution)
package_metadata = copy_metadata("fastmcp")

a = Analysis(
    [str(ROOT / "src" / "etabs_mcp" / "main.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=skills_data + package_metadata,
    hiddenimports=[
        "etabs_mcp",
        "etabs_mcp.server",
        "etabs_mcp.connection",
        "etabs_mcp.sandbox",
        "etabs_mcp.sandbox.executor",
        "uvicorn",
        "fastmcp",
        "pythoncom",
        "win32com",
        "win32com.client",
        "comtypes",
        "comtypes.client",
        "rank_bm25",
        "numpy",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "torch",
        "torchvision",
        "torchaudio",
        "sentence_transformers",
        "transformers",
        "tokenizers",
        "huggingface_hub",
        "scipy",
        "sklearn",
        "tensorflow",
        "keras",
        "PIL",
        "matplotlib",
        "pandas",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

console_exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="etabs-mcp",
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
    icon=None,
)
