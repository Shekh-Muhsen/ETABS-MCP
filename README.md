# ETABS MCP Server

> **Connect Claude AI directly to your CSI ETABS structural model — query, analyze, and design with natural language.**

An MCP (Model Context Protocol) server that bridges AI assistants to **CSI ETABS** via the ETABS COM API. Ask Claude to extract results, modify geometry, run analysis, check code compliance, and more — all without writing a single line of API code yourself.

---

## What Can You Do With It?

Ask Claude things like:

- *"Check the modal mass participation and tell me if we meet the 90% requirement"*
- *"Extract all story drifts for the seismic load combinations and flag any that exceed h/400"*
- *"Run the seismic check workflow and give me a summary report"*
- *"What is the base shear for EQX and EQY?"*
- *"List all frame sections used in the model and their assignments"*
- *"Run analysis, then extract pier forces for all piers at all stories"*
- *"Scale the response spectrum by 0.85 × static base shear and re-run"*

---

## Features

### AI-Native Workflow
- **Natural language to ETABS** — describe what you want, Claude handles the API calls
- **Built-in skills** — 21 pre-loaded guidance documents covering every part of the ETABS API so Claude always knows the right method, parameter order, and return format
- **API search** — BM25 keyword search over **2,458 ETABS API methods** so Claude can discover any method instantly (`search_docs` tool)

### Full ETABS API Coverage
- **Geometry** — joints, frames, areas, stories, groups, restraints
- **Materials & Sections** — define steel, concrete, rebar; frame and area sections
- **Loads** — load patterns, static/modal/response spectrum cases, combinations, joint/frame/area loads
- **Analysis** — run analysis, P-delta, modal (Ritz/Eigen), nonlinear staged construction
- **Results** — joint displacements, base reactions, frame forces, story drifts, modal periods, mass participation, pier/spandrel forces
- **Design** — steel (AISC 360, Eurocode 3, AS4100, and more), concrete (ACI 318, Eurocode 2, IS 456, and more), composite, shear wall
- **Database Tables** — bulk read of all 165 ETABS database tables via `GetTableForDisplayArray`

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
- Only `model` (SapModel), `json`, and `math` are available
- All data stays local — nothing sent to the cloud

### Lightweight & Fast
- **40.8 MB** single-file `.mcpb` extension (no Python or runtime required)
- Startup in under 1 second — BM25 search replaces heavy ML models (no PyTorch)
- **Zero install** — drag `.mcpb` onto Claude Desktop and you're connected

### Developer-Friendly
- Add custom skills by dropping `.md` files next to the exe — no rebuild needed
- `build.ps1` one-command build: PyInstaller → stage → mcpb pack → optional hot-swap
- Two API index builders: CHM HTML parser + direct type library extractor (`ETABSv1.tlb`)

---

## Requirements

- Windows 10/11 (64-bit) — ETABS COM API is Windows-only
- CSI ETABS 21 or later, running with a model open
- Claude Desktop (latest)

---

## Quick Install

1. Download **`etabs-mcp.mcpb`** from [Releases](../../releases)
2. Open **Claude Desktop** → Settings → Extensions → drag the file onto the window
3. Open ETABS with a model loaded
4. Start a new Claude conversation and ask anything about your model

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

## License

MIT — free to use, modify, and distribute.
