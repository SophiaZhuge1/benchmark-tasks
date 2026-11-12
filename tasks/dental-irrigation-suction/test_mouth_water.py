import unittest
import numpy as np
from fluid_model import WaterModel,SITES,MOUTH_CENTRES,MOUTH_FLOOR
from scenario_checks import run

class MouthChecks(unittest.TestCase):
    def test_full_and_wrong_place_isolate_suction(self):
        a,b=run('full')['final'],run('wrong_place')['final']
        self.assertEqual(a['coverage'],b['coverage'])
        self.assertEqual(a['delivered_ml'],b['delivered_ml'])
        self.assertLess(a['mouth_water_ml'],.5)
        self.assertGreater(b['mouth_water_ml'],2.)
        self.assertEqual(sum(b['captured_ml']),0.)
    def test_water_remains_on_crown_before_runoff(self):
        w=WaterModel(t=16.);w.step(.05,SITES[0]+[0,0,.018],[0,0,.1])
        self.assertGreater(w.crown[0],0.);self.assertGreater(w.pool[0],0.)
        self.assertAlmostEqual(w.mouth_water(),.02)
        self.assertAlmostEqual(w.balance_error(),0.)
    def test_dry_inlet_cannot_aspirate_distant_pool(self):
        w=WaterModel(pool=[.5,0,0],supplied=.5)
        for _ in range(20):w.step(.05,[0,0,.1],MOUTH_CENTRES[2]+[0,0,.001])
        self.assertLess(sum(w.captured),.002) # only physically modelled crossflow can reach cell 3
        self.assertAlmostEqual(w.balance_error(),0.)
    def test_high_inlet_cannot_capture(self):
        w=WaterModel(pool=[.5,0,0],supplied=.5)
        w.step(.05,[0,0,.1],MOUTH_CENTRES[0]+[0,0,.020])
        self.assertEqual(sum(w.captured),0.)
    def test_subfloor_inlet_cannot_capture(self):
        w=WaterModel(pool=[.5,0,0],supplied=.5)
        w.step(.05,[0,0,.1],MOUTH_CENTRES[0]-[0,0,.003])
        self.assertEqual(sum(w.captured),0.)
    def test_missed_crown_but_inside_mouth_counts_as_retained_water(self):
        w=WaterModel(t=16.)
        w.step(.05,MOUTH_CENTRES[0]+[0,0,.018],[0,0,.1])
        self.assertEqual(w.delivered,[0,0,0]);self.assertAlmostEqual(w.mouth_water(),.02)
        self.assertAlmostEqual(w.lost,0.)
    def test_late_cleanup_cannot_erase_peak(self):
        r=run('late_suction');self.assertEqual(r['measured_model_score'],0.)
        self.assertLess(r['final']['mouth_water_ml'],.5);self.assertGreater(r['final']['peak_pool_ml'],1.)
    def test_global_threshold_is_not_per_cell(self):
        w=WaterModel(pool=[.4,.4,.4],supplied=1.2)
        w.step(.05,[0,0,.1],[0,0,.1]);self.assertGreater(w.peak,1.)
    def test_single_suction_budget(self):
        w=WaterModel(pool=[.5,.5,.5],supplied=1.5)
        w.step(.05,[0,0,.1],MOUTH_CENTRES[1]+[0,0,.001])
        self.assertLessEqual(sum(w.captured),.65*.05+1e-12)
    def test_current_zero_water_does_not_override_history(self):
        w=WaterModel(t=40,supplied=6,captured=[2,2,2],delivered=[2,2,2],coverage_s=[[.2]*9 for _ in range(3)],peak=1.01)
        self.assertEqual(w.score(True,finished=True),0.)
    def test_partial_credit_requires_water_control(self):
        w=WaterModel(t=40,supplied=6,captured=[2,2,2],delivered=[2,2,2],coverage_s=[[.2]*9,[0.]*9,[0.]*9],peak=.4)
        self.assertEqual(w.score(True,finished=True),.25)
        w.coverage_s[1]=[.2]*9;self.assertEqual(w.score(True,finished=True),.5)
        w.coverage_s[2]=[.2]*9;self.assertEqual(w.score(False,finished=True),.75)
        self.assertEqual(w.score(True,finished=True),1.)
if __name__=='__main__':unittest.main()
