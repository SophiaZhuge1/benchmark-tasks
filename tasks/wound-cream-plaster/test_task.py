"""Unit tests of the cream-and-plaster model and the scorer, without the simulator (pytest, harness Python)."""

from __future__ import annotations

import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import firstaid as F  # noqa: E402
import gripgeo  # noqa: E402
import rules  # noqa: E402
import scene as S  # noqa: E402

FAR = {"left": np.array([0.10, 0.30, 0.30]), "right": np.array([0.10, -0.30, 0.30])}


def rot(f, c):
    f = np.asarray(f, float) / np.linalg.norm(f)
    c = np.asarray(c, float) - f * (np.dot(c, f) / np.dot(f, f))
    c /= np.linalg.norm(c)
    return np.stack([c, np.cross(f, c), f], 1)


DOWN = rot((0, 0, -1), (0, 1, 0))


def hand(side, t=None, R=DOWN, ap=0.09, force=0.0):
    t = FAR[side] if t is None else np.asarray(t, float)
    return F.Hand(side, R, t, ap, list(gripgeo.tcp_boxes(ap)), {"tip_left": force, "tip_right": force})


def idle():
    return {k: hand(k) for k in F.SIDES}


class Rig:
    """Stand-in for the simulator's loose bodies in these tests: a tab held by a hand keeps its grip point at the hand's
    TCP (as friction keeps it in the fingers), reported with 2 N on both pads; everything else stays where it is."""

    def __init__(self, w):
        self.w = w
        self.pose = {"applicator": (w.app.b.copy(), np.diag([-1.0, -1.0, 1.0]))}
        for k in F.SIDES:
            self.pose[f"tab_{k}"] = F.tab_rest_pose(k)
        self.held = {}

    def step(self, hs, held=None):
        if held is not None:
            self.held = dict(held)
        contact = {k: {} for k in F.SIDES}
        for side, part in self.held.items():
            if part is None:
                continue
            p, R = self.pose[part]
            ax = F.tab_out(part[4:], R) if part.startswith("tab") else R[:, 0]
            x = S.TAB_GRIP if part.startswith("tab") else 0.03
            self.pose[part] = (hs[side].t - ax * x, R)
            contact[side][part] = (2.0, 2.0)
        self.w.step(hs, {"pose": self.pose, "contact": contact})


def tab_R(side):
    s = F.SIGN[side]
    b = math.radians(30)
    return rot((0, -s * math.cos(b), -math.sin(b)), (0, 0, 1))


def lay_plaster(w, rig):
    """Take both tabs on the stand, carry the strip and lay it centred on the wound (scripted hand poses)."""
    pts = {k: w.pl.tab_point(k) for k in F.SIDES}
    rig.step({k: hand(k, pts[k], tab_R(k), 0.09) for k in F.SIDES})
    for _ in range(F.TAKE_STEPS):
        rig.step({k: hand(k, pts[k], tab_R(k), 0.0) for k in F.SIDES}, {k: f"tab_{k}" for k in F.SIDES})
    assert w.grips.holding == {"left": "tab_left", "right": "tab_right"}
    assert w.pl.unhinge == ["left", "right"]
    top, _ = S.ARM.point(0.0, 0.0)
    targets = {k: top + np.array([0, F.SIGN[k] * (S.PL_LEN / 2 + 0.012), 0.016]) for k in F.SIDES}
    for a in np.linspace(0, 1, 30):
        rig.step({k: hand(k, pts[k] + (targets[k] + [0, 0, 0.05] - pts[k]) * a, tab_R(k), 0.0) for k in F.SIDES})
    for a in np.linspace(0, 1, 15):
        rig.step({k: hand(k, targets[k] + [0, 0, 0.05 * (1 - a)], tab_R(k), 0.0) for k in F.SIDES})
    assert w.pl.state == "skin"
    return targets


def test_cream_wipe_needs_a_loaded_bud_and_counts_double_dips():
    c = F.Cream()
    p, n = S.ARM.point(0.0, 0.0)
    tip = p + n * (S.APP_TIP_R - 0.0005)
    for k in range(10):
        c.step(tip + [0, 0.001 * k, 0], tip + [0, 0.001 * (k + 1), 0], held=True)
    assert c.coverage() == 0.0  # nothing on the bud
    assert c.touched_skin
    cup = np.array([S.CUP_C[0], S.CUP_C[1], S.CUP_Z + 0.004])
    c.step(cup + [0, 0, 0.05], cup, held=True)
    assert c.double_dip and c.load > 0


