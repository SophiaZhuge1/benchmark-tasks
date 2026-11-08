#!/usr/bin/env bash
set -euo pipefail
TASK_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
PYTHON_BIN="${YAM_PYTHON:-/data/IsaacLab-Arena/.venv/bin/python}"
OUTPUT="${1:-$PWD/results}"
exec "$PYTHON_BIN" "$TASK_DIR/demokit.py" "$TASK_DIR/task.py" "$OUTPUT" --seed 1 --render 640x360 "${@:2}"
