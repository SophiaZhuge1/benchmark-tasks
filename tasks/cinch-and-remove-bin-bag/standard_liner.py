"""Dimensions for the ordinary-liner development scene, in SI units.

The commercial reference is Brabantia PerfectFit Code A, current SKU 137600:
270 x 290 mm laid flat. The Code A family data sheet for article 137488
 reports PE 15--25 micrometres; actual sample thickness remains to measure.
Tape width, friction and the idealised expanded shape remain assumptions to
measure on a purchased sample. They are not manufacturer specifications.
"""
import numpy as np

BAG_RADIUS = .075
BAG_HEIGHT = .215
BAG_ORIGIN = np.array([.22, 0., .768])
FILM_THICKNESS = .000020
BIN_INNER_RADIUS = .082
BIN_WALL_HEIGHT = .150
HEM_COUNT = 20
TAPE_LINK_COUNT = 80
TAPE_LENGTH = .540
TAPE_WIDTH = .008
TAPE_COLLISION_THICKNESS = .0005
TAPE_MASS = .0012
HEM_MASS = .00005
INSTRUCTION = ('Pull the liner\'s built-in drawtapes, tie them to secure the mouth, '
               'then lift the bag out and place it on the table without spilling.')

def drawtape_nodes():
    """Closed, initially unknotted tape with two small exposed bights.

    Its whole length, including exposed bights, is the bag's flat perimeter.
    The old scene incorrectly added long external cords to an open full hem.
    """
    from scipy.optimize import brentq
    a = np.linspace(0., 2*np.pi, 4001)
    def curve(amplitude):
        bumps = np.exp(-((np.cos(a))/.12)**2)
        r = BAG_RADIUS + amplitude*bumps
        return np.c_[r*np.cos(a), r*np.sin(a), np.zeros(len(a))]
    def length(p):
        return np.linalg.norm(np.diff(p,axis=0),axis=1).sum()
    amplitude = brentq(lambda v:length(curve(v))-TAPE_LENGTH,0.,.1)
    p = curve(amplitude)
    cumulative = np.r_[0.,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    q = np.array([np.interp(np.arange(TAPE_LINK_COUNT)*TAPE_LENGTH/TAPE_LINK_COUNT,cumulative,p[:,k]) for k in range(3)]).T
    return q+BAG_ORIGIN+[0.,0.,BAG_HEIGHT]

def tape_links():
    from scipy.spatial.transform import Rotation
    p=drawtape_nodes();q=np.roll(p,-1,axis=0)
    delta=q-p;length=np.linalg.norm(delta,axis=1);x=delta/length[:,None]
    z=np.tile([0.,0.,1.],(len(p),1));y=np.cross(z,x)
    rotations=Rotation.from_matrix(np.stack([x,y,z],axis=2)).as_quat()
    return (p+q)/2,length,rotations

def hem_positions():
    a=np.arange(HEM_COUNT)*2*np.pi/HEM_COUNT
    return BAG_ORIGIN+np.c_[BAG_RADIUS*np.cos(a),BAG_RADIUS*np.sin(a),np.full(HEM_COUNT,BAG_HEIGHT)]

def bight_indices():
    p,_,_=tape_links()
    return [int(np.argmax(p[:,1])),int(np.argmin(p[:,1]))]