def test_cream_wipe_lays_a_film_from_the_load():
    c = F.Cream()
    cup = np.array([S.CUP_C[0], S.CUP_C[1], S.CUP_Z + 0.004])
    for _ in range(3):
        c.step(cup, cup, held=True)
    assert not c.double_dip and c.load == pytest.approx(F.LOAD_CAP)
    p, n = S.ARM.point(-0.008, 0.0)
    prev = p + n * (S.APP_TIP_R - 0.0005)
    c.step(prev + [0, 0, 0.02], prev, held=True)
    for k in range(1, 30):
        q, m = S.ARM.point(-0.008 + 0.0006 * k, 0.0)
        tip = q + m * (S.APP_TIP_R - 0.0005)
        c.step(prev, tip, held=True)
        prev = tip
    line = (np.abs(c.Sg) < 0.0005) & (np.abs(c.Y) < 0.006)
    assert np.all(c.h[line] >= F.COVER_H)
    assert c.h.max() <= F.DAB + 1e-9


def test_tabs_carry_and_lay_the_strip_centred():
    w = F.World()
    lay_plaster(w, Rig(w))
    off = w.pl.pad_offset()
    assert off[0] < 0.002 and off[1] < 1.0


def test_a_grip_needs_both_pads_pressing_and_lets_go_when_they_stop():
    g = F.Grips()
    g.step({"left": {"tab_left": (2.0, 0.6)}, "right": {}})
    assert g.holding["left"] is None  # one pad under 1 N: not held
    for _ in range(F.TAKE_STEPS - 1):
        g.step({"left": {"tab_left": (2.0, 1.1)}, "right": {}})
    assert g.holding["left"] is None  # a brush in passing does not take it
    g.step({"left": {"tab_left": (2.0, 1.1)}, "right": {}})
    assert g.holding["left"] == "tab_left"
    for _ in range(F.LET_GO_STEPS - 1):
        g.step({"left": {"tab_left": (2.0, 0.1)}, "right": {}})
    assert g.holding["left"] == "tab_left"
    g.step({"left": {"tab_left": (2.0, 0.1)}, "right": {}})
    assert g.holding["left"] is None


def _pull(w, rig, tg, steep):
    for a in np.linspace(0, 1, 40):
        g = tg["right"] + (np.array([0, -0.005 * a, 0.12 * a]) if steep else np.array([0, -0.13 * a, 0.012 * a]))
        rig.step({"left": hand("left", tg["left"], tab_R("left"), 0.0), "right": hand("right", g, tab_R("right"), 0.0)})


def test_shallow_pull_peels_steep_pull_lifts():
    for steep, expect in ((False, "held"), (True, "on")):
        w = F.World()
        rig = Rig(w)
        tg = lay_plaster(w, rig)
        _pull(w, rig, tg, steep)
        assert w.pl.liners["right"].state == expect
        if steep:
            assert w.pl.lift["right"] is not None


def test_a_strip_held_by_nothing_slides_with_the_pull():
    w = F.World()
    rig = Rig(w)
    tg = lay_plaster(w, rig)
    for _ in range(F.LET_GO_STEPS):
        rig.step({"left": hand("left", tg["left"], tab_R("left"), 0.09), "right": hand("right", tg["right"], tab_R("right"), 0.0)},
                 {"left": None, "right": "tab_right"})
    assert w.grips.holding["left"] is None
    for a in np.linspace(0, 1, 20):
        rig.step({"left": hand("left"), "right": hand("right", tg["right"] + [0, -0.03 * a, 0], tab_R("right"), 0.0)})
    assert w.pl.liners["right"].state == "on"
    assert w.pl.slid > 0.02


def _press(w, rig, side, y, s, forces):
    p, n = S.ARM.point(y, s)
    R = rot(-n, (0, -1, 0))
    t = p + n * (0.0128 - 0.004)
    hs = idle()
    hs[side] = F.Hand(side, R, t, 0.0, list(gripgeo.tcp_boxes(0.0)), dict(zip(("tip_left", "tip_right"), forces)))
    rig.step(hs)


