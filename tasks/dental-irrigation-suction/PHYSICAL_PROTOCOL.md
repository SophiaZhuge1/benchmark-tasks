# Mouth-water v4: affordable physical reconstruction and scoring

Equipment revision: 15 November 2026. **Untested benchtop reconstruction on an inert phantom.**

The current build is [EQUIPMENT.md](EQUIPMENT.md): standard peristaltic pumps, stock tubing, printed PETG fixture and ordinary camera/balance measurements. It supersedes the earlier specialist-pump procurement requirements. Geometry and simulation scoring remain v4. This retains the mouth-water model and adds measured post-rinse cleanup and return to the original stands. The older held-and-withdrawn endpoint is superseded. The current score measures total water retained in the mouth, including crown films and floor pools. Simulation results do not establish clinical safety or real suction performance.

## Procedure and equipment context

The represented procedure is the **water-rinsing and evacuation stage after professional air polishing during dental prophylaxis**, applied to three marked crown tops. Polishing itself, powder, plaque removal, saliva, aerosols, swallowing and airway behaviour are outside this task. A dental air/water syringe operated in water-only mode provides the real-world analogy for the blue tool; the white tool represents an evacuation tip. Neither a basin threshold nor a tool clearance here is a patient-treatment limit.

Dentsply Sirona's Cavitron JET Plus instructions describe rinsing groups of one to three teeth during air-polishing work and using adequate evacuation. This supports the workflow context, **not** our timing, water quantities, synthetic anatomy or suction law. We use calibrated low-cost peristaltic pumps and stock tubing on printed handles for repeatability; the simulation does not reproduce a Cavitron device.

## Reconstructable fixture

Dimensions are mm; nominal tolerance +/-0.5 mm unless calibration establishes a tighter bound. Record the as-built geometry. Coordinates are relative to the tabletop; the phantom centre is (270,0). Initial tool stands are at (280,+200,30) and (280,-200,30).

