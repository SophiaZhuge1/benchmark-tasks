import math
"""Collect verified two-arm curling recordings and their reproducibility evidence."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from replay_trace import replay

def main():
    ap=argparse.ArgumentParser();ap.add_argument('run_dir');a=ap.parse_args()
    root=Path(a.run_dir).resolve();p=Path(__file__).resolve().parent
    suite=unittest.defaultTestLoader.discover(str(p),pattern='test_*.py')
    count=suite.countTestCases();test_result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not test_result.wasSuccessful():raise RuntimeError('Rule tests failed')
    v=p/'validation';v.mkdir(exist_ok=True);media=p/'media';media.mkdir(exist_ok=True)
    summaries=[];traces=[]
    for mode in ['full','no_rescue','none']:
        folder=root/mode;d=json.loads((folder/'result.json').read_text());t=d['task_metrics']
        d['video']=f'media/{"demo" if mode=="full" else mode}.mp4' if mode!='none' else None
        (v/(mode+'_result.json')).write_text(json.dumps(d,indent=2)+'\n')
        shutil.copy(folder/'trace.json',v/(mode+'_trace.json'))
        check=replay(v/(mode+'_trace.json'));check['trace']='validation/'+Path(check['trace']).name;traces.append(check)
        summaries.append(dict(mode=mode,score=d['task_score'],steps=d['steps'],sim_seconds=d['seconds'],wall_seconds=d['wall_s'],
            blank_frames=d['blank_frames'],reason=t['reason'],threat_t=t['threat_t'],block_t=t['block_t'],saved=t['saved'],
            blue_distance_m=math.hypot(t['pucks']['blue']['pos'][0]-.710,t['pucks']['blue']['pos'][1]-.180),puck_positions={n:s['pos'] for n,s in t['pucks'].items()},ik_worst=d['ik_worst']))
    assert summaries[0]['score']==1 and summaries[0]['saved'],'Full demonstration not completed'
    assert summaries[1]['score']==0 and summaries[1]['reason']=='puck_left_board','No-rescue comparison did not leave board'
    assert summaries[2]['score']==0,'No-action control unexpectedly scored'
    assert all(s['blank_frames']==0 for s in summaries),'Blank camera frames'
    source=json.loads((root/'source/manifest.json').read_text())
    checked=['task.py','curling_model.py','demokit.py','mechkit.py','labels.py']
    matches={n:hashlib.sha256((p/n).read_bytes()).hexdigest()==source['sha256'][n] for n in checked}
    assert all(matches.values()),'Recording source differs from packaged implementation'
    (v/'recorded_source_manifest.json').write_text(json.dumps(source,indent=2)+'\n')
    status=dict(status='TWO_ARM_RESCUE_VALIDATED',date=date.today().isoformat(),seed=0,board_m=[.84,.42],pucks=4,
        rule_tests=count,rule_tests_passed=True,recording_source_matches=matches,results=summaries,trace_replays=traces,
        dream1_run=False,published=False,scope='Fixed-layout seed-0 scripted physics demo and paired controls; no general hardware certification')
    (v/'status.json').write_text(json.dumps(status,indent=2)+'\n')
    for name in ['demo.mp4','setup.png']:shutil.copy(root/'full'/name,media/name)
    shutil.copy(root/'no_rescue/demo.mp4',media/'no_rescue.mp4')
    for mode,name in [('full','final.png'),('no_rescue','no_rescue.png')]:
        subprocess.run(['ffmpeg','-y','-loglevel','error','-sseof','-0.1','-i',str(root/mode/'top_cam.mp4'),'-frames:v','1',str(media/name)],check=True)
    subprocess.run(['ffmpeg','-y','-loglevel','error','-ss','5.5','-i',str(root/'full/top_cam.mp4'),
        '-vf','fps=2,scale=480:270,tile=3x2','-frames:v','1',str(media/'rescue_sequence.jpg')],check=True)
    data=json.loads((p/'task.json').read_text());data['scores']='Scripted two-arm demo: 1.0; no-rescue and no-action: 0.0; Dream-1 not run.'
    (p/'task.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(status,indent=2))

if __name__=='__main__':main()
