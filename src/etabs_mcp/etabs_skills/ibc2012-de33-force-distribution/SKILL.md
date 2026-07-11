---
name: ibc2012-de33-force-distribution
description: "IBC 2012 / ASCE 7-10 §12.8.4 — Horizontal Distribution of Forces with Rigid Diaphragm. TWO METHODS: (A) ASCE 7-10 9-step formula — CR, eccentricity, J, direct shear, torsional shear, irregularity Type 1b, Ax amplification, design shears; (B) ETABS OAPI — ShellThin walls, rigid diaphragm, JointReact + CenterOfMassAndRigidity. Verified: V_A=61.8 kips, V_B=49.3 kips, Ax=1.47, Type 1b EXISTS."
---

# IBC 2012 / ASCE 7-10 §12.8.4 — Horizontal Distribution of Forces (Rigid Diaphragm)

**Reference:** ASCE 7-10 §12.8.4, §12.8.4.2, §12.8.4.3  
**Verified:** SEAOC SDM Vol. 1, DE 33

---

## Building Description

**1-story building, N-S seismic load, rigid roof diaphragm:**

```
Plan (80 ft × 40 ft = 24.384m × 12.192m):

x=0                    x=40ft(12.19m)         x=80ft(24.38m)
Wall A                 CM(40,20)ft             Wall B
R=300 k/in             ·                       R=100 k/in
  |                                               |
y=40ft(12.19m) ┌──────────── Wall C (R=200) ─────┐
               │                                  │
y=20ft(6.10m)  │      · CM                        │
               │                                  │
y=0            └──────────── Wall D (R=200) ─────┘
```

| Wall | x or y | Rigidity R | Resists | Dir to CR |
|---|---|---|---|---|
| A | x = 0 ft | 300 kip/in | E-W shear | d_A = 20 ft from CR |
| B | x = 80 ft | 100 kip/in | E-W shear | d_B = 60 ft from CR |
| C | y = 40 ft | 200 kip/in | N-S shear | d_C = 20 ft from CR |
| D | y = 0 ft | 200 kip/in | N-S shear | d_D = 20 ft from CR |

**Given:** V = 100 kips N-S direction, CM = (40, 20) ft

---

# METHOD A — ASCE 7-10 Formula

## Step 1 — Center of Rigidity (CR)

**ASCE 7-10 §12.8.4 — Formula:**
```
x_CR = Σ(R_i × x_i) / Σ(R_i)    walls in same direction as load
y_CR = Σ(R_i × y_i) / Σ(R_i)    walls perpendicular to load
```

```python
R_A, R_B = 300, 100   # kip/in  (N-S walls at x=0, x=80)
R_C, R_D = 200, 200   # kip/in  (E-W walls at y=40, y=0)

x_CR = (R_A*0 + R_B*80) / (R_A + R_B)   # = 100*80/400 = 20 ft
y_CR = (R_C*40 + R_D*0) / (R_C + R_D)   # = 200*40/400 = 20 ft
# CR = (20, 20) ft
```

## Step 2 — Eccentricity

**ASCE 7-10 §12.8.4.2:**
```python
e     = x_CM - x_CR   # 40 - 20 = 20 ft   (actual eccentricity)
e_acc = 0.05 * 80     # = 4.0 ft           (5% of building dimension)
```

## Step 3 — Torsional Rigidity J

**Formula:**  `J = Σ R_i × d_i²`  (sum over ALL walls)

```python
d_A = x_CR - 0    # 20 ft
d_B = 80 - x_CR   # 60 ft
d_C = 40 - y_CR   # 20 ft
d_D = y_CR - 0    # 20 ft

J = R_A*d_A**2 + R_B*d_B**2 + R_C*d_C**2 + R_D*d_D**2
  = 300*20² + 100*60² + 200*20² + 200*20²
  = 120,000 + 360,000 + 80,000 + 80,000
  = 640,000 (kip/in)·ft²
```

## Step 4 — Direct Shear

**ASCE 7-10 Eq. 12.8-13:**  proportional to rigidity
```python
V_d_A = R_A / (R_A + R_B) * V   # 300/400 * 100 = 75.0 kips
V_d_B = R_B / (R_A + R_B) * V   # 100/400 * 100 = 25.0 kips
```

## Step 5 — Torsional Shear (for Irregularity Check)

**ASCE 7-10 §12.8.4 — Formula:**
```
V_t,i = T × R_i × d_i / J     where T = V × e_total
```

