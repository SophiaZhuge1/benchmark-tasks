"""pongkit: what the task needs from the simulator, beyond scenekit.

- Physics at 500 Hz instead of the harness's 240 Hz (a hit lasts about a millisecond), set when ``yam_arena.scene`` is
  imported and before the environment is built. Nothing in yam_arena is edited.
- A tracker that runs after every physics step: it reads the PhysX contact report for the ball and the bat, sorts what
  touches the ball into the classes of ``bounce_rules``, and feeds ``BounceCounter``. It also checks, while the count
  runs, that the bat stays in the right hand: the bat touches nothing but the ball and the right arm, and its pose in the
  right gripper's frame moves less than 10 mm and 5 degrees from where it was at the first hit.

Everything that needs Isaac Sim is imported lazily, after the simulator starts. With ``TASK_TRACE=<file.npz>`` the tracker
also saves the ball's and bat's states at every physics step, for checking the physics.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import numpy as np

import scenekit
from bounce_rules import BounceCounter

PHYSICS_HZ = 500
FACE_COS = np.cos(np.radians(20.0))
HOLD_MM, HOLD_DEG = 10.0, 5.0
FORCE_EPS = 1e-4  # N: a contact with less force than this (over a physics step) is not a touch
BAT_EPS = 0.02  # N: the bat is held with tens of newtons, so its unexplained remainder is judged more loosely


def _patch_physics(scene) -> None:
    scene.PHYSICS_DT = 1.0 / PHYSICS_HZ


def install_physics_rate() -> None:
    import sys

    if "yam_arena.scene" in sys.modules:
        _patch_physics(sys.modules["yam_arena.scene"])
    patch = scenekit._Finder.targets["yam_arena.scene"]
    if getattr(patch, "_pong", False):
        return

    def both(module):
        patch(module)
        _patch_physics(module)

    both._pong = True
    scenekit._Finder.targets["yam_arena.scene"] = both


def _quat_matrix(q) -> np.ndarray:
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def _np(a) -> np.ndarray:
    if hasattr(a, "torch") and not hasattr(a, "detach"):
        a = a.torch
    if hasattr(a, "detach"):
        a = a.detach().cpu().numpy()
    elif hasattr(a, "numpy"):
        a = a.numpy()
    return np.asarray(a, dtype=np.float64)


def classify(path: str) -> str:
    if "left_robot" in path:
        return "left"
    if "right_robot" in path:
        return "right"
    if path.rstrip("/").split("/")[-1] == "bat" or "/bat/" in path:
        return "bat"
    if path.rstrip("/").split("/")[-1] == "ball" or "/ball/" in path:
        return "ball"
    return "other"


class Tracker:
    def __init__(self, table_top: float, finger_points):
        self.table_top = table_top
        self.finger_points = finger_points  # callable(env) -> (n, 3) points on the left fingers, world frame
        self.env = None
        self.subs = []
        self.trace_path = os.environ.get("TASK_TRACE")
        self.reset()

    def reset(self) -> None:
        self.counter = BounceCounter(self.table_top)
        self.t = 0.0
        self.steps = 0
        self.bat_ref = None  # bat pose in the right gripper's frame at the first hit
        self.bat_touch_bad = ""
        self.trace = []
        self.events = []
        self.active = False
        self._right_touch = False
        self.cpu_s = 0.0

    # -- reading the simulator ----------------------------------------------------------------
    def _origin(self):
        return self.origin

    def _rigid(self, name):
        asset = self.env.unwrapped.scene[name]
        pose = _np(asset.root_view.get_transforms())[0]
        vel = _np(asset.root_view.get_velocities())[0]
        return pose[:3] - self._origin(), pose[3:7], vel[:3], vel[3:6]

    def gripper_pose(self, side: str):
        robot = self.env.unwrapped.scene[f"{side}_robot"]
        poses = _np(robot.root_view.get_link_transforms())[0]
        i = robot.body_names.index("gripper")
        return poses[i, :3] - self._origin(), poses[i, 3:7]

    def _bat_in_gripper(self):
        bp, bq, _, _ = self._rigid("bat")
        gp, gq = self.gripper_pose("right")
        rg = _quat_matrix(gq)
        return rg.T @ (bp - gp), rg.T @ _quat_matrix(bq)

    # -- hooks ----------------------------------------------------------------------------------
    def attach(self, env) -> None:
        self.env = env
        if self.subs:
            return
        import omni.physx

        self.origin = _np(env.unwrapped.scene.env_origins)[0]
        self._make_views()
        self.subs.append(omni.physx.get_physx_interface().subscribe_physics_on_step_events(self._on_step, pre_step=False, order=100))

    def _make_views(self) -> None:
        """PhysX contact views (as Isaac Lab's contact sensor uses): the ball against the bat and each arm link, and the
        bat against the ball and each arm link. What a body touches beyond its filters shows as the rest of its net force."""
        from isaaclab.sim.utils.stage import get_current_stage
        from pxr import Usd, UsdPhysics

        base = self.env.unwrapped
        stage = get_current_stage()
        ball, bat = base.scene["ball"], base.scene["bat"]
        ball_path, bat_path = ball.root_view.prim_paths[0], bat.root_view.prim_paths[0]
        ns = ball_path.rsplit("/", 1)[0]

        def links(robot):
            paths = list(base.scene[robot].root_view.link_paths[0])
            return [p for p in paths if stage.GetPrimAtPath(p).HasAPI(UsdPhysics.RigidBodyAPI)] or paths

        self.left_links, self.right_links = links("left_robot"), links("right_robot")
        sim_view = ball._physics_sim_view
        self.ball_filters = [bat_path, *self.left_links, *self.right_links]
        self.ball_view = sim_view.create_rigid_contact_view(ball_path, filter_patterns=self.ball_filters, max_contact_data_count=64)
        self.bat_filters = [ball_path, *self.right_links, *self.left_links]
        self.bat_view = sim_view.create_rigid_contact_view(bat_path, filter_patterns=self.bat_filters, max_contact_data_count=0)
        n_left = len(self.left_links)
        print(f"[pongkit] ball {ball_path} bat {bat_path} left links {self.left_links} right links {self.right_links}", flush=True)
        print(f"[pongkit] ball view filters {self.ball_view.filter_count if hasattr(self.ball_view, 'filter_count') else '?'}", flush=True)
        self.ball_class = ["bat"] + ["left"] * n_left + ["right"] * len(self.right_links)
        self.bat_class = ["ball"] + ["right"] * len(self.right_links) + ["left"] * n_left

    def _contacts(self, dt):
        """The classes touching the ball in the last physics step."""
        net = _np(self.ball_view.get_net_contact_forces(dt))[0]
        mat = _np(self.ball_view.get_contact_force_matrix(dt))[0]
        touch = set()
        mags = np.linalg.norm(mat, axis=1)
        for k in np.nonzero(mags > FORCE_EPS)[0]:
            touch.add(self.ball_class[k])
        if np.linalg.norm(net - mat.sum(axis=0)) > FORCE_EPS:
            touch.add("other")
        if "bat" in touch:
            touch.discard("bat")
            touch.add(self._face_or_bat(dt))
        return touch

    def _face_or_bat(self, dt) -> str:
        """The red face if every contact point with the bat lies on its top face, inside the blade's outline, with a
        normal within 20 degrees of the face's; otherwise the bat's edge, back or handle."""
        import pongassets as pa

        forces, points, normals, _, counts, starts = (_np(x) for x in self.ball_view.get_contact_data(dt))
        n, s = int(counts[0, 0]), int(starts[0, 0])
        bp, bq, _, _ = self._rigid("bat")
        rot = _quat_matrix(bq)
        up = rot[:, 2]
        ok = 0
        for i in range(s, s + n):
            if abs(float(forces[i].reshape(-1)[0])) <= FORCE_EPS:
                continue
            local = rot.T @ (points[i] - self.origin - bp)
            inside = (local[0] / (pa.BLADE_L / 2)) ** 2 + (local[1] / (pa.BLADE_W / 2)) ** 2 <= 1.0
            on_top = abs(local[2] - pa.BLADE_T / 2) < 0.003
            if not (inside and on_top and abs(float(normals[i] @ up)) >= FACE_COS):
                return "bat"
            ok += 1
        return "face" if ok else "bat"

    def _bat_partners(self, dt) -> set:
        net = _np(self.bat_view.get_net_contact_forces(dt))[0]
        mat = _np(self.bat_view.get_contact_force_matrix(dt))[0]
        out = {self.bat_class[k] for k in np.nonzero(np.linalg.norm(mat, axis=1) > FORCE_EPS)[0]}
        if np.linalg.norm(net - mat.sum(axis=0)) > BAT_EPS:
            out.add("other")
        return out

    def _first_face(self):
        lp, _, _, _ = self._rigid("ball")
        pts = self.finger_points(self)
        gap = float(np.min(np.linalg.norm(pts - lp, axis=1))) - 0.02
        held, why = self._bat_held_now()
        return gap, held, why

    def _bat_held_now(self):
        if self.bat_touch_bad:
            return False, self.bat_touch_bad
        if not self._right_touch:
            return False, "the bat does not touch the right hand"
        return True, ""

    def _on_step(self, dt: float) -> None:
        if self.env is None:
            return
        t0 = time.perf_counter()
        try:
            self.t += dt
            self.steps += 1
            if self.counter.state in ("ended", "done", "zero") and not self.trace_path:
                return
            ball_touch = self._contacts(dt)
            live = self.counter.state in ("released", "counting") or self.trace_path
            if live or self.steps % 5 == 0:
                bat = self._bat_partners(dt)
                self._right_touch = "right" in bat
                bad = sorted(bat - {"right", "ball"})
                self.bat_touch_bad = f"the bat touches {bad}" if bad else ""
            lp = self._rigid("ball")[0] if live or ball_touch else np.zeros(3)
            was = self.counter.state
            self.counter.step(self.t, ball_touch, float(lp[2] - 0.02), self._first_face)
            if self.counter.state == "counting" and (was != "counting" or self.steps % 5 == 0):
                pos, rot = self._bat_in_gripper()
                if was != "counting":
                    self.bat_ref = (pos, rot)
                else:
                    self._check_hold(pos, rot)
            if self.trace_path:
                lp, _, lv, _ = self._rigid("ball")
                bp, bq, bv, bw = self._rigid("bat")
                code = sum(1 << i for i, c in enumerate(("face", "bat", "left", "right", "other")) if c in ball_touch)
                self.trace.append(np.r_[self.t, lp, lv, bp, bq, bv, bw, code, {"start": 0, "held": 1, "released": 2, "counting": 3,
                                                                          "ended": 4, "done": 5, "zero": 6}[self.counter.state], self.counter.count])
        except Exception as exc:  # a tracker fault must not pass silently: it scores 0
            self.counter.state, self.counter.why = "zero", f"tracker fault: {type(exc).__name__}: {exc}"
            raise
        finally:
            self.cpu_s += time.perf_counter() - t0

    def _check_hold(self, pos, rot) -> None:
        if self.bat_touch_bad:
            self.counter.bat_lost(self.t, self.bat_touch_bad)
            return
        p0, r0 = self.bat_ref
        moved = float(np.linalg.norm(pos - p0)) * 1000
        turn = float(np.degrees(np.arccos(np.clip((np.trace(r0.T @ rot) - 1) / 2, -1, 1))))
        if moved > HOLD_MM or turn > HOLD_DEG:
            self.counter.bat_lost(self.t, f"bat moved {moved:.1f} mm / {turn:.1f} deg in the hand")

    def save(self) -> None:
        if not self.trace_path or not self.trace:
            return
        path = Path(self.trace_path)
        np.save(path.with_suffix(".trace.npy"), np.array(self.trace))
        with open(path.with_suffix(".log.txt"), "w") as f:
            for row in self.counter.log:
                f.write(f"{row}\n")
            f.write(f"final: {self.counter.state} {self.counter.count} {self.counter.why}\n")
            f.write(f"tracker wall time {self.cpu_s:.1f} s over {self.steps} physics steps\n")
        with open(path.with_suffix(".events.txt"), "w") as f:
            for e in self.events[:4000]:
                f.write(f"{e}\n")
