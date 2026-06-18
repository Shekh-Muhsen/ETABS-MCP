# workflow-story-drift

Extract story drifts for all seismic cases, check against code limits, and flag exceedances.

## When to use
- Post-analysis drift check
- ASCE 7, BNBC, or custom code compliance
- Identify critical story/direction

## Code drift limits (ASCE 7-16 Table 12.12-1)

| Structure Type | Risk Cat I/II | Risk Cat III | Risk Cat IV |
|---|---|---|---|
| Other structures | 2.0% | 1.5% | 1.0% |
| Masonry cantilever | 1.0% | 1.0% | 1.0% |
| 1-story, Cd·δ/hsx | 2.5% | 2.5% | 2.5% |

## Verified code

```python
model.SetPresentUnits(6)

# Select seismic cases
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
lc_names = list(model.LoadCases.GetNameList()[1])
seismic = [c for c in lc_names if any(k in c.upper() for k in ["EX","EY","SPEC","EQ"])]
for c in seismic:
    model.Results.Setup.SetCaseSelectedForOutput(c)

# StoryDrifts: [n, Story, Case, StepType, StepNum, Direction, Drift, Label, X, Y, ret]
drifts = model.Results.StoryDrifts()
n = drifts[0]

LIMIT = 0.02   # 2% — change as needed

rows = []
for i in range(n):
    d = abs(drifts[6][i])
    rows.append({
        "story":     drifts[1][i],
        "case":      drifts[2][i],
        "direction": drifts[5][i],
        "drift":     round(d, 5),
        "drift_pct": round(d * 100, 3),
        "PASS":      d <= LIMIT,
    })

fails   = [r for r in rows if not r["PASS"]]
max_row = max(rows, key=lambda r: r["drift"]) if rows else {}

result = {
    "limit_pct":    LIMIT * 100,
    "total_checks": n,
    "failures":     len(fails),
    "max_drift":    max_row,
    "top_10":       sorted(rows, key=lambda r: r["drift"], reverse=True)[:10],
    "fail_list":    fails,
}
```

## Notes
- `StoryDrifts()` returns one row per story × case × direction
- `Drift` is the inelastic drift ratio = Cd × elastic drift / hsx (when ETABS applies Cd)
- Check `Direction` field: "X" or "Y"
- For envelope combos (Max/Min), ETABS reports both; take `abs()`
- `StepType` = "Max" or "Min" for response spectrum / envelope cases
