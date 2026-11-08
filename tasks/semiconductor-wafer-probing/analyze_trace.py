"""Audit recorded scores against the per-step motion/contact trace."""
import argparse, hashlib, json
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('trial');p.add_argument('--expected',type=float)
a=p.parse_args();folder=Path(a.trial)
r=json.loads((folder/'result.json').read_text());trace=json.loads((folder/'trace.json').read_text())
transitions=[];previous={};moving=[]
for row in trace:
    for key in ('lifted','aligned','contact','damaged','released','score'):
        if key in row and row[key]!=previous.get(key):
            transitions.append(dict(time=row['time'],field=key,value=row[key]))
    if previous and abs(row['stage_mm']-previous['stage_mm'])>.05:
        moving.append(min(row['lift_mm'],previous['lift_mm']))
    if previous:
        assert row['scrape_mm'] >= previous['scrape_mm']-1e-6
        assert not previous['damaged'] or row['damaged']
    previous=row
if a.expected is not None:assert r['task_score']==a.expected,(r['task_score'],a.expected)
if r['task_score']==1.:
    assert r['success'] and not any(row['damaged'] for row in trace)
    assert trace[-1]['aligned'] and trace[-1]['contact'] and trace[-1]['released']
    assert trace[-1]['final_dwell']>=1.
elif r['mode'] in ('drag','early_release'):
    assert r['task_score']==0. and trace[-1]['damaged'] and trace[-1]['aligned']
elif r['mode']=='leave_lifted':
    assert r['task_score']==.75 and trace[-1]['aligned'] and not trace[-1]['contact']
summary=dict(mode=r['mode'],score=r['task_score'],steps=r['steps'],seconds=r['seconds'],
    wall_seconds=r['wall_s'],blank_frames=r['blank_frames'],final=trace[-1],
    minimum_lift_during_observed_motion_mm=min(moving) if moving else None,
    transitions=transitions)
(folder/'events.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
