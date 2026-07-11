---
name: ibc2012-de34-torsion-amplification
description: "IBC 2012 / ASCE 7-10 §12.8.4.3 — Amplification of Accidental Torsion Ax. TWO METHODS: (A) ASCE 7-10 formula — read story drifts and displacements from 3 load cases (CM, CM+e, CM-e), find worst Δmax/Δavg, compute Ax=(δmax/1.2δavg)², get new e_acc_new=Ax×e_acc; (B) ETABS OAPI — 5-story shear wall, 3 load cases with moment offset at CM, Results.StoryDrifts / JointDispl to extract per-story Ax. Verified: Ax=1.19, e_new=4.76ft, Type 1a EXISTS."
---

# IBC 2012 / ASCE 7-10 §12.8.4.3 — Amplification of Accidental Torsion Ax

**Reference:** ASCE 7-10 §12.8.4.3, Eq. 12.8-14  
**Verified:** SEAOC SDM Vol. 1, DE 34 — 5-story RC shear wall, Story 2 check

---

## Building Description

**5-story RC building frame with shear walls, SDC D, rigid diaphragms**

- Plan: 80 ft × ? (≈ 24.384m × 12.192m)
- Story height: 12 ft (3.658m) per story
- Shear walls A and B resist N-S loads (at opposite ends in X)
- **Given for each story:** Fx, Lx (= 80 ft all stories), xCS, e_acc = ±0.05×Lx

| Level | Fx (kips) | Lx (ft) | e_acc = 0.05Lx (ft) |
|---|---|---|---|
| 5 | 110.0 | 80.0 | ±4.0 |
| 4 | 82.8 | 80.0 | ±4.0 |
| 3 | 65.1 | 80.0 | ±4.0 |
| 2 | 42.1 | 80.0 | ±4.0 |
| 1 | 23.0 | 80.0 | ±4.0 |

**Computer analysis results for Story 2** (three load cases):

| Result | At xCM | At xCM+4ft | At xCM−4ft |
|---|---|---|---|
| Wall shear VA | 185.0 k | 196.0 k | 174.0 k |
| Wall shear VB | 115.0 k | 104.0 k | 126.0 k |
| Story drift ΔA | 0.35 in | 0.37 in | 0.33 in |
| Story drift ΔB | 0.62 in | 0.56 in | **0.68 in** |
| Level 2 disp δA | 0.80 in | 0.85 in | 0.75 in |
| Level 2 disp δB | 1.31 in | 1.18 in | **1.44 in** |

> CM is assumed coincident with CR for this floor (zero inherent torsion) — all torsion comes from accidental eccentricity only.

---

# METHOD A — ASCE 7-10 Formula

## Step 1 — Maximum Wall Forces

**ASCE 7-10 §12.8.4.2:** For each wall, take the maximum from all three load cases:

```python
VA_max = max(185.0, 196.0, 174.0) = 196.0 kips   (from CM+e_acc case)
VB_max = max(115.0, 104.0, 126.0) = 126.0 kips   (from CM-e_acc case)
```

> Each wall gets its maximum from a **different** load case — do not use a single case for all walls.

## Step 2 — Torsional Irregularity Check (§12.3.2.1 Table 12.3-1)

Use the load case that gives the largest Δ_max/Δ_avg ratio:

```python
# For each load case, compute ratio:
cases = {
    "CM":       {"dA": 0.35, "dB": 0.62},   # ratio = 0.62/0.485 = 1.28
    "CM+e_acc": {"dA": 0.37, "dB": 0.56},   # ratio = 0.56/0.465 = 1.20
    "CM-e_acc": {"dA": 0.33, "dB": 0.68},   # ratio = 0.68/0.505 = 1.35 ← worst
}

# Worst case: CM-e_acc
delta_max = 0.68   # in  (story drift at Wall B)
delta_min = 0.33   # in  (story drift at Wall A)
delta_avg = (0.68 + 0.33) / 2 = 0.505 in  ≈ 0.51 in  (book rounds)

ratio = delta_max / delta_avg = 0.68 / 0.51 = 1.33

# ASCE 7-10 Table 12.3-1 thresholds:
# ratio > 1.2 → Type 1a (Torsional Irregularity)     → 1.33 > 1.2 → YES
# ratio > 1.4 → Type 1b (Extreme Torsional)           → 1.33 < 1.4 → NO
```

**Result: Type 1a Torsional Irregularity EXISTS at Story 2.**  
→ A_x amplification is required.

## Step 3 — Amplification Factor Ax (ASCE 7-10 Eq. 12.8-14)

**Formula:**
```
Ax = (δ_max / (1.2 × δ_avg))²     ≤ 3.0
```

