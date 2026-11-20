"""On the station table: a pillow with a practice forearm strapped along it, palm up, the left hand at its end clenched
into a fist. Tape marks on the table frame the pillow. A hand cone lies on its side between
two rails on a box in front of the right arm, its wide end overhanging the box towards the robot.

The task: fit the cone across the palm, wide end at the little-finger side, with all four fingers curled round it,
without forcing the fingers open; then let go and move clear.

The hand is rigid parts on pin joints: a palm (with a fixed thumb) on a wrist hinge, and four fingers, each a
proximal phalanx and a middle-distal piece. Every physics step, each finger's flexor and extensor cord tensions are
computed from the cord path lengths (wrist and finger angles, handmodel.tendons) and applied as joint torques, with the
wrist's return spring. Each flexor is a silicone section with a check loop beside it that goes taut after 15.5 mm of
stretch, the contracted tissue's end-stop. Nothing else drives the hand: the fingers stop only against the palm, the cone or a gripper.
Each finger's flexor gauge keeps its peak tension.
"""

from __future__ import annotations

import math
import os
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # lets this file import helpers beside it

import bodykit as bk  # noqa: E402
import cone_rules as rules  # noqa: E402
import handmodel as hm  # noqa: E402
import steptime  # noqa: E402
from yam_arena.task_file import TABLE_TOP, Box  # noqa: E402

SCENE = "station"
TOP = TABLE_TOP[SCENE]
PILLOW_TOP = TOP + hm.PILLOW_SIZE[2]
WRIST = np.array([hm.WRIST_XY[0], hm.WRIST_XY[1], PILLOW_TOP + hm.HALF_T + 0.0005])
SKIN = (0.86, 0.68, 0.56)
SOLVER_IT = 32
FINGER_DAMP = 2.0e-5   # N m per deg/s at each finger joint (the pins' friction)
WRIST_DAMP = 2.0e-4


def world(u: float, v: float, n: float) -> np.ndarray:
    """A neutral hand-frame point in the world."""
    return WRIST + hm.uvn(u, v, n)


