# Physical setup, ordinary closure, reset and scoring

Distances are metres unless marked. Station frame: arm mounts at `(0, +0.305, 0.750)` and `(0, -0.305, 0.750)` facing +x; y lateral, z up; table top z = 0.7475, rubber mat top z = 0.750.

## Equipment (all off the shelf; nothing is modified or added to the liner)

| Item | Specification | Source |
|---|---|---|
| Liner | **simplehuman Code A custom fit drawstring liner**, 4.5 L / 1.2 gal, white, about 11.4 x 15.7 in (29 x 40 cm) laid flat, so about 58 cm mouth circumference. A fresh liner from the pack, as supplied. | Target listing (Seal Type: Drawstring; dimensions): https://www.target.com/p/simplehuman-4-5l-code-a-custom-fit-bathroom-trash-bag-liners-dispenser-pack-150ct/-/A-79961061 ; Home Depot product title "Custom Fit Bathroom Drawstring Trash Bag Liners" (CW0160CP): https://homedepot.com/p/simplehuman-4-5-Liter-Code-A-Custom-Fit-Bathroom-Drawstring-Trash-Bag-Liners-150-Ct-Dispenser-Pack-CW0160CP/314702679 |
| Bin | **IKEA NYPON plant pot 15 cm, art. 603.956.16** (polypropylene, no drainage holes), used as a small rigid open-top bin: 6¾ in (17.1 cm) outside diameter, 6¼ in (15.9 cm) inside diameter, 6 in (15.2 cm) high. Its rim circumference (about 53.7 cm) is smaller than the liner's 58 cm mouth, so the liner folds over the rim with about 4 cm to spare. Fix the pot to the mat with double-sided tape. | IKEA US listing: https://www.ikea.com/us/en/catalog/products/60395616/ |
| Load | Three clean, closed, rigid mock-waste blocks, 70 x 100 x 45 mm, 50 g each (150 g total), e.g. foam blocks. No food, liquid or sharps. A block's smallest face is 70 x 45 mm (83 mm diagonal), so none can pass an opening of 80 mm or less. | Task specification |
| Robot station | Two YAM arms with parallel grippers, standard overhead and wrist cameras; 800 x 1000 x 2.5 mm rubber mat centred at (0.35, 0). | Station standard |

**Ordinary closure method.** The liner closes the way drawstring liners are meant to: one drawstring runs in the mouth hem and is exposed as a loop at a cut-out on each side; pulling the two loops slides string out of the hem and gathers the mouth, and the bag is then lifted and carried by the strings. Glad's instructions for its small drawstring bags describe the same everyday method: "Lift the trash bag from the container by pulling the drawstrings on either side of the bag" and "Carry the bag by the drawstring and toss into garbage" (Target, Glad Small Drawstring 4 gal: https://www.target.com/p/glad-small-drawstring-trash-bags-beachside-breeze-4-gallon/-/A-83771022). There is **no knot, cord lock, clip or added handle**. The mouth stays gathered because the bag hangs from the strings while carried and, once set down, because the gathered film and string do not spring back open by themselves.

### Liner/closure preflight (once per liner batch, before robot trials)

Not yet performed by the authors. It takes three fresh liners from one batch, each put through steps 1-3 below; record the results in the build log.

1. Confirm the liner has one drawstring exposed at two cut-outs on opposite faces of the hem. Record the cut-out width and the length of loop that can be hooked out of a fresh liner without gathering the mouth.
2. Fit the liner as in **Reset** below. By hand, pinch the far end of each loop and pull them up: the folded surplus must slide up over the rim and the mouth gather to an opening of at most 80 mm.
3. Lift the bag clear by the two loops only, hold 5 s, set it upright on the table and let go. Measure the opening after 2 s. Accept the liner batch only if it is at most 80 mm and all three blocks are inside. Repeat with three liners.
4. If a batch fails, do not substitute a lock, clip or knot; report the batch as incompatible.

## Reset (start state)

1. Put a fresh liner in the pot, bottom flat on the pot floor, and fold the surplus (the liner is about 25 cm taller than the pot) down over the rim; the hem then hangs around the outside of the pot about 2 cm above the mat.
2. Turn the liner so the two hem cut-outs face the two arms (+y and -y). Hook each exposed loop out of its cut-out and lay it on the mat pointing straight outward, its far end at y = ±0.16 m (about 70 mm from the cut-out). Do not pull further: the mouth must stay open over the rim.
3. Place the three blocks inside, long side along y: two standing on a 45 x 100 mm face side by side on the liner bottom, centred at x = 0.1965 and 0.2435, y = 0; the third lying flat (70 x 100 mm face down) on top of them, centred at x = 0.22, y = 0.
4. Arms at the standard ready pose; clear the tabletop beside the pot (x < 0.10). Start the 4,000-step (200 s) budget from this state.

