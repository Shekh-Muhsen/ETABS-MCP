---
name: etabs-results
description: "Use when extracting analysis results: joint displacements, joint reactions, base shear, frame forces, area stresses, story drifts, modal periods, mass participation, pier/spandrel forces, and DatabaseTables bulk extraction."
---

# ETABS Results (`model.Results`)

Read `etabs-core` first. The model must be **locked** (analysis complete) before extracting results.

**Key convention:** All Results methods return tuples. Index `[0]` is `n` (number of result rows), the last index is `ret`. Lists of values start at index `[1]`.

---

## Setup — Select Output Cases

**Always call DeselectAllCasesAndCombosForOutput() before selecting cases.** Stale selections produce unexpected combined results.

> **CRITICAL distinction:**
> - Use `SetCaseSelectedForOutput(name)` for **load cases** (Dead, Modal, Spec X, EX, etc.)
> - Use `SetComboSelectedForOutput(name)` for **load combinations** (ENV-ULS, 1.2D+1.6L, etc.)
> These are different methods — mixing them up produces empty results.

```python
# Must be called before any results extraction
ret = model.Results.Setup.DeselectAllCasesAndCombosForOutput()

# Select load cases for output
ret = model.Results.Setup.SetCaseSelectedForOutput("Dead")
ret = model.Results.Setup.SetCaseSelectedForOutput("LL")
ret = model.Results.Setup.SetCaseSelectedForOutput("Modal")

# Select combinations for output (DIFFERENT method from cases!)
ret = model.Results.Setup.SetComboSelectedForOutput("1.2D+1.6L")
ret = model.Results.Setup.SetComboSelectedForOutput("ENV-ULS")

# Check if a case is selected
# GetCaseSelectedForOutput(Name) → [is_selected, ret]
t = model.Results.Setup.GetCaseSelectedForOutput("Dead")
is_selected = t[0]
print("Dead selected:", is_selected)
```

---

## Base Reactions

```python
ret = model.Results.Setup.DeselectAllCasesAndCombosForOutput()
ret = model.Results.Setup.SetCaseSelectedForOutput("Dead")

# BaseReact() → [n, LoadCase_t, StepType_t, StepNum_t, FX_t, FY_t, FZ_t,
#                MX_t, MY_t, MZ_t, gX_t, gY_t, gZ_t, ret]
# NOTE: gX, gY, gZ are scalars (not tuples) at indices [10], [11], [12]
# NOTE: directional cases (EX, EY) return 2 rows each (max/min step) — use max(abs(...))
t = model.Results.BaseReact()
n = t[0]
load_cases = list(t[1])
fx = list(t[4])
fy = list(t[5])
fz = list(t[6])
mx = list(t[7])
my = list(t[8])
mz = list(t[9])
ret = t[-1]

result = [
    {"case": load_cases[i], "FX": fx[i], "FY": fy[i], "FZ": fz[i],
     "MX": mx[i], "MY": my[i], "MZ": mz[i]}
    for i in range(n)
]
```

### Base Shear — Multiple Seismic Cases

```python
# Select EQX, EQY, Spec X, Spec Y at once
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
for c in ["EX", "EY", "Spec X", "Spec Y"]:
    model.Results.Setup.SetCaseSelectedForOutput(c)
br = model.Results.BaseReact()
n = br[0]
cases = [br[1][i] for i in range(n)]
FX    = [br[4][i] for i in range(n)]
FY    = [br[5][i] for i in range(n)]

# Max absolute base shear per case
summary = {}
for case in set(cases):
    vx = max(abs(FX[i]) for i in range(n) if cases[i] == case)
    vy = max(abs(FY[i]) for i in range(n) if cases[i] == case)
    summary[case] = {"max_FX": vx, "max_FY": vy}
result = summary
```

---

## Joint Displacements

