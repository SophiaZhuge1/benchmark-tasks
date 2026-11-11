# Tabletop curling: take the shot and save the runaway stone

The left arm slides the blue stone towards the target. Its glancing collision sends the red stone towards the open side edge. The right arm watches the motion, moves down to block red before it falls, then withdraws. All four stones must remain supported on the board.

## Changes from the first version

- Board length increased from **68 cm to 84 cm**. The updated board is **42 cm wide**.
- **Four curling stones**, up from two: blue, red, green and orange. The green and orange stones add obstacles around the scoring area.
- **Two active arms**: a shot with the left arm and an emergency block with the right.
- The side edge has no rail or automatic catcher. The simulation uses real rigid-body contacts; it never teleports a stone or assigns its velocity during play.
- The original ban on touching red has been replaced by a conditional rescue rule. The shooting arm must still release blue before the yellow line.

## Instruction

Slide blue towards the target with the left arm and release before the yellow line; use the right arm to stop red if it heads off the side, then withdraw both arms and leave all four stones on the board.

This is a tabletop curling game with an added cooperative rescue rule. It does not model ice curl or sweeping. The scripted demonstration reads privileged object poses and velocities; it is a feasibility demonstration, not a visual-model evaluation.

## Physical setup

The board spans station coordinates x=0.040–0.880 m and y=-0.070–0.350 m. Its top is 16 mm above the table. Each rigid stone has radius 32 mm, body height 24 mm, mass 100 g and a 34 x 18 x 23 mm handle. The board and stones use static/dynamic friction 0.035 and zero restitution.

| Stone | Initial centre x, y (m) | Role |
|---|---|---|
| Blue | 0.120, 0.040 | Stone launched by the left arm |
| Red | 0.350, -0.005 | Deflected stone that may need rescue |
| Green | 0.510, 0.290 | Additional stone near the target approach |
| Orange | 0.720, 0.060 | Additional stone near the target |

Stone centres start 12 mm above the board. The target is at (0.710, 0.180), with rings of radii 15, 10 and 6.5 cm. The yellow release line is x=0.300. A red stripe near the open side draws attention to the rescue area; it is a visual marking with no collision geometry.

## Rules and scoring

The left arm may touch blue only before its centre crosses the release line. The right arm may not touch blue. Neither arm may directly touch green or orange, and the left arm may not touch red.

The right arm may touch red only after an outward edge threat has been observed and while red's centre is at y <= -0.025 m. A threat requires red moving towards the side faster than 6 cm/s and a friction-only stopping-position estimate beyond the open edge. With observed planar speed `v`, this estimate is `red_y + red_vy * v / (2 * 0.035 * 9.81)`. A paired no-rescue trial checks whether the default shot actually leaves the board.

After all four stones stop for two seconds and both hands are clear:

| Outcome | Score |
|---|---:|
| Legal released shot; blue misses the 10 cm target and no rescue | 0.25 |
| Blue centre within 10 cm of target; no completed rescue | 0.50 |
| Red rescued and all stones retained; blue misses the 10 cm target | 0.75 |
| Blue centre within 10 cm **and** red rescued | **1.00** |

No action scores zero. Any stone centre leaving the board, a forbidden touch, a lift over 12 mm above normal resting height, or tilt over 25 degrees permanently scores zero. A stone can partly overhang during a save, but its centre must remain on the board and it must finish stably supported at board height. Holding red indefinitely does not complete a rescue: both arms must withdraw.

Rest means all linear speeds below 1 cm/s and all angular speeds below 0.15 rad/s. Contact is approximated using sampled finger points within 6 mm of a stone's cylinder or handle. Rules run at 20 Hz; this is not certification of whole-arm collision avoidance, nor of events between samples.

## Run and reproduce

Use a Linux NVIDIA GPU environment with Isaac Sim 6.2, Isaac Lab Arena v0.3.1, the YAM adapter and Inspect Robots. Activate that environment before running. The scene and rule helpers are included in this folder.

```bash
cd tasks/tabletop-curling-rescue
export CUDA_VISIBLE_DEVICES=0  # choose an available GPU
bash run.sh check
bash run.sh demo 0
bash run.sh negative 0
# With DREAM_API_KEY supplied securely through the environment:
bash run.sh dream 0
```

The setup is fixed and seed 0 is used for the reported trials. The successful script takes 10 simulated seconds (26.07 wall seconds on an RTX 4090); the no-rescue control takes 18.7 simulated seconds (44.18 wall seconds). Exact runtime depends on hardware.

The limit is 1,200 control steps, or 60 simulated seconds. The default scripted stroke travels 18 cm in 0.35 s. The rescue uses observed red-stone velocity to predict an intercept point; it does not read the scorer's threat flag. Development runs can override `CURL_STROKE_TIME`.

Outputs include source snapshots, per-step traces, result JSON, setup images and H.264 videos. `replay_trace.py` independently re-evaluates the recorded observations. `collect_results.py RUN_DIRECTORY` gathers the three final modes (`full`, `no_rescue`, `none`) into the package and reruns the rule tests.

## Validation

Final recording results are stored in `validation/status.json`. The recorded demo and paired no-rescue control have been validated; their task-board media upload is pending. Running the commands above generates new recordings. Dream-1 has not been run. This PR remains a draft until its required model video and task-board media upload are complete.

The YAM and simulation helpers are reused from the preceding implementation. This revision changes the board, stones, two-arm script and rules. Recorded trials use the fixed layout at seed 0; they establish feasibility for that trial, not a broad model success rate or real-hardware safety certification.
