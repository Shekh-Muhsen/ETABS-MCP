# BNBC 2020 Load Combinations — Complete Auto-Generator

Generates all SLS + ULS + Deflection combinations for any Zone (1–4) and Soil Type (SA–SE).
Total: 63 combos per model setup.

---

## Step 1 — BNBC 2020 Parameter Tables

```python
# Official gazette values — Fa/Fv same for all zones, only Ss/S1 change
BNBC_Ss = {'Zone1':0.3,  'Zone2':0.5,  'Zone3':0.7,  'Zone4':0.9 }
BNBC_S1 = {'Zone1':0.12, 'Zone2':0.20, 'Zone3':0.28, 'Zone4':0.36}
BNBC_Fa = {'SA':1.0, 'SB':1.2,  'SC':1.15, 'SD':1.35, 'SE':1.4 }
BNBC_Fv = {'SA':1.0, 'SB':1.5,  'SC':1.725,'SD':2.7,  'SE':1.75}

def bnbc_params(zone, soil):
    """zone=1-4 (int), soil='SA'-'SE' (str). Returns dict of seismic params."""
    Ss  = BNBC_Ss[f'Zone{zone}']
    S1  = BNBC_S1[f'Zone{zone}']
    Fa  = BNBC_Fa[soil]
    Fv  = BNBC_Fv[soil]
    SDS = round(2/3*Fa*Ss, 4)
    SD1 = round(2/3*Fv*S1, 4)
    TL  = 4.0
    To  = round(0.2*SD1/SDS, 4)
    Ts  = round(SD1/SDS, 4)
    return {'Ss':Ss,'S1':S1,'Fa':Fa,'Fv':Fv,'SDS':SDS,'SD1':SD1,'TL':TL,'To':To,'Ts':Ts}
```

---

## Step 2 — Combo Coefficient Derivation

### ULS (Ultimate Limit State) — from SDS
```python
def uls_factors(SDS):
    """
    gp = amplified gravity with seismic  (1.2 + 0.2×SDS)
    gm = reduced gravity for uplift      (0.9 - 0.2×SDS)
    Source: ASCE 7-05 §12.4.2, Ev = 0.2×SDS×D
    """
    gp = round(1.2 + 0.2*SDS, 4)
    gm = round(0.9 - 0.2*SDS, 4)
    return gp, gm
```

### SLS (Serviceability) — from SDS
```python
def sls_factors(SDS):
    """
    SLS seismic = 0.70 × ULS seismic  (ASD reduction = 1/√2 ≈ 0.70)
    Ev_sls = 0.70 × 0.2 × SDS
    """
    Ev   = round(0.70 * 0.2 * SDS, 6)
    return {
        'D_up'   : round(1.0 + Ev,          4),  # seismic only   DL factor
        'D_up75' : round(1.0 + 0.75*Ev,     4),  # seismic+gravity DL factor
        'D_dn'   : round(0.6 - Ev,           4),  # uplift          DL factor
        'EH'     : 0.70,                           # 100% SLS seismic
        'EH3'    : round(0.70 * 0.30,        4),  # 30% orthogonal → 0.21
        'EH75'   : round(0.75 * 0.70,        4),  # 75% simult. × seismic → 0.525
        'EH753'  : round(0.75 * 0.70 * 0.30, 4),  # 75% × seismic × ortho → 0.1575
    }
```

### Coefficient reference table (all zones × soils SA–SE)

**ULS factors gp / gm:**

| | SA | SB | SC | SD | SE |
|---|---|---|---|---|---|
| Zone 1 | 1.240 / 0.860 | 1.248 / 0.852 | 1.246 / 0.854 | 1.254 / 0.846 | 1.256 / 0.844 |
| Zone 2 | 1.267 / 0.833 | 1.280 / 0.820 | 1.277 / 0.823 | 1.290 / 0.810 | 1.293 / 0.807 |
| Zone 3 | 1.293 / 0.807 | 1.312 / 0.788 | 1.307 / 0.793 | **1.326 / 0.774** | 1.331 / 0.769 |
| Zone 4 | 1.320 / 0.780 | 1.344 / 0.756 | 1.338 / 0.762 | 1.362 / 0.738 | 1.368 / 0.732 |

**SLS D_up / D_up75 / D_dn:**

