# workflow-modifiers

Apply ACI 318 / AISC cracked-section stiffness modifiers to frame and area objects by group.

## When to use
- Service load analysis (pre-design): reduced stiffness
- Design analysis: ACI 318 Table 6.6.3.1 values
- Always run BEFORE analysis

## ACI 318 Table 6.6.3.1 — Effective Stiffness

| Element | I33 (bending) | Notes |
|---|---|---|
| Columns (uncracked) | 0.70 | Conservative for service |
| Beams | 0.35 | About major axis |
| Slabs (diaphragm) | 0.25 | In-plane f11/f22/f12 |
| Slabs (non-diaphragm) | 0.10 | Flat plate/slab |
| Walls (in-plane) | 0.35 | f11/f22 |
| Spandrels | 0.35 | Shell m11/m22 |

## Frame modifiers array — 8 values
`[CrossSectArea, As2, As3, Torsion(J), I22, I33, Mass, Weight]`

## Area modifiers array — 10 values
`[f11, f22, f12, m11, m22, m12, v13, v23, Mass, Weight]`

## itemType
- `0` = single object by name
- `1` = all objects in named group
- `2` = all selected objects

## Verified code — Service modifiers

```python
model.SetModelIsLocked(False)

# Columns: I22=0.70, I33=0.70
model.FrameObj.SetModifiers("AllColumns", [1,1,1,1,0.70,0.70,1,1], 1)

# Beams: J=0.05 (torsion), I22=I33=0.35
model.FrameObj.SetModifiers("AllBeams", [1,1,1,0.05,0.35,0.35,1,1], 1)

# Diaphragm slabs: f11=f22=f12=0.25, m11=m22=m12=0.25
model.AreaObj.SetModifiers("AllDiaphragmSlabs",    [0.25]*6 + [1,1,1,1], 1)

# Non-diaphragm slabs: 0.10
model.AreaObj.SetModifiers("AllNonDiaphragmSlabs", [0.10]*6 + [1,1,1,1], 1)

# Walls: 0.35 in-plane stiffness
model.AreaObj.SetModifiers("AllWalls",    [0.35,0.35,0.35,0.35,0.35,0.35,1,1,1,1], 1)

# Spandrels: 0.35
model.AreaObj.SetModifiers("AllSpandrels",[0.35,0.35,0.35,0.35,0.35,0.35,1,1,1,1], 1)

result = "Service modifiers applied"
```

## Design modifiers (post-scaling)

```python
model.SetModelIsLocked(False)

model.FrameObj.SetModifiers("AllColumns",    [1,1,1,1,0.70,0.70,1,1], 1)
model.FrameObj.SetModifiers("AllBeams",      [1,1,1,0.05,0.35,0.35,1,1], 1)
model.AreaObj.SetModifiers("AllDiaphragmSlabs",    [0.10]*6 + [1,1,1,1], 1)
model.AreaObj.SetModifiers("AllNonDiaphragmSlabs", [0.10]*6 + [1,1,1,1], 1)
model.AreaObj.SetModifiers("AllWalls",    [0.35,0.35,0.35,0.10,0.10,0.10,1,1,1,1], 1)
model.AreaObj.SetModifiers("AllSpandrels",[0.35,0.35,0.35,0.35,0.35,0.35,1,1,1,1], 1)

result = "Design modifiers applied"
```

## Read current modifiers

```python
# Frame: returns [(A,As2,As3,J,I22,I33,Mass,Weight), ret]
fm = model.FrameObj.GetModifiers("frame_name")
i33 = fm[0][5]

# Area: returns [(f11,f22,f12,m11,m22,m12,v13,v23,Mass,Weight), ret]
am = model.AreaObj.GetModifiers("area_name")
f11 = am[0][0]
```
