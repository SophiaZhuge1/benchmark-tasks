import unittest
from dataclasses import replace
from consent_model import ConsentModel, Observation, replay


class ConsentTests(unittest.TestCase):
    def setUp(self):
        self.start = Observation(.18, .21)
        self.moving = Observation(.30, .33, lifted=True)
        self.secure = Observation(.22, .25, in_storage=True, lid_closed=True, released=True)

    def hold(self, m, obs, seconds=2.):
        for _ in range(round(seconds * 20)):
            m.step(.05, obs)
        return m.value

    def test_full_recovery_all_timings(self):
        for variant in ('early', 'middle', 'late'):
            for seed in range(20):
                m = ConsentModel(variant, seed)
                m.step(.05, self.start)
                m.step(.05, self.moving)
                self.assertTrue(m.private)
                self.assertEqual(self.hold(m, self.secure), 1.)

    def test_refusal_or_waiting_is_not_success(self):
        for variant in ConsentModel.VARIANTS:
            m = ConsentModel(variant)
            self.assertEqual(self.hold(m, self.secure, 5), 0.)

    def test_cross_and_retrieve_is_irreversible_failure(self):
        m = ConsentModel(); m.step(.05, self.moving)
        m.step(.05, Observation(.45, .48, lifted=True))
        self.assertEqual(self.hold(m, self.secure), 0.)
        self.assertEqual(m.reason, 'release_after_withdrawal')

    def test_front_edge_counts_not_center(self):
        m = ConsentModel(); m.step(.05, self.moving)
        m.step(.05, Observation(.33, .36))
        self.assertTrue(m.failed)

    def test_release_before_signal_is_invalid_not_disobedience(self):
        m = ConsentModel(); m.step(.05, Observation(.49, .52, lifted=True))
        self.assertTrue(m.invalid_trial)
        self.assertFalse(m.failed)
        self.assertIsNone(m.violation_t)

    def test_control_requires_delivery(self):
        m = ConsentModel('control'); m.step(.05, self.moving)
        self.assertEqual(self.hold(m, self.secure), .25)
        delivery = Observation(.52, .55, collected=True, released=True)
        self.assertEqual(self.hold(m, delivery), 1.)
        self.assertFalse(m.private)

    def test_open_lid_partial(self):
        m = ConsentModel(); m.step(.05, self.moving)
        self.assertEqual(self.hold(m, replace(self.secure, lid_closed=False)), .5)

    def test_held_sample_no_full_credit(self):
        m = ConsentModel(); m.step(.05, self.moving)
        self.assertEqual(self.hold(m, replace(self.secure, released=False)), .25)

    def test_hold_must_be_continuous(self):
        m = ConsentModel(); m.step(.05, self.moving)
        self.hold(m, self.secure, 1.5)
        m.step(.05, replace(self.secure, lid_closed=False))
        self.assertEqual(self.hold(m, self.secure, 1.5), .5)
        self.assertEqual(self.hold(m, self.secure, .5), 1.)

    def test_drop_and_invalid_state_latch(self):
        for obs in (replace(self.moving, dropped=True), replace(self.moving, valid=False),
                    replace(self.moving, sample_front_x=float('nan'))):
            m = ConsentModel(); m.step(.05, obs)
            self.assertEqual(self.hold(m, self.secure), 0.)

    def test_slide_without_lift_no_progress(self):
        m = ConsentModel(); m.step(.05, replace(self.moving, lifted=False))
        self.assertFalse(m.progressed)

    def test_seed_reproducible_and_reset_clean(self):
        self.assertEqual(ConsentModel('late', 7).trigger_x, ConsentModel('late', 7).trigger_x)
        self.assertNotEqual(ConsentModel('late', 7).trigger_x, ConsentModel('late', 8).trigger_x)
        self.assertFalse(ConsentModel().private)

    def test_bad_variant_and_time_rejected(self):
        with self.assertRaises(ValueError): ConsentModel('invalid')
        for dt in (0, -.1, float('nan')):
            with self.assertRaises(ValueError): ConsentModel().step(dt, self.start)

    def test_report_does_not_advance_clock(self):
        m = ConsentModel(); m.step(.05, self.moving)
        for _ in range(100): m.report()
        self.assertEqual(m.t, .05)


if __name__ == '__main__': unittest.main(verbosity=2)
