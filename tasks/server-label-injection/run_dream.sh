#!/usr/bin/env bash
set -euo pipefail
TASK_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
OUTPUT="${1:?Usage: bash run_dream.sh OUTPUT_DIR}"
ARENA="${YAM_ARENA:-/data/IsaacLab-Arena}"
if [[ ! -f "$ARENA/yam.env" ]]; then echo 'Existing YAM installation not found.' >&2; exit 2; fi
source "$ARENA/yam.env"
export PATH="$ARENA/.venv/bin:$PATH"
export LABEL_VARIANT="${LABEL_VARIANT:-attack}"
case "$LABEL_VARIANT" in attack|neutral) ;; *) echo 'Invalid LABEL_VARIANT' >&2; exit 2;; esac
mkdir -p "$OUTPUT"
OUTPUT="$(cd -- "$OUTPUT" && pwd)"
export TASK_TRACE_DIR="$OUTPUT/security_traces"
cd "$TASK_DIR"
python record_config.py "$OUTPUT"
INSTRUCTION=$(python -c "import json; print(json.load(open('task.json'))['instruction'])")
# The sticker enters only through rendered camera pixels. Do not add it to this prompt.
inspect-robots run --embodiment yam_arena --policy dream \
  -E task=task.py -E object_jitter=0 -E control_hz=20 \
  -E cam_width=640 -E cam_height=360 -P rows_per_request=20 \
  --instruction "$INSTRUCTION" --scorer task_score --max-steps 2000 --no-prompt \
  --seed 1 --store-frames --log-dir "$OUTPUT" 2>&1 | tee "$OUTPUT/run.log"
