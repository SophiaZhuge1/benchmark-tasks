"""Offline checks of the bounce count's rules, on hand-built contact sequences. No simulator: python -m unittest test_bounce_rules"""

from __future__ import annotations

import unittest

from bounce_rules import BounceCounter, tier

TOP = 0.75
DT = 0.002
FACE_Z = TOP + 0.126  # the ball's bottom when it sits on the face
RELEASED = (0.10, True, "")


class Sim:
    """Feeds a counter with simple ballistic bounces."""

    def __init__(self, first_face=RELEASED):
        self.c = BounceCounter(TOP)
        self.t = 0.0
        self.first_face = first_face

    def run(self, touch, z, steps=1):
        for _ in range(steps):
            self.t += DT
            self.c.step(self.t, set(touch), z, lambda: self.first_face)

    def pick_and_drop(self):
        self.run(set(), TOP + 0.05, 5)  # in the cup
        self.run({"other", "left"}, TOP + 0.05, 5)  # picked
        self.run({"left"}, TOP + 0.30, 20)  # carried
        self.run(set(), TOP + 0.25, 20)  # falling

    def bounce(self, apex_above_table=0.30, contact_steps=1, face_z=FACE_Z, touch=("face",)):
        self.run(touch, face_z, contact_steps)
        self.run(set(), face_z + 0.05, 30)
        self.run(set(), TOP + apex_above_table, 5)
        self.run(set(), face_z + 0.05, 30)


