"""The practice hand and forearm, the hand cone and the tendon force law. Pure Python and NumPy: the simulator is not
needed to import this file, so the scorer's tests and the build arithmetic run offline.

Hand frame (u, v, n), origin on the wrist axis: u along the fingers, v across the palm towards the thumb, n out of the
palm. The forearm lies palm up along world +y on a pillow, fingers pointing to -y, so with the wrist straight
(neutral) u = -y, v = +x and n = +z. Flexing the wrist or a finger turns u towards n, about the hand's -v axis.

The flexor tendon of each finger is a cord on the palm side: from the fingertip piece, over the PIP and MCP joints and
a pulley at the wrist, to the forearm anchor through a peak-hold gauge. Its stretch is

    e = E0 + R_MCP (THETA_M0 - theta_m) + R_PIP (THETA_P0 - theta_p) - R_WRIST phi

(phi, theta in radians from the authored clenched pose's angles), its tension K_FLEX * max(e, 0). It closes the MCP
and PIP with R_MCP T and R_PIP T and flexes the wrist with R_WRIST T. A light extensor cord on the back of each
finger, crossing the back of the wrist, does the opposite. Flexing the wrist slackens the flexor and stretches the
extensor (tenodesis), so the fingers fall open; straightening it closes them. The extensor acts mainly at the MCP
and crosses the back of the wrist on a 20 mm arm. Like a contracted hand, the fingers never straighten fully: the
MCPs stop at 20 degrees of flexion and the PIPs at 40.
"""

from __future__ import annotations

import math

import numpy as np

# -- placement (m, world; the table top is added by the task file) ------------------------------------------------------
PILLOW_C = (0.37, 0.10)          # the pillow's centre on the table
PILLOW_SIZE = (0.17, 0.34, 0.06)  # x, y, z
PILLOW_MASS = 0.45
FOREARM_MASS = 1.10              # the forearm, ballasted, strapped to the pillow
WRIST_XY = (0.37, 0.07)          # the wrist axis' x and y; it is HALF_T above the pillow
HALF_T = 0.012                   # half the palm's thickness: the back of the hand rests on the pillow

# -- the hand -------------------------------------------------------------------------------------------------------------
PALM_LEN = 0.095
KNUCKLE_U = 0.091                    # the knuckle roll across the palm's end
PALM_W_PROX, PALM_W = 0.070, 0.085   # across the palm, at the wrist and at the knuckles
PALM_MASS = 0.085                    # with the thumb
FINGERS = ("index", "middle", "ring", "little")
# per finger: v of its axis, u of its MCP, lengths of the proximal, middle and distal phalanges, radius
FINGER_V = (0.0315, 0.0105, -0.0105, -0.0315)
MCP_U = (0.094, 0.096, 0.093, 0.086)
MCP_N = 0.004
LENGTHS = ((0.042, 0.024, 0.020), (0.045, 0.027, 0.022), (0.043, 0.026, 0.021), (0.038, 0.021, 0.019))
RADII = (0.0085, 0.0085, 0.0080, 0.0075)
DIP_DEG = 35.0                       # the middle and distal phalanges are one printed piece, bent this much at the DIP
PROX_MASS, DIST_MASS = 0.012, 0.010
THUMB = ((0.045, 0.056, -0.002), (0.096, 0.054, 0.000), 0.0100)  # fixed, adducted along the index side (u, v, n)

MCP_MIN_DEG = 20.0                   # the contracted joints do not straighten past these (printed stops on the pins)
PIP_MIN_DEG = 40.0
# the authored (clenched, wrist neutral) pose: each finger's MCP and PIP flexion, degrees
CLENCH = ((104.0, 93.0), (102.0, 96.0), (104.0, 93.0), (101.0, 95.0))  # 1 degree short of the tips' contact with the palm

# -- tendons --------------------------------------------------------------------------------------------------------------
R_MCP, R_PIP = 0.008, 0.006          # flexor moment arms (m)
R_WRIST = 0.024                      # flexor wrist pulley radius (m)
E_CHECK = 0.0155                     # m: the check loop beside the silicone section goes taut at this stretch
K_CHECK = 2500.0                     # N/m, each flexor once its check loop is taut (the contracted tissue's end-stop)
K_FLEX = 300.0                       # N/m, each finger's flexor cord (a 60 mm length of 4 mm silicone cord)
T_REST = 1.0                         # N, each flexor's tension in the authored pose
RE_MCP, RE_PIP, RE_WRIST = 0.008, 0.003, 0.020   # extensor moment arms (m): mainly at the MCP and over the back of the wrist
K_EXT = 300.0                        # N/m, each extensor cord
TE_REST = 0.6                        # N, each extensor's tension in the authored pose
K_WRIST = 0.04                       # N m/rad, the wrist's return spring to neutral
GAUGE_LIMIT = 5.0                    # N: any finger's flexor gauge reading more than this is a zero

