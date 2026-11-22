# Wrap, fasten and set down a folded umbrella

The left YAM gripper holds the handle while the right catches the loose tie. The arms gather the canopy, wind the tie once, press its hook-and-loop faces together and set the umbrella on a bare table. Storage begins with the frame already collapsed. A successful wrap stays bundled when the hands leave.

## Physical setup and reset

Use a dry compact umbrella with a foldable fabric canopy, a straight handle that fits the gripper and a textile hook-and-loop tie. A wrist lanyard remains loose throughout. The simulated umbrella is approximately 300 mm from ferrule to handle end, with a 32 mm handle and 190 mm of folded canopy. The nominal webbing is 239 × 24 mm, with 55 mm of hook material on the free end and 72 mm of loop material near the sewn end, on opposite faces. Choose a strap long enough for one complete wrap plus visible mating overlap. Before a robot trial, wrap it once by hand, release it and check that the closed wrap holds on the table.

A low-cost retail example is the Home Shopping Selections H67003 compact manual umbrella (£4.99 listed). Its product page confirms a hook-and-loop tie. Measure the item you use and record its dimensions; the retail listing gives no tie dimensions. To reproduce the simulated long tie, cut a 239 mm finished length of 24–25 mm woven polyester ribbon. Sew the two fastener patches around their edges and attach the loop end at the original tie seam with the hook facing inward when wrapped. Sew-on hook-and-loop tape is available in 25 mm widths. Record whether you used the stock or replacement tie. [Umbrella H67003](https://hssuk.co.uk/product/96cm-manual-umbrella/) · [Sew-on tape V25](https://www.profabrics.co.uk/products/sew-on-hook-and-loop-25mm)

Put a contrasting tape mark on the handle and marks at the strap seam and tip. Mount a phone looking along the shaft and put a ruler in the plane of the strap. Add a side view for the release. Put the dry umbrella horizontally in the left gripper, with the seam uppermost, the untied strap hanging to the right and both fabric faces clean. The YAM scene places the shaft 258 mm above a 747.5 mm tabletop and starts the open right gripper about 60 mm from the webbing. Record the open bundle's shaft-centred diameter before each run, using twice the greatest visible distance from the shaft centre to the folded canopy. Use the same scale and cross-section at the end. Undo the tie and restore the same loose folds before the next trial.

## Scoring the outcome

Read the terminal state. The wrap must stay closed under its own weight. A loose non-mating corner of the tie is acceptable if the sewn faces retain contact over part of their area. The score is the highest tier whose conditions all hold.

| Score | Observable requirement |
| --- | --- |
| 0.00 | The canopy is loose, or the handle is neither held above the worktop nor supported on the table after a controlled set-down. |
| 0.25 | The bundle's shaft-centred diameter is at most 80% of its loose reference diameter, and it is held or supported as above. |
| 0.50 | The tie also travels at least three quarters of the way around the shaft (4.7 radians in the simulator). |
| 0.75 | The left hand turned the handle at least once while the right guided the tie. At the end the strap goes around the canopy with visible overlap (at least 365° in simulation), and the aligned hook-and-loop faces are engaged. |
| 1.00 | The table supports the still-fastened umbrella after a controlled set-down. Both grippers are withdrawn at least 20 mm. The umbrella and free end stay still for at least one second and remain in that state at the end. |

For a real trial, follow the mark on the handle during the guided turn, trace the strap from seam to tip, compare the two end-on diameter readings and check retention and hand clearance in the side view. The simulation uses loaded table contact, clearance, and finite differences in the poses of the moving parts to verify those observations. Its one-second window spans 20 controls and limits speed to 0.022 m/s and 1 rad/s. The compactness reference for this model is approximately 49.7 mm in radius before wrapping. The 20% reduction is a benchmark definition of a gathered canopy, independent of a particular storage sleeve.

## Simulation and reproduction

Use the Inspect Robots YAM Arena adapter in an Isaac Lab environment with CUDA. Include this folder on the task loader's search path by running from inside it. The model uses a free shaft, twelve radially sprung canopy sections, fifteen hinged strap sections, and distributed hook-and-loop patches. Overlap, sustained measured normal load and separation of engaged material points govern attachment and peeling. The material properties approximate fabric and hook-and-loop tape and have not been calibrated to a retail umbrella. The scripted demonstrator uses simulator poses and contact forces. Dream-1 uses its policy interface.

```bash
python -m unittest -v
UMBRELLA_TRACE=1 bash run.sh yam_scripted
UMBRELLA_TRACE=1 bash run.sh dream
```

Each episode allows 1,800 controls at 20 Hz (90 simulated seconds) with zero starting-object jitter. The initial held handle and open right hand are part of the setup. For the model run, configure Dream-1 credentials using the adapter's normal login. The demonstration and model scores are recorded in task.json.
All umbrella and tabletop geometry is generated from primitives in this task. Robot geometry and station assets come from the upstream YAM Arena adapter.

Verified environment: Inspect Robots 1.0.0, Isaac Sim 6.1.0.0, Isaac Lab 17.0.2 and Isaac Lab Arena 0.3.0. Install the [YAM Isaac Lab Arena adapter](https://github.com/kairosiann/yam-isaac-lab-arena/tree/0059d02a1a91bc6834c1d0846022891df0c78730) at this revision. At control 640 the task refines the contact solver for thin fabric links on the same schedule for both policies. Use the included run script to reproduce the recorded timing.

## Recorded outcome

The scripted demonstration ends at control 1,185 (59.25 simulated seconds). The handle turned 360.1° under guidance and the strap remained wound 380.0°. At control 1,180 the canopy radius was 37.4 mm against a 49.7 mm loose reference, the tabletop carried 0.74 N and both grippers were clear. Throughout the qualifying second the maximum observed linear and angular speeds across all 28 moving bodies were 0.00614 m/s and 0.70324 rad/s. The scorer uses observed pose changes at physics substeps; the native velocity diagnostic still reported motion. The final score was 1.00.

Dream-1 ran all 1,800 controls on the same setup. It released the umbrella without guiding a turn or engaging the strap and scored 0.00. Both results are single runs on the fixed starting layout.