| | SA | SB | SC | SD | SE |
|---|---|---|---|---|---|
| Zone 1 | 1.028/1.021/0.572 | 1.034/1.025/0.566 | 1.032/1.024/0.568 | 1.038/1.028/0.562 | 1.039/1.029/0.561 |
| Zone 2 | 1.047/1.035/0.553 | 1.056/1.042/0.544 | 1.054/1.040/0.546 | 1.063/1.047/0.537 | 1.065/1.049/0.535 |
| Zone 3 | 1.065/1.049/0.535 | 1.078/1.059/0.522 | 1.075/1.056/0.525 | **1.088/1.066/0.512** | 1.091/1.068/0.509 |
| Zone 4 | 1.084/1.063/0.516 | 1.101/1.076/0.499 | 1.097/1.072/0.503 | 1.113/1.085/0.487 | 1.118/1.088/0.482 |

Note: EH=0.70, EH3=0.21, EH75=0.525, EH753=0.1575 are constant for ALL zones and soils.

---

## Step 3 — Complete Combo Definitions

### ULS Combos (20 total)

```python
def uls_combos(zone, soil, dead='Dead', live='LL', eqx='EQX', eqy='EQY'):
    SDS = bnbc_params(zone, soil)['SDS']
    gp, gm = uls_factors(SDS)

    return {
        # ── Gravity only ──────────────────────────────────────────────────
        '2001-1.4D'         : [(dead, 1.4)],
        '2002-1.2D+1.6LL'   : [(dead, 1.2), (live, 1.6)],

        # ── Seismic ULS — X dominant, amplified gravity (2003-2006) ─────
        # 100% EQX ± 30% EQY   (ASCE 7-05 §12.5.3 orthogonal rule)
        f'2003-{gp}D+LL+EQX+0.3EQY'  : [(dead,gp),(live,1.0),(eqx, 1.0),(eqy, 0.3)],
        f'2004-{gp}D+LL+EQX-0.3EQY'  : [(dead,gp),(live,1.0),(eqx, 1.0),(eqy,-0.3)],
        f'2005-{gp}D+LL-EQX+0.3EQY'  : [(dead,gp),(live,1.0),(eqx,-1.0),(eqy, 0.3)],
        f'2006-{gp}D+LL-EQX-0.3EQY'  : [(dead,gp),(live,1.0),(eqx,-1.0),(eqy,-0.3)],

        # ── Seismic ULS — Y dominant, amplified gravity (2007-2010) ─────
        # 100% EQY ± 30% EQX
        f'2007-{gp}D+LL+0.3EQX+EQY'  : [(dead,gp),(live,1.0),(eqx, 0.3),(eqy, 1.0)],
        f'2008-{gp}D+LL+0.3EQX-EQY'  : [(dead,gp),(live,1.0),(eqx, 0.3),(eqy,-1.0)],
        f'2009-{gp}D+LL-0.3EQX+EQY'  : [(dead,gp),(live,1.0),(eqx,-0.3),(eqy, 1.0)],
        f'2010-{gp}D+LL-0.3EQX-EQY'  : [(dead,gp),(live,1.0),(eqx,-0.3),(eqy,-1.0)],

        # ── Seismic ULS — X dominant, uplift (2011-2014) ─────────────────
        f'2011-{gm}D+EQX+0.3EQY'     : [(dead,gm),(eqx, 1.0),(eqy, 0.3)],
        f'2012-{gm}D+EQX-0.3EQY'     : [(dead,gm),(eqx, 1.0),(eqy,-0.3)],
        f'2013-{gm}D-EQX+0.3EQY'     : [(dead,gm),(eqx,-1.0),(eqy, 0.3)],
        f'2014-{gm}D-EQX-0.3EQY'     : [(dead,gm),(eqx,-1.0),(eqy,-0.3)],

        # ── Seismic ULS — Y dominant, uplift (2015-2018) ─────────────────
        f'2015-{gm}D+0.3EQX+EQY'     : [(dead,gm),(eqx, 0.3),(eqy, 1.0)],
        f'2016-{gm}D+0.3EQX-EQY'     : [(dead,gm),(eqx, 0.3),(eqy,-1.0)],
        f'2017-{gm}D-0.3EQX+EQY'     : [(dead,gm),(eqx,-0.3),(eqy, 1.0)],
        f'2018-{gm}D-0.3EQX-EQY'     : [(dead,gm),(eqx,-0.3),(eqy,-1.0)],
    }
```

### SLS Combos (39 total)

