"""Shared physical assets for native and Inspect Robots drawstring removal.

Import and build only after Isaac starts. Object transforms are reset geometry.
"""

def build_assets():
    import numpy as np
    import trimesh
    import isaaclab.sim as sim
    from isaaclab.sim.utils import clone
    from isaaclab.sim.spawners.meshes.meshes import _spawn_mesh_geom_from_mesh
    from isaaclab_physx.sim.schemas import PhysxCollisionCfg, PhysxDeformableBodyPropertiesCfg, PhysxRigidBodyPropertiesCfg, PhysxCollisionPropertiesCfg
    from isaaclab_physx.sim.spawners.materials import PhysxSurfaceDeformableBodyMaterialCfg
    from isaaclab_arena.assets.deformable_object import DeformableObject
    from isaaclab_arena.assets.object import Object
    from isaaclab_arena.assets.object_type import ObjectType
    from isaaclab_arena.utils.pose import Pose
    def _box(name,size,pos,color,rot_xyzw=(0.,0.,0.,1.)):
        return Object(name=name,object_type=ObjectType.BASE,spawner_cfg=sim.CuboidCfg(size=tuple(size),collision_props=PhysxCollisionPropertiesCfg(contact_offset=.0005,rest_offset=0.),visual_material=sim.PreviewSurfaceCfg(diffuse_color=color,roughness=.7)),initial_pose=Pose(position_xyz=tuple(pos),rotation_xyzw=tuple(rot_xyzw)))


    from standard_liner import (BAG_HEIGHT, FILM_THICKNESS, BIN_INNER_RADIUS, TAPE_LINK_COUNT,
        TAPE_WIDTH, TAPE_COLLISION_THICKNESS, TAPE_MASS, HEM_MASS, tape_links, hem_positions, bight_indices)
    from realistic_meshes_v32 import dirty_mesh
    dv,df,dirty_mouth=dirty_mesh()
    loaded_mesh=trimesh.Trimesh(vertices=dv,faces=df,process=False)
    models={'loaded_bag':loaded_mesh}
    raw={k:np.asarray(v.vertices).copy() for k,v in models.items()}
    centroids={k:np.asarray(v.vertices).mean(0) for k,v in models.items()}
    for k,v in models.items():v.apply_translation(-centroids[k]);v.fix_normals()
    bead_count=20
    bead_positions=hem_positions()
    tape_pos,tape_length,tape_rotation=tape_links()
    bights=bight_indices()
    tape_names=[('cord_end_'+str(bights.index(j))) if j in bights else ('tape_%03d'%j) for j in range(TAPE_LINK_COUNT)]
    anchors={}
    from pxr import UsdGeom,UsdPhysics,Gf,Vt
    import omni.usd
    @clone
    def spawn_bag(prim_path,cfg,translation=None,orientation=None,**kwargs):
        name=prim_path.rsplit('/',1)[-1];model=models[name]
        root=_spawn_mesh_geom_from_mesh(prim_path,cfg,model,translation,orientation)
        stage=omni.usd.get_context().get_stage();v=np.asarray(model.vertices)+centroids[name]
        hem=np.where(np.abs(v[:,2]-BAG_HEIGHT)<1e-5)[0]
        theta=np.arctan2(v[hem,1],v[hem,0])%(2*np.pi)
        assignments=np.round(theta*bead_count/(2*np.pi)).astype(int)%bead_count
        for j in range(bead_count):
            # A 3 mm seam marker must not rigidly constrain an entire 35 mm
            # arc of film. Attach its nearest mouth vertex; the intervening
            # film remains free to gather and fold under cord tension.
            candidates=hem[assignments==j]
            distances=np.linalg.norm(v[candidates,:2]-bead_positions[j,:2]+np.array([.22,0.]),axis=1)
            ids=candidates[np.argsort(distances)[:1]]
            fast_path=prim_path.rsplit('/',1)[0]+'/hem_%02d'%j
            attach=stage.DefinePrim(prim_path+'/hem_seam_%02d'%j,'OmniPhysicsVtxXformAttachment')
            attach.GetRelationship('omniphysics:src0').SetTargets([prim_path]);attach.GetRelationship('omniphysics:src1').SetTargets([fast_path])
            attach.GetAttribute('omniphysics:vtxIndicesSrc0').Set(ids.tolist())
            local=v[ids]+np.array(translation)-centroids[name]-bead_positions[j]
            attach.GetAttribute('omniphysics:localPositionsSrc1').Set(Vt.Vec3fArray.FromNumpy(local.astype(np.float32)))
            UsdPhysics.FilteredPairsAPI.Apply(root).CreateFilteredPairsRel().AddTarget(fast_path)
        anchors[name]=hem.tolist()
        return root
    def bag(name,pos,color):
        cfg=sim.MeshRectangleCfg(size=(.172,.172),edge_refinement=1.,func=spawn_bag,
            deformable_props=PhysxDeformableBodyPropertiesCfg(self_collision=True,solver_position_iteration_count=64,linear_damping=.5,sleep_threshold=0.,settling_threshold=0.,settling_damping=0.),
            collision_props=[PhysxCollisionCfg(rest_offset=.00005,contact_offset=.0005)],
            physics_material=PhysxSurfaceDeformableBodyMaterialCfg(density=900.,surface_thickness=FILM_THICKNESS,
                youngs_modulus=2.5e7,poissons_ratio=.3,surface_bend_stiffness=2.5e7/(12.*(1.-.3**2)),
                elasticity_damping=.05,bend_damping=.05,static_friction=.3,dynamic_friction=.25),
            visual_material=sim.PreviewSurfaceCfg(diffuse_color=color,roughness=.65))
        return DeformableObject(name=name,spawner_cfg=cfg,initial_pose=Pose(position_xyz=tuple(float(v) for v in np.array(pos)+centroids[name])))

    from yam_arena import station
    from station_setup import rig as standard_rig, scene_assets as station_assets, setup_manifest, save_views, setup_result
    assets=station_assets()
    centre=np.array([.22,0.,.768])
    # Separate static wall colliders preserve the hollow interior.
    for j in range(32):
        a=2*np.pi*j/32; wall_h=.15
        pos=centre+np.array([(BIN_INNER_RADIUS+.006)*np.cos(a),(BIN_INNER_RADIUS+.006)*np.sin(a),wall_h/2])
        assets.append(_box('bin_wall_%02d'%j,(.012,.022,wall_h),pos,(.45,.5,.53),rot_xyzw=(0,0,np.sin(a/2),np.cos(a/2))))
    assets.append(_box('bin_floor',(.19,.19,.012),(.22,0,.756),(.35,.4,.43)))
    assets.append(bag('loaded_bag',centre,(.90,.90,.88)))
    def marker(name,pos,size,mass,color):
        return Object(name=name,object_type=ObjectType.RIGID,spawner_cfg=sim.CuboidCfg(size=size,
            rigid_props=PhysxRigidBodyPropertiesCfg(sleep_threshold=0.),collision_props=PhysxCollisionPropertiesCfg(contact_offset=.0005,rest_offset=0.),
            mass_props=sim.MassPropertiesCfg(mass=mass),physics_material=sim.RigidBodyMaterialCfg(static_friction=1.,dynamic_friction=.8),
            visual_material=sim.PreviewSurfaceCfg(diffuse_color=color)),initial_pose=Pose(position_xyz=tuple(map(float,pos))))
    for j,pos in enumerate(bead_positions):assets.append(marker('hem_%02d'%j,pos,(.001,.001,.001),HEM_MASS,(.90,.90,.88)))
    spawn_cuboid=sim.CuboidCfg(size=(1.,1.,1.)).func
    @clone
    def spawn_tape(prim_path,cfg,translation=None,orientation=None,**kwargs):
        root=spawn_cuboid(prim_path,cfg,translation,orientation,**kwargs)
        stage=omni.usd.get_context().get_stage()
        parent=prim_path.rsplit('/',1)[0]
        name=prim_path.rsplit('/',1)[-1];j=tape_names.index(name);k=(j+1)%TAPE_LINK_COUNT
        joint=UsdPhysics.SphericalJoint.Define(stage,parent+'/tape_joints/joint_%03d'%j)
        joint.CreateBody0Rel().SetTargets([prim_path]);joint.CreateBody1Rel().SetTargets([parent+'/'+tape_names[k]])
        joint.CreateLocalPos0Attr().Set(Gf.Vec3f(float(tape_length[j]/2),0.,0.))
        joint.CreateLocalPos1Attr().Set(Gf.Vec3f(float(-tape_length[k]/2),0.,0.))
        joint.CreateExcludeFromArticulationAttr().Set(True)
        joint.CreateCollisionEnabledAttr().Set(False)
        pairs=UsdPhysics.FilteredPairsAPI.Apply(root).CreateFilteredPairsRel()
        for offset in (-2,-1,1,2):pairs.AddTarget(parent+'/'+tape_names[(j+offset)%TAPE_LINK_COUNT])
        return root
    for j,pos in enumerate(tape_pos):
        cfg=sim.CuboidCfg(size=(float(tape_length[j]*.98),TAPE_WIDTH,TAPE_COLLISION_THICKNESS),func=spawn_tape,
            rigid_props=PhysxRigidBodyPropertiesCfg(sleep_threshold=0.,solver_position_iteration_count=32,solver_velocity_iteration_count=8),
            collision_props=PhysxCollisionPropertiesCfg(contact_offset=.0002,rest_offset=0.),
            mass_props=sim.MassPropertiesCfg(mass=TAPE_MASS/TAPE_LINK_COUNT),
            physics_material=sim.RigidBodyMaterialCfg(static_friction=.45,dynamic_friction=.35),
            visual_material=sim.PreviewSurfaceCfg(diffuse_color=(.9,.12,.12),roughness=.6))
        assets.append(Object(name=tape_names[j],object_type=ObjectType.RIGID,spawner_cfg=cfg,
            initial_pose=Pose(position_xyz=tuple(map(float,pos)),rotation_xyzw=tuple(map(float,tape_rotation[j])))))
    for i in range(6):
        assets.append(Object(name='rubbish_%d'%i,object_type=ObjectType.RIGID,
            spawner_cfg=sim.CuboidCfg(size=(.048,.080,.035),rigid_props=PhysxRigidBodyPropertiesCfg(sleep_threshold=0.),
                collision_props=PhysxCollisionPropertiesCfg(contact_offset=.001,rest_offset=0.),
                mass_props=sim.MassPropertiesCfg(mass=.025),
                physics_material=sim.RigidBodyMaterialCfg(static_friction=.8,dynamic_friction=.7),
                visual_material=sim.PreviewSurfaceCfg(diffuse_color=[(.6,.35,.16),(.8,.8,.5),(.2,.65,.3)][i%3])),
            initial_pose=Pose(position_xyz=(.22+(.025 if i%2 else -.025),0.,.786+.036*(i//2)))))
    return assets, anchors, bead_count
