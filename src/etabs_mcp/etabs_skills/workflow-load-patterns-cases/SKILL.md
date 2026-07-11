---
name: workflow-load-patterns-cases
description: Create missing load patterns and load cases in ETABS — gravity (Dead/SuperDead/Live), seismic ELF (ASCE 7-05 auto), wind (ASCE 7-05 auto), composite cases (DL, LLA), Ev = 0.2·SDS·Dead, modal, and response spectrum cases.
---

# workflow-load-patterns-cases

One-stop setup for all standard load patterns and load cases needed before combo generation. Reads what already exists and creates only what is missing. Never modifies existing patterns or cases.

## When to use
- New model setup before defining load combinations
- Adding missing seismic (ELF) or wind auto patterns
- Creating composite cases (DL = all Dead, LLA = all Live) for combo reference
- Creating Ev = 0.2·SDS × Dead patterns (vertical seismic per ASCE 7-05 §12.4.2.2)
- Creating modal and response-spectrum load cases

## Item creation order

```
Phase 1: Load Patterns
  → gravity SuperDead (PWL, FF), Live (Live_G, Live_W, LLR)
  → seismic auto patterns EX, EY  (ASCE 7-05 via database table)
  → wind auto patterns WX, WY     (ASCE 7-05 via database table)

Phase 2: RS Function  (ASCE 7-05 design spectrum, built from SDS/SD1/TL)

Phase 3: Load Cases
  → individual static cases (one pattern each): PW, FF, Live_G, Live_W, LLR, EX, EY, WX, WY
  → composite static cases:
      DL  = Dead + SuperDead patterns (SF = 1.0 each)
      LLA = Live patterns (SF = 1.0 each)
  → modal case (Eigen, standard settings)
  → RS cases Spec X (U1), Spec Y (U2), scale = 386.089 (lb_in_F)
  → Ev case = 0.2·SDS × all Dead-type patterns
```

## Verified code

