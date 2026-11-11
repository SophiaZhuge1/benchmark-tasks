import unittest
from dataclasses import replace
from curling_model import CurlingModel,Observation

class RescueRules(unittest.TestCase):
    def start(self):
        m=CurlingModel();m.step(.05,Observation(.34,.04,.38,-.005))
        return m

    def threat(self,m):
        m.step(.05,Observation(.40,.08,.40,-.03,red_vx=.25,red_vy=-.30,max_speed=.4))

    def finish(self,m,on_target=True):
        o=Observation(.71 if on_target else .08,.18,.45,-.06)
        for _ in range(40):m.step(.05,o)
        return m

    def test_reactive_rescue_full_score(self):
        m=self.start();self.threat(m)
        m.step(.05,Observation(.48,.12,.44,-.06,right_red=True))
        self.assertEqual(self.finish(m).score,1.)
        self.assertTrue(m.saved)

    def test_target_without_rescue_is_only_half(self):
        self.assertEqual(self.finish(self.start()).score,.5)

    def test_rescue_without_target_is_three_quarters(self):
        m=self.start();self.threat(m);m.step(.05,Observation(.48,.12,.44,-.06,right_red=True))
        self.assertEqual(self.finish(m,False).score,.75)

    def test_no_action(self):
        m=CurlingModel()
        for _ in range(100):m.step(.05,Observation(.15,.04,.38,-.005))
        self.assertEqual(m.score,0.)

    def test_sideways_motion_without_predicted_escape_is_not_threat(self):
        m=self.start();m.step(.05,Observation(.4,.08,.4,-.02,red_vy=-.07,max_speed=.07))
        self.assertFalse(m.threat)

    def test_threat_is_recorded_before_contact(self):
        m=self.start();self.threat(m)
        self.assertTrue(m.threat);self.assertFalse(m.blocked)

    def test_premature_block_fails(self):
        m=self.start();m.step(.05,Observation(.4,.08,.4,-.06,right_red=True))
        self.assertEqual(m.reason,'red_contact_before_edge_threat')

    def test_block_far_from_edge_fails(self):
        m=self.start();self.threat(m);m.step(.05,Observation(.4,.08,.4,.02,right_red=True))
        self.assertTrue(m.failed)

    def test_shooting_arm_cannot_rescue(self):
        m=self.start();self.threat(m);m.step(.05,Observation(.4,.08,.4,-.06,left_red=True))
        self.assertEqual(m.reason,'unauthorised_puck_contact')

    def test_direct_contact_with_guard_fails(self):
        m=self.start();m.step(.05,Observation(.4,.08,.4,-.06,other_contact=True))
        self.assertTrue(m.failed)

    def test_shooting_arm_must_release(self):
        m=self.start();m.step(.05,Observation(.4,.08,.4,-.06,left_blue=True))
        self.assertEqual(m.reason,'shooting_arm_contact_after_release')

    def test_puck_leaving_board_latches_failure(self):
        m=self.start();self.threat(m);m.step(.05,Observation(.4,.08,.4,-.10,any_out=True))
        self.assertEqual(self.finish(m).score,0.)
        self.assertEqual(m.reason,'puck_left_board')

    def test_lifting_or_tipping_fails(self):
        for key in ['lifted','tipped']:
            m=self.start();m.step(.05,replace(Observation(.4,.08,.4,-.06),**{key:True}))
            self.assertTrue(m.failed)

    def test_hold_requires_release_of_rescued_stone(self):
        m=self.start();self.threat(m)
        for _ in range(80):m.step(.05,Observation(.71,.18,.44,-.06,right_red=True))
        self.assertEqual(m.score,0.)
        self.assertEqual(m.rest_s,0.)

    def test_invalid_physics_fails(self):
        m=self.start();m.step(.05,Observation(float('nan'),.08,.4,-.06))
        self.assertEqual(m.reason,'invalid_physics')

if __name__=='__main__':unittest.main()
