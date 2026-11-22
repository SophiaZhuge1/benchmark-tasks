"""Track side entry and seating load per bead in the moving fork's frame (metres, N)."""


class ClipSeat:
    def __init__(self):
        self.progress = {}

    def sample(self, bead, xyz, stop_force):
        x, y, z = xyz
        if abs(y) > 0.0016 or abs(z) > 0.0015 or not -0.016 <= x <= 0.001:
            self.progress.pop(bead, None)
            return False
        if x <= -0.009:
            self.progress[bead] = (False, 0)
            return False
        if bead not in self.progress:
            return False
        entered, count = self.progress[bead]
        if -0.008 <= x <= -0.003:
            entered = True
        pressed = entered and abs(x) <= 0.0009 and stop_force >= 0.5
        count = count + 1 if pressed else 0
        self.progress[bead] = (entered, count)
        return count >= 2
