---
name: etabs-auto-seismic
description: "Use when defining auto seismic or auto wind lateral load patterns in ETABS. Covers ASCE 7-05 ELF seismic (IBC 2006/2009/2012), BNBC 2020, and ASCE 7-05 wind. CRITICAL: All COM SetXXX methods (SetIBC2006, SetASCE705, etc.) are BROKEN — always use DatabaseTables. SiteClass must always be 'F' to preserve custom Fa/Fv."
---

# ETABS Auto Lateral Load Patterns

## ⚠️ CRITICAL RULES — READ FIRST

| Rule | Detail |
|---|---|
| **COM methods broken** | `AutoSeismic.SetIBC2006()`, `SetASCE705()`, etc. — argument types cannot be resolved. Always use DatabaseTables instead. |
| **SiteClass = "F" always** | ETABS overwrites Fa/Fv for classes A–E with its own table. Only `"F"` preserves your custom values. |
| **Table name** | `"Load Pattern Definitions - Auto Seismic - ASCE 7-05"` |
| **Pattern must exist first** | Add the load pattern with `model.LoadPatterns.Add(name, 5, 0.0, True)` before writing the table row. |

---

## Available Auto-Lateral Tables (ETABS 23.2.0)

| Table Name | Use For |
|---|---|
| `Load Pattern Definitions - Auto Seismic - ASCE 7-05` | ASCE 7-05 ELF seismic (IBC 2006 / IBC 2009 / IBC 2012) |
| `Load Pattern Definitions - Auto Wind - ASCE 7-05` | ASCE 7-05 wind |

---

## Auto Seismic — ASCE 7-05 (IBC 2012)

### Full Field List

```
Name, IsAuto, XDir, XDirPlusE, XDirMinusE,
YDir, YDirPlusE, YDirMinusE, EccRatio,
TopStory, BotStory, PeriodType, CtAndX,
SsAndS1From, Ss, S1, TL, SiteClass, Fa, Fv,
SDS, SD1, R, Omega, Cd, I
```

### Key Field Values

| Field | Options / Notes |
|---|---|
| `IsAuto` | `"No"` = primary pattern; `"Yes"` = auto-generated ±eccentricity variant |
| `XDir` / `YDir` | `"Yes"` or `"No"` |
| `XDirPlusE`, `XDirMinusE` | `"Yes"` to include accidental eccentricity variants |
| `PeriodType` | `"Program Calculated"` or `"User Defined"` |
| `CtAndX` | `"0.016; 0.9"` for concrete MRF; `"0.028; 0.8"` for steel MRF |
| `SsAndS1From` | `"User Defined"` |
| `SiteClass` | **Always `"F"`** when using custom Fa/Fv |
| `SDS`, `SD1` | Computed: SDS = 2/3·Fa·Ss, SD1 = 2/3·Fv·S1 |

### Common Structural System Parameters (ASCE 7-05 Table 12.2-1)

| System | R | Ω | Cd |
|---|---|---|---|
| Concrete SMF | 8 | 3 | 5.5 |
| Steel SMF | 8 | 3 | 5.5 |
| Steel IMF | 4.5 | 3 | 4 |
| Concrete SW (special) | 6 | 2.5 | 5 |
| Steel EBF | 8 | 2 | 4 |

### IBC 2012 Standard Seismic Parameters

```
Ss=1.5, S1=0.6, TL=8, Site Class D → Fa=1.0, Fv=1.5
SDS = 2/3 × 1.0 × 1.5 = 1.00 g
SD1 = 2/3 × 1.5 × 0.6 = 0.60 g
```

---

## Verified Code — Add Auto Seismic Patterns

