"""The scripted reference demo, closed loop: each control step it reads the ball's and the bat's poses (both in view of
every camera) and the arms' own joints. A policy gets only the cameras and joints.

Right hand: picks the bat off its block by the taped handle (tool 45 degrees down and forward, fingers on the handle's
edges) and holds it blade flat at the playing spot. Left hand: picks the ball from the egg cup, carries it over the
blade and lets go 18 cm above it, then withdraws. Then the right hand keeps the ball bouncing: before each landing it
predicts where and when the ball will meet the face, moves the blade under that point, tilts it to send the ball back
towards the centre, and strokes upward through the hit, fast enough to send the ball to a set height.
"""

from __future__ import annotations

import math
import os

import numpy as np

import demokit as dk
from demokit import CONTROL_HZ, DT
from yam_arena import ik
from yam_arena.constants import FINGER_OPEN
from yam_arena.urdf import axis_angle_matrix

G = 9.81
GRIP_BACK = 0.102  # TCP behind the blade's centre, along the handle
R_GRIP = dk.tilted(45.0, 0.0)  # tool 45 degrees down and forward, fingers closing along y
L_DROP = dk.tilted(60.0, 0.0)
PLAY_XY = np.array([0.40, 0.0])
PLAY_H = 0.1225  # the blade's centre above the table while playing


def _rot(axis, deg):
    return axis_angle_matrix(np.asarray(axis, float), math.radians(deg))


class BatHand:
    """The right hand with the bat in it. Commands the blade's pose; the TCP follows from the bat's measured place in the
    hand. A slow integral trim takes out the arm's droop under the bat."""

    def __init__(self, ctx, top):
        self.ctx, self.arm, self.top = ctx, ctx.right, top
        self.p_in_tcp = np.array([GRIP_BACK, 0.0, 0.0])
        self.r_in_tcp = np.eye(3)
        self.trim_p = np.zeros(3)
        self.trim_r = np.zeros(3)

    def learn(self):
        """The bat's pose in the hand, from what is seen now."""
        st = self.ctx.state("bat")
        q = self.ctx.observed("right")[:6]
        tp, tr = ik.tcp_pose(q, self.arm.base)
        self.r_in_tcp = tr.T @ st.rotation()
        self.p_in_tcp = tr.T @ (np.asarray(st.pos) - tp)

    def tcp_for(self, blade_pos, blade_rot):
        r_tcp = blade_rot @ self.r_in_tcp.T
        return blade_pos - r_tcp @ self.p_in_tcp, r_tcp

    def command(self, blade_pos, blade_rot):
        """One control step's command for a blade pose (with trims)."""
        rot = _rot_vec(self.trim_r) @ blade_rot
        p, r = self.tcp_for(np.asarray(blade_pos) + self.trim_p, rot)
        self.arm._solve(p, r)

    def blade(self):
        st = self.ctx.state("bat")
        return np.asarray(st.pos, float), st.rotation()

    def update_trim(self, goal_pos, goal_rot, gain=0.05):
        p, r = self.blade()
        self.trim_p += gain * (np.asarray(goal_pos) - p)
        err = ik._rot_error(goal_rot, r)
        self.trim_r += gain * err


def _rot_vec(v):
    n = float(np.linalg.norm(v))
    return np.eye(3) if n < 1e-9 else axis_angle_matrix(v / n, n)


def pick_bat(ctx, top):
    r = ctx.right
    st = ctx.state("bat")
    rb = st.rotation()
    tcp = np.asarray(st.pos) + rb @ np.array([-GRIP_BACK, 0.0, 0.0])
    back = tcp - 0.07 * R_GRIP.rot[:, 2] + np.array([0, 0, 0.02])
    yield from r.move(back, grip=R_GRIP, finger=FINGER_OPEN, t=2.0, label="bat: approach")
    yield from r.move(tcp, t=1.0, label="bat: in")
    yield from r.servo(tcp, timeout=1.0, label="bat: in")
    yield from r.close(0.030, force=40.0, t=0.6, label="bat: close")
    yield from r.wait(0.3)
    yield from r.move(r.at() + np.array([0, 0, 0.03]), t=0.6, label="bat: lift")


