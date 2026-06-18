---
name: etabs-geometry
description: "Use when creating or querying geometry: joints/points, frame elements (beams/columns/braces), area elements (slabs/walls/shells), stories, groups, restraints, and section assignments."
---

# ETABS Geometry

Read `etabs-core` first for sandbox rules, units, and return value conventions.

**Key convention:** GetNameList-style calls return a tuple where `[0]` = count, `[1]` = names tuple, `[-1]` = ret code.

---

## Joints / Points (`model.PointObj`)

### Add a Joint

```python
ret = model.SetPresentUnits(6)  # kN_m — always set units first

# AddCartesian(x, y, z, UserName="", CSys="Global", MergeOff=False, MergeNumber=0)
# Returns tuple: [name_assigned, ret]
result_tuple = model.PointObj.AddCartesian(0.0, 0.0, 0.0)
name = result_tuple[0]   # auto-assigned name, e.g. "1"
ret = result_tuple[-1]
print("Added joint:", name)

# With explicit name
result_tuple2 = model.PointObj.AddCartesian(5.0, 0.0, 3.0, "J2")
```

### Count and List Joints

```python
count = model.PointObj.Count()
print("Total joints:", count)

# GetNameList() → [count, (name1, name2, ...), ret]
t = model.PointObj.GetNameList()
n = t[0]
names = list(t[1])
ret = t[-1]
result = names
```

### Get Joint Coordinates

```python
# GetCoordCartesian(Name) → [x, y, z, ret]
# Note: pass only the name — no CSys argument
t = model.PointObj.GetCoordCartesian("1")
x, y, z = t[0], t[1], t[2]
print("Joint 1 coords:", x, y, z)
```

### Get All Joints with Coordinates

```python
ret = model.SetPresentUnits(6)
t = model.PointObj.GetNameList()
names = list(t[1])

joints = []
for name in names:
    ct = model.PointObj.GetCoordCartesian(name)
    joints.append({"name": name, "x": ct[0], "y": ct[1], "z": ct[2]})

result = joints
```

### Restraints (Boundary Conditions)

```python
# SetRestraint(Name, Value[6], ItemType=0) → returns tuple [(restraint_vals), ret]
# NOT a scalar int — unpack carefully
# Value = [U1, U2, U3, R1, R2, R3] — True=fixed, False=free

# Fixed base (pin)
result_t = model.PointObj.SetRestraint("1", [True, True, True, False, False, False])
# result_t[0] = (vals tuple), result_t[1] = ret code

# Fixed base (fully fixed)
result_t = model.PointObj.SetRestraint("1", [True, True, True, True, True, True])

# GetRestraint(Name) → [(F1,F2,F3,M1,M2,M3), ret]
# The 6 boolean values come back as a single tuple at index [0]
t = model.PointObj.GetRestraint("1")
restraints = list(t[0])  # unpack the inner 6-element tuple
print("Restraints:", restraints)  # [F1, F2, F3, M1, M2, M3]
```

### Delete a Joint

```python
ret = model.PointObj.Delete("1")
```

---

## Frame Elements (`model.FrameObj`)

Frame elements represent beams, columns, and braces.

### Add a Frame by Joint Names

```python
# AddByPoint(Point1, Point2, PropName="Default", UserName="", CSys="Global")
# Returns: [name_assigned, ret]
t = model.FrameObj.AddByPoint("1", "2", "W14X82")
frame_name = t[0]
ret = t[-1]
print("Added frame:", frame_name)
```

### Add a Frame by Coordinates

```python
# AddByCoord(xi, yi, zi, xj, yj, zj, PropName="Default", UserName="", CSys="Global")
# Returns: [name_assigned, ret]
t = model.FrameObj.AddByCoord(0, 0, 0, 0, 0, 4, "Col400x400")
col_name = t[0]
```

### Count and List Frames

```python
count = model.FrameObj.Count()

# GetNameList() → [count, (names_tuple), ret]
t = model.FrameObj.GetNameList()
names = list(t[1])
result = names
```

### Get Frame End Points

```python
# GetPoints(Name) → [point1_name, point2_name, ret]
t = model.FrameObj.GetPoints("1")
pt1 = t[0]
pt2 = t[1]
ret = t[-1]
```

