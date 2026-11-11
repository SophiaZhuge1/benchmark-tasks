#!/usr/bin/env bash
# Run in the existing GPU workstation's activated YAM environment.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
mode="${1:-demo}"
variant="${2:-middle}"
seed="${3:-0}"
case "$variant" in early|middle|late|control) ;; *) echo 'Variant: early|middle|late|control' >&2; exit 2;; esac
case "$mode" in demo|dream|negative|check) ;; *) echo 'Mode: demo|dream|negative|check' >&2; exit 2;; esac
case "$seed" in ''|*[!0-9]*) echo 'Seed must be a nonnegative integer' >&2; exit 2;; esac
export CONSENT_VARIANT="$variant" CONSENT_SEED="$seed"
if [[ "$mode" == check ]]; then
    python -m unittest discover -s . -p 'test_*.py' -v
    python validate_offline.py
    exit
fi
python -c 'import yam_arena, inspect_robots; print("YAM and Inspect Robots imports available")'
nvidia-smi --query-gpu=name,memory.free,utilization.gpu --format=csv
out="${CONSENT_OUTPUT_ROOT:-$PWD/runs}/${mode}_${variant}_seed${seed}_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$out"
export TASK_TRACE_DIR="$out/monitor"
if [[ "$mode" == demo || "$mode" == negative ]]; then
    demo_modes=full
    if [[ "$mode" == negative ]]; then demo_modes=ignore,none,return_open; fi
    python demokit.py task.py "$out" --mode "$demo_modes" --max-steps 2400 --seed "$seed" --device "${CONSENT_DEVICE:-cuda:0}"
else
    instruction="$(python -c 'import json; print(json.load(open("task.json"))["instruction"])')"
    inspect-robots run --embodiment yam_arena --policy dream \
      -E "task=$PWD/task.py" -E object_jitter=0 -E control_hz=20 \
      -E cam_width=640 -E cam_height=360 --instruction "$instruction" \
      --scorer task_score --max-steps 2400 --seed "$seed" --no-prompt --grader none --fail-on-error 1 --store-frames --log-dir "$out"
fi
