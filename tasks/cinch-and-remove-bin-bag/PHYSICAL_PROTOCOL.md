# Physical setup, closure and scoring

## Objects and fixed layout

Distances below are metres unless marked otherwise. The station frame has arm mounts at `(0, +0.305, 0.750)` and `(0, -0.305, 0.750)`, facing +x; y is lateral and z is vertical. The floor is z = -0.0125. This is a real small countertop-bin specification, not a scaled claim about large refuse collection.

| Object | Type, size, material and reset |
|---|---|
| Robot station | Two standard six-joint YAM arms with parallel grippers; 610 mm base separation; existing overhead and two wrist cameras. Diagnostic overview camera is not a policy input. |
| Table and mat | Wood table, 1100 x 1300 x 60 mm, top z = 0.7475; centre xy = (0.36, 0); 800 x 1000 x 2.5 mm rubber mat centred at (0.35, 0), top z = 0.750. |
| Bin | Rigid plastic small open cylinder, approximately 186 mm inside diameter, 212 mm outer envelope, 150 mm wall height; xy centre (0.22, 0); rim z = 0.918. A 190 x 190 x 12 mm plastic bottom plate has centre z = 0.756. Secure the base to the work surface; static segmented walls approximate this secured bin. |
| Loaded liner | Flexible polyethylene film, nominal 0.10 mm thickness, 172 mm body diameter, 180 mm open mouth and 250 mm authored height; base initially at z = 0.768; xy centre (0.22, 0). The upper 115 mm is spare neck material, initially unfolded. Initial settling is allowed; begin the recorded trial with an open mouth of at least 100 mm and all contents inside. |
| Drawcord | One continuous approximately 2 mm braided cord routed through the mouth hem with opposed pull-out bights. Reset routed length is set from the initial geometry plus 2 mm slack. For physical construction, thread the actual hem and adjust the free bights to the specified toggle starting positions, without pre-cinching. |
| Two pull handles | Polymer grips, 18 x 14 x 24 mm, 6 g each; centres (0.22, +0.22, 0.762) and (0.22, -0.22, 0.762), resting free on the mat. Each grips a bight, not a preclosed neck. |
| Two tethered cord locks | Pull-to-tighten, separately released cord-lock design: ITW Nexus Cyberian CL Small 350-8200 or an equivalent with the same operation, approximately 23.8 x 16.0 x 7.4 mm; acetal body with steel internal element. Attach to reinforced hem exits at opposite sides. Thread bight strands so outward handle pull tightens the hem and reverse feed is resisted after release. The simulation depicts housings at hem markers 5 and 15 and models their combined holding action. |
| Six inert contents | Six clean closed rigid polypropylene mock-waste blocks, each 58 x 100 x 40 mm and 25 g. Two columns at x = 0.19 and 0.25, y = 0, three rows with centre z = 0.786, 0.827, 0.868; identity rotation at reset. Use clean lightweight material, not biological waste, sharps or liquids. |
| Camera stand | Fixed standard station mast, foot and crosspiece generated from the calibrated overhead-camera pose; retain the station placement and do not add a hidden support for the bag. |

The simulated hem's 20 small markers are numerical seam mass/tension points, not 20 additional physical accessories. Twenty 1 g marker masses lump hem/lock inertia; the actual manufacturer's individual lock inertia is not resolved. Their film attachments represent sewn/reinforced hem connections, not robot grasps.

For the cord topology, proposed assembly sequence and unperformed physical preflight, see [ASSEMBLY_GUIDE.md](ASSEMBLY_GUIDE.md) and [cord-routing.svg](cord-routing.svg).

## Why closure holds without a knot

The specified liner has **tethered pull-to-tighten cord locks**. The grippers pull the free handles; the housings stay at the hem. The manufacturer describes tightening by pulling the cord and loosening by pulling the housing/tether, without pushing a small plunger. The task never requires operating the release during execution.

