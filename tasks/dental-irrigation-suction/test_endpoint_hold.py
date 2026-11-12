import unittest
from endpoint_hold import EndpointHold

class EndpointHoldTests(unittest.TestCase):
    def test_timeout_before_hold_cannot_receive_full_credit(self):
        for fallback in (.6, .75):
            h = EndpointHold(fallback)
            self.assertEqual(h.step(.05, 1.), fallback)
            for _ in range(19):
                self.assertEqual(h.step(.05, 1.), fallback)
            self.assertEqual(h.step(.05, 1.), 1.)

    def test_interrupted_endpoint_restarts_clock(self):
        h = EndpointHold(.75)
        for _ in range(21): h.step(.05, 1.)
        self.assertEqual(h.step(.05, 0.), 0.)
        self.assertEqual(h.step(.05, 1.), .75)
        self.assertEqual(h.elapsed, 0.)

    def test_water_or_pose_failure_cannot_latch_full_score(self):
        h = EndpointHold(.75)
        for _ in range(21): h.step(.05, 1.)
        self.assertEqual(h.step(.05, .5), .5)
        self.assertEqual(h.elapsed, 0.)

    def test_invalid_timing_fails_closed(self):
        h = EndpointHold(.6)
        for _ in range(21): h.step(.05, 1.)
        self.assertEqual(h.step(float('nan'), 1.), 0.)
        self.assertEqual(h.step(.05, 1.), .6)

if __name__ == '__main__': unittest.main()
