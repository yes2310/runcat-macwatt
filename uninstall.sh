#!/bin/bash
# Remove just the RunCat x macwatt bridge. Run without sudo.
set -euo pipefail
if [[ "$(uname -s)" != "Darwin" ]] || [[ "$(id -u)" == "0" ]]; then
  echo "Run this script as your regular macOS user (without sudo)." >&2
  exit 1
fi
LABEL="dev.runcat.macwatt"
launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
rm -f "$HOME/Library/LaunchAgents/$LABEL.plist"
rm -f "$HOME/.config/runcat-neo-metrics/macbook-power.json"
rm -rf "$HOME/.local/share/runcat-macwatt"
echo "Removed the macwatt bridge. Also remove its Custom Metrics source in RunCat Neo settings."
