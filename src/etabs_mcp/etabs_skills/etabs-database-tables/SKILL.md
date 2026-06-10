---
name: etabs-database-tables
description: "Use when reading any model definition or analysis result table in bulk via DatabaseTables, or when editing model properties via object-model methods. Covers GetTableForDisplayArray, result table setup, field schemas for all 165 tables, and the correct edit patterns."
---

# ETABS DatabaseTables — Read, Edit, and Results Extraction

Read `etabs-core` first.

---

## Table Inventory (165 total)

### Result Tables (42) — require `Results.Setup` pre-selection

| Table | Key Fields | Notes |
|---|---|---|
| `Base Reactions` | OutputCase, FX, FY, FZ, MX, MY, MZ | Select cases first |
| `Story Forces` | Story, OutputCase, Location, VX, VY, T, MX, MY | Top+Bottom per story |
| `Story Drifts` | Story, OutputCase, Direction, Drift, Drift/ | Filter CaseType=LinRespSpec, StepType=Max |
| `Story Stiffness` | Story, OutputCase, ShearX, DriftX, StiffX, ShearY, DriftY, StiffY | EX/EY cases only |
| `Story Max Over Avg Drifts` | Story, OutputCase, Direction, Max Drift, Avg Drift, Ratio | Irregularity check |
| `Diaphragm Max Over Avg Drifts` | Story, OutputCase, Item, Max Drift, Avg Drift, Ratio, Label | Per diaphragm |
| `Diaphragm Forces` | Story, OutputCase, Item, FX, FY, MZ | Diaphragm seismic force |
| `Diaphragm Center Of Mass Displacements` | Story, OutputCase, Item, Ux, Uy | CM displacement |
| `Centers Of Mass And Rigidity` | Story, Diaphragm, MassX, XCM, YCM, XCR, YCR | No case selection needed |
| `Mass Summary by Story` | Story, UX, UY, UZ | No case selection needed |
| `Mass Summary by Group` | GroupName, UX, UY, UZ | No case selection needed |
| `Mass Summary by Diaphragm` | Story, Diaphragm, UX, UY | No case selection needed |
| `Assembled Joint Masses` | Story, Label, Ux, Uy, Uz | No case selection needed |
| `Joint Displacements` | Story, Label, UniqueName, OutputCase, Ux, Uy, Uz, Rx, Ry, Rz | Large: 34k+ rows |
| `Joint Displacements - Absolute` | Same as above | Absolute values |
| `Joint Reactions` | Story, Label, UniqueName, OutputCase, FX, FY, FZ, MX, MY, MZ | Support joints only |
| `Joint Design Reactions` | Story, Label, OutputCase, FX, FY, FZ | Design combinations |
| `Joint Drifts` | Story, Label, OutputCase, Ux, Uy | Relative story drifts |
| `Element Forces - Beams` | Story, Label, OutputCase, Station, P, V2, V3, T, M2, M3 | Very large — use Group filter |
| `Element Forces - Columns` | Same fields as beams | Very large — use Group filter |
| `Element Joint Forces - Frame` | Story, Label, OutputCase, JtLabel, F1, F2, F3, M1, M2, M3 | At joints |
| `Element Forces - Area Shells` | Story, Label, OutputCase, F11, F22, F12, M11, M22, M12 | Shell forces |
| `Element Joint Forces - Shells` | Story, Label, OutputCase, F1, F2, F3 | Shell joint forces |
| `Element Stresses - Area Shells` | Story, Label, OutputCase, S11Top, S22Top, S12Top, S11Bot, S22Bot | Stresses top/bot |
| `Element Strains - Area Shells` | Story, Label, OutputCase, E11Top, E22Top | Strains |
| `Pier Forces` | Story, Pier, OutputCase, Location, P, V2, V3, T, M2, M3 | 4k+ rows |
| `Integrated Wall Reactions` | Story, Pier, OutputCase, Location, F1, F2, F3, M1, M2, M3 | Wall resultants |
| `Modal Periods And Frequencies` | Case, Mode, Period, Frequency, CircFreq, Eigenvalue | Modal case only |
| `Modal Participating Mass Ratios` | Case, Mode, Period, UX, UY, UZ, SumUX, SumUY, SumUZ, RX, RY, RZ, SumRX, SumRY, SumRZ | Modal case only |
| `Modal Load Participation Ratios` | Case, ItemType, Item, Static, Dynamic | UX/UY/UZ participation % |
| `Modal Direction Factors` | Case, Mode, Period, UX, UY, UZ, RZ | Mode dominant direction |
| `Modal Participation Factors` | Case, Mode, Period, Ux, Uy, Uz, Rx, Ry, Rz | Raw factors |
| `Response Spectrum Modal Info` | SpecCase, ModalCase, Mode, Period, DampRatio, U1Acc, U2Acc, U1Amp | RS spectral amplitudes |
| `Story Accelerations` | Story, OutputCase, Direction, Acc | Floor accelerations |
| `Joint Accelerations - Absolute` | Story, Label, OutputCase, Ux, Uy, Uz | Absolute joint acc |
| `Joint Velocities - Absolute` | Story, Label, OutputCase, Ux, Uy, Uz | Absolute joint vel |
| `Story Max Over Avg Displacements` | Story, OutputCase, Direction, Max Disp, Avg Disp, Ratio | Disp irregularity |

