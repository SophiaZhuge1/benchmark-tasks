"""Sampled probe-clearance and irreversible lateral-scrape model (SI units)."""
from dataclasses import dataclass
import math

CONTACT = .0008
CLEARANCE = .008
TARGET = .060
POSITION_TOL = .002
DAMAGE_TRAVEL = .0002


def contact_fraction(a, b):
    """Fraction of a linear inter-sample segment within the contact band."""
    if max(a, b) <= CONTACT:
        return 1.
    if min(a, b) > CONTACT:
        return 0.
    return (CONTACT - min(a, b)) / abs(b - a)


@dataclass
class ProbeModel:
    previous_x: float = 0.
    previous_lift: float = 0.
    t: float = 0.
    scrape_m: float = 0.
    damaged: bool = False
    first_damage: float | None = None
    lifted: bool = False
    contact: bool = True
    aligned: bool = False
    lift_dwell: float = 0.
    final_dwell: float = 0.
    value: float = 0.

    def step(self, dt, x, lift, released=False):
        if not all(math.isfinite(v) for v in (dt, x, lift)) or dt <= 0:
            raise ValueError('finite coordinates and positive dt required')
        self.t += dt
        dx = abs(x - self.previous_x)
        self.scrape_m += dx * contact_fraction(self.previous_lift, lift)
        self.contact = lift <= CONTACT
        self.aligned = abs(x - TARGET) <= POSITION_TOL
        self.lift_dwell = self.lift_dwell + dt if lift >= CLEARANCE else 0.
        self.lifted |= self.lift_dwell >= .25 - 1e-9
        # Exceeding the rail bounds also fails instead of rewarding broken fixtures.
        self.damaged |= self.scrape_m > DAMAGE_TRAVEL or not (-.002 <= x <= .072 and -.002 <= lift <= .062)
        if self.damaged and self.first_damage is None:
            self.first_damage = self.t
        stable = dx / dt <= .001
        final = self.lifted and self.aligned and self.contact and stable and released and not self.damaged
        self.final_dwell = self.final_dwell + dt if final else 0.
        self.value = 0. if self.damaged else (1. if self.final_dwell >= 1. - 1e-9 else
            .75 if self.lifted and self.aligned and lift >= CLEARANCE else .25 if self.lifted else 0.)
        self.previous_x, self.previous_lift = x, lift
        return self.value
