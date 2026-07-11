# Changelog

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
