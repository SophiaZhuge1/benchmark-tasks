# Uploaded evidence

The official upload returned **M-C8X8HT**, recorded in task.json. It contains the final tabletop task's original demo.mp4, model_run.mp4 and setup.png. They are served by the task board and are not committed as binaries in this source directory. SHA-256 hashes, sizes, frame counts and codec information are in [evidence/MEDIA_PROVENANCE.json](evidence/MEDIA_PROVENANCE.json).

| Recording | Recorded result | Video |
|---|---|---|
| Scripted demo_002 | 1.0 at step 939 / 46.95 simulated seconds | H.264 640 × 360, 5 fps, 234 frames, 46.8 s; sampled every four control steps. |
| Dream-1 dream_002 | 0.0; normal completion at 4,000 steps / 200 simulated seconds | H.264 640 × 576, 20 fps, 4,001 frames, 200.05 s; original camera montage. |

The demo video ends at its last sampled frame; the full control trace contains states 0–939 and the final two-second acceptance interval. Independent full-geometry replays returned 1.0 and 0.0. These are recorded outcomes, not a newly executed trial for this metadata change.

The submitted instruction, physics, controller and scorer are unchanged. Requested CLI seed 0 maps to effective adapter environment seed 42, with zero object jitter. Multi-seed performance is not established. The cord-routing.svg drawing is an original topology schematic, not a hardware photograph or evidence of physical assembly validation.
