# ETABS MCP

MCP server that bridges AI agents (Claude, Copilot, Gemini) to **CSI ETABS** via the ETABS COM API.

## Requirements

- Windows (COM API is Windows-only)
- ETABS 21 or later with a model open
- Python 3.11+

## Installation

```bash
cd etabs-mcp
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## Usage

### stdio (Claude Desktop)

Add to your Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "etabs-mcp": {
      "command": "C:\\path\\to\\etabs-mcp\\.venv\\Scripts\\etabs-mcp.exe",
      "args": []
    }
  }
}
```

### HTTP

```bash
etabs-mcp --transport http --port 18121 --log-level DEBUG
```

## Tools

| Tool | Description |
|------|-------------|
| `discover_api` | List available skills and usage guidance |
| `read_skills` | Load detailed skill docs (geometry, loads, analysis, etc.) |
| `list_instances` | Show running ETABS instances |
| `get_status` | Check connection and model state |
| `execute_code` | Run Python code against the live ETABS model |

## Sandbox

`execute_code` runs in a sandboxed environment. The `model` variable is the pre-connected `SapModel` object.

```python
# Example: count joints
count = model.PointObj.Count()
result = count
```

Available: `model` (SapModel), `json`, `math`, standard builtins.

Blocked: `import`, `dir()`, `getattr()`, dunder attributes, `eval`, `exec`, `open`.

## Skills

| Skill | Description |
|-------|-------------|
| `etabs-core` | Sandbox rules, units, model lock, file operations |
| `etabs-geometry` | Joints, frames, areas, stories, groups |
| `etabs-materials` | Material definitions (steel, concrete, rebar) |
| `etabs-sections` | Frame and area section properties |
| `etabs-loads` | Load patterns, cases, combinations, and load application |
| `etabs-analysis` | Running analysis, P-delta, modal, lock state |
| `etabs-results` | Displacements, reactions, frame forces, drifts, modes |
| `etabs-design` | Steel and concrete frame design |
| `etabs-errors` | Troubleshooting, ret codes, common mistakes |

## Development

```bash
# Lint
ruff check . && ruff format --check .

# Tests (unit — no ETABS needed)
pytest

# Integration tests (requires running ETABS)
pytest -m integration -v
```
