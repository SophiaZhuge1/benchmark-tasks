"""Mechanical invariants, separate from demonstration feasibility."""
import unittest
import numpy as np
from drawcord_physics_v37 import SlidingDrawcord,routed_length_gradient

def reset_positions():
    a=np.arange(20)*2*np.pi/20
    return np.r_[np.c_[.111*np.cos(a),.111*np.sin(a),np.zeros(20)],[[0,.22,-.071]]]

class CordMechanicsTests(unittest.TestCase):
    def test_length_gradient_matches_small_displacement(self):
        points=np.array([[0.,0,0],[1,0,0],[1,1,0],[.2,1,.4]])
        length,gradient=routed_length_gradient(points)
        direction=np.array([[.2,-.1,.3],[.4,.2,.1],[-.2,.1,.1],[.3,-.2,.2]])
        measured=(routed_length_gradient(points+1e-6*direction)[0]-length)/1e-6
        self.assertAlmostEqual(measured,float((gradient*direction).sum()),places=5)
    def test_slack_cord_has_no_force(self):
        p=reset_positions();cord=SlidingDrawcord(p,exit_index=5)
        np.testing.assert_array_equal(cord.forces(p,np.zeros_like(p)),np.zeros_like(p))
    def test_tension_conserves_net_force(self):
        p=reset_positions();cord=SlidingDrawcord(p,exit_index=5);p[-1,1]+=.16
        force=cord.forces(p,np.zeros_like(p))
        np.testing.assert_allclose(force.sum(0),0,atol=1e-12)
        self.assertLess(force[-1,1],0.)
        self.assertGreater(cord.last['tensions'][0],0.)
    def test_480hz_force_conservation(self):
        p=reset_positions();cord=SlidingDrawcord(p,exit_index=5);p[-1,1]+=.05
        force=cord.forces(p,np.zeros_like(p),dt=1/480)
        self.assertTrue(np.isfinite(force).all())
        np.testing.assert_allclose(force.sum(0),0,atol=1e-12)
        self.assertLess(force[-1,1],0.)
    def test_world_translation_changes_no_force(self):
        p=reset_positions();q=p+[1.3,-.7,.9]
        c=SlidingDrawcord(p,exit_index=5);d=SlidingDrawcord(q,exit_index=5)
        p[-1,1]+=.16;q[-1,1]+=.16
        np.testing.assert_allclose(c.forces(p,np.zeros_like(p)),d.forces(q,np.zeros_like(q)),atol=1e-12)
    def test_opposed_bights_pull_both_hands_inward_without_net_force(self):
        p=reset_positions();p=np.r_[p,[[0,-.22,-.071]]]
        cord=SlidingDrawcord(p,exit_index=5,handle_count=2)
        p[-2,1]+=.12;p[-1,1]-=.12
        force=cord.forces(p,np.zeros_like(p))
        np.testing.assert_allclose(force.sum(0),0,atol=1e-12)
        self.assertLess(force[-2,1],0.)
        self.assertGreater(force[-1,1],0.)
        np.testing.assert_allclose(force[-2,1],-force[-1,1],atol=1e-12)

if __name__=='__main__':unittest.main()
