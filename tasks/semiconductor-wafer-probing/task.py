"""Lift, index and re-contact a semiconductor wafer without lateral probe drag."""
import pathlib, sys
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import mechkit as m
from labels import label
from probe_model import ProbeModel, CONTACT, TARGET, CLEARANCE
from yam_arena.task_file import TABLE_TOP

SCENE = 'station'
TOP = TABLE_TOP[SCENE]
SCORE_OVER = 'end'
SUCCESS_HOLD_S = 1.
INSTRUCTION = 'Move the semiconductor wafer to the next marked test position without dragging the probes across its surface.'
ORIGIN = np.array([.280, -.055, TOP])
WAFER_Z = .052
LIFT_HANDLE = np.array([.245, .140, TOP + .125])
STAGE_HANDLE = np.array([.280, -.205, TOP + .080])
LOOKS = {k: m.Look(color=m.rgb(*v), roughness=.4) for k, v in {
    'steel':(.55,.61,.67), 'black':(.045,.055,.075), 'wafer':(.16,.13,.32),
    'die':(.29,.32,.49), 'gold':(.92,.68,.20), 'blue':(.08,.40,.95),
    'amber':(1.,.58,.03), 'green':(.08,.88,.24), 'red':(.95,.03,.03),
    'white':(.92,.94,.97)}.items()}
for c in ('green','red','blue','amber'):
    LOOKS[c+'_lit'] = m.Look(color=LOOKS[c].color, emissive=tuple(v*.5 for v in LOOKS[c].color), roughness=.25)


def stage():
    parts = [('carriage',m.box((.180,.180,.020),(0,0,.025)),'black'),
             ('chuck',m.cylinder(.087,.016,(0,0,.043)),'steel'),
             ('wafer',m.cylinder(.082,.002,(0,0,.051)),'wafer'),
             ('handle_arm',m.box((.022,.085,.016),(0,-.112,.034)),'steel'),
             ('handle',m.box((.028,.024,.074),(0,-.150,.068)),'blue')]
    for i in range(-3,4):
        for j in range(-3,4):
            if (i*.020)**2+(j*.020)**2 < .070**2:
                parts.append((f'die_{i+3}_{j+3}',m.box((.017,.017,.0004),(i*.020,j*.020,.0522)),'die'))
    for site,x,color in [('A',.030,'amber'),('B',-.030,'blue')]:
        for j,y in enumerate((-.018,.018)):
            parts.append((site+str(j),m.box((.012,.012,.0006),(x,y,.0525)),'gold'))
            for k,dy in enumerate((-.008,.008)):
                parts.append((site+str(j)+str(k),m.box((.017,.0015,.0008),(x,y+dy,.0526)),color))
        parts.append((site+'_label',label(site,(x,.041,.0528),.0013),color))
    # A permanently clamped surrogate wafer rides with the carriage; no wafer picking.
    cols=[m.col_box('carriage_c',(.180,.180,.020),(0,0,.025)),
          m.col_cylinder('chuck_c',.087,.016,(0,0,.043)),
          m.col_cylinder('wafer_c',.082,.002,(0,0,.051)),
          m.col_box('handle_c',(.028,.024,.074),(0,-.150,.068)),
          m.col_box('handle_arm_c',(.022,.085,.016),(0,-.112,.034))]
    rail=m.slider('carriage','X',0.,.070,parts,cols,mass=.25,friction=1.,damping=3.)
    frame=[('base',m.box((.280,.208,.012),(.030,0,.006)),'steel'),
           ('track',m.box((.250,.012,.009),(.030,-.101,.017)),'black')]
    for name,x,c in [('A',0.,'amber'),('B',TARGET,'blue')]:
        frame += [(name+'_mark',m.box((.002,.024,.002),(x,-.110,.019)),c),
                  (name+'_rail_label',label(name,(x,-.130,.014),.0013),c)]
    frame += [('arrow',m.prism([(.008,-.117),(.045,-.117),(.045,-.122),(.055,-.114),(.045,-.106),(.045,-.111),(.008,-.111)],.013,.014),'white')]
    return m.mechanism('wafer_stage',ORIGIN,[rail],LOOKS,frame_parts=frame,
        frame_colliders=[m.col_box('base_c',(.280,.208,.012),(.030,0,.006))])


def probes():
    # Probes at x=+30 mm contact site A initially; moving the chuck +60 mm brings B beneath them.
    offset = LIFT_HANDLE - ORIGIN
    handle=m.box((.028,.024,.056),offset+[0,0,-.006])
    beam=m.box((.024,.215,.014),(.030,.085,.099))
    bridge=m.box((.085,.024,.014),(-.0025,.195,.099))
    p=[('handle',handle,'amber'),('beam',beam,'steel'),('bridge',bridge,'steel')]
    c=[m.col_hull('handle_c',handle),m.col_hull('beam_c',beam),m.col_hull('bridge_c',bridge)]
    for i,y in enumerate((-.018,.018)):
        tip=m.cylinder(.0025,.040,(.030,y,WAFER_Z+.0202))
        p.append((f'needle{i}',tip,'gold'));c.append(m.col_hull(f'needle_c{i}',tip))
    link=m.slider('lift','Z',0.,.060,p,c,mass=.10,spring=25.,damping=1.,friction=.02)
    frame=[('foot',m.box((.085,.060,.018),(-.035,.195,.009)),'black'),
           ('column',m.box((.012,.012,.165),(-.070,.195,.091)),'steel')]
    return m.mechanism('probe_assembly',ORIGIN,[link],LOOKS,frame_parts=frame,
        frame_colliders=[m.col_box('foot_c',(.085,.060,.018),(-.035,.195,.009)),
                         m.col_box('column_c',(.012,.012,.165),(-.070,.195,.091))])


