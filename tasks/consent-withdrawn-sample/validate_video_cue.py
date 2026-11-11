"""Compare the recorded top-camera colour transition with the monitor event.

This fixed-scene check complements visual inspection; it is not a text reader.
Requires ffmpeg, Pillow and numpy. Pass a demokit mode directory with result.json.
"""
import io
import json
import subprocess
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

def frame_at(path, t):
    data = subprocess.check_output([
        "ffmpeg", "-v", "error", "-ss", str(max(0., t)),
        "-i", str(path), "-frames:v", "1", "-f", "image2pipe",
        "-vcodec", "png", "-"])
    return Image.open(io.BytesIO(data)).convert("RGB")

def colours(image):
    a = np.asarray(image).astype(np.int16)
    r, g, b = a[:,:,0], a[:,:,1], a[:,:,2]
    return {"red": int(((r > 120) & (r > 1.5*g) & (r > 1.3*b)).sum()),
            "green": int(((g > 120) & (g > 1.5*r) & (g > 1.3*b)).sum())}

def check(directory):
    p = Path(directory)
    result = json.loads((p/"result.json").read_text())
    metrics = result["task_metrics"]
    t = metrics["withdrawal_t"]
    if t is None:
        raise ValueError("No withdrawal occurred; this checker needs a withdrawal trial")
    t = round(t, 6)
    times = [round(t-.05, 6), t, round(t+.05, 6)]
    frames = [frame_at(p/"top_cam.mp4", at) for at in times]
    counts = [colours(im) for im in frames]
    passed = (counts[0]["green"] > 200 and counts[0]["red"] < 50
              and all(c["red"] > 200 and c["red"] > 3*c["green"] for c in counts[1:]))
    report = {"run": str(p), "withdrawal_t": t, "control_hz": 20,
              "sample_times_s": times, "colour_pixels": counts,
              "cue_frame_check_passed": passed,
              "scope": "Fixed scene, recorded top camera; full-frame dominant red/green colour check, plus manual word readability review."}
    (p/"cue_validation.json").write_text(json.dumps(report, indent=2)+"\n")
    board = Image.new("RGB", (1200,250), "white")
    draw = ImageDraw.Draw(board)
    for i,(im,at) in enumerate(zip(frames,times)):
        board.paste(im.resize((400,225)),(i*400,25))
        draw.text((i*400+8,6),f"{at:.2f} s",fill="black")
    board.save(p/"cue_transition.jpg")
    print(json.dumps(report))
    return passed

if __name__ == "__main__":
    raise SystemExit(0 if check(sys.argv[1]) else 1)
