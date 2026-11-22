"""The scripted reference demo, open loop from the fixed start: Cartesian waypoints for each arm, played by the
harness's ``yam_scripted`` policy with IK on the arm's URDF. It reads nothing from the simulator while it runs; the
points where the chain is picked up and where the chain meets the clip come from a logged first run (the chain's resting
place after the flapper is seated), as for any part that moves before it is grasped.

1. Each hand reaches into the tank over the rim and pinches one of the flapper's ear tabs by its front and back edges
   (the hole free between the fingers), tilted 25 degrees in. The hands draw the ears apart (each rubber arm bends
   outward) and slide the flapper back on the seat until each ear's hole is in line with its peg, outside its tip.
2. The left hand pushes its ear in over the left peg while the right hand holds the right ear spread; then the right
   hand pushes its ear in over the right peg while the left hand holds the left ear on. Both let go and lift clear.
3. The left hand parks. The right hand picks the chain up off the floor at the bead that leaves about 18 mm of slack,
   lifts it straight up, presses that bead into the clip's slot, holds it, lets go, draws its fingers back along the
   chain and parks.

Modes (TASK_DEMO): success; one_ear (the right ear is let go in front of its peg, never pushed on); slack (the chain is
clipped three beads too long).
"""

from __future__ import annotations

import math

import numpy as np

from yam_arena import ik, station
from yam_arena.constants import FINGER_OPEN, READY
from yam_arena.demo import Waypoint

import toiletkit as tk

TOP = station.TABLE_TOP


def allow_matrix_grips() -> None:
    """Let a Waypoint's ``yaw`` be a full 3x3 TCP rotation (world frame)."""
    from yam_arena import demo

    if getattr(demo, "_matrix_grips", False):
        return
    plain = demo.grip_rotation

    def grip_rotation(yaw=0.0):
        return np.asarray(yaw, float) if np.ndim(yaw) == 2 else plain(yaw)

    demo.grip_rotation = grip_rotation
    demo._matrix_grips = True


def grip(close, app) -> np.ndarray:
    """A TCP rotation whose fingers point along ``app`` and close along ``close`` (world)."""
    z = np.asarray(app, float)
    z = z / np.linalg.norm(z)
    x = np.asarray(close, float)
    x = x - np.dot(x, z) * z
    x = x / np.linalg.norm(x)
    return np.column_stack([x, np.cross(z, x), z])


def ear_grip(side: int, tilt_in: float = 25.0, fwd: float | None = None, yaw: float = 0.0) -> np.ndarray:
    """Fingers down, tilted ``tilt_in`` toward the midline and ``fwd`` toward +x, closing along x turned by ``yaw``
    (rad) about the vertical: the pads take an ear tab by its front and back edges, the hole free between them."""
    if fwd is None:
        fwd = 20
    a, b = math.radians(18), math.radians(fwd)
    app = np.array([math.sin(b) * math.cos(a), -side * math.sin(a), -math.cos(a) * math.cos(b)])
    close = -side * np.array([math.cos(yaw), math.sin(yaw), 0.0])
    return grip(close, app)


def park(P, side: str) -> None:
    """Out of the tank: straight up above the rim, then back beside the robot, clear of the tank."""
    sg = 1.0 if side == "left" else -1.0
    w = P.arms[side][-1]
    from yam_arena.demo import grip_rotation
    P.add(side, 1.5, (w.pos[0], w.pos[1], TOP + 0.33), FINGER_OPEN, "up out of the tank", ear_grip(int(sg), fwd=25.0))
    P.add(side, 1.5, (0.17, sg * 0.12, TOP + 0.33), FINGER_OPEN, "back over the tank's wall", ear_grip(int(sg), fwd=25.0))
    P.add(side, 2.0, (0.13, sg * 0.22, TOP + 0.20), FINGER_OPEN, "park beside the tank", np.asarray(grip_rotation(0.0)))


def home(side: str, t: float = 2.0) -> Waypoint:
    pos, rot = ik.tcp_pose(np.array(READY, float), station.BASES[side])
    return Waypoint(t, tuple(float(v) for v in pos), FINGER_OPEN, "home", rot)


OPEN = -0.017          # fingers 34 mm apart: round an ear tab 18 mm across
PINCH = -0.004         # closing on the tab's 18 mm with about 25 N a finger
PINCH_Z = 0.014        # the TCP this far above the ear's hole (F z), the pads on the tab's edges
SPREAD = 0.015         # each ear drawn this far outward to clear its peg's tip
PUSH_IN = -0.0035       # the TCP aimed this far past the ear's seated place: the arm gives, and the tab is pushed home
                       # against the peg's boss (2 mm in from its seated place) with a few newtons
LIFT_Z = 0.375         # carrying height of the TCP above the table (the seal clears the tank's rim)
IN_FWD = 30.0          # fingers tipped this far back toward the robot at the ears (the wrist clears the back wall)
CARRY_FWD = 25.0       # fingers tipped forward while carrying high (reach), which tips the seal up


