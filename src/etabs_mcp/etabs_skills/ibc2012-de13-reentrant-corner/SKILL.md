---
name: ibc2012-de13-reentrant-corner
description: "IBC 2012 / ASCE 7-10 §12.3.2.1 — Horizontal Irregularity Type 2: Re-entrant Corner. Builds an L-shaped 3-story RC building (30m × 24m plan, 7.5m × 6m top-right corner removed), verifies both arm projections exceed 15% of plan dimension, and flags Type 2 irregularity. Verified in ETABS 23.2.0."
---

# IBC 2012 / ASCE 7-10 §12.3.2.1 — Re-entrant Corner Irregularity (Type 2)

**Reference:** ASCE 7-10 §12.3.2.1, Table 12.3-1  
**Verified:** ETABS 23.2.0 — `D:\Works\IBC2012_DE13_ReentrantCorner.EDB`

---

## Code Procedure — ASCE 7-10 §12.3.2.1 Type 2

**Re-entrant corner irregularity exists** when the plan configuration has re-entrant corners where **both** projections of the structure beyond the re-entrant corner exceed **15%** of the plan dimension in that direction:

```
rx = projection_X / total_X  >  0.15   AND
ry = projection_Y / total_Y  >  0.15
```

Where:
- **projection_X** = the amount by which one arm of the building extends beyond the other in the X direction (width of the cut-out / notch in X)
- **projection_Y** = same, in the Y direction
- **total_X** = overall plan dimension in X
- **total_Y** = overall plan dimension in Y

| Condition | Classification |
|---|---|
| rx > 0.15 **AND** ry > 0.15 | **Type 2 — Re-entrant Corner Irregularity** |
| Either projection ≤ 0.15 | No irregularity |

> **Note:** This is a **geometric check only** — no lateral analysis is needed to classify. Run the analysis to assess consequences (torsional response, stress concentrations at the re-entrant corner).

---

## Building Description

**3-story L-shaped RC building**

- Overall plan: **30m × 24m** (before cut-out)
- Cut-out: **7.5m × 6m** from top-right corner (X=22.5→30, Y=18→24)
- Resulting L-shaped floor area: 30×24 − 7.5×6 = **675 m²**
- 3 stories @ 4m = 12m total height
- Uniform COL400 (400×400 C30) columns, BM300×500 gravity beams (pinned)
- 125mm concrete slab (SLAB125) on all L-shaped floor panels
- Units: kN, m

**L-shaped plan (plan view, top = Y=24m):**
```
Y=24  [col][col][col][col][ -- ]
       0    7.5  15  22.5  30
Y=18  [col][col][col][col][col]   ← re-entrant corner at (22.5, 18)
Y=12  [col][col][col][col][col]
Y=6   [col][col][col][col][col]
Y=0   [col][col][col][col][col]
```
The top-right position (X=30, Y=24) does not exist — this creates the notch.

