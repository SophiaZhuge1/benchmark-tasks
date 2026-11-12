import unittest
import numpy as np
from finish import FinishTracker,rack_state
from fluid_model import WaterModel

class FinishChecks(unittest.TestCase):
    def water(self,amount=0.):
        return WaterModel(t=45.,supplied=6.,delivered=[2.,2.,2.],coverage_s=[[.3]*9 for _ in range(3)],captured=[2.,2.,2.-amount],pool=[0.,0.,amount],peak=.4)
    def test_old_withdrawal_no_longer_full(self):self.assertEqual(self.water(.22).score(clear=True,held=True),.75)
    def test_small_residual_still_blocks_full(self):self.assertEqual(self.water(.06).score(clear=True,finished=True),.75)
    def test_released_tools_can_finish(self):self.assertEqual(self.water(.01).score(clear=True,held=False,finished=True),1.)
    def test_empty_at_reset_not_completed(self):
        t=FinishTracker();t.step(2.,2.,False,True,True,0.);self.assertFalse(t.cleanup_complete)
    def test_both_tools_leave_early_not_completed(self):
        t=FinishTracker();t.step(2.,40.,True,True,False,0.);self.assertFalse(t.cleanup_complete)
    def test_rinse_tool_not_lifted_not_completed(self):
        t=FinishTracker();t.step(2.,40.,True,False,True,0.);self.assertFalse(t.cleanup_complete)
    def test_stay_sucking_until_dry(self):
        t=FinishTracker();t.step(1.,40.,True,True,True,.1);self.assertFalse(t.cleanup_complete)
        t.step(.05,40.05,True,True,True,.04);self.assertTrue(t.cleanup_complete)
        self.assertEqual(t.cleanup_time,40.05)
    def test_short_visit_and_interruption_do_not_count(self):
        t=FinishTracker();t.step(.6,40.,True,True,True,0.)
        t.step(.1,40.1,True,True,False,0.);t.step(.6,40.7,True,True,True,0.)
        self.assertFalse(t.cleanup_complete)
    def test_original_rack_released_settled(self):
        home=np.array([.28,.20,.03]);fingers=np.array([[.28,.20,.20]])
        self.assertEqual(rack_state(home,np.eye(3),np.zeros(3),home,fingers,home+[0,0,.04]),(True,True))
    def test_holding_over_rack_is_not_release(self):
        home=np.array([.28,.20,.03]);grasp=home+[0,0,.04]
        self.assertEqual(rack_state(home,np.eye(3),np.zeros(3),home,[grasp],grasp),(True,False))
    def test_wrong_stand_and_moving_tool_rejected(self):
        home=np.array([.28,.20,.03]);g=home+[0,0,.04];f=[g+[0,0,.1]]
        self.assertFalse(rack_state(home+[0,-.4,0],np.eye(3),np.zeros(3),home,f,g)[0])
        self.assertFalse(rack_state(home,np.eye(3),[0,0,.03],home,f,g)[0])
    def test_tipped_tool_rejected(self):
        home=np.array([.28,.20,.03]);r=np.array([[1,0,0],[0,0,-1],[0,1,0]])
        self.assertFalse(rack_state(home,r,np.zeros(3),home,[home+[0,0,.2]],home+[0,0,.04])[0])
if __name__=='__main__':unittest.main()
