---
name: etabs-errors
description: "Use when troubleshooting errors: interpreting ret codes, common failure modes (locked model, no results, wrong units, name conflicts), sandbox restrictions, COM connection issues, and debugging patterns."
---

# ETABS Errors & Troubleshooting

Read `etabs-core` first for sandbox rules.

---

## Return Code Conventions

Every ETABS API call returns `ret` as **0** (success) or **non-zero** (error). In comtypes late-binding, return values come back as a tuple — `ret` is the **last element**.

```python
# Always check ret before using output
t = model.PointObj.GetNameList()
ret = t[-1]
if ret != 0:
    print("GetNameList failed: ret =", ret)
else:
    names = list(t[1])
    result = names
```

**Common ret values:**

| ret | Typical Meaning |
|-----|----------------|
| 0 | Success |
| 1 | General failure / invalid input |
| 2 | Object not found |
| 3 | Model is locked (cannot modify) |
| -1 | COM error or method not available |

---

## ⚠️ CRITICAL: SetModelIsLocked(False) Destroys All Results

**`model.SetModelIsLocked(False)` permanently deletes all analysis results.** This is irreversible — results are gone until the next analysis run.

**Never call this unless you intend to modify the model and re-run analysis.**

```python
# WRONG pattern — destroys results before reading them:
model.Analyze.RunAnalysis()
model.SetModelIsLocked(False)   # ← destroys results!
br = model.Results.BaseReact()  # returns empty

# CORRECT pattern:
model.Analyze.RunAnalysis()
# model auto-locks — do NOT unlock!
br = model.Results.BaseReact()  # read results while locked
```

---

## Common Error: Model is Locked (Cannot Modify)

**Symptom:** Geometry/property/load modifications return `ret != 0` unexpectedly.

**Cause:** `model.GetModelIsLocked()` returns `True` — analysis results exist.

```python
# Diagnose
is_locked = model.GetModelIsLocked()
print("Locked:", is_locked)

# Fix: unlock (DESTROYS all analysis results — only do if you will re-run!)
if is_locked:
    ret = model.SetModelIsLocked(False)
    print("Unlocked — results deleted, ret:", ret)
```

---

## Common Error: No Results Available

**Symptom:** Results methods return `ret != 0`, `n = 0`, or empty arrays.

**Cause 1:** Analysis has not been run (model is unlocked).
**Cause 2:** The load case/combo was not selected for output.
**Cause 3:** Using `SetCaseSelectedForOutput` for a combination (or `SetComboSelectedForOutput` for a case) — wrong method.
**Cause 4:** The load case was not set to run (`SetRunCaseFlag`).
**Cause 5:** DatabaseTables result table called without pre-selecting output cases.

```python
# Check lock state (results only available when locked)
if not model.GetModelIsLocked():
    print("No results — run analysis first: model.Analyze.RunAnalysis()")

# Always deselect all before selecting specific cases
ret = model.Results.Setup.DeselectAllCasesAndCombosForOutput()

# Use correct method based on type:
ret = model.Results.Setup.SetCaseSelectedForOutput("Dead")      # for load CASES
ret = model.Results.Setup.SetComboSelectedForOutput("ENV-ULS")  # for COMBINATIONS

# Verify the case exists
t = model.LoadCases.GetNameList()
names = list(t[1])
print("Available cases:", names)
```

---

## Common Error: Wrong Units

**Symptom:** Geometry appears at wrong scale (building 1000m tall), loads at wrong magnitude, or unexpected result values.

**Cause:** The model's present units differ from what you're entering.

```python
# Always set units explicitly at top of every code block
ret = model.SetPresentUnits(6)  # kN_m

# Verify current units
units = model.GetPresentUnits()
print("Current units enum:", units)
# 6 = kN_m (recommended)
# 3 = kip_in (for AISC catalog imports)
```

---

## Common Error: Name Already Exists

**Symptom:** `AddCartesian`, `AddByPoint`, `SetCase`, etc. return non-zero `ret`.

**Cause:** An object with the same name already exists.

```python
# Let ETABS auto-assign names — pass empty string or omit UserName
t = model.PointObj.AddCartesian(0, 0, 0)   # name auto-assigned by ETABS
name = t[0]
print("Auto-assigned name:", name)

# Check if a name exists before creating
t_list = model.PointObj.GetNameList()
existing_names = list(t_list[1])
if "MyJoint" in existing_names:
    print("Joint MyJoint already exists — skip creation")
```

---

## Common Error: Element Not Found

**Symptom:** Methods on a specific name return `ret != 0`.

**Cause:** The name doesn't exist — typo, not yet created, or deleted.

```python
# Verify existence before operating
t = model.FrameObj.GetNameList()
names = list(t[1])
target = "B1"
if target not in names:
    print("Frame", target, "does not exist. Available:", names[:5])
else:
    t2 = model.FrameObj.GetPoints(target)
    print("Points:", t2[0], t2[1])
```

---

## Common Error: GetNameList Unpacking

**Symptom:** `ret, num, names = model.PointObj.GetNameList()` raises `ValueError: not enough values to unpack`.

