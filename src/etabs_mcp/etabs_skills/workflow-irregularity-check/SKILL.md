---
name: workflow-irregularity-check
description: Vertical irregularity checks — soft story (stiffness), mass irregularity, and CM-CR eccentricity per BNBC 2020 / ASCE 7-05 §12.3.2.
---

# workflow-irregularity-check

Reads `Story Stiffness` and `Centers Of Mass And Rigidity` database tables from ETABS to flag:
- **Soft story** — stiffness K < 0.7×K_above or K < 0.8×avg(3 above); extreme at K < 0.6 / K < 0.7×avg3 (ASCE 7-05 Table 12.3-2 Type 1a/1b)
- **Mass irregularity** — story mass > 1.5× either adjacent story (roof exempt, ASCE 7-05 §12.3.2.2)
- **CM-CR eccentricity** — informational offset between centre of mass and centre of rigidity per diaphragm

## When to use
- Code check for vertical structural irregularities (ASCE 7-05, BNBC 2020 §2.5.5.3)
- Pre-analysis verification before applying accidental eccentricity
- Any building with potential soft stories or uneven mass distribution

## Thresholds

| Check | Irregular | Extreme |
|---|---|---|
| K vs K_above | K < 0.7·K_above | K < 0.6·K_above |
| K vs avg of 3 above | K < 0.8·avg3 | K < 0.7·avg3 |
| Mass ratio | m > 1.5·adjacent | — |

## Verified code

