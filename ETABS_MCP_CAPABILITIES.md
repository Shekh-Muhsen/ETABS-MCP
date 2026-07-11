# ETABS MCP Server — What You Can Ask & Extract

A reference guide for engineers using Claude + ETABS MCP to interrogate and control ETABS models.

---

## 1. MODEL INFORMATION

| Request | Example Prompt | Data Returned |
|---|---|---|
| Version & file | "What version of ETABS is running?" | Version string, build number, file path |
| Unit system | "What units is the model in?" | Unit code (kN_m, kip_ft, etc.) |
| Lock status | "Is the model locked?" | True/False |
| Story list | "List all stories with elevations" | Story names, heights, master story flags |
| Full audit | "Give me a model summary" | Stories, element counts, materials, sections |

```python
# Model summary
ver = model.GetVersion()          # ['23.2.0', 0.0, 0]
fname = model.GetModelFilename(True)
locked = model.GetModelIsLocked()
stories = model.Story.GetStories()  # [n, names, heights, ...]
n_frames = model.FrameObj.GetNameList()[0]
n_areas = model.AreaObj.GetNameList()[0]
n_points = model.PointObj.GetNameList()[0]
```

---

## 2. GEOMETRY

| Request | Example Prompt | Data Returned |
|---|---|---|
| All stories | "List all stories and their elevations" | Names, heights in model units |
| All groups | "What groups are defined?" | Group names |
| Group members | "What elements are in AllColumns?" | Object types + names |
| Frame list | "How many frames/beams/columns are there?" | Count, names |
| Area list | "List all slabs and walls" | Count, names |
| Point coordinates | "Get coordinates of joint 42" | X, Y, Z |
| Point restraints | "Is joint 1 fixed?" | 6 DOF booleans (F1–F3, M1–M3) |
| Frame endpoints | "What joints does frame 10 connect?" | Pt1 name, Pt2 name |
| Frame section | "What section is assigned to beam 5?" | Section name |

```python
# Get all group names
groups = model.GroupDef.GetNameList()   # [n, (names,), ret]
names = list(groups[1])

# Get members of a group
grp = model.GroupDef.GetAssignments("AllColumns")
# [n, (objTypes,), (objNames,), ret]  — objType: 1=Point, 2=Frame, 3=Area

# Point coordinates
coords = model.PointObj.GetCoordCartesian("42")  # [x, y, z, ret]

# Frame endpoint joints
pts = model.FrameObj.GetPoints("10")   # [pt1, pt2, ret]

# Point restraint
rest = model.PointObj.GetRestraint("1")  # [(F1,F2,F3,M1,M2,M3), ret]
```

---

## 3. MATERIALS

| Request | Example Prompt | Data Returned |
|---|---|---|
| Material list | "List all materials" | Names, count |
| Concrete strength | "What is fc for CON 4000 PSI?" | fc, lightweight flag, strain params |
| Steel strength | "What are Fy and Fu for A992?" | Fy, Fu, EFy, EFu, stress-strain params |
| Rebar properties | "Get rebar material properties" | Fy, Fu, strain params |
| Elastic modulus | "What is E and Poisson's ratio for Steel-A36?" | E, ν, α (thermal), G |
| Unit weight | "What is the density of concrete?" | Weight/volume, mass/volume |

```python
mats = model.PropMaterial.GetNameList()   # [n, (names,), ret]

# Concrete
conc = model.PropMaterial.GetOConcrete_1("CON 4000 PSI")
# [fc, isLightweight, fcsFactor, ssType, ssHysType, strainFc, strainUlt, strainFinal, slope, 0, ret]

# Steel
steel = model.PropMaterial.GetOSteel_1("A992Fy50")
# [Fy, Fu, EFy, EFu, ssType, ssHysType, strainHard, strainUlt, strainFinal, slope, ret]

# Elastic properties
iso = model.PropMaterial.GetMPIsotropic("A992Fy50")
# [E, nu(Poisson), alpha(thermal), G(shear), ret]

# Unit weight
wm = model.PropMaterial.GetWeightAndMass("A992Fy50")
# [weightPerVol, massPerVol, ret]
```

---

## 4. SECTIONS (Frame & Area)

