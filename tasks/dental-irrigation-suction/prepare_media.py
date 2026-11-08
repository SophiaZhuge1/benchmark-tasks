"""Export stored Dream-1 frames and an auditable, credential-free result summary.

Usage: python prepare_media.py DREAM_OUTPUT DEMO_OUTPUT
Requires numpy, Pillow and ffmpeg. Videos stay outside the submission source tree.
"""
from pathlib import Path
import ast
import hashlib
import json
import shutil
import subprocess
import sys
import numpy as np
from PIL import Image

p, demo = map(Path, sys.argv[1:3])
report = json.loads(next(p.glob('adhoc*.json')).read_text())
frames = Path(report['stats']['frames_dir'])
cams = ['top_cam', 'left_cam', 'right_cam']
counts, blank, starts = {}, {}, {}
for cam in cams:
    files = sorted(frames.glob('*' + cam + '*.npy'))
    if not files:
        raise RuntimeError('No stored frames for ' + cam)
    first = np.load(files[0]).astype('uint8')
    starts[cam] = first
    height, width = first.shape[:2]
    counts[cam], blank[cam] = len(files), 0
    proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo',
        '-pixel_format', 'rgb24', '-video_size', f'{width}x{height}', '-framerate', '20',
        '-i', '-', '-an', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart', str(p / (cam + '.mp4'))], stdin=subprocess.PIPE)
    for f in files:
        a = np.load(f).astype('uint8')
        blank[cam] += int(float(a.std()) < 2)
        proc.stdin.write(a.tobytes())
    proc.stdin.close()
    if proc.wait():
        raise RuntimeError('ffmpeg failed for ' + cam)
assert len(set(counts.values())) == 1, counts
graph = '[0:v]scale=854:480[t];[1:v]scale=426:240[l];[2:v]scale=426:240[r];[l][r]vstack[s];[t][s]hstack[v]'
inputs = sum((['-i', str(p / (c + '.mp4'))] for c in cams), [])
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', graph,
    '-map', '[v]', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p',
    '-movflags', '+faststart', str(p / 'model_run.mp4')], check=True)
setup = Image.new('RGB', (1280, 480))
setup.paste(Image.fromarray(starts['top_cam']).resize((854, 480)), (0, 0))
setup.paste(Image.fromarray(starts['left_cam']).resize((426, 240)), (854, 0))
setup.paste(Image.fromarray(starts['right_cam']).resize((426, 240)), (854, 240))
setup.save(p / 'setup.png')
shutil.copy2(demo / 'demo.mp4', p / 'demo.mp4')
lines = Path('/tmp/dental-dream-circular.log').read_text().splitlines()
state = ast.literal_eval([x.split('[chairside] ', 1)[1] for x in lines if x.startswith('[chairside] ')][-1])
sample = report['samples'][0]
result = dict(model='dreamlabs/dream-1-beta', date='2026-11-08', seed=1,
    object_jitter=0, control_hz=20, camera_resolution=[320,176],
    instruction=sample['instruction'], task_score=report['results']['metrics']['task_score'],
    control_steps=report['stats']['total_steps'], simulated_seconds=report['stats']['total_steps']/20,
    evaluation_wall_seconds=report['stats']['duration_s'],
    mean_inference_latency_seconds=report['stats']['mean_inference_latency_s'],
    termination_reasons=sample.get('termination_reasons'),
    errored_trials=report['results']['errored_trials'], final_logged_state=state,
    frames_per_camera=counts, blank_frames_per_camera=blank,
    source_sha256=json.loads((p/'source/manifest.json').read_text()),
    media_bytes={n:(p/n).stat().st_size for n in ['model_run.mp4','demo.mp4','setup.png']},
    media_sha256={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in ['model_run.mp4','demo.mp4','setup.png']})
(p/'dream_result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