This is a reproducible fixture-assisted drawstring liner, not a claim that every ordinary supermarket liner has self-locking drawstrings. The manufacturer reference establishes a real operating principle and dimensions, not validation of the simulator's force constants or of this bag assembly. Before physical trials, verify that the constructed hem, tethers and selected cord cooperate as described and that the 150 g load stays contained after release. Hardware testing has not been performed by this simulation work.

Source: https://eu.itwnexus.com/content/cyberian-cordloc

## Reset

1. Remove the previous liner and inspect it for damage; replace damaged film. Open both cord locks by their release operation and restore the open neck.
2. Install the liner base inside the secured bin, with the neck unfolded upward. Place all six blocks at the listed positions; the top row must remain below the mouth.
3. Lay the two handles at their specified mat positions, route both free bights without tangles and leave the neck open; do not pretie, preclose or attach the bag to a robot.
4. Return the arms to the standard ready configuration. Capture the setup image, then begin the 4,000-step budget from the recorded initial state; include subsequent settling/actions in that budget.
5. Clear the tabletop placement area and keep the overhead stand/table fixed. There is no artificial event, label choice or scheduled interruption.

## Ruler/video scoring

Use fixed overhead and side video with a ruler/grid in the bag's plane, a stopwatch or frame timestamps, and a final six-object inventory. Camera calibration uses the known bin and table dimensions. Do not insert measuring tools into the bag during the robot trial.

- **Opening:** measure the greatest straight-line distance across the mouth boundary, not average radius or a convenient projection. For a tilted mouth, use two views or inspect the final state after the trial without changing its closure. Record whether opening ever reached 50 mm or less, and whether the final opening is 60 mm or less.
- **Retention:** watch for any of the six blocks crossing out of the bag; after scoring, open it manually and count six. Replacing an escaped block does not erase a spill. If video occlusion prevents determining whether a spill occurred, mark the trial unverified and repeat/inspect, rather than guessing a success.
- **Clearance:** for the final two seconds, the lowest bag/content point is at least 20 mm above the rim, or every part of the load is at least 20 mm beyond one side of the bin's outer bounding envelope. A tabletop deposit may satisfy the side-clearance alternative directly; a prescribed high-lift pause is unnecessary.
- **Table support:** the bottom must be within 25 mm of the table top (z = 0.7475 m), and the bag must be visibly supported there. The 2.5 mm work mat is part of this support surface. Every film vertex and content-box corner must project at least 20 mm inside all four table edges: x in [-0.170, 0.890] m and y in [-0.630, 0.630] m. The whole load must also clear the bin by 20 mm. Any clear landing position is acceptable.
- **Release/rest:** during the final two seconds both grippers stay at least 60 mm away from film and handles, and the six extrema of the visible bag (left/right, front/back, bottom/top) each vary by no more than 10 mm over the whole interval. Measure using calibrated overhead and side views. Internal content velocity is diagnostic only and is not a condition for success; harmless internal settling is allowed.
- **Damage:** score zero if destroying the bag is used to bypass closure/extraction or if contents escape. Do not translate the simulator's strain bound into a purported physical tear measurement.

Award the highest of 0, 0.4, 0.7, 1.0 whose conditions are established. A bag still held above the table can earn 0.7; an open/reopened bag cannot. No condition requires a particular wrist orientation, motion speed, sequence of corrective grasps or exact tabletop landing spot.

## Simulation measurements and limits

The primary simulation scorer uses the same geometric thresholds. It checks all content-box corners and film vertices for removal, and corners/centres/face centres against the **non-convex film mesh** for containment, with a 5 mm contact tolerance. A virtual cap closes the mouth for the inside/outside calculation only; it exerts no force and is not rendered. Highly self-intersecting film and finite sampling remain approximation limits. Non-finite/incomplete evidence or edge stretch over 1.5 invalidates the simulation trial; hardware retention is judged directly. No upper bag-height cap is imposed on an otherwise settled tabletop result.
