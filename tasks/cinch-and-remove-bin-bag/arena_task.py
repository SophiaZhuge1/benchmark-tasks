"""Ordinary factory drawtape liner development scene; closure not yet validated."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
import mechkit as m
from yam_arena.task_file import Box
from ordinary_closure import OrdinaryLinerJudge as RemovalJudge

SCENE='station'
STANDARD_LINER=True
from standard_liner import INSTRUCTION
SUCCESS_HOLD_S=0.
SCORE_OVER='end'
OBJECTS=[Box(name=f'rubbish_{i}',pos=(.22+(.025 if i%2 else -.025),0,.786+.036*(i//2)),size=(.048,.080,.035),mass=.025) for i in range(6)]
ANCHORS={}

original_patch=m._patch_scene
def patch_scene(scene):
    original_patch(scene)
    original_build=scene.build_task_environment
    def build(embodiment,task,control_hz=None):
        if getattr(task.module,'INSTRUCTION',None)!=INSTRUCTION:return original_build(embodiment,task,control_hz)
        from isaaclab_arena.environments.isaaclab_arena_environment import IsaacLabArenaEnvironment
        from isaaclab_arena.scene.scene import Scene
        from yam_arena.embodiment import BimanualYamEmbodiment
        from scipy.spatial.transform import Rotation
        from removal_assets import build_assets
        assets,anchors,_=build_assets();ANCHORS.clear();ANCHORS.update(anchors)
        # anchors is populated during asset spawn, so retain its live mapping.
        TRACKER.anchors=anchors
        cameras=BimanualYamEmbodiment(rig=embodiment.rig,enable_cameras=True,overview_cam=True,cam_width=640,cam_height=360)
        embodiment.camera_config=cameras.camera_config
        eye=np.array([1.15,2.0,1.85]);forward=np.array([.20,.30,.72])-eye;forward/=np.linalg.norm(forward)
        left=np.cross([0.,0.,1.],forward);left/=np.linalg.norm(left);up=np.cross(forward,left)
        embodiment.camera_config.overview_cam.offset.pos=tuple(eye)
        embodiment.camera_config.overview_cam.offset.rot=tuple(Rotation.from_matrix(np.stack([forward,left,up],axis=1)).as_quat())
        for side in ['left','right']:
            robot=getattr(embodiment.scene_config,side+'_robot')
            robot.actuators['gripper'].joint_effort_limit=8.
            from isaaclab_physx.sim.schemas import PhysxCollisionPropertiesCfg
            robot.spawn.collision_props=PhysxCollisionPropertiesCfg(contact_offset=.001,rest_offset=0.)
        def configure(cfg):
            cfg=scene.env_cfg_callback(control_hz)(cfg);cfg.sim.dt=1/480.;cfg.decimation=24;cfg.sim.render_interval=96;p=cfg.sim.physics
            p.gpu_max_rigid_contact_count=2**17;p.gpu_max_rigid_patch_count=2**15;p.gpu_found_lost_pairs_capacity=2**16
            p.gpu_found_lost_aggregate_pairs_capacity=2**18;p.gpu_total_aggregate_pairs_capacity=2**16
            p.gpu_max_soft_body_contacts=2**16;p.gpu_max_particle_contacts=2**16
            return cfg
        return IsaacLabArenaEnvironment(name='bin_removal_inspect',scene=Scene(assets),embodiment=embodiment,env_cfg_callback=configure)
    scene.build_task_environment=build
m._patch_scene=patch_scene
m._Finder.targets['yam_arena.scene']=patch_scene
if 'yam_arena.scene' in sys.modules:patch_scene(sys.modules['yam_arena.scene'])

# Remove the previous episode's force callback before reset settles the scene.
original_embodiment_patch=m._patch_embodiment
def patch_embodiment(module):
    original_embodiment_patch(module)
    cls=module.YamArenaEmbodiment
    if getattr(cls,'_bin_reset_hook',False):return
    original_reset=cls.reset
    def reset(self,*a,**kw):
        if getattr(getattr(self,'task',None),'module',None) is not None and getattr(self.task.module,'INSTRUCTION',None)==INSTRUCTION and TRACKER.runtime is not None:
            TRACKER.runtime.detach();TRACKER.runtime=None
        return original_reset(self,*a,**kw)
    original_close=cls.close
    def close(self,*a,**kw):
        # Isaac can terminate before Python atexit runs. Persist the last
        # observations before simulator shutdown, including policy errors.
        task=getattr(getattr(self,'task',None),'module',None)
        if getattr(task,'INSTRUCTION',None)==INSTRUCTION:TRACKER.flush()
        return original_close(self,*a,**kw)
    cls.reset=reset;cls.close=close;cls._bin_reset_hook=True
m._patch_embodiment=patch_embodiment
m._Finder.targets['yam_arena.inspect_embodiment']=patch_embodiment
if 'yam_arena.inspect_embodiment' in sys.modules:patch_embodiment(sys.modules['yam_arena.inspect_embodiment'])

class Tracker:
    def __init__(self):
        self.runtime=None;self.anchors={};self.result={'score':0.};self.count=0;self.save_dir=None;self.trace=[];self.episode=-1
        import atexit
        atexit.register(self.flush)
    def flush(self):
        if self.save_dir is not None:
            import json
            (self.save_dir/'trace.json').write_text(json.dumps(self.trace))
            (self.save_dir/'live_result.json').write_text(json.dumps(self.result,indent=2))
    def reset(self,env):
        from removal_runtime import DrawstringRuntime
        if self.runtime is not None:self.runtime.detach()
        self.runtime=DrawstringRuntime(env);self.count=0;self.trace=[];self.snapshots={};self.result={'score':0.}
        import os,json,hashlib
        parameters={'bin_top_z':.918,'bin_center_xy':[.22,0.],'sample_interval_steps':1,'require_table_deposit':True,'require_ordinary_closure':True,'control_hz':20}
        self.judge=RemovalJudge(parameters)
        if os.environ.get('BIN_EVIDENCE_DIR'):
            self.episode+=1;self.save_dir=Path(os.environ['BIN_EVIDENCE_DIR'])/f'episode_{self.episode:03d}'
            self.save_dir.mkdir(parents=True,exist_ok=False)
            (self.save_dir/'task_parameters.json').write_text(json.dumps(parameters,indent=2))
            (self.save_dir/'source_hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')},indent=2))
        self.record(env)
    def record(self,env):
        from removal_runtime import observation
        s,v=observation(env,self.count,self.anchors['loaded_bag']);self.trace.append(s);self.snapshots[self.count]=v
        self.result=self.judge.update(s,v)
        if self.save_dir is not None:
            np.savez_compressed(self.save_dir/f'state_{self.count:04d}.npz',loaded_bag=v[None])
            if self.count%10==0:self.flush()
    def step(self,env):
        self.count+=1
        self.record(env)
TRACKER=Tracker()
m.on_reset(TRACKER.reset)
m.on_step(TRACKER.step)
def score(objects):return float(TRACKER.result.get('score',0.))
def success(objects):return score(objects)==1.
