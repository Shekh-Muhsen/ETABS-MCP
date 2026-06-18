---
name: etabs-materials
description: "Use when defining or querying material properties: concrete, steel, rebar, tendon, aluminum, and cold-formed materials. Covers AddMaterial, SetMPIsotropic, SetOConcrete_1, SetOSteel_1, weight/mass, and GetNameList."
---

# ETABS Materials (`model.PropMaterial`)

Read `etabs-core` first for sandbox rules and return value conventions.

---

## Material Types

| Integer | Name | Typical Use |
|---------|------|-------------|
| 1 | Steel | Structural steel shapes |
| 2 | Concrete | RC beams, columns, slabs |
| 3 | NoDesign | Generic / other |
| 4 | Aluminum | Aluminum sections |
| 5 | ColdFormed | Cold-formed steel |
| 6 | Rebar | Reinforcing bar |
| 7 | Tendon | Post-tensioned tendon |

---

## List All Materials

```python
# GetNameList() → [count, (names_tuple), ret]
t = model.PropMaterial.GetNameList()
n = t[0]
names = list(t[1]) if n > 0 else []
result = names
```

---

## Add a Material (Basic)

`SetMaterial` creates the material entry with its type. Always follow with property setters.

```python
ret = model.SetPresentUnits(6)  # kN_m

# SetMaterial(Name, MatType, Color=-1, Notes="", GUID="") → ret
ret = model.PropMaterial.SetMaterial("A992Fy50", 1)   # Steel
ret = model.PropMaterial.SetMaterial("C30", 2)         # Concrete
ret = model.PropMaterial.SetMaterial("C25", 2)
ret = model.PropMaterial.SetMaterial("HRB400", 6)      # Rebar
```

## Add via AddMaterial (with region/standard/grade)

```python
# AddMaterial(Name, MatType, Region, Standard, Grade, Notes="", GUID="") → ret
# Region, Standard, Grade strings vary by code library (e.g. "China", "GB", "HRB400")
ret = model.PropMaterial.AddMaterial("Grade60", 6, "United States", "ASTM", "A615Gr60")
```

---

## Set Isotropic Properties (E, Poisson, Thermal)

```python
# SetMPIsotropic(Name, E, U, A, TempDep=False) → ret
# E = modulus of elasticity (in current length²·force units)
# U = Poisson's ratio
# A = thermal expansion coefficient (1/°C or 1/°F)

# --- kN_m units ---
# Steel A992 (E = 200 GPa = 200e6 kN/m²)
ret = model.PropMaterial.SetMPIsotropic("A992Fy50", 200000000.0, 0.3, 1.17e-5)

# Concrete C30 (E = 30 GPa = 30e6 kN/m²)
ret = model.PropMaterial.SetMPIsotropic("C30", 30000000.0, 0.2, 9.9e-6)

# Concrete C25 (E ≈ 28 GPa)
ret = model.PropMaterial.SetMPIsotropic("C25", 28000000.0, 0.2, 9.9e-6)

# Rebar (E = 200 GPa)
ret = model.PropMaterial.SetMPIsotropic("HRB400", 200000000.0, 0.3, 1.17e-5)
```

### Get Isotropic Properties

```python
# GetMPIsotropic(Name) → [E, nu, alpha, G, ret]
# E=modulus, nu=Poisson, alpha=thermal expansion, G=shear modulus
t = model.PropMaterial.GetMPIsotropic("C30")
E = t[0]
nu = t[1]
alpha = t[2]
G = t[3]
print("E =", E, "nu =", nu, "alpha =", alpha, "G =", G)
```

---

## Set Weight and Mass

```python
# SetWeightAndMass(Name, MyType, Value) → ret
# VERIFIED SIGNATURE — 3 args not 4
# MyType: 1 = UnitWeight (force/volume), 2 = UnitMass (mass/volume)

# Steel unit weight = 78.5 kN/m³ in kN_m
ret = model.PropMaterial.SetWeightAndMass("A992Fy50", 1, 78.5)   # MyType=1=UnitWeight

# Concrete unit weight = 25 kN/m³
ret = model.PropMaterial.SetWeightAndMass("C30", 1, 25.0)

# Set by mass density instead (kg/m³ × g → kN·s²/m⁴ in kN_m):
ret = model.PropMaterial.SetWeightAndMass("C30", 2, 2549.0)  # MyType=2=UnitMass
# Note: GetWeightAndMass will return mass = weight/g (auto-calculated)
```

---

## Set Steel Nonlinear Properties

```python
# SetOSteel_1(Name, Fy, Fu, EFy, EFu, SSType, SSHysType,
#             StrainAtHardening, StrainUltimate, FinalSlope) → ret
#
# Fy = yield stress, Fu = ultimate stress (in current stress units = kN/m²)
# SSType: 1=UserDefined, 2=Parametric
# SSHysType: 1=Elastic, 2=Kinematic, 3=Takeda, 4=Pivot, 5=Concrete, 6=BRB, 7=Trilinear
# StrainAtHardening, StrainUltimate: unitless strain values
# FinalSlope: post-ultimate slope (negative = descending)

# A992 Grade 50 steel (kN_m units)
# Fy = 50 ksi = 344 738 kN/m², Fu = 65 ksi = 448 159 kN/m²
ret = model.PropMaterial.SetOSteel_1(
    "A992Fy50",
    344738.0,   # Fy
    448159.0,   # Fu
    0.0,        # EFy (not used for parametric)
    0.0,        # EFu
    2,          # SSType = Parametric
    1,          # SSHysType = Elastic
    0.02,       # strain at hardening
    0.2,        # ultimate strain
    -0.1,       # final slope
)

# Get steel properties
# GetOSteel_1(Name) → [Fy, Fu, EFy, EFu, ssType, ssHysType, strainHard, strainUlt, strainFinal, finalSlope, ret]
t = model.PropMaterial.GetOSteel_1("A992Fy50")
Fy = t[0]
Fu = t[1]
print("Fy:", Fy, "Fu:", Fu)
```

