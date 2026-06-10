---
name: etabs-sections
description: "Use when defining section properties: frame sections (rectangular, circular, I-shape, tube, pipe), area/slab/shell sections, wall sections, section modifiers, and assigning sections to elements."
---

# ETABS Section Properties

Read `etabs-core` and `etabs-materials` first. Materials must exist before sections reference them.

---

## Frame Sections (`model.PropFrame`)

### List Frame Sections

```python
# GetNameList() → [count, (names_tuple), ret]
t = model.PropFrame.GetNameList()
n = t[0]
names = list(t[1]) if n > 0 else []
result = names
```

### Rectangular Concrete Section

```python
ret = model.SetPresentUnits(6)  # kN_m — dimensions in metres

# SetRectangle(Name, MatProp, T3, T2, Color=-1, Notes="", GUID="") → ret
# T3 = depth (local 3-axis / height), T2 = width (local 2-axis)
ret = model.PropFrame.SetRectangle("Col400x400", "C30", 0.4, 0.4)
ret = model.PropFrame.SetRectangle("Col500x500", "C30", 0.5, 0.5)
ret = model.PropFrame.SetRectangle("Beam300x600", "C30", 0.6, 0.3)
ret = model.PropFrame.SetRectangle("Beam250x500", "C30", 0.5, 0.25)

# GetRectangle(Name) → [propName, matName, t3(depth), t2(width), color, notes, guid, ret]
# propName = section name, matName = material, t3 = depth (m), t2 = width (m)
t = model.PropFrame.GetRectangle("Col400x400")
prop_name = t[0]
mat = t[1]
t3 = t[2]
t2 = t[3]
print("Section:", prop_name, "Material:", mat, "Depth:", t3, "Width:", t2)
```

### Circular Concrete Section

```python
# SetCircle(Name, MatProp, T3, Color=-1, Notes="", GUID="") → ret
# T3 = diameter
ret = model.PropFrame.SetCircle("Col500dia", "C30", 0.5)
ret = model.PropFrame.SetCircle("Pile600dia", "C30", 0.6)
```

### I-Section (Steel, General)

```python
# SetISection(Name, MatProp, T3, T2, Tf, Tw, T2b, Tfb) → ret
# T3=total depth, T2=top flange width, Tf=top flange thickness
# Tw=web thickness, T2b=bottom flange width, Tfb=bottom flange thickness
# All dimensions in current length units (metres for kN_m)

# W360x101 equivalent (mm → m)
ret = model.PropFrame.SetISection(
    "W360x101", "A992Fy50",
    0.357,   # depth
    0.257,   # top flange width
    0.0185,  # top flange thickness
    0.011,   # web thickness
    0.257,   # bottom flange width
    0.0185,  # bottom flange thickness
)
```

### Tube / Box Section

```python
# SetTube(Name, MatProp, T3, T2, Tf, Tw) → ret
# T3=depth, T2=width, Tf=flange thickness, Tw=web thickness
ret = model.PropFrame.SetTube("SHS200x200x10", "A992Fy50", 0.2, 0.2, 0.01, 0.01)
ret = model.PropFrame.SetTube("RHS200x150x8", "A992Fy50", 0.2, 0.15, 0.008, 0.008)
```

### Pipe / CHS Section

```python
# SetPipe(Name, MatProp, T3, Tw) → ret
# T3 = outer diameter, Tw = wall thickness
ret = model.PropFrame.SetPipe("CHS219x8", "A992Fy50", 0.219, 0.008)

# GetPipe(Name) → [propName, matName, diameter_m, thickness_m, color, notes, guid, ret]
t = model.PropFrame.GetPipe("CHS219x8")
prop_name = t[0]
mat = t[1]
diameter = t[2]
thickness = t[3]
print("Diameter:", diameter, "Thickness:", thickness)
```

### Import from Steel Section Database

