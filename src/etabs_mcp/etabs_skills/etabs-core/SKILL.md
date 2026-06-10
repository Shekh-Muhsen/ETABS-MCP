---
name: etabs-core
description: "Essential patterns: sandbox rules, the model variable, units, file operations, locking, version info, DatabaseTables, and model state. Read this before any other skill."
---

# ETABS Core — Sandbox Rules, Units, File & Model Operations

## The `model` Variable

Inside every `execute_code` call, **`model`** is the pre-connected `SapModel` object (root of the ETABS OAPI v1 COM API). You never import anything — the sandbox provides `model` directly, along with `json` and `math`.

Connection is made via:
```
ETABSv1.Helper → GetObject("CSI.ETABS.API.ETABSObject") → .SapModel
```
comtypes late binding is used (no type library). All COM calls are late-bound.

```python
# Correct — use model directly
ret = model.SetPresentUnits(6)

# Wrong — import is blocked
import comtypes  # ValidationError: import statements are not allowed
```

### Sub-Objects of `model`

| Sub-object | Purpose |
|------------|---------|
| `model.PointObj` | Joints / nodes |
| `model.FrameObj` | Frame elements (beams, columns, braces) |
| `model.AreaObj` | Area elements (slabs, walls, shells) |
| `model.SolidObj` | Solid elements |
| `model.LinkObj` | Links and springs |
| `model.PropFrame` | Frame section properties |
| `model.PropArea` | Area / slab / shell section properties |
| `model.PropMaterial` | Material definitions |
| `model.LoadPatterns` | Load pattern definitions |
| `model.LoadCases` | Load case definitions |
| `model.LoadCombos` | Load combinations (RespCombo) |
| `model.Analyze` | Analysis control |
| `model.Results` | Results extraction |
| `model.Results.Setup` | Results output case selection |
| `model.DesignConcrete` | Concrete frame design |
| `model.DesignSteel` | Steel frame design |
| `model.Story` | Story data |
| `model.File` | File operations (open, save) |
| `model.View` | Viewport control |
| `model.SelectObj` | Object selection (All, None_, ClearSelection) |
| `model.GroupDef` | Group management |
| `model.DatabaseTables` | Table-based data extraction |

---

## Sandbox Restrictions

| Blocked | Reason |
|---------|--------|
| `import X` | Security — all needed objects are pre-injected |
| `dir(obj)` | Blocked builtin |
| `getattr(obj, name)` | Blocked builtin |
| `obj.__class__` | Dunder attribute access |
| `obj._oleobj_` | COM internal attribute |
| `open()` | File system access blocked |
| `exec()` / `eval()` | Code execution blocked |
| `global` / `nonlocal` | Scope escape |
| `async def` / `await` | Not needed |
| `@decorator` | Blocked |

**Available builtins:** `abs`, `all`, `any`, `bool`, `dict`, `enumerate`, `filter`, `float`, `frozenset`, `int`, `isinstance`, `iter`, `len`, `list`, `map`, `max`, `min`, `next`, `print`, `range`, `repr`, `reversed`, `round`, `set`, `sorted`, `str`, `sum`, `tuple`, `zip`.

**Available modules:** `json` (`dumps`, `loads`), `math` (all standard functions).

**Use `print()` for debug output** — captured in the `stdout` field of the response.

---

## Units

ETABS uses a units enum (`eUnits`). Always set units explicitly before geometry or load operations.

### Unit Enum Reference

| Enum | Units | Typical Use |
|------|-------|-------------|
| 1 | lb_in | Imperial small |
| 2 | lb_ft | Imperial large |
| 3 | kip_in | US structural |
| 4 | kip_ft | US structural |
| 5 | kN_mm | Metric small |
| 6 | kN_m | Metric standard (recommended) |
| 7 | kN_cm | Metric medium |
| 8 | N_mm | SI small |
| 9 | N_m | SI |
| 10 | tf_m | Metric tonnef |

### Getting and Setting Units

```python
# Get current units enum
units = model.GetPresentUnits()
print("Current units enum:", units)  # e.g. 6 = kN_m

# Set to kN_m (recommended for SI practice)
ret = model.SetPresentUnits(6)
if ret != 0:
    print("Warning: SetPresentUnits failed, ret =", ret)
```

### Unit Conversion Reference (to kN/m²)

| Value | kN/m² |
|-------|-------|
| 1 MPa | 1 000 kN/m² |
| 1 GPa | 1 000 000 kN/m² |
| 200 GPa (steel E) | 200 000 000 kN/m² |
| 30 GPa (concrete E) | 30 000 000 kN/m² |
| 1 ksi | 6 894.76 kN/m² |
| 50 ksi (Fy steel) | 344 738 kN/m² |

