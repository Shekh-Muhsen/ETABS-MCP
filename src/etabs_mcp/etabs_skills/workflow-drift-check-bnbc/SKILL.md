---
name: workflow-drift-check-bnbc
description: Dual-method inter-story drift check (ETABS StoryDrifts + hand calc) with Cd/I factor and occupancy-based allowables per BNBC 2020 / ASCE 7-05.
---

# workflow-drift-check-bnbc

Dual-method inter-story drift check: ETABS `StoryDrifts` ratio **and** hand calc `Δ = (δᵢ − δ_below) / h` from joint displacements. Both multiplied by Cd/I and compared against the allowable per BNBC 2020 Table 6.2.21 / ASCE 7-05 Table 12.12-1.

## When to use
- Post-analysis drift compliance check (EQX, EQY, Spec X, Spec Y, or any seismic case)
- BNBC 2020 or ASCE 7 code-check with Cd/I amplification
- Cross-verify ETABS built-in drift against independent hand computation

## Code drift limits (BNBC 2020 Table 6.2.21 / ASCE 7-05 Table 12.12-1)

| Occupancy / Risk Category | Allowable Δₐ/hₛₓ |
|---|---|
| I / II (General) | 2.0% |
| III (Assembly / High Occupancy) | 1.5% |
| IV (Essential Facilities) | 1.0% |

## Verified code

```python
import math

model.SetPresentUnits(6)  # lb_in_F — story heights returned in inches

cases   = ["EX", "EY", "Spec X", "Spec Y"]  # adjust as needed
allow_pct = 2.0   # occupancy I/II: 2.0%; III: 1.5%; IV: 1.0%
cd_over_i = 1.0   # set to actual Cd/I for your system

# ── Story heights from "Story Definitions" table (top→bottom) ──────────────
sd = model.DatabaseTables.GetTableForDisplayArray(
    "Story Definitions", [], "All", 0, [], 0, [])
sd_fields = list(sd[1])
sd_data   = list(sd[6])
nc = len(sd_fields)
iS = next(i for i, f in enumerate(sd_fields) if f.lower() == "story")
iH = next(i for i, f in enumerate(sd_fields) if f.lower() == "height")
nr = sd[5]
stories = [(sd_data[r*nc+iS], float(sd_data[r*nc+iH] or 0)) for r in range(nr)]
# stories is top→bottom: stories[0] = roof, stories[-1] = lowest

rows = []
for cse in cases:
    model.Results.Setup.DeselectAllCasesAndCombosForOutput()
    model.Results.Setup.SetCaseSelectedForOutput(cse, True)

    # Method A — ETABS StoryDrifts (built-in, enveloped over Max/Min steps)
    sd_res = model.Results.StoryDrifts()
    n_sd   = sd_res[0]
    st_arr, dir_arr, drift_arr = list(sd_res[1]), list(sd_res[5]), list(sd_res[6])
    etabs_drift = {}
    for i in range(n_sd):
        k = (st_arr[i], dir_arr[i])
        v = abs(drift_arr[i])
        if etabs_drift.get(k, 0) < v:
            etabs_drift[k] = v

    # Method B — hand calc (δᵢ − δ_below) / h from joint displacements
    jd = model.Results.JointDrifts()
    jn = jd[0]
    j_story, j_dx, j_dy = list(jd[1]), list(jd[7]), list(jd[8])
    disp = {"X": {}, "Y": {}}
    for i in range(jn):
        s = j_story[i]
        if abs(j_dx[i]) > disp["X"].get(s, 0): disp["X"][s] = abs(j_dx[i])
        if abs(j_dy[i]) > disp["Y"].get(s, 0): disp["Y"][s] = abs(j_dy[i])

    for idx, (story, h_in) in enumerate(stories):
        if h_in <= 0:
            continue
        below = stories[idx+1][0] if idx+1 < len(stories) else None
        for direction in ("X", "Y"):
            e_drift = etabs_drift.get((story, direction))
            if e_drift is None:
                continue
            d_top = disp[direction].get(story, 0)
            d_bot = disp[direction].get(below, 0) if below else 0
            hand   = (d_top - d_bot) / h_in
            pct    = e_drift * cd_over_i * 100.0
            dc     = pct / allow_pct
            rows.append({
                "story":      story,
                "case":       cse,
                "dir":        direction,
                "h_m":        round(h_in * 0.0254, 3),
                "etabs_drift": round(e_drift, 6),
                "hand_drift":  round(hand, 6),
                "drift_pct":   round(pct, 3),
                "allow_pct":   allow_pct,
                "dc":          round(dc, 3),
                "status":      "OK" if pct <= allow_pct else "FAIL",
            })

fails   = [r for r in rows if r["status"] == "FAIL"]
gov     = max(rows, key=lambda r: r["drift_pct"]) if rows else {}

result = {
    "allow_pct":    allow_pct,
    "cd_over_i":    cd_over_i,
    "total_checks": len(rows),
    "failures":     len(fails),
    "governing":    gov,
    "fail_list":    fails,
    "all_rows":     sorted(rows, key=lambda r: r["drift_pct"], reverse=True)[:20],
}
```

## Notes
- `StoryDrifts()` returns indices: `[0]=n, [1]=Story, [2]=LoadCase, [3]=StepType, [4]=StepNum, [5]=Dir, [6]=Drift, [7]=Label, [8]=X, [9]=Y, [10]=Z`
- ETABS `Drift` is the inelastic ratio only when ETABS applies Cd internally — if you supply raw elastic results, multiply by Cd/I yourself
- For RS cases, displacements are unsigned envelopes, so the hand calc is approximate; the ETABS StoryDrifts value governs
- Story table order is **top→bottom**; `below = stories[idx+1]` for the hand calc
- Units: `SetPresentUnits(6)` = lb_in_F — heights in inches; convert to metres with `× 0.0254`
