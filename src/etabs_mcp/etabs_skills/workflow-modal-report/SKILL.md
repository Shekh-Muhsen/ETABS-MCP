# workflow-modal-report

Extract modal periods, frequencies, and mass participation ratios. Checks 90% mass participation requirement.

## When to use
- Verify sufficient modes captured (≥90% mass participation)
- Review fundamental periods
- Confirm modal case is set up correctly

## Verified code

```python
model.SetPresentUnits(6)

# Find and select modal cases
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
lc_names = list(model.LoadCases.GetNameList()[1])
modal_cases = [c for c in lc_names if "MODAL" in c.upper() or "MODE" in c.upper()]
for c in modal_cases:
    model.Results.Setup.SetCaseSelectedForOutput(c)

# Modal periods: [n, Case, StepType, StepNum, Period, Freq, CircFreq, EigenVal, ret]
periods = model.Results.ModalPeriod()

# Mass ratios: [n, Case, StepType, StepNum, Period, UX,UY,UZ, SumUX,SumUY,SumUZ,
#               RX,RY,RZ, SumRX,SumRY,SumRZ, ret]
mass = model.Results.ModalParticipatingMassRatios()

n_p = periods[0]
n_m = mass[0]

modes = []
for i in range(n_p):
    modes.append({
        "mode":  int(periods[3][i]),
        "T_sec": round(periods[4][i], 4),
        "f_Hz":  round(periods[5][i], 4),
    })

mass_table = []
for i in range(n_m):
    # StepNum at [3] is 0 for all rows when using a Ritz modal case (ETABS 23.x).
    # Use row index (i+1) as the mode number — rows are always in ascending mode order.
    step_num = int(mass[3][i])
    mode_num = step_num if step_num > 0 else i + 1
    mass_table.append({
        "mode":   mode_num,
        "UX_pct": round(mass[5][i]*100, 2),
        "UY_pct": round(mass[6][i]*100, 2),
        "UZ_pct": round(mass[7][i]*100, 2),
        "SumUX":  round(mass[8][i]*100, 2),
        "SumUY":  round(mass[9][i]*100, 2),
    })

# Find mode where 90% is achieved
req = 90.0
mode_90_X = next((r["mode"] for r in mass_table if r["SumUX"] >= req), None)
mode_90_Y = next((r["mode"] for r in mass_table if r["SumUY"] >= req), None)
final_sumX = mass_table[-1]["SumUX"] if mass_table else 0
final_sumY = mass_table[-1]["SumUY"] if mass_table else 0

result = {
    "modal_cases": modal_cases,
    "total_modes": n_p,
    "modes":       modes,
    "mass_table":  mass_table,
    "90pct_mode_X": mode_90_X,
    "90pct_mode_Y": mode_90_Y,
    "final_SumUX":  final_sumX,
    "final_SumUY":  final_sumY,
    "meets_90pct":  final_sumX >= req and final_sumY >= req,
}
```

## Notes
- `StepNum` field = mode number
- `UX`, `UY`, `UZ` = incremental participation per mode (%)
- `SumUX`, `SumUY` = cumulative participation (%)
- ASCE 7-16 §12.9.1: min 90% of total mass in each direction
- If `meets_90pct = False`: increase number of modes in modal case settings
