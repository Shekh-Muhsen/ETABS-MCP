---
name: ibc2012-de12-torsion-irreg
description: "IBC 2012 / ASCE 7-10 §12.3.2.1 — Horizontal Irregularity Type 1a/1b: Torsional. Builds a 3-story asymmetric RC frame building (stiff columns Y=0, flexible columns Y=18), applies ELF, extracts story drifts at each side, computes δmax/δavg and Ax amplification factor. Verified in ETABS 23.2.0."
---

# IBC 2012 / ASCE 7-10 §12.3.2.1 — Horizontal Torsional Irregularity (Type 1a / 1b)

**Reference:** ASCE 7-10 §12.3.2.1, Table 12.3-1  
**Verified:** ETABS 23.2.0 — `IBC2012_DE12_TorsionIrreg.EDB`

---

## Code Procedure — ASCE 7-10 §12.3.2.1

Torsional irregularity exists when the **maximum story drift at one end** of the structure is more than 1.2× the **average story drift at the two ends**:

```
δmax / δavg > 1.2  → Type 1a (Torsional)
δmax / δavg > 1.4  → Type 1b (Extreme Torsional)
```

Where (for lateral load in X direction):
- **δmax** = larger of the story drifts at Y=0 end and Y=far end, in X direction
- **δavg** = (drift at Y=0 + drift at Y=far) / 2
- Story drift = floor displacement − floor below displacement (X component)

**Accidental Torsion Amplification (§12.8.4.3):**
```
Ax = (δmax / (1.2 × δavg))²    ≤ 3.0     [Eq 12.8-14]
```
Required for SDC C–F when torsion irregularity exists.

---

## Building Description

**3-story asymmetric RC frame, 36m × 18m plan**

- 5 column lines @ 9m in X (4 bays, 36m total)
- 3 column lines @ 9m in Y (2 bays, 18m total)
- 3 stories @ 4m = 12m total height
- **Y=0 side: COL500 (500×500 C30)** — stiff lateral resistance
- **Y=9 and Y=18 sides: COL350 (350×350 C30)** — flexible
- All beams: pinned gravity connections (columns act as cantilevers)
- **No slab / no diaphragm constraint** — differential drifts measured directly
- Units: kN, m

**Why no slab:**  
A rigid concrete slab (as in DE11) forces all floor nodes to the same X displacement, erasing the differential drift needed for the DE12 check. With only frame elements, COL500 (stiff) deflects less than COL350 (flexible) under equal applied force, directly producing δmax ≠ δavg.

**Stiffness ratio (cantilever columns):**  
k ∝ I/h³ ∝ b⁴ → COL500/COL350 stiffness ratio = (500/350)⁴ ≈ 4.2×

---

## Step 1 — Materials and Sections

```python
ret = model.SetPresentUnits(6)   # kN_m

# C30 concrete (if not already defined)
ret = model.PropMaterial.SetMaterial("C30", 2)
ret = model.PropMaterial.SetMPIsotropic("C30", 30000000.0, 0.2, 9.9e-6)
ret = model.PropMaterial.SetOConcrete_1("C30", 30000.0, False, 0.0, 2, 1, 0.003, 0.005, -0.1)
ret = model.PropMaterial.SetWeightAndMass("C30", 1, 25.0)

ret = model.PropFrame.SetRectangle("COL500",   "C30", 0.5,  0.5)   # stiff side
ret = model.PropFrame.SetRectangle("COL350",   "C30", 0.35, 0.35)  # flexible sides
ret = model.PropFrame.SetRectangle("BM300x500","C30", 0.5,  0.3)   # gravity beams
```

## Step 2 — Grid and Nodes

```python
X = [0, 9, 18, 27, 36]
Y = [0, 9, 18]
Z = [0, 4, 8, 12]

nodes = {}
for iz in range(4):
    for iy in range(3):
        for ix in range(5):
            t = model.PointObj.AddCartesian(X[ix], Y[iy], Z[iz])
            nodes[(ix, iy, iz)] = t[0]

# Fixed bases
for iy in range(3):
    for ix in range(5):
        model.PointObj.SetRestraint(nodes[(ix, iy, 0)], [True]*6)
```

