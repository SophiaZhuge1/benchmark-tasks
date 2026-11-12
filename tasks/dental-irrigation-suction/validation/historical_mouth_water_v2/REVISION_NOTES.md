# PR1160: mouth-water revision for owner review

Local draft, not pushed. User requested visible nozzle-to-tooth-to-mouth flow, actual location-dependent suction, total mouth-water scoring and a specific dental procedure/equipment context.

- Added crown inventories, drainage, connected floor pools, pool-surface-dependent capture, actual-flow animations and total-mouth metrics.
- Replaced per-tooth peak/recovery scoring with total mouth water: peak<=1.00 mL, final<=0.50 mL, loss<=0.30 mL, recovery>=90% supplied. These gate every score tier; peak/loss cannot be erased by late cleanup.
- Kept measurable regional wet coverage and explicit partial credit; added wrong-place and raised-tip controls.
- Added mouth-floor fixture geometry, lowered intended suction to the water, and increased withdrawal lift to preserve endpoint clearance.
- Specified the rinse/evacuation stage after air polishing, custom water-only dental-syringe and evacuation surrogates, metered pump, protected vacuum circuit and revised physical measurements.
- Removed the need to assign mixed recovered water to an originating tooth. This deliberately supersedes that part of the earlier reviewer response; the total collected volume and total mouth-water inventory are now the scored quantities.

Historical per-tooth recordings and documentation are preserved as historical. Model tests do not verify real suction reach or clinical performance. New robot controls, final Dream-1/media and owner review are required before resubmission; nothing has been pushed.

Robot feasibility iteration: added an above-mouth approach before descent and widened/recentred the mouth-floor wells to28x18 mm at y=0 so the9 mm suction tool can enter without the prior side-wall interference. Full-score water limits remain unchanged. The initial failed builds and narrow-well rollout are retained as development diagnostics, not successful evidence.

The scripted suction controller now uses measured tip-position feedback during each pulse, through normal arm actions, to correct millimetre-scale height/position error. It does not set water volumes, object poses, coverage or reward. The wider-well open-loop rollout still exceeded the peak-water limit and is retained as a failed development trial.

## Recorded robot results: mouth-water v2

Three fresh CPU-PhysX / RTX-rendered scripted trials, seed1, zero jitter, 20 Hz. These are robot rollouts, not the prescribed-coordinate model comparisons.

| Approach | Score | Regions covered | Peak total mouth water (mL) | Final mouth water (mL) | Recovered (mL) | Lost (mL) |
|---|---:|---:|---:|---:|---:|---:|
| Correct rinse and local suction |1.0|27/27|0.4650|0.2222|5.7778|0.0000|
| Suction at the wrong location |0.0|27/27|2.8960|2.8131|0.0000|3.1870|
| Point rinse with working suction |0.0|3/27|0.8883|0.3569|5.6431|0.0000|

All three retained and withdrew both tools, with no guard failure. The wrong-place run isolates failed water recovery despite complete coverage. The point-rinse run passes the water gates but misses the outer crown regions. Reported per-cell capture counters describe the location of aspiration, not which tooth originally supplied mixed water.

Three synchronized native640x360 views at20 fps and full source/metric traces are retained. Review labels are added after recording; they are not policy inputs. Old per-tooth runs and initial development failures are not evidence for the revised positive result. Current instruction and runtime sources are frozen in each run; final explanatory documents are updated afterward. Fresh Dream-1 and hardware trials remain pending.

[Current recorded evidence and source/video hashes](validation/mouth_water_v2/recorded_results_20261112.json). Initial, active-rinse and endpoint frames were inspected in all three camera views.
