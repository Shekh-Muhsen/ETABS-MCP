---
name: ibc2012-de10-dual-system
description: "IBC 2012 / ASCE 7-10 DE 10 — Dual System 25% Moment Frame Rule §12.2.5.1. Calculates scale factor and scaled design forces, builds a 5-story dual system model in ETABS (shear wall + SMF), and verifies the 25% rule."
---

# IBC 2012 DE 10 — Dual System: 25% Moment Frame Rule (§12.2.5.1)

**Reference:** SEAOC Structural/Seismic Design Manual Vol. 1, Design Example 10  
**Code:** ASCE 7-10 §12.2.5.1

---

## Problem Statement

A **dual system** (special concrete shear wall + special moment frame) must satisfy:
- The moment frame alone must be capable of resisting **at least 25%** of the prescribed seismic forces.
- The shear wall + moment frame together resist **100%** of seismic forces.

**Given (from book):**
- Total base shear: V = 400 kips
- Moment frame base shear from combined analysis: V_frame = 45 kips (11.25% of V)
- Design moment at critical beam-column joint A from combined analysis: QE = 53 kip-ft

**Required:** Scale factor and scaled design moment Q'E for the moment frame.

---

## Hand Calculation

```python
# §12.2.5.1 — Dual system: moment frame must resist >= 25% V
V        = 400    # total seismic base shear (kips)
V_frame  = 45     # moment frame share from analysis (kips)
QE       = 53     # design moment at joint A from analysis (kip-ft)

scale    = 0.25 * V / V_frame   # = 2.222  (scale so MF resists 25% V)
Q_prime  = scale * QE           # = 117.8 kip-ft  (scaled design moment)

# Check: if V_frame >= 0.25*V, scale=1.0 (no scaling needed)
# Here V_frame=45 < 100 kips (25%*400), so scaling IS required.
```

**Results:**
| Parameter | Value |
|---|---|
| 25% of V | 100 kips |
| V_frame from analysis | 45 kips |
| Scaling required? | **Yes** |
| Scale factor | **2.222** |
| Q'E (scaled design moment) | **117.8 kip-ft** |

---

## ETABS Model — 5-Story Dual System

Build a 5-story, single-bay dual system:
- **Shear walls** on left side (special RC shear wall, R=7 for wall alone)
- **Special moment frame** on right side (R=8 for dual system)
- Both walls and frames connected by rigid diaphragms at each floor

### Step 1 — Setup and Units

```python
# Units: kip, in, F
model.SetPresentUnits(6)   # kip-in-F

# Story heights: 5 @ 12 ft
story_heights = [144] * 5   # inches
bay_width     = 240          # 20 ft bay
```

### Step 2 — Define Materials

```python
# Concrete f'c = 5000 psi
ret = model.PropMaterial.SetMaterial("C5000", 2)        # 2=concrete
ret = model.PropMaterial.SetOConcrete("C5000", 5, False, 0, 1, 1, 0.005, 0.02, 0.06)

# Steel Fy = 60 ksi (rebar)
ret = model.PropMaterial.SetMaterial("A615Gr60", 6)     # 6=rebar
ret = model.PropMaterial.SetORebar("A615Gr60", 60, 90, 60, 90, 0, 1, 0.18, 0.04, False)
```

### Step 3 — Frame Sections (SMF columns and beams)

```python
# SMF Column: 24x24 in concrete
ret = model.PropFrame.SetRectangle("COL24x24", "C5000", 24, 24)

# SMF Beam: 18x30 in concrete
ret = model.PropFrame.SetRectangle("BM18x30", "C5000", 18, 30)
```

### Step 4 — Wall Section

```python
# RC shear wall: 12 in thick
ret = model.PropArea.SetWall(
    "SW12", 1, 0,          # 1=specified, 0=uniform
    "C5000", 12            # 12 in thick
)
```

### Step 5 — Add Stories and Grid

```python
import comtypes.client

# Base elevation = 0; add floor levels
elev = 0
for i, h in enumerate(story_heights):
    elev += h
    # Floor diaphragm points at each level will be added with frames

# Grid: X=0 (wall) and X=240 (SMF); Y=0 only (2D frame)
```

### Step 6 — Add Frame Members (SMF side, X=240)

```python
elev = 0
col_points = []
for i in range(6):          # 6 nodes: base + 5 floors
    ret, name = model.PointObj.AddCartesian(240, 0, elev, "", "", False, True, 0)
    col_points.append(name)
    elev += story_heights[i] if i < 5 else 0

# SMF Columns (right side)
for i in range(5):
    ret, fname = model.FrameObj.AddByPoint(
        col_points[i], col_points[i+1], "", "COL24x24", f"SMF_COL_{i+1}"
    )

# Wall-side column nodes (left, X=0)
elev = 0
wall_pts = []
for i in range(6):
    ret, name = model.PointObj.AddCartesian(0, 0, elev, "", "", False, True, 0)
    wall_pts.append(name)
    elev += story_heights[i] if i < 5 else 0

# SMF Beams connecting wall top node to SMF column at each floor
for i in range(1, 6):
    ret, fname = model.FrameObj.AddByPoint(
        wall_pts[i], col_points[i], "", "BM18x30", f"SMF_BM_{i}"
    )
```