For **irregularity check only**, use `e_total = e + e_acc` (most severe):
```python
T_check = V * (e + e_acc)   # 100 * 24 = 2,400 kip·ft

V_t_A = T_check * R_A * d_A / J   # 2400*300*20/640000 = 22.5 kips  (SUBTRACTS from V_d_A)
V_t_B = T_check * R_B * d_B / J   # 2400*100*60/640000 = 22.5 kips  (ADDS to V_d_B)
```

**Sign rule:** CM is east of CR → counterclockwise torsion →
- Wall A (left): torsion pushes it west → opposes direct shear → **subtract**
- Wall B (right): torsion pushes it east → adds to direct shear → **add**

## Step 6 — Torsional Irregularity Check (§12.3.2.1)

```python
V_A_check = V_d_A - V_t_A   # 75.0 - 22.5 = 52.5 kips
V_B_check = V_d_B + V_t_B   # 25.0 + 22.5 = 47.5 kips

delta_A = V_A_check / R_A   # 52.5/300 = 0.175 in
delta_B = V_B_check / R_B   # 47.5/100 = 0.475 in

delta_avg = (delta_A + delta_B) / 2   # (0.175+0.475)/2 = 0.325 in
delta_max = delta_B                    # 0.475 in

ratio = delta_max / delta_avg   # 0.475/0.325 = 1.46

# Thresholds (ASCE 7-10 Table 12.3-1):
# ratio > 1.2  → Type 1a (Torsional Irregularity)
# ratio > 1.4  → Type 1b (Extreme Torsional Irregularity)
# 1.46 > 1.4  → TYPE 1b EXISTS
```

## Step 7 — Amplification Factor Ax (§12.8.4.3)

**ASCE 7-10 Eq. 12.8-14:**
```python
Ax = (delta_max / (1.2 * delta_avg))**2
   = (0.475 / (1.2 * 0.325))**2
   = (1.218)**2
   = 1.48   (≤ 3.0)
# Book value: 1.47  (small rounding difference)
```

> Ax is computed ONCE from unamplified displacements. NOT iterative.

## Step 8 — Amplified Torsional Shears

**Only e_acc is amplified — not the actual e:**
```python
# Wall A (subtractive): minimise subtraction → use e - Ax*e_acc
e_eff_A = e - Ax * e_acc   # 20 - 1.48*4 = 14.07 ft
T_A     = V * e_eff_A       # 100 * 14.07 = 1407 kip·ft
V_t_A   = T_A * R_A * d_A / J   # 1407*300*20/640000 = 13.2 kips

# Wall B (additive): maximise addition → use e + Ax*e_acc
e_eff_B = e + Ax * e_acc   # 20 + 1.48*4 = 25.93 ft
T_B     = V * e_eff_B       # 100 * 25.93 = 2593 kip·ft
V_t_B   = T_B * R_B * d_B / J   # 2593*100*60/640000 = 24.3 kips
```

## Step 9 — Total Design Shears

```python
V_A = V_d_A - V_t_A   # 75.0 - 13.2 = 61.8 kips  ← DESIGN VALUE
V_B = V_d_B + V_t_B   # 25.0 + 24.3 = 49.3 kips  ← DESIGN VALUE
```

---

# METHOD B — ETABS OAPI

## Step B1 — Build Model: Materials and Wall Property

```python
model.SetPresentUnits(6)   # kN_m

model.PropMaterial.SetMaterial("C30", 2)
model.PropMaterial.SetMPIsotropic("C30", 30e6, 0.2, 9.9e-6)
model.PropMaterial.SetWeightAndMass("C30", 1, 25.0)

# ShellThin wall section, 250mm thick
model.PropArea.SetShell_1("WALL250", 1, False, "C30", "C30", 0, 0.25)
```

## Step B2 — Grid Nodes

