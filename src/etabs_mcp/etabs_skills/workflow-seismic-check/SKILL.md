# workflow-seismic-check

Full dynamic/seismic check: ensure results are available, then extract modal periods, mass participation, base shears, and story drifts in one pass. Verified against ETABS 23.2.0 with Eigen modal case.

## RS Function Warning
**`'Functions - Response Spectrum - ASCE7-05'` is NOT available on fresh/new models.**
Always create RS functions via `'Functions - Response Spectrum - User Defined'` with explicit T-Sa pairs.
See `bnbc2020-seismic-params` skill for the verified `create_bnbc_rs()` function.

After creating the function, configure RS cases BEFORE running analysis:
```python
model.LoadCases.ResponseSpectrum.SetCase("EX")
model.LoadCases.ResponseSpectrum.SetLoads(
    "EX", 1, ["U1"], ["BNBC2020-Z2-SD"], [9.81], ["Global"], [0.0])
model.LoadCases.ResponseSpectrum.SetCase("EY")
model.LoadCases.ResponseSpectrum.SetLoads(
    "EY", 1, ["U2"], ["BNBC2020-Z2-SD"], [9.81], ["Global"], [0.0])
# Verify n_loads > 0 before running:
t = model.LoadCases.ResponseSpectrum.GetLoads("EX")
print("EX n_loads:", t[0])  # must be 1, not 0
```

## When to use
- Quick seismic health-check of a dynamic model
- Confirm 90% mass participation is met
- Get base shear (static EQ + response spectrum) and max story drift
- First step before RS scaling or detailed drift checks

## Critical: Results Availability

When a model is opened from disk, it may be **locked but results inaccessible** via COM (ret=1). Always check and fix before extracting results:

```python
model.SetPresentUnits(6)
is_locked = model.GetModelIsLocked()

if not is_locked:
    result = {"error": "Model not analysed. Run analysis first."}
else:
    # Test if results are actually accessible
    model.Results.Setup.DeselectAllCasesAndCombosForOutput()
    lc = model.LoadCases.GetNameList()
    cases = list(lc[1])
    gravity = next((c for c in cases if "dead" in c.lower()), cases[0])
    model.Results.Setup.SetCaseSelectedForOutput(gravity)
    br = model.Results.BaseReact()
    results_ok = (br[-1] == 0 and br[0] > 0)

    if not results_ok:
        # Results not in COM memory — must re-run analysis
        # This happens after opening a saved EDB without its results cache
        ret_unlock = model.SetModelIsLocked(False)
        for c in cases:
            model.Analyze.SetRunCaseFlag(c, True)
        ret_run = model.Analyze.RunAnalysis()
        result = {"ran_analysis": True, "unlock_ret": ret_unlock, "run_ret": ret_run}
    else:
        result = {"results_available": True}
```

## Step 1 — Modal Periods

```python
model.SetPresentUnits(6)
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
lc_names = list(model.LoadCases.GetNameList()[1])
modal_cases = [c for c in lc_names if "modal" in c.lower() or "mode" in c.lower()]
for c in modal_cases:
    model.Results.Setup.SetCaseSelectedForOutput(c)

# ModalPeriod → [n, Case_t, StepType_t, StepNum_t, Period_t, Freq_t, CircFreq_t, EigenVal_t, ret]
# StepNum at [3] = mode number (1, 2, 3...) — VERIFIED for Ritz case in ETABS 23.2.0
mp = model.Results.ModalPeriod()
n = mp[0]
modes = [
    {"mode": int(list(mp[3])[i]), "T_s": round(list(mp[4])[i], 4), "f_Hz": round(list(mp[5])[i], 4)}
    for i in range(n)
]
result = {"total_modes": n, "periods": modes[:6]}
```

## Step 2 — Mass Participation

> **CRITICAL — Ritz vs Eigenvector:** `ModalParticipatingMassRatios()[3]` (StepNum) returns **0 for all modes** when using a Ritz modal case. Use the row index `(i+1)` as the mode number instead. Eigenvector cases populate StepNum correctly.

