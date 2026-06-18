---
name: ibc2012-seismic-params
description: "IBC 2012 / ASCE 7-05 seismic design parameters: Ss, S1, Fa, Fv, SDS, SD1, site class, R, I, Cd. For creating the load patterns in ETABS, use skill 'etabs-auto-seismic'."
---

# IBC 2012 / ASCE 7-05 Seismic Parameters

For creating load patterns in ETABS → read skill **`etabs-auto-seismic`**.

---

## Standard IBC 2012 Parameters (SEAOC SDM Vol.1 baseline)

```python
Ss   = 1.5    # MCE short-period spectral acceleration (g)
S1   = 0.6    # MCE 1-sec spectral acceleration (g)
Fa   = 1.0    # Site coefficient, Site Class D, ASCE 7-05 Table 11.4-1
Fv   = 1.5    # Site coefficient, Site Class D, ASCE 7-05 Table 11.4-2

SMS  = Fa * Ss             # = 1.50 g   (Eq 11.4-1)
SM1  = Fv * S1             # = 0.90 g   (Eq 11.4-2)
SDS  = (2/3) * SMS         # = 1.00 g   (Eq 11.4-3)
SD1  = (2/3) * SM1         # = 0.60 g   (Eq 11.4-4)
T0   = 0.2 * SD1 / SDS    # = 0.12 s
Ts   = SD1 / SDS           # = 0.60 s
TL   = 8.0                 # long-period transition (s)
```

## Site Coefficients — ASCE 7-05 Table 11.4-1 / 11.4-2

| Site Class | Fa (Ss=1.5) | Fv (S1=0.6) |
|---|---|---|
| A | 0.8 | 0.8 |
| B | 1.0 | 1.0 |
| C | 1.0 | 1.3 |
| D | 1.0 | 1.5 |
| E | 0.9 | 2.4 |

## Structural System Parameters — ASCE 7-05 Table 12.2-1

| System | R | Ω | Cd | Ct | x |
|---|---|---|---|---|---|
| Concrete SMF | 8 | 3 | 5.5 | 0.016 | 0.9 |
| Steel SMF | 8 | 3 | 5.5 | 0.028 | 0.8 |
| Steel IMF | 4.5 | 3 | 4.0 | 0.028 | 0.8 |
| Concrete SW (special) | 6 | 2.5 | 5.0 | 0.016 | 0.9 |
| Steel EBF | 8 | 2 | 4.0 | 0.03 | 0.75 |
| BRBF | 8 | 2.5 | 5.0 | 0.03 | 0.75 |

## Seismic Design Category — ASCE 7-05 Table 11.6-1 / 11.6-2

```python
# Risk Category II: SDS=1.0 >= 0.50 → SDC D
# Risk Category II: SD1=0.6 >= 0.20 → SDC D
SDC = "D"
```

## Importance Factor — ASCE 7-05 Table 11.5-1

| Risk Category | Ie |
|---|---|
| I, II | 1.0 |
| III | 1.25 |
| IV | 1.5 |

## Seismic Response Coefficient Cs — ASCE 7-05 §12.8.1

```python
R, Ie = 8.0, 1.0
T_ELF = 0.272    # min(T_ETABS, Cu*Ta)
TL = 8.0

Cs_eq2 = SDS / (R/Ie)                     # upper bound = 0.1250
Cs_eq3 = SD1 / (T_ELF * (R/Ie))           # upper, T<=TL = 0.2757
Cs_eq5 = max(0.044 * SDS * Ie, 0.01)      # lower min = 0.0440
Cs_eq6 = 0.5 * S1 / (R/Ie)               # S1>=0.6g lower = 0.0375

Cs = max(min(Cs_eq2, Cs_eq3), max(Cs_eq5, Cs_eq6))  # = 0.1250
```

## Load Combinations — ASCE 7-05 §12.4.2.3

```python
# Strength design with seismic
# U = (1.2 + 0.2*SDS)*D + rho*QE + L        [Combo 5]
# U = (0.9 - 0.2*SDS)*D + rho*QE            [Combo 7]
rho = 1.0   # or 1.3 for SDC D without condition §12.3.4
```