```python
# Building: 24.384m × 12.192m (80ft × 40ft), story h = 3.658m (12ft)
Lx = 24.384   # m
Ly = 12.192   # m
h  = 3.658    # m

# Wall lengths calibrated for R ratio A:B:C:D = 3:1:2:2
# Solved from cantilever formula R = 1/(h³/3EI + 1.2h/GA):
Lw = {"A": 3.108, "B": 2.000, "C": 2.623, "D": 2.623}   # m

# Key nodes (base and top for each wall)
nodes = {}
def add_node(tag, x, y, z):
    t = model.PointObj.AddCartesian(x, y, z)
    nodes[tag] = t[0]
    return t[0]

# Wall A: at x=0, centred in Y, spans h in Z
yA = Ly/2 - Lw["A"]/2
add_node("A_bot_L", 0, yA,         0)
add_node("A_bot_R", 0, yA+Lw["A"], 0)
add_node("A_top_L", 0, yA,         h)
add_node("A_top_R", 0, yA+Lw["A"], h)

# Wall B: at x=Lx
yB = Ly/2 - Lw["B"]/2
add_node("B_bot_L", Lx, yB,         0)
add_node("B_bot_R", Lx, yB+Lw["B"], 0)
add_node("B_top_L", Lx, yB,         h)
add_node("B_top_R", Lx, yB+Lw["B"], h)

# Wall C: at y=Ly
xC = Lx/2 - Lw["C"]/2
add_node("C_bot_L", xC,         Ly, 0)
add_node("C_bot_R", xC+Lw["C"], Ly, 0)
add_node("C_top_L", xC,         Ly, h)
add_node("C_top_R", xC+Lw["C"], Ly, h)

# Wall D: at y=0
xD = Lx/2 - Lw["D"]/2
add_node("D_bot_L", xD,         0, 0)
add_node("D_bot_R", xD+Lw["D"], 0, 0)
add_node("D_top_L", xD,         0, h)
add_node("D_top_R", xD+Lw["D"], 0, h)

# CM node at roof level
x_CM_m = 40 * 0.3048   # 12.192m
y_CM_m = 20 * 0.3048   # 6.096m
add_node("CM", x_CM_m, y_CM_m, h)
```

## Step B3 — Wall Shell Panels

```python
for wall in ["A", "B", "C", "D"]:
    pts = [nodes[f"{wall}_bot_L"], nodes[f"{wall}_bot_R"],
           nodes[f"{wall}_top_R"], nodes[f"{wall}_top_L"]]
    model.AreaObj.AddByPoint(4, pts, "WALL250")

# Fix all base nodes
for wall in ["A", "B", "C", "D"]:
    model.PointObj.SetRestraint(nodes[f"{wall}_bot_L"], [True]*6)
    model.PointObj.SetRestraint(nodes[f"{wall}_bot_R"], [True]*6)
```

## Step B4 — Rigid Diaphragm at Roof Level

```python
# Assign rigid diaphragm to all roof-level nodes
roof_nodes = [nodes[f"{w}_top_L"] for w in ["A","B","C","D"]] + \
             [nodes[f"{w}_top_R"] for w in ["A","B","C","D"]] + \
             [nodes["CM"]]

model.Diaphragm.Add("RD_ROOF", 1)   # type 1 = XY plane
for pn in roof_nodes:
    model.PointObj.SetDiaphragm(pn, "RD_ROOF", 0)   # 0 = global Z
```

## Step B5 — Apply Lateral Force at CM with Accidental Eccentricity

```python
# V = 100 kips = 444.82 kN (N-S = Y direction)
V_kN = 100 * 4.4482
e_acc_m = 0.05 * Lx   # = 1.219m (4.0ft)
# Accidental eccentricity → apply as moment Mz = V × e_acc at CM
Mz_acc = V_kN * e_acc_m   # 444.82 × 1.219 = 542.2 kN·m

model.LoadPatterns.Add("EQ_Y", 5, 0, True)
model.PointObj.SetLoadForce(nodes["CM"], "EQ_Y",
    [0, V_kN, 0, 0, 0, Mz_acc], False, "Global")
# Note: Mz direction (+/-) depends on accidental eccentricity sense
# Run both +Mz and -Mz, take most severe per wall
```

## Step B6 — Analyze

```python
model.File.Save("D:\\Works\\IBC2012_DE33_ForceDistrib.EDB")
model.Analyze.SetRunCaseFlag("", False, True)
model.Analyze.SetRunCaseFlag("EQ_Y", True, False)
ret = model.Analyze.RunAnalysis()
assert ret == 0
```

## Step B7 — Read CR from ETABS

```python
model.SetPresentUnits(6)

# ETABS computes CR automatically from wall stiffnesses
r = model.Results.CenterOfMassAndRigidity("Story1", 0, 0)
# r: [ret, NumResults, Story, MassX, MassY, XCM, YCM, CumMassX, CumMassY,
#     XCCM, YCCM, XCR, YCR, TORSRATIO]
if r[0] == 0:
    x_cm_etabs = r[5][0]   # ETABS CM x
    y_cm_etabs = r[6][0]   # ETABS CM y
    x_cr_etabs = r[11][0]  # ETABS CR x
    y_cr_etabs = r[12][0]  # ETABS CR y
    print(f"ETABS CR: ({x_cr_etabs:.3f}, {y_cr_etabs:.3f}) m")
    print(f"Formula CR: ({40*0.3048:.3f}, {20*0.3048:.3f}) m")
```

## Step B8 — Read Wall Base Reactions