### Editable Definition / Assignment Tables (60)

| Table | Key Fields | Edit via |
|---|---|---|
| `Project Information` | ClientName, ProjectName, ProjectNum, CompanyName, Engineer | DatabaseTables GET only; edit via `model.File` or direct ETABS |
| `Story Definitions` | Tower, Story, Height, IsMaster, SimilarTo | `model.Story.SetHeight()` |
| `Frame Section Property Definitions - Concrete Rectangular` | Name, Material, t3, t2, AMod..WMod, DesignType | `model.PropFrame.SetRectangle()` |
| `Frame Section Property Definitions - Concrete Circle` | Name, Material, Diameter | `model.PropFrame.SetCircle()` |
| `Frame Section Property Definitions - Steel I/Wide Flange` | Name, Material, t3, t2, tf, tw | `model.PropFrame.SetISection()` |
| `Frame Section Property Definitions - Summary` | Name, Material, Shape, t3, t2 | Read-only summary |
| `Frame Assignments - Property Modifiers` | Story, Label, UniqueName, AMod, A2Mod..WMod | `model.FrameObj.SetModifiers()` |
| `Frame Assignments - Section Properties` | Story, Label, UniqueName, AnalSect, DesignSect | `model.FrameObj.SetSection()` |
| `Frame Assignments - Releases and Partial Fixity` | Story, Label, UniqueName, II, JJ, StartM, EndM | `model.FrameObj.SetReleases()` |
| `Frame Assignments - End Length Offsets` | Story, Label, iOff, jOff | `model.FrameObj.SetEndLengthOffset()` |
| `Area Assignments - Section Properties` | Story, Label, UniqueName, AnalSect, DesignSect | `model.AreaObj.SetProperty()` |
| `Area Assignments - Stiffness Modifiers` | Story, Label, UniqueName, f11..m | `model.AreaObj.SetModifiers()` |
| `Load Combination Definitions` | Name, Type, IsAuto, LoadName, SF | `model.RespCombo.Add/Delete/GetCaseList()` |
| `Load Case Definitions - Linear Static` | Name, InitialCond | `model.LoadCases` methods |
| `Load Case Definitions - Response Spectrum` | Name, ModalCase, DirCombo, AbsSF | `model.LoadCases` methods |
| `Load Case Definitions - Summary` | Name, Type, InitialCond, DesignAct | Read; add via `model.LoadCases.Add()` |
| `Load Pattern Definitions` | Name, Type, SelfWtMult | `model.LoadPatterns.Add/SetSelfWTMultiplier()` |
| `Frame Loads Assignments - Distributed` | Story, Label, UniqueName, LoadPat, Dir, DistType, WA, WB | `model.FrameObj.SetLoadDistributed()` |
| `Area Load Assignments - Uniform` | Story, Label, UniqueName, LoadPat, Dir, Value | `model.AreaObj.SetLoadUniform()` |
| `Joint Loads Assignments - Force` | Story, Label, UniqueName, LoadPat, FX, FY, FZ, MX, MY, MZ | `model.PointObj.SetLoadForce()` |
| `Joint Assignments - Restraints` | Story, Label, UniqueName, U1..R3 | `model.PointObj.SetRestraint()` |
| `Material Properties - General` | Name, Type, Color | Read via `model.PropMaterial` |
| `Group Definitions` | GroupName, ObjectType, ObjectLabel | `model.GroupDef` methods |

