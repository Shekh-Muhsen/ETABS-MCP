# workflow-gravity-report

Extract total gravity loads (Dead, Live) at base and per story using BaseReact and DatabaseTables.

## When to use
- Verify total building weight
- Compare dead vs live load ratio
- Generate load takeoff for design

## Verified code — Total base gravity

```python
model.SetPresentUnits(6)

model.Results.Setup.DeselectAllCasesAndCombosForOutput()
gravity_cases = ["Dead", "LL", "LLR", "SDL", "FF"]
lc_names = list(model.LoadCases.GetNameList()[1])
active = [c for c in gravity_cases if c in lc_names]
for c in active:
    model.Results.Setup.SetCaseSelectedForOutput(c)

# BaseReact: [n, Case, StepType, StepNum, FX, FY, FZ, MX, MY, MZ, gX, gY, gZ, ret]
base = model.Results.BaseReact()
n = base[0]

totals = {}
for i in range(n):
    case = base[1][i]
    fz   = abs(base[6][i])
    if case not in totals or fz > totals[case]:
        totals[case] = round(fz, 1)

result = {
    "gravity_cases_found": active,
    "base_vertical_kN":   totals,
    "total_dead_kN":      totals.get("Dead", 0),
    "total_live_kN":      totals.get("LL", 0),
    "total_W_kN":         totals.get("Dead", 0) + totals.get("LL", 0),
}
```

## Story-level forces via DatabaseTables (ENV combo)

```python
# Note: GetTableForDisplayArray returns whichever cases/combos are
# currently set for display in ETABS. Set Dead/LL output first.
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
model.Results.Setup.SetCaseSelectedForOutput("Dead")
model.Results.Setup.SetCaseSelectedForOutput("LL")

t = model.DatabaseTables.GetTableForDisplayArray(
    "Story Forces", [], "Mode", 0, [], 0, []
)
fields = list(t[2]); flat = list(t[4]); n = t[3]; nf = len(fields)
rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n)]

# Group by story + case, take Bottom location
by_story = {}
for r in rows:
    st   = r.get("Story","")
    case = r.get("OutputCase","")
    loc  = r.get("Location","")
    p    = r.get("P","0")
    if loc == "Bottom" and st and case:
        key = (st, case)
        by_story[key] = round(float(p or 0), 1)

result = {"story_forces_bottom": {str(k): v for k, v in by_story.items()}}
```

## Notes
- `FZ` from `BaseReact` = total vertical reaction = total gravity load
- `P` in Story Forces = cumulative axial load at story level
- For envelope combos, table only shows the selected combo — use `SetCaseSelectedForOutput` to target individual cases
- `StoryForce()` API method does not exist — use DatabaseTables or BaseReact
