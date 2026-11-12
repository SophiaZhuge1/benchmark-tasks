# Dental hygienist assistant: rinse, clear the mouth and return both tools
Current submission media: **M-XPKWYY** — Dream-1 beta **0.0**, scripted demo **1.0**; source and video hashes accompany the current evidence. Earlier media IDs below are historical.


**Current revision: mouth-water v4 (continuous raw-score endpoint hold).** Category: Societal relevance.

> Rinse the highlighted teeth, lift the rinsing tool while suction clears the mouth, then return and release both tools on their stands.

The procedure represents rinsing/evacuation after professional air polishing on an inert dental phantom. It does not simulate polishing, plaque removal or clinical treatment. Equipment, dimensions, physical measurement procedures and limitations are in [PHYSICAL_PROTOCOL.md](PHYSICAL_PROTOCOL.md).

## Relevance and the ability being tested

**Societal relevance** (called societal relatability in the review rubric): a familiar dental-visit procedure, rinsing and evacuating water after tooth polishing. The difficulty is simultaneous wet crown coverage and removal of runoff through an inlet that must actually reach pooled water. Neither a dry circular motion nor suction in the wrong location meets the score; clearing later cannot undo an excessive earlier peak. The final return/release is a completion requirement, not the source of the task's distinctiveness. This is an inert training phantom, with no claim to plaque removal or patient-treatment safety. The workflow reference is the [Cavitron JET Plus instructions](https://www.dentsplysirona.com/content/dam/master/product-procedure-brand-categories/preventive/product-categories/ultrasonic-scaling/table-top-units/cavitron-jet-plus-ultrasonic-scaler-and-air-polishing-prophylaxis-system-with-tap-on-technology/documents/PRE-IFU-Cavitron-Jet-Plus-Ultrasonic-Scaler-and-Air-Polishing-Prophylaxis-System-with-Tap-On-Technology-2020-05.pdf), section9.8; the metered bench rig does not reproduce that commercial instrument.

## Physical rig and measurement essentials

All coordinates below are millimetres relative to the tabletop, not robot-base coordinates. Use the standard fixed bimanual YAM station, seed1 and zero jitter; the setup image fixes the starting arm pose.

| Component | Reproduction specification |
|---|---|
| Phantom | Acetal base170x130x12 centred(270,0); gum rails115x28x18 at(270,+/-25,19), front rail28x70x18 at(209,0,19). Clamp the base. |
| Crowns | Six acetal cylinders diameter20,height14 at(235/270/305,+/-25,30); four rounded cusps per crown, half-ellipsoid radii4.5x4.5x3 at offsets+/-4. Treat the three +Y crowns, nominal planez37. Front teeth12x12x18 at(209,-18/0/18,35); rigid tongue ellipsoid radii43x10x7 at(275,0,18). |
| Mouth water | Three transparent PMMA wells28x18 centred(235/270/305,0), floorz31, walls1 thick with inner facesy+/-9 and topz34.5; sealed7x3 connecting gutters. PETG runoff guides6 wide slope from crowns toward wells, drop6 over25. Calibrate1 mL overflow ports into the external catch. Include films and gutter water in the inventory. |
| Instruments | PETG handles28x24x55 with silicone grip29x25x20 centred40 above origin; target75 g each. Rounded hollow316 stainless irrigation OD5/ID3 and suction OD9/ID7. Tube centreline(0,0,22),(0,s25,22),(0,s90,-9),(0,s90,-25); s=-1 irrigation,+1 suction. |
| Original stands | Acetal cylinders diameter50,height30: basez0,centrez15,topz30, XY(280,+200)/(280,-200); tool origins start on the tops atz30, in the specified starting orientation. |
| Irrigation | Pump11 Elite,20 mL syringe, distilled water,1 m of2 mm-ID silicone hose; normally closed pinch valve, microcontroller/reset LED. Calibrate actual outlet0.40 mL/s at16-21,24-29,32-37 s:2.00 +/-0.02 mL/pulse,6.00 +/-0.03 total. Include delayed drips. |
| Evacuation | KNF N838 gas-pump family with regulator/gauge/relief, water trap, overflow trap and hydrophobic filter; record exact variant. Tool to150 mm ID6/OD9 silicone hose, combined vacuum-rated receiver; support hose slack. Commission at-10 kPa gauge and calibrate liquid recovery; gas ratings are not liquid performance. |
| Metrology | >=60 fps synchronized overhead and two macro/oblique cameras, grid/backlight/reset LED; calibrated pipette,0.001 g-readability balance, thermometer,10 mL receiver with0.1 mL divisions and1 mL fine receiver with0.01 mL divisions. Catch tray220x180x15. |

