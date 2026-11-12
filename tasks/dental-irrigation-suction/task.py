"""Bimanual irrigation and aspiration on a rigid dental training phantom.
Tool manipulation uses rigid contact. Water is a conservative lumped-volume model.
"""
import pathlib,sys,math
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import mechkit as m
from fluid_model import WaterModel,SITES,STARTS,DURATION,sweep_offsets,COVERAGE_DWELL,MOUTH_CENTRES,MOUTH_AREA,MOUTH_FLOOR
from finish import FinishTracker,rack_state,DRY_LIMIT
from endpoint_hold import EndpointHold
from yam_arena.task_file import TABLE_TOP
SCENE='station';TOP=TABLE_TOP[SCENE]
SCORE_OVER='end';SUCCESS_HOLD_S=0.05  # one confirmation step; raw score enforces a continuous 1 s hold
INSTRUCTION='Rinse the highlighted teeth, lift the rinsing tool while suction clears the mouth, then return and release both tools on their stands.'
LOOKS={k:m.Look(color=m.rgb(*v),roughness=.35) for k,v in {
 'white':(.96,.95,.87),'gum':(.80,.34,.40),'tongue':(.64,.22,.29),
 'steel':(.59,.66,.69),'blue':(.05,.38,.70),'water':(.08,.63,.93),
 'clear':(.75,.88,.92),'yellow':(.98,.72,.05),'green':(.12,.76,.24),'black':(.06,.08,.09),'grey':(.45,.48,.50)}.items()}
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
    for i,site in enumerate(MOUTH_CENTRES):
        loc=site-np.array([.27,0,0])
        floor=m.box((.028,.018,.001),loc+[0,0,-.0005])
        p.append((f'mouth_floor{i}',floor,'gum'));c.append(m.col_hull(f'mouth_floorc{i}',floor))
        for sign in (-1,1):
            wall=m.box((.028,.001,.004),loc+[0,sign*.0095,.0015])
            p.append((f'mouth_wall{i}_{sign+1}',wall,'gum'));c.append(m.col_hull(f'mouth_wallc{i}_{sign+1}',wall))
        if i<2:
            bridge=m.box((.007,.003,.001),loc+[.0175,0,-.0005])
            p.append((f'flow_channel{i}',bridge,'gum'));c.append(m.col_hull(f'flow_channelc{i}',bridge))
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
        p.append((f'mouth_pool{i}',m.box((.028,.018,.001)),'water',True))
        p.append((f'crown_water{i}',ellipsoid((.009,.009,.0004),(0,0,0)),'water',True))
        for j in range(10):
            p.append((f'runoff{i}_{j}',m.sphere(.0010),'water',True))
            p.append((f'aspirate{i}_{j}',m.sphere(.0009),'water',True))
    for j in range(18):p.append((f'jet{j}',m.sphere(.00085),'water',True))
    # A visible graduated collection vial; its levels follow captured volume only.
    p.append(('vial',m.cylinder(.018,.008,(.39,-.12,.004)),'white'))
    for i in range(20):p.append((f'collected{i}',m.cylinder(.014,.003,(.39,-.12,.010+i*.0035)),'water',True))
    for k,(x,y) in enumerate(((.372,-.12),(.408,-.12))):
        p.append((f'post{k}',m.cylinder(.002,.085,(x,y,.0425)),'steel'))
    return m.fixed('indicators',(0,0,TOP),p,[],LOOKS)

OBJECTS=[phantom(),instrument('irrigator',IR_RACK),instrument('suction',SU_RACK),rack('irrigation_rack',IR_RACK,'blue'),rack('suction_rack',SU_RACK,'white'),indicators()]

