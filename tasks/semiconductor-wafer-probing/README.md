# Semiconductor wafer probing: move without scratching

**Instruction:** Move the semiconductor wafer to the next marked test position without dragging the probes across its surface.

A semiconductor wafer is already clamped to a sliding chuck, with two probes at test site A. The left YAM arm raises and holds the amber probe assembly; the right arm moves the blue stage handle to B. Once the stage has stopped and aligned, the probes must be lowered onto B and both handles released. Lateral probe contact permanently damages the trial, even if the robot subsequently reaches the correct final pose.

This is an enlarged probe-station trainer, representing the lift–index–contact sequence. It does not claim that ordinary YAM grippers can position production probes at micron resolution. The spring-return lift is a training fixture that requires one arm to maintain clearance while the other indexes the stage.

## Context and related tasks

[Inseto's Probe Station Basics](https://www.inseto.com/wp-content/uploads/2020/04/IKB051_PROBE_STATION_BASICS.pdf) describes raising the platen after testing one device, moving the wafer stage to the next device, and positioning the probes again. This task abstracts that coordination and surface-protection requirement.

GitHub searches on 8 November 2026 found seven wafer-related PRs and twelve probe-related PRs. Related wafer tasks covered coating, lift-off rinsing, cassette transfer, carrier loading, mask exchange, tape mounting and airlock transfer. [PR 114](https://github.com/robocurve/benchmark-tasks/pull/114) clamps a chip carrier under a spring clip with pin-1 alignment. Here the wafer starts clamped; the action is stage indexing under delicate probes, with irreversible damage from lateral contact. No exact lift–index–recontact match was found in those searches; this is not an exhaustive novelty guarantee.

## Fixed setup

Coordinates are metres in the YAM station frame; vertical dimensions are relative to the table. Seed 1, no object jitter. Props are rigid and the wafer is permanently attached to the moving chuck, representing a vacuum-clamped wafer. Both robot arms retain their standard parallel grippers.

| Part | Dimensions and starting pose | Material surrogate |
|---|---|---|
| Stage base | 280 × 208 × 12 mm; centre (0.310, −0.055), bottom on table | Aluminium |
| Moving carriage | 180 × 180 × 20 mm; centre (0.280, −0.055), bottom 15 mm above table; 0–70 mm X travel | Rigid polymer |
| Chuck | Diameter 174 mm, height 16 mm, centre 43 mm above table | Aluminium |
| Wafer | Diameter 164 mm, thickness 2 mm; top 52 mm above table | Purple rigid polymer representing silicon |
| Sites A and B | Two 12 × 12 mm pads per site; local x = +30 mm (A), −30 mm (B), y = ±18 mm; 60 mm site spacing | Gold-coloured markings |
| Stage handle | 28 × 24 × 74 mm; centre (0.280, −0.205), 68 mm above table; nominal grasp at 80 mm | Blue polymer on a metal support |
| Probe tips | Two 5 mm diameter, 40 mm long blunt pins, at x = 0.310 and y = −0.073 / −0.037; initial lower tip height 52.2 mm | Brass-coloured rigid surrogate |
| Probe platen | 60 mm vertical travel; 0.10 kg, 25 N/m return spring, 1 N·s/m damping, 0.02 N joint friction | Metal beam on a linear guide |
| Probe handle | 28 × 24 × 56 mm; centre (0.245, 0.140), 119 mm above table; nominal grasp at 125 mm | Amber polymer |
| Status panel | 205 × 100 × 45 mm; centre (0.485, 0.180); four labelled 18 mm lamps | Rigid polymer |

The stage has no return spring, 1 N joint friction and 3 N·s/m damping. Both slides move through gripper contact; neither the scene nor the scripted policy teleports objects or commands fixture joint targets. The wafer and probes are enlarged for visible, repeatable tabletop manipulation.

## Scoring and damage history

The control rate is 20 Hz. Let **x** be stage displacement from A, and **z** be probe lift from its initial position.

- Probe contact band: z ≤ 0.8 mm. Safe lift milestone: z ≥ 8 mm continuously for 0.25 s.
- Next test site B: x = 60 mm, with ±2 mm placement tolerance.
- Cumulative lateral travel while in the contact band exceeding **0.2 mm** permanently sets damage and score zero. This small tolerance accommodates numerical and fixture measurement noise; slow increments and reversals accumulate rather than cancel.
- If a control interval crosses the contact-band boundary, its lateral displacement is weighted by the fraction of the linearly interpolated interval in contact. Lifting and translating in the same control interval therefore cannot evade detection simply by ending above the wafer. Unobserved motion within a sample is outside the model.
- Stage outside −2 to 72 mm, or lift outside −2 to 62 mm, also fails the trial as a fixture-bound violation.
- **0.25:** safe lift milestone reached, with no damage.
- **0.75:** safe lift milestone reached, stage currently within 2 mm of B and probes currently at least 8 mm clear, with no damage.
- **1.0:** probes returned to the contact band at B, stage sampled speed ≤1 mm/s, and sampled fingertip points more than 50 mm from both handle grasp centres, continuously for 1 s. The harness adds its normal 1 s success hold.

There is no credit for merely leaving the initial assembly untouched. Reaching B after a scrape remains zero. Reaching B with probes left raised remains partial credit. Full-credit conditions are checked continuously and can be lost if the stage moves again before termination.

The blue **LIFT** lamp shows clearance ≥8 mm. Amber **PAD** shows the contact band. Red **FAIL** latches damage or a fixture violation. Green **READY** shows completed alignment, contact and release.

## Run

Use the Isaac Lab / yam_arena Python environment. `YAM_PYTHON` overrides the default installation path in `run_brev.sh`.

```bash
bash run_brev.sh "$PWD/results/safe" --mode full --render 640x360
bash run_brev.sh "$PWD/results/drag" --mode drag --render 640x360
bash run_brev.sh "$PWD/results/early-release" --mode early_release --render 640x360
bash run_brev.sh "$PWD/results/raised" --mode leave_lifted --render 640x360
python -m unittest discover -s . -p 'test_*.py'
```

Run each mode in a separate simulator process. `full` performs safe indexing and recontact; `drag` moves without lifting; `early_release` lifts but lets the probes return before indexing; `leave_lifted` indexes successfully but omits final recontact; `none` takes no action. The declared episode limit is 1,200 steps / 60 simulated seconds.

The recorder writes source snapshots, per-step traces, result JSON, setup PNG and H.264 videos with top and wrist views. The scripted controller uses simulator joint positions and robot feedback, so it is not a learned-policy result. See `VALIDATION.md` for runs actually completed and their measured runtime.

## Physical reproduction and limits

Use a sacrificial coated polymer wafer and blunt low-force probes on an unpowered tabletop trainer. A contact indicator plus a stage scale or displacement logger can measure motion while probes touch; an irreversible mark on a sacrificial coating can provide additional evidence. The 0.2 mm travel tolerance requires suitable displacement resolution and a recorded contact history, not just an end-of-trial photograph.

The simulation models rigid contacts, joint positions and geometric proximity. It does not simulate electrical measurements, contact resistance, probe scrubbing, compliant needles, microscopic damage, silicon fracture, contamination or production cleanroom operations. [Actual wafer-probing equipment](https://www.formfactor.com/blog/2022/removing-probing-debris-from-springs-dram-flash-applications/) may intentionally use controlled microscopic scrub to establish contact; this trainer penalises macroscopic lateral indexing with probes engaged. The model is sampled, not a continuous-time collision certificate.

## Dream-1 evaluation

Dream-1 beta scored **0.0** over **1,200 steps / 60 simulated seconds**, ending at the step limit with no evaluation errors. It moved the stage without first lifting the probes. Damage latched at **22.60 s**, with **10.11881 mm** cumulative contact travel by the end. The wafer did not reach B; final stage displacement was 0.0094 mm and probe lift was 0 mm. Evaluation wall time was **342.31 s**, with **0.511 s** mean inference latency. All three cameras recorded **1,201 frames**, with zero blank frames.

With `DREAM_API_KEY` set securely in the environment:

```bash
bash run_dream.sh "$PWD/results/wafer-dream"
python prepare_media.py "$PWD/results/wafer-dream" "$PWD/results/safe/full"
```

The exporter creates `model_run.mp4`, `demo.mp4`, `setup.png` and `dream_result.json`. Upload the three media files with the repository's `tools/upload_media.py`. Videos are H.264/yuv420p at 1280 × 480; Dream-1 observations are 320 × 176 per camera. The setup image is the initial Dream-1 frame. The source and scoring hashes match the successful scripted demo. See `dream_result.json`, `validation.json` and `VALIDATION.md` for measured results and provenance.