| Request | Example Prompt | Data Returned |
|---|---|---|
| Frame sections | "List all frame sections" | Names, count |
| Rectangular column | "Get dimensions of C4-18X30" | Depth, width, material |
| Pipe/CHS section | "Get pipe dimensions for BRACING_Pipe" | Diameter, thickness, material |
| I-section | "Get steel beam dimensions" | D, bf, tf, tw, material |
| Area sections | "List slab and wall sections" | Names, count |
| Slab thickness | "How thick is the S-6 slab?" | Thickness, shell type, material |
| Frame modifiers | "What are the stiffness modifiers on frame 1?" | 8 modifier values |
| Area modifiers | "Get slab modifiers for AllDiaphragmSlabs" | 10 modifier values |

```python
# Frame sections
secs = model.PropFrame.GetNameList()   # [n, (names,), ret]

# Rectangle: [propName, matName, depth(t3), width(t2), color, notes, guid, ret]
rect = model.PropFrame.GetRectangle("C4-18X30")
depth_m, width_m = rect[2], rect[3]

# Pipe/CHS: [propName, matName, diameter, wallThickness, color, notes, guid, ret]
pipe = model.PropFrame.GetPipe("BRACING_Pipe-220X7.62")

# I-Section: [propName, matName, t3, t2, tf, tw, t2b, tfb, color, notes, guid, ret]
isec = model.PropFrame.GetISection("W14X48")

# Slab: [shellType, matType, matName, thickness, color, notes, guid, ret]
slab = model.PropArea.GetSlab("S-6")
thickness_m = slab[3]

# Frame stiffness modifiers: [(A,As2,As3,J,I22,I33,Mass,Weight), ret]
mods = model.FrameObj.GetModifiers("1")
i33_mod = mods[0][5]   # bending modifier about major axis

# Area modifiers (10 values): [(f11,f22,f12,m11,m22,m12,v13,v23,mass,weight), ret]
amods = model.AreaObj.GetModifiers("slab_1")
```

---

## 5. LOAD PATTERNS, CASES & COMBINATIONS

| Request | Example Prompt | Data Returned |
|---|---|---|
| Load patterns | "List all load patterns" | Names, count (60 in this model) |
| Pattern type | "What type is the Dead load pattern?" | Type code (1=Dead, 5=Quake, 6=Wind) |
| Self-weight | "What is the self-weight multiplier for Dead?" | Multiplier value |
| Load cases | "List all load cases" | Names, count (33 in this model) |
| Case type | "What type is the EX load case?" | Type code, auto flag |
| Static case loads | "What loads are in the Dead load case?" | Load names, types, scale factors |
| Response spectrum | "Get Spec X parameters" | Function, SF, direction |
| Seismic parameters | "Show EX auto seismic parameters" | Code, Ss, S1, R, I, SDS, SD1, site class |
| Load combos | "List all load combinations" | Names, count (79 in this model) |
| Combo contents | "What cases make up 2007-1.2DL+LL+0.5LLR+1.6WX?" | Case names + scale factors |

```python
# Load patterns
lp = model.LoadPatterns.GetNameList()   # [n, (names,), ret]

# Pattern type: [typeCode, ret] — 1=Dead, 2=SuperDead, 3=Live, 5=Quake, 6=Wind
lt = model.LoadPatterns.GetLoadType("EX")

# Self-weight multiplier: [mult, ret]
sw = model.LoadPatterns.GetSelfWtMultiplier("Dead")

# Case type: [typeCode, iAuto, ret] — 1=StaticLinear, 2=StaticNL, 3=Modal...
ct = model.LoadCases.GetTypeOAPI("Spec X")

# Static loads: [n, (types,), (names,), (SFs,), ret]
sl = model.LoadCases.StaticLinear.GetLoads("Dead")

# Response spectrum: [n, (LoadNames,), (Funcs,), (SFs,), (CSys,), (Angles,), ret]
rs = model.LoadCases.ResponseSpectrum.GetLoads("Spec X")
sf = rs[3][0]   # scale factor

# Combo contents: [n, (typeCodes,), (caseNames,), (SFs,), ret]
# typeCode: 0=LoadCase, 1=LoadCombo
combo = model.RespCombo.GetCaseList("2007-1.2DL+LL+0.5LLR+1.6WX")

# Seismic auto-load parameters via DatabaseTables:
table = model.DatabaseTables.GetTableForDisplayArray(
    "Load Pattern Definitions - Auto Seismic - ASCE 7-05", [], "Mode", 0, [], 0, []
)
fields = list(table[2]); flat = list(table[4]); n = table[3]; nf = len(fields)
rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n)]
# Gives: Name, Ss, S1, SDS, SD1, R, I, Omega, Cd, SiteClass, PeriodType, TopStory, BotStory ...
```