def panel():
    p=[('base',m.box((.205,.100,.045),(0,0,.0225)),'black')]
    for name,x,c in [('LIFT',-.073,'blue'),('PAD',-.025,'amber'),('FAIL',.025,'red'),('READY',.075,'green')]:
        p.extend([(name+'_off',m.cylinder(.010,.002,(x,0,.046)),'steel'),
                  (name,m.cylinder(.009,.003,(x,0,.047)),c+'_lit',True),
                  (name+'_label',label(name,(x,.027,.046),.0011),'white')])
    return m.fixed('status',(.485,.180,TOP),p,[m.col_box('base_c',(.205,.100,.045),(0,0,.0225))],LOOKS)


OBJECTS=[stage(),probes(),panel()]


class Trial:
    def reset(self,env=None):
        self.model=ProbeModel();self.report={};self.steps=0
    def step(self,env):
        self.steps+=1
        x=float(m.state(env,'wafer_stage').joint('carriage'))
        lift=float(m.state(env,'probe_assembly').joint('lift'))
        fingers=m.fingertips(env)
        handles=(STAGE_HANDLE+[x,0,0],LIFT_HANDLE+[0,0,lift])
        released=all(np.min(np.linalg.norm(fingers-h,axis=1))>.050 for h in handles)
        self.model.step(float(env.unwrapped.step_dt),x,lift,bool(released))
        for name,on in [('LIFT',lift>=CLEARANCE),('PAD',self.model.contact),('FAIL',self.model.damaged),('READY',self.model.value==1.)]:
            m.set_visible(f'{m.ENV_PATH}/status/visual/{name}',on)
        self.report=dict(score=self.model.value,time=round(self.model.t,3),stage_mm=round(x*1000,4),
            lift_mm=round(lift*1000,4),contact=self.model.contact,aligned=self.model.aligned,
            scrape_mm=round(self.model.scrape_m*1000,6),damaged=self.model.damaged,
            first_damage=self.model.first_damage,lifted=self.model.lifted,released=bool(released),
            final_dwell=round(self.model.final_dwell,3))
        if self.steps%100==0: print('[wafer]',self.report,flush=True)


TRIAL=Trial();TRIAL.reset();m.on_reset(TRIAL.reset);m.on_step(TRIAL.step)
def score(objects): return TRIAL.model.value
def success(objects): return score(objects)==1.


def demo_script(ctx):
    import demokit as d
    L,R=ctx.left,ctx.right
    x=lambda:float(m.state(ctx.emb._env,'wafer_stage').joint('carriage'))
    z=lambda:float(m.state(ctx.emb._env,'probe_assembly').joint('lift'))
    if ctx.mode=='none': yield from R.wait(3);return
    # Staged approaches keep the arms in their own half of the station.
    if ctx.mode!='drag':
        yield from L.pick(lambda:LIFT_HANDLE+[0,0,z()],0.,width=.024,grip=d.down(0),above=.045,lift=0.,label='hold probe lift')
        yield from L.move(L.at()+[0,0,.040-z()],t=1.3,label='retract probes')
        yield from L.servo(L.tcp()+[0,0,.040-z()],timeout=1.,label='confirm clearance')
        yield from L.wait(.35)
    yield from R.pick(lambda:STAGE_HANDLE+[x(),0,0],0.,width=.024,grip=d.down(0),above=.050,lift=0.,label='grasp wafer stage')
    if ctx.mode=='early_release':
        yield from L.open();yield from L.move(L.at()+[0,0,.060],t=.7,label='release lift too early')
        yield from L.wait(1.)
    yield from R.move(R.at()+[TARGET-x(),0,0],t=2.,label='index wafer to B')
    for _ in range(2):
        yield from R.servo(R.tcp()+[TARGET-x(),0,0],tol=.001,timeout=1.2,label='align next pad')
    yield from R.open()
    yield from R.move(R.at()+[0,-.070,.060],t=.7,label='clear stage')
    yield from R.wait(.4)
    if ctx.mode not in ('drag','early_release','leave_lifted'):
        yield from L.move(L.at()+[0,0,.0002-z()],t=1.8,label='lower probes onto B')
        yield from L.open()
        yield from L.move(L.at()+[0,.060,.070],t=.8,label='clear probe handle')
    yield from R.wait(2.)
