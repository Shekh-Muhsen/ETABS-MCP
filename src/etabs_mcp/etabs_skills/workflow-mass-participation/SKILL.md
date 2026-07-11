---
name: workflow-mass-participation
description: Extract modal mass participation ratios from ETABS, flag whether the 90% UX/UY target is met, and report defined vs actual mode count.
---

# workflow-mass-participation

Reads `ModalParticipatingMassRatios` from ETABS for a specified modal case and returns:
- Per-mode period, UX/UY/UZ and RX/RY/RZ participation ratios with cumulative sums
- 90% mass target status for UX and UY (ASCE 7 / BNBC 2020 §2.5.9.2)
- Comparison of defined (requested) modes vs modes actually run by ETABS

## When to use
- Verify sufficient modes for response-spectrum analysis (ASCE 7-16 §12.9.1 / BNBC 2020 §2.5.9.2)
- Check whether ETABS stopped early (mass-participation target already reached)
- Report modal periods and mass distribution to the seismic review team

## Code requirement

ASCE 7 §12.9.1 / BNBC 2020 §2.5.9.2: combined mass participation **≥ 90%** in each orthogonal horizontal direction (UX and UY), or include all modes with period ≥ 0.05 s.

## Verified code

```python
modal_case = "MODAL"   # change to your modal case name

# ── Select only the modal case for output ──────────────────────────────────
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
model.Results.Setup.SetCaseSelectedForOutput(modal_case, True)

# ── Get defined mode count (works for both Eigen and Ritz) ─────────────────
max_modes = 0; min_modes = 0
defined_info = None
if model.LoadCases.ModalEigen.GetNumberModes(modal_case, max_modes, min_modes)[0] == 0:
    max_modes = model.LoadCases.ModalEigen.GetNumberModes(modal_case, 0, 0)[1]
    min_modes = model.LoadCases.ModalEigen.GetNumberModes(modal_case, 0, 0)[2]
    defined_info = {"type": "Eigen", "max": max_modes, "min": min_modes}
else:
    r = model.LoadCases.ModalRitz.GetNumberModes(modal_case, 0, 0)
    if r[0] == 0:
        defined_info = {"type": "Ritz", "max": r[1], "min": r[2]}

# ── Modal mass participation ratios ───────────────────────────────────────
r = model.Results.ModalParticipatingMassRatios()
n       = r[0]
periods = list(r[4])
ux      = list(r[5]);  uy  = list(r[6]);  uz  = list(r[7])
sux     = list(r[8]);  suy = list(r[9]);  suz = list(r[10])
rx      = list(r[11]); ry  = list(r[12]); rz  = list(r[13])
srx     = list(r[14]); sry = list(r[15]); srz = list(r[16])

modes = []
for i in range(n):
    modes.append({
        "mode":   i+1,
        "T_s":    round(periods[i], 4),
        "UX":     round(ux[i],  4), "UY": round(uy[i],  4), "UZ": round(uz[i],  4),
        "SumUX":  round(sux[i], 4), "SumUY": round(suy[i], 4), "SumUZ": round(suz[i], 4),
        "RX":     round(rx[i],  4), "RY": round(ry[i],  4), "RZ": round(rz[i],  4),
        "SumRX":  round(srx[i], 4), "SumRY": round(sry[i], 4), "SumRZ": round(srz[i], 4),
    })

max_sux = max(sux) if sux else 0
max_suy = max(suy) if suy else 0
target_met = max_sux >= 0.90 and max_suy >= 0.90

# Mode that first crosses 90% in UX and UY
def first90(arr):
    for i, v in enumerate(arr):
        if v >= 0.90:
            return i+1
    return None

result = {
    "modal_case":      modal_case,
    "defined_modes":   defined_info,
    "modes_run":       n,
    "max_sum_UX":      round(max_sux, 4),
    "max_sum_UY":      round(max_suy, 4),
    "max_sum_UZ":      round(max(suz) if suz else 0, 4),
    "target_90pct_met": target_met,
    "mode_90pct_UX":   first90(sux),
    "mode_90pct_UY":   first90(suy),
    "modes":           modes,
}
```

## Notes
- `ModalParticipatingMassRatios()` indices: `[0]=n, [1]=LoadCase[], [2]=StepType[], [3]=StepNum[], [4]=Period[], [5]=UX[], [6]=UY[], [7]=UZ[], [8]=SumUX[], [9]=SumUY[], [10]=SumUZ[], [11]=RX[], [12]=RY[], [13]=RZ[], [14]=SumRX[], [15]=SumRY[], [16]=SumRZ[]`
- If `modes_run < defined_info.max`, ETABS stopped early because the mass-participation target inside the case was already met — this is normal
- If `modes_run > defined_info.max`, the case definition changed after analysis; re-run
- First mode = fundamental period of the structure; dominant direction indicates the primary lateral mode shape
- For 3D asymmetric buildings, also check SumRZ ≥ 90% for torsional mass participation
