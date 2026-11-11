"""Re-score a monitor JSONL trace without importing YAM or Isaac Sim."""
import argparse
import json
from consent_model import replay

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('trace')
    args=parser.parse_args()
    with open(args.trace) as stream:
        rows=[json.loads(line) for line in stream if line.strip()]
    if not rows: parser.error('Trace is empty')
    if [r['step'] for r in rows] != list(range(1,len(rows)+1)):
        parser.error('Trace must contain one complete, sequential episode starting at step 1')
    variant,seed=rows[0]['variant'],rows[0]['seed']
    if any(r['variant']!=variant or r['seed']!=seed for r in rows):
        parser.error('Trace mixes episode settings')
    result=replay(rows,variant,seed)
    if abs(result['score']-rows[-1]['score'])>1e-9:
        parser.error('Replayed score disagrees with recorded score')
    print(json.dumps(result,indent=2))
