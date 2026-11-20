"""The scorer's rules as plain functions of the state, so they can be tested on hand-built states without a simulator.

The tracker in task.py builds an observation each control step:

    palm      (pos, quat_xyzw) of the hand's palm body; its frame is the hand frame (handmodel), body x = v, -y = u, z = n
    cone      (pos, quat_xyzw) of the cone; its body x runs from the wide end to the narrow end
    tips      the four fingertip centres (world), index to little
    pillow    the pillow's displacement from its start (m, on the table)
    gauge     each finger's flexor gauge peak so far (N)
    grippers  sample points on both grippers' fingers (world)
    hand      capsules (p0, p1, r) of the hand's fingers and thumb, and the palm box, for the clearance check
    floor     the pillow's top height (world z): the cone fell if it lies below it

Score tiers (held 2 s running, HOLD_STEPS control steps):
    1.0  the cone lies across the palm (in it, axis within 25 deg of the knuckle line, wide end at the little-finger
         side), all four fingertips curled over it; forearm within 2 cm of its marks; grippers 3 cm clear
    0.5  the cone in the palm under at least two curled fingertips; forearm and grippers as for 1.0
    0.25 the cone in the palm, fewer than two fingertips curled over it; forearm and grippers as for 1.0
Zeros, latched for the rest of the trial: any finger's gauge over the limit, the forearm 2 cm off its marks, the cone
fallen below the pillow's top. A gripper within 3 cm of the hand or cone scores the state 0 while it lasts.
"""

from __future__ import annotations

import math

import numpy as np

import handmodel as hm

HOLD_STEPS = 40          # 2 s at 20 Hz
CLEAR = 0.03             # grippers this far from the hand and the cone
PILLOW_TOL = 0.02        # forearm (pillow) from its tape marks
AXIS_TOL_DEG = 25.0      # the cone's axis from the palm's knuckle line
TIP_GAP = 0.005          # a fingertip this close to the cone's surface touches it
PALM_GAP = 0.006         # the cone this close to the palm surface rests on it
IN_PALM_U = (0.040, hm.PALM_LEN + 0.005)
IN_PALM_V = (-0.045, 0.045)


def rot(q) -> np.ndarray:
    return hm.rot(q)


def to_hand(palm, p) -> np.ndarray:
    """A world point in the hand frame (u, v, n)."""
    pp, pq = palm
    b = rot(pq).T @ (np.asarray(p, float) - np.asarray(pp, float))
    return np.array([-b[1], b[0], b[2]])


def cone_axis_hand(palm, cone) -> np.ndarray:
    """The cone's axis (wide to narrow) as a hand-frame unit vector (u, v, n)."""
    b = rot(palm[1]).T @ rot(cone[1])[:, 0]
    return np.array([-b[1], b[0], b[2]])


def cone_surface_gap(cone, p) -> tuple[float, float]:
    """(the gap from point ``p`` to the cone's surface, ``p``'s coordinate along the cone's axis from its middle)."""
    cp, cq = cone
    b = rot(cq).T @ (np.asarray(p, float) - np.asarray(cp, float))
    x = float(np.clip(b[0], -hm.CONE_LEN / 2, hm.CONE_LEN / 2))
    radial = math.hypot(b[1], b[2])
    gap = radial - hm.cone_radius(x)
    if abs(b[0]) > hm.CONE_LEN / 2:
        gap = math.hypot(max(gap, 0.0), abs(b[0]) - hm.CONE_LEN / 2)
    return gap, x


def curled(palm, cone, tip, r_tip: float) -> bool:
    """The fingertip touches the cone on its upper half (palm-side view: above the cone's axis, out of the palm)."""
    gap, _ = cone_surface_gap(cone, tip)
    if gap - r_tip > TIP_GAP:
        return False
    return float(to_hand(palm, tip)[2]) > float(to_hand(palm, cone[0])[2])


