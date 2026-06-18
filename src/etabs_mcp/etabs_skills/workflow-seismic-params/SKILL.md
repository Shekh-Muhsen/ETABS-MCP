# workflow-seismic-params

Extract seismic code parameters (Ss, S1, SDS, SD1, R, I, Cd, site class, period) for all auto-seismic load patterns.

## When to use
- Review seismic design parameters
- Verify code inputs before analysis
- Extract for design report

## Verified code

```python
# Extract seismic parameters via DatabaseTables
t = model.DatabaseTables.GetTableForDisplayArray(
    "Load Pattern Definitions - Auto Seismic - ASCE 7-05", [], "Mode", 0, [], 0, []
)
fields = list(t[2]); flat = list(t[4]); n = t[3]; nf = len(fields)
seismic = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n)]

# Filter to primary patterns only (IsAuto = "No")
primary = [r for r in seismic if r.get("IsAuto") == "No"]

result = {
    "all_patterns": len(seismic),
    "primary_patterns": len(primary),
    "params": [
        {
            "Name":       r.get("Name"),
            "Direction":  "X" if r.get("XDir")=="Yes" else "Y",
            "TopStory":   r.get("TopStory"),
            "BotStory":   r.get("BotStory"),
            "Ss":         r.get("Ss"),
            "S1":         r.get("S1"),
            "SDS":        r.get("SDS"),
            "SD1":        r.get("SD1"),
            "R":          r.get("R"),
            "I":          r.get("I"),
            "Cd":         r.get("Cd"),
            "Omega":      r.get("Omega"),
            "SiteClass":  r.get("SiteClass"),
            "Fa":         r.get("Fa"),
            "Fv":         r.get("Fv"),
            "PeriodType": r.get("PeriodType"),
            "Ct_x":       r.get("CtAndX"),
            "Ecc":        r.get("EccRatio"),
        }
        for r in primary
    ]
}
```

## Response spectrum parameters

```python
lc_names = list(model.LoadCases.GetNameList()[1])

rs_params = {}
for name in lc_names:
    type_code = model.LoadCases.GetTypeOAPI(name)[0]
    if type_code == 4:  # ResponseSpectrum — VERIFIED: 4 not 5
    # Confirmed type codes: 1=StaticLinear, 3=Modal(Ritz/Eigen), 4=ResponseSpectrum
        rs = model.LoadCases.ResponseSpectrum.GetLoads(name)
        # [n, (LoadNames,), (Funcs,), (SFs,), (CSys,), (Angles,), ret]
        if rs[0] > 0:
            rs_params[name] = {
                "function":     rs[2][0],
                "scale_factor": round(rs[3][0], 4),
                "csys":         rs[4][0],
            }

result = {"response_spectrum_cases": rs_params}
```

## Key fields returned by seismic table

| Field | Description |
|---|---|
| `Name` | Load pattern name (EX, EY, EXS…) |
| `Ss`, `S1` | Spectral accelerations at 0.2s and 1s |
| `SDS`, `SD1` | Design spectral accelerations |
| `R` | Response modification factor |
| `I` | Importance factor |
| `Cd` | Deflection amplification factor |
| `Omega` | Overstrength factor |
| `SiteClass` | A–F |
| `Fa`, `Fv` | Site coefficients |
| `PeriodType` | Approximate / Program Calculated |
| `TUsed` | Period used (after analysis) |
| `BaseShear` | Computed base shear (after analysis) |
