"""Bimanual irrigation and aspiration on a rigid dental training phantom.
Tool manipulation uses rigid contact. Water is a conservative lumped-volume model.
"""
import pathlib,sys,math
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import mechkit as m
from fluid_model import WaterModel,SITES,STARTS,DURATION,sweep_offsets,COVERAGE_DWELL
from yam_arena.task_file import TABLE_TOP
SCENE='station';TOP=TABLE_TOP[SCENE]
SCORE_OVER='end';SUCCESS_HOLD_S=1.
INSTRUCTION='Clean each highlighted tooth with circular rinsing motions while keeping the suction tube beside it.'
LOOKS={k:m.Look(color=m.rgb(*v),roughness=.35) for k,v in {
 'white':(.96,.95,.87),'gum':(.80,.34,.40),'tongue':(.64,.22,.29),
 'steel':(.59,.66,.69),'blue':(.05,.38,.70),'water':(.08,.63,.93),
 'yellow':(.98,.72,.05),'green':(.12,.76,.24),'black':(.06,.08,.09),'grey':(.45,.48,.50)}.items()}
IR_RACK=np.array([.28,.20,TOP+.030]);SU_RACK=np.array([.28,-.20,TOP+.030])
TIPS={'irrigator':np.array([0.,-.090,-.025]),'suction':np.array([0.,.090,-.025])}
GRIP_H=.040

def ellipsoid(scale,center):
    q=m.sphere(1.,segments=24);return m.Mesh(q.v*np.asarray(scale)+np.asarray(center),q.f)

def phantom():
    p=[('base',m.box((.17,.13,.012),(0,0,.006)),'white')];c=[m.col_box('basec',(.17,.13,.012),(0,0,.006))]
    for n,size,loc in [('left',(.115,.028,.018),(0,.025,.019)),('right',(.115,.028,.018),(0,-.025,.019)),('front',(.028,.070,.018),(-.061,0,.019))]:
        mesh=m.box(size,loc);p.append((n,mesh,'gum'));c.append(m.col_hull(n+'c',mesh))
    tongue=ellipsoid((.043,.010,.007),(.005,0,.018));p.append(('tongue',tongue,'tongue'));c.append(m.col_hull('tonguec',tongue))
    for side in (-1,1):
        for i,x in enumerate((-.035,0,.035)):
            n=f'tooth{0 if side<0 else 1}_{i}';loc=np.array([x,side*.025,.030])
            crown=m.cylinder(.010,.014,loc,segments=24);p.append((n,crown,'white'));c.append(m.col_hull(n+'c',crown))
            for a,(dx,dy) in enumerate(((-.004,-.004),(-.004,.004),(.004,-.004),(.004,.004))):
                cusp=ellipsoid((.0045,.0045,.003),loc+[dx,dy,.007]);p.append((n+str(a),cusp,'white'));c.append(m.col_hull(n+str(a)+'c',cusp))
    for i,y in enumerate((-.018,0,.018)):
        incisor=m.box((.012,.012,.018),(-.061,y,.035));p.append((f'incisor{i}',incisor,'white'));c.append(m.col_hull(f'incisorc{i}',incisor))
    return m.fixed('phantom',(.27,0,TOP),p,c,LOOKS)

def instrument(name,pos):
    sign=-1 if name=='irrigator' else 1
    color='blue' if name=='irrigator' else 'white';rad=.0025 if name=='irrigator' else .0045
    handle=m.box((.028,.024,.055),(0,0,.0275))
    shaft=m.tube([(0,0,.022),(0,sign*.025,.022),(0,sign*.09,-.009),(0,sign*.09,-.025)],rad,sides=12)
    # Segment hulls preserve the bent shape; one hull across the bend would fill the gap.
    points=[(0,0,.022),(0,sign*.025,.022),(0,sign*.09,-.009),(0,sign*.09,-.025)]
    cols=[m.col_hull('handlec',handle)]
    for i in range(3):cols.append(m.col_hull(f'shaftc{i}',m.tube(points[i:i+2],rad,sides=10)))
    p=[('handle',handle,color),('grip',m.box((.029,.025,.020),(0,0,.041)),'grey'),('shaft',shaft,'steel'),
       ('port',m.cylinder(rad*.75,.0005,(0,sign*.09,-.0252)),'black')]
    return m.free(name,pos,p,cols,LOOKS,mass=.075,friction=(1.4,1.1))

