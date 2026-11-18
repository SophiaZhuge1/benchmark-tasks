"""The scoring rules for the bounce count, as a plain state machine fed once per physics step. Pure Python: no simulator.

Each step it gets what touches the ball (a set of partner classes), the height of the ball's bottom, and, at the
first contact with the bat's red face, the facts the rules check there. The simulator side (pongkit.py) works these out
from PhysX contact reports; the tests (test_bounce_rules.py) build them by hand.

Partner classes:
  "face"   the bat's red face (the blade's top, contact normal within 20 degrees of the face's normal)
  "bat"    any other part of the bat: its edge, its black back, its handle
  "left"   any link of the left arm, its fingers included
  "right"  any link of the right arm
  "other"  anything else: the table, the mat, the board, the egg cup, the bat stand
"""

from __future__ import annotations

from dataclasses import dataclass, field

TARGET = 10  # qualifying bounces for full credit
MAX_CONTACT_S = 0.1  # a contact with the face longer than this is a carry
RELEASE_GAP = 0.03  # m: the left fingers' distance from the ball's surface at its first contact
BLUE_LINE = 0.15  # m above the table: the face must be at or below it when it hits the ball
RED_LINE = 0.25  # m above the table: the ball's bottom must rise above it after each hit

TIERS = ((10, 1.0), (7, 0.75), (4, 0.5), (1, 0.25))


def tier(count: int) -> float:
    for n, s in TIERS:
        if count >= n:
            return s
    return 0.0


@dataclass
class BounceCounter:
    """States: "start" (the ball has not yet been in the left hand), "held" (in the left hand), "released" (let go, not yet
    touched anything), "counting", then "ended" (the count stopped), "done" (10 reached) or "zero" (a rule that scores 0)."""

    table_top: float
    state: str = "start"
    count: int = 0
    pending: bool = False  # the last face hit has not yet sent the ball's bottom above the red line
    in_contact: bool = False
    contact_start: float = 0.0
    why: str = ""
    log: list = field(default_factory=list)

    @property
    def score(self) -> float:
        return 0.0 if self.state == "zero" else tier(self.count)

    @property
    def counting(self) -> bool:
        return self.state == "counting"

    def _end(self, t: float, state: str, why: str) -> None:
        self.state, self.why = state, why
        self.log.append((round(t, 4), state, why, self.count))

    def bat_lost(self, t: float, why: str) -> None:
        """The bat slipped in or out of the right hand (checked by the caller while the count runs)."""
        if self.state == "counting":
            self._end(t, "zero", f"bat not held: {why}")

    def step(self, t: float, touch: set, ball_bottom: float, first_face=None) -> None:
        """One physics step at time `t`. `first_face` is a callable giving (left_gap_m, bat_held, why) at the first face
        contact after release, read only then."""
        s = self.state
        if s in ("ended", "done", "zero"):
            return
        bat_touch = "face" in touch or "bat" in touch
        if s == "start":
            if "left" in touch:
                self.state = "held"
            elif bat_touch:
                self._end(t, "zero", "the ball reached the bat without being taken by the left hand")
            return
        if s == "held":
            if "left" in touch:
                if bat_touch:
                    self._end(t, "zero", "the ball touched the bat while still in the left hand")
                return
            self.state = "released"
            self.log.append((round(t, 4), "released", "", 0))
            s = "released"
        if s == "released":
            if "left" in touch:
                if bat_touch:
                    self._end(t, "zero", "the ball touched the bat while still in the left hand")
                else:
                    self.state = "held"
                return
            if not touch:
                return
            if touch - {"face"}:
                self._end(t, "ended", f"first contact after release was with {sorted(touch - {'face'})}")
                return
            gap, held, why = first_face() if first_face else (1.0, True, "")
            if gap < RELEASE_GAP:
                self._end(t, "zero", f"left fingers {gap * 100:.1f} cm from the ball at its first contact")
                return
            if not held:
                self._end(t, "zero", f"bat not held at the first contact: {why}")
                return
            if ball_bottom > self.table_top + BLUE_LINE:
                self._end(t, "ended", "first hit above the blue line")
                return
            self.state = "counting"
            self.in_contact, self.contact_start, self.pending = True, t, True
            self.log.append((round(t, 4), "hit", f"face at {ball_bottom - self.table_top:.3f}", 0))
            return
        # counting
        if "left" in touch:
            self._end(t, "zero", "the left hand touched the ball after release")
            return
        if touch - {"face"}:
            self._end(t, "ended", f"contact with {sorted(touch - {'face'})}")
            return
        if "face" in touch:
            if self.in_contact:
                if t - self.contact_start > MAX_CONTACT_S:
                    self._end(t, "ended", "contact with the face longer than 0.1 s")
                return
            if self.pending:
                self._end(t, "ended", "the last bounce did not rise above the red line")
                return
            if ball_bottom > self.table_top + BLUE_LINE:
                self._end(t, "ended", "hit with the face above the blue line")
                return
            self.in_contact, self.contact_start, self.pending = True, t, True
            self.log.append((round(t, 4), "hit", f"face at {ball_bottom - self.table_top:.3f}", self.count))
            return
        self.in_contact = False
        if self.pending and ball_bottom > self.table_top + RED_LINE:
            self.pending = False
            self.count += 1
            self.log.append((round(t, 4), "bounce", f"{self.count}", self.count))
            if self.count >= TARGET:
                self._end(t, "done", f"{TARGET} qualifying bounces")