def test_tack_needs_one_newton_under_each_pad_and_never_spreads():
    w = F.World()
    rig = Rig(w)
    tg = lay_plaster(w, rig)
    _pull(w, rig, tg, False)
    rig.step({"left": hand("left", tg["left"], tab_R("left"), 0.0), "right": hand("right", tg["right"] + [0, -0.2, 0.05], tab_R("right"), 0.09)},
             {"left": "tab_left", "right": None})
    _press(w, rig, "right", -0.035, 0.0, (0.6, 0.6))  # 1.2 N in all, but under 1 N on each pad
    assert not w.pl.tacked.any()
    _press(w, rig, "right", -0.035, 0.0, (1.2, 0.0))  # one pad pressing 1.2 N: only under that pad
    k1 = w.pl.tacked.sum()
    assert 0 < k1
    _press(w, rig, "right", -0.035, 0.0, (1.2, 1.2))
    k2 = w.pl.tacked.sum()
    assert k1 < k2 < (w.pl.wing & (w.pl.U < 0)).sum()


def test_scorer_tiers_and_zero_latches():
    t = rules.Tracker()
    w = F.World()
    t.update(w, idle())
    assert t.score() == 0.0
    w.cream.h[w.cream.zone] = 0.0001
    w.app.state = "binned"
    t.update(w, idle())
    assert t.score() == 0.25
    w.cream.double_dip = True
    t.update(w, idle())
    assert t.score() == 0.0 and "dipped" in t.latched


def test_stray_cream_counts_the_largest_single_smear():
    c = F.Cream()
    far = (np.abs(c.Y - 0.030) < 0.0009) & (np.abs(c.Sg) < 0.0009)  # about 1.8 x 1.8 mm, well past the margin
    c.h[far] = 0.0001
    other = (np.abs(c.Y + 0.030) < 0.0009) & (np.abs(c.Sg) < 0.0009)
    c.h[other] = 0.0001
    assert c.stray_area() <= rules.STRAY_MAX  # two small smears, each under 2 x 2 mm
    c.h[(np.abs(c.Y - 0.030) < 0.0015) & (np.abs(c.Sg) < 0.0015)] = 0.0001  # one grows to 3 x 3 mm
    assert c.stray_area() > rules.STRAY_MAX


def test_applicator_is_binned_only_when_it_lies_in_the_pot():
    w = F.World()
    pot = np.array([S.POT_C[0], S.POT_C[1], 0.02])
    up = np.array([0.0, 0.0, 1.0])
    R = np.stack([up, np.array([0, 1.0, 0]), np.cross(up, [0, 1.0, 0])], 1)
    w.app.set_pose(pot + [0, 0, 0.2], up, "right")
    assert w.app.state == "held"
    w.app.set_pose(pot + [0, 0, 0.2], up, None)
    assert w.app.state == "dropped"  # let go above the pot: still falling
    w.app.set_pose(pot - up * (S.APP_LEN / 2 - 0.05), up, None)
    assert w.app.state == "binned"


def test_cream_under_a_wing_spoils_it():
    w = F.World()
    w.cream.h[(np.abs(w.cream.Y + 0.03) < 0.003) & (np.abs(w.cream.Sg) < 0.003)] = 0.0002
    rig = Rig(w)
    tg = lay_plaster(w, rig)
    _pull(w, rig, tg, False)
    assert w.pl.creamed.any()


def test_tabs_pulled_apart_in_the_air_bare_the_strip_and_it_falls():
    w = F.World()
    rig = Rig(w)
    pts = {k: w.pl.tab_point(k) for k in F.SIDES}
    for _ in range(F.TAKE_STEPS):
        rig.step({k: hand(k, pts[k], tab_R(k), 0.0) for k in F.SIDES}, {k: f"tab_{k}" for k in F.SIDES})
    top, _ = S.ARM.point(0.0, 0.0)
    over = {k: top + np.array([0, F.SIGN[k] * (S.PL_LEN / 2 + S.TAB_GRIP), 0.05]) for k in F.SIDES}
    for a in np.linspace(0, 1, 30):
        rig.step({k: hand(k, pts[k] + (over[k] - pts[k]) * a, tab_R(k), 0.0) for k in F.SIDES})
    assert w.pl.state == "air"
    for a in np.linspace(0, 1, 20):  # pulled apart over the wound: both liners peel off in the hands
        rig.step({k: hand(k, over[k] + [0, F.SIGN[k] * 0.12 * a, 0], tab_R(k), 0.0) for k in F.SIDES})
    assert all(w.pl.liners[k].state == "held" for k in F.SIDES)
    assert w.pl.state == "fallen"
    t = rules.Tracker()
    t.update(w, idle())
    assert t.score() == 0.0 and "fell" in t.latched