```python
ret = model.Results.Setup.DeselectAllCasesAndCombosForOutput()
ret = model.Results.Setup.SetCaseSelectedForOutput("Dead")

# JointDispl(Name, ItemTypeElm) → [n, ObjName_t, ElmName_t, LoadCase_t, StepType_t,
#            StepNum_t, U1_t, U2_t, U3_t, R1_t, R2_t, R3_t, ret]
# ItemTypeElm: 0=ObjectElm (single object), 1=Element, 2=Group/SelectedObjects
# VERIFIED: itemType=0 with a specific joint name works reliably.
# WARNING: itemType=1 with "All" or a group name returns EMPTY — use single object (itemType=0)
#          or DatabaseTables("Joint Displacements") for bulk extraction.

# All joints for selected cases (may return empty — use DatabaseTables instead)
t = model.Results.JointDispl("", 2)
n = t[0]
obj_names = list(t[1])
load_cases = list(t[3])
u1 = list(t[6])   # translation along local 1 (typically X)
u2 = list(t[7])   # translation along local 2 (typically Y)
u3 = list(t[8])   # translation along local 3 (typically Z)
r1 = list(t[9])
r2 = list(t[10])
r3 = list(t[11])
ret = t[-1]

result = [
    {"joint": obj_names[i], "case": load_cases[i],
     "U1": u1[i], "U2": u2[i], "U3": u3[i], "R1": r1[i], "R2": r2[i], "R3": r3[i]}
    for i in range(n)
]
```

### Max Displacement at a Specific Joint — Verified Pattern

```python
ret = model.Results.Setup.DeselectAllCasesAndCombosForOutput()
ret = model.Results.Setup.SetCaseSelectedForOutput("Dead")

# itemType=0 (single object) — CONFIRMED WORKING
t = model.Results.JointDispl("POINT_NAME", 0)
# Returns: [n, (ObjName,), (ElmName,), (Case,), (StepType,), (StepNum,), (U1,), (U2,), (U3,), (R1,), (R2,), (R3,), ret]
# U1 at [6], U2 at [7], U3 at [8]
n = t[0]
if n > 0:
    u1 = list(t[6])
    u2 = list(t[7])
    u3 = list(t[8])
    result = {"joint": "POINT_NAME", "U1": u1, "U2": u2, "U3": u3, "max_U3": min(u3)}
```

---

## Joint Reactions

```python
ret = model.Results.Setup.DeselectAllCasesAndCombosForOutput()
ret = model.Results.Setup.SetCaseSelectedForOutput("Dead")

# JointReact(Name, ItemTypeElm) → [n, ObjName_t, ElmName_t, LoadCase_t, StepType_t,
#            StepNum_t, F1_t, F2_t, F3_t, M1_t, M2_t, M3_t, ret]

# All support reactions
t = model.Results.JointReact("", 2)
n = t[0]
obj_names = list(t[1])
load_cases = list(t[3])
f1 = list(t[6])
f2 = list(t[7])
f3 = list(t[8])
m1 = list(t[9])
m2 = list(t[10])
m3 = list(t[11])
ret = t[-1]

result = [
    {"joint": obj_names[i], "case": load_cases[i],
     "F1": f1[i], "F2": f2[i], "F3": f3[i]}
    for i in range(n)
]

# Total base shear
total_F1 = sum(f1)
total_F2 = sum(f2)
total_F3 = sum(f3)
print("Base shear FX:", total_F1, "FY:", total_F2, "FZ:", total_F3)
```

---

## Frame Forces

> **CRITICAL:** `FrameForce` with group itemType=1 returns **empty** results. Always use itemType=0 (single object) or DatabaseTables for bulk extraction.
> For **combinations** use `SetComboSelectedForOutput`; for **load cases** use `SetCaseSelectedForOutput`.

