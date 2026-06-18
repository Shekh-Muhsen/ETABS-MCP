# workflow-rs-scaling

Scale response spectrum cases to satisfy the 85% minimum base shear rule (ASCE 7 §12.9.1.4 / similar codes).

## When to use
- After initial analysis to check if dynamic base shear meets minimum
- Apply corrected scale factors and re-analyze

## Process
1. Get static base shear (EX → FX, EY → FY)
2. Get dynamic base shear (Spec X → FX, Spec Y → FY)
3. Compute scale factor = (0.85 × V_static) / V_dynamic
4. If scale > 1.0 → scaling required, apply to response spectrum SF
5. Re-run analysis

## Verified code

```python
model.SetPresentUnits(6)

# Step 1–2: get base shears
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
for c in ["EX", "EY", "Spec X", "Spec Y"]:
    model.Results.Setup.SetCaseSelectedForOutput(c)

base = model.Results.BaseReact()
n = base[0]

V = {"EX": 0, "EY": 0, "Spec X": 0, "Spec Y": 0}
for i in range(n):
    case = base[1][i]
    if case in V:
        if "X" in case:
            V[case] = max(V[case], abs(base[4][i]))   # FX
        else:
            V[case] = max(V[case], abs(base[5][i]))   # FY

# Step 3: compute scale factors
Sx = (0.85 * V["EX"]) / V["Spec X"] if V["Spec X"] > 0 else 1.0
Sy = (0.85 * V["EY"]) / V["Spec Y"] if V["Spec Y"] > 0 else 1.0

# Step 4: apply only if > 1.0 (code minimum; some engineers always apply)
def scale_rs(case_name, factor):
    rs = model.LoadCases.ResponseSpectrum.GetLoads(case_name)
    # GetLoads → [n, (LoadNames,), (Funcs,), (SFs,), (CSys,), (Angles,), ret]
    n = rs[0]; names = rs[1]; funcs = rs[2]; sfs = rs[3]; csys = rs[4]; angles = rs[5]
    new_sfs = [sf * factor for sf in sfs]
    # CRITICAL: SetLoads order is CSys BEFORE Angles (opposite of what you'd guess)
    # SetLoads(Name, N, LoadName[], Func[], SF[], CSys[], Angle[]) ← CSys at pos 5, Angle at pos 6
    model.LoadCases.ResponseSpectrum.SetLoads(case_name, n, list(names), list(funcs), new_sfs, list(csys), list(angles))

model.SetModelIsLocked(False)

if Sx > 1.0:
    scale_rs("Spec X", Sx)
if Sy > 1.0:
    scale_rs("Spec Y", Sy)

result = {
    "V_EX": round(V["EX"], 2), "V_EY": round(V["EY"], 2),
    "V_SpecX": round(V["Spec X"], 2), "V_SpecY": round(V["Spec Y"], 2),
    "Sx": round(Sx, 4), "Sy": round(Sy, 4),
    "scaling_applied_X": Sx > 1.0,
    "scaling_applied_Y": Sy > 1.0,
    "note": "Re-run analysis after scaling",
}
```

## To always apply (not just when > 1.0)

```python
scale_rs("Spec X", Sx)
scale_rs("Spec Y", Sy)
```

## ResponseSpectrum.SetLoads signature
```
SetLoads(Name, NumberLoads, LoadName[], Func[], SF[], CSys[], Angle[]) → ret
```
- **VERIFIED:** CSys comes BEFORE Angle (position 5 and 6 respectively)
- `CSys[]` values: string `"Global"` (not int 0)
- `Angle[]` values: float degrees (typically 0.0)
- `SF[]` values: overall scale factor applied to the function (e.g. 9.81 for kN_m units)
