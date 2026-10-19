#!/bin/bash
# End-to-end install and uninstall on Linux with fake macOS command-line APIs.
# This is NOT a substitute for a real MacBook hardware test.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin" "$TMP/home"
export HOME="$TMP/home"
export PATH="$TMP/bin:$PATH"
cat > "$TMP/bin/uname" <<'EOF'
#!/bin/sh
printf 'Darwin\n'
EOF
cat > "$TMP/bin/id" <<'EOF'
#!/bin/sh
if [ "$1" = '-u' ]; then printf '501\n'; else /usr/bin/id "$@"; fi
EOF
cat > "$TMP/bin/launchctl" <<'EOF'
#!/bin/sh
echo "$*" >> "$HOME/launchctl.log"
if [ "${1:-}" = "bootstrap" ] && [ -f "$HOME/fail-next-bootstrap" ]; then
  rm "$HOME/fail-next-bootstrap"
  exit 77
fi
exit 0
EOF
cat > "$TMP/bin/ioreg" <<'EOF'
#!/bin/sh
cat <<'TELEMETRY'
+-- AppleSmartBattery <class AppleSmartBattery>
    "PowerTelemetryData" = {"SystemPowerIn"=86100,"BatteryPower"=67500,"SystemLoad"=18600}
    "AdapterDetails" = {"Watts"=140,"AdapterVoltage"=28000,"Current"=5000}
    "CurrentCapacity" = 70
    "ExternalConnected" = Yes
    "IsCharging" = Yes
TELEMETRY
EOF
chmod +x "$TMP/bin"/*

# First install: produces JSON and a single resident launchd job.
bash "$ROOT/install.sh" > "$TMP/install-output.log"
python3 - "$HOME" <<'PY'
import json, plistlib, sys
from pathlib import Path
home = Path(sys.argv[1])
json_path = home / '.config/runcat-neo-metrics/macbook-power.json'
data = json.loads(json_path.read_text())
assert data['title'] == '전력', data
assert data['metrics'][0]['formattedValue'] == '86.1 W', data
assert data['metrics'][3]['formattedValue'] == '140 W · 28 V / 5 A', data
assert 'metricsBarValue' not in data
service = plistlib.loads((home / 'Library/LaunchAgents/dev.runcat.macwatt.plist').read_bytes())
assert service['ProgramArguments'][-2:] == ['--interval','5'], service
assert service['RunAtLoad'] and service['KeepAlive'] is True
PY

# Repeat install: still works, same RunCat source path.
bash "$ROOT/install.sh" > /dev/null
test -f "$HOME/.config/runcat-neo-metrics/macbook-power.json"

# Preflight failure must not touch the current installation.
cp "$HOME/.local/share/runcat-macwatt/power_metrics.py" "$TMP/original.py"
cat > "$TMP/bin/ioreg" <<'EOF'
#!/bin/sh
exit 12
EOF
chmod +x "$TMP/bin/ioreg"
if bash "$ROOT/install.sh" > "$TMP/fail.log" 2>&1; then
  echo "Expected preflight failure" >&2
  exit 1
fi
cmp "$TMP/original.py" "$HOME/.local/share/runcat-macwatt/power_metrics.py"

# Bootstrap failure after files are replaced should roll back to the old files.
# Keep a harmless marker in the installed bridge so restoration is observable.
printf '\n# pre-upgrade-install marker\n' >> "$HOME/.local/share/runcat-macwatt/power_metrics.py"
touch "$HOME/fail-next-bootstrap"
cat > "$TMP/bin/ioreg" <<'EOF'
#!/bin/sh
cat <<'TELEMETRY'
+-- AppleSmartBattery <class AppleSmartBattery>
    "PowerTelemetryData" = {"SystemPowerIn"=86100,"BatteryPower"=67500,"SystemLoad"=18600}
    "AdapterDetails" = {"Watts"=140,"AdapterVoltage"=28000,"Current"=5000}
    "CurrentCapacity" = 70
    "ExternalConnected" = Yes
    "IsCharging" = Yes
TELEMETRY
EOF
chmod +x "$TMP/bin/ioreg"
if bash "$ROOT/install.sh" > "$TMP/bootstrap-fail.log" 2>&1; then
  echo "Expected launchctl bootstrap failure" >&2
  exit 1
fi
grep -q 'pre-upgrade-install marker' "$HOME/.local/share/runcat-macwatt/power_metrics.py"
test -f "$HOME/Library/LaunchAgents/dev.runcat.macwatt.plist"

# Removal must not delete unrelated metrics.
touch "$HOME/.config/runcat-neo-metrics/unrelated.json"
bash "$ROOT/uninstall.sh" >/dev/null
test ! -f "$HOME/Library/LaunchAgents/dev.runcat.macwatt.plist"
test ! -d "$HOME/.local/share/runcat-macwatt"
test ! -f "$HOME/.config/runcat-neo-metrics/macbook-power.json"
test -f "$HOME/.config/runcat-neo-metrics/unrelated.json"
echo 'Mock install / upgrade / preflight rollback / uninstall: PASS'
