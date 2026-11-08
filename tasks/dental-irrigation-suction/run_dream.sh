#!/usr/bin/env bash
set -euo pipefail
TASK_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
OUTPUT="${1:?Usage: bash run_dream.sh OUTPUT_DIR}"
ARENA="${YAM_ARENA:-/data/IsaacLab-Arena}"
source "$ARENA/yam.env"
export PATH="$ARENA/.venv/bin:$PATH"
mkdir -p "$OUTPUT/source"
cp "$TASK_DIR"/*.py "$TASK_DIR/task.json" "$OUTPUT/source/"
cd "$TASK_DIR"
INSTRUCTION=$(python -c "import json; print(json.load(open('task.json'))['instruction'])")
python -c "import hashlib,json,pathlib; p=pathlib.Path('$OUTPUT/source'); (p/'manifest.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in p.iterdir() if f.is_file()},indent=2))"
inspect-robots run --embodiment yam_arena --policy dream \
  -E task=task.py -E object_jitter=0 -E control_hz=20 \
  -E cam_width=320 -E cam_height=176 -P rows_per_request=20 \
  --instruction "$INSTRUCTION" --scorer task_score --max-steps 1200 \
  --seed 1 --store-frames --log-dir "$OUTPUT" 2>&1 | tee "$OUTPUT/run.log"