class Plan:
    def __init__(self):
        self.arms = {"left": [], "right": []}
        self.t = {"left": 0.0, "right": 0.0}

    def add(self, side, dur, pos, f, label, rot):
        self.arms[side].append(Waypoint(float(dur), tuple(float(v) for v in pos), float(f), f"{side}: {label}", rot))
        self.t[side] += dur

    def both(self, dur, pl, pr, f, label, rl, rr, fr=None):
        self.add("left", dur, pl, f, label, rl)
        self.add("right", dur, pr, f if fr is None else fr, label, rr)

    def wait(self, side, until):
        """Hold the last waypoint until both arms' clocks agree at ``until``."""
        w = self.arms[side][-1]
        if until > self.t[side] + 1e-6:
            self.add(side, until - self.t[side], w.pos, w.finger, "wait", w.yaw)

    def sync(self):
        t = max(self.t.values())
        for s in self.arms:
            self.wait(s, t)


def ear_point(f_origin, side: int, spread: float = 0.0, dz: float = PINCH_Z) -> np.ndarray:
    """World position of the TCP pinching one ear (F frame not rotated): the hole's centre, drawn ``spread`` outward,
    raised ``dz``."""
    dx = tk.ARM_ROOT_X * (1.0 - math.cos(math.asin(min(abs(spread) / tk.ARM_ROOT_X, 0.9)))) if spread > 0 else 0.0
    return np.asarray(f_origin, float) + np.array((-dx, side * (tk.EAR_Y + spread), dz))


def spread_yaw(side: int, spread: float) -> float:
    """The ear tab's turn about the vertical when drawn ``spread`` outward (the arm pivots at its root)."""
    return side * math.asin(min(spread / tk.ARM_ROOT_X, 0.9))


def plan(mode: str, f_start, hinge_w, slot_w=None, chain_pick=None, chain_put=None) -> dict:
    """``f_start``: the flapper frame's origin at the start (world); ``hinge_w``: the pegs' axis point at y 0 (world);
    ``slot_w``: the clip's slot (world). ``chain_pick``/``chain_put``: logged chain points (world) for step 3."""
    allow_matrix_grips()
    P = Plan()
    f0 = np.asarray(f_start, float)
    h = np.asarray(hinge_w, float)
    R = {s: ear_grip(sg) for s, sg in (("left", 1), ("right", -1))}

    def Rs(side, spread, fwd=None):
        sg = 1 if side == "left" else -1
        return ear_grip(sg, fwd=fwd, yaw=0.0)

    def EP(side, origin, spread=0.0, dz=PINCH_Z):
        return ear_point(origin, 1 if side == "left" else -1, spread, dz)

    # 1. into the tank over the rim, and pinch both ear tabs (the flapper rests on the seat, ears in front of the pegs)
    for side, sg in (("left", 1.0), ("right", -1.0)):
        P.add(side, 2.5, (0.30, sg * 0.10, TOP + 0.33), OPEN, "up over the tank's rim", ear_grip(int(sg), fwd=25.0))
    P.both(2.0, EP("left", f0, dz=0.10), EP("right", f0, dz=0.10), OPEN, "over the ear tab", R["left"], R["right"])
    P.both(1.5, EP("left", f0), EP("right", f0), OPEN, "round the ear tab", R["left"], R["right"])
    P.both(0.8, EP("left", f0), EP("right", f0), PINCH, "pinch the ear tab", R["left"], R["right"])
    # draw the ears apart (each rubber arm bends outward), then slide the flapper back on the seat until each ear's
    # hole is in line with its peg, just outside the peg's tip
    lifted = f0 + np.array((0.0, 0.0, 0.002))
    P.both(1.5, EP("left", lifted, SPREAD), EP("right", lifted, SPREAD), PINCH, "draw the ears apart",
           Rs("left", SPREAD), Rs("right", SPREAD))
    P.both(1.5, EP("left", h, SPREAD), EP("right", h, SPREAD), PINCH, "holes in line with the pegs",
           Rs("left", SPREAD), Rs("right", SPREAD))
    # 2. left ear over its peg while the right hand holds its ear spread
    tip = tk.PEG_TIP_Y + 0.0035 - tk.EAR_Y  # spread at which the hole's inner face meets the peg's tip
    if mode == "one_ear":  # scripted failure: the right hand first takes its ear forward, out of line with its peg
        P.add("right", 1.0, EP("right", h + np.array((0.014, 0.0, 0.0)), SPREAD), PINCH, "right ear forward",
              Rs("right", SPREAD))
        P.wait("left", P.t["right"])
    P.add("left", 0.8, EP("left", h, tip), PINCH, "left ear's hole at its peg's tip", Rs("left", tip))
    P.add("left", 1.2, EP("left", h, PUSH_IN), PINCH, "push the left ear over its peg, home on its boss", Rs("left", 0.0))
    P.add("left", 0.5, EP("left", h, PUSH_IN), PINCH, "hold it pushed home", Rs("left", 0.0))
    P.wait("right", P.t["left"])
    if mode == "one_ear":  # scripted failure: the right ear is let go in front of its peg, never pushed on
        P.add("right", 0.6, EP("right", h + np.array((0.014, 0.0, 0.0)), SPREAD), OPEN, "let go of the right ear",
              Rs("right", SPREAD))
        P.add("right", 1.2, EP("right", h, SPREAD + 0.01, dz=0.12), OPEN, "lift clear", Rs("right", SPREAD))
        P.wait("left", P.t["right"])
    else:
        P.add("right", 0.8, EP("right", h, tip), PINCH, "right ear's hole at its peg's tip", Rs("right", tip))
        P.add("right", 1.2, EP("right", h, PUSH_IN), PINCH, "push the right ear over its peg, home on its boss",
              Rs("right", 0.0))
        P.add("right", 0.5, EP("right", h, PUSH_IN), PINCH, "hold it pushed home", Rs("right", 0.0))
    P.wait("left", P.t["right"])

    # let go: open a little, then lift straight up
    sides = ("left",) if mode == "one_ear" else ("left", "right")
    for sd in sides:
        P.add(sd, 0.6, EP(sd, h, -0.001), OPEN, "let go of the ear", Rs(sd, 0.0))
    for sd in sides:
        P.add(sd, 1.5, EP(sd, h, 0.004, dz=0.12), OPEN, "lift clear", Rs(sd, 0.0))
    P.sync()
    park(P, "right")
    if chain_pick is not None and chain_put is not None:
        _chain(P, mode, np.asarray(chain_pick, float), np.asarray(chain_put, float))
    park(P, "left")
    P.sync()
    return P.arms