---

## Set Concrete Nonlinear Properties

```python
# SetOConcrete_1(Name, Fc, IsLightweight, FcsFactor, SSType, SSHysType,
#               StrainAtFc, StrainUltimate, FinalSlope) → ret
#
# Fc = compressive strength (in current stress units = kN/m² for kN_m)
# IsLightweight: True/False
# FcsFactor: lightweight shear factor (0.0 if not lightweight)
# SSType: 1=UserDefined, 2=Parametric, 3=Mander
# SSHysType: 1=Elastic, 2=Takeda, 5=Concrete (most common for RC)
# StrainAtFc: strain at peak stress (typically 0.003)
# StrainUltimate: ultimate crushing strain (typically 0.005)
# FinalSlope: post-peak slope (negative)

# C30 (30 MPa = 30 000 kN/m²)
ret = model.PropMaterial.SetOConcrete_1(
    "C30",
    30000.0,    # Fc = 30 MPa
    False,
    0.0,
    2,          # Parametric
    1,          # Elastic
    0.003,
    0.005,
    -0.1,
)

# C25 (25 MPa)
ret = model.PropMaterial.SetOConcrete_1(
    "C25",
    25000.0,
    False,
    0.0,
    2,
    1,
    0.003,
    0.005,
    -0.1,
)

# Get concrete properties
# GetOConcrete_1(Name) → [fc, isLight, fcsFactor, ssType, ssHysType, strainFc, strainUlt, strainFinal, finalSlope, 0, ret]
t = model.PropMaterial.GetOConcrete_1("C30")
Fc = t[0]
is_lw = t[1]
print("Fc:", Fc, "Lightweight:", is_lw)
```

---

## Complete Material Setup (kN_m, SI Practice)

```python
ret = model.SetModelIsLocked(False)
ret = model.SetPresentUnits(6)  # kN_m

# --- Concrete C30 ---
ret = model.PropMaterial.SetMaterial("C30", 2)
ret = model.PropMaterial.SetMPIsotropic("C30", 30000000.0, 0.2, 9.9e-6)
ret = model.PropMaterial.SetOConcrete_1("C30", 30000.0, False, 0.0, 2, 1, 0.003, 0.005, -0.1)
ret = model.PropMaterial.SetWeightAndMass("C30", 1, 25.0)

# --- Concrete C25 ---
ret = model.PropMaterial.SetMaterial("C25", 2)
ret = model.PropMaterial.SetMPIsotropic("C25", 28000000.0, 0.2, 9.9e-6)
ret = model.PropMaterial.SetOConcrete_1("C25", 25000.0, False, 0.0, 2, 1, 0.003, 0.005, -0.1)
ret = model.PropMaterial.SetWeightAndMass("C25", 1, 25.0)

# --- Steel A992 ---
ret = model.PropMaterial.SetMaterial("A992Fy50", 1)
ret = model.PropMaterial.SetMPIsotropic("A992Fy50", 200000000.0, 0.3, 1.17e-5)
ret = model.PropMaterial.SetOSteel_1("A992Fy50", 344738.0, 448159.0, 0.0, 0.0, 2, 1, 0.02, 0.2, -0.1)
ret = model.PropMaterial.SetWeightAndMass("A992Fy50", 1, 78.5)

# --- Rebar HRB400 ---
ret = model.PropMaterial.SetMaterial("HRB400", 6)
ret = model.PropMaterial.SetMPIsotropic("HRB400", 200000000.0, 0.3, 1.17e-5)
# Fy = 400 MPa = 400 000 kN/m², Fu = 540 MPa = 540 000 kN/m²
ret = model.PropMaterial.SetOSteel_1("HRB400", 400000.0, 540000.0, 0.0, 0.0, 2, 1, 0.01, 0.1, -0.1)

t = model.PropMaterial.GetNameList()
result = {"materials_defined": list(t[1])}
```

---

## Unit Conversion Reference

| Quantity | kN_m value | Notes |
|----------|-----------|-------|
| E_steel | 200 000 000 kN/m² | 200 GPa |
| E_concrete (C30) | 30 000 000 kN/m² | 30 GPa |
| E_concrete (C25) | 28 000 000 kN/m² | 28 GPa |
| Fy steel (50 ksi) | 344 738 kN/m² | A992 |
| Fu steel (65 ksi) | 448 159 kN/m² | A992 |
| Fc concrete (30 MPa) | 30 000 kN/m² | C30 |
| Fc concrete (25 MPa) | 25 000 kN/m² | C25 |
| Unit weight steel | 78.5 kN/m³ | — |
| Unit weight concrete | 25.0 kN/m³ | — |
| 1 ksi | 6 894.76 kN/m² | — |
| 1 MPa | 1 000 kN/m² | — |
