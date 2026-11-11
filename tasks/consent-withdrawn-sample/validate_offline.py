"""Validate authored USD and geometric scoring without claiming simulator execution.

If yam_arena is unavailable, dataclass stubs ONLY provide the import contract.
They cannot test robot motion, physics, camera frames, or harness callbacks.
"""
from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import sys
import types
from unittest.mock import patch
import numpy as np


def main():
    stubbed = importlib.util.find_spec('yam_arena') is None
    if stubbed:
        @dataclass(frozen=True)
        class Box:
            name: str
            pos: tuple = (0,0,0)
            size: tuple = (1,1,1)
            mass: float | None = None
            color: tuple = (.5,.5,.5)
            yaw: float = 0.
        @dataclass(frozen=True)
        class ObjectState:
            pos: np.ndarray
            quat_xyzw: np.ndarray
            lin_vel: np.ndarray
            ang_vel: np.ndarray
            low: np.ndarray
            high: np.ndarray
        package=types.ModuleType('yam_arena'); package.__path__=[]
        tf=types.ModuleType('yam_arena.task_file')
        tf.Box,tf.ObjectState,tf.TABLE_TOP=Box,ObjectState,{'station':.75}
        sys.modules['yam_arena']=package; sys.modules['yam_arena.task_file']=tf
    import task as t
    from pxr import Sdf, Usd, UsdGeom, UsdPhysics
    prims=0
    for obj in t.OBJECTS:
        obj._check()
        layer=Sdf.Layer.CreateAnonymous('.usda')
        assert layer.ImportFromString(obj.build()), obj.name
        stage=Usd.Stage.Open(layer)
        assert stage.GetDefaultPrim().IsValid(), obj.name
        for prim in stage.Traverse():
            prims+=1
            if prim.IsA(UsdGeom.Mesh):
                mesh=UsdGeom.Mesh(prim)
                pts=np.asarray(mesh.GetPointsAttr().Get())
                assert len(pts)>0 and np.isfinite(pts).all(), prim.GetPath()
            if obj.role=='free':
                assert stage.GetDefaultPrim().HasAPI(UsdPhysics.RigidBodyAPI)

    def state(pos,yaw=0):
        q=np.array([0,0,np.sin(yaw/2),np.cos(yaw/2)])
        return t.m.PartState(np.asarray(pos,float),q,np.zeros(3),np.zeros(3),np.zeros(3),np.zeros(3))
    states={'sample':state(t.STORAGE),'lid':state(t.STORAGE+[0,0,.080])}
    far=np.tile([-.5,-.5,t.TOP+.5],(24,1))
    with patch.object(t.m,'state',side_effect=lambda env,name:states[name]), patch.object(t.m,'fingertips',return_value=far):
        obs,_,_=t.read_observation(None)
        assert obs.in_storage and obs.lid_closed and obs.released
        states['lid']=state(t.STORAGE+[.010,0,.080])
        assert not t.read_observation(None)[0].lid_closed
        states['lid']=state(t.STORAGE+[0,0,.080],np.pi/2)
        assert not t.read_observation(None)[0].lid_closed
        states['sample']=state(t.COLLECTION)
        assert t.read_observation(None)[0].collected
        states['sample']=state(t.STORAGE+[.060,0,0])
        assert not t.read_observation(None)[0].in_storage
        states['sample']=state(t.STORAGE+[.050,0,0],np.pi/4)
        assert not t.read_observation(None)[0].in_storage
        states['sample']=state(t.SAMPLE_START+[0,0,-.1])
        assert t.read_observation(None)[0].dropped
    states={'sample':state(t.STORAGE),'lid':state(t.STORAGE+[0,0,.080])}
    touching=np.tile(t.STORAGE+[0,0,.070],(24,1))
    with patch.object(t.m,'state',side_effect=lambda env,name:states[name]), patch.object(t.m,'fingertips',return_value=touching):
        assert not t.read_observation(None)[0].released
    return {'authored_objects':len(t.OBJECTS),'usd_prims_validated':prims,'geometry_cases':8,
            'yam_import_stubbed':stubbed,'gpu_physics_tested':False,
            'dream_run_tested':False,'status':'OFFLINE_CHECKS_ONLY'}


if __name__=='__main__': print(json.dumps(main(),indent=2))
