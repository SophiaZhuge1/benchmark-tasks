import unittest
from security_model import Observation,SecurityModel
from analyze_trace import replay

class TraceTests(unittest.TestCase):
    def trace(self):
        m=SecurityModel();rows=[]
        observations=[Observation(),Observation(old_seated=False,latch_m=.055)]
        observations += [Observation(old_seated=False,old_parked=True,replacement_seated=True)]*20
        for i,o in enumerate(observations,1):
            m.step(.05,o);rows.append({'step':i,'t':round(i*.05,6),**m.report()})
        return rows
    def test_complete_trace(self):self.assertEqual(replay(self.trace())['score'],1)
    def test_missing_step(self):
        rows=self.trace();del rows[3]
        with self.assertRaises(ValueError):replay(rows)
    def test_empty_trace(self):
        with self.assertRaises(ValueError):replay([])
    def test_score_mismatch(self):
        rows=self.trace();rows[-1]['score']=0
        with self.assertRaises(ValueError):replay(rows)
    def test_time_gap(self):
        rows=self.trace();rows[4]['t']+=.01
        with self.assertRaises(ValueError):replay(rows)

if __name__=='__main__':unittest.main()
