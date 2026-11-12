import unittest
from fluid import Fluid, AREA
from sample_visuals import phase_segments


class SampleVisualTests(unittest.TestCase):
    def test_phase_bands_remain_contiguous_and_volume_conserving(self):
        f = Fluid()
        for q, up in [(0, 0), (.003, 0), (.004, 1), (.002, 1), (.009, 1)]:
            f.update(q, up, .05)
            s = phase_segments(f, .05)
            cursor = .05
            for centre, length in s.values():
                self.assertGreaterEqual(length, 0)
                self.assertAlmostEqual(centre+length/2, cursor)
                cursor = centre-length/2
            self.assertAlmostEqual(sum(s[n][1]*AREA for n in ['sample_front','sample_rear']), f.sample)
            self.assertAlmostEqual(sum(s[n][1]*AREA for n in ['bubble','air_front']), f.air)
            self.assertAlmostEqual(.05-cursor, (f.sample+f.air)/AREA)

    def test_migrated_pocket_and_aspirated_air_stay_distinct(self):
        f = Fluid();f.pocket = 0
        s = phase_segments(f, .05)
        self.assertEqual(s['sample_front'][1], 0)
        f.update(.004, 1, .05);f.update(.002, 1, .05)
        s = phase_segments(f, .05)
        self.assertGreater(s['air_front'][1], 0)
        self.assertAlmostEqual(s['air_front'][1]*AREA, f.front_air)


if __name__ == '__main__': unittest.main()
