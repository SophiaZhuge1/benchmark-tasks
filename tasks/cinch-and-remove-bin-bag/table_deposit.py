"""Read-only outcome checks for a released bag settled on the tabletop.

This extends the existing cinch/removal score without changing its film-strain,
closure, clearance, retained-content, or evidence-continuity thresholds.
"""
from collections import deque
import numpy as np
from evaluate_removal import RemovalJudge

TABLE_Z = .7475
TABLE_LO = np.array([-.19, -.65])
TABLE_HI = np.array([.91, .65])

class TableDepositJudge(RemovalJudge):
    def __init__(self, parameters):
        # Preserve the original floor-level escape guard. A harmless lowering
        # followed by recovery is allowed; tabletop support is a final outcome.
        parameters = dict(parameters, minimum_content_z=-.0125 - .010)
        super().__init__(parameters)
        self.table_tail = deque()
        self.table_metrics = {}

    def update(self, s, vertices):
        base = super().update(s, vertices)
        if self.failure is not None:
            return base
        v = np.asarray(vertices, float)
        endpoints = np.asarray(s.get('cord_end_positions', []), float)
        if endpoints.shape != (2,3) and 'fasteners' in s:
            endpoints = np.asarray([s['fasteners'][f'cord_end_{i}']['pos'] for i in range(2)])
        tcp = np.asarray(s.get('tcp', []), float)
        velocities = np.asarray(s.get('rubbish_velocities', []), float)
        if endpoints.shape == (2,3) and tcp.shape == (2,3):
            grasp_points = np.concatenate([v,endpoints])
            separation = float(np.linalg.norm(tcp[:,None,:]-grasp_points[None,:,:],axis=2).min())
        else:
            separation = 0.
        speed = float(np.linalg.norm(velocities,axis=1).max()) if velocities.shape==(6,3) else float('inf')
        bottom = float(v[:,2].min())
        top = float(v[:,2].max())
        centre = v[:,:2].mean(0)
        # Any tabletop landing position is acceptable. The whole load must
        # stay 20 mm inside the table edge and clear the bin by 20 mm.
        from evaluate_removal import clear_of_bin
        corners = self.content_corners
        points = np.concatenate([v, corners])
        lo=points[:,:2].min(0);hi=points[:,:2].max(0)
        on_table=bool(np.all(lo>=TABLE_LO+.020) and np.all(hi<=TABLE_HI-.020))
        beside = clear_of_bin(v,corners,self.top,self.centre)
        # Height above the support is not a task condition: retained contents,
        # support, rest and release determine completion, independent of folds.
        # The 2.5 mm work mat lies on the table and is inside this tolerance.
        settled = bool(on_table and beside and abs(bottom-TABLE_Z)<=.025
                       and separation>=.060 and s['mouth_diameter']<=.060)
        self.table_metrics = {'table_settled':settled,'whole_load_on_table':on_table,'bag_bottom_z_m':bottom,
            'bag_centre_xy_m':centre.tolist(),'maximum_contents_speed_m_s':speed,
            'minimum_gripper_distance_m':separation}
        # Rest is an observable geometric outcome. Internal object velocities
        # are diagnostic only; harmless settling inside opaque film is allowed.
        bounds = np.concatenate([v.min(0),v.max(0)])
        self.table_tail.append((int(s['step']),settled,bounds))
        while len(self.table_tail)>1 and self.table_tail[1][0]<=self.previous-40:
            self.table_tail.popleft()
        return self.result()

    def result(self):
        base = super().result()
        if self.failure is not None or base.get('score',0)<1.:
            return base
        tail = getattr(self,'table_tail',[])
        motion = float(np.ptp(np.asarray([x[2] for x in tail]),axis=0).max()) if tail else float('inf')
        deposited = len(tail)>=3 and tail[0][0]<=self.previous-40 and all(x[1] for x in tail) and motion<=.010
        return dict(base,score=1. if deposited else .7,full_task_success=bool(deposited),
            table_deposit_verified=bool(deposited),table_hold_seconds=2. if deposited else 0.,
            final_two_second_bag_bounds_motion_m=motion,
            **getattr(self,'table_metrics',{}),
            scope='Cinch, remove, and release the loaded bag onto the table beside the bin.')
