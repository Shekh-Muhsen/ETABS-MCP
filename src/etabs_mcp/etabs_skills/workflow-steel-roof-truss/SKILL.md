---
name: workflow-steel-roof-truss
description: "Complete analysis workflow for 3D steel roof truss / space frame structures: sections → geometry → loads → load cases → analysis → frame forces → steel design (DCR) → serviceability deflection check. All API calls VERIFIED against ETABS 23.2.0."
---

# Workflow: Steel Roof Truss / Space Frame — Complete Analysis

Covers the full pipeline for a 3D steel roof structure (parallel trusses + purlins + end bracing).
Read `etabs-core` first for sandbox rules and unit conventions.

---

## Workflow Map (8 Steps)

```
1. SECTIONS     → PropFrame.SetPipe / SetRectangle / SetISection
2. GEOMETRY     → PointObj.AddCartesian + FrameObj.AddByPoint (parallel trusses + purlins)
3. LOADS        → LoadPatterns.Add + FrameObj.SetLoadDistributed
4. LOAD CASES   → LoadCases.StaticLinear.SetCase + SetLoads
5. ANALYSIS     → Analyze.RunAnalysis()  [model auto-locks after]
6. REACTIONS    → Results.BaseReact()    [verify total FZ = applied load]
7. FRAME FORCES → DatabaseTables("Element Forces - Beams")  [NOT "Frame Forces - Beams"]
8. STEEL DESIGN → DesignSteel.SetCode + StartDesign + DatabaseTables for DCR
9. DEFLECTION   → JointDispl per joint loop → compare to L/250 or L/300
```

> **Critical order:** Never call `SetModelIsLocked(False)` between steps 5 and 9.
> It permanently deletes all results. Unlock → modify → re-run is the only safe pattern.

---

## STEP 1 — Sections

```python
model.SetModelIsLocked(False)
model.SetPresentUnits(6)   # kN_m throughout

# CHS pipe sections (roof truss)
model.PropFrame.SetPipe("CHS114x3",  "S355", 0.1143, 0.003)   # chord
model.PropFrame.SetPipe("CHS76x2.5", "S355", 0.076,  0.0025)  # web / diagonals
model.PropFrame.SetPipe("CHS60x2.5", "S355", 0.060,  0.0025)  # purlins

# RC columns (supports)
model.PropFrame.SetRectangle("Col400x400", "C25", 0.4, 0.4)
```

---

## STEP 2 — Geometry (3D Space Frame Pattern)

The structure shown is a series of **parallel bow/Fink trusses** spaced along the Y-axis,
connected at top chord nodes by **purlins**, with **end frames** for lateral stability.

### Key coordinate conventions
- X = span direction (truss length)
- Y = longitudinal direction (bay spacing)
- Z = height

### Single truss builder (parametric)

```python
def build_truss_at_y(y_pos, L, Z, rise, n, CH, WB):
    """
    Build one 2D bowstring truss at y=y_pos.
    Returns (bot_nodes, top_nodes, top_chord_frames)
    """
    p = L / n
    bot, top = [], []
    for i in range(n + 1):
        x = i * p
        zt = rise * 4.0 * x * (L - x) / (L * L)   # parabolic
        bot.append(model.PointObj.AddCartesian(x, y_pos, Z)[0])
        top.append(model.PointObj.AddCartesian(x, y_pos, Z + zt)[0])

    for i in range(n):
        model.FrameObj.AddByPoint(bot[i], bot[i+1], CH)   # bottom chord
    tc = []
    for i in range(n):
        tc.append(model.FrameObj.AddByPoint(top[i], top[i+1], CH)[0])  # top chord
    for i in range(1, n):
        model.FrameObj.AddByPoint(bot[i], top[i], WB)     # verticals

    return bot, top, tc
```

### 3D multi-bay space frame

