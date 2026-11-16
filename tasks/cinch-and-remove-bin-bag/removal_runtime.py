"""Ordinary closed-loop drawtape: contact dynamics plus symmetric sliding hem."""
import numpy as np
from sliding_hem import SlidingHem
from standard_liner import HEM_COUNT,TAPE_LINK_COUNT,HEM_MASS,TAPE_MASS,bight_indices

def tensor(value):return value.torch if hasattr(value,'torch') else value
def array(value):return tensor(value).detach().cpu().numpy()

def tape_names():
    b=bight_indices()
    return ['cord_end_'+str(b.index(j)) if j in b else 'tape_%03d'%j for j in range(TAPE_LINK_COUNT)]

class DrawstringRuntime:
    def __init__(self,env):
        import warp as wp
        from isaaclab_physx.physics import PhysxManager
        self.base=env.unwrapped;self.count=0;self.wp=wp
        self.objects=[self.base.scene.rigid_objects[n] for n in [*[f'hem_{j:02d}' for j in range(HEM_COUNT)],*tape_names()]]
        paths=[o.root_view.prim_paths[0] for o in self.objects]
        self.view=PhysxManager.get_physics_sim_view().create_rigid_body_view(paths)
        actual=list(self.view.prim_paths)
        if self.view.count!=len(paths) or set(actual)!=set(paths):raise RuntimeError('Tape body view mismatch')
        self.order=np.array([actual.index(p) for p in paths])
        self.indices=wp.array(np.arange(len(paths),dtype=np.int32),dtype=wp.int32,device=self.base.device)
        self.zero_torque=wp.zeros(len(paths)*3,dtype=wp.float32,device=self.base.device)
        p=self.positions();self.cable=SlidingHem(p[:HEM_COUNT],p[HEM_COUNT:],HEM_MASS,TAPE_MASS/TAPE_LINK_COUNT)
        self.original=self.base.scene.write_data_to_sim
        self.base.scene.write_data_to_sim=self.write_forces
    def positions(self):return self.view.get_transforms().numpy()[self.order,:3]
    def detach(self):self.base.scene.write_data_to_sim=self.original
    def write_forces(self):
        p=self.positions();v=self.view.get_velocities().numpy()[self.order,:3]
        hf,tf=self.cable.forces(p[:HEM_COUNT],p[HEM_COUNT:],v[:HEM_COUNT],v[HEM_COUNT:],float(self.base.cfg.sim.dt))
        f=np.concatenate([hf,tf])
        if not np.isfinite(f).all() or np.abs(f).max()>10:raise RuntimeError('Invalid sliding hem force')
        raw=np.empty_like(f);raw[self.order]=f
        self.force_wp=self.wp.array(raw.astype(np.float32).ravel(),dtype=self.wp.float32,device=self.base.device)
        self.count+=1;self.original()
        self.view.apply_forces_and_torques_at_position(force_data=self.force_wp,torque_data=self.zero_torque,position_data=None,indices=self.indices,is_global=True)

def observation(env,step,mouth_ids):
    base=env.unwrapped
    vertices=array(base.scene.deformable_objects['loaded_bag'].data.nodal_pos_w)[0].copy()
    neck=vertices[mouth_ids]
    s={'step':step,'mouth_diameter':float(np.linalg.norm(neck[:,None]-neck[None,:],axis=2).max())}
    for key,attr in [('rubbish','root_pos_w'),('rubbish_quaternions','root_quat_w'),('rubbish_velocities','root_lin_vel_w')]:
        s[key]=[array(getattr(base.scene.rigid_objects[f'rubbish_{i}'].data,attr))[0].tolist() for i in range(6)]
    from yam_arena.runtime import tcp_world
    s['tcp']=[tcp_world(base.scene.articulations[n]).tolist() for n in ['left_robot','right_robot']]
    s['cord_end_positions']=[array(base.scene.rigid_objects[f'cord_end_{i}'].data.root_pos_w)[0].tolist() for i in range(2)]
    s['drawtape_positions']=[array(base.scene.rigid_objects[n].data.root_pos_w)[0].tolist() for n in tape_names()]
    s['drawtape_quaternions']=[array(base.scene.rigid_objects[n].data.root_quat_w)[0].tolist() for n in tape_names()]
    return s,vertices
