#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
source .venv/bin/activate

python pronunciation_worker.py > pronunciation_worker.log 2>&1 &
worker_pid=$!
trap 'kill "$worker_pid" 2>/dev/null || true' EXIT INT TERM

uvicorn main:app --reload