**Projections:**
- projection_X = 30 − 22.5 = **7.5m** (lower arm sticks out 7.5m beyond upper arm's right edge)
- projection_Y = 24 − 18 = **6.0m** (upper arm height above the lower arm's right side)
- rx = 7.5/30 = **0.25 > 0.15** ✓
- ry = 6.0/24 = **0.25 > 0.15** ✓

---

## Step 1 — Materials and Sections

```python
ret = model.SetPresentUnits(6)   # kN_m

ret = model.PropMaterial.SetMaterial("C30", 2)
ret = model.PropMaterial.SetMPIsotropic("C30", 30000000.0, 0.2, 9.9e-6)
ret = model.PropMaterial.SetOConcrete_1("C30", 30000.0, False, 0.0, 2, 1, 0.003, 0.005, -0.1)
ret = model.PropMaterial.SetWeightAndMass("C30", 1, 25.0)

ret = model.PropFrame.SetRectangle("COL400",    "C30", 0.4, 0.4)
ret = model.PropFrame.SetRectangle("BM300x500", "C30", 0.5, 0.3)
ret = model.PropArea.SetSlab("SLAB125", 0, 0, "C30", 0.125)
```

## Step 2 — Grid and L-shaped Node Layout

```python
X = [0, 7.5, 15, 22.5, 30]    # 5 column lines (ix = 0..4)
Y = [0, 6,  12, 18,   24]     # 5 column lines (iy = 0..4)
Z = [0, 4,   8, 12]           # base + 3 floors (iz = 0..3)

def ne(ix, iy):
    # L-shape: remove only top-right corner node (X=30, Y=24)
    return not (ix == 4 and iy == 4)

nodes = {}
for iz in range(4):
    for iy in range(5):
        for ix in range(5):
            if ne(ix, iy):
                t = model.PointObj.AddCartesian(X[ix], Y[iy], Z[iz])
                nodes[(ix, iy, iz)] = t[0]

# Fixed bases
for iy in range(5):
    for ix in range(5):
        if ne(ix, iy):
            model.PointObj.SetRestraint(nodes[(ix,iy,0)], [True]*6)
```

## Step 3 — Columns

```python
for iz in range(3):
    for iy in range(5):
        for ix in range(5):
            if ne(ix, iy) and (ix,iy,iz) in nodes and (ix,iy,iz+1) in nodes:
                model.FrameObj.AddByPoint(nodes[(ix,iy,iz)], nodes[(ix,iy,iz+1)], "COL400")

# Force-assign sections (ETABS 23 quirk — AddByPoint may not apply section)
tl = model.FrameObj.GetNameList()
ptf = {}
for fn in list(tl[1]):
    pt = model.FrameObj.GetPoints(fn)
    ptf[frozenset([pt[0], pt[1]])] = fn
for iz in range(3):
    for iy in range(5):
        for ix in range(5):
            if (ix,iy,iz) in nodes and (ix,iy,iz+1) in nodes:
                key = frozenset([nodes[(ix,iy,iz)], nodes[(ix,iy,iz+1)]])
                fn  = ptf.get(key)
                if fn:
                    model.FrameObj.SetSection(fn, "COL400")
```

## Step 4 — Gravity Beams (pinned, L-shaped)

```python
for iz in range(1, 4):
    # X-direction beams
    for iy in range(5):
        for ix in range(4):
            if (ix,iy,iz) in nodes and (ix+1,iy,iz) in nodes:
                t = model.FrameObj.AddByPoint(nodes[(ix,iy,iz)], nodes[(ix+1,iy,iz)], "BM300x500")
                model.FrameObj.SetReleases(t[0], [False]*4+[True,True], [False]*4+[True,True])
    # Y-direction beams
    for iy in range(4):
        for ix in range(5):
            if (ix,iy,iz) in nodes and (ix,iy+1,iz) in nodes:
                t = model.FrameObj.AddByPoint(nodes[(ix,iy,iz)], nodes[(ix,iy+1,iz)], "BM300x500")
                model.FrameObj.SetReleases(t[0], [False]*4+[True,True], [False]*4+[True,True])
```

## Step 5 — Slab Panels (L-shaped, skip cut-out bay)

```python
def panel_exists(ix, iy):
    # All four corners of the panel must exist
    return ne(ix,iy) and ne(ix+1,iy) and ne(ix+1,iy+1) and ne(ix,iy+1)

for iz in range(1, 4):
    for iy in range(4):
        for ix in range(4):
            if panel_exists(ix, iy):
                pts = [
                    nodes[(ix,   iy,   iz)],
                    nodes[(ix+1, iy,   iz)],
                    nodes[(ix+1, iy+1, iz)],
                    nodes[(ix,   iy+1, iz)],
                ]
                model.AreaObj.AddByPoint(4, pts, "SLAB125")
# Panels: 4×4=16 per floor minus 1 cut-out bay = 15 × 3 floors = 45 total
```

## Step 6 — ELF Load (X direction)

```python
# L-shaped area = 30×24 − 7.5×6 = 675 m²
# W_floor = 25 kN/m² × 675 = 16875 kN; W_total = 3 × 16875 = 50625 kN
# Cs = 0.10 → V = 0.10 × 50625 = 5062.5 kN
# Triangular: Fx_i = V × hi / (4+8+12)
model.LoadPatterns.Add("EQ_X", 5, 0, True)
V = 5062.5
heights = [4, 8, 12]
Fx_floor = [V * h / sum(heights) for h in heights]   # [844, 1688, 2531] kN

for iz_idx, iz in enumerate([1, 2, 3]):
    fx_node = Fx_floor[iz_idx] / 24.0   # 24 nodes per L-shaped floor
    for iy in range(5):
        for ix in range(5):
            if (ix,iy,iz) in nodes:
                model.PointObj.SetLoadForce(nodes[(ix,iy,iz)], "EQ_X",
                                            [fx_node, 0, 0, 0, 0, 0], False, "Global")
```

## Step 7 — Analyze

```python
model.File.Save("D:\\Works\\IBC2012_DE13_ReentrantCorner.EDB")
model.Analyze.SetRunCaseFlag("", False, True)
model.Analyze.SetRunCaseFlag("EQ_X", True, False)
ret = model.Analyze.RunAnalysis()
assert ret == 0, f"Analysis failed ret={ret}"
```

## Step 8 — §12.3.2.1 Type 2 Re-entrant Corner Check

```python
# Geometric check — independent of analysis results
total_x  = 30.0
total_y  = 24.0
proj_x   = 7.5    # 30 − 22.5
proj_y   = 6.0    # 24 − 18

rx = proj_x / total_x   # 0.25
ry = proj_y / total_y   # 0.25

irregularity = rx > 0.15 and ry > 0.15

print(f"Projection X: {proj_x}m / {total_x}m = {rx:.4f}  >0.15? {rx>0.15}")
print(f"Projection Y: {proj_y}m / {total_y}m = {ry:.4f}  >0.15? {ry>0.15}")

if irregularity:
    print("→ TYPE 2 RE-ENTRANT CORNER IRREGULARITY EXISTS (§12.3.2.1, Table 12.3-1)")
else:
    print("→ No irregularity")

result = {
    "total_x_m": total_x, "total_y_m": total_y,
    "projection_x_m": proj_x, "projection_y_m": proj_y,
    "rx": rx, "ry": ry,
    "irregularity_type2": irregularity,
}
```

---

## Verified Results — 30m × 24m L-shape (7.5m × 6m cut-out)

| Parameter | Value | >15%? |
|---|---|---|
| total_X | 30.0 m | — |
| total_Y | 24.0 m | — |
| projection_X | 7.5 m | — |
| projection_Y | 6.0 m | — |
| **rx = proj_X / total_X** | **0.2500** | **YES ✓** |
| **ry = proj_Y / total_Y** | **0.2500** | **YES ✓** |
| **Type 2 irregularity** | **EXISTS** | — |

**Book values:** SEAOC SDM Vol. 1, DE 13 — rx = 25/100 = 0.25, ry = 20/80 = 0.25 → **MATCH ✓**

### Floor displacements at re-entrant corner (X=22.5m, Y=18m), EQ_X:

| Floor | U1 (mm) |
|---|---|
| 1 | 20.2 |
| 2 | 38.9 |
| 3 | 50.2 |

The re-entrant corner node experiences intermediate displacements (between the stiff full-depth arm and the flexible upper arm) — this differential response is the physical basis for requiring special analysis attention at re-entrant corners.

---

## Consequences of Type 2 (ASCE 7-10)

| Consequence | Reference |
|---|---|
| SDC D–F: chord and collector elements + connections shall be designed for Ω₀ × force | §12.3.3.4 |
| Diaphragm should be checked for in-plane demands at the notch | §12.10 |
| Consider collector design for force transfer across the re-entrant corner | §12.10.2 |
| Both directions must exceed 15% — single direction only is NOT Type 2 | Table 12.3-1 |

---

## Hand Calculation

```python
def reentrant_corner_check(projection_x, total_x, projection_y, total_y):
    """Type 2 exists if projection > 15% of plan dimension in BOTH directions."""
    rx = projection_x / total_x
    ry = projection_y / total_y
    exists = rx > 0.15 and ry > 0.15
    return rx, ry, exists

# DE 13 — book values (ft, but ratio is dimensionless)
rx, ry, irr = reentrant_corner_check(25, 100, 20, 80)
# rx=0.25, ry=0.25, irr=True  → Type 2 Re-entrant Corner

# Metric equivalents (same ratios)
rx, ry, irr = reentrant_corner_check(7.5, 30, 6.0, 24)
# rx=0.25, ry=0.25, irr=True  ← matches ETABS model ✓
```

---

## Key Implementation Notes (Verified ETABS 23.2)

- `ne(ix, iy)` only excludes node (ix=4, iy=4) = (X=30m, Y=24m) — the single missing corner node forms the L-shape ✓
- `panel_exists(ix, iy)` skips the top-right slab bay (ix=3, iy=3) since corner (4,4) missing ✓
- `AreaObj.AddByPoint(4, pts, sec)` → area name at `t[1]`, NOT `t[0]` (see DE11 note) ✓
- Section force-assign loop required after `AddByPoint` (see DE12 note) ✓
- **Re-entrant corner check is geometric only** — no displacement extraction needed for the §12.3.2.1 classification ✓
- Total plan nodes per floor: 24 (25 minus 1 cut-out) ✓
- Total slab panels: 45 (16 per floor × 3 floors minus 3 cut-out panels) ✓