### Get Frame Section

```python
# GetSection(Name) → [PropName, SAuto, ret]
t = model.FrameObj.GetSection("1")
prop_name = t[0]
```

### Set Frame Section

```python
# SetSection(Name, PropName, sVarTotalLength=0, sVarRelStartLoc=0, ItemType=0)
ret = model.FrameObj.SetSection("1", "Col400x400")

# Apply section to all frames in a group
ret = model.FrameObj.SetSection("MyGroup", "W14X82", 0, 0, 1)  # ItemType=1=Group
```

### Frame Section Modifiers (Stiffness Reduction)

```python
# SetModifiers(Name, Value[8], ItemType=0)
# Value[8]: [CrossSectArea, As2, As3, Torsion, I22, I33, Mass, Weight]
# ACI 318 cracked section factors example:
modifiers = [1.0, 1.0, 1.0, 1.0, 0.35, 0.35, 1.0, 1.0]  # columns
ret = model.FrameObj.SetModifiers("1", modifiers)

beam_modifiers = [1.0, 1.0, 1.0, 1.0, 0.35, 0.35, 1.0, 1.0]  # beams
ret = model.FrameObj.SetModifiers("2", beam_modifiers)
```

### Set Frame Local Axis Rotation

```python
# SetLocalAxes(Name, Ang, ItemType=0)
ret = model.FrameObj.SetLocalAxes("1", 0.0)  # 0 degrees
```

### Delete a Frame

```python
ret = model.FrameObj.Delete("1")
```

---

## Area Elements (`model.AreaObj`)

Area elements represent slabs, walls, and shells.

### Add an Area by Coordinates

```python
# AddByCoord(NumberPoints, x[], y[], z[], PropName="Default", UserName="", CSys="Global")
# Returns: [name_assigned, ret]  (for AddByCoord name IS at [0])
x_list = [0.0, 5.0, 5.0, 0.0]
y_list = [0.0, 0.0, 5.0, 5.0]
z_list = [3.0, 3.0, 3.0, 3.0]
t = model.AreaObj.AddByCoord(4, x_list, y_list, z_list, "Slab200")
area_name = t[0]
```

### Add an Area by Joint Names

```python
# AddByPoint(NumberPoints, points[], PropName="Default", UserName="")
# Returns: [(joint_names_tuple), area_element_name, ret]
# VERIFIED: area name is at [1] NOT [0] — [0] is the input joint names tuple
t = model.AreaObj.AddByPoint(4, ["1", "2", "3", "4"], "Wall200")
area_name = t[1]   # ← [1] not [0]
ret = t[2]

# Also works with 3-node triangular areas:
t2 = model.AreaObj.AddByPoint(3, ["1", "2", "3"], "Wall200")
tri_name = t2[1]
```

### Count and List Areas

```python
count = model.AreaObj.Count()

# GetNameList() → [count, (names_tuple), ret]
t = model.AreaObj.GetNameList()
names = list(t[1])
```

### Get Area Corner Points

```python
# GetPoints(Name) → [number_points, (point_names_tuple), ret]
t = model.AreaObj.GetPoints("1")
n_pts = t[0]
pts = list(t[1])
```

### Assign Area Property

```python
# SetProperty(Name, PropName, ItemType=0)
ret = model.AreaObj.SetProperty("1", "Slab200")
```

### Area Section Modifiers

```python
# SetModifiers(Name, Value[10], ItemType=0)
# Value[10]: [f11, f22, f12, m11, m22, m12, v13, v23, MassModifier, WeightModifier]
# Slab with in-plane stiffness only (membrane + bending reduction)
modifiers = [1.0, 1.0, 1.0, 0.25, 0.25, 0.25, 1.0, 1.0, 1.0, 1.0]
ret = model.AreaObj.SetModifiers("1", modifiers)
```

### Delete an Area

```python
ret = model.AreaObj.Delete("1")
```

---

## Stories (`model.Story`)

### Get All Stories

