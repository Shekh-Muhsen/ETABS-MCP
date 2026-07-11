---
name: ibc2012-de18-soft-story
description: "IBC 2012 / ASCE 7-10 §12.3.2.2 — Vertical Irregularity Type 1a (Soft Story) and Type 1b (Extreme Soft Story). Accepts floor displacements from ETABS or input; computes story drift ratios; checks 70%/80% (Type 1a) and 60%/70% (Type 1b) limits for all stories. Verified against SEAOC SDM Vol. 1 DE 18: Type 1a EXISTS at story 1 (DR1/DR2 = 1.60), Type 1b EXISTS at story 1."
---

# IBC 2012 / ASCE 7-10 §12.3.2.2 — Soft Story Irregularity (Type 1a / 1b)

**Reference:** ASCE 7-10 §12.3.2.2, Table 12.3-2  
**Book values:** SEAOC SDM Vol. 1, DE 18 — 5-story concrete SMRF, SDC D

---

## Code Procedure — ASCE 7-10 §12.3.2.2

**Drift-ratio method** (recommended when story heights differ; equivalent to stiffness comparison):

Compute story drift ratios: `DR_i = Δ_i / h_i` where `Δ_i = δ_i − δ_{i-1}` (story drift).

**Type 1a — Soft Story exists if ANY story satisfies EITHER:**
```
DR_i > (1/0.70) × DR_{i+1}      [70% stiffness = 1/0.70 drift ratio limit]
DR_i > (1/0.80) × avg(DR_{i+1}, DR_{i+2}, DR_{i+3})
```

**Type 1b — Extreme Soft Story exists if ANY story satisfies EITHER:**
```
DR_i > (1/0.60) × DR_{i+1}
DR_i > (1/0.70) × avg(DR_{i+1}, DR_{i+2}, DR_{i+3})
```

**Exception (§12.3.2.2):** Irregularities Type 1a, 1b, 2 do NOT apply where no story drift ratio exceeds 130% of the story above:
```
max(DR_i / DR_{i+1}) ≤ 1.30 for all i  →  no irregularity check required
```

**Alternative — Stiffness-based method (ETABS):**
```
K_i = V_i / Δ_i   (story shear / story displacement)
```
Apply stiffness ratios: `K_i < 0.70×K_{i+1}` (Type 1a) or `K_i < 0.60×K_{i+1}` (Type 1b).

| Type | Condition 1 | Condition 2 |
|---|---|---|
| **1a Soft Story** | DR_i > (1/0.70)×DR_above | DR_i > (1/0.80)×avg(3 above) |
| **1b Extreme** | DR_i > (1/0.60)×DR_above | DR_i > (1/0.70)×avg(3 above) |

---

## Building Description

**5-story concrete Special Moment-Resisting Frame (SMRF), SDC D**

- 4 bays × 4 bays plan (generic; Figure 18-1 geometry not given in text)
- **Story 1: 3.658m (12 ft)** — taller first story (commercial/retail)
- **Stories 2–5: 3.048m (10 ft each)**
- Total height: 3.658 + 4 × 3.048 = 15.85m (52 ft)
- C30 concrete columns and beams, SDC D detailing (SMRF)
- ELF analysis per §12.8

**Key displacements (from book, Figure 18-1):**

| Story | δ_x (in) | Drift Δ (in) | h (in) | DR = Δ/h |
|---|---|---|---|---|
| 5 | 2.02 | 0.27 | 120 | 0.00225 |
| 4 | 1.75 | 0.30 | 120 | 0.00250 |
| 3 | 1.45 | 0.37 | 120 | 0.00308 |
| 2 | 1.08 | 0.37 | 120 | 0.00308 |
| 1 | 0.71 | 0.71 | 144 | **0.00493** |

---

## Hand Calculation — Soft Story Check Function

