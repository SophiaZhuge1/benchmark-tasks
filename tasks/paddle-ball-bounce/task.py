"""On the station table, on a grey rubber mat: a table-tennis bat lying red face up on a wooden block in front of the
right arm, its handle towards the arm; a white 40 mm table-tennis ball in a white egg cup in front of the left arm; and
behind them a white board standing across the table, ruled every 1 cm, with a blue line 15 cm and a red line 25 cm above
the table.

The task: hold the bat red face up in the right hand, take the ball from the egg cup with the left hand and drop it onto
the bat, then keep it bouncing on the bat 10 times in a row without it touching anything else. Every bounce must rise
above the red line, and the bat's face must be below the blue line when it hits the ball.
"""

from __future__ import annotations

import math
import os
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # lets this file import helpers beside it

import scenekit  # noqa: E402
import steptime  # noqa: E402
import pongassets  # noqa: E402
import pongkit  # noqa: E402
from bounce_rules import BLUE_LINE, RED_LINE  # noqa: E402
from yam_arena.task_file import TABLE_TOP, Box  # noqa: E402

pongkit.install_physics_rate()

SCENE = "station"
TOP = TABLE_TOP[SCENE]
MAT_T = 0.003
FLOOR = TOP + MAT_T  # top of the mat
PROBE = os.environ.get("TASK_PROBE") == "1"  # development only: the bat on a tall block at the playing spot

USD = pongassets.write_all()

CUP_XY = (0.25, 0.20)
STAND_XY = (0.40, 0.0) if PROBE else (0.30, -0.16)
STAND_H = 0.1145 if PROBE else pongassets.STAND[2]
BLADE_Z0 = FLOOR + STAND_H + pongassets.BLADE_T / 2  # the bat's origin (blade centre) as it lies on the block
BOARD_X = 0.56

MAT = Box("mat", pos=(0.33, 0.0, TOP + MAT_T / 2), size=(0.44, 0.70, MAT_T), color=(0.32, 0.33, 0.34))
EGG_CUP = scenekit.UsdBody("egg_cup", pos=(*CUP_XY, FLOOR), usd=USD["egg_cup"], size=(0.044, 0.044, 0.05), own_materials=True)
BALL = scenekit.UsdBody("ball", pos=(*CUP_XY, FLOOR + pongassets.CUP_H + math.sqrt(0.02**2 - 0.015**2) + 0.0003),
                        usd=USD["ball"], mass=pongassets.BALL_MASS, size=(0.04, 0.04, 0.04), own_materials=True)
STAND = scenekit.UsdBody("stand", pos=(*STAND_XY, FLOOR), usd=USD["stand"], size=pongassets.STAND, own_materials=True)
if PROBE:
    STAND = scenekit.Shape("stand", pos=(*STAND_XY, FLOOR + STAND_H / 2), size=(0.12, 0.09, STAND_H), color=(0.45, 0.30, 0.17))
BAT = scenekit.UsdBody("bat", pos=(*STAND_XY, BLADE_Z0 + 0.0005), usd=USD["bat"], mass=pongassets.BAT_MASS,
                       size=(0.26, 0.15, 0.023), own_materials=True, solver_iters=32, torsional_patch=0.01)
BOARD = scenekit.UsdBody("board", pos=(BOARD_X, -0.30, TOP), usd=USD["board"], size=pongassets.BOARD, own_materials=True)
OBJECTS = [MAT, EGG_CUP, STAND, BAT, BALL, BOARD]


# -- scoring --------------------------------------------------------------------------------------------------------------

def _left_finger_points(tr) -> np.ndarray:
    """Points over the inner faces of the left gripper's two finger pads (world frame)."""
    gp, gq = tr.gripper_pose("left")
    rot = pongkit._quat_matrix(gq)
    robot = tr.env.unwrapped.scene["left_robot"]
    ids = robot.find_joints(["joint7", "joint8"])[0]
    q = pongkit._np(robot.data.joint_pos)[0, ids]
    half = float(np.mean(np.abs(q)))
    tcp = gp + rot @ np.array([0.0, 0.0, 0.134])
    pts = []
    for side in (-1.0, 1.0):
        for a in np.linspace(-0.05, 0.013, 8):
            for b in np.linspace(-0.018, 0.018, 4):
                pts.append(tcp + rot @ np.array([side * half, b, a]))
    return np.array(pts)


TRACKER = pongkit.Tracker(TOP, _left_finger_points)
if TRACKER.trace_path:
    import atexit

    atexit.register(TRACKER.save)


@scenekit.on_reset
def _reset(env) -> None:
    TRACKER.attach(env)
    TRACKER.reset()


@scenekit.on_step
def _step(env) -> None:
    TRACKER.attach(env)
    if TRACKER.trace_path and TRACKER.steps % 1000 < 30:
        TRACKER.save()


def score(objects) -> float:
    """The bounce count's tier (bounce_rules.py): 1.0 at 10 qualifying bounces in a row, 0.75 at 7 to 9, 0.5 at 4 to 6,
    0.25 at 1 to 3, and 0 for no qualifying bounce or a broken rule (no clean release, the left hand touching the ball
    after release, the bat slipping in the hand)."""
    return TRACKER.counter.score


def success(objects) -> bool:
    steptime.tick()  # the harness calls success() once per control step
    return TRACKER.counter.state == "done"


# -- the scripted demo (closed loop; reads the poses of the ball and the bat, which every camera sees) ------------------

def demo_script(ctx):
    import pongdemo

    yield from pongdemo.script(ctx, TOP)
