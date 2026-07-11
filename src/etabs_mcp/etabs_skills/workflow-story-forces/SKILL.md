---
name: workflow-story-forces
description: Read story shears, axial forces, torsion, and overturning moments from the ETABS "Story Forces" table (Location = Bottom), including foundation OTM = 0.75×M per BNBC 2020 §2.5.7.8.
---

# workflow-story-forces

Reads the `Story Forces` results table from ETABS for one or more load cases or combos. Returns story-by-story P, VX, VY, T (torsion), MX, MY — plus the foundation OTM scaled by 0.75.

## When to use
- Extract base shear and overturning moments directly from ETABS analysis results
- Compare against hand-calc OTM (see `workflow-otm-check`)
- Foundation overturning demand at each story level

## Columns returned by "Story Forces" table

| Field | Meaning |
|---|---|
| Story | Story name |
| Location | "Bottom" or "Top" — use Bottom for shear/OTM at cut section |
| P (kN) | Axial force |
| VX, VY (kN) | Story shear in X and Y |
| T (kN·m) | Torsional moment |
| MX, MY (kN·m) | Overturning moments |

## Verified code

```python
model.SetPresentUnits(6)  # lb_in_F — then convert to kN·m

LB_TO_KN   = 4.4482216 / 1000.0      # lb → kN
LBIN_TO_KNM = 4.4482216 * 0.0254 / 1000.0  # lb·in → kN·m

case_name = "EX"   # adjust as needed

model.Results.Setup.DeselectAllCasesAndCombosForOutput()
model.Results.Setup.SetCaseSelectedForOutput(case_name, True)

sf = model.DatabaseTables.GetTableForDisplayArray(
    "Story Forces", [], "All", 0, [], 0, [])
fields = list(sf[1])
nr     = sf[5]
data   = list(sf[6])
nc     = len(fields)

def col(*names):
    for n in names:
        try: return next(i for i, f in enumerate(fields) if f.lower() == n.lower())
        except StopIteration: pass
    return -1

iStory = col("Story")
iLoc   = col("Location", "Loc")
iP     = col("P")
iVX    = col("VX", "V X")
iVY    = col("VY", "V Y")
iT     = col("T")
iMX    = col("MX", "M X")
iMY    = col("MY", "M Y")

rows = []
for r in range(nr):
    loc = data[r*nc+iLoc] if iLoc >= 0 else ""
    if loc and loc.lower() != "bottom":
        continue   # use Bottom cut only
    def v(idx): return float(data[r*nc+idx] or 0) if idx >= 0 else 0
    P  = v(iP)  * LB_TO_KN
    VX = v(iVX) * LB_TO_KN
    VY = v(iVY) * LB_TO_KN
    T  = v(iT)  * LBIN_TO_KNM
    MX = v(iMX) * LBIN_TO_KNM
    MY = v(iMY) * LBIN_TO_KNM
    rows.append({
        "story":        data[r*nc+iStory] if iStory >= 0 else "",
        "P_kN":         round(P, 1),
        "VX_kN":        round(VX, 1),
        "VY_kN":        round(VY, 1),
        "T_kNm":        round(T, 1),
        "MX_kNm":       round(MX, 1),
        "MY_kNm":       round(MY, 1),
        "fnd_MX_kNm":   round(MX*0.75, 1),
        "fnd_MY_kNm":   round(MY*0.75, 1),
    })

base = rows[0] if rows else {}
result = {
    "case":          case_name,
    "story_count":   len(rows),
    "base_VX_kN":    base.get("VX_kN"),
    "base_VY_kN":    base.get("VY_kN"),
    "base_MX_kNm":   base.get("MX_kNm"),
    "base_MY_kNm":   base.get("MY_kNm"),
    "fnd_MX_kNm":    base.get("fnd_MX_kNm"),
    "fnd_MY_kNm":    base.get("fnd_MY_kNm"),
    "rows":          rows,
}
```

## Notes
- Always filter `Location == "Bottom"` — "Top" values are the force above the cut, not the accumulated shear below
- Story Forces table is ordered top→bottom in ETABS; `rows[0]` after filtering is the **base** (largest accumulated shear and OTM)
- Foundation OTM = 0.75 × MX (or MY) per BNBC 2020 §2.5.7.8 — this reduction accounts for the beneficial effect of gravity loads on overturning
- For response-spectrum combos (SRSS), MX and MY are already enveloped and unsigned
- To query multiple cases, loop over `case_name` list and deselect/reselect output cases between iterations
