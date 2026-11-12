# Validation: mouth-water v2

35 unit/evidence-harness tests and14 water-model comparisons pass locally. See `validation/mouth_water_v2/scenario_results.json` for exact model outcomes, traces and source hashes. Three recorded robot scenarios passed automated evidence checks; see the current results below. Earlier per-tooth records are historical and must not be combined with this new scorer.

Hardware testing remains outstanding: near-surface capture, peak water measurement, real drainage/crossflow, hose drag and collision-free reach. No patient experiment is proposed.

## Recorded robot results: mouth-water v2

Three fresh CPU-PhysX / RTX-rendered scripted trials, seed1, zero jitter, 20 Hz. These are robot rollouts, not the prescribed-coordinate model comparisons.

| Approach | Score | Regions covered | Peak total mouth water (mL) | Final mouth water (mL) | Recovered (mL) | Lost (mL) |
|---|---:|---:|---:|---:|---:|---:|
| Correct rinse and local suction |1.0|27/27|0.4650|0.2222|5.7778|0.0000|
| Suction at the wrong location |0.0|27/27|2.8960|2.8131|0.0000|3.1870|
| Point rinse with working suction |0.0|3/27|0.8883|0.3569|5.6431|0.0000|

All three retained and withdrew both tools, with no guard failure. The wrong-place run isolates failed water recovery despite complete coverage. The point-rinse run passes the water gates but misses the outer crown regions. Reported per-cell capture counters describe the location of aspiration, not which tooth originally supplied mixed water.

Three synchronized native640x360 views at20 fps and full source/metric traces are retained. Review labels are added after recording; they are not policy inputs. Old per-tooth runs and initial development failures are not evidence for the revised positive result. Current instruction and runtime sources are frozen in each run; final explanatory documents are updated afterward. Fresh Dream-1 and hardware trials remain pending.

[Current recorded evidence and source/video hashes](validation/mouth_water_v2/recorded_results_20261112.json). Initial, active-rinse and endpoint frames were inspected in all three camera views.