def rack(name,pos,color):
    return m.fixed(name,pos-[0,0,.03],[('rack',m.cylinder(.025,.03,(0,0,.015)),color)],[m.col_cylinder('rackc',.025,.03,(0,0,.015))],LOOKS)

def indicators():
    p=[]
    for i,site in enumerate(SITES):
        p.append((f'target{i}',m.cylinder(.007,.003,(site[0],.072,.020)),'yellow'))
        for z in range(9):
            a=(z-.5)*math.pi/4
            loc=site+np.array([.0085*math.cos(a),.0085*math.sin(a),.004]) if z else site+np.array([0,0,.001])
            for label,color in [('pending','yellow'),('covered','green')]:
                p.append((f'{label}{i}_{z}',m.sphere(.0009,loc),color,label=='covered'))
        for level in range(1,6):
            p.append((f'pool{i}_{level}',ellipsoid((.004+level*.001,.004+level*.001,.0005),(site[0],site[1],.038+level*.0007)),'water',True))
    for j in range(4):p.append((f'jet{j}',m.sphere(.0015),'water',True))
    # A visible graduated collection vial; its levels follow captured volume only.
    p.append(('vial',m.cylinder(.018,.008,(.39,-.12,.004)),'white'))
    for i in range(20):p.append((f'collected{i}',m.cylinder(.014,.003,(.39,-.12,.010+i*.0035)),'water',True))
    for k,(x,y) in enumerate(((.372,-.12),(.408,-.12))):
        p.append((f'post{k}',m.cylinder(.002,.085,(x,y,.0425)),'steel'))
    return m.fixed('indicators',(0,0,TOP),p,[],LOOKS)

OBJECTS=[phantom(),instrument('irrigator',IR_RACK),instrument('suction',SU_RACK),rack('irrigation_rack',IR_RACK,'blue'),rack('suction_rack',SU_RACK,'white'),indicators()]

class Trial:
    def reset(self,env=None):
        self.water=WaterModel();self.value=0.;self.steps=0;self.report={};self.ops={}
    def draw(self,ir,axis):
        prefix=f'{m.ENV_PATH}/indicators/visual/'
        next_site=min(2,sum(self.water.t>=s+DURATION for s in STARTS[:2]))
        for i in range(3):
            for z,t in enumerate(self.water.coverage_s[i]):
                done=t>=COVERAGE_DWELL-1e-9
                m.set_visible(prefix+f'pending{i}_{z}',not done)
                m.set_visible(prefix+f'covered{i}_{z}',done)
            m.set_visible(prefix+f'target{i}',i==next_site)
            level=min(5,max(1,math.ceil(self.water.pool[i]/.09))) if self.water.pool[i]>.005 else 0
            for k in range(1,6):m.set_visible(prefix+f'pool{i}_{k}',k==level)
        for k in range(20):m.set_visible(prefix+f'collected{k}',sum(self.water.captured)>=(k+1)*.3)
        for j in range(4):
            m.set_visible(prefix+f'jet{j}',self.water.active>=0)
            if self.water.active>=0:
                if j not in self.ops:
                    import isaaclab.sim as sim_utils
                    from pxr import UsdGeom
                    prim=sim_utils.get_current_stage().GetPrimAtPath(prefix+f'jet{j}');xf=UsdGeom.Xformable(prim)
                    ops=xf.GetOrderedXformOps();self.ops[j]=ops[0] if ops else xf.AddTranslateOp()
                p=ir+axis*.020*((self.water.t*8+j/4)%1)
                self.ops[j].Set(tuple(float(v) for v in p))
    def step(self,env):
        self.steps+=1;dt=float(env.unwrapped.step_dt)
        states={n:m.state(env,n) for n in TIPS}
        tips={n:s.to_world(TIPS[n])[0]-np.array([0,0,TOP]) for n,s in states.items()}
        axes={n:s.rotation()@np.array([0,0,-1.]) for n,s in states.items()}
        safe=True
        for n,s in states.items():
            p=tips[n]
            # Conservative tip-clearance guard around the rigid gum model.
            over_gum=.195<p[0]<.340 and abs(p[1])<.045
            safe &= not(over_gum and p[2]<.030)
            safe &= np.isfinite(s.pos).all() and s.pos[2]>TOP+.005
        separation=float(np.linalg.norm(tips['irrigator']-tips['suction']))
        safe &= separation>.006
        self.water.step(dt,tips['irrigator'],tips['suction'],axes['irrigator'],axes['suction'],safe=bool(safe))
        fingers=m.fingertips(env)
        held=all(np.min(np.linalg.norm(fingers[slice(0,12) if n=='irrigator' else slice(12,24)]-states[n].to_world((0,0,GRIP_H))[0],axis=1))<.035 for n in TIPS)
        clear=all(p[2]>.080 or abs(p[1])>.075 for p in tips.values())
        self.value=self.water.score(clear=clear,held=held)
        self.draw(tips['irrigator'],axes['irrigator'])
        self.report=dict(score=self.value,time=round(self.water.t,2),active=self.water.active,supplied=round(self.water.supplied,3),delivered=np.round(self.water.delivered,3).tolist(),captured=np.round(self.water.captured,3).tolist(),pool=np.round(self.water.pool,3).tolist(),coverage=self.water.covered(),coverage_s=np.round(self.water.coverage_s,3).tolist(),lost=round(self.water.lost,3),peak_pool=round(self.water.peak,3),balance_error=round(self.water.balance_error(),10),failed=bool(self.water.failed),held=bool(held),clear=bool(clear),separation=round(separation,4),irrigator_tip=np.round(tips['irrigator'],4).tolist(),suction_tip=np.round(tips['suction'],4).tolist())
        if self.steps%100==0:print('[chairside]',self.report,flush=True)