```python
model.SetPresentUnits(6)
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
lc_names = list(model.LoadCases.GetNameList()[1])
for c in lc_names:
    if "modal" in c.lower() or "mode" in c.lower():
        model.Results.Setup.SetCaseSelectedForOutput(c)

# ModalParticipatingMassRatios →
#   [n, Case_t, StepType_t, StepNum_t, Period_t,
#    UX_t, UY_t, UZ_t, SumUX_t, SumUY_t, SumUZ_t,
#    RX_t, RY_t, RZ_t, SumRX_t, SumRY_t, SumRZ_t, ret]
# NOTE: StepNum [3] = 0 for ALL rows when Ritz case is used.
#       Use (i+1) as mode number — row order matches ascending mode number.
mpr = model.Results.ModalParticipatingMassRatios()
n = mpr[0]
UX    = list(mpr[5])
UY    = list(mpr[6])
SumUX = list(mpr[8])
SumUY = list(mpr[9])
Period = list(mpr[4])

mass_table = [
    {
        "mode":   i + 1,
        "T_s":    round(Period[i], 4),
        "UX_pct": round(UX[i] * 100, 2),
        "UY_pct": round(UY[i] * 100, 2),
        "SumUX":  round(SumUX[i] * 100, 2),
        "SumUY":  round(SumUY[i] * 100, 2),
    }
    for i in range(n)
]

req = 90.0
mode_90_X = next((r["mode"] for r in mass_table if r["SumUX"] >= req), None)
mode_90_Y = next((r["mode"] for r in mass_table if r["SumUY"] >= req), None)
final_SumUX = mass_table[-1]["SumUX"] if mass_table else 0
final_SumUY = mass_table[-1]["SumUY"] if mass_table else 0

result = {
    "mass_table": mass_table,
    "90pct_mode_X": mode_90_X,
    "90pct_mode_Y": mode_90_Y,
    "final_SumUX": final_SumUX,
    "final_SumUY": final_SumUY,
    "meets_90pct": final_SumUX >= req and final_SumUY >= req,
}
```

## Step 3 — Base Shears (Static EQ + Response Spectrum)

Use `DatabaseTables` — more robust than `model.Results.BaseReact()` for multi-step cases (EX/EY have 3 step-by-step rows each).

```python
model.SetPresentUnits(6)
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
lc_names = list(model.LoadCases.GetNameList()[1])

# Select all seismic cases
seismic_keywords = ["ex", "ey", "spec", "eq", "wx", "wy"]
for c in lc_names:
    if any(k in c.lower() for k in seismic_keywords):
        model.Results.Setup.SetCaseSelectedForOutput(c)

raw = model.DatabaseTables.GetTableForDisplayArray("Base Reactions", [], "All", 0, [], 0, [])
# Fields: [OutputCase, CaseType, StepType, StepNumber, FX, FY, FZ, MX, MY, MZ, X, Y, Z]
fields = [f for f in list(raw[2]) if f is not None]
n_rows = raw[3]
flat = list(raw[4])
nf = len(fields)
rows = [{fields[j]: flat[i * nf + j] for j in range(nf)} for i in range(n_rows)]

# Summarise: max |FX| and |FY| per case
summary = {}
for r in rows:
    case = r.get("OutputCase", "")
    try:
        fx = abs(float(r.get("FX", 0) or 0))
        fy = abs(float(r.get("FY", 0) or 0))
    except Exception:
        continue
    if case not in summary:
        summary[case] = {"max_FX_kN": 0, "max_FY_kN": 0, "CaseType": r.get("CaseType", "")}
    summary[case]["max_FX_kN"] = max(summary[case]["max_FX_kN"], round(fx, 1))
    summary[case]["max_FY_kN"] = max(summary[case]["max_FY_kN"], round(fy, 1))

result = summary
# Example output from TEP-MC1-DYNAMIC-304.EDB (kN_m):
# EX: FX=7024.5, EY: FY=6146.5, Spec X: FX=6321.3, Spec Y: FY=5044.6
```

## Step 4 — Story Drifts