```python
def sls_combos(zone, soil, dead='DL', live='LL', llr='LLR',
               wx='WX', wy='WY', ex='EX', ey='EY'):
    SDS = bnbc_params(zone, soil)['SDS']
    F   = sls_factors(SDS)
    D   = F['D_up'];   D75 = F['D_up75'];  Dd = F['D_dn']
    EH  = F['EH'];     EH3 = F['EH3']
    E75 = F['EH75'];   E753= F['EH753']

    return {
        # ── Gravity service (3) ───────────────────────────────────────────
        '1001-DL+LL'                     : [(dead,1.0),(live,1.0)],
        '1002-DL+LLR'                    : [(dead,1.0),(llr, 1.0)],
        '1003-DL+0.75LL+LLR'            : [(dead,1.0),(live,0.75),(llr,1.0)],

        # ── Wind service (4) ──────────────────────────────────────────────
        '1004-DL+WX'                     : [(dead,1.0),(wx, 1.0)],
        '1005-DL-WX'                     : [(dead,1.0),(wx,-1.0)],
        '1006-DL+WY'                     : [(dead,1.0),(wy, 1.0)],
        '1007-DL-WY'                     : [(dead,1.0),(wy,-1.0)],

        # ── Seismic SLS only (1008-1015) — D_up×DL ± 0.70E ± 0.21E_ortho ─
        f'1008-{D}DL+{EH}EX+{EH3}EY'    : [(dead,D),(ex, EH),(ey, EH3)],
        f'1009-{D}DL-{EH}EX+{EH3}EY'    : [(dead,D),(ex,-EH),(ey, EH3)],
        f'1010-{D}DL+{EH}EX-{EH3}EY'    : [(dead,D),(ex, EH),(ey,-EH3)],
        f'1011-{D}DL-{EH}EX-{EH3}EY'    : [(dead,D),(ex,-EH),(ey,-EH3)],
        f'1012-{D}DL+{EH3}EX+{EH}EY'    : [(dead,D),(ex, EH3),(ey, EH)],
        f'1013-{D}DL-{EH3}EX+{EH}EY'    : [(dead,D),(ex,-EH3),(ey, EH)],
        f'1014-{D}DL+{EH3}EX-{EH}EY'    : [(dead,D),(ex, EH3),(ey,-EH)],
        f'1015-{D}DL-{EH3}EX-{EH}EY'    : [(dead,D),(ex,-EH3),(ey,-EH)],

        # ── Wind + gravity SLS (1016-1019) — 0.75 simultaneous ───────────
        '1016-DL+0.75LL+0.75LLR+0.75WX' : [(dead,1.0),(live,0.75),(llr,0.75),(wx, 0.75)],
        '1017-DL+0.75LL+0.75LLR-0.75WX' : [(dead,1.0),(live,0.75),(llr,0.75),(wx,-0.75)],
        '1018-DL+0.75LL+0.75LLR+0.75WY' : [(dead,1.0),(live,0.75),(llr,0.75),(wy, 0.75)],
        '1019-DL+0.75LL+0.75LLR-0.75WY' : [(dead,1.0),(live,0.75),(llr,0.75),(wy,-0.75)],

        # ── Seismic + gravity SLS (1020-1027) — 0.75 simultaneous ────────
        f'1020-{D75}DL+0.75LL+{E75}EX+{E753}EY'  : [(dead,D75),(live,0.75),(llr,0.75),(ex, E75),(ey, E753)],
        f'1021-{D75}DL+0.75LL-{E75}EX+{E753}EY'  : [(dead,D75),(live,0.75),(llr,0.75),(ex,-E75),(ey, E753)],
        f'1022-{D75}DL+0.75LL+{E75}EX-{E753}EY'  : [(dead,D75),(live,0.75),(llr,0.75),(ex, E75),(ey,-E753)],
        f'1023-{D75}DL+0.75LL-{E75}EX-{E753}EY'  : [(dead,D75),(live,0.75),(llr,0.75),(ex,-E75),(ey,-E753)],
        f'1024-{D75}DL+0.75LL+{E753}EX+{E75}EY'  : [(dead,D75),(live,0.75),(llr,0.75),(ex, E753),(ey, E75)],
        f'1025-{D75}DL+0.75LL-{E753}EX+{E75}EY'  : [(dead,D75),(live,0.75),(llr,0.75),(ex,-E753),(ey, E75)],
        f'1026-{D75}DL+0.75LL+{E753}EX-{E75}EY'  : [(dead,D75),(live,0.75),(llr,0.75),(ex, E753),(ey,-E75)],
        f'1027-{D75}DL+0.75LL-{E753}EX-{E75}EY'  : [(dead,D75),(live,0.75),(llr,0.75),(ex,-E753),(ey,-E75)],

        # ── Wind uplift SLS (1028-1031) ───────────────────────────────────
        '1028-0.6DL+WX'                  : [(dead,0.6),(wx, 1.0)],
        '1029-0.6DL-WX'                  : [(dead,0.6),(wx,-1.0)],
        '1030-0.6DL+WY'                  : [(dead,0.6),(wy, 1.0)],
        '1031-0.6DL-WY'                  : [(dead,0.6),(wy,-1.0)],

        # ── Seismic uplift SLS (1032-1039) — D_dn×DL ± 0.70E ± 0.21E_ortho
        f'1032-{Dd}DL+{EH}EX+{EH3}EY'   : [(dead,Dd),(ex, EH),(ey, EH3)],
        f'1033-{Dd}DL-{EH}EX+{EH3}EY'   : [(dead,Dd),(ex,-EH),(ey, EH3)],
        f'1034-{Dd}DL+{EH}EX-{EH3}EY'   : [(dead,Dd),(ex, EH),(ey,-EH3)],
        f'1035-{Dd}DL-{EH}EX-{EH3}EY'   : [(dead,Dd),(ex,-EH),(ey,-EH3)],
        f'1036-{Dd}DL+{EH3}EX+{EH}EY'   : [(dead,Dd),(ex, EH3),(ey, EH)],
        f'1037-{Dd}DL-{EH3}EX+{EH}EY'   : [(dead,Dd),(ex,-EH3),(ey, EH)],
        f'1038-{Dd}DL+{EH3}EX-{EH}EY'   : [(dead,Dd),(ex, EH3),(ey,-EH)],
        f'1039-{Dd}DL-{EH3}EX-{EH}EY'   : [(dead,Dd),(ex,-EH3),(ey,-EH)],
    }
```