class Trial:
    def reset(self,env=None):
        self.water=WaterModel();self.finish=FinishTracker();self.endpoint=EndpointHold(.75);self.value=0.;self.steps=0;self.report={};self.ops={}
    def draw(self,ir,axis,su):
        prefix=f'{m.ENV_PATH}/indicators/visual/'
        def pose(name,p,scale=None):
            if name not in self.ops:
                import isaaclab.sim as sim_utils
                from pxr import UsdGeom
                prim=sim_utils.get_current_stage().GetPrimAtPath(prefix+name);xf=UsdGeom.Xformable(prim)
                existing=xf.GetOrderedXformOps()
                translate=next((op for op in existing if op.GetOpType()==UsdGeom.XformOp.TypeTranslate),None)
                scale_op=next((op for op in existing if op.GetOpType()==UsdGeom.XformOp.TypeScale),None)
                self.ops[name]=(translate if translate is not None else xf.AddTranslateOp(),scale_op if scale_op is not None else xf.AddScaleOp())
            self.ops[name][0].Set(tuple(float(v) for v in p))
            self.ops[name][1].Set(tuple(float(v) for v in (scale if scale is not None else (1,1,1))))
        next_site=min(2,sum(self.water.t>=s+DURATION for s in STARTS[:2]))
        for i,site in enumerate(SITES):
            for z,t in enumerate(self.water.coverage_s[i]):
                done=t>=COVERAGE_DWELL-1e-9
                m.set_visible(prefix+f'pending{i}_{z}',not done);m.set_visible(prefix+f'covered{i}_{z}',done)
            m.set_visible(prefix+f'target{i}',i==next_site)
            volume=self.water.pool[i];depth=volume*1e-6/MOUTH_AREA
            m.set_visible(prefix+f'mouth_pool{i}',volume>.002)
            pose(f'mouth_pool{i}',MOUTH_CENTRES[i]+[0,0,depth/2],(1,1,max(.001,depth/.001)))
            m.set_visible(prefix+f'crown_water{i}',self.water.crown[i]>.002)
            pose(f'crown_water{i}',site+[0,0,.0034])
            for j in range(10):
                phase=(self.water.t*3+j/10)%1
                # Film travels from the crown edge down to the lingual mouth-floor cell.
                start=site+np.array([.005*math.sin(j*2.4),-.005,.003])
                end=MOUTH_CENTRES[i]+[.005*math.sin(j*2.4),0,depth]
                m.set_visible(prefix+f'runoff{i}_{j}',self.water.last_runoff[i]>.00005)
                pose(f'runoff{i}_{j}',start*(1-phase)+end*phase)
                wet=MOUTH_CENTRES[i]+[0,0,depth]
                m.set_visible(prefix+f'aspirate{i}_{j}',self.water.last_capture[i]>.00005)
                pose(f'aspirate{i}_{j}',wet*(1-phase)+(su+[0,0,.004])*phase)
        for k in range(20):m.set_visible(prefix+f'collected{k}',sum(self.water.captured)>=(k+1)*.3)
        for j in range(18):
            on=self.water.active>=0;m.set_visible(prefix+f'jet{j}',on)
            if on:
                phase=(self.water.t*5+j/18)%1
                pose(f'jet{j}',ir*(1-phase)+np.asarray(self.water.jet_end)*phase)
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
        ir_lifted=bool(tips['irrigator'][2]>.080)
        su=tips['suction']
        su_in_mouth=bool(MOUTH_CENTRES[0,0]-.014<=su[0]<=MOUTH_CENTRES[-1,0]+.014 and abs(su[1])<=.009 and MOUTH_FLOOR-.0005<=su[2]<=MOUTH_FLOOR+.0015 and axes['suction'][2]<-.94)
        self.finish.step(dt,self.water.t,self.water.t>=STARTS[-1]+DURATION,ir_lifted,su_in_mouth,self.water.mouth_water())
        parked={};released={}
        for name,target in [('irrigator',IR_RACK),('suction',SU_RACK)]:
            state=states[name]
            parked[name],released[name]=rack_state(state.pos,state.rotation(),state.lin_vel,target,fingers,state.to_world((0,0,GRIP_H))[0])
        finished=bool(self.finish.cleanup_complete and all(parked.values()) and all(released.values()))
        self.value=self.endpoint.step(dt,self.water.score(clear=clear,held=held,finished=finished))
        self.draw(tips['irrigator'],axes['irrigator'],tips['suction'])
        self.report=dict(score=self.value,time=round(self.water.t,2),active=self.water.active,supplied=round(self.water.supplied,3),delivered=np.round(self.water.delivered,3).tolist(),captured=np.round(self.water.captured,3).tolist(),pool=np.round(self.water.pool,3).tolist(),coverage=self.water.covered(),coverage_s=np.round(self.water.coverage_s,3).tolist(),lost=round(self.water.lost,3),peak_pool=round(self.water.peak,3),balance_error=round(self.water.balance_error(),10),failed=bool(self.water.failed),held=bool(held),clear=bool(clear),separation=round(separation,4),irrigator_tip=np.round(tips['irrigator'],4).tolist(),suction_tip=np.round(tips['suction'],4).tolist())
        self.report.update(mouth_water_ml=round(self.water.mouth_water(),4),peak_mouth_water_ml=round(self.water.peak,4),crown_water_ml=np.round(self.water.crown,4).tolist(),floor_water_ml=np.round(self.water.pool,4).tolist(),recovered_total_ml=round(sum(self.water.captured),4),capture_rate_ml_s=round(sum(self.water.last_capture)/dt,4),model_version='mouth-water-v4-held-return',endpoint_hold_s=round(self.endpoint.elapsed,3),cleanup_complete=self.finish.cleanup_complete,cleanup_time=self.finish.cleanup_time,suction_after_lift_s=round(self.finish.suction_after_lift_s,3),irrigator_lifted=ir_lifted,suction_in_mouth=su_in_mouth,parked=parked,released=released,finish_ready=finished,obstruction_s=round(self.water.obstruction_s,4),guard_safe=bool(safe))
        if self.steps%100==0:print('[chairside]',self.report,flush=True)
