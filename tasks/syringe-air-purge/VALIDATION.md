# Validation — 8 November 2026

The full scripted return-to-rack task passed with score **1.0** in the fixed-layout Brev run `syringe-seal-v16/full` (seed 1, object jitter 0).

| Measure | Result |
|---|---:|
| Control steps | 675 |
| Simulated time at 20 Hz | 33.75 s |
| Rollout wall time, excluding simulator startup | 115.05 s |
| Residual air | 0.0106 mL |
| Sample loss | 0.0444 mL |
| Total aspirated air | 0.0412 mL |
| Lift / return / release gates | Passed |
| Blank video frames | 0 |
| Worst reported IK position error | 0.1 mm per arm |

The no-action, horizontal-push and excessive-push controls each scored **0.0**. Horizontal push lost 1.5764 mL sample; excessive push lost 2.5618 mL. Both returned and released but correctly failed the persistent sample-loss gate.

Nine fluid/scoring checks and four passive-seal checks pass. The current submission files match the live Brev source used for the successful run. The original diagnostic variants remain outside this submission.

The demo reads simulator state. The fluid and seal models are illustrative, uncalibrated approximations; this single seed establishes simulation feasibility only. Hardware validation is outstanding. Task-board media ID: **M-SEEP5V** (model video, full-score demo and setup screenshot).

## Dream-1 beta — actual model trial

On 8 November 2026, `dreamlabs/dream-1-beta` completed one independent trial using the same physics source and exact submitted instruction. See [dream_result.json](dream_result.json).

| Measure | Result |
|---|---:|
| Task score | 0.0 |
| Control steps / simulated time | 1,800 / 90 s |
| Evaluation wall time, including startup and inference | 231.61 s |
| Mean inference latency | 0.603 s |
| Residual air / sample loss / aspiration | 1.5 / 0.0 / 0.0 mL |
| Lift achieved | No |
| End condition | Step limit |
| Evaluation errors | 0 |
| Recorded frames per camera | 1,801 |
| Blank frames per camera | 0 |

The arms moved around the syringe, but the logged state never achieved the required lift or air removal. Initial, midpoint and final camera frames were inspected. The final logged syringe position remained (0.25, 0, 0.8868) m. A three-camera H.264 model video was assembled from the recorded trial frames; no scripted actions were substituted. The existing full-score scripted demo remains separate.

The automatic video export initially could not find FFmpeg on PATH. Export succeeded using the installed `imageio_ffmpeg` binary; this did not rerun or change the model trial. The runner now resolves that binary automatically. The three required media files were uploaded successfully as **M-SEEP5V**. The model video is H.264, 1280 × 480, 20 fps, 90.05 s (7,475,578 bytes); the full-score demo is H.264, 1280 × 480, 20 fps, 33.8 s (2,797,164 bytes); the setup screenshot is 48,065 bytes. The official Python upload request returned Cloudflare error 1010; curl succeeded with the same documented endpoint, bearer authentication and multipart fields.