```python
def soft_story_check(delta_x, h_story):
    """
    ASCE 7-10 §12.3.2.2 soft story check — drift ratio method.
    
    delta_x : list of floor displacements from bottom [δ1, δ2, ..., δn], same units
    h_story : list of story heights [h1, h2, ..., hn], same units
    
    Returns dict with story results and irregularity flags.
    """
    n = len(delta_x)
    assert len(h_story) == n

    # Story drifts and drift ratios
    dr = []
    for i in range(n):
        drift = delta_x[i] if i == 0 else delta_x[i] - delta_x[i-1]
        dr.append(drift / h_story[i])

    # Exception: check if max DR ratio ≤ 1.30 (no check needed)
    max_ratio = max(dr[i] / dr[i+1] for i in range(n-1)) if n > 1 else 0.0
    if max_ratio <= 1.30:
        return {"exception_applies": True, "max_dr_ratio": max_ratio,
                "type1a": False, "type1b": False}

    results = []
    type1a = False
    type1b = False

    for i in range(n):
        # DR of story above (i+1)
        dr_above = dr[i+1] if i+1 < n else None
        # Average DR of 3 stories above
        avg3 = sum(dr[i+1:i+4]) / len(dr[i+1:i+4]) if i+1 < n else None

        # Type 1a checks
        c1a_1 = (dr[i] > dr_above / 0.70) if dr_above is not None else False
        c1a_2 = (dr[i] > avg3    / 0.80) if avg3    is not None else False
        is_1a = c1a_1 or c1a_2

        # Type 1b checks
        c1b_1 = (dr[i] > dr_above / 0.60) if dr_above is not None else False
        c1b_2 = (dr[i] > avg3    / 0.70) if avg3    is not None else False
        is_1b = c1b_1 or c1b_2

        if is_1a: type1a = True
        if is_1b: type1b = True

        results.append({
            "story": i+1, "DR": dr[i], "DR_above": dr_above, "avg3_above": avg3,
            "type1a": is_1a, "type1b": is_1b,
            "cond1a_1": c1a_1, "cond1a_2": c1a_2,
            "cond1b_1": c1b_1, "cond1b_2": c1b_2,
        })

    return {
        "exception_applies": False, "max_dr_ratio": max_ratio,
        "type1a": type1a, "type1b": type1b,
        "stories": results,
    }
```

## Book Verification

```python
# DE 18 — given displacements (inches), bottom story first
delta_x = [0.71, 1.08, 1.45, 1.75, 2.02]
h_story = [144, 120, 120, 120, 120]   # inches; story 1 = 12 ft, stories 2-5 = 10 ft

r = soft_story_check(delta_x, h_story)

print("DE 18 — Soft Story Check (ASCE 7-10 §12.3.2.2)")
print(f"  Exception (max DR ratio ≤ 1.30)? {r['exception_applies']} "
      f"(max ratio = {r['max_dr_ratio']:.2f})")
for s in r["stories"]:
    print(f"  Story {s['story']}: DR={s['DR']:.5f}  "
          f"1a={s['type1a']}  1b={s['type1b']}")
print(f"  TYPE 1a (Soft Story):         {'EXISTS' if r['type1a'] else 'NONE'}")
print(f"  TYPE 1b (Extreme Soft Story): {'EXISTS' if r['type1b'] else 'NONE'}")

# Expected: Type 1a EXISTS (story 1), Type 1b EXISTS (story 1)
# Exception: max DR ratio = 0.00493/0.00308 = 1.60 > 1.30 → check required
```

---

## ETABS Procedure — Extract Story Drift Ratios

Use this to get `delta_x` and `h_story` from a live ETABS model.

```python
model.SetPresentUnits(6)   # kN_m

# Story definition (adjust to match actual model)
story_names = ["Story1", "Story2", "Story3", "Story4", "Story5"]
h_m = [3.658, 3.048, 3.048, 3.048, 3.048]   # story heights in m
lc  = "EQ_X"   # load case

# Extract center-of-mass displacement at each floor
# Option A: use story results (if stories defined in ETABS)
delta_x_m = []
for story in story_names:
    r = model.Results.StoryDrifts(story, lc, 0, 0)
    # r: [ret, NumberResults, Story, LoadCase, StepType, StepNum,
    #      Direction, Drift, Label, X, Y, Z]
    # Direction 1 = UX; find matching story
    if r[0] == 0 and r[1] > 0:
        # Get displacement, not drift (story displacement from base)
        pass  # See Option B below

# Option B: query specific joint displacement at center-of-mass node
# For each floor, identify the CM node (center of plan at that elevation)
# cm_nodes = {1: "node_id_floor1", 2: "node_id_floor2", ...}  # from model
cm_z = {1: 3.658, 2: 6.706, 3: 9.754, 4: 12.802, 5: 15.850}

# Get all nodes, find CM node at each floor Z
tl = model.PointObj.GetNameList()
cm_nodes = {}
tol = 0.01
target_x, target_y = 12.0, 12.0   # center of plan; adjust to model

for pn in list(tl[1]):
    cx = model.PointObj.GetCoordCartesian(pn, 0, 0, 0)
    x, y, z = cx[1], cx[2], cx[3]
    for floor, zf in cm_z.items():
        if abs(z - zf) < tol and abs(x - target_x) < tol and abs(y - target_y) < tol:
            cm_nodes[floor] = pn

# Extract U1 (X-direction displacement) at each CM node
delta_x_m = []
for floor in range(1, 6):
    pn = cm_nodes[floor]
    r = model.Results.JointDispl(pn, 0, 0)
    delta_x_m.append(r[6][0])   # U1 in m

# Convert to consistent units (m or in) and run check
h_m_list = [3.658, 3.048, 3.048, 3.048, 3.048]
r = soft_story_check(delta_x_m, h_m_list)
# (same function; ratio is dimensionless)
```

