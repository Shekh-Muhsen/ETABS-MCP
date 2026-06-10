# workflow-base-shear

Extract base shear (FX, FY, FZ) for all seismic load cases. Compares static (EX/EY) vs dynamic (Spec X/Spec Y).

## When to use
- Check static vs dynamic base shear ratio
- Before response spectrum scaling
- Design report

## Verified code

```python
model.SetPresentUnits(6)  # kN_m

# Select all seismic cases for output
model.Results.Setup.DeselectAllCasesAndCombosForOutput()

lc_names = list(model.LoadCases.GetNameList()[1])
seismic_cases = [c for c in lc_names if any(
    k in c.upper() for k in ["EX","EY","SPEC","SEISMIC","EQ"]
)]
for c in seismic_cases:
    model.Results.Setup.SetCaseSelectedForOutput(c)

# Extract base reactions
# [n, LoadCase, StepType, StepNum, FX, FY, FZ, MX, MY, MZ, gX, gY, gZ, ret]
base = model.Results.BaseReact()
n = base[0]

rows = []
for i in range(n):
    rows.append({
        "case": base[1][i],
        "FX_kN": round(base[4][i], 2),
        "FY_kN": round(base[5][i], 2),
        "FZ_kN": round(base[6][i], 2),
    })

# Summarise static vs dynamic
V_EX = max(abs(r["FX_kN"]) for r in rows if r["case"]=="EX") if any(r["case"]=="EX" for r in rows) else 0
V_EY = max(abs(r["FY_kN"]) for r in rows if r["case"]=="EY") if any(r["case"]=="EY" for r in rows) else 0
V_SX = max(abs(r["FX_kN"]) for r in rows if "SPEC X" in r["case"].upper() or r["case"]=="Spec X") if any("spec" in r["case"].lower() for r in rows) else 0
V_SY = max(abs(r["FY_kN"]) for r in rows if "SPEC Y" in r["case"].upper() or r["case"]=="Spec Y") if any("spec" in r["case"].lower() for r in rows) else 0

result = {
    "all_cases": rows,
    "summary": {
        "V_EX_kN": V_EX, "V_EY_kN": V_EY,
        "V_SpecX_kN": V_SX, "V_SpecY_kN": V_SY,
        "ratio_X": round(V_SX/V_EX, 3) if V_EX else None,
        "ratio_Y": round(V_SY/V_EY, 3) if V_EY else None,
        "85pct_rule_X": V_SX >= 0.85*V_EX,
        "85pct_rule_Y": V_SY >= 0.85*V_EY,
    }
}
```

## Notes
- `BaseReact()` returns one row per case + step combination
- For envelope combos (Max/Min steps), use `abs()` and `max()`
- 85% rule: Dynamic base shear must be ≥ 85% of static (ASCE 7-16 §12.9.1.4)
- Results require model to be analyzed — check `model.GetModelIsLocked()` == True
