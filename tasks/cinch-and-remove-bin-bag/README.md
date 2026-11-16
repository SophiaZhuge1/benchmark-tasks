# Take out the trash with an ordinary factory drawtape liner

**Development candidate — not ready for resubmission. No revised 1.0 demo or Dream-1 run exists.**

Instruction: Pull the liner's built-in drawtapes, tie them to secure the mouth, then lift the bag out and place it on the table without spilling.

This revises the rejected custom cord-lock/rigid-handle task toward an ordinary commercial liner. The reference product is Brabantia PerfectFit Code A, SKU 137600 (270 x 290 mm), paired with the manufacturer's compatible Sort & Go 3 L bin. See [PHYSICAL_PROTOCOL.md](PHYSICAL_PROTOCOL.md) for product sources, the proposed real setup and the unperformed physical preflight.

The active simulation replaces rigid handles with uniform contact links of one articulated tape loop and replaces one-way locking with symmetric sliding-hem forces. There is no automatic closure latch or knot flag. Tape dimensions, its factory routing and material/friction parameters remain unverified assumptions. The inherited cylindrical diagnostic bin has not yet been replaced with the manufacturer's rectangular bin, and the inherited controller does not tie a knot. [REVISION_STATUS.md](REVISION_STATUS.md) lists all outstanding work.

The primary scorer is `OrdinaryLinerJudge`. It can award 0.25 for retained cinching; it deliberately withholds closure-dependent credit while knot verification is unimplemented. The older geometry scorer is retained to debug extraction/placement. A geometric score of 1.0 from that helper is **not** a full task score. Scripted and Dream-1 episodes, offline evaluation, and replay all select the same conservative primary scorer.

The category remains Impact on jobs: ordinary loaded-liner closure/removal is a bounded step in routine cleaning. No demonstrated capability is inferred from worker counts; see JOB_IMPACT.md. Prior-art overlap remains disclosed in NOVELTY.md.

## Running development checks

On the current two-GPU host, isolate the selected device with `CUDA_VISIBLE_DEVICES=1` and pass `--device cuda:0` so PhysX and rendering use the same logical device. Direct `--device cuda:1` failed during initialization.

Use the operator-installed Isaac and Inspect Robots Python environment and the pinned YAM adapter listed in runtime_versions.json. No credentials belong in the repository. Use a fresh output directory for every run.

```bash
/path/to/env/bin/python launch.py setup --adapter /path/to/yam-adapter --arena-root /path/to/IsaacLab-Arena --out runs/setup_001
/path/to/env/bin/python launch.py demo --adapter /path/to/yam-adapter --arena-root /path/to/IsaacLab-Arena --out runs/demo_001
```

`setup` is a diagnostic, and `demo` currently invokes the inherited cinch/lift controller. Its success exit is blocked unless the full primary score is verified. Neither command currently proves a tied factory closure.

Once the exact final scene and scorer are validated, make DREAM_API_KEY available securely and use `launch.py model` with the same arguments. Budget: 4,000 control steps at 20 Hz (200 simulated seconds); requested seed 0, adapter environment seed 42, zero object jitter. A failed task score is a valid Dream-1 outcome; initialization errors are not completed policy trials.

```bash
python3 -m unittest discover -v
python3 replay_run.py runs/demo_001 --out runs/demo_001/independent_replay.json
```

Offline synthetic tests assess code invariants and adversarial scoring cases, not robot feasibility. New full-score video and Dream-1 media are still required. The rejected scene's videos and scores are archived under evidence/rejected-custom-liner and cannot be reused.

## Fidelity and licence notes

The bag uses PhysX surface deformation; the tape uses 80 uniform articulated rigid segments with ordinary contact and self-contact. A local symmetric force model approximates sliding in the hem. Tape collision thickness is exaggerated for numerical stability; tape/hem masses, stiffness and friction are uncalibrated. The idealised bag mesh, current bin, factory tape route and bight lengths require matching to the actual product. Knot mechanics, tear propagation, puncture, wet waste and sharp waste are unvalidated or absent. No bag or waste poses are scripted after reset and no robot-object grasp attachment is introduced.

All new task geometry is procedural; manufacturer photos/CAD are not included. YAM assets remain external MIT assets with the notice in LICENSES/I2RT-MIT.txt. The pinned yam-isaac-lab-arena adapter declares no source licence and is not redistributed; Isaac/Inspect dependencies retain their upstream terms.