**Cause:** comtypes returns `[count, (names_tuple), ret]` as a single tuple — not 3 separate values.

```python
# WRONG (win32com style — does NOT work with comtypes)
# ret, num, names = model.PointObj.GetNameList()

# CORRECT (comtypes late-binding style)
t = model.PointObj.GetNameList()
count = t[0]
names = list(t[1])   # t[1] is a tuple of name strings
ret = t[-1]
```

---

## Common Error: Results Tuple Indexing

**Symptom:** Results values are wrong or IndexError.

**Cause:** Results return a tuple where `[0]` is `n` (row count) and values start at `[1]`. The last element `[-1]` is `ret`.

```python
# BaseReact structure: [n, LC_t, StepType_t, StepNum_t, FX_t, FY_t, FZ_t, MX_t, MY_t, MZ_t, gX_t, gY_t, gZ_t, ret]
t = model.Results.BaseReact()
n = t[0]
ret = t[-1]
if ret != 0 or n == 0:
    print("No base reaction results. Check case selection and analysis status.")
else:
    fx = list(t[4])
    print("Base shear FX:", fx)
```

---

## AttributeError on COM Methods

**Symptom:** `AttributeError: 'ETABSv1...' object has no attribute 'MethodName'`

The error message contains only the **method name** (e.g. `'GetShell_1'`), not a full path. This means the method does not exist on that COM object.

**Known non-existent methods (do NOT use):**
- `PropArea.GetShell_1()` → use `PropArea.GetSlab()` or `PropArea.GetWall()`
- `PropArea.GetShell()` → does not exist
- `Analyze.GetRunCaseFlag(name)` → takes integer index, not string name; call `GetRunCaseFlag()` with no args to get all flags
- `DesignConcrete.GetOverwrites()` → does not exist
- `DesignConcrete.GetComboStrength()` → does not exist
- `DesignSteel.GetCombo()` → does not exist

**Methods with incorrect signature (common mistake):**
- `DesignConcrete.SetComboStrength(name)` — WRONG, missing second arg. Use `SetComboStrength(name, True)`.
- `FrameForce("GroupName", 1)` — returns EMPTY. Group itemType=1 does NOT work for FrameForce. Use itemType=0 per object or DatabaseTables.
- `JointDispl("All", 1)` or `JointDispl("GroupName", 1)` — returns EMPTY. Use itemType=0 with specific joint names or DatabaseTables("Joint Displacements").

---

## Scalar-Return Methods Return int 0 on Success

These methods return a **scalar int** (not a tuple) — `0` means success, non-zero means error:
- `model.SetPresentUnits(n)` → `int`
- `model.SetModelIsLocked(bool)` → `int`
- `model.Analyze.RunAnalysis()` → `int`
- `model.File.Save()` → `int`
- `model.PointObj.SetRestraint(...)` → `int`

```python
# Correct — scalar return
ret = model.SetPresentUnits(6)
if ret != 0:
    print("SetPresentUnits failed:", ret)
```

Do NOT unpack these as tuples.

---

## Large Model Analysis Timeout

**Symptom:** `execute_code` call never returns, or returns a timeout error after `RunAnalysis()`.

**Cause:** `model.Analyze.RunAnalysis()` blocks until analysis is complete. For large models (>1000 elements) this exceeds the MCP timeout.

**Fix:** Tell the user to run analysis directly in ETABS:
1. In ETABS: **Analyze → Run Analysis (F5)**
2. Wait for analysis to complete in ETABS
3. After completion, `model.GetModelIsLocked()` returns `True`
4. Results are then accessible via MCP

```python
# Check if analysis is done (model is locked)
is_locked = model.GetModelIsLocked()
if not is_locked:
    result = {"status": "Analysis not run. Please run analysis in ETABS: Analyze → Run Analysis (F5), then retry."}
else:
    result = {"status": "Analysis complete — model is locked, results available"}
```

---

## Sandbox Restriction Errors

| Error Message | Cause | Fix |
|---------------|-------|-----|
| `Validation failed: import statements are not allowed` | Used `import X` | Remove import; use pre-injected `model`, `json`, `math` |
| `access to 'dir' is not allowed` | Called `dir(obj)` | Use skill docs for API reference instead |
| `access to '__class__' is not allowed` | Accessed `obj.__class__` | Remove dunder access |
| `access to '_oleobj_' is not allowed` | Accessed COM internal | Don't access `_`-prefixed attributes |
| `access to 'getattr' is not allowed` | Called `getattr(obj, name)` | Use direct attribute access instead |
| `Executor busy` | Previous call timed out | Restart the MCP server |

**Available builtins (safe to use):**
`abs`, `all`, `any`, `bool`, `dict`, `enumerate`, `filter`, `float`, `frozenset`,
`int`, `isinstance`, `iter`, `len`, `list`, `map`, `max`, `min`, `next`, `print`,
`range`, `repr`, `reversed`, `round`, `set`, `sorted`, `str`, `sum`, `tuple`, `zip`.

---

## COM Connection Errors

### No ETABS Instances Found

