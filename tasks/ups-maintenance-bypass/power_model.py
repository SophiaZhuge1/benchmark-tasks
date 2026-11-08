"""Idealised isolated, make-before-break training switch and outage history."""
from dataclasses import dataclass
import math

@dataclass
class PowerModel:
    t: float = 0.
    ready_s: float = 0.
    outage_s: float = 0.
    first_outage: float | None = None
    unsafe_removal: bool = False
    bypass_used: bool = False
    exchanged: bool = False
    final_s: float = 0.
    powered: bool = True
    bypass: bool = False
    normal: bool = True
    ready: bool = False
    previous_old: bool = True

    def step(self, dt, switch, old_seated, new_seated, old_parked=False, clear=False):
        if not math.isfinite(dt) or dt <= 0 or not math.isfinite(switch):
            raise ValueError('finite positive dt and finite switch position required')
        self.t += dt
        self.bypass = switch >= .025
        self.normal = switch <= .045
        self.ready_s = self.ready_s + dt if new_seated else 0.
        self.ready = new_seated and self.ready_s >= 1. - 1e-9
        self.powered = self.bypass or (self.normal and (old_seated or self.ready))
        if not self.powered:
            if self.first_outage is None: self.first_outage = self.t
            self.outage_s += dt
        # The service position isolates the cartridge before withdrawal.
        if self.previous_old and not old_seated and self.normal:
            self.unsafe_removal = True
        self.previous_old = old_seated
        self.bypass_used |= self.bypass and not self.normal and old_seated
        self.exchanged |= self.bypass_used and old_parked and self.ready
        final = (self.exchanged and old_parked and self.ready and switch <= .008
                 and not self.bypass and clear and not self.failed)
        self.final_s = self.final_s + dt if final else 0.

    @property
    def failed(self): return self.first_outage is not None or self.unsafe_removal

    def score(self):
        if self.failed: return 0.
        if self.final_s >= 1. - 1e-9: return 1.
        return .25 * self.bypass_used + .5 * self.exchanged
