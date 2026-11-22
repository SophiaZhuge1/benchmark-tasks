"""toiletkit: a two-piece toilet tank (lid off, water off) and a new rubber flapper with its bead chain, as two PhysX
articulations, for a yam_arena task file.

Frames. The tank frame T: origin on the tank's interior floor under the flush valve's centre, x toward the tank's front
(away from the robot: the tank stands with its back toward the robot), y to the robot's left, z up. The flapper frame F:
origin on the hinge line (the two pegs' common axis) at y 0, axes as T's when the flapper is seated.

- ``Toilet`` (fixed base): the tank body carries every static part as colliders (walls, floor, flush valve and seat,
  overflow tube and its two ear pegs, fill valve with float cup, refill tube) and the trip lever, a revolute link on
  the handle's shaft through the front wall, with a return spring onto its rest stop. A chain clip hangs from the
  lever's middle hole.
- ``Flapper`` (free): the seal disk with its float cup (the root), two ears on sprung hinges (the rubber arms bend
  sideways), each ear a tab with a square hole made of four bars, so that a peg holds an ear only by passing through
  its hole; and the stainless bead chain, beads on ball joints from the lug at the disk's front edge.

Chain clip: for each bead from ``CLIP_FROM`` on, a point joint (free rotations, stiff translational springs) between the
bead and the clip's slot is authored disabled; :class:`ClipCatcher` switches one on when a bead lies in the slot and
the chain is let go there (the slot is a 2 mm gap that holds the wire between two beads). Pure Python at import time.
"""

from __future__ import annotations

import importlib.abc
import importlib.util
import math
import sys
from dataclasses import dataclass

import numpy as np
from yam_arena.task_file import Box, ObjectState

# -- tank geometry (T frame, m) ---------------------------------------------------------------------------------------
IN_X = (-0.107, 0.080)            # interior: back wall (robot side) and front wall inner faces
IN_Y = 0.205                      # interior half-width
WALL = 0.010
DEPTH = 0.245                     # interior floor to rim
BOTTOM = 0.012                    # the tank's bottom slab
LID_SIZE = (0.46, 0.20, 0.022)   # the tank's lid, lying on the table
LID_CENTRE_T = (-0.020, -0.43, -0.050 + 0.011)
RAIL_H = 0.038                    # two 2x4 rails under the tank, laid flat (38 mm)
VALVE_R, VALVE_TOP = 0.041, 0.018  # flush valve body (flange and nut collar) inside the tank
SEAT_R, SEAT_TOP, SEAT_IN = 0.034, 0.030, 0.025  # the valve seat ring: outer radius, top, opening radius
TUBE_X, TUBE_R, TUBE_TOP = -0.055, 0.0160, 0.215  # overflow tube
PEG_Z = 0.055                     # the pegs' axis height (T)
PEG_R = 0.0028
PEG_CORE_R = 0.0015                # the peg's collider (the real pin is 5.6 mm; see EarCatcher)
EAR_CAPTURE_R = 0.004             # an ear's hole centre within this of the peg's axis, pushed onto the peg, is held on it
EAR_PUSH_N = 0.5                  # ... pushed home: the tab bears on the peg's boss with this
                                  # force (N, the physics engine's contact force along the peg) for 2 control steps
BOSS_Y, PEG_TIP_Y = 0.031, 0.044  # peg boss (r 4.5 mm) from the tube out to |y| 0.031; the peg on to |y| 0.044
FILL_XY, FILL_R, FILL_TOP = (0.040, 0.172), 0.016, 0.230  # fill valve shank (tank's own right = robot's left)
FLOAT_R, FLOAT_Z = 0.030, (0.095, 0.150)
REFILL_FROM = (0.040, 0.150, 0.236)  # the fill valve's refill nipple (T)
REFILL_TO = (-0.053, 0.004, 0.223)    # the refill tube's clip in the overflow tube's mouth (T)
REFILL_SEGS, REFILL_SAG = 9, 0.022     # vinyl tube in 9 sprung links, arching 22 mm above the straight line
LEVER_PIVOT = (0.071, 0.150, 0.200)  # the arm's pivot (on the handle shaft, which runs along x through the front wall)
LEVER_DIR = -1.0                  # the arm runs from the pivot toward -y (a right-hand trip lever)
LEVER_LEN = 0.185                 # arm length
LEVER_HOLES = tuple(LEVER_DIR * h for h in (0.140, 0.155, 0.170))  # holes along the arm (signed y from the pivot)
CLIP_HOLE = 1                     # the clip hangs from the middle hole
CLIP_DROP = 0.013                 # the clip's slot is this far below the arm's hole
CLIP_BACK = 0.010                 # ... and this far behind it (toward the tank's back): the clip is a C-hook
# -- flapper geometry (F frame, m) ------------------------------------------------------------------------------------
HINGE_T = np.array((TUBE_X, 0.0, PEG_Z))  # F origin in T when the ears are on the pegs
DISK_X, DISK_R, DISK_H = 0.055, 0.036, 0.010  # disk centre (F x), radius, thickness (its bottom at F z -0.010)
CUP_R, CUP_H = 0.020, 0.012       # the float cup on top
DISK_TOP = -0.015                 # the seal's top face, 15 mm below the hinge line (the ears ride above the seal)
EAR_Y = 0.0345                    # ear tab centre |y| (seated, on its peg, tab 3 mm thick)
EAR_T = 0.006
EAR_W = 0.018                     # tab along x
EAR_Z = (-0.010, 0.026)           # tab bottom and top (F z)
HOLE = 0.0085                     # square hole in the tab, centred on the hinge line
ARM_ROOT_X = 0.045                # the ear arm's hinge (spread) at the disk's edge
LUG = np.array((0.095, 0.0, -0.013))  # chain lug (F)
BEAD_PITCH, BEAD_R = 0.006, 0.00225
BEAD_COL_R = 0.0027                # the beads' colliders (0.9 mm gaps between them, so a pinch holds anywhere)
CLIP_FROM = 16                    # beads from here on can be clipped


def T_to_F(p_t):
    return np.asarray(p_t, float) - HINGE_T


def lever_up_deg(deg: float) -> float:
    """The lever joint's angle that lifts the arm's end by ``deg`` (turning about +x lifts an arm running to +y and
    lowers one running to -y)."""
    return LEVER_DIR * deg


def lever_hole_T(k: int = CLIP_HOLE) -> np.ndarray:
    return np.array((LEVER_PIVOT[0], LEVER_PIVOT[1] + LEVER_HOLES[k], LEVER_PIVOT[2]))


def clip_slot_T() -> np.ndarray:
    return lever_hole_T() + np.array((-CLIP_BACK, 0.0, -CLIP_DROP))


# -- small maths -------------------------------------------------------------------------------------------------------

def rotmat(q) -> np.ndarray:
    q = np.asarray(q, float)
    x, y, z, w = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    return np.stack([np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)], -1),
                     np.stack([2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)], -1),
                     np.stack([2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)], -1)], -2)


def quat_axis(axis, angle) -> tuple:
    a = np.asarray(axis, float) / np.linalg.norm(axis)
    s = math.sin(angle / 2)
    return (float(a[0] * s), float(a[1] * s), float(a[2] * s), math.cos(angle / 2))


