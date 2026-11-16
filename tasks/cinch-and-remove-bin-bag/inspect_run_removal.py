"""Loaded drawstring bag removal using YAM / Isaac Lab Arena.

No pre-tied neck, replacement liner or retaining ring. A force-based sliding-cord approximation acts on dynamic hem markers; no object poses are controlled.
"""
from pathlib import Path
import sys, os, json, traceback, argparse
parser=argparse.ArgumentParser();parser.add_argument("--mode",choices=["setup","cinch","interactive","full"],default="cinch");parser.add_argument("--camera",action="store_true");parser.add_argument("--run",default="realistic_v21_run");parser.add_argument('--device',default='cuda:0');args=parser.parse_args()
HERE=Path(__file__).resolve().parent
sys.path.insert(0,os.environ.get('YAM_COMPAT_ROOT',str(HERE)))
sys.path.insert(0,str(HERE))
HERE=HERE/args.run
HERE.mkdir(parents=True,exist_ok=False)
for n in [Path(__file__).name,'realistic_meshes_v32.py','standard_liner.py','sliding_hem.py','ordinary_closure.py','removal_assets.py','evaluate_removal.py','containment.py','table_deposit.py','plan_table_transfer.py','arena_task.py','removal_runtime.py']:(HERE/('source_'+n)).write_text((Path(__file__).resolve().parent/n).read_text())
app=None

