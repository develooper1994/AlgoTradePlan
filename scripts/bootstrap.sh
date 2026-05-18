#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$ROOT_DIR/artifacts" "$ROOT_DIR/data" "$ROOT_DIR/logs"
python -m compileall "$ROOT_DIR/src" "$ROOT_DIR/scripts" "$ROOT_DIR/tests" >/dev/null
printf "Bootstrap complete.\n"