def test_gripper_on_the_bare_pad_face_latches():
    w = F.World()
    rig = Rig(w)
    pts = {k: w.pl.tab_point(k) for k in F.SIDES}
    for _ in range(F.TAKE_STEPS):
        rig.step({k: hand(k, pts[k], tab_R(k), 0.0) for k in F.SIDES}, {k: f"tab_{k}" for k in F.SIDES})
    up = np.array([0, 0, 0.1])
    rig.step({k: hand(k, pts[k] + up, tab_R(k), 0.0) for k in F.SIDES})
    rig.step({k: hand(k, pts[k] + up + [0, F.SIGN[k] * 0.012, 0], tab_R(k), 0.0) for k in F.SIDES})  # pulled apart a little
    assert 0.003 < w.pl.liners["left"].p < S.PAD_HALF and w.pl.state == "air"
    assert not w.pl.touched_face
    c = w.pl.c - w.pl.en * 0.0015
    w.pl._face_check({"right": hand("right", c, rot((0, 0, -1), (1, 0, 0)), 0.0)})  # a jaw closed on the strip's middle
    assert w.pl.touched_face


def test_a_strip_let_fall_hanging_from_one_tab_lands_crooked():
    w = F.World()
    rig = Rig(w)
    pts = {k: w.pl.tab_point(k) for k in F.SIDES}
    for _ in range(F.TAKE_STEPS):
        rig.step({k: hand(k, pts[k], tab_R(k), 0.0) for k in F.SIDES}, {k: f"tab_{k}" for k in F.SIDES})
    rig.step({"left": hand("left", pts["left"] + [0, 0, 0.05], tab_R("left"), 0.0), "right": hand("right")},
             {"left": "tab_left", "right": None})
    for _ in range(F.LET_GO_STEPS + 1):
        rig.step({"left": hand("left", pts["left"] + [0, 0, 0.05], tab_R("left"), 0.0), "right": hand("right")})
    top, _ = S.ARM.point(0.0, 0.0)
    g = top + np.array([0, 0, S.TAB_GRIP + S.PL_LEN + 0.004])  # the strip hangs from the left tab, its end 4 mm over the skin
    for a in np.linspace(0, 1, 20):
        rig.step({"left": hand("left", pts["left"] + [0, 0, 0.05] + (g - pts["left"] - [0, 0, 0.05]) * a, tab_R("left"), 0.0),
                  "right": hand("right")})
    assert w.pl.state == "air"
    for _ in range(F.LET_GO_STEPS + 1):
        rig.step({"left": hand("left", g, tab_R("left"), 0.09), "right": hand("right")}, {"left": None, "right": None})
    assert w.pl.state == "fallen"


def _bud_at(tip, d=(0.0, 0.0, -1.0)):
    """The applicator's back end and direction that put its bud's end sphere centred on tip."""
    d = np.asarray(d, float) / np.linalg.norm(d)
    return np.asarray(tip, float) - d * (S.APP_LEN - S.APP_TIP_R), d