| Component | Specification |
|---|---|
| Base and gums | Printed PETG base 170x130x12; two pink PETG rails 115x28x18 centred at (270,+/-25,19), plus front rail 28x70x18 centred at (209,0,19). Clamp the base. |
| Teeth | Six PETG crowns, diameter 20, height 14, centres (235/270/305,+/-25,30); crown plane z=37. Four rounded cusps per crown, half-ellipsoid radii 4.5x4.5x3 at x/y offsets +/-4. Three front blocks 12x12x18 at (209,-18/0/18,35). |
| Tongue | Rigid pink ellipsoid with semiaxes 43x10x7 centred at (275,0,18). A geometric fixture, not soft tissue. |
| Mouth-floor cells | Three open wells centred at (235/270/305,0,31), internal floor 28x18 each. Floor top z=31; side walls 1 thick, inner faces y=-9 and y=9, top z=34.5. Use 1 mm clear PET sheet for the physical measurement windows and a silicone seal at seams. Simulation walls are opaque pink for visibility. |
| Cell connections | Between adjacent cells, channel length 7, width 3, floor top z=31, with sealed sides. The real gutters allow water redistribution. Their transit volume must be included in total retained mouth water; the reduced-order model treats connections as zero-storage conductances. |
| Runoff guides | Removable transparent PETG strips slope from each treated crown's lingual edge toward its floor well; channel width 6, fitted from the inner crown edge (nominal y=15,z=37) to the cell (y=9,z=31). Seal seams; include their retained film in the mouth inventory. The model displays runoff paths but does not solve flow over these surfaces. |
| Overflow and catch | Use the open well rims and an external catch tray; no precision overflow standpipes are required. Measure any overflow as loss. The physical rim capacity need not reproduce the simulator's 1 mL per-cell clipping because the whole-mouth 1 mL limit fails first. Include a 220x180x15 polypropylene spill tray below the fixture. The model clips each well at 1.0 mL. The **score limit of 1.0 mL is total mouth water**, so a run can fail before any individual well overflows. |
| Tool handles | PETG 28x24x55; silicone grip band 29x25x20 centred 40 above tool origin. Target mass 75 g including moving hose; record actual mass. |
| Hollow bent tools | Stock hollow silicone tubing on rigid supports: irrigation OD5/ID3; evacuation OD9/ID7. Centreline points relative to handle: (0,0,22),(0,s*25,22),(0,s*90,-9),(0,s*90,-25), s=-1 irrigation, +1 suction. Outlet plane is the tracked tip. Physical tubes are hollow; simulated collision/shaft geometry remains solid with a visible dark opening. |
| Racks | Printed PETG cylinders diameter50,height30; basez0,centrez15,topz30 at XY(280,+200)/(280,-200). Tool origins start atz30 on the tops. |
| Water source | Adafruit 1150 12 V peristaltic pump, water reservoir and primed silicone hose; target measured 24 mL/min. See EQUIPMENT.md for connections and calibration. |
| Timing | Arduino Nano Every and protected motor drivers; supplied `hardware/pulse_controller.ino`, visible start LED. Actual outlet windows16-21,24-29,32-37 s; target0.40 mL/s. Commission ten five-second pulses at1.90-2.10 mL each, record actual flow/drips and use measured quantities in scoring. Schedule never waits for robot readiness. |
| Evacuation source | Second Adafruit 1150 peristaltic pump; target measured water recovery0.65 mL/s at a submerged inlet. No gas vacuum system or vacuum-rated trap. Test actual near-surface pickup and dry-inlet behaviour separately; catalogue flow is not proof. |
| Suction plumbing | Distal OD9/ID7 tube ->150 mm transparent ID6/OD9 hose ->barbed reducer ->pump tubing ->open collection cup. Support slack; record liquid holdup and transport delay. One combined receiver; never infer per-tooth source identity after water mixes. |
| Volume metrology | Mercury456.047UK 50 g/0.001 g pocket balance, tared small cups/absorbent strips, needle-free1 mL and10 mL syringes, thermometer and ruler. Verify accuracy/repeatability; do not place the whole fixture on this balance. Detailed collection and uncertainty method: EQUIPMENT.md. |
| Video | Three existing1080p/60 fps phones/action cameras, one overhead and two close oblique views, printed grid, diffuse lamp and common start LED. Verify <=0.5 mm jet/tip resolution. No scientific high-speed camera or motion-capture system. |

All fitted dimensions must permit the two tools to reach their targets without collisions. A commercial dental chair or suction line must not be assumed equivalent to this metered inert rig.

## Calibration and trial procedure

1. Measure distilled-water density at the trial temperature. Calibrate supply, receiver and complete mouth inventory using known weighed syringe-delivered volumes and gravimetry. For the floor wells and crown/guide films, record macro reference images at 0.05 mL increments; add denser calibration around total 0.50 and 1.00 mL. Include channel water and surface films. Target peak-mouth uncertainty <=0.05 mL, final-mouth uncertainty <=0.01 mL, and recovery/loss uncertainty <=0.03 mL; these are acceptance targets, not achieved results.
2. Calibrate actual pulse flow at the nozzle into weighed receivers. Record outlet start/stop delays and drips. Include off-window drips in supplied volume and its physical location. Prime before reset; collectors and suction line begin empty, crowns/fixture dry.
3. Measure suction recovery over a grid of inlet x/y/z positions and orientations with known water levels. The intended inlet is inside the wet mouth-floor region, nominally z=32 (1 mm above its floor). Test wrong side, dry cell, high tip, reversed tip and blocked tip. The model's 1.5 mm surface-reach approximation needs experimental validation; a dry inlet must not gain credit for remotely removing water. Record liquid retained in the suction line and calibrate transit delay. If the real inlet cannot recover enough water at a collision-free pose, change geometry/model and rerun before claiming physical feasibility.
4. Calibrate redistribution between floor cells and guide/crown drainage. The current model uses a 0.20 s exponential crown-drain time and 0.08/s neighbour volume-equalisation coefficient; these are declared approximations, not measured properties. Build verification must establish whether the physical behaviour supports the task.
5. Start at reset, fixed seed/layout, both tools on their racks and all liquid inventory zero. Irrigation begins at t=16 s regardless of tool readiness. Suction runs continuously. The robot has 1,200 steps /60 s, picks up both tools, sweeps the crowns and positions suction at accessible wet floor pools, then lifts only the irrigator, keeps suction in the mouth until cleared, and finally returns and releases both tools on their original stands.
6. Record every camera and supply/suction trace throughout. At endpoint record the one-second hold, then stop flows and collect remaining mouth water, including films and channel inventory, into tared small cups/strips. Weigh those within the 50 g balance capacity; do not weigh the complete fixture. Account for line water separately. No hidden drain may remove water without appearing in recovered volume or spill loss.

