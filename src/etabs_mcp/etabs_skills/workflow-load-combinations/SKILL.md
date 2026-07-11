---
name: workflow-load-combinations
description: Generate standard ASCE 7-05 / BNBC 2020 load combinations in ETABS — full SLS gravity/wind/seismic and ULS gravity/wind/seismic combo library with role mapping (D, L, Lr, Ex, Ey, Wx, Wy, Sx, Sy, Ev) and ETABS RespCombo API.
---

# workflow-load-combinations

Creates the full ASCE 7-05 / BNBC 2020 load combination library in ETABS using `RespCombo.Add` and `RespCombo.SetCaseList`. Combos are grouped into SLS (gravity, wind, seismic ELF) and ULS (gravity, wind, seismic RS + ELF) categories. Uses role mapping so the abstract roles (D, L, Ex, …) link to the actual case names in your model.

## When to use
- First-time combo generation for a new model
- Rebuilding combos after case names change
- Adding a specific combo group (e.g. only ULS-Seismic RS)
- Auditing which ASCE 7-05 / BNBC 2020 combos are missing from the model

## Role mapping (edit to match your model)

| Role | Default name | What it represents |
|---|---|---|
| D | DL | Composite dead case (Dead + SuperDead) |
| L | LLA | Composite live case (all Live patterns) |
| Lr | LLR | Roof live load case |
| Ex | EX | Seismic ELF X-direction |
| Ey | EY | Seismic ELF Y-direction |
| Ev | Ev | Vertical seismic = 0.2·SDS × Dead |
| Wx | WX | Wind X-direction |
| Wy | WY | Wind Y-direction |
| Sx | Spec X | Response spectrum X (RS case) |
| Sy | Spec Y | Response spectrum Y (RS case) |

## Combo type codes (ETABS RespCombo.Add)

| Code | Type |
|---|---|
| 0 | Linear Add |
| 1 | Envelope |
| 2 | Absolute Add |
| 3 | SRSS |

## Full combo template library (ASCE 7-05 / BNBC 2020)

### SLS Gravity (ASD / service-level)
| Name | Expression |
|---|---|
| 1001-DL+LLA | D + L |
| 1002-DL+LLR | D + Lr |
| 1003-DL+0.75LLA+0.75LLR | D + 0.75L + 0.75Lr |

### SLS Wind
| Name | Expression |
|---|---|
| 1004…1007 | D ± Wx, D ± Wy |
| 1016…1019 | D + 0.75L + 0.75Lr ± 0.75Wx/Wy |
| 1028…1031 | 0.6D ± Wx, 0.6D ± Wy |

### SLS Seismic — ELF (BNBC 2020 §2.5.7, 100%+30% combos ±Ev)
| Name | Expression |
|---|---|
| 1008…1015 | (D±Ev) + 0.7(±Ex ± 0.3Ey), (D±Ev) + 0.7(±0.3Ex ± Ey) |
| 1020…1027 | (D±Ev) + 0.75L + 0.75Lr + 0.7·0.75(±Ex±0.3Ey), … |
| 1032…1039 | (D−Ev) + 0.7(±Ex ± 0.3Ey) — uplift-dominant |

### ULS Gravity (LRFD)
| Name | Expression |
|---|---|
| 2001-1.4DL | 1.4D |
| 2002-1.2DL+1.6LLA+0.5LLR | 1.2D + 1.6L + 0.5Lr |

### ULS Wind (ASCE 7-05 §2.3)
| Name | Expression |
|---|---|
| 2003…2006 | 1.2D + 1.6Lr ± 0.8Wx/Wy |
| 2007…2010 | 1.2D + L + 0.5Lr ± 1.6Wx/Wy |
| 2019…2022 | 0.9D ± 1.6Wx/Wy |

### ULS Seismic — RS cases (ASCE 7-05 §12.4 / ACI 318-19)
| Name | Expression |
|---|---|
| 2011…2018 | (1.2D+Ev) + L ± Sx ± 0.3Sy, … (8 combos) |
| 2023…2030 | (0.9D−Ev) ± Sx ± 0.3Sy, … (8 combos) |

### ULS Seismic — ELF cases (ASCE 7-05 §12.4)
| Name | Expression |
|---|---|
| 2031…2038 | (1.2D+Ev) + L ± Ex ± 0.3Ey, … (8 combos) |
| 2039…2046 | (0.9D−Ev) ± Ex ± 0.3Ey, … (8 combos) |