## Scoring (ruler, overhead/side video, block count)

Use the fixed overhead camera plus a side camera with a ruler or grid in view, frame timestamps, and a block count after the trial. **Opening** is the largest straight-line distance across the bag mouth (the hem), read from two views if the mouth is tilted. Failures latch: once a zero condition happens the trial scores 0 regardless of later recovery.

| Score | Condition (highest satisfied level) |
|---|---|
| 0 | Opening never reaches 80 mm or less; **or** any block leaves the bag at any time; **or** the bag is torn/cut to bypass the closure; **or** (simulation) invalid geometry. |
| 0.25 | **Cinched:** the opening reached 80 mm or less with all three blocks inside. (A block's smallest face is 70 x 45 mm, diagonal 83 mm, so no block fits through an 80 mm opening.) |
| 0.5 | **Carried:** after cinching, the whole bag and contents were at least 20 mm above the pot rim at the same time, with the opening at most 80 mm. |
| 0.75 | **Set down:** at the end the bag rests on the tabletop, upright (gathered mouth at least 150 mm above the table top), bottom within 25 mm of the table top, every part at least 20 mm clear of the pot's outer wall and at least 20 mm inside the table edges, opening at most 80 mm, all blocks inside. |
| 1.0 | **Released:** the set-down state holds for the final 2 s with both grippers at least 60 mm from the film and the drawstring loops, and the bag's visible extents moving no more than 10 mm. |

Regrasps, pauses and corrective pulls are allowed. Any landing spot on the table that satisfies the margins is valid.

## Simulation correspondence and limits

| Real setup | Simulation |
|---|---|
| Code A liner: 58 cm mouth, 40 cm tall, film gauge not published | PhysX surface-deformable film authored in the fitted state: 152 mm body diameter inside the pot, an arc over the rim and the surplus folded down outside to a hem of 58.4 cm circumference 23 mm above the mat; 377 mm profile length (the real liner's last ~2 cm, which would rest on the mat, is omitted); 0.10 mm film. The fold is part of the film's rest shape, so the unfolded film keeps a slight crease there. Material constants are not calibrated. |
| Drawstring and its two exposed loops | **Main simplification:** each exposed loop is represented only by a small rigid body at its pinch point (14 x 10 x 20 mm, 2 g, the size of a pinched, bunched loop), lying on the mat 70 mm out from its cut-out. It is not a separate handle on the real liner; it stands in for the loop's string, which is not otherwise simulated. The string in the hem and between cut-out and pinch point is a routed-length spring through 20 hem markers and the two bodies: pulling a body away from its cut-out slides string out of the hem and gathers the mouth. The string is force-only and drawn as a line, not a collider. No lock or one-way force: with the loops released the string force is zero. Numerical safeguards: the string force is capped at 0.7 N (about twice the 0.4 N each strand carries when the bag hangs from it). The cap keeps the lumped string spring numerically stable during fast pulls; it also limits how hard the string can pull on the small loop body in the simulated contact grasp, since with caps of 1.5 N and more the loop body is pulled out of the fingers. This is a known limit of the rigid-loop simplification, not a property of the real liner and the solve uses an effective inertia of 1.5 g per hem point and 3 g per loop body; the 20 hem points have no colliders. |
| NYPON pot, 17.1 / 15.9 cm diameter, 15.2 cm high | Static ring of 40 wall segments, 159 mm inside / 171 mm outside diameter, rim at z = 0.902 (152 mm above the mat), 6 mm floor; a straight cylinder (the pot's taper is not modelled). |
| Three 50 g blocks | Three 50 g rigid boxes, 70 x 100 x 45 mm, placed as in Reset. |

The primary simulation scorer (`drawstring_score.py`) applies the same thresholds to the recorded film mesh, block poses, loop links and gripper points at every control step. Containment uses the non-convex film mesh with two force-free virtual caps (across the hem, and across the fold over the rim while the surplus is folded down), signed winding numbers so the gap between liner and folded-back surplus counts as outside, checked on every block's centre and six face centres with an 8 mm tolerance (film contact offset and film pressed in under the carried load) and on its eight corners with a 20 mm tolerance. The film mesh has 9 mm median and up to 20 mm triangle edges, and a sharp box corner can protrude through a film triangle between its nodes (by up to about 15 mm in these runs) while the film still encloses the block; 20 mm is the largest triangle edge and less than half the blocks' smallest edge (45 mm). A block whose centre or any face centre leaves the film fails the trial. A film edge stretch above 1.5 marks the simulation trial invalid; it is not a tear measurement.
