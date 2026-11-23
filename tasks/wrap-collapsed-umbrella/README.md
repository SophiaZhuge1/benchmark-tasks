# Wrap, fasten and set down a folded umbrella

The left YAM gripper starts holding the handle and the right starts beside the loose tie. The arms gather the canopy, wind the tie once round it, press its hook-and-loop faces together and set the umbrella on a bare table. Storage begins with the frame already collapsed. A successful wrap stays bundled when the hands leave. Only the result is scored: the tie may be wound by turning the handle, by carrying the tie round the canopy or any other way, and either hand may hold, press or set down.

## Physical setup and reset

Use a dry compact umbrella with a foldable fabric canopy, a straight handle that fits the gripper and a textile hook-and-loop tie. A wrist lanyard remains loose throughout. The simulated umbrella is approximately 300 mm from ferrule to handle end, with a 32 mm handle and 190 mm of folded canopy, and weighs 0.19 kg with its strap; record the mass of the umbrella you use. The nominal webbing is 239 × 24 mm, with 55 mm of hook material on the free end and 72 mm of loop material near the sewn end, on opposite faces. Choose a strap long enough for one complete wrap plus visible mating overlap. Before a robot trial, wrap it once by hand, release it and check that the closed wrap holds on the table.

A low-cost retail example is the Home Shopping Selections H67003 compact manual umbrella (£4.99 listed). Its product page confirms a hook-and-loop tie. Measure the item you use and record its dimensions; the retail listing gives no tie dimensions. To reproduce the simulated long tie, cut a 239 mm finished length of 24–25 mm woven polyester ribbon. Sew the two fastener patches around their edges and attach the loop end at the original tie seam with the hook facing inward when wrapped. Sew-on hook-and-loop tape is available in 25 mm widths. Record whether you used the stock or replacement tie. [Umbrella H67003](https://hssuk.co.uk/product/96cm-manual-umbrella/) · [Sew-on tape V25](https://www.profabrics.co.uk/products/sew-on-hook-and-loop-25mm)

Put contrasting tape marks at the strap seam and tip. Mount a phone looking along the shaft and put a ruler in the plane of the strap. Add a second phone recording a side view, with a ruler standing on the table, for the set-down and release. Put the dry umbrella horizontally in the left gripper, with the seam uppermost, the untied strap hanging to the right and both fabric faces clean. The YAM scene places the shaft 258 mm above a 747.5 mm tabletop and starts the open right gripper about 60 mm from the webbing. Record the open bundle's shaft-centred diameter before each run, using twice the greatest visible distance from the shaft centre to the folded canopy. Use the same scale and cross-section at the end. Undo the tie and restore the same loose folds before the next trial.

## Scoring the outcome

Read the state at the end of the trial. The score is the highest tier whose conditions all hold then; each tier includes the ones below it. No winding technique or choice of hand enters the score; apart from the end state, only the release is checked (the umbrella must already rest on the table when the last gripper lets go).

| Score | Observable requirement | Real-trial check |
| --- | --- | --- |
| 0.00 | The canopy is not gathered, or the umbrella is neither held in a gripper nor resting on the table (for example, it fell off). | End-on photo; side view. |
| 0.25 | Gathered: the bundle's shaft-centred diameter is at most 80% of its loose reference diameter, and the umbrella is held or resting as above. | End-on photo with the ruler, against the same reading taken before the run. |
| 0.50 | The tie also travels at least three quarters of the way round the shaft (270°; 4.7 rad in the simulator). | Trace the strap from the seam mark to the tip mark in the end-on photo. |
| 0.75 | The tie goes once round the canopy with visible overlap (at least 365°), and the hook patch is engaged on the loop patch: overlapping, aligned and pressed closed (at least 48 mm² of hook face still engaged in simulation). | Photo of the closed patches: the tip patch lies on the loop patch, aligned, and is pressed closed. |
| 1.00 | The umbrella rests on the table after being lowered, not dropped: it is already resting on the table when the last gripper lets go. Both grippers are at least 20 mm from every part of it and touch none of it. Retention: after the last gripper clears, the released wrap stays gathered, wound at least 365° and fastened, with the umbrella and strap still, for at least one second, and it is still so at the end. The canopy may first spring out a little as the hands leave. | Side video with the standing ruler: the umbrella touches the table before the last gripper opens; gripper gap to the umbrella against the ruler; once it settles, the wrap stays closed with nothing moving for at least one second; end-on photo repeated at the end. |

A loose non-mating corner of the tie is acceptable if the sewn faces retain contact over part of their area. A drop onto the table still earns the lower tiers if the wrap survives it. It can reach 1.00 only if a gripper takes hold of the umbrella again and the last gripper lets go while the umbrella rests on the table. The compactness reference for this model is approximately 49.7 mm in radius before wrapping, so the gathered limit is 39.8 mm. The 20% reduction is a benchmark definition of a gathered canopy, independent of a particular storage sleeve.

In simulation, holding means both pads of either gripper bear at least 0.1 N on the umbrella, and the set-down needs table support in the last control in which any gripper held it; release means no pad bears 0.1 N on it and every pad sample is at least 20 mm from it. Table support is a measured load of at least 0.6 N from the tabletop with the lowest part within 18 mm of it. The one-second window spans 20 controls and limits every moving part to 0.022 m/s and 1 rad/s, observed from pose changes at physics substeps.

### Checks of the scorer

Scripted routes that do not finish the task, run with the same command and `UMBRELLA_NEGATIVE` set (see below):

| `UMBRELLA_NEGATIVE` | What the script does | End state | Score |
| --- | --- | --- | --- |
| `none` | Holds the handle; the right hand never takes the strap. | Canopy loose (radius 49.7 mm), strap wound 160°. | 0.00 |
| `unfastened` | Winds the strap once round, then lets go of it without pressing the fastener, and sets the umbrella down. | The wrap sprang open: strap at 16°, canopy loose (49.7 mm). | 0.00 |
| `drop` | Winds and fastens the strap, backs the right hand away, then opens the left hand with the handle about 0.45 m above the table. | Fastened wrap survives the fall and lies on the table: radius 35.1 mm, wound 378°; not set down. | 0.75 |
| `held` | Winds, fastens and lowers the umbrella to the table, but never lets go. | Gathered (30.4 mm), wound 380° and fastened, still gripped just above the table. | 0.75 |
| (none) | The full demonstration. | See "Recorded outcome". | 1.00 |

## Simulation and reproduction

Use the Inspect Robots YAM Arena adapter in an Isaac Lab environment with CUDA. Include this folder on the task loader's search path by running from inside it. The model uses a free shaft, twelve radially sprung canopy sections, fifteen hinged strap sections, and distributed hook-and-loop patches. Hook-and-loop engages when overlapping, aligned patches are pressed together with a measured normal load of at least 0.15 N for three consecutive controls while a fingertip of either gripper is at the strap end or its hook patch; how the strap was wound plays no part. Separation or sliding of engaged material points peels the bond. The material properties approximate fabric and hook-and-loop tape and have not been calibrated to a retail umbrella. The scripted demonstrator reads simulator poses, contact forces and the fastener model's engagement state, published to it after each control; it never reads the score. Dream-1 uses its policy interface.

```bash
python -m unittest -v
UMBRELLA_TRACE=1 bash run.sh yam_scripted
UMBRELLA_TRACE=1 bash run.sh dream
UMBRELLA_TRACE=1 UMBRELLA_NEGATIVE=unfastened bash run.sh yam_scripted   # also none, held, drop
```

Each episode allows 1,800 controls at 20 Hz (90 simulated seconds) with zero starting-object jitter. The initial held handle and open right hand are part of the setup. For the model run, configure Dream-1 credentials using the adapter's normal login. `run.sh` passes the instruction from task.json. The demonstration and model scores are recorded in task.json.

Verified environment: Inspect Robots 1.0.0, Isaac Sim 6.1.0.0, Isaac Lab 17.0.2 and Isaac Lab Arena 0.3.0. Install the [YAM Isaac Lab Arena adapter](https://github.com/kairosiann/yam-isaac-lab-arena/tree/0059d02a1a91bc6834c1d0846022891df0c78730) at this revision. At control 640 the task refines the contact solver for thin fabric links on the same schedule for both policies. Use the included run script to reproduce the recorded timing.

## Assets and licenses

All umbrella, strap, fastener and tabletop-skin geometry is generated from primitive shapes in this folder's code; no third-party mesh, scan or texture is bundled or loaded by the task. The robot, station and cameras are the standard benchmark infrastructure supplied by the pinned YAM Isaac Lab Arena adapter, which the task loads unchanged; nothing from them is copied into this folder.

| Asset used in the scene | Source | License |
| --- | --- | --- |
| Two YAM arms with parallel grippers: URDF, link and finger meshes, collision hulls and the converted USD | I2RT YAM model at commit `120c3c81400171174604e503943f8d1ebc891058`, supplied in the [adapter's `yam_arena/assets/yam`][yam-assets] | [MIT, Copyright (c) I2RT Robotics][i2rt-license] |
| Black and white visual meshes of arm links 2 and 3 | I2RT's link meshes split for the station's appearance, [shipped with the adapter][split-links] | [MIT, under the I2RT license][i2rt-license] |
| Station table, floor, top-camera stand, dome light and lamp | Procedural boxes, capsules and lights generated by the [adapter's station code][station] | Generated in code, no asset files; the [adapter repository declares no license yet][adapter-license]. The lighting runtime is Isaac Lab-Arena, [Apache-2.0][arena-license] |
| Overhead and wrist cameras | Virtual cameras placed by the adapter from the [YAMLab station calibration][calibration] | [MIT][calibration-license] |

[yam-assets]: https://github.com/kairosiann/yam-isaac-lab-arena/tree/0059d02a1a91bc6834c1d0846022891df0c78730/yam_arena/assets/yam
[i2rt-license]: https://github.com/kairosiann/yam-isaac-lab-arena/blob/0059d02a1a91bc6834c1d0846022891df0c78730/yam_arena/assets/yam/LICENSE.i2rt
[split-links]: https://github.com/kairosiann/yam-isaac-lab-arena/blob/0059d02a1a91bc6834c1d0846022891df0c78730/yam_arena/assets/yam/dream/SOURCE
[station]: https://github.com/kairosiann/yam-isaac-lab-arena/blob/0059d02a1a91bc6834c1d0846022891df0c78730/yam_arena/station.py
[adapter-license]: https://github.com/kairosiann/yam-isaac-lab-arena/blob/0059d02a1a91bc6834c1d0846022891df0c78730/README.md#license
[arena-license]: https://github.com/isaac-sim/IsaacLab-Arena/blob/c7edf3a9d5d8276565208f72422f8f8a0806d6cf/LICENSE.md
[calibration]: https://github.com/ARISE-Initiative/yamlab/tree/ec0455d2b4ce35f21fc126418ea5e74ac567133d
[calibration-license]: https://github.com/ARISE-Initiative/yamlab/blob/ec0455d2b4ce35f21fc126418ea5e74ac567133d/LICENSE

## Recorded outcome

The scripted demonstration ends at control 1,185 (59.25 simulated seconds). It winds the strap by turning the handle once (360.1°) while the right hand guides the strap; the strap then stays wound 380.0°. The fastener engaged at control 938, the umbrella rested on the table while the right gripper still held it, and at control 1,180 the canopy radius was 37.4 mm against a 49.7 mm loose reference (30.5 mm while still held; it sprang out to 43.5 mm for a moment at release, then settled), the tabletop carried 0.74 N and both grippers were clear. Throughout the qualifying second the maximum observed linear and angular speeds across all 28 moving bodies were 0.00614 m/s and 0.70324 rad/s. The scorer uses observed pose changes at physics substeps; the native velocity diagnostic still reported motion. The final score was 1.00.

Dream-1 ran all 1,800 controls on the same setup with the instruction exactly as in task.json, in one session from the first action to the end, and scored 0.00. Both results are single runs on the fixed starting layout.
