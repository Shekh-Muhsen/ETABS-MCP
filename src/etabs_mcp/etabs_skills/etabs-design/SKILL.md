---
name: etabs-design
description: "Use when running concrete or steel frame design, setting design codes, reading design summary results (DCR ratios, rebar areas), resetting design, and pier/spandrel wall design. Covers DesignConcrete, DesignSteel, GetSummaryResultsBeam, GetSummaryResultsColumn, GetSummaryResultsFrame."
---

# ETABS Frame Design

Read `etabs-core` and `etabs-analysis` first. Analysis must be **complete** (model locked) before running design.

---

## Steel Frame Design (`model.DesignSteel`)

### Common Steel Design Codes

| Code String | Standard |
|-------------|----------|
| `"AISC 360-16"` | AISC 360 16th edition |
| `"AISC 360-10"` | AISC 360 10th edition |
| `"AISC 360-05"` | AISC 360 05 edition |
| `"BS5950-2000"` | British Standard |
| `"EC3-2005"` | Eurocode 3 |
| `"IS 800:2007"` | Indian Standard |
| `"AS 4100-1998"` | Australian Standard |

### Set Steel Design Code

```python
# SetCode(CodeName) → ret
ret = model.DesignSteel.SetCode("AISC 360-16")

# GetCode() → [CodeName, ret]
t = model.DesignSteel.GetCode()
print("Steel design code:", t[0])
```

### Run Steel Design

```python
is_locked = model.GetModelIsLocked()
if not is_locked:
    print("Run analysis first — model is not locked")
else:
    ret = model.DesignSteel.StartDesign()
    if ret != 0:
        print("Steel design failed, ret =", ret)
    else:
        print("Steel design completed")
```

### Check All Frames Pass

```python
# DesignSteel.VerifyAllPassed() — NOT confirmed in ETABS 23.2.0
# DesignConcrete.VerifyAllPassed() → AttributeError — does NOT exist
# Use DatabaseTables or GetSummaryResults to check design ratios instead
t = model.DesignSteel.GetSummaryResultsFrame("", 0)
all_passed = all(list(t[2])[i] <= 1.0 for i in range(t[0]))
```

### Get Steel Design Summary — All Frames

```python
# GetSummaryResultsFrame(Name, ItemType) → [n, FrameName_t, Ratio_t, RatioType_t,
#   Location_t, ComboName_t, ErrMsg_t, WarnMsg_t, ret]
# Name="" + ItemType=0 returns all frames

t = model.DesignSteel.GetSummaryResultsFrame("", 0)
n = t[0]
frame_names = list(t[1])
ratios = list(t[2])
ratio_types = list(t[3])
locations = list(t[4])
combo_names = list(t[5])
err_msgs = list(t[6])
warn_msgs = list(t[7])
ret = t[-1]

result = [
    {"frame": frame_names[i], "DCR": ratios[i], "ratio_type": ratio_types[i],
     "location": locations[i], "combo": combo_names[i],
     "error": err_msgs[i], "warning": warn_msgs[i]}
    for i in range(n)
]
```

### Get Critical (Highest DCR) Steel Frame

```python
t = model.DesignSteel.GetSummaryResultsFrame("", 0)
n = t[0]
if n > 0:
    ratios = list(t[2])
    frame_names = list(t[1])
    combo_names = list(t[5])
    max_idx = ratios.index(max(ratios))
    result = {
        "critical_frame": frame_names[max_idx],
        "max_DCR": ratios[max_idx],
        "governing_combo": combo_names[max_idx],
    }
```

### Set Design Section Override

```python
# SetDesignSection(Name, PropName, ResetToLastAnalysis, ItemType) → ret
ret = model.DesignSteel.SetDesignSection("1", "W18X97", False, 0)
```

### Reset Steel Design

```python
ret = model.DesignSteel.ResetDesign()
```

---

## Concrete Frame Design (`model.DesignConcrete`)

### Common Concrete Design Codes

| Code String | Standard |
|-------------|----------|
| `"ACI 318-19"` | ACI 318 2019 (verified in ETABS 23.2.0) |
| `"ACI 318-14"` | ACI 318 2014 (verified in ETABS 23.2.0) |
| `"ACI 318-08"` | ACI 318 2008 (verified in ETABS 23.2.0) |
| `"ACI 318-08/IBC 2009"` | ACI 318-08 with IBC |
| `"Eurocode 2-2004"` | EN 1992-1-1 |
| `"BS 8110-97"` | British Standard |
| `"IS 456-2000"` | Indian Standard |
| `"AS 3600-2009"` | Australian Standard |
| `"GB 50010-2010"` | Chinese Standard |

