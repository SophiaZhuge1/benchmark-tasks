"""Geometry-only score for cinching and lifting a loaded drawstring bag.

The grippers may keep holding the removed bag. No new liner, ring, set-down,
phase label or controller completion flag is required for a geometric score.
"""
import argparse, json
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull,QhullError
from scipy.spatial.transform import Rotation

def contents_retained(s, vertices):
    centres=np.asarray(s['rubbish'],float)
    quats=np.asarray(s['rubbish_quaternions'],float)
    if centres.shape!=(6,3) or quats.shape!=(6,4):return False,None
    offsets=np.array([[x*.024,y*.04,z*.0175] for x in [-1,1] for y in [-1,1] for z in [-1,1]])
    corners=np.concatenate([c+Rotation.from_quat(q).apply(offsets) for c,q in zip(centres,quats)])
    from containment import closed_triangles, contains_points
    from realistic_meshes_v32 import dirty_mesh
    _,faces,mouth_ids=dirty_mesh()
    triangles=closed_triangles(vertices,faces,mouth_ids)
    # Corners, face centres and the centre of each waste block are checked.
    # Face/centre samples also catch a rigid block bridging an exterior fold.
    face_offsets=np.array([[.024,0,0],[-.024,0,0],[0,.04,0],[0,-.04,0],[0,0,.0175],[0,0,-.0175],[0,0,0]])
    other=np.concatenate([c+Rotation.from_quat(q).apply(face_offsets) for c,q in zip(centres,quats)])
    points=np.concatenate([corners,other])
    return bool(np.all(contains_points(points,triangles,tolerance=.005))),corners

def clear_of_bin(vertices, corners, top, centre, radius=.106):
    """Entire load above the rim or entirely beside the outer bin envelope.

    A final set-down beside the bin is a valid removal too. Use a conservative
    bounding box around the segmented bin, with the same 20 mm clearance.
    """
    points=np.concatenate([vertices,corners])
    if points[:,2].min()>=top+.020:return True
    lo=points[:,:2].min(0);hi=points[:,:2].max(0)
    return bool(np.any(lo>=centre+radius+.020) or np.any(hi<=centre-radius-.020))