Use **absolute floor displacements** (not story drifts) from the worst case (CM-e_acc):

```python
delta_A_abs = 0.75 in   # Level 2 absolute displacement at Wall A
delta_B_abs = 1.44 in   # Level 2 absolute displacement at Wall B  ← largest

delta_max_abs = 1.44 in
delta_avg_abs = (1.44 + 0.75) / 2 = 1.095 in  ≈ 1.10 in  (book rounds)

Ax = (1.44 / (1.2 × 1.10))²
   = (1.44 / 1.32)²
   = (1.091)²
   = 1.19   (book value)
```

> **Key distinction:**
> - **Step 2 irregularity check** uses STORY DRIFTS (Δ = relative displacement floor-to-floor)
> - **Step 3 Ax formula** uses ABSOLUTE FLOOR DISPLACEMENTS (δ = total displacement from base)

## Step 4 — New Accidental Eccentricity

**ASCE 7-10 §12.8.4.3:**
```python
e_acc     = 0.05 × 80 = 4.0 ft
e_acc_new = Ax × e_acc = 1.19 × 4.0 = 4.76 ft
```

Re-run torsion analysis with e_acc_new = 4.76 ft (instead of 4.0 ft) to get final design forces. Ax is NOT recomputed from the second run.

---

# METHOD B — ETABS OAPI

## Step B1 — Build Model: Materials and Sections

```python
model.SetPresentUnits(6)   # kN_m

model.PropMaterial.SetMaterial("C30", 2)
model.PropMaterial.SetMPIsotropic("C30", 30e6, 0.2, 9.9e-6)
model.PropMaterial.SetWeightAndMass("C30", 1, 25.0)

model.PropArea.SetShell_1("WALL300", 1, False, "C30", "C30", 0, 0.30)   # 300mm wall
```

## Step B2 — Geometry (5 stories, 2 shear walls)

```python
Lx = 24.384   # m (80 ft)
Ly = 12.192   # m (40 ft)
hs = 3.658    # m (12 ft) story height
n_stories = 5

# Wall lengths: choose to give representative rigidity ratio
Lw_A = 3.5   # m — longer/stiffer wall (Wall A at x=0)
Lw_B = 2.5   # m — shorter/more flexible (Wall B at x=Lx)

nodes = {}
Z = [hs * iz for iz in range(n_stories+1)]   # [0, 3.658, 7.316, ...]

# Create wall corner nodes for all stories
for iz, zv in enumerate(Z):
    # Wall A at x=0, centred in Y
    yA = Ly/2 - Lw_A/2
    t = model.PointObj.AddCartesian(0, yA,        zv); nodes[("A","L",iz)] = t[0]
    t = model.PointObj.AddCartesian(0, yA+Lw_A,   zv); nodes[("A","R",iz)] = t[0]
    # Wall B at x=Lx
    yB = Ly/2 - Lw_B/2
    t = model.PointObj.AddCartesian(Lx, yB,       zv); nodes[("B","L",iz)] = t[0]
    t = model.PointObj.AddCartesian(Lx, yB+Lw_B,  zv); nodes[("B","R",iz)] = t[0]
    # CM node at each floor level
    t = model.PointObj.AddCartesian(Lx/2, Ly/2, zv); nodes[("CM", iz)] = t[0]

# Fix base nodes (iz=0)
for wall in ["A", "B"]:
    for side in ["L", "R"]:
        model.PointObj.SetRestraint(nodes[(wall,side,0)], [True]*6)
```

## Step B3 — Wall Shell Panels (one panel per story per wall)

```python
for wall in ["A", "B"]:
    for iz in range(n_stories):
        pts = [nodes[(wall,"L",iz)],  nodes[(wall,"R",iz)],
               nodes[(wall,"R",iz+1)], nodes[(wall,"L",iz+1)]]
        model.AreaObj.AddByPoint(4, pts, "WALL300")
```

## Step B4 — Rigid Diaphragm at Each Floor Level

```python
for iz in range(1, n_stories+1):
    dname = f"RD_{iz}"
    model.Diaphragm.Add(dname, 1)   # type 1 = XY-plane rigid
    for wall in ["A", "B"]:
        for side in ["L", "R"]:
            model.PointObj.SetDiaphragm(nodes[(wall,side,iz)], dname, 0)
    model.PointObj.SetDiaphragm(nodes[("CM",iz)], dname, 0)
```

## Step B5 — Three Load Cases with Accidental Eccentricity