## Step 3 — Columns

```python
for iz in range(3):
    for iy in range(3):
        for ix in range(5):
            sec = "COL500" if iy == 0 else "COL350"
            model.FrameObj.AddByPoint(nodes[(ix,iy,iz)], nodes[(ix,iy,iz+1)], sec)
```

> ⚠️ **ETABS 23 quirk:** `AddByPoint` may NOT apply the section name if the section was just overwritten with `SetRectangle`. Always verify with `GetSection` after adding, and use `SetSection` to force-assign if needed (see Step 3b).

## Step 3b — Force Section Assignment (Verified Fix)

```python
# Build reverse lookup: frozenset({pt1,pt2}) → frame name
t = model.FrameObj.GetNameList()
pt_to_frame = {}
for fn in list(t[1]):
    pt = model.FrameObj.GetPoints(fn)
    pt_to_frame[frozenset([pt[0], pt[1]])] = fn

# Force-assign sections by column grid position
for iz in range(3):
    for iy in range(3):
        for ix in range(5):
            key = frozenset([nodes[(ix,iy,iz)], nodes[(ix,iy,iz+1)]])
            fn  = pt_to_frame.get(key)
            if fn:
                sec = "COL500" if iy == 0 else "COL350"
                model.FrameObj.SetSection(fn, sec)

# Verify
stiff = pt_to_frame[frozenset([nodes[(0,0,0)], nodes[(0,0,1)]])]
flex  = pt_to_frame[frozenset([nodes[(0,2,0)], nodes[(0,2,1)]])]
print(model.FrameObj.GetSection(stiff)[0])   # → COL500
print(model.FrameObj.GetSection(flex)[0])    # → COL350
```

## Step 4 — Gravity Beams (all pinned)

```python
for iz in range(1, 4):
    for iy in range(3):          # X-direction
        for ix in range(4):
            t = model.FrameObj.AddByPoint(nodes[(ix,iy,iz)], nodes[(ix+1,iy,iz)], "BM300x500")
            model.FrameObj.SetReleases(t[0],
                [False,False,False,False,True,True],
                [False,False,False,False,True,True])
    for iy in range(2):          # Y-direction
        for ix in range(5):
            t = model.FrameObj.AddByPoint(nodes[(ix,iy,iz)], nodes[(ix,iy+1,iz)], "BM300x500")
            model.FrameObj.SetReleases(t[0],
                [False,False,False,False,True,True],
                [False,False,False,False,True,True])
```

## Step 5 — ELF Load

```python
# V = 4860 kN, triangular: [810, 1620, 2430] kN per floor
# Distributed equally among 15 nodes per floor
model.LoadPatterns.Add("EQ_X", 5, 0, True)

Fx_floor = [810.0, 1620.0, 2430.0]
for iz_idx, iz in enumerate([1, 2, 3]):
    fx = Fx_floor[iz_idx] / 15
    for iy in range(3):
        for ix in range(5):
            model.PointObj.SetLoadForce(nodes[(ix,iy,iz)], "EQ_X",
                                        [fx, 0, 0, 0, 0, 0], False, "Global")
```

## Step 6 — Analyze

```python
model.Analyze.SetRunCaseFlag("", False, True)
model.Analyze.SetRunCaseFlag("EQ_X", True, False)
ret = model.Analyze.RunAnalysis()
assert ret == 0, f"Analysis failed ret={ret}"
```

## Step 7 — §12.3.2.1 Torsional Irregularity Check

