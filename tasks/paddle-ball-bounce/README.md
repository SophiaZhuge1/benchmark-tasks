# Ping-pong keep-ups: 10 bounces in a row on the bat

Two YAM arms at the station table. The right hand picks a table-tennis bat off its block and holds it red face up; the
left hand takes a 40 mm ball from an egg cup and drops it onto the bat; then the bat must keep the ball bouncing 10 times
in a row, every bounce rising above the red line on the board behind, and the bat's face below the blue line when it
hits. The ball loses about 28 % of its height on a still bat, so every hit has to be timed to add energy and angled to
keep the ball over the blade.

A task file for the `yam_arena` embodiment ([yam-isaac-lab-arena](https://github.com/kairosiann/yam-isaac-lab-arena),
Isaac Lab-Arena 0.3.1).

## Run a trial

Any policy, here Dream-1:

```bash
inspect-robots run --embodiment yam_arena --policy dream \
  -E task=task.py -E object_jitter=0 -E control_hz=20 -E cam_width=320 -E cam_height=176 \
  --instruction "Pick up the bat from its block with your right hand and hold it red face up. Take the ball from the egg cup with your other hand and drop it onto the bat, then keep it bouncing on the bat 10 times in a row without it touching anything else. Every bounce must rise above the red line on the board behind, and the bat must be below the blue line when it hits the ball." \
  --scorer task_score --max-steps 1200 --store-frames --log-dir runs/dream
```

Scripted demo (scores 1.0), the same command through Inspect Robots' CLI with the demo registered as a policy:

```bash
python run_demo.py runs/demo            # 640 x 360; --width 320 --height 176 for Dream-1's size
```

The run prints `task_score` at the end: 1.0 once the tenth qualifying bounce has held for 1 s, and otherwise the tier
the count reached.

**The demo is a scripted reference that reads the poses of visible objects.** Each control step it reads the ball's and
the bat's poses from the simulator (both are in view of every camera) and its own joints, predicts where and when the
ball will next meet the face, and strokes the blade up through that moment on a sine at the bounce rate, tilted to send
the ball back over the centre. It learns from each bounce: the apex sets the stroke's strength, and the outgoing sideways
speed the tilt that the stroke itself adds. A policy gets only the cameras and the joints. `pongdemo.py` holds the demo;
`demokit.py` its arm primitives.

## How it is scored

`bounce_rules.py` is the count, as a state machine fed once per physics step; `pongkit.py` feeds it from PhysX contact
forces (contact views of the ball and of the bat, as Isaac Lab's contact sensor uses), at every physics step:

- A contact with the bat counts as the red face only if every contact point lies on the blade's top face, inside its
  outline, with a normal within 20 degrees of the face's; anything else on the bat (edge, black back, handle) ends the count.
- A qualifying bounce: the ball's bottom is at or below the blue line (0.15 m above the table) when it hits the face, and
  rises above the red line (0.25 m) before its next contact. A contact with the face longer than 0.1 s, a contact with
  anything else (table, mat, board, egg cup, block, either arm), or a bounce that does not qualify ends the count.
- The count starts at the ball's first contact after it leaves the left hand. Score 0 if the ball reaches the bat before
  it is taken by the left hand or while still in it, if the left fingers are within 3 cm of the ball at its first contact,
  if the left hand touches it again before the count ends, or if the bat is not held: from the first hit to the end of the
  count the bat must touch nothing but the ball and the right arm, and its pose in the right gripper's frame must stay
  within 10 mm and 5 degrees of where it was at the first hit. Only the first drop counts: once the count has ended, it
  stays ended.
- 1.0 at 10 qualifying bounces in a row; 0.75 at 7 to 9; 0.5 at 4 to 6; 0.25 at 1 to 3; otherwise 0.

Offline checks of the rules on hand-built contact sequences, no simulator: `python -m unittest test_bounce_rules`.

## Runtime and seeds

- Demo: about 375 steps (18.7 s simulated); the tenth bounce comes about 17.7 s in. About 3 control steps per second of
  wall time on one RTX 4090 (physics at 500 Hz), so about 2 to 3 minutes with start-up.
- A full 1,200-step trial: about 6 to 7 minutes.
- `object_jitter=0` keeps the layout fixed, so no seed is needed.

## Files

- `task.py`: the scene, `score()` and `success()`, and the demo's entry point.
- `bounce_rules.py`, `test_bounce_rules.py`: the count and its tests.
- `pongkit.py`: physics at 500 Hz, and the per-physics-step tracker that reads contacts and feeds the count.
- `pongassets.py`: writes the bat, ball, egg cup, board and block as USD into `assets/`, and the board's ruled face into
  `textures/`, when the task loads.
- `pongdemo.py`, `demokit.py`, `run_demo.py`: the scripted demo.
- `scenekit.py`, `usdkit.py`: helpers for USD bodies and meshes; `steptime.py`: step timing.

## Sources

Every mesh and texture is generated by `pongassets.py` from plain shapes; there are no third-party assets. Sizes come from
real products: an ITTF 40+ 3-star ball (40 mm, 2.7 g; ITTF bounce test 240 to 265 mm from 305 mm), a recreational bat of
the STIGA Apex kind (blade about 157 x 150 mm, 6 mm with rubbers, handle about 100 x 30 x 23 mm, about 160 g), a porcelain
egg cup and a 5 mm foam board.

## Licence

MIT
