# Positive, negative and adversarial scenarios

## What the task measures

Aim a flowing rinse across nine defined crown-top regions at **each of three teeth**, while positioning suction to remove the water during the fixed pump windows. The skill is timed coverage and concurrent water removal with two held tools, followed by withdrawal. Recovering the total water alone is insufficient; drawing circles without flowing water is insufficient; recovering water after it has overflowed cannot undo the loss.

The model does **not** require the suction tool to copy every irrigator motion. It can stay still at a suitable position beside the currently active tooth. Moving it to the next tooth before that tooth's pulse is sufficient. The valid `fixed_site` alternative is deliberately retained: it prevents us from mistaking a different efficient solution for cheating. The scorer also accepts any correctly aimed wet trajectory that covers the specified regions for the required dwell; it does not require a particular clockwise order or exact circular path.

## Exact common conditions

Fresh simulator process per case; seed 1; zero jitter; 20 Hz; 1,200 steps maximum. The same three sites, tool geometry, initial poses, instruction, pump timing and scoring code apply to every case. Supply is 0.4 mL/s over [16,21), [24,29), [32,37) s, nominally 2 mL per tooth and 6 mL total. Controllers move the tools through arm actions; they never set volume, coverage, object pose or reward.

Centre radius<=2.5 mm and eight sectors in the 4.5-9.5 mm annulus each need >=0.15 s of active, correctly aimed flow. Delivered>=1.8 mL, collected>=1.8 mL and final pool<=0.10 mL complete a site. Full score also requires loss<=0.30 mL, peak pool<=0.45 mL, tool retention and withdrawal. See [PHYSICAL_PROTOCOL.md](PHYSICAL_PROTOCOL.md) for all position/orientation/clearance conditions and measurement procedures.

## Paired comparisons

| Case / controller mode | Deliberate change | Required score | Evidence needed to isolate the reason |
|---|---|---:|---|
| Positive `full` | Centre/inner/outer sweeps at each tooth; nearby suction during each pulse; withdraw. | 1.0 | 27/27 covered regions, >=1.8 mL captured/site, loss/peak within limits, tools retained and withdrawn, no guard failure. |
| Valid alternative `fixed_site` | Suction holds still beside each tooth throughout its rinse, then moves to the next tooth. Irrigator still sweeps. | 1.0 | Same success metrics. Within-tooth following is not essential under the present model and must not be claimed. |
| Collection-only shortcut `point` | Keep the wet jet at each crown centre; maintain correct suction. | 0 | Recover all 6 mL and satisfy endpoint/guard checks but cover only 3/27 regions. This is the strongest coverage-specific negative. |
| Leave suction behind `static` | Suction remains at the first tooth for all three pulses; irrigator still visits all regions. | 0.25 | 27/27 coverage but only the first tooth recovers >=1.8 mL. Partial credit is intentional, not a scoring leak. |
| Sequential-cleanup shortcut `late_suction` | Perform all three rinses on time with suction held away; only after all pulses, visit the three pools with suction. | 0 | Still deliver 6 mL and cover 27/27; overflow/loss and insufficient per-site recovery prevent success. Late cleanup cannot restore lost water. |
| No local suction `off` | Pick up both tools, but leave suction away from the teeth throughout rinsing. | 0 | Coverage can pass; collection/pooling must fail. |
| Omit withdrawal `no_withdraw` | Perform the full rinsing/recovery sequence but leave tips at the last tooth. | 0.75 | 27/27 and volume thresholds pass, tools remain held, but `clear=false`. Preserve earned site credit. |
| Block the working area `obstruct` | Put suction at the active crown centre, 7 mm above its plane, during the pulse. | 0 | Persistent working-area/clearance failure. Check trace/video; a missed grasp or runtime error is not this control. |
| No-action baseline `none` | No actions throughout the full 60 s; scheduled water still runs. | 0 | No qualifying wet coverage or recovery. |

## Fresh recorded controls — 12 November 2026

| Recorded approach | Score | Covered regions | Captured by site (mL) | Lost (mL) | Peak pool (mL) | Steps |
|---|---:|---:|---|---:|---:|---:|
| `full` | 1.0 | 27/27 | [2.0, 2.0, 2.0] | 0.0 | 0.0 | 783 |
| `point` | 0.0 | 3/27 | [2.0, 2.0, 2.0] | 0.0 | 0.0 | 832 |
| `late_suction` | 0.0 | 27/27 | [0.45, 0.45, 0.45] | 4.65 | 0.47 | 994 |

