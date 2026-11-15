"""Exercise the actual Inspect Robots adapter without claiming task success."""
from pathlib import Path
import argparse,os,sys,json
p=argparse.ArgumentParser();p.add_argument('--device',default='cuda:1');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parent
sys.path.insert(0,os.environ.get('YAM_COMPAT_ROOT',str(root)));sys.path.insert(0,str(root))
a.out.mkdir(parents=True,exist_ok=False)
import traceback
try:
    from inspect_robots import Scene
    from yam_arena.inspect_embodiment import YamArenaEmbodiment
    from types import SimpleNamespace
    import numpy as np
    from yam_arena.constants import READY
    ins=YamArenaEmbodiment(task=str(root/'arena_task.py'),device=a.device,control_hz=20,cam_width=640,cam_height=360,object_jitter=0)
    ins.reset(Scene(id='bin-removal-setup',instruction=ins.task.module.INSTRUCTION))
    from station_setup import save_views
    for _ in range(40):r=ins.step(SimpleNamespace(data=np.r_[READY,1.,READY,1.]))
    save_views(ins._env.unwrapped,a.out)
    tracker=ins.task.module.TRACKER
    result={'interface':'Inspect Robots YamArenaEmbodiment','setup_complete':True,'steps':tracker.count,'info':r.info,'score':tracker.result,'full_score_verified':False}
    (a.out/'setup_result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
    ins.close()
except Exception:
    (a.out/'error.txt').write_text(traceback.format_exc());raise
