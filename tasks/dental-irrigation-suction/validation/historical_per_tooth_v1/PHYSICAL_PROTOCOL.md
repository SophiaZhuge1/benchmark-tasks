# Water rig, video measurements and physical score sheet

Revision for PR #1160, 12 November 2026. **Proposed benchtop reconstruction, not tested hardware.** The existing videos show the simulated phantom. No physical pump output, suction recovery, pooling accuracy or human-use performance has been measured for this rig.

The action is **rinsing exposed crown-top regions while coordinating suction**. The task does not measure plaque removal or side/interproximal cleaning. Category: **Societal relevance**. All clearance values are benchmark definitions for an inert fixture, not clinical limits.

## 1. Build specification

Dimensions below are nominal design dimensions in millimetres. Unless otherwise stated, fixture tolerance is +/-0.5 mm; record as-built measurements. Global z is height above the tabletop; x/y follow the simulation station. The wet collectors, plumbing and measurement equipment are additional physical reconstruction components, not objects already demonstrated in the dry simulation.

| Component | Specification and placement |
|---|---|
| Base | 170 x 130 x 12 mm acetal plate, centred at (270,0), bottom z=0. Rigidly clamp to the table. |
| Gum surrogate | Pink acetal rails: two 115 x 28 x 18 mm at (270,+/-25,19), plus 28 x 70 x 18 mm front rail at (209,0,19). These are rigid fixtures, not tissue. |
| Crown surrogates | Six acetal cylinders, diameter 20 mm, height 14 mm, centres (235/270/305,+/-25,30); nominal crown plane z=37. Four rounded 4.5 x 4.5 x 3 mm half-ellipsoid cusps per crown at x/y offsets +/-4 mm. Three front acetal blocks 12 x 12 x 18 mm at (209,-18/0/18,35). |
| Other geometry | Pink rigid tongue ellipsoid, semiaxes 43 x 10 x 7 mm, centre (275,0,18). Match visible geometry without adding soft-tissue claims. |
| Active sites | Three crowns centred at **(235,25,37), (270,25,37), (305,25,37)**. Nine non-raised fiducials per active crown: centre plus eight sector centres. Use waterproof printed dots or engraved/painted marks; no simulated plaque. |
| Independent collectors | One transparent PMMA annular collector per active crown: outer diameter 32 mm, inner crown diameter 20 mm, floor z=31, rim z=39. Seal the crown base with a silicone gasket. Crown runoff enters its surrounding annulus. No shared liquid channel between sites; 35 mm site spacing leaves 3 mm between collectors. Provide a plugged side port for post-trial drainage and a separate overflow outlet leading to that site's labelled graduated catch vessel. Calibrate actual capacity, including cusp wetting; do not equate a drawn pool level to a measured volume. |
| Outer catch tray | 220 x 180 x 15 mm polypropylene tray under the phantom, outside the collectors. It catches missed delivery and splashes separately. Include a transparent splash enclosure around the bench area outside the robot envelope. |
| Tool handles | PETG blocks 28 x 24 x 55 mm, silicone grip band 29 x 25 x 20 mm centred 40 mm above each tool origin. Nominal whole-tool mass 75 g; weigh and record the physical value including attached moving hose. |
| Bent tubes | Rounded 316 stainless tubing: irrigator OD 5 mm, ID 3 mm; suction OD 9 mm, ID 7 mm. Centreline points relative to handle origin: (0,0,22), (0,s*25,22), (0,s*90,-9), (0,s*90,-25), where s=-1 for irrigation and +1 for suction. The downward outlet centre is the scoring tip. Real hollow tubes replace the simulation's solid visual proxies. |
| Tool stands | Acetal cylinders, diameter 50 mm, height 30 mm; origins at (280,200,30) and (280,-200,30). Match the initial tool orientation in `task.py`. |
| Irrigation source | Harvard Apparatus **Pump 11 Elite programmable syringe pump**, one 20 mL syringe, distilled water, nominal **24 mL/min = 0.4 mL/s**. Prime the complete 1 m, 2 mm-ID silicone feed hose and tool before reset; no trapped bubbles. Specify the fitted syringe diameter in the pump. |
| Timing controls | Microcontroller TTL/isolated interface to the pump and a normally closed, water-compatible pinch valve within 50 mm of the tool feed. A reset button starts the schedule and a visible LED in all videos. Log actual valve commands and visible outlet flow. Account for startup/shutoff delay by calibration at the outlet. |
| Suction source | **KNF N 838 family oil-free gas diaphragm pump**, isolated from water by collection traps, a secondary overflow trap and a hydrophobic filter. Use an adjustable vacuum regulator, relief valve, gauge and airflow meter. Initial commissioning setting: -10 kPa gauge at the trap; record actual flow under the assembled load. This is a design starting point, not a measured operating condition or a clinical specification. |
| Suction plumbing | Rounded suction tool to 150 mm of transparent silicone hose, 6 mm ID / 9 mm OD, then a low-dead-volume four-way liquid selector. The four outlets go to labelled, vacuum-rated **site 1, site 2, site 3, and unassigned** traps. Their headspaces join the protected vacuum manifold. Fix receiver vessels and valve to the bench; support flexible hose overhead with a slack service loop. Measure rather than assume hose drag and carryover. |
| Collection readings | Use removable 10 mL graduated inserts with 0.1 mL divisions inside the vacuum-rated traps; pipette their final contents into a calibrated 1 mL receiver with 0.01 mL divisions for fine readings. Do not subject a non-vacuum-rated graduated cylinder to vacuum. Include films and retained droplets by gravimetric cross-check using a 0.001 g balance. |
| Video | Synchronised top and two oblique views, at least 60 fps and sufficient resolution for <=0.5 mm tip/jet localisation at the crowns; macro side view(s) of each collector. Include reset LED, a length standard, the valve position and receiver labels. Keep raw timestamps. |

