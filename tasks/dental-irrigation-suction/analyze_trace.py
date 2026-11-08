"""Report measured circular motion from demokit's trace, without importing Isaac.

Usage: python3 analyze_trace.py /path/to/full/trace.json
The trace rounds tip positions to 0.1 mm; these measurements are approximate.
"""
import json
import sys
import numpy as np
from fluid_model import SITES, STARTS


def analyze(path):
    trace = json.load(open(path))
    output = []
    for i, (site, start) in enumerate(zip(SITES, STARTS)):
        rows = [r for r in trace if start + 1.8 <= r['time'] <= start + 4.6]
        if len(rows) < 2:
            output.append({'tooth': i + 1, 'error': 'outer sweep missing'})
            continue
        delta = np.array([r['irrigator_tip'][:2] for r in rows]) - site[:2]
        radii = np.linalg.norm(delta, axis=1) * 1000
        angle = np.unwrap(np.arctan2(delta[:, 1], delta[:, 0]))
        output.append({
            'tooth': i + 1,
            'outer_sweep_degrees': round(float(np.degrees(angle[-1] - angle[0])), 1),
            'radius_mm_min_mean_max': np.round([radii.min(), radii.mean(), radii.max()], 2).tolist(),
            'covered_regions': trace[-1]['coverage'][i],
            'minimum_region_dwell_s': min(trace[-1]['coverage_s'][i]),
        })
    return output


if __name__ == '__main__':
    print(json.dumps(analyze(sys.argv[1]), indent=2))
