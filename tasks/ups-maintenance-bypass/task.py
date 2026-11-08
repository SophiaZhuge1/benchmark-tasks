"""UPS service trainer: preserve load continuity through a cartridge exchange."""
import pathlib, sys, math
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import mechkit as m
from power_model import PowerModel
from labels import label
from yam_arena.task_file import TABLE_TOP
SCENE='station'; TOP=TABLE_TOP[SCENE]
SCORE_OVER='end'; SUCCESS_HOLD_S=1.
INSTRUCTION='Use the bypass to replace the faulty UPS cartridge without interrupting the server, then restore normal power.'
LOOKS={k:m.Look(color=m.rgb(*v),roughness=.4) for k,v in {
 'steel':(.53,.59,.65),'black':(.055,.07,.09),'grey':(.23,.29,.34),
 'blue':(.05,.35,.85),'amber':(1.,.60,.02),'green':(.08,.90,.22),
 'red':(.95,.035,.025),'white':(.88,.92,.94),'gold':(.9,.66,.18)}.items()}
for color in ('green','red','amber','blue'):
    LOOKS[color+'_lit']=m.Look(color=LOOKS[color].color,emissive=tuple(v*.45 for v in LOOKS[color].color),roughness=.3)
SOCKET=np.array([.285,-.025,TOP+.012]); NEW=np.array([.195,-.235,TOP+.012]); PARK=np.array([.365,-.235,TOP+.012])
SWITCH=np.array([.245,.190,TOP]); GRIP_H=.100

def cartridge(name,pos,color):
    body=m.box((.060,.050,.040),(0,0,.020)); handle=m.box((.028,.024,.075),(0,0,.0775))
    p=[('case',body,'steel'),('face',m.box((.061,.051,.006),(0,0,.038)),color),('handle',handle,color)]
    for i in range(5):p.append((f'vent{i}',m.box((.003,.038,.001),(-.020+i*.010,0,.0415)),'black'))
    for i in (-1,1):p.append((f'contact{i+1}',m.box((.009,.010,.002),(i*.018,0,.001)),'gold'))
    return m.free(name,pos,p,[m.col_hull('casec',body),m.col_hull('handlec',handle)],LOOKS,mass=.12,friction=(1.4,1.1))

def cradle(name,pos,color,guides=False):
    dims=(.112,.102,.012) if guides else (.086,.076,.012)
    p=[('base',m.box(dims,(0,0,-.006)),color)];c=[m.col_box('basec',dims,(0,0,-.006))]
    if guides:
        # Flared mouth guides a slightly misaligned module into the close-fitting seat.
        for i,(inner,depth,angle) in enumerate(((.035,.094,0),(.035,.094,180),(.030,.070,90),(.030,.070,270))):
            wall=m.prism([(inner,0),(inner+.017,0),(inner+.017,.029),(inner+.012,.029)],-depth/2,depth/2).turned(90,'x').turned(angle,'z')
            p.append((f'guide{i}',wall,'grey'));c.append(m.col_hull(f'guidec{i}',wall))
        for i in (-1,1):p.append((f'contact{i+1}',m.box((.009,.010,.0007),(i*.018,0,.0004)),'gold'))
    return m.fixed(name,pos,p,c,LOOKS)

def switch():
    knob=m.box((.028,.024,.042),(0,0,.054))
    base=[('housing',m.box((.118,.080,.028),(.035,0,.014)),'grey'),('slot',m.box((.088,.008,.002),(.035,0,.029)),'black'),
          ('normal',m.box((.020,.022,.003),(0,-.026,.030)),'blue'),('service',m.box((.020,.022,.003),(.070,-.026,.030)),'amber')]
    base.extend([('ups_label',label('UPS',(0,.027,.029),.001),'white'),('byp_label',label('BYP',(.070,.027,.029),.001),'white')])
    link=m.slider('selector','X',0.,.070,[('handle',knob,'white')],[m.col_hull('handlec',knob)],friction=1.,damping=3.,mass=.06)
    return m.mechanism('bypass_switch',SWITCH,[link],LOOKS,frame_parts=base,frame_colliders=[m.col_box('housingc',(.118,.080,.028),(.035,0,.014))])

def server():
    p=[('rack',m.box((.22,.10,.10),(.42,.015,.050)),'black')]
    for i in range(3):
        p.append((f'blade{i}',m.box((.19,.004,.024),(.42,-.038,.018+i*.031)),'grey'))
        for j in range(6):p.append((f'vent{i}_{j}',m.box((.010,.002,.013),(.36+j*.023,-.041,.018+i*.031)),'black'))
    # Large, separate lamps: live power, sticky outage, maintenance supply, UPS ready.
    for name,x,color in [('live',.35,'green'),('outage',.395,'red'),('bypass',.44,'amber'),('ready',.485,'blue')]:
        p.append((name+'_label',label({'live':'LIVE','outage':'FAIL','bypass':'BYP','ready':'READY'}[name],(x,.041,.101),.0011),'white'))
        p.append((name+'_off',m.cylinder(.013,.004,(x,.014,.103)),'grey'))
        p.append((name,m.cylinder(.012,.005,(x,.014,.104)),color+'_lit',name!='live'))
    for name,a,b,color in [('normalwire',(.285,.025,.003),(.355,-.025,.003),'blue'),('bypasswire',(.315,.15,.003),(.44,.065,.003),'amber')]:
        p.append((name,m.tube([a,b],.003),color))
    return m.fixed('server',(.07,.18,TOP),p,[m.col_box('rackc',(.22,.10,.10),(.42,.015,.050))],LOOKS)

