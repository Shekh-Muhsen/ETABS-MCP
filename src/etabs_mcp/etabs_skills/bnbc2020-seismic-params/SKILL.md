# BNBC 2020 Seismic Parameters — Auto Calculator

Automatically compute Ss, S1, Fa, Fv, SDS, SD1 for any BNBC 2020 Zone + Site Class combination.

---

## Input Parameters

| Parameter | Options |
|---|---|
| Zone | 1, 2, 3, 4 |
| SiteClass | SA, SB, SC, SD, SE, SF |

---

## BNBC 2020 Tables (official gazette)

### Mapped Spectral Accelerations (Table 6.C.1)
```python
BNBC_Ss = {'Zone1': 0.3, 'Zone2': 0.5, 'Zone3': 0.7, 'Zone4': 0.9}
BNBC_S1 = {'Zone1': 0.12, 'Zone2': 0.20, 'Zone3': 0.28, 'Zone4': 0.36}
```

### Site Coefficients Fa (Table 6.C.2) — same for all zones
```python
BNBC_Fa = {'SA': 1.0, 'SB': 1.2, 'SC': 1.15, 'SD': 1.35, 'SE': 1.4, 'SF': 2.1}
```
SF = 1.5 × SE (site-specific study required per BNBC; 1.5× is minimum).

### Site Coefficients Fv (Table 6.C.3) — same for all zones
```python
BNBC_Fv = {'SA': 1.0, 'SB': 1.5, 'SC': 1.725, 'SD': 2.7, 'SE': 1.75, 'SF': 2.625}
```
SF = 1.5 × SE.

---

## Calculator Function

```python
def bnbc_params(zone, site_class):
    """
    zone        : int 1-4
    site_class  : str 'SA','SB','SC','SD','SE','SF'
    returns     : dict with Ss, S1, Fa, Fv, SDS, SD1, To, Ts, TL
    """
    BNBC_Ss = {'Zone1':0.3,  'Zone2':0.5,  'Zone3':0.7,  'Zone4':0.9 }
    BNBC_S1 = {'Zone1':0.12, 'Zone2':0.20, 'Zone3':0.28, 'Zone4':0.36}
    BNBC_Fa = {'SA':1.0, 'SB':1.2,  'SC':1.15, 'SD':1.35, 'SE':1.4,  'SF':2.1  }
    BNBC_Fv = {'SA':1.0, 'SB':1.5,  'SC':1.725,'SD':2.7,  'SE':1.75, 'SF':2.625}

    key = f'Zone{zone}'
    Ss  = BNBC_Ss[key]
    S1  = BNBC_S1[key]
    Fa  = BNBC_Fa[site_class]
    Fv  = BNBC_Fv[site_class]
    SDS = round(2/3 * Fa * Ss, 6)
    SD1 = round(2/3 * Fv * S1, 6)
    TL  = 4.0
    To  = round(0.2 * SD1 / SDS, 6)
    Ts  = round(SD1 / SDS, 6)

    return {'Ss':Ss, 'S1':S1, 'Fa':Fa, 'Fv':Fv,
            'SDS':SDS, 'SD1':SD1, 'To':To, 'Ts':Ts, 'TL':TL}
```

### Usage example
```python
p = bnbc_params(2, 'SD')
# Ss=0.5, S1=0.2, Fa=1.35, Fv=2.7, SDS=0.45, SD1=0.36, To=0.16, Ts=0.8, TL=4.0

p = bnbc_params(1, 'SA')
# Ss=0.3, S1=0.12, Fa=1.0, Fv=1.0, SDS=0.2, SD1=0.08, To=0.08, Ts=0.4, TL=4.0

p = bnbc_params(1, 'SD')
# Ss=0.3, S1=0.12, Fa=1.35, Fv=2.7, SDS=0.27, SD1=0.216, To=0.16, Ts=0.8, TL=4.0
```

---

## Full Reference Table — All Zones × All Site Classes

### SDS = 2/3 × Fa × Ss