def pick_ball(ctx, top):
    l = ctx.left
    ball = ctx.pos("ball")
    yield from l.move(ball + np.array([0, 0, 0.09]), grip=dk.down(0.0), finger=FINGER_OPEN, t=2.0, label="ball: over")
    ball = ctx.pos("ball")
    yield from l.servo(ball + np.array([0, 0, 0.09]), timeout=0.8, label="ball: over")
    yield from l.move(ball + np.array([0, 0, 0.002]), t=1.0, label="ball: down")
    yield from l.servo(ball + np.array([0, 0, 0.002]), timeout=0.8, label="ball: down")
    yield from l.close(0.040, force=3.0, t=0.5, label="ball: close")
    yield from l.move(l.at() + np.array([0, 0, 0.10]), t=0.8, label="ball: lift")


def carry_ball(ctx, top, over_xy, bottom_z):
    """Carry the ball over `over_xy` with its bottom at `bottom_z`, tool 60 degrees from vertical."""
    l = ctx.left
    goal = np.array([*over_xy, bottom_z + 0.02])
    yield from l.move(goal + np.array([-0.04, 0.06, 0.03]), grip=L_DROP, t=2.0, label="ball: carry")
    yield from l.move(goal, t=0.8, label="ball: over the bat")
    for _ in range(int(1.5 * CONTROL_HZ)):  # servo on the ball itself
        err = goal - ctx.pos("ball")
        if np.linalg.norm(err) < 0.002:
            break
        c = ik.tcp_pose(l.q, l.base)[0] + np.clip(0.5 * err, -0.004, 0.004)
        l._solve(c, l.grip.rot)
        yield


def release(ctx, top):
    """Open the fingers while backing the hand out along its own axis (up and back), so that the fingers slide off the
    falling ball; then clear the ball's column towards the left."""
    l = ctx.left
    back = -l.approach_axis()
    yield from l.move(l.at() + 0.10 * back, finger=FINGER_OPEN, t=0.35, label="ball: release")
    yield from l.move(l.at() + np.array([-0.04, 0.15, 0.02]), t=0.6, label="withdraw")
    yield from l.move(np.array([0.24, 0.30, top + 0.18]), grip=dk.down(0.0), t=1.5, label="away")


def probe(ctx, top):
    """Physics check: drop the ball 18 cm onto the bat lying on its block, then pick the bat up and stroke it."""
    yield from pick_ball(ctx, top)
    bat = np.asarray(ctx.state("bat").pos)
    face = bat[2] + 0.003
    yield from carry_ball(ctx, top, bat[:2], face + 0.18)
    yield from ctx.together(release(ctx, top), ctx.right.wait(3.0))
    yield from pick_bat(ctx, top)
    hand = BatHand(ctx, top)
    hand.learn()
    goal_p = np.array([*PLAY_XY, top + PLAY_H + 0.05])
    flat = np.eye(3)
    for k in range(int(2.0 * CONTROL_HZ)):
        hand.command(goal_p, flat)
        yield
    for k in range(int(1.0 * CONTROL_HZ)):
        hand.update_trim(goal_p, flat, 0.1)
        hand.command(goal_p, flat)
        yield
    # strokes: sinusoids of 1, 2, 3 cm at 3 Hz, then steps
    for amp in (0.01, 0.02, 0.03):
        for k in range(int(1.0 * CONTROL_HZ)):
            z = amp * math.sin(2 * math.pi * 3.0 * (k + 1) * DT)
            hand.command(goal_p + [0, 0, z], flat)
            yield
        for k in range(10):
            hand.command(goal_p, flat)
            yield
    for amp in (0.01, 0.02):
        hand.command(goal_p + [0, 0, amp], flat)
        yield
        for k in range(15):
            hand.command(goal_p, flat)
            yield
    for tilt in (5.0, -5.0):
        for k in range(15):
            hand.command(goal_p, _rot([1, 0, 0], tilt))
            yield
        for k in range(15):
            hand.command(goal_p, _rot([0, 1, 0], tilt))
            yield
    for k in range(20):
        hand.command(goal_p, flat)
        yield


# -- the bounce controller ----------------------------------------------------------------------------------------------