```python
# Use kip_in for AISC catalog import, then switch back
ret = model.SetPresentUnits(3)  # kip_in

# ImportProp(fileName, propType, matProp, propName, Color=-1, Notes="", GUID="") → ret
# fileName: section database filename (e.g. "AISC14" for AISC 14th edition)
# propType: determined automatically from DB

ret = model.PropFrame.ImportProp("W14X82", "AISC14", "A992Fy50", "W14X82")
ret = model.PropFrame.ImportProp("W18X97", "AISC14", "A992Fy50", "W18X97")
ret = model.PropFrame.ImportProp("HSS6X6X0.500", "AISC14", "A992Fy50", "HSS6X6X0.500")

ret = model.SetPresentUnits(6)  # restore kN_m
```

### Get Section General Properties

```python
# GetSection(Name) → varies by section type
# For any section, use GetNameList to verify it exists first
t = model.PropFrame.GetNameList()
names = list(t[1])
print("Sections:", names)
```

---

## Frame Section Modifiers

Stiffness modifiers are commonly applied for ACI 318 cracked section analysis.

```python
# SetModifiers(Name, Value[8], ItemType=0) → ret
# Value[8] = [CrossSectArea, As2, As3, Torsion, I22, I33, Mass, Weight]
# ItemType: 0=Object, 1=Group, 2=SelectedObjects

# ACI 318-14 Table 6.6.3.1 cracked section factors:
# Columns (uncracked): I22=I33=0.70
col_mods = [1.0, 1.0, 1.0, 1.0, 0.70, 0.70, 1.0, 1.0]
ret = model.FrameObj.SetModifiers("1", col_mods)

# Beams (cracked): I22=I33=0.35
beam_mods = [1.0, 1.0, 1.0, 1.0, 0.35, 0.35, 1.0, 1.0]
ret = model.FrameObj.SetModifiers("2", beam_mods)

# Apply to all frames in a group
ret = model.FrameObj.SetModifiers("Columns", col_mods, 1)   # ItemType=1=Group
ret = model.FrameObj.SetModifiers("Beams", beam_mods, 1)
```

---

## Area / Shell Sections (`model.PropArea`)

### List Area Sections

```python
t = model.PropArea.GetNameList()
n = t[0]
names = list(t[1]) if n > 0 else []
result = names
```

### Shell Section (Slab)

**IMPORTANT:** `PropArea.GetShell_1()` and `PropArea.GetShell()` do NOT exist in ETABS 23.
To read back slab properties use `GetSlab(name)`. To read wall properties use `GetWall(name)`.
`SetShell_1` still works for creating/setting sections.

```python
ret = model.SetPresentUnits(6)  # kN_m — thickness in metres

# SetShell_1(Name, ShellType, IncludeDrillingDOF, MatProp, MatAng,
#            Thickness, Bending12KFactor, Color=-1, Notes="", GUID="") → ret
#
# ShellType:
#   1 = ShellThin (Kirchhoff — thin slab, no shear deformation)
#   2 = ShellThick (Mindlin — thick slab, includes shear)
#   3 = Membrane (in-plane only)
#   4 = Plate (Kirchhoff plate, no in-plane)
#   5 = PlateThick (Mindlin plate)
#   6 = ShellLayered (layered / nonlinear)

# Thin slab 200mm
ret = model.PropArea.SetShell_1(
    "Slab200",
    1,          # ShellThin
    True,       # IncludeDrillingDOF
    "C30",
    0.0,        # material angle
    0.2,        # thickness = 200mm = 0.2m
    1.0,        # Bending12KFactor
)

# Thick slab 300mm
ret = model.PropArea.SetShell_1("Slab300", 2, True, "C30", 0.0, 0.3, 1.0)

# GetSlab(Name) → [shellType, matType, matName, thickness_m, color, notes, guid, ret]
# Use GetSlab() to read back slab properties (GetShell_1 does NOT exist)
t = model.PropArea.GetSlab("Slab200")
shell_type = t[0]
mat_type = t[1]
mat = t[2]
thickness = t[3]
print("Type:", shell_type, "Mat:", mat, "Thickness:", thickness)
```

### Membrane Section (In-plane Only — for rigid diaphragm or non-structural slab)

```python
ret = model.PropArea.SetShell_1("Membrane200", 3, True, "C30", 0.0, 0.2, 1.0)
```

