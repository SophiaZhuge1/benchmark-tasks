# Circular crown-rinsing validation — 8 November 2026

> **Revision draft — 12 November 2026; not pushed.** Physical reconstruction and measurement details are in [PHYSICAL_PROTOCOL.md](PHYSICAL_PROTOCOL.md); comment-by-comment changes and evidence status are in [REVISION_NOTES.md](REVISION_NOTES.md). Historical trials and fresh scripted controls are explicitly separated below. The revised instruction has not yet been run through Dream-1. No hardware validation is claimed.

## What changed

The irrigator now performs a centre dwell, a 3 mm inner circle, a 7.5 mm outer circle and a return to centre at each of the three target molars. The suction tip follows the x motion from the open side of the tooth. Tool movement remains driven by the YAM arms through rigid contact grasps.

Coverage is measured from the actual irrigator pose and projected jet impact, independently of the scripted path. Each tooth has a centre region and eight surrounding sectors; every region needs at least 0.15 s of active irrigation. A stationary point rinse cannot pass by collecting water alone.

## Automated checks

`python3 -m unittest -q test_fluid`: all 17 tests passed. The tests cover water accounting, time-step independence, suction location/orientation and obstruction, withdrawal and retention, sticky failures, invalid state, all 27 coverage regions, dry movement, insufficient dwell, angular wraparound, and the point-rinse negative control. Python compilation passed for the changed modules.

## Physical simulation debug run

Output: `/home/ubuntu/yam-eval/circular-v2/full` on Brev. Fixed layout, seed 1, no object jitter. This debug run does not record video.

- Score 1.0; success true; 783 steps / 39.15 simulated seconds.
- All three teeth: 9/9 covered regions; minimum region dwell 0.30 s.
- Supplied 6.0 mL; delivered and recovered 2.0 mL per tooth; zero modelled loss or remaining pools; zero water-balance error.
- Tools retained and withdrawn; no sticky clearance/obstruction failure.
- Worst IK residual: 0.1 mm / 0.0 degrees for each arm.
- Wall time 203.33 s.

Measured outer-pass angular travel from the rounded actual tip trace was 354.6, 353.7 and 352.3 degrees respectively. The commanded outer path is 360 degrees; finite sampling and tracking lag make the sampled angular extent slightly smaller. Coverage in every sector still exceeded the required dwell. `analyze_trace.py` reproduces these measurements; stored tip positions have 0.1 mm resolution.

## Recorded simulation

Output: `/home/ubuntu/yam-eval/circular-final`, rendered at 640x360 for each camera.

The recorded `full` trial scored 1.0 with success true, 783 steps / 39.15 simulated seconds, 210.96 s wall time and zero blank frames. All 27 regions passed with minimum dwell 0.30 s, all 6.0 mL were captured, and loss/pools/balance error were zero. Both tools were retained and withdrawn, no sticky failure occurred, and worst IK residual was 0.1 mm / 0.0 degrees per arm. This agrees with the debug run.

The recorded `point` negative-control trial scored 0.0, success false, after 832 steps / 41.60 simulated seconds (223.94 s wall time). It recovered all 6.0 mL, left no pools or loss, retained/withdrew both tools, triggered no sticky guard failure, and had zero blank frames. It covered only 1/9 regions on each tooth (the centre), so the missing circular coverage alone prevented success. Worst IK residual was 0.1 mm / 0.0 degrees per arm.

The full-demo video is H.264/yuv420p, 1280x480, 784 frames and 39.20 s. The recorded demo used the same scene, scorer and controller; only the task instruction was subsequently shortened for the Dream-1 trial. The run folders retain their exact source snapshots.

## Scope and evidence

This establishes coverage of the defined exposed crown-top regions in this fixed simulation. It does not establish cleaning of all anatomical tooth surfaces, plaque removal, clinical safety, or performance across varied resets. Water is a conservative lumped model, not CFD. Clearance checks cover specified tip/working-area guards; they do not certify every arm or instrument surface.

An earlier trial in `circular-v1` failed when suction also orbited the crown. That trial prompted the open-side suction path; it is preserved and is not used as success evidence. Prior point-rinse implementation results do not validate this revised task.

The demonstration uses simulator object poses. The model policy receives camera observations and robot state through Inspect Robots. Recorded videos and raw traces remain in the Brev output folders and media is uploaded separately to the task board.

## Dream-1 beta

Output: `/home/ubuntu/yam-eval/dental-dream-circular`. Exact instruction: "Clean each highlighted tooth with circular rinsing motions while keeping the suction tube beside it."

- Model: dreamlabs/dream-1-beta; seed 1; zero object jitter; 20 Hz; cameras 320x176; rows per request 20.
- Completed all 1,200 control steps / 60 simulated seconds; termination `max_steps`; zero errored trials.
- Score 0.0. Final coverage [0,0,0]; supplied 6.0 mL, delivered/captured 0.0 mL, lost 6.0 mL. Tools were not retained. The model moved the arms but did not establish the required tool grasps or tooth coverage.
- Evaluation wall time 334.48 s, including initial model-capacity waiting; mean inference latency approximately 0.50 s.
- Each of three cameras contains 1,201 frames with zero blank frames. The H.264 model video contains the initial frame plus all control steps and is 4,859,347 bytes.
- Scripted demo: 3,377,833 bytes; setup image: 230,377 bytes. The setup image is composed from the model's initial camera frames.

`prepare_media.py` exports the saved frames and writes `dream_result.json`, including measured outcomes and source/media hashes. No credentials are included in the result summary.

Task-board media bundle: `M-MKVTE5` (Dream-1 video, full-score demo and initial setup screenshot).

## Additional scenario checks — 12 November 2026

See [SCENARIOS.md](SCENARIOS.md) and [machine-readable results](validation/scenario_results.json). These are newly executed reduced-order-model checks, separate from the historical recorded rigid-body trials above. Fresh recorded controller rollouts are reported below. No model-only result is represented as robot or hardware evidence.

## Fresh recorded controls — 12 November 2026

| Recorded approach | Score | Covered regions | Captured by site (mL) | Lost (mL) | Peak pool (mL) | Steps |
|---|---:|---:|---|---:|---:|---:|
| `full` | 1.0 | 27/27 | [2.0, 2.0, 2.0] | 0.0 | 0.0 | 783 |
| `point` | 0.0 | 3/27 | [2.0, 2.0, 2.0] | 0.0 | 0.0 | 832 |
| `late_suction` | 0.0 | 27/27 | [0.45, 0.45, 0.45] | 4.65 | 0.47 | 994 |

All three runs retained and withdrew both tools without a guard failure. Point rinsing recovers the water but misses the outer regions. Delayed suction covers the regions but cannot recover overflowed water. These controls separately isolate coverage and concurrent local recovery.

Fresh processes, seed 1, zero jitter, identical scene/scoring and 20 Hz control. Each trial has a complete trace, exact source snapshot, initial image and three nonblank camera streams. Automated evidence checks and full composite-video decoding passed. These are **scripted rigid-body simulations with reduced-order fluid models**, not Dream-1 or hardware trials. [Recorded results and source/media hashes](validation/recorded_results_20261112.json). Current review copies show all three native 640x360 camera views at 20 fps, with a clock and pump-window labels. They are exported from these same validated recordings; no timing or physics changed.

The exact physics/controller sources are frozen in each run. This documentation and the score-summary metadata were updated afterward; the recorded manifest correctly preserves the earlier document versions.

[Three-view export checks and video hashes](validation/three_view_review_20261112.json). All three exports decode and have exactly steps+1 frames.
