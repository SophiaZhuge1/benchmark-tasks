#!/usr/bin/env bash
set -euo pipefail
TASK_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
PYTHON_BIN="${YAM_PYTHON:-/data/IsaacLab-Arena/.venv/bin/python}"
OUTPUT="${1:?Usage: bash run_brev.sh OUTPUT_DIR [--mode full] [--render 640x360]}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "YAM runtime missing: set YAM_PYTHON to the existing Isaac Lab environment's Python." >&2
  exit 2
fi
export LABEL_VARIANT="${LABEL_VARIANT:-attack}"
case "$LABEL_VARIANT" in attack|neutral) ;; *) echo 'Invalid LABEL_VARIANT' >&2; exit 2;; esac
mkdir -p "$OUTPUT"
OUTPUT="$(cd -- "$OUTPUT" && pwd)"
"$PYTHON_BIN" "$TASK_DIR/record_config.py" "$OUTPUT"
exec "$PYTHON_BIN" "$TASK_DIR/demokit.py" "$TASK_DIR/task.py" "$OUTPUT" --seed 1 "${@:2}"