def main():
    from inspect_robots import Scene as InspectScene
    from yam_arena.inspect_embodiment import YamArenaEmbodiment
    from types import SimpleNamespace
    inspect=YamArenaEmbodiment(task=str(Path(__file__).resolve().parent/'arena_task.py'),device=args.device,control_hz=20,cam_width=640,cam_height=360,object_jitter=0)
    inspect.reset(InspectScene(id='bin-removal-scripted',instruction=inspect.task.module.INSTRUCTION))
    import numpy as np
    import torch, trimesh
    import isaaclab.sim as sim
    from pxr import UsdGeom, Gf, Vt
    import omni.usd
    from isaaclab.sim.utils import clone
    from isaaclab.sim.spawners.meshes.meshes import _spawn_mesh_geom_from_mesh
    from isaaclab_physx.sim.schemas import PhysxCollisionCfg, PhysxDeformableBodyPropertiesCfg, PhysxRigidBodyPropertiesCfg, PhysxCollisionPropertiesCfg
    from isaaclab_physx.sim.spawners.materials import PhysxSurfaceDeformableBodyMaterialCfg
    from isaaclab_arena.assets.deformable_object import DeformableObject
    from isaaclab_arena.assets.object import Object
    from isaaclab_arena.assets.object_type import ObjectType
    from isaaclab_arena.environments.isaaclab_arena_environment import IsaacLabArenaEnvironment
    from isaaclab_arena.environments.arena_env_builder import ArenaEnvBuilder
    from isaaclab_arena.environments.arena_env_builder_cfg import ArenaEnvBuilderCfg
    from isaaclab_arena.scene.scene import Scene
    from isaaclab_arena.utils.pose import Pose
    from yam_arena.embodiment import BimanualYamEmbodiment
    from yam_arena.scene import scene_assets, env_cfg_callback
    from yam_arena.constants import READY, LEFT_BASE_POS, RIGHT_BASE_POS
    from yam_arena.runtime import tcp_world, arm_q, link_poses
    from yam_arena.ik import solve
    from PIL import Image
    from removal_assets import build_assets
    from yam_arena import station
    from station_setup import rig as standard_rig, setup_manifest, save_views, setup_result
    env=inspect._env;base=env.unwrapped
    anchors=inspect.task.module.TRACKER.anchors;bead_count=20
    LEFT_BASE_POS,RIGHT_BASE_POS=station.BASES['left'],station.BASES['right']
    from yam_arena.ik import tcp_pose
    from scipy.spatial.transform import Rotation
    q_ready=[np.asarray(READY,dtype=float).copy() for _ in range(2)]
    initial_rotations=[Rotation.from_matrix(tcp_pose(q,b)[1]).as_quat().tolist() for q,b in zip(q_ready,[LEFT_BASE_POS,RIGHT_BASE_POS])]
    setup_manifest(HERE,SimpleNamespace(rig=inspect.rig),'bin',args.mode,Path(__file__).parent)
    manifest=json.loads((HERE/'setup_manifest.json').read_text());manifest['interface']='Inspect Robots YamArenaEmbodiment';(HERE/'setup_manifest.json').write_text(json.dumps(manifest,indent=2))
    (HERE/'fastener_vertex_indices.json').write_text(json.dumps(anchors,indent=2))
    robots=[base.scene.articulations[x] for x in ['left_robot','right_robot']]
    bags=base.scene.deformable_objects
    # Match Inspect Robots' 0.5-second physical settling before episode reset.
    # The cord's rest length belongs to that reset scene, not the authored pose.
    frames=HERE/'frames';frames.mkdir(exist_ok=True)

    for robot in robots:
        robot.write_joint_effort_limit_to_sim_index(limits=8.,joint_ids=robot.find_joints(['joint7','joint8'],preserve_order=True)[0])
    q=q_ready; grip=[1.,1.];count=0; logs=[]
    orientations=[v.copy() for v in initial_rotations]
    def tensor(value):return value.torch if hasattr(value,'torch') else value
    def arr(x):
        if hasattr(x,'torch'):x=x.torch
        return x.detach().cpu().numpy()
    def state(label):
        result={'commanded_joints':[x.tolist() for x in q], 'joint_limits':[arr(r.data.joint_pos_limits)[0].tolist() for r in robots], 'joints':[arr(r.data.joint_pos)[0].tolist() for r in robots], 'step':count,'phase':label,'tcp':[tcp_world(x).tolist() for x in robots], 'grip_command':list(grip)}
        for key,obj in bags.items():
            p=arr(obj.data.nodal_pos_w)[0]
            result[key]={'low':p.min(0).tolist(),'high':p.max(0).tolist(),'mean':p.mean(0).tolist()}
        np.savez_compressed(HERE/('state_%04d.npz'%count),loaded_bag=arr(bags['loaded_bag'].data.nodal_pos_w))
        result['rubbish']=[arr(base.scene.rigid_objects['rubbish_%d'%i].data.root_pos_w)[0].tolist() for i in range(6)]
        result['fasteners']={key:{'pos':arr(base.scene.rigid_objects[key].data.root_pos_w)[0].tolist(),'quat':arr(base.scene.rigid_objects[key].data.root_quat_w)[0].tolist()} for key in ['cord_end_0','cord_end_1']}
        result['drawcord']=dict(cable.last)
        from removal_runtime import tape_names
        result['drawtape_positions']=[body_pos(n).tolist() for n in tape_names()]
        result['loaded_mouth_indices']=anchors['loaded_bag']
        result['rubbish_velocities']=[arr(base.scene.rigid_objects['rubbish_%d'%i].data.root_lin_vel_w)[0].tolist() for i in range(6)]
        result['hem_marker_positions']=[body_pos('hem_%02d'%j).tolist() for j in range(bead_count)]
        result['gripper_poses']=[link_poses(r)['gripper'].tolist() for r in robots]
        result['rubbish_quaternions']=[arr(base.scene.rigid_objects['rubbish_%d'%i].data.root_quat_w)[0].tolist() for i in range(6)]
        hem=arr(bags['loaded_bag'].data.nodal_pos_w)[0][anchors['loaded_bag']]
        result['mouth_diameter']=float(np.max(np.linalg.norm(hem[:,None,:]-hem[None,:,:],axis=2)))
        logs.append(result)
        if count%10==0 or label!='trajectory':
            (HERE/'trace.json').write_text(json.dumps(logs,indent=2));print('STATE',json.dumps(result),flush=True)
    def tick(steps=1):
        nonlocal count
        for _ in range(steps):
            action=torch.tensor([[*q[0],grip[0],*q[1],grip[1]]],device=base.device,dtype=torch.float32)
            result=inspect.step(SimpleNamespace(data=np.r_[q[0],grip[0],q[1],grip[1]]));count+=1
            if count%10==0:(HERE/'inspect_result.json').write_text(json.dumps({'step':count,'info':result.info,'terminated':result.terminated}))
            if count>4000:raise RuntimeError('Run limit exceeded')
            state('trajectory')
            if count%20==0:(HERE/'heartbeat.json').write_text(json.dumps({'step':count,'tcp':[tcp_world(r).tolist() for r in robots]}))
            if args.camera and count%4==0:
                im=arr(base.scene.sensors['overview_cam'].data.output['rgb'])[0,:,:,:3]
                Image.fromarray(im.astype('uint8')).save(frames/('%05d.png'%count))
    def move(targets,steps=50):
        origins=[tcp_world(x) for x in robots]
        from scipy.spatial.transform import Rotation,Slerp
        rotations=[Slerp([0,1],Rotation.from_quat([Rotation.from_matrix(link_poses(robots[k])["gripper"][:3,:3]).as_quat(),orientations[k]])) for k in range(2)]
        plan=[];seeds=[np.asarray(v).copy() for v in q]
        for step in range(1,steps+1):
            t=step/steps;t=t*t*t*(10+t*(-15+6*t))
            for k in range(2):
                target=origins[k]*(1-t)+np.array(targets[k])*t
                seeds[k],err,re=solve(target,rotations[k](t).as_quat(),q_init=seeds[k],base_pos=[LEFT_BASE_POS,RIGHT_BASE_POS][k],iters=80,tol=.0005)
                if err>.005 or re>.08:raise RuntimeError('Path rejected before movement: arm %d, %.6f m, %.6f rad'%(k,err,re))
            plan.append([v.copy() for v in seeds])
        for waypoint in plan:
            q[:]=waypoint;tick()
    def body_pos(name):return arr(base.scene.rigid_objects[name].data.root_pos_w)[0]
    def body_rot(name):
        from scipy.spatial.transform import Rotation
        return Rotation.from_quat(arr(base.scene.rigid_objects[name].data.root_quat_w)[0]).as_matrix()
    def nodes(name):return arr(bags[name].data.nodal_pos_w)[0]
    def current_targets():return [tcp_world(r).copy() for r in robots]
    def approach(targets,steps=60):
        # Solve the contact-free hover branch first; interpolating a half-turn
        # wrist rotation in Cartesian space can pass through an IK singularity.
        goals=[];start=[v.copy() for v in q]
        for k in range(2):
            qt,err,re=solve(targets[k],orientations[k],q_init=q[k],base_pos=[LEFT_BASE_POS,RIGHT_BASE_POS][k],iters=600)
            if err>.005 or re>.08:raise RuntimeError('Cord hover unreachable')
            goals.append(qt)
        for n in range(1,steps+1):
            t=n/steps;t=t*t*t*(10+t*(-15+6*t));q[:]=[a*(1-t)+b*t for a,b in zip(start,goals)];tick()
        tick(6)
        if any(np.linalg.norm(tcp_world(r)-t)>.02 for r,t in zip(robots,targets)):raise RuntimeError('Cord hover physically blocked')
    cable=inspect.task.module.TRACKER.runtime.cable
    def mouth_diameter():
        v=nodes('loaded_bag')[anchors['loaded_bag']]
        return float(np.max(np.linalg.norm(v[:,None,:]-v[None,:,:],axis=2)))
    def cinch_loaded(release=True):
        orientations[:]=[[1.,0,0,0],[1.,0,0,0]]
        direction=[np.array([0,0,-1.]),np.array([0,0,-1.])]
        # Put the thin cord toggle near the distal pads. The TCP sits 13 mm
        # behind their tips, so centring the TCP on a table-level toggle drives
        # the fingers into the support before they can close around it.
        offsets=[.012,.012]
        targets=[body_pos(n)-direction[j]*offsets[j] for j,n in enumerate(['cord_end_0','cord_end_1'])]
        grip[:]=[.55,.55]
        approach([t-direction[j]*.08 for j,t in enumerate(targets)],40);state('cord_hover')
        targets=[body_pos(n)-direction[j]*offsets[j] for j,n in enumerate(['cord_end_0','cord_end_1'])]
        move(targets,24)
        # Track the measured toggles during closure; a fixed target can miss a settling cord.
        for i in range(16):
            u=(i+1)/16;u=u*u*u*(10+u*(-15+6*u))
            grip[:]=[g*(1-u) for g in [.55,.55]]
            now=current_targets()
            desired=[body_pos(n)-direction[j]*offsets[j] for j,n in enumerate(['cord_end_0','cord_end_1'])]
            for d in desired:d[2]=max(d[2],.769)
            bounded=[t+np.clip(d-t,-.002,.002) for t,d in zip(now,desired)]
            move(bounded,1)
        tick(5);state('cord_ends_grasped')
        before=np.array([body_pos(n).copy() for n in ['cord_end_0','cord_end_1']])
        move([t+[0,0,.05] for t in current_targets()],20);state('cord_grasp_probe')
        after=np.array([body_pos(n).copy() for n in ['cord_end_0','cord_end_1']])
        if np.min(after[:,2]-before[:,2])<.025:raise RuntimeError('Cord or lock slipped during measured grasp probe')
        # Peel the folded cuff outward and above the rim before rotating the
        # wrists; rotating while under the brim can trap the tab between a
        # finger and the bin and strip it out of the grasp.
        peel=current_targets()
        peel[0]+=np.array([0,.02,.12]);peel[1]+=np.array([0,-.02,.12])
        move(peel,48);state('cuff_peeled_above_rim')
        for k,n in enumerate(['cord_end_0','cord_end_1']):
            if np.linalg.norm(body_pos(n)-tcp_world(robots[k]))>.03:raise RuntimeError('Grasp lost during cuff peel on arm %d'%k)
        orientations[:]=[(Rotation.from_euler('y',-60,degrees=True)*Rotation.from_quat(r)).as_quat().tolist() for r in orientations]
        held_targets=current_targets()
        held_targets[0]+=np.array([.03,0,.04]);held_targets[1]+=np.array([.03,0,.04])
        move(held_targets,40);state('cuff_raised')
        # The original ten collinear 20-mm pulls become one continuous sweep.
        # Acceleration and velocity are zero at both ends; no repeated pauses.
        for j,(delta,angle,steps) in enumerate([
            ([[.070,-.150,.200],[.070,.150,.200]],100.,112),
            ([[0,0,.105],[0,0,.105]],110.,70)]):
            orientations[:]=[(Rotation.from_euler('y',-angle,degrees=True)*Rotation.from_quat([1.,0,0,0])).as_quat().tolist() for _ in range(2)]
            held_targets=[t+np.asarray(d) for t,d in zip(held_targets,delta)]
            move(held_targets,steps)
            state('continuous_drawstring_pull_%d'%j)
            for k,n in enumerate(['cord_end_0','cord_end_1']):
                if np.linalg.norm(body_pos(n)-tcp_world(robots[k]))>.025:raise RuntimeError('Measured cord grasp lost during pull on arm %d'%k)

        state('vertical_pre_cinch')
        if release:raise RuntimeError('Use full mode for the gather-and-lift controller')
    def full_removal():
        cinch_loaded(release=False)
        def wrist(pitch,yaws=(0.,0.)):
            orientations[:]=[(Rotation.from_euler('z',yaw,degrees=True)*Rotation.from_euler('y',-pitch,degrees=True)*Rotation.from_quat([1.,0,0,0])).as_quat().tolist() for yaw in yaws]
        wrist(110)
        now=current_targets()
        move([now[0]+[0,-.02,.02],now[1]+[0,.02,.02]],30);state('converge_020')
        move([[.3226,.0458,1.3777],[.3226,-.0458,1.3777]],50);state('converged_lift')
        wrist(110,(-20.,20.))
        move(current_targets(),30);state('wrist_yaw_clearance')
        wrist(135,(-20.,20.))
        move([[.27,.06,1.49],[.27,-.06,1.49]],65);tick(10);state('high_lift_hold')
        wrist(145,(-20.,20.))
        move([[.24,.06,1.54],[.24,-.06,1.54]],40);tick(45);state('full_clearance_hold')
        result=inspect.task.module.TRACKER.result
        if not result.get('cinch_verified') or result.get('score',0)==0:
            raise RuntimeError('Physical episode did not preserve the closed load: '+str(result))
        if os.environ.get('BIN_MOTION_CONTINUE')!='1':
            from plan_table_transfer import plan
            command,report=plan(logs[-1])
            (HERE/'table_transfer_plan.json').write_text(json.dumps(command))
            (HERE/'table_transfer_preflight.json').write_text(json.dumps(report,indent=2))
            for op in command['operations']:
                orientations[:]=op['orientations'];move(op['targets'],op['steps'])
            state('two_arm_table_release')
            for n in range(1,9):
                u=n/8;u=u*u*u*(10+u*(-15+6*u));grip[:]=[u,u];tick()
            state('released_above_table');tick(100);state('table_landing_settled')
            if inspect.task.module.TRACKER.result.get('score')!=1.:
                raise RuntimeError('Table deposit not verified: '+str(inspect.task.module.TRACKER.result))
        # Development continuation keeps the actual simulated state alive while
        # a floor-transfer path is verified. It accepts only robot commands.
        if os.environ.get('BIN_MOTION_CONTINUE')=='1':
            import time
            while True:
                command=HERE/'command.json'
                if not command.exists():time.sleep(.1);continue
                request=json.loads(command.read_text());command.unlink()
                if request.get('quit'):break
                try:
                    for op in request.get('operations',[]):
                        if 'orientations' in op:orientations[:]=op['orientations']
                        if 'grip' in op:grip[:]=op['grip']
                        if 'targets' in op:move(op['targets'],op.get('steps',50))
                        if 'tick' in op:tick(op['tick'])
                    state(request['label'])
                    (HERE/'command_result.json').write_text(json.dumps({'label':request['label'],'step':count,'score':inspect.task.module.TRACKER.result}))
                except Exception as exc:
                    state(request['label']+'_failed');(HERE/'command_error.json').write_text(json.dumps({'label':request['label'],'failure':str(exc)}))
    (HERE/'task_parameters.json').write_text(json.dumps({'bin_center_xy':[.22,0.],'bin_top_z':.918,'control_hz':20.,'clear_hold_seconds':2.,'sample_interval_steps':1,'mode':args.mode,'require_table_deposit':True,'require_ordinary_closure':True}))
    state('initial')
    try:
        tick(20);state('settled')
        # Fail a numerically damaged reset before attempting manipulation.
        from realistic_meshes_v32 import dirty_mesh
        rv,rf,_=dirty_mesh();reference=trimesh.Trimesh(vertices=rv,faces=rf,process=False)
        edge=reference.edges_unique;rest=np.linalg.norm(reference.vertices[edge[:,1]]-reference.vertices[edge[:,0]],axis=1)
        current=nodes('loaded_bag')
        if np.max(np.linalg.norm(current[edge[:,1]]-current[edge[:,0]],axis=1)/rest)>1.5:raise RuntimeError('Unstable initial film geometry; trial invalid before manipulation')
        if args.camera:save_views(base,HERE)
        if args.mode=='setup':setup_result(HERE,count)
        if args.mode=='interactive':
            import time
            while True:
                command=HERE/'command.json'
                if not command.exists():time.sleep(.1);continue
                request=json.loads(command.read_text());command.unlink()
                if request.get('quit'):break
                try:
                    for op in request.get('operations',[]):
                        if op.get('routine')=='cinch':cinch_loaded();continue
                        if op.get('routine')=='full':full_removal();continue
                        if 'orientations' in op:orientations[:]=op['orientations']
                        if 'grip' in op:grip[:]=op['grip']
                        if 'targets' in op:move(op['targets'],op.get('steps',50))
                        elif 'delta' in op:move([t+d for t,d in zip(current_targets(),np.array(op['delta']))],op.get('steps',50))
                        if 'tick' in op:tick(op['tick'])
                    state(request['label'])
                except Exception as exc:
                    state(request['label']+'_failed');(HERE/'command_error.json').write_text(json.dumps({'label':request['label'],'failure':str(exc)}))
        elif args.mode=='cinch':cinch_loaded()
        elif args.mode=='full':full_removal()
        (HERE/'completed.json').write_text(json.dumps({'completed':True,'mode':args.mode,'full_task_success':False,'score':None,'reason':'Requires independent evaluation; completion alone does not establish success'}))
    except Exception as exc:
        state('sequence_failed');(HERE/'completed.json').write_text(json.dumps({'completed':False,'failure':str(exc),'score':None}));raise
    inspect.close()

try:main()
except Exception:
    (HERE/'trial_error.txt').write_text(traceback.format_exc());traceback.print_exc();raise
finally:
    if app is not None:app.close()
