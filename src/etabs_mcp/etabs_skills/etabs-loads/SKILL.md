---
name: etabs-loads
description: "Use when defining load patterns, load cases (static, modal, response spectrum), load combinations, and applying loads to joints, frames, and areas. Covers joint forces, frame distributed/point loads, area uniform loads, self-weight, and temperature loads."
---

# ETABS Loads

Read `etabs-core` first for sandbox rules and return value conventions.

---

## Load Patterns (`model.LoadPatterns`)

Load patterns define the *type* of loading (Dead, Live, Wind, Seismic, etc.). Each pattern has a self-weight multiplier.

### Load Pattern Type Codes

| Code | Pattern Type |
|------|-------------|
| 1 | Dead |
| 2 | SuperDead |
| 3 | Live |
| 4 | ReducibleLive |
| 5 | Quake (seismic) |
| 6 | Wind |
| 7 | Snow |
| 8 | Other |
| 9 | Move |
| 10 | Temperature |
| 11 | RoofLive |
| 12 | Notional |

### Add Load Patterns

```python
ret = model.SetModelIsLocked(False)
ret = model.SetPresentUnits(6)  # kN_m

# Add(Name, MyType, SelfWTMultiplier=0, AddLoadCase=True) → ret
ret = model.LoadPatterns.Add("Dead", 1, 1.0, True)     # Dead with self-weight
ret = model.LoadPatterns.Add("SDL", 2, 0.0, True)      # Super Dead (finishes, etc.)
ret = model.LoadPatterns.Add("LL", 3, 0.0, True)       # Live
ret = model.LoadPatterns.Add("LL_Roof", 11, 0.0, True) # Roof Live
ret = model.LoadPatterns.Add("WX+", 6, 0.0, True)      # Wind X+
ret = model.LoadPatterns.Add("WX-", 6, 0.0, True)      # Wind X-
ret = model.LoadPatterns.Add("WY+", 6, 0.0, True)
ret = model.LoadPatterns.Add("EQX", 5, 0.0, True)      # Seismic X
ret = model.LoadPatterns.Add("EQY", 5, 0.0, True)      # Seismic Y
```

### List Load Patterns

```python
# GetNameList() → [count, (names_tuple), ret]
t = model.LoadPatterns.GetNameList()
n = t[0]
names = list(t[1]) if n > 0 else []
result = names
```

### Self-Weight Multiplier

```python
# GetSelfWtMultiplier(Name) → [multiplier, ret]
t = model.LoadPatterns.GetSelfWtMultiplier("Dead")
mult = t[0]
print("Self-weight multiplier:", mult)

# SetSelfWtMultiplier(Name, Multiplier) → ret
ret = model.LoadPatterns.SetSelfWtMultiplier("Dead", 1.0)
```

### Delete a Load Pattern

```python
ret = model.LoadPatterns.Delete("WX+")
```

---

## Load Cases (`model.LoadCases`)

### List Load Cases

```python
# GetNameList() → [count, (names_tuple), ret]
t = model.LoadCases.GetNameList()
names = list(t[1]) if t[0] > 0 else []
result = names
```

### Get Load Case Type

```python
# GetTypeOAPI(Name) → [typeCode, iAuto, ret]
# typeCode: 1=StaticLinear, 2=StaticNonlinear, 3=Modal, 5=ResponseSpectrum, etc.
# iAuto: 0=not auto-created, 1=auto-created from load pattern
t = model.LoadCases.GetTypeOAPI("Dead")
type_code = t[0]
i_auto = t[1]
print("Case type:", type_code, "iAuto:", i_auto)
```

### Static Linear Load Case