The collector annulus has nominal cross-sectional area pi*(16^2-10^2)=490 mm^2. A 0.45 mL pool corresponds to only about **0.92 mm** mean water depth in a flat annulus; 0.10 mL corresponds to about 0.20 mm. Consequently ordinary distant overview video is insufficient. Use empirical calibration images and macro views; do not infer pooling from the overview animation.

## 2. Commission the rig before scoring a robot

1. Calibrate the water density and every receiver/collector using known dispensed volumes and mass. For each assembled site, collect macro reference images from dry through 1.0 mL, in 0.025 mL increments around 0.10 and 0.45 mL. Include wet films, meniscus and occlusion in the error budget. Require pool-volume uncertainty <=0.025 mL and final recovery/loss uncertainty <=0.03 mL, or report the relevant threshold unverified. These are required calibration targets, not results.
2. Set the pump to 0.4 mL/s; run the complete schedule through the actual tip into weighed receivers. Require each five-second pulse to deliver 2.00 +/-0.02 mL and total 6.00 +/-0.03 mL. Measure actual opening/closing and wet-flow times on video; timing uncertainty target <=1/60 s. Compensate pump and valve delay so **flow at the outlet**, not merely the command, matches [16,21), [24,29), [32,37) s. Record any off-window drips as supplied water and loss; do not erase them from the balance.
3. Run the suction source continuously from t=0 to the endpoint. With an independent test reservoir, measure water removal at the reference tool pose, including the proposed 10 mm tip height and approximately 17 mm lateral offset. Map several offsets/heights, reversed orientation, blocked tip and air-only operation. A gas-flow specification does **not** establish 0.65 mL/s water recovery. Calibrate the regulator against water recovery; do not claim the simulator's suction law from a pump datasheet.
4. Calibrate selector transit time, switching dead volume and line retention with small visible dyed-water pulses in a separate commissioning run; flush and dry before the scored distilled-water trial. Bound carryover per switch to <=0.02 mL or include a larger bound in every affected site's uncertainty. Film retained in the common line is not zero simply because it looks empty.
5. Confirm that the collectors are isolated and collect their own overflow. Measure a no-action evaporation/film blank over 60 s. Verify camera reconstruction of known tool positions, angles and clearances; record the actual achieved uncertainty.

**Hardware feasibility gate:** if the elevated tip cannot remove enough real water while remaining outside the working-area exclusion zone, the current suction model overstates feasibility. Do not hide this by connecting invisible drains, assigning recovered volume from the simulation or silently lowering the real tip. Revise the suction model/geometry, rerun the full demo and controls, and record new media. No such physical commissioning has yet been performed.

## 3. Trial schedule and site-specific recovery

