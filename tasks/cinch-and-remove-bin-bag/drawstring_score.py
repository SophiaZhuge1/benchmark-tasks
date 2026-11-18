"""Tiered, latched, geometry-only score for the drawstring bin-bag task.

Shared by the scripted demo, the Dream-1 run and offline replay. It reads only
recorded geometry (film mesh, waste-block poses, drawstring-loop poses, TCPs).
Every rule mirrors a check a person can make with a ruler, a photo and a count.

Tiers (highest satisfied applies; failures latch to 0 for the rest of the run):
  0.00  never cinched (opening never <= 80 mm), any waste block escapes the bag,
        or invalid/incomplete geometry (film edge stretch > 1.5, gaps, NaN).
  0.25  cinched: opening <= 80 mm at some step with all three blocks inside.
  0.50  carried: after cinching, the whole bag and its contents were clear of
        the bin (>= 20 mm above its rim) with the opening <= 80 mm.
  0.75  set down: at the end the bag rests upright on the tabletop, beside and
        clear of the bin, opening <= 80 mm, contents inside; still held or
        moving.
  1.00  released: the 0.75 state holds for the final two seconds with both
        grippers >= 60 mm from film and drawstring loops and bag bounds moving
        <= 10 mm.
"""
from collections import deque
import numpy as np
from evaluate_removal import contents_retained

TABLE_Z = .7475
TABLE_LO = np.array([-.19, -.65])
TABLE_HI = np.array([.91, .65])
# A 70 x 100 x 45 mm block's smallest face has an 83 mm diagonal, so it cannot
# pass a mouth opening of 80 mm or less: that is the closure threshold.
CINCH_M = .080          # opening that counts as cinched
CLOSED_M = .080         # opening that must be kept while carried / set down
CLEAR_M = .020          # clearance above rim, and margin to table edges / bin
UPRIGHT_MOUTH_M = .15   # gathered mouth at least this high above the tabletop
SUPPORT_M = .025        # bag bottom within this of the tabletop
RELEASE_M = .060        # grippers away from film and loops
STILL_M = .010          # bag-bounds motion over the final hold
HOLD_STEPS = 40         # two seconds at 20 Hz


