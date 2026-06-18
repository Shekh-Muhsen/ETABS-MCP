---
name: workflow-tool-test
description: "Live test results for all 6 MCP tools against ETABS 23.2.0. Use as a reference for expected behavior and known issues."
---

# ETABS MCP — Tool Test Reference

Tested against: ETABS 23.2.0, model `TEP-MC1-DYNAMIC-304.EDB`, Windows 11.
Server version: BM25 build (rank_bm25, no PyTorch), exe ~41 MB.

---

## Tool 1 — `get_status`

**Purpose:** Check connection state, version, model path, lock status.

**Call:**
```
get_status()          # no arguments needed when one instance is running
get_status(instance="etabs1")   # explicit alias
```

**Live result:**
```json
{
  "connected": true,
  "etabs_version": "23.2.0",
  "model_path": "D:\\Works\\...\\TEP-MC1-DYNAMIC-304.EDB",
  "alias": "etabs1",
  "model_locked": true
}
```

**Status:** ✅ Working. `model_locked: true` means analysis results exist and model is read-only.

---

## Tool 2 — `list_instances`

**Purpose:** List all running ETABS processes.

**Call:**
```
list_instances()
```

**Live result:**
```json
[{"alias": "etabs1", "pid": 10932, "file_path": "...EDB", "version": "23.2.0"}]
```

**Status:** ✅ Working. Use `alias` field in `execute_code` or `get_status` when multiple instances are open.

---

## Tool 3 — `discover_api`

**Purpose:** List all available skills. Call before `read_skills`.

**Call:**
```
discover_api()
```

**Live result (21 skills found):**
- `etabs-core`, `etabs-analysis`, `etabs-results`, `etabs-geometry`, `etabs-loads`
- `etabs-sections`, `etabs-materials`, `etabs-design`, `etabs-errors`
- `etabs-database-tables`
- `workflow-seismic-check`, `workflow-modal-report`, `workflow-seismic-params`
- `workflow-story-drift`, `workflow-base-shear`, `workflow-frame-forces`
- `workflow-gravity-report`, `workflow-design-concrete`, `workflow-model-audit`
- `workflow-modifiers`, `workflow-rs-scaling`
- `workflow-tool-test` (this skill)

**Status:** ✅ Working. Rescans sidecar folder on every call.

---

## Tool 4 — `read_skills`

**Purpose:** Load one or more skill documents by name.

**Call:**
```
read_skills(skills=["etabs-core"])
read_skills(skills=["etabs-results", "workflow-seismic-check"])
```

**Live result:** Full Markdown content of the skill returned. Tested with `etabs-core` — 100% success.

**Status:** ✅ Working.

---

## Tool 5 — `execute_code`

**Purpose:** Run Python in a sandbox against the live ETABS COM API.

**Call:**
```python
result = {
    "version": model.GetVersion()[0],
    "locked": bool(model.GetModelIsLocked()),
    "units": model.GetPresentUnits()
}
```

**Live result:**
```json
{"version": "23.2.0", "locked": true, "units": 6}
```

**Status:** ✅ Working. `units: 6` = kN_m.

### Quick model audit snippet
```python
ret = model.SetPresentUnits(6)
result = {
    "version": model.GetVersion()[0],
    "file": model.GetModelFilename(True),
    "locked": bool(model.GetModelIsLocked()),
    "joints": model.PointObj.Count(),
    "frames": model.FrameObj.Count(),
    "areas": model.AreaObj.Count(),
    "load_cases": list(model.LoadCases.GetNameList()[1]),
}
```

### Sandbox rules (must follow)
- `model` is pre-connected `SapModel` — no imports needed
- `import`, `dir()`, `getattr()`, dunders are **BLOCKED**
- Available: `json`, `math`, standard builtins (`list`, `dict`, `len`, `range`, etc.)
- Use `result = ...` or last expression to return data
- `print()` goes to `stdout` field in the response

---

## Tool 6 — `search_docs`

**Purpose:** BM25 keyword search over 1464 ETABS API methods.

**Call:**
```
search_docs(query="get joint displacement", top_k=5)
search_docs(query="run modal analysis")
search_docs(query="assign frame section property")
```

**Status:** ✅ Working after BM25 tokenizer fix (v2).

### BM25 tokenizer fix (important)
The original tokenizer used `.lower().split()` which kept dotted method names as single tokens (e.g. `cpointobj.getdispl` → one token). Queries like "joint" or "displacement" returned zero scores.

**Fix applied:** camelCase splitting + regex tokenization:
```python
text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)  # camelCase → camel Case
return re.findall(r"[a-z0-9]+", text.lower())
```
Now `cPointObj.GetDispl` → tokens `['c', 'point', 'obj', 'get', 'displ']`.

### Effective query strategies
| Goal | Query |
|------|-------|
| Joint displacements | `"joint displacement"` or `"point displ"` |
| Base reactions | `"base react"` |
| Frame forces | `"frame force"` |
| Modal periods | `"modal period"` |
| Story drifts | `"story drift"` |
| Assign section | `"assign frame section"` |
| Run analysis | `"run analysis"` |
| Set load case | `"load case set"` |

---

## Common Workflow Pattern

```
1. discover_api()                          → see available skills
2. read_skills(["etabs-core", "..."])      → load guidance
3. get_status()                            → confirm connection + lock state
4. search_docs(query="...")                → find API method if needed
5. execute_code(code="...")                → interact with ETABS
```

---

## Known Limitations (from live testing)

| Issue | Status |
|-------|--------|
| `SetTableForEditingArray` — comtypes cannot pass Python list as ByRef SAFEARRAY | Permanent — use object model methods instead |
| Results after EDB open — model locked but COM results not in memory | Workaround: unlock → set flags → RunAnalysis() |
| Ritz modal `StepNum` returns 0 | Use `i+1` as mode number fallback |
| Large model analysis via MCP | Must use ETABS UI (F5) — COM timeout |
| `SetModelIsLocked(False)` destroys results | Never unlock between RunAnalysis and result read |