```python
model.SetPresentUnits(6)
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
lc_names = list(model.LoadCases.GetNameList()[1])
for c in lc_names:
    if any(k in c.lower() for k in ["spec", "ex", "ey", "eq"]):
        model.Results.Setup.SetCaseSelectedForOutput(c)

raw = model.DatabaseTables.GetTableForDisplayArray("Story Drifts", [], "All", 0, [], 0, [])
# Fields: [Story, OutputCase, CaseType, StepType, StepNumber, Direction, Drift, Drift/, Label, X, Y, Z]
fields = [f for f in list(raw[2]) if f is not None]
n_rows = raw[3]
flat = list(raw[4])
nf = len(fields)
rows = [{fields[j]: flat[i * nf + j] for j in range(nf)} for i in range(n_rows)]

# Filter to response spectrum Max rows only (avoid mode-by-mode noise)
rs_rows = [r for r in rows if r.get("CaseType") == "LinRespSpec" and r.get("StepType") == "Max"]
x_drifts = [float(r["Drift"]) for r in rs_rows if r.get("Direction") == "X" and r.get("Drift") not in ("", None)]
y_drifts = [float(r["Drift"]) for r in rs_rows if r.get("Direction") == "Y" and r.get("Drift") not in ("", None)]

max_X = max(x_drifts) if x_drifts else None
max_Y = max(y_drifts) if y_drifts else None

# Find critical story
crit_X = next((r for r in rs_rows if r.get("Direction") == "X" and r.get("Drift") and float(r["Drift"]) == max_X), {})
crit_Y = next((r for r in rs_rows if r.get("Direction") == "Y" and r.get("Drift") and float(r["Drift"]) == max_Y), {})

result = {
    "max_drift_X": round(max_X, 6) if max_X else None,
    "max_drift_Y": round(max_Y, 6) if max_Y else None,
    "critical_story_X": crit_X.get("Story"),
    "critical_case_X": crit_X.get("OutputCase"),
    "critical_story_Y": crit_Y.get("Story"),
    "critical_case_Y": crit_Y.get("OutputCase"),
}
# Example: max_drift_X=0.0142, max_drift_Y=0.0214, critical_story=OHWR
```

## Full One-Shot Seismic Check

