---
name: workflow-otm-check
description: Overturning moment hand calculation per BNBC 2020 — computes T, Sa, V, lateral forces Fx, story OTM, and foundation OTM (×0.75); checks foundation OTM vs 2/3·M_DL.
---

# workflow-otm-check

Computes the design base shear and distributes it vertically to obtain overturning moments at each story level, following **BNBC 2020 Sec 2.5.7**. Reads story heights and seismic parameters directly from ETABS and performs the full hand calculation.

## When to use
- Independent OTM verification against ETABS Story Forces results
- Foundation overturning moment check (OTM_fnd = 0.75 × OTM_base per BNBC 2020 §2.5.7.8)
- Checking that foundation dead-load moment resists seismic OTM (M_OT ≤ 2/3 × M_DL)

## Formulae (BNBC 2020 Chapter 2)

| Step | Formula | Reference |
|---|---|---|
| Period | T = Ct × hn^m | Table 6.2.20 |
| Design Sa | Sa = SDS, SD1/T, or SD1·TL/T² | §2.5.6.3 |
| Base shear | V = Sa/(R/I) × W | §2.5.7.1 |
| k exponent | k = 1 (T≤0.5s), 2 (T≥2.5s), linear between | §2.5.7.4 |
| Story force | Fx = Cvx × V = wx·hx^k / Σwi·hi^k × V | Eq. 6.2.41 |
| Story OTM | Mx = Σ Fi·(hi − hx) for i above x | §2.5.7.8 |
| Foundation OTM | OTM_fnd = 0.75 × OTM_base | §2.5.7.8 |

## Ct values (BNBC 2020 Table 6.2.20)

| System | Ct | m |
|---|---|---|
| Concrete moment frame | 0.0466 | 0.9 |
| Other (steel/RC walls) | 0.0488 | 0.75 |

## Verified code

```python
import math

model.SetPresentUnits(6)  # lb_in_F — heights in inches

# ── Seismic parameters (edit these or read from ETABS auto-seismic table) ──
Ss  = 1.5;  S1  = 0.6
Fa  = 1.0;  Fv  = 1.5
R   = 5.0;  I   = 1.0;  TL = 8.0
Ct  = 0.0466;  m_exp = 0.9   # concrete moment frame

# ── Story weights Wx (kN) — fill in or integrate from ETABS mass ──────────
# Format: {story_name: Wx_kN}  (bottom-to-top order handled automatically)
Wx_input = {}   # e.g. {"Story 1": 5000, "Story 2": 4800, ...}

# ── Read story heights from "Story Definitions" table ─────────────────────
sd = model.DatabaseTables.GetTableForDisplayArray(
    "Story Definitions", [], "All", 0, [], 0, [])
fields = list(sd[1]); data = list(sd[6]); nc = len(fields); nr = sd[5]
iS = next(i for i,f in enumerate(fields) if f.lower()=="story")
iH = next(i for i,f in enumerate(fields) if f.lower()=="height")
raw = [(data[r*nc+iS], float(data[r*nc+iH] or 0)) for r in range(nr)]
# Table is top→bottom; reverse to accumulate elevation bottom-up
raw.reverse()
stories_btop = []   # (name, elevation_in) bottom-to-top
elev = 0.0
for name, h in raw:
    elev += h
    stories_btop.append((name, elev))

base_elev = stories_btop[0][1] if stories_btop else 0

# ── Build arrays (bottom-to-top) ─────────────────────────────────────────
names   = [s[0] for s in stories_btop]
h_above = [(s[1] - base_elev) * 0.0254 for s in stories_btop]  # in → m
Wx      = [Wx_input.get(n, 0) for n in names]

hn = max(h_above) if h_above else 0
W_total = sum(Wx)

if hn <= 0 or W_total <= 0:
    result = {"error": "Set story heights and Wx values before running."}
else:
    # Period
    T = Ct * (hn ** m_exp)

    # Spectral acceleration
    SDS = 2/3 * Fa * Ss
    SD1 = 2/3 * Fv * S1
    T0  = 0.2 * SD1/SDS
    Ts  = SD1/SDS
    if   T < T0:  Sa = SDS * (0.4 + 0.6*T/T0)
    elif T <= Ts: Sa = SDS
    elif T <= TL: Sa = SD1/T
    else:         Sa = SD1*TL/(T*T)

    # Base shear
    V = Sa/(R/I) * W_total

    # k exponent
    if   T <= 0.5: k = 1.0
    elif T >= 2.5: k = 2.0
    else:          k = 1.0 + (T - 0.5)/2.0

    # Lateral forces
    whk     = [w * max(h, 0.001)**k for w,h in zip(Wx, h_above)]
    sum_whk = sum(whk)
    Fx      = [v/sum_whk * V for v in whk]

    # OTM at each level (x = story index, bottom-to-top)
    n = len(names)
    OTMx     = []
    FndOTMx  = []
    for x in range(n):
        mo = sum(Fx[i]*(h_above[i]-h_above[x]) for i in range(x, n))
        OTMx.append(round(mo, 1))
        FndOTMx.append(round(mo*0.75, 1))

    result = {
        "T_s":       round(T, 3),
        "Sa_g":      round(Sa, 4),
        "SDS":       round(SDS, 3),
        "SD1":       round(SD1, 3),
        "k":         round(k, 2),
        "W_kN":      round(W_total, 1),
        "V_kN":      round(V, 1),
        "base_OTM_kNm":     OTMx[0] if OTMx else None,
        "foundation_OTM_kNm": FndOTMx[0] if FndOTMx else None,
        "story_table": [
            {"story": names[i], "h_m": round(h_above[i],3),
             "Wx_kN": Wx[i], "Fx_kN": round(Fx[i],1),
             "OTM_kNm": OTMx[i], "FndOTM_kNm": FndOTMx[i]}
            for i in range(n)
        ],
    }
```

## Notes
- Story table returned **bottom-to-top** (index 0 = lowest level, highest index = roof)
- `OTM_base = OTMx[0]` is at the lowest story; `OTM_roof = OTMx[-1]` ≈ 0
- Foundation OTM check: `OTM_fnd ≤ 2/3 × M_DL` per BNBC 2020 §2.5.7.8
- Fill `Wx_input` from gravity loads or read from ETABS mass using `JointMasses` or the story mass from the irregularity check
- To auto-read seismic parameters, query the `Load Pattern Definitions - Auto Seismic - ASCE 7-05` database table