# -- tape marks: an L at each corner of the pillow --------------------------------------------------------------------
MARKS = []
_px, _py = hm.PILLOW_C
_hx, _hy = hm.PILLOW_SIZE[0] / 2 + 0.004, hm.PILLOW_SIZE[1] / 2 + 0.004
for k, (sx, sy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
    cx, cy = _px + sx * _hx, _py + sy * _hy
    MARKS.append(Box(f"mark{k}a", pos=(cx - sx * 0.012, cy, TOP + 0.0005), size=(0.030, 0.006, 0.001), color=(0.95, 0.55, 0.10)))
    MARKS.append(Box(f"mark{k}b", pos=(cx, cy - sy * 0.012, TOP + 0.0005), size=(0.006, 0.030, 0.001), color=(0.95, 0.55, 0.10)))

# -- the pillow with the forearm strapped on it -----------------------------------------------------------------------
_P0 = np.array([hm.PILLOW_C[0], hm.PILLOW_C[1], TOP])


def _pl(p) -> tuple:
    return tuple(float(v) for v in (np.asarray(p, float) - _P0))


_pillow_shapes = [bk.BoxShape((0.0, 0.0, hm.PILLOW_SIZE[2] / 2), hm.PILLOW_SIZE, color=(0.86, 0.89, 0.94))]
for y0, y1, r in ((WRIST[1] + 0.010, WRIST[1] + 0.10, 0.025), (WRIST[1] + 0.10, _P0[1] + 0.17, 0.031)):
    zc = PILLOW_TOP + r
    _pillow_shapes += hm.capsule(bk, _pl((WRIST[0], y0 + r, zc)), _pl((WRIST[0], y1 - r, zc)), r, SKIN)
for y in (WRIST[1] + 0.06, WRIST[1] + 0.15):  # two hook-and-loop straps over the forearm, round the pillow
    _pillow_shapes.append(bk.BoxShape(_pl((WRIST[0], y, PILLOW_TOP + 0.035)), (0.070, 0.025, 0.002), color=(0.25, 0.30, 0.40),
                                      collide=False))
PILLOW = bk.Body.build("pillow", tuple(_P0), hm.PILLOW_MASS + hm.FOREARM_MASS, _pillow_shapes, friction=(0.7, 0.6),
                       solver_iterations=SOLVER_IT, contact_report=True)

# -- the palm, with its thumb: origin on the wrist axis ----------------------------------------------------------------
_palm_shapes = [
    bk.BoxShape(tuple(hm.uvn(0.0265, 0.0, 0.0)), (hm.PALM_W_PROX, 0.037, 2 * hm.HALF_T), color=SKIN),
    bk.BoxShape(tuple(hm.uvn((0.045 + hm.PALM_LEN) / 2, 0.0, 0.0)), (hm.PALM_W, hm.PALM_LEN - 0.045, 2 * hm.HALF_T), color=SKIN),
]
_palm_shapes += hm.capsule(bk, hm.uvn(hm.KNUCKLE_U, -0.032, 0.0), hm.uvn(hm.KNUCKLE_U, 0.032, 0.0), hm.HALF_T, SKIN)  # knuckle roll
(tu0, tv0, tn0), (tu1, tv1, tn1), tr = hm.THUMB
_palm_shapes += hm.capsule(bk, hm.uvn(tu0, tv0, tn0), hm.uvn(tu1, tv1, tn1), tr, SKIN)
PALM = bk.Body.build("palm", tuple(WRIST), hm.PALM_MASS, _palm_shapes, friction=(0.8, 0.7), solver_iterations=SOLVER_IT,
                     contact_report=True, torsional_patch=0.012)
bk.hinge("wrist", "pillow", "palm", tuple(WRIST), axis="X", limits_deg=(-85.0, 0.0), damping=WRIST_DAMP)  # the wrist stops at straight

# -- the fingers ------------------------------------------------------------------------------------------------------
PROX, DIST = [], []
PROX_NAMES = [f"{f}_prox" for f in hm.FINGERS]
DIST_NAMES = [f"{f}_dist" for f in hm.FINGERS]
for i, f in enumerate(hm.FINGERS):
    tm, tp = hm.CLENCH[i]
    p0, p1, p2, p3 = hm.finger_segments(i, tm, tp)
    v = hm.FINGER_V[i]
    l1, l2, l3 = hm.LENGTHS[i]
    r = hm.RADII[i]
    mcp = world(p0[0], v, p0[1])
    pip = world(p1[0], v, p1[1])
    rm = hm.flex_rot(tm)
    rp = hm.flex_rot(tm + tp)
    PROX.append(bk.Body.build(PROX_NAMES[i], tuple(mcp), hm.PROX_MASS, hm.capsule(bk, (0, 0, 0), (0, -l1, 0), r, SKIN),
                              start_xyzw=hm.quat_of(rm), friction=(0.8, 0.7), solver_iterations=SOLVER_IT,
                              contact_report=True, ignore=("palm", *PROX_NAMES[:i])))
    dip, tip = hm.distal_local(i)
    DIST.append(bk.Body.build(DIST_NAMES[i], tuple(pip), hm.DIST_MASS,
                              hm.capsule(bk, (0, 0, 0), tuple(dip), r, SKIN) + hm.capsule(bk, tuple(dip), tuple(tip), r * 0.95, SKIN),
                              start_xyzw=hm.quat_of(rp), friction=(0.8, 0.7), solver_iterations=SOLVER_IT,
                              contact_report=True, ignore=(*PROX_NAMES, *DIST_NAMES[:i])))
    bk.hinge(f"{f}_mcp", "palm", PROX_NAMES[i], tuple(mcp), axis="X", limits_deg=(-(110.0 - tm), tm - hm.MCP_MIN_DEG),
             damping=FINGER_DAMP)
    bk.hinge(f"{f}_pip", PROX_NAMES[i], DIST_NAMES[i], tuple(pip), axis="X", limits_deg=(-(120.0 - tp), tp - hm.PIP_MIN_DEG),
             damping=FINGER_DAMP)

# -- the hand cone: on its side on a tray in front of the right arm, wide end overhanging towards the robot ------------
import conedemo  # noqa: E402

TRAY = Box("tray", pos=(conedemo.TRAY_C[0], conedemo.TRAY_C[1], TOP + conedemo.TRAY_SIZE[2] / 2), size=conedemo.TRAY_SIZE,
           color=(0.80, 0.80, 0.78))
RAILS = [Box(f"rail{k}", pos=(conedemo.TRAY_C[0] + 0.01, conedemo.TRAY_C[1] + s * 0.028, TOP + conedemo.TRAY_SIZE[2] + 0.006),
             size=(0.08, 0.008, 0.012), color=(0.55, 0.55, 0.55)) for k, s in enumerate((-1, 1))]
_cp, _cf, _cn = hm.cone_mesh()
_ct = conedemo.CONE_TILT
CONE = bk.Body.build("cone", conedemo.CONE_START, hm.CONE_MASS,
                     [bk.MeshShape((0.0, 0.0, 0.0), tuple(_cp), tuple(_cf), color=(0.55, 0.74, 0.90),
                                   normals=tuple(_cn), roughness=0.45),
                      bk.ConvexShape((0.0, 0.0, 0.0), tuple(_cp[:2 * 28]), tuple(_cf[:2 * 28]))],
                     start_xyzw=(0.0, math.sin(_ct / 2), 0.0, math.cos(_ct / 2)),
                     friction=(0.7, 0.6), solver_iterations=SOLVER_IT, contact_report=True)

HAND_NAMES = ["pillow", "palm", *PROX_NAMES, *DIST_NAMES]
OBJECTS = [*MARKS, TRAY, *RAILS, PILLOW, PALM, *PROX, *DIST, CONE]
HAND_START = {b.name: (np.array(b.pos), b.start_xyzw) for b in (PILLOW, PALM, *PROX, *DIST, CONE)}


def _np(x) -> np.ndarray:
    x = getattr(x, "torch", x)
    if hasattr(x, "detach"):
        return x.detach().cpu().numpy().astype(np.float64)
    return np.asarray(x.numpy(), dtype=np.float64)


# -- the tendons (every physics step) and the trial tracker (every control step) ---------------------------------------

class Hand:
    """Applies the tendon law every physics step and keeps each flexor gauge's peak."""

    def __init__(self):
        self.env = None
        self.views = None
        self.sub = None
        self.reset()

    def reset(self) -> None:
        self.peak = np.zeros(4)
        self.last = {}
        self.physics_steps = 0

    def attach(self, env) -> None:
        self.env = env
        if self.views is not None:
            return
        import warp as wp

        base = env.unwrapped
        self.wp = wp
        self.device = str(base.device)
        self.origin = _np(base.scene.env_origins)[0]
        self.names = HAND_NAMES + ["cone"]
        paths = [base.scene[n].root_view.prim_paths[0] for n in self.names]
        self.view = None
        try:  # one view over every hand body: one read and one write a physics step
            view = base.scene["palm"]._physics_sim_view.create_rigid_body_view(paths)
            if view.count == len(paths) and list(view.prim_paths) == paths:
                self.view = view
        except Exception as e:  # noqa: BLE001
            print(f"[cone] note: no combined body view ({e}); one view per body", flush=True)
        self.views = {n: base.scene[n].root_view for n in self.names}
        n = len(HAND_NAMES)
        self.all_idx = wp.array(np.arange(n, dtype=np.int32), dtype=wp.int32, device=self.device)
        self.idx = wp.array(np.zeros(1, dtype=np.int32), dtype=wp.int32, device=self.device)
        import omni.physx

        self.sub = omni.physx.get_physx_interface().subscribe_physics_on_step_events(self._physics_step, pre_step=True,
                                                                                      order=100)

    def poses(self) -> dict:
        out = {}
        if self.view is not None:
            t = _np(self.view.get_transforms())
            for k, n in enumerate(self.names):
                out[n] = (t[k, :3] - self.origin, t[k, 3:7])
            return out
        for n, v in self.views.items():
            t = _np(v.get_transforms())[0]
            out[n] = (t[:3] - self.origin, t[3:7])
        return out

    def angles(self, P: dict):
        R = {n: hm.rot(q) for n, (_, q) in P.items()}
        phi = hm.flex_angle(R["pillow"], R["palm"])
        tm = np.array([hm.flex_angle(R["palm"] @ hm.flex_rot(hm.CLENCH[i][0]), R[PROX_NAMES[i]]) for i in range(4)])
        tp = np.array([hm.flex_angle(R[PROX_NAMES[i]] @ hm.flex_rot(hm.CLENCH[i][1]), R[DIST_NAMES[i]]) for i in range(4)])
        return phi, tm, tp, R

    def _w(self, a) -> object:
        return self.wp.array(np.ascontiguousarray(a, dtype=np.float32), dtype=self.wp.float32, device=self.device)

    def apply(self, torques: dict, P: dict, forces: dict | None = None) -> None:
        """World torques on each hand body, applied at its origin, and any calibration-check forces at points."""
        forces = forces or {}
        n = len(self.names)  # data arrays cover the whole view (the cone gets nothing); indices pick the hand
        T = np.zeros((n, 3))
        F = np.zeros((n, 3))
        X = np.zeros((n, 3))
        X[n - 1] = P["cone"][0] + self.origin
        for k, name in enumerate(HAND_NAMES):
            T[k] = torques[name]
            X[k] = P[name][0] + self.origin
            if name in forces:
                F[k] = forces[name][0]
                X[k] = np.asarray(forces[name][1]) + self.origin
        if self.view is not None:
            self.view.apply_forces_and_torques_at_position(self._w(F), self._w(T), self._w(X), self.all_idx, True)
            return
        for k, name in enumerate(HAND_NAMES):
            self.views[name].apply_forces_and_torques_at_position(self._w(F[k:k + 1]), self._w(T[k:k + 1]),
                                                                  self._w(X[k:k + 1]), self.idx, True)

    def _physics_step(self, dt) -> None:
        if self.env is None or self.views is None:
            return
        try:
            P = self.poses()
        except Exception:  # noqa: BLE001  (views not ready during a reset)
            return
        self.physics_steps += 1
        phi, tm, tp, R = self.angles(P)
        tf, te, tw, tmcp, tpip = hm.tendons(phi, tm, tp)
        self.peak = np.maximum(self.peak, tf)
        self.last = {"phi": phi, "tm": tm, "tp": tp, "tf": tf, "te": te}
        torques = {n: np.zeros(3) for n in HAND_NAMES}
        ax = R["pillow"] @ np.array([-1.0, 0.0, 0.0])  # flexion turns about the parent's -x
        torques["palm"] += tw * ax
        torques["pillow"] -= tw * ax
        for i in range(4):
            a1 = R["palm"] @ np.array([-1.0, 0.0, 0.0])
            torques[PROX_NAMES[i]] += tmcp[i] * a1
            torques["palm"] -= tmcp[i] * a1
            a2 = R[PROX_NAMES[i]] @ np.array([-1.0, 0.0, 0.0])
            torques[DIST_NAMES[i]] += tpip[i] * a2
            torques[PROX_NAMES[i]] -= tpip[i] * a2
        forces = CHECK.step(self, P, R, phi, dt, torques) if CHECK is not None else None
        self.apply(torques, P, forces)


HAND = Hand()
CHECK = None
if os.environ.get("TASK_CHECK"):  # the calibration checks (handcheck.py); never in a trial
    import handcheck

    CHECK = handcheck.Check(os.environ["TASK_CHECK"])


class Tracker:
    """Runs after every control step; latches the zeros."""

    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self.trial = rules.Trial()
        self.end: dict = {}
        self.steps = 0
        self.noted: set = set()
        self.log = []

    def tcp(self, env, side: str):
        from yam_arena import ik, station
        from yam_arena.constants import ARM_JOINTS

        robot = env.unwrapped.scene[f"{side}_robot"]
        ids = robot.find_joints(list(ARM_JOINTS), preserve_order=True)[0]
        return ik.tcp_pose(_np(robot.data.joint_pos)[0, ids], station.BASES[side])

    def gripper_points(self, env) -> list:
        """Each gripper: its TCP and points along each pad, from 3 cm behind the TCP to the tip 13 mm ahead."""
        from yam_arena.constants import FINGER_JOINTS

        pts = []
        for side in ("left", "right"):
            t, r = self.tcp(env, side)
            robot = env.unwrapped.scene[f"{side}_robot"]
            ids = robot.find_joints(list(FINGER_JOINTS), preserve_order=True)[0]
            half = -float(np.mean(_np(robot.data.joint_pos)[0, ids]))
            pts.append(t)
            for sign in (1.0, -1.0):
                mid = t + sign * half * r[:, 0]
                for s in (-0.03, -0.015, 0.0, 0.013):
                    pts.append(mid + s * r[:, 2])
        return pts

    def hand_capsules(self, P: dict) -> list:
        caps = []
        for i in range(4):
            p, q = P[PROX_NAMES[i]]
            r = hm.rot(q)
            l1 = hm.LENGTHS[i][0]
            caps.append((p, p + r @ np.array([0.0, -l1, 0.0]), hm.RADII[i]))
            p, q = P[DIST_NAMES[i]]
            r = hm.rot(q)
            dip, tip = hm.distal_local(i)
            caps.append((p, p + r @ dip, hm.RADII[i]))
            caps.append((p + r @ dip, p + r @ tip, hm.RADII[i]))
        p, q = P["palm"]
        r = hm.rot(q)
        (tu0, tv0, tn0), (tu1, tv1, tn1), tr = hm.THUMB
        caps.append((p + r @ hm.uvn(tu0, tv0, tn0), p + r @ hm.uvn(tu1, tv1, tn1), tr))
        caps.append((p + r @ hm.uvn(0.091, -0.032, 0.0), p + r @ hm.uvn(0.091, 0.032, 0.0), hm.HALF_T))
        return caps

    def step(self, env) -> None:
        self.steps += 1
        P = HAND.poses()
        tips = []
        for i in range(4):
            p, q = P[DIST_NAMES[i]]
            tips.append(p + hm.rot(q) @ hm.distal_local(i)[1])
        obs = {"palm": P["palm"], "cone": P["cone"], "tips": tips,
               "pillow": (P["pillow"][0] - HAND_START["pillow"][0])[:2], "gauge": HAND.peak.copy(),
               "grippers": self.gripper_points(env), "hand": self.hand_capsules(P), "floor": PILLOW_TOP - 0.01}
        self.trial.update(obs)
        m = self.trial.m
        for why in self.trial.faults:
            if why not in self.noted:
                self.noted.add(why)
                print(f"[cone] zero: {why} (step {self.steps}) gauge {np.round(HAND.peak, 2)}", flush=True)
        last = HAND.last
        if last and (self.steps % int(os.environ.get("TASK_TRACE_EVERY", "20")) == 0):
            print(f"[cone] step {self.steps} wrist {math.degrees(last['phi']):.1f} deg mcp "
                  f"{np.round(np.degrees(last['tm']) + [c[0] for c in hm.CLENCH], 0)} pip "
                  f"{np.round(np.degrees(last['tp']) + [c[1] for c in hm.CLENCH], 0)} flexor {np.round(last['tf'], 2)} "
                  f"peak {np.round(HAND.peak, 2)} tier {m['tier_now']} curled {m['curled']} in_palm {m['in_palm']} "
                  f"clear {m['clear'] * 100:.1f} cm pillow {m['pillow'] * 1000:.1f} mm score {m['score']}", flush=True)
        self.end = m


TRIAL = Tracker()


@bk.on_reset
def _reset() -> None:
    HAND.reset()
    TRIAL.reset()
    if bk.env() is not None:
        HAND.attach(bk.env())


@bk.on_step
def _step(env) -> None:
    HAND.attach(env)
    TRIAL.step(env)


def score(objects) -> float:
    """The tier held for the last 2 s (cone_rules.Trial); 0 once any zero has latched."""
    return float(TRIAL.end.get("score", 0.0)) if TRIAL.end else 0.0


def success(objects) -> bool:
    steptime.tick()  # the harness calls success() once per control step
    return bool(TRIAL.end) and TRIAL.end.get("score") == 1.0


def demo():
    """Waypoints for each arm, played open loop by the harness's ``yam_scripted`` policy (conedemo.py)."""
    import conedemo

    return conedemo.plan(os.environ.get("TASK_DEMO", "success"))