## Verified code

```python
# ── Role mapping — edit to match your model's case names ──────────────────
ROLES = {
    "D":  "DL",      "L":  "LLA",   "Lr": "LLR",
    "Ex": "EX",      "Ey": "EY",    "Ev": "Ev",
    "Wx": "WX",      "Wy": "WY",
    "Sx": "Spec X",  "Sy": "Spec Y",
}

# ── Combo templates ───────────────────────────────────────────────────────
# (group, name, type_code, [(role, sf), ...])
TEMPLATES = [
    # SLS-Gravity
    ("SLS-Gravity","1001-DL+LLA",                 0, [("D",1.0),("L",1.0)]),
    ("SLS-Gravity","1002-DL+LLR",                 0, [("D",1.0),("Lr",1.0)]),
    ("SLS-Gravity","1003-DL+0.75LLA+0.75LLR",    0, [("D",1.0),("L",0.75),("Lr",0.75)]),
    # SLS-Wind
    ("SLS-Wind","1004-DL+Wx",                     0, [("D",1.0),("Wx",1.0)]),
    ("SLS-Wind","1005-DL-Wx",                     0, [("D",1.0),("Wx",-1.0)]),
    ("SLS-Wind","1006-DL+Wy",                     0, [("D",1.0),("Wy",1.0)]),
    ("SLS-Wind","1007-DL-Wy",                     0, [("D",1.0),("Wy",-1.0)]),
    ("SLS-Wind","1016-DL+0.75LLA+0.75LLR+0.75Wx",0,[("D",1.0),("L",0.75),("Lr",0.75),("Wx",0.75)]),
    ("SLS-Wind","1017-DL+0.75LLA+0.75LLR-0.75Wx",0,[("D",1.0),("L",0.75),("Lr",0.75),("Wx",-0.75)]),
    ("SLS-Wind","1018-DL+0.75LLA+0.75LLR+0.75Wy",0,[("D",1.0),("L",0.75),("Lr",0.75),("Wy",0.75)]),
    ("SLS-Wind","1019-DL+0.75LLA+0.75LLR-0.75Wy",0,[("D",1.0),("L",0.75),("Lr",0.75),("Wy",-0.75)]),
    ("SLS-Wind","1028-0.6DL+Wx",                  0,[("D",0.6),("Wx",1.0)]),
    ("SLS-Wind","1029-0.6DL-Wx",                  0,[("D",0.6),("Wx",-1.0)]),
    ("SLS-Wind","1030-0.6DL+Wy",                  0,[("D",0.6),("Wy",1.0)]),
    ("SLS-Wind","1031-0.6DL-Wy",                  0,[("D",0.6),("Wy",-1.0)]),
    # SLS-Seismic ELF (BNBC 2020 §2.5.7, 0.7·E 100%+30%, ±Ev)
    ("SLS-Seismic","1008-1.0+Ev DL+0.70Ex+0.21Ey",0,[("D",1.0),("Ev",1.0),("Ex",0.70),("Ey",0.21)]),
    ("SLS-Seismic","1009-1.0+Ev DL-0.70Ex+0.21Ey",0,[("D",1.0),("Ev",1.0),("Ex",-0.70),("Ey",0.21)]),
    ("SLS-Seismic","1010-1.0+Ev DL+0.70Ex-0.21Ey",0,[("D",1.0),("Ev",1.0),("Ex",0.70),("Ey",-0.21)]),
    ("SLS-Seismic","1011-1.0+Ev DL-0.70Ex-0.21Ey",0,[("D",1.0),("Ev",1.0),("Ex",-0.70),("Ey",-0.21)]),
    ("SLS-Seismic","1012-1.0+Ev DL+0.21Ex+0.70Ey",0,[("D",1.0),("Ev",1.0),("Ex",0.21),("Ey",0.70)]),
    ("SLS-Seismic","1013-1.0+Ev DL-0.21Ex+0.70Ey",0,[("D",1.0),("Ev",1.0),("Ex",-0.21),("Ey",0.70)]),
    ("SLS-Seismic","1014-1.0+Ev DL+0.21Ex-0.70Ey",0,[("D",1.0),("Ev",1.0),("Ex",0.21),("Ey",-0.70)]),
    ("SLS-Seismic","1015-1.0+Ev DL-0.21Ex-0.70Ey",0,[("D",1.0),("Ev",1.0),("Ex",-0.21),("Ey",-0.70)]),
    ("SLS-Seismic","1020-1.0+Ev DL+0.75L+0.75Lr+0.525Ex+0.1575Ey",0,[("D",1.0),("Ev",1.0),("L",0.75),("Lr",0.75),("Ex",0.525),("Ey",0.1575)]),
    ("SLS-Seismic","1021-1.0+Ev DL+0.75L+0.75Lr+0.525Ex-0.1575Ey",0,[("D",1.0),("Ev",1.0),("L",0.75),("Lr",0.75),("Ex",0.525),("Ey",-0.1575)]),
    ("SLS-Seismic","1022-1.0+Ev DL+0.75L+0.75Lr-0.525Ex+0.1575Ey",0,[("D",1.0),("Ev",1.0),("L",0.75),("Lr",0.75),("Ex",-0.525),("Ey",0.1575)]),
    ("SLS-Seismic","1023-1.0+Ev DL+0.75L+0.75Lr-0.525Ex-0.1575Ey",0,[("D",1.0),("Ev",1.0),("L",0.75),("Lr",0.75),("Ex",-0.525),("Ey",-0.1575)]),
    ("SLS-Seismic","1024-1.0+Ev DL+0.75L+0.75Lr+0.1575Ex+0.525Ey",0,[("D",1.0),("Ev",1.0),("L",0.75),("Lr",0.75),("Ex",0.1575),("Ey",0.525)]),
    ("SLS-Seismic","1025-1.0+Ev DL+0.75L+0.75Lr+0.1575Ex-0.525Ey",0,[("D",1.0),("Ev",1.0),("L",0.75),("Lr",0.75),("Ex",0.1575),("Ey",-0.525)]),
    ("SLS-Seismic","1026-1.0+Ev DL+0.75L+0.75Lr-0.1575Ex+0.525Ey",0,[("D",1.0),("Ev",1.0),("L",0.75),("Lr",0.75),("Ex",-0.1575),("Ey",0.525)]),
    ("SLS-Seismic","1027-1.0+Ev DL+0.75L+0.75Lr-0.1575Ex-0.525Ey",0,[("D",1.0),("Ev",1.0),("L",0.75),("Lr",0.75),("Ex",-0.1575),("Ey",-0.525)]),
    ("SLS-Seismic","1032-1.0-Ev DL+0.70Ex+0.21Ey",0,[("D",1.0),("Ev",-1.0),("Ex",0.70),("Ey",0.21)]),
    ("SLS-Seismic","1033-1.0-Ev DL+0.70Ex-0.21Ey",0,[("D",1.0),("Ev",-1.0),("Ex",0.70),("Ey",-0.21)]),
    ("SLS-Seismic","1034-1.0-Ev DL-0.70Ex+0.21Ey",0,[("D",1.0),("Ev",-1.0),("Ex",-0.70),("Ey",0.21)]),
    ("SLS-Seismic","1035-1.0-Ev DL-0.70Ex-0.21Ey",0,[("D",1.0),("Ev",-1.0),("Ex",-0.70),("Ey",-0.21)]),
    ("SLS-Seismic","1036-1.0-Ev DL+0.21Ex+0.70Ey",0,[("D",1.0),("Ev",-1.0),("Ex",0.21),("Ey",0.70)]),
    ("SLS-Seismic","1037-1.0-Ev DL+0.21Ex-0.70Ey",0,[("D",1.0),("Ev",-1.0),("Ex",0.21),("Ey",-0.70)]),
    ("SLS-Seismic","1038-1.0-Ev DL-0.21Ex+0.70Ey",0,[("D",1.0),("Ev",-1.0),("Ex",-0.21),("Ey",0.70)]),
    ("SLS-Seismic","1039-1.0-Ev DL-0.21Ex-0.70Ey",0,[("D",1.0),("Ev",-1.0),("Ex",-0.21),("Ey",-0.70)]),
    # ULS-Gravity
    ("ULS-Gravity","2001-1.4DL",                   0,[("D",1.4)]),
    ("ULS-Gravity","2002-1.2DL+1.6LLA+0.5LLR",    0,[("D",1.2),("L",1.6),("Lr",0.5)]),
    # ULS-Wind
    ("ULS-Wind","2003-1.2DL+1.6LLR+0.8Wx",        0,[("D",1.2),("Lr",1.6),("Wx",0.8)]),
    ("ULS-Wind","2004-1.2DL+1.6LLR-0.8Wx",        0,[("D",1.2),("Lr",1.6),("Wx",-0.8)]),
    ("ULS-Wind","2005-1.2DL+1.6LLR+0.8Wy",        0,[("D",1.2),("Lr",1.6),("Wy",0.8)]),
    ("ULS-Wind","2006-1.2DL+1.6LLR-0.8Wy",        0,[("D",1.2),("Lr",1.6),("Wy",-0.8)]),
    ("ULS-Wind","2007-1.2DL+LLA+0.5LLR+1.6Wx",    0,[("D",1.2),("L",1.0),("Lr",0.5),("Wx",1.6)]),
    ("ULS-Wind","2008-1.2DL+LLA+0.5LLR-1.6Wx",    0,[("D",1.2),("L",1.0),("Lr",0.5),("Wx",-1.6)]),
    ("ULS-Wind","2009-1.2DL+LLA+0.5LLR+1.6Wy",    0,[("D",1.2),("L",1.0),("Lr",0.5),("Wy",1.6)]),
    ("ULS-Wind","2010-1.2DL+LLA+0.5LLR-1.6Wy",    0,[("D",1.2),("L",1.0),("Lr",0.5),("Wy",-1.6)]),
    ("ULS-Wind","2019-0.9DL+1.6Wx",                0,[("D",0.9),("Wx",1.6)]),
    ("ULS-Wind","2020-0.9DL-1.6Wx",                0,[("D",0.9),("Wx",-1.6)]),
    ("ULS-Wind","2021-0.9DL+1.6Wy",                0,[("D",0.9),("Wy",1.6)]),
    ("ULS-Wind","2022-0.9DL-1.6Wy",                0,[("D",0.9),("Wy",-1.6)]),
    # ULS-Seismic RS (ACI 318-19 / ASCE 7-05 §12.4, 100%+30%, ±Ev)
    ("ULS-Seismic","2011-1.2+Ev DL+LLA+Sx+0.3Sy", 0,[("D",1.2),("Ev",1.0),("L",1.0),("Sx",1.0),("Sy",0.3)]),
    ("ULS-Seismic","2012-1.2+Ev DL+LLA+Sx-0.3Sy", 0,[("D",1.2),("Ev",1.0),("L",1.0),("Sx",1.0),("Sy",-0.3)]),
    ("ULS-Seismic","2013-1.2+Ev DL+LLA-Sx+0.3Sy", 0,[("D",1.2),("Ev",1.0),("L",1.0),("Sx",-1.0),("Sy",0.3)]),
    ("ULS-Seismic","2014-1.2+Ev DL+LLA-Sx-0.3Sy", 0,[("D",1.2),("Ev",1.0),("L",1.0),("Sx",-1.0),("Sy",-0.3)]),
    ("ULS-Seismic","2015-1.2+Ev DL+LLA+0.3Sx+Sy", 0,[("D",1.2),("Ev",1.0),("L",1.0),("Sx",0.3),("Sy",1.0)]),
    ("ULS-Seismic","2016-1.2+Ev DL+LLA+0.3Sx-Sy", 0,[("D",1.2),("Ev",1.0),("L",1.0),("Sx",0.3),("Sy",-1.0)]),
    ("ULS-Seismic","2017-1.2+Ev DL+LLA-0.3Sx+Sy", 0,[("D",1.2),("Ev",1.0),("L",1.0),("Sx",-0.3),("Sy",1.0)]),
    ("ULS-Seismic","2018-1.2+Ev DL+LLA-0.3Sx-Sy", 0,[("D",1.2),("Ev",1.0),("L",1.0),("Sx",-0.3),("Sy",-1.0)]),
    ("ULS-Seismic","2023-0.9-Ev DL+Sx+0.3Sy",     0,[("D",0.9),("Ev",-1.0),("Sx",1.0),("Sy",0.3)]),
    ("ULS-Seismic","2024-0.9-Ev DL+Sx-0.3Sy",     0,[("D",0.9),("Ev",-1.0),("Sx",1.0),("Sy",-0.3)]),
    ("ULS-Seismic","2025-0.9-Ev DL-Sx+0.3Sy",     0,[("D",0.9),("Ev",-1.0),("Sx",-1.0),("Sy",0.3)]),
    ("ULS-Seismic","2026-0.9-Ev DL-Sx-0.3Sy",     0,[("D",0.9),("Ev",-1.0),("Sx",-1.0),("Sy",-0.3)]),
    ("ULS-Seismic","2027-0.9-Ev DL+0.3Sx+Sy",     0,[("D",0.9),("Ev",-1.0),("Sx",0.3),("Sy",1.0)]),
    ("ULS-Seismic","2028-0.9-Ev DL+0.3Sx-Sy",     0,[("D",0.9),("Ev",-1.0),("Sx",0.3),("Sy",-1.0)]),
    ("ULS-Seismic","2029-0.9-Ev DL-0.3Sx+Sy",     0,[("D",0.9),("Ev",-1.0),("Sx",-0.3),("Sy",1.0)]),
    ("ULS-Seismic","2030-0.9-Ev DL-0.3Sx-Sy",     0,[("D",0.9),("Ev",-1.0),("Sx",-0.3),("Sy",-1.0)]),
    # ULS-Seismic ELF (ASCE 7-05 §12.4, 100%+30%, ±Ev)
    ("ULS-Seismic","2031-1.2+Ev DL+LLA+Ex+0.3Ey", 0,[("D",1.2),("Ev",1.0),("L",1.0),("Ex",1.0),("Ey",0.3)]),
    ("ULS-Seismic","2032-1.2+Ev DL+LLA+Ex-0.3Ey", 0,[("D",1.2),("Ev",1.0),("L",1.0),("Ex",1.0),("Ey",-0.3)]),
    ("ULS-Seismic","2033-1.2+Ev DL+LLA-Ex+0.3Ey", 0,[("D",1.2),("Ev",1.0),("L",1.0),("Ex",-1.0),("Ey",0.3)]),
    ("ULS-Seismic","2034-1.2+Ev DL+LLA-Ex-0.3Ey", 0,[("D",1.2),("Ev",1.0),("L",1.0),("Ex",-1.0),("Ey",-0.3)]),
    ("ULS-Seismic","2035-1.2+Ev DL+LLA+0.3Ex+Ey", 0,[("D",1.2),("Ev",1.0),("L",1.0),("Ex",0.3),("Ey",1.0)]),
    ("ULS-Seismic","2036-1.2+Ev DL+LLA+0.3Ex-Ey", 0,[("D",1.2),("Ev",1.0),("L",1.0),("Ex",0.3),("Ey",-1.0)]),
    ("ULS-Seismic","2037-1.2+Ev DL+LLA-0.3Ex+Ey", 0,[("D",1.2),("Ev",1.0),("L",1.0),("Ex",-0.3),("Ey",1.0)]),
    ("ULS-Seismic","2038-1.2+Ev DL+LLA-0.3Ex-Ey", 0,[("D",1.2),("Ev",1.0),("L",1.0),("Ex",-0.3),("Ey",-1.0)]),
    ("ULS-Seismic","2039-0.9-Ev DL+Ex+0.3Ey",     0,[("D",0.9),("Ev",-1.0),("Ex",1.0),("Ey",0.3)]),
    ("ULS-Seismic","2040-0.9-Ev DL+Ex-0.3Ey",     0,[("D",0.9),("Ev",-1.0),("Ex",1.0),("Ey",-0.3)]),
    ("ULS-Seismic","2041-0.9-Ev DL-Ex+0.3Ey",     0,[("D",0.9),("Ev",-1.0),("Ex",-1.0),("Ey",0.3)]),
    ("ULS-Seismic","2042-0.9-Ev DL-Ex-0.3Ey",     0,[("D",0.9),("Ev",-1.0),("Ex",-1.0),("Ey",-0.3)]),
    ("ULS-Seismic","2043-0.9-Ev DL+0.3Ex+Ey",     0,[("D",0.9),("Ev",-1.0),("Ex",0.3),("Ey",1.0)]),
    ("ULS-Seismic","2044-0.9-Ev DL+0.3Ex-Ey",     0,[("D",0.9),("Ev",-1.0),("Ex",0.3),("Ey",-1.0)]),
    ("ULS-Seismic","2045-0.9-Ev DL-0.3Ex+Ey",     0,[("D",0.9),("Ev",-1.0),("Ex",-0.3),("Ey",1.0)]),
    ("ULS-Seismic","2046-0.9-Ev DL-0.3Ex-Ey",     0,[("D",0.9),("Ev",-1.0),("Ex",-0.3),("Ey",-1.0)]),
]

# ── Apply to ETABS ─────────────────────────────────────────────────────────
model.SetModelIsLocked(False)

# Existing combos
ex_cnt, ex_names = model.RespCombo.GetNameList()[0:2]
existing = set(list(ex_names))

# Existing cases (to detect if a role maps to a combo vs case)
_, case_names = model.LoadCases.GetNameList()[0:2]
_, combo_names = model.RespCombo.GetNameList()[0:2]
combo_set = set(list(combo_names))

created = []; skipped = []; missing_roles = []

# Resolve role → actual case name; check it exists
def resolve(role):
    name = ROLES.get(role, role)
    if name not in list(case_names) and name not in combo_set:
        missing_roles.append(f"{role}→{name}")
        return None
    return name

for group, combo_name, ctype, items in TEMPLATES:
    if combo_name in existing:
        skipped.append(combo_name)
        continue
    # Resolve all roles first
    resolved = [(resolve(r), sf) for r, sf in items]
    if any(n is None for n, _ in resolved):
        skipped.append(f"{combo_name} (missing role)")
        continue
    model.RespCombo.Add(combo_name, ctype)
    for case_or_combo, sf in resolved:
        is_combo = case_or_combo in combo_set
        item_type = 1 if is_combo else 0   # 0=LoadCase, 1=LoadCombo
        model.RespCombo.SetCaseList(combo_name, item_type, case_or_combo, sf)
    created.append(combo_name)

result = {
    "created":       len(created),
    "skipped":       len(skipped),
    "missing_roles": list(set(missing_roles)),
    "created_list":  created,
    "skipped_list":  skipped,
}
```

