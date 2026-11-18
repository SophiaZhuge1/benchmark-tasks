"""Force-based sliding drawstring for an ordinary drawstring trash bag.

One continuous string runs around the mouth hem and leaves it at two opposite
cut-outs, where a short loop is exposed on each side. The string is modelled
as a unilateral routed-length spring: tension acts along every hem segment
and on the two loop bodies, so pulling a loop away from its cut-out slides
string out of the hem and gathers the mouth. There is NO lock, ratchet or
one-way element: when the loops are released the string tension drops to zero
and only film contact/friction keeps the mouth gathered, as on a real bag.

This is a lumped, uncalibrated model, not explicit rope/hem contact. Forces are
applied to dynamic rigid hem markers and loop bodies; no poses are set.
"""
import numpy as np


def routed_length_gradient(points):
    delta = np.diff(points, axis=0)
    length = np.linalg.norm(delta, axis=1)
    direction = delta / np.maximum(length[:, None], 1e-9)
    gradient = np.zeros_like(points)
    gradient[:-1] -= direction
    gradient[1:] += direction
    return float(length.sum()), gradient


class SlidingDrawstring:
    """positions: n hem markers followed by the two loop bodies."""

    def __init__(self, positions, exit_index, stiffness=40., damping=.03, hem_mass=.001, loop_mass=.002, slack=.002, tension_cap=.7):
        self.tension_cap = tension_cap
        self.n = len(positions) - 2
        self.k = stiffness
        self.d = damping
        start = int(exit_index) % self.n
        opposite = (start + self.n // 2) % self.n
        half0 = [(start + i) % self.n for i in range(self.n // 2 + 1)]
        half1 = [(opposite + i) % self.n for i in range(self.n // 2 + 1)]
        # loop 0 -> hem from cut-out 0 to cut-out 1 -> loop 1 -> hem back -> loop 0
        self.route = np.array([self.n, *half0, self.n + 1, *half1, self.n])
        self.cutouts = (start, opposite)
        self.rest = routed_length_gradient(np.asarray(positions)[self.route])[0] + slack
        self.mass = np.r_[np.full(self.n, hem_mass), np.full(2, loop_mass)]
        self.max_extension = 0.
        self.last = {}

    def forces(self, positions, velocities, dt=1 / 240):
        length, g = routed_length_gradient(positions[self.route])
        G = np.zeros_like(positions)
        np.add.at(G, self.route, g)
        extension = length - self.rest
        rate = float((G * velocities).sum())
        self.max_extension = max(self.max_extension, max(0., extension))
        # Implicit (backward-Euler) unilateral spring along the routed length.
        W = float(np.einsum('ij,ij,i->', G, G, 1 / self.mass))
        A = 1. + (dt * self.d + dt * dt * self.k) * W
        rhs = self.k * extension + (dt * self.k + self.d) * rate
        tension = rhs / A if (extension + dt * rate > 0 and rhs > 0) else 0.
        # Numerical safeguard: cap the per-step string force (0.7 N, about twice
        # the 0.4 N each strand carries when the 160 g bag hangs from it).
        tension = min(tension, self.tension_cap)
        out = -tension * G
        hem = np.r_[np.arange(self.n), 0]
        perimeter = routed_length_gradient(positions[hem])[0]
        self.last = {'length': length, 'rest_length': self.rest, 'tension': float(tension),
                     'hem_perimeter': perimeter, 'max_extension': self.max_extension,
                     'net_force': out.sum(0).tolist()}
        return out
