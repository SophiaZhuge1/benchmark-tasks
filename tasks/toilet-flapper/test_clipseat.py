import unittest
from clipseat import ClipSeat


class ClipTests(unittest.TestCase):
    def setUp(self):
        self.seat = ClipSeat()

    def move(self, x, load=0., bead=27, y=0., z=0.):
        return self.seat.sample(bead, (x, y, z), load)

    def enter(self):
        self.move(-0.012)
        self.move(-0.005)

    def test_seated_press(self):
        self.enter()
        self.assertFalse(self.move(0, 0.5))
        self.assertTrue(self.move(0, 0.6))

    def test_hover_and_unloaded_seating(self):
        self.enter()
        for _ in range(10):
            self.assertFalse(self.move(0, 0.1))

    def test_bead_identity(self):
        self.enter()
        for bead in (27, 28, 28):
            self.assertFalse(self.move(0, 0.9, bead))

    def test_side_entry(self):
        self.enter()
        self.move(-0.003, y=0.005)
        for _ in range(3):
            self.assertFalse(self.move(0, 1.))

    def test_jump_from_mouth(self):
        self.move(-0.012)
        for _ in range(3):
            self.assertFalse(self.move(0, 1.))

    def test_intermittent_press(self):
        self.enter()
        for load in (0.6, 0.3, 0.8):
            self.assertFalse(self.move(0, load))