```python
model.SetModelIsLocked(False); model.SetPresentUnits(6)

# Parameters
L      = 23.34   # span (m)
Z      = 5.0     # column top elevation (m)
rise   = 3.0     # bowstring rise (m)
n      = 12      # top chord panels per truss
bay_sp = 4.0     # Y-spacing between trusses (m)
n_bays = 5       # number of truss bays
CH     = "CHS114x3"
WB     = "CHS76x2.5"
PU     = "CHS60x2.5"  # purlin

# Columns
for i in range(n_bays + 1):
    y = i * bay_sp
    model.FrameObj.AddByCoord(0.0, y, 0, 0.0, y, Z, "Col400x400")
    model.FrameObj.AddByCoord(L,   y, 0, L,   y, Z, "Col400x400")
    lb = model.PointObj.AddCartesian(0.0, y, 0)
    rb = model.PointObj.AddCartesian(L,   y, 0)
    model.PointObj.SetRestraint(lb[0], [True,True,True,True,True,True])
    model.PointObj.SetRestraint(rb[0], [True,True,True,True,True,True])

# Trusses at each bay position
all_bots, all_tops, all_tc = [], [], []
for j in range(n_bays + 1):
    y = j * bay_sp
    bot, top, tc = build_truss_at_y(y, L, Z, rise, n, CH, WB)
    all_bots.append(bot); all_tops.append(top); all_tc.append(tc)

# Purlins connecting top chords between adjacent trusses
for j in range(n_bays):
    top_a = all_tops[j]; top_b = all_tops[j + 1]
    for i in range(len(top_a)):
        model.FrameObj.AddByPoint(top_a[i], top_b[i], PU)

# Bottom chord lateral ties (optional — add between bottom nodes at same x)
for j in range(n_bays):
    bot_a = all_bots[j]; bot_b = all_bots[j + 1]
    for i in [0, len(bot_a)//2, len(bot_a)-1]:   # at ends and midspan only
        model.FrameObj.AddByPoint(bot_a[i], bot_b[i], WB)

model.File.Save()
result = {"joints": model.PointObj.Count(), "frames": model.FrameObj.Count()}
```

---

## STEP 3 — Load Patterns & Applied Loads

```python
model.SetModelIsLocked(False); model.SetPresentUnits(6)

# Check existing patterns before adding
lp_existing = list(model.LoadPatterns.GetNameList()[1])

def add_pat(name, code, sw=0.0):
    if name not in lp_existing:
        model.LoadPatterns.Add(name, code, sw, True)

add_pat("Dead",    1, 1.0)   # self-weight activated
add_pat("SDL",     2, 0.0)   # superimposed DL (roofing, insulation)
add_pat("Roof_DL", 2, 0.0)   # roofing finish
add_pat("Roof_LL", 11, 0.0)  # roof live / maintenance
add_pat("WX",      6, 0.0)   # wind X
add_pat("WY",      6, 0.0)   # wind Y (longitudinal)
add_pat("Snow",    7, 0.0)   # snow

# Apply distributed loads to top chord members
# All top chord frame names collected in all_tc lists above
for tc_list in all_tc:
    for fn in tc_list:
        # Roof DL: 0.8 kN/m (roofing + purlins self-weight)
        model.FrameObj.SetLoadDistributed(fn,"Roof_DL",1,6,0.0,1.0,-0.8,-0.8,"Global",True,True,0)
        # Roof LL: 1.5 kN/m (maintenance)
        model.FrameObj.SetLoadDistributed(fn,"Roof_LL",1,6,0.0,1.0,-1.5,-1.5,"Global",True,True,0)
        # Snow: 0.6 kN/m (example — adjust to site)
        model.FrameObj.SetLoadDistributed(fn,"Snow",1,6,0.0,1.0,-0.6,-0.6,"Global",True,True,0)
```

### Wind load direction codes
```python
# Dir parameter in SetLoadDistributed:
# 4 = Global X   5 = Global Y   6 = Global Z
# 7 = Projected X (wind on inclined surface → use for pitched/arched roofs)
# Positive = in + direction, negative = in − direction
```

---

## STEP 4 — Load Cases (Static Linear)

