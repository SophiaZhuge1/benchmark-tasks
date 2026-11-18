# Media provenance

Media ID in `task.json.media`: M-K63S4Z. All three files come from runs of this source on the official Isaac Lab-Arena release/0.3.1 environment.

- `demo.mp4`: encoded from the frames of the scripted run `FB_ol1` named in [VALIDATION.json](VALIDATION.json) (every fourth control step, 5 fps, the `ffmpeg` command in README.md). Score 1.0, independent replay 1.0.
- `setup.png`: that run's start-state image (top, left, right and overview cameras).
- `model_run.mp4`: the Dream-1 run listed in VALIDATION.json (320 x 176 cameras), encoded from its recorded camera streams with `inspect-robots video`; the run errored at step 1,427, and the video shows those steps.
