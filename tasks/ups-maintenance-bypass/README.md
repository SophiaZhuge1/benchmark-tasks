# Keep the servers online: UPS cartridge replacement

**Instruction:** Use the bypass to replace the faulty UPS cartridge without interrupting the server, then restore normal power.

The left YAM arm transfers the load to maintenance bypass. The right arm withdraws the amber faulted cartridge, parks it in the amber tray, and seats the blue replacement. After its ready lamp comes on, the left arm returns the switch to normal UPS supply. The green server lamp must remain on for the entire trial. A separate red outage lamp latches even if supply is subsequently restored.

This is a bench-scale, low-voltage training surrogate. The initial cartridge is faulted but still passes utility power; it is not a completely dead supply. The external bypass provides an independent path while the cartridge is physically absent. The slide switch represents a mechanically linked make-before-break selector with a service isolation position. It is not a servicing procedure for a particular commercial UPS.

## What makes the task distinct

Success depends on the trajectory of the power network, not just the final object poses. Removing the cartridge before bypass, or returning to UPS before the replacement is seated and ready, interrupts the load. Removing during contact overlap also violates service isolation even if the server lamp remains on. Leaving the bypass engaged cannot achieve full credit.

Related work checked on 8 November 2026:

- [RoboCurve PR 688](https://github.com/robocurve/benchmark-tasks/pull/688): replacement of the whole battery string containing a failed module; failed module initially already removed. This task instead evaluates live-source transfer, service isolation and latched continuity throughout exchange.
- [DataCenterBench Tier 1](https://robocurve.org/datacenterbench/): includes individual UPS selector, switch and slider actions. Those manipulations overlap; the proposed contribution is their state-dependent use around a cartridge exchange and irreversible outage history. Novelty is not guaranteed by the different prop.
- GitHub PR searches for `UPS`, `bypass` and `power` found no exact bypass-and-exchange match; keyword searches are not an exhaustive novelty proof.
- [Eaton maintenance-bypass explanation](https://www.eaton.com/us/en-us/products/backup-power-ups-surge-it-power-distribution/backup-power-ups/maintenance-bypass-for-ups-redundancy.html) grounds the use of an external path to keep connected equipment running during UPS replacement.

## Setup

Coordinates are metres in the YAM station frame; z heights below are above the table. Both arms use normal parallel grippers. All props are rigid, with enlarged handles.

| Object | Size / pose | Construction |
|---|---|---|
| Cartridge socket | Centre (0.285,-0.025), floor 12 mm high; 112 × 102 mm base | Rigid insulating mock housing; four 29 mm flared guide rails, 94 × 84 mm mouth narrowing to a 70 × 60 mm seat |
| Faulted cartridge | Starts seated in socket | 60 × 50 × 40 mm body, amber face, 28 × 24 × 75 mm handle; mass 120 g |
| Replacement | Centre (0.195,-0.235), floor 12 mm high | Same body and handle, blue face; mass 120 g |
| Service tray | Centre (0.365,-0.235), floor 12 mm high | Amber 86 × 76 × 12 mm platform |
| Bypass selector | Origin (0.245,0.190), 70 mm travel along +x | 118 × 80 × 28 mm housing, white 28 × 24 × 42 mm handle; passive sliding joint |
| Server surrogate | Centre (0.490,0.195), body 220 × 100 × 100 mm | Rigid rack with visible green live-power, red latched-outage, amber bypass and blue replacement-ready lamps |

The socket is vertical to permit repeatable tabletop YAM manipulation; it does not reproduce a commercial rack's horizontal extraction mechanism. Actual rigid contact carries and seats both cartridges. There are no attachments, object teleports or scripted joint targets in the demonstration.

## Electrical model and scoring

The switch's measured translation q controls two ideal contact sets:

- UPS path closed when q ≤ 45 mm.
- External bypass closed when q ≥ 25 mm.
- 25–45 mm is the make-before-break overlap. q > 45 mm isolates the cartridge path.
- A cartridge is seated only within 6 mm in x/y and 4 mm in z of the socket origin, with upright-axis tilt <8° and +x-axis error <10°. Replacement readiness requires 1 s of uninterrupted valid seating.
- The faulted cartridge passes power while seated. The replacement passes power only after readiness qualification. Either a live UPS path or the bypass supplies the server.
- Continuity is sampled every control step, nominally 50 ms. A sampled outage permanently fails the episode; sub-step transients and AC electrical behaviour are outside this model.
- Withdrawal of the old cartridge while the UPS contact is still closed permanently fails the episode, including during overlap.

Scores are 0 after any outage, isolation violation or cartridge origin falling more than 10 mm below the tabletop; otherwise 0.25 after maintenance bypass is established and isolated while the old cartridge remains seated, 0.75 once the replacement is qualified and old cartridge parked, and 1.0 after normal UPS operation is restored with bypass off and both cartridges released for 1 s. Full credit requires q ≤ 8 mm, old-cartridge x/y position within 13 mm of its tray, its z within 4 mm and the same orientation tolerances, plus all sampled robot fingertip points more than 50 mm from both grasp centres. The harness then applies its usual 1 s success hold.

## Run

With the Isaac Lab / yam_arena installation active:

```bash
bash run_brev.sh $PWD/results/ups-demo --mode full --render 640x360
```

Negative controls:

```bash
bash run_brev.sh $PWD/results/ups-outage-control --render 640x360 --mode outage_recovery
bash run_brev.sh $PWD/results/ups-bypass-control --render 640x360 --mode leave_bypass
python -m unittest discover -s . -p 'test_*.py'
```

`no_bypass` exchanges the cartridge without transferring supply; `early_return` restores the UPS path while the socket is empty; `leave_bypass` completes the exchange but leaves the external supply selected; `none` takes no action. `outage_recovery` deliberately removes the old module before bypass, then restores supply; its green live lamp comes back on while the red outage history remains latched and its score remains 0. Expected scores are 0 for unsafe sequences, 0.75 for leaving bypass on, and 0 for no action. Full mode should score 1.0.

Run control cases in separate simulator sessions; one multi-case session crashed during its second trial. `YAM_PYTHON` can override the default Brev Python path. `demokit.py` uses the installed yam_arena embodiment and stores source snapshots, per-step contact/continuity traces, result JSON, setup image and videos. The scripted demonstration observes simulator poses and joint state; it is not a learned policy or Dream-1 result. The task limit is 1,600 steps / 80 seconds at 20 Hz. Reset restores all poses, the switch, qualification timer and sticky failure history. Fixed layout, seed 1, zero jitter.

## Limits and reproduction

Use an isolated extra-low-voltage LED or microcontroller training rig for physical reproduction. Real mains equipment, synchronisation, arcing, thermal behaviour, capacitor discharge and actual battery faults are not simulated. The linked selector abstracts the isolation interlocks of a maintenance trainer. Camera-visible lamps and a continuity latch can reproduce the evaluation without privileged electrical state, with a logger recording any power loss. This simulation does not certify electrical service safety or physical robot clearance.

## Dream-1 evaluation

Dream-1 beta scored **0.0** over 1,600 steps / 80 simulated seconds, terminating at the step limit with no evaluation errors. The switch stayed at normal, the old cartridge remained seated and the replacement stayed on its tray. Server power stayed on, but no maintenance milestone was reached. Evaluation wall time was 408.03 s; mean inference latency was 0.511 s. All three cameras recorded 1,601 frames with zero blank frames.

With `DREAM_API_KEY` already set securely in the environment:

```bash
bash run_dream.sh "$PWD/results/ups-dream"
python prepare_media.py "$PWD/results/ups-dream" "$PWD/results/ups-demo/full"
```

The exporter creates `model_run.mp4`, `demo.mp4`, `setup.png` and `dream_result.json`. Upload the three media files using the repository's `tools/upload_media.py`. Videos are H.264/yuv420p, 1280×480; the original Dream-1 observations are 320×176 per camera. Both model and scripted videos accompany this submission.

See VALIDATION.md, validation.json and dream_result.json for measured results and source hashes.