### Deflection Combos (4 total)

```python
def deflection_combos(dead='Dead', live='LL', llr='LLR', wx='WX', wy='WY'):
    return {
        '3001-DL+0.5LL+0.25LLR-LT' : [(dead,1.0),(live,0.5),(llr,0.25)],
        '3002-DL+LL-ST'             : [(dead,1.0),(live,1.0)],
        '3003-DL+0.5LL+0.7WX'      : [(dead,1.0),(live,0.5),(wx,0.7)],
        '3004-DL+0.5LL+0.7WY'      : [(dead,1.0),(live,0.5),(wy,0.7)],
    }
```

---

## Step 4 — Write All 63 Combos to ETABS

```python
def create_all_combos(model, zone, soil,
                      dead='Dead', live='LL', llr='LLR',
                      wx='WX',  wy='WY',
                      eqx='EQX', eqy='EQY',
                      ex='EX',   ey='EY'):
    """
    Creates all 63 load combinations for given zone and soil type.
    zone : int 1-4
    soil : str 'SA','SB','SC','SD','SE'
    Remaining args: load pattern names as they exist in the ETABS model.
    Returns (fatal, warnings) from ApplyEditedTables.
    """
    COMBO_TABLE = 'Load Combination Definitions'
    model.SetModelIsLocked(False)

    # CRITICAL: hardcode fields — when all combos are empty the table returns only
    # ('Name','Type','IsAuto','GUID','Notes') and LoadName/SF are missing from schema.
    USE_F = ('Name', 'Type', 'IsAuto', 'LoadName', 'SF', 'GUID', 'Notes')
    nf = len(USE_F)

    # Read existing combos (to preserve non-BNBC combos)
    raw   = model.DatabaseTables.GetTableForDisplayArray(COMBO_TABLE,[],  'All',0,[],0,[])
    f_got = [x for x in list(raw[2]) if x is not None]
    n_got = raw[3]
    rows  = [{f_got[j]:list(raw[4])[i*len(f_got)+j] for j in range(len(f_got))} for i in range(n_got)] if f_got else []

    # Merge all three sets
    ALL = {}
    ALL.update(uls_combos(zone, soil, dead, live, eqx, eqy))
    ALL.update(sls_combos(zone, soil, dead, live, llr, wx, wy, ex, ey))
    ALL.update(deflection_combos(dead, live, llr, wx, wy))

    # Drop any existing version of our combos
    rows_keep = [r for r in rows if r.get('Name') not in list(ALL.keys())]

    def blank(): return {fld: None for fld in USE_F}

    new_rows = []
    for name, cases in ALL.items():
        for idx,(ln,sf) in enumerate(cases):
            r = blank()
            r['Name']     = name
            r['LoadName'] = ln
            r['SF']       = str(sf)
            if idx == 0:
                r['Type']   = 'Linear Add'
                r['IsAuto'] = 'No'
            new_rows.append(r)

    rows_out = rows_keep + new_rows
    flat_out = tuple(r.get(fld) for r in rows_out for fld in USE_F)
    ret_s = model.DatabaseTables.SetTableForEditingArray(COMBO_TABLE, 0, USE_F, len(rows_out), flat_out)
    ret_a = model.DatabaseTables.ApplyEditedTables(True)
    return ret_a[0], ret_a[1]   # fatal, warnings
```

