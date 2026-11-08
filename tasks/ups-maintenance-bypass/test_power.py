import unittest
from power_model import PowerModel

class PowerTests(unittest.TestCase):
    def advance(self,p,n=20,q=.07,old=False,new=True,park=True,clear=True):
        for _ in range(n):p.step(.05,q,old,new,park,clear)
    def test_normal_start(self):
        p=PowerModel();self.advance(p,old=True,new=False,q=0);self.assertFalse(p.failed);self.assertEqual(p.score(),0)
    def test_overlap_is_continuous(self):
        p=PowerModel()
        for q in (0,.024,.025,.035,.045,.046,.07):p.step(.05,q,True,False)
        self.assertFalse(p.failed);self.assertEqual(p.score(),.25)
    def test_successful_exchange(self):
        p=PowerModel();p.step(.05,.07,True,False);self.advance(p)
        self.assertEqual(p.score(),.75);self.advance(p,q=0);self.assertEqual(p.score(),1)
    def test_outage_cannot_be_erased(self):
        p=PowerModel();p.step(.05,.07,True,False);p.step(.05,.07,False,False)
        p.step(.05,0,False,False);self.advance(p);self.advance(p,q=0)
        self.assertFalse(p.unsafe_removal)
        self.assertTrue(p.powered);self.assertEqual(p.outage_s,.05);self.assertEqual(p.score(),0)
    def test_remove_during_overlap_is_not_isolated(self):
        p=PowerModel();p.step(.05,.035,False,False)
        self.assertTrue(p.powered);self.assertTrue(p.unsafe_removal);self.assertEqual(p.score(),0)
    def test_early_return(self):
        p=PowerModel();p.step(.05,.07,True,False);p.step(.05,.07,False,False);p.step(.05,0,False,False)
        self.assertTrue(p.failed)
    def test_readiness_required(self):
        p=PowerModel();p.step(.05,.07,True,False);self.advance(p,n=18);p.step(.05,0,False,True)
        self.assertTrue(p.failed)
    def test_contact_loss_resets_readiness(self):
        p=PowerModel();p.step(.05,.07,True,False);self.advance(p);self.assertTrue(p.ready)
        p.step(.05,.07,False,False);p.step(.05,0,False,True);self.assertTrue(p.failed)
    def test_bypass_left_on_is_incomplete(self):
        p=PowerModel();p.step(.05,.07,True,False);self.advance(p,n=80);self.assertEqual(p.score(),.75)
    def test_old_not_parked_is_incomplete(self):
        p=PowerModel();p.step(.05,.07,True,False);self.advance(p,park=False);self.advance(p,q=0,park=False);self.assertEqual(p.score(),.25)
    def test_fingers_must_clear(self):
        p=PowerModel();p.step(.05,.07,True,False);self.advance(p);self.advance(p,q=0,clear=False);self.assertEqual(p.score(),.75)
    def test_post_success_outage_revokes_success(self):
        p=PowerModel();p.step(.05,.07,True,False);self.advance(p);self.advance(p,q=0);self.assertEqual(p.score(),1)
        p.step(.05,0,False,False);self.assertEqual(p.score(),0)
    def test_invalid_inputs_rejected(self):
        for dt,q in [(0,0),(-.05,0),(.05,float('nan'))]:
            with self.assertRaises(ValueError):PowerModel().step(dt,q,True,False)

if __name__=='__main__':unittest.main()