def quat_from_matrix(m) -> tuple:
    m = np.asarray(m, float)
    t = np.trace(m)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        w, x, y, z = 0.25 * s, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        w, x, y, z = (m[2, 1] - m[1, 2]) / s, 0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        w, x, y, z = (m[0, 2] - m[2, 0]) / s, (m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        w, x, y, z = (m[1, 0] - m[0, 1]) / s, (m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s
    return (float(x), float(y), float(z), float(w))


# -- specs --------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Toilet(Box):
    """``pos``: the T frame's origin in the world (no rotation)."""

    lever_k: float = 0.15          # N m/rad: the handle's return spring, preloaded onto the rest stop
    lever_preload_deg: float = 10.0
    lever_c: float = 0.004
    lever_mass: float = 0.030
    press_deg: float = 40.0        # the scorer's full press of the handle: the trip arm turns 40 deg (the clip rises ~10 cm)
    refill_mass: float = 0.015     # 1/4 in vinyl refill tube, about 17 cm
    refill_k: float = 0.10         # N m/rad per link: the tube's bending springs toward its rest shape
    refill_c: float = 0.002
    friction: float = 0.6
    peg_friction: float = 0.5


@dataclass(frozen=True)
class Flapper(Box):
    """``pos``: the F frame's origin in the world at the start; ``yaw`` turns the flapper about the vertical."""

    start_yaw: float = 0.0
    disk_mass: float = 0.055
    ear_mass: float = 0.008
    ear_k: float = 0.06            # N m/rad: an ear arm bending sideways (about 1 N to spread an ear 13 mm)
    ear_c: float = 0.002
    ear_limit_deg: float = 40.0
    n_beads: int = 42              # 25 cm of #6 bead chain
    bead_mass: float = 0.0015      # per bead; heavier than the real 0.3 g, for a stable solver
    bead_c: float = 2e-5           # ball-joint damping (N m s/rad)
    chain_path: tuple = ()         # the chain's resting line at the start after the lug (world points)
    chain_start_turn: float = 0.0
    rubber_friction: float = 1.0
    tab_friction: float = 1.2      # the ear tab's rubber in a pinch
    tab_torsion: float = 0.008     # m: torsional friction patch where the pads pinch an ear tab
    peg_k: float = 600.0           # N/m: an ear's hole held round its peg (rubber round a 5.6 mm peg)
    peg_slide_k: float = 150.0     # N/m: the ear along its peg, back toward the boss
    peg_c: float = 3.0
    peg_rot_k: float = 0.3         # N m/rad: the hole's 6 mm thickness keeps the tab square to the peg
    peg_rot_c: float = 0.005
    open_limit_deg: float = 66.0   # it opens until its float cup rests against the overflow tube
    clip_k: float = 500.0          # N/m: the bead held in the clip's slot
    clip_c: float = 1.5
    contact_offset: float = 0.0008
    solver_pos_iters: int = 48


SEG_BEADS = 2  # beads per rigid chain link (one link body carries two beads; the ball joints are between pairs)
SEG_LEN = SEG_BEADS * BEAD_PITCH


def seg_name(k: int) -> str:
    return f"seg_{k:02d}"


def bead_offset(b: int) -> float:
    """Bead b's centre along its segment's chain axis, from the segment's centre."""
    return ((b % SEG_BEADS) - (SEG_BEADS - 1) / 2) * BEAD_PITCH


def bead_pos(raw: dict, b: int, dirs) -> np.ndarray:
    """World position of bead b from the raw state (its segment's pose) and the segments' directions in their own
    frames (``chain_dirs_local``)."""
    k = b // SEG_BEADS
    p, q = raw["pos"][seg_name(k)], raw["quat"][seg_name(k)]
    return p + rotmat(q) @ (np.asarray(dirs[k]) * bead_offset(b))


def _yaw_R(spec) -> np.ndarray:
    c, s = math.cos(spec.start_yaw), math.sin(spec.start_yaw)
    return np.array(((c, -s, 0), (s, c, 0), (0, 0, 1)))


def chain_chords(spec) -> np.ndarray:
    """The chain's segment ends at the start (world): points SEG_LEN apart along the polyline that starts at the lug
    and continues through ``spec.chain_path``."""
    lug = np.asarray(spec.pos, float) + _yaw_R(spec) @ LUG
    pts = [lug] + [np.asarray(p, float) for p in spec.chain_path]
    cum = np.concatenate([[0.0], np.cumsum([np.linalg.norm(b - a) for a, b in zip(pts[:-1], pts[1:])])])
    n = spec.n_beads // SEG_BEADS
    out = []
    for k in range(n + 1):
        t = min(k * SEG_LEN, cum[-1] - 1e-9)
        i = int(np.searchsorted(cum, t, side="right") - 1)
        out.append(pts[i] + (pts[i + 1] - pts[i]) * (t - cum[i]) / (cum[i + 1] - cum[i]))
    return np.array(out)


def chain_dirs_local(spec) -> list:
    """Each segment's direction at the start in the flapper bodies' own frame (every link keeps the disk's
    orientation at the start; the joints carry the bends)."""
    e = chain_chords(spec)
    R = _yaw_R(spec)
    return [R.T @ ((e[k + 1] - e[k]) / np.linalg.norm(e[k + 1] - e[k])) for k in range(len(e) - 1)]


def flapper_start(spec: Flapper):
    """(name -> (world pos, quat_xyzw)) for every body of the flapper at the start."""
    R = _yaw_R(spec)
    q = quat_axis((0, 0, 1), spec.start_yaw)
    o = np.asarray(spec.pos, float)
    out = {"disk": (o + R @ np.array((DISK_X, 0, 0)), q)}
    for tag, sgn in (("l", 1), ("r", -1)):
        out[f"ear_{tag}"] = (o + R @ np.array((ARM_ROOT_X, sgn * EAR_Y, 0)), q)
    e = chain_chords(spec)
    for k in range(spec.n_beads // SEG_BEADS):
        out[seg_name(k)] = ((e[k] + e[k + 1]) / 2, q)
    return out


# -- spawning -----------------------------------------------------------------------------------------------------------

_SPECS: dict = {}
PATHS: dict = {}


IDENT_Q = (0.0, 0.0, 0.0, 1.0)


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)


def qinv(a):
    return (-a[0], -a[1], -a[2], a[3])


class _Builder:
    def __init__(self, stage, root: str, friction: float):
        import isaaclab.sim as sim_utils
        self.stage, self.root, self.looks = stage, root, {}
        self.sim_utils = sim_utils
        self.phys = self.material("physics", friction)

    def material(self, name, friction, combine="average"):
        p = f"{self.root}/Looks/{name}"
        m = self.sim_utils.RigidBodyMaterialCfg(static_friction=friction, dynamic_friction=friction, restitution=0.0,
                                                friction_combine_mode=combine)
        m.func(p, m)
        return p

    def look(self, name, color, rough=0.5, metal=0.0, opacity=None):
        if name not in self.looks:
            from yam_arena.station import linear_rgb
            p = f"{self.root}/Looks/{name}"
            kw = dict(diffuse_color=linear_rgb(color), roughness=rough, metallic=metal)
            if opacity is not None:
                kw["opacity"] = opacity
            m = self.sim_utils.PreviewSurfaceCfg(**kw)
            m.func(p, m)
            self.looks[name] = p
        return self.looks[name]

    def body(self, path, pos, quat_xyzw, mass, inertia=None, maxv=None, report=False, com=None):
        from pxr import Gf, PhysxSchema, UsdGeom, UsdPhysics
        xf = UsdGeom.Xform.Define(self.stage, path)
        xf.AddTranslateOp(precision=UsdGeom.XformOp.PrecisionDouble).Set(Gf.Vec3d(*map(float, pos)))
        x, y, z, w = quat_xyzw
        xf.AddOrientOp(precision=UsdGeom.XformOp.PrecisionDouble).Set(Gf.Quatd(w, x, y, z))
        prim = xf.GetPrim()
        UsdPhysics.RigidBodyAPI.Apply(prim)
        ma = UsdPhysics.MassAPI.Apply(prim)
        ma.CreateMassAttr(float(mass))
        if inertia is not None:
            ma.CreateDiagonalInertiaAttr(Gf.Vec3f(*map(float, inertia)))
        if com is not None:
            ma.CreateCenterOfMassAttr(Gf.Vec3f(*map(float, com)))
        rb = PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
        rb.CreateMaxDepenetrationVelocityAttr(0.5)
        rb.CreateSleepThresholdAttr(0.0)
        rb.CreateLinearDampingAttr(0.5 if mass < 0.005 else 0.05)
        rb.CreateAngularDampingAttr(2.0 if mass < 0.005 else 0.2)
        if maxv is not None:
            rb.CreateMaxLinearVelocityAttr(maxv)
        if report:
            PhysxSchema.PhysxContactReportAPI.Apply(prim).CreateThresholdAttr(0.0)
        return prim

    def collider(self, prim, offset=0.001, material=None, torsion=None):
        from isaaclab.sim.utils import bind_physics_material
        from pxr import PhysxSchema, UsdPhysics
        UsdPhysics.CollisionAPI.Apply(prim)
        cp = PhysxSchema.PhysxCollisionAPI.Apply(prim)
        cp.CreateContactOffsetAttr(float(offset))
        cp.CreateRestOffsetAttr(0.0)
        if torsion:  # the pads resist twisting a part held in a pinch
            cp.CreateTorsionalPatchRadiusAttr(float(torsion))
            cp.CreateMinTorsionalPatchRadiusAttr(0.8 * float(torsion))
        bind_physics_material(str(prim.GetPath()), material or self.phys, stage=self.stage)

    def _finish(self, g, path, look, collide, offset, material, torsion=None):
        from isaaclab.sim.utils import bind_visual_material
        from pxr import UsdGeom
        if collide:
            self.collider(g.GetPrim(), offset, material, torsion)
        if look:
            bind_visual_material(path, look, stage=self.stage)
        else:
            UsdGeom.Imageable(g.GetPrim()).CreatePurposeAttr("guide")
        return g

    def box(self, path, centre, size, look, quat_xyzw=None, collide=True, offset=0.001, material=None, torsion=None):
        from pxr import Gf, UsdGeom
        g = UsdGeom.Cube.Define(self.stage, path)
        g.CreateSizeAttr(1.0)
        g.AddTranslateOp().Set(Gf.Vec3d(*map(float, centre)))
        if quat_xyzw is not None:
            x, y, z, w = quat_xyzw
            g.AddOrientOp().Set(Gf.Quatf(float(w), float(x), float(y), float(z)))
        g.AddScaleOp().Set(Gf.Vec3f(*map(float, size)))
        return self._finish(g, path, look, collide, offset, material, torsion)

    def cyl(self, path, centre, r, h, axis, look, collide=True, offset=0.001, material=None, capsule=False):
        from pxr import Gf, UsdGeom
        g = (UsdGeom.Capsule if capsule else UsdGeom.Cylinder).Define(self.stage, path)
        g.CreateRadiusAttr(float(r))
        g.CreateHeightAttr(float(h))
        g.CreateAxisAttr(axis)
        g.AddTranslateOp().Set(Gf.Vec3d(*map(float, centre)))
        return self._finish(g, path, look, collide, offset, material)

    def sphere(self, path, centre, r, look, collide=True, offset=0.001, material=None):
        from pxr import Gf, UsdGeom
        g = UsdGeom.Sphere.Define(self.stage, path)
        g.CreateRadiusAttr(float(r))
        g.AddTranslateOp().Set(Gf.Vec3d(*map(float, centre)))
        return self._finish(g, path, look, collide, offset, material)

    def revolute(self, path, b0, b1, p0, q0, p1, q1, axis, k=0.0, c=0.0, lo=None, hi=None):
        from pxr import Gf, Sdf, UsdPhysics
        j = UsdPhysics.RevoluteJoint.Define(self.stage, path)
        if b0:
            j.CreateBody0Rel().SetTargets([Sdf.Path(b0)])
        j.CreateBody1Rel().SetTargets([Sdf.Path(b1)])
        j.CreateLocalPos0Attr(Gf.Vec3f(*map(float, p0)))
        j.CreateLocalRot0Attr(Gf.Quatf(q0[3], q0[0], q0[1], q0[2]))
        j.CreateLocalPos1Attr(Gf.Vec3f(*map(float, p1)))
        j.CreateLocalRot1Attr(Gf.Quatf(q1[3], q1[0], q1[1], q1[2]))
        j.CreateAxisAttr(axis)
        if lo is not None:
            j.CreateLowerLimitAttr(float(lo))
            j.CreateUpperLimitAttr(float(hi))
        d = UsdPhysics.DriveAPI.Apply(j.GetPrim(), "angular")
        d.CreateTypeAttr("force")
        d.CreateTargetPositionAttr(0.0)
        d.CreateStiffnessAttr(float(k) * math.pi / 180)
        d.CreateDampingAttr(float(c) * math.pi / 180)
        return j

    def d6_bend(self, path, b0, b1, p0, p1, rot0=IDENT_Q, rot1=IDENT_Q, max_bend=80.0):
        return self.spherical(path, b0, b1, p0, p1, rot0, rot1, max_bend)

    def spherical(self, path, b0, b1, p0, p1, rot0=IDENT_Q, rot1=IDENT_Q, max_bend=80.0):
        """A bead's ball joint as a D6: no stretch, no twist, bending about the two axes across the chain up to
        ``max_bend`` degrees. rot1: the child's joint frame, so that both frames agree at the authored poses."""
        from pxr import Gf, Sdf, UsdPhysics
        j = UsdPhysics.Joint.Define(self.stage, path)
        j.CreateBody0Rel().SetTargets([Sdf.Path(b0)])
        j.CreateBody1Rel().SetTargets([Sdf.Path(b1)])
        j.CreateLocalPos0Attr(Gf.Vec3f(*map(float, p0)))
        j.CreateLocalRot0Attr(Gf.Quatf(float(rot0[3]), float(rot0[0]), float(rot0[1]), float(rot0[2])))
        j.CreateLocalPos1Attr(Gf.Vec3f(*map(float, p1)))
        j.CreateLocalRot1Attr(Gf.Quatf(float(rot1[3]), float(rot1[0]), float(rot1[1]), float(rot1[2])))
        prim = j.GetPrim()
        for dof in ("transX", "transY", "transZ", "rotX"):
            lim = UsdPhysics.LimitAPI.Apply(prim, dof)
            lim.CreateLowAttr(1.0)
            lim.CreateHighAttr(-1.0)
        for dof in ("rotY", "rotZ"):
            lim = UsdPhysics.LimitAPI.Apply(prim, dof)
            lim.CreateLowAttr(-float(max_bend))
            lim.CreateHighAttr(float(max_bend))
        return j


IDENT = (0.0, 0.0, 0.0, 1.0)
CHINA = (0.95, 0.95, 0.93)


def _spawn_toilet(prim_path: str, cfg, translation=None, orientation=None, **kwargs):
    from isaaclab.sim.utils.stage import get_current_stage
    from pxr import Gf, PhysxSchema, Sdf, UsdGeom, UsdPhysics

    spec: Toilet = _SPECS[cfg.kit_name]
    PATHS[spec.name] = prim_path
    stage = get_current_stage()
    root = UsdGeom.Xform.Define(stage, prim_path)
    T = np.array(translation or (0.0, 0.0, 0.0), dtype=float)
    root.AddTranslateOp(precision=UsdGeom.XformOp.PrecisionDouble).Set(Gf.Vec3d(*T))
    B = _Builder(stage, prim_path, spec.friction)
    china = B.look("china", CHINA, 0.30)
    china_in = B.look("china_in", (0.88, 0.88, 0.86), 0.35)
    pvc = B.look("pvc", (0.92, 0.92, 0.90), 0.45)        # the flush valve's white plastic
    grey = B.look("grey", (0.45, 0.47, 0.50), 0.5)       # fill valve body
    black = B.look("black", (0.06, 0.06, 0.07), 0.5)     # seat opening, refill tube
    chrome = B.look("chrome", (0.80, 0.81, 0.83), 0.15, 0.9)
    wood = B.look("wood", (0.72, 0.56, 0.36), 0.8)
    lever_l = B.look("lever", (0.85, 0.85, 0.83), 0.45)  # white plastic trip arm
    peg_mat = B.material("peg", spec.peg_friction)

    tank = f"{prim_path}/tank"
    B.body(tank, (0, 0, 0), IDENT, 12.0, inertia=(0.2, 0.2, 0.2))
    x0, x1 = IN_X
    zr = DEPTH
    ex0, ex1, ey = x0 - WALL, x1 + WALL, IN_Y + WALL
    zc = (zr - BOTTOM) / 2
    hz = zr + BOTTOM
    # walls (china), floor, bottom slab
    B.box(f"{tank}/wall_back", ((ex0 + x0) / 2, 0, zc), (WALL, 2 * ey, hz), china)
    B.box(f"{tank}/wall_front", ((ex1 + x1) / 2, 0, zc), (WALL, 2 * ey, hz), china)
    for k, s in enumerate((1, -1)):
        B.box(f"{tank}/wall_side_{k}", ((x0 + x1) / 2, s * (IN_Y + WALL / 2), zc), (x1 - x0, WALL, hz), china)
    B.box(f"{tank}/bottom", ((ex0 + ex1) / 2, 0, -BOTTOM / 2), (ex1 - ex0, 2 * ey, BOTTOM), china_in)
    # rounded-looking rim (visual only): a thin band on the wall tops
    for k, s in enumerate((1, -1)):
        B.cyl(f"{tank}/rim_side_{k}", ((x0 + x1) / 2, s * (IN_Y + WALL / 2), zr), WALL / 2, x1 - x0 + 2 * WALL, "X",
              china, collide=False)
    for k, xx in enumerate(((ex0 + x0) / 2, (ex1 + x1) / 2)):
        B.cyl(f"{tank}/rim_end_{k}", (xx, 0, zr), WALL / 2, 2 * ey, "Y", china, collide=False)
    # the tank's lid, taken off and laid flat on the table to the robot's right
    lid_c = np.array(LID_CENTRE_T)
    B.box(f"{tank}/lid", tuple(lid_c), LID_SIZE, china)
    for k, s in enumerate((1, -1)):
        B.cyl(f"{tank}/lid_edge_{k}", tuple(lid_c + np.array((0, s * LID_SIZE[1] / 2, 0))), LID_SIZE[2] / 2,
              LID_SIZE[0], "X", china, collide=False)
    # rails (2x4 laid flat) under the tank, along x, either side of the valve shank
    for k, s in enumerate((1, -1)):
        B.box(f"{tank}/rail_{k}", ((ex0 + ex1) / 2, s * 0.12, -BOTTOM - RAIL_H / 2), (ex1 - ex0 + 0.06, 0.089, RAIL_H),
              wood, collide=False)
    # flush valve: body, seat ring (collider: a flat disk whose top is the seat), seat opening (visual)
    B.cyl(f"{tank}/valve_body", (0, 0, VALVE_TOP / 2), VALVE_R, VALVE_TOP, "Z", pvc)
    B.cyl(f"{tank}/valve_seat", (0, 0, (VALVE_TOP + SEAT_TOP) / 2), SEAT_R, SEAT_TOP - VALVE_TOP, "Z", pvc)
    B.cyl(f"{tank}/seat_hole", (0, 0, SEAT_TOP + 0.0002), SEAT_IN, 0.0006, "Z", black, collide=False)
    # overflow tube on its bracket, with the refill tube's clip at its top
    B.cyl(f"{tank}/tube", (TUBE_X, 0, (0.010 + TUBE_TOP) / 2), TUBE_R, TUBE_TOP - 0.010, "Z", pvc)
    B.box(f"{tank}/tube_bracket", (TUBE_X / 2, 0, 0.010), (abs(TUBE_X), 0.030, 0.016), pvc, collide=False)
    B.cyl(f"{tank}/tube_mouth", (TUBE_X, 0, TUBE_TOP), TUBE_R - 0.002, 0.001, "Z", black, collide=False)
    # ear pegs: a boss from the tube, then the peg, along y
    for k, s in enumerate((1, -1)):
        yb = (TUBE_R - 0.002 + BOSS_Y) / 2
        B.cyl(f"{tank}/boss_{k}", (TUBE_X, s * yb, PEG_Z), 0.0045, BOSS_Y - TUBE_R + 0.002, "Y", pvc,
              material=peg_mat)
        yp = (BOSS_Y + PEG_TIP_Y) / 2
        B.cyl(f"{tank}/peg_{k}", (TUBE_X, s * yp, PEG_Z), PEG_R, PEG_TIP_Y - BOSS_Y, "Y", pvc, collide=False)
        # the peg's collider is a thinner core: the rubber hole stretches round the peg (see EarCatcher)
        B.cyl(f"{tank}/peg_core_{k}", (TUBE_X, s * yp, PEG_Z), PEG_CORE_R, PEG_TIP_Y - BOSS_Y, "Y", None,
              material=peg_mat, offset=0.0006)
    # fill valve (tank's own left): shank, float cup, cap; refill tube over to the overflow tube's top
    fx, fy = FILL_XY
    B.cyl(f"{tank}/fill_shank", (fx, fy, FILL_TOP / 2), FILL_R, FILL_TOP, "Z", grey)
    B.cyl(f"{tank}/fill_float", (fx, fy, sum(FLOAT_Z) / 2), FLOAT_R, FLOAT_Z[1] - FLOAT_Z[0], "Z", grey)
    B.cyl(f"{tank}/fill_cap", (fx, fy, FILL_TOP + 0.010), 0.024, 0.020, "Z", grey)
    # the refill tube: soft vinyl, a chain of sprung links from the fill valve's nipple (a joint on the tank) to the
    # overflow tube's mouth, where its clip holds the last link (a point joint outside the articulation)
    pts = refill_points()
    prev, prev_q, prev_end = tank, IDENT, np.asarray(pts[0], float)
    for i in range(REFILL_SEGS):
        p0, p1 = np.asarray(pts[i], float), np.asarray(pts[i + 1], float)
        d = p1 - p0
        L = float(np.linalg.norm(d))
        q = quat_from_matrix(_frame_x(d / L))
        rp = f"{prim_path}/refill_{i}"
        B.body(rp, (p0 + p1) / 2, q, spec.refill_mass / REFILL_SEGS, inertia=(2e-7, 2e-6, 2e-6), maxv=2.0)
        B.cyl(f"{rp}/tube", (0, 0, 0), 0.0032, max(L - 0.0064, 0.001), "X", black, capsule=True, offset=0.0008)
        B.d6_bend(f"{rp}/refill_j_{i:02d}", prev, rp, prev_end, (-L / 2, 0, 0), qmul(qinv(prev_q), q), IDENT_Q, 50.0)
        prev, prev_q, prev_end = rp, q, (L / 2, 0, 0)
    # its free end rests in the overflow tube's mouth (the clip is not modelled: the end can be knocked out)
    # handle (chrome, outside the front wall) and its shaft
    px, py, pz = LEVER_PIVOT
    B.cyl(f"{tank}/handle_shaft", ((px + ex1) / 2 + 0.005, py, pz), 0.006, ex1 - px + 0.010, "X", chrome,
          collide=False)
    B.cyl(f"{tank}/handle_nut", (x1 - 0.004, py, pz), 0.013, 0.008, "X", chrome, collide=False)
    hb = np.array((ex1 + 0.012, py, pz))
    B.cyl(f"{tank}/handle_boss", tuple(hb), 0.014, 0.020, "X", chrome, collide=False)
    B.box(f"{tank}/handle", (ex1 + 0.020, py + LEVER_DIR * 0.040, pz - 0.004), (0.012, 0.075, 0.016), chrome, collide=False)
    # lever arm (its own link): a flat plastic arm along +y from the pivot, holes near its end, the clip in one hole
    lev = f"{prim_path}/lever"
    B.body(lev, (px, py, pz), IDENT, spec.lever_mass, inertia=(1e-4, 1e-5, 1e-4), com=(0, LEVER_DIR * LEVER_LEN / 2, 0))
    B.box(f"{lev}/arm", (0, LEVER_DIR * LEVER_LEN / 2, 0), (0.004, LEVER_LEN, 0.014), lever_l, collide=False)
    B.cyl(f"{lev}/hub", (0.006, 0, 0), 0.010, 0.012, "X", lever_l, collide=False)
    for k, hy in enumerate(LEVER_HOLES):
        B.cyl(f"{lev}/hole_{k}", (0, hy, 0), 0.0022, 0.0045, "X", black, collide=False)
    # the clip: a stainless hook through the hole and a slotted plate below it (visual; ClipCatcher holds the bead)
    hy = LEVER_HOLES[CLIP_HOLE]
    # the clip: a stainless C-hook through the hole whose lower jaw, 10 mm behind the arm, has the slot that takes the
    # chain between two beads (visual; ClipCatcher holds the bead)
    B.cyl(f"{lev}/clip_hook", (0, hy, 0.004), 0.0012, 0.006, "Y", chrome, collide=False)
    B.box(f"{lev}/clip_top", (-CLIP_BACK / 2, hy, 0.008), (CLIP_BACK + 0.004, 0.0024, 0.0024), chrome, collide=False)
    B.box(f"{lev}/clip_back", (-CLIP_BACK - 0.002, hy, -CLIP_DROP / 2 + 0.004), (0.0024, 0.0024, CLIP_DROP + 0.010),
          chrome, collide=False)
    B.box(f"{lev}/clip_jaw", (-CLIP_BACK, hy, -CLIP_DROP - 0.001), (0.008, 0.010, 0.0015), chrome, collide=False)
    j = B.revolute(f"{lev}/lever_hinge", tank, lev, (px, py, pz), IDENT, (0, 0, 0), IDENT, "X", spec.lever_k,
                   spec.lever_c, lo=min(0.0, LEVER_DIR * 70.0), hi=max(0.0, LEVER_DIR * 70.0))
    # articulation
    UsdPhysics.ArticulationRootAPI.Apply(stage.GetPrimAtPath(tank))
    art = PhysxSchema.PhysxArticulationAPI.Apply(stage.GetPrimAtPath(tank))
    art.CreateEnabledSelfCollisionsAttr(False)
    art.CreateSolverPositionIterationCountAttr(32)
    art.CreateSolverVelocityIterationCountAttr(4)
    fj = UsdPhysics.FixedJoint.Define(stage, f"{prim_path}/fixed")
    fj.CreateBody1Rel().SetTargets([Sdf.Path(tank)])
    fj.CreateLocalPos0Attr(Gf.Vec3f(*map(float, T)))
    fj.CreateLocalRot0Attr(Gf.Quatf(1, 0, 0, 0))
    fj.CreateLocalPos1Attr(Gf.Vec3f(0, 0, 0))
    fj.CreateLocalRot1Attr(Gf.Quatf(1, 0, 0, 0))
    return root.GetPrim()


def refill_points() -> list:
    """The refill tube's centre line at rest (T): a sagging-upward arc from the nipple to the tube's mouth."""
    a, b = np.asarray(REFILL_FROM, float), np.asarray(REFILL_TO, float)
    return [a + (b - a) * t + np.array((0.0, 0.0, REFILL_SAG * math.sin(math.pi * t)))
            for t in np.linspace(0.0, 1.0, REFILL_SEGS + 1)]


def _frame_x(x) -> np.ndarray:
    """A rotation whose x axis is ``x``."""
    f = _frame_z(x)
    return np.column_stack([f[:, 2], f[:, 0], f[:, 1]])


def _frame_z(z) -> np.ndarray:
    z = np.asarray(z, float) / np.linalg.norm(z)
    a = np.array((1.0, 0, 0)) if abs(z[0]) < 0.9 else np.array((0, 1.0, 0))
    x = np.cross(a, z)
    x /= np.linalg.norm(x)
    return np.column_stack([x, np.cross(z, x), z])


def _spawn_flapper(prim_path: str, cfg, translation=None, orientation=None, **kwargs):
    from isaaclab.sim.utils.stage import get_current_stage
    from pxr import Gf, PhysxSchema, Sdf, UsdGeom, UsdPhysics

    spec: Flapper = _SPECS[cfg.kit_name]
    PATHS[spec.name] = prim_path
    stage = get_current_stage()
    root = UsdGeom.Xform.Define(stage, prim_path)
    # Isaac Lab places the articulation's root link (the disk) at the object's initial pose; children are authored in
    # world coordinates relative to a root transform that puts the disk where flapper_start() says.
    st = flapper_start(spec)
    disk_p, disk_q = st["disk"]
    root.AddTranslateOp(precision=UsdGeom.XformOp.PrecisionDouble).Set(Gf.Vec3d(0, 0, 0))
    B = _Builder(stage, prim_path, spec.rubber_friction)
    rubber = B.look("rubber", (0.10, 0.10, 0.11), 0.75)    # black chlorine-resistant rubber
    cup = B.look("cup", (0.14, 0.14, 0.16), 0.6)
    steel = B.look("steel", (0.74, 0.75, 0.77), 0.25, 0.9)
    bead_mat = B.material("bead", 0.4)
    grip_mat = B.material("ear_grip", spec.tab_friction, "max")
    R0 = rotmat(np.array(disk_q))

    def local(p_f, body_origin_f):
        return np.asarray(p_f, float) - np.asarray(body_origin_f, float)

    disk = f"{prim_path}/disk"
    B.body(disk, disk_p, disk_q, spec.disk_mass, inertia=(2.0e-5, 2.0e-5, 3.6e-5), maxv=2.0)
    dc = np.array((DISK_X, 0, 0))
    B.cyl(f"{disk}/seal", local((DISK_X, 0, DISK_TOP - DISK_H / 2), dc), DISK_R, DISK_H, "Z", rubber, offset=0.0008)
    B.cyl(f"{disk}/cup", local((DISK_X + 0.005, 0, DISK_TOP + CUP_H / 2), dc), CUP_R, CUP_H, "Z", cup, offset=0.0008)
    B.cyl(f"{disk}/cup_rim", local((DISK_X + 0.005, 0, DISK_TOP + CUP_H), dc), CUP_R + 0.001, 0.002, "Z", rubber,
          collide=False)
    B.box(f"{disk}/lug", local((LUG[0] - 0.004, 0, LUG[2]), dc), (0.012, 0.010, 0.006), rubber, collide=False)
    B.cyl(f"{disk}/lug_ring", local(LUG, dc), 0.003, 0.002, "Y", steel, collide=False)
    # ears: each a sprung link at the arm's root (bends sideways, about z), carrying the arm and the holed tab
    for tag, s in (("l", 1), ("r", -1)):
        ear = f"{prim_path}/ear_{tag}"
        eo = np.array((ARM_ROOT_X, s * EAR_Y, 0.0))
        p, q = st[f"ear_{tag}"]
        B.body(ear, p, q, spec.ear_mass, inertia=(2e-6, 2e-6, 2e-6), maxv=2.0, report=True)
        # the arm slopes down from the tab to the seal's edge (the hinge line rides 15 mm above the seal)
        ax0, az0, ax1, az1 = EAR_W / 2 - 0.002, 0.0, ARM_ROOT_X + 0.004, DISK_TOP + 0.003
        alen = math.hypot(ax1 - ax0, az1 - az0)
        B.box(f"{ear}/arm", local(((ax0 + ax1) / 2, s * EAR_Y, (az0 + az1) / 2), eo), (alen, EAR_T, 0.010), rubber,
              quat_xyzw=quat_axis((0, 1, 0), math.atan2(az0 - az1, ax1 - ax0)))
        hz0, hz1 = -HOLE / 2, HOLE / 2
        B.box(f"{ear}/tab_top", local((0, s * EAR_Y, (hz1 + EAR_Z[1]) / 2), eo), (EAR_W, EAR_T, EAR_Z[1] - hz1),
              rubber, offset=0.0006, material=grip_mat, torsion=spec.tab_torsion)
        B.box(f"{ear}/tab_bot", local((0, s * EAR_Y, (EAR_Z[0] + hz0) / 2), eo), (EAR_W, EAR_T, hz0 - EAR_Z[0]),
              rubber, offset=0.0006)
        side_w = (EAR_W - HOLE) / 2
        for k, sx in enumerate((-1, 1)):
            B.box(f"{ear}/tab_side_{k}", local((sx * (HOLE / 2 + side_w / 2), s * EAR_Y, 0), eo),
                  (side_w, EAR_T, HOLE), rubber, offset=0.0006)
        # spread hinge about z at the arm's root (the tab lies behind the root, toward -x): turning the left ear
        # negative (the right ear positive) draws its tab outward
        lo, hi = (-spec.ear_limit_deg, 6.0) if s > 0 else (-6.0, spec.ear_limit_deg)
        B.revolute(f"{ear}/ear_{tag}_spread", disk, ear, local(eo, dc), IDENT, (0, 0, 0), IDENT, "Z", spec.ear_k,
                   spec.ear_c, lo=lo, hi=hi)
    # bead chain: every bead keeps the disk's orientation; the joints' frames carry the chain's direction (their x)
    dirs = chain_dirs_local(spec)
    prev, prev_end, prev_dir = disk, local(LUG, dc), dirs[0]
    for k in range(spec.n_beads // SEG_BEADS):
        bp = f"{prim_path}/{seg_name(k)}"
        p, q = st[seg_name(k)]
        d_l = dirs[k]
        wq = quat_from_matrix(_frame_z(d_l))
        B.body(bp, p, q, spec.bead_mass * SEG_BEADS, inertia=(1e-6, 1e-6, 1e-6), maxv=3.0)  # inertia raised for the solver
        for j in range(SEG_BEADS):
            off = d_l * bead_offset(k * SEG_BEADS + j)
            B.sphere(f"{bp}/bead_{j}", tuple(off), BEAD_R, steel, collide=False)
            B.sphere(f"{bp}/bead_col_{j}", tuple(off), BEAD_COL_R, None, offset=0.0005, material=bead_mat)
            w = B.cyl(f"{bp}/wire_{j}", tuple(off - d_l * BEAD_PITCH / 2), 0.0006, BEAD_PITCH - 2 * BEAD_R + 0.0016, "Z",
                      steel, collide=False)
            w.AddOrientOp().Set(Gf.Quatf(wq[3], wq[0], wq[1], wq[2]))
        jq = quat_from_matrix(_frame_x(prev_dir))  # both frames along the previous link: zero is the start's bend
        B.spherical(f"{bp}/link_{k:02d}", prev, bp, prev_end, tuple(-d_l * SEG_LEN / 2), jq, jq)
        prev, prev_end, prev_dir = bp, tuple(d_l * SEG_LEN / 2), d_l
    UsdPhysics.ArticulationRootAPI.Apply(stage.GetPrimAtPath(disk))
    art = PhysxSchema.PhysxArticulationAPI.Apply(stage.GetPrimAtPath(disk))
    art.CreateEnabledSelfCollisionsAttr(False)
    art.CreateSolverPositionIterationCountAttr(spec.solver_pos_iters)
    art.CreateSolverVelocityIterationCountAttr(4)
    art.CreateSleepThresholdAttr(0.0)
    art.CreateStabilizationThresholdAttr(0.0)
    # clip joints (disabled): bead i held at the clip's slot
    toilet = next((PATHS[n] for n, s in _SPECS.items() if isinstance(s, Toilet)), None)
    if toilet is not None:
        lev = f"{toilet}/tank"  # anchored on the tank at the slot's rest place; ClipCatcher.follow moves it with the lever
        slot_l = clip_slot_T()
        for i in range(CLIP_FROM, spec.n_beads):
            jp = f"{prim_path}/clip_{i:02d}"
            boff = dirs[i // SEG_BEADS] * bead_offset(i)
            pj = UsdPhysics.Joint.Define(stage, jp)
            pj.CreateBody0Rel().SetTargets([Sdf.Path(lev)])
            pj.CreateBody1Rel().SetTargets([Sdf.Path(f"{prim_path}/{seg_name(i // SEG_BEADS)}")])
            pj.CreateLocalPos0Attr(Gf.Vec3f(*map(float, slot_l)))
            pj.CreateLocalRot0Attr(Gf.Quatf(1, 0, 0, 0))
            pj.CreateLocalPos1Attr(Gf.Vec3f(*map(float, boff)))
            pj.CreateLocalRot1Attr(Gf.Quatf(1, 0, 0, 0))
            pj.CreateExcludeFromArticulationAttr(True)
            pj.CreateJointEnabledAttr(False)
            pj.CreateCollisionEnabledAttr(True)
            for ax in ("transX", "transY", "transZ"):
                d = UsdPhysics.DriveAPI.Apply(pj.GetPrim(), ax)
                d.CreateTypeAttr("force")
                d.CreateStiffnessAttr(spec.clip_k)
                d.CreateDampingAttr(spec.clip_c)
                d.CreateTargetPositionAttr(0.0)
    # ear-on-peg joints (disabled): each ear's hole held on its peg's axis (EarCatcher switches one on)
    if toilet is not None:
        tank_b = f"{toilet}/tank"
        for tag, sg in (("l", 1), ("r", -1)):
            pj = UsdPhysics.Joint.Define(stage, f"{prim_path}/on_peg_{tag}")
            pj.CreateBody0Rel().SetTargets([Sdf.Path(tank_b)])
            pj.CreateBody1Rel().SetTargets([Sdf.Path(f"{prim_path}/ear_{tag}")])
            pj.CreateLocalPos0Attr(Gf.Vec3f(float(TUBE_X), float(sg * EAR_Y), float(PEG_Z)))
            pj.CreateLocalRot0Attr(Gf.Quatf(1, 0, 0, 0))
            pj.CreateLocalPos1Attr(Gf.Vec3f(float(-ARM_ROOT_X), 0.0, 0.0))
            pj.CreateLocalRot1Attr(Gf.Quatf(1, 0, 0, 0))
            pj.CreateExcludeFromArticulationAttr(True)
            pj.CreateJointEnabledAttr(False)
            pj.CreateCollisionEnabledAttr(True)
            for ax, k, c in (("transX", spec.peg_k, spec.peg_c), ("transZ", spec.peg_k, spec.peg_c),
                             ("transY", spec.peg_slide_k, spec.peg_c)):
                d = UsdPhysics.DriveAPI.Apply(pj.GetPrim(), ax)
                d.CreateTypeAttr("force")
                d.CreateStiffnessAttr(k)
                d.CreateDampingAttr(c)
                d.CreateTargetPositionAttr(0.0)
            lim = UsdPhysics.LimitAPI.Apply(pj.GetPrim(), "rotY")  # the flapper opens until it rests against the
            lim.CreateLowAttr(-float(spec.open_limit_deg))           # overflow tube
            lim.CreateHighAttr(2.0)
            for ax in ("rotX", "rotZ"):
                d = UsdPhysics.DriveAPI.Apply(pj.GetPrim(), ax)
                d.CreateTypeAttr("force")
                d.CreateStiffnessAttr(spec.peg_rot_k * math.pi / 180)
                d.CreateDampingAttr(spec.peg_rot_c * math.pi / 180)
                d.CreateTargetPositionAttr(0.0)
    return root.GetPrim()


def _arena_object(spec):
    from isaaclab.actuators import ImplicitActuatorCfg
    from isaaclab.assets import ArticulationCfg
    from isaaclab.sim.spawners.spawner_cfg import SpawnerCfg
    from isaaclab.sim.utils import clone
    from isaaclab.utils import configclass
    from isaaclab_arena.assets.object import Object
    from isaaclab_arena.assets.object_type import ObjectType
    from isaaclab_arena.utils.pose import Pose

    toilet = isinstance(spec, Toilet)

    @configclass
    class KitSpawnerCfg(SpawnerCfg):
        func: object = clone(_spawn_toilet if toilet else _spawn_flapper)
        kit_name: str = ""

    if toilet:
        acts = {"lever": ImplicitActuatorCfg(joint_names_expr=["lever_hinge"], stiffness=spec.lever_k,
                                             damping=spec.lever_c),
                "refill": ImplicitActuatorCfg(joint_names_expr=["refill_j_.*"], stiffness=spec.refill_k,
                                              damping=spec.refill_c)}
        pose = Pose(position_xyz=tuple(float(v) for v in spec.pos), rotation_xyzw=IDENT)
    else:
        acts = {"ears": ImplicitActuatorCfg(joint_names_expr=["ear_.*"], stiffness=spec.ear_k, damping=spec.ear_c),
                "chain": ImplicitActuatorCfg(joint_names_expr=["link_.*"], stiffness=0.0, damping=spec.bead_c)}
        p, q = flapper_start(spec)["disk"]
        pose = Pose(position_xyz=tuple(float(v) for v in p), rotation_xyzw=tuple(float(v) for v in q))

    class KitObject(Object):
        def _generate_articulation_cfg(self):
            cfg = ArticulationCfg(prim_path=self.prim_path, spawn=self.spawner_cfg, actuators=acts)
            return self._add_initial_pose_to_cfg(cfg)

    return KitObject(name=spec.name, object_type=ObjectType.ARTICULATION, spawner_cfg=KitSpawnerCfg(kit_name=spec.name),
                     initial_pose=pose)


# -- reading the state -------------------------------------------------------------------------------------------------

def _t(x):
    return getattr(x, "torch", x)


def as_np(x) -> np.ndarray:
    x = _t(x)
    if hasattr(x, "detach"):
        return x.detach().cpu().numpy().astype(np.float64)
    return np.asarray(x.numpy(), dtype=np.float64)


def articulation(env, name: str):
    base = env.unwrapped if hasattr(env, "unwrapped") else env
    return base.scene[name]


def _origin(env):
    base = env.unwrapped if hasattr(env, "unwrapped") else env
    return as_np(base.scene.env_origins)[0]


def raw_state(env, name: str) -> dict:
    art = articulation(env, name)
    o = _origin(env)
    pos = as_np(art.data.body_link_pos_w)[0] - o
    quat = as_np(art.data.body_link_quat_w)[0]
    q = as_np(art.data.joint_pos)[0]
    return {"pos": dict(zip(art.body_names, pos)), "quat": dict(zip(art.body_names, quat)),
            "joint": dict(zip(art.joint_names, q))}


@dataclass(frozen=True)
class KitState(ObjectState):
    raw: dict = None


def kit_state(env, name: str) -> KitState:
    raw = raw_state(env, name)
    root = "tank" if isinstance(_SPECS[name], Toilet) else "disk"
    p, q = raw["pos"][root], raw["quat"][root]
    pts = np.array(list(raw["pos"].values()))
    return KitState(pos=p, quat_xyzw=q, lin_vel=np.zeros(3), ang_vel=np.zeros(3), low=pts.min(0), high=pts.max(0),
                    raw=raw)


# -- the chain clip -----------------------------------------------------------------------------------------------------

class ClipCatcher:
    """Switches on the clip joint of the bead held within the slot's window for DWELL steps (0.3 s); it
    holds for good after that (a real clip holds the chain until it is lifted out by hand, which the task never asks
    for)."""

    SLOT_R = 0.008    # a bead within this of the slot's point (across the slot) counts as in it
    SLOT_Z = 0.008    # ... and within this up or down
    DWELL = 6         # control steps (0.3 s)

    def __init__(self, flapper: str = "flapper", toilet: str = "toilet"):
        self.flapper, self.toilet = flapper, toilet
        self.on: int | None = None
        self.since: dict = {}
        self.events: list = []

    def slot_world(self, traw) -> np.ndarray:
        p, q = traw["pos"]["lever"], traw["quat"]["lever"]
        return p + rotmat(q) @ np.array((-CLIP_BACK, LEVER_HOLES[CLIP_HOLE], -CLIP_DROP))

    def candidate(self, fraw, traw) -> int | None:
        """The bead in the slot: of the beads within the slot's window, the nearest to the slot's point."""
        s = self.slot_world(traw)
        spec = _SPECS[self.flapper]
        dl = chain_dirs_local(spec)
        best, bd = None, 1e9
        for i in range(CLIP_FROM, spec.n_beads):
            if seg_name(i // SEG_BEADS) not in fraw["pos"]:
                break
            d = bead_pos(fraw, i, dl) - s
            if math.hypot(d[0], d[1]) < self.SLOT_R and abs(d[2]) < self.SLOT_Z and float(np.linalg.norm(d)) < bd:
                best, bd = i, float(np.linalg.norm(d))
        return best

    def _set(self, i: int, on: bool):
        import omni.usd
        from pxr import UsdPhysics
        stage = omni.usd.get_context().get_stage()
        prim = stage.GetPrimAtPath(f"{PATHS[self.flapper]}/clip_{i:02d}")
        UsdPhysics.Joint(prim).GetJointEnabledAttr().Set(bool(on))

    def update(self, step: int, fraw, traw, fingertips=None) -> int | None:
        """The clip takes the bead nearest its slot once some bead has stayed inside the slot's window for DWELL
        control steps running (a proximity model: no force, direction or release is checked; ``fingertips`` unused)."""
        if self.on is not None:
            self.check_pull(step, fraw, traw)
            return self.on
        i = self.candidate(fraw, traw)
        if i is None:
            self.since = {}
            return None
        self.since = {"n": self.since.get("n", 0) + 1}  # the chain has been in the slot this many steps running
        if self.since["n"] >= self.DWELL:
            self._set(i, True)
            self.on = i
            self.events.append((step, "clip", i))
        return self.on

    PULL_OUT_M = 0.010  # the clip lets the chain go if its bead is dragged this far out of the slot

    def check_pull(self, step, fraw, traw) -> None:
        if self.on is None:
            return
        d = float(np.linalg.norm(bead_pos(fraw, self.on, chain_dirs_local(_SPECS[self.flapper])) - self.slot_world(traw)))
        if d > self.PULL_OUT_M:
            self._set(self.on, False)
            self.events.append((step, "chain_out", self.on, round(d, 4)))
            self.on = None
            self.since = {}
            self.out = True

    def follow(self, traw) -> None:
        """Keep the held bead's spring anchored on the slot as the lever moves (the clip hangs from the lever)."""
        if self.on is None:
            return
        import omni.usd
        from pxr import UsdPhysics
        d = self.slot_world(traw) - (traw["pos"]["tank"] + clip_slot_T())
        prim = omni.usd.get_context().get_stage().GetPrimAtPath(f"{PATHS[self.flapper]}/clip_{self.on:02d}")
        for k, ax in enumerate(("transX", "transY", "transZ")):
            UsdPhysics.DriveAPI(prim, ax).GetTargetPositionAttr().Set(float(d[k]))

    def release(self):
        if self.on is not None:
            self._set(self.on, False)
        self.on = None
        self.since = {}


class EarCatcher:
    """An ear's hole goes over its peg when pushed onto it: once the hole's centre is within EAR_CAPTURE_R of the
    peg's axis, between the peg's tip (2 mm in) and its boss, and the tab is pushed home against the boss (the physics
    engine's contact force from the tank on the ear, along the peg, at least EAR_PUSH_N) for 2 control steps, a sprung
    joint draws the hole round the peg for SEAT_STEPS steps (the rubber hole stretching over the peg), then lets go:
    from then on the ear simply hangs on the peg (the peg's core passes through its hole). If an ear later leaves its
    peg, it can be put on again the same way."""

    SEAT_STEPS = 10

    def __init__(self, flapper: str = "flapper"):
        self.flapper = flapper
        self.state = {"l": "off", "r": "off"}
        self.count = {"l": 0, "r": 0}
        self.events: list = []

    @property
    def on(self) -> dict:
        return {t: v != "off" for t, v in self.state.items()}

    def _set(self, tag: str, on: bool):
        import omni.usd
        from pxr import UsdPhysics
        prim = omni.usd.get_context().get_stage().GetPrimAtPath(f"{PATHS[self.flapper]}/on_peg_{tag}")
        UsdPhysics.Joint(prim).GetJointEnabledAttr().Set(bool(on))

    @staticmethod
    def on_peg(hole, sg, r=EAR_CAPTURE_R) -> bool:
        x, y, z = hole
        return math.hypot(x - TUBE_X, z - PEG_Z) < r and BOSS_Y - 0.001 < sg * y < PEG_TIP_Y - 0.002

    def update(self, step: int, holes_t: dict, push: dict) -> dict:
        """``push``: per ear, the contact force from the tank along the peg, outward (N; EarPush.read)."""
        for tag, sg in (("l", 1), ("r", -1)):
            st = self.state[tag]
            if st == "seating":
                self.count[tag] += 1
                if self.count[tag] >= self.SEAT_STEPS:
                    self._set(tag, False)
                    self.state[tag], self.count[tag] = "on", 0
                    self.events.append((step, "ear_seated", tag))
                continue
            ok = self.on_peg(holes_t[tag], sg)
            if st == "on":
                self.count[tag] = 0 if ok else self.count[tag] + 1
                if self.count[tag] >= 10:
                    self.state[tag], self.count[tag] = "off", 0
                    self.events.append((step, "ear_off", tag))
                continue
            self.count[tag] = self.count[tag] + 1 if ok and push[tag] >= EAR_PUSH_N else 0
            if self.count[tag] >= 2:
                self._set(tag, True)
                self.state[tag], self.count[tag] = "seating", 0
                self.events.append((step, "ear_on", tag))
        return self.on

    def release(self):
        for tag in self.state:
            if self.state[tag] == "seating":
                self._set(tag, False)
            self.state[tag], self.count[tag] = "off", 0


class EarPush:
    """The physics engine's contact force on each ear from the tank (its pegs, bosses and overflow tube), through a
    PhysX rigid contact view on the ear bodies (contact reports on) filtered on the tank's body. ``read`` gives, per
    ear, the force's component along its peg, outward (the push of the tab against the peg's boss), in N."""

    def __init__(self):
        self.view = None

    def attach(self, env):
        if self.view is not None:
            return
        art = articulation(env, "flapper")
        sim_view = art._physics_sim_view
        f, t = PATHS["flapper"], PATHS["toilet"]
        self.view = sim_view.create_rigid_contact_view([f"{f}/ear_l", f"{f}/ear_r"],
                                                       filter_patterns=[[f"{t}/tank"], [f"{t}/tank"]])

    def read(self, dt: float) -> dict:
        m = as_np(self.view.get_contact_force_matrix(dt))  # (2 ears, 1 filter, 3), world frame, on the ear
        return {"l": float(m[0, 0, 1]), "r": float(-m[1, 0, 1])}


# -- yam_arena hooks ------------------------------------------------------------------------------------------------------

def _patch_scene(scene) -> None:
    if getattr(scene, "_toiletkit", False):
        return
    orig_obj, orig_states = scene.task_object, scene.object_states

    def task_object(spec):
        if isinstance(spec, (Toilet, Flapper)):
            _SPECS[spec.name] = spec
            return _arena_object(spec)
        return orig_obj(spec)

    def object_states(env, names):
        plain = [n for n in names if n not in _SPECS]
        out = orig_states(env, plain) if plain else {}
        out.update({n: kit_state(env, n) for n in names if n in _SPECS})
        return {n: out[n] for n in names}

    scene.task_object, scene.object_states = task_object, object_states
    scene._toiletkit = True


class _Finder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname != "yam_arena.scene":
            return None
        sys.meta_path.remove(self)
        try:
            spec = importlib.util.find_spec(fullname)
        finally:
            sys.meta_path.insert(0, self)
        if spec is None or spec.loader is None:
            return None
        orig = spec.loader.exec_module

        def exec_module(module):
            orig(module)
            _patch_scene(module)

        spec.loader.exec_module = exec_module
        return spec


def install() -> None:
    if "yam_arena.scene" in sys.modules:
        _patch_scene(sys.modules["yam_arena.scene"])
    elif not any(isinstance(f, _Finder) for f in sys.meta_path):
        sys.meta_path.insert(0, _Finder())


install()
