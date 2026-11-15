"""Outcome counterexamples, not simulation feasibility evidence."""
import unittest
import numpy as np
from test_removal_scoring import fixture
from table_deposit import TableDepositJudge,TABLE_Z

def table_fixture():
    t,v,p=fixture()
    for s in t:
        s['tcp']=[[.2,.3,1.2],[.2,-.3,1.2]]
        s['cord_end_positions']=[[.2,.05,.9],[.2,-.05,.9]]
        s['rubbish_velocities']=[[0.,0.,0.] for _ in range(6)]
        if s['step']>=90:
            delta=np.array([.32,0.,TABLE_Z+.003-v[s['step']][:,2].min()])
            v[s['step']]+=delta
            s['rubbish']=(np.asarray(s['rubbish'])+delta).tolist()
            s['cord_end_positions']=[[.54,.02,1.0],[.54,-.02,1.0]]
    return t,v,p

def score(data):
    t,v,p=data;j=TableDepositJudge(p)
    for s in t:j.update(s,v[s['step']])
    return j.result()['score']

class TableTests(unittest.TestCase):
    def test_landed_released_full(self):self.assertEqual(score(table_fixture()),1.)
    def test_held_clear_is_partial(self):self.assertEqual(score(fixture()),.7)
    def test_table_with_spill_is_zero(self):
        d=table_fixture();d[0][-1]['rubbish'][0][0]+=1.;self.assertEqual(score(d),0.)
    def test_supported_by_gripper_not_full(self):
        d=table_fixture()
        for s in d[0][9:]:s['tcp'][0]=s['cord_end_positions'][0]
        self.assertEqual(score(d),.7)
    def test_still_bouncing_not_full(self):
        d=table_fixture();s=d[0][-1];d[1][s['step']][:,2]+=.020
        s['rubbish']=(np.asarray(s['rubbish'])+[0,0,.020]).tolist()
        self.assertEqual(score(d),.7)
    def test_harmless_internal_settling_is_allowed(self):
        d=table_fixture();d[0][-1]['rubbish_velocities'][0]=[0,0,.12]
        self.assertEqual(score(d),1.)
    def test_floor_not_table(self):
        d=table_fixture()
        for s in d[0][9:]:
            delta=np.array([-.9,0.,-.76]);d[1][s['step']]+=delta
            s['rubbish']=(np.asarray(s['rubbish'])+delta).tolist()
        self.assertEqual(score(d),.7)
    def test_harmless_floor_lowering_then_table_recovery(self):
        d=table_fixture();s=next(x for x in d[0] if x['step']==70)
        delta=np.array([.32,0.,-.0125+.003-d[1][70][:,2].min()])
        d[1][70]+=delta;s['rubbish']=(np.asarray(s['rubbish'])+delta).tolist()
        self.assertEqual(score(d),1.)
    def test_overhanging_table_edge_not_full(self):
        d=table_fixture()
        for s in d[0][9:]:
            delta=np.array([.34,0.,0.]);d[1][s['step']]+=delta
            s['rubbish']=(np.asarray(s['rubbish'])+delta).tolist()
        self.assertEqual(score(d),.7)
    def test_back_in_bin_not_full(self):
        d=table_fixture()
        for s in d[0][9:]:
            delta=np.array([-.32,0.,0.]);d[1][s['step']]+=delta
            s['rubbish']=(np.asarray(s['rubbish'])+delta).tolist()
        self.assertEqual(score(d),.4)
    def test_short_table_hold_not_full(self):
        t,v,p=table_fixture();self.assertLess(score((t[:-1],v,p)),1.)

if __name__=='__main__':unittest.main()