```python
model.SetModelIsLocked(False); model.SetPresentUnits(6)

for pat in ["Dead","SDL","Roof_DL","Roof_LL","WX","WY","Snow"]:
    model.LoadCases.StaticLinear.SetCase(pat)
    model.LoadCases.StaticLinear.SetLoads(pat, 1, ["Load"], [pat], [1.0])

# Optional modal case (needed only for seismic or dynamic)
model.LoadCases.Modal.SetCase("Modal")
model.LoadCases.ModalEigen.SetNumberModes("Modal", 12, 1)
```

### Load Combinations

> **ETABS auto-generates AISC 360 design combos** (DStlS1–DStlS31, DStlD1–DStlD2)
> as soon as `DesignSteel.SetCode("AISC 360-16")` is called.
> You do NOT need to manually create ULS combos for steel design — ETABS handles them.
> Manual combos are only needed for custom serviceability (SLS) checks.

```python
# Manual SLS combo for deflection check — using RespCombo (LoadCombos has AttributeError)
model.RespCombo.Add("SLS_Char", 0)    # LinearAdd
# VERIFIED: RespCombo.SetCaseList signature is broken for arrays in the MCP sandbox.
# Use individual case additions via SetCaseList one load at a time is also broken.
# Workaround: run the SLS analysis case-by-case and combine deflections manually,
# OR run analysis, then manually sum deflection results per case in code.

# Example: SLS deflection = Dead_U3 + Roof_DL_U3 + Roof_LL_U3
```

---

## STEP 5 — Analysis

```python
model.SetModelIsLocked(False); model.SetPresentUnits(6)

# Configure which cases to run
model.Analyze.SetRunCaseFlag("", False, True)   # deselect all first
for case in ["Dead","SDL","Roof_DL","Roof_LL","WX","WY","Snow"]:
    model.Analyze.SetRunCaseFlag(case, True)
# model.Analyze.SetRunCaseFlag("Modal", True)   # add if seismic needed

model.File.Save()
ret = model.Analyze.RunAnalysis()

result = {
    "analysis_ret": ret,
    "success": ret == 0,
    "locked": model.GetModelIsLocked(),  # should be True after analysis
}
# For large models (>500 joints): run analysis in ETABS UI (F5)
# — MCP will time out. After UI run, GetModelIsLocked() returns True and results are available.
```

---

## STEP 6 — Reactions (Verify Loads)

```python
model.SetPresentUnits(6)

model.Results.Setup.DeselectAllCasesAndCombosForOutput()
for case in ["Dead","Roof_DL","Roof_LL"]:
    model.Results.Setup.SetCaseSelectedForOutput(case)

br = model.Results.BaseReact()
n = br[0]
result = [
    {"case": list(br[1])[i], "FX": round(list(br[4])[i],2),
     "FY": round(list(br[5])[i],2), "FZ": round(list(br[6])[i],2)}
    for i in range(n)
]
# FZ should equal total applied load (Dead self-weight + distributed loads × tributary area)
```

---

## STEP 7 — Frame Forces

> **VERIFIED:** Use `"Element Forces - Beams"` (NOT `"Frame Forces - Beams"` — returns empty).
> `model.Results.FrameForce(name, 0)` also returns 0 rows for truss members.
> DatabaseTables is the ONLY reliable method for bulk frame force extraction.

```python
model.SetPresentUnits(6)

# Select output cases or combos BEFORE calling DatabaseTables
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
model.Results.Setup.SetComboSelectedForOutput("DStlS5")   # 1.2D+1.6Lr (max gravity)
# OR: model.Results.Setup.SetCaseSelectedForOutput("Roof_LL")

raw = model.DatabaseTables.GetTableForDisplayArray(
    "Element Forces - Beams", [], "All", 0, [], 0, [])
fields = [f for f in list(raw[2]) if f is not None]
n_rows = raw[3]; flat = list(raw[4]); nf = len(fields)
rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n_rows)]

# Fields returned: Story, Beam, UniqueName, OutputCase, CaseType, Station,
#                  P, V2, V3, T, M2, M3, Element, ElemStation, Location

P_vals  = [float(r.get("P","0") or 0)  for r in rows]
M3_vals = [float(r.get("M3","0") or 0) for r in rows]

result = {
    "n_rows": n_rows,
    "max_tension_kN":     round(max(P_vals,  key=abs) if P_vals else 0, 2),
    "max_compression_kN": round(min(P_vals)             if P_vals else 0, 2),
    "max_moment_kNm":     round(max(M3_vals, key=abs)   if M3_vals else 0, 2),
}
```

