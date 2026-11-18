# Take out the trash: cinch and remove a loaded drawstring liner

> Pull both drawstrings to close the full bag, lift it out of the bin by the drawstrings, and set it down upright on the table beside the bin without spilling any contents.

**Category:** Societal relatability. Taking out a small kitchen or bathroom bin by pulling its drawstring liner shut and lifting it out is something almost everyone does at home and recognises in a 10-second clip.

A small round bin (an IKEA NYPON 15 cm pot) holds an ordinary, unmodified **simplehuman Code A drawstring liner**, its surplus folded over the rim the usual way, loaded with three light mock-waste blocks (70 x 100 x 45 mm, 50 g each). The two arms pinch the liner's two drawstring loops where they lie on the mat beside the bin, pull them so the folded surplus slides up over the rim and the string slides out of the hem and gathers the mouth, lift the loaded bag out by the strings, set it down upright on the table beside the bin and let go. This is the closure the liner is sold with: pull the drawstrings, then carry by the drawstrings. There is no knot, cord lock, clip or added handle.

## What changed in this revision (review of PR #2134)

| Review point | Change |
|---|---|
| Custom cord-lock liner and added handles were not an established method | Replaced by a standard commercially available drawstring liner (simplehuman Code A) used exactly as supplied, with its ordinary closure. Cord-lock housings, their one-way holding force and the polymer handles are gone from scene, physics and protocol. |
| Locks and handles removed the normal difficulty of securing an ordinary liner | **Partly addressed.** The cord locks and their one-way force are gone; closure now depends only on keeping string tension (`drawstring_physics.py`, `test_drawstring_physics.py`), and the real trial uses the liner's unmodified loop with no handle. In simulation each loop's pinch point is still a 2 g rigid body, because a stable simulated string is not available; this makes the simulated grasp easier than the real one (listed under Fidelity). |
| Threading, cord pairing and assembly unverified | Nothing is assembled. The bin is chosen so the liner verifiably fits: the NYPON pot's 53.7 cm rim is smaller than the liner's 58 cm mouth, so the surplus folds over the rim as people normally fit a liner. The simulation starts in that folded state with the loops lying at the cut-outs, matching [PHYSICAL_PROTOCOL.md](PHYSICAL_PROTOCOL.md), which also gives sources, reset, a hand preflight of liner and closure, and ruler/video scoring. |
| Update simulation, scoring and fidelity note | Folded-cuff liner mesh, thin pot, a load of three 70 x 100 x 45 mm blocks, tiered scorer (`drawstring_score.py`, `test_drawstring_score.py`) with a two-cap containment check (`test_containment.py`), rewritten fidelity table. |
| New full-score demo and Dream-1 run | New scripted demo on the official environment below. Dream-1 was run on the official environment; it errored before the step limit (see Results). |
| Runtime | The task now runs on the official Isaac Lab-Arena release/0.3.1 environment with the installed YAM adapter as is; the earlier compatibility overlay is only applied if a newer Arena API is detected. |

The closure threshold went from 60 mm to 80 mm together with the larger blocks: a block's smallest face (70 x 45 mm) has an 83 mm diagonal, so no block can pass through an opening at the 80 mm limit.

## Scoring

