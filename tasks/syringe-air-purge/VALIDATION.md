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

The demo reads simulator state. The fluid and seal models are illustrative, uncalibrated approximations; this single seed establishes simulation feasibility only. Dream-1 and hardware validation are outstanding. No task-board media ID has yet been issued for this task.
