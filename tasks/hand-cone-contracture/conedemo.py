"""The scripted reference demo, open loop from the fixed start: Cartesian waypoints for each arm, played by the
harness's ``yam_scripted`` policy with IK on the arm's URDF. It reads nothing from the simulator while it runs.

1. The left gripper, pointing down, pinches across the hand just past the wrist and turns it up about the wrist,
   and holds it there. The wrist flexes about 40 degrees; the fingers fall half open.
2. The right gripper picks the cone by its wide end, which overhangs its box, carries it high over the open fingers
   and lowers it across the palm, wide end at the little-finger side.
3. The left eases the wrist back to straight over 2.5 s; the right follows with the cone. The fingers close round it.
4. Both grippers open and back away: the left rises, the right draws back along the cone's axis. Both go home.

TASK_DEMO=idle keeps both arms at home (the hand at rest). TASK_DEMO=force is the careless way: the left arm stays
home, the wrist straight, and the right presses the cone down onto the clenched fist on the same path.
"""

from __future__ import annotations

import math

import numpy as np

import bodykit as bk
import handmodel as hm
from yam_arena import ik, station
from yam_arena.constants import FINGER_OPEN, GRIPPER, READY
from yam_arena.demo import Waypoint

TOP = station.TABLE_TOP
PILLOW_TOP = TOP + hm.PILLOW_SIZE[2]
WRIST = np.array([hm.WRIST_XY[0], hm.WRIST_XY[1], PILLOW_TOP + hm.HALF_T + 0.0005])

FLEX_DEG = 62.0          # the left arm's commanded wrist flexion; the hand's springs hold it near 42 degrees
CONE_FLEX = 42.0         # where the hand is when flexed: the right arm aims the cone there
PINCH_FORCE = 30.0       # N a finger, across the hand
GRIP_U = 0.016           # where the left pinches across the hand (u, m from the wrist axis)
GRIP_N = 0.004           # and the TCP's height off the palm's mid-plane
SEAT = hm.CONE_SEAT      # the cone's middle on the palm (u, v)
SEAT_LIFT = 0.012        # the cone comes down to this far off the palm before the wrist eases back
TCP_ON_CONE = -0.054     # the right TCP along the cone's axis from its middle (the wide end is at -0.065)


def grip(x, z) -> np.ndarray:
    """A TCP rotation whose fingers point along ``z`` and close along ``x`` (world)."""
    x, z = np.asarray(x, float), np.asarray(z, float)
    z = z / np.linalg.norm(z)
    x = x - np.dot(x, z) * z
    x = x / np.linalg.norm(x)
    return np.column_stack([x, np.cross(z, x), z])


def finger_for(width: float, force: float = 0.0) -> float:
    """The finger joint target that closes the pads on something ``width`` across with about ``force`` N a finger."""
    return float(np.clip(-(width / 2 - force / GRIPPER["stiffness"]), FINGER_OPEN, 0.0))


DOWN_X = grip((-1, 0, 0), (0, 0, -1))     # left: pointing down, closing along x (across the hand)
LEVEL_Z = grip((0, 0, 1), (1, 0, 0))      # right: level, pointing +x along the cone, closing top and bottom


def hand_point(u: float, v: float, n: float, flex_deg: float) -> np.ndarray:
    """A hand-frame point in the world, with the wrist flexed ``flex_deg``."""
    return WRIST + hm.flex_rot(flex_deg) @ hm.uvn(u, v, n)


def tp(p) -> tuple:
    return tuple(float(v) for v in p)


def home(side: str, t: float = 2.5) -> Waypoint:
    pos, rot = ik.tcp_pose(np.array(READY, float), station.BASES[side])
    return Waypoint(t, tp(pos), FINGER_OPEN, "home", rot)


# the cone's start: on its side on a supply box, between two rails, wide end overhanging the box towards the robot
TRAY_C = (0.315, -0.15)
TRAY_SIZE = (0.10, 0.08, 0.12)
CONE_TILT = math.atan((hm.CONE_R_WIDE - hm.CONE_R_NARROW) / hm.CONE_LEN)   # lying on its side, its axis slopes
CONE_START = (TRAY_C[0] - 0.015, TRAY_C[1], TOP + TRAY_SIZE[2] + hm.cone_radius(0.0) / math.cos(CONE_TILT) + 0.0005)


