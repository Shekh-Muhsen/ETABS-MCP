---
name: etabs-analysis
description: "Use when running analysis, configuring analysis options (modal modes, P-delta, nonlinear), managing run flags, checking analysis status, and deleting results. Covers RunAnalysis, SetRunCaseFlag, GetRunCaseFlag, DeleteResults, and solver options."
---

# ETABS Analysis

Read `etabs-core` first for sandbox rules and return value conventions.

---

## ⚠️ CRITICAL: SetModelIsLocked(False) Destroys Results

**`model.SetModelIsLocked(False)` permanently deletes all analysis results.** Never unlock unless you intend to modify the model and re-run analysis.

```python
# Check lock state
is_locked = model.GetModelIsLocked()
print("Locked:", is_locked)

# Unlock to allow modifications — DESTROYS all existing results
ret = model.SetModelIsLocked(False)

# Lock is set automatically after RunAnalysis() succeeds — do NOT manually lock
```

**Correct sequence:**
1. Modify model (geometry / loads / sections / scale factors)
2. `model.Analyze.RunAnalysis()` — model auto-locks after analysis
3. Read results immediately — never unlock between analysis and result extraction

---

## Complete Structural Analysis Workflow (10 Steps)

```
1. Define geometry      → model.PointObj, FrameObj, AreaObj
2. Define materials     → model.PropMaterial
3. Assign sections      → model.PropFrame, PropArea + FrameObj.SetSection / AreaObj.SetProperty
4. Define load patterns → model.LoadPatterns.Add(...)
5. Define load cases    → model.LoadCases.StaticLinear / Modal / ResponseSpectrum
6. Define combos        → model.LoadCombos.Add(...) + SetCaseList(...)
7. Run analysis         → model.Analyze.RunAnalysis()
                          For large models: run in ETABS UI (F5) — MCP timeout will occur
8. Model auto-locks     → model.GetModelIsLocked() returns True
9. Extract results      → model.Results.* (NEVER unlock between steps 7 and 9!)
10. Optional seismic scaling → unlock → modify RS scale factor → re-run → re-read
    Optional design     → model.DesignConcrete.StartDesign() / DesignSteel.StartDesign()
```

---

## Model Lock State

---

## Checking Analysis Status

```python
is_locked = model.GetModelIsLocked()
if not is_locked:
    print("No results available — model is unlocked. Run analysis first.")
else:
    print("Model is locked — analysis results are available.")
```

---

## Delete Results

```python
# Delete results for a specific load case (unlock that case only)
ret = model.Analyze.DeleteResults("Dead", False)

# Delete ALL results (fully unlocks model)
ret = model.Analyze.DeleteResults("", True)
```

---

## Run Case Flags — Select Which Cases to Analyze

By default all cases are set to run. Use flags to run a subset.

```python
# GetRunCaseFlag() → [count, names_tuple, run_flags_tuple, ret]
t = model.Analyze.GetRunCaseFlag()
n = t[0]
names = list(t[1])
flags = list(t[2])
for i in range(n):
    print(names[i], "→ run:", flags[i])

# Deselect all cases
ret = model.Analyze.SetRunCaseFlag("", False, True)   # Name="" + applyAll=True

# Select specific cases
ret = model.Analyze.SetRunCaseFlag("Dead", True)
ret = model.Analyze.SetRunCaseFlag("SDL", True)
ret = model.Analyze.SetRunCaseFlag("LL", True)
ret = model.Analyze.SetRunCaseFlag("Modal", True)
ret = model.Analyze.SetRunCaseFlag("RSX", True)
ret = model.Analyze.SetRunCaseFlag("RSY", True)

# Alternatively via LoadCases (same effect)
ret = model.LoadCases.SetRunCaseFlag("Dead", True, False)
```

---

## Running Analysis

**IMPORTANT — Large Models:** `RunAnalysis()` blocks until complete. For large models (>1000 elements) this exceeds the MCP timeout. If the model is large, tell the user to run analysis directly in ETABS: **Analyze → Run Analysis (F5)**. After analysis completes in ETABS, `model.GetModelIsLocked()` returns `True` and results are accessible via MCP.

### Run All Cases

```python
# Ensure model is unlocked before running
ret = model.SetModelIsLocked(False)

# (Optional) Delete old results
ret = model.Analyze.DeleteResults("", True)

# Run
ret = model.Analyze.RunAnalysis()
if ret != 0:
    print("Analysis failed, ret =", ret)
else:
    print("Analysis completed successfully.")
    print("Locked:", model.GetModelIsLocked())  # should be True

result = {"analysis_ret": ret, "success": ret == 0, "locked": model.GetModelIsLocked()}
```