E = 0.85  # ball on rubber, as the task states it
DRAG = 0.26  # 1/s, the ball's linear damping
APEX = 0.31  # m above the table: where each bounce aims the ball's bottom (the red line is at 0.25)
LAG = 0.135  # s from a command to the blade's following it (measured: blade height against command)
GAIN = 0.55  # the blade's stroke over the commanded stroke at about 3 Hz (measured)
MAX_AMP = 0.035
MAX_TILT = math.radians(6.0)


def predict(p, v, face_z, horizon=1.0, dt=0.002):
    """Time, position and velocity at which the ball's bottom next comes down to `face_z`, with drag."""
    p, v = np.array(p, float), np.array(v, float)
    t = 0.0
    while t < horizon:
        if p[2] - 0.02 <= face_z and v[2] < 0:
            return t, p, v
        v = v + dt * (np.array([0.0, 0.0, -G]) - DRAG * v)
        p = p + dt * v
        t += dt
    return None


class Bouncer:
    """Each control step: predict the ball's next landing on the face; drive the blade on a sine at the bounce rate whose
    upward zero-crossing (fastest upward motion) meets the ball, with the stroke sized for the planned rebound; tilt the
    face to send the ball back over the centre. Learns from each bounce: its apex sets the stroke gain, and its outgoing
    sideways velocity the tilt the strokes add."""

    def __init__(self, ctx, hand, top):
        self.ctx, self.hand, self.top = ctx, hand, top
        self.center = np.array([*PLAY_XY, top + PLAY_H])
        self.face_z = self.center[2] + 0.003 - 0.006  # the blade rides about 6 mm low while stroking
        self.k_u = 1.0
        self.bias = np.array([0.015, 0.02])  # rad: the strokes tip the face towards +x and +y at the hit
        self.tilt = np.zeros(2)
        self.cmd_tilt = np.zeros(2)
        self.last_v = None
        self.hit_at = None
        self.at_hit = None  # (vh_in, v_in, commanded tilt) just before the last hit
        self.rising = False
        self.log = []

    def v_target(self):
        return math.sqrt(2 * G * max(self.top + APEX - self.face_z, 0.02))

    def learn(self, p, v):
        ctx = self.ctx
        if self.last_v is not None and self.last_v[2] < -0.3 and v[2] > 0.3:
            self.hit_at = ctx.t
            self.rising = True
        if self.hit_at is not None and self.at_hit is not None and ctx.t - self.hit_at >= 2 * DT - 1e-9:
            vh_in, v_in, tilt = self.at_hit
            eff = (v[:2] - vh_in) / ((1 + E) * max(v_in, 0.5))
            self.bias += 0.5 * (eff - tilt - self.bias)
            self.log.append(("hit", round(ctx.t, 3), *np.round(np.degrees(eff), 2), *np.round(np.degrees(self.bias), 2)))
            self.hit_at = None
        if self.rising and v[2] <= 0 < self.last_v[2]:
            apex = self.last_p[2] - 0.02 + self.last_v[2] ** 2 / (2 * G) - self.top
            self.k_u = float(np.clip(self.k_u + 10.0 * (APEX - apex), 0.3, 3.0))
            self.log.append(("apex", round(ctx.t, 3), round(apex, 4), round(self.k_u, 3)))
            self.rising = False
        self.last_v, self.last_p = v, p

    def step(self, planned_tau=None):
        ctx = self.ctx
        ball = ctx.state("ball")
        p, v = np.asarray(ball.pos, float), np.asarray(ball.lin_vel, float)
        self.learn(p, v)
        if planned_tau is not None:
            tau, p_imp = planned_tau, p.copy()
            v_imp = np.array([0.0, 0.0, -math.sqrt(2 * G * max(p[2] - 0.02 - self.face_z, 0.01))])
        else:
            pred = predict(p, v, self.face_z)
            if pred is None:
                tau, p_imp, v_imp = 0.4, p, np.array([0.0, 0.0, -1.9])
            else:
                tau, p_imp, v_imp = pred
        v_in = -v_imp[2]
        v_out = self.v_target()
        u = self.k_u * (v_out - E * v_in) / (1 + E)
        period = 2 * v_out / G
        w = 2 * math.pi / period
        amp = float(np.clip(u / (w * GAIN), 0.0, MAX_AMP))
        z = self.center[2] + amp * math.sin(w * (LAG - tau))
        # steer: tilt the face so that the ball comes back over the centre on the next bounce
        vh_des = (self.center[:2] - p_imp[:2]) / period * 0.7
        theta = (vh_des - v_imp[:2]) / ((1 + E) * max(v_in, 0.5))
        n = float(np.linalg.norm(theta))
        if n > MAX_TILT:
            theta *= MAX_TILT / n
        self.tilt += 0.5 * (theta - self.tilt)
        self.at_hit = (v_imp[:2].copy(), v_in, self.tilt.copy())
        cmd = self.tilt - self.bias
        rot = _rot([0, 1, 0], math.degrees(cmd[0])) @ _rot([1, 0, 0], -math.degrees(cmd[1]))
        off = p_imp[:2] - self.center[:2]
        shift = np.clip(np.sign(off) * np.maximum(np.abs(off) - 0.03, 0.0), -0.03, 0.03)
        goal = np.array([*(self.center[:2] + shift), z])
        self.hand.command(goal, rot)
        self.log.append((round(ctx.t, 3), *np.round(goal, 4), *np.round(np.degrees(cmd), 2), round(tau, 3), round(v_in, 3), round(u, 3), round(amp, 4)))