def in_palm(palm, cone) -> bool:
    """The cone's middle over the palm, its underside resting on the palm surface."""
    c = to_hand(palm, cone[0])
    if not (IN_PALM_U[0] <= c[0] <= IN_PALM_U[1] and IN_PALM_V[0] <= c[1] <= IN_PALM_V[1]):
        return False
    _, x = cone_surface_gap(cone, cone[0])
    # the lowest point of the cone's surface along the palm normal, near the middle
    a = cone_axis_hand(palm, cone)
    n_axis = c[2]
    r = hm.cone_radius(0.0)
    tilt = math.sqrt(max(0.0, 1.0 - a[2] ** 2))  # the axis' component in the palm plane
    low = n_axis - r * tilt
    return low - hm.HALF_T <= PALM_GAP


def across(palm, cone) -> bool:
    a = cone_axis_hand(palm, cone)
    return abs(a[1]) >= math.cos(math.radians(AXIS_TOL_DEG))


def wide_to_little(palm, cone) -> bool:
    """The axis runs wide to narrow towards the thumb (+v): the wide end is at the little-finger side."""
    return cone_axis_hand(palm, cone)[1] > 0


def _seg_dist(p, a, b) -> float:
    p, a, b = (np.asarray(x, float) for x in (p, a, b))
    ab = b - a
    t = float(np.clip(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-12), 0.0, 1.0))
    return float(np.linalg.norm(p - (a + t * ab)))


def clearance(obs) -> float:
    """The least distance from any gripper sample point to the hand (capsules and palm box) or the cone (m)."""
    best = 1.0
    pp, pq = obs["palm"]
    rp = rot(pq)
    half = np.array([hm.PALM_W / 2, hm.PALM_LEN / 2, hm.HALF_T])
    centre = np.array([0.0, -hm.PALM_LEN / 2, 0.0])
    for g in obs["grippers"]:
        g = np.asarray(g, float)
        for a, b, r in obs["hand"]:
            best = min(best, _seg_dist(g, a, b) - r)
        local = rp.T @ (g - np.asarray(pp, float)) - centre
        best = min(best, float(np.linalg.norm(np.maximum(np.abs(local) - half, 0.0))))
        gap, _ = cone_surface_gap(obs["cone"], g)
        best = min(best, gap)
    return best


def state_tier(obs) -> tuple[float, dict]:
    """The tier of this state alone, before the hold and the latched zeros."""
    palm, cone = obs["palm"], obs["cone"]
    curls = [curled(palm, cone, t, hm.RADII[i]) for i, t in enumerate(obs["tips"])]
    m = {"in_palm": in_palm(palm, cone), "across": across(palm, cone), "wide_little": wide_to_little(palm, cone),
         "curled": curls, "clear": clearance(obs), "pillow": float(np.linalg.norm(obs["pillow"]))}
    ok = m["clear"] >= CLEAR and m["pillow"] <= PILLOW_TOL
    n = sum(curls)
    if not ok or not m["in_palm"]:
        return 0.0, m
    if n == 4 and m["across"] and m["wide_little"]:
        return 1.0, m
    if n >= 2:
        return 0.5, m
    return 0.25, m


class Trial:
    """Latches the zeros and holds each tier for 2 s."""

    def __init__(self):
        self.faults: list[str] = []
        self.recent: list[float] = []
        self.score = 0.0
        self.m: dict = {}

    def update(self, obs) -> float:
        if max(obs["gauge"]) > hm.GAUGE_LIMIT and "gauge" not in self.faults:
            self.faults.append("gauge")
        if float(np.linalg.norm(obs["pillow"])) > PILLOW_TOL and "forearm" not in self.faults:
            self.faults.append("forearm")
        if float(np.asarray(obs["cone"][0])[2]) < obs["floor"] and "fell" not in self.faults:
            self.faults.append("fell")
        tier, self.m = state_tier(obs)
        self.recent = (self.recent + [tier])[-HOLD_STEPS:]
        held = min(self.recent) if len(self.recent) >= HOLD_STEPS else 0.0
        self.score = 0.0 if self.faults else held
        self.m.update({"tier_now": tier, "score": self.score, "faults": list(self.faults),
                       "gauge_peak": [round(float(g), 2) for g in obs["gauge"]]})
        return self.score
