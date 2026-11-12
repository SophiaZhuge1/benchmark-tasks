"""Axial phase bands for the reduced-order model, not a free-surface simulation."""
from fluid import AREA


def phase_segments(fluid, outlet_y):
    """Return non-overlapping phase lengths/centres, ordered inward from the outlet.

    Newly aspirated air exits first, then the liquid ahead of the trapped pocket,
    the trapped air, and the remaining liquid. Geometry follows measured model
    volumes; it never changes physics or scoring.
    """
    front_air = max(0., min(fluid.front_air, fluid.air))
    front_liquid = max(0., min(fluid.pocket * AREA, fluid.sample))
    phases = [('air_front', front_air), ('sample_front', front_liquid),
              ('bubble', max(0., fluid.air-front_air)),
              ('sample_rear', max(0., fluid.sample-front_liquid))]
    cursor = outlet_y
    segments = {}
    for name, volume in phases:
        length = volume / AREA
        segments[name] = (cursor-length/2, length)
        cursor -= length
    return segments