OBJECTS=[cradle('ups_socket',SOCKET,'black',True),cradle('new_tray',NEW,'blue'),cradle('service_tray',PARK,'amber'),cartridge('faulted',SOCKET+[0,0,.0005],'amber'),cartridge('replacement',NEW+[0,0,.0005],'blue'),switch(),server()]

def aligned(state,target,tol=.006):
    p=np.asarray(state.pos)-target; r=state.rotation()
    return bool(abs(p[0])<tol and abs(p[1])<tol and abs(p[2])<.004 and r[2,2]>math.cos(math.radians(8)) and r[0,0]>math.cos(math.radians(10)))

class Trial:
    def reset(self,env=None):
        self.power=PowerModel();self.value=0.;self.steps=0;self.report={};self.dropped=False
    def step(self,env):
        self.steps+=1
        old=m.state(env,'faulted');new=m.state(env,'replacement');q=m.state(env,'bypass_switch').joint('selector')
        fingers=m.fingertips(env)
        clear=all(np.min(np.linalg.norm(fingers-s.to_world((0,0,GRIP_H))[0],axis=1))>.050 for s in (old,new))
        old_seated=aligned(old,SOCKET);new_seated=aligned(new,SOCKET);parked=aligned(old,PARK,.013)
        self.power.step(float(env.unwrapped.step_dt),float(q),old_seated,new_seated,parked,bool(clear))
        self.dropped |= any(s.pos[2]<TOP-.010 for s in (old,new))
        self.value=0. if self.dropped else self.power.score()
        for name,visible in [('live',self.power.powered),('outage',self.power.first_outage is not None),('bypass',self.power.bypass),('ready',self.power.ready)]:
            m.set_visible(f'{m.ENV_PATH}/server/visual/{name}',visible)
        self.report=dict(score=self.value,dropped=self.dropped,time=round(self.power.t,2),switch_mm=round(float(q)*1000,2),powered=self.power.powered,outage_s=round(self.power.outage_s,3),first_outage=self.power.first_outage,unsafe_removal=self.power.unsafe_removal,old_seated=old_seated,new_seated=new_seated,ready=self.power.ready,old_parked=parked,clear=bool(clear),final_s=round(self.power.final_s,2),old_pos=np.round(old.pos,4).tolist(),new_pos=np.round(new.pos,4).tolist(),new_axis=np.round(np.diag(new.rotation()),3).tolist())
        if self.steps%100==0:print('[ups]',self.report,flush=True)
TRIAL=Trial();TRIAL.reset();m.on_reset(TRIAL.reset);m.on_step(TRIAL.step)
def score(objects):return TRIAL.value
def success(objects):return score(objects)==1.

def demo_script(ctx):
    import demokit as d
    L,R=ctx.left,ctx.right
    if ctx.mode=='none':yield from L.wait(3);return
    def set_switch(target):
        q=lambda:m.state(ctx.emb._env,'bypass_switch').joint('selector')
        at=lambda:SWITCH+np.array([q(),0,.061])
        yield from L.pick(at,0.,width=.024,grip=d.down(0),above=.055,lift=0.,label='grasp bypass selector')
        anchor=L.at().copy();start=q()
        yield from L.move(anchor+[target-start,0,0],t=1.6,label='transfer supply')
        yield from L.servo(L.tcp()+[target-q(),0,0],timeout=.8,label='seat switch')
        yield from L.open()
        yield from L.move(L.at()+[0,0,.10],t=.6,label='clear switch')
    def place(name,point):
        state=lambda:m.state(ctx.emb._env,name)
        yield from R.move(R.at()+point+[0,0,.050]-state().pos,t=1.4,label='carry '+name)
        for _ in range(3):
            yield from R.servo(R.tcp()+point+[0,0,.050]-state().pos,timeout=1.,label='align '+name)
        for height in (.035,.020,.008,0.):
            goal=point+[0,0,height]
            yield from R.move(R.at()+goal-state().pos,t=.7,label='lower '+name)
            for _ in range(2):
                yield from R.servo(R.tcp()+goal-state().pos,timeout=.6,label='seat '+name)
        yield from R.open()
        yield from R.move(R.at()+[0,0,.040],t=.6,label='release '+name)
        yield from R.move(R.at()+[0,.070 if name=='faulted' else -.090,.010],t=.6,label='withdraw fingers')
    if ctx.mode not in ('no_bypass','outage_recovery'):yield from set_switch(.069)
    yield from R.pick('faulted',GRIP_H,width=.024,grip=d.down(0),above=.050,lift=.055,label='withdraw faulted cartridge')
    yield from place('faulted',PARK)
    if ctx.mode=='outage_recovery':
        yield from set_switch(.069)
        yield from R.wait(2.)
        return
    if ctx.mode=='early_return':yield from set_switch(.001)
    yield from R.pick('replacement',GRIP_H,width=.024,grip=d.down(0),above=.050,lift=.055,label='grasp replacement')
    yield from place('replacement',SOCKET)
    yield from R.wait(1.3)
    if ctx.mode=='full' and not aligned(m.state(ctx.emb._env,'replacement'),SOCKET):
        print('[ups-demo] Insertion not confirmed; keeping maintenance bypass engaged.',flush=True)
        return
    if ctx.mode not in ('leave_bypass','no_bypass','early_return'):yield from set_switch(.001)
    yield from R.wait(1.5)
