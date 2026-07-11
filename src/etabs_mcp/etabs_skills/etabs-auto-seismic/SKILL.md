---
name: etabs-auto-seismic
description: "Use when defining auto seismic or auto wind lateral load patterns in ETABS. Covers ASCE 7-05 ELF seismic (IBC 2006/2009/2012), BNBC 2020, and ASCE 7-05 wind. CRITICAL: All COM SetXXX methods are BROKEN — always use DatabaseTables. SiteClass must always be 'F' to preserve custom Fa/Fv. Never strip field list — always use ETABS-returned fields when writing back."
---

# ETABS Auto Lateral Load Patterns

## ⚠️ CRITICAL RULES — READ FIRST

| Rule | Detail |
|---|---|
| **COM methods broken** | `AutoSeismic.SetIBC2006()`, `SetASCE705()`, `SetASCE716()` — all broken. `SetASCE716` silently writes `TopStory=BotStory="Base"` → zero base shear. Always use DatabaseTables. |
| **SiteClass = "F" always** | ETABS overwrites Fa/Fv for classes A–E with its own table. Only `"F"` preserves custom values. |
| **Never strip fields** | Use the field list returned by `GetTableForDisplayArray` when writing back. Filtering to a subset strips data from existing rows and deletes/corrupts them. |
| **Pattern must exist first** | Add the load pattern with `model.LoadPatterns.Add(name, 5, 0.0, True)` before writing the table row. |

---

## Available Auto-Lateral Tables (ETABS 23.2.0)

| Table Name | Use For |
|---|---|
| `Load Pattern Definitions - Auto Seismic - ASCE 7-05` | ASCE 7-05 ELF seismic — EX, EY, EXS, EYS (IBC 2006 / 2009 / 2012, BNBC 2020) |
| `Load Pattern Definitions - Auto Wind - ASCE 7-05` | ASCE 7-05 wind |

---

## Auto Seismic — ASCE 7-05

### Full Field List (ETABS 23.2.0 — verified)

```
Name, IsAuto, XDir, XDirPlusE, XDirMinusE,
YDir, YDirPlusE, YDirMinusE, EccRatio,
TopStory, BotStory, PeriodType, CtAndX,
SsAndS1From, Ss, S1, TL, SiteClass, Fa, Fv,
SDS, SD1, R, Omega, Cd, I
```

### Key Field Values — VERIFIED from live ETABS 23.2.0 model

| Field | Correct value | Common mistake |
|---|---|---|
| `PeriodType` | `"Approximate"` | ~~`"Program Calculated"`~~ ~~`"Prog Calc"`~~ — both break ETABS 23 |
| `CtAndX` | `"0.016; 0.9"` | ~~`"0.016, 0.9"`~~ (comma) — wrong separator, rejected |
| `SsAndS1From` | `"User Defined"` | ~~`"UserDefined"`~~ (no space) — rejected |
| `SiteClass` | `"F"` | Never A–E — ETABS overwrites Fa/Fv |
| `IsAuto` | `"No"` for primary | `"Yes"` = auto sub-pattern (EX1, EX2 etc.) |
| `XDirPlusE/MinusE` | Same as `XDir` | Must match XDir on primary rows |
| `YDirPlusE/MinusE` | Same as `YDir` | Must match YDir on primary rows |
| `TopStory` | Real story name e.g. `"Top of OHWT"` | Never `"Base"` — zero height = zero base shear |

### Verified Example — EX and EY exact values from model

```
EX: XDir=Yes, XDirPlusE=Yes, XDirMinusE=Yes, YDir=No, YDirPlusE=No, YDirMinusE=No
    TopStory="Top of OHWT", BotStory="Base", PeriodType="Approximate"
    CtAndX="0.016; 0.9", SsAndS1From="User Defined"
    Ss=0.5, S1=0.2, TL=4, SiteClass=F, Fa=1.35, Fv=2.7
    SDS=0.45, SD1=0.36, R=7, Omega=2.5, Cd=5, I=1

EY: YDir=Yes, YDirPlusE=Yes, YDirMinusE=Yes, XDir=No, XDirPlusE=No, XDirMinusE=No
    (same seismic parameters as EX)
```

### Verified Code — Add ASCE 7-05 Patterns (safe, preserves all existing rows)

