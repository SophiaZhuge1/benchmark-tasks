"""The scoring rules, as a plain state machine fed once per control step with what an overhead video, a blot, a meter and
a scale would show. Pure Python and NumPy: test it on hand-built states with test_cellrules.py.

The tiers follow task.json's `scoring`, line by line (see `CellJudge.tier`).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

ORDER = ("zinc_1", "separator", "zinc_2", "spacer", "spring", "cap")
STACK = ("zinc_1", "separator", "zinc_2", "spacer", "spring")  # the cap rests on the spring by its top's inside
DIAM = {"zinc_1": 0.012, "zinc_2": 0.012, "separator": 0.019, "spacer": 0.0158, "spring": 0.015, "cap": 0.0193}
THICK = {"zinc_1": 0.0001, "zinc_2": 0.0001, "separator": 0.00026, "spacer": 0.0010, "spring": 0.0012}
CAP_H, CAP_TOP_T = 0.0020, 0.00025
CAN_ID = 0.0195
FLAT_MM = 0.5  # no edge raised more than this
STACK_TOL = 0.0004  # m: a part rests on the one below within this (above it)
SINK_TOL = 0.0001  # m: and how far it may sit into it (checked when the cap goes in and up to the press, not after it)
SPRING_GIVE = 0.0009  # m: the most the spring compresses under a press
FINGER_NEAR = 0.002  # m: a fingertip this close to a part's outline counts as touching it
MOVED = 0.0003  # m: a part moved by this in total during one contact with a gripper's fingertips is displaced
OUT_UP, OUT_SIDE = 0.006, 0.0115  # m: a part this far above the rim, or this far from the axis (past the wall), is out
CLEAR = 0.030  # m: fingers clear of the tools and of the cell
CAN_R = 0.010  # m: the can's outside radius
CLEAR_S = 1.0
ARM_AWAY = 0.05  # m: the left fingers this far from the can's axis: "the arm is away at a dish"
BAND_FULL, BAND_HALF = (0.080, 0.120), (0.050, 0.150)


@dataclass
class Layout:
    top: float  # the table
    axis: tuple  # the can's axis, x y
    floor: float  # the can's floor (inside)
    rim: float  # the can's rim
    stand: tuple  # the tweezer stand's slot centre x y, and the stand's top z
    holder: tuple  # the pipette's home origin (tip end) x y z


@dataclass
class Part:
    pos: np.ndarray  # the origin: centre of the bottom face (for the cap: of the skirt's bottom)
    rot: np.ndarray  # 3 x 3

    @property
    def up(self) -> np.ndarray:
        return self.rot[:, 2]

    def tilt_deg(self) -> float:
        return math.degrees(math.acos(max(-1.0, min(1.0, float(self.up[2])))))

    def centre_xy(self, height: float) -> np.ndarray:
        """The centre of the part's mid-plane, seen from above."""
        return (self.pos + self.up * height / 2)[:2]


def edge_rise_mm(part: Part, name: str) -> float:
    return DIAM[name] * math.sin(math.radians(part.tilt_deg())) * 1000.0


@dataclass
class Snapshot:
    t: float
    parts: dict  # name -> Part
    left: np.ndarray  # (n, 3) fingertip points
    right: np.ndarray
    tweezers: tuple  # (tips' centre, head) world points
    tweezers_tilt: float
    pipette: tuple  # (tip end, button top)
    pipette_tilt: float
    can_g: float
    spilled_g: float
    dispense_times: tuple  # times of dispenses onto the separator
    cap_pressing: bool = False  # the right arm's fingers bear on the cap's top


