"""Passive elastic/sliding seal approximation, independent of task goals.

The rest point slips only to cap elastic strain. This removes stored elastic
energy; it never increases it. A bounded PhysX joint drive applies the force.
Parameters are illustrative, not calibrated to a commercial syringe.
"""
from dataclasses import dataclass
import math

SEAL_STIFFNESS = 10000.0  # N/m
SEAL_FORCE = 0.6         # N; maximum resistance in either direction


def elastic_energy(strain: float) -> float:
    """Potential of the force-clipped spring, including its linear tail."""
    limit = SEAL_FORCE / SEAL_STIFFNESS
    magnitude = abs(strain)
    if magnitude <= limit:
        return .5 * SEAL_STIFFNESS * strain * strain
    return SEAL_FORCE * (magnitude - .5 * limit)


@dataclass
class Seal:
    anchor: float = 0.0
    dissipated: float = 0.0

    def update(self, position: float) -> float:
        if not math.isfinite(position):
            raise ValueError('Nonfinite seal position')
        strain = position - self.anchor
        limit = SEAL_FORCE / SEAL_STIFFNESS
        bounded = max(-limit, min(limit, strain))
        self.dissipated += elastic_energy(strain) - elastic_energy(bounded)
        self.anchor = position - bounded
        return self.anchor
