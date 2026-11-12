# Mouth-water v3: finishing controls

All cases share the same scene, water model, rinse path, timing and scoring. They differ only in the named finishing behaviour. The revised scorer preserves the prior water/coverage checks while requiring near-dry cleanup and original-stand return/release for full marks.

| Current case | Expected score | Required evidence |
|---|---:|---|
| full |1.0|27 regions; water gates pass; irrigator lifted while suction stays in mouth; final water<=0.05 mL; both tools correctly parked, released and settled. |
| early_return |0.75|27 regions and general water gates pass; both tools parked/released, but no qualifying post-rinse cleanup. |
| no_return |0.75|Cleanup succeeds and water<=0.05 mL, but both tools remain held away from their stands. |
| no_release |0.75|Cleanup and rack placement succeed but fingers do not release. |

The prior wrong-location and point-rinsing controls still exercise water recovery and coverage. Their older v2 recordings are labelled historical; v3 unit/model tests continue to cover those mechanisms. A crash, unrelated guard failure or lost tool is not evidence for the finishing shortcut being tested.

`verify_scenarios.py` checks full traces, three nonblank cameras, source snapshots and the intended failure cause. Post-rinse cleanup cannot be inferred from a final dry-mouth image or returned tools alone.

## Recorded robot results — 12 November 2026

CPU PhysX with RTX rendering, seed 1, no jitter, 20 Hz; all three native cameras contain no blank frames. Runtime Python source hashes match the reviewed source. Each run covers all 27 regions, peaks at 0.4650 mL retained water, loses 0 mL and passes the mechanical guard.

| Scenario | Score | Duration | Final mouth water | Recovered | Cleanup | Tools returned/released |
|---|---:|---:|---:|---:|---|---|
| Complete sequence | 1.00 | 50.35 s | 0.0027 mL | 5.9973 mL | Yes | Both |
| Return before clearance | 0.75 | 47.20 s | 0.2222 mL | 5.7778 mL | No | Both |
| Clear mouth but omit return | 0.75 | 48.40 s | 0.0027 mL | 5.9973 mL | Yes | Neither |

In the successful run, the near-dry cleanup condition first latches at 43.15 s; full reward is awarded only after original-stand placement, release and the 1 s settled hold. The no_release case has unit coverage but has not been recorded as a robot rollout. These are scripted simulations, not Dream-1 or real-water results. Detailed evidence and source/video hashes: `validation/mouth_water_v3/recorded_results_20261112.json`.