```python
TABLE = "Load Pattern Definitions - Auto Seismic - ASCE 7-05"

model.SetModelIsLocked(False)

# Step 1: Add load patterns (type 5 = Quake/Seismic)
for name in ("IBC_EQX", "IBC_EQY"):
    t = model.LoadPatterns.GetNameList()
    if name not in list(t[1]):
        model.LoadPatterns.Add(name, 5, 0.0, True)

# Step 2: Read existing seismic table (preserve other patterns)
t = model.DatabaseTables.GetTableForDisplayArray(TABLE, [], "All", 0, [], 0, [])
fields = [f for f in list(t[2]) if f is not None]
n = t[3]; nf = len(fields); flat = list(t[4])
rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n)]

# Step 3: Remove old versions to avoid duplicates
rows = [r for r in rows if r["Name"] not in ("IBC_EQX", "IBC_EQY")]

# Step 4: Build new rows
def seismic_row(name, x_dir, y_dir,
                top="Story4", bot="Base",
                Ss="1.5", S1="0.6", TL="8",
                Fa="1", Fv="1.5", SDS="1", SD1="0.6",
                R="8", Omega="3", Cd="5.5", I="1",
                Ct="0.016", x="0.9", ecc="0.05"):
    yes = lambda v: "Yes" if v else "No"
    return {
        "Name": name, "IsAuto": "No",
        "XDir": yes(x_dir), "XDirPlusE": yes(x_dir), "XDirMinusE": yes(x_dir),
        "YDir": yes(y_dir), "YDirPlusE": yes(y_dir), "YDirMinusE": yes(y_dir),
        "EccRatio": ecc,
        "TopStory": top, "BotStory": bot,
        "PeriodType": "Program Calculated",
        "CtAndX": f"{Ct}; {x}",
        "SsAndS1From": "User Defined",
        "Ss": Ss, "S1": S1, "TL": TL,
        "SiteClass": "F",   # ALWAYS "F" to preserve Fa/Fv
        "Fa": Fa, "Fv": Fv,
        "SDS": SDS, "SD1": SD1,
        "R": R, "Omega": Omega, "Cd": Cd, "I": I,
    }

rows.append(seismic_row("IBC_EQX", x_dir=True,  y_dir=False))
rows.append(seismic_row("IBC_EQY", x_dir=False, y_dir=True))

# Step 5: Write back
flat_out = tuple(r.get(f) for r in rows for f in fields)
ret_s = model.DatabaseTables.SetTableForEditingArray(TABLE, 0, fields, len(rows), flat_out)
ret_a = model.DatabaseTables.ApplyEditedTables(True)

result = {
    "staged": ret_s[0],        # 1 = OK
    "errors": ret_a[0],        # 0 = no errors
    "warnings": ret_a[1],
    "messages": list(ret_a[2]) if ret_a[2] else [],
}
# Expected: staged=1, errors=0, warnings=0
```

### Verify Read-Back

```python
t = model.DatabaseTables.GetTableForDisplayArray(
    "Load Pattern Definitions - Auto Seismic - ASCE 7-05", [], "All", 0, [], 0, []
)
fields = [f for f in list(t[2]) if f is not None]
n = t[3]; nf = len(fields); flat = list(t[4])
rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n)]
result = [r for r in rows if r.get("IsAuto") == "No"]  # primary patterns only
```

---

## BNBC 2020 — Use Dedicated Skill

For BNBC 2020, read skill `bnbc2020-seismic-params` — it uses the same
`"Load Pattern Definitions - Auto Seismic - ASCE 7-05"` table with BNBC-specific
Ss/S1/Fa/Fv values. The RS function also uses `SiteClass="F"` for same reason.

---

## Auto Wind — ASCE 7-05

### Full Field List

```
Name, IsAuto, Exposure, TopStory, BotStory, Parapet, UserCp, ASCECase,
e1, e2, WindSpeed, ExpType, Importance, kzt, GustFact, Kd,
WidthType, Angle, Story, Diaphragm, Width, Depth, X, Y
```

### Add Wind Pattern (Example)

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
    return {
        "Name": name, "IsAuto": "No",
        "Exposure": "Windward + Leeward",
        "TopStory": "Story4", "BotStory": "Base",
        "Parapet": "0", "UserCp": "No",
        "ASCECase": "1", "e1": "0.15", "e2": "0.15",
        "WindSpeed": "115",       # mph
        "ExpType": "B",           # Exposure category
        "Importance": "1",        # Importance factor
        "kzt": "1", "GustFact": "0.85", "Kd": "0.85",
        "WidthType": "User", "Angle": str(angle),
        "Story": None, "Diaphragm": None,
        "Width": None, "Depth": None, "X": None, "Y": None,
    }

rows.append(wind_row("WX", 0))
rows.append(wind_row("WY", 90))

flat_out = tuple(r.get(f) for r in rows for f in fields)
ret_s = model.DatabaseTables.SetTableForEditingArray(WIND_TABLE, 0, fields, len(rows), flat_out)
ret_a = model.DatabaseTables.ApplyEditedTables(True)
result = {"errors": ret_a[0], "warnings": ret_a[1]}
```

---

## Notes

- After `ApplyEditedTables`, ETABS auto-creates the ±eccentricity sub-patterns
  (e.g. `IBC_EQX1`, `IBC_EQX2`) — these have `IsAuto="Yes"`.
- `SDS` and `SD1` in the table are informational display values; ETABS recomputes
  them internally from Ss, S1, Fa, Fv, SiteClass.
- **Verified on ETABS 23.2.0**, model `IBC2012_Test.EDB`.
