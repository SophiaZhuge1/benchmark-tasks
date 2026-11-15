"""Synthetic scoring counterexamples; never physical feasibility evidence."""
import copy
import unittest
import numpy as np
import trimesh
from evaluate_removal import evaluate
from realistic_meshes_v32 import dirty_mesh

def fixture(early_lift=False):
    vertices,faces,mouth=dirty_mesh()
    closed=vertices.copy()
    n=len(mouth)
    # Unfold/gather the spare cuff while retaining the loaded lower bag volume.
    rings=[(.086*t/4,0.) for t in range(1,5)]
    rings += [(.086,.135*t/9) for t in range(1,10)]
    rings += [(.080,.145),(.075,.155)]
    rings += [(float(r),float(z)) for r,z in zip(np.linspace(.075,.020,10)[1:],np.linspace(.155,.220,10)[1:])]
    for k,(radius,z) in enumerate(rings):
        angle=np.arange(n)*2*np.pi/n
        closed[1+k*n:1+(k+1)*n]=np.c_[radius*np.cos(angle),radius*np.sin(angle),np.full(n,z)]
    initial=trimesh.Trimesh(vertices=vertices,faces=faces,process=False).vertices
    gathered=trimesh.Trimesh(vertices=closed,faces=faces,process=False).vertices
    trace=[];snapshots={}
    for step in range(0,131,10):
        cinch=np.clip((step-30)/30,0,1)
        lift=.195*np.clip((step-60)/30,0,1)
        if early_lift and 0<step<30:lift=.195
        v=initial*(1-cinch)+gathered*cinch+[.22,0,.768+lift]
        neck=v[mouth];diameter=float(np.linalg.norm(neck[:,None,:]-neck[None,:,:],axis=2).max())
        centres=[[.22+(.03 if i%2 else -.03),0,.786+.041*(i//2)+lift] for i in range(6)]
        trace.append({'step':step,'mouth_diameter':diameter,'rubbish':centres,'rubbish_quaternions':[[0,0,0,1] for _ in range(6)]})
        snapshots[step]=v
    return trace,snapshots,{'bin_top_z':.918,'bin_center_xy':[.22,0.]}

class RemovalScoringTests(unittest.TestCase):
    def test_full_completion(self):self.assertEqual(evaluate(*fixture())['score'],1.)
    def test_harmless_early_lift_then_recovery(self):
        normal=fixture();recovery=fixture(True)
        np.testing.assert_array_equal(normal[1][130],recovery[1][130])
        self.assertEqual(evaluate(*recovery)['score'],1.)
    def test_set_down_beside_bin_is_full(self):
        t,v,p=fixture()
        for s in t[9:]:
            v[s['step']]+=np.array([.32,0,-.195])
            s['rubbish']=(np.array(s['rubbish'])+[.32,0,-.195]).tolist()
        self.assertEqual(evaluate(t,v,p)['score'],1.)
    def test_lowered_back_inside_bin_is_not_full(self):
        t,v,p=fixture()
        for s in t[9:]:
            v[s['step']][:,2]-=.195
            s['rubbish']=(np.array(s['rubbish'])+[0,0,-.195]).tolist()
        self.assertEqual(evaluate(t,v,p)['score'],.4)
    def test_cinch_only_is_partial(self):
        t,v,p=fixture();self.assertEqual(evaluate(t[:7],v,p)['score'],.4)
    def test_insufficient_hold_is_not_full(self):
        t,v,p=fixture();self.assertLess(evaluate(t[:-1],v,p)['score'],1.)
    def test_open_bag_is_zero(self):
        t,v,p=fixture();t=t[:4];self.assertEqual(evaluate(t,v,p)['score'],0.)
    def test_preclosed_initial_bag_is_zero(self):
        t,v,p=fixture();t[0]['mouth_diameter']=.04
        self.assertEqual(evaluate(t,v,p)['score'],0.)
    def test_missing_waste_is_zero(self):
        t,v,p=fixture();t[-1]['rubbish'].pop()
        self.assertEqual(evaluate(t,v,p)['score'],0.)
    def test_spill_then_recovery_is_zero(self):
        t,v,p=fixture();t[7]['rubbish'][0][0]=.8
        self.assertEqual(evaluate(t,v,p)['score'],0.)
    def test_invented_closure_measurement_is_zero(self):
        t,v,p=fixture();t[2]['mouth_diameter']=.02
        self.assertEqual(evaluate(t,v,p)['score'],0.)
    def test_film_overstretch_is_zero(self):
        t,v,p=fixture();v[70][42,0]+=.10
        self.assertEqual(evaluate(t,v,p)['score'],0.)
    def test_gap_in_evidence_is_zero(self):
        t,v,p=fixture();t.pop(4)
        self.assertEqual(evaluate(t,v,p)['score'],0.)
    def test_bag_clears_but_contents_do_not_is_not_full(self):
        t,v,p=fixture()
        for s in t[9:]:s['rubbish'][0][2]=.90
        self.assertLess(evaluate(t,v,p)['score'],1.)
    def test_run_limit_is_enforced(self):
        t,v,p=fixture();t[-1]['step']=4001
        self.assertEqual(evaluate(t,v,p)['score'],0.)

if __name__=='__main__':unittest.main()
