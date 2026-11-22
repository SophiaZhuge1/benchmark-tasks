"""Offline tests of the scorer (no simulator): python test_flapscore.py"""
import unittest

import numpy as np

import flapscore as fs

TUBE_X, PEG_Z, HOLE, Y_IN, Y_TIP = -0.052, 0.040, 0.0085, 0.022, 0.040


def frame(t, ears=(True, True), seat=True, slack=15.0, dist=0.10):
    return fs.Frame(t=t, ears=ears, seat=seat, slack=slack, robot_dist=dist)


def run(frames, scorer=None):
    sc = scorer or fs.Scorer()
    for f in frames:
        sc.update(f)
    return sc


class Geometry(unittest.TestCase):
    def test_ear_on_peg(self):
        self.assertTrue(fs.ear_on_peg((TUBE_X, 0.0305, PEG_Z), 1, TUBE_X, PEG_Z, HOLE, Y_IN, Y_TIP))
        self.assertFalse(fs.ear_on_peg((TUBE_X, 0.0305, PEG_Z), -1, TUBE_X, PEG_Z, HOLE, Y_IN, Y_TIP))  # wrong peg
        self.assertFalse(fs.ear_on_peg((TUBE_X, 0.045, PEG_Z), 1, TUBE_X, PEG_Z, HOLE, Y_IN, Y_TIP))   # past the tip
        self.assertFalse(fs.ear_on_peg((TUBE_X, 0.0305, PEG_Z + 0.006), 1, TUBE_X, PEG_Z, HOLE, Y_IN, Y_TIP))

    def test_seated(self):
        self.assertTrue(fs.seated(np.full(8, 0.0002), 0.002))
        self.assertFalse(fs.seated(np.r_[np.full(7, 0.0002), 0.002], 0.002))  # one side lifted 2 mm
        self.assertFalse(fs.seated(np.full(8, 0.0002), 0.010))                 # off centre

    def test_slack(self):
        self.assertAlmostEqual(fs.slack_mm(26, 0.006, (0, 0, 0), (0, 0, 0.150)), 9.0, places=6)
        self.assertIsNone(fs.slack_mm(None, 0.006, (0, 0, 0), (0, 0, 0.15)))


class Press(unittest.TestCase):
    """The computed handle press with the tank's geometry (tank frame, m): hinge, lug, clip slot, lever pivot."""
    HINGE, LUG = (-0.055, 0.0, 0.055), (0.095, 0.0, -0.013)
    SLOT, PIVOT = (0.061, -0.005, 0.187), (0.071, 0.150, 0.200)

    def lift(self, bead, deg=40.0):
        import math
        return fs.press_lift_deg((bead + 0.5) * 0.006, self.SLOT, self.PIVOT, math.radians(-deg), self.HINGE, self.LUG,
                                 66.0)

    def test_right_slack_lifts_to_the_stop(self):
        self.assertGreaterEqual(self.lift(26), 60.0)
        self.assertGreaterEqual(self.lift(27), 60.0)

    def test_too_slack_lifts_too_little(self):
        self.assertLess(self.lift(28), 60.0)
        self.assertLess(self.lift(30), 60.0)

    def test_no_press_no_lift(self):
        self.assertEqual(self.lift(27, deg=0.0), 0.0)


class Tiers(unittest.TestCase):
    def test_nothing(self):
        self.assertEqual(run([frame(0.0, ears=(False, False), seat=False, slack=None)]).score, 0.0)

    def test_one_ear(self):
        self.assertEqual(run([frame(0.0, ears=(True, False), seat=False, slack=None)]).score, 0.25)

    def test_both_ears_not_seated(self):
        self.assertEqual(run([frame(0.0, seat=False, slack=None)]).score, 0.25)

    def test_seated_no_chain(self):
        sc = run([frame(t * 0.05, slack=None) for t in range(60)])
        self.assertEqual(sc.score, 0.5)
        self.assertFalse(sc.want_press)

    def test_chain_too_tight_or_slack(self):
        for s in (4.0, 26.0):
            sc = run([frame(t * 0.05, slack=s) for t in range(60)])
            self.assertEqual(sc.score, 0.5)
            self.assertFalse(sc.want_press)

    def test_robot_too_close(self):
        sc = run([frame(t * 0.05, dist=0.02) for t in range(60)])
        self.assertEqual(sc.score, 0.0)
        self.assertFalse(sc.want_press)

    def test_full_after_hold_and_press(self):
        sc = run([frame(t * 0.05) for t in range(19)])
        self.assertFalse(sc.want_press)
        sc = run([frame(t * 0.05) for t in range(19, 21)], sc)
        self.assertTrue(sc.want_press)
        sc.press_result(72.0, True)
        self.assertTrue(sc.success)
        self.assertEqual(sc.score, 1.0)

    def test_failed_press_caps(self):
        sc = run([frame(t * 0.05) for t in range(21)])
        sc.press_result(40.0, True)  # too slack: lifts too little
        self.assertFalse(sc.success)
        sc = run([frame(2.0 + t * 0.05) for t in range(40)], sc)
        self.assertEqual(sc.score, 0.5)
        self.assertFalse(sc.want_press)
        sc2 = run([frame(t * 0.05) for t in range(21)])
        sc2.press_result(75.0, False)  # does not drop back seated
        self.assertEqual(sc2.score, 0.5)

    def test_hold_resets(self):
        fr = [frame(t * 0.05) for t in range(15)] + [frame(0.75, dist=0.01)] + [frame(0.8 + t * 0.05) for t in range(15)]
        self.assertFalse(run(fr).want_press)


if __name__ == "__main__":
    unittest.main()