### Usage examples
```python
# Zone 2, SD soil (Dhaka typical)
fatal, warn = create_all_combos(model, zone=2, soil='SD')

# Zone 3, SB soil
fatal, warn = create_all_combos(model, zone=3, soil='SB',
                                 dead='Dead', live='LL', llr='LLR',
                                 wx='WX', wy='WY', eqx='EQX', eqy='EQY',
                                 ex='EX', ey='EY')

# Zone 1, SA soil
fatal, warn = create_all_combos(model, zone=1, soil='SA')
```

---

## Complete Coefficient Logic (WHY each number)

### ULS coefficients
| Factor | Formula | Meaning |
|---|---|---|
| **1.4** | fixed | Gravity only, no live — high DL structures |
| **1.2** | fixed | Factored DL with live or lateral |
| **1.6** | fixed | Factored LL alone (most uncertain) |
| **1.0LL** with E | fixed | Full LL during quake unlikely |
| **gp = 1.2+0.2×SDS** | Ev up | Vertical seismic amplifies gravity |
| **gm = 0.9−0.2×SDS** | Ev dn | Vertical seismic reduces gravity → uplift/tension |
| **±1.0 EQX** | 100% | Primary seismic direction |
| **±0.3 EQY** | 30% | Orthogonal simultaneous (ASCE 7-05 §12.5.3) |

### SLS coefficients
| Factor | Formula | Meaning |
|---|---|---|
| **0.70** | SLS/ULS | ASD seismic reduction = 1/√2 |
| **D_up = 1.0+0.70×0.2×SDS** | Ev_sls | SLS vertical seismic |
| **D_up75 = 1.0+0.75×0.70×0.2×SDS** | Ev×0.75 | SLS vert. seismic × simultaneous reduction |
| **D_dn = 0.6−0.70×0.2×SDS** | Ev_sls | SLS uplift — min DL |
| **0.21 = 0.70×0.30** | ortho | SLS seismic × 30% orthogonal |
| **0.525 = 0.75×0.70** | simult | 75% simult. × SLS seismic |
| **0.1575 = 0.75×0.70×0.30** | all | 75% × SLS seismic × 30% ortho |
| **0.75** | simult | Full gravity AND full lateral same time unlikely |
| **0.6D** with W/E | uplift | Minimum DL against uplift forces |

### Deflection coefficients
| Factor | Meaning |
|---|---|
| **0.5LL** | Sustained portion of live (long-term creep) |
| **0.25LLR** | Small sustained roof live component |
| **0.7W** | Frequent wind (not peak gust) for deflection |

---

## Total Combo Count

| Group | Count | Purpose |
|---|---|---|
| ULS gravity | 2 | Strength — gravity only |
| ULS seismic amplified (X+Y dom.) | 8 | Strength — seismic + gravity |
| ULS seismic uplift (X+Y dom.) | 8 | Strength — seismic uplift |
| SLS gravity service | 3 | Deflection/crack — gravity |
| SLS wind service | 4 | Drift/deflection — wind |
| SLS seismic only | 8 | Drift — seismic |
| SLS wind+gravity (0.75) | 4 | Service — combined |
| SLS seismic+gravity (0.75) | 8 | Service — combined |
| SLS wind uplift | 4 | Service — wind uplift |
| SLS seismic uplift | 8 | Service — seismic uplift |
| Deflection | 4 | Beam/slab deflection limits |
| **TOTAL** | **63** | |

---

## Notes
- **Load pattern names must match the model exactly.** Check with `model.LoadPatterns.GetNameList()` before calling.
- EQX/EQY = static auto-seismic patterns. EX/EY = response spectrum cases. These are different load cases.
- For SLS seismic (1008–1039), use EX/EY (response spectrum). For ULS seismic (2001+), use EQX/EQY (static) OR SX/SY (RS) depending on model setup.
- Orthogonal 30% rule is now included in all ULS seismic combos (was missing in older simplified set).
- `create_all_combos()` preserves all pre-existing non-BNBC combos in the model.
