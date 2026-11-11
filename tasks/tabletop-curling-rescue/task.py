"""Two-arm tabletop curling: a four-stone shot and reactive side-edge save."""
import json
import os
import sys
from pathlib import Path
from dataclasses import asdict
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
import mechkit as m
from labels import label
from curling_model import CurlingModel, Observation, TARGET, RELEASE_X, RADIUS, BOARD
from yam_arena.task_file import TABLE_TOP

SCENE='station'
TOP=TABLE_TOP[SCENE]
SURFACE=TOP+.016
SCORE_OVER='end'
SUCCESS_HOLD_S=.1
INSTRUCTION='Slide blue towards the target with the left arm and release before the yellow line; use the right arm to stop red if it heads off the side, then withdraw both arms and leave all four stones on the board.'
BLUE_START=np.array([.120,.040,SURFACE+.012])
RED_START=np.array([.350,-.005,SURFACE+.012])
EXTRA_STARTS={"green":np.array([.510,.290,SURFACE+.012]),"orange":np.array([.720,.060,SURFACE+.012])}
NAMES=("blue","red","green","orange")
MU=.035
LOOKS={n:m.Look(color=m.rgb(*c),roughness=.35) for n,c in {
    'white':(.94,.97,.98),'navy':(.035,.09,.16),'blue':(.05,.35,.96),
    'red':(.92,.06,.10),'yellow':(1.,.75,.03),'grey':(.28,.35,.43),
    'ice':(.76,.89,.94),'wood':(.55,.32,.15),'green':(.05,.65,.30),'orange':(1.,.45,.04)}.items()}


def disc(name,pos,color):
    body=m.cylinder(RADIUS,.024,segments=64)
    handle=m.box((.034,.018,.023),(0,0,.0235))
    return m.free(name,pos,[('puck',body,color),('rim',m.cylinder(RADIUS+.0003,.004,(0,0,.008),segments=64),'navy'),
        ('handle',handle,color)], [m.col_cylinder('puck_c',RADIUS,.024),m.col_hull('handle_c',handle)],
        LOOKS,mass=.10,friction=(MU,MU),torsional_patch=.004)


def board():
    # Ring meshes are visual only: a single flat collider prevents raised seams.
    parts=[('deck',m.box((.840,.420,.016)),'wood'),
           ('ice',m.box((.838,.418,.0006),(0,0,.0084)),'ice')]
    center=np.array([.460,.140,TOP+.008])
    tc=np.array([*TARGET,SURFACE+.001])-center
    for name,r,color,z in [('outer',.150,'blue',0),('middle',.100,'white',.0002),('inner',.065,'red',.0004),('button',.015,'white',.0006)]:
        parts.append((name,m.cylinder(r,.0001,tc+[0,0,z],segments=96),color))
    for x,color,name in [(RELEASE_X,'yellow','release'),(.150,'white','start')]:
        parts.append((name,m.box((.003,.415,.0002),(x-center[0],0,.009)),color))
    parts.append(('rescue_line',m.box((.835,.003,.0002),(0,-.195,.009)),'red'))
    parts.extend([('title',label('CURLING',(-.20,.185,.009),.003),'navy'),
                  ('line_label',label('RELEASE',(-.13,-.19,.009),.0018),'navy')])
    return m.fixed('board',center,parts,[m.col_box('surface',(.840,.420,.016))],LOOKS,friction=(MU,MU))


OBJECTS=[board(),disc('blue',BLUE_START,'blue'),disc('red',RED_START,'red')]
for name,pos in EXTRA_STARTS.items():OBJECTS.append(disc(name,pos,name))


def finger_clearance(s,fingers):
    p=s.to_local(fingers)
    # Distance to cylinder and handle; the fingertip sampling method is explicit.
    radial=np.maximum(np.linalg.norm(p[:,:2],axis=1)-RADIUS,0.)
    vertical=np.maximum(np.abs(p[:,2])-.012,0.)
    body=np.hypot(radial,vertical)
    handle=np.linalg.norm(np.maximum(np.abs(p-[0,0,.0235])-[.017,.009,.0115],0),axis=1)
    return float(np.minimum(body,handle).min())


