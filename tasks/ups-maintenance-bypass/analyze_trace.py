"""Summarise observed contact transitions and validate a recorded UPS trial."""
import argparse,json,pathlib
p=argparse.ArgumentParser();p.add_argument('trial');p.add_argument('--expect',type=float);args=p.parse_args()
root=pathlib.Path(args.trial);result=json.loads((root/'result.json').read_text());trace=json.loads((root/'trace.json').read_text())
fields=('powered','old_seated','new_seated','ready','old_parked','unsafe_removal')
last={};events=[]
for row in trace:
    changed={key:row[key] for key in fields if row[key]!=last.get(key)}
    if changed:events.append({'step':row['step'],'time':row['time'],**changed})
    last={key:row[key] for key in fields}
summary={'score':result['task_score'],'success':result['success'],'steps':result['steps'],'seconds':result['seconds'],'wall_s':result['wall_s'],'blank_frames':result['blank_frames'],'events':events,'final':result['task_metrics']}
print(json.dumps(summary,indent=2))
if args.expect is not None:assert result['task_score']==args.expect,(result['task_score'],args.expect)
if result['task_score']==1:
    assert all(row['powered'] and row['outage_s']==0 and not row['unsafe_removal'] and not row.get('dropped',False) for row in trace)
    assert trace[-1]['new_seated'] and trace[-1]['old_parked'] and trace[-1]['ready'] and trace[-1]['clear']
    assert trace[-1]['switch_mm']<=8
# Any observed interruption must remain a failure after supply is restored.
if any(not row['powered'] for row in trace):assert result['task_score']==0