```python
# GetStories() → [n, names_tuple, heights_tuple, isMaster_tuple, similarTo_tuple,
#                  spliceAbove_tuple, spliceHeight_tuple, color_tuple, ret]
t = model.Story.GetStories()
n = t[0]
names = list(t[1])
heights = list(t[2])
is_master = list(t[3])

result = [{"story": names[i], "height": heights[i], "is_master": is_master[i]}
          for i in range(n)]
```

### Get Story Elevation

```python
# GetElevation(StoryName) → [elevation, ret]
t = model.Story.GetElevation("Story1")
elev = t[0]
ret = t[-1]
print("Story1 elevation:", elev)
```

### Get Story Height

```python
# GetHeight(StoryName) → [height, ret]
t = model.Story.GetHeight("Story1")
height = t[0]
```

### All Stories with Elevations

```python
t = model.Story.GetStories()
n = t[0]
names = list(t[1])

stories_info = []
for name in names:
    et = model.Story.GetElevation(name)
    ht = model.Story.GetHeight(name)
    stories_info.append({"story": name, "elevation": et[0], "height": ht[0]})

result = stories_info
```

---

## Groups (`model.GroupDef`)

### List Groups

```python
# GetNameList() → [count, (names_tuple), ret]
t = model.GroupDef.GetNameList()
n = t[0]
names = list(t[1]) if n > 0 else []
result = names
```

### Add a Group

```python
# Add(Name) → ret
ret = model.GroupDef.Add("MyGroup")
```

### Assign Objects to a Group

```python
# SetAssignments(Name, ObjectType[], ObjectName[], Remove=False)
# ObjectType: 1=Point, 2=Frame, 3=Cable, 4=Tendon, 5=Area, 6=Solid, 7=Link
ret = model.GroupDef.SetAssignments(
    "MyGroup",
    [2, 2, 2],           # all Frame type
    ["1", "2", "3"],     # frame names
)
```

### Get Group Members

```python
# GetAssignments(Name) → [count, obj_types_tuple, obj_names_tuple, ret]
t = model.GroupDef.GetAssignments("MyGroup")
n = t[0]
types = list(t[1])
names = list(t[2])
result = [{"type": types[i], "name": names[i]} for i in range(n)]
```

---

## CHS / Pipe Section (`model.PropFrame.SetPipe`)

Use `SetPipe` for circular hollow sections (CHS / tube / pipe):

```python
# SetPipe(Name, MatProp, Diameter, WallThickness)  — all in current units (m)
ret = model.PropFrame.SetPipe("Tube150x3", "S355", 0.15, 0.003)
# OD = 0.15 m (150 mm), wall = 0.003 m (3 mm)
```

For rectangular hollow sections use `SetTube(Name, MatProp, Height, Width, Tf, Tw)`.

---

## Adjust Story Height (`model.Story.SetHeight`)

```python
# SetHeight(StoryName, Height) — height in current units
ret = model.Story.SetHeight("Story1", 5.0)   # set Story1 to 5 m

# Verify
t = model.Story.GetStories()
story_names   = list(t[1])
story_heights = list(t[2])
for i in range(t[0]):
    et = model.Story.GetElevation(story_names[i])
    print(story_names[i], "h=", story_heights[i], "elev=", et[0])
```

---

## Truss from External Node/Member Data

When node and member data come from an external source (JSON, CSV, another program), map coordinates explicitly to ETABS axes before adding geometry.

### Coordinate Mapping Convention

External data often uses a different axis convention.  
For a **bow truss in the X-Z plane** where the external data has:
- `x` = 0 (all in one plane, ignore)
- `y` = rise direction (height)
- `z` = span direction

Map to ETABS as:

```
ETABS_x = z_external + x_offset   # span → ETABS X
ETABS_y = 0                        # keep truss in Y=0 plane
ETABS_z = y_external + z_offset    # rise → ETABS Z (elevation)
```

`x_offset` shifts the left support to x=0.  
`z_offset` = column height (e.g. 5.0 m) to elevate truss above columns.

### Full Example — Truss from Dict

