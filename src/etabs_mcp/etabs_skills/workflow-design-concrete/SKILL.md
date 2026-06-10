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

# Step 3: Check if all members passed
all_ok = model.DesignConcrete.VerifyAllPassed()

# Step 4: Get current code
code = model.DesignConcrete.GetCode()[0]

result = {
    "design_code": code,
    "all_passed": all_ok,
}
```

## Extract beam summary results

```python
# GetSummaryResultsBeam: [n, Name, Location, RLLF,
#   TopAsReqd, TopAsProvd, TopRatioBot, BotAsReqd, BotAsProvd, BotRatioBot,
#   VuMajor, PhiVcMajor, ErrMsg, WarnMsg, ret]
beams = list(model.FrameObj.GetNameList()[1])

beam_results = []
for name in beams[:30]:
    try:
        r = model.DesignConcrete.GetSummaryResultsBeam(name)
        if r[0] > 0:
            beam_results.append({
                "name":     name,
                "location": r[2][0],
                "top_As":   round(r[4][0], 4) if r[4] else None,
                "bot_As":   round(r[7][0], 4) if r[7] else None,
                "Vu_kN":    round(r[10][0], 2) if r[10] else None,
                "warn":     r[13][0] if r[13] else "",
            })
    except Exception:
        pass

result = {"beam_design": beam_results}
```

## Extract column summary results

```python
# GetSummaryResultsColumn: [n, Name, MyComboName, DesignType,
#   DesignPTOpt, ErrMsg, WarnMsg, ret]
cols = list(model.FrameObj.GetNameList()[1])

col_results = []
for name in cols[:30]:
    try:
        r = model.DesignConcrete.GetSummaryResultsColumn(name)
        if r[0] > 0:
            col_results.append({
                "name":    name,
                "combo":   r[2][0],
                "type":    r[3][0],
                "error":   r[5][0] if r[5] else "",
                "warning": r[6][0] if r[6] else "",
            })
    except Exception:
        pass

result = {"column_design": col_results}
```

## Via DatabaseTables (full results)

```python
t = model.DatabaseTables.GetTableForDisplayArray(
    "Concrete Frame Design Load Combination Data", [], "Mode", 0, [], 0, []
)
fields = list(t[2]); flat = list(t[4]); n = t[3]; nf = len(fields)
rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n)]
result = {"design_combos": rows[:20], "fields": fields}
```

## Notes
- `StartDesign()` blocks until design is complete
- `VerifyAllPassed()` returns True only if all members passed
- Call `DesignConcrete.ResetOverwrites(name, itemType)` to clear manual overwrites
- Design uses whichever combos are checked in ETABS design preferences
- Results from `GetSummaryResultsBeam/Column` only available after `StartDesign()`