## Measurements and exact scoring

**Mouth water W(t)** = all water on the crowns, runoff guides, floor wells and connecting channels. Water inside the suction hose is recovered inventory only after it crosses the inlet; receiver delay and line holdup must be calibrated. Water outside the mouth is loss. Supply = recovered + W + loss, within measurement uncertainty.

| Quantity | Method | Threshold |
|---|---|---|
| Crown delivery | Calibrated outlet flow integrated over video frames whose projected wet jet reaches that crown: axis z<-0.94, height8-30 above z=37, impact radius<=10. | >=1.8 mL per completed tooth. |
| Regional dwell | Timestamped wet-impact video. Centre radius<=2.5; eight 45-degree sectors within radius4.5-9.5. Sector0 begins at +X, increases toward +Y. Gap/edge areas can earn delivery but not dwell. | >=0.15 s in **each** of nine regions per completed tooth. Dry motion earns zero. |
| Peak mouth water | Maximum over **all times**, summing calibrated crown/guide films and every pool/channel in synchronized macro frames. Cross-check against cumulative measured supply minus recovered/spilled water, correcting line delay. | <=1.00 mL total throughout. Late removal does not undo a violation. |
| Endpoint mouth water | Final macro estimate, then separately collect/weigh all fixture water and films in tared cups/strips (EQUIPMENT.md). | <=0.50 mL for partial credit; **<=0.05 mL for full score**. |
| Recovered water | Combined graduated receiver plus measured liquid still in suction hose/tool downstream of inlet; gravimetric cross-check. | >=90% of total supplied; nominally >=5.40 mL from 6 mL. |
| External loss | Whole-trial supply minus recovered minus endpoint W. Cross-check overflow vessels and spill tray; include unresolved surface inventory in uncertainty. | <=0.30 mL. Never improve a score by assigning a negative balance error to loss. |
| Tip separation | Reconstruct both tip centres from calibrated views. | >6 mm at all times. |
| Gum guard | Either tip in 195<x<340 and abs(y)<45, but below z=30. | Any entry fails permanently. |
| Tool-origin guard | Either tool origin z<=5. | Any entry fails permanently. |
| Working-area obstruction | Suction within 9 mm XY of active crown centre and z<65 during flowing pulse; sum across pulses. | Total <=0.25 s. |
| Retention | At least one assigned-arm fingertip within35 mm of each handle reference (0,0,40). | Diagnostic during use only; holding the tools at endpoint no longer earns1.0. |
| Withdrawal | Each tip z>80 OR abs(y)>75 at endpoint. | Both tips clear at the returned-and-released endpoint. |

Use [lower,upper] measurement bounds. An upper-limit test passes only if upper<=limit; lower-limit tests pass only if lower>=limit. Preserve strict inequalities. Boundary-overlapping, occluded or missing records are **unverified**, not rounded passes or measured zeroes. At60 fps, 0.15 s is nine complete intervals, not nine individual stills. Bound unobserved inter-frame peak increases by maximum measured inflow times the gap. An overview picture alone is insufficient to establish the peak.

**Score decision order:**

1. Any measured guard failure, loss>0.30 mL, peak W>1.00 mL, endpoint W>0.50 mL, or recovery<90% supplied gives **0**. These water gates apply to every tier.
2. Otherwise count fully rinsed teeth, after their own pulse has ended: zero/one/two/three earn **0/0.25/0.50/0.75**.
3. Upgrade three completed teeth from0.75 to **1.0** only when the full finishing sequence below passes and total mouth water is <=0.05 mL. Hold the final returned/released state continuously1 s.