### Set Concrete Design Code

```python
ret = model.DesignConcrete.SetCode("ACI 318-19")

t = model.DesignConcrete.GetCode()
print("Concrete design code:", t[0])
```

### Set Design Combinations

```python
# SetComboStrength(comboName, Selected) → ret
# CRITICAL: Takes TWO arguments — combo name AND a boolean. Missing the bool causes an error.
ret = model.DesignConcrete.SetComboStrength("ENV-ULS", True)
ret = model.DesignConcrete.SetComboStrength("1.2D+1.6L", True)
```

### Run Concrete Design

```python
is_locked = model.GetModelIsLocked()
if not is_locked:
    print("Run analysis first")
else:
    # Set design combinations first
    ret = model.DesignConcrete.SetComboStrength("ENV-ULS", True)

    ret = model.DesignConcrete.StartDesign()
    # NOTE: may return 1 if no design sections are assigned — check section assignments
    if ret != 0:
        print("Concrete design returned ret =", ret, "(may be OK if sections assigned)")
    else:
        print("Concrete design completed")
```

### Check All Frames Pass

```python
# DesignConcrete.VerifyAllPassed() does NOT exist in ETABS 23.2.0 — AttributeError
# Use DatabaseTables instead:
raw = model.DatabaseTables.GetTableForDisplayArray(
    "Concrete Beam Design Summary - ACI 318-14", [], "All", 0, [], 0, [])
# OR check GetSummaryResultsBeam for error/warn messages
```

### Verify a Specific Frame

```python
# VerifyPassed(Name) → [passed, ret]
t = model.DesignConcrete.VerifyPassed("1")
passed = t[0]
print("Frame 1 passed:", passed)
```

### Get Concrete Beam Design Summary

```python
# GetSummaryResultsBeam returns 16-element tuple — VERIFIED indices:
# [n, Names, Stations, FlexCombo, TopAs(m²), TopCombo, BotAs(m²), BotCombo,
#  ShearCombo, ShearRebar, PhiVcMajor, ...(more), ErrMsg, WarnMsg, ret]
# CRITICAL: top_As at [4], bot_As at [6]  (NOT [5] or [7])

t = model.DesignConcrete.GetSummaryResultsBeam("", 0)
n = t[0]
frame_names = list(t[1])
top_As = list(t[4])   # top rebar area (m²) — index [4]
bot_As = list(t[6])   # bot rebar area (m²) — index [6]

result = [
    {"frame": frame_names[i], "top_As_m2": top_As[i], "bot_As_m2": bot_As[i]}
    for i in range(n)
]
```

### Get Concrete Column Design Summary

```python
# GetSummaryResultsColumn returns 14-element tuple — VERIFIED indices:
# [n, Names, DesignType(int), Stations, Combo, RebarRatio, ...(more), ErrMsg, WarnMsg, ret]
# CRITICAL: combo at [4], rebar_ratio at [5]  (NOT [2]/[3] as prior docs showed)

t = model.DesignConcrete.GetSummaryResultsColumn("", 0)
n = t[0]
frame_names = list(t[1])
combos = list(t[4])        # governing combo — index [4]
rebar_ratios = list(t[5])  # rebar ratio — index [5]
err_msgs = list(t[11])     # ErrMsg at [11]
warn_msgs = list(t[12])    # WarnMsg at [12]
ret = t[-1]

result = [
    {"frame": frame_names[i], "combo": combos[i],
     "rebar_ratio": rebar_ratios[i], "error": err_msgs[i]}
    for i in range(n)
]
```

### Reset Concrete Design

```python
ret = model.DesignConcrete.ResetDesign()
```

### Reset Overwrites

```python
# ResetOverwrites(Name, ItemType) → ret
ret = model.DesignConcrete.ResetOverwrites("1", 0)       # single frame
ret = model.DesignConcrete.ResetOverwrites("", 2)         # all selected
```

---

## Design Overwrites (Frame-Level)

Overwrites apply code-specific parameters to individual frames, overriding global preferences.

### Steel Overwrites

```python
# OverwritesSteel.SetOverwrite(Name, Item, Value, ItemType=0) → ret
# Item numbers are code-specific — refer to ETABS documentation
# Common items (AISC 360-16):
# 1=DesignProcedure, 2=FrameType, 3=Omega0, 6=unbraced length ratio (major), etc.

# Force design on frame "1"
ret = model.DesignSteel.OverwritesSteel.SetOverwrite("1", 1, 1.0)
```

### Concrete Overwrites

```python
# OverwritesConcrete.SetOverwrite(Name, Item, Value, ItemType=0) → ret
ret = model.DesignConcrete.OverwritesConcrete.SetOverwrite("1", 1, 1.0)
```

