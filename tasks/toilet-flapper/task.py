"""Fit a new toilet flapper: hook its two ears over the overflow tube's pegs, seat it on the flush valve, and set its
bead chain into the clip on the trip lever with the right slack.

A two-piece toilet tank stands on the table, lid off and empty (water off, as when a flapper is changed), its back
toward the robot. The old flapper has been taken off. The new one rests on the flush valve's seat, 15 mm forward of its
place, its ears in front of the overflow tube's pegs and its bead chain lying on the tank's floor; the chain clip
already hangs from the trip lever's middle hole.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import flapscore  # noqa: E402
import robotpts  # noqa: E402
import scenekit  # noqa: E402
import steptime  # noqa: E402
import toiletkit as tk  # noqa: E402
from yam_arena.task_file import TABLE_TOP  # noqa: E402

SCENE = "station"
TOP = TABLE_TOP[SCENE]
MODE = os.environ.get("TASK_DEMO", "success")

ZF = tk.RAIL_H + tk.BOTTOM                    # the interior floor above the table
T0 = np.array((0.327, 0.0, TOP + ZF))         # tank frame origin (world)
# The new flapper has been put into the tank: its seal rests on the valve seat 15 mm forward of its fitted place, so its
# ears stand just in front of the pegs, and its chain lies on the tank's floor, round the valve to the right and back.
F_START = T0 + np.array((tk.TUBE_X + 0.015, 0.0, tk.PEG_Z))
CHAIN_PATH_T = ((0.062, -0.040, 0.003), (-0.040, -0.056, 0.003), (-0.040, -0.165, 0.003))

TOILET = tk.Toilet(name="toilet", pos=tuple(T0), size=(0.19, 0.43, 0.26), color=tk.CHINA)
FLAPPER = tk.Flapper(name="flapper", pos=tuple(F_START), size=(0.10, 0.07, 0.03), color=(0.1, 0.1, 0.1),
                     chain_path=tuple(tuple(float(v) for v in T0 + np.array(p)) for p in CHAIN_PATH_T))
OBJECTS = [TOILET, FLAPPER]
SUCCESS_HOLD_S = 0.0
# The demo video's views into the tank (tankcam.py, TASK_TANKCAM=<folder>), tank frame: eye, target, focal length (mm)
TANK_VIEWS = {"ears": ((0.12, -0.03, 0.43), (-0.050, 0.0, 0.07), 10.0),
              "clip": ((-0.01, 0.16, 0.40), (0.055, -0.01, 0.17), 12.0),
              # close views of each peg from low beside it, looking along the peg at the ear's tab
              "ear_l": ((-0.085, 0.150, 0.075), (-0.055, 0.036, 0.056), 24.0),
              "ear_r": ((-0.085, -0.150, 0.075), (-0.055, -0.036, 0.056), 24.0)}
if os.environ.get("TANKCAM_VIEW"):  # development: a viewpoint of one's own, "ex,ey,ez,tx,ty,tz" in the tank frame
    _v = [float(v) for v in os.environ["TANKCAM_VIEW"].split(",")]
    TANK_VIEWS = {"dev": (tuple(_v[:3]), tuple(_v[3:]), float(os.environ.get("TANKCAM_FOCAL", "11")))}


def _new_state():
    return {"n": 0, "log": [], "clip": tk.ClipCatcher(), "ears": tk.EarCatcher(), "push": tk.EarPush(), "scorer": flapscore.Scorer()}


_S = _new_state()


@scenekit.on_reset
def _reset(env):
    global _S
    _S["clip"].release()
    _S["ears"].release()
    _S = _new_state()


# -- measurements ---------------------------------------------------------------------------------------------------

DL = tk.chain_dirs_local(FLAPPER)
ANG = np.linspace(0, 2 * np.pi, 12, endpoint=False)


def hole_t(fraw, ear: str) -> np.ndarray:
    """An ear's hole centre in the tank frame (the ear body's origin is its arm's root)."""
    R = tk.rotmat(fraw["quat"][ear])
    return fraw["pos"][ear] + R @ np.array((-tk.ARM_ROOT_X, 0.0, 0.0)) - T0


