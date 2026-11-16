# Ordinary drawtape liner: proposed reproducible real setup

**Status: product compatibility documented; physical preflight not performed.**

## Equipment

| Item | Specification | Evidence/status |
|---|---|---|
| Factory liner | Brabantia PerfectFit Code A, SKU 137600 / EAN 8710755137600; 270 mm laid-flat width, 290 mm height; original factory tie-tapes | Current manufacturer listing |
| Bin | Brabantia Sort & Go 3 L, grey SKU 137389; exterior 188 x 139 x 181 mm; normal lid held fully open by its own stay-open feature | Manufacturer data sheet identifies Code A compatibility; internal dimensions to measure |
| Load | Six clean, rigid polypropylene blocks, 48 x 80 x 35 mm, 25 g each; 150 g total | Fixed task load; no liquid or sharp refuse |
| Work surface | Stable 1100 x 1300 mm table with top at z=747.5 mm and non-slip mat | Same station as the simulator |
| Robots | Two YAM arms, original parallel grippers, bases at (0, +/-305, 750) mm | Existing station |
| Measurement | Ruler, scale, top/side video with timestamps | Ordinary tools |

Place the bin centred at (220,0) mm, long side along x, on the mat. Install a fresh liner using its factory hem; leave both factory drawtape openings accessible. Start with mouth width at least 100 mm, no knot, and all six blocks inside in two columns and three layers. Place the lid away from the planned extraction path. The final landing region is any clear tabletop position at least 20 mm inside its edges and at least 20 mm from the bin.

**Do not infer tape dimensions from bag dimensions.** Record the tape width, film and tape thickness, factory route, exposed bight length, and the bin's internal dimensions on the actual purchased sample. Adjust the scene to these measurements before recording submission media. The current simulation uses an idealised cylindrical fixture and a single closed tape loop; these are not verified replicas of this product.

## Ordinary closure

Pull the two built-in tape bights to gather the mouth. Secure the gathered mouth with a normal tied knot using only those tapes. A reproducible reference technique is an overhand crossing followed by an opposite overhand crossing, drawn snug to form a square knot in the doubled bights. Do not use external fasteners, self-locking devices, rigid handles, glue, or a pre-tied knot. Whether these particular factory bights provide sufficient length for that technique must be checked on the actual sample before adoption.

Then lift the loaded liner clear of the bin and release it onto the adjacent table. Count all six blocks before and after.

## Physical preflight needed before submission

1. Photograph the package SKU, empty liner, factory hem and two tape openings beside a ruler. Record measured dimensions and load mass.
2. Film an uninterrupted manual trial: install open liner, load it, gather and tie the factory tapes, extract, place, release both tapes and withdraw hands.
3. After release, observe for 10 seconds. The mouth must remain at most 60 mm wide, the knot must remain tied, all six blocks must remain inside, and there must be no visible tear or tape separation. Show the tied crossings clearly from above and the side.
4. Repeat with three fresh liners from the same product, recording every result and failure. This is a proposed repeatability check, not a claim of completed trials.
5. If available bight length, fit or retention fails, change the specified commercial liner or geometry openly and rerun the check. Do not add custom hardware to make it pass.

## Target scoring once implemented and verified

Highest satisfied tier; an escaped block, destructive bypass, detached tape or invalid evidence gives zero. Observe the entire trial so spilling then retrieving contents cannot pass.

| Score | Outcome |
|---|---|
| 0.0 | No valid cinch, lost contents, destructive bypass, invalid geometry/evidence, or mouth reopened beyond 60 mm |
| 0.25 | Mouth reaches at most 50 mm, ends at most 60 mm, all six blocks retained |
| 0.50 | Above plus ordinary tied closure demonstrably remains secure without either gripper supporting the tapes for 2 seconds |
| 0.75 | Above plus the whole bag and contents clear the bin by at least 20 mm for 2 seconds |
| 1.0 | Above plus released tabletop placement for 2 seconds: whole load 20 mm inside edges; bottom within 25 mm of support; grippers 60 mm from film and tape; each bag bounding-box extremum moves at most 10 mm |

The candidate primary scorer currently implements only the 0.0/0.25 tiers and explicitly withholds all knot-dependent credit. Higher tiers are the proposed specification, not an implemented or validated evaluator. The retained placement geometry scorer is diagnostic only.

## Sources checked 16 November 2026

- Current liner product: https://www.brabantia.com/uk/perfectfit-bin-bags-code-a-3-5-litres-40-bags-in-dispenser-pack-white/
- Code A family data sheet, article 137488, including PE 15–25 micrometre film: https://media.cdn.bauhaus/m/1465563/BH_DOC_1465563.pdf
- Matching bin data sheet, SKU 137389: https://sales.brabantia.com/Articles/137389.pdf

Product documentation does not substitute for the physical preflight or a successful robotic simulation.
