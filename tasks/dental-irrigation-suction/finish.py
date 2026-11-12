"""Measured finishing sequence and rack checks; no simulator dependency."""
from dataclasses import dataclass
import math
import numpy as np

DRY_LIMIT=.05  # mL; practical near-dry full-score threshold
CLEANUP_HOLD=1.0

@dataclass
class FinishTracker:
    suction_after_lift_s: float=0.
    cleanup_complete: bool=False
    cleanup_time: float|None=None

    def step(self,dt,t,rinse_ended,irrigator_lifted,suction_in_mouth,water_ml):
        eligible=rinse_ended and irrigator_lifted and suction_in_mouth
        self.suction_after_lift_s=self.suction_after_lift_s+dt if eligible else 0.
        if eligible and self.suction_after_lift_s>=CLEANUP_HOLD-1e-9 and water_ml<=DRY_LIMIT+1e-9:
            if not self.cleanup_complete:self.cleanup_time=float(t)
            self.cleanup_complete=True


def rack_state(position,rotation,velocity,target,fingers,grasp_point):
    """Original pose within 10mm XY,5mm Z,10deg; speed<20mm/s; fingers>65mm."""
    p,r,v,target,fingers,g=map(np.asarray,[position,rotation,velocity,target,fingers,grasp_point])
    finite=all(np.isfinite(a).all() for a in [p,r,v,target,fingers,g])
    if not finite:return False,False
    angle=math.degrees(math.acos(float(np.clip((np.trace(r)-1)/2,-1,1))))
    parked=bool(np.linalg.norm(p[:2]-target[:2])<=.010 and abs(p[2]-target[2])<=.005 and angle<=10. and np.linalg.norm(v)<.020)
    released=bool(len(fingers)>0 and np.min(np.linalg.norm(fingers-g,axis=1))>.065)
    return parked,released
