---
name: ibc2012-de11-diaphragm-class
description: "IBC 2012 / ASCE 7-10 §12.3.1 — Diaphragm Flexibility Classification. Builds a 3-story concrete moment-frame building with semi-rigid slab shells (no diaphragm constraint), applies ELF lateral load, extracts MFAD and AVSD from joint displacements, and classifies each floor per §12.3.1.3. Verified in ETABS 23.2.0."
---

# IBC 2012 / ASCE 7-10 §12.3.1 — Diaphragm Flexibility Classification

**Reference:** ASCE 7-10 §12.3.1  
**Verified:** ETABS 23.2.0 — `IBC2012_DE11_Diaphragm.EDB`

---

## Code Procedure — ASCE 7-10 §12.3.1

### §12.3.1.1 Rigid Diaphragm (Prescriptive — no calculation needed)
Concrete slabs or concrete-filled metal deck with:
- Span-to-depth ratio ≤ 3, AND
- No horizontal irregularities (§12.3.2.1)

→ Classify as **Rigid** without calculation.

### §12.3.1.2 Flexible Diaphragm (Prescriptive — no calculation needed)
- Wood structural panels (light-frame construction)
- Untopped steel decking:
  - SDC B/C: all occupancies
  - SDC D/E/F: one- and two-family dwellings only

→ Classify as **Flexible** without calculation.

### §12.3.1.3 Calculated Diaphragm Flexibility (General Case)

Diaphragm is **Flexible** if:

```
MFAD > 2 × AVSD
```

Where:
- **MFAD** = Maximum In-Plane Diaphragm Deflection  
  = |δ_center − (δ_left + δ_right) / 2|  
  (deflection of diaphragm center relative to average of two end supports)
- **AVSD** = Average Story Drift of adjoining vertical elements  
  = [(δ_left − δ_left_below) + (δ_right − δ_right_below)] / 2  
  (story drift = floor displacement minus displacement at floor below)

**All displacements U1 in the direction of applied lateral load (X).**

| Condition | Classification |
|---|---|
| MFAD > 2 × AVSD | Flexible |
| MFAD ≤ 2 × AVSD | Rigid |

---

## Building Description

**3-story RC office building, 36m × 18m plan**

- 5 column lines @ 9m in X (4 bays, 36m total)
- 3 column lines @ 9m in Y (2 bays, 18m total)
- 3 stories @ 4m = 12m total height
- Lateral system: concrete moment frames at X=0 and X=36m (outermost bays)
- Interior columns: gravity (pinned beam connections)
- **Slab: 125mm concrete shell-thin** — classifies as Rigid
- Units: kN, m

**Why this geometry:**  
The 36m span between moment frames maximises potential diaphragm deflection. A stiff concrete slab produces MFAD/AVSD ≈ 0.001–0.003 → confirmed Rigid. Replace slab with thin untopped deck to demonstrate Flexible classification.

---

## Step 1 — Units and Materials

```python
ret = model.SetPresentUnits(6)   # kN_m

ret = model.PropMaterial.SetMaterial("C30", 2)
ret = model.PropMaterial.SetMPIsotropic("C30", 30000000.0, 0.2, 9.9e-6)
ret = model.PropMaterial.SetOConcrete_1("C30", 30000.0, False, 0.0, 2, 1, 0.003, 0.005, -0.1)
ret = model.PropMaterial.SetWeightAndMass("C30", 1, 25.0)
```

## Step 2 — Sections

```python
ret = model.PropFrame.SetRectangle("COL500",   "C30", 0.5, 0.5)   # MF columns
ret = model.PropFrame.SetRectangle("COL350",   "C30", 0.35, 0.35) # interior gravity
ret = model.PropFrame.SetRectangle("BM300x600","C30", 0.6, 0.3)   # all beams

# 125mm slab — ShellThin, NO diaphragm constraint assigned later
ret = model.PropArea.SetSlab("SLAB125", 0, 0, "C30", 0.125)
```

## Step 3 — Grid and Nodes

```python
X = [0, 9, 18, 27, 36]
Y = [0, 9, 18]
Z = [0, 4, 8, 12]

nodes = {}   # (ix, iy, iz) -> ETABS joint name
for iz in range(4):
    for iy in range(3):
        for ix in range(5):
            t = model.PointObj.AddCartesian(X[ix], Y[iy], Z[iz])
            nodes[(ix, iy, iz)] = t[0]

# Fix all base nodes
for iy in range(3):
    for ix in range(5):
        model.PointObj.SetRestraint(nodes[(ix, iy, 0)],
                                    [True, True, True, True, True, True])
```

