"""Conservative lumped water model for a dry dental-phantom benchmark.
Volumes are mL, time seconds, distances metres. Not CFD or clinical calibration.
"""
from dataclasses import dataclass, field
import math
import numpy as np

SITES=np.array([[.235,.025,.037],[.270,.025,.037],[.305,.025,.037]])
STARTS=(16.,24.,32.)
DURATION=5.
IRRIGATION_RATE=.4
SUCTION_RATE=.65
CAPACITY=.45
COVERAGE_DWELL=.15

def sweep_offsets(phase):
    """Centre, inner circle, outer circle and return, during one five-second rinse.
    Suction stays on the open side and tracks the outer pass laterally.
    """
    a=-math.pi/2
    if phase<.25:r=0.
    elif phase<.5:r=.003*(phase-.25)/.25
    elif phase<1.5:r=.003;a+=2*math.pi*(phase-.5)
    elif phase<1.8:r=.003+.0045*(phase-1.5)/.3
    elif phase<4.6:r=.0075;a+=2*math.pi*(phase-1.8)/2.8
    else:r=.0075*max(0.,1-(phase-4.6)/.4)
    return np.array([r*math.cos(a),r*math.sin(a),.018]), np.array([r*math.cos(a),-.017,.010])


@dataclass
class WaterModel:
    t: float=0.
    supplied: float=0.
    delivered: list=field(default_factory=lambda:[0.,0.,0.])
    coverage_s: list=field(default_factory=lambda:[[0.]*9 for _ in range(3)])
    captured: list=field(default_factory=lambda:[0.,0.,0.])
    pool: list=field(default_factory=lambda:[0.,0.,0.])
    lost: float=0.
    peak: float=0.
    obstruction_s: float=0.
    failed: bool=False
    active: int=-1
    aimed: bool=False

    def step(self,dt,irrigator,suction,irrigator_axis=(0,0,-1),suction_axis=(0,0,-1),safe=True):
        points=np.asarray([irrigator,suction,irrigator_axis,suction_axis],float)
        if not np.isfinite(points).all() or not math.isfinite(dt) or dt<=0:
            self.failed=True;return
        ir,su,ia,sa=points
        self.failed |= not safe
        # Integrate schedule overlap exactly, so changing step size cannot change supply.
        self.active=-1;self.aimed=False
        for i,start in enumerate(STARTS):
            on=max(0.,min(self.t+dt,start+DURATION)-max(self.t,start))
            if on<=1e-10:continue
            self.active=i;v=on*IRRIGATION_RATE;self.supplied+=v
            height=ir[2]-SITES[i,2]
            hit=ir[:2]+ia[:2]*height/max(1e-9,-ia[2])
            aimed=ia[2]<-.94 and .008<=height<=.030 and np.linalg.norm(hit-SITES[i,:2])<=.010
            self.aimed=bool(aimed)
            if aimed:
                self.delivered[i]+=v;self.pool[i]+=v
                delta=hit-SITES[i,:2];radius=float(np.linalg.norm(delta))
                zone=0 if radius<=.0025 else 1+(int((math.atan2(delta[1],delta[0])%(2*math.pi))/(math.pi/4))%8) if .0045<=radius<=.0095 else None
                if zone is not None:self.coverage_s[i][zone]+=on
            else:self.lost+=v
            # A transparent, benchmark-specific working-area exclusion zone.
            obstructed=np.linalg.norm(su[:2]-SITES[i,:2])<.009 and su[2]<SITES[i,2]+.028
            self.obstruction_s+=on*bool(obstructed)
        self.failed |= self.obstruction_s>.25
        # Allocate one finite suction capacity across all reachable pools.
        weights=[]
        for i,p in enumerate(SITES):
            d=float(np.linalg.norm(su-p));h=su[2]-p[2]
            orientation=max(0.,min(1.,(-sa[2]-.8)/.2))
            weights.append(math.exp(-((d-.012)/.014)**2)*orientation if d<.025 and .003<=h<=.020 else 0.)
        remaining=SUCTION_RATE*dt
        for i in sorted(range(3),key=lambda i:weights[i],reverse=True):
            take=min(self.pool[i],remaining*weights[i]);self.pool[i]-=take;self.captured[i]+=take;remaining-=take
        for i in range(3):
            self.peak=max(self.peak,self.pool[i])
            overflow=max(0.,self.pool[i]-CAPACITY);self.pool[i]-=overflow;self.lost+=overflow
        self.t+=dt

    def covered(self):
        return [sum(t>=COVERAGE_DWELL-1e-9 for t in row) for row in self.coverage_s]

    def score(self,clear=False,held=True):
        if self.failed:return 0.
        completed=sum(self.t>=s+DURATION and self.delivered[i]>=1.8 and self.captured[i]>=1.8 and self.pool[i]<=.10 and self.covered()[i]==9 for i,s in enumerate(STARTS))
        if completed==3 and self.lost<=.30 and self.peak<=CAPACITY and clear and held:return 1.
        return .25*completed

    def balance_error(self):return self.supplied-sum(self.captured)-sum(self.pool)-self.lost