@dataclass
class CellJudge:
    lay: Layout
    arrived: dict = field(default_factory=dict)  # part -> time it first lay in the can
    frame: dict = field(default_factory=dict)  # part -> its centre xy in its placement frame
    frozen: set = field(default_factory=set)
    gripper_moved: list = field(default_factory=list)
    contact: dict = field(default_factory=dict)  # (side, part) -> the part's position when that contact began
    left_can: list = field(default_factory=list)  # parts that left the can after they had been laid in it
    peak: dict = field(default_factory=dict)  # part -> (highest over the rim, farthest from the axis) since it arrived, m
    cap_check: tuple | None = None  # the layers' check when the cap went in
    pre_press_check: tuple | None = None  # the layers' check in the latest step before the press began
    press_started: bool = False
    blot_wet: bool = False
    left_table: list = field(default_factory=list)
    pressed: bool = False
    clear_since: float | None = None
    last: Snapshot | None = None
    notes: list = field(default_factory=list)

    # -- per step ---------------------------------------------------------------------------------------------------
    def in_can(self, name: str, p: Part) -> bool:
        off = np.linalg.norm(p.pos[:2] - np.asarray(self.lay.axis))
        return off < CAN_ID / 2 and self.lay.floor - 0.0005 < p.pos[2] < self.lay.rim + 0.0005

    def offset(self, name: str, p: Part) -> float:
        h = THICK.get(name, CAP_H)
        return float(np.linalg.norm(p.centre_xy(h) - np.asarray(self.lay.axis)))

    def update(self, s: Snapshot) -> None:
        lay = self.lay
        for name, p in s.parts.items():
            if p.pos[2] < lay.top - 0.005:
                if name not in self.left_table:
                    self.left_table.append(name)
            if name not in self.arrived and self.in_can(name, p) and p.tilt_deg() < 45:
                self.arrived[name] = s.t
                k = ORDER.index(name)
                for below in ORDER[:k]:  # a part laid on top hides the ones below: their frames are final
                    self.frozen.add(below)
                if name == "cap":
                    self.cap_check = self.layers(s)
            elif name in self.arrived:
                up, side = p.pos[2] - lay.rim, float(np.linalg.norm(p.pos[:2] - np.asarray(lay.axis)))
                hi, far = self.peak.get(name, (-math.inf, 0.0))
                self.peak[name] = (max(hi, up), max(far, side))
                if (up > OUT_UP or side > OUT_SIDE) and name not in self.left_can:
                    self.left_can.append(name)  # each part once: lifted back out after it was laid in
        if s.cap_pressing and "cap" in self.arrived:
            self.press_started = True
        if "cap" in self.arrived and not self.press_started:
            self.pre_press_check = self.layers(s)
        away = s.left.size == 0 or float(np.min(np.linalg.norm(s.left[:, :2] - np.asarray(lay.axis), axis=1))) > ARM_AWAY
        for name in self.arrived:
            if name in self.frozen or name not in s.parts:
                continue
            p = s.parts[name]
            if away and self.in_can(name, p):
                self.frame[name] = p.centre_xy(THICK.get(name, CAP_H))
        # a gripper's direct contact displacing a part: its total travel over one contact (the cap press is exempt)
        if self.last is not None:
            for name, p in s.parts.items():
                q = self.last.parts.get(name)
                if q is None:
                    continue
                for side, pts in (("left", s.left), ("right", s.right)):
                    key = (side, name)
                    if side == "right" and (s.cap_pressing or self.last.cap_pressing) and self.under_cap(s, name):
                        self.contact.pop(key, None)  # the press: the fingers on the cap's top move the cap and the stack under it
                        continue
                    if not (touching(pts, p, name) or touching(getattr(self.last, side), q, name)):
                        self.contact.pop(key, None)
                        continue
                    start = self.contact.setdefault(key, q.pos.copy())
                    if np.linalg.norm(p.pos - start) >= MOVED and not any(g[1:] == key for g in self.gripper_moved):
                        self.gripper_moved.append((round(s.t, 2), side, name))
        # the blot: a fingertip in the wet separator's well
        if s.can_g > 0 and not ("cap" in s.parts and self.in_can("cap", s.parts["cap"])):
            for pts in (s.left, s.right):
                if pts.size and np.any((np.linalg.norm(pts[:, :2] - np.asarray(lay.axis), axis=1) < CAN_ID / 2) & (pts[:, 2] < lay.rim + 0.0015)):
                    self.blot_wet = True
        # the press: the right fingers on the cap, the cap seated and pushed below where the spring holds it
        if s.cap_pressing and "cap" in s.parts:
            rest = self.cap_rest(s)
            if rest is not None and self.seated(s) and s.parts["cap"].pos[2] < rest - 0.0002:
                self.pressed = True
        # fingers clear of the tools and of the cell (the press hand lifted away)
        if fingers_clear(s) and self.clear_of_cell(s):
            if self.clear_since is None:
                self.clear_since = s.t
        else:
            self.clear_since = None
        self.last = s

    def clear_of_cell(self, s: Snapshot) -> bool:
        """Every fingertip at least CLEAR from the can and the cap in its mouth."""
        pts = np.vstack([p for p in (s.left, s.right) if p.size]) if (s.left.size or s.right.size) else np.zeros((0, 3))
        if pts.size == 0:
            return True
        radial = np.maximum(np.linalg.norm(pts[:, :2] - np.asarray(self.lay.axis), axis=1) - CAN_R, 0.0)
        top = self.lay.rim + CAP_H
        vertical = np.maximum(np.maximum(pts[:, 2] - top, self.lay.top - pts[:, 2]), 0.0)
        return bool(np.hypot(radial, vertical).min() >= CLEAR)

    def under_cap(self, s: Snapshot, name: str) -> bool:
        """The cap, or a part lying in the can under the cap, while the cap is in the can's mouth."""
        cap = s.parts.get("cap")
        if cap is None or not self.in_can("cap", cap):
            return False
        return name == "cap" or (name in s.parts and self.in_can(name, s.parts[name]))

    # -- the state's checks -----------------------------------------------------------------------------------------
    def cap_rest(self, s: Snapshot) -> float | None:
        """The cap's origin height when its top's inside rests on the uncompressed spring, standing on the spacer."""
        if "spacer" not in s.parts:
            return None
        sp = s.parts["spacer"]
        return sp.pos[2] + sp.up[2] * THICK["spacer"] + THICK["spring"] - (CAP_H - CAP_TOP_T)

    def seated(self, s: Snapshot) -> bool:
        """Open side down, square, the gasket inside the can's mouth all round."""
        c = s.parts.get("cap")
        if c is None or c.up[2] < 0:
            return False
        return c.tilt_deg() < 2.0 and self.offset("cap", c) < 0.0004 and c.pos[2] < self.lay.rim and self.in_can("cap", c)

    def stacked(self, s: Snapshot, names) -> tuple[bool, str]:
        """Each part lies in the can, flat, on the one below (the first on the floor): at most STACK_TOL above it and
        SINK_TOL into it."""
        below = self.lay.floor
        for name in names:
            ok, why = self.placed(s, (name,))
            if not ok:
                return ok, why
            p = s.parts[name]
            give = SPRING_GIVE if name == "spring" else 0.0
            if not (below - SINK_TOL - give <= p.pos[2] <= below + STACK_TOL):
                return False, f"{name} not resting on the part below ({(p.pos[2] - below) * 1000:+.2f} mm)"
            below = p.pos[2] + p.up[2] * THICK[name]
        return True, ""

    def placed(self, s: Snapshot, names) -> tuple[bool, str]:
        """Each part lies in the can, flat (no height check: after the press the simulated thin discs sink into
        each other)."""
        for name in names:
            p = s.parts.get(name)
            if p is None or name not in self.arrived or not self.in_can(name, p):
                return False, f"{name} not in the can"
            if p.up[2] < 0 or edge_rise_mm(p, name) > FLAT_MM:
                return False, f"{name} not flat ({edge_rise_mm(p, name):.2f} mm edge rise)"
        return True, ""

    def layers(self, s: Snapshot) -> tuple:
        """The stacking check of the lower four parts and of all five under the cap."""
        return self.stacked(s, STACK[:4]) + self.stacked(s, STACK)

    def sinks_mm(self, s: Snapshot) -> dict:
        """Each part's height over the top of the one below (negative: sunk into it), mm; for the log."""
        out, below = {}, self.lay.floor
        for name in STACK:
            p = s.parts.get(name)
            if p is None:
                break
            out[name] = round((p.pos[2] - below) * 1000, 3)
            below = p.pos[2] + p.up[2] * THICK[name]
        return out

    def stack_ok(self, s: Snapshot, upto: int) -> tuple[bool, str]:
        """The layers rest on each other when the cap goes in and up to the press (or now, before the cap); after the
        press, only in the can and flat. `upto`: 4 (zinc to spacer) or 5 (to the spring)."""
        names = STACK[:upto]
        ok, why = self.placed(s, names)
        if not ok:
            return ok, why
        k = 0 if upto == 4 else 2
        checks = [self.cap_check, self.pre_press_check] if "cap" in self.arrived else [self.layers(s)]
        for c in checks:
            if c is not None and not c[k]:
                return False, c[k + 1] + (" when the cap went in" if c is self.cap_check else "")
        return True, ""

    def in_order(self, names) -> bool:
        times = [self.arrived.get(n) for n in names]
        return all(t is not None for t in times) and all(a < b for a, b in zip(times, times[1:]))

    def no_short(self, s: Snapshot, upto: str) -> bool:
        """The meter reads over R0: the separator lies between the zinc discs, and nothing of the upper electrode
        touches the can's wall."""
        z1, sep, z2 = (s.parts.get(n) for n in ("zinc_1", "separator", "zinc_2"))
        if None in (z1, sep, z2):
            return False
        sc = sep.centre_xy(THICK["separator"])
        cover = (DIAM["separator"] - DIAM["zinc_1"]) / 2
        if np.linalg.norm(z1.centre_xy(1e-4) - sc) > cover or np.linalg.norm(z2.centre_xy(1e-4) - sc) > cover:
            return False
        if self.offset("spacer", s.parts["spacer"]) >= (CAN_ID - DIAM["spacer"]) / 2:
            return False
        sp = s.parts.get("spring")
        if upto == "spring" and sp is not None and "spring" in self.arrived and self.in_can("spring", sp) and self.offset("spring", sp) >= (CAN_ID - DIAM["spring"]) / 2:
            return False
        return True

    def tools_stowed(self, s: Snapshot) -> bool:
        sx, sy, stop = self.lay.stand
        tips = np.asarray(s.tweezers[0])
        tw = abs(tips[0] - sx) < 0.004 and abs(tips[1] - sy) < 0.017 and tips[2] < stop - 0.010 and s.tweezers_tilt < 20.0
        d = np.asarray(s.pipette[0]) - np.asarray(self.lay.holder)  # the hook's collar on the cradle's prongs
        pip = -0.012 < d[0] < 0.015 and abs(d[1]) < 0.004 and abs(d[2]) < 0.002 and s.pipette_tilt < 10.0
        return bool(tw and pip)

    # -- the tier --------------------------------------------------------------------------------------------------
    def tier(self, s: Snapshot) -> tuple[float, str]:
        """task.json `scoring`: 1.0, 0.5, 0.25 or 0, and why."""
        fail = self.hard_fail(s)
        if fail:
            return 0.0, fail
        g = s.can_g
        zinc_off = max(self.frame_offset("zinc_1"), self.frame_offset("zinc_2"))
        zz = self.zinc_distance()
        lower_ok, why = self.stack_ok(s, 4)
        if not lower_ok:
            return 0.0, why
        if not self.in_order(STACK[:4]):
            return 0.0, "zinc, separator, zinc, spacer not in that order"
        if not self.electrolyte_in_order():
            return 0.0, "electrolyte not dispensed between the separator and the second zinc"
        if not self.no_short(s, "spring"):  # the meter: the separator between the zinc discs, no metal of the top on the wall
            return 0.0, "short: under R0"
        sp_off = self.frame_offset("spacer")
        if sp_off >= (CAN_ID - DIAM["spacer"]) / 2:  # the spacer on the wall: out of every tier
            return 0.0, f"spacer offset {sp_off * 1000:.2f} mm: on the wall"
        quarter = zinc_off <= 0.002 and zz <= 0.002 and BAND_HALF[0] <= g <= BAND_HALF[1]
        top_ok, why_top = self.stack_ok(s, 5)
        complete = (top_ok and self.in_order(ORDER) and self.seated(s) and self.pressed
                    and sp_off < (CAN_ID - DIAM["spacer"]) / 2)
        if not complete:
            if quarter:
                return 0.25, "spring or cap missing, inverted, not seated or not pressed" + (f" ({why_top})" if why_top else "")
            return 0.0, "the upper parts are not right and the lower stack is out of the 0.25 tier"
        stowed = self.tools_stowed(s)
        clear = self.clear_since is not None and s.t - self.clear_since >= CLEAR_S - 1e-9
        full = zinc_off <= 0.001 and zz <= 0.001 and sp_off <= 0.0015 and BAND_FULL[0] <= g <= BAND_FULL[1] and stowed and clear
        if full:
            return 1.0, "all checks hold"
        half = zinc_off <= 0.002 and zz <= 0.002 and BAND_HALF[0] <= g <= BAND_HALF[1]
        if half:
            misses = []
            if zinc_off > 0.001:
                misses.append(f"zinc offset {zinc_off * 1000:.2f} mm")
            if zz > 0.001:
                misses.append(f"zinc-to-zinc {zz * 1000:.2f} mm")
            if sp_off > 0.0015:
                misses.append(f"spacer offset {sp_off * 1000:.2f} mm")
            if not BAND_FULL[0] <= g <= BAND_FULL[1]:
                misses.append(f"electrolyte {g:.3f} g")
            if not stowed:
                misses.append("a tool not in its stand")
            if not clear:
                misses.append("fingers not 3 cm clear of the tools and the cell for 1 s")
            return 0.5, "; ".join(misses)
        return 0.0, "out of every tier"

    def hard_fail(self, s: Snapshot) -> str:
        if self.left_table:
            return f"{self.left_table[0]} left the table"
        if self.gripper_moved:
            t, side, name = self.gripper_moved[0]
            return f"the {side} gripper moved the {name} at {t} s"
        if self.left_can:
            return f"{self.left_can[0]} left the can after it was laid in"
        if self.blot_wet:
            return "electrolyte on a gripper"
        if s.spilled_g > 0:
            return "electrolyte dispensed outside the separator"
        if s.can_g < BAND_HALF[0] or s.can_g > BAND_HALF[1]:
            return f"electrolyte {s.can_g:.3f} g, out of 0.050-0.150 g"
        for n in ("zinc_1", "zinc_2"):
            if n in self.frame and self.frame_offset(n) > 0.002:
                return f"{n} offset over 2.0 mm"
        if "zinc_1" in self.frame and "zinc_2" in self.frame and self.zinc_distance() > 0.002:
            return "zinc-to-zinc centre distance over 2.0 mm"
        return ""

    def frame_offset(self, name: str) -> float:
        if name not in self.frame:
            return math.inf
        return float(np.linalg.norm(self.frame[name] - np.asarray(self.lay.axis)))

    def zinc_distance(self) -> float:
        if "zinc_1" not in self.frame or "zinc_2" not in self.frame:
            return math.inf
        return float(np.linalg.norm(self.frame["zinc_1"] - self.frame["zinc_2"]))

    def electrolyte_in_order(self) -> bool:
        if self.last is None or not self.last.dispense_times:
            return False
        a, b = self.arrived.get("separator"), self.arrived.get("zinc_2")
        return a is not None and b is not None and all(a < t < b for t in self.last.dispense_times)