---

## DatabaseTables — Design Results

Use DatabaseTables for tabular bulk export of design results. This is often more reliable than the `GetSummaryResults*` API methods and provides all frames at once.

### Common Design Table Names

| Table Name | Content |
|------------|---------|
| `"Steel Frame Design Summary - AISC 360-16"` | Steel DCR ratios (add code+year suffix) |
| `"Concrete Beam Design Summary - ACI 318-14"` | Beam rebar areas ✓ VERIFIED |
| `"Concrete Column Design Summary - ACI 318-14"` | Column rebar areas ✓ VERIFIED |
| `"Concrete Frame Design Load Combination Data"` | Design combo assignments (no suffix needed) |

> **CRITICAL:** Design table names require code+year suffix: `"ACI 318-14"` not `"ACI 318"`.
> Generic names like `"Concrete Beam Summary - ACI 318"` return ret=-96 (not found).
> Use `model.DatabaseTables.GetAllTables()` to find the exact table name for your code version.

```python
# Steel design summary
raw = model.DatabaseTables.GetTableForDisplayArray(
    "Steel Frame Design Summary - AISC 360", [], "All", 0, [], 0, []
)
fields = list(raw[2])
n_rows = raw[3]
flat = list(raw[4])
n_fields = len(fields)
rows = [{fields[j]: flat[i * n_fields + j] for j in range(n_fields)} for i in range(n_rows)]
result = rows
```

```python
# Concrete beam design summary — VERIFIED table name (needs code+year suffix)
raw = model.DatabaseTables.GetTableForDisplayArray(
    "Concrete Beam Design Summary - ACI 318-14", [], "All", 0, [], 0, []
)
fields = [f for f in list(raw[2]) if f is not None]
n_rows = raw[3]; flat = list(raw[4]); nf = len(fields)
result = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n_rows)]
```

```python
# Concrete column design summary — VERIFIED table name
raw = model.DatabaseTables.GetTableForDisplayArray(
    "Concrete Column Design Summary - ACI 318-14", [], "All", 0, [], 0, []
)
fields = [f for f in list(raw[2]) if f is not None]
n_rows = raw[3]; flat = list(raw[4]); nf = len(fields)
result = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n_rows)]
```

---

## Complete Steel Design Workflow

```python
# 1. Verify analysis is done
if not model.GetModelIsLocked():
    result = {"error": "Run analysis first"}
else:
    # 2. Set code
    ret = model.DesignSteel.SetCode("AISC 360-16")

    # 3. Run design
    ret = model.DesignSteel.StartDesign()
    if ret != 0:
        result = {"error": "Steel design failed", "ret": ret}
    else:
        # 4. Check overall pass/fail via summary ratios
        # (DesignSteel.VerifyAllPassed() not confirmed — check ratios instead)

        # 5. Get summary for all frames
        t = model.DesignSteel.GetSummaryResultsFrame("", 0)
        n = t[0]
        ratios = list(t[2])
        frame_names = list(t[1])
        combo_names = list(t[5])

        max_dcr = max(ratios) if n > 0 else 0
        max_idx = ratios.index(max_dcr) if n > 0 else 0

        all_passed = all(r <= 1.0 for r in ratios)
        result = {
            "all_passed": all_passed,
            "total_frames": n,
            "max_DCR": max_dcr,
            "critical_frame": frame_names[max_idx] if n > 0 else None,
            "governing_combo": combo_names[max_idx] if n > 0 else None,
            "frames_over_1": sum(1 for r in ratios if r > 1.0),
        }
```

---

## Complete Concrete Design Workflow

```python
if not model.GetModelIsLocked():
    result = {"error": "Run analysis first"}
else:
    ret = model.DesignConcrete.SetCode("ACI 318-19")

    # SetComboStrength(comboName, Selected) — BOTH args required
    ret = model.DesignConcrete.SetComboStrength("ENV-ULS", True)

    ret = model.DesignConcrete.StartDesign()
    # ret may be 1 even on partial success — check design results directly

    if ret != 0:
        result = {"warning": "Concrete design ret != 0 (ret=" + str(ret) + "), check section assignments", "ret": ret}
    else:
        # VerifyAllPassed() does NOT exist in ETABS 23.2.0 — AttributeError
        # Get column results
        tc = model.DesignConcrete.GetSummaryResultsColumn("", 0)
        n_col = tc[0]

        # Get beam results
        tb = model.DesignConcrete.GetSummaryResultsBeam("", 0)
        n_beam = tb[0]

        result = {
            "columns_designed": n_col,
            "beams_designed": n_beam,
        }
```
