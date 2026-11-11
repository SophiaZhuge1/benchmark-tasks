#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
mode="${1:-demo}"
seed="${2:-0}"
case "$mode" in demo|debug|negative|dream|check) ;; *) echo 'Use demo|debug|negative|dream|check'; exit 2;; esac
if [[ "$mode" == check ]]; then python -m unittest discover -s . -p 'test_*.py' -v; exit; fi
out="${CURL_OUTPUT_ROOT:-$PWD/runs}/${mode}_seed${seed}_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$out"
export TASK_TRACE_DIR="$out/monitor"
if [[ "$mode" == dream ]]; then
  instruction="$(python -c 'import json;print(json.load(open("task.json"))["instruction"])')"
  inspect-robots run --embodiment yam_arena --policy dream -E "task=$PWD/task.py" -E object_jitter=0 -E control_hz=20 -E cam_width=640 -E cam_height=360 --instruction "$instruction" --scorer task_score --max-steps 1200 --seed "$seed" --no-prompt --grader none --fail-on-error 1 --store-frames --log-dir "$out"
else
  args=(--mode full --max-steps 1200 --seed "$seed" --device "${CURL_DEVICE:-cuda:0}")
  if [[ "$mode" == debug ]]; then args+=(--no-record --stills 20); fi
  if [[ "$mode" == negative ]]; then args[1]='no_rescue,none,weak'; fi
  python demokit.py task.py "$out" "${args[@]}"
fi
