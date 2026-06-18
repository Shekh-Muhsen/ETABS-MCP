# workflow-design-concrete

Run ACI concrete frame design and extract beam/column summary results.

## When to use
- After setting design modifiers and re-analyzing
- Check design ratios and critical combos
- Identify over/under-designed members

## Prerequisites
1. Model analyzed (`model.GetModelIsLocked()` == True)
2. Correct design modifiers applied (see `workflow-modifiers`)
3. Design combos set up in ETABS

## Verified code — Run design and check results

```python
model.SetPresentUnits(6)

# Step 1: Set design code
model.DesignConcrete.SetCode("ACI 318-14")
# Common codes: "ACI 318-08", "ACI 318-14", "ACI 318-19",
#               "ACI 318-08/IBC 2009"

# Step 2: Run design (requires model to be locked/analyzed)
model.DesignConcrete.StartDesign()

# Step 3: Get current code
code = model.DesignConcrete.GetCode()[0]

# NOTE: DesignConcrete.VerifyAllPassed() does NOT exist in ETABS 23.2.0 — AttributeError
# Use DatabaseTables to check design results instead (see below)

result = {"design_code": code}
```

## Extract beam summary results

```python
# GetSummaryResultsBeam returns 16-element tuple — VERIFIED indices:
# [n, Names, Stations, FlexCombo, TopAs, BotCombo_top, BotAs, BotCombo_bot,
#  ShearCombo, ShearRebar, PhiVcMajor, ..., ErrMsg, WarnMsg, ret]
# CRITICAL: top_As=[4], bot_As=[6]  (NOT [7] as you might expect)
beams = list(model.FrameObj.GetNameList()[1])

beam_results = []
for name in beams[:30]:
    try:
        r = model.DesignConcrete.GetSummaryResultsBeam(name, 0)
        if r[0] > 0:
            beam_results.append({
                "name":    name,
                "top_As":  round(r[4][0], 6) if r[4] else None,  # m² — index [4]
                "bot_As":  round(r[6][0], 6) if r[6] else None,  # m² — index [6]
            })
    except Exception:
        pass

result = {"beam_design": beam_results}
```

## Extract column summary results

```python
# GetSummaryResultsColumn returns 14-element tuple — VERIFIED indices:
# [n, Names, DesignType(int), Stations, combo, rebar_ratio, ..., ErrMsg, WarnMsg, ret]
# CRITICAL: combo=[4], rebar_ratio=[5]  (NOT [2]/[3] as old docs show)
cols = list(model.FrameObj.GetNameList()[1])

col_results = []
for name in cols[:30]:
    try:
        r = model.DesignConcrete.GetSummaryResultsColumn(name, 0)
        if r[0] > 0:
            col_results.append({
                "name":        name,
                "combo":       r[4][0] if r[4] else "",    # governing combo at [4]
                "rebar_ratio": r[5][0] if r[5] else None,  # rebar ratio at [5]
                "error":       r[11][0] if r[11] else "",   # ErrMsg at [11]
                "warning":     r[12][0] if r[12] else "",   # WarnMsg at [12]
            })
    except Exception:
        pass

result = {"column_design": col_results}
```

## Via DatabaseTables (preferred — full results, cleaner fields)

```python
# Table names need code+year suffix — e.g. "ACI 318-14" not just "ACI 318"
# VERIFIED working table names:
raw = model.DatabaseTables.GetTableForDisplayArray(
    "Concrete Beam Design Summary - ACI 318-14", [], "All", 0, [], 0, []
)
fields = [f for f in list(raw[2]) if f is not None]
flat = list(raw[4]); n = raw[3]; nf = len(fields)
rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n)]
result = {"beam_design": rows[:20], "fields": fields}

# For columns:
raw2 = model.DatabaseTables.GetTableForDisplayArray(
    "Concrete Column Design Summary - ACI 318-14", [], "All", 0, [], 0, []
)
fields2 = [f for f in list(raw2[2]) if f is not None]
flat2 = list(raw2[4]); n2 = raw2[3]; nf2 = len(fields2)
rows2 = [{fields2[j]: flat2[i*nf2+j] for j in range(nf2)} for i in range(n2)]

# For combo data:
raw3 = model.DatabaseTables.GetTableForDisplayArray(
    "Concrete Frame Design Load Combination Data", [], "All", 0, [], 0, []
)
```

## Notes
- `StartDesign()` blocks until design is complete
- `DesignConcrete.VerifyAllPassed()` does **NOT** exist in ETABS 23.2.0 — use DatabaseTables instead
- DatabaseTables design table names need `"- ACI 318-14"` suffix (or whichever code year)
- Call `DesignConcrete.ResetOverwrites(name, itemType)` to clear manual overwrites
- Results from `GetSummaryResultsBeam/Column` only available after `StartDesign()`
- `GetSummaryResultsBeam(name, 0)` and `GetSummaryResultsColumn(name, 0)` — pass itemType=0