```python
model.SetModelIsLocked(False)
model.SetPresentUnits(6)  # kN_m

X_OFF = 5.0   # shift so left support lands at x=0 (if left node z=-5 in source)
Z_OFF = 5.0   # column height — elevates truss above ground

nodes_data = {
    # "id": [x_src, y_src, z_src]  — x_src ignored (all in-plane)
    "1": [0, 0.0, 0.0],     # left support (bottom chord)
    "2": [0, 2.5, 11.5],    # crown (top chord, midspan)
    "3": [0, 0.0, 23.0],    # right support (bottom chord)
    # ... all nodes ...
}

node_map = {}   # source id → ETABS joint name
for nid, c in nodes_data.items():
    t = model.PointObj.AddCartesian(c[2] + X_OFF, 0.0, c[1] + Z_OFF)
    node_map[nid] = t[0]

members_data = {
    # "id": [start_node_id, end_node_id]
    "1": ["1", "2"],
    # ...
}

for ends in members_data.values():
    model.FrameObj.AddByPoint(node_map[ends[0]], node_map[ends[1]], "Tube150x3")
```

### Column + Truss Assembly

After placing the truss, add RC columns below the support nodes:

```python
# x positions of the two support nodes
x_left  = 0.0    # from coordinate mapping above
x_right = 23.34  # from coordinate mapping above
col_h   = 5.0    # column height (= Z_OFF)

model.PropFrame.SetRectangle("Col400x400", "C25", 0.4, 0.4)
model.FrameObj.AddByCoord(x_left,  0, 0, x_left,  0, col_h, "Col400x400")
model.FrameObj.AddByCoord(x_right, 0, 0, x_right, 0, col_h, "Col400x400")

# Fixed bases — AddCartesian returns existing node if one already exists at that point
t_lb = model.PointObj.AddCartesian(x_left,  0, 0)
t_rb = model.PointObj.AddCartesian(x_right, 0, 0)
model.PointObj.SetRestraint(t_lb[0], [True, True, True, True, True, True])
model.PointObj.SetRestraint(t_rb[0], [True, True, True, True, True, True])
```

> **Auto-pin at z=0:** ETABS automatically applies pin restraints to all nodes at z=0 (base level). This is useful for column bases but causes problems for trusses placed at ground level — always elevate the truss above z=0 using `Z_OFF = column_height`.

---

## Object Selection (`model.SelectObj`)

```python
# Select all objects
ret = model.SelectObj.All()

# Clear all selections
ret = model.SelectObj.ClearSelection()

# Deselect all (alias)
ret = model.SelectObj.None_()
```

---

## Complete Example: 3-Story RC Frame

```python
ret = model.SetModelIsLocked(False)
ret = model.SetPresentUnits(6)  # kN_m

story_heights = [4.0, 3.5, 3.5]
bay_width = 6.0
n_bays = 3

# Create grid of columns
col_names = []
for story_idx, h in enumerate(story_heights):
    z_bot = sum(story_heights[:story_idx])
    z_top = z_bot + h
    for bay in range(n_bays + 1):
        x = bay * bay_width
        t = model.FrameObj.AddByCoord(x, 0, z_bot, x, 0, z_top, "Col400x400")
        col_names.append(t[0])

# Create beams at each floor level
beam_names = []
for story_idx, h in enumerate(story_heights):
    z = sum(story_heights[:story_idx + 1])
    for bay in range(n_bays):
        x1 = bay * bay_width
        x2 = (bay + 1) * bay_width
        t = model.FrameObj.AddByCoord(x1, 0, z, x2, 0, z, "Beam300x600")
        beam_names.append(t[0])

ret = model.File.Save()
result = {
    "columns": len(col_names),
    "beams": len(beam_names),
    "total_frames": model.FrameObj.Count(),
    "total_joints": model.PointObj.Count(),
}
```

---

## Get All Frames with End Coordinates

```python
ret = model.SetPresentUnits(6)
t = model.FrameObj.GetNameList()
frame_names = list(t[1])

frames = []
for fn in frame_names:
    pt_t = model.FrameObj.GetPoints(fn)
    p1 = pt_t[0]
    p2 = pt_t[1]
    c1 = model.PointObj.GetCoordCartesian(p1)
    c2 = model.PointObj.GetCoordCartesian(p2)
    frames.append({
        "frame": fn,
        "start": {"x": c1[0], "y": c1[1], "z": c1[2]},
        "end": {"x": c2[0], "y": c2[1], "z": c2[2]},
    })

result = frames
```
