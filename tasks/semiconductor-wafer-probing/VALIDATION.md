# Recorded validation

8 November 2026. Isaac Lab / yam_arena, two YAM arms, fixed layout and seed 1. These are scripted joint-feedback demonstrations, not Dream-1 trials.

The successful full run scored **1.0**, with `success=true`, at **340 steps / 17.0 simulated seconds**. Evaluation wall time was **91.78 s**. The stage ended at **59.8575 mm**, only **0.1425 mm** from the 60 mm target. Probe lift returned to **0 mm**; both handles were released and final dwell was **1.95 s**. All recorded samples retained an undamaged state; cumulative scrape travel was **0 mm**.

For intervals with more than 0.05 mm observed stage travel, the minimum endpoint probe lift was **39.3557 mm**, well above the 8 mm clearance milestone. This reporting threshold is only used to summarise movement; the scorer accumulates all absolute travel within the contact band without a per-step movement deadband.

Probe contact ended at **3.50 s**. The lift milestone was reached at **3.95 s**. Site B alignment was reached at **10.20 s**. Probe contact resumed at **14.15 s**, and full credit began at **16.05 s**. The harness ended successfully at **17.0 s**.

The recorded video is H.264/yuv420p, 1280 × 480, with top and wrist views; browser playback was checked. The run reported **zero blank frames**. Both arms' worst inverse-kinematics position error was **0.1 mm**, with orientation error rounding to **0.0 degrees**. These are reach diagnostics, not a certification of physical hardware safety or all robot collisions.

The source snapshot hashes in `validation.json (`source-manifest`)` match the task, damage model, labels and manipulation helpers in this package. `validation.json` (`full-result`) contains actual simulator results and `validation.json` (`full-events`) summarises the per-step trace. Video paths are expressed relative to the evaluation output root for blind review; measured values are unchanged.

## Scorer checks

Three additional simulator runs test the failure and partial-credit conditions:

| Trial | Score | Final stage (mm) | Contact travel (mm) | Damaged | Simulated duration |
| --- | ---: | ---: | ---: | --- | ---: |
| Move with probes down | 0.0 | 60.0776 | 60.099449 | Yes | 11.10 s |
| Release probe lift too early | 0.0 | 59.6134 | 58.583306 | Yes | 18.35 s |
| Leave probes raised | 0.75 | 59.8575 | 0 | No | 16.15 s |

Both damaging controls reached B but retained an irreversible failure. Damage first occurred at 2.90 s and 10.40 s respectively. The raised-only control ended with 39.4341 mm probe lift and no contact, so it did not earn full credit. All three reported zero blank frames. Trace assertions passed for every run. Each trial used a fresh simulator process and the same core source hashes as the successful demonstration; per-trial results, event summaries and source manifests are included in `validation.json`.

After recording, only documentation and the `task.json` scores field were updated; the task and scorer code are unchanged. Videos are uploaded separately through the task board; the source tree contains no videos. The successful scripted demonstration and Dream-1 run accompany the submission. All four scripted videos and traces are retained with the evaluation outputs.

Fifteen unit tests pass, covering safe completion, no-action zero credit, irreversible damage, slow incremental drag, reversal without cancellation, lift-and-slide in one sample, lower-and-slide in one sample, boundary interpolation, raised-only partial credit, wrong position, required release, interrupted dwell, damage after success, rail-bound violations and nonfinite-input rejection.

## Scope

One fixed-layout successful demonstration establishes feasibility for this surrogate. It does not establish robustness across layouts, learned-policy capability, production semiconductor handling accuracy or actual silicon damage prediction. The first launch stopped before simulation because the label font lacked T; that was fixed before the recorded successful trial.

## Dream-1 run

A separate Dream-1 beta trial completed 1,200 steps / 60 simulated seconds with score 0.0 and no evaluation errors. Contact damage latched at 22.60 s, with 10.11881 mm cumulative contact travel; the safe-lift milestone was never reached. All three cameras have 1,201 frames and zero blank frames. The run took 342.31 s wall time. Source hashes for the task, scorer and manipulation helpers match the successful scripted run. See `dream_result.json` for the complete sanitized result and media hashes. No model-run success is claimed.