All three runs retained and withdrew both tools without a guard failure. Point rinsing recovers the water but misses the outer regions. Delayed suction covers the regions but cannot recover overflowed water. These controls separately isolate coverage and concurrent local recovery.

Fresh processes, seed 1, zero jitter, identical scene/scoring and 20 Hz control. Each trial has a complete trace, exact source snapshot, initial image and three nonblank camera streams. Automated evidence checks and full composite-video decoding passed. These are **scripted rigid-body simulations with reduced-order fluid models**, not Dream-1 or hardware trials. [Recorded results and source/media hashes](validation/recorded_results_20261112.json). Current review copies show all three native 640x360 camera views at 20 fps, with a clock and pump-window labels. They are exported from these same validated recordings; no timing or physics changed.

The exact physics/controller sources are frozen in each run. This documentation and the score-summary metadata were updated afterward; the recorded manifest correctly preserves the earlier document versions.

## Other evidence

**Historical recorded rigid-body simulations (8 November, previous source snapshot):** positive full=1.0 with 27/27 regions, point-rinse=0.0 with 3/27 regions. Both recovered all 6 mL. This isolates why water recovery alone is insufficient. These are historical runs, not recordings of the newly expanded controller.

**New water-model comparisons (12 November):** [validation/scenario_results.json](validation/scenario_results.json) contains measured outcomes, assumptions, source hashes and compressed per-step traces for 12 cases:

| Model-only case | Score | Key observed model result |
|---|---:|---|
| Full | 1.0 | All 27 regions and all 6 mL recovered. |
| Fixed suction beside each active tooth | 1.0 | Same success; validates the simpler legitimate policy. |
| Point rinse | 0.0 | 6 mL recovered, only 3/27 regions. |
| Suction at first tooth only | 0.25 | Only one site completes. |
| Suction away | 0.0 | No qualifying per-site recovery. |
| Rinse first, suction afterward | 0.0 | 27/27 regions and 6 mL delivered, but only 0.45 mL/site remains recoverable; 4.65 mL lost. |
| Do not withdraw | 0.75 | Three sites complete; endpoint clearance gate supplied false. |
| Do not retain tools | 0.75 | Three sites complete; endpoint retention gate supplied false. |
| Obstruct throughout | 0.0 | Persistent obstruction failure. |
| Obstruct for 0.35 s, then recover correctly | 0.0 | Final coverage still 27/27; prior violation cannot be erased. |
| Sweep before flow, then move away | 0.0 | No covered regions; dry motion earns no dwell. |
| No action | 0.0 | No covered regions. |

These prescribed-coordinate tests exercise the real water/scoring code but **do not simulate robot contacts, feasible motions or real suction**. The endpoint flags are test inputs. Their instantaneous site transitions are not a robot policy. Report them separately from PhysX rollouts and physical trials.

## Reproduce and record

```bash
python scenario_checks.py --output validation/scenario_results.json
python -m unittest -v test_fluid

export YAM_PYTHON=/path/to/yam-environment/bin/python
bash run_scenarios.sh /new/output/root full point static late_suction
# Additional alternative and controls:
bash run_scenarios.sh /another/new/output/root fixed_site no_withdraw off obstruct none
```

Each mode runs in a fresh process and writes source hashes, complete trace, numeric result, H.264 videos and initial screenshot. The runner refuses to overwrite existing evidence. `verify_scenarios.py` rejects missing/blank recordings, incomplete traces, source mismatch, wrong scores and important confounds: for example, a point-control failure caused by losing the suction tool rather than missing coverage is not a clean coverage comparison. Camera validity is now checked per camera, not only by whether any one view is nonblank.

Report per-site delivered/captured/pool volumes, peak pool, total loss, coverage/dwell, guard failures, retained/clear flags, steps and source snapshot for every comparison. Inspect video at initial state, during each pulse and at the endpoint. Retain failed positives and unexpected negative successes and investigate them. Single-seed demonstrations establish fixed-scene examples, not a general success rate or proof against every exploit.

## Physical reconstruction and limits

[PHYSICAL_PROTOCOL.md](PHYSICAL_PROTOCOL.md) specifies materials/dimensions, isolated collectors, pump/valve timing, protected vacuum source, hose and receiver arrangement, wet-jet video annotation, source attribution, carryover, peak pooling, loss and clearances. [MEASUREMENT_SHEET.csv](MEASUREMENT_SHEET.csv) records all 27 dwell measurements and uncertainty intervals.

Real water capture at the simulated elevated suction pose remains a hardware feasibility question. Unit tests cannot establish it. Do not describe this task as plaque removal, cleaning every anatomical surface, or validated clinical use. Category remains **Societal relevance**.
