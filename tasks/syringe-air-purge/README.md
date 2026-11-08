# Purge the bubble, preserve the sample

**Status: the full scripted task passed with score 1.0 on Brev (seed 1). This is simulation feasibility evidence, not hardware validation. See [VALIDATION.md](VALIDATION.md).**

A YAM pair lifts a needle-free laboratory syringe, raises its outlet so an air pocket migrates toward it, advances the plunger with the other arm, and returns the syringe to its rack. This is a laboratory manipulation prototype, not a medical procedure or a clinical validation.

## Run

Use the existing IsaacLab-Arena Python environment with `yam_arena` installed:

```bash
bash run_brev.sh /home/ubuntu/yam-eval/syringe-air-purge --mode full
python check_physics_model.py
python check_seal.py
```

Use `--mode none`, `--mode horizontal`, or `--mode overpush` for negative controls. Each starts from the same layout (seed 1, object jitter 0). Limit: 1,800 actions at 20 Hz, or 90 simulated seconds. `demokit.py` writes `result.json`, a three-camera `demo.mp4`, individual camera videos and `setup.png`. Runtime depends on the GPU; inspect `wall_s` in the result rather than treating simulation time as wall time.

## Setup and physical model

All dimensions are metres in `task.py`; table top is 0.7475 m. The syringe starts with its local +Y axis horizontal and outlet toward the left arm. Its barrel origin is (0.25, 0, 0.8875). The transparent barrel is 88 mm long and 18.6 mm in outside diameter, with a 15 mm bore, a 19 mm needle-free outlet, a finger flange and a blue 35 × 8 × 30 mm thumb plate. The 85 mm plunger stem is on a free prismatic joint with physical contact and friction. Two 150 mm-high white saddle supports stand on a blue base; the barrel rests 140 mm above the table. A white catch tray stands beside it. Every model is procedural; no texture downloads are required.

The syringe is a floating articulation: the robot must hold it. Object poses, the plunger position and arm movements come from PhysX, without attachment-to-gripper tricks. The rendering of the contents comes from `fluid.py`, a volume-conserving **reduced-order model**, not a fluid solver. Initial contents are 10.5 mL sample and 1.5 mL air. The original coalesced air pocket moves along the barrel under the axial component of gravity; any newly aspirated air is tracked separately at the outlet, so a small retraction cannot move the trapped pocket there instantly. The measured piston displacement expels the phase at the outlet; retracting the piston admits air. Air and sample inventories are independently conserved.

This approximation omits bubble breakup, capillary pinning, fluid viscosity and radial fluid motion. The passive seal uses an elastic/sliding approximation: a 10,000 N/m joint spring with force capped at 0.6 N, a rest point that slips only to limit stored strain, and 10 N·s/m damping. It does not lock the piston on task success or prescribe its displacement. Rest-point updates only remove elastic energy; forces remain bounded in both directions. Seal parameters and axial bubble-rise speed are illustrative, not measurements from a particular syringe. A bubble is drawn as a simplified indicator, not a quantitatively accurate interface. Those limitations matter for transfer to hardware; the current artifact is a prototype.

## Scoring

Score is evaluated at the end after the syringe has been lifted above its initial rack, returned with its axis with axis components |z| < 0.15 and y > 0.985 relative to the original +Y direction, within 25 mm of its start XY position and between 125 and 155 mm above the tabletop, stopped below 25 mm/s, and the fingers withdrawn at least 65 mm from the grasp and thumb-plate locations.

- 1.0: at most 0.05 mL air remains and sample loss is at most 0.30 mL.
- 0.6: at most 0.30 mL air remains and sample loss is at most 0.50 mL.
- 0.3: at most 0.75 mL air remains and sample loss is at most 0.50 mL.
- 0 otherwise. Dropping the syringe, losing over 0.50 mL sample or drawing in over 0.20 mL air permanently invalidates the episode.

The reference controller reads geometric state to grasp and advance the piston. The floating articulation uses eight velocity solver iterations to reduce numerical drift. It is a feasibility demonstration, not a vision-policy result. Dream-1 has not been run. Validation results are recorded separately; do not treat a playable video as proof of a full score.

## Novelty check

On 7 November 2026, the 981-listing RoboCurve board was checked along with targeted public benchmark searches. No exact air-purge task was found. Nearby existing tasks include syringe-pump loading (TK-RDGQZY) and needle safety-guard closure (TK-NCHKZQ). The proposed distinction is orientation-dependent phase migration plus coordinated piston control while preserving sample. Novelty and acceptance are not guaranteed.

A broader follow-up search on 8 November found **robotic syringe air removal already described in [US5366896A](https://patents.google.com/patent/US5366896A/en)**: a robot brings a syringe to an air-removal fixture, regrips the plunger and advances it upward, with vacuum assisting removal. [Brooks Guidance Dispense](https://www2.brooksautomation.com/Guidance_Dispense/GD_Software_Introduction/gdsi_cfg_purge.htm) also documents automated dispenser purging, a related but different operation. This task must therefore be presented as a possible benchmark formulation of an established operation, not a newly invented robotic capability. The proposed distinction is two free arms coordinating orientation and piston travel, without a dedicated air-removal fixture.

See `ATTRIBUTION.md` for the shared scene/demo infrastructure.

## Submission status

This draft contains the validated scripted task. The required Dream-1 run and task-board media upload are pending. The empty `media` field is intentional until the official upload succeeds. Do not substitute a scripted or no-action video for the model run.