class DrawstringJudge:
    def __init__(self, parameters):
        import trimesh
        from realistic_meshes_v32 import dirty_mesh
        self.top = float(parameters['bin_top_z'])
        self.centre = np.asarray(parameters['bin_center_xy'], float)
        self.radius = float(parameters.get('bin_outer_radius_m', .106))
        self.maximum_gap = int(parameters.get('sample_interval_steps', 1))
        vv, ff, _ = dirty_mesh()
        mesh = trimesh.Trimesh(vertices=vv, faces=ff, process=False)
        self.shape = mesh.vertices.shape
        self.edges = mesh.edges_unique
        self.rest = np.linalg.norm(mesh.vertices[self.edges[:, 1]] - mesh.vertices[self.edges[:, 0]], axis=1)
        self.mouth_ids = np.unique(mesh.edges_unique[np.bincount(mesh.edges_unique_inverse) == 1])
        self.failure = None
        self.count = 0
        self.previous = -1
        self.first_cinch = None
        self.first_carry = None
        self.max_strain = 1.
        self.tail = deque()
        self.last = {}

    def fail(self, why, **extra):
        self.failure = {'score': 0., 'full_task_success': False, 'tier': 'failed', 'reason': why,
                        'failure_step': self.previous + 1, **extra}
        return self.failure

    @staticmethod
    def opening(v, ids):
        neck = v[ids]
        return float(np.max(np.linalg.norm(neck[:, None, :] - neck[None, :, :], axis=2)))

    def update(self, s, vertices):
        if self.failure is not None:
            return self.failure
        try:
            step = int(s['step'])
            v = np.asarray(vertices, float)
            if step > 4000:
                return self.fail('Run limit exceeded')
            if step < self.previous or (self.previous >= 0 and step - self.previous > self.maximum_gap):
                return self.fail('Incomplete or unordered motion evidence')
            if v.shape != self.shape or not np.isfinite(v).all():
                return self.fail('Invalid bag mesh evidence')
            mouth = self.opening(v, self.mouth_ids)
            if abs(mouth - float(s['mouth_diameter'])) > .001:
                return self.fail('Mouth measurement inconsistent with recorded mesh')
            if self.count == 0:
                if step != 0:
                    return self.fail('Missing initial state')
                if mouth < .10:
                    return self.fail('Bag did not start open')
                if np.linalg.norm(v[:, :2].mean(0) - self.centre) > .03 or v[:, 2].min() > self.top - .10:
                    return self.fail('Bag did not start inside bin')
            strain = float(np.max(np.linalg.norm(v[self.edges[:, 1]] - v[self.edges[:, 0]], axis=1) / self.rest))
            self.max_strain = max(self.max_strain, strain)
            if strain > 1.5:
                return self.fail('Numerically invalid film deformation; rerun required', trial_valid=False,
                                 max_recorded_edge_stretch_ratio=self.max_strain)
            retained, corners = contents_retained(s, v)
            if not retained:
                return self.fail('Waste block outside the bag' if self.count else 'Initial three waste blocks not retained')
            points = np.concatenate([v, corners])
            if mouth <= CINCH_M and self.first_cinch is None:
                self.first_cinch = step
            above_rim = bool(points[:, 2].min() >= self.top + CLEAR_M)
            if self.first_cinch is not None and self.first_carry is None and above_rim and mouth <= CLOSED_M:
                self.first_carry = step
            # Tabletop state.
            loops = np.asarray(s.get('loop_points', []), float).reshape(-1, 3)
            tcp = np.asarray(s.get('tcp', []), float)
            if len(loops) and tcp.shape == (2, 3):
                grasp_points = np.concatenate([v, loops])
                separation = float(np.linalg.norm(tcp[:, None, :] - grasp_points[None, :, :], axis=2).min())
            else:
                separation = 0.
            lo, hi = points[:, :2].min(0), points[:, :2].max(0)
            on_table = bool(np.all(lo >= TABLE_LO + CLEAR_M) and np.all(hi <= TABLE_HI - CLEAR_M))
            beside = bool(np.any(lo >= self.centre + self.radius + CLEAR_M) or np.any(hi <= self.centre - self.radius - CLEAR_M))
            bottom = float(points[:, 2].min())
            mouth_height = float(v[self.mouth_ids, 2].mean() - TABLE_Z)
            set_down = bool(on_table and beside and abs(bottom - TABLE_Z) <= SUPPORT_M
                            and mouth_height >= UPRIGHT_MOUTH_M and mouth <= CLOSED_M)
            released = bool(set_down and separation >= RELEASE_M)
            bounds = np.concatenate([v.min(0), v.max(0)])
            self.tail.append((step, set_down, released, bounds))
            while len(self.tail) > 1 and self.tail[1][0] <= step - HOLD_STEPS:
                self.tail.popleft()
            self.last = {'final_mouth_diameter_m': mouth, 'bag_bottom_above_table_m': bottom - TABLE_Z,
                         'mouth_height_above_table_m': mouth_height, 'whole_load_on_table': on_table,
                         'beside_bin': beside, 'minimum_gripper_distance_m': separation,
                         'set_down_now': set_down, 'released_now': released}
            self.previous = step
            self.count += 1
            return self.result()
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            return self.fail('Invalid evidence: ' + str(exc))

    def result(self):
        if self.failure is not None:
            return self.failure
        if self.count < 1:
            return {'score': 0., 'full_task_success': False, 'tier': 'none', 'reason': 'Missing initial state'}
        base = {'first_cinch_step': self.first_cinch, 'first_carry_step': self.first_carry,
                'max_recorded_edge_stretch_ratio': self.max_strain, 'steps': self.previous, **self.last}
        if self.first_cinch is None:
            return dict(base, score=0., full_task_success=False, tier='none', reason='Opening never reached 80 mm')
        tail = list(self.tail)
        motion = float(np.ptp(np.asarray([x[3] for x in tail]), axis=0).max()) if tail else float('inf')
        full_window = len(tail) >= 2 and tail[0][0] <= self.previous - HOLD_STEPS
        if self.first_carry is not None and full_window and all(x[2] for x in tail) and motion <= STILL_M:
            score, tier = 1., 'released'
        elif self.first_carry is not None and tail and tail[-1][1]:
            score, tier = .75, 'set_down'
        elif self.first_carry is not None:
            score, tier = .5, 'carried'
        else:
            score, tier = .25, 'cinched'
        return dict(base, score=score, full_task_success=score == 1., tier=tier, cinch_verified=True,
                    final_two_second_bag_bounds_motion_m=motion)


def evaluate(trace, snapshots, parameters):
    judge = DrawstringJudge(parameters)
    for s in trace:
        judge.update(s, snapshots[s['step']])
        if judge.failure is not None:
            break
    return judge.result()
