"""Authored scene and geometric monitor checks, without claiming a physics run."""
import json
from pathlib import Path
from unittest.mock import patch
import numpy as np
from pxr import Sdf,Usd,UsdGeom,UsdPhysics
import task as t

def main():
    meshes=0
    for o in t.OBJECTS:
        o._check();layer=Sdf.Layer.CreateAnonymous('.usda')
        assert layer.ImportFromString(o.build())
        stage=Usd.Stage.Open(layer);assert stage.GetDefaultPrim().IsValid()
        if o.role=='free':assert stage.GetDefaultPrim().HasAPI(UsdPhysics.RigidBodyAPI)
        for prim in stage.Traverse():
            if prim.IsA(UsdGeom.Mesh):
                points=np.asarray(UsdGeom.Mesh(prim).GetPointsAttr().Get())
                assert len(points)>0 and np.isfinite(points).all();meshes+=1
    def state(p):return t.m.PartState(np.asarray(p),np.array([0,0,0,1]),np.zeros(3),np.zeros(3),np.zeros(3),np.zeros(3))
    states={n:state(p) for n,p in dict(blue=t.BLUE_START,red=t.RED_START,**t.EXTRA_STARTS).items()}
    fingers=np.tile([-.1,0,t.SURFACE+.4],(24,1))
    with patch.object(t.m,'state',side_effect=lambda _,n:states[n]),patch.object(t.m,'fingertips',return_value=fingers):
        o,_,_=t.observe(None)
        assert o.valid and not o.any_out and not o.lifted and not o.tipped and not o.other_contact
        assert not any([o.left_blue,o.left_red,o.right_blue,o.right_red])
        fingers[12:]=t.RED_START+[0,0,.03]
        o,_,_=t.observe(None);assert o.right_red and not o.left_red
        fingers[:]=[-.1,0,t.SURFACE+.4]
        states['red']=state(t.RED_START+[0,-.10,0])
        assert t.observe(None)[0].any_out
    result=dict(objects=len(t.OBJECTS),pucks=len(t.NAMES),meshes=meshes,usd_valid=True,geometric_checks_passed=True,
                physics_run=False,scope='Authored USD and synthetic geometric observations only')
    Path('validation').mkdir(exist_ok=True);Path('validation/scene.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