---

## ETABS Model Build — 5-Story Concrete SMRF

```python
ret = model.SetPresentUnits(6)   # kN_m

# Materials
ret = model.PropMaterial.SetMaterial("C30", 2)
ret = model.PropMaterial.SetMPIsotropic("C30", 30000000.0, 0.2, 9.9e-6)
ret = model.PropMaterial.SetOConcrete_1("C30", 30000.0, False, 0.0, 2, 1, 0.003, 0.005, -0.1)
ret = model.PropMaterial.SetWeightAndMass("C30", 1, 25.0)

# Sections — heavier ground story column to model typical SMRF
ret = model.PropFrame.SetRectangle("COL600", "C30", 0.6, 0.6)   # story 1
ret = model.PropFrame.SetRectangle("COL500", "C30", 0.5, 0.5)   # stories 2-5
ret = model.PropFrame.SetRectangle("BM400x600", "C30", 0.6, 0.4)
ret = model.PropArea.SetSlab("SLAB150", 0, 0, "C30", 0.15)

# Grid
X = [0, 6, 12, 18, 24]   # 4 bays × 6m
Y = [0, 6, 12, 18, 24]
# Story 1 = 3.658m (12ft); stories 2-5 = 3.048m (10ft)
Z = [0, 3.658, 6.706, 9.754, 12.802, 15.850]

nodes = {}
for iz, zv in enumerate(Z):
    for iy, yv in enumerate(Y):
        for ix, xv in enumerate(X):
            t = model.PointObj.AddCartesian(xv, yv, zv)
            nodes[(ix, iy, iz)] = t[0]

# Fixed bases
for iy in range(5):
    for ix in range(5):
        model.PointObj.SetRestraint(nodes[(ix,iy,0)], [True]*6)

# Columns — COL600 story 1, COL500 stories 2-5
for iz in range(5):
    sec = "COL600" if iz == 0 else "COL500"
    for iy in range(5):
        for ix in range(5):
            model.FrameObj.AddByPoint(nodes[(ix,iy,iz)], nodes[(ix,iy,iz+1)], sec)

# Force-assign sections
tl = model.FrameObj.GetNameList()
ptf = {}
for fn in list(tl[1]):
    pt = model.FrameObj.GetPoints(fn)
    ptf[frozenset([pt[0], pt[1]])] = fn

for iz in range(5):
    sec = "COL600" if iz == 0 else "COL500"
    for iy in range(5):
        for ix in range(5):
            key = frozenset([nodes[(ix,iy,iz)], nodes[(ix,iy,iz+1)]])
            fn = ptf.get(key)
            if fn:
                model.FrameObj.SetSection(fn, sec)

# Beams
for iz in range(1, 6):
    for iy in range(5):
        for ix in range(4):
            t = model.FrameObj.AddByPoint(nodes[(ix,iy,iz)], nodes[(ix+1,iy,iz)], "BM400x600")
            model.FrameObj.SetReleases(t[0], [False]*4+[True,True], [False]*4+[True,True])
    for iy in range(4):
        for ix in range(5):
            t = model.FrameObj.AddByPoint(nodes[(ix,iy,iz)], nodes[(ix,iy+1,iz)], "BM400x600")
            model.FrameObj.SetReleases(t[0], [False]*4+[True,True], [False]*4+[True,True])

# Slabs
for iz in range(1, 6):
    for iy in range(4):
        for ix in range(4):
            pts = [nodes[(ix,iy,iz)], nodes[(ix+1,iy,iz)],
                   nodes[(ix+1,iy+1,iz)], nodes[(ix,iy+1,iz)]]
            model.AreaObj.AddByPoint(4, pts, "SLAB150")

# ELF loads — triangular distribution
# Cs = 0.10, W_floor = 25×(24^2)×0.15 = 2160 kN per floor, W_total = 10800 kN
# V = 0.10 × 10800 = 1080 kN; distribute as Fx = V × hx^k / Σ(wi×hi^k)
model.LoadPatterns.Add("EQ_X", 5, 0, True)

floor_Z = [Z[iz] for iz in range(1, 6)]
k = 1.0   # k=1 for T < 0.5s (approximate)
sum_wh = sum(floor_Z)   # all floors same weight
V = 1080.0
Fx = [V * hz / sum_wh for hz in floor_Z]

n_nodes_floor = 25
for iz_idx, iz in enumerate(range(1, 6)):
    fx_node = Fx[iz_idx] / n_nodes_floor
    for iy in range(5):
        for ix in range(5):
            model.PointObj.SetLoadForce(nodes[(ix,iy,iz)], "EQ_X",
                                        [fx_node, 0, 0, 0, 0, 0], False, "Global")

model.File.Save("D:\\Works\\IBC2012_DE18_SoftStory.EDB")
model.Analyze.SetRunCaseFlag("", False, True)
model.Analyze.SetRunCaseFlag("EQ_X", True, False)
ret = model.Analyze.RunAnalysis()
assert ret == 0
```

