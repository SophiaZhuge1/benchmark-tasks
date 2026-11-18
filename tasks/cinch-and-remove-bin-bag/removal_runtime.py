"""Force callback and geometry observations shared by the evaluation adapter."""
import numpy as np
from drawstring_physics import SlidingDrawstring
from removal_assets import BLOCK_COUNT

EXIT_INDEX=5      # hem markers 5 and 15: the two opposite cut-outs
LOOP_MASS=.002    # kg, pinched loop of drawstring
# Inertia used by the implicit string solve: hem bead plus the film it drags
# (about 2 g) and loop body plus its string (about 4 g). With the bare 1-2 g
# bead masses the one-step solve lets the string stretch by several cm.
SOLVER_HEM_MASS=.0015
SOLVER_LOOP_MASS=.003
STRING_COLOR=(.80,.80,.78)

def tensor(value):
    return value.torch if hasattr(value,"torch") else value

def array(value):
    if hasattr(value,'torch'):value=value.torch
    return value.detach().cpu().numpy()

class DrawstringRuntime:
    def __init__(self,env):
        import torch
        import warp as wp
        from isaaclab_physx.physics import PhysxManager
        import omni.usd
        from pxr import UsdGeom,Gf,Vt
        self.base=env.unwrapped;self.torch=torch;self.Vt=Vt;self.count=0
        self.objects=[self.base.scene.rigid_objects[n] for n in [*[f'hem_{j:02d}' for j in range(20)],'cord_end_0','cord_end_1']]
        # A single PhysX view avoids 22 separate wrench composers per substep.
        # Only forces are written; object poses and velocities are never set.
        paths=[o.root_view.prim_paths[0] for o in self.objects]
        self.view=PhysxManager.get_physics_sim_view().create_rigid_body_view(paths)
        actual=list(self.view.prim_paths)
        if self.view.count!=len(paths) or set(actual)!=set(paths):raise RuntimeError('Cord body view mismatch')
        self.order=np.array([actual.index(path) for path in paths])
        self.wp=wp;self.indices=wp.array(np.arange(len(paths),dtype=np.int32),dtype=wp.int32,device=self.base.device)
        self.zero_torque=wp.zeros(len(paths)*3,dtype=wp.float32,device=self.base.device)
        self.cable=SlidingDrawstring(self.positions(),exit_index=EXIT_INDEX,hem_mass=SOLVER_HEM_MASS,loop_mass=SOLVER_LOOP_MASS)
        stage=omni.usd.get_context().get_stage()
        # Visual-only polyline showing the string path (hem, cut-outs, loops).
        c=UsdGeom.BasisCurves.Define(stage,'/World/drawstring')
        c.CreateTypeAttr('linear');c.CreateCurveVertexCountsAttr([len(self.cable.route)]);c.CreateWidthsAttr([.004]);c.SetWidthsInterpolation('constant');c.CreateDisplayColorAttr([Gf.Vec3f(*STRING_COLOR)]);self.curves=[c]
        self.original=self.base.scene.write_data_to_sim
        self.base.scene.write_data_to_sim=self.write_forces
    def positions(self):return self.view.get_transforms().numpy()[self.order,:3]
    def detach(self):self.base.scene.write_data_to_sim=self.original
    def write_forces(self):
        pos=self.positions();vel=self.view.get_velocities().numpy()[self.order,:3];force=self.cable.forces(pos,vel,dt=float(self.base.cfg.sim.dt))
        if not np.isfinite(force).all() or np.abs(force).max()>10:raise RuntimeError('Invalid drawstring force')
        if self.count%48==0:
            for c,r in zip(self.curves,[self.cable.route]):c.GetPointsAttr().Set(self.Vt.Vec3fArray.FromNumpy(pos[r].astype(np.float32)))
        raw_force=np.empty_like(force);raw_force[self.order]=force
        self.force_wp=self.wp.array(raw_force.astype(np.float32).ravel(),dtype=self.wp.float32,device=self.base.device)
        self.count+=1;self.original()
        self.view.apply_forces_and_torques_at_position(force_data=self.force_wp,torque_data=self.zero_torque,position_data=None,indices=self.indices,is_global=True)

def observation(env,step,mouth_ids):
    base=env.unwrapped
    vertices=array(base.scene.deformable_objects['loaded_bag'].data.nodal_pos_w)[0].copy()
    neck=vertices[mouth_ids]
    state={'step':step,'mouth_diameter':float(np.linalg.norm(neck[:,None]-neck[None,:],axis=2).max())}
    for key,attribute in [('rubbish','root_pos_w'),('rubbish_quaternions','root_quat_w')]:
        state[key]=[array(getattr(base.scene.rigid_objects[f'rubbish_{i}'].data,attribute))[0].tolist() for i in range(BLOCK_COUNT)]
    from yam_arena.runtime import tcp_world
    state['tcp']=[tcp_world(base.scene.articulations[name]).tolist() for name in ['left_robot','right_robot']]
    state['cord_end_positions']=[array(base.scene.rigid_objects[f'cord_end_{i}'].data.root_pos_w)[0].tolist() for i in range(2)]
    state['loop_points']=[[p] for p in state['cord_end_positions']]
    state['rubbish_velocities']=[array(base.scene.rigid_objects[f'rubbish_{i}'].data.root_lin_vel_w)[0].tolist() for i in range(BLOCK_COUNT)]
    return state,vertices