### Column forces

```python
raw_col = model.DatabaseTables.GetTableForDisplayArray(
    "Element Forces - Columns", [], "All", 0, [], 0, [])
fields_c = [f for f in list(raw_col[2]) if f]
rows_c = [{fields_c[j]: flat[i*len(fields_c)+j] for j in range(len(fields_c))} 
          for i in range(raw_col[3])]
```

---

## STEP 8 — Steel Design (DCR Ratios)

> **VERIFIED:** `model.DesignSteel.GetSummaryResultsFrame` does NOT exist in ETABS 23.2.0.
> Use `DatabaseTables("Steel Frame Design Summary - AISC 360-16")` instead.

```python
if not model.GetModelIsLocked():
    result = {"error": "Run analysis first — model is unlocked"}
else:
    # Set design code — also auto-generates AISC design combos (DStlS1–DStlS31)
    ret_code = model.DesignSteel.SetCode("AISC 360-16")
    # Alternatives: "EC3-2005", "BS5950-2000", "IS 800:2007", "AS 4100-1998"

    # Run design
    ret_design = model.DesignSteel.StartDesign()

    # Read results via DatabaseTables (GetSummaryResultsFrame does NOT exist)
    raw = model.DatabaseTables.GetTableForDisplayArray(
        "Steel Frame Design Summary - AISC 360-16", [], "All", 0, [], 0, [])
    fields = [f for f in list(raw[2]) if f]
    n_rows = raw[3]; flat = list(raw[4]); nf = len(fields)
    rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n_rows)]

    # Fields: Story, Label, UniqueName, DesignType, DesignSect, Status,
    #         PMMCombo, PMMRatio, PRatio, MMajRatio, MMinRatio,
    #         VMajCombo, VMajRatio, VMinCombo, VMinRatio

    pmm = [float(r.get("PMMRatio","0") or 0) for r in rows]
    vmaj = [float(r.get("VMajRatio","0") or 0) for r in rows]

    max_pmm = max(pmm) if pmm else 0
    max_v   = max(vmaj) if vmaj else 0
    crit_i  = pmm.index(max_pmm) if pmm else 0

    result = {
        "design_code": "AISC 360-16",
        "members_checked": n_rows,
        "all_pass": all(p <= 1.0 for p in pmm),
        "max_PMM_ratio": round(max_pmm, 3),
        "max_V_ratio": round(max_v, 3),
        "critical_member": rows[crit_i].get("Label","") if rows else "",
        "governing_section": rows[crit_i].get("DesignSect","") if rows else "",
        "governing_combo": rows[crit_i].get("PMMCombo","") if rows else "",
        "members_over_unity": sum(1 for p in pmm if p > 1.0),
    }
```

### EC3 equivalent
```python
ret = model.DesignSteel.SetCode("EC3-2005")
ret = model.DesignSteel.StartDesign()
raw = model.DatabaseTables.GetTableForDisplayArray(
    "Steel Frame Design Summary - EC3-2005", [], "All", 0, [], 0, [])
```

---

## STEP 9 — Serviceability: Deflection Check

> **VERIFIED:** `JointDispl("", 2)` (all joints) returns EMPTY. Loop per joint with `itemType=0`.