```python
# StaticLinear.SetCase(Name) → ret — creates the case
ret = model.LoadCases.StaticLinear.SetCase("Dead")
ret = model.LoadCases.StaticLinear.SetCase("SDL")
ret = model.LoadCases.StaticLinear.SetCase("LL")
ret = model.LoadCases.StaticLinear.SetCase("WX+")

# StaticLinear.SetLoads(Name, NumberLoads, LoadType[], LoadName[], SF[]) → ret
# LoadType: "Load" = load pattern, "Accel" = acceleration
ret = model.LoadCases.StaticLinear.SetLoads("Dead", 1, ["Load"], ["Dead"], [1.0])
ret = model.LoadCases.StaticLinear.SetLoads("SDL", 1, ["Load"], ["SDL"], [1.0])
ret = model.LoadCases.StaticLinear.SetLoads("LL", 1, ["Load"], ["LL"], [1.0])
ret = model.LoadCases.StaticLinear.SetLoads("WX+", 1, ["Load"], ["WX+"], [1.0])

# Get static linear loads
# StaticLinear.GetLoads(Name) → [n, LoadType_tuple, LoadName_tuple, SF_tuple, ret]
t = model.LoadCases.StaticLinear.GetLoads("Dead")
n = t[0]
load_types = list(t[1])
load_names = list(t[2])
sfs = list(t[3])
```

### Modal Eigen Case

```python
# Modal.SetCase(Name) → ret
ret = model.LoadCases.Modal.SetCase("Modal")

# Set number of modes
# ModalEigen.SetNumberModes(Name, MaxModes, MinModes) → ret
ret = model.LoadCases.ModalEigen.SetNumberModes("Modal", 12, 1)
```

### Response Spectrum Case

```python
# ResponseSpectrum.SetCase(Name) → ret
ret = model.LoadCases.ResponseSpectrum.SetCase("RSX")
ret = model.LoadCases.ResponseSpectrum.SetCase("RSY")

# ResponseSpectrum.SetLoads(Name, n, LoadName[], Func[], SF[], Ang[], CSys[]) → ret
# LoadName: direction ("U1", "U2", "U3")
# Func: spectrum function name
# SF: scale factor (typically g = 9.81 for kN_m)
# Ang: angle of loading
# CSys: coordinate system

ret = model.LoadCases.ResponseSpectrum.SetLoads(
    "RSX", 1,
    ["U1"],          # X direction
    ["RS_Func"],     # spectrum function name
    [9.81],          # scale factor = g
    [0.0],           # angle
    ["Global"],      # coordinate system
)
ret = model.LoadCases.ResponseSpectrum.SetLoads(
    "RSY", 1,
    ["U2"],
    ["RS_Func"],
    [9.81],
    [0.0],
    ["Global"],
)

# Get RS loads
# ResponseSpectrum.GetLoads(Name) → [n, LoadNames_t, Funcs_t, SFs_t, CSys_t, Angles_t, ret]
# Note: CSys is at index [4], Angles at index [5] (order differs from SetLoads)
t = model.LoadCases.ResponseSpectrum.GetLoads("RSX")
n = t[0]
load_names = list(t[1])
funcs = list(t[2])
sfs = list(t[3])
csys_list = list(t[4])    # CSys strings
angles = list(t[5])       # angles
```

### Seismic 85% Scaling — Modify RS Scale Factor

```python
# Verified pattern for applying the 85% base shear scaling rule (ASCE 7):
# Must read current SF, multiply by scale factor, then SetLoads with new SF.
# Do this AFTER reading base shears (while locked), BEFORE unlocking.

# Step 1: Read base shears (model must be locked with results)
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
for c in ["EX", "EY", "Spec X", "Spec Y"]:
    model.Results.Setup.SetCaseSelectedForOutput(c)
br = model.Results.BaseReact()
n = br[0]
cases = list(br[1])
FX = list(br[4])
FY = list(br[5])
# NOTE: directional cases return 2 rows each (top/bottom of step) — use max abs
V_EX = max(abs(FX[i]) for i in range(n) if cases[i] == "EX")
V_EY = max(abs(FY[i]) for i in range(n) if cases[i] == "EY")
V_SX = max(abs(FX[i]) for i in range(n) if cases[i] == "Spec X")
V_SY = max(abs(FY[i]) for i in range(n) if cases[i] == "Spec Y")

Sx = (0.85 * V_EX) / V_SX   # scale factor to apply to Spec X
Sy = (0.85 * V_EY) / V_SY

# Step 2: Unlock model (destroys results — that's OK, we already read shears)
ret = model.SetModelIsLocked(False)

# Step 3: Multiply existing scale factors
rs_x = model.LoadCases.ResponseSpectrum.GetLoads("Spec X")
n_x = rs_x[0]
new_SFs = [rs_x[3][i] * Sx for i in range(n_x)]
model.LoadCases.ResponseSpectrum.SetLoads(
    "Spec X", n_x, list(rs_x[1]), list(rs_x[2]), new_SFs, list(rs_x[4]), list(rs_x[5]))

rs_y = model.LoadCases.ResponseSpectrum.GetLoads("Spec Y")
n_y = rs_y[0]
new_SFs_y = [rs_y[3][i] * Sy for i in range(n_y)]
model.LoadCases.ResponseSpectrum.SetLoads(
    "Spec Y", n_y, list(rs_y[1]), list(rs_y[2]), new_SFs_y, list(rs_y[4]), list(rs_y[5]))

# Step 4: Re-run analysis
ret = model.Analyze.RunAnalysis()
result = {"Sx": Sx, "Sy": Sy, "rerun_success": ret == 0}
```