def save_log(rows, name):
    path = os.environ.get("TASK_TRACE")
    if path:
        with open(f"{path}.{name}.txt", "w") as f:
            for r in rows:
                f.write(f"{r}\n")


def full(ctx, top):
    hand = BatHand(ctx, top)
    center = np.array([*PLAY_XY, top + PLAY_H])
    flat = np.eye(3)

    def right_side():
        yield from pick_bat(ctx, top)
        hand.learn()
        start = hand.tcp_for(np.asarray(ctx.state("bat").pos) + np.array([0, 0, 0.0]), ctx.state("bat").rotation())
        mid = center + np.array([-0.04, -0.06, 0.04])
        yield from ctx.right.move(hand.tcp_for(mid, flat)[0], grip=dk._as_grip(hand.tcp_for(mid, flat)[1]), t=1.5, label="bat: to play")
        yield from ctx.right.move(hand.tcp_for(center, flat)[0], t=1.0, label="bat: play spot")
        hand.learn()
        for k in range(int(1.5 * CONTROL_HZ)):
            hand.update_trim(center, flat, 0.15)
            hand.command(center, flat)
            yield

    def left_side():
        yield from pick_ball(ctx, top)
        yield from ctx.left.move(np.array([0.30, 0.12, top + 0.30]), grip=L_DROP, t=1.5, label="ball: wait")

    yield from ctx.together(right_side(), left_side())
    blade = np.asarray(ctx.state("bat").pos)
    over = blade[:2]
    face = center[2] + 0.003

    def hold_bat(seconds):
        for _ in range(int(seconds * CONTROL_HZ)):
            hand.command(center, flat)
            yield

    yield from ctx.together(carry_ball(ctx, top, over, face + 0.174), hold_bat(3.0))
    bouncer = Bouncer(ctx, hand, top)
    # the blade starts its stroke before the release, timed for the planned first landing
    lead = 0.6
    ball = ctx.pos("ball")
    fall = predict(ball, np.zeros(3), bouncer.face_z)[0] + 0.03  # the fingers take about 30 ms to let go
    t_land = ctx.t + lead + fall
    falling = [False]

    def play(seconds):
        if ctx.mode == "still":  # the careless way: hold the bat still and let the ball bounce
            yield from hold_bat(seconds)
            return
        for _ in range(int(seconds * CONTROL_HZ)):
            if not falling[0] and ctx.state("ball").lin_vel[2] < -0.3:
                falling[0] = True
            bouncer.step(None if falling[0] else max(t_land - ctx.t, 0.0))
            yield
            if len(bouncer.log) % 40 == 0:
                save_log(bouncer.log, "bouncer")

    def let_go():
        yield from ctx.left.wait(lead)
        yield from release(ctx, top)

    yield from ctx.together(let_go(), play(16.0))
    save_log(bouncer.log, "bouncer")


def script(ctx, top):
    mode = ctx.mode
    if mode == "probe":
        yield from probe(ctx, top)
        return
    yield from full(ctx, top)
