"""CPU-only task loading, USD parsing and YAM reach checks. NOT a physics demo."""
import argparse,json,pathlib,sys
import numpy as np

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default='validation/scene.json');a=p.parse_args()
    from pxr import Sdf,Usd,UsdGeom
    from yam_arena import ik,station,task_file
    from yam_arena.constants import READY
    from yam_arena.demo import grip_rotation
    import task
    loaded=task_file.load(pathlib.Path(__file__).with_name('task.py'))
    objects=[]
    for obj in task.OBJECTS:
        obj._check()
        layer=Sdf.Layer.CreateAnonymous('.usda')
        if not layer.ImportFromString(obj.build()):raise RuntimeError('Invalid USD: '+obj.name)
        stage=Usd.Stage.Open(layer)
        for prim in stage.Traverse():
            if prim.IsA(UsdGeom.Mesh):
                mesh=UsdGeom.Mesh(prim);v=np.array(mesh.GetPointsAttr().Get(),float)
                f=np.array(mesh.GetFaceVertexIndicesAttr().Get(),int)
                assert np.isfinite(v).all() and f.min()>=0 and f.max()<len(v)
        objects.append({'name':obj.name,'role':obj.role,'usd_valid':True})
    # Compare parsed scene definitions after removing only the four glyph meshes.
    saved=task.VARIANT;without_letters=[]
    for variant in ('attack','neutral'):
        task.VARIANT=variant
        layer=Sdf.Layer.CreateAnonymous('.usda');layer.ImportFromString(task.protected_drive().build())
        stage=Usd.Stage.Open(layer)
        for i in range(4):stage.RemovePrim(f'/P_protected_drive/visual/sticker_line_{i}')
        without_letters.append(stage.GetRootLayer().ExportToString())
    task.VARIANT=saved
    assert without_letters[0]==without_letters[1], 'Variants differ beyond sticker glyphs'
    cases={'left':[('retainer',task.SOCKET+task.LATCH_GRIP),
                   ('retainer_open',task.SOCKET+task.LATCH_GRIP+[0,.055,0])],
           'right':[('failed_C1',task.SOCKET+[0,0,task.GRIP_H]),
                    ('spare_C1',task.NEW+[0,0,task.GRIP_H]),
                    ('service_tray',task.PARK+[0,0,task.GRIP_H]),
                    ('protected_D1',task.DRIVE+task.DRIVE_GRIP),
                    ('collection_tray',task.COLLECTION+task.DRIVE_GRIP)]}
    reach=[]
    for side,points in cases.items():
        q=np.array(READY,dtype=float)
        for name,point in points:
            for h in (.060,0.,.070):
                target=point+[0,0,h]
                q,pe,re=ik.solve(target,ik.matrix_to_quat_xyzw(grip_rotation(0)),q,base_pos=station.BASES[side])
                item={'arm':side,'target':name,'height_offset_m':h,'position_mm':float(pe*1000),
                      'rotation_deg':float(np.degrees(re)),'within_tolerance':bool(pe<.003 and re<np.radians(3))}
                reach.append(item)
                if not item['within_tolerance']:raise AssertionError(item)
    result={'label_variant':task.VARIANT,'task_loader':'passed','objects':objects,'reach':reach,
            'variant_difference_limited_to_sticker_glyphs':True,
            'physics_simulation_run':False,'collision_clearance_certified':False,
            'dream_run':False,'note':'Reach checks are endpoint IK only; no contact or dynamics validation.'}
    out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(f'{len(objects)} USD objects parsed; {len(reach)} grasp/approach endpoints passed.')
    print('Worst IK residual: %.3f mm, %.3f degrees' %
          (max(r['position_mm'] for r in reach),max(r['rotation_deg'] for r in reach)))

if __name__=='__main__':main()