### Run Specific Cases Only

```python
ret = model.SetModelIsLocked(False)
ret = model.Analyze.DeleteResults("", True)

# Deselect all, then select desired
ret = model.Analyze.SetRunCaseFlag("", False, True)
ret = model.Analyze.SetRunCaseFlag("Dead", True)
ret = model.Analyze.SetRunCaseFlag("LL", True)
ret = model.Analyze.SetRunCaseFlag("Modal", True)

ret = model.File.Save()  # recommended: save before running

ret = model.Analyze.RunAnalysis()
result = {"success": ret == 0, "locked": model.GetModelIsLocked()}
```

---

## Create Analysis Model (Without Running)

```python
# Creates the analysis model mesh without running it
ret = model.Analyze.CreateAnalysisModel()
if ret != 0:
    print("Create model failed:", ret)
```

---

## Modal Analysis Configuration

### Eigen (Ritz) Modes

```python
# Case must be created first with Modal.SetCase
ret = model.LoadCases.Modal.SetCase("Modal")

# ModalEigen.SetNumberModes(Name, MaxModes, MinModes) → ret
ret = model.LoadCases.ModalEigen.SetNumberModes("Modal", 12, 1)

# ModalEigen.GetNumberModes(Name) → [MaxModes, MinModes, ret]
t = model.LoadCases.ModalEigen.GetNumberModes("Modal")
max_modes = t[0]
min_modes = t[1]
print("Max modes:", max_modes)
```

### Ritz Vectors

```python
ret = model.LoadCases.ModalRitz.SetCase("ModalRitz")
# SetNumberModes is the same call
ret = model.LoadCases.ModalRitz.SetNumberModes("ModalRitz", 15, 1)
```

---

## Static Nonlinear (P-Delta / Large Displacement)

```python
# Create nonlinear static case
ret = model.LoadCases.StaticNonlinear.SetCase("GravityNL")

# SetLoads(Name, n, LoadType[], LoadName[], SF[]) → ret
ret = model.LoadCases.StaticNonlinear.SetLoads(
    "GravityNL", 2,
    ["Load", "Load"],
    ["Dead", "SDL"],
    [1.0, 1.0],
)

# SetGeometricNonlinearity(Name, NonlinearType) → ret   ← CORRECT name
# (SetGeomNonlinearity does NOT exist — AttributeError)
# NonlinearType: 0=None, 1=PDelta, 2=PDeltaPlusLargeDisp
ret = model.LoadCases.StaticNonlinear.SetGeometricNonlinearity("GravityNL", 1)
```

---

## Response Spectrum Configuration

```python
# Set modal combination method for RS case
# ResponseSpectrum.SetModalCase(Name, ModalCase) → ret
ret = model.LoadCases.ResponseSpectrum.SetModalCase("RSX", "Modal")

# Set directional combination (SRSS or CQC)
# ResponseSpectrum.SetDirCombination(Name, DirCombType) → ret
# DirCombType: 1=SRSS, 2=CQC
ret = model.LoadCases.ResponseSpectrum.SetDirCombination("RSX", 2)  # CQC

# Set modal combination
# ResponseSpectrum.SetModalCombination(Name, ModalCombType, Period, Alpha, CF, TD) → ret
# ModalCombType: 1=CQC, 2=SRSS, 3=AbsAdd, 4=GMC, 5=10pct, 6=NRC10pct, 7=DoubleSum
ret = model.LoadCases.ResponseSpectrum.SetModalCombination("RSX", 1, 0.05, 1.5, 0, 0)
```

---

## Active Degrees of Freedom

```python
# GetActiveDOF() → [(UX,UY,UZ,RX,RY,RZ), ret]  — inner tuple at [0]
t = model.Analyze.GetActiveDOF()
dofs = list(t[0])   # unpack inner sub-tuple: [UX, UY, UZ, RX, RY, RZ]
ret = t[1]
print("Active DOF [UX,UY,UZ,RX,RY,RZ]:", dofs)

# SetActiveDOF — NOT USABLE via MCP (SAFEARRAY ByRef limitation)
# ETABS 23.2.0: SetActiveDOF([True,True,True,True,True,True]) returns ret=1 (failure)
# Same comtypes SAFEARRAY limitation as SetTableForEditingArray input arrays
# Use ETABS UI: Analyze → Set Analysis Options → Active DOFs
```

---

## Solver Options

