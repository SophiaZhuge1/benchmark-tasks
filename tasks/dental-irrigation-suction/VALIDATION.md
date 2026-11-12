# Mouth-water v3 validation

47 unit/evidence-harness tests pass, including12 finishing-sequence and rack-state tests. 14 prescribed-coordinate model comparisons pass; their explicit endpoint assumptions are not robot evidence. Current robot rollout checks are recorded separately. Prior v2 results and documentation are historical.

Hardware remains untested. Full-score near-dry measurement now needs final-mouth uncertainty<=0.01 mL to adjudicate the0.05 mL limit. These are proposed measurement requirements, not achieved physical results. Current Dream-1 completed with score0.0; current official media are identified in task.json.

## Recorded robot results — 12 November 2026

CPU PhysX with RTX rendering, seed 1, no jitter, 20 Hz; all three native cameras contain no blank frames. Runtime Python source hashes match the reviewed source. Each run covers all 27 regions, peaks at 0.4650 mL retained water, loses 0 mL and passes the mechanical guard.

| Scenario | Score | Duration | Final mouth water | Recovered | Cleanup | Tools returned/released |
|---|---:|---:|---:|---:|---|---|
| Complete sequence | 1.00 | 50.35 s | 0.0027 mL | 5.9973 mL | Yes | Both |
| Return before clearance | 0.75 | 47.20 s | 0.2222 mL | 5.7778 mL | No | Both |
| Clear mouth but omit return | 0.75 | 48.40 s | 0.0027 mL | 5.9973 mL | Yes | Neither |

In the successful run, the near-dry cleanup condition first latches at 43.15 s; full reward is awarded only after original-stand placement, release and the 1 s settled hold. The no_release case has unit coverage but has not been recorded as a robot rollout. These are scripted simulations, not Dream-1 or real-water results. Detailed evidence and source/video hashes: `validation/mouth_water_v3/recorded_results_20261112.json`.