def plan(mode: str = "success") -> dict:
    bk.allow_matrix_grips()
    if mode == "idle":
        return {"left": [home("left", 20.0)], "right": [home("right", 20.0)]}
    cone_flex = 0.0 if mode == "force" else CONE_FLEX

    # -- left: pinch across the hand, flex the wrist, hold, ease it back
    pinch = finger_for(hm.PALM_W_PROX, PINCH_FORCE)
    left_at = lambda deg: hand_point(GRIP_U, 0.0, GRIP_N, deg)  # noqa: E731
    left_rot = lambda deg: hm.flex_rot(deg) @ DOWN_X  # noqa: E731
    left = [
        Waypoint(2.5, tp(left_at(0) + [0, 0, 0.05]), FINGER_OPEN, "left: over the hand", DOWN_X),
        Waypoint(1.5, tp(left_at(0)), FINGER_OPEN, "left: down beside the hand", DOWN_X),
        Waypoint(1.0, tp(left_at(0)), pinch, "left: pinch across the hand", DOWN_X),
    ]
    n_arc = 8
    for k in range(1, n_arc + 1):
        d = FLEX_DEG * k / n_arc
        left.append(Waypoint(3.0 / n_arc, tp(left_at(d)), pinch, "left: flex the wrist", left_rot(d)))
    t_flexed = 2.5 + 1.5 + 1.0 + 3.0
    t_back = 13.0
    left.append(Waypoint(t_back - t_flexed, tp(left_at(FLEX_DEG)), pinch, "left: hold the wrist flexed", left_rot(FLEX_DEG)))
    n_ret, ret_t = 10, 2.5
    for k in range(1, n_ret + 1):
        d = FLEX_DEG * (1 - k / n_ret)
        left.append(Waypoint(ret_t / n_ret, tp(left_at(d)), pinch, "left: ease the wrist back", left_rot(d)))
    left += [
        Waypoint(1.0, tp(left_at(0)), pinch, "left: settle", DOWN_X),
        Waypoint(0.6, tp(left_at(0)), FINGER_OPEN, "left: let go", DOWN_X),
        Waypoint(1.2, tp(left_at(0) + [0, 0, 0.08]), FINGER_OPEN, "left: up and clear", DOWN_X),
        home("left"),
    ]

    # -- right: the cone by its wide end, down onto the open palm from above, then follow the wrist back
    axis = np.array([1.0, 0.0, 0.0])  # the cone's axis, wide end to narrow, across the palm
    pick = np.array(CONE_START) + TCP_ON_CONE * np.array([math.cos(CONE_TILT), 0.0, -math.sin(CONE_TILT)])
    hold = finger_for(2 * hm.cone_radius(TCP_ON_CONE), 10.0)
    seat_n = hm.HALF_T + hm.cone_radius(0.0)
    wide = finger_for(0.075)

    def tcp_for(deg: float, lift: float) -> np.ndarray:
        """The right TCP with the cone over its seat, ``lift`` off the palm, the wrist flexed ``deg``."""
        return hand_point(SEAT[0], SEAT[1], seat_n + lift, deg) + TCP_ON_CONE * axis

    right = [
        Waypoint(2.5, tp(pick + [-0.06, 0, 0.06]), wide, "right: above, behind the cone's wide end", LEVEL_Z),
        Waypoint(1.0, tp(pick + [-0.06, 0, 0]), wide, "right: down behind it", LEVEL_Z),
        Waypoint(1.2, tp(pick), wide, "right: round the wide end", LEVEL_Z),
        Waypoint(0.8, tp(pick), hold, "right: grip", LEVEL_Z),
        Waypoint(0.8, tp(pick + [0, 0, 0.05]), hold, "right: lift", LEVEL_Z),
        Waypoint(0.8, tp(tcp_for(cone_flex, 0.10) + [0, -0.06, 0.04]), hold, "right: up, over the fingers", LEVEL_Z),
        Waypoint(0.8, tp(tcp_for(cone_flex, 0.08)), hold, "right: over the palm", LEVEL_Z),
    ]
    t = 2.5 + 1.0 + 1.2 + 0.8 + 0.8 + 1.6
    right.append(Waypoint(t_flexed + 0.3 - t, tp(tcp_for(cone_flex, 0.03)), hold, "right: lower", LEVEL_Z))
    right.append(Waypoint(2.5, tp(tcp_for(cone_flex, SEAT_LIFT)), hold, "right: down to the palm", LEVEL_Z))
    t2 = t_flexed + 0.3 + 2.5
    right.append(Waypoint(t_back - t2, tp(tcp_for(cone_flex, 0.0)), hold, "right: set it on the palm", LEVEL_Z))
    for k in range(1, n_ret + 1):
        d = cone_flex * (1 - k / n_ret)
        right.append(Waypoint(ret_t / n_ret, tp(tcp_for(d, 0.0)), hold, "right: follow the palm down", LEVEL_Z))
    rest = tcp_for(0.0, 0.0)
    right += [
        Waypoint(1.0, tp(rest), hold, "right: settle", LEVEL_Z),
        Waypoint(0.6, tp(rest), FINGER_OPEN, "right: let go", LEVEL_Z),
        Waypoint(1.2, tp(rest - 0.06 * axis), FINGER_OPEN, "right: back off along the cone", LEVEL_Z),
        Waypoint(1.0, tp(rest - 0.08 * axis + [0, 0, 0.06]), FINGER_OPEN, "right: up", LEVEL_Z),
        home("right"),
    ]
    if mode == "force":  # the careless way: the wrist left straight, the cone pressed onto the clenched fist
        left = [home("left", 20.0)]
    return {"left": left, "right": right}
