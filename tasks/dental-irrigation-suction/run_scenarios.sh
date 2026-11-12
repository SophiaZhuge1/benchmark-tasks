#!/usr/bin/env bash
set -euo pipefail
TASK_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
PYTHON_BIN="${YAM_PYTHON:-/data/IsaacLab-Arena/.venv/bin/python}"
OUTPUT="${1:?Supply a NEW output directory}"
shift
if [[ -e "$OUTPUT" ]]; then echo "Refusing to overwrite existing evidence: $OUTPUT" >&2; exit 2; fi
mkdir -p "$OUTPUT"
OUTPUT="$(cd "$OUTPUT" && pwd)"
if (( $# == 0 )); then set -- full point static late_suction fixed_site no_withdraw off obstruct none; fi
for scenario in "$@"; do
  # New simulator process per case prevents state/failed-flag leakage.
  "$PYTHON_BIN" "$TASK_DIR/demokit.py" "$TASK_DIR/task.py" "$OUTPUT/$scenario" --mode "$scenario" --seed 1 --render 640x360 --device "${YAM_DEVICE:-cuda:0}" > "$OUTPUT/$scenario.log" 2>&1
  "$PYTHON_BIN" "$TASK_DIR/verify_scenarios.py" "$OUTPUT/$scenario" > "$OUTPUT/$scenario-check.json"
done