```python
ret = model.Results.Setup.DeselectAllCasesAndCombosForOutput()
ret = model.Results.Setup.SetCaseSelectedForOutput("Dead")      # for load cases
ret = model.Results.Setup.SetComboSelectedForOutput("ENV-ULS")  # for combinations

# FrameForce(Name, itemType) — use itemType=0 (single object) only
# Returns: [n, (ObjName,), (ElmName,), (PointElm,), (Case,), (StepType,), (StepNum,),
#            (P,), (V2,), (V3,), (T,), (M2,), (M3,), ret]
# P at [7], V2 at [8], V3 at [9], T at [10], M2 at [11], M3 at [12]

t = model.Results.FrameForce("FRAME_NAME", 0)  # itemType=0 — CONFIRMED WORKING
n = t[0]
obj_names = list(t[1])
load_cases = list(t[4])   # index 4 (not 5) — PointElm is at [3]
P = list(t[7])
V2 = list(t[8])
V3 = list(t[9])
T_torsion = list(t[10])
M2 = list(t[11])
M3 = list(t[12])
ret = t[-1]

result = [
    {"frame": obj_names[i], "case": load_cases[i],
     "P": P[i], "V2": V2[i], "V3": V3[i], "T": T_torsion[i], "M2": M2[i], "M3": M3[i]}
    for i in range(n)
]
```

### Frame Forces — Bulk via DatabaseTables (Preferred for All Frames)

```python
# Must pre-select output cases first
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
model.Results.Setup.SetComboSelectedForOutput("ENV-ULS")

raw = model.DatabaseTables.GetTableForDisplayArray("Frame Forces - Beams", [], "All", 0, [], 0, [])
fields = [f for f in list(raw[2]) if f is not None]
n_rows = raw[3]
flat = list(raw[4])
nf = len(fields)
rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n_rows)]
result = rows
```

---

## Area Stresses

```python
ret = model.Results.Setup.DeselectAllCasesAndCombosForOutput()
ret = model.Results.Setup.SetCaseSelectedForOutput("Dead")

# AreaStress(Name, ItemTypeElm) → [n, ObjName_t, ElmName_t, PointElm_t, LoadCase_t,
#   StepType_t, StepNum_t, S11_t, S22_t, S12_t, SMax_t, SMin_t, SAngle_t, SVM_t,
#   T13_t, T23_t, SMaxTop_t, SMinTop_t, ret]

t = model.Results.AreaStress("1", 0)
n = t[0]
obj_names = list(t[1])
load_cases = list(t[4])
S11 = list(t[7])
S22 = list(t[8])
S12 = list(t[9])

result = [
    {"area": obj_names[i], "case": load_cases[i],
     "S11": S11[i], "S22": S22[i], "S12": S12[i]}
    for i in range(n)
]
```

### Shell Area Stresses (Top/Bottom)

```python
# AreaStressShell(Name, ItemTypeElm) → [n, ObjName_t, ElmName_t, PointElm_t, LoadCase_t,
#   StepType_t, StepNum_t, S11Top_t, S22Top_t, S12Top_t, S11Bot_t, S22Bot_t, S12Bot_t,
#   SMaxTop_t, SMinTop_t, SAngleTop_t, SMaxBot_t, SMinBot_t, SAngleBot_t,
#   SVMaxTop_t, SVMaxBot_t, SAngleVTop_t, SAngleVBot_t, ret]

t = model.Results.AreaStressShell("1", 0)
n = t[0]
S11Top = list(t[7])
S22Top = list(t[8])
S11Bot = list(t[10])
S22Bot = list(t[11])
result = [{"S11_top": S11Top[i], "S22_top": S22Top[i], "S11_bot": S11Bot[i], "S22_bot": S22Bot[i]}
          for i in range(n)]
```

---

## Story Drifts

```python
ret = model.Results.Setup.DeselectAllCasesAndCombosForOutput()
for c in ["Spec X", "Spec Y", "EX", "EY"]:
    model.Results.Setup.SetCaseSelectedForOutput(c)

# StoryDrifts() → [n, Story_t, LoadCase_t, StepType_t, StepNum_t,
#                   Direction_t, Drift_t, Label_t, X_t, Y_t, ret]
# Story at [1], Case at [2], Direction at [5], Drift at [6]
t = model.Results.StoryDrifts()
n = t[0]
story = list(t[1])
load_cases = list(t[2])
direction = list(t[5])
drift = list(t[6])
ret = t[-1]

rows = [
    {"story": story[i], "case": load_cases[i],
     "dir": direction[i], "drift": drift[i]}
    for i in range(n)
]

# Maximum drift per story and direction
max_drift = max(drift) if n > 0 else 0
print("Max drift:", max_drift)
# Real ETABS 23.2.0 result example: max drift 0.0278 at OHWR story, EY direction Y

result = {"rows": rows, "max_drift": max_drift}
```