| Site Class | Fa | Zone 1 (Ss=0.3) | Zone 2 (Ss=0.5) | Zone 3 (Ss=0.7) | Zone 4 (Ss=0.9) |
|---|---|---|---|---|---|
| SA | 1.000 | 0.200 | 0.333 | 0.467 | 0.600 |
| SB | 1.200 | 0.240 | 0.400 | 0.560 | 0.720 |
| SC | 1.150 | 0.230 | 0.383 | 0.537 | 0.690 |
| SD | 1.350 | 0.270 | 0.450 | 0.630 | 0.810 |
| SE | 1.400 | 0.280 | 0.467 | 0.653 | 0.840 |
| SF | 2.100 | 0.420 | 0.700 | 0.980 | 1.260 |

### SD1 = 2/3 × Fv × S1

| Site Class | Fv | Zone 1 (S1=0.12) | Zone 2 (S1=0.20) | Zone 3 (S1=0.28) | Zone 4 (S1=0.36) |
|---|---|---|---|---|---|
| SA | 1.000 | 0.080 | 0.133 | 0.187 | 0.240 |
| SB | 1.500 | 0.120 | 0.200 | 0.280 | 0.360 |
| SC | 1.725 | 0.138 | 0.230 | 0.322 | 0.414 |
| SD | 2.700 | 0.216 | 0.360 | 0.504 | 0.648 |
| SE | 1.750 | 0.140 | 0.233 | 0.327 | 0.420 |
| SF | 2.625 | 0.210 | 0.350 | 0.490 | 0.630 |

---

## ETABS RS Function Creation — VERIFIED METHOD (User Defined table)

### CRITICAL: Use 'Functions - Response Spectrum - User Defined', NOT ASCE7-05 table
The `'Functions - Response Spectrum - ASCE7-05'` table is **NOT available** on a fresh/new model
(returns empty fields and rows). Attempting to write to it silently succeeds but the function
never appears. Always use `'Functions - Response Spectrum - User Defined'` and supply the
spectrum curve as explicit T-Sa pairs computed from the BNBC 2020 four-segment shape.

Fields for User Defined table: `('Name', 'Period', 'Value', 'DampRatio', 'GUID')`

```python
def create_bnbc_rs(model, zone, site_class, func_name=None):
    """
    Create BNBC 2020 RS function in ETABS as a User Defined spectrum.
    Verified working on ETABS 23.2.0 — 2026-06-15.
    """
    p = bnbc_params(zone, site_class)
    if func_name is None:
        func_name = f'BNBC2020-Z{zone}-{site_class}'

    SDS=p['SDS']; SD1=p['SD1']; To=p['To']; Ts=p['Ts']; TL=p['TL']

    def sa(T):
        if T <= 0:      return round(0.4*SDS, 6)
        elif T <= To:   return round(SDS*(0.4 + 0.6*T/To), 6)
        elif T <= Ts:   return round(SDS, 6)
        elif T <= TL:   return round(SD1/T, 6)
        else:           return round(SD1*TL/T**2, 6)

    T_pts = [0, 0.02, 0.04, 0.08, 0.12, 0.16, 0.20, 0.30, 0.40, 0.50, 0.60,
             0.70, 0.80, 0.90, 1.00, 1.20, 1.50, 1.75, 2.00, 2.50, 3.00,
             3.50, 4.00, 4.50, 5.00]
    spectrum = [(T, sa(T)) for T in T_pts]

    RS_TABLE = 'Functions - Response Spectrum - User Defined'
    model.SetModelIsLocked(False)
    raw = model.DatabaseTables.GetTableForDisplayArray(RS_TABLE, [], 'All', 0, [], 0, [])
    USE_F = tuple(x for x in list(raw[2]) if x is not None)
    nf = len(USE_F); n = raw[3]
    rows = [{USE_F[j]: list(raw[4])[i*nf+j] for j in range(nf)} for i in range(n)] if nf else []

    # Remove old version, add new rows (one per T-Sa point)
    rows_keep = [r for r in rows if r.get('Name') != func_name]
    new_rows = []
    for idx, (T, Sa) in enumerate(spectrum):
        r = {fld: None for fld in USE_F}
        r['Name'] = func_name
        r['Period'] = str(T)
        r['Value']  = str(Sa)
        if idx == 0:
            r['DampRatio'] = '0.05'
        new_rows.append(r)

    rows_out = rows_keep + new_rows
    flat_out = tuple(r.get(fld) for r in rows_out for fld in USE_F)
    ret_s = model.DatabaseTables.SetTableForEditingArray(RS_TABLE, 0, USE_F, len(rows_out), flat_out)
    ret_a = model.DatabaseTables.ApplyEditedTables(True)
    # ret_s[0]==1 staged OK; ret_a[0]==0 no fatal errors
    return p, ret_a

# After creating the function, set RS load case:
# model.LoadCases.ResponseSpectrum.SetCase("EX")
# model.LoadCases.ResponseSpectrum.SetLoads(
#     "EX", 1, ["U1"], [func_name], [9.81], ["Global"], [0.0])
# Scale factor = g = 9.81 (kN_m units); multiply by I if I ≠ 1.0
```