```python
# Base reactions at wall base nodes → get wall shear
# Sum reactions at both base nodes of each wall
results = {}
for wall in ["A", "B", "C", "D"]:
    FY_total = 0
    for side in ["L", "R"]:
        pn = nodes[f"{wall}_bot_{side}"]
        r = model.Results.JointReact(pn, 0, 0)
        # r: [ret, num, obj, elm, lc, steptype, stepnum, F1, F2, F3, M1, M2, M3]
        if r[0] == 0:
            FY_total += r[8][0]   # F2 = Y-direction reaction
    results[wall] = abs(FY_total)
    print(f"Wall {wall}: V_Y = {abs(FY_total):.1f} kN = {abs(FY_total)/4.4482:.1f} kips")

# Compare to formula
print("\nFormula results: V_A=61.8 kips, V_B=49.3 kips")
```

---

## Verified Results

### Formula Method (Method A)

| Step | Parameter | Formula | Value |
|---|---|---|---|
| 1 | x_CR | R_B×80/(R_A+R_B) | **20.0 ft** |
| 1 | y_CR | R_C×40/(R_C+R_D) | **20.0 ft** |
| 2 | e, e_acc | 40−20; 0.05×80 | **20 ft, 4 ft** |
| 3 | J | 300×20²+100×60²+200×20²+200×20² | **640,000 (k/in)·ft²** |
| 4 | V_d,A / V_d,B | 300/400×100; 100/400×100 | **75.0 / 25.0 kips** |
| 5 | V_t,A / V_t,B | 2400×300×20/640k; 2400×100×60/640k | **22.5 kips each** |
| 6 | δ_max/δ_avg | 0.475/0.325 | **1.46 > 1.4 → Type 1b** |
| 7 | A_x | (0.475/1.2×0.325)² | **1.48 (book 1.47)** |
| 8 | V_t,A / V_t,B (amplified) | with A_x×e_acc | **13.2 / 24.3 kips** |
| 9 | **V_A / V_B** | 75−13.2; 25+24.3 | **61.8 / 49.3 kips ✓** |

### ETABS Method (Method B) — Key API Calls

| Purpose | ETABS OAPI Call | Returns |
|---|---|---|
| Create wall property | `PropArea.SetShell_1("WALL250", 1, False, "C30","C30", 0, 0.25)` | Wall shell section |
| Add rigid diaphragm | `Diaphragm.Add("RD_ROOF", 1)` | Diaphragm name |
| Assign diaphragm to node | `PointObj.SetDiaphragm(node, "RD_ROOF", 0)` | — |
| Apply force at CM | `PointObj.SetLoadForce(CM_node, "EQ_Y", [0,V,0,0,0,Mz], ...)` | — |
| Read CR from ETABS | `Results.CenterOfMassAndRigidity("Story1", 0, 0)` | XCR=r[11][0], YCR=r[12][0] |
| Read wall reactions | `Results.JointReact(base_node, 0, 0)` | F2=r[8][0] (Y-shear) |

### Wall Dimensions for ETABS Model

To match book rigidities R_A:R_B:R_C:R_D = 3:1:2:2 (t=0.25m, h=3.658m, E=30 GPa):

| Wall | Length (m) | R_calibrated | Target ratio |
|---|---|---|---|
| A | 3.108 m | 3.00 × R_B | 3.00 × R_B ✓ |
| B | 2.000 m | 1.00 × R_B | 1.00 × R_B ✓ |
| C | 2.623 m | 2.00 × R_B | 2.00 × R_B ✓ |
| D | 2.623 m | 2.00 × R_B | 2.00 × R_B ✓ |

---

## Consequences — Type 1b (Extreme Torsional Irregularity)

| Consequence | ASCE 7-10 Reference |
|---|---|
| 3D model required for SDC D | §12.7.3 |
| Diaphragm shear to collectors increased 25% | §12.3.3.4 |
| Apply A_x to accidental torsion | §12.8.4.3 |
| Not permitted in SDC E or F | §12.3.3.1 |

---

## Key Notes

- **A_x is NOT iterative** — one pass only; do not re-run with amplified torsion
- **Only e_acc is amplified** — actual e is unchanged
- Wall A (closer to CR, higher R): takes more direct shear but less torsional shear
- Wall B (farther from CR, lower R): takes less direct shear but far more torsional shear at arm d=60ft
- `CenterOfMassAndRigidity` returns m, ft, or in depending on current units — match `SetPresentUnits`
- `JointReact` sign convention: positive in global +Y direction; use abs() and check equilibrium
- J units: (kip/in)·ft² — do NOT use inches for distance and kip/in for R simultaneously
