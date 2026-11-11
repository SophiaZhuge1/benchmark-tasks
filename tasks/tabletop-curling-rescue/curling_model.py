"""Two-arm curling with a conditional emergency interception rule."""
from dataclasses import dataclass
import math

TARGET=(.710,.180)
RELEASE_X=.300
RADIUS=.032
BOARD=(.040,.880,-.070,.350)
FRICTION=.035

@dataclass
class Observation:
    blue_x: float
    blue_y: float
    red_x: float
    red_y: float
    red_vx: float=0.
    red_vy: float=0.
    max_speed: float=0.
    max_spin: float=0.
    left_blue: bool=False
    right_blue: bool=False
    left_red: bool=False
    right_red: bool=False
    other_contact: bool=False
    lifted: bool=False
    tipped: bool=False
    any_out: bool=False
    valid: bool=True

class CurlingModel:
    def __init__(self):
        self.t=0.;self.launched=False;self.release_t=None
        self.threat=False;self.threat_t=None;self.blocked=False;self.block_t=None
        self.saved=False;self.failed=False;self.reason=None;self.rest_s=0.;self.score=0.
        self.blue_distance=None;self.red_stop_y=None

    def step(self,dt,o):
        if not math.isfinite(dt) or dt<=0:raise ValueError('Positive finite dt required')
        self.t+=dt
        reason=None
        vals=(o.blue_x,o.blue_y,o.red_x,o.red_y,o.red_vx,o.red_vy,o.max_speed,o.max_spin)
        if not o.valid or not all(math.isfinite(v) for v in vals):reason='invalid_physics'
        elif o.any_out:reason='puck_left_board'
        elif o.lifted or o.tipped:reason='puck_lifted_or_tipped'
        elif o.left_red or o.right_blue or o.other_contact:reason='unauthorised_puck_contact'
        if not self.launched and o.blue_x>=RELEASE_X:
            self.launched=True;self.release_t=self.t
        if self.launched and o.left_blue:reason=reason or 'shooting_arm_contact_after_release'
        speed=math.hypot(o.red_vx,o.red_vy)
        self.red_stop_y=o.red_y+o.red_vy*speed/(2*FRICTION*9.81)
        # A moving red stone is on an outward path whose friction-only stopping
        # estimate crosses the board edge. The no-rescue trial validates this.
        danger=(self.launched and o.red_vy<-.06 and o.red_y<.015 and
                self.red_stop_y<BOARD[2])
        if danger and not self.threat:
            self.threat=True;self.threat_t=self.t
        if o.right_red:
            if not self.threat or o.red_y>-.025:
                reason=reason or 'red_contact_before_edge_threat'
            elif not self.blocked and not self.failed and reason is None:
                self.blocked=True;self.block_t=self.t
        if reason:self.failed=True;self.reason=self.reason or reason
        self.score=0.
        if self.failed:self.rest_s=0.;return self.score
        clear=not (o.left_blue or o.right_blue or o.left_red or o.right_red or o.other_contact)
        still=o.max_speed<.01 and o.max_spin<.15
        self.rest_s=self.rest_s+dt if self.launched and clear and still else 0.
        self.blue_distance=math.hypot(o.blue_x-TARGET[0],o.blue_y-TARGET[1])
        if self.rest_s+1e-8>=2:
            self.saved=self.blocked
            self.score=.25
            on_target=self.blue_distance<=.100+1e-9
            if on_target:self.score=.5
            if self.saved:self.score=.75
            if self.saved and on_target:self.score=1.
        return self.score

    def report(self):
        return {k:getattr(self,k) for k in ['t','launched','release_t','threat','threat_t','blocked','block_t',
                'saved','failed','reason','rest_s','score','blue_distance','red_stop_y']}