### Wall Section

```python
# Walls typically use ShellThin or ShellThick
ret = model.PropArea.SetShell_1("Wall200", 1, True, "C30", 0.0, 0.2, 1.0)
ret = model.PropArea.SetShell_1("Wall300", 2, True, "C30", 0.0, 0.3, 1.0)

# Membrane wall (no out-of-plane stiffness)
ret = model.PropArea.SetShell_1("WallMembrane", 3, True, "C30", 0.0, 0.2, 1.0)
```

### SetSlab — High-Level Slab Definition

```python
# SetSlab(Name, Thick, SlabType, ShellType, MatProp) → ret
# SlabType: 0=Slab, 1=Drop, 2=Stiff, 3=Ribbed, 4=Waffle, 5=Mat, 6=Footing
# ShellType: 1=ShellThin, 2=ShellThick, 3=Membrane
ret = model.PropArea.SetSlab("Slab200_HL", 0.2, 0, 1, "C30")
```

### SetWall — High-Level Wall Definition

```python
# SetWall(Name, WallType, ShellType, MatProp, Thick) → ret
# WallType: 0=Specified, 1=Auto
ret = model.PropArea.SetWall("Wall200_HL", 0, 1, "C30", 0.2)
```

---

## Area Section Modifiers

```python
# AreaObj.SetModifiers(Name, Value[10], ItemType=0) → ret
# Value[10]: [f11, f22, f12, m11, m22, m12, v13, v23, MassModifier, WeightModifier]
# ACI 318-14 cracked slab: m11=m22=m12=0.25 (two-way), shear unchanged

cracked_slab_mods = [1.0, 1.0, 1.0, 0.25, 0.25, 0.25, 1.0, 1.0, 1.0, 1.0]
ret = model.AreaObj.SetModifiers("1", cracked_slab_mods)

# Apply to all areas in a group
ret = model.AreaObj.SetModifiers("Slabs", cracked_slab_mods, 1)  # ItemType=1=Group
```

---

## Assigning Sections to Elements

```python
# Assign frame section to a single element
# SetSection(Name, PropName, sVarTotalLength=0, sVarRelStartLoc=0, ItemType=0) → ret
ret = model.FrameObj.SetSection("1", "Col400x400")
ret = model.FrameObj.SetSection("2", "Beam300x600")

# Assign to all frames in a group
ret = model.FrameObj.SetSection("Columns", "Col500x500", 0, 0, 1)  # ItemType=1=Group
ret = model.FrameObj.SetSection("Beams", "Beam300x600", 0, 0, 1)

# Assign area section to a single area
# SetProperty(Name, PropName, ItemType=0) → ret
ret = model.AreaObj.SetProperty("1", "Slab200")

# Assign to group
ret = model.AreaObj.SetProperty("Slabs", "Slab200", 1)

# Get current frame section
# GetSection(Name) → [PropName, SAuto, ret]
t = model.FrameObj.GetSection("1")
prop_name = t[0]
print("Section:", prop_name)
```

---

## Complete Section Setup Example

```python
ret = model.SetModelIsLocked(False)
ret = model.SetPresentUnits(6)  # kN_m

# Frame sections (assumes C30 and A992Fy50 materials exist)
ret = model.PropFrame.SetRectangle("Col400x400", "C30", 0.4, 0.4)
ret = model.PropFrame.SetRectangle("Col500x500", "C30", 0.5, 0.5)
ret = model.PropFrame.SetRectangle("Beam300x600", "C30", 0.6, 0.3)
ret = model.PropFrame.SetRectangle("Beam250x500", "C30", 0.5, 0.25)

# Area sections
ret = model.PropArea.SetShell_1("Slab200", 1, True, "C30", 0.0, 0.2, 1.0)
ret = model.PropArea.SetShell_1("Wall200", 1, True, "C30", 0.0, 0.2, 1.0)

t = model.PropFrame.GetNameList()
frame_sections = list(t[1])
t2 = model.PropArea.GetNameList()
area_sections = list(t2[1])

result = {"frame_sections": frame_sections, "area_sections": area_sections}
```