def seal_rim(fraw) -> tuple:
    """Heights above the seat's top of 12 points round the seal's underside where it meets the seat ring, and the
    seal centre's offset from the valve's axis (m)."""
    R = tk.rotmat(fraw["quat"]["disk"])
    r = tk.SEAT_R - 0.003
    pts = np.stack([r * np.cos(ANG), r * np.sin(ANG), np.full_like(ANG, tk.DISK_TOP - tk.DISK_H)], 1) @ R.T + fraw["pos"]["disk"] - T0
    c = fraw["pos"]["disk"] - T0
    return pts[:, 2] - tk.SEAT_TOP, float(np.hypot(c[0], c[1]))


def lift_deg(fraw) -> float:
    """The flapper's angle up from flat (its seal's axis from the vertical)."""
    z = tk.rotmat(fraw["quat"]["disk"])[:, 2]
    return float(np.degrees(np.arccos(np.clip(z[2], -1.0, 1.0))))


def lug_w(fraw) -> np.ndarray:
    R = tk.rotmat(fraw["quat"]["disk"])
    return fraw["pos"]["disk"] + R @ (tk.LUG - np.array((tk.DISK_X, 0.0, 0.0)))


def slot_w(traw) -> np.ndarray:
    return _S["clip"].slot_world(traw)


