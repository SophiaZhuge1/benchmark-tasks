"""Offline checks of the lock-free sliding drawstring; not physics evidence."""
import unittest
import numpy as np
from drawstring_physics import SlidingDrawstring


def ring(radius=.09, n=20, z=1.):
    a = np.arange(n) * 2 * np.pi / n
    return np.c_[radius * np.cos(a), radius * np.sin(a), np.full(n, z)]


def scene(loop_out=.02):
    hem = ring()
    loops = np.array([hem[5] + [0, loop_out, -.01], hem[15] + [0, -loop_out, -.01]])
    return np.r_[hem, loops]


class DrawstringPhysicsTests(unittest.TestCase):
    def test_rest_state_is_force_free(self):
        p = scene();s = SlidingDrawstring(p, exit_index=5)
        self.assertTrue(np.allclose(s.forces(p, np.zeros_like(p)), 0))

    def test_pulling_loops_gathers_hem_inward(self):
        p = scene();s = SlidingDrawstring(p, exit_index=5)
        q = p.copy();q[20, 1] += .05;q[21, 1] -= .05
        f = s.forces(q, np.zeros_like(q))
        self.assertGreater(s.last['tension'], 0)
        radial = np.einsum('ij,ij->i', f[:20, :2], p[:20, :2])
        others = [i for i in range(20) if i not in (5, 15)]
        self.assertTrue(np.all(radial[others] < 0), radial)   # hem pulled inward
        self.assertLess(f[20, 1], 0);self.assertGreater(f[21, 1], 0)  # loops pulled back
        self.assertTrue(np.allclose(f.sum(0), 0, atol=1e-9))   # internal force only

    def test_no_lock_after_release(self):
        """A gathered hem with slack string carries no force: nothing holds it shut."""
        p = scene();s = SlidingDrawstring(p, exit_index=5)
        q = p.copy();q[20, 1] += .08;q[21, 1] -= .08
        s.forces(q, np.zeros_like(q))
        released = p.copy();released[:20, :2] *= .5           # mouth gathered, loops back
        f = s.forces(released, np.zeros_like(released))
        self.assertEqual(s.last['tension'], 0.)
        self.assertTrue(np.allclose(f, 0))
        reopened = p.copy()
        self.assertTrue(np.allclose(s.forces(reopened, np.zeros_like(reopened)), 0))

    def test_force_cap(self):
        p = scene(); s = SlidingDrawstring(p, exit_index=5, tension_cap=2.)
        q = p.copy(); q[20, 1] += .5; q[21, 1] -= .5
        s.forces(q, np.zeros_like(q))
        self.assertLessEqual(s.last['tension'], 2.)

    def test_symmetric_route(self):
        s = SlidingDrawstring(scene(), exit_index=5)
        self.assertEqual(s.cutouts, (5, 15))
        self.assertEqual(sorted(set(s.route.tolist())), list(range(22)))


if __name__ == '__main__':
    unittest.main()