def touching(pts: np.ndarray, p: Part, name: str) -> bool:
    """Fingertip points within FINGER_NEAR of the part's outline (a flat cylinder, or the cap's 2 mm body)."""
    if pts is None or pts.size == 0:
        return False
    h = THICK.get(name, CAP_H)
    local = (pts - p.pos) @ p.rot
    r = np.linalg.norm(local[:, :2], axis=1)
    return bool(np.any((r < DIAM[name] / 2 + FINGER_NEAR) & (local[:, 2] > -FINGER_NEAR) & (local[:, 2] < h + FINGER_NEAR)))


def _seg_dist(pts: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    ab = b - a
    t = np.clip((pts - a) @ ab / max(float(ab @ ab), 1e-12), 0.0, 1.0)
    return np.linalg.norm(pts - (a + t[:, None] * ab), axis=1)


TWEEZER_R, PIPETTE_R = 0.008, 0.015  # m: the tools' half widths about their axes


def fingers_clear(s: Snapshot) -> bool:
    pts = np.vstack([p for p in (s.left, s.right) if p.size]) if (s.left.size or s.right.size) else np.zeros((0, 3))
    if pts.size == 0:
        return True
    tw = _seg_dist(pts, np.asarray(s.tweezers[0]), np.asarray(s.tweezers[1])).min() - TWEEZER_R
    pp = _seg_dist(pts, np.asarray(s.pipette[0]), np.asarray(s.pipette[1])).min() - PIPETTE_R
    return bool(tw >= CLEAR and pp >= CLEAR)
