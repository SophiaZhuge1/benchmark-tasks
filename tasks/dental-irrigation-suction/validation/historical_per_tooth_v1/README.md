# Dental hygienist assistant: circular tooth rinsing with coordinated suction

> **Revision draft — 12 November 2026; not pushed.** Physical reconstruction and measurement details are in [PHYSICAL_PROTOCOL.md](PHYSICAL_PROTOCOL.md); comment-by-comment changes and evidence status are in [REVISION_NOTES.md](REVISION_NOTES.md). Historical trials and fresh scripted controls are explicitly separated below. The revised instruction has not yet been run through Dream-1. No hardware validation is claimed.

Two YAM arms operate dental instruments on a rigid training phantom: one rinses the highlighted tooth and the other positions an HVE-like suction tip beside the jet. The task measures simultaneous tool coordination, fluid removal and clearance of the working area.

## Why the dental context changes the task

A completed motion alone earns nothing. Each tooth receives a metered water burst, so the robot must arrive on time, aim the irrigator, keep suction effective throughout the burst and prevent retained water from overflowing. Suction must be close enough to collect water but outside the working-area exclusion zone. Moving only the irrigator while leaving suction at the first tooth cannot earn full credit.

The real clinical role motivating the task is irrigation and aspiration of the treatment site. Published dental-assistant guidance describes placing the suction inlet near the aerosol/water source while avoiding soft-tissue suction and interference with the working instrument. The submitted simulation uses a rigid training surrogate and does not establish patient safety.

## Instruction

Rinse each highlighted tooth with circular rinsing motions while keeping the suction tube beside it.

## Positive and negative controls

See [SCENARIOS.md](SCENARIOS.md) for the physical skill, paired interventions, exact expected scores, fresh recorded controls, historical evidence, model-only results and recording commands. `run_scenarios.sh` uses a fresh simulator process per case; `verify_scenarios.py` checks recordings and the intended failure cause. A valid alternative that meets the outcome requirements remains eligible for full credit.

## Run

```bash
bash run_brev.sh ~/yam-eval/dental-chairside-demo --render 640x360 --mode full,point
bash run_brev.sh ~/yam-eval/dental-chairside-debug --no-record --stills 100 --mode full
bash run_dream.sh "$PWD/results/dream"
python3 prepare_media.py "$PWD/results/dream" ~/yam-eval/dental-chairside-demo/full
python3 -m unittest -v test_fluid
```

Use the installed RoboCurve YAM/Isaac Lab Python on Brev, selected by run_brev.sh. For Dream-1, provide DREAM_API_KEY in the environment; the run script never stores it. The media export uses numpy, Pillow and ffmpeg. The runner saves exact source hashes, per-step traces and per-trial result.json. Use `python3 analyze_trace.py OUT/full/trace.json` to inspect measured circular travel and minimum coverage dwell. Recorded trials include a setup image, a three-camera H.264 demo and individual camera videos. The demonstration reads simulator object poses and is not a VLA. Do not label unrecorded debug runs as final media validation.

## Circular coverage

For each five-second rinse, the scripted arm starts at the centre, makes a 3 mm radius inner circle, expands to a 7.5 mm radius outer circle, and returns to the centre. The suction tip stays on the open side, 17 mm laterally from the crown centre, while matching the rinsing tip’s x motion. Its height is 10 mm above the treatment plane. This keeps the two bent instruments from crossing as the irrigator circles the tooth. The sweep uses a mounted-tool offset measured at the start of each tooth; the scorer independently measures the resulting tool pose.

The scorer uses the actual tool pose and jet axis to project an impact onto the crown plane. A centre disk (radius up to 2.5 mm) and eight 45-degree sectors in the 4.5–9.5 mm annulus must each receive at least 0.15 seconds of correctly aimed irrigation. Coverage only accumulates while the timed pump is flowing. Yellow/green markers are training overlays showing this state, not simulated plaque. `--mode point` repeats the old point-rinse behaviour and must fail the new coverage requirement even if it removes all water.

This covers defined regions of the exposed crown top. Circular motion alone does not establish clinical cleaning of every tooth surface: side faces, tight interproximal spaces, the gingival margin, plaque removal and tissue interaction are outside this model.

## Fixed fixture and timing

