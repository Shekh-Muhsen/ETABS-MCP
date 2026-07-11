---
name: workflow-torsion-check
description: Torsional irregularity check — dmax/davg per story from selected edge joint pairs, Ax amplification factor, and ASCE 7 / BNBC 2020 Type 1a/1b classification.
---

# workflow-torsion-check

Computes the torsional irregularity ratio **δ_max / δ_avg** for each story by reading joint displacements at user-specified edge joints. Flags Type 1a (Torsional) and Type 1b (Extreme Torsional) irregularities and computes the accidental eccentricity amplification factor Ax.

## When to use
- ASCE 7-16 §12.3.2.1 / BNBC 2020 §2.5.5.3 torsional irregularity check
- Determine Ax amplification for accidental eccentricity (ASCE 7 §12.8.4.3)
- Verify that rigid-diaphragm buildings do not have extreme torsional response

## Classification thresholds

| Ratio δ_max / δ_avg | Classification |
|---|---|
| > 1.2 | Type 1a — Torsional Irregularity |
| > 1.4 | Type 1b — Extreme Torsional Irregularity |

## Ax amplification factor

```
Ax = (δ_max / (1.2 × δ_avg))²      (ASCE 7 §12.8.4.3)
Ax is clamped to [1.0, 3.0]
```

## Verified code

```python
import math

load_case = "EX"     # seismic case — use EX for X-direction, EY for Y-direction
direction = "U1"     # displacement direction: U1 (X) or U2 (Y)

# ── Edge joint pairs per story (user-specified) ────────────────────────────
# List of (left_joint, right_joint) per story to be checked.
# Joints must be on the diaphragm edges in the direction of loading.
# Example for a 3-story building:
story_joints = [
    ("51",  "61"),   # Story 3
    ("52",  "62"),   # Story 2
    ("53",  "63"),   # Story 1
]
story_names = ["Story 3", "Story 2", "Story 1"]   # matching order

model.SetPresentUnits(6)  # lb_in_F
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
model.Results.Setup.SetCaseSelectedForOutput(load_case, True)

comp = 1 if direction == "U1" else 2   # U1=X, U2=Y

rows = []
for (left_j, right_j), story in zip(story_joints, story_names):
    # Joint displacements: [n, Obj[], Elm[], ACase[], StepType[], StepNum[], U1[], U2[], U3[], R1[], R2[], R3[]]
    res_l = model.Results.JointDispl(left_j,  0)  # 0 = joint object
    res_r = model.Results.JointDispl(right_j, 0)

    # Take absolute maximum across all steps (envelope)
    u_left  = max(abs(v) for v in res_l[comp+5]) if res_l[0] > 0 else 0   # indices: U1=6, U2=7
    u_right = max(abs(v) for v in res_r[comp+5]) if res_r[0] > 0 else 0

    d_max = max(u_left, u_right)
    d_avg = (u_left + u_right) / 2.0
    ratio = d_max / d_avg if d_avg > 0 else 0
    Ax    = min(3.0, max(1.0, (d_max / (1.2 * d_avg))**2)) if d_avg > 0 else 1.0

    if   ratio > 1.4: status = "EXTREME TORSIONAL (Type 1b)"
    elif ratio > 1.2: status = "TORSIONAL (Type 1a)"
    else:             status = "OK"

    rows.append({
        "story":      story,
        "left_joint": left_j,
        "right_joint": right_j,
        "delta_left_in":  round(u_left,  5),
        "delta_right_in": round(u_right, 5),
        "delta_max_in":   round(d_max, 5),
        "delta_avg_in":   round(d_avg, 5),
        "ratio":          round(ratio, 3),
        "Ax":             round(Ax,    3),
        "status":         status,
    })

flagged = [r for r in rows if "TORSIONAL" in r["status"]]
gov     = max(rows, key=lambda r: r["ratio"]) if rows else {}

result = {
    "load_case":     load_case,
    "direction":     direction,
    "flagged_count": len(flagged),
    "governing":     gov,
    "rows":          rows,
}
```

## Notes
- **Joint selection**: choose the two joints on opposite edges of the diaphragm at each story level — the joints should be at the extreme ends in the direction perpendicular to the applied load
- `JointDispl(name, itemType)`: `itemType=0` = joint object name; returns arrays indexed from 0. U1=index 6, U2=index 7, U3=index 8
- For envelope combos (Max/Min), take `max(abs(v) for v in array)` to get the worst step
- **Ax** is applied to the accidental eccentricity offset in the next load pattern iteration; values between 1.0 and 3.0 are enforced
- If no joint pairs are known, read them from the `Joint Assignments - Diaphragms` database table and select corner joints automatically
- BNBC 2020 does not define Ax explicitly; apply ASCE 7-16 §12.8.4.3 formula for consistency
