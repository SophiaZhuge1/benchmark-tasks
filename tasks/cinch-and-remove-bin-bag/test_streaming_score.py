import copy,unittest
import numpy as np
from evaluate_removal import RemovalJudge,evaluate
from evaluate_removal import evaluate as previous_evaluate
from test_removal_scoring import fixture
class StreamingScoringTests(unittest.TestCase):
 def test_streaming_matches_batch_at_each_recorded_state(self):
  trace,states,p=fixture();judge=RemovalJudge(p)
  for i,s in enumerate(trace):
   got=judge.update(s,states[s['step']]);want=previous_evaluate(trace[:i+1],states,p)
   self.assertEqual(got,want)
 def test_brief_spill_between_ten_step_samples_is_rejected(self):
  trace,states,p=fixture();dense=[];snapshots={}
  for step in range(131):
   lower=(step//10)*10;upper=min(lower+10,130);alpha=(step-lower)/10
   s=copy.deepcopy(trace[lower//10]);s['step']=step
   s['rubbish']=(np.array(trace[lower//10]['rubbish'])*(1-alpha)+np.array(trace[upper//10]['rubbish'])*alpha).tolist()
   vertices=states[lower]*(1-alpha)+states[upper]*alpha
   judge=RemovalJudge(p);neck=vertices[judge.mouth_ids];s['mouth_diameter']=float(np.linalg.norm(neck[:,None]-neck[None,:],axis=2).max())
   snapshots[step]=vertices;dense.append(s)
  p['sample_interval_steps']=1
  self.assertEqual(evaluate(dense,snapshots,p)['score'],1.)
  dense[67]['rubbish'][0][0]=.8
  self.assertEqual(evaluate(dense,snapshots,p)['reason'],'Waste lost from bag')
if __name__=='__main__':unittest.main()