---

## Return Value Convention

Nearly every ETABS API call returns `ret` as the **last** element (0 = success, non-zero = error). In comtypes late-binding Python, out-parameters become a tuple:

```python
# GetNameList-style: returns [count, (names_tuple,), ret]
ret_tuple = model.PointObj.GetNameList()
# ret_tuple[0] = count (int)
# ret_tuple[1] = tuple of name strings
# ret_tuple[-1] = ret code
count = ret_tuple[0]
names = list(ret_tuple[1])
ret = ret_tuple[-1]

# GetVersion: returns [version_str, build_num, ret]
ver_tuple = model.GetVersion()
version_str = ver_tuple[0]
build_num = ver_tuple[1]
ret = ver_tuple[2]
print("ETABS version:", version_str, "build:", build_num)

# Simple methods that only return ret
ret = model.Analyze.RunAnalysis()
```

**Always check `ret == 0` before using output values.**

---

## Model State: Lock / Unlock

The model must be **unlocked** to modify geometry, properties, and loads.
After a successful analysis, the model is **locked** (results available).
Unlocking clears all analysis results.

```python
# Check lock state
is_locked = model.GetModelIsLocked()
print("Locked:", is_locked)

# Unlock to allow modifications (clears existing results)
ret = model.SetModelIsLocked(False)

# Lock manually (rarely needed — RunAnalysis locks automatically)
ret = model.SetModelIsLocked(True)
```

---

## Version and File Info

```python
# Get ETABS version
ver_tuple = model.GetVersion()
print("Version:", ver_tuple[0], "Build:", ver_tuple[1])

# Get model filename
# GetModelFilename(bIncludePath=True)
filename = model.GetModelFilename(True)
print("File:", filename)  # e.g. "C:\Projects\Ati-12 Seismic model-v5.EDB"

# Get filename without path
short_name = model.GetModelFilename(False)
```

---

## File Operations

```python
# Save current model in-place
ret = model.File.Save()

# Save to a new path (absolute .edb path required)
ret = model.File.SaveAs("C:\\Projects\\building_v2.edb")

# Open an existing file (model must be unlocked first)
ret = model.File.OpenFile("C:\\Projects\\building.edb")

# Initialize a new blank model
# InitializeNewModel(eUnits)
ret = model.InitializeNewModel(6)  # new model in kN_m
```

---

## Result Capture

The last expression OR an explicit `result = ...` is returned to the caller:

```python
# Option 1: last expression (auto-captured)
model.PointObj.Count()

# Option 2: explicit result assignment (preferred for clarity)
ret_tuple = model.PointObj.GetNameList()
names = list(ret_tuple[1])
result = {"count": ret_tuple[0], "names": names}
```

---

## Definitive Tuple Index Reference

All `GetNameList`-style calls return `[count, (names_tuple,), ret]`:
```python
t = model.PointObj.GetNameList()
count = t[0]          # number of items
names = list(t[1])    # tuple of name strings → convert to list
ret   = t[-1]         # return code (0 = success)
```

Results API general pattern — **all** `model.Results.*` methods:
- `result[0]` = n (number of result rows)
- `result[1]` through `result[-2]` = data tuples (one tuple per column)
- `result[-1]` = ret code (0 = success)
- Access a column: `[result[k][i] for i in range(result[0])]`

Quick index cheat-sheet for the most-used Results calls:

| Method | Key indices |
|--------|-------------|
| `BaseReact()` | [1]=Case [4]=FX [5]=FY [6]=FZ [7]=MX [8]=MY [9]=MZ |
| `ModalPeriod()` | [1]=Case [3]=StepNum [4]=Period [5]=Freq [6]=CircFreq |
| `ModalParticipatingMassRatios()` | [3]=StepNum [4]=Period [5]=UX [6]=UY [8]=SumUX [9]=SumUY |
| `StoryDrifts()` | [1]=Story [2]=Case [5]=Direction [6]=Drift |
| `JointDispl(name,0)` | [1]=ObjName [3]=Case [6]=U1 [7]=U2 [8]=U3 |
| `FrameForce(name,0)` | [1]=ObjName [4]=Case [7]=P [8]=V2 [9]=V3 [10]=T [11]=M2 [12]=M3 |
| `PierForce()` | [1]=Story [2]=Pier [3]=Case [6]=Location [7]=P [8]=V2 [9]=V3 [10]=T |

---

## DatabaseTables — Bulk Data Extraction

`model.DatabaseTables` provides access to all tabular data in ETABS. This is the most robust way to extract large result sets.

