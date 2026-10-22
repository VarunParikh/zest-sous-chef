#!/bin/bash
# Zest server (ADR-011), started by the Dock app (ZestApp.swift) from Contents/Resources.
# Checks the CPU before the arm64-only Python runs, then starts the launcher.
RES="$(cd "$(dirname "$0")" && pwd)"
if [ "$(/usr/bin/uname -m)" != "arm64" ] && [ "$(/usr/sbin/sysctl -n hw.optional.arm64 2>/dev/null)" != "1" ]; then
  /usr/bin/osascript -e 'display alert "Zest cannot run on this Mac" message "Zest needs a Mac with Apple silicon (M1 or newer)." as critical' >/dev/null 2>&1
  exit 1
fi
export PYTHONPATH="$RES/zest/src:$RES/zest"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
export PYTHONUNBUFFERED=1
export HF_HUB_OFFLINE=1
cd "$RES/zest" || exit 1
LOG_DIR="${ZEST_RUNTIME_DIR:-$HOME/Library/Application Support/Zest 2.0}/logs"  # Zest 2.0 data folder (ADR-012)
mkdir -p "$LOG_DIR"
exec "$RES/python/bin/python3" -s -X utf8 "$RES/zest/macapp/launcher.py" "$@" 2>>"$LOG_DIR/launcher.log"