### Full-score finishing sequence

- After the final pump pulse ends (t>=37 s), the rinsing tip lifts above z=80 mm. Suction remains in the mouth and continues running. Its tracked tip must lie within x=221-319 mm, abs(y)<=9 mm, z=30.5-32.5 mm, with downward axis z<-0.94. This is the declared inert-fixture working region.
- Require at least **1.0 continuous second** of this post-rinse arrangement, and measured total mouth water <=0.05 mL, before marking cleanup complete. Include all floor regions and crown films; emptying only the final tooth's region is insufficient. The scripted demo targets <=0.005 mL, leaving margin below the scoring limit. Exactly zero is not a realistic physical measurement requirement.
- Only then withdraw suction and return **both** tool origins to their original stands: irrigator(280,200,30), suction(280,-200,30) mm. Require XY error<=10 mm, Z error<=5 mm, orientation error<=10 degrees from the original pose, and speed<20 mm/s for each tool.
- Open both grippers and move every fingertip >65 mm from each tool's handle reference(0,0,40) in tool coordinates. Both tools must remain settled on the stands for1 s. Holding a tool above its stand, swapping stands or leaving a tool in the mouth does not pass.
- Measure the sequence from synchronized timestamped video; record final near-dry volume by calibrated macro views and endpoint drainage/gravimetry. Use uncertainty intervals; if the upper volume bound exceeds0.05 mL, do not claim full score. Record rack offsets, orientation, speed and minimum fingertip distances.

A run that meets all water/coverage requirements but returns early, omits cleanup, omits return or omits release earns at most0.75. Exceeding the general water/guard limits still gives0. A good final rack photograph alone cannot establish the required earlier cleanup sequence.

Empty-mouth/no-action cannot pass: it completes no rinsing regions and loses the scheduled water. Point rinsing with excellent suction cannot pass: it misses the eight outer regions. Correct rinsing with wrongly placed suction cannot pass: water remains in the mouth or spills. Flooding first and suctioning later cannot pass: peak history and loss persist. Per-site recovered volume is no longer a scoring requirement because water can mix; earlier 0.45 mL per-tooth peak and separate recovery traps are superseded.

## Fidelity and evidence limits

The simulator conserves water across supply, three crown inventories, three connected floor pools, recovered water and loss. Droplets/streams visualise these transfers; they are not independent physics particles or a CFD solution. Pool depth follows volume/area. A single finite suction budget is allocated only to reachable wet cells; tip height, orientation and local water surface affect capture. Fluid geometry is simplified; no soft tissue, swallowing, breathing, saliva or clinical harm is modelled. Blue is a visibility cue for simulated water; physical validation uses distilled water unless a separately calibrated tracer is declared.

Physical peak measurement, wetting, suction reach, guide drainage, line drag and collision-free access remain unvalidated. Current v4 simulation evidence is media M-XPKWYY: Dream-1 beta0.0 and demo1.0. Earlier per-tooth recordings are historical. The equipment revision changes no runtime source or scoring; it does not establish real hardware performance. **Do not claim these thresholds are safe patient mouth-water levels.**

## References

- [Dentsply Sirona Cavitron JET Plus instructions](https://www.dentsplysirona.com/content/dam/master/product-procedure-brand-categories/preventive/product-categories/ultrasonic-scaling/table-top-units/cavitron-jet-plus-ultrasonic-scaler-and-air-polishing-prophylaxis-system-with-tap-on-technology/documents/PRE-IFU-Cavitron-Jet-Plus-Ultrasonic-Scaler-and-Air-Polishing-Prophylaxis-System-with-Tap-On-Technology-2020-05.pdf), section9.8: workflow context only.
- [Adafruit1150](https://www.adafruit.com/product/1150): standard peristaltic pump; actual flow, pulsation and near-dry recovery need calibration.
- [Affordable equipment, prices and assembly](EQUIPMENT.md).