### Other Tables (64) — read-only metadata

Analysis Options, Concrete/Steel Design Preferences, Overwrites, Bay geometry, Connectivity, Functions, Grid definitions, Mass Source, Material data details, Misc Options.

---

## Read Pattern — `GetTableForDisplayArray`

```python
# Works for ALL 165 tables
# For result tables: must pre-select output cases via Results.Setup first
# For definition/assignment tables: no setup needed

raw = model.DatabaseTables.GetTableForDisplayArray(
    "Story Forces",  # table name
    [],              # field filter (empty = all fields)
    "All",           # group name
    0,               # table version placeholder
    [],              # fields included placeholder
    0,               # num records placeholder
    []               # table data placeholder
)
# Returns: (ret, version, fields_tuple, n_rows, flat_data_tuple, ret2_or_similar)
# raw[0] = ret tuple (usually empty)
# raw[1] = table version int
# raw[2] = fields tuple (may contain None — filter them)
# raw[3] = n_rows int
# raw[4] = flat data tuple (all rows concatenated, n_rows × n_fields values)
# raw[5] = ret code (0 = success) — VERIFY: raw[-1] for the actual ret

fields = [f for f in list(raw[2]) if f is not None]
n_rows = raw[3]
flat   = list(raw[4])
nf     = len(fields)

rows = [
    {fields[j]: flat[i * nf + j] for j in range(nf)}
    for i in range(n_rows)
]
# All values are strings — convert to float/int as needed:
# float(row["Drift"]) if row["Drift"] not in ("", None) else None
```

### Result Table Setup (required before reading result tables)

```python
model.SetPresentUnits(6)
model.Results.Setup.DeselectAllCasesAndCombosForOutput()

# For load cases:
model.Results.Setup.SetCaseSelectedForOutput("Dead")
model.Results.Setup.SetCaseSelectedForOutput("MODAL CASE")
model.Results.Setup.SetCaseSelectedForOutput("EX")
model.Results.Setup.SetCaseSelectedForOutput("Spec X")

# For load combinations:
model.Results.Setup.SetComboSelectedForOutput("ENV-ULS")

# Then read:
raw = model.DatabaseTables.GetTableForDisplayArray("Base Reactions", [], "All", 0, [], 0, [])
```

### Filter by Group (reduces rows for large tables)

```python
# Use group name instead of "All" to limit rows
raw = model.DatabaseTables.GetTableForDisplayArray(
    "Element Forces - Beams", [], "1st Floor Ex Wall", 0, [], 0, [])
```

---

## Read Recipes — Key Result Tables

### Modal Mass Participation

```python
model.SetPresentUnits(6)
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
model.Results.Setup.SetCaseSelectedForOutput("MODAL CASE")  # exact case name

raw = model.DatabaseTables.GetTableForDisplayArray(
    "Modal Participating Mass Ratios", [], "All", 0, [], 0, [])
# Fields: Case, Mode, Period, UX, UY, UZ, SumUX, SumUY, SumUZ, RX, RY, RZ, SumRX, SumRY, SumRZ
fields = [f for f in list(raw[2]) if f is not None]
n = raw[3]; flat = list(raw[4]); nf = len(fields)
rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n)]

# 90% check
for r in rows:
    if float(r["SumUX"] or 0) >= 0.90 and float(r["SumUY"] or 0) >= 0.90:
        print("90% mass met at mode", r["Mode"])
        break

result = {"n_modes": n, "table": rows}
```