TRIAL=Trial();TRIAL.reset();m.on_reset(TRIAL.reset);m.on_step(TRIAL.step)
def score(objects):return TRIAL.value
def success(objects):return score(objects)==1.

def demo_script(ctx):
    import demokit as d
    L,R=ctx.left,ctx.right
    if ctx.mode=='none':yield from L.wait(3);return
    yield from L.pick('irrigator',GRIP_H,width=.024,grip=d.down(0),above=.045,lift=.060,label='grasp irrigator')
    yield from R.pick('suction',GRIP_H,width=.024,grip=d.down(0),above=.045,lift=.060,label='grasp HVE')
    def move_tip(arm,name,target):
        target=np.asarray(target)+[0,0,TOP]
        tip=lambda:m.state(ctx.emb._env,name).to_world(TIPS[name])[0]
        yield from arm.move(arm.at()+target-tip(),t=1.6,label='position '+name)
        yield from arm.servo(arm.tcp()+target-tip(),timeout=1.2,label='align '+name)
    for i,site in enumerate(SITES):
        ir0,su0=sweep_offsets(0.)
        actions=[move_tip(L,'irrigator',site+ir0)]
        if ctx.mode!='static' or i==0:actions.append(move_tip(R,'suction',site+su0))
        yield from ctx.together(*actions)
        yield from ctx.until(lambda:ctx.t>=STARTS[i],timeout=20,label='start metered circular rinse')
        if ctx.mode=='point':
            yield from ctx.until(lambda:ctx.t>=STARTS[i]+DURATION,timeout=8,label='point-rinse control')
        else:
            mounts={name:arm.at()-m.state(ctx.emb._env,name).to_world(TIPS[name])[0]
                    for arm,name in [(L,'irrigator'),(R,'suction')]}
            def tcp_target(arm,name,index):
                ir,su=sweep_offsets(ctx.t-STARTS[i]+d.DT)
                desired=site+(ir if index==0 else su)+[0,0,TOP]
                return desired+mounts[name]
            seconds=max(.05,STARTS[i]+DURATION-ctx.t)
            motions=[L.follow(lambda:tcp_target(L,'irrigator',0),t=seconds,speed=.08,label='inner and outer crown circles')]
            if ctx.mode!='static':motions.append(R.follow(lambda:tcp_target(R,'suction',1),t=seconds,speed=.08,label='follow crown from open side'))
            yield from ctx.together(*motions)
        yield from ctx.until(lambda:ctx.t>=STARTS[i]+DURATION+.4,timeout=2,label='finish aspiration')
    yield from ctx.together(L.move(L.at()+[0,0,.045],t=1.2,label='withdraw irrigator'),R.move(R.at()+[0,0,.045],t=1.2,label='withdraw HVE'))
    yield from L.wait(1)
    print('[chairside final]',TRIAL.report,flush=True)
