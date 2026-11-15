# Take out the trash: cinch and remove a loaded bin liner

Pull both drawstrings to close the full bag, lift it out of the bin, and release it onto the table beside the bin without spilling any contents.

**Category: Impact on jobs.** This task targets the repetitive close-and-remove step in janitorial trash collection. O*NET lists gathering and emptying trash as a core duty for SOC 37-2011; BLS reports 2,432,600 US jobs in 2025. The task demonstrates a small countertop-bin handling step, with a 150 g load and a specified cord-lock liner. See [JOB_IMPACT.md](JOB_IMPACT.md) for the occupational evidence and scope.

**Proposed distinction:** maintain closure and all contents while extracting the preloaded flexible liner from a surrounding rigid bin, then release it in a stable state. TRI already demonstrates loaded drawstring-bag closure; [NOVELTY.md](NOVELTY.md) compares the actual outcomes and acknowledges that extraction may be judged insufficiently distinct. No novelty clearance or official acceptance is claimed.

**Recorded evidence:** scripted demo 1.0 in 939/4,000 steps; Dream-1 0.0 after normal 4,000-step completion. Original videos and setup image are uploaded as **M-C8X8HT** in `task.json`. Physics and scoring are unchanged by this occupational/novelty documentation update.

## Physical specification and scoring

See [PHYSICAL_PROTOCOL.md](PHYSICAL_PROTOCOL.md) for every task object, measured placement, reset and ruler/video scoring. [ASSEMBLY_GUIDE.md](ASSEMBLY_GUIDE.md) adds the continuous cord route, tether locations, construction steps and an explicitly unperformed physical preflight. The [routing diagram](cord-routing.svg) is schematic, not a hardware-validation claim. There is no fresh liner or retaining-ring replacement. The actual test load is six clean 25 g blocks, 150 g total; this task makes no claim about lifting a full-sized heavy refuse sack.

| Primary score | Outcome |
|---|---|
| 0.0 | No successful cinch; final opening exceeds 60 mm; any content escaped during the trial; or the bag was destroyed to bypass handling. |
| 0.4 | Opening reached at most 50 mm and ends at most 60 mm, with all six contents retained. |
| 0.7 | The same closed load is also wholly clear of the bin by at least 20 mm for the final two seconds. |
| 1.0 | The same closed load is released and supported on the table beside the bin for the final two seconds, with the whole bag and contents at least 20 mm inside the table edges, bottom within 25 mm of the table top, visible bag bounds moving no more than 10 mm over those two seconds, and both grippers at least 60 mm from film/handles. |

Highest satisfied level applies. Any clear tabletop landing position is valid. Harmless lowering, regrasping, pauses and corrective pulls are allowed. Closure and clearance are geometric outcomes, not controller phase names or prescribed movement order. Run limit: **4,000 control steps at 20 Hz (200 simulated seconds)**. Requested CLI seed: 0; the installed adapter reports environment seed 42; object jitter: 0. Multi-seed reliability has not been established.

`TableDepositJudge` is shared by the scripted and Dream-1 interfaces. Every control step checks non-convex film containment, using the actual film triangles plus an evaluator-only mouth cap; it no longer uses a convex hull. Eight corners, six face centres and the centre of every content block are tested, with a 5 mm contact tolerance. This finite sampling and the virtual mouth cap remain disclosed numerical approximations. `test_containment.py` includes an exterior-fold case that the previous convex hull wrongly classified as interior.

The 1.5 film-edge-stretch bound is a **simulation-validity guard**, not a calibrated tearing threshold or a physical scoring measurement. Such a run returns `trial_valid: false`; investigate/rerun it rather than reporting it as an ordinary valid physical task result. Non-finite or incomplete geometry likewise cannot substantiate a successful demonstration. In a physical trial, count escaped contents and inspect film integrity directly as described in the protocol.

## Run in the installed Isaac / Inspect Robots environment

Use Python 3.12 and the versions in [runtime_versions.json](runtime_versions.json). The operator must already have the simulator installed and its licences accepted. Keep the existing converted YAM USD assets. No credentials belong in this directory.

The adapter dependency is `kairosiann/yam-isaac-lab-arena` at commit `0059d02a1a91bc6834c1d0846022891df0c78730`. `prepare_runtime.py` checks that revision and creates a local `.runtime/` overlay with the two exact compatibility changes used for the demo. Assets stay linked to the operator's installed checkout. There is no dependency on a previous bin-bag experiment directory.

From this task directory, replace the three installation paths below with your installed paths:

```bash
/path/to/environment/bin/python launch.py demo \
  --adapter /path/to/yam-adapter \
  --arena-root /path/to/IsaacLab-Arena \
  --out runs/demo_001
```

For a setup-only render, replace `demo` with `setup`. Use a new output directory each time. The demo writes per-step geometry, a trace, source snapshots, setup views and rendered frames, then independently evaluates the result. It succeeds only for an error-free full-score episode.

For Dream-1, make `DREAM_API_KEY` available securely to the process, then use the identical command with `model` and `--out runs/dream_001`. The launcher calls the installed `inspect-robots` Dream policy at 20 Hz with 320 x 176 policy-camera frames, requested CLI seed 0 (effective adapter environment seed 42), zero jitter, 4,000 steps and the same primary scorer. Full geometry is recorded in `geometry/episode_000/`. The overview camera is diagnostic only; the model receives the standard top and wrist cameras. A model score of zero is a legitimate result and must be reported as such.

Independent replay and offline tests:

```bash
python replay_run.py runs/demo_001 --out runs/demo_001/independent_replay.json
python -m unittest discover -v
```

