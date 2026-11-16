"""Fail-closed scorer for the ordinary-liner revision under development.

The legacy geometry judge can establish a cinched mouth, retention and placement.
It CANNOT establish that a factory drawtape knot was tied. Until a knot/closure
verifier is validated against physical and adversarial examples, no episode of
this candidate can claim the secure-closure/extraction/deposit tiers. This is a
visible development blocker, not a fake success predicate or a controller flag.
"""
from table_deposit import TableDepositJudge

class OrdinaryLinerJudge(TableDepositJudge):
    def result(self):
        geometry=super().result()
        if self.failure is not None:return geometry
        cinched=bool(geometry.get('cinch_verified')) and geometry.get('score',0.)>0
        return dict(geometry,placement_geometry_score=geometry.get('score',0.),
                    score=.25 if cinched else 0.,full_task_success=False,
                    ordinary_closure_verified=False,
                    reason='Ordinary drawtape knot verification has not been validated; closure-dependent credit is withheld.',
                    scope='Development candidate: cinching only may receive partial credit; no full-score claim.')
