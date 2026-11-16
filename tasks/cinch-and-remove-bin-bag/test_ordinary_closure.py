import unittest
from evaluate_removal import evaluate
from test_table_deposit import table_fixture

class ClosureEvidenceTests(unittest.TestCase):
    def test_narrow_mouth_and_placement_do_not_prove_a_knot(self):
        t,v,p=table_fixture();p['require_ordinary_closure']=True
        r=evaluate(t,v,p)
        self.assertEqual(r['placement_geometry_score'],1.)
        self.assertEqual(r['score'],.25)
        self.assertFalse(r['full_task_success'])
    def test_controller_knot_flag_cannot_award_closure_credit(self):
        t,v,p=table_fixture();p['require_ordinary_closure']=True
        for s in t:s.update(knot_verified=True,phase='knot_complete')
        self.assertEqual(evaluate(t,v,p)['score'],.25)
    def test_spilled_load_cannot_receive_cinch_credit(self):
        t,v,p=table_fixture();p['require_ordinary_closure']=True
        t[-1]['rubbish'][0][0]+=1.
        self.assertEqual(evaluate(t,v,p)['score'],0.)

if __name__=='__main__':unittest.main()
