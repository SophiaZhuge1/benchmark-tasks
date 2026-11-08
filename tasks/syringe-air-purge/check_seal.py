"""Check the passive seal's force bound and elastic-energy bookkeeping."""
import unittest
from seal import Seal, SEAL_FORCE, SEAL_STIFFNESS, elastic_energy


class SealChecks(unittest.TestCase):
    def test_stick_under_small_displacement(self):
        seal = Seal()
        seal.update(.25 * SEAL_FORCE / SEAL_STIFFNESS)
        self.assertAlmostEqual(seal.anchor, 0.)
        self.assertEqual(seal.dissipated, 0.)

    def test_slip_removes_energy_and_caps_force_in_both_directions(self):
        seal = Seal()
        for position in (0., .001, .002, .0015, -.001, -.003, 0.):
            before = elastic_energy(position - seal.anchor)
            dissipated_before = seal.dissipated
            seal.update(position)
            after = elastic_energy(position - seal.anchor)
            self.assertLessEqual(abs(SEAL_STIFFNESS * (position - seal.anchor)), SEAL_FORCE + 1e-12)
            self.assertAlmostEqual(before, after + seal.dissipated - dissipated_before)
            self.assertGreaterEqual(seal.dissipated, dissipated_before)

    def test_repeated_rest_does_not_drive_joint(self):
        seal = Seal()
        seal.update(.009)
        anchor, dissipated = seal.anchor, seal.dissipated
        for _ in range(100):
            seal.update(.009)
        self.assertAlmostEqual(seal.anchor, anchor)
        self.assertAlmostEqual(seal.dissipated, dissipated)

    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            Seal().update(float('nan'))


if __name__ == '__main__':
    unittest.main()
