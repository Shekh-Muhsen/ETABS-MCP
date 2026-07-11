# Changelog

## [2.1.0] - 2026-07-11

### Added — Load Setup & Combination Skills (from plugin source)

Two new workflow skills derived from the `Form1.Tab.LoadSetup.cs` and `Form1.Tab.ComboEditor.cs` plugin tabs:

- **`workflow-load-patterns-cases`** — Idempotent setup of all standard load patterns and cases: gravity SuperDead patterns (PWL, FF), Live patterns (Live_G, Live_W, LLR), seismic ELF auto patterns EX/EY (ASCE 7-05), wind auto patterns WX/WY (ASCE 7-05), composite cases DL (all Dead+SuperDead) and LLA (all Live), RS function (ASCE 7-05 design spectrum from SDS/SD1/TL), RS cases Spec X / Spec Y, modal Eigen case, and Ev = 0.2·SDS × all Dead patterns. Only creates items not already present.
- **`workflow-load-combinations`** — Full ASCE 7-05 / BNBC 2020 combination library (68 combos) with role mapping (D→DL, L→LLA, Lr→LLR, Ex→EX, Ey→EY, Ev→Ev, Wx→WX, Wy→WY, Sx→Spec X, Sy→Spec Y): SLS gravity (3 combos), SLS wind (8 combos), SLS seismic ELF ±Ev (24 combos), ULS gravity (2), ULS wind (8), ULS seismic RS 100%+30% ±Ev (16), ULS seismic ELF 100%+30% ±Ev (16). Includes helpers for reading, editing, and bulk-adding cases to combos via `RespCombo` API.

### Changed
- Version bumped to 2.1.0.
- README skill table updated with v2.1 load setup section.

---

## [2.0.0] - 2026-07-11

### Added — Code Check Workflow Skills (from plugin source)

Six new workflow skills derived from the CSiNET8PluginMhn plugin source, covering BNBC 2020 / ASCE 7 structural code checks:

- **`workflow-drift-check-bnbc`** — Dual-method inter-story drift check: ETABS `StoryDrifts` API result and independent hand calc `(δᵢ − δ_below) / h` from joint displacements. Applies Cd/I amplification and compares against BNBC 2020 Table 6.2.21 / ASCE 7-05 Table 12.12-1 occupancy-based allowables.
- **`workflow-irregularity-check`** — Vertical irregularity checks from the `Story Stiffness` and `Centers Of Mass And Rigidity` database tables: soft story (K < 0.7·K_above or K < 0.8·avg3; extreme at 0.6/0.7 thresholds), mass irregularity (m > 1.5×adjacent story, roof exempt), and CM-CR eccentricity per diaphragm.
- **`workflow-otm-check`** — Overturning moment hand calculation per BNBC 2020 §2.5.7: reads story heights from the model, computes T = Ct·hn^m, spectral Sa, base shear V = Sa/(R/I)·W, vertical distribution exponent k, story lateral forces Fx, and cumulative OTMx. Foundation OTM = 0.75×base OTM check vs 2/3·M_DL.
- **`workflow-story-forces`** — Reads the `Story Forces` results table (Location = Bottom) for story P, VX, VY, T, MX, MY in kN/kN·m with unit conversion from lb_in_F. Appends foundation OTM = 0.75×MX/MY columns.
- **`workflow-mass-participation`** — Extracts `ModalParticipatingMassRatios` for a selected modal case, reports per-mode periods and UX/UY/UZ/RX/RY/RZ cumulative sums, compares modes defined vs actually run, and flags whether the ASCE 7 / BNBC 2020 90% mass participation requirement is met.
- **`workflow-torsion-check`** — Torsional irregularity check using user-specified edge joint pairs: reads `JointDispl` for each pair, computes δ_max/δ_avg per story, classifies Type 1a (>1.2) / Type 1b (>1.4) per ASCE 7-16 §12.3.2.1, and computes Ax = min(3.0, (δ_max/(1.2·δ_avg))²).

### Changed
- Version bumped to 2.0.0 across `version.py`, `pyproject.toml`, `mcpb/manifest.json`, and `README.md`.
- README skill table updated with new v2.0 skills section.

---

## [1.0.0] - 2026-06-01

### Added
- Initial release: geometry, loads, analysis, results, and design skills.
- BM25 semantic search over 2,458 ETABS API methods.
- BNBC 2020 and IBC 2012 seismic parameter and design equation skills.
- Response-spectrum auto-seismic and RS function skills.
- `etabs-database-tables`, `etabs-errors`, `etabs-results`, `etabs-design` reference skills.