## Additional tasks — single combo or bulk case add

```python
# Read existing combo contents
combo_name = "2011-1.2+Ev DL+LLA+Sx+0.3Sy"
r = model.RespCombo.GetCaseList(combo_name)
n, types, names, sfs = r[0], list(r[1]), list(r[2]), list(r[3])
items = [{"name": names[i], "type": "Combo" if types[i]==1 else "Case", "sf": sfs[i]} for i in range(n)]

# Delete and recreate a combo
model.SetModelIsLocked(False)
model.RespCombo.Delete(combo_name)
model.RespCombo.Add(combo_name, 0)   # Linear Add
model.RespCombo.SetCaseList(combo_name, 0, "DL", 1.2)   # add DL case
model.RespCombo.SetCaseList(combo_name, 0, "Ev", 1.0)   # add Ev case

# Add a case to many combos at once
case_to_add = "NewCase"; sf_add = 1.0
_, all_combos = model.RespCombo.GetNameList()[0:2]
for c in list(all_combos):
    model.RespCombo.SetCaseList(c, 0, case_to_add, sf_add)
```

## Notes
- `RespCombo.Add(name, type)` — type: 0=Linear Add, 1=Envelope, 2=Absolute Add, 3=SRSS
- `RespCombo.SetCaseList(combo, itemType, caseName, sf)` — itemType: 0=LoadCase, 1=LoadCombo; call once per case/combo in the combination (it appends, not replaces)
- `RespCombo.GetCaseList(combo)` returns `[ret, n, types[], names[], sfs[]]` — iterate over `n` items
- Never modify the model while it is locked — call `model.SetModelIsLocked(False)` before adding or editing combos
- SLS seismic factors 0.70 and 0.30 = 0.7 × BNBC 2020 §2.5.7 "E" applied as 1.0E·0.7 orthogonal = 100% major + 30% minor (= 0.21)
- ULS seismic factors use the ASCE 7-05 §12.4.2 formula E_h = ρ·Q_E with ρ=1.0 and E_v included via separate Ev case
- Run `workflow-load-patterns-cases` first to ensure all required cases exist before generating combos