### Story Forces — Seismic Shear per Story

```python
model.SetPresentUnits(6)
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
for c in ["EX", "EY", "Spec X", "Spec Y"]:
    model.Results.Setup.SetCaseSelectedForOutput(c)

raw = model.DatabaseTables.GetTableForDisplayArray("Story Forces", [], "All", 0, [], 0, [])
# Fields: Story, OutputCase, CaseType, StepType, StepNumber, Location, P, VX, VY, T, MX, MY
fields = [f for f in list(raw[2]) if f is not None]
n = raw[3]; flat = list(raw[4]); nf = len(fields)
rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n)]

# Filter to bottom of each story, RS Max steps only
rs_bot = [r for r in rows
          if r.get("Location") == "Bottom"
          and r.get("CaseType") == "LinRespSpec"
          and r.get("StepType") == "Max"]

result = rs_bot
```

### Story Drifts — Max per Story

```python
model.SetPresentUnits(6)
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
for c in ["Spec X", "Spec Y"]:
    model.Results.Setup.SetCaseSelectedForOutput(c)

raw = model.DatabaseTables.GetTableForDisplayArray("Story Drifts", [], "All", 0, [], 0, [])
# Fields: Story, OutputCase, CaseType, StepType, StepNumber, Direction, Drift, Drift/, Label, X, Y, Z
fields = [f for f in list(raw[2]) if f is not None]
n = raw[3]; flat = list(raw[4]); nf = len(fields)
rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n)]

# RS Max rows only
rs = [r for r in rows
      if r.get("CaseType") == "LinRespSpec" and r.get("StepType") == "Max"
      and r.get("Drift") not in ("", None)]

max_X = max((float(r["Drift"]) for r in rs if r.get("Direction") == "X"), default=None)
max_Y = max((float(r["Drift"]) for r in rs if r.get("Direction") == "Y"), default=None)
result = {"max_drift_X": max_X, "max_drift_Y": max_Y, "rows": rs}
```

### Pier Forces

```python
model.SetPresentUnits(6)
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
model.Results.Setup.SetComboSelectedForOutput("ENV-ULS")  # or SetCaseSelectedForOutput

raw = model.DatabaseTables.GetTableForDisplayArray("Pier Forces", [], "All", 0, [], 0, [])
# Fields: Story, Pier, OutputCase, CaseType, StepType, StepNumber, Location, P, V2, V3, T, M2, M3
fields = [f for f in list(raw[2]) if f is not None]
n = raw[3]; flat = list(raw[4]); nf = len(fields)
rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n)]
result = rows
```

### Frame Property Modifiers (all frames)

```python
model.SetPresentUnits(6)
raw = model.DatabaseTables.GetTableForDisplayArray(
    "Frame Assignments - Property Modifiers", [], "All", 0, [], 0, [])
# Fields: Story, Label, UniqueName, AMod, A2Mod, A3Mod, JMod, I2Mod, I3Mod, MMod, WMod
fields = [f for f in list(raw[2]) if f is not None]
n = raw[3]; flat = list(raw[4]); nf = len(fields)
rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n)]
result = rows
```

### Load Combinations

```python
model.SetPresentUnits(6)
raw = model.DatabaseTables.GetTableForDisplayArray("Load Combination Definitions", [], "All", 0, [], 0, [])
# Fields: Name, Type, IsAuto, LoadName, SF, GUID, Notes
# Each combination spans multiple rows (one per load case component)
fields = [f for f in list(raw[2]) if f is not None]
n = raw[3]; flat = list(raw[4]); nf = len(fields)
rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n)]

# Group by combo name
combos = {}
for r in rows:
    name = r.get("Name") or r.get("combo_name", "")
    if name:
        combos.setdefault(name, [])
    if r.get("LoadName"):
        combos[name].append({"load": r["LoadName"], "SF": r.get("SF")})

result = combos
```