## Step 4 — Columns

```python
for iz in range(3):
    for iy in range(3):
        for ix in range(5):
            sec = "COL500" if ix in (0, 4) else "COL350"
            model.FrameObj.AddByPoint(nodes[(ix, iy, iz)], nodes[(ix, iy, iz+1)], sec)
```

## Step 5 — Beams

```python
for iz in range(1, 4):
    for iy in range(3):
        for ix in range(4):   # X-direction beams
            t = model.FrameObj.AddByPoint(
                nodes[(ix, iy, iz)], nodes[(ix+1, iy, iz)], "BM300x600"
            )
            fn = t[0]
            if ix not in (0, 3):   # interior spans: pin (gravity only)
                model.FrameObj.SetReleases(fn,
                    [False,False,False,False,True,True],
                    [False,False,False,False,True,True])

    for iy in range(2):
        for ix in range(5):   # Y-direction beams: all gravity pinned
            t = model.FrameObj.AddByPoint(
                nodes[(ix, iy, iz)], nodes[(ix, iy+1, iz)], "BM300x600"
            )
            model.FrameObj.SetReleases(t[0],
                [False,False,False,False,True,True],
                [False,False,False,False,True,True])
```

## Step 6 — Slab Panels (semi-rigid, NO diaphragm constraint)

```python
# 4×2 = 8 panels per floor × 3 floors = 24 panels
# AddByPoint returns [(joint_names), area_name, ret] — area name is at [1]
for iz in range(1, 4):
    for iy in range(2):
        for ix in range(4):
            pts = [
                nodes[(ix,   iy,   iz)],
                nodes[(ix+1, iy,   iz)],
                nodes[(ix+1, iy+1, iz)],
                nodes[(ix,   iy+1, iz)],
            ]
            t = model.AreaObj.AddByPoint(4, pts, "SLAB125")
            # area_name = t[1]   ← NOT t[0]
```

> **CRITICAL:** Do NOT call `model.DiaphragmObj.Add()` or assign any diaphragm constraint.
> A rigid diaphragm constraint forces MFAD = 0 by definition — the shell stiffness must be the only in-plane stiffness.

## Step 7 — ELF Loads (X direction)

```python
# W_floor = 25 kN/m² × 36 × 18 = 16200 kN
# V = Cs × W_total = 0.10 × (3 × 16200) = 4860 kN
# Triangular: Fx_i = V × hi / (4+8+12)
model.LoadPatterns.Add("EQ_X", 5, 0, True)   # 5=Seismic

V = 4860.0
heights = [4, 8, 12]
Fx_floor = [V * h / sum(heights) for h in heights]   # [810, 1620, 2430] kN

# Distribute equally among 15 nodes per floor
for iz_idx, iz in enumerate([1, 2, 3]):
    fx_node = Fx_floor[iz_idx] / 15
    for iy in range(3):
        for ix in range(5):
            model.PointObj.SetLoadForce(
                nodes[(ix, iy, iz)], "EQ_X",
                [fx_node, 0, 0, 0, 0, 0],
                False, "Global"
            )
```

## Step 8 — Analyze

```python
model.Analyze.SetRunCaseFlag("", False, True)
model.Analyze.SetRunCaseFlag("EQ_X", True, False)
ret = model.Analyze.RunAnalysis()
assert ret == 0, f"Analysis failed: ret={ret}"
# model auto-locks after analysis — do NOT call SetModelIsLocked(False)
```

## Step 9 — §12.3.1.3 Classification Check

