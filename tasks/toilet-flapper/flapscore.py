"""The scorer as plain functions and one small state machine. NumPy only (tested offline by test_flapscore.py).

Each control step the task measures a :class:`Frame` from the simulator. The score follows task.json's ``scoring``:

- 0.25 when at least one ear is on its peg (the peg through the ear's hole);
- 0.5 when both ears are on their pegs and the flapper is seated flat on the valve seat;
- 1.0 when, besides, the chain is in the lever's clip with 10 to 20 mm of slack, and then, with the robot at least
  3 cm clear, one full press of the handle (the scorer's own, once) lifts the flapper at least 60 degrees and it drops
  back seated;
- 0 while any part of the robot is within 3 cm of the flapper, its chain or the lever.

A press that fails (the flapper lifts less than 60 degrees, or does not drop back seated) caps the score at 0.5 for
the rest of the trial.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

HOLD_S = 1.0             # the full-score state, robot clear, before the press
CLEAR_M = 0.030          # every part of the robot at least this far from the flapper, chain and lever
SLACK_MM = (10.0, 20.0)  # chain slack at rest: the arm's hole rises this far before the chain lifts the flapper
LIFT_DEG = 60.0          # the flapper must lift at least this far on the press
SEAT_GAP_M = 0.0006      # seated: every point round the seal's rim within this of the seat (a 0.5 mm feeler can't enter)
SEAT_OFF_M = 0.006       # ... with the seal's centre within this of the valve's axis


def ear_on_peg(hole_t, side: int, tube_x: float, peg_z: float, hole: float, y_in: float, y_tip: float) -> bool:
    """Is the peg through the ear's hole? ``hole_t``: the hole's centre in the tank frame; ``side`` +1 (left peg) or
    -1 (right peg). The hole's centre must lie on the peg: within the hole's half-size of the peg's axis, between the
    peg's root (boss) and its tip."""
    x, y, z = hole_t
    radial = math.hypot(x - tube_x, z - peg_z)
    return bool(radial < hole / 2 and y_in < side * y < y_tip)


def seated(rim_heights, centre_offset: float) -> bool:
    """``rim_heights``: heights (m) of points round the seal's underside above the seat's top surface; the seal's
    centre offset (m) from the valve's axis."""
    h = np.asarray(rim_heights, float)
    return bool(centre_offset < SEAT_OFF_M and np.all(h < SEAT_GAP_M) and np.all(h > -0.003))


def slack_mm(bead: int | None, pitch: float, lug, slot) -> float | None:
    """Chain slack (mm) with bead ``bead`` in the clip: the chain's length from the lug to that bead's centre less the
    straight distance from the lug to the clip's slot."""
    if bead is None:
        return None
    return 1000.0 * ((bead + 0.5) * pitch - float(np.linalg.norm(np.asarray(slot) - np.asarray(lug))))


def rot_x(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array(((1, 0, 0), (0, c, -s), (0, s, c)))


def rot_y(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array(((c, 0, s), (0, 1, 0), (-s, 0, c)))


def press_lift_deg(chain_len: float, slot_rest, pivot, lever_rad: float, hinge, lug_f, stop_deg: float) -> float:
    """The flapper's lift (deg) on a full handle press: the lever turns ``lever_rad`` about its pivot (x axis), the
    clip's slot rises, and the chain (``chain_len`` from the lug to the clipped bead) lifts the lug about the hinge
    once it is taut, up to the flapper's stop against the overflow tube. All points in the tank frame."""
    slot = np.asarray(pivot) + rot_x(lever_rad) @ (np.asarray(slot_rest) - np.asarray(pivot))
    for k in range(0, int(stop_deg * 10) + 1):
        th = math.radians(k / 10)
        lug = np.asarray(hinge) + rot_y(-th) @ np.asarray(lug_f)
        if np.linalg.norm(slot - lug) <= chain_len:
            return k / 10
    return float(stop_deg)


@dataclass
class Frame:
    t: float
    ears: tuple                 # (left on, right on)
    seat: bool
    slack: float | None         # mm, None when the chain is not in the clip
    robot_dist: float           # m, robot to the flapper, chain and lever


class Scorer:
    def __init__(self):
        self.score = 0.0
        self.success = False
        self.press = None       # None, or the press's result dict
        self.want_press = False
        self._since = None
        self.last = {}

    @staticmethod
    def tier(f: Frame) -> float:
        if f.robot_dist < CLEAR_M:
            return 0.0
        if all(f.ears) and f.seat:
            return 0.5
        if any(f.ears):
            return 0.25
        return 0.0

    @staticmethod
    def full_state(f: Frame) -> bool:
        return (all(f.ears) and f.seat and f.slack is not None and SLACK_MM[0] <= f.slack <= SLACK_MM[1]
                and f.robot_dist >= CLEAR_M)

    def update(self, f: Frame) -> None:
        tier = self.tier(f)
        full = self.full_state(f)
        self.last = {"tier": tier, "full": full, "ears": list(f.ears), "seat": f.seat,
                     "slack": None if f.slack is None else round(f.slack, 1), "dist": round(f.robot_dist, 3)}
        if self.success:
            self.score = 1.0
            return
        if self.press is None and full:
            self._since = f.t if self._since is None else self._since
            if f.t - self._since >= HOLD_S - 1e-9:
                self.want_press = True
        else:
            self._since = None
        self.score = tier if self.press is None else min(tier, 0.5)

    def press_result(self, lift_deg: float, reseated: bool) -> None:
        self.want_press = False
        ok = bool(lift_deg >= LIFT_DEG and reseated)
        self.press = {"lift_deg": round(float(lift_deg), 1), "reseated": bool(reseated), "ok": ok}
        if ok:
            self.success = True
            self.score = 1.0
        else:
            self.score = min(self.score, 0.5)