def test_bud_touching_any_body_but_the_cream_and_the_skin_counts():
    w = F.World()
    rb = S.APP_TIP_R
    cx, cy = S.CUP_C

    def what(tip, hands=None, held=True):
        b, d = _bud_at(tip)
        return F.bud_contact(F.bud_points(b, d), hands or idle(), w.pl, held)

    skin, n = S.ARM.point(0.0, 0.0)
    assert what(skin + n * (rb - 0.0005)) is None  # pressed on the wound
    assert what((cx, cy, S.CUP_Z + 0.0055)) is None  # in the dollop
    assert what((cx + S.CUP_R_TOP - 0.001, cy, S.CUP_Z + S.CUP_H + rb)) == "cup's rim or wall"  # wiped on the rim
    assert what((cx + S.CUP_R_BOT - rb, cy, S.CUP_Z + 0.02)) == "cup's rim or wall"
    assert what((cx + 0.013, cy, S.CUP_Z + 0.0012 + rb)) == "cup's bare floor"
    pot_wall = (S.POT_C[0] + S.POT_R - 0.0015 - rb, S.POT_C[1], 0.06)
    assert what(pot_wall) == "waste pot"
    assert what(pot_wall, held=False) is None  # falling into the pot as it is binned
    assert what((0.05, -0.30, rb)) == "table"
    assert what((S.XW + 0.08, 0.25, S.PAD_Z + rb)) == "underpad"
    assert what((S.TRAY_C[0], S.TRAY_C[1], S.TRAY_SIZE[2] + rb)) == "applicator tray"
    pl_top = w.pl.c + np.array([0.0, 0.0, S.PL_T / 2 + rb])
    assert what(pl_top) == "plaster"  # on the strip lying on its riser
    tp, _ = F.tab_rest_pose("left")
    assert what(tp + np.array([0.0, 0.012, S.TAB_THICK / 2 + rb])) == "plaster's liner tab"
    # a gripper's fingertip: a hand closed just over the bud
    probe = np.array([0.20, -0.10, 0.15])
    hs = idle()
    hs["left"] = hand("left", probe + [0, 0, 0.0], DOWN, 0.0)
    near = [b for b in hs["left"].posed()]
    pt = (near[0][1] + near[0][0] @ ((near[0][2] + near[0][3]) / 2))  # the middle of the hand's first collision box
    assert what(pt, hs) == "left gripper"
    assert what(probe + [0.0, 0.0, 0.2], hs) is None  # in the air


def test_bud_on_the_cup_rim_latches_zero_in_the_world():
    w = F.World()
    t = rules.Tracker()
    w.app.lifted_once, w.app.state = True, "dropped"
    R = np.eye(3)

    def step(tip):
        b, d = _bud_at(tip)
        R[:, 0] = d
        pose = {"applicator": (b, R.copy()), **{f"tab_{k}": F.tab_rest_pose(k) for k in F.SIDES}}
        w.step(idle(), {"pose": pose, "contact": {k: {} for k in F.SIDES}})
        t.update(w, idle())

    step((S.POT_C[0], S.POT_C[1], 0.004 + S.APP_TIP_R))  # let fall into the pot: allowed
    assert w.app.touched_other is None and t.latched is None
    w.app.state = "dropped"
    step((S.CUP_C[0] + S.CUP_R_TOP - 0.001, S.CUP_C[1], S.CUP_Z + S.CUP_H + S.APP_TIP_R))
    assert t.score() == 0.0 and "cup's rim" in t.latched


def _good_plaster(w):
    """Stub the plaster's state as fully done (centred, both liners binned, both wings tacked)."""
    pl = w.pl
    pl.covers_zone = lambda cr: True
    pl.pad_offset = lambda: (0.001, 1.0)
    pl.wing_done = lambda k: True
    for k in F.SIDES:
        pl.liners[k].state = "binned"


def _cover(w, frac):
    z = np.argwhere(w.cream.zone)
    w.cream.h[:] = 0.0
    n = int(round(frac * len(z)))
    for a, b in z[:n]:
        w.cream.h[a, b] = 0.0001


@pytest.mark.parametrize("frac,app,expect", [(0.95, "binned", 1.0), (0.85, "binned", 0.5), (0.76, "binned", 0.5),
                                              (0.60, "binned", 0.25), (0.0, "pouch", 0.25), (0.0, "dropped", 0.0)])
def test_a_good_plaster_with_short_cream_gets_partial_credit(frac, app, expect):
    w = F.World()
    _good_plaster(w)
    _cover(w, frac)
    w.app.state = app
    t = rules.Tracker()
    for _ in range(rules.HOLD_STEPS + 1):
        t.update(w, idle())
    assert t.score() == expect
    assert t.success_now() == (expect == 1.0)


def test_short_cream_caps_a_lesser_plaster():
    w = F.World()
    _good_plaster(w)
    w.pl.wing_done = lambda k: k == "right"  # one wing pressed: a 0.75 plaster
    w.app.state = "binned"
    t = rules.Tracker()
    for frac, expect in ((0.95, 0.75), (0.85, 0.5), (0.5, 0.0)):
        _cover(w, frac)
        t.update(w, idle())
        assert t.score() == expect, frac
    _cover(w, 0.5)
    w.pl.covers_zone = lambda cr: False  # no plaster on: short cream alone scores nothing
    t.update(w, idle())
    assert t.score() == 0.0