```python
TABLE = "Load Pattern Definitions - Auto Seismic - ASCE 7-05"

model.SetModelIsLocked(False)

# Step 1: Add load pattern shells (type 5 = Quake)
for name in ("EQX", "EQY"):
    t = model.LoadPatterns.GetNameList()
    if name not in list(t[1]):
        model.LoadPatterns.Add(name, 5, 0.0, True)

# Step 2: Read existing table — use ETABS's own field list (NEVER filter it)
t = model.DatabaseTables.GetTableForDisplayArray(TABLE, [], "All", 0, [], 0, [])
fields = [f for f in list(t[2]) if f is not None]
n = t[3]; nf = len(fields); flat = list(t[4])
rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n)]

# Step 3: Remove only EQX/EQY (preserve EX, EY, EXS, EYS and all others)
rows = [r for r in rows if r["Name"] not in ("EQX", "EQY")]

# Step 4: Build new rows — start from blank dict with all fields
def make_row(name, x_dir,
             top="Top of OHWT", bot="Base",
             Ss=0.5, S1=0.2, TL=4, Fa=1.35, Fv=2.7,
             SDS=0.45, SD1=0.36, R=7, Omega=2.5, Cd=5, I=1, ecc=0.05):
    yes = lambda v: "Yes" if v else "No"
    r = {f: "" for f in fields}   # blank base — preserves any unknown fields
    r.update({
        "Name":         name,
        "IsAuto":       "No",
        "XDir":         yes(x_dir),
        "XDirPlusE":    yes(x_dir),
        "XDirMinusE":   yes(x_dir),
        "YDir":         yes(not x_dir),
        "YDirPlusE":    yes(not x_dir),
        "YDirMinusE":   yes(not x_dir),
        "EccRatio":     str(ecc),
        "TopStory":     top,
        "BotStory":     bot,
        "PeriodType":   "Approximate",          # VERIFIED: not "Program Calculated"
        "CtAndX":       "0.016; 0.9",           # VERIFIED: semicolon, not comma
        "SsAndS1From":  "User Defined",         # VERIFIED: space required
        "Ss":  str(Ss),  "S1": str(S1), "TL": str(TL),
        "SiteClass": "F",                       # ALWAYS "F"
        "Fa":  str(Fa),  "Fv": str(Fv),
        "SDS": str(SDS), "SD1": str(SD1),
        "R":   str(R),   "Omega": str(Omega), "Cd": str(Cd), "I": str(I),
    })
    return r

rows.append(make_row("EQX", x_dir=True))
rows.append(make_row("EQY", x_dir=False))

# Step 5: Write back using ETABS's own field list
flat_out = tuple(r.get(f, "") for r in rows for f in fields)
ret_s = model.DatabaseTables.SetTableForEditingArray(TABLE, 0, fields, len(rows), flat_out)
ret_a = model.DatabaseTables.ApplyEditedTables(True)
result = {"staged": ret_s[0], "errors": ret_a[0], "warnings": ret_a[1]}
# Expected: staged=1, errors=0, warnings=0
```

### Verify Read-Back

```python
t = model.DatabaseTables.GetTableForDisplayArray(
    "Load Pattern Definitions - Auto Seismic - ASCE 7-05", [], "All", 0, [], 0, [])
fields = [f for f in list(t[2]) if f is not None]
n = t[3]; nf = len(fields); flat = list(t[4])
rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n)]
result = [r for r in rows if r.get("IsAuto") == "No"]  # primary patterns only
```

---

## SetASCE716 COM Bug — TopStory=BotStory="Base"

`model.AutoSeismic.SetASCE716(...)` accepts the call but always writes `TopStory=BotStory="Base"`.
Zero story height → zero base shear → scale factor = 0 → RS cases scale to zero → all members overstress in design.
**Fix:** After any COM seismic call, always read back the table and verify TopStory is a real story name. Better: skip COM entirely and use DatabaseTables only.

---

## BNBC 2020

Uses the same `"Load Pattern Definitions - Auto Seismic - ASCE 7-05"` table with BNBC-specific Ss/S1/Fa/Fv values.
Read skill `bnbc2020-seismic-params` for the parameter values.

---

## Auto Wind — ASCE 7-05

### Full Field List

```
Name, IsAuto, Exposure, TopStory, BotStory, Parapet, UserCp, ASCECase,
e1, e2, WindSpeed, ExpType, Importance, kzt, GustFact, Kd,
WidthType, Angle, Story, Diaphragm, Width, Depth, X, Y
```

### Add Wind Pattern

```python
WIND_TABLE = "Load Pattern Definitions - Auto Wind - ASCE 7-05"

model.SetModelIsLocked(False)
for name in ("WX", "WY"):
    t = model.LoadPatterns.GetNameList()
    if name not in list(t[1]):
        model.LoadPatterns.Add(name, 6, 0.0, True)

t = model.DatabaseTables.GetTableForDisplayArray(WIND_TABLE, [], "All", 0, [], 0, [])
fields = [f for f in list(t[2]) if f is not None]
n = t[3]; nf = len(fields); flat = list(t[4])
rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n)]
rows = [r for r in rows if r["Name"] not in ("WX", "WY")]

def wind_row(name, angle):
    r = {f: "" for f in fields}
    r.update({
        "Name": name, "IsAuto": "No",
        "Exposure": "Windward + Leeward",
        "TopStory": "Story4", "BotStory": "Base",
        "Parapet": "0", "UserCp": "No",
        "ASCECase": "1", "e1": "0.15", "e2": "0.15",
        "WindSpeed": "115", "ExpType": "B",
        "Importance": "1", "kzt": "1", "GustFact": "0.85", "Kd": "0.85",
        "WidthType": "User", "Angle": str(angle),
    })
    return r

rows.append(wind_row("WX", 0))
rows.append(wind_row("WY", 90))

flat_out = tuple(r.get(f, "") for r in rows for f in fields)
ret_s = model.DatabaseTables.SetTableForEditingArray(WIND_TABLE, 0, fields, len(rows), flat_out)
ret_a = model.DatabaseTables.ApplyEditedTables(True)
result = {"errors": ret_a[0], "warnings": ret_a[1]}
```

---

## Notes

- After `ApplyEditedTables`, ETABS auto-creates ±eccentricity sub-patterns (e.g. `EQX1`, `EQX2`) with `IsAuto="Yes"`.
- `SDS` and `SD1` in the table are display values — ETABS recomputes them from Ss, S1, Fa, Fv, SiteClass.
- **Verified on ETABS 23.2.0**, model `D:\Atibazar\etabs2\Ati-N-15.$et`.
