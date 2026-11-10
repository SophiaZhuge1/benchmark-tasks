"""Independently replay a demo trace using the shipped trajectory scorer."""
import argparse,dataclasses,json,pathlib
from security_model import Observation,SecurityModel

def replay(rows):
    if not rows:raise ValueError('Empty trace is not a trial')
    names=[f.name for f in dataclasses.fields(Observation)]
    m=SecurityModel();previous_t=0.;previous_step=0
    for row in rows:
        if row['step']!=previous_step+1:raise ValueError('Missing or unordered control steps')
        t=float(row['t']);dt=t-previous_t
        if abs(dt-.05)>1e-5:raise ValueError('Expected contiguous 20 Hz trace')
        obs=Observation(**{key:row[key] for key in names})
        actual=m.step(dt,obs)
        if abs(actual-float(row['score']))>1e-6:raise ValueError('Recorded score differs from replay')
        previous_t=t;previous_step=row['step']
    return m.report()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('trace');p.add_argument('--output');a=p.parse_args()
    path=pathlib.Path(a.trace)
    rows=[json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.suffix=='.jsonl' else json.loads(path.read_text())
    result=replay(rows)
    text=json.dumps(result,indent=2)+'\n'
    if a.output:pathlib.Path(a.output).write_text(text)
    print(text)