The retained inventory is **all** water on crowns, guides, pools and channels. Water crossing the suction inlet counts as recovered, including calibrated hose holdup; water leaving the mouth otherwise is loss. Check supplied = recovered + retained + lost. Use calibrated macro images throughout for peak volume, with supply/recovery/line-delay cross-checks. After recording the final settled endpoint, independently collect and weigh retained water/films against dry tare. A single final cup reading cannot establish a historical peak.

Track the wet jet impact in calibrated video: downward axisz<-0.94, height8-30 above crown plane, radius<=10. Nine regions per tooth are centre radius<=2.5 and eight45-degree sectors at radii4.5-9.5, sector0 starting+X toward+Y. Integrate calibrated flow only where it hits that crown; require>=1.8 mL delivery and>=0.15 s wet dwell in each region. Dry motion earns no dwell. Target uncertainty: jet position/height<=0.5 mm, peak volume<=0.05 mL, final volume<=0.01 mL, recovered/lost<=0.03 mL. These are calibration requirements, not achieved hardware results. At60 fps count nine complete intervals for0.15 s, and bound unobserved between-frame peak increases using measured maximum inflow.

Pass numerical limits only when the complete uncertainty interval passes; missing/occluded or threshold-straddling evidence is unverified. Calibrate suction over wet/dry cells and inlet heights, and verify collision-free access before a physical trial. See [PHYSICAL_PROTOCOL.md](PHYSICAL_PROTOCOL.md) for exact fabrication, calibration, guards, reset, measurement and rejection procedures. The numerical water limits define the inert benchmark, not patient safety.

## Required finishing sequence

1. Finish rinsing the third tooth; the timed water pulse stops.
2. Lift the rinsing tool clear while keeping suction inside the mouth.
3. Suction all remaining mouth-floor regions until total retained water is <=0.05 mL; the demo aims for <=0.005 mL. Continue in-mouth suction for at least1 s after the rinsing tool lifts.
4. Withdraw suction, return both tools to their **original** stands, open both grippers and withdraw the fingers. Both tools must settle for1 s.

Water still visibly travels from the nozzle onto crowns, runs into connected mouth-floor pools and enters the suction inlet only when the volume model actually recovers it. Pool depth follows retained volume. Blue is a visibility cue, not a measured liquid colour or CFD solution.

## Scoring

| Condition | Requirement |
|---|---|
| Whole-trial peak mouth water | <=1.00 mL total |
| Final mouth water | <=0.50 mL for partial credit; **<=0.05 mL for1.0** |
| Recovery | >=90% of supplied water |
| Spill/loss | <=0.30 mL |
| Each completed tooth | >=1.8 mL delivery and >=0.15 s wet dwell in each of9 regions |
| Full-score cleanup | Irrigator lifted; suction remains in mouth>=1 s after the final pulse and mouth water reaches<=0.05 mL |
| Full-score return | Each original stand: XY<=10 mm, Z<=5 mm, orientation<=10 degrees, speed<20 mm/s |
| Full-score release | Every fingertip>65 mm from both handle references; settled endpoint holds1 s |

Any permanent guard or general water-gate failure gives0. Otherwise zero/one/two/three completed teeth earn0/0.25/0.50/0.75. Full1.0 additionally requires the complete cleanup, return and release sequence. Exact geometry/measurement boundaries are in the protocol. These are inert-fixture benchmark choices, not patient-treatment limits.

The fixed water schedule is0.4 mL/s during16-21,24-29,32-37 s, independent of robot readiness. Limit1,200 actions/60 s at20 Hz, seed1, no jitter. The setup wait before16 s is retained.

## Verification

```bash
python -m unittest -v test_fluid test_mouth_water test_finish test_evidence
python scenario_checks.py --output validation/mouth_water_v3/scenario_results.json
export YAM_PYTHON=/path/to/yam-environment/bin/python
bash run_scenarios.sh /new/output/root full early_return no_return
```

51 tests and14 prescribed-coordinate model comparisons pass. Model comparisons supply endpoint assumptions and do not establish robot feasibility. The three recorded robot cases below passed trace, camera and source checks; sampled finishing frames were visually inspected. The scripted controller uses privileged geometric/volume state only to choose arm actions; it never sets fluid inventories, object poses, coverage or rewards.

Earlier mouth-water v2 recordings remain historical: its full1.0 ended with both tools held and is **not** evidence for the new finishing requirement. The current Dream-1 trial completed on 12 November 2026; hardware calibration remains pending; current media are identified in task.json. Current media are identified in task.json.

## Earlier v3 recorded robot results — 12 November 2026