Start with dry collectors, empty tared receivers, primed irrigation line, and no water in the suction line. Fixed layout, seed 1, no jitter. Use the instruction in `task.json`. Robot limit: 1,200 steps / 60 s. The scheduler opens irrigation at 16-21, 24-29 and 32-37 s; it must not wait for the robot to become ready. Show the upcoming/active site with the corresponding LED at (235/270/305,72,20) mm. LEDs are timing cues; coverage is judged from video afterward.

Record recovered liquid by **the pool actually aspirated**, not by which tooth is scheduled. An independent instrumentation operator or camera-tracked selector routes to site i only while video establishes that the inlet is collecting exclusively from collector i. Switching does not change the vacuum setting, tool movement or irrigation. Before changing the selected receiver, keep that assignment through the calibrated line-clearance interval after the last liquid bolus. Route all ambiguous, mixed or transitional collection to the fourth receiver. A late return to a previous site must route back to its receiver; the timer alone cannot determine source.

This instrumentation must not help the robot recover water. If selecting a branch changes suction, the rig fails commissioning. Keep a continuous video of selector states and line boluses. If two collectors could supply the tip, source cannot be seen, or carryover cannot be bounded, retain an interval of possible per-site recovery; do not arbitrarily credit the current site. Unassigned liquid is still recovered water in the **total** balance but cannot be confidently credited to any one site.

At the endpoint, stop both flows and close the irrigation valve. Record all pool levels, then separately drain each collector into its labelled fine-scale receiver. Measure any retained film by weighing the removable collector/crown assembly against its dry tare. Weigh receivers before optional transfer, to detect transfer loss. Include late water residing in the suction tool/hose as unresolved inventory until attributed; do not manufacture a site assignment from the desired score.

## 4. Video-to-measurement procedure

Use video/manual annotation and calibrated geometry; **do not rerun `WaterModel` to fabricate physical recovered or pooled volumes**.

| Quantity | Practical measurement and threshold |
|---|---|
| Delivered volume at site i | Integrate measured outlet flow over frames with the active jet demonstrably reaching the target: irrigator axis z<-0.94, tip height 8-30 mm above z=37, and projected impact radius <=10 mm. Require >=1.8 mL. Compare projected intersection with the visible wet footprint; divergence is a model discrepancy, not assumed coverage. |
| Centre dwell | Sum only time with water flowing and projected impact radius <=2.5 mm. Require >=0.15 s for each site's centre. |
| Sector dwell | For 4.5<=radius<=9.5 mm, assign `floor((atan2(dy,dx) mod 2*pi)/(pi/4))`; sector 0 begins along +X and increases toward +Y. Each of eight 45-degree sectors needs >=0.15 s while flowing. The 2.5-4.5 mm gap and 9.5-10 mm edge earn delivery but no dwell credit. |
| Recovery | Fine graduated reading of the site's assigned receiver, corrected for measured line inventory/carryover with its uncertainty. Require >=1.8 mL for each completed site. Keep unassigned receiver separate. |
| Final pool | Endpoint calibrated macro view, checked by separate drainage/film measurement; <=0.10 mL for each completed site. Residual water on that site's crown is part of its retained pool. |
| Peak pool | Maximum calibrated pool volume over **the full trial**, per site, including before overflow. Use frame-by-frame macro video. Full score requires max across sites <=0.45 mL. A final dry tooth does not prove this. For gaps between frames, bound unseen accumulation using maximum measured incoming flow times the gap; an occluded interval without a bound is unverified. |
| Total loss | Measured total supply minus all assigned recovery, unassigned recovery and endpoint pooled water, with unresolved line/film inventory reported separately. Cross-check outer spill tray and site overflow vessels by volume/mass. Full score requires <=0.30 mL; never count the same overflow twice. |
| Obstruction | During active irrigation, suction tip XY radius <9 mm from the active centre AND z<65 mm. Sum obstruction across all three pulses, not just the longest event. Permanent failure if total >0.25 s. |
| Tip separation | Three-view Euclidean tip-centre separation >6 mm throughout. A measured value <=6 mm is permanent failure. |
| Gum guard | For either tip: 195<x<340 mm and abs(y)<45 mm defines the guard footprint; z<30 mm within it is permanent failure. |
| Low tool origin | Either tool origin at or below z=5 mm is permanent failure (`task.py` requires z>5). |
| Retention | At endpoint, at least one fingertip of the assigned arm is <35 mm from that tool's handle reference (0,0,40) in tool coordinates. Report this as the existing proximity proxy, not proof of grasp force. |
| Withdrawal | Each tip has z>80 mm OR abs(y)>75 mm at endpoint; the latter is measured from world y=0, not distance from the tooth. Full success must hold 1 s. |