### Verify the function was created
```python
raw = model.DatabaseTables.GetTableForDisplayArray(
    'Functions - Response Spectrum - User Defined', [], 'All', 0, [], 0, [])
flds = tuple(x for x in list(raw[2]) if x is not None); nf = len(flds)
rows = [{flds[j]: list(raw[4])[i*nf+j] for j in range(nf)} for i in range(raw[3])]
func_names = list(set(r.get('Name') for r in rows))
print("RS functions:", func_names)  # should include your func_name
```

---

## Spectrum Shape (BNBC 2020 / ASCE 7-05 4-segment)

```python
def bnbc_spectrum(p, T):
    """Sa(T) in g given params dict from bnbc_params()."""
    SDS, SD1, To, Ts, TL = p['SDS'], p['SD1'], p['To'], p['Ts'], p['TL']
    if   T <= 0:   return round(0.4 * SDS, 6)
    elif T <= To:  return round(SDS * (0.4 + 0.6 * T / To), 6)
    elif T <= Ts:  return round(SDS, 6)
    elif T <= TL:  return round(SD1 / T, 6)
    else:          return round(SD1 * TL / T**2, 6)
```

---

## ETABS Auto Seismic (ELF) Setup — VERIFIED METHOD (ASCE 7-05 DatabaseTables)

### CRITICAL: Load pattern must already exist before writing to auto seismic table
ETABS rejects `"Item EQX not recognized"` if the named load pattern doesn't exist in the model.
Create EQX/EQY load patterns first (type=Seismic), THEN write to the auto seismic table.

### Verified fields (23 fields, exclude IsAuto — it's read-only)
```
('Name','XDir','XDirPlusE','XDirMinusE',
 'YDir','YDirPlusE','YDirMinusE',
 'EccRatio','TopStory','BotStory','PeriodType','CtAndX',
 'SsAndS1From','Ss','S1','TL','SiteClass','Fa','Fv',
 'R','Omega','Cd','I')
```

### Verified `PeriodType` value
- `'Program Calculated'` — ETABS computes period from eigenvalue analysis. **This is the ONLY accepted string** (not 'Ct', not 'Approximate', not 'User Defined').
- `CtAndX` stores Ct and x as `'0.0466; 0.9'` (concrete MF per ASCE 7-05 T12.8-2) but is ignored when PeriodType='Program Calculated'.
- For user-specified period: PeriodType string unknown — not yet tested.

### Verified `SiteClass` values
- `'F'` = Site Class F (SD soil in BNBC uses Fa=1.35, Fv=2.7 which matches SF=F in ETABS)
- Note: BNBC 2020 SD soil → ETABS SiteClass='F' with manually entered Fa, Fv

