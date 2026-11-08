import unittest
from probe_model import ProbeModel, contact_fraction


class TestProbeProtection(unittest.TestCase):
    def lift(self,m):
        for _ in range(6): m.step(.05,0.,.040)
    def finish(self,m):
        m.step(.05,.060,.040)
        m.step(.05,.060,0.)
        for _ in range(22): m.step(.05,.060,0.,True)
    def test_full_sequence(self):
        m=ProbeModel();self.lift(m);self.finish(m)
        self.assertEqual(m.value,1.);self.assertFalse(m.damaged)
    def test_idle_has_no_credit(self):
        m=ProbeModel()
        for _ in range(100):m.step(.05,0.,0.,True)
        self.assertEqual(m.value,0.)
    def test_drag_is_irreversible(self):
        m=ProbeModel();m.step(.05,.001,0.);self.lift(m);self.finish(m)
        self.assertTrue(m.damaged);self.assertEqual(m.value,0.)
    def test_slow_drag_accumulates(self):
        m=ProbeModel()
        for i in range(1,41):m.step(.05,i*.00001,0.)
        self.assertTrue(m.damaged)
    def test_reverse_drag_does_not_cancel(self):
        m=ProbeModel();m.step(.05,.00015,0.);m.step(.05,0.,0.)
        self.assertTrue(m.damaged)
    def test_lift_and_slide_same_step(self):
        m=ProbeModel();m.step(.05,.060,.040)
        self.assertTrue(m.damaged)
    def test_lower_and_slide_same_step(self):
        m=ProbeModel();self.lift(m);m.step(.05,.060,0.)
        self.assertTrue(m.damaged)
    def test_contact_fraction(self):
        self.assertAlmostEqual(contact_fraction(0.,.040),.02)
        self.assertAlmostEqual(contact_fraction(.040,0.),.02)
        self.assertEqual(contact_fraction(.02,.04),0.)
    def test_raised_target_partial_only(self):
        m=ProbeModel();self.lift(m);m.step(.05,.060,.040,True)
        self.assertEqual(m.value,.75)
    def test_wrong_position_no_full_credit(self):
        m=ProbeModel();self.lift(m);m.step(.05,.03,.04)
        for _ in range(30):m.step(.05,.03,0.,True)
        self.assertEqual(m.value,.25)
    def test_release_required(self):
        m=ProbeModel();self.lift(m);m.step(.05,.06,.04)
        for _ in range(30):m.step(.05,.06,0.,False)
        self.assertLess(m.value,1.)
    def test_dwell_resets_when_lifted(self):
        m=ProbeModel();self.lift(m);self.finish(m);m.step(.05,.06,.04,True)
        self.assertEqual(m.value,.75);self.assertEqual(m.final_dwell,0.)
    def test_post_success_damage(self):
        m=ProbeModel();self.lift(m);self.finish(m);m.step(.05,.061,0.,True)
        self.assertEqual(m.value,0.)
    def test_broken_rail_fails(self):
        m=ProbeModel();self.lift(m);m.step(.05,.080,.040)
        self.assertTrue(m.damaged)
    def test_reject_nonfinite(self):
        for args in [(0.,0.,0.),(.05,float('nan'),0.),(.05,0.,float('inf'))]:
            with self.assertRaises(ValueError):ProbeModel().step(*args)


if __name__=='__main__':unittest.main()