For model replay, point `replay_run.py` at its geometry episode directory. Replay does not modify physics or source evidence. Full lossless geometry is retained in the development evidence archive; it is not committed in this PR. Reproduce it with the demo/model launch commands above, then replay the newly generated output directory. Compact recorded measurements and source hashes are included in `VALIDATION.json`. Fresh tabletop-run metrics are recorded after physics validation. Wall-clock time depends on hardware and recording/scoring overhead. The current run results, including actual wall time, belong in `VALIDATION.json`; do not substitute offline unit-test results for physical success.

Encode a scripted recording from its every-four-step PNGs at 5 fps:

```bash
ffmpeg -framerate 5 -pattern_type glob -i 'runs/demo_001/frames/*.png' \
  -c:v libx264 -pix_fmt yuv420p -movflags +faststart demo.mp4
```

For the model recording, use `inspect-robots video` on its evaluation JSON. The submission needs `demo.mp4`, `model_run.mp4` and `setup.png` uploaded with the repository's media tool; its returned ID fills `task.json.media`. Never invent a media ID or label a pending model run as completed.

## Reproduction and reviewer evidence

| Parameter | Evidence-backed value |
|---|---|
| Launch request | CLI seed 0 in the launch command; keep this value to reproduce the submitted run. |
| Simulator environment | Installed adapter reports seed 42. Do not describe the run as an environment-seed-0 trial. |
| Object randomisation | Zero jitter; one fixed setup. |
| Budget | 4,000 control steps × 0.05 s = 200 simulated seconds. |
| Scripted demo | 939 steps / 46.95 s; primary score 1.0; complete geometry replay 1.0. |
| Dream-1 | 4,000 steps / 200 s; primary score 0.0; normal completion; complete geometry replay 0.0. |
| Reliability | No multi-seed or hardware reliability claim. |

See [MEDIA_PROVENANCE.md](MEDIA_PROVENANCE.md) for hashes and frame counts of the original uploaded recordings. Binary videos and the setup screenshot are served through the media ID, rather than committed to this source folder. See [NOVELTY.md](NOVELTY.md) for the direct TRI loaded-drawstring-bag overlap and the remaining novelty risk.

## Tabletop update

The final goal releases the lifted bag onto the tabletop beside the bin. The fresh demo scored **1.0**, with all 940 recorded states independently replayed. It took 46.95 simulated seconds; the bag was released 46.2 mm above the table. All six contents remain inside, the final mouth is 49.64 mm, and final two-second bag motion is 0.173 mm.

Dream-1: completed 4000 steps; task score 0.0, independently reproduced from geometry (0.0). No refusal or runtime error. Read `VALIDATION.json` for the recorded Inspect status and metrics. The retained development trace and meshes cover every control step; they are not bundled in this source-only PR.

The finalized scorer preserves harmless below-table lowering/recovery; original source snapshots and final-scorer replays explain this scoring-only correction. The physical scene is unchanged. Historical floor runs remain archived in the checkpoint and are not evidence for the new goal. The earlier tabletop development trial scored 0.7 because it overhung the table; its release point was then shifted 60 mm inward.

Original demo/model/setup media uploaded successfully as **M-C8X8HT**, recorded in `task.json.media`. The direct loaded-drawstring-bag closure overlap and proposed distinction are disclosed in `NOVELTY.md`. Official acceptance is not claimed.

## Fidelity

PhysX surface film, normal robot actuation and contact grasps are used. Routed spring/damping forces approximate the continuous drawcord, with back-feed resistance approximating two tethered cord locks. Small visible housings are original primitive proxies; housing/hem inertia is lumped into the 20 dynamic hem markers. The model does not resolve the locks' internal cam, explicit rope/hem sliding contact, real puncture/tear propagation, dust, liquid or sharp rubbish. Material and lock forces are not hardware-calibrated. No bag/contents poses are scripted after reset, and no robot-object grasp attachments are used. The scripted controller may use simulator state, as permitted by the review prompt.

## Third-party assets and software

| Item | Source / licence / use |
|---|---|
| YAM robot meshes, URDF and derived USD, including split-colour cover meshes | I2RT Robotics, MIT; source commit `120c3c81400171174604e503943f8d1ebc891058`; upstream adapter identifies the split meshes as derivatives of these MIT assets. Notice retained in `LICENSES/I2RT-MIT.txt`. |
| Table, floor, camera-stand primitives and station coordinates | Generated by the operator-installed YAM adapter pinned above; **the adapter declares no source-code licence at that revision**. It is an external dependency, not redistributed or relicensed in this task. Its source and licence status are explicitly disclosed. |
| Bag film, bin segments, waste blocks, cord curves and lock housing proxies | Procedural geometry in this task/checkpoint; no downloaded product mesh, scan, texture or manufacturer artwork. |
| Cyberian cord-lock reference | ITW Nexus technical dimensions and operating principle are cited for physical specification only; manufacturer CAD, photographs and documents are not bundled or claimed as MIT. |
| Simulation/runtime libraries | Installed Isaac Sim, Isaac Lab, Isaac Lab-Arena, Inspect Robots and Dream client retain their own upstream terms; they are not bundled. |

Adapter licence declaration: https://github.com/kairosiann/yam-isaac-lab-arena/blob/0059d02a1a91bc6834c1d0846022891df0c78730/README.md#license

I2RT: https://github.com/i2rt-robotics/i2rt/tree/120c3c81400171174604e503943f8d1ebc891058

Cord-lock manufacturer: https://eu.itwnexus.com/content/cyberian-cordloc

See [NOVELTY.md](NOVELTY.md) for the evidence and limits of the comparison; no official acceptance or exclusive claim to bag handling is asserted.
