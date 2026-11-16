"""Run the same scene/scorer for scripted and Dream-1 episodes."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
from prepare_runtime import prepare
ROOT=Path(__file__).resolve().parent
from standard_liner import INSTRUCTION

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['setup','demo','model']);p.add_argument('--adapter',type=Path,required=True);p.add_argument('--arena-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--python',default=sys.executable);p.add_argument('--device',default='cuda:0');a=p.parse_args()
    out=a.out.resolve()
    if out.exists():p.error('Use a fresh output directory')
    overlay=prepare(a.adapter);env=os.environ.copy();env['YAM_COMPAT_ROOT']=str(overlay)
    env['PYTHONPATH']=os.pathsep.join([str(ROOT),str(overlay),env.get('PYTHONPATH','')])
    if a.mode=='model':
        out.mkdir(parents=True);env['BIN_EVIDENCE_DIR']=str(out/'geometry')
        cli=Path(a.python).resolve().parent/'inspect-robots'
        # Resolve scripts from the supplied environment, not the system Python.
        cli=Path(a.python).parent/'inspect-robots'
        command=[str(cli),'run','--embodiment','yam_arena','--policy','dream','-E','task='+str(ROOT/'arena_task.py'),'-E','object_jitter=0','-E','control_hz=20','-E','cam_width=320','-E','cam_height=176','-E','device='+a.device,'--instruction',INSTRUCTION,'--scorer','task_score','--max-steps','4000','--seed','0','--epochs','1','--no-prompt','--store-frames','--log-dir',str(out/'model_logs')]
    else:
        command=[a.python,'-u',str(ROOT/'task.py'),a.mode,'--out',str(out),'--device',a.device,'--interface','inspect']
    start=time.monotonic();rc=subprocess.call(command,env=env,cwd=a.arena_root.resolve())
    status={'mode':a.mode,'exit_code':rc,'wall_seconds':round(time.monotonic()-start,2),'seed':0,'run_limit_steps':4000}
    if out.exists():(out/'launch_status.json').write_text(json.dumps(status,indent=2))
    return rc

if __name__=='__main__':raise SystemExit(main())