### Verified code (BNBC 2020 Zone 2, SD soil, ASCE 7-05 ELF, IMF)
```python
model.SetModelIsLocked(False)

# Step 1: ensure EQX and EQY load patterns already exist
# model.LoadPatterns.Add("EQX", 5, 0, True)  # 5=Seismic
# model.LoadPatterns.Add("EQY", 5, 0, True)

TABLE = 'Load Pattern Definitions - Auto Seismic - ASCE 7-05'
FIELDS = ('Name','XDir','XDirPlusE','XDirMinusE',
          'YDir','YDirPlusE','YDirMinusE',
          'EccRatio','TopStory','BotStory','PeriodType','CtAndX',
          'SsAndS1From','Ss','S1','TL','SiteClass','Fa','Fv',
          'R','Omega','Cd','I')

rows_out = [
    {'Name':'EQX','XDir':'Yes','XDirPlusE':'Yes','XDirMinusE':'Yes',
     'YDir':'No','YDirPlusE':'No','YDirMinusE':'No',
     'EccRatio':'0.05','TopStory':'Story4','BotStory':'Base',
     'PeriodType':'Program Calculated','CtAndX':'0.0466; 0.9',
     'SsAndS1From':'User Defined','Ss':'0.5','S1':'0.2','TL':'4',
     'SiteClass':'F','Fa':'1.35','Fv':'2.7',
     'R':'5','Omega':'3','Cd':'4.5','I':'1'},
    {'Name':'EQY','XDir':'No','XDirPlusE':'No','XDirMinusE':'No',
     'YDir':'Yes','YDirPlusE':'Yes','YDirMinusE':'Yes',
     'EccRatio':'0.05','TopStory':'Story4','BotStory':'Base',
     'PeriodType':'Program Calculated','CtAndX':'0.0466; 0.9',
     'SsAndS1From':'User Defined','Ss':'0.5','S1':'0.2','TL':'4',
     'SiteClass':'F','Fa':'1.35','Fv':'2.7',
     'R':'5','Omega':'3','Cd':'4.5','I':'1'},
]
flat = tuple(r.get(f) for r in rows_out for f in FIELDS)
ret_s = model.DatabaseTables.SetTableForEditingArray(TABLE, 0, FIELDS, 2, flat)
ret_a = model.DatabaseTables.ApplyEditedTables(True)
# Expected: "2 of 2 records successfully read"
log = ret_a[4]
for line in log.split('\r\n'):
    if 'record' in line.lower() or 'Error' in line:
        print(line.strip())
```

### BNBC 2020 ASCE 7-05 ELF parameters (Zone 2, SD soil, IMF R=5)
| Parameter | Value | Note |
|-----------|-------|------|
| Ss | 0.5 | Zone 2 mapped short-period |
| S1 | 0.2 | Zone 2 mapped 1-sec |
| SiteClass | F (ETABS) | = SD in BNBC; enter Fa/Fv manually |
| Fa | 1.35 | BNBC Table 6.C.2, SD soil |
| Fv | 2.7 | BNBC Table 6.C.3, SD soil |
| SDS | 0.45 | = 2/3 × Fa × Ss |
| SD1 | 0.36 | = 2/3 × Fv × S1 |
| R | 5 | IMF (Intermediate Moment Frame) |
| Omega | 3 | overstrength factor |
| Cd | 4.5 | deflection amplification |
| I | 1 | Risk Category II |
| TL | 4.0 | long-period transition (all zones) |

### Benchmark (5-story 3×3 bays @5m, 3.5m story, verified 2026-06-15)
- T1 = 0.404s (eigenvalue)
- EQX base shear = 796.5 kN, EQY = 796.5 kN
- Max amplified story drift = 0.0010 (PASS, limit 0.020)
- Cs = SDS/(R/I) = 0.45/5 = 0.090 → V = 0.090 × W

---

---

## ETABS Auto Wind Setup — VERIFIED METHOD (ASCE 7-05 DatabaseTables)

### CRITICAL: Write with a minimal row first — the table is empty on fresh models
Like the auto seismic table, `'Load Pattern Definitions - Auto Wind - ASCE 7-05'` returns empty
fields when no wind auto patterns exist. Write with the actual known fields (hardcoded). After
the first successful write, subsequent reads will return the proper schema.

### Verified fields
```
('Name', 'IsAuto', 'Exposure', 'TopStory', 'BotStory', 'Parapet', 'UserCp',
 'ASCECase', 'e1', 'e2', 'WindSpeed', 'ExpType', 'Importance', 'kzt',
 'GustFact', 'Kd', 'WidthType', 'Angle', 'Story', 'Diaphragm', 'Width', 'Depth', 'X', 'Y')
```