---

## 6. ANALYSIS

| Request | Example Prompt | Data Returned |
|---|---|---|
| Run analysis | "Run the analysis" | Return code (0=success). **Large models: run in ETABS UI (F5)** |
| Analysis status | "Has the model been analyzed?" | Lock state (True = analyzed) |
| Active DOF | "What degrees of freedom are active?" | 6 booleans (T1,T2,T3,R1,R2,R3) |
| Solver settings | "What solver is being used?" | Solver type, multithread flag |

```python
# Unlock, run, re-check
model.SetModelIsLocked(False)
ret = model.Analyze.RunAnalysis()   # 0 = success
# NOTE: Large models (>1000 elements) will timeout via MCP — run in ETABS UI instead

locked = model.GetModelIsLocked()   # True after successful analysis

# Active DOF: [(T1,T2,T3,R1,R2,R3), ret]
dof = model.Analyze.GetActiveDOF()

# Solver: [SolverType, MultiThread, Force32Bit, StiffCase, ret]
solver = model.Analyze.GetSolverOption_1()
```

---

## 7. RESULTS (requires analysis to be run first)

| Request | Example Prompt | Data Returned |
|---|---|---|
| Base shear | "What is the base shear for EX and EY?" | FX, FY, FZ, MX, MY, MZ per case |
| Story drifts | "Show story drifts for all seismic cases" | Story, case, direction, drift ratio |
| Modal periods | "What are the first 6 modal periods?" | Period (s), frequency (Hz) |
| Mass participation | "Show modal mass participation ratios" | UX, UY, UZ, RX, RY, RZ per mode |
| Joint displacements | "Get displacements at joint 42 for Dead" | U1, U2, U3, R1, R2, R3 |
| Joint reactions | "Get base reactions at support joints" | F1, F2, F3, M1, M2, M3 |
| Frame forces | "Get moment and shear in beam 10 for 2002-1.2DL+1.6LL" | P, V2, V3, T, M2, M3 at each station |
| Pier forces | "Get pier forces for all seismic combos" | P, V2, V3, T, M2, M3 per pier |
| Spandrel forces | "Get spandrel forces" | P, V2, V3, T, M2, M3 per spandrel |
| Area stresses | "Get slab stresses for Dead+Live" | S11, S22, S12, Smax, Smin, SVM |
| Any table | "Extract the Story Forces table" | All fields from DatabaseTables |

```python
# Setup — always do this first
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
model.Results.Setup.SetCaseSelectedForOutput("EX")
# or: model.Results.Setup.SetComboSelectedForOutput("ENV-ULS")

# Base reactions: [n, LoadCase, StepType, StepNum, FX, FY, FZ, MX, MY, MZ, gX, gY, gZ, ret]
base = model.Results.BaseReact()
for i in range(base[0]):
    print(base[1][i], base[4][i], base[5][i])   # case, FX, FY

# Story drifts: [n, Story, LoadCase, StepType, StepNum, Direction, Drift, Label, X, Y, ret]
drifts = model.Results.StoryDrifts()

# Modal periods: [n, LoadCase, StepType, StepNum, Period, Freq, CircFreq, EigenVal, ret]
modal = model.Results.ModalPeriod()
periods = [modal[4][i] for i in range(modal[0])]

# Mass participation: [n, Case, StepType, StepNum, Period, UX,UY,UZ,SumUX,SumUY,SumUZ,RX,RY,RZ,SumRX,SumRY,SumRZ, ret]
mass = model.Results.ModalParticipatingMassRatios()

# Joint displacements: [n, ObjName, ElmName, Case, StepType, StepNum, U1,U2,U3,R1,R2,R3, ret]
disp = model.Results.JointDispl("42", 0)

# Joint reactions: [n, ObjName, ElmName, Case, StepType, StepNum, F1,F2,F3,M1,M2,M3, ret]
react = model.Results.JointReact("1", 0)

# Frame forces: [n, ObjName, ElmName, PointElm, Case, StepType, StepNum, P,V2,V3,T,M2,M3, ret]
forces = model.Results.FrameForce("10", 0)

# Pier forces: [n, Story, PierName, Case, StepType, StepNum, Loc, P,V2,V3,T,M2,M3, ret]
pier = model.Results.PierForce()

# Spandrel forces
span = model.Results.SpandrelForce()

# DatabaseTables — bulk extraction (preferred for large datasets)
table = model.DatabaseTables.GetTableForDisplayArray(
    "Story Forces", [], "Mode", 0, [], 0, []
)
fields = list(table[2]); flat = list(table[4]); n = table[3]; nf = len(fields)
rows = [{fields[j]: flat[i*nf+j] for j in range(nf)} for i in range(n)]
```