For every frame interval, classify a region only when position/axis uncertainty remains inside its boundaries. An uncertain boundary frame contributes to the **upper bound** on dwell, not the lower bound. At 60 fps, 0.15 s equals nine full frame intervals, but count actual timestamp differences, not nine isolated images. For 20 Hz comparability, retain both the native video measurements and any 20 Hz subsample; a between-frame physical collision must not be erased by subsampling.

For each metric report [lower,upper]. Pass an upper limit only with upper<=limit, a lower limit only with lower>=limit, and preserve strict inequalities from the table. If a bound crosses a threshold, report indeterminate and re-measure/repeat; do not round into a pass. A measured failure scores zero; an occluded or missing record is **unverified**, not a measured zero.

## 5. Score and accounting

After the corresponding pulse has ended, a site is complete only when all nine dwell requirements, delivered>=1.8 mL, recovered>=1.8 mL and final pool<=0.10 mL pass. With no permanent failure:

- Zero, one, two or three completed sites earn 0, 0.25, 0.50 or 0.75 respectively.
- Upgrade three complete sites to 1.0 only if total loss<=0.30 mL, peak pool<=0.45 mL, both endpoint retention/withdrawal gates and the one-second full-success hold pass.
- Failure of a full-score-only gate leaves 0.75 when three sites otherwise qualify. It does not erase partial credit.
- Any permanent guard/obstruction/invalid-state failure overrides all milestones to zero.

Use a physical water ledger:

```
supplied = assigned_recovery + unassigned_recovery + final_pools
           + measured_spills + unresolved_line_and_surface_inventory
           + evaporation_or_other_unaccounted_loss
```

Measurements must close within their propagated uncertainty. Keep nonnegative intervals for ambiguous inventory; do not put a negative balance error into "loss" to obtain full credit. The geometry-derived delivered volume and the per-site recovery/pool/overflow must also be consistent. If missed irrigation runs into a collector or water crosses sites, document it and bound attribution; where it cannot be resolved, the simulated per-site accounting is not physically verified.

## 6. Remaining fidelity differences and evidence status

The enlarged crowns, collector cups, regulated aspiration, hoses and measurement valves form a training fixture. They are not a clinical mouth. The original simulation has rigid decorative crowns, no wet collector hardware or hose drag, a lumped pool per site, a 0.45 mL numerical overflow capacity, and a geometric conductance curve with 0.65 mL/s maximum suction. Real collector volume can exceed 0.45 mL; exceeding the **benchmark peak threshold** still prevents full score even if the physical cup has not overflowed.

Real wetting, surface tension, splashing, film retention and aspiration through an elevated inlet must be commissioned. The simulation's blue pool overlay has coarse levels and cannot demonstrate the proposed macro-video measurement resolution. The visible common vial is a simulation indicator, not evidence of real per-site measurements. Physical tip-centre separation also does not certify clearance between whole shafts or arms.

The revised wording uses "Rinse"; the archived Dream-1 run used "Clean ... with circular rinsing motions". Physics/scoring remain unchanged in this revision. A fresh Dream-1 run with the final instruction and refreshed media are required before treating it as the model trial for the revised submission. Hardware construction and calibration remain outstanding separately.

## Equipment references checked 12 November 2026

- [Harvard Apparatus Pump 11 Elite manual](https://support.harvardapparatus.com/hc/en-us/article_attachments/31241958761107): programmable pump, syringe sizes and I/O. Its rated flow range supports the proposed 24 mL/min supply; actual installed output must be measured.
- [KNF N 838](https://knf.com/en/global/solutions/pumps/series/diaphragm-gas-pump-n-838): oil-free gas/vapour pump, up to 34 L/min rated gas flow. This is **not** a water-recovery rating; keep water out of the pump and measure performance through the actual protected circuit.

These references identify components, not a tested water rig or clinical operating procedure.
