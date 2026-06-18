# ETABS MCP Server

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![ETABS](https://img.shields.io/badge/ETABS-21%2B-orange)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

> **Connect Claude AI directly to your CSI ETABS structural model — query, analyze, and design with natural language.**

**etabs-mcp** is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that gives Claude direct access to your live CSI ETABS model through the ETABS COM API. Describe what you need in plain English — Claude finds the right API methods, writes the code, runs it against your open model, and returns the results. No scripting required.

---

## What Can You Do With It?

| Category | Example prompt |
|----------|---------------|
| Seismic check | *"Check modal mass participation — do we meet the 90% requirement?"* |
| Story drifts | *"Extract all story drifts for seismic combos and flag anything over h/400"* |
| Base shear | *"What is the base shear for EQX and EQY?"* |
| Results | *"Run analysis then extract pier forces for all piers at every story"* |
| Design | *"Run concrete design and show me the worst DCR ratios"* |
| RS scaling | *"Scale the response spectrum by 0.85 × static base shear and re-run"* |
| Audit | *"List all frame sections used in the model and their assignments"* |

---

## Features

### Natural Language to ETABS
Claude translates your request into ETABS COM API calls automatically — no scripting, no manual method lookup.

- **21 built-in skill documents** — step-by-step guidance for every area of the ETABS API (geometry, loads, analysis, results, design, troubleshooting)
- **BM25 API search** over **2,458 ETABS methods** — Claude finds the exact method name, parameter order, and return format before writing any code
- **Structural vocabulary expansion** — abbreviations like `GetDispl`, `BaseReact`, `ModalFreq` are matched by full English queries

### Full ETABS API Coverage

| Area | What's covered |
|------|---------------|
| Geometry | Joints, frames, areas, stories, groups, restraints |
| Materials & Sections | Steel, concrete, rebar; frame and area sections |
| Loads | Patterns, static/modal/response spectrum cases, combinations, joint/frame/area loads |
| Analysis | Linear static, P-delta, modal (Ritz/Eigen), nonlinear staged construction |
| Results | Joint displacements, base reactions, frame forces, story drifts, modal periods, mass participation, pier/spandrel forces |
| Design | Steel (AISC 360, EC3, AS4100+), concrete (ACI 318, EC2, IS 456+), composite, shear wall |
| Database Tables | Bulk read of all **165 ETABS database tables** via `GetTableForDisplayArray` |

### Built-in Workflow Skills

| Skill | What it does |
|-------|-------------|
| `workflow-seismic-check` | Full dynamic seismic check — modal periods, mass participation, base shear, story drifts |
| `workflow-modal-report` | Modal analysis report with Ritz/Eigen mass participation table |
| `workflow-story-drift` | Story drift extraction and code compliance check |
| `workflow-base-shear` | Base shear summary across all seismic load cases |
| `workflow-frame-forces` | Frame force extraction by group or story |
| `workflow-gravity-report` | Gravity load reaction summary |
| `workflow-design-concrete` | Concrete frame design run and DCR summary |
| `workflow-seismic-params` | Seismic parameters extraction and verification |
| `workflow-rs-scaling` | Response spectrum scaling (85% rule) |
| `workflow-model-audit` | Full model inventory — geometry counts, sections, materials, cases |
| `workflow-modifiers` | Frame and area stiffness modifier review and assignment |
| `etabs-database-tables` | Complete guide to all 165 database tables with field schemas |
| `etabs-errors` | Troubleshooting guide — ret codes, locked model, COM issues |

### Safe Execution Sandbox
- Code runs in a **restricted Python sandbox** — no arbitrary imports, no filesystem writes, no shell access
- Only `model` (SapModel), `json`, and `math` are available inside executed code
- All processing is local — no data leaves your machine

### Lightweight & Fast
- **40.8 MB** single-file `.mcpb` extension — no Python or runtime installation required
- Starts in under 1 second — BM25 keyword search, no PyTorch or ML models
- **Zero install** — drag `.mcpb` onto Claude Desktop and you're ready

### Developer-Friendly
- Add custom skills by dropping `.md` files next to the exe — no rebuild needed
- `build.ps1` one-command build: PyInstaller → stage → mcpb pack → optional hot-swap
- Two API index builders: CHM HTML parser + direct type library extractor (`ETABSv1.tlb`)

---

## Requirements

| Requirement | Version |
|-------------|---------|
| OS | Windows 10/11 (64-bit) |
| CSI ETABS | 21.0 or later, running with a model open |
| Claude Desktop | Latest |

---

## Installation

### Option A — Claude Desktop extension (recommended, no Python needed)

1. Download **`etabs-mcp.mcpb`** from [Releases](../../releases)
2. Open **Claude Desktop** → **Settings** → **Extensions**
3. Drag `etabs-mcp.mcpb` onto the Extensions window
4. Open ETABS and load a model
5. Start a new Claude conversation — Claude now has access to your model

### Option B — Run from source (Python 3.11+)

```powershell
# Clone and install
git clone https://github.com/your-org/etabs-mcp.git
cd etabs-mcp
pip install .

# Start the server (stdio, for Claude Desktop)
etabs-mcp

# Or HTTP mode with bearer token
etabs-mcp --transport http --port 18121 --token <your-token>
```

Add to `claude_desktop_config.json` (stdio mode):

```json
{
  "mcpServers": {
    "etabs-mcp": {
      "command": "etabs-mcp",
      "args": []
    }
  }
}
```

### Restricting file access

Use `--allowed-dirs` to limit which directories the server can read/write for file I/O:

```powershell
etabs-mcp --allowed-dirs "C:\Projects\MyBuilding" "C:\Exports"
```

---

## Tools

| Tool | Description |
|------|-------------|
| `discover_api` | List all available skills — **call this first** |
| `read_skills` | Load one or more skill documents by name |
| `list_instances` | Show running ETABS instances (alias, PID, file, version) |
| `get_status` | Check connection, ETABS version, lock state, server version |
| `execute_code` | Run Python in a sandbox against the live ETABS model |
| `search_docs` | BM25 search over 2,458 ETABS API methods |

---

## Example Session

```
User:  Run a seismic check on my model

Claude: [calls discover_api]
        [calls read_skills(["workflow-seismic-check"])]
        [calls get_status → connected, model locked]
        [calls execute_code → extracts modal periods, mass participation, base shear, story drifts]

        Here is the seismic check summary:
        • Modal periods: T1=1.24s, T2=1.18s, T3=0.41s
        • Mass participation: UX=94.2% ✅, UY=91.8% ✅ (>90% achieved at mode 12)
        • Base shear: EQX=1842 kN, EQY=1756 kN
        • Max story drift: 0.0041 at Story 5 (EQX) — exceeds h/400 limit ⚠️
```

---

## Building from Source

```powershell
# Install dependencies
pip install pyinstaller rank_bm25 numpy fastmcp uvicorn comtypes pywin32 beautifulsoup4

# Build exe + mcpb
.\build.ps1

# Rebuild API index from type library (when upgrading ETABS version)
py build_api_index_typelib.py --merge

# Then rebuild
.\build.ps1 -SkipPyInstaller
```

### API Index Sources

| Script | Source | Methods |
|--------|--------|---------|
| `build_api_index.py` | ETABS CHM help file (HTML parse) | 1,464 |
| `build_api_index_typelib.py` | `ETABSv1.tlb` type library (COM) | 2,458 |
| **Merged (default)** | CHM quality + typelib completeness | **2,458** |

### Source Layout

```
src/etabs_mcp/
  main.py                    ← entry point
  server.py                  ← MCP tools, BM25 search, lifespan
  version.py                 ← SERVER_VERSION (single source of truth)
  connection.py              ← COM connection, InstanceRegistry
  skills.py                  ← SkillsManager (discovery, sidecar support)
  sandbox/executor.py        ← restricted Python sandbox
  file_io/                   ← CSV/XLSX input-output helpers
  etabs_skills/              ← 21 built-in skill .md files
  etabs_api_index.json       ← pre-built API index (2,458 methods)
mcpb/
  etabs-mcp.spec             ← PyInstaller spec
  manifest.json              ← mcpb manifest (version auto-synced from version.py)
build.ps1                    ← one-command build script
build_api_index.py           ← CHM → JSON index builder
build_api_index_typelib.py   ← ETABSv1.tlb → JSON index builder
```

---

## Known Limitations

| Issue | Workaround |
|-------|-----------|
| `SetTableForEditingArray` — comtypes cannot pass Python lists as ByRef SAFEARRAY | Use object model methods (e.g. `model.FrameObj.SetSection()`) |
| Results after EDB open — model locked but COM results not in memory | Unlock → set run flags → `RunAnalysis()` |
| Ritz modal `StepNum` returns 0 | Use row index `i+1` as mode number |
| Large model analysis via MCP | Run analysis from ETABS UI (F5) — COM can time out |
| `SetModelIsLocked(False)` permanently deletes results | Never unlock between `RunAnalysis()` and result read |

---

## Changelog

### v1.0.0 — 2026-06-18

**Initial release.**

#### Features
- `execute_code` — run Python against live ETABS model via sandboxed COM bridge
- `search_docs` — BM25 full-text search over 2,458 ETABS API methods with structural vocabulary expansion (camelCase splitting, abbreviation → full-word mapping)
- `discover_api` / `read_skills` — skill-based guidance system; 21 built-in skill documents covering geometry, loads, analysis, results, design, and troubleshooting
- `list_instances` / `get_status` — multi-instance support with per-instance alias, version check, and lock state
- File I/O — `input_data_path` / `output_data_path` for `.csv` and `.xlsx` (single-sheet and multi-sheet)
- HTTP transport — bearer token auth, `SecFetchMiddleware`, `TrustedHostMiddleware` (localhost only)
- Sandboxed execution — blocks `import`, `dir()`, `getattr()`, dunder access; only `model`, `json`, `math` available
- Version guard — warns when connected ETABS version is below 21.0.0
- Sidecar skills — drop `.md` files next to the exe to extend Claude's guidance without rebuilding
- Single-file `.mcpb` extension — 40.8 MB, zero runtime dependencies, drag-and-drop install in Claude Desktop

---

## License

MIT — free to use, modify, and distribute.