```python
# ELF forces per story (kips converted to kN)
k2kN = 4.4482
Fx_kips = {5: 110.0, 4: 82.8, 3: 65.1, 2: 42.1, 1: 23.0}
e_acc_m = 0.05 * Lx   # = 1.219 m (4.0 ft)

# Three load patterns:
# LC1: forces at CM (no eccentricity)
# LC2: forces at CM + accidental moment Mz = Fx × e_acc  (positive offset)
# LC3: forces at CM − accidental moment Mz = Fx × e_acc  (negative offset)
for lc in ["EQ_CM", "EQ_CM_pos", "EQ_CM_neg"]:
    model.LoadPatterns.Add(lc, 5, 0, True)

for iz in range(1, n_stories+1):
    cm_node = nodes[("CM", iz)]
    Fy = Fx_kips[iz] * k2kN   # lateral force in Y (N-S)
    Mz = Fy * e_acc_m           # accidental torsion moment

    # LC1: direct force only, no torsion
    model.PointObj.SetLoadForce(cm_node, "EQ_CM",
        [0, Fy, 0, 0, 0, 0], False, "Global")
    # LC2: force + positive torsion
    model.PointObj.SetLoadForce(cm_node, "EQ_CM_pos",
        [0, Fy, 0, 0, 0, +Mz], False, "Global")
    # LC3: force + negative torsion
    model.PointObj.SetLoadForce(cm_node, "EQ_CM_neg",
        [0, Fy, 0, 0, 0, -Mz], False, "Global")
```

## Step B6 — Analyze

```python
model.File.Save("D:\\Works\\IBC2012_DE34_TorsionAmp.EDB")
model.Analyze.SetRunCaseFlag("", False, True)
for lc in ["EQ_CM", "EQ_CM_pos", "EQ_CM_neg"]:
    model.Analyze.SetRunCaseFlag(lc, True, False)
ret = model.Analyze.RunAnalysis()
assert ret == 0
```

## Step B7 — Read Floor Displacements and Compute Ax Per Story

```python
model.SetPresentUnits(6)   # kN_m

# Rebuild nodes dict from ETABS (state not persisted between calls)
Lx = 24.384; Ly = 12.192; hs = 3.658; n_stories = 5
tol = 0.01

tl = model.PointObj.GetNameList()
nodes = {}
for pn in list(tl[1]):
    cx = model.PointObj.GetCoordCartesian(pn, 0, 0, 0)
    x, y, z = cx[1], cx[2], cx[3]
    # Identify CM nodes (at building centre)
    if abs(x - Lx/2) < tol and abs(y - Ly/2) < tol:
        iz = round(z / hs)
        if 0 <= iz <= n_stories:
            nodes[("CM", iz)] = pn
    # Wall A nodes (x=0)
    if abs(x) < tol:
        iz = round(z / hs)
        nodes[("A", z, iz)] = pn
    # Wall B nodes (x=Lx)
    if abs(x - Lx) < tol:
        iz = round(z / hs)
        nodes[("B", z, iz)] = pn

def get_U2(pn, lc):
    """Get Y-direction displacement at node pn for load case lc (m)."""
    r = model.Results.JointDispl(pn, 0, 0)
    # r[7] = U2 (Y-direction) list; find index matching load case
    # For single load case runs, index 0 applies
    return r[7][0]

Ax_per_story = {}
for story in range(1, n_stories+1):
    # Identify wall A and B nodes at this floor level
    zA = story * hs
    # Get all nodes on Wall A at this floor
    A_nodes = [v for k, v in nodes.items() if k[0] == "A" and k[2] == story]
    B_nodes = [v for k, v in nodes.items() if k[0] == "B" and k[2] == story]

    # For each load case, get average displacement of wall A and wall B nodes
    results = {}
    for lc in ["EQ_CM", "EQ_CM_pos", "EQ_CM_neg"]:
        if A_nodes and B_nodes:
            dA = sum(get_U2(pn, lc) for pn in A_nodes) / len(A_nodes) * 1000  # mm
            dB = sum(get_U2(pn, lc) for pn in B_nodes) / len(B_nodes) * 1000  # mm
            results[lc] = (dA, dB)

    # Find worst case for Ax: largest delta_max_abs / delta_avg_abs
    worst_Ax = 0
    worst_case = None
    for lc, (dA, dB) in results.items():
        d_max = max(abs(dA), abs(dB))
        d_avg = (abs(dA) + abs(dB)) / 2
        if d_avg > 0:
            Ax_cand = min((d_max / (1.2 * d_avg))**2, 3.0)
            if Ax_cand > worst_Ax:
                worst_Ax = Ax_cand
                worst_case = lc

    Ax_per_story[story] = worst_Ax
    print(f"Story {story}: Ax = {worst_Ax:.3f}  (worst case: {worst_case})")

print("\nApply Ax to e_acc for each story:")
e_acc_m = 0.05 * Lx
for story, Ax in Ax_per_story.items():
    e_new_m = Ax * e_acc_m
    e_new_ft = e_new_m / 0.3048
    print(f"  Story {story}: Ax={Ax:.2f}  e_new = {Ax:.2f}×{e_acc_m:.3f}m = {e_new_m:.3f}m ({e_new_ft:.2f}ft)")
```

