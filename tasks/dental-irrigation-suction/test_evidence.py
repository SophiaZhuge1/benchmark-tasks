"""Mock evidence tests; these fixtures are NOT simulation results."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from verify_scenarios import verify

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name);self.case=self.root/'point';self.case.mkdir()
        source=self.root/'source';source.mkdir();(source/'task.py').write_text('# fixture\n')
        (source/'manifest.json').write_text(json.dumps({'sha256':{'task.py':hashlib.sha256((source/'task.py').read_bytes()).hexdigest()}}))
        self.metrics={'supplied':6.,'mouth_water_ml':0.,'peak_mouth_water_ml':.3,'score':0.,'coverage':[1,1,1],'captured':[2.,2.,2.],'lost':0.,'failed':False,'held':True,'clear':True,'balance_error':0.}
        self.result={'mode':'point','task_score':0.,'steps':1,'termination':None,'blank_frames':0,'recorded_frames_per_camera':2,'blank_frames_by_camera':{'top_cam':0,'left_cam':0,'right_cam':0},'task_metrics':self.metrics}
        # Existence stubs: video decoding and visual inspection are separate checks.
        (self.case/'demo.mp4').write_bytes(b'not-a-real-video-fixture')
        (self.case/'setup.png').write_bytes(b'not-a-real-image-fixture')
        self.write()
    def tearDown(self):self.temp.cleanup()
    def write(self):
        (self.case/'result.json').write_text(json.dumps(self.result))
        (self.case/'trace.json').write_text(json.dumps([self.metrics]))
    def test_consistent_numeric_evidence_still_requires_visual_inspection(self):
        self.assertEqual(verify(self.case,'dental')['visual_inspection'],'required')
    def test_zero_after_unrelated_guard_failure_is_rejected(self):
        self.metrics['failed']=True;self.write()
        with self.assertRaises(AssertionError):verify(self.case,'dental')
    def test_one_blank_camera_is_rejected(self):
        self.result['blank_frames_by_camera']['left_cam']=1;self.write()
        with self.assertRaises(AssertionError):verify(self.case,'dental')
    def test_model_only_run_is_rejected(self):
        self.result['blank_frames']=None;self.write()
        with self.assertRaises(AssertionError):verify(self.case,'dental')
    def test_changed_snapshot_is_rejected(self):
        (self.root/'source/task.py').write_text('# changed\n')
        with self.assertRaises(AssertionError):verify(self.case,'dental')
    def test_incomplete_trace_is_rejected(self):
        self.result['steps']=2;self.write()
        with self.assertRaises(AssertionError):verify(self.case,'dental')
    def test_failed_water_recovery_cannot_support_coverage_claim(self):
        self.metrics['captured']=[0.,0.,0.];self.write()
        with self.assertRaises(AssertionError):verify(self.case,'dental')

if __name__=='__main__':unittest.main()