def observe(env):
    states={n:m.state(env,n) for n in NAMES}
    b,r=states['blue'],states['red'];f=m.fingertips(env)
    clear={n:[finger_clearance(s,f[:12]),finger_clearance(s,f[12:])] for n,s in states.items()}
    valid=all(np.isfinite(a).all() for s in states.values() for a in (s.pos,s.lin_vel,s.ang_vel)) and np.isfinite(f).all()
    inside=all(BOARD[0]<=s.pos[0]<=BOARD[1] and BOARD[2]<=s.pos[1]<=BOARD[3] for s in states.values())
    o=Observation(float(b.pos[0]),float(b.pos[1]),float(r.pos[0]),float(r.pos[1]),
        red_vx=float(r.lin_vel[0]),red_vy=float(r.lin_vel[1]),
        max_speed=max(float(np.linalg.norm(s.lin_vel)) for s in states.values()),
        max_spin=max(float(np.linalg.norm(s.ang_vel)) for s in states.values()),
        left_blue=clear['blue'][0]<.006,right_blue=clear['blue'][1]<.006,
        left_red=clear['red'][0]<.006,right_red=clear['red'][1]<.006,
        other_contact=any(min(clear[n])<.006 for n in ['green','orange']),
        lifted=any(s.pos[2]>SURFACE+.024 or s.pos[2]<SURFACE-.005 for s in states.values()),
        tipped=any(s.tilt_deg()>25 for s in states.values()),any_out=not inside,valid=bool(valid))
    return o,states,clear


class Trial:
    def reset(self,env=None):
        self.model=CurlingModel();self.value=0.;self.steps=0;self.report=self.model.report()
        if getattr(self,'trace',None):self.trace.close()
        self.trace=None
        directory=os.environ.get('TASK_TRACE_DIR')
        if env is not None and directory:
            p=Path(directory);p.mkdir(parents=True,exist_ok=True)
            n=1
            while True:
                try:self.trace=(p/f'episode_{n:03d}.jsonl').open('x',buffering=1);break
                except FileExistsError:n+=1

    def step(self,env):
        o,states,clear=observe(env);self.steps+=1
        dt=float(env.unwrapped.step_dt);self.value=self.model.step(dt,o)
        self.report={**self.model.report(),'pucks':{n:dict(pos=s.pos.tolist(),vel=s.lin_vel.tolist(),clearance=clear[n]) for n,s in states.items()},'observation':asdict(o)}
        if self.trace:self.trace.write(json.dumps({'step':self.steps,'dt':dt,**self.report})+'\n')


TRIAL=Trial();TRIAL.reset();m.on_reset(TRIAL.reset);m.on_step(TRIAL.step)
def score(objects):return TRIAL.value
def success(objects):return TRIAL.value==1.


def demo_script(ctx):
    """Observe puck velocity and physically intercept; no puck state assignment."""
    import demokit as d
    L,R=ctx.left,ctx.right
    if ctx.mode=='none':yield from L.wait(4.);return
    if ctx.mode not in ('full','no_rescue','weak'):raise ValueError('full, no_rescue, weak, none')
    hover=np.array([.410,-.100,SURFACE+.055])
    if ctx.mode=='no_rescue':hover=np.array([.14,-.29,TOP+.18])
    yield from R.move(hover,grip=d.down(0),finger=d.FINGER_CLOSED,t=2.,label='watch side edge')
    start=ctx.pos('blue')+[-.063,0,.007]
    yield from L.move(start+[0,0,.10],grip=d.down(0),finger=d.FINGER_CLOSED,t=2.,label='approach blue')
    yield from L.move(start,t=1.2,label='lower shooting fingers')
    yield from L.servo(start,tol=.002,timeout=1.,label='align shot')
    def shoot():
        duration=float(os.environ.get('CURL_STROKE_TIME','.35'))
        if ctx.mode=='weak':duration=1.4
        yield from L.move(start+[.180,0,0],t=duration,label='glancing shot')
        yield from L.move(L.at()+[-.05,0,.12],t=.35,label='release')
        yield from L.move((.14,.29,TOP+.18),t=1.,label='park shooting arm')
    def rescue():
        if ctx.mode!='full':yield from R.wait(6.);return
        for _ in range(80):
            s=ctx.state('red')
            if s.lin_vel[1]<-.08:break
            yield
        else:return
        # Predict where the moving centre reaches the catch line from observed
        # position/velocity; speed ratio sets direction under isotropic friction.
        catch_y=-.100
        centre_y=catch_y+.045
        tau=max(0.,(centre_y-s.pos[1])/s.lin_vel[1])
        catch_x=float(np.clip(s.pos[0]+s.lin_vel[0]*tau,.34,.450))
        target=np.array([catch_x,catch_y,SURFACE+.018])
        print('RESCUE',s.pos.tolist(),s.lin_vel.tolist(),target.tolist(),flush=True)
        yield from R.move(target,t=.18,label='intercept runaway red')
        yield from R.servo(target,tol=.003,timeout=.4,label='hold blocking position')
        yield from R.wait(1.2)
        yield from R.move(R.at()+[-.10,-.06,.10],t=.7,label='release saved stone')
        yield from R.move((.14,-.29,TOP+.18),t=1.,label='park rescue arm')
    yield from ctx.together(shoot(),rescue())
    yield from L.wait(5.)
