# Ordinary drawtape revision — development checkpoint

This revision addresses reviewer feedback on PR #2134. **It is not ready for resubmission.**

Implemented in the candidate scene:

- Removed custom self-lock housings and the one-way minimum-perimeter force law from the active runtime.
- Replaced the two 18 x 14 x 24 mm rigid handles with uniform segments of a continuous tape loop. The bight segments have the same dimensions and material as the rest of the tape.
- Added 80 articulated contact links, a symmetric sliding-hem model, full tape pose recording, and pre-settle force initialization.
- Limited the entire tape loop to the nominal flat bag perimeter; no additional long cord is appended to an already-open bag.
- Reduced film thickness from 100 micrometres to a 20 micrometre development value within the manufacturer's published 15–25 micrometre range for the reference liner family.
- Added a separate primary scorer that withholds closure-dependent credit until an ordinary knot is actually verified. A narrow mouth, a controller phase name, or a claimed `knot_verified` flag cannot produce full score.

Commercial reference: Brabantia PerfectFit Code A, current SKU 137600, 270 x 290 mm laid flat, factory tie-tapes. The manufacturer explicitly identifies Code A as compatible with Sort & Go 3 L bins. The original cord-lock assembly and added handles are no longer proposed equipment.

Outstanding work:

1. Fix the ordinary starting cuff/grasp. After isolating GPU 1 as logical cuda:0, the scene completed 20 setup steps, but both initially tagged bight segments settled inside the bin. The old arm trajectory cannot be treated as a valid ordinary-tape grasp controller. Direct cuda:1 had failed during initialization.
2. Replace the inherited diagnostic bin with the rectangular Sort & Go 3 L geometry (published exterior 188 x 139 x 181 mm), after measuring its internal dimensions. The current cylindrical bin is a development fixture, not a claim of product fidelity.
3. Measure the purchased liner's factory tape width, thickness, route and available bight length. The 8 mm tape width, 0.5 mm collision thickness and single closed-loop routing are explicit simulation assumptions, not verified product specifications.
4. Implement and validate the ordinary knot manipulation and its evaluator. The inherited arm controller is a diagnostic cinch/lift controller and does not tie a knot.
5. Perform the physical preflight in PHYSICAL_PROTOCOL.md, then record a new full-score demo and Dream-1 run in the exact same final scene. Neither exists yet.
6. Upload new media and update the existing PR only after these checks pass. The old media ID M-C8X8HT demonstrates the rejected custom liner and cannot support this candidate.

A fresh demo attempt using the current candidate failed during reset with `CUBLAS_STATUS_ALLOC_FAILED` before any arm actions. It is not a zero-score completed demo and is not submission evidence.

Offline tests: 41 passed (evidence/revision-unit-tests.log); these are code checks, not feasibility evidence.

No physical equipment trial, successful knot, new 1.0 demo, or completed revised-scene Dream-1 run is claimed.
