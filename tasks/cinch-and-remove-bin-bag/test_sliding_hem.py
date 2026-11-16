"""Mechanical invariants; these tests do not establish robot feasibility."""
import unittest
import numpy as np
from standard_liner import *
from sliding_hem import SlidingHem

class OrdinaryTapeTests(unittest.TestCase):
    def setup_case(self):
        tape,_,_=tape_links();hem=hem_positions()
        return hem,tape,SlidingHem(hem,tape,HEM_MASS,TAPE_MASS/TAPE_LINK_COUNT)
    def test_no_extra_cord_length_for_prepositioned_handles(self):
        p=drawtape_nodes();length=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1).sum()
        self.assertLessEqual(length,TAPE_LENGTH)
        self.assertGreater(length,TAPE_LENGTH-.002)
    def test_bights_are_ordinary_uniform_tape_links(self):
        p,length,q=tape_links()
        self.assertLess(max(length),.007)
        self.assertEqual(len(p),80)
        self.assertEqual(bight_indices(),[20,59])
    def test_net_force_is_balanced(self):
        h,t,c=self.setup_case();h=h.copy();h[:,2]+=.003
        hf,tf=c.forces(h,t,np.zeros_like(h),np.zeros_like(t),1/480)
        np.testing.assert_allclose(hf.sum(0)+tf.sum(0),0.,atol=1e-14)
    def test_no_memory_of_minimum_perimeter(self):
        h,t,c=self.setup_case();z1=np.zeros_like(h);z2=np.zeros_like(t)
        first=c.forces(h,t,z1,z2,1/480)
        narrow=h.copy();narrow[:,:2]=[.22,0]+(narrow[:,:2]-[.22,0])*.7
        c.forces(narrow,t,z1,z2,1/480)
        for _ in range(10):returned=c.forces(h,t,z1,z2,1/480)
        np.testing.assert_allclose(returned[0],first[0],atol=1e-12)
        self.assertFalse(c.last['one_way_lock'])
    def test_translation_invariance(self):
        h,t,c=self.setup_case();d=np.array([2.,-1.,.6])
        other=SlidingHem(h+d,t+d,HEM_MASS,TAPE_MASS/TAPE_LINK_COUNT)
        a=c.forces(h,t,np.zeros_like(h),np.zeros_like(t),1/480)
        b=other.forces(h+d,t+d,np.zeros_like(h),np.zeros_like(t),1/480)
        np.testing.assert_allclose(a[0],b[0],atol=1e-12)
    def test_tangential_friction_dissipates_in_both_directions(self):
        tape=np.array([[0.,0,0],[.02,0,0],[.02,.02,0],[0,.02,0]])
        hem=np.array([[.01,0,.001]])
        for sign in (-1,1):
            c=SlidingHem(hem,tape,.001,.001)
            hv=np.array([[sign*.01,0,0.]])
            hf,tf=c.forces(hem,tape,hv,np.zeros_like(tape),1/480)
            self.assertLess(float((hf*hv).sum()),0.)

if __name__=='__main__':unittest.main()
