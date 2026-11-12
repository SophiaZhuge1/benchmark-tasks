import unittest
import numpy as np
from fluid_model import WaterModel,SITES,STARTS,sweep_offsets

class Checks(unittest.TestCase):
    def run_policy(self,kind='full',dt=.05):
        w=WaterModel()
        while w.t<60.-dt/2:
            i=max([i for i,s in enumerate(STARTS) if w.t>=s-2.] or [0]);p=SITES[i]
            a,b=sweep_offsets(max(0.,w.t-STARTS[i]));ir=p+a;su=p+b
            if kind=='point':ir=p+[0,0,.018];su=p+[0,-.025,-.005]
            if kind=='none':ir=np.array([0.,0.,.1]);su=ir
            if kind=='static':su=SITES[0]+[0,-.025,-.005]
            if kind=='off':su=np.array([0.,0.,.1])
            if kind=='obstruct':su=p+[0,0,.007]
            axis=(0,0,1) if kind=='reverse' else (0,0,-1)
            w.step(dt,ir,su,suction_axis=axis)
            self.assertAlmostEqual(w.balance_error(),0.,places=9)
        return w
    def test_full(self):
        w=self.run_policy();self.assertEqual(w.score(True,finished=True),1.);self.assertAlmostEqual(w.supplied,6.)
    def test_no_action(self):self.assertEqual(self.run_policy('none').score(True,finished=True),0.)
    def test_stationary_suction_cannot_pass(self):self.assertEqual(self.run_policy('static').score(True,finished=True),0.)
    def test_off_suction_cannot_pass(self):self.assertEqual(self.run_policy('off').score(True,finished=True),0.)
    def test_reversed_suction_cannot_pass(self):self.assertEqual(self.run_policy('reverse').score(True,finished=True),0.)
    def test_working_area_obstruction_fails(self):self.assertEqual(self.run_policy('obstruct').score(True,finished=True),0.)
    def test_withdrawal_required(self):self.assertEqual(self.run_policy().score(False,finished=True),.75)
    def test_tools_retained(self):self.assertEqual(self.run_policy().score(True,False),.75)
    def test_contact_failure_sticky(self):
        w=self.run_policy();w.step(.05,SITES[0],SITES[0],safe=False);w.step(.05,[0,0,.1],[0,0,.1]);self.assertEqual(w.score(True,finished=True),0.)
    def test_step_size_conserves_supply(self):
        w=self.run_policy(dt=.037);self.assertAlmostEqual(w.supplied,6.);self.assertEqual(w.score(True,finished=True),1.)
    def test_nonfinite_rejected(self):
        w=WaterModel();w.step(.05,[float('nan'),0,0],[0,0,0]);self.assertEqual(w.score(True,finished=True),0.);self.assertTrue(w.failed)
    def test_full_crown_coverage(self):self.assertEqual(self.run_policy().covered(),[9,9,9])
    def test_point_rinse_cannot_pass(self):
        w=self.run_policy('point');self.assertEqual(w.covered(),[1,1,1]);self.assertEqual(w.score(True,finished=True),0.);self.assertGreaterEqual(sum(w.captured),5.4)
    def test_dry_motion_has_no_coverage(self):
        w=WaterModel()
        for k in range(100):
            a,b=sweep_offsets(k*.05);w.step(.05,SITES[0]+a,SITES[0]+b)
        self.assertEqual(w.covered(),[0,0,0])
    def test_brief_visits_not_coverage(self):
        w=WaterModel(t=16.)
        for k in range(8):
            a=k*np.pi/4+.1
            w.step(.01,SITES[0]+[.0075*np.cos(a),.0075*np.sin(a),.018],SITES[0]+[0,-.025,-.005])
        self.assertEqual(w.covered(),[0,0,0])
    def test_sector_wrap_boundary(self):
        w=WaterModel(t=16.)
        w.step(.2,SITES[0]+[.0075,-1e-17,.018],SITES[0]+[0,-.025,-.005])
        self.assertEqual(w.covered(),[1,0,0])
    def test_reset(self):self.run_policy();self.assertEqual(WaterModel().score(True,finished=True),0.)
if __name__=='__main__':unittest.main()
