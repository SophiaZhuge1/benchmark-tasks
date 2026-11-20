"""Offline tests of the scorer (cone_rules) on hand-built states: every tier and every zero. No simulator.

    python -m pytest -q test_cone_rules.py
"""

from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import cone_rules as rules  # noqa: E402
import handmodel as hm  # noqa: E402

W = np.array([0.37, 0.07, 0.82])
IDENT = (0.0, 0.0, 0.0, 1.0)


def palm_pose(flex_deg: float = 0.0):
    return (W.copy(), hm.quat_of(hm.flex_rot(flex_deg)))


def hand_world(u, v, n, flex_deg=0.0):
    return W + hm.flex_rot(flex_deg) @ hm.uvn(u, v, n)


def cone_pose(u=hm.CONE_SEAT[0], v=hm.CONE_SEAT[1], n=None, flip=False, yaw_deg=0.0, flex_deg=0.0):
    """The cone lying across the palm, its middle at (u, v), its underside on the palm; ``flip``: wide end at the thumb
    side; ``yaw_deg``: turned in the palm plane."""
    r = hm.cone_radius(0.0)
    n = hm.HALF_T + r if n is None else n
    rc = hm.flex_rot(flex_deg) @ (np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], float))
    yaw = math.radians(yaw_deg + (180.0 if flip else 0.0))
    rz = np.array([[math.cos(yaw), -math.sin(yaw), 0], [math.sin(yaw), math.cos(yaw), 0], [0, 0, 1]])
    return (hand_world(u, v, n, flex_deg), hm.quat_of(rc @ rz))


def tips_on(cone, curled=(True, True, True, True), flex_deg=0.0):
    """Fingertip centres: on top of the cone (touching it, above its axis) or, if not curled, 4 cm beyond it."""
    cp, cq = cone
    rc = hm.rot(cq)
    out = []
    for i in range(4):
        v = hm.FINGER_V[i]
        x = float((rc.T @ (hand_world(0.0, v, 0.0, flex_deg) - hand_world(0.0, 0.0, 0.0, flex_deg)))[0])
        rad = hm.cone_radius(float(np.clip(x, -0.06, 0.06)))
        up = hm.flex_rot(flex_deg) @ np.array([0, 0, 1.0])
        if curled[i]:
            out.append(cp + rc @ np.array([x, 0.0, 0.0]) + up * (rad + hm.RADII[i] + 0.001))
        else:
            out.append(cp + rc @ np.array([x, 0.0, 0.0]) + up * (rad + 0.04))
    return out


def obs(cone=None, curled=(True,) * 4, gauge=(2.0,) * 4, pillow=(0.0, 0.0), grippers=None, flex_deg=0.0, tips=None):
    cone = cone if cone is not None else cone_pose(flex_deg=flex_deg)
    far = [np.array([0.0, -0.30, 1.10]), np.array([0.0, 0.30, 1.10])]
    return {"palm": palm_pose(flex_deg), "cone": cone, "tips": tips if tips is not None else tips_on(cone, curled, flex_deg),
            "pillow": np.array(pillow, float), "gauge": np.array(gauge, float),
            "grippers": far if grippers is None else grippers,
            "hand": [(hand_world(0.10, -0.03, 0.03), hand_world(0.12, -0.03, 0.05), 0.008)], "floor": W[2] - 0.03}


def run(o, steps=rules.HOLD_STEPS, trial=None):
    t = trial or rules.Trial()
    for _ in range(steps):
        t.update(o)
    return t


def test_full_score_after_2s():
    assert run(obs()).score == 1.0


def test_not_before_2s():
    assert run(obs(), steps=rules.HOLD_STEPS - 1).score == 0.0


def test_half_two_fingers():
    assert run(obs(curled=(True, True, False, False))).score == 0.5


def test_half_three_fingers():
    assert run(obs(curled=(True, True, True, False))).score == 0.5


def test_half_wrong_way_round():
    assert run(obs(cone=cone_pose(flip=True))).score == 0.5


def test_half_not_across():
    assert run(obs(cone=cone_pose(yaw_deg=35.0))).score == 0.5


def test_quarter_one_finger():
    assert run(obs(curled=(False, False, False, True))).score == 0.25


def test_quarter_no_finger():
    assert run(obs(curled=(False,) * 4)).score == 0.25


def test_zero_cone_off_palm():
    assert run(obs(cone=cone_pose(u=0.16))).score == 0.0


def test_zero_cone_lifted_off_palm():
    assert run(obs(cone=cone_pose(n=hm.HALF_T + hm.cone_radius(0.0) + 0.02))).score == 0.0


def test_zero_gauge_any_time():
    t = run(obs(gauge=(2.0, 5.2, 2.0, 2.0)), steps=1)
    run(obs(), trial=t)
    assert t.score == 0.0 and "gauge" in t.faults


def test_gauge_at_limit_ok():
    assert run(obs(gauge=(hm.GAUGE_LIMIT,) * 4)).score == 1.0


def test_zero_forearm_moved():
    t = run(obs(pillow=(0.0, 0.025)), steps=1)
    run(obs(), trial=t)
    assert t.score == 0.0 and "forearm" in t.faults


def test_forearm_within_marks_ok():
    assert run(obs(pillow=(0.012, 0.012))).score == 1.0


def test_zero_cone_fell():
    cone = (np.array([0.30, -0.10, W[2] - 0.08]), IDENT)
    t = run(obs(cone=cone), steps=1)
    run(obs(), trial=t)
    assert t.score == 0.0 and "fell" in t.faults


def test_zero_gripper_close():
    cp = cone_pose()[0]
    near = [cp + np.array([-0.07, 0.0, 0.0])]  # 0.5 cm off the wide end's face
    assert run(obs(grippers=near)).score == 0.0


def test_gripper_clear_3cm_ok():
    cp = cone_pose()[0]
    clear = [cp + np.array([-0.065 - 0.031, 0.0, 0.0])]
    assert run(obs(grippers=clear)).score == 1.0


def test_gripper_must_stay_clear_whole_hold():
    cp = cone_pose()[0]
    t = run(obs(), steps=rules.HOLD_STEPS - 5)
    t.update(obs(grippers=[cp]))
    run(obs(), steps=rules.HOLD_STEPS - 2, trial=t)
    assert t.score == 0.0
    run(obs(), steps=2, trial=t)
    assert t.score == 1.0


def test_zero_nothing_done():
    cone = (np.array([0.30, -0.15, W[2] + 0.05]), IDENT)  # still on its box, away from the hand
    assert run(obs(cone=cone, tips=tips_on(cone_pose(), (False,) * 4))).score == 0.0


def test_flexed_wrist_full_tier_state():
    """The tiers follow the hand: the same fit with the hand flexed scores the same (the hold is what the zeros guard)."""
    assert run(obs(flex_deg=40.0)).score == 1.0