```python
model.SetPresentUnits(6)

# -- Ensure results available --
is_locked = model.GetModelIsLocked()
if not is_locked:
    result = {"error": "Model not analysed"}
else:
    model.Results.Setup.DeselectAllCasesAndCombosForOutput()
    lc = model.LoadCases.GetNameList()
    cases = list(lc[1])
    gravity = next((c for c in cases if "dead" in c.lower()), cases[0])
    model.Results.Setup.SetCaseSelectedForOutput(gravity)
    br_test = model.Results.BaseReact()
    if br_test[-1] != 0 or br_test[0] == 0:
        model.SetModelIsLocked(False)
        for c in cases:
            model.Analyze.SetRunCaseFlag(c, True)
        model.Analyze.RunAnalysis()

    # -- Modal --
    model.Results.Setup.DeselectAllCasesAndCombosForOutput()
    modal_cases = [c for c in cases if "modal" in c.lower() or "mode" in c.lower()]
    for c in modal_cases:
        model.Results.Setup.SetCaseSelectedForOutput(c)
    mp = model.Results.ModalPeriod()
    mpr = model.Results.ModalParticipatingMassRatios()

    n_mp = mp[0]
    periods = [{"mode": int(list(mp[3])[i]), "T_s": round(list(mp[4])[i], 4)} for i in range(min(n_mp, 6))]

    n_mpr = mpr[0]
    SumUX = list(mpr[8])
    SumUY = list(mpr[9])
    # Ritz: StepNum[3]=0 for all, use row index
    mass_table = [{"mode": i+1, "SumUX": round(SumUX[i]*100,2), "SumUY": round(SumUY[i]*100,2)} for i in range(n_mpr)]
    meets_90 = (mass_table[-1]["SumUX"] >= 90 and mass_table[-1]["SumUY"] >= 90) if mass_table else False

    # -- Base shear via DatabaseTables --
    model.Results.Setup.DeselectAllCasesAndCombosForOutput()
    seismic_cases = [c for c in cases if any(k in c.lower() for k in ["ex","ey","spec","eq"])]
    for c in seismic_cases:
        model.Results.Setup.SetCaseSelectedForOutput(c)
    raw_br = model.DatabaseTables.GetTableForDisplayArray("Base Reactions", [], "All", 0, [], 0, [])
    fields = [f for f in list(raw_br[2]) if f is not None]
    nf = len(fields)
    n_rows = raw_br[3]
    flat = list(raw_br[4])
    br_rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n_rows)]
    base_shear = {}
    for r in br_rows:
        case = r.get("OutputCase","")
        try:
            fx = abs(float(r.get("FX",0) or 0))
            fy = abs(float(r.get("FY",0) or 0))
        except Exception:
            continue
        if case not in base_shear:
            base_shear[case] = {"FX_kN": 0, "FY_kN": 0}
        base_shear[case]["FX_kN"] = max(base_shear[case]["FX_kN"], round(fx,1))
        base_shear[case]["FY_kN"] = max(base_shear[case]["FY_kN"], round(fy,1))

    # -- Story drifts --
    raw_sd = model.DatabaseTables.GetTableForDisplayArray("Story Drifts", [], "All", 0, [], 0, [])
    fields_sd = [f for f in list(raw_sd[2]) if f is not None]
    nf_sd = len(fields_sd)
    n_sd = raw_sd[3]
    flat_sd = list(raw_sd[4])
    sd_rows = [{fields_sd[j]: flat_sd[i*nf_sd+j] for j in range(nf_sd)} for i in range(n_sd)]
    rs_sd = [r for r in sd_rows if r.get("CaseType") == "LinRespSpec" and r.get("StepType") == "Max"]
    max_dx = max((float(r["Drift"]) for r in rs_sd if r.get("Direction")=="X" and r.get("Drift") not in ("",None)), default=None)
    max_dy = max((float(r["Drift"]) for r in rs_sd if r.get("Direction")=="Y" and r.get("Drift") not in ("",None)), default=None)

    result = {
        "periods_first6": periods,
        "meets_90pct_mass": meets_90,
        "final_SumUX_pct": mass_table[-1]["SumUX"] if mass_table else 0,
        "final_SumUY_pct": mass_table[-1]["SumUY"] if mass_table else 0,
        "base_shear": base_shear,
        "max_story_drift_X": round(max_dx, 6) if max_dx else None,
        "max_story_drift_Y": round(max_dy, 6) if max_dy else None,
    }
```

## Notes

- **Ritz StepNum bug**: `ModalParticipatingMassRatios()[3]` is all 0 for Ritz cases. Always use `i+1` as mode number.
- **Results not in COM**: After opening a saved EDB, results may be locked but inaccessible (BaseReact ret=1). Must unlock → run → re-lock. This is normal ETABS COM behaviour.
- **DatabaseTables vs Results API**: DatabaseTables is more robust for multi-step cases. Always pre-select output cases via `Results.Setup` before calling `GetTableForDisplayArray` on result tables.
- **RS drift filter**: Filter `CaseType=LinRespSpec, StepType=Max` to avoid mode-by-mode drift rows inflating the max.
- **NEVER use InitializeNewModel()** — blanks the ETABS viewport permanently. Clear geometry with `SelectObj.All()` → `FrameObj.Delete("",2)` → `AreaObj.Delete("",2)` → `PointObj.DeleteSpecialPoint("",2)`.
- **model.LoadCases.Modal does not exist** — use `model.LoadCases.ModalEigen.SetCase("Modal")` instead.
- **model.LoadCombos does not exist** — use `model.RespCombo` for reading, and DatabaseTables for bulk combo creation.
- **RS function ASCE7-05 table not available on fresh models** — use User Defined table with T-Sa pairs. See bnbc2020-seismic-params skill.
- **Verified on**: 5story_BNBC2020.EDB (3×3 bays, 5m, 5×3.5m) — T1=0.404s (Y), T2=0.318s (X); EX=3786.5 kN, EY=3808.5 kN; max drift EX=0.000697 raw → 0.00383 amplified (PASS ≤0.020), EY=0.001065 → 0.00586 (PASS); critical Story4. BNBC 2020 Zone2 SD, SDS=0.45, SD1=0.36.
