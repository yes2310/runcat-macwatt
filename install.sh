#!/bin/bash
# RunCat Neo x macwatt: offline installer and in-place updater. Run as your user.
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Error: macOS is required." >&2
  exit 1
fi
if [[ "$(id -u)" == "0" ]]; then
  echo "Error: run as your regular user, without sudo." >&2
  exit 1
fi

SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/share/runcat-macwatt"
JSON_FILE="$HOME/.config/runcat-neo-metrics/macbook-power.json"
AGENT="$HOME/Library/LaunchAgents/dev.runcat.macwatt.plist"
LABEL="dev.runcat.macwatt"
PYTHON="$(command -v python3 || true)"

if [[ -z "$PYTHON" ]] || ! "$PYTHON" -c 'import sys; assert sys.version_info >= (3, 8)' 2>/dev/null; then
  echo "Error: Python 3.8+ is required (check: python3 --version)." >&2
  exit 1
fi
for file in power_metrics.py third_party/macwatt/macwatt.py third_party/macwatt/LICENSE; do
  if [[ ! -f "$SOURCE_DIR/$file" ]]; then
    echo "Error: missing $file. Extract the whole release ZIP first." >&2
    exit 1
  fi
done

TEMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/runcat-macwatt.XXXXXXXX")"
RESTORE_ON_FAILURE=0
restore_on_error() {
  local result=$?
  if [[ "$RESTORE_ON_FAILURE" == "1" && "$result" != "0" ]]; then
    echo "Update failed; restoring previous installation." >&2
    launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
    for file in macwatt.py LICENSE.macwatt power_metrics.py; do
      if [[ -f "$TEMP_DIR/backup/$file" ]]; then
        cp "$TEMP_DIR/backup/$file" "$INSTALL_DIR/$file" || true
      else
        rm -f "$INSTALL_DIR/$file"
      fi
    done
    if [[ -f "$TEMP_DIR/backup/agent.plist" ]]; then
      cp "$TEMP_DIR/backup/agent.plist" "$AGENT" || true
      launchctl bootstrap "gui/$(id -u)" "$AGENT" >/dev/null 2>&1 || true
    else
      rm -f "$AGENT"
    fi
    if [[ -f "$TEMP_DIR/backup/metrics.json" ]]; then
      cp "$TEMP_DIR/backup/metrics.json" "$JSON_FILE" || true
    else
      rm -f "$JSON_FILE"
    fi
  fi
  rm -rf "$TEMP_DIR"
}
trap restore_on_error EXIT

# Preflight runs before terminating an existing installation.
cp "$SOURCE_DIR/power_metrics.py" "$TEMP_DIR/power_metrics.py"
cp "$SOURCE_DIR/third_party/macwatt/macwatt.py" "$TEMP_DIR/macwatt.py"
cp "$SOURCE_DIR/third_party/macwatt/LICENSE" "$TEMP_DIR/LICENSE.macwatt"

echo "[1/4] Check the bundled Python files and live MacBook power telemetry"
"$PYTHON" -m py_compile "$TEMP_DIR/macwatt.py" "$TEMP_DIR/power_metrics.py"
if ! "$PYTHON" -B "$TEMP_DIR/power_metrics.py" --check >"$TEMP_DIR/preflight.json"; then
  echo "Error: power telemetry is not available; existing installation is unchanged." >&2
  echo "Check: ioreg -rn AppleSmartBattery -w0" >&2
  exit 1
fi

mkdir -p "$INSTALL_DIR" "$(dirname "$JSON_FILE")" "$HOME/Library/LaunchAgents" "$TEMP_DIR/backup"
for file in macwatt.py LICENSE.macwatt power_metrics.py; do
  if [[ -f "$INSTALL_DIR/$file" ]]; then
    cp "$INSTALL_DIR/$file" "$TEMP_DIR/backup/$file"
  fi
done
if [[ -f "$AGENT" ]]; then
  cp "$AGENT" "$TEMP_DIR/backup/agent.plist"
fi
if [[ -f "$JSON_FILE" ]]; then
  cp "$JSON_FILE" "$TEMP_DIR/backup/metrics.json"
fi

RESTORE_ON_FAILURE=1

echo "[2/4] Stop the previous service, if installed"
launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true

echo "[3/4] Install bundled macwatt and the RunCat bridge"
install -m 644 "$TEMP_DIR/macwatt.py" "$INSTALL_DIR/macwatt.py"
install -m 644 "$TEMP_DIR/LICENSE.macwatt" "$INSTALL_DIR/LICENSE.macwatt"
install -m 644 "$TEMP_DIR/power_metrics.py" "$INSTALL_DIR/power_metrics.py"

"$PYTHON" - "$AGENT" "$PYTHON" "$INSTALL_DIR/power_metrics.py" "$INSTALL_DIR/service-error.log" <<'PY'
import plistlib
import sys
plist_path, interpreter, script, log = sys.argv[1:]
service = {
    "Label": "dev.runcat.macwatt",
    "ProgramArguments": [interpreter, "-B", script, "--interval", "5"],
    "RunAtLoad": True,
    "KeepAlive": True,
    "ThrottleInterval": 10,
    "ProcessType": "Background",
    "EnvironmentVariables": {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin"},
    "StandardErrorPath": log,
}
with open(plist_path, "wb") as handle:
    plistlib.dump(service, handle)
PY

"$PYTHON" -B "$INSTALL_DIR/power_metrics.py" --once >/dev/null

echo "[4/4] Register login service (5-second polling)"
launchctl bootstrap "gui/$(id -u)" "$AGENT"
RESTORE_ON_FAILURE=0

echo
echo "Installed! The service checks every 5 seconds and writes only on change."
echo "RunCat Neo > Settings > Metrics > Custom Metrics > Add Custom Metrics Source"
echo "Source file: $JSON_FILE"
echo "On upgrade, keep the existing source; its path does not change."
echo "For a cat-only menu bar, keep the Metrics Bar disabled."
echo "Status: bash '$SOURCE_DIR/status.sh'"
