# Fit a hand cone into a contracted hand without forcing its fingers

A practice forearm lies palm up on a pillow, strapped in place, its hand clenched in a fist as a resident's contracted
hand is. The robot fits a rigid hand cone into the fist: across the palm, wide end at the little-finger side, every
finger curled round it, the thumb outside. Prying the fingers open is not allowed, and a peak-hold gauge on each
finger's tendon records any attempt.

## Why it matters

Many older people in care homes live with a hand clenched into a fist after a stroke, or with dementia,
Parkinson's disease or long immobility. Left closed, the fingers stiffen for good, the palm sweats and the skin breaks
down, nails dig into the palm, and washing the hand becomes painful. A hand cone held in the fist keeps the palm open,
clean and dry and slows the contracture, so carers fit one every day. A robot that can do it gently, without forcing
the fingers, would help the resident stay comfortable and keep their hand usable for longer, and would free the carer
for the parts of care that need a person.

Nursing assistants (O*NET 31-1131.00, 1,505,900 US workers) "turn or reposition bedridden patients" and "exercise
patients who are comatose, paralyzed, or have restricted mobility"; home health and personal care aides (31-1122.00)
do the same at home. Hand cones and palm rolls are standard positioning devices for residents whose fingers have
contracted into a fist after a stroke or long immobility: they keep the palm open, clean and dry and slow the
contracture.

Fitting one is awkward for exactly the reason the task models. With the wrist straight the contracted flexors are
tight: the fingers cannot be opened far enough for the cone without stretching them hard, which tears skin and soft
tissue and hurts the resident. The way carers do it uses tenodesis: let the wrist bend forward (flex), which slackens
the finger flexor tendons, so the fingers loosen and fall half open by themselves; slide the device into the palm;
then let the wrist come back, and the fingers close round it. One hand must hold the wrist bent against its return
while the other places the cone, and both must stay clear at the end.

The gauges measure that harm: the tension in each finger's flexor tendon, which is what forcing a contracted finger
raises. Measured on the simulated hand with a scripted opening force on all four fingertips (`handcheck.py`):

| | wrist straight | wrist flexed 40° |
|---|---|---|
| fingertips with no force | in the palm, 19-20 mm off its mid-plane | half open by themselves, 53-63 mm |
| flexor tension with no force | 0.9 N | 0.2 N |
| a flexor passes the 5 N gauge limit | at 0.64 N a fingertip, before the fingers reach their open stops | never (at most 1.6 N) |
| fingers pushed to their open stops | 17-18 N in each flexor, 2.6 N a fingertip | 1.6 N in each flexor, 0.4 N a fingertip |

With the wrist straight, the fingers give at first, then the check loops go taut: opening them fully takes three to
four times the gauge limit, and prying passes the limit before they get there. Fitting the cone the right way peaks
at 3.2-4.2 N.

## The real build

Positions in m from the arm bases' midpoint, x forward, y left, heights above the table. Printable meshes of the palm,
the eight finger pieces and the cone are in `stl/` (millimetres; `python export_stl.py` writes them from the same
shapes the simulation uses).

- Pillow: 17 × 34 × 6 cm, firm polyurethane foam (about 35 kg/m³) in a cotton cover, centred at (0.37, 0.10), with
  orange tape L-marks at its corners.
- Forearm: a 50 mm PVC tube in a 5 mm foam sleeve, sand-ballasted to 1.1 kg, palm up along +y, held to the pillow by
  two hook-and-loop straps round the pillow; the wrist axis at (0.37, 0.07).
- Hand (left, palm up), printed in PLA (40% infill), on 3 mm steel pins: palm 9.5 cm from the wrist axis to the
  knuckles, 8.5 cm across the knuckles, 7.0 cm at the wrist, 2.4 cm thick; thumb printed with the palm, adducted along
  the index side.
- Fingers: a proximal phalanx and a middle-distal piece (bent 35° at the DIP) per finger, lengths (mm): index 42 and
  24 + 20, middle 45 and 27 + 22, ring 43 and 26 + 21, little 38 and 21 + 19. Printed stops on the pins limit the MCPs
  to 20-110° and the PIPs to 40-120° of flexion: like a contracted hand, the fingers never straighten.
- Flexor tendon, one per finger: 0.5 mm braided fishing line, tied through the tip of the middle-distal piece, runs in
  1.5 mm channels on the palm side, 8 mm from the MCP pin and 6 mm from the PIP pin, over a 24 mm radius pulley (a
  printed half-disc on the palm side of the wrist pin), into the forearm. There it joins a 60 mm length of 4 mm Shore 40A
  silicone cord (300 N/m), with a loop of the same braided line tied beside it, 15.5 mm slack, through a 6 mm rubber
  bumper (together about 2.5 N/mm once taut): the contracted tissue's end-stop. The cord ends on the hook of a 10 N
  push-pull force gauge with peak hold (for example a Sauter FK 10) screwed to the forearm, one gauge per finger.
  Pre-tension about 1 N with the fist clenched and the wrist straight.
- Extensor cord, one per finger: 2 mm round elastic (300 N/m), anchored on the back of the proximal phalanx, runs in a
  covered 3 mm groove along the back of the hand (8 mm from the MCP pin, 3 mm from the PIP pin), over a 20 mm radius
  pulley on the back of the wrist pin and along a groove in the forearm to an anchor screw. The grooves are covered by
  1 mm printed lids, so the back of the hand lies flat on the pillow and the cords run free. 0.6 N with the fist
  clenched.