## Step B8 — Read Wall Base Shears

```python
# Get maximum Y-shear at base of Wall A and Wall B across all load cases
for wall in ["A", "B"]:
    V_max = 0
    V_max_lc = None
    # Base nodes (iz=0) for this wall
    base_nodes = [v for k, v in nodes.items() if k[0] == wall and k[2] == 0]
    for lc in ["EQ_CM", "EQ_CM_pos", "EQ_CM_neg"]:
        V_total = 0
        for pn in base_nodes:
            r = model.Results.JointReact(pn, 0, 0)
            # r[8][0] = F2 = Y-direction reaction
            if r[0] == 0:
                V_total += r[8][0]   # kN
        V_kips = abs(V_total) / 4.4482
        if V_kips > V_max:
            V_max = V_kips
            V_max_lc = lc
    print(f"Wall {wall}: V_max = {V_max:.1f} kips  (case: {V_max_lc})")
# Expected: VA_max ≈ 196, VB_max ≈ 126 kips
```

---

## Verified Results

### Method A — Formula

| Step | Parameter | Formula | Value |
|---|---|---|---|
| 1 | VA_max | max(185, 196, 174) | **196.0 kips** (CM+e case) |
| 1 | VB_max | max(115, 104, 126) | **126.0 kips** (CM-e case) |
| 2 | Worst Δ_max | from CM-e_acc case: ΔB | **0.68 in** |
| 2 | Δ_avg | (0.68+0.33)/2 | **0.51 in** (book rounds 0.505→0.51) |
| 2 | Δ_max/Δ_avg | 0.68/0.51 | **1.33 > 1.2 → Type 1a ✓** |
| 3 | δ_max (abs) | Level 2 disp at Wall B, CM-e case | **1.44 in** |
| 3 | δ_avg (abs) | (1.44+0.75)/2 | **1.10 in** (book rounds 1.095→1.10) |
| 3 | **Ax** | (1.44/(1.2×1.10))² | **1.19** ✓ |
| 4 | **e_acc_new** | 1.19 × 4.0 ft | **4.76 ft** ✓ |

### Method B — ETABS API Calls

| Purpose | ETABS OAPI Call | Output field |
|---|---|---|
| Apply force + torsion at CM | `PointObj.SetLoadForce(cm_node, lc, [0,Fy,0,0,0,±Mz], ...)` | — |
| Assign rigid diaphragm | `Diaphragm.Add(dname, 1)` + `PointObj.SetDiaphragm(node, dname, 0)` | — |
| Read floor displacement | `Results.JointDispl(node, 0, 0)` | `r[7][0]` = U2 (Y) in m |
| Read wall base shear | `Results.JointReact(base_node, 0, 0)` | `r[8][0]` = F2 (Y) in kN |

---

## Key Distinctions

| Check | Use | Why |
|---|---|---|
| Irregularity Type 1a/1b | **Story DRIFTS** Δ = floor disp − floor below | Drift captures story deformation shape |
| Ax formula | **Absolute displacements** δ = total from base | Eq. 12.8-14 uses δ, not Δ |
| Max wall force | Take **max across all 3 load cases** per wall | Different walls are worst in different cases |
| Ax iteration | **No** — one pass only; do not recompute Ax with amplified torsion | §12.8.4.3 explicitly prohibits iteration |

---

## ASCE 7-10 §12.8.4.3 — Ax Flow

```
Step 1: Run 3 load cases per story (CM, CM+e_acc, CM-e_acc)
         ↓
Step 2: For each case, compute Δmax/Δavg using STORY DRIFTS
         → If max ratio > 1.2: Type 1a exists → Ax required
         → If max ratio > 1.4: Type 1b exists
         ↓
Step 3: Ax = (δmax_abs / 1.2δavg_abs)²  using ABSOLUTE DISPLACEMENTS, worst case, ≤ 3.0
         ↓
Step 4: e_acc_new = Ax × e_acc  (replace original 5% eccentricity)
         ↓
Step 5: Re-run torsion analysis with e_acc_new → read final design wall shears
         (Ax is NOT recomputed from this second run)
```