def kit_points(fraw, traw) -> np.ndarray:
    """Points standing for the flapper, its chain and the lever, for the robot's 3 cm hands-off check."""
    R = tk.rotmat(fraw["quat"]["disk"])
    rim = []
    for z in (tk.DISK_TOP - tk.DISK_H, tk.DISK_TOP + tk.CUP_H):
        rim.append(np.stack([tk.DISK_R * np.cos(ANG), tk.DISK_R * np.sin(ANG), np.full_like(ANG, z)], 1))
    pts = [np.vstack(rim) @ R.T + fraw["pos"]["disk"], np.array([hole_t(fraw, e) + T0 for e in ("ear_l", "ear_r")])]
    pts.append(np.array([tk.bead_pos(fraw, b, DL) for b in range(FLAPPER.n_beads)
                         if tk.seg_name(b // tk.SEG_BEADS) in fraw["pos"]]).reshape(-1, 3))
    Rl = tk.rotmat(traw["quat"]["lever"])
    arm = np.stack([np.zeros(10), np.linspace(0, tk.LEVER_DIR * tk.LEVER_LEN, 10), np.zeros(10)], 1) @ Rl.T + traw["pos"]["lever"]
    pts.append(arm)
    return np.vstack(pts)


def _frame(env, fraw, traw, t) -> flapscore.Frame:
    ears = tuple(flapscore.ear_on_peg(hole_t(fraw, e), s, tk.TUBE_X, tk.PEG_Z, tk.HOLE, tk.BOSS_Y - 0.001,
                                      tk.PEG_TIP_Y) for e, s in (("ear_l", 1), ("ear_r", -1)))
    h, off = seal_rim(fraw)
    seat = flapscore.seated(h, off)
    slack = flapscore.slack_mm(_S["clip"].on, tk.BEAD_PITCH, lug_w(fraw), slot_w(traw))
    robot = robotpts.robot_points(env)
    kp = kit_points(fraw, traw)
    d = float(np.min(np.linalg.norm(robot[:, None, :] - kp[None, :, :], axis=2))) if len(robot) else 1.0
    _S["meas"] = {"seat_h_mm": np.round(1000 * h, 2).tolist(), "off_mm": round(1000 * off, 2),
                  "holes": [np.round(hole_t(fraw, e), 4).tolist() for e in ("ear_l", "ear_r")]}
    return flapscore.Frame(t=t, ears=ears, seat=seat, slack=slack, robot_dist=d)


# -- the scorer's handle press -----------------------------------------------------------------------------------------

def _lever_target(env, deg, stiff=None):
    import torch
    art = tk.articulation(env, "toilet")
    jid = [list(art.joint_names).index("lever_hinge")]
    dev = tk._t(art.data.joint_pos).device
    if stiff is not None:
        art.write_joint_stiffness_to_sim_index(stiffness=torch.tensor([[float(stiff)]], device=dev), joint_ids=jid)
    art.set_joint_position_target_index(target=torch.tensor([[math.radians(deg)]], device=dev, dtype=torch.float32),
                                        joint_ids=jid)


def _tcp(env, side) -> np.ndarray:
    """An arm's tool centre point (between the finger pads), from its gripper link's pose."""
    base = env.unwrapped
    robot = base.scene[f"{side}_robot"]
    i = list(robot.body_names).index("gripper")
    p = tk.as_np(robot.data.body_link_pos_w)[0, i] - tk.as_np(base.scene.env_origins)[0]
    q = tk.as_np(robot.data.body_link_quat_w)[0, i]
    return p + tk.rotmat(q) @ np.array((0.0, 0.0, 0.134))


def _set_lever(env):
    _lever_target(env, tk.lever_up_deg(-TOILET.lever_preload_deg))




def _press(env) -> tuple:
    """The scorer's one full press of the handle, computed from the scene (not simulated: a chain pulled taut between
    the clip and a flapper on its stop is beyond what this solver holds steadily): the lever turns the toilet's press
    angle, the clip's slot rises with it, and the chain, its length from the lug to the clipped bead, lifts the flapper
    about its pegs once taut, up to its stop against the overflow tube. It drops back seated if it is seated now and
    the chain is slack at rest. Returns (the flapper's lift in degrees, drops back seated)."""
    fraw, traw = tk.raw_state(env, "flapper"), tk.raw_state(env, "toilet")
    bead = _S["clip"].on
    if bead is None:
        return 0.0, False
    chain = (bead + 0.5) * tk.BEAD_PITCH
    lug_rest = tk.HINGE_T + tk.LUG
    lift = flapscore.press_lift_deg(chain, tk.clip_slot_T(), np.array(tk.LEVER_PIVOT),
                                    math.radians(tk.lever_up_deg(TOILET.press_deg)), tk.HINGE_T, tk.LUG,
                                    FLAPPER.open_limit_deg)
    h, off = seal_rim(fraw)
    slack_ok = np.linalg.norm(tk.clip_slot_T() - lug_rest) <= chain
    return lift, bool(flapscore.seated(h, off) and slack_ok)


@scenekit.on_step
def _step(env):
    try:
        _step_inner(env)
    except Exception:
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        raise


def _step_inner(env):
    _S["n"] += 1
    t = _S["n"] / 20.0
    if _S["n"] <= 2:
        _set_lever(env)
    fraw = tk.raw_state(env, "flapper")
    traw = tk.raw_state(env, "toilet")
    links = scenekit.robot_links(env)
    tips = np.array([links[s][k] for s in links for k in ("tip_left", "tip_right")])
    _S["clip"].update(_S["n"], fraw, traw, tips)
    _S["clip"].follow(traw)
    _S["push"].attach(env)
    _S["push_n"] = _S["push"].read(float(getattr(env.unwrapped, "physics_dt", 1.0 / 240.0)))
    _S["ears"].update(_S["n"], {"l": hole_t(fraw, "ear_l"), "r": hole_t(fraw, "ear_r")}, _S["push_n"])
    _S["tcp"] = [np.round(_tcp(env, side) - T0, 4).tolist() for side in ("left", "right")]
    sc = _S["scorer"]
    sc.update(_frame(env, fraw, traw, t))
    if sc.want_press:
        lift, seated = _press(env)
        sc.press_result(lift, seated)
        fraw, traw = tk.raw_state(env, "flapper"), tk.raw_state(env, "toilet")
        sc.update(_frame(env, fraw, traw, t))
    if os.environ.get("TASK_TANKCAM"):  # the demo video's view down into the tank (tankcam.py); not a policy camera
        import tankcam
        if _S["n"] == 1:
            env_path = tk.PATHS["toilet"].rsplit("/", 1)[0]
            tankcam.start(env_path, {k: (T0 + np.array(e), T0 + np.array(t), f) for k, (e, t, f) in TANK_VIEWS.items()})
        tankcam.step()
    _log(fraw, traw, sc)


def _log(fraw, traw, sc):
    out = os.environ.get("TASK_SCORE_DIR")
    if not out:
        return
    rec = {"step": _S["n"], "score": sc.score, "check": sc.last, "clip": _S["clip"].on, "meas": _S.get("meas"), "ear_on": dict(_S["ears"].on),
           "push": {k: round(v, 3) for k, v in _S["push_n"].items()},
           "disk": np.round(fraw["pos"]["disk"] - T0, 4).tolist(), "lift": round(lift_deg(fraw), 2),
           "spread": [round(float(fraw["joint"][k]), 4) for k in ("ear_l_spread", "ear_r_spread")],
           "lever": round(float(traw["joint"]["lever_hinge"]), 4), "tcp": _S.get("tcp"),
           "segs": [np.round(fraw["pos"][tk.seg_name(k)] - T0, 4).tolist() for k in range(FLAPPER.n_beads // tk.SEG_BEADS)
                    if tk.seg_name(k) in fraw["pos"]]}
    sw = slot_w(traw)
    bd = [float(np.linalg.norm(tk.bead_pos(fraw, b, DL) - sw)) for b in range(FLAPPER.n_beads)]
    b = int(np.argmin(bd))
    rec["slot_near"] = (b, round(1000 * bd[b], 1), np.round(1000 * (tk.bead_pos(fraw, b, DL) - sw), 1).tolist())
    if sc.press is not None:
        rec["press"] = sc.press
    _S["log"].append(rec)
    if _S["n"] % 20 == 0 or sc.press is not None:
        pathlib.Path(out).mkdir(parents=True, exist_ok=True)
        (pathlib.Path(out) / "task_log.json").write_text(json.dumps(_S["log"]))


def success(objects) -> bool:
    steptime.tick()
    return bool(_S["scorer"].success)


def score(objects) -> float:
    return float(_S["scorer"].score)


HINGE_W = T0 + tk.HINGE_T                     # the pegs' axis at y 0 (world)
SLOT_W = T0 + tk.clip_slot_T()                # the chain clip's slot at rest (world)
# Where the right hand picks the chain up (the bead that gives the right slack, where it lies on the tank's floor) and
# where it presses that bead into the clip's slot.
CHAIN_PICK = T0 + np.array((-0.040, -0.073, 0.012))  # bead 27's place on the floor: about 18 mm of slack
CHAIN_PUT = SLOT_W + np.array((-0.012, 0.009, -0.010))  # the held bead into the clip's slot
# the scripted failure "slack" picks the chain further along; it clips bead 30 (about 36 mm of slack)
CHAIN_PICK_FAULT = {"slack": T0 + np.array((-0.045, -0.087, 0.012))}
CHAIN_PUT_FAULT = {"slack": CHAIN_PUT + np.array((0.007, -0.003, 0.0))}  # that bead held where bead 27 would be


def demo():
    """Waypoints for each arm, played open loop by the harness's ``yam_scripted`` policy (flapdemo.py)."""
    import flapdemo
    return flapdemo.plan(MODE, F_START, HINGE_W, SLOT_W, CHAIN_PICK_FAULT.get(MODE, CHAIN_PICK),
                          CHAIN_PUT_FAULT.get(MODE, CHAIN_PUT))
