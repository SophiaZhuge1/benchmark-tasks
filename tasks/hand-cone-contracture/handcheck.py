"""Calibration checks of the practice hand, the simulated counterpart of the bench checks in the README. Selected by
TASK_CHECK (with TASK_DEMO=idle, so the arms stay home); never part of a trial.

    TASK_CHECK=pry      the wrist held straight; from 1 s, an opening force on every fingertip, perpendicular to the
                        middle-distal piece, ramping 0.5 N/s to 8 N
    TASK_CHECK=flexed   the wrist held at 40 degrees of flexion; from 3 s, the same force ramping 0.25 N/s to 1 N

The wrist is held by a stiff torque on the palm, as a tester holds the forearm and hand. Every 0.25 s it prints the
fingertip force, each finger's MCP and PIP angles, flexor tension and fingertip height off the palm surface, and
whether all four fingertips are high enough for the cone to pass under them.
"""

from __future__ import annotations

import math

import numpy as np

import handmodel as hm

CLEAR_N = hm.HALF_T + 2 * hm.cone_radius(-0.0165) + 0.004  # a fingertip's centre this high off the palm's mid-plane


class Check:
    def __init__(self, mode: str):
        self.mode = mode
        self.t = 0.0
        self.last_phi = 0.0
        self.next_print = 0.0
        self.tripped = None
        self.cleared = None

    def step(self, hand, P, R, phi, dt, torques) -> dict:
        self.t += dt
        target = math.radians(40.0) if self.mode == "flexed" else 0.0
        rate = (phi - self.last_phi) / dt
        self.last_phi = phi
        hold = (8.0 * (target - phi) - 0.3 * rate) * (R["pillow"] @ np.array([-1.0, 0.0, 0.0]))
        torques["palm"] += hold
        torques["pillow"] -= hold
        start, slope, top = (1.0, 0.5, 8.0) if self.mode == "pry" else (3.0, 0.25, 1.0)
        f = float(np.clip(slope * (self.t - start), 0.0, top))
        forces, tips_n = {}, []
        rp = R["palm"]
        for i, name in enumerate(hand_dist_names()):
            p, _ = P[name]
            r = R[name]
            tip = p + r @ hm.distal_local(i)[1]
            forces[name] = (-(r @ np.array([0.0, 0.0, 1.0])) * f, tip)
            tips_n.append(float((rp.T @ (tip - P["palm"][0]))[2]))
        last = hand.last
        if last and self.tripped is None and max(last["tf"]) > hm.GAUGE_LIMIT:
            self.tripped = (f, list(np.round(np.degrees(last["tm"]) + [c[0] for c in hm.CLENCH], 0)), list(np.round(tips_n, 3)))
            print(f"[check] gauge passed {hm.GAUGE_LIMIT} N at fingertip force {f:.2f} N, t {self.t:.2f} s, tips n {np.round(tips_n, 3)}",
                  flush=True)
        if self.cleared is None and min(tips_n) >= CLEAR_N:
            self.cleared = f
            print(f"[check] all fingertips high enough for the cone at fingertip force {f:.2f} N, t {self.t:.2f} s, "
                  f"flexors {np.round(last['tf'], 2) if last else None}", flush=True)
        if self.t >= self.next_print and last:
            self.next_print += 0.25
            print(f"[check] t {self.t:5.2f} f {f:4.2f} N wrist {math.degrees(phi):5.1f} mcp "
                  f"{np.round(np.degrees(last['tm']) + [c[0] for c in hm.CLENCH], 0)} pip "
                  f"{np.round(np.degrees(last['tp']) + [c[1] for c in hm.CLENCH], 0)} flexor {np.round(last['tf'], 2)} "
                  f"tips_n {np.round(np.array(tips_n) * 1000, 0)} mm (clear at {CLEAR_N * 1000:.0f})", flush=True)
        return forces


def hand_dist_names() -> list:
    return [f"{f}_dist" for f in hm.FINGERS]
