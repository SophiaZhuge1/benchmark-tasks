# Dental hygienist assistant: rinse teeth and evacuate mouth water

**Current revision: mouth-water v2, 12 November 2026.** Category: Societal relevance.

> Rinse each highlighted tooth and suction the runoff from inside the mouth without letting water accumulate.

This represents the rinse-and-evacuate stage after professional air polishing during dental prophylaxis, using a rigid training phantom. A water-only dental syringe surrogate rinses three crown tops; the other arm holds an evacuation tip in the wet mouth-floor region. This does not perform polishing or plaque removal.

## What changed

Water now visibly leaves the irrigator, hits the tooth, runs into three connected mouth-floor pools and moves into the suction inlet **only when the model actually removes it**. Pool depth tracks retained volume. The receiver rises with recovered volume. High or misplaced suction cannot collect water remotely. All water on crowns and in the mouth contributes to a single total and a persistent whole-trial peak.

The scripted demonstration uses simulator pose feedback to correct suction-inlet position through arm actions; it is not a learned vision-policy result.

The flow animation is driven by a conservative reduced-order water model, not CFD. The current physical reconstruction and its remaining limitations are in [PHYSICAL_PROTOCOL.md](PHYSICAL_PROTOCOL.md). The previous per-tooth pool design is superseded.

## Clear scoring

| Check | Requirement |
|---|---|
| Peak water inside mouth | <=1.00 mL **total**, throughout the trial |
| Water left inside mouth | <=0.50 mL at endpoint |
| Recovered | >=90% of supplied volume (>=5.40 mL for nominal6 mL) |
| Spill/loss | <=0.30 mL |
| Each rinsed tooth | >=1.8 mL delivered, with >=0.15 s wet dwell in its centre and each of eight outer sectors |

Any water-gate or permanent guard failure scores0. Otherwise, zero/one/two/three completed teeth earn0/0.25/0.50/0.75. Three teeth plus both tools held and withdrawn for1 s earn1.0. Exact region boundaries, tool guards, physical measurement procedures and uncertainty rules are in the protocol. These are benchmark thresholds for an inert fixture, not patient-safety limits.

The same fixed pump schedule applies in every case:0.4 mL/s during16-21,24-29,32-37 s. Setup may finish before16 s, explaining the initial wait. Dry movement earns no coverage. Limit1,200 actions/60 s at20 Hz, seed1 and zero jitter.

## Positive and negative controls

- `full`: sweep all27 regions and keep suction at the wet mouth-floor region; expected1.
- `wrong_place`: identical rinse, suction beside the opposite dry side of the fixture; expected0 from retained water/overflow, not a missed grasp.
- `too_high`: identical rinse, inlet raised above the pool; expected0.
- `point`: suction works but rinse hits only crown centres; expected0 from incomplete coverage.
- `late_suction`: rinse first and remove water later; expected0 because peak water and loss persist.
- `no_withdraw`: otherwise successful, no withdrawal; expected0.75.

See [SCENARIOS.md](SCENARIOS.md) for measured outcomes and evidence levels.

## Run

```bash
python -m unittest -v test_fluid test_mouth_water test_evidence
python scenario_checks.py --output validation/mouth_water_v2/scenario_results.json
export YAM_PYTHON=/path/to/yam-environment/bin/python
bash run_scenarios.sh /new/output/root full wrong_place point
```

The recording harness saves overhead and both wrist views, initial image, full metric trace and frozen source files. Never count a runtime crash or missed grasp as a clean negative control. Verify source hashes and inspect the images.

## Evidence status

35 tests and14 prescribed-coordinate water-model comparisons pass. The three recorded robot controls below passed automated evidence checks; visual review is complete. Earlier per-tooth videos, Dream-1 results and `recorded_results_20261112.json` are historical and do not validate this new scorer. No new media has been uploaded or PR pushed. Hardware construction/calibration and a fresh Dream-1 trial remain outstanding.

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