```python
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
model.Results.Setup.SetCaseSelectedForOutput("EQ_X")

# Check points: Y=9m (center Y), X=0 (left), X=18 (center), X=36 (right)
# JointDispl returns: [0]=n, [6]=U1 tuple (X-displacement)

def get_U1(pt_name):
    r = model.Results.JointDispl(pt_name, 0, 0)
    return r[6][0] if r[0] > 0 else 0.0

results = {}
for iz in [1, 2, 3]:
    d_left   = get_U1(nodes[(0, 1, iz)])   # X=0,  Y=9m
    d_right  = get_U1(nodes[(4, 1, iz)])   # X=36, Y=9m
    d_center = get_U1(nodes[(2, 1, iz)])   # X=18, Y=9m

    d_left_b  = get_U1(nodes[(0, 1, iz-1)]) if iz > 1 else 0.0
    d_right_b = get_U1(nodes[(4, 1, iz-1)]) if iz > 1 else 0.0

    d_avg  = (d_left + d_right) / 2.0
    MFAD   = abs(d_center - d_avg)
    AVSD   = ((d_left - d_left_b) + (d_right - d_right_b)) / 2.0
    ratio  = MFAD / AVSD if abs(AVSD) > 1e-9 else 0.0
    classif = "FLEXIBLE" if MFAD > 2.0 * AVSD else "RIGID"

    print(f"Floor {iz}:  MFAD={MFAD*1000:.3f}mm  AVSD={AVSD*1000:.3f}mm  "
          f"ratio={ratio:.4f}  → {classif}")
    results[f"Floor{iz}"] = {"MFAD_mm": MFAD*1000, "AVSD_mm": AVSD*1000,
                              "ratio": ratio, "classification": classif}

result = results
```

---

## Verified Results — 125mm Concrete Slab, 36m × 18m Plan

| Floor | δ_left (m) | δ_center (m) | δ_right (m) | MFAD (mm) | AVSD (mm) | Ratio | Classification |
|---|---|---|---|---|---|---|---|
| 1 | 0.005763 | 0.005771 | 0.005763 | 0.008 | 5.763 | **0.0013** | **RIGID** |
| 2 | 0.013271 | 0.013267 | 0.013271 | 0.004 | 7.508 | **0.0005** | **RIGID** |
| 3 | 0.018304 | 0.018290 | 0.018304 | 0.015 | 5.033 | **0.0029** | **RIGID** |

MFAD/AVSD ≪ 2.0 → **All floors: Rigid Diaphragm** per §12.3.1.3.

> Prescriptive check also passes: span/depth = 36/18 = 2.0 ≤ 3.0 → §12.3.1.1 Rigid.

---

## Key Implementation Notes (Verified)

- `AreaObj.AddByPoint(4, pts, sec)` → area name is at `t[1]`, NOT `t[0]`
- `PropArea.SetSlab("SLAB125", 0, 0, "C30", 0.125)` — ShellType 0 = ShellThin ✓
- `PropArea.SetShell_1()` does NOT exist in ETABS 23 — use `SetSlab` ✓
- `Results.JointDispl(pt, 0, 0)` → `r[6]` = U1 tuple (index 6, not 3) ✓
- Do NOT assign `DiaphragmObj` — rigid constraint forces MFAD = 0 ✓
- Do NOT call `SetModelIsLocked(False)` after `RunAnalysis()` — destroys results ✓

---

## §12.3.1.1 Prescriptive Check (Quick Reference)

```python
# Before running ETABS — check prescriptive rigid condition first
span = 36.0   # m, dimension parallel to lateral load
depth = 18.0  # m, dimension perpendicular to lateral load
ratio = span / depth   # = 2.0

if ratio <= 3.0:
    print(f"Span/depth = {ratio:.1f} ≤ 3.0 → Prescriptively RIGID (§12.3.1.1)")
    print("No ETABS calculation required (if no horizontal irregularities)")
else:
    print(f"Span/depth = {ratio:.1f} > 3.0 → Must use §12.3.1.3 calculated check")
```

---

## Flexible Diaphragm Variant (Steel Deck, for comparison)

To model an untopped steel deck:

```python
# Replace SLAB125 with thin steel deck (equivalent membrane stiffness)
# E_deck ≈ E_steel × t_effective / t_concrete_equiv
# For 20-ga (0.9mm) untopped deck: t_eff ≈ 0.9mm steel, use NoDesign material
ret = model.PropMaterial.SetMaterial("STL_Deck", 1)
ret = model.PropMaterial.SetMPIsotropic("STL_Deck", 200000000.0, 0.3, 1.17e-5)
ret = model.PropArea.SetSlab("DECK_UNFILLED", 0, 2, "STL_Deck", 0.0009)  # 0.9mm, Membrane
# Expected result: ratio >> 2.0 → FLEXIBLE
```
