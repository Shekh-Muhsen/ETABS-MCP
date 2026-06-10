# ETABS MCP Server

An MCP (Model Context Protocol) server that bridges Claude AI to CSI ETABS via the COM API. Use Claude to query, analyze, and modify your ETABS models with natural language.

## Features

- **Full ETABS COM API access** — geometry, loads, analysis, results, design
- **AI-friendly skills** — built-in guidance for common workflows (seismic check, modal report, database tables, etc.)
- **BM25 API search** — fast keyword search across all ETABS API methods (`search_docs` tool)
- **Sandboxed code execution** — restricted Python sandbox; no arbitrary imports, no filesystem writes
- **Privacy-first** — all processing is local; no data sent to the cloud
- **Sidecar skills** — drop new `.md` skill files next to the exe without rebuilding

## Requirements

- Windows 10/11 (64-bit)
- CSI ETABS 21 or later, installed and running with a model open
- Claude Desktop (latest)

## Quick Start

1. **Download** `etabs-mcp.mcpb` from the [Releases](../../releases) page (or this folder)
2. **Open Claude Desktop** → Settings → Extensions → drag `etabs-mcp.mcpb` onto the window (or use "Install from file")
3. **Open ETABS** with a model loaded
4. **Start a new Claude conversation** — ask Claude to call `discover_api` and you're connected

## Tools

| Tool | Description |
|------|-------------|
| `discover_api` | List available skills and usage guidance — call this first |
| `read_skills` | Load one or more skill documents by name |
| `list_instances` | List running ETABS instances (alias, PID, file, version) |
| `get_status` | Check connection state, version, lock status |
| `execute_code` | Run Python in a sandbox against the live ETABS model |
| `search_docs` | BM25 keyword search across all ETABS API methods |

## Built-in Skills

| Skill | Description |
|-------|-------------|
| `etabs-core` | Core API patterns — geometry, sections, materials |
| `etabs-loads` | Load patterns, cases, combinations |
| `etabs-analysis` | Analysis setup and execution |
| `etabs-results` | Reading analysis results |
| `etabs-design` | Frame and area design |
| `workflow-seismic-check` | Full dynamic seismic check workflow |
| `workflow-modal-report` | Modal analysis and mass participation report |
| `etabs-database-tables` | DatabaseTables read/write patterns (165 tables) |

## Adding Skills (without rebuilding)

Create a folder named `etabs_skills/` next to `etabs-mcp.exe` in the extension directory:

```
C:\Users\<YOU>\AppData\Roaming\Claude\Claude Extensions\
  local.mcpb.etabs-mcp-contributors.etabs-mcp\
    etabs-mcp.exe
    etabs_skills\
      my-custom-skill\
        SKILL.md
```

Each skill is a folder with a `SKILL.md` file. The file should start with YAML front-matter:

```markdown
---
name: my-custom-skill
description: Short description shown in discover_api
---

# My Custom Skill

...guidance text...
```

The server rescans the skills directory on every `discover_api` call.

## Building from Source

### Prerequisites

```powershell
pip install pyinstaller rank_bm25 numpy fastmcp uvicorn comtypes pywin32
```

### Build

```powershell
git clone <this-repo>
cd etabs-mcp
.\build.ps1
```

Output: `etabs-mcp.mcpb` (~41 MB)

Optional flags:
- `.\build.ps1 -SkipPyInstaller` — skip PyInstaller, repack existing `dist\etabs-mcp.exe`
- `.\build.ps1 -Install` — hot-swap the exe into the Claude Desktop extension folder after build

### Source Layout

```
src/
  etabs_mcp/
    main.py           # entry point
    server.py         # MCP tools, BM25 search, lifespan
    connection.py     # COM connection, InstanceRegistry
    skills.py         # SkillsManager (discovery, loading, sidecar)
    sandbox/
      executor.py     # restricted Python sandbox
    file_io/          # CSV/XLSX input/output helpers
    etabs_skills/     # built-in skill .md files
    etabs_api_index.json  # pre-built API index for search_docs
mcpb/
  etabs-mcp.spec      # PyInstaller spec
  manifest.json       # mcpb manifest
build.ps1             # one-command build script
```

## Known Limitations

- **`DatabaseTables.SetTableForEditingArray`** — comtypes late-binding cannot pass Python lists as ByRef SAFEARRAY arguments. Use the ETABS object model methods instead (e.g. `model.FrameObj.SetSection()`).
- **Results after EDB open** — if you open a `.edb` file the model is locked but results are not in COM memory. Workaround: `SetModelIsLocked(False)` → set run flags → `RunAnalysis()`. See `workflow-seismic-check` skill.
- **Ritz modal StepNum** — `ModalParticipatingMassRatios()[3]` returns 0 for Ritz cases. Use row index `i+1` as mode number. See `workflow-modal-report` skill.
- **Large models** — analysis of large models must be triggered from the ETABS UI (F5). MCP-triggered analysis via `RunAnalysis()` works for small/medium models.

## License

MIT