def _chain_grip(fwd: float = 0.0, yaw: float = 30.0):
    """Down, tipped ``fwd`` deg toward +x, the fingers closing across the chain where it lies (yaw 0 closes along y)."""
    from yam_arena.demo import grip_rotation
    b = math.radians(fwd)
    Ry = np.array(((math.cos(b), 0, math.sin(b)), (0, 1, 0), (-math.sin(b), 0, math.cos(b))))
    return Ry @ np.asarray(grip_rotation(math.radians(yaw)), float)


PAD_MID = 0.005  # the pads' middle is this far past the TCP along the fingers


def _chain(P: Plan, mode: str, pick, put) -> None:
    """The right hand picks the chain up at the bead that gives the right slack (``pick``: where it lies on the
    tank's floor), lifts it over the flapper to the clip on the trip lever and presses that bead into the clip's slot
    (``put``), holds it there while the clip takes it, lets go and draws back."""
    s = "left"
    a0, b0 = math.radians(15), math.radians(-5)  # down, tipped 15 deg in from the right, closing along x
    down = grip((1.0, 0.0, 0.0), np.array((math.sin(b0) * math.cos(a0), -math.sin(a0), -math.cos(a0) * math.cos(b0))))
    a, b = math.radians(30), math.radians(30)  # from the right and from behind, 30 deg each, fingertips down to the clip
    app = np.array((math.sin(b) * math.cos(a), -math.sin(a), -math.cos(a) * math.cos(b)))
    app = app / np.linalg.norm(app)
    clip = grip((0.0, -1.0, 0.0), app)
    at = put - app * PAD_MID  # the TCP that puts the pads' middle at the slot
    P.add(s, 1.5, (0.27, 0.10, TOP + 0.33), CHAIN_OPEN, "over the tank's rim", ear_grip(-1, fwd=25.0))
    P.add(s, 2.0, pick + np.array((0, 0, 0.06)), CHAIN_OPEN, "over the chain", down)
    P.add(s, 1.2, pick, CHAIN_OPEN, "round the chain", down)
    P.add(s, 0.6, pick, CHAIN_PINCH, "pinch the chain at the bead", down)
    P.add(s, 1.5, pick + np.array((0, 0, 0.08)), CHAIN_PINCH, "lift the chain straight up", down)
    P.add(s, 2.0, at + np.array((0.016, 0., 0.012)), CHAIN_PINCH, "over the open end of the fork", clip)
    P.add(s, 1.0, at + np.array((0.012, 0., 0.)), CHAIN_PINCH, "line up at the fork mouth", clip)
    P.add(s, 1.5, at - np.array((0.002, 0., 0.)), CHAIN_PINCH, "press along the slot to its stop", clip)
    P.add(s, 0.4, at - np.array((0.002, 0., 0.)), CHAIN_PINCH, "maintain the seating load", clip)
    P.add(s, 0.6, at, RELEASE_OPEN, "let go of the chain", clip)
    P.add(s, 1.5, at - app * 0.05, RELEASE_OPEN, "draw the fingers back off the chain", clip)
    P.add(s, 1.2, at - app * 0.05 + np.array((0.0, -0.03, 0.04)), RELEASE_OPEN, "and up", clip)


CHAIN_OPEN, CHAIN_PINCH, RELEASE_OPEN = -0.010, 0.0, -0.030