```python
model.SetPresentUnits(6)  # lb_in_F — stiffness in lb/in

LB_PER_IN_TO_KN_PER_M = 4.4482216 / 0.0254 / 1000.0
MASS_TO_TONNE = 4.4482216 / 0.0254 / 1000.0  # lb·s²/in → tonne

case_name = "EX"   # seismic case used for the stiffness table

# ── Helper: read a database table ──────────────────────────────────────────
def read_table(table_name, case=""):
    t = model.DatabaseTables.GetTableForDisplayArray(
        table_name, [], case or "All", 0, [], 0, [])
    fields = list(t[1])
    nr     = t[5]
    data   = list(t[6])
    nc     = len(fields)
    def col(*names):
        for n in names:
            try: return next(i for i, f in enumerate(fields) if f.lower() == n.lower())
            except StopIteration: pass
        return -1
    return fields, nr, nc, data, col

findings = []

# ── 1. Soft-story check ─────────────────────────────────────────────────────
fields, nr, nc, data, col = read_table("Story Stiffness", case_name)
iS  = col("Story")
iKx = col("StiffX", "Stiff X", "Stiffness X")
iKy = col("StiffY", "Stiff Y", "Stiffness Y")
iD  = col("Diaphragm", "Diaph", "DiaphragmName")

if nr > 0 and iS >= 0 and iKx >= 0 and iKy >= 0:
    by_diaph = {}
    for r in range(nr):
        story = data[r*nc+iS]
        diaph = data[r*nc+iD] if iD >= 0 else "-"
        diaph = diaph or "-"
        kx = float(data[r*nc+iKx] or 0)
        ky = float(data[r*nc+iKy] or 0)
        if diaph not in by_diaph:
            by_diaph[diaph] = []
        if not by_diaph[diaph] or by_diaph[diaph][-1][0] != story:
            by_diaph[diaph].append((story, kx, ky))

    for diaph, k_list in by_diaph.items():
        for i, (story, kx, ky) in enumerate(k_list):
            for direction, kv in (("X", kx), ("Y", ky)):
                if kv <= 0:
                    continue
                k_above = k_list[i-1][1 if direction=="X" else 2] if i > 0 else 0
                n3 = min(3, i)
                avg3 = sum(k_list[i-j][1 if direction=="X" else 2] for j in range(1, n3+1)) / n3 if n3 == 3 else 0
                soft = extreme = False
                if k_above > 0:
                    if kv < 0.6 * k_above: extreme = True
                    elif kv < 0.7 * k_above: soft = True
                if avg3 > 0:
                    if kv < 0.7 * avg3: extreme = True
                    elif kv < 0.8 * avg3: soft = True
                if soft or extreme or (i > 0 and not extreme and not soft):
                    findings.append({
                        "check":     "Soft Story",
                        "story":     story,
                        "diaphragm": diaph,
                        "dir":       direction,
                        "K_kNm":     round(kv * LB_PER_IN_TO_KN_PER_M),
                        "K_above_kNm": round(k_above * LB_PER_IN_TO_KN_PER_M) if k_above else None,
                        "ratio_to_above": round(kv/k_above, 3) if k_above else None,
                        "status":    "EXTREME SOFT STORY" if extreme else "SOFT STORY" if soft else "OK",
                    })

# ── 2. Mass irregularity + CM-CR eccentricity ───────────────────────────────
fields, nr, nc, data, col = read_table("Centers Of Mass And Rigidity", case_name)
iS   = col("Story")
iM   = col("MassX", "Mass X")
iXcm = col("XCM", "X CM")
iYcm = col("YCM", "Y CM")
iXcr = col("XCR", "X CR")
iYcr = col("YCR", "Y CR")
iD   = col("Diaphragm", "Diaph")

if nr > 0 and iS >= 0 and iM >= 0:
    story_order = []
    story_mass  = {}
    per_diaph   = []
    seen = set()
    for r in range(nr):
        story = data[r*nc+iS]
        diaph = data[r*nc+iD] if iD >= 0 else "-"
        diaph = diaph or "-"
        if (story, diaph) in seen: continue
        seen.add((story, diaph))
        mass = float(data[r*nc+iM] or 0)
        xcm  = float(data[r*nc+iXcm] or 0) if iXcm >= 0 else 0
        ycm  = float(data[r*nc+iYcm] or 0) if iYcm >= 0 else 0
        xcr  = float(data[r*nc+iXcr] or 0) if iXcr >= 0 else 0
        ycr  = float(data[r*nc+iYcr] or 0) if iYcr >= 0 else 0
        per_diaph.append((story, diaph, mass, abs(xcm-xcr)*25.4/1000, abs(ycm-ycr)*25.4/1000))
        if story not in story_mass:
            story_order.append(story)
            story_mass[story] = 0
        story_mass[story] += mass

    for i, story in enumerate(story_order):
        m = story_mass[story]
        worst_ratio = 0
        adj_worst = None
        for j in (i-1, i+1):
            if j < 0 or j >= len(story_order): continue
            if j == 0: continue  # roof exempt
            adj_m = story_mass[story_order[j]]
            if adj_m > 0 and m/adj_m > worst_ratio:
                worst_ratio = m/adj_m
                adj_worst = story_order[j]
        heavy = (i != 0) and worst_ratio > 1.5
        findings.append({
            "check":        "Mass",
            "story":        story,
            "mass_tonne":   round(m * MASS_TO_TONNE, 1),
            "worst_ratio":  round(worst_ratio, 3) if worst_ratio else None,
            "compared_to":  adj_worst,
            "status":       "(roof — exempt)" if i == 0 else "MASS IRREGULARITY" if heavy else "OK",
        })

    for story, diaph, mass, ex, ey in per_diaph:
        findings.append({
            "check":   "CM-CR Eccentricity",
            "story":   story,
            "diaph":   diaph,
            "ex_m":    round(ex, 3),
            "ey_m":    round(ey, 3),
            "status":  "informational",
        })

flagged = [f for f in findings if "SOFT" in f.get("status","") or "MASS IRREG" in f.get("status","")]
result = {
    "total_findings": len(findings),
    "flagged_count":  len(flagged),
    "flagged":        flagged,
    "all":            findings,
}
```

## Notes
- `Story Stiffness` table is **top→bottom** (index 0 = roof); `i-1` is the story above
- Buildings with multiple rigid diaphragms per story return one row per (Story, Diaphragm) — the code groups by diaphragm to avoid mixing K from different towers
- Mass comparison uses **total story mass** (summed across all diaphragms of that story) — per ASCE 7-05 §12.3.2.2
- Roof mass comparison is exempt per ASCE 7-05 §12.3.2.2 (index 0 in top→bottom order)
- CM-CR eccentricity rows are informational; use them to set accidental eccentricity offsets
