"""Offline checks of the water model and the score, on hand-built trials: python -m unittest -v test_mouth (no simulator)."""

import unittest

import numpy as np

import mouth as M

DT = 0.05
SUMP = M.world(58, 16, -8.5)
AWAY = np.array([0.42, 0.2, M.TOP + 0.2])


def rinse(w, teeth=(0, 1, 2), squeeze_per=0.9, suction=True, outside=False, tip_shift=(0, 0, 0)):
    s = w.squeeze_max
    for k in teeth:
        tip = M.aim(M.SPOTS[k], M.BULB_AXIS, 0.018) + np.asarray(tip_shift)
        if outside:
            tip = tip + np.array([0.0, 0.07, 0.03])
        for _ in range(10):
            s += squeeze_per / 10
            w.step(DT, s, tip, M.BULB_AXIS, SUMP if suction else AWAY)
        for _ in range(8):
            w.step(DT, s, tip, M.BULB_AXIS, SUMP if suction else AWAY)


def wait(w, seconds, suction=True):
    for _ in range(int(seconds / DT)):
        w.step(DT, w.squeeze_max, AWAY, M.BULB_AXIS, SUMP if suction else AWAY)


class WaterTests(unittest.TestCase):
    def test_full(self):
        w = M.Water()
        rinse(w)
        wait(w, 8)
        self.assertEqual(w.rinsed(), [True, True, True])
        self.assertLessEqual(w.in_mouth(), M.LEFT_MAX)
        self.assertEqual(w.throat, 0.0)
        self.assertEqual(w.spill, 0.0)
        self.assertEqual(M.score(w, True, True), 1.0)
        self.assertEqual(M.score(w, True, False), 0.75)
        self.assertEqual(M.score(w, False, True), 0.0)
        self.assertAlmostEqual(w.balance(), 0.0, places=9)

    def test_no_suction_pools_and_fails(self):
        w = M.Water()
        rinse(w, suction=False)
        wait(w, 8, suction=False)
        self.assertGreater(w.in_mouth(), M.LEFT_MAX)
        self.assertEqual(M.score(w, True, True), 0.0)

    def test_no_suction_large_volume_reaches_throat(self):
        w = M.Water()
        rinse(w, squeeze_per=2.0, suction=False)
        self.assertGreater(w.throat, M.THROAT_MAX)
        self.assertEqual(M.score(w, True, True), 0.0)

    def test_outside_spills(self):
        w = M.Water()
        rinse(w, outside=True)
        self.assertGreater(w.spill, M.SPILL_MAX)
        self.assertEqual(sum(w.rinsed()), 0)
        self.assertEqual(M.score(w, True, True), 0.0)

    def test_skip_one(self):
        w = M.Water()
        rinse(w, teeth=(0, 1))
        wait(w, 8)
        self.assertEqual(M.score(w, True, True), 0.5)

    def test_off_target_misses_dot(self):
        w = M.Water()
        rinse(w, tip_shift=(0.0, -0.008, 0.0))
        self.assertLess(sum(w.rinsed()), 3)

    def test_bulb_ratchet(self):
        w = M.Water()
        w.step(DT, 4.0, AWAY, M.BULB_AXIS, None, away=True)
        w.step(DT, 0.0, AWAY, M.BULB_AXIS, None, away=True)  # released: it draws air back in
        w.step(DT, 4.0, AWAY, M.BULB_AXIS, None, away=True)  # squeezing back to the same depth expels only air
        self.assertAlmostEqual(w.dispensed, 4.0 * M.ML_PER_MM)
        self.assertAlmostEqual(w.dripped, 4.0 * M.ML_PER_MM)

    def test_nothing(self):
        w = M.Water()
        wait(w, 5)
        self.assertEqual(M.score(w, True, True), 0.0)


if __name__ == "__main__":
    unittest.main()