TRIAL=Trial();TRIAL.reset();m.on_reset(TRIAL.reset);m.on_step(TRIAL.step)
def score(objects):return TRIAL.value
def success(objects):return score(objects)==1.

def demo_script(ctx):
    import demokit as d
    modes={'full','early_return','no_return','no_release','wrong_place','too_high','none','point','static','fixed_site','off','late_suction','no_withdraw','obstruct'}
    if ctx.mode not in modes:
        raise ValueError(f'Unknown demo mode {ctx.mode!r}; choose {sorted(modes)}')
    L,R=ctx.left,ctx.right
    if ctx.mode=='none':yield from L.wait(60);return
    yield from L.pick('irrigator',GRIP_H,width=.024,grip=d.down(0),above=.045,lift=.060,label='grasp irrigator')
    yield from R.pick('suction',GRIP_H,width=.024,grip=d.down(0),above=.045,lift=.060,label='grasp evacuation tip')
    def move_tip(arm,name,target):
        target=np.asarray(target)+[0,0,TOP]
        tip=lambda:m.state(ctx.emb._env,name).to_world(TIPS[name])[0]
        if ctx.t<STARTS[0]:
            yield from arm.move(arm.at()+target+[0,0,.045]-tip(),t=1.0,label='approach above mouth '+name)
            yield from arm.servo(arm.tcp()+target+[0,0,.045]-tip(),timeout=.6,label='align above mouth '+name)
        yield from arm.move(arm.at()+target-tip(),t=1.0,label='position in working region '+name)
        yield from arm.servo(arm.tcp()+target-tip(),tol=.0005 if name=='suction' else .003,timeout=1.2,label='align '+name)
    for i,site in enumerate(SITES):
        ir0,su0=sweep_offsets(0.)
        if ctx.mode=='wrong_place':su0=np.array([0,-.080,-.005])
        if ctx.mode=='too_high':su0=np.array([0,-.025,.018])
        if ctx.mode=='obstruct':su0=np.array([0,0,.007])
        actions=[move_tip(L,'irrigator',site+ir0)]
        if ctx.mode not in {'off','late_suction'} and (ctx.mode!='static' or i==0):
            actions.append(move_tip(R,'suction',site+su0))
        yield from ctx.together(*actions)
        yield from ctx.until(lambda:ctx.t>=STARTS[i],timeout=20,label='start metered circular rinse')
        if ctx.mode=='point':
            yield from ctx.until(lambda:ctx.t>=STARTS[i]+DURATION,timeout=8,label='point-rinse control')
        else:
            mounts={name:arm.at()-m.state(ctx.emb._env,name).to_world(TIPS[name])[0]
                    for arm,name in [(L,'irrigator'),(R,'suction')]}
            def tcp_target(arm,name,index):
                ir,su=sweep_offsets(ctx.t-STARTS[i]+d.DT)
                if ctx.mode=='wrong_place':su=np.array([su[0],-.080,-.005])
                if ctx.mode=='too_high':su=np.array([su[0],-.025,.018])
                if ctx.mode=='obstruct':su=np.array([0,0,.007])
                desired=site+(ir if index==0 else su)+[0,0,TOP]
                if name=='suction':
                    actual=m.state(ctx.emb._env,name).to_world(TIPS[name])[0]
                    return arm.at()+np.clip(.30*(desired-actual),-.001,.001)
                return desired+mounts[name]
            seconds=max(.05,STARTS[i]+DURATION-ctx.t)
            motions=[L.follow(lambda:tcp_target(L,'irrigator',0),t=seconds,speed=.08,label='inner and outer crown circles')]
            if ctx.mode not in {'static','fixed_site','off','late_suction'}:
                motions.append(R.follow(lambda:tcp_target(R,'suction',1),t=seconds,speed=.08,label='aspirate the mouth-floor pool'))
            yield from ctx.together(*motions)
        yield from ctx.until(lambda:ctx.t>=STARTS[i]+DURATION+.4,timeout=2,label='finish aspiration')
    if ctx.mode=='late_suction':
        # Complete all three rinses first, then try to recover spilled water.
        # Irrigator timing/path stays the same as full mode during every pulse.
        for site in SITES:
            yield from move_tip(R,'suction',site+[0,-.025,-.005])
            yield from R.wait(1.)
    async_cleanup=ctx.mode in {'full','no_return','no_release','fixed_site','point'}
    if async_cleanup:
        # Irrigation has ended. Lift only the rinse tool; suction remains in the mouth.
        yield from L.move(L.at()+[0,0,.060],t=1.2,label='lift rinsing tool; keep suction inside mouth')
        def drain_target(index):
            desired=MOUTH_CENTRES[index]+[0,0,.001]+[0,0,TOP]
            actual=m.state(ctx.emb._env,'suction').to_world(TIPS['suction'])[0]
            return R.at()+np.clip(.30*(desired-actual),-.001,.001)
        # Sweep all mouth-floor regions, then revisit remaining water if required.
        deadline=min(52.,ctx.t+11.)
        for index in [2,1,0]:
            if ctx.t>=deadline:break
            yield from R.follow(lambda j=index:drain_target(j),t=1.6,speed=.05,label='clear mouth-floor region '+str(index+1))
        while (TRIAL.water.mouth_water()>.005 or not TRIAL.finish.cleanup_complete) and ctx.t<deadline:
            index=int(np.argmax(TRIAL.water.pool))
            yield from R.follow(lambda j=index:drain_target(j),t=.8,speed=.05,label='remove remaining mouth water')
        if TRIAL.water.mouth_water()>DRY_LIMIT or not TRIAL.finish.cleanup_complete:
            print('[cleanup incomplete] tools not returned; full score unavailable',flush=True)
            yield from L.wait(1.)
            return
        yield from R.move(R.at()+[0,0,.060],t=1.0,label='withdraw suction after mouth is clear')
    elif ctx.mode!='no_withdraw':
        yield from ctx.together(L.move(L.at()+[0,0,.085],t=1.6,label='withdraw irrigator'),R.move(R.at()+[0,0,.085],t=1.6,label='withdraw suction early'))
    if ctx.mode in {'full','early_return','no_release','point','fixed_site'}:
        def return_tool(arm,name,home):
            origin=lambda:m.state(ctx.emb._env,name).pos
            yield from arm.move(arm.at()+home+[0,0,.045]-origin(),t=1.5,label='carry '+name+' above original stand')
            yield from arm.servo(arm.tcp()+home+[0,0,.045]-origin(),timeout=.8,label='align with original stand')
            yield from arm.move(arm.at()+home+[0,0,.002]-origin(),t=1.0,label='lower '+name+' onto original stand')
            yield from arm.servo(arm.tcp()+home+[0,0,.002]-origin(),tol=.001,timeout=.8,label='settle on original stand')
            if ctx.mode!='no_release':
                yield from arm.open(t=.5,label='release '+name)
                yield from arm.move(arm.at()+[0,0,.090],t=1.0,label='clear fingers from returned '+name)
        yield from ctx.together(return_tool(L,'irrigator',IR_RACK),return_tool(R,'suction',SU_RACK))
    yield from L.wait(1.2)
    print('[chairside final]',TRIAL.report,flush=True)