---

## Edit Pattern — Object Model Methods

> **CRITICAL:** `DatabaseTables.SetTableForEditingArray` **cannot be used** via comtypes late-binding. Passing Python lists to ByRef input SAFEARRAY parameters is not supported — you will get `TypeError: 'list' object cannot be interpreted as an integer`. Use individual object model methods instead.

### Story Heights

```python
model.SetPresentUnits(6)
model.SetModelIsLocked(False)  # DESTROYS RESULTS — only call when you intend to re-run

ret = model.Story.SetHeight("OHWR", 2.0)   # height in current units (m for kN_m)
print("SetHeight ret:", ret)  # 0 = success
```

### Frame Section Dimensions

```python
model.SetPresentUnits(6)
model.SetModelIsLocked(False)

# Rectangular: SetRectangle(Name, MatProp, t3_depth, t2_width)
ret = model.PropFrame.SetRectangle("FB1-400X800", "CON 4500 PSI", 0.85, 0.4)

# Circular: SetCircle(Name, MatProp, diameter)
ret = model.PropFrame.SetCircle("C1- dia 800", "CON 4500 PSI", 0.85)

# I-section: SetISection(Name, MatProp, t3, t2, tf, tw, t2b, tfb)
ret = model.PropFrame.SetISection("I-500x250x10x16", "A992Fy50", 0.5, 0.25, 0.016, 0.01, 0.25, 0.016)
```

### Frame Property Modifiers

```python
model.SetPresentUnits(6)
model.SetModelIsLocked(False)

# SetModifiers(Name, Value[8])
# Value order: [A, AS2, AS3, J, I22, I33, Mass, Weight]
# Typical beam: J=0.05, I22=I33=0.35
mods = [1.0, 1.0, 1.0, 0.05, 0.35, 0.35, 1.0, 1.0]
ret = model.FrameObj.SetModifiers("B12", mods)

# To apply to ALL frames in a group:
t = model.GroupDef.GetAssignments("1st Floor Ex Wall")
# t[0]=n, t[1]=obj_types_tuple, t[2]=obj_names_tuple, t[-1]=ret
n = t[0]
obj_names = list(t[2]) if n > 0 else []
obj_types = list(t[1]) if n > 0 else []
for i, name in enumerate(obj_names):
    if obj_types[i] == 2:  # 2 = Frame
        model.FrameObj.SetModifiers(name, mods)
```

### Area (Shell/Slab) Modifiers

```python
model.SetPresentUnits(6)
model.SetModelIsLocked(False)

# SetModifiers(Name, Value[10])
# Order: [f11, f22, f12, m11, m22, m12, v13, v23, mass, weight]
slab_mods = [1.0, 1.0, 1.0, 0.25, 0.25, 0.25, 1.0, 1.0, 1.0, 1.0]
ret = model.AreaObj.SetModifiers("SLAB1", slab_mods)
```

### Load Combinations

```python
model.SetPresentUnits(6)
model.SetModelIsLocked(False)

# Add combo (0=Linear Add, 1=Envelope, 2=ABS Add, 3=SRSS, 4=Range)
ret = model.RespCombo.Add("1.2D+1.6L", 0)

# Read combo case list
t = model.RespCombo.GetCaseList("1.2D+1.6L")
# Returns: (n, (type_codes,), (case_names,), (scale_factors,), ret)
# type_codes: 0=load case, 1=load combination
n = t[0]
case_names = list(t[2]) if n > 0 else []
scale_factors = list(t[3]) if n > 0 else []
print("Cases:", list(zip(case_names, scale_factors)))

# Delete combo
ret = model.RespCombo.Delete("1.2D+1.6L")

# NOTE: SetCaseList(Name, NumItems, CaseName[], SF[]) FAILS via comtypes
# — cannot pass Python list/tuple to SAFEARRAY ByRef input param.
# Add cases one at a time? Not supported by this API — see workaround below.
```