CPU PhysX with RTX rendering, seed 1, no jitter, 20 Hz; all three native cameras contain no blank frames. Runtime Python source hashes match the reviewed source. Each run covers all 27 regions, peaks at 0.4650 mL retained water, loses 0 mL and passes the mechanical guard.

| Scenario | Score | Duration | Final mouth water | Recovered | Cleanup | Tools returned/released |
|---|---:|---:|---:|---:|---|---|
| Complete sequence | 1.00 | 50.35 s | 0.0027 mL | 5.9973 mL | Yes | Both |
| Return before clearance | 0.75 | 47.20 s | 0.2222 mL | 5.7778 mL | No | Both |
| Clear mouth but omit return | 0.75 | 48.40 s | 0.0027 mL | 5.9973 mL | Yes | Neither |

In the successful run, the near-dry cleanup condition first latches at 43.15 s; full reward is awarded only after original-stand placement, release and the 1 s settled hold. The no_release case has unit coverage but has not been recorded as a robot rollout. These are scripted simulations, not Dream-1 or real-water results. Detailed evidence and source/video hashes: `validation/mouth_water_v3/recorded_results_20261112.json`.

## Exact guard and endpoint checks

Every trial checks tip separation>6 mm; a tip entering195<x<340,abs(y)<45 belowz30 or a tool originz<=5 permanently fails. During flowing pulses, suction within9 mm XY of the active crown centre belowz65 may obstruct it for at most0.25 s cumulatively. Water gates apply to every partial tier. Aftert37, cleanup needs irrigator tipz>80 while downward suction axisz<-0.94 remains atx221-319,abs(y)<=9,z30.5-32.5 for>=1 s and total retained water<=0.05 mL. Both tools then return within10 mm XY,5 mm Z and10 degrees of their own starting stands, speed<20 mm/s; all fingertips>65 mm from both handle references, and both tips withdrawn(z>80 orabs(y)>75). Hold the returned/released endpoint1 s.

## Source and asset provenance

The task phantom, instruments, water indicators and racks are procedural geometry in task.py; no additional third-party task mesh, scan or texture is bundled. Robot/station assets come from the installed YAM/Arena runtime. A scripted controller may read simulator state to select actions; it does not teleport objects or set coverage, water inventories or score.

## Endpoint-hold correction after independent review

The raw scorer now requires **one continuous second** of the complete full-score endpoint before returning1.0. The first eligible observation starts the clock; loss of any full-score condition resets it. Timing out just after placement cannot earn full marks. Before that hold completes, otherwise complete dental endpoints receive0.75. Runtime success adds no second hold. This changes scoring timing only; the scene, controller, liquid limits and operational instruction are unchanged. Earlier videos/manifests preserve their original scorer; the current scorer-version evidence is reported below.

Check with `python -m unittest -v test_endpoint_hold`.

## Current v4 held-endpoint recording — 12 November 2026

The corrected scorer completes the full scripted sequence at **1008/1200 steps,50.40 s,score1.0**, leaving0.0027 mL, recovering5.9973 mL, peaking at0.4650 mL, with no spill. Both tools return and release. All three640x360 camera streams have zero blank frames. Raw score remains0.75 at step1007 with0.95 s hold and becomes1.0 at step1008 with1.00 s hold. Fifty-one offline tests pass. Current task.py hash: `4e1c014efffee6276c4c58b7da8aea57d6f264e3f19c85e41a1ed4d2ef40dc34`.

Both recordings use CPU PhysX and RTX rendering, seed1, zero jitter and20 Hz; these are scripted runs, not Dream-1 or physical experiments. Complete traces, source snapshots and three-camera footage are retained. Source bytes were independently checked against the separate pre-run run_config hashes. The automatically generated manifest mistakenly hashed its own preceding version; its original and original failed verification were preserved, that self-entry was removed with a correction note, and all remaining source hashes and evidence checks pass. No source/score was changed to repair packaging. The current Dream-1 result is recorded below; current official media are identified in task.json.


## Current Dream-1 evidence — 12 November 2026

Dream-1 beta (`dreamlabs/dream-1-beta`) completed the current instruction, scene and continuous-hold scorer with **score0.0** after **1200 control steps**, with no evaluation error. This is an actual model-policy run, not a refusal or an access failure. Seed1, zero jitter,20 Hz, CPU PhysX and RTX rendering; three640x360 camera recordings are retained. Model failure does not alter the independently recorded full-score scripted demonstration. The run configuration, results, source hashes and recording validation are in `validation/current_dream_20261112.json`. Current demo, model and setup media are prepared separately from the historical media ID; current media are identified in task.json.

Prepared current `model_run.mp4`, `demo.mp4` and `setup.png` are recorded in `validation/current_media_20261112.json`; both videos are H.264 and below50 MB. Current public media mapping: M-XPKWYY.