---

## Modal Periods and Frequencies

```python
ret = model.Results.Setup.DeselectAllCasesAndCombosForOutput()
ret = model.Results.Setup.SetCaseSelectedForOutput("MODAL CASE")  # use actual case name

# ModalPeriod() → [n, LoadCase_t, StepType_t, StepNum_t, Period_t, Frequency_t,
#                   CircFreq_t, EigenValue_t, ret]
# Period at [4], Frequency at [5], CircFreq at [6], EigenValue at [7]
t = model.Results.ModalPeriod()
n = t[0]
load_cases = list(t[1])
step_num = list(t[3])
period = list(t[4])
freq = list(t[5])
circ_freq = list(t[6])
ret = t[-1]

result = [
    {"mode": int(step_num[i]), "period_s": period[i],
     "frequency_hz": freq[i], "circ_freq": circ_freq[i]}
    for i in range(n)
]
# Real ETABS 23.2.0 example: Mode 1 T=1.345s, Mode 2 T=1.152s, Mode 3 T=0.915s
```

---

## Modal Mass Participation Ratios

```python
ret = model.Results.Setup.DeselectAllCasesAndCombosForOutput()
ret = model.Results.Setup.SetCaseSelectedForOutput("Modal")

# ModalParticipatingMassRatios() → [n, LoadCase_t, StepType_t, StepNum_t, Period_t,
#   UX_t, UY_t, UZ_t, SumUX_t, SumUY_t, SumUZ_t,
#   RX_t, RY_t, RZ_t, SumRX_t, SumRY_t, SumRZ_t, ret]
t = model.Results.ModalParticipatingMassRatios()
n = t[0]
step_num = list(t[3])
period = list(t[4])
UX = list(t[5])
UY = list(t[6])
SumUX = list(t[8])
SumUY = list(t[9])
SumUZ = list(t[10])
ret = t[-1]

result = [
    {"mode": int(step_num[i]), "period": period[i],
     "UX": UX[i], "UY": UY[i], "SumUX": SumUX[i], "SumUY": SumUY[i]}
    for i in range(n)
]

# Find mode reaching 90% mass in X
for i in range(n):
    if SumUX[i] >= 0.90:
        print("90% UX reached at mode", int(step_num[i]))
        break
```

---

## Pier Forces

```python
ret = model.Results.Setup.DeselectAllCasesAndCombosForOutput()
ret = model.Results.Setup.SetComboSelectedForOutput("ENV-ULS")  # use SetComboSelectedForOutput for combos

# PierForce() → [n, StoryName_t, PierName_t, LoadCase_t, StepType_t, StepNum_t,
#                 Location_t, P_t, V2_t, V3_t, T_t, ret]
# VERIFIED: 11 elements total (no M2, M3 in pier forces — only P, V2, V3, T)
# P at [7], V2 at [8], V3 at [9], T at [10]
t = model.Results.PierForce()
n = t[0]
story_names = list(t[1])
pier_names = list(t[2])
load_cases = list(t[3])
location = list(t[6])
P = list(t[7])
V2 = list(t[8])
V3 = list(t[9])
T = list(t[10])
ret = t[-1]

result = [
    {"story": story_names[i], "pier": pier_names[i], "case": load_cases[i],
     "location": location[i], "P": P[i], "V2": V2[i], "V3": V3[i], "T": T[i]}
    for i in range(n)
]
```

---

## Spandrel Forces

