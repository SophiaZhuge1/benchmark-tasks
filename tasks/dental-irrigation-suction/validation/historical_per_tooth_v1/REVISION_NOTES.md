# PR #1160 — revision preview

Prepared 12 November 2026. **Local draft only; no push or reviewer reply sent.**

Review: [RoboCurve comment on PR #1160](https://github.com/robocurve/benchmark-tasks/pull/1160#issuecomment-6820119118), posted 12 November at 09:40 UTC. The stated unmet criteria are **scoring** and **clarity and reproducibility**. The issue is the lack of a reconstructable real-water rig and practical observations for the existing numeric thresholds. The reviewer also requests rinsing wording and a more appropriate category.

| Review request | Prepared change | Evidence limit |
|---|---|---|
| Physical pump and timing controls | Pump 11 Elite, syringe/hoses, 24 mL/min, timed outlet valve, visible reset LED and three five-second windows. | Outlet flow and delays require commissioning; command timing alone is not evidence. |
| Suction source and plumbing | Protected KNF N 838 gas-vacuum circuit, regulator, filter, traps, tubing dimensions, overhead slack support and carryover calibration. | Rated gas flow does not establish real water capture at the simulated tip height. |
| Phantom regions/materials/dimensions | Dimensioned acetal crown/rail fixture and three isolated transparent annular collectors. | Added wet collectors/plumbing are a physical proposal, not shown in the existing simulation. |
| Each region's irrigation dwell | Calibrated wet-jet video, exact centre/annulus/sector boundaries, actual timestamps and uncertainty bounds. | A circular motion or dry tool movement does not establish coverage. |
| Per-site collection | Source-attributed graduated receivers, line-clearance accounting and separate unassigned receiver. | Routing by schedule alone is invalid; ambiguous recovery remains uncredited/uncertain. |
| Peak pooling, loss and clearances | Empirical macro pool calibration, whole-trial peak, endpoint drainage/film check, complete water ledger and exact geometric guards. | One final vial or final dry tooth is insufficient; occlusions can make a result unverified. |
| Rinsing rather than plaque removal | Changed instruction to "Rinse" and narrowed the context to crown-top rinsing and water handling. | No plaque-removal, all-surfaces-cleaning or clinical validation claims. |
| Category | `Impact on jobs` -> **`Societal relevance`**. | Matches the reviewer's societal-relatability framing using the repository's permitted category name. |

## Resulting title and instruction

Title: **Dental hygienist assistant: circular tooth rinsing with coordinated suction**.

> Rinse each highlighted tooth with circular rinsing motions while keeping the suction tube beside it.

`task.py`, `task.json` and the current README instruction match. The archived Dream-1 result used "Clean each ..." and is labelled historical; a new run is needed for the revised exact prompt. The title retains "Dental hygienist" as requested previously.

## Changed files

- `PHYSICAL_PROTOCOL.md`: build specification, water/pump/vacuum commissioning, site attribution, all numeric measurements and limits.
- `MEASUREMENT_SHEET.csv`: blank measurement/evidence/uncertainty record including all 27 dwell values.
- `task.py`: instruction wording and additional scripted positive/negative controller modes; scoring/scene unchanged.
- `task.json`: instruction, category, context, physical setup/scoring summaries, fidelity and evidence status. Also corrected the low-origin prose to "at or below 5 mm", matching the existing code.
- `README.md`, `VALIDATION.md`: reconstruction links and historical-result notices.
- `REVISION_NOTES.md`: this review mapping.

Scene geometry, water dynamics and scoring thresholds remain unchanged. The demo controller now includes explicit adversarial scenarios; the recording harness checks every camera and initial-frame validity. See SCENARIOS.md for the new controls and their evidence status. Existing animations show the same simulated motions. The revision supplies a physical reconstruction proposal, not footage of a built wet rig.

## Validation performed locally

- `python -m unittest -v test_fluid`: **17 tests passed**, including dry/point rinse, insufficient dwell, water conservation, static/reversed suction, obstruction, retention and withdrawal.
- Static checks: task JSON parses; instruction equals code; fidelity text is below 500 characters; changed Python parses; changes remain confined to this task folder.

Detailed local check record: [LOCAL_CHECKS.txt](LOCAL_CHECKS.txt).

Fresh recorded scripted trials completed on Chrysler in isolated RoboCurve output directories. Existing jobs and the separate physical-verification project were left untouched. Compatible Arena/Isaac Lab sources were selected per process without changing shared installed packages. The initial version-mismatch startup failures are retained separately and are not counted as negative results.

## Additional adversarial revision

[SCENARIOS.md](SCENARIOS.md) now specifies paired comparisons, expected partial credit, legitimate alternatives and evidence limitations. New `scenario_checks.py` results and compressed traces are stored under `validation/`. The demo controls use arm actions only. `run_scenarios.sh` isolates episodes and `verify_scenarios.py` rejects crashes, missing/blank media and unintended failure causes.

## Before resubmission

1. Run Dream-1 with the final "Rinse" sentence and preserve its actual score, instruction and source hashes.
2. After owner review, upload the new demonstration/control recordings with the refreshed Dream-1 run and replace the official media reference. Current task-board media IDs still point to the historical bundle.
3. Review this draft with the owner before pushing to the **existing** `submit-dental-circular-rinsing` branch / PR #1160. Do not open a replacement PR.

The written requests are covered in the draft. The main remaining physical uncertainty is suction performance at the elevated simulated tip pose; if the bench rig cannot reproduce it, geometry/fluid changes and a fresh full-score demo will be necessary. The protocol makes that falsifiable instead of assuming the numerical suction curve is real.

## Fresh recorded controls — 12 November 2026

| Recorded approach | Score | Covered regions | Captured by site (mL) | Lost (mL) | Peak pool (mL) | Steps |
|---|---:|---:|---|---:|---:|---:|
| `full` | 1.0 | 27/27 | [2.0, 2.0, 2.0] | 0.0 | 0.0 | 783 |
| `point` | 0.0 | 3/27 | [2.0, 2.0, 2.0] | 0.0 | 0.0 | 832 |
| `late_suction` | 0.0 | 27/27 | [0.45, 0.45, 0.45] | 4.65 | 0.47 | 994 |

All three runs retained and withdrew both tools without a guard failure. Point rinsing recovers the water but misses the outer regions. Delayed suction covers the regions but cannot recover overflowed water. These controls separately isolate coverage and concurrent local recovery.

Fresh processes, seed 1, zero jitter, identical scene/scoring and 20 Hz control. Each trial has a complete trace, exact source snapshot, initial image and three nonblank camera streams. Automated evidence checks and full composite-video decoding passed. These are **scripted rigid-body simulations with reduced-order fluid models**, not Dream-1 or hardware trials. [Recorded results and source/media hashes](validation/recorded_results_20261112.json). Current review copies show all three native 640x360 camera views at 20 fps, with a clock and pump-window labels. They are exported from these same validated recordings; no timing or physics changed.

The exact physics/controller sources are frozen in each run. This documentation and the score-summary metadata were updated afterward; the recorded manifest correctly preserves the earlier document versions.

## Why the demo waits before the first tooth

The pump starts at t=16 s after reset, then at t=24 s and t=32 s, for 5 s per tooth. Pickup/alignment can finish before t=16; the controller then waits for the scheduled outlet flow. This is preparation time, not cleaning dwell or a stalled robot. Dry sweeping earns no coverage. The schedule is independent of robot readiness and remains the same in the positive and negative trials. Three-view review exports retain this interval and label the pump phase so that waiting is explicit.
