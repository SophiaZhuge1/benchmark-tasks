# Measured validation

Date: 8 November 2026. Isaac Lab / yam_arena station, bimanual YAM, seed 1, zero object jitter. Scripted pose-feedback policy, not Dream-1.

The final successful recorded trial is `results/ups-v5/full`. It scored **1.0**, with **success=true**, after **705 control steps / 35.25 simulated seconds**. Measured simulation wall time was 177.23 s. All 705 recorded control samples had power, with zero accumulated outage, no isolation violation and no dropped cartridge. The replacement was seated at 25.70 s and ready at 26.65 s. At termination the switch was 1.35 mm from its normal stop, the old cartridge was parked and both grippers were clear. Final replacement origin: (0.2860,-0.0248,0.7595) m. Both arms' worst inverse-kinematics position error was 0.1 mm, and reported orientation error rounded to 0.0 degrees.

The `full-result` entry in `validation.json` is the simulator's actual result, and its `full-events` entry is the transition summary produced by `analyze_trace.py`. The analyzer also asserted that every recorded sample retained power and that final placement, readiness, release and selector conditions held.

The successful demo is H.264/yuv420p, 1280×480, with the top view and both wrist views. Browser playback was checked. The recorder reported zero blank frames. The complete per-step trace and video are retained with the evaluation output. The core source hashes were compared against both simulator snapshot manifests and matched exactly. The `source-hashes` entry in `validation.json` identify the task, electrical model, labels and manipulation helpers used for the recorded trials.

The scoring model passed 13 unit tests: normal starting supply, continuous switch overlap, successful exchange, irreversible outage history, isolation during overlap, early return, readiness qualification, contact-loss reset, bypass left on, old module not parked, fingers not clear, post-success outage and invalid input rejection.

## Controls

The recorded outage-recovery control at `results/ups-controls/outage_recovery` scored **0.0**, after 429 steps / 21.45 simulated seconds. It removed the cartridge without bypass, lost power for 11.8 s, then restored power by engaging bypass. The final server power state was true, but the outage and isolation failure remained latched. Zero blank frames were reported.

The multi-case simulator session subsequently crashed during the `leave_bypass` trial. That unfinished trial is excluded. The fresh-session rerun at `results/ups-bypass-control/leave_bypass` completed with **0.75**, after **653 steps / 32.65 simulated seconds**, 160.66 s wall time and zero blank frames. It left the switch at 67.97 mm, with the replacement seated and ready, the old cartridge parked and the server powered with zero outage. Its score correctly remained below full credit. The no-action physical case was not run; no-action scoring is covered by the model tests.

## Scope

This validates one fixed-layout scripted demonstration and the listed controls. The single model run below does not establish general learned-policy performance or randomised-layout reliability, electrical safety or collision certification on real hardware. The electrical logic is idealised and sampled at 20 Hz; transients between samples are not measured. Early prototype failures led to flared socket guides, taller handles, staged insertion and lower travel heights. Those failed prototypes are not the submitted full-score demonstration.

The archived result video paths are expressed relative to the evaluation output root for blind review. All measured values are unchanged.

## Dream-1 beta

One trial used the same core scene and scorer, seed 1, zero jitter, 20 Hz and 20 action rows per inference request. Score **0.0**, 1,600 steps / 80 s, termination `max_steps`, zero errored trials. Wall time 408.03 s and mean inference latency 0.511 s. Final state: switch 0 mm, old cartridge seated, replacement not seated, zero outage and no unsafe removal. No maintenance milestone was achieved. Three cameras each retained 1,601 frames, with zero blank frames. `dream_result.json` records the actual metrics and media hashes. The task/scorer/helper hashes match the scripted demonstration exactly; task.json was subsequently updated only to describe results and reference uploaded media.
