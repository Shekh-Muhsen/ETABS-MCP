# workflow-frame-forces

Extract axial (P), shear (V2, V3), torsion (T), and moment (M2, M3) for frames, piers, and spandrels.

## When to use
- Get design forces for specific beams/columns
- Extract pier and spandrel forces for wall design
- Check critical load combinations

## Frame forces

```python
model.SetPresentUnits(6)

model.Results.Setup.DeselectAllCasesAndCombosForOutput()
# Use a specific combo or case:
model.Results.Setup.SetComboSelectedForOutput("ENV-ULS")
# or: model.Results.Setup.SetCaseSelectedForOutput("Dead")

# FrameForce: [n, ObjName, ElmName, PointElm, Case, StepType, StepNum,
#              P, V2, V3, T, M2, M3, ret]
ff = model.Results.FrameForce("frame_name", 0)
n = ff[0]

forces = []
for i in range(n):
    forces.append({
        "frame":  ff[1][i],
        "point":  ff[3][i],
        "case":   ff[4][i],
        "step":   ff[5][i],
        "P_kN":   round(ff[7][i], 2),
        "V2_kN":  round(ff[8][i], 2),
        "V3_kN":  round(ff[9][i], 2),
        "T_kNm":  round(ff[10][i], 3),
        "M2_kNm": round(ff[11][i], 3),
        "M3_kNm": round(ff[12][i], 3),
    })

result = {"frame_forces": forces}
```

## All frames in a group

```python
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
model.Results.Setup.SetComboSelectedForOutput("ENV-ULS")

# Get all frame names in group
grp = model.GroupDef.GetAssignments("AllColumns")
# [n, (objTypes,), (objNames,), ret]  — objType 2 = Frame
col_names = [grp[2][i] for i in range(grp[0]) if grp[1][i] == 2]

max_axial = []
for name in col_names[:20]:   # limit for speed
    ff = model.Results.FrameForce(name, 0)
    if ff[0] > 0:
        p_vals = [abs(ff[7][i]) for i in range(ff[0])]
        max_axial.append({"frame": name, "max_P_kN": round(max(p_vals), 1)})

result = {"max_axial_by_column": sorted(max_axial, key=lambda r: r["max_P_kN"], reverse=True)[:10]}
```

## Pier forces (shear walls)

```python
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
model.Results.Setup.SetComboSelectedForOutput("ENV-ULS")

# PierForce: [n, Story, PierName, Case, StepType, StepNum, Location,
#             P, V2, V3, T, M2, M3, ret]
pf = model.Results.PierForce()
n = pf[0]

piers = []
for i in range(n):
    piers.append({
        "story":    pf[1][i],
        "pier":     pf[2][i],
        "case":     pf[3][i],
        "step":     pf[4][i],
        "location": pf[6][i],
        "P_kN":     round(pf[7][i], 2),
        "V2_kN":    round(pf[8][i], 2),
        "V3_kN":    round(pf[9][i], 2),
        "M2_kNm":   round(pf[11][i], 2),
        "M3_kNm":   round(pf[12][i], 2),
    })

result = {"pier_forces": piers[:20]}
```

## Spandrel forces

```python
# SpandrelForce: same structure as PierForce
sf = model.Results.SpandrelForce()
n = sf[0]
spandrels = [{"story": sf[1][i], "spandrel": sf[2][i],
              "case": sf[3][i], "P": round(sf[7][i],2),
              "V2": round(sf[8][i],2), "M3": round(sf[12][i],2)}
             for i in range(n)]
result = {"spandrel_forces": spandrels[:20]}
```

## Notes
- `FrameForce(name, itemType)` — `itemType=0` means single object by name
- Output has multiple rows per frame (one per station × step × case)
- `PointElm` field = "I" (start) or "J" (end) station
- Results require analysis; check `model.GetModelIsLocked()` == True first
