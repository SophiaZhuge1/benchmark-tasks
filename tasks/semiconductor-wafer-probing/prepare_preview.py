"""Build a local preview from completed trials; never uploads or publishes."""
import argparse, json, pathlib, shutil

p=argparse.ArgumentParser()
p.add_argument('full');p.add_argument('destination')
p.add_argument('--drag');p.add_argument('--early-release');p.add_argument('--leave-lifted')
a=p.parse_args();out=pathlib.Path(a.destination);out.mkdir(parents=True,exist_ok=True)
sections=[]
for name,source,title in [('full',a.full,'Safe semiconductor wafer indexing'),
    ('drag',a.drag,'Control: move with probes down'),
    ('early_release',a.early_release,'Control: release probe lift too early'),
    ('leave_lifted',a.leave_lifted,'Control: leave probes raised')]:
    if not source:continue
    src=pathlib.Path(source);r=json.loads((src/'result.json').read_text())
    for f in ('demo.mp4','setup.png','result.json','trace.json'):
        if (src/f).exists():shutil.copy2(src/f,out/(name+'-'+f))
    sections.append(f'<section><h2>{title}</h2><p>Score <b>{r["task_score"]}</b> · {r["seconds"]} simulated seconds · damage: {r["task_metrics"]["damaged"]}</p><video controls preload="metadata" poster="{name}-setup.png" src="{name}-demo.mp4"></video><p><a href="{name}-result.json">Result</a> · <a href="{name}-trace.json">Trace</a></p></section>')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Semiconductor wafer probing</title><style>body{background:#111827;color:#e5e7eb;font:17px/1.6 system-ui;margin:0}main{max-width:1100px;margin:auto;padding:30px 24px}h1{font-size:38px;line-height:1.15}h2{font-size:24px;margin-top:36px}video{width:100%;border-radius:12px}a{color:#93c5fd}.muted{color:#a7b4ca}</style><main><p class="muted">Bimanual YAM · Probe-station trainer</p><h1>Semiconductor wafer probing: move without scratching</h1><p>Move the semiconductor wafer to the next marked test position without dragging the probes across its surface.</p><p>Left arm holds the amber probe lift; right arm indexes the blue wafer-stage handle from A to B. After alignment, the probes return to B.</p>'''
page+=''.join(sections)
page+='<p><b>LIFT</b>: clearance achieved. <b>PAD</b>: probe contact band. <b>FAIL</b>: irreversible damage. <b>READY</b>: completed and released.</p><p class="muted">Scripted demonstrations using simulator state, not Dream-1. Enlarged rigid fixture with a sampled geometric damage model; no electrical testing or silicon fracture simulation.</p></main></html>'
(out/'index.html').write_text(page)
print('Preview ready:',out/'index.html')