```
ValueError: No ETABS instances found. Is ETABS running?
```

**Fix:** Launch ETABS with a model open, then retry. Use `list_instances` to verify.

### Connection Timed Out

```
{"connected": false, "error": "Connection timed out"}
```

**Cause:** ETABS is open but unresponsive (modal dialog, long operation in progress).

**Fix:**
- Dismiss any dialog boxes in ETABS
- Close and reopen the model
- Restart the MCP server

### Model Not Open

**Cause:** ETABS is running but no model file is loaded.

**Fix:** Open a model file in ETABS (File → Open), then retry.

---

## Debugging Patterns

### Print All Intermediate Values

```python
ret = model.SetPresentUnits(6)
print("SetPresentUnits ret:", ret)

t = model.PointObj.GetNameList()
print("GetNameList:", "count=", t[0], "ret=", t[-1])
print("First 5 names:", list(t[1])[:5])

t2 = model.FrameObj.GetNameList()
print("Frames:", t2[0])

t3 = model.AreaObj.GetNameList()
print("Areas:", t3[0])

result = {"joints": t[0], "frames": t2[0], "areas": t3[0]}
```

### Full Model State Audit

```python
ret = model.SetPresentUnits(6)

ver = model.GetVersion()
filename = model.GetModelFilename(True)
is_locked = model.GetModelIsLocked()
units = model.GetPresentUnits()

n_pts = model.PointObj.Count()
n_frames = model.FrameObj.Count()
n_areas = model.AreaObj.Count()

t_lp = model.LoadPatterns.GetNameList()
t_lc = model.LoadCases.GetNameList()
t_co = model.LoadCombos.GetNameList()
t_mat = model.PropMaterial.GetNameList()
t_sec = model.PropFrame.GetNameList()

result = {
    "version": ver[0],
    "build": ver[1],
    "file": filename,
    "units_enum": units,
    "locked": is_locked,
    "joints": n_pts,
    "frames": n_frames,
    "areas": n_areas,
    "load_patterns": list(t_lp[1]) if t_lp[0] > 0 else [],
    "load_cases": list(t_lc[1]) if t_lc[0] > 0 else [],
    "combos": list(t_co[1]) if t_co[0] > 0 else [],
    "materials": list(t_mat[1]) if t_mat[0] > 0 else [],
    "frame_sections": list(t_sec[1]) if t_sec[0] > 0 else [],
}
```

### Diagnose Results Failure

```python
# Check analysis status
is_locked = model.GetModelIsLocked()
print("Model locked (results available):", is_locked)

# Check run flags
t = model.Analyze.GetRunCaseFlag()
n = t[0]
for i in range(n):
    print(list(t[1])[i], "run flag:", list(t[2])[i])

# Try to read base reactions
ret2 = model.Results.Setup.DeselectAllCasesAndCombosForOutput()
t_lc = model.LoadCases.GetNameList()
lc_names = list(t_lc[1])

if len(lc_names) > 0:
    ret3 = model.Results.Setup.SetCaseSelectedForOutput(lc_names[0])
    br = model.Results.BaseReact()
    print("BaseReact n:", br[0], "ret:", br[-1])

result = {"locked": is_locked, "cases": lc_names}
```

---

## Analysis Not Converging

**Symptom:** `RunAnalysis()` returns non-zero or results are all zero.

**Checks:**
1. All joints have proper boundary conditions (at least one support)
2. All frames/areas have valid section assignments
3. Load patterns referenced in load cases actually exist
4. Modal case has `SetNumberModes` configured

```python
# Quick geometry check
n_pts = model.PointObj.Count()
n_frames = model.FrameObj.Count()
if n_pts == 0 or n_frames == 0:
    print("Model has no geometry — add joints and frames first")

# Check that load patterns exist
t_lp = model.LoadPatterns.GetNameList()
print("Load patterns:", list(t_lp[1]))

# Check that load cases exist
t_lc = model.LoadCases.GetNameList()
print("Load cases:", list(t_lc[1]))

result = {"joints": n_pts, "frames": n_frames}
```

---

## itemType Parameter Reference

Many methods accept `ItemType` (or `ItemTypeElm`) to control scope:

| itemType | Meaning |
|----------|---------|
| 0 | Single object (Name = object name) |
| 1 | Group (Name = group name) |
| 2 | Selected objects (Name ignored) |

```python
# Apply to single object
ret = model.FrameObj.SetSection("B1", "Beam300x600", 0, 0, 0)

# Apply to all members in group "Beams"
ret = model.FrameObj.SetSection("Beams", "Beam300x600", 0, 0, 1)

# Apply to currently selected objects
ret = model.FrameObj.SetSection("", "Beam300x600", 0, 0, 2)
```

> **CONFIRMED LIMITATION — Results API:** `model.Results.FrameForce(name, 1)` (group itemType=1) and `model.Results.JointDispl(name, 1)` (group) return **empty results** in ETABS 23.2.0. For these results methods, always use itemType=0 with a specific object name, or use `DatabaseTables` for bulk extraction (after pre-selecting output cases via Results.Setup).