### Enable / Disable Cases for Analysis

```python
# SetRunCaseFlag(Name, Run, applyAll=False) → ret
# Deselect all cases first
ret = model.LoadCases.SetRunCaseFlag("", False, True)   # applyAll=True clears all

# Select specific cases to run
ret = model.LoadCases.SetRunCaseFlag("Dead", True)
ret = model.LoadCases.SetRunCaseFlag("SDL", True)
ret = model.LoadCases.SetRunCaseFlag("LL", True)
ret = model.LoadCases.SetRunCaseFlag("Modal", True)
ret = model.LoadCases.SetRunCaseFlag("RSX", True)
```

---

## Load Combinations (`model.LoadCombos` / `model.RespCombo`)

### Combo Type Codes

| Code | Type |
|------|------|
| 0 | LinearAdd |
| 1 | Envelope |
| 2 | AbsoluteAdd |
| 3 | SRSS |
| 4 | RangeAdd |

### Add Combinations

```python
# Add(Name, ComboType) → ret
ret = model.LoadCombos.Add("1.4D", 0)                  # LinearAdd
ret = model.LoadCombos.Add("1.2D+1.6L", 0)
ret = model.LoadCombos.Add("1.2D+1.0L+1.0EQX", 0)
ret = model.LoadCombos.Add("ENVELOPE", 1)              # Envelope

# SetCaseList(Name, NumberItems, CNameType[], CName[], SF[]) → ret
# CNameType: "LoadCase" or "LoadCombo"
ret = model.LoadCombos.SetCaseList(
    "1.4D", 1,
    ["LoadCase"],
    ["Dead"],
    [1.4],
)
ret = model.LoadCombos.SetCaseList(
    "1.2D+1.6L", 2,
    ["LoadCase", "LoadCase"],
    ["Dead", "LL"],
    [1.2, 1.6],
)
ret = model.LoadCombos.SetCaseList(
    "1.2D+1.0L+1.0EQX", 3,
    ["LoadCase", "LoadCase", "LoadCase"],
    ["Dead", "LL", "RSX"],
    [1.2, 1.0, 1.0],
)
```

### List and Inspect Combinations

```python
# GetNameList() → [count, (names_tuple), ret]
t = model.LoadCombos.GetNameList()
names = list(t[1]) if t[0] > 0 else []

# RespCombo.GetCaseList(Name) → [n, (typeCodes_t), (names_t), (SFs_t), ret]
# typeCodes: 0=LoadCase, 1=LoadCombo (integers, not strings)
t2 = model.RespCombo.GetCaseList("1.2D+1.6L")
n = t2[0]
type_codes = list(t2[1])  # 0=LoadCase, 1=LoadCombo
case_names = list(t2[2])
sfs = list(t2[3])
result = [{"type_code": type_codes[i], "case": case_names[i], "SF": sfs[i]} for i in range(n)]
```

### Delete a Combination

