# PR1160: post-rinse clearance and equipment return

Revised submission, 12 November 2026. The owner's requested final sequence is now part of the controller and full-score definition:

- Lift the rinsing tool after the final tooth while suction remains inside the mouth.
- Scan all mouth-floor pools; target<=0.005 mL in the demo, full-score threshold<=0.05 mL.
- Require>=1 s of in-mouth suction after the rinsing tip lifts, after the final pump pulse.
- Return each tool to its original stand, release both grippers and settle for1 s.
- Preserve0.75 partial credit for complete rinsing/general water management when this new finishing sequence is incomplete.

New pure finishing-sequence and rack-state checks guard against early withdrawal, a dry initial state, wrong stand, held tool, motion and tipped placement. The water transport, pump schedule, peak/loss limits and clinical scope remain unchanged. The new recorded comparisons are full, early_return and no_return. Earlier v2 full-score footage is historical and cannot demonstrate this new endpoint.

## Recorded robot results — 12 November 2026

CPU PhysX with RTX rendering, seed 1, no jitter, 20 Hz; all three native cameras contain no blank frames. Runtime Python source hashes match the reviewed source. Each run covers all 27 regions, peaks at 0.4650 mL retained water, loses 0 mL and passes the mechanical guard.

| Scenario | Score | Duration | Final mouth water | Recovered | Cleanup | Tools returned/released |
|---|---:|---:|---:|---:|---|---|
| Complete sequence | 1.00 | 50.35 s | 0.0027 mL | 5.9973 mL | Yes | Both |
| Return before clearance | 0.75 | 47.20 s | 0.2222 mL | 5.7778 mL | No | Both |
| Clear mouth but omit return | 0.75 | 48.40 s | 0.0027 mL | 5.9973 mL | Yes | Neither |

In the successful run, the near-dry cleanup condition first latches at 43.15 s; full reward is awarded only after original-stand placement, release and the 1 s settled hold. The no_release case has unit coverage but has not been recorded as a robot rollout. These are scripted simulations, not Dream-1 or real-water results. Detailed evidence and source/video hashes: `validation/mouth_water_v3/recorded_results_20261112.json`.

## Independent review iteration — 12 November 2026

Added reviewer-visible physical setup/metrology and explicit occupational/procedure scope. Corrected the raw-score timeout edge: a complete endpoint must hold continuously1 s before score1.0, not merely before early termination. Source now reports endpoint_hold_s. A reset, interruption or invalid timing clears the hold; this is covered by offline checks. The latest scorer needs fresh robot/model evidence; earlier recordings remain preserved. No push or publication.

## Current v4 held-endpoint recording — 12 November 2026

The corrected scorer completes the full scripted sequence at **1008/1200 steps,50.40 s,score1.0**, leaving0.0027 mL, recovering5.9973 mL, peaking at0.4650 mL, with no spill. Both tools return and release. All three640x360 camera streams have zero blank frames. Raw score remains0.75 at step1007 with0.95 s hold and becomes1.0 at step1008 with1.00 s hold. Fifty-one offline tests pass. Current task.py hash: `4e1c014efffee6276c4c58b7da8aea57d6f264e3f19c85e41a1ed4d2ef40dc34`.

Both recordings use CPU PhysX and RTX rendering, seed1, zero jitter and20 Hz; these are scripted runs, not Dream-1 or physical experiments. Complete traces, source snapshots and three-camera footage are retained. Source bytes were independently checked against the separate pre-run run_config hashes. The automatically generated manifest mistakenly hashed its own preceding version; its original and original failed verification were preserved, that self-entry was removed with a correction note, and all remaining source hashes and evidence checks pass. No source/score was changed to repair packaging. The current Dream-1 run subsequently completed with score0.0; see validation/current_dream_20261112.json. Current official media are identified in task.json.


## Final model evidence — 12 November2026

Authentic Dream-1 beta run completed at the declared step limit, score0.0, without evaluation error. Exact current instruction and all Python source hashes match the reviewed implementation. Six evenly spaced model and demo frame composites and full decoding of all three model camera videos were checked. Current model result/provenance: `validation/current_dream_20261112.json`. Full-score scripted evidence is unchanged. Current media are identified in task.json.
