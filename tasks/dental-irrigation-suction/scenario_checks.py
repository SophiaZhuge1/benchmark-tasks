"""Controlled water-model comparisons; no robot, contact or hardware evidence.

python scenario_checks.py --output validation/scenario_results.json
All cases use the production 20 Hz water model and identical supply windows.
"""
import argparse
import hashlib
import gzip
import json
from pathlib import Path
import numpy as np
from fluid_model import WaterModel, SITES, STARTS, DURATION, sweep_offsets

EXPECTED = {'full': 1., 'fixed_site': 1., 'point': 0., 'static': 0.,
            'wrong_place': 0., 'too_high': 0., 'off': 0., 'late_suction': 0., 'no_withdraw': .75,
            'not_retained': .75, 'obstruct': 0., 'obstruct_then_recover': 0.,
            'dry_sweep': 0., 'none': 0.}


def run(mode, dt=.05):
    w = WaterModel()
    trace = []
    away = np.array([0., 0., .1])
    for k in range(round(60/dt)):
        t = k*dt
        i = max([i for i,s in enumerate(STARTS) if t >= s-2.] or [0])
        p = SITES[i]
        ir_offset, su_offset = sweep_offsets(max(0., t-STARTS[i]))
        ir, su = p+ir_offset, p+su_offset
        if mode == 'fixed_site': su = p+[0,-.025,-.005]
        if mode == 'point': ir, su = p+[0,0,.018], p+[0,-.025,-.005]
        if mode == 'static': su = SITES[0]+[0,-.025,-.005]
        if mode == 'wrong_place': su = p+[0,-.080,-.005]
        if mode == 'too_high': su = p+[0,-.025,.018]
        if mode == 'off': su = away
        if mode == 'late_suction':
            su = away if t < 38. else SITES[min(2,int((t-38.)/6.))]+[0,-.025,-.005]
        if mode == 'obstruct' or (mode == 'obstruct_then_recover' and 16. <= t < 16.35):
            su = p+[0,0,.007]
        if mode == 'dry_sweep':
            if t < 15.:
                j = min(2,int(t/5.)); a,b = sweep_offsets(t-j*5.)
                ir, su = SITES[j]+a, SITES[j]+b
            else: ir, su = away, away+[.1,0,0]
        if mode == 'none': ir, su = away, away+[.1,0,0]
        w.step(dt, ir, su)
        assert abs(w.balance_error()) < 1e-8
        trace.append(dict(t=round(w.t,6), delivered=list(w.delivered), captured=list(w.captured),
                          pool=list(w.pool), crown=list(w.crown), mouth_water_ml=w.mouth_water(), lost=w.lost, peak=w.peak,
                          coverage=w.covered(), obstruction_s=w.obstruction_s,
                          failed=bool(w.failed)))
    clear, held = mode!='no_withdraw', mode!='not_retained'
    finished=mode not in {'no_withdraw','not_retained'}
    score = w.score(clear=clear, held=held, finished=finished)
    assert score == EXPECTED[mode], (mode,score,EXPECTED[mode])
    if mode == 'point':
        assert w.covered()==[1,1,1] and sum(w.captured)>=5.4
    if mode == 'late_suction':
        assert w.covered()==[9,9,9] and abs(sum(w.delivered)-6.) < 1e-8
    if mode == 'obstruct_then_recover':
        assert w.obstruction_s>.25 and w.failed and w.covered()==[9,9,9]
    return dict(mode=mode, expected_score=EXPECTED[mode], measured_model_score=score,
                passed=True, evidence_level='water_model_only', endpoint_gate_assumptions=dict(clear=clear,held=held,finished=finished),
                final=dict(supplied_ml=w.supplied, delivered_ml=list(w.delivered),
                           captured_ml=list(w.captured), pool_ml=list(w.pool), crown_ml=list(w.crown), mouth_water_ml=w.mouth_water(),
                           loss_ml=w.lost, peak_pool_ml=w.peak, coverage=w.covered(),
                           coverage_s=w.coverage_s, obstruction_s=w.obstruction_s,
                           failed=bool(w.failed), balance_error_ml=w.balance_error()), trace=trace)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    result = dict(evidence_level='water_model_only', control_hz=20, duration_s=60,
                  limitation='Prescribed tool coordinates, no robot contacts or feasible trajectories. Endpoint retention/withdrawal gates supplied by test. No video or hardware validation.',
                  source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest()
                                 for p in ['fluid_model.py','scenario_checks.py','finish.py']},
                  cases=[run(mode) for mode in EXPECTED])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for case in result['cases']:
        trace_path = args.output.parent / (case['mode'] + '.model_trace.json.gz')
        trace_bytes = gzip.compress(json.dumps(case.pop('trace'), separators=(',', ':')).encode(), mtime=0)
        trace_path.write_bytes(trace_bytes)
        case['trace_file'] = trace_path.name
        case['trace_sha256'] = hashlib.sha256(trace_bytes).hexdigest()
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    for case in result['cases']:
        print(f"{case['mode']}: {case['measured_model_score']} (water model only)")


if __name__ == '__main__':
    main()