### ETABS auto wind field values
| Field | WX | WY | Notes |
|-------|----|----|-------|
| Exposure | `'Diaphragms'` | `'Diaphragms'` | Use diaphragm extents |
| ASCECase | `'1'` | `'1'` | ASCE 7-05 Case 1 |
| WindSpeed | `'80'` | `'80'` | mph; Dhaka area ~80 mph |
| ExpType | `'B'` | `'B'` | Exposure B (suburban) |
| Importance | `'1'` | `'1'` | Risk Cat II |
| kzt | `'1'` | `'1'` | Flat terrain (Kzt=1.0) |
| GustFact | `'0.85'` | `'0.85'` | Standard gust factor |
| Kd | `'0.85'` | `'0.85'` | Buildings directional |
| Angle | `'0'` | `'90'` | WX=X dir, WY=Y dir |
| TopStory | `'Story4'` | `'Story4'` | Highest story name |
| BotStory | `'Base'` | `'Base'` | |

### Verified code (BNBC 2020 Bangladesh defaults)
```python
model.SetModelIsLocked(False)

# WX and WY load patterns must already exist as Wind type (6)
TABLE_W = 'Load Pattern Definitions - Auto Wind - ASCE 7-05'
WIND_F = ('Name','IsAuto','Exposure','TopStory','BotStory','Parapet','UserCp',
          'ASCECase','e1','e2','WindSpeed','ExpType','Importance','kzt',
          'GustFact','Kd','WidthType','Angle','Story','Diaphragm','Width','Depth','X','Y')

rows_w = [
    {'Name':'WX','Exposure':'Diaphragms','TopStory':'Story4','BotStory':'Base',
     'Parapet':'No','UserCp':'No','ASCECase':'1','e1':'0.15','e2':'0.15',
     'WindSpeed':'80','ExpType':'B','Importance':'1','kzt':'1',
     'GustFact':'0.85','Kd':'0.85','Angle':'0'},
    {'Name':'WY','Exposure':'Diaphragms','TopStory':'Story4','BotStory':'Base',
     'Parapet':'No','UserCp':'No','ASCECase':'1','e1':'0.15','e2':'0.15',
     'WindSpeed':'80','ExpType':'B','Importance':'1','kzt':'1',
     'GustFact':'0.85','Kd':'0.85','Angle':'90'},
]
flat_w = tuple(r.get(f) for r in rows_w for f in WIND_F)
ret_s = model.DatabaseTables.SetTableForEditingArray(TABLE_W, 0, WIND_F, 2, flat_w)
ret_a = model.DatabaseTables.ApplyEditedTables(True)
# First write: "2 of 10 records" is OK — ETABS creates rows for each field value
# After write, check: model.LoadPatterns.GetAutoWindCode("WX") → ['ASCE 7-05', 0]
log = ret_a[4]
for line in log.split('\r\n'):
    if 'record' in line.lower() or 'Error' in line:
        print(line.strip())
```

### Verify
```python
print(model.LoadPatterns.GetAutoWindCode("WX"))  # ['ASCE 7-05', 0]
print(model.LoadPatterns.GetAutoWindCode("WY"))  # ['ASCE 7-05', 0]
```

---

## Load Combination Definitions — CRITICAL: hardcode fields

When the `'Load Combination Definitions'` table has no rows with LoadName (e.g. all combos empty),
the table returns only header fields `('Name', 'Type', 'IsAuto', 'GUID', 'Notes')` — LoadName and
SF are missing from the schema. **Always hardcode the full field tuple** to include LoadName and SF:

```python
USE_F = ('Name', 'Type', 'IsAuto', 'LoadName', 'SF', 'GUID', 'Notes')
# Write 197 rows for 61 combos — "197 of 197 records successfully read"
```

---

## Notes
- Fa/Fv are **identical for all zones** — only Ss/S1 differ by zone.
- SF values (Fa=2.1, Fv=2.625) are 1.5 × SE — minimum without site-specific study.
- I (importance factor) is NOT stored in the RS function; apply as scale factor = I × 9.81 in RS load case.
- TL = 4.0 s for all zones (BNBC 2020).
- **Auto seismic `IsAuto` field is read-only** — never include it in the write fields tuple; ETABS silently drops all records when it's present.
- **Auto wind**: `cAutoWind` sub-object exists (`model.LoadPatterns.AutoWind`) but has no discoverable Set methods in comtypes late-binding. Use DatabaseTables instead.