```python
ret = model.LoadCombos.Delete("ENVELOPE")
```

---

## Joint Loads (`model.PointObj`)

### Point Force on Joint

```python
ret = model.SetPresentUnits(6)  # kN_m — forces in kN, moments in kN·m

# SetLoadForce(Name, LoadPat, Value[6], Replace=True, CSys="Global", ItemType=0) → ret
# Value = [F1(X), F2(Y), F3(Z), M1(RX), M2(RY), M3(RZ)]

# 100 kN downward (−Z) at joint "1"
ret = model.PointObj.SetLoadForce(
    "1", "Dead",
    [0.0, 0.0, -100.0, 0.0, 0.0, 0.0],
    True, "Global", 0,
)

# Moment at joint
ret = model.PointObj.SetLoadForce(
    "2", "Dead",
    [0.0, 0.0, 0.0, 0.0, 50.0, 0.0],  # 50 kN·m about Y
    True, "Global", 0,
)
```

### Joint Settlement / Prescribed Displacement

```python
# SetLoadDispl(Name, LoadPat, Value[6], Replace=True, CSys="Global", ItemType=0) → ret
# Value = [U1, U2, U3, R1, R2, R3] — displacements in metres, rotations in radians
ret = model.PointObj.SetLoadDispl(
    "1", "Dead",
    [0.0, 0.0, -0.025, 0.0, 0.0, 0.0],  # 25mm settlement
    True, "Global", 0,
)
```

### Delete Joint Loads

```python
ret = model.PointObj.DeleteLoadForce("1", "Dead")
```

---

## Frame Loads (`model.FrameObj`)

### Distributed Load on Frame

```python
ret = model.SetPresentUnits(6)  # forces in kN/m

# SetLoadDistributed(Name, LoadPat, MyType, Dir, Dist1, Dist2, Val1, Val2,
#                    CSys="Global", RelDist=True, Replace=True, ItemType=0) → ret
#
# MyType: 1=Force, 2=Moment
# Dir: 1=Local1, 2=Local2, 3=Local3, 4=X, 5=Y, 6=Z,
#      7=ProjX, 8=ProjY, 9=ProjZ, 10=GravityScale
# RelDist: True = Dist1/Dist2 are 0-to-1 fractions; False = absolute metres

# Uniform gravity load on beam: 20 kN/m downward (Z)
ret = model.FrameObj.SetLoadDistributed(
    "1",    # frame name
    "LL",   # load pattern
    1,      # Force
    6,      # Z direction
    0.0,    # start (relative)
    1.0,    # end (relative)
    -20.0,  # start value (kN/m, negative = downward)
    -20.0,  # end value
    "Global", True, True, 0,
)

# Triangular load (0 to 30 kN/m)
ret = model.FrameObj.SetLoadDistributed(
    "2", "Dead", 1, 6, 0.0, 1.0, 0.0, -30.0,
    "Global", True, True, 0,
)

# Partial UDL from 0.25 to 0.75 of span
ret = model.FrameObj.SetLoadDistributed(
    "3", "LL", 1, 6, 0.25, 0.75, -15.0, -15.0,
    "Global", True, True, 0,
)

# Apply same load to all frames in a group
ret = model.FrameObj.SetLoadDistributed(
    "Beams", "LL", 1, 6, 0.0, 1.0, -20.0, -20.0,
    "Global", True, True, 1,  # ItemType=1=Group
)
```

### Point Load on Frame

```python
# SetLoadPoint(Name, LoadPat, MyType, Dir, Dist, Val,
#              CSys="Global", RelDist=True, Replace=True, ItemType=0) → ret
# 50 kN at midspan
ret = model.FrameObj.SetLoadPoint("1", "Dead", 1, 6, 0.5, -50.0)
```

### Temperature Load on Frame

```python
# SetLoadTemperature(Name, LoadPat, MyType, Val, PatternName="", Replace=True, ItemType=0) → ret
# MyType: 1=Temperature (uniform), 2=Gradient local 2, 3=Gradient local 3
ret = model.FrameObj.SetLoadTemperature("1", "Dead", 1, 30.0)  # +30°C uniform
```