# -- the hand cone --------------------------------------------------------------------------------------------------------
CONE_LEN = 0.130
CONE_R_WIDE, CONE_R_NARROW = 0.025, 0.015
CONE_MASS = 0.040
CONE_SEAT = (0.080, -0.015)       # where the cone's middle lies across the palm (u, v) when fitted


def cone_radius(x: float) -> float:
    """The cone's radius at ``x`` along its axis (m from its middle, + towards the narrow end)."""
    return CONE_R_WIDE + (CONE_R_NARROW - CONE_R_WIDE) * (x / CONE_LEN + 0.5)


# -- frames ---------------------------------------------------------------------------------------------------------------

def rot_x(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], float)


def flex_rot(deg: float) -> np.ndarray:
    """The world rotation of flexing by ``deg`` (u = -y turns towards n = +z): about -x."""
    return rot_x(-math.radians(deg))


def quat_of(m: np.ndarray) -> tuple:
    w = math.sqrt(max(0.0, 1.0 + m[0, 0] + m[1, 1] + m[2, 2])) / 2
    x = math.copysign(math.sqrt(max(0.0, 1.0 + m[0, 0] - m[1, 1] - m[2, 2])) / 2, m[2, 1] - m[1, 2])
    y = math.copysign(math.sqrt(max(0.0, 1.0 - m[0, 0] + m[1, 1] - m[2, 2])) / 2, m[0, 2] - m[2, 0])
    z = math.copysign(math.sqrt(max(0.0, 1.0 - m[0, 0] - m[1, 1] + m[2, 2])) / 2, m[1, 0] - m[0, 1])
    n = math.sqrt(w * w + x * x + y * y + z * z)
    return (x / n, y / n, z / n, w / n)


def rot(q) -> np.ndarray:
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def uvn(u: float, v: float, n: float) -> np.ndarray:
    """A hand-frame point or vector as the neutral hand's world axes (no translation)."""
    return np.array([v, -u, n], float)


def flex_angle(r_parent: np.ndarray, r_child: np.ndarray) -> float:
    """The flexion (rad) of a child body against its parent, from their world rotations, both measured from the
    authored pose: positive turns u towards n (about the parent's -x)."""
    r = r_parent.T @ r_child
    return math.atan2(-r[2, 1], r[1, 1])


# -- the tendon force law -------------------------------------------------------------------------------------------------

def flexor_tension(e):
    """A flexor's tension (N) at stretch ``e`` (m): the silicone section alone up to E_CHECK, then the check loop too."""
    e = np.asarray(e, float)
    return K_FLEX * np.clip(e, 0.0, E_CHECK) + K_CHECK * np.maximum(e - E_CHECK, 0.0)


def tendons(phi: float, tm, tp):
    """Tensions and torques for wrist flexion ``phi`` and each finger's MCP and PIP flexion (all rad, from the
    authored pose). Returns (flexor tensions[4], extensor tensions[4], wrist torque, MCP torques[4], PIP torques[4]);
    torques are flexing-positive, N m. The wrist torque includes the return spring."""
    tm, tp = np.asarray(tm, float), np.asarray(tp, float)
    e = T_REST / K_FLEX - R_MCP * tm - R_PIP * tp - R_WRIST * phi
    s = TE_REST / K_EXT + RE_MCP * tm + RE_PIP * tp + RE_WRIST * phi
    tf = flexor_tension(e)
    te = K_EXT * np.maximum(s, 0.0)
    wrist = R_WRIST * tf.sum() - RE_WRIST * te.sum() - K_WRIST * (phi)
    mcp = R_MCP * tf - RE_MCP * te
    pip = R_PIP * tf - RE_PIP * te
    return tf, te, wrist, mcp, pip


# -- shapes ---------------------------------------------------------------------------------------------------------------