The geometry and all positions are in task.py and task.json. The phantom has six molar crowns and three incisors on a rigid pink gum model. Three molars on one side are treatment sites. The blue irrigator and white suction instrument begin on separate stands, with enlarged grasp handles and narrow bent tips that keep the grippers apart near the mouth.

The metering pump supplies 0.4 mL/s for five seconds at each site: 16–21, 24–29 and 32–37 seconds after reset. The upcoming/active site is indicated by a yellow lamp. Total supply is 6 mL. A timed external pump substitutes for a clinician's foot pedal. The robot cannot earn credit by simply switching off irrigation. Blue surface levels show pooling; the collection vial shows recovered volume. The reset fixes the initial layout with seed 1 and zero object jitter.

## Scoring

Each completed site earns 0.25 only after all nine coverage regions meet their dwell requirement, plus: at least 1.8 mL delivered to that tooth, at least 1.8 mL recovered from it and no more than 0.10 mL left pooled. Full 1.0 additionally requires all three sites, total loss no more than 0.30 mL, peak per-site pool no more than 0.45 mL, tools retained and tips withdrawn clear of the phantom.

A tip entering the conservative gum guard, tools approaching within 6 mm at their tips, an instrument origin below 5 mm above the table, invalid state, or suction obstructing the working tooth for more than 0.25 seconds makes failure irreversible. These numerical zones and volumes are benchmark choices, not validated clinical limits. The implementation defines exact geometric boundaries. Tool retention uses finger-to-handle proximity (35 mm), not a force sensor. The low-height guard is not a complete detector of every possible drop or bench contact. This task does not certify clearance of every arm and instrument surface.

The proposed physical reconstruction is specified in [PHYSICAL_PROTOCOL.md](PHYSICAL_PROTOCOL.md): pump/valve timing, protected vacuum plumbing, isolated collectors, source-attributed receivers and video/volume measurements for every threshold. It includes explicit calibration gates and records where the simulator may overestimate real suction. This protocol has not been physically commissioned.

## Fluid and hardware fidelity

Tool motion and grasping use rigid-body contact. Water uses a conservative lumped-volume model: supplied volume is accounted for as captured water, remaining pools or loss. Capture is limited by a finite suction capacity and depends on the actual suction tip's position and orientation. The water animation displays this model; it is not a particle or CFD simulation. Surface wetting, splashing, aerosols, tissue deformation, biological contamination and hose drag are not modelled. The visual jaw is a simplified training fixture, not a clinical anatomical replica.

The coupled model is stronger than a final-pose reward but does not establish real suction performance. The 17 unit tests include volume conservation across step sizes, static/off/reversed suction, working-area obstruction, tool retention, withdrawal, sticky failure and invalid inputs.

## Sources

- U.S. Air Force dental-assistant training, "Irrigate and Aspirate the Treatment Site": https://static.e-publishing.af.mil/production/1/af_sg/publication/qtp4y0x1-3/qtp4y0x1-3.pdf
- Mamoun, "Clinical techniques of performing suctioning tasks and of positioning the high volume evacuation (HVE) attachment and inlet when assisting a dentist. A guide for dental assistants: Part 1": https://pubmed.ncbi.nlm.nih.gov/22039690/

## Related-task check

A title scan of the 1,150 PRs retrieved on 8 November 2026 found no dental irrigation/aspiration entry. The suction-related matches concerned suction lifters, an HVAC suction line and pump-valve sequencing. This is a limited duplicate check, not proof of novelty across every benchmark or a guarantee of acceptance.

## Status

Recorded on Brev: circular demo score 1.0 with all 27 coverage regions reached; stationary point-rinse control score 0.0 with only the three centre regions reached. Both recovered all 6.0 mL, confirming that water collection alone does not satisfy the revised task. All 17 unit tests pass. See VALIDATION.md for measurements, output paths and limitations. Dream-1 beta completed 1,200 control steps (60 simulated seconds) with score 0.0, no covered regions and no evaluation errors. Its three cameras recorded 1,201 frames each with zero blank frames. Evaluation wall time was 334.48 s, including an initial wait for model capacity. The historical model instruction began "Clean each". The revised instruction begins "Rinse each" and requires a new model run. Media is uploaded separately to the task board; videos are not committed to this source folder.

Task-board media bundle: `M-MKVTE5` (Dream-1 video, full-score demo and initial setup screenshot).

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
