#!/bin/bash
# Check installation without modifying anything.
set -euo pipefail
LABEL=dev.runcat.macwatt
INSTALL_DIR="$HOME/.local/share/runcat-macwatt"
JSON_FILE="$HOME/.config/runcat-neo-metrics/macbook-power.json"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Run on the MacBook where the bridge is installed." >&2
  exit 1
fi

echo "=== RunCat x macwatt status ==="
if launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1; then
  echo "launchd: registered"
else
  echo "launchd: not registered"
fi
if [[ -f "$JSON_FILE" ]]; then
  echo "JSON: $JSON_FILE"
  python3 -m json.tool "$JSON_FILE"
else
  echo "JSON: missing ($JSON_FILE)"
fi
if [[ -f "$INSTALL_DIR/last-error.txt" ]]; then
  echo "Last sensor error:"
  cat "$INSTALL_DIR/last-error.txt"
fi
if [[ -f "$INSTALL_DIR/service-error.log" ]]; then
  echo "Recent service stderr (last 10 lines):"
  tail -n 10 "$INSTALL_DIR/service-error.log"
fi
