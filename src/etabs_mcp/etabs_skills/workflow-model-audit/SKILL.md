# workflow-model-audit

Complete model audit before running analysis. Returns version, file, element counts, materials, sections, loads, and groups in one call.

## When to use
Run this first to verify a model is properly set up before proceeding with analysis or results extraction.

## Verified code (ETABS 23.2.0)

```python
model.SetPresentUnits(6)  # kN_m

ver    = model.GetVersion()          # ['23.2.0', 0.0, 0]
fname  = model.GetModelFilename(True) # string directly
locked = model.GetModelIsLocked()    # bool directly

stories = model.Story.GetStories()   # [n, (names,), (heights,), ...]
groups  = model.GroupDef.GetNameList()
mats    = model.PropMaterial.GetNameList()
secs    = model.PropFrame.GetNameList()
asecs   = model.PropArea.GetNameList()
lp      = model.LoadPatterns.GetNameList()
lc      = model.LoadCases.GetNameList()
co      = model.RespCombo.GetNameList()
pts     = model.PointObj.GetNameList()
frames  = model.FrameObj.GetNameList()
areas   = model.AreaObj.GetNameList()

result = {
    "version":        ver[0],
    "file":           fname.split("\\")[-1],
    "analyzed":       locked,
    "stories":        stories[0],
    "story_names":    list(stories[1]),
    "groups":         list(groups[1]),
    "materials":      list(mats[1]),
    "frame_sections": secs[0],
    "area_sections":  asecs[0],
    "load_patterns":  lp[0],
    "load_cases":     lc[0],
    "combinations":   co[0],
    "joints":         pts[0],
    "frames":         frames[0],
    "areas":          areas[0],
}
```

## Return notes
- All `GetNameList()` return `[count, (names_tuple), ret]` — names at `[1]`, count at `[0]`
- `GetModelIsLocked()` returns `bool` (True = model has been analyzed)
- `GetModelFilename(True)` returns full path as `str`
- `GetVersion()` returns `[version_str, build_num, ret]`
