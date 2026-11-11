"""Replay the observed physics through the current rule monitor."""
import json
from pathlib import Path
import sys
from curling_model import CurlingModel,Observation

def replay(path):
    rows=json.loads(Path(path).read_text());m=CurlingModel()
    for row in rows:
        m.step(.05,Observation(**row['observation']))
        for key in ['score','failed','reason','threat','blocked','saved']:
            assert m.report()[key]==row[key],(str(path),row['step'],key)
    return dict(trace=str(path),steps=len(rows),score=m.score,reason=m.reason,matches=True)

if __name__=='__main__':print(json.dumps([replay(x) for x in sys.argv[1:]],indent=2))