```python
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
model.Results.Setup.SetCaseSelectedForOutput("EQ_X")

def get_U1(nm):
    r = model.Results.JointDispl(nm, 0, 0)
    return r[6][0] if r[0] > 0 else 0.0

def avg_drift(iy, iz):
    fl  = sum(get_U1(nodes[(ix,iy,iz)])   for ix in range(5)) / 5
    blw = sum(get_U1(nodes[(ix,iy,iz-1)]) for ix in range(5)) / 5 if iz > 1 else 0.0
    return fl - blw

for iz in [1, 2, 3]:
    drift_Y0  = avg_drift(0, iz)   # stiff side (Y=0, COL500)
    drift_Y18 = avg_drift(2, iz)   # flexible side (Y=18, COL350)

    d_max = max(drift_Y0, drift_Y18)
    d_avg = (drift_Y0 + drift_Y18) / 2.0
    ratio = d_max / d_avg
    Ax    = min((d_max / (1.2 * d_avg))**2, 3.0)

    if   ratio > 1.4: irr = "Type 1b — EXTREME TORSIONAL"
    elif ratio > 1.2: irr = "Type 1a — TORSIONAL"
    else:             irr = "None"

    print(f"Floor {iz}: δY0={drift_Y0*1000:.1f}mm  δY18={drift_Y18*1000:.1f}mm  "
          f"ratio={ratio:.4f}  Ax={Ax:.4f}  → {irr}")
```

---

## Verified Results — COL500 (Y=0) vs COL350 (Y=9,18), 36m×18m

| Floor | δ_stiff Y=0 (mm) | δ_flex Y=18 (mm) | δmax/δavg | Ax | Classification |
|---|---|---|---|---|---|
| 1 | 21.21 | 44.95 | **1.359** | 1.282 | **Type 1a Torsional** |
| 2 | 22.04 | 40.87 | **1.299** | 1.172 | **Type 1a Torsional** |
| 3 | 13.23 | 24.78 | **1.304** | 1.181 | **Type 1a Torsional** |

All floors: **Type 1a Torsional Irregularity** per §12.3.2.1.

---

## Consequences of Type 1a/1b (ASCE 7-10)

| Condition | Type 1a | Type 1b |
|---|---|---|
| SDC C–F: must include accidental torsion | ✓ | ✓ |
| SDC C–F: amplify accidental torsion by Ax | ✓ | ✓ |
| SDC D–F: §12.3.3.4 — 3D analysis required | ✓ | ✓ |
| SDC E–F: Type 1b not permitted | — | prohibited |

---

## Key Implementation Notes (Verified ETABS 23.2)

- **No slab for this check** — rigid concrete slab forces all floor nodes to same X displacement, making ratio = 1.0 regardless of column stiffness differences ✓
- **Section assignment bug** — `AddByPoint(pt1, pt2, secName)` may revert to a prior section if the named section was recently overwritten. Always follow with `SetSection` force-assign loop ✓
- `JointDispl` → `r[6][0]` = U1 (X-displacement) ✓
- Average across all 5 X-positions per floor side for robustness ✓
- `FrameObj.SetReleases(fn, [F,F,F,F,T,T], [F,F,F,F,T,T])` = pin M2, M3 at both ends ✓

---

## Hand Calculation Verification

```python
# §12.3.2.1 check functions (from ibc2012_all_calculations.py)
def torsion_irregularity(drift_stiff, drift_flex):
    d_max = max(drift_stiff, drift_flex)
    d_avg = (drift_stiff + drift_flex) / 2.0
    ratio = d_max / d_avg
    if   ratio > 1.4: t = "1b-Extreme"
    elif ratio > 1.2: t = "1a-Torsional"
    else:             t = None
    return ratio, t

def torsion_amplification(d_max, d_avg):
    return min((d_max / (1.2 * d_avg))**2, 3.0)   # Eq 12.8-14

# Floor 1 ETABS values
ratio, irr = torsion_irregularity(21.21, 44.95)   # → (1.359, "1a-Torsional")
Ax = torsion_amplification(44.95, (21.21+44.95)/2) # → 1.282
```