---

## 8. DESIGN

| Request | Example Prompt | Data Returned |
|---|---|---|
| Design code | "What concrete design code is set?" | Code string (e.g. "ACI 318-08") |
| Set code | "Set concrete design code to ACI 318-19" | Confirmation |
| Run design | "Run concrete frame design" | Completion status |
| Verify design | "Did all concrete frames pass design?" | Pass/fail flag |
| Beam summary | "Get design summary for beam 10" | Ratio, combo, location, rebar |
| Column summary | "Get design results for column 5" | Design type, combo, error/warning |
| Steel summary | "Get steel design ratio for frame 20" | Ratio, ratio type, combo, location |
| Design tables | "Extract concrete design results table" | All fields from DatabaseTables |

```python
# Concrete design
conc_code = model.DesignConcrete.GetCode()   # ['ACI 318-08', ret]
model.DesignConcrete.SetCode("ACI 318-14")
model.DesignConcrete.StartDesign()
all_ok = model.DesignConcrete.VerifyAllPassed()

# Beam results: [n, Name, Location, RLLF, TopRatioTot, BotRatioTot, ..., ErrMsg, WarnMsg, ret]
beam = model.DesignConcrete.GetSummaryResultsBeam("beam_name")

# Column results: [n, Name, MyCombo, DesignType, DesignPTOpt, ErrMsg, WarnMsg, ret]
col = model.DesignConcrete.GetSummaryResultsColumn("col_name")

# Steel design
steel_code = model.DesignSteel.GetCode()   # ['AISC 360-05', ret]
model.DesignSteel.SetCode("AISC 360-16")
model.DesignSteel.StartDesign()

# Steel results: [n, Name, Ratio, RatioType, Location, ComboName, ErrMsg, WarnMsg, ret]
sf = model.DesignSteel.GetSummaryResultsFrame("frame_name")

# Via DatabaseTables (for bulk results):
table = model.DatabaseTables.GetTableForDisplayArray(
    "Concrete Frame Design Load Combination Data", [], "Mode", 0, [], 0, []
)
```

---

## 9. MODIFYING THE MODEL

| Request | Example Prompt | Data Returned |
|---|---|---|
| Set modifiers | "Set beam I33 modifier to 0.35 for AllBeams" | Confirmation |
| Scale spectrum | "Scale Spec X by factor 1.25" | Confirmation |
| Unlock model | "Unlock the model for editing" | Confirmation |
| Add load | "Add 5 kN/m uniform load on frame 10 for LL" | Confirmation |
| Set units | "Switch to kN_m units" | Confirmation |

```python
# Frame modifiers — [A, As2, As3, J, I22, I33, Mass, Weight]
mods = [1.0, 1.0, 1.0, 1.0, 0.35, 0.35, 1.0, 1.0]
model.FrameObj.SetModifiers("AllBeams", mods, 1)   # itemType=1 → Group

# Area modifiers — [f11, f22, f12, m11, m22, m12, v13, v23, mass, weight]
amods = [0.25]*6 + [1.0, 1.0, 1.0, 1.0]
model.AreaObj.SetModifiers("AllDiaphragmSlabs", amods, 1)

# Scale response spectrum SF
rs = model.LoadCases.ResponseSpectrum.GetLoads("Spec X")
n, names, funcs, sfs, csys, angles = rs[0], rs[1], rs[2], rs[3], rs[4], rs[5]
new_sfs = [sf * 1.25 for sf in sfs]
model.LoadCases.ResponseSpectrum.SetLoads("Spec X", n, names, funcs, new_sfs, angles, csys)

# Uniform frame load
model.FrameObj.SetLoadDistributed("10", "LL", 1, 6, 0.0, 1.0, 5.0, 5.0, "Global", True, True, 0)
# (name, pattern, myType=1:Force, dir=6:Gravity, dist1, dist2, val1, val2, csys, relDist, replace, itemType)

# Unlock
model.SetModelIsLocked(False)
```