- Wrist: pin hinge, flexion 0-85°, stopped at straight (the back of the hand on the pillow); a torsion spring
  (0.04 N·m/rad) returns it.
- Hand cone: rigid, printed PLA (`stl/hand_cone.stl`), 13 cm long, 5.0 cm across at the wide end, 3.0 cm at the narrow
  end, 40 g, the size of a Rolyan or North Coast rigid hand cone. It lies on its side between two 8 × 12 mm wooden rails
  glued 5.6 cm apart on a 10 × 8 × 12 cm plywood box at (0.315, -0.15), wide end towards the robot, overhanging the
  box by 2.5 cm.

## Calibration

- Each flexor's silicone section: hang 2 N on it, the stretch is 6-7 mm (300 N/m); its check loop goes taut at
  15.5 mm and then 2.5 N/mm (hang 5 N: 16.5 mm).
- Every 10 trials: with the wrist straight and the fist clenched each gauge reads 0.8-1.2 N; with the wrist held at
  40° (protractor) every fingertip lifts at least 4 cm off the palm surface by itself. Re-tension a cord that reads outside.

## A real trial and its score

Instruction: "Fit the hand cone into this practice hand: across the palm, wide end at the little-finger side, with all
four fingers curled round it and the thumb outside. Don't force the fingers open. Then let go and move clear."

Scored with a ruler, phone photos from the side and from above, and the four gauges' peak marks. Every score needs,
held for 2 s, both grippers 3 cm clear of the hand and the cone, and the forearm within 2 cm of its tape marks.

| Score | When |
|---|---|
| 1.0 | the cone lies across the palm (resting on it, axis within 25° of the knuckle line, wide end at the little-finger side) with every fingertip resting on its upper half |
| 0.5 | the cone rests in the palm with at least two fingertips on its upper half |
| 0.25 | the cone rests in the palm |
| 0 | any finger's gauge peaked over 5 N; the forearm left its marks by 2 cm at any time; the cone fell below the pillow's top; any other end state, including a gripper within 3 cm |

Reset: lift the cone out by its wide end with the wrist flexed (never pry), let the wrist return, zero the gauges'
peak marks, and check the pillow sits in its marks.

## In simulation

- The hand is rigid parts on pin joints: the palm (with its thumb) on a wrist hinge, and per finger a proximal phalanx
  and a middle-distal piece, with the stops above.
- Every physics step, each flexor's and extensor's stretch is computed from the cord path: the joint angles times
  their moment arms, plus the wrist angle times the pulley radius. The tension follows the cord's rate (and, for a
  flexor past 15.5 mm, the check loop's), zero when slack, and is applied as torques at the finger joints and the
  wrist, with the wrist's return spring. Nothing else moves the hand: the fingers stop only against the palm, the cone
  or a gripper. There are no rule- or timer-driven events.
- Each gauge is that flexor's peak tension over the trial.
- The forearm and pillow are one body on the table; "within its marks" is the pillow's displacement.
- Fingertip on the cone's upper half: within 5 mm of the cone's surface and above its axis, as seen from the palm.
- Silicone skin is not modelled: contacts are rigid, friction 0.8, with a 12 mm torsional patch on the palm so that a
  pinch across the hand can turn it. The thumb is fixed outside the cone.

## Run a trial

Scripted demo (score 1.0):

```bash
TASK_DEMO=success inspect-robots run --embodiment yam_arena --policy yam_scripted -E task=task.py -E object_jitter=0 \
  -E control_hz=20 --instruction "$(python -c 'import json; print(json.load(open("task.json"))["instruction"])')" \
  --scorer task_score --max-steps 1200
```

Any policy, here Dream-1, with the same command and `--policy dream -E cam_width=320 -E cam_height=176`.

The demo is an open-loop script of waypoints from the fixed start (`conedemo.py`): it reads no simulator state.
`TASK_DEMO=force` runs the careless way, the wrist left straight and the cone pressed onto the clenched fist, which
scores 0. `TASK_DEMO=idle` leaves the hand at rest.

The calibration checks above, in simulation: `TASK_DEMO=idle TASK_CHECK=pry` (wrist straight) or `TASK_CHECK=flexed`
(wrist at 40°) with the same command and `--max-steps 340`; they print the fingertip force, joint angles, flexor
tensions and fingertip heights (`handcheck.py`).

Offline tests of the scoring rules (they import `yam_arena`, but need no simulator): `python -m pytest test_cone_rules.py`.

Runtime: the demo reaches its full score at step 432 (21.6 s simulated). On one RTX 4070 Ti SUPER a run stores frames
at about 0.3 s per control step, so a full 1,200-step trial takes about 6 minutes of wall time plus about 30 s of
start-up. The layout is fixed (`object_jitter=0`), so no seed is needed.

## Files

- `task.py`: the scene, the tendon law applied every physics step, `score()` and `success()`.
- `handmodel.py`: the hand's sizes, the tendon force law and the shapes.
- `cone_rules.py`, `test_cone_rules.py`: the scoring rules and their offline tests.
- `conedemo.py`: the scripted demo.
- `handcheck.py`: the calibration checks.
- `export_stl.py`, `stl/`: the printable parts.
- `bodykit.py`, `demokit.py`, `steptime.py`: helpers for multi-shape bodies, demos and step timing.

## Assets

Every mesh, the STL files included, is generated by the code in this folder from plain shapes; there are no
third-party meshes, scans or textures. The robot and the station come with the harness. The STL files are under the
same licence as the code.

## Licence

MIT