> **CRITICAL for result tables:** DatabaseTables for analysis results (Story Forces, Story Drifts, Frame Forces, etc.) **only returns data when output cases are pre-selected** via `model.Results.Setup`. Always call `DeselectAllCasesAndCombosForOutput()` + `SetCaseSelectedForOutput()` / `SetComboSelectedForOutput()` before calling `GetTableForDisplayArray` for result tables. Model definition tables (materials, sections, geometry) do not require this.

### List Available Tables

```python
# GetAvailableTables() → [n, (names_tuple), ret]
t = model.DatabaseTables.GetAvailableTables()
n = t[0]
names = list(t[1]) if n > 0 else []
result = names
```

### Read a Table

```python
# GetTableForDisplayArray(TableName, FieldKeyList, GroupName, TableVersion, FieldsKeysIncluded, NumRecords, TableData)
# All output args are passed as empty placeholders; ETABS fills them
# Returns: [ret, TableVersion, Fields_tuple, NumRecords, FlatData_tuple, ret2]

raw = model.DatabaseTables.GetTableForDisplayArray(
    "Story Forces",  # table name (from GetAvailableTables)
    [],              # field key list (empty = all fields)
    "All",           # group name
    0,               # table version
    [],              # fields keys included placeholder
    0,               # num records placeholder
    []               # table data placeholder
)
# raw[0] = ret, raw[1] = version, raw[2] = fields tuple, raw[3] = row count
# raw[4] = flat data tuple (all rows concatenated), raw[5] = ret2

fields = list(raw[2])
n_rows = raw[3]
flat = list(raw[4])
n_fields = len(fields)

rows = []
for i in range(n_rows):
    row = {}
    for j in range(n_fields):
        row[fields[j]] = flat[i * n_fields + j]
    rows.append(row)

result = rows
```

### Common Table Names

| Table Name | Content |
|------------|---------|
| `"Story Forces"` | Story shears and overturning moments |
| `"Story Drifts"` | Story drift results |
| `"Joint Displacements"` | All joint displacements |
| `"Frame Forces - Beams"` | Beam internal forces |
| `"Frame Forces - Columns"` | Column internal forces |
| `"Modal Participating Mass Ratios"` | Modal mass participation |
| `"Base Reactions"` | Base reaction forces |
| `"Concrete Column Summary - ACI 318"` | Concrete column design |
| `"Concrete Beam Summary - ACI 318"` | Concrete beam design |
| `"Steel Frame Design Summary - AISC 360"` | Steel design results |

---

## Quick Model Audit

```python
ret = model.SetPresentUnits(6)  # kN_m

ver_tuple = model.GetVersion()
filename = model.GetModelFilename(True)
is_locked = model.GetModelIsLocked()

n_pts = model.PointObj.Count()
n_frames = model.FrameObj.Count()
n_areas = model.AreaObj.Count()

lp_tuple = model.LoadPatterns.GetNameList()
lc_tuple = model.LoadCases.GetNameList()

result = {
    "version": ver_tuple[0],
    "build": ver_tuple[1],
    "file": filename,
    "locked": is_locked,
    "joints": n_pts,
    "frames": n_frames,
    "areas": n_areas,
    "load_patterns": list(lp_tuple[1]) if lp_tuple[0] > 0 else [],
    "load_cases": list(lc_tuple[1]) if lc_tuple[0] > 0 else [],
}
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Ignoring `ret` | Always check `ret == 0` before using output |
| Adding geometry while model is locked | Call `model.SetModelIsLocked(False)` first |
| Unpacking GetNameList as `ret, num, names` | Use tuple indexing: `[0]`=count, `[1]`=names tuple, `[-1]`=ret |
| Wrong units | Call `model.SetPresentUnits(6)` before any geometry/load operation |
| Calling `dir(model.PointObj)` | Blocked — use skill docs for API reference |
| DatabaseTables result table returns empty | Must select output cases via Results.Setup first |

## ⚠️ CRITICAL: SetModelIsLocked(False) Destroys Results

**`model.SetModelIsLocked(False)` permanently deletes all analysis results.** Never call this unless you intend to modify the model and re-run the full analysis.

Correct pattern:
1. Modify model (geometry / loads / sections)
2. `model.Analyze.RunAnalysis()` — model auto-locks after analysis
3. Read results — never unlock between step 2 and 3!
4. If scaling is needed (e.g. seismic 85% rule): unlock → modify scale factor → re-run → read results

```python
# WRONG — destroys results before reading them
model.Analyze.RunAnalysis()
model.SetModelIsLocked(False)   # ← never do this before reading results!
br = model.Results.BaseReact()

# CORRECT
model.Analyze.RunAnalysis()
# model is now auto-locked
br = model.Results.BaseReact()   # read results while locked
```