```python
model.SetPresentUnits(6)
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
# Use SLS load cases (unfactored)
for case in ["Dead", "Roof_DL", "Roof_LL"]:
    model.Results.Setup.SetCaseSelectedForOutput(case)

jt = model.PointObj.GetNameList()
joints = list(jt[1])

# Loop all joints — collect max vertical deflection
max_u3 = 0.0; max_jn = ""; deflections = {}
for jn in joints:
    t = model.Results.JointDispl(jn, 0)
    if t[0] > 0:
        u3_vals = list(t[8])   # U3 = vertical (Z) displacement in metres
        for v in u3_vals:
            if abs(v) > abs(max_u3):
                max_u3 = v; max_jn = jn

L_span = 23.34   # adjust to your span (m)

# Deflection limits (choose per code / application)
limits = {
    "L/200 (pre-cast cladding)": L_span / 200,
    "L/250 (general steel)":     L_span / 250,
    "L/300 (plastered ceiling)": L_span / 300,
    "L/360 (brittle finish)":    L_span / 360,
}

result = {
    "max_deflection_mm": round(abs(max_u3) * 1000, 2),
    "at_joint": max_jn,
    "checks": {k: {"limit_mm": round(v*1000,1), "pass": abs(max_u3) < v}
               for k, v in limits.items()},
}
```

---

## Auto-Generated AISC 360 Design Combinations

When `DesignSteel.SetCode("AISC 360-16")` is called, ETABS auto-generates:

| Combo | Cases & Factors |
|-------|----------------|
| DStlS1 | 1.4×(D+SDL+Roof_DL) |
| DStlS2 | 1.2D+1.6L+0.5Snow |
| DStlS3 | 1.2D+1.6L+0.5Lr |
| DStlS4 | 1.2D+1.0L+1.6Snow |
| DStlS5 | 1.2D+1.0L+1.6Lr |
| DStlS6–S9 | 1.2D+1.0L+0.5S±1.0WX/WY |
| DStlS10–S13 | 1.2D+1.0L+0.5Lr±1.0WX/WY |
| DStlS14–S21 | 1.2D+1.6S or Lr ± 0.5W |
| DStlS22–S25 | 0.9D ± 1.0WX/WY |
| DStlS26–S31 | Seismic combos (1.3D ± EQX, 0.8D ± EQX) |
| DStlD1 | 1.0(D+SDL+Roof_DL) — service |
| DStlD2 | 1.0(D+L+SDL+Roof_DL) — service |

> **Key:** Make sure ALL load patterns referenced in the combos exist in the model
> (Dead, SDL, Roof_DL, Live, Roof_LL / Snow, WX, WY) otherwise those combos will error during design.

---

## Known API Limitations (ETABS 23.2.0)

| Call | Status | Workaround |
|------|--------|------------|
| `DesignSteel.GetSummaryResultsFrame` | ❌ AttributeError | `DatabaseTables("Steel Frame Design Summary - AISC 360-16")` |
| `Results.FrameForce(name, 0)` | ❌ returns 0 rows for truss members | `DatabaseTables("Element Forces - Beams")` |
| `Results.JointDispl("", 2)` | ❌ returns empty | Loop per joint with `itemType=0` |
| `Results.JointReact("", 2)` | ❌ returns empty | Loop per joint with `itemType=0` |
| `RespCombo.SetCaseList(Name, n, list, list, list)` | ❌ array error | Use auto-generated design combos |
| `LoadCombos.*` | ❌ AttributeError | Use `model.RespCombo.*` |
| `"Frame Forces - Beams"` table | ❌ returns empty | `"Element Forces - Beams"` |

---

## Quick Audit Script

```python
# Run this to check model readiness before analysis
model.SetPresentUnits(6)
ver = model.GetVersion()
lp = model.LoadPatterns.GetNameList()
lc = model.LoadCases.GetNameList()
result = {
    "etabs_version": ver[0],
    "joints": model.PointObj.Count(),
    "frames": model.FrameObj.Count(),
    "locked": model.GetModelIsLocked(),
    "load_patterns": list(lp[1]) if lp[0]>0 else [],
    "load_cases": list(lc[1]) if lc[0]>0 else [],
}
```
