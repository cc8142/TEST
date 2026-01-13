#!/usr/bin/env bash
set -euo pipefail

SUITE="${1:-all}"
ENV_NAME="${2:-local}"
BASE_URL="${BASE_URL:-}"
WORKERS="${WORKERS:-0}"
RERUNS="${RERUNS:-0}"
BROWSER="${BROWSER:-chromium}"
HEADED="${HEADED:-0}"

ARGS=(tests/run_all.py --suite "$SUITE" --env "$ENV_NAME" --workers "$WORKERS" --reruns "$RERUNS" --browser "$BROWSER" --allure-report)

if [[ -n "$BASE_URL" ]]; then
  ARGS+=(--base-url "$BASE_URL")
fi

if [[ "$HEADED" == "1" ]]; then
  ARGS+=(--headed)
fi

python "${ARGS[@]}"
echo "Report generated at reports/summary.html"
