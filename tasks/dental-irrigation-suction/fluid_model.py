"""Conservative crown-runoff and mouth-water model for an inert dental phantom.
Volumes are mL, time seconds, distances metres. Not CFD or clinical calibration.
"""
from dataclasses import dataclass, field
import math
import numpy as np
from finish import DRY_LIMIT

SITES=np.array([[.235,.025,.037],[.270,.025,.037],[.305,.025,.037]])
STARTS=(16.,24.,32.)
DURATION=5.
IRRIGATION_RATE=.4
SUCTION_RATE=.65
CAPACITY=1.0  # per mouth-floor cell; overflow is external loss
MOUTH_PEAK_LIMIT=1.0  # total crown + floor water, not per tooth
MOUTH_FINAL_LIMIT=.50
MOUTH_FLOOR=.031
MOUTH_CENTRES=SITES+np.array([0.,-.025,MOUTH_FLOOR-.037])
MOUTH_AREA=.028*.018  # square metres per floor cell
DRAIN_TIME=.20
WET_REACH=.0015  # unvalidated near-surface capture approximation, not remote suction
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
    return np.array([r*math.cos(a),r*math.sin(a),.018]), np.array([0.,-.025,-.005])


@dataclass
class WaterModel:
    t: float=0.
    supplied: float=0.
    delivered: list=field(default_factory=lambda:[0.,0.,0.])
    coverage_s: list=field(default_factory=lambda:[[0.]*9 for _ in range(3)])
    captured: list=field(default_factory=lambda:[0.,0.,0.])
    pool: list=field(default_factory=lambda:[0.,0.,0.])
    crown: list=field(default_factory=lambda:[0.,0.,0.])
    drained: list=field(default_factory=lambda:[0.,0.,0.])
    last_runoff: list=field(default_factory=lambda:[0.,0.,0.])
    last_capture: list=field(default_factory=lambda:[0.,0.,0.])
    jet_end: list=field(default_factory=lambda:[0.,0.,0.])
    jet_in_mouth: bool=False
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
        self.active=-1;self.aimed=False;self.jet_in_mouth=False
        self.last_runoff=[0.,0.,0.];self.last_capture=[0.,0.,0.]
        for i,start in enumerate(STARTS):
            on=max(0.,min(self.t+dt,start+DURATION)-max(self.t,start))
            if on<=1e-10:continue
            self.active=i;v=on*IRRIGATION_RATE;self.supplied+=v
            height=ir[2]-SITES[i,2]
            hit=ir[:2]+ia[:2]*height/max(1e-9,-ia[2])
            aimed=ia[2]<-.94 and .008<=height<=.030 and np.linalg.norm(hit-SITES[i,:2])<=.010
            self.aimed=bool(aimed)
            if aimed:
                self.delivered[i]+=v;self.crown[i]+=v
                delta=hit-SITES[i,:2];radius=float(np.linalg.norm(delta))
                zone=0 if radius<=.0025 else 1+(int((math.atan2(delta[1],delta[0])%(2*math.pi))/(math.pi/4))%8) if .0045<=radius<=.0095 else None
                if zone is not None:self.coverage_s[i][zone]+=on
                self.jet_end=[float(hit[0]),float(hit[1]),float(SITES[i,2])]
                self.jet_in_mouth=True
            else:
                # A missed crown can still send water into the open mouth floor.
                floor_hit=ir[:2]+ia[:2]*max(0.,ir[2]-MOUTH_FLOOR)/max(1e-9,-ia[2])
                j=int(np.argmin(np.linalg.norm(MOUTH_CENTRES[:,:2]-floor_hit,axis=1)))
                in_floor=ia[2]<-.8 and abs(floor_hit[0]-MOUTH_CENTRES[j,0])<=.0175 and abs(floor_hit[1])<=.009
                if in_floor:self.pool[j]+=v;self.jet_in_mouth=True
                else:self.lost+=v
                self.jet_end=[float(floor_hit[0]),float(floor_hit[1]),MOUTH_FLOOR]
            # A transparent, benchmark-specific working-area exclusion zone.
            obstructed=np.linalg.norm(su[:2]-SITES[i,:2])<.009 and su[2]<SITES[i,2]+.028
            self.obstruction_s+=on*bool(obstructed)
        self.failed |= self.obstruction_s>.25
        # Crown water drains into the mouth; neither a visual marker nor a score event removes it.
        for i in range(3):
            runoff=self.crown[i]*(1-math.exp(-dt/DRAIN_TIME))
            self.crown[i]-=runoff;self.pool[i]+=runoff
            self.drained[i]+=runoff;self.last_runoff[i]=runoff
        # A shallow connected gutter permits slow redistribution between neighbouring cells.
        before=list(self.pool)
        for i in range(2):
            flow=.08*(before[i]-before[i+1])*dt
            donor=i if flow>=0 else i+1;receiver=i+1 if flow>=0 else i
            amount=min(abs(flow),self.pool[donor]);self.pool[donor]-=amount;self.pool[receiver]+=amount
        # Record the PRE-suction maximum so a large simultaneous pump step cannot hide a peak.
        self.peak=max(self.peak,self.mouth_water())
        weights=[]
        for i,p in enumerate(MOUTH_CENTRES):
            dx,dy=np.abs(su[:2]-p[:2]);surface=MOUTH_FLOOR+self.pool[i]*1e-6/MOUTH_AREA
            gap=su[2]-surface
            orientation=max(0.,min(1.,(-sa[2]-.8)/.2))
            local=dx<=.014 and dy<=.009 and MOUTH_FLOOR-.0005<=su[2] and gap<WET_REACH
            wet=max(0.,min(1.,1-gap/WET_REACH))
            weights.append(wet*orientation if local and self.pool[i]>0 else 0.)
        remaining=SUCTION_RATE*dt
        for i in sorted(range(3),key=lambda i:weights[i],reverse=True):
            take=min(self.pool[i],remaining*weights[i]);self.pool[i]-=take;self.captured[i]+=take
            self.last_capture[i]=take;remaining-=take
        for i in range(3):
            overflow=max(0.,self.pool[i]-CAPACITY);self.pool[i]-=overflow;self.lost+=overflow
        self.t+=dt

    def covered(self):
        return [sum(t>=COVERAGE_DWELL-1e-9 for t in row) for row in self.coverage_s]

    def mouth_water(self):return sum(self.crown)+sum(self.pool)

    def score(self,clear=False,held=True,*,finished=False):
        # Water outcomes gate every tier. Cleaning later cannot erase an earlier flood.
        if self.failed or self.lost>.30+1e-9 or self.peak>MOUTH_PEAK_LIMIT+1e-9:return 0.
        if self.mouth_water()>MOUTH_FINAL_LIMIT+1e-9:return 0.
        if sum(self.captured)<.90*self.supplied-1e-9:return 0.
        completed=sum(self.t>=s+DURATION and self.delivered[i]>=1.8 and self.covered()[i]==9 for i,s in enumerate(STARTS))
        if completed==3 and clear and finished and self.mouth_water()<=DRY_LIMIT+1e-9:return 1.
        return .25*completed

    def balance_error(self):return self.supplied-sum(self.captured)-self.mouth_water()-self.lost