### Delete Frame Loads

```python
ret = model.FrameObj.DeleteLoad("1", "LL")
```

---

## Area Loads (`model.AreaObj`)

### Uniform Load on Area (Pressure)

```python
ret = model.SetPresentUnits(6)  # kN/m²

# SetLoadUniform(Name, LoadPat, Value, Dir, Replace=True, CSys="Global", ItemType=0) → ret
# Dir: 1=Local1, 2=Local2, 3=Local3, 4=X, 5=Y, 6=Z,
#      7=ProjX, 8=ProjY, 9=ProjZ (use 6 or 9 for gravity on slabs)

# Gravity load on slab (5 kN/m² downward)
ret = model.AreaObj.SetLoadUniform("1", "LL", -5.0, 6)

# Wind pressure on wall (positive = inward)
ret = model.AreaObj.SetLoadUniform("2", "WX+", 1.5, 4)  # X direction

# Apply to all areas in a group
ret = model.AreaObj.SetLoadUniform("Slabs", "LL", -5.0, 6, True, "Global", 1)
```

### Uniform Load Distributed to Frames (Slab Load → Beams)

```python
# SetLoadUniformToFrame(Name, LoadPat, Value, Dir, DistType, Replace=True, ItemType=0) → ret
# DistType: 1=One-Way, 2=Two-Way
# Distributes area load to surrounding frame elements

ret = model.AreaObj.SetLoadUniformToFrame(
    "1", "SDL", -2.0, 6, 2, True, 0  # 2kN/m² SDL, two-way distribution
)
```

### Delete Area Loads

```python
ret = model.AreaObj.DeleteLoadUniform("1", "LL")
```

---

## Complete Load Setup Example

```python
ret = model.SetModelIsLocked(False)
ret = model.SetPresentUnits(6)  # kN_m

# --- Load Patterns ---
ret = model.LoadPatterns.Add("Dead", 1, 1.0, True)
ret = model.LoadPatterns.Add("SDL", 2, 0.0, True)
ret = model.LoadPatterns.Add("LL", 3, 0.0, True)
ret = model.LoadPatterns.Add("EQX", 5, 0.0, True)
ret = model.LoadPatterns.Add("EQY", 5, 0.0, True)

# --- Load Cases ---
ret = model.LoadCases.StaticLinear.SetCase("Dead")
ret = model.LoadCases.StaticLinear.SetLoads("Dead", 1, ["Load"], ["Dead"], [1.0])
ret = model.LoadCases.StaticLinear.SetCase("SDL")
ret = model.LoadCases.StaticLinear.SetLoads("SDL", 1, ["Load"], ["SDL"], [1.0])
ret = model.LoadCases.StaticLinear.SetCase("LL")
ret = model.LoadCases.StaticLinear.SetLoads("LL", 1, ["Load"], ["LL"], [1.0])
ret = model.LoadCases.Modal.SetCase("Modal")
ret = model.LoadCases.ModalEigen.SetNumberModes("Modal", 12, 1)

# --- Combinations ---
ret = model.LoadCombos.Add("1.2D+1.6L", 0)
ret = model.LoadCombos.SetCaseList(
    "1.2D+1.6L", 3,
    ["LoadCase", "LoadCase", "LoadCase"],
    ["Dead", "SDL", "LL"],
    [1.2, 1.2, 1.6],
)

# --- Apply Loads: Slab pressure ---
area_t = model.AreaObj.GetNameList()
area_names = list(area_t[1])
for an in area_names:
    ret = model.AreaObj.SetLoadUniform(an, "SDL", -2.0, 6)  # 2 kN/m² SDL
    ret = model.AreaObj.SetLoadUniform(an, "LL", -3.0, 6)   # 3 kN/m² LL

lp_t = model.LoadPatterns.GetNameList()
lc_t = model.LoadCases.GetNameList()
co_t = model.LoadCombos.GetNameList()

result = {
    "load_patterns": list(lp_t[1]),
    "load_cases": list(lc_t[1]),
    "combos": list(co_t[1]),
}
```