| Score | Outcome |
|---|---|
| 0 | Never cinched to 80 mm or less, any block leaves the bag (latched), bag destroyed, or invalid simulation geometry. |
| 0.25 | Cinched: opening reached 80 mm or less (smaller than the 83 mm diagonal of a block's 70 x 45 mm smallest face) with all three blocks inside. |
| 0.5 | Carried: after cinching, the opening is at most 80 mm when the whole bag and its contents first clear the bin rim by 20 mm. |
| 0.75 | Set down: at the end the bag rests upright on the table (mouth at least 150 mm above it), clear of the bin and table edges by 20 mm, opening at most 80 mm, contents inside. |
| 1.0 | Released: that state, opening included, holds for the final 2 s with both grippers at least 60 mm from film and loops and the bag still (bounds move at most 10 mm). |

Highest satisfied level counts. Containment is checked at every step; the opening is checked at rim clearance and over the final 2 s, so it may widen (to about 107 mm in the demos) while the bag swings in transit. Regrasps and corrections are allowed. Run limit: 4,000 control steps at 20 Hz (200 s); requested CLI seed 0 (the installed adapter reports environment seed 42); no object jitter. `DrawstringJudge` runs live at every control step for both the scripted demo and Dream-1, and `evaluate_removal.py` / `replay_run.py` re-score recorded geometry offline.

## Running

The official environment: Python 3.12 with Isaac Lab-Arena release/0.3.1 (`c7edf3a`), Isaac Sim 6.1.0, Isaac Lab 17.0.2 and Inspect Robots, as in [runtime_versions.json](runtime_versions.json); YAM adapter `kairosiann/yam-isaac-lab-arena` at `0059d02a1a91bc6834c1d0846022891df0c78730`, used as installed. `launch.py` puts the adapter on the path directly; only if it detects a newer Arena API (`Embodiment.registry_name`, no `GroundPlane`) does it build the `.runtime/` overlay from `prepare_runtime.py`. From this directory:

```bash
/path/to/env/bin/python launch.py setup --adapter /path/to/yam-adapter --arena-root /path/to/IsaacLab-Arena --out runs/setup_001
/path/to/env/bin/python launch.py demo  --adapter /path/to/yam-adapter --arena-root /path/to/IsaacLab-Arena --out runs/demo_001
/path/to/env/bin/python launch.py model --adapter /path/to/yam-adapter --arena-root /path/to/IsaacLab-Arena --out runs/dream_001   # needs Dream credentials (~/.dreamlabs/credentials)
python replay_run.py runs/demo_001 --out runs/demo_001/independent_replay.json
python -m unittest discover -v
```

The scripted demo is a closed-loop controller that reads simulator state (loop positions, bag mesh) to aim its grasps and choose its set-down height, as the rules allow; it never sets object poses. Robot and gripper use the adapter's standard settings. The model run gives Dream-1 the standard top and wrist cameras at 320 x 176; the overview camera is diagnostic only. Encode the scripted recording with `ffmpeg -framerate 5 -pattern_type glob -i 'runs/demo_001/frames/*.png' -c:v libx264 -pix_fmt yuv420p demo.mp4`.

## Results

All runs below are the scripted controller on the same task source; there is no tuning between them.

| Run | Result |
|---|---|
| Scripted demo, official environment (`FB_ol1`, the media demo) | **task_score 1.0** (tier `released`), 1,197 control steps / 59.85 simulated s, 957 s wall time. Cinched to 80 mm or less at step 372, carried clear of the bin from step 546, set down upright and released; final opening 71.7 mm, mouth 0.253 m above the table, grippers 0.212 m away, bag bounds moved 0.9 mm over the last 2 s, peak film edge stretch 1.284. Independent replay of all recorded states: 1.0. |
| Repeat, official environment (`FB_ol2`) | 0.5 (`carried`): set down upright beside the bin, but the mouth sprang open to 80.15 mm at release, just above the 80 mm limit. |
| Earlier runs of the same source on an Arena main build (`3b0f10c`, Isaac Sim 6.2, with the compatibility overlay) | `FB_t3` 1.0 and `FB_t4` 1.0 (both independent replays 1.0); `FB_t1` and `FB_t2` 0.5, the mouth reopening to 96 mm and 81 mm at release. |
| Summary | **1.0 in 3 of 6 runs across two environments; the failure mode is the mouth springing open to about 80 mm at release.** GPU physics is not bit-for-bit repeatable, and the scripted controller is not a reliability claim. |
| Opening while carried | In both official-environment runs the opening first met 80 mm with the load clear of the bin, then widened to up to about 107 mm for a few seconds while the bag swung in transit, with all blocks inside. Containment is checked every step; the opening is checked at rim clearance and in the final 2 s. |
| Dream-1 (official environment, 320 x 176 cameras, one session) | **Errored at step 1,427 of 4,000**: the harness's Dream bridge rejected a model reply whose gripper value (-0.071) was outside 0..1, so the harness recorded no score; the session was not lost. The live judge stood at 0.0 at that point (the opening never reached 80 mm; 194 mm). `model_run.mp4` shows the 1,427 steps played. |

The scripted demo only shows the scene and scorer can be completed; no physical trial has been run. Run records and a summary are in [VALIDATION.json](VALIDATION.json).

## Fidelity

PhysX surface-deformable film (not calibrated) authored in the fitted state, folded over the rim, with a slight crease kept at the fold and loose pleats in the hanging surplus; rigid blocks; standard robot actuation (the adapter's own gripper force) and contact grasps; no robot-object attachment and no scripted object poses after reset. Each exposed loop is represented by a small rigid body at its pinch point (14 x 10 x 20 mm, 2 g) joined to the hem by the force-only string; this is the main remaining simplification. The string force is capped at 0.7 N (about twice the static load per strand) as a numerical safeguard; with the rigid loop bodies, higher caps pull a loop body out of the contact grasp. Block containment allows 8 mm on block centres and face centres (film contact offset, film pressed in under load) and 20 mm on block corners, which can protrude through a film triangle (mesh edges up to 20 mm) between its nodes. The string inside the hem is a lumped routed-length spring acting on 20 hem markers and the loop chains' ends; string pulled out beyond the original loops is force-only and drawn as a line, not a collider; there is no explicit string/hem contact model and no lock. Known gaps, listed in [PHYSICAL_PROTOCOL.md](PHYSICAL_PROTOCOL.md#simulation-correspondence-and-limits): 0.10 mm film (product gauge unpublished), the pot modelled as a straight cylinder, the liner's last ~2 cm on the mat omitted. Containment uses the film mesh with force-free virtual caps. The film-stretch guard flags invalid simulation, not tearing. The real trial uses the liner's unmodified loops with no handle, so the 2 g rigid pinch body makes the simulated grasp easier than the real one. No physical trial has been run.

## Third-party assets and software

| Item | Source / licence |
|---|---|
| YAM robot meshes, URDF, derived USD | I2RT Robotics, MIT, commit `120c3c81400171174604e503943f8d1ebc891058`; notice in `LICENSES/I2RT-MIT.txt`. |
| Table, floor, camera stand, station coordinates | Operator-installed YAM adapter pinned above; it declares no source licence at that revision and is not redistributed here. |
| Liner film, pot segments, blocks, loop bodies | Procedural geometry in this directory; no product mesh, scan, texture or artwork. Product names and dimensions are cited for the physical specification only. |
| Isaac Sim, Isaac Lab, Isaac Lab-Arena, Inspect Robots, Dream client | Installed separately under their own terms; not bundled. |

Novelty against TRI's loaded drawstring-bag closure and other prior art is discussed in [NOVELTY.md](NOVELTY.md).