def _capsule_mesh(p0, p1, r: float, rings: int = 6, segs: int = 14):
    """Points, faces and normals of a capsule from ``p0`` to ``p1`` (body frame)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    length = float(np.linalg.norm(d))
    a = d / length
    t = np.array([1.0, 0, 0]) if abs(a[0]) < 0.9 else np.array([0, 1.0, 0])
    b1 = np.cross(a, t)
    b1 /= np.linalg.norm(b1)
    b2 = np.cross(a, b1)
    pts, nrm = [], []
    lat = [(-math.pi / 2 + math.pi / 2 * i / rings, 0) for i in range(rings + 1)] + \
          [(math.pi / 2 * i / rings, 1) for i in range(rings + 1)]
    for th, end in lat:
        c = p1 if end else p0
        for k in range(segs):
            ph = 2 * math.pi * k / segs
            n = math.cos(th) * (math.cos(ph) * b1 + math.sin(ph) * b2) + math.sin(th) * a
            pts.append(c + r * n)
            nrm.append(n)
    faces = []
    rows = len(lat)
    for i in range(rows - 1):
        for k in range(segs):
            a0, a1 = i * segs + k, i * segs + (k + 1) % segs
            b0, b1_ = a0 + segs, a1 + segs
            faces += [(a0, b0, b1_), (a0, b1_, a1)]
    return np.array(pts), faces, np.array(nrm)


def capsule(bk, p0, p1, r: float, color, collide: bool = True) -> list:
    """A capsule as a bodykit convex collider plus a smooth visual mesh."""
    pts, faces, nrm = _capsule_mesh(p0, p1, r)
    c = tuple(((np.asarray(p0) + np.asarray(p1)) / 2).tolist())
    P = tuple(tuple(float(x) for x in p) for p in pts)
    F = tuple(tuple(int(i) for i in f) for f in faces)
    out = [bk.MeshShape(c, P, F, color=color, normals=tuple(tuple(float(x) for x in n) for n in nrm), roughness=0.6)]
    if collide:
        out.append(bk.ConvexShape(c, P, F))
    return out


def cone_mesh(segs: int = 28):
    """The cone along body x, wide end at -x: points, faces and normals (sides, then the two end caps)."""
    half = CONE_LEN / 2
    slope = (CONE_R_WIDE - CONE_R_NARROW) / CONE_LEN
    pts, nrm, faces = [], [], []
    for x, r in ((-half, CONE_R_WIDE), (half, CONE_R_NARROW)):
        for k in range(segs):
            ph = 2 * math.pi * k / segs
            pts.append((x, r * math.cos(ph), r * math.sin(ph)))
            n = np.array([slope, math.cos(ph), math.sin(ph)])
            nrm.append(tuple(n / np.linalg.norm(n)))
    for k in range(segs):
        a, b = k, (k + 1) % segs
        faces += [(a, b, b + segs), (a, b + segs, a + segs)]
    for x, r, sgn in ((-half, CONE_R_WIDE, -1.0), (half, CONE_R_NARROW, 1.0)):  # flat caps, their own vertices
        base = len(pts)
        pts.append((x, 0.0, 0.0))
        nrm.append((sgn, 0.0, 0.0))
        for k in range(segs):
            ph = 2 * math.pi * k / segs
            pts.append((x, 0.97 * r * math.cos(ph), 0.97 * r * math.sin(ph)))
            nrm.append((sgn, 0.0, 0.0))
        for k in range(segs):
            a, b = base + 1 + k, base + 1 + (k + 1) % segs
            faces.append((base, b, a) if sgn < 0 else (base, a, b))
    return pts, faces, nrm


def finger_segments(i: int, tm_deg: float, tp_deg: float):
    """Hand-frame (u, n) points MCP, PIP, DIP and tip of finger ``i`` at these flexions (degrees, absolute)."""
    l1, l2, l3 = LENGTHS[i]
    a1, a2 = math.radians(tm_deg), math.radians(tm_deg + tp_deg)
    a3 = a2 + math.radians(DIP_DEG)
    p0 = np.array([MCP_U[i], MCP_N])
    p1 = p0 + l1 * np.array([math.cos(a1), math.sin(a1)])
    p2 = p1 + l2 * np.array([math.cos(a2), math.sin(a2)])
    p3 = p2 + l3 * np.array([math.cos(a3), math.sin(a3)])
    return p0, p1, p2, p3


def distal_local(i: int):
    """Finger ``i``'s middle-distal piece in its own body frame (origin on the PIP axis, unrotated: the piece points
    along -y with the DIP bend towards +z): the DIP and the fingertip's centre."""
    _, l2, l3 = LENGTHS[i]
    dip = np.array([0.0, -l2, 0.0])
    b = math.radians(DIP_DEG)
    tip = dip + l3 * np.array([0.0, -math.cos(b), math.sin(b)])
    return dip, tip
