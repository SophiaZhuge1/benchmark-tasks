"""Continuous full-score endpoint hold, enforced before raw reward is returned."""
from dataclasses import dataclass
import math

@dataclass
class EndpointHold:
    fallback: float
    duration: float = 1.0
    elapsed: float = 0.0
    previous_eligible: bool = False

    def step(self, dt, candidate):
        if not math.isfinite(dt) or dt <= 0 or not math.isfinite(candidate):
            self.elapsed = 0.0
            self.previous_eligible = False
            return 0.0
        eligible = candidate == 1.0
        self.elapsed = self.elapsed + dt if eligible and self.previous_eligible else 0.0
        self.previous_eligible = eligible
        if not eligible:
            return candidate
        return 1.0 if self.elapsed >= self.duration - 1e-9 else self.fallback