class RemovalJudge:
    """Incremental read-only geometry checks; identical rules at each sample."""
    def __init__(self,parameters):
        from collections import deque
        from realistic_meshes_v32 import dirty_mesh
        import trimesh
        self.top=float(parameters['bin_top_z']);self.centre=np.asarray(parameters['bin_center_xy'])
        self.minimum_content_z=float(parameters.get('minimum_content_z',.735))
        self.maximum_gap=int(parameters.get('sample_interval_steps',10))
        vv,ff,_=dirty_mesh();mesh=trimesh.Trimesh(vertices=vv,faces=ff,process=False)
        self.shape=mesh.vertices.shape;self.edges=mesh.edges_unique
        self.rest=np.linalg.norm(mesh.vertices[self.edges[:,1]]-mesh.vertices[self.edges[:,0]],axis=1)
        self.mouth_ids=np.unique(mesh.edges_unique[np.bincount(mesh.edges_unique_inverse)==1])
        self.failure=None;self.count=0;self.previous=-1;self.first_cinch=None;self.max_strain=1.;self.tail=deque();self.final=None
    def fail(self,why,**extra):
        self.failure={'score':0.,'full_task_success':False,'reason':why,**extra}
        return self.failure
    def update(self,s,vertices):
        if self.failure is not None:return self.failure
        try:
            step=int(s['step']);v=np.asarray(vertices,float)
            if step>4000:return self.fail('Run limit exceeded')
            if self.maximum_gap<1 or step<self.previous or (self.previous>=0 and step-self.previous>self.maximum_gap):return self.fail('Incomplete or unordered motion evidence')
            if v.shape!=self.shape or not np.isfinite(v).all():return self.fail('Invalid bag mesh evidence')
            if self.count==0:
                if step!=0:return self.fail('Missing initial state')
                if s['mouth_diameter']<.10:return self.fail('Bag did not start open')
                if np.linalg.norm(v[:,:2].mean(0)-self.centre)>.03 or v[:,2].min()>self.top-.10:return self.fail('Bag did not start inside bin')
                if not contents_retained(s,v)[0]:return self.fail('Initial six waste blocks not retained')
            strain=float(np.max(np.linalg.norm(v[self.edges[:,1]]-v[self.edges[:,0]],axis=1)/self.rest));self.max_strain=max(self.max_strain,strain)
            if strain>1.5:return self.fail('Numerically invalid film deformation; rerun required',trial_valid=False,failure_step=step,max_recorded_edge_stretch_ratio=self.max_strain)
            retained,corners=contents_retained(s,v)
            self.content_corners=corners
            if not retained or corners[:,2].min()<self.minimum_content_z:return self.fail('Waste lost from bag')
            neck=v[self.mouth_ids];mouth=float(np.max(np.linalg.norm(neck[:,None,:]-neck[None,:,:],axis=2)))
            if abs(mouth-float(s['mouth_diameter']))>.001:return self.fail('Mouth measurement inconsistent with recorded mesh')
            if not np.isfinite(mouth):return self.fail('Invalid mouth measurement')
            clear=clear_of_bin(v,corners,self.top,self.centre)
            if mouth<=.050 and self.first_cinch is None:self.first_cinch=step
            self.tail.append((step,clear and mouth<=.060))
            # Preserve the last sample at/before the two-second hold boundary.
            while len(self.tail)>1 and self.tail[1][0]<=step-40:self.tail.popleft()
            self.previous=step;self.final=s;self.count+=1
            return self.result()
        except (ValueError,KeyError,TypeError,IndexError,QhullError) as exc:return self.fail('Invalid evidence: '+str(exc))
    def result(self):
        if self.failure is not None:return self.failure
        if self.count<2:return {'score':0.,'full_task_success':False,'reason':'Missing initial state'}
        if self.first_cinch is None:return {'score':0.,'full_task_success':False,'reason':'Bag was not cinched below 50 mm'}
        held=len(self.tail)>=3 and self.tail[0][0]<=self.previous-40 and all(g for _,g in self.tail)
        score=1. if held else (.4 if self.final['mouth_diameter']<=.060 else 0.)
        return {'score':score,'full_task_success':score==1.,'cinch_verified':True,'clear_hold_seconds':2. if held else 0.,'final_mouth_diameter_m':self.final['mouth_diameter'],'max_recorded_edge_stretch_ratio':self.max_strain,'steps':self.previous,'scope':'Loaded-bag cinch and removal only. Held clearance and harmless recovery are permitted. Film and sliding cord remain uncalibrated approximations.'}

def evaluate(trace,snapshots,parameters):
    try:
        if parameters.get('require_ordinary_closure',False):
            from ordinary_closure import OrdinaryLinerJudge
            judge=OrdinaryLinerJudge(parameters)
        elif parameters.get('require_table_deposit',False):
            from table_deposit import TableDepositJudge
            judge=TableDepositJudge(parameters)
        else:
            judge=RemovalJudge(parameters)
        for s in trace:
            judge.update(s,snapshots[s['step']])
            if judge.failure is not None:break
        return judge.result()
    except (ValueError,KeyError,TypeError,IndexError,QhullError) as exc:return {'score':0.,'full_task_success':False,'reason':'Invalid evidence: '+str(exc)}

def main():
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);a=p.parse_args();root=a.run
    trace=json.loads((root/'trace.json').read_text())
    states={s['step']:np.load(root/('state_%04d.npz'%s['step']))['loaded_bag'][0] for s in trace}
    result=evaluate(trace,states,json.loads((root/'task_parameters.json').read_text()))
    result['execution_error']=any((root/n).exists() for n in ['error.txt','trial_error.txt'])
    # Preserve the geometric score. The launcher separately rejects an
    # exception as successful demonstration evidence, even if the final
    # physical state was complete before a later recording/runtime error.
    (root/'verified_result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
