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
# VerifyAllPassed() → [all_passed, ret]
t = model.DesignSteel.VerifyAllPassed()
all_passed = t[0]
print("All steel frames passed:", all_passed)
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
t = model.DesignConcrete.VerifyAllPassed()
all_passed = t[0]
print("All concrete frames passed:", all_passed)
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
# GetSummaryResultsBeam(Name, ItemType) → [n, FrameName_t, Location_t, RLLF_t,
#   TotalRatioTop_t, TotalRatioBot_t, TotalRatioShear_t,
#   RebarTop_t, RebarBot_t, RebarShear_t,
#   RebarMajorMin_t, WarnMsg_t, ret]
# OR for some ETABS versions:
# [n, FrameName_t, Location_t, RLLF_t, TopCombo_t, TopArea_t,
#  BotCombo_t, BotArea_t, VMajorCombo_t, AVMajor_t, TLCombo_t, ALong_t, ret]

t = model.DesignConcrete.GetSummaryResultsBeam("", 0)
n = t[0]
frame_names = list(t[1])
locations = list(t[2])

# Indices depend on ETABS version — check n first
print("Fields available:", len(t) - 2, "columns")
if n > 0:
    result = [
        {"frame": frame_names[i], "location": locations[i]}
        for i in range(n)
    ]
```

### Get Concrete Beam Design — Rebar Areas

```python
t = model.DesignConcrete.GetSummaryResultsBeam("", 0)
n = t[0]
frame_names = list(t[1])
locations = list(t[2])
# Indices [5]=TopArea, [7]=BotArea, [9]=ShearRebar (version-dependent — verify)

beams = []
for i in range(n):
    row = {"frame": frame_names[i], "location": locations[i]}
    # Try to get additional fields safely
    if len(t) > 6:
        row["top_area"] = list(t[5])[i] if len(t) > 5 else None
    if len(t) > 8:
        row["bot_area"] = list(t[7])[i] if len(t) > 7 else None
    beams.append(row)

result = beams
```

### Get Concrete Column Design Summary

```python
# GetSummaryResultsColumn(Name, ItemType) → [n, FrameName_t, MyComboName_t,
#   DesignType_t, DesignPTOpt_t, ErrMsg_t, WarnMsg_t, ret]

t = model.DesignConcrete.GetSummaryResultsColumn("", 0)
n = t[0]
frame_names = list(t[1])
combo_names = list(t[2])
design_types = list(t[3])
err_msgs = list(t[5])
warn_msgs = list(t[6])
ret = t[-1]

result = [
    {"frame": frame_names[i], "combo": combo_names[i],
     "design_type": design_types[i], "error": err_msgs[i]}
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
| `"Steel Frame Design Summary - AISC 360"` | Steel DCR ratios, governing combo |
| `"Steel Frame Design Summary - Eurocode 3"` | EC3 steel design results |
| `"Concrete Beam Summary - ACI 318"` | Beam rebar areas, ratios |
| `"Concrete Column Summary - ACI 318"` | Column rebar areas, DCR |
| `"Concrete Beam Summary - Eurocode 2"` | EC2 beam results |
| `"Concrete Column Summary - Eurocode 2"` | EC2 column results |
| `"Concrete Shear Wall Summary - ACI 318"` | Shear wall design |
| `"Steel Frame Design Preferences"` | Global design preferences |

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
# Concrete beam design summary
raw = model.DatabaseTables.GetTableForDisplayArray(
    "Concrete Beam Summary - ACI 318", [], "All", 0, [], 0, []
)
fields = list(raw[2])
n_rows = raw[3]
flat = list(raw[4])
n_fields = len(fields)
result = [{fields[j]: flat[i * n_fields + j] for j in range(n_fields)} for i in range(n_rows)]
```

```python
# Concrete column design summary
raw = model.DatabaseTables.GetTableForDisplayArray(
    "Concrete Column Summary - ACI 318", [], "All", 0, [], 0, []
)
fields = list(raw[2])
n_rows = raw[3]
flat = list(raw[4])
n_fields = len(fields)
result = [{fields[j]: flat[i * n_fields + j] for j in range(n_fields)} for i in range(n_rows)]
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
        # 4. Check overall pass/fail
        t_pass = model.DesignSteel.VerifyAllPassed()
        all_passed = t_pass[0]

        # 5. Get summary for all frames
        t = model.DesignSteel.GetSummaryResultsFrame("", 0)
        n = t[0]
        ratios = list(t[2])
        frame_names = list(t[1])
        combo_names = list(t[5])

        max_dcr = max(ratios) if n > 0 else 0
        max_idx = ratios.index(max_dcr) if n > 0 else 0

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
        t_pass = model.DesignConcrete.VerifyAllPassed()
        all_passed = t_pass[0]

        # Get column results
        tc = model.DesignConcrete.GetSummaryResultsColumn("", 0)
        n_col = tc[0]

        # Get beam results
        tb = model.DesignConcrete.GetSummaryResultsBeam("", 0)
        n_beam = tb[0]

        result = {
            "all_passed": all_passed,
            "columns_designed": n_col,
            "beams_designed": n_beam,
        }
```