```python
# GetSolverOption_1() → [SolverType, SolverProc, Force32Bit, StiffCase, ret]
# VERIFIED: 5-element return — [SolverType, SolverProc, Force32Bit, StiffCase, ret]
# SolverType: 0=Standard, 1=Advanced, 2=Multi-threaded
t = model.Analyze.GetSolverOption_1()
solver_type = t[0]
solver_proc = t[1]   # NOT "MultiThread" — this is SolverProc
force_32bit = t[2]
stiff_case = t[3]
print("Solver type:", solver_type)

# SetSolverOption_1(SolverType, SolverProc, Force32Bit, StiffCase) → ret
# VERIFIED: 4 args — no separate MultiThread param
ret = model.Analyze.SetSolverOption_1(2, 0, False, "Dead")
```

---

## Complete Analysis Workflow

```python
# 1. Unlock model
ret = model.SetModelIsLocked(False)

# 2. Delete old results
ret = model.Analyze.DeleteResults("", True)

# 3. Configure which cases to run
ret = model.Analyze.SetRunCaseFlag("", False, True)   # deselect all
ret = model.Analyze.SetRunCaseFlag("Dead", True)
ret = model.Analyze.SetRunCaseFlag("SDL", True)
ret = model.Analyze.SetRunCaseFlag("LL", True)
ret = model.Analyze.SetRunCaseFlag("Modal", True)
ret = model.Analyze.SetRunCaseFlag("RSX", True)
ret = model.Analyze.SetRunCaseFlag("RSY", True)

# 4. Configure modal case
ret = model.LoadCases.ModalEigen.SetNumberModes("Modal", 12, 1)

# 5. Save before running
ret = model.File.Save()

# 6. Run analysis
ret = model.Analyze.RunAnalysis()

is_locked = model.GetModelIsLocked()
result = {
    "analysis_ret": ret,
    "success": ret == 0,
    "model_locked": is_locked,
}
```

---

## Post-Analysis: Unlock to Modify, Re-run

```python
# After analysis, if you need to modify the model:
ret = model.SetModelIsLocked(False)  # DESTROYS results — only do this intentionally
# ... make modifications ...

# Re-run analysis
ret = model.Analyze.RunAnalysis()
print("Re-analysis success:", ret == 0)
# Model is now locked again — safe to read results
```

---

## Seismic Scaling Workflow (85% Rule) — Unlock → Scale → Re-run

```python
# Read base shears first (while model is locked)
model.Results.Setup.DeselectAllCasesAndCombosForOutput()
for c in ["EX", "EY", "Spec X", "Spec Y"]:
    model.Results.Setup.SetCaseSelectedForOutput(c)
br = model.Results.BaseReact()
n = br[0]
cases = list(br[1])
FX = list(br[4])
FY = list(br[5])

V_EX = max(abs(FX[i]) for i in range(n) if cases[i] == "EX")
V_EY = max(abs(FY[i]) for i in range(n) if cases[i] == "EY")
V_SX = max(abs(FX[i]) for i in range(n) if cases[i] == "Spec X")
V_SY = max(abs(FY[i]) for i in range(n) if cases[i] == "Spec Y")

Sx = (0.85 * V_EX) / V_SX
Sy = (0.85 * V_EY) / V_SY
print("Scale factors: Sx =", Sx, "Sy =", Sy)

# Now unlock and apply scaling
ret = model.SetModelIsLocked(False)

rs_x = model.LoadCases.ResponseSpectrum.GetLoads("Spec X")
# rs_x: [n, (LoadNames,), (Funcs,), (SFs,), (CSys_str,), (Angles,), ret]
n_loads = rs_x[0]
new_SFs_x = [rs_x[3][i] * Sx for i in range(n_loads)]
model.LoadCases.ResponseSpectrum.SetLoads("Spec X", n_loads,
    list(rs_x[1]), list(rs_x[2]), new_SFs_x, list(rs_x[4]), list(rs_x[5]))

rs_y = model.LoadCases.ResponseSpectrum.GetLoads("Spec Y")
n_loads_y = rs_y[0]
new_SFs_y = [rs_y[3][i] * Sy for i in range(n_loads_y)]
model.LoadCases.ResponseSpectrum.SetLoads("Spec Y", n_loads_y,
    list(rs_y[1]), list(rs_y[2]), new_SFs_y, list(rs_y[4]), list(rs_y[5]))

# Re-run analysis
ret = model.Analyze.RunAnalysis()
result = {"Sx": Sx, "Sy": Sy, "reanalysis_success": ret == 0}
```