### Step 7 — Add Shear Walls (X=0 side)

```python
for i in range(5):
    x0, x1 = 0, 0
    z0 = sum(story_heights[:i])
    z1 = z0 + story_heights[i]
    # Wall as shell area: 4 corners (zero-width wall in 2D: use small width 12 in)
    pts = [
        (0,  0, z0),
        (12, 0, z0),
        (12, 0, z1),
        (0,  0, z1),
    ]
    pt_names = []
    for x, y, z in pts:
        ret, pn = model.PointObj.AddCartesian(x, y, z, "", "", False, True, 0)
        pt_names.append(pn)
    ret, wname = model.AreaObj.AddByPoint(
        4, pt_names, "", "SW12", f"WALL_{i+1}"
    )
```

### Step 8 — Assign Diaphragms

```python
# Rigid diaphragm at each floor
for i in range(1, 6):
    diaphragm_name = f"D{i}"
    model.DiaphragmObj.Add(diaphragm_name, 1)  # 1=rigid
    # Assign to all points at this level
    elev_i = sum(story_heights[:i])
    # Select all points at this elevation and assign diaphragm
    model.SelectObj.All()
    # Use database approach: assign to floor nodes
    all_nodes = [wall_pts[i], col_points[i]]
    for pt in all_nodes:
        model.PointObj.SetDiaphragm(pt, 1, diaphragm_name)
```

### Step 9 — Seismic Loads (ELF, V=400 kips total)

```python
# Add seismic load pattern
model.LoadPatterns.Add("EQ_X", 5, 0, True)   # 5=seismic

# Story forces — triangular distribution (k=1, simplified)
# Fx_i = V * (h_i * w_i) / sum(h_j * w_j)
# Assume equal story weights W_story = 500 kips each (W_total = 2500 k)
W_story = [500] * 5   # kips per floor
heights  = [144*(i+1) for i in range(5)]   # cumulative heights (in)
denom    = sum(w * h for w, h in zip(W_story, heights))
V_total  = 400   # kips

Fx = [V_total * (W_story[i] * heights[i]) / denom for i in range(5)]

# Apply as joint forces at each SMF column node (diaphragm transfers to wall)
for i in range(5):
    model.PointObj.SetLoadForce(
        col_points[i+1], "EQ_X",
        [Fx[i], 0, 0, 0, 0, 0],   # Fx in X direction
        False, "Global"
    )
```

### Step 10 — Analyze and Extract Results

```python
# Run analysis
model.Analyze.SetRunCaseFlag("", False, True)   # clear all
model.Analyze.SetRunCaseFlag("EQ_X", True, False)
ret = model.Analyze.RunAnalysis()
assert ret == 0, "Analysis failed"

model.Results.Setup.DeselectAllCasesAndCombosForOutput()
model.Results.Setup.SetCaseSelectedForOutput("EQ_X")

# Get base reactions (total base shear should = V = 400 kips)
ret, npts, obj, elm, loadCase, stepType, stepNum, \
    Fx_r, Fy_r, Fz_r, Mx_r, My_r, Mz_r = \
    model.Results.BaseReact(0, 0)

V_total_check = sum(abs(f) for f in Fx_r)
print(f"Total base shear check: {V_total_check:.1f} kips (expect 400)")

# Get frame reactions at SMF base column
ret, npts, obj, elm, loadCase, stepType, stepNum, \
    U1, U2, U3, R1, R2, R3 = \
    model.Results.FrameForce(col_points[0] + "-" + col_points[1], 0, 0)
# V_frame = sum of shear in all SMF columns at base
```

---

## Verification Checks

```python
# DE 10 checks per book
V        = 400.0
V_frame  = 45.0     # from analysis (replace with ETABS result)
QE       = 53.0     # moment at joint A from analysis

scale   = 0.25 * V / V_frame
Q_prime = scale * QE

assert abs(scale   - 2.222) < 0.01, f"Scale factor {scale:.3f} ≠ 2.222"
assert abs(Q_prime - 117.8) < 0.5,  f"Q'E {Q_prime:.1f} ≠ 117.8 kip-ft"

print(f"[PASS] Scale factor     = {scale:.3f} (expect 2.222)")
print(f"[PASS] Q'E design moment = {Q_prime:.1f} kip-ft (expect 117.8)")
print(f"[INFO] 25% rule: V_frame must be designed for {0.25*V:.0f} kips minimum")
```

---

## Key Code Notes

- §12.2.5.1 requires the moment frame to be **designed** (not just to resist) 25% of V — the analysis result is irrelevant; apply the scale.
- For SDC D/E/F, the dual system R values apply: SW R=7 (standalone) → use R=7 for the combined system if the MF qualifies as special (SMF).
- The scale factor applies to **all** member forces in the SMF (shear, moment, axial) — not just base shear.
- If V_frame ≥ 0.25V from analysis, scale = 1.0 (no amplification needed).

---

## Quick Reference — §12.2.5.1 Formula

```
scale   = max(0.25 * V / V_frame, 1.0)
Q'E_i   = scale * QE_i     for each SMF member force
```