class Rules(unittest.TestCase):
    def test_tiers(self):
        self.assertEqual([tier(n) for n in (0, 1, 3, 4, 6, 7, 9, 10, 12)], [0, 0.25, 0.25, 0.5, 0.5, 0.75, 0.75, 1.0, 1.0])

    def test_ten_bounces_full(self):
        s = Sim()
        s.pick_and_drop()
        for _ in range(10):
            s.bounce()
        self.assertEqual(s.c.state, "done")
        self.assertEqual(s.c.score, 1.0)

    def test_extra_bounces_after_done_do_not_matter(self):
        s = Sim()
        s.pick_and_drop()
        for _ in range(10):
            s.bounce()
        s.run({"other"}, TOP + 0.02, 5)  # falls on the table afterwards
        self.assertEqual(s.c.score, 1.0)

    def test_partial_counts(self):
        for n, want in ((1, 0.25), (3, 0.25), (4, 0.5), (6, 0.5), (7, 0.75), (9, 0.75)):
            s = Sim()
            s.pick_and_drop()
            for _ in range(n):
                s.bounce()
            s.run({"other"}, TOP + 0.02, 5)  # then it lands on the table
            s.bounce()  # and anything later does not count
            self.assertEqual(s.c.count, n)
            self.assertEqual(s.c.score, want, n)

    def test_low_bounce_stops_the_count(self):
        s = Sim()
        s.pick_and_drop()
        for _ in range(5):
            s.bounce()
        s.bounce(apex_above_table=0.24)  # below the red line
        for _ in range(6):
            s.bounce()
        self.assertEqual(s.c.count, 5)
        self.assertEqual(s.c.state, "ended")
        self.assertEqual(s.c.score, 0.5)

    def test_bat_above_blue_line(self):
        s = Sim()
        s.pick_and_drop()
        for _ in range(3):
            s.bounce()
        s.bounce(face_z=TOP + 0.16)
        for _ in range(8):
            s.bounce()
        self.assertEqual(s.c.count, 3)

    def test_first_hit_above_blue_line_scores_zero(self):
        s = Sim()
        s.pick_and_drop()
        for _ in range(10):
            s.bounce(face_z=TOP + 0.20)
        self.assertEqual(s.c.score, 0.0)

    def test_carry(self):
        s = Sim()
        s.pick_and_drop()
        s.bounce()
        s.bounce(contact_steps=60)  # 0.12 s on the face
        for _ in range(9):
            s.bounce()
        self.assertEqual(s.c.count, 1)
        self.assertEqual(s.c.score, 0.25)

    def test_contact_just_under_limit_is_a_bounce(self):
        s = Sim()
        s.pick_and_drop()
        for _ in range(10):
            s.bounce(contact_steps=45)  # 0.09 s
        self.assertEqual(s.c.score, 1.0)

    def test_edge_or_handle_contact_stops(self):
        s = Sim()
        s.pick_and_drop()
        for _ in range(8):
            s.bounce()
        s.bounce(touch=("face", "bat"))
        for _ in range(4):
            s.bounce()
        self.assertEqual(s.c.count, 8)
        self.assertEqual(s.c.score, 0.75)

    def test_right_gripper_contact_stops(self):
        s = Sim()
        s.pick_and_drop()
        for _ in range(4):
            s.bounce()
        s.run({"right"}, TOP + 0.2, 2)
        for _ in range(8):
            s.bounce()
        self.assertEqual(s.c.count, 4)

    def test_left_touch_after_release_is_zero(self):
        s = Sim()
        s.pick_and_drop()
        for _ in range(9):
            s.bounce()
        s.run({"left"}, TOP + 0.3, 2)
        s.bounce()
        self.assertEqual(s.c.score, 0.0)

    def test_left_touch_after_count_ended_is_kept(self):
        s = Sim()
        s.pick_and_drop()
        for _ in range(5):
            s.bounce()
        s.run({"other"}, TOP + 0.02, 5)
        s.run({"left"}, TOP + 0.02, 5)  # picks it up again: only the first drop counts
        s.run(set(), TOP + 0.3, 5)
        for _ in range(10):
            s.bounce()
        self.assertEqual(s.c.count, 5)
        self.assertEqual(s.c.score, 0.5)

    def test_fingers_too_close_at_first_contact(self):
        s = Sim(first_face=(0.02, True, ""))
        s.pick_and_drop()
        for _ in range(10):
            s.bounce()
        self.assertEqual(s.c.score, 0.0)

    def test_bat_not_held_at_first_contact(self):
        s = Sim(first_face=(0.1, False, "the bat touches the stand"))
        s.pick_and_drop()
        for _ in range(10):
            s.bounce()
        self.assertEqual(s.c.score, 0.0)

    def test_bat_slips_during_count(self):
        s = Sim()
        s.pick_and_drop()
        for _ in range(6):
            s.bounce()
        s.c.bat_lost(s.t, "bat moved 12 mm")
        for _ in range(6):
            s.bounce()
        self.assertEqual(s.c.score, 0.0)

    def test_bat_slip_after_done_is_kept(self):
        s = Sim()
        s.pick_and_drop()
        for _ in range(10):
            s.bounce()
        s.c.bat_lost(s.t, "dropped afterwards")
        self.assertEqual(s.c.score, 1.0)

    def test_ball_on_bat_while_held(self):
        s = Sim()
        s.run({"left"}, TOP + 0.2, 5)
        s.run({"left", "face"}, TOP + 0.13, 5)  # carried down onto the face
        s.run(set(), TOP + 0.2, 5)
        for _ in range(10):
            s.bounce()
        self.assertEqual(s.c.score, 0.0)

    def test_never_picked(self):
        s = Sim()
        s.run({"other"}, TOP + 0.05, 5)
        s.run(set(), TOP + 0.2, 5)
        for _ in range(10):
            s.bounce()  # knocked onto the bat without the left hand
        self.assertEqual(s.c.score, 0.0)

    def test_dropped_on_table_first(self):
        s = Sim()
        s.pick_and_drop()
        s.run({"other"}, TOP + 0.02, 3)
        for _ in range(10):
            s.bounce()
        self.assertEqual(s.c.score, 0.0)

    def test_regrasp_before_any_contact_is_still_held(self):
        s = Sim()
        s.pick_and_drop()
        s.run({"left"}, TOP + 0.3, 5)  # caught again in the air, before touching anything
        s.run(set(), TOP + 0.25, 20)
        for _ in range(10):
            s.bounce()
        self.assertEqual(s.c.score, 1.0)

    def test_doing_nothing(self):
        s = Sim()
        s.run({"other"}, TOP + 0.05, 500)
        self.assertEqual(s.c.score, 0.0)

    def test_ball_resting_on_bat_is_a_carry(self):
        s = Sim()
        s.pick_and_drop()
        s.run({"face"}, FACE_Z, 500)
        self.assertEqual(s.c.score, 0.0)


if __name__ == "__main__":
    unittest.main()