```python
import math

model.SetPresentUnits(6)   # lb_in_F throughout

# ── Seismic parameters ─────────────────────────────────────────────────────
Ss=1.5; S1=0.6; TL=8.0; Fa=1.0; Fv=1.5
R=8.0; Omega=3.0; Cd=5.5; I=1.0; Ecc=0.05
SDS = 2/3*Fa*Ss; SD1 = 2/3*Fv*S1

# ── Wind parameters ───────────────────────────────────────────────────────
WindSpeed=115; ExpType="C"; WindImp=1.0; Kzt=1.0; GustF=0.85; Kd=0.85

# ── Story range ────────────────────────────────────────────────────────────
top_story = "Roof"; bot_story = "Base"

# ── Pattern / case names (edit to match project) ──────────────────────────
names = {
    "PW": "PWL", "FF": "FF", "LiveG": "Live_G", "LiveW": "Live_W",
    "LLR": "LLR", "EX": "EX", "EY": "EY", "WX": "WX", "WY": "WY",
    "DL": "DL", "LLA": "LLA", "Ev": "Ev",
    "Modal": "MODAL CASE", "RsFunc": "ASCE 7-05",
    "SpecX": "Spec X", "SpecY": "Spec Y",
}

# ── Helpers ────────────────────────────────────────────────────────────────
def pat_exists(n):
    cnt, pats = model.LoadPatterns.GetNameList()[0:2]
    return n in list(pats)

def case_exists(n):
    cnt, cases = model.LoadCases.GetNameList()[0:2]
    return n in list(cases)

def dead_patterns():
    cnt, pats = model.LoadPatterns.GetNameList()[0:2]
    dead = []
    for p in list(pats):
        r = model.LoadPatterns.GetLoadType(p)
        if r[0] == 0 and r[1] in (1, 5):  # Dead=1, SuperDead=5
            dead.append(p)
    return dead

def live_patterns():
    cnt, pats = model.LoadPatterns.GetNameList()[0:2]
    live = []
    for p in list(pats):
        r = model.LoadPatterns.GetLoadType(p)
        if r[0] == 0 and r[1] == 3:  # Live=3
            live.append(p)
    return live

log = []

# ── PHASE 1: Load Patterns ─────────────────────────────────────────────────
model.SetModelIsLocked(False)

# Gravity patterns (SuperDead = 5, Live = 3)
for n, pat_type, desc in [
    (names["PW"],    5, "SuperDead — partition wall"),
    (names["FF"],    5, "SuperDead — floor finish"),
    (names["LiveG"], 3, "Live — general"),
    (names["LiveW"], 3, "Live — walkway"),
    (names["LLR"],   3, "Live — roof live"),
]:
    if not pat_exists(n):
        model.LoadPatterns.Add(n, pat_type, 0, True)
        log.append(f"CREATED pattern '{n}' ({desc})")
    else:
        log.append(f"EXISTS pattern '{n}'")

# Seismic patterns EX, EY via database table (ASCE 7-05 auto seismic)
for pat_name, x_dir in [(names["EX"], "Yes"), (names["EY"], "No")]:
    if not pat_exists(pat_name):
        model.LoadPatterns.Add(pat_name, 6, 0, True)   # 6 = Quake
        # Write ASCE 7-05 seismic parameters via database table edit
        fields = ["Name","LoadType","AutoSeismicCode","IsAuto","XDir","YDir",
                  "EccRatio","TopStory","BotStory","Ss","S1","Fa","Fv","TL",
                  "R","Omega","Cd","I","UserT","Ct","CtAndX","PeriodT"]
        vals   = [pat_name,"Quake","ASCE 7-05","Yes",x_dir,("No" if x_dir=="Yes" else "Yes"),
                  str(Ecc),top_story,bot_story,
                  str(Ss),str(S1),str(Fa),str(Fv),str(TL),
                  str(R),str(Omega),str(Cd),str(I),"No","0.0466","0.0466; 0.9","0"]
        model.DatabaseTables.SetTableForEditingArray(
            "Load Pattern Definitions - Auto Seismic - ASCE 7-05",
            0, fields, 1, vals)
        model.DatabaseTables.ApplyEditedTables(True)
        log.append(f"CREATED seismic pattern '{pat_name}' ({'X' if x_dir=='Yes' else 'Y'})")
    else:
        log.append(f"EXISTS seismic pattern '{pat_name}'")

# Wind patterns WX (0°), WY (90°) via database table
for pat_name, angle in [(names["WX"], 0.0), (names["WY"], 90.0)]:
    if not pat_exists(pat_name):
        model.LoadPatterns.Add(pat_name, 7, 0, True)   # 7 = Wind
        fields = ["Name","LoadType","AutoWindCode","IsAuto","Angle","WindSpeed",
                  "ExpType","Importance","kzt","GustFact","Kd"]
        vals   = [pat_name,"Wind","ASCE 7-05","Yes",str(angle),str(WindSpeed),
                  ExpType,str(WindImp),str(Kzt),str(GustF),str(Kd)]
        model.DatabaseTables.SetTableForEditingArray(
            "Load Pattern Definitions - Auto Wind - ASCE 7-05",
            0, fields, 1, vals)
        model.DatabaseTables.ApplyEditedTables(True)
        log.append(f"CREATED wind pattern '{pat_name}' ({angle}°)")
    else:
        log.append(f"EXISTS wind pattern '{pat_name}'")

# ── PHASE 2: RS Function ───────────────────────────────────────────────────
rs_func = names["RsFunc"]
# Check via FuncRS.GetNameList
fr = model.Func.FuncRS.GetNameList()
rs_names = list(fr[1]) if fr[0] > 0 else []
if rs_func not in rs_names:
    T0  = 0.2*SD1/SDS
    Ts  = SD1/SDS
    pts = [(0, 0.4*SDS), (T0, SDS), (Ts, SDS), (TL, SD1/TL), (4*TL, SD1*TL/(4*TL)**2)]
    n_pts = len(pts)
    T_arr = [p[0] for p in pts]
    Sa_arr= [p[1] for p in pts]
    model.Func.FuncRS.SetUser(rs_func, n_pts, T_arr, Sa_arr)
    log.append(f"CREATED RS function '{rs_func}' (SDS={SDS:.3f}, SD1={SD1:.3f})")
else:
    log.append(f"EXISTS RS function '{rs_func}'")

# ── PHASE 3: Load Cases ────────────────────────────────────────────────────

# 3a — individual static cases (one pattern each)
for n in [names["PW"], names["FF"], names["LiveG"], names["LiveW"], names["LLR"],
          names["EX"], names["EY"], names["WX"], names["WY"]]:
    if not case_exists(n):
        model.LoadCases.StaticLinear.SetCase(n)
        loadTypes = ["Load"]; loadNames = [n]; factors = [1.0]
        model.LoadCases.StaticLinear.SetLoads(n, 1, loadTypes, loadNames, factors)
        log.append(f"CREATED static case '{n}'")
    else:
        log.append(f"EXISTS case '{n}'")

# 3b — composite cases DL and LLA
dead = dead_patterns()
live = live_patterns()
for case_name, pats, label in [(names["DL"], dead, "DL"), (names["LLA"], live, "LLA")]:
    if not case_exists(case_name):
        if pats:
            model.LoadCases.StaticLinear.SetCase(case_name)
            model.LoadCases.StaticLinear.SetLoads(
                case_name, len(pats),
                ["Load"]*len(pats), pats, [1.0]*len(pats))
            log.append(f"CREATED composite case '{case_name}' = {pats}")
        else:
            log.append(f"SKIPPED '{case_name}' — no {'Dead' if label=='DL' else 'Live'} patterns found")
    else:
        log.append(f"EXISTS case '{case_name}'")

# 3c — modal case
modal = names["Modal"]
if not case_exists(modal):
    model.LoadCases.ModalEigen.SetCase(modal)
    model.LoadCases.ModalEigen.SetNumberModes(modal, 12, 1)
    log.append(f"CREATED modal case '{modal}' (12 modes)")
else:
    log.append(f"EXISTS modal case '{modal}'")

# 3d — RS cases
rs_sf = 386.089   # lb_in_F
for case_name, func_dir, angle in [
    (names["SpecX"], "U1", 0.0),
    (names["SpecY"], "U2", 90.0),
]:
    if not case_exists(case_name):
        model.LoadCases.ResponseSpectrum.SetCase(case_name)
        model.LoadCases.ResponseSpectrum.SetLoads(
            case_name, 1, [func_dir], [rs_func], [rs_sf], [angle])
        model.LoadCases.ResponseSpectrum.SetModalCase(case_name, modal)
        log.append(f"CREATED RS case '{case_name}' ({func_dir}, {angle}°)")
    else:
        log.append(f"EXISTS case '{case_name}'")

# 3e — Ev = 0.2·SDS × Dead patterns
ev_factor = round(0.2 * SDS, 6)
ev_case   = names["Ev"]
dead = dead_patterns()   # re-query after creation
if not case_exists(ev_case):
    if dead:
        model.LoadCases.StaticLinear.SetCase(ev_case)
        model.LoadCases.StaticLinear.SetLoads(
            ev_case, len(dead),
            ["Load"]*len(dead), dead, [ev_factor]*len(dead))
        log.append(f"CREATED Ev case '{ev_case}' = {ev_factor:.6f} × {dead}")
    else:
        log.append(f"SKIPPED Ev case — no Dead patterns found")
else:
    log.append(f"EXISTS Ev case '{ev_case}'")

result = {"items": len(log), "log": log}
```

## Notes
- `LoadPatterns.Add(name, type, selfWt, includeInSelfWt)` — type codes: Dead=1, Live=3, SuperDead=5, Quake=6, Wind=7
- Auto seismic and auto wind pattern parameters are written via `DatabaseTables.SetTableForEditingArray` + `ApplyEditedTables` — this is the only reliable way to set ASCE 7-05 parameters programmatically
- `LoadCases.StaticLinear.SetLoads(name, n, typeArr, nameArr, sfArr)` — `typeArr` entries are `"Load"` (pattern) or `"Accel"` (acceleration)
- Composite case DL bundles all Dead + SuperDead patterns found in the model at SF=1.0; add PWL, FF after creating them, then re-query
- Ev = 0.2·SDS × Dead patterns; factor = `0.2 × (2/3 × Fa × Ss)`
- RS function `SetUser(name, n, T_list, Sa_list)` — build the ASCE 7-05 design spectrum from T0, Ts, Ts, TL inflection points
- RS case scale factor 386.089 converts g to in/s² (lb_in_F); use 9.81 for kN_m_C
- Run `model.Analyze.RunAnalysis()` after setup to validate all cases run cleanly