```python
ret = model.Results.Setup.DeselectAllCasesAndCombosForOutput()
ret = model.Results.Setup.SetCaseSelectedForOutput("Dead")

# SpandrelForce() → [n, StoryName_t, SpandrelName_t, LoadCase_t, StepType_t, StepNum_t,
#                     Location_t, P_t, V2_t, V3_t, T_t, M2_t, M3_t, ret]
t = model.Results.SpandrelForce()
n = t[0]
story_names = list(t[1])
spandrel_names = list(t[2])
P = list(t[7])
M3 = list(t[12])
ret = t[-1]

result = [
    {"story": story_names[i], "spandrel": spandrel_names[i], "P": P[i], "M3": M3[i]}
    for i in range(n)
]
```

---

## DatabaseTables — Primary Alternative for Bulk Extraction

Use DatabaseTables as the **preferred approach** for extracting large result sets, all load cases at once, or when the `model.Results` API returns empty/unexpected results.

> **CRITICAL:** DatabaseTables for **result tables** (Story Forces, Story Drifts, Frame Forces, etc.) only returns data when output cases are pre-selected via `Results.Setup`. Model definition tables (materials, sections) do not require this.

```python
# MUST select output cases first for result tables
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
model.Results.Setup.SetComboSelectedForOutput("ENV-ULS")  # for combos
# model.Results.Setup.SetCaseSelectedForOutput("Spec X")  # for cases

# GetTableForDisplayArray(TableName, [], GroupName, 0, [], 0, [])
# Returns: [ret, version, fields_tuple, n_rows, flat_data_tuple, ret2]

raw = model.DatabaseTables.GetTableForDisplayArray(
    "Story Forces", [], "All", 0, [], 0, []
)
fields = [f for f in list(raw[2]) if f is not None]
n_rows = raw[3]
flat = list(raw[4])
nf = len(fields)

rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n_rows)]
result = rows
# Fields: ["Story","OutputCase","CaseType","StepType","Location","P","VX","VY","T","MX","MY"]
```

### Useful Table Names for Results

| Table | Content |
|-------|---------|
| `"Story Forces"` | Story shears and overturning moments by level |
| `"Story Drifts"` | Story drift ratios by load case |
| `"Joint Displacements"` | All joint displacement results |
| `"Frame Forces - Beams"` | Beam internal forces at all stations |
| `"Frame Forces - Columns"` | Column internal forces |
| `"Frame Forces - Braces"` | Brace internal forces |
| `"Modal Participating Mass Ratios"` | Modal mass participation table |
| `"Modal Periods And Frequencies"` | Period, frequency per mode |
| `"Base Reactions"` | Global base reactions |
| `"Pier Forces"` | Pier shear and moment results |
| `"Spandrel Forces"` | Spandrel results |

---

## Complete Results Extraction Workflow

```python
# Verify model is locked (analysis done)
is_locked = model.GetModelIsLocked()
if not is_locked:
    result = {"error": "Analysis not run — model is unlocked"}
else:
    ret = model.SetPresentUnits(6)  # kN_m for results

    # Setup
    ret = model.Results.Setup.DeselectAllCasesAndCombosForOutput()
    ret = model.Results.Setup.SetCaseSelectedForOutput("Dead")
    ret = model.Results.Setup.SetCaseSelectedForOutput("Modal")

    # Base reactions
    br = model.Results.BaseReact()
    n_br = br[0]
    base_reactions = [
        {"case": list(br[1])[i], "FX": list(br[4])[i],
         "FY": list(br[5])[i], "FZ": list(br[6])[i]}
        for i in range(n_br)
    ]

    # Modal periods
    mp = model.Results.ModalPeriod()
    n_mp = mp[0]
    periods = [
        {"mode": int(list(mp[3])[i]), "period": list(mp[4])[i]}
        for i in range(min(n_mp, 6))
    ]

    # Story drifts (select RS cases)
    ret = model.Results.Setup.DeselectAllCasesAndCombosForOutput()
    ret = model.Results.Setup.SetCaseSelectedForOutput("RSX")
    sd = model.Results.StoryDrifts()
    n_sd = sd[0]
    max_drift = max(list(sd[6])) if n_sd > 0 else 0

    result = {
        "base_reactions": base_reactions,
        "modal_periods": periods,
        "max_story_drift": max_drift,
    }
```