---

## Verified Results — Book Values (DE 18)

Floor displacements from Figure 18-1 (given):

| Story | δ_x (in) | Drift Δ (in) | h (in) | DR = Δ/h | 0.7×DR | 0.8×DR | Avg3 above |
|---|---|---|---|---|---|---|---|
| 5 | 2.02 | 0.27 | 120 | 0.00225 | — | — | — |
| 4 | 1.75 | 0.30 | 120 | 0.00250 | — | — | — |
| 3 | 1.45 | 0.37 | 120 | 0.00308 | — | — | — |
| 2 | 1.08 | 0.37 | 120 | 0.00308 | 0.00247 | — | 0.00261 |
| **1** | **0.71** | **0.71** | **144** | **0.00493** | **0.00345** | **0.00394** | **0.00289** |

**Exception check:** DR₁/DR₂ = 0.00493/0.00308 = **1.60 > 1.30** → check NOT waived.

**Type 1a — Soft Story (§12.3.2.2):**
- Cond. 1: 0.70×DR₁ = 0.00345 > DR₂ = 0.00308 → **NOT OK → soft story** ✓
- Cond. 2: 0.80×DR₁ = 0.00394 > avg(DR₂,DR₃,DR₄) = 0.00289 → **NOT OK → soft story** ✓
- **Type 1a EXISTS at Story 1** ← matches book ✓

**Type 1b — Extreme Soft Story (§12.3.2.2):**
- Cond. 1: 0.60×DR₁ = 0.00296 < DR₂ = 0.00308 → OK (not extreme by Cond. 1)
- Cond. 2: 0.70×DR₁ = 0.00345 > avg(DR₂,DR₃,DR₄) = 0.00289 → **NOT OK → extreme soft story** ✓
- **Type 1b EXISTS at Story 1** ← matches book ✓

---

## Consequences

| Consequence | Reference |
|---|---|
| Type 1a → Modal RSA required (SDC D) | Table 12.6-1 |
| Type 1b → Not permitted in SDC E or F | §12.3.3.1 |
| Type 1b → SDC D: permitted but RSA required | Table 12.6-1 |
| If modal RSA performed, Type 1a/1b/2 need not be checked | §12.3.2.2 Exception 2 |

---

## Key Notes

- **Drift-ratio method is preferred** when story heights differ (normalizes for height effect)
- Story 1 is tall (144" = 12 ft vs. 120" = 10 ft upper stories) — this is the classic "soft story" configuration (commercial at grade)
- Even when only Condition 2 of Type 1b fails, the extreme soft story classification applies
- **Exception §12.3.2.2:** if max(DR_i / DR_{i+1}) ≤ 1.30 for all stories, no check is required
- `soft_story_check()` function handles all stories at once; loop from ground up
- Story heights must match what the ETABS model uses (convert m ↔ in as needed)