### Load Pattern Add/Delete

```python
model.SetPresentUnits(6)
model.SetModelIsLocked(False)

# Add(Name, MyType, SelfWTMult, AddLoadCase)
# MyType: 1=Dead, 3=Live, 5=Seismic, 6=Wind, etc.
ret = model.LoadPatterns.Add("WIND_Z", 6, 0.0, True)

# Set self-weight multiplier
ret = model.LoadPatterns.SetSelfWTMultiplier("Dead", 1.0)

# Delete
ret = model.LoadPatterns.Delete("WIND_Z")
```

---

## Edit Workflow — Unlock → Edit → Re-run

```python
model.SetPresentUnits(6)

# 1. Check current state
is_locked = model.GetModelIsLocked()
print("Locked:", is_locked)

# 2. Unlock (destroys analysis results!)
ret = model.SetModelIsLocked(False)

# 3. Make edits via object model
model.PropFrame.SetRectangle("FB1-400X800", "CON 4500 PSI", 0.85, 0.4)
model.FrameObj.SetModifiers("B12", [1,1,1,0.05,0.35,0.35,1,1])

# 4. Save
model.File.Save()

# 5. Re-run analysis
lc = list(model.LoadCases.GetNameList()[1])
for c in lc:
    model.Analyze.SetRunCaseFlag(c, True)
ret_run = model.Analyze.RunAnalysis()
print("RunAnalysis ret:", ret_run)  # 0 = success

# 6. Read results (model is now locked again)
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
model.Results.Setup.SetCaseSelectedForOutput("Dead")
br = model.Results.BaseReact()
result = {"run_ret": ret_run, "FZ": list(br[6])[0] if br[0] > 0 else None}
```

---

## ApplyEditedTables

`ApplyEditedTables` is used after staging edits via `SetTableForEditingArray`. Since `SetTableForEditingArray` does not work via comtypes late-binding, this is **not usable** in the MCP sandbox. Documented for reference only.

```python
# NOT USABLE in sandbox — included for reference
# r = model.DatabaseTables.ApplyEditedTables(True)
# Returns: (NumFatalErrors, NumWarnMsgs, NumInfoMsgs, AllMsg, ret)
# True = DoNotDeletePreviousResults (keep results if no geometry changes)
```

---

## Timeout Prevention

Large tables like `Element Forces - Beams` (50k+ rows) and `Joint Displacements` (34k+ rows) can exceed the MCP timeout (30s) when all cases are selected. Strategies:

```python
# 1. Select only one case at a time
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
model.Results.Setup.SetCaseSelectedForOutput("Dead")  # one case only

# 2. Filter by group (reduces rows dramatically)
raw = model.DatabaseTables.GetTableForDisplayArray(
    "Element Forces - Beams", [], "1st Floor Ex Wall", 0, [], 0, [])

# 3. Get fields and count first (no data)
raw = model.DatabaseTables.GetTableForDisplayArray("Element Forces - Beams", [], "All", 0, [], 0, [])
fields = [f for f in list(raw[2]) if f is not None]
n_rows = raw[3]
result = {"fields": fields, "n_rows": n_rows}  # return early, don't process flat data
```

---

## Notes

- **All values in `flat` are strings** — always convert: `float(r["VX"] or 0)`, `int(r["Mode"])`
- **`None` in flat data** is valid — means field not applicable for that row (e.g. StepNumber for static cases)
- **Result tables return 0 rows** if no output cases are selected — always call `Results.Setup` first
- **`Modal Participating Mass Ratios`** requires the exact modal case name in `SetCaseSelectedForOutput`
- **SetTableForEditingArray LIMITATION**: Cannot pass input arrays (FieldsKeyList, TableData) via comtypes IDispatch late-binding. Use individual object-model methods for all edits.
- **Verified on**: ETABS 23.2.0, TEP-MC1-DYNAMIC-304.EDB (9 stories, 1551 joints, 913 frames)