---

## 10. DATABASE TABLES (Universal Extractor)

142 tables are available. Key ones:

| Table Name | Contents |
|---|---|
| `Story Forces` | Shear, moment, torsion at each story |
| `Story Drifts` | Drift ratios per story and case |
| `Load Pattern Definitions - Auto Seismic - ASCE 7-05` | Full seismic parameters |
| `Load Pattern Definitions - Auto Notional Loads` | Notional load parameters |
| `Frame Section Property Definitions - Concrete Rectangular` | Column/beam dimensions |
| `Area Section Property Definitions - Slab` | Slab thickness, shell type |
| `Material Properties - Concrete` | fc, modulus, density |
| `Material Properties - Steel` | Fy, Fu, modulus |
| `Concrete Frame Design Preferences - ACI 318-08` | Design preference settings |
| `Concrete Frame Design Load Combination Data` | Design combos per member |
| `Analysis Options - SAPFire Options` | Solver settings |

```python
# Universal pattern — works for ANY table
def get_table(model, table_name):
    t = model.DatabaseTables.GetTableForDisplayArray(table_name, [], "Mode", 0, [], 0, [])
    fields = list(t[2])
    n, nf = t[3], len(fields)
    flat = list(t[4])
    return [
        {fields[j]: flat[i*nf+j] for j in range(nf)}
        for i in range(n)
    ]

rows = get_table(model, "Story Forces")

# List all available tables
all_tables = model.DatabaseTables.GetAvailableTables()
table_names = list(all_tables[1])   # 142 tables
```

---

## 11. TYPICAL WORKFLOW EXAMPLES

### Seismic Scaling Workflow
```python
# 1. Get static base shear
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
model.Results.Setup.SetCaseSelectedForOutput("EX")
V_EX = max(abs(v) for v in model.Results.BaseReact()[4])

model.Results.Setup.DeselectAllCasesAndCombosForOutput()
model.Results.Setup.SetCaseSelectedForOutput("Spec X")
V_SX = max(abs(v) for v in model.Results.BaseReact()[4])

# 2. Compute scale factor
Sx = (0.85 * V_EX) / V_SX

# 3. Apply to spectrum
rs = model.LoadCases.ResponseSpectrum.GetLoads("Spec X")
new_sfs = [sf * Sx for sf in rs[3]]
model.SetModelIsLocked(False)
model.LoadCases.ResponseSpectrum.SetLoads("Spec X", rs[0], rs[1], rs[2], new_sfs, rs[4], rs[5])
```

### Apply ACI Cracked Section Modifiers
```python
model.SetModelIsLocked(False)

# Columns: I22=0.70, I33=0.70
model.FrameObj.SetModifiers("AllColumns",    [1,1,1,1,0.70,0.70,1,1], 1)
# Beams: I33=0.35
model.FrameObj.SetModifiers("AllBeams",      [1,1,1,0.05,0.35,0.35,1,1], 1)
# Slabs: f11=f22=f12=m11=m22=m12=0.25
model.AreaObj.SetModifiers("AllDiaphragmSlabs", [0.25]*6+[1,1,1,1], 1)
# Walls: 0.35 in-plane
model.AreaObj.SetModifiers("AllWalls",          [0.35]*6+[1,1,1,1], 1)
```

### Extract Story Drift Report
```python
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
for case in ["EX", "EY", "Spec X", "Spec Y"]:
    model.Results.Setup.SetCaseSelectedForOutput(case)

drifts = model.Results.StoryDrifts()
n = drifts[0]
report = [
    {"story": drifts[1][i], "case": drifts[2][i],
     "dir": drifts[5][i], "drift": round(drifts[6][i]*1000, 4)}
    for i in range(n)
]
result = sorted(report, key=lambda r: r["drift"], reverse=True)[:20]
```

---

## LIMITATIONS

| Limitation | Workaround |
|---|---|
| `RunAnalysis()` times out for large models | Run in ETABS UI: **Analyze → Run Analysis (F5)** |
| No `import` in sandbox | `json`, `math` available; use built-in Python only |
| `dir()`, `type()`, `hasattr()` blocked | Use `str()` to inspect return values |
| File write requires `output_data_path` param | Pass path to `execute_code` to export CSV/XLSX |
| Results require analysis first | Check `model.GetModelIsLocked()` == True |
| `GetRunCaseFlag` takes integer index, not name | Use DatabaseTables to check case run status |
