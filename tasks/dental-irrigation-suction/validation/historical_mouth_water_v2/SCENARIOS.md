# Mouth-water v2 controls and evidence

The current scorer and fluid model supersede the previous per-tooth collector design. Historical documentation is retained under `validation/historical_per_tooth_v1`; historical result JSONs remain unchanged.

All comparisons use the same pump schedule, seed1, zero jitter and20 Hz. Only the named behaviour changes. 14 model-only comparisons are in [validation/mouth_water_v2/scenario_results.json](validation/mouth_water_v2/scenario_results.json), with source hashes and compressed traces. They prescribe tool coordinates and do not establish robot feasibility or hardware performance.

| Case | Expected score | Intended distinction |
|---|---:|---|
| full / fixed_site |1| Wet coverage plus local aspiration; fixed suction beside a current tooth is legitimate. |
| wrong_place / too_high |0| Same full coverage, inlet cannot reach wet mouth-floor water. |
| point |0| Successful water management but only3/27 covered regions. |
| static / off |0| Suction cannot manage water from the other floor regions in time. |
| late_suction |0| End dry state cannot erase earlier flooding and overflow. |
| no_withdraw / not_retained |0.75| Water/coverage pass but endpoint gates fail. |
| obstruct / obstruct_then_recover |0| Persistent working-area violation. |
| dry_sweep / none |0| No qualifying wet coverage. |

`verify_scenarios.py` checks recorded score, all cameras, trace completeness, source hashes, water balance and intended failure cause. A wrong-place control must still cover27/27, retain/withdraw the tools and avoid unrelated guard failures. A point control must have passing water metrics. The recorded results below passed the automated rollout checks.

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
