# RunCat Neo × macwatt

**English** | [한국어](README.ko.md)

**MacBook charging and power metrics for RunCat Neo** — keep only the cat in your menu bar and check power details from the RunCat dashboard.

An unofficial, offline-installable Custom Metrics integration powered by [macwatt](https://github.com/ytomasch/macwatt). It reads your MacBook's actual power telemetry and maintains a local [RunCat Neo Custom Metrics](https://github.com/runcat-dev/RunCatNeo/blob/main/docs/CustomMetricsSchema.md) JSON file.

## What the card displays

| Metric | Example | Meaning |
| --- | --- | --- |
| `입력 전력` (input) | `86.1 W` | Measured power entering the Mac from the adapter |
| `배터리` (battery) | `충전 67.5 W` / `방전 18.6 W` | Power flowing into (charge) or out of (discharge) the battery |
| `시스템 소비` (system) | `18.6 W` | System power consumption |
| `충전기` (adapter) | `140 W · 28 V / 5 A` | The **negotiated** charger contract reported by the Mac |

> Values above are illustrative. The card title (`전력`, "Power") and row labels are currently in Korean. Adapter information is **not** the charger make/model or a wall-meter reading. This relies on Apple's undocumented power telemetry, so some fields may be missing or update late depending on the Mac model and macOS version.

No wattage is added to the menu bar. If RunCat Neo's **Metrics Bar** is enabled, turn it off or hide this source to keep only the cat.

## Requirements

- **Apple Silicon MacBook** exposing `PowerTelemetryData` under `AppleSmartBattery` (checked automatically before install)
- [RunCat Neo](https://github.com/runcat-dev/RunCatNeo) with Custom Metrics support
- `python3` **3.8 or later**, standard library only
- Runs in your macOS user session (no `sudo`)

**No internet connection is needed** to install. The release ZIP bundles the unmodified `macwatt.py` and its MIT license. At runtime it makes no network connections and asks for no account permissions.

## Install

Download `runcat-macwatt-v1.0.0.zip` from [GitHub Releases](https://github.com/yes2310/runcat-macwatt/releases), extract it, then run:

```bash
cd ~/Downloads/runcat-macwatt
bash install.sh
```

> If you extracted it somewhere else, `cd` into that folder and run `bash install.sh`.

When installation finishes, open RunCat Neo → **Settings → Metrics → Custom Metrics → Add Custom Metrics Source** and add this file:

```text
~/.config/runcat-neo-metrics/macbook-power.json
```

In the file picker, press `Command + Shift + G` to type the path. Keep the **Metrics Bar disabled** to show only the cat in your menu bar.

### Upgrading from v2/v3

Run the same `bash install.sh`. It stops the existing `dev.runcat.macwatt` agent and registers the new one. The metrics JSON **path stays the same, so you don't need to re-add it in RunCat.** The installer checks live sensor access before changing anything and tries to restore the previous install if the upgrade fails.

## How it works

1. macOS `launchd` starts **a single resident Python process** at login.
2. [macwatt](https://github.com/ytomasch/macwatt) reads power telemetry from `ioreg` **every 5 seconds**.
3. The RunCat JSON file is **atomically replaced only when the displayed values change**.
4. RunCat Neo detects the file change and refreshes the Custom Metrics card.

**Polling every 5 seconds does not mean a fresh sensor sample every 5 seconds.** The underlying macOS telemetry may refresh much less often. Right after unplugging, a stale positive battery charge is shown as `갱신 대기` (awaiting refresh), and adapter input is shown as `0.0 W` while disconnected. After 3 consecutive read failures the card shows `측정 불가` (unavailable) and recovers automatically once telemetry returns.

This is not a separate GUI app — it's a background tool that produces local JSON data for RunCat.

## Status / troubleshooting

From the extracted folder:

```bash
bash status.sh
```

Or check directly:

```bash
python3 -m json.tool ~/.config/runcat-neo-metrics/macbook-power.json
python3 ~/.local/share/runcat-macwatt/power_metrics.py --check
launchctl print "gui/$(id -u)/dev.runcat.macwatt"
```

Log files:

```text
~/.local/share/runcat-macwatt/last-error.txt
~/.local/share/runcat-macwatt/service-error.log
```

- `측정 불가` / "telemetry unavailable" during install: check that your Mac exposes `PowerTelemetryData`. Other sensors are never substituted as estimates.
- `python3 not found`: install Python 3.8+ and run again.
- Card not showing in RunCat: check the file path and that it's registered under Custom Metrics.
- Stopped updating after changing macOS or Homebrew Python: rerun `bash install.sh` to refresh the Python path in the launch agent.

## Uninstall

Remove the Custom Metrics source in RunCat settings, then:

```bash
bash uninstall.sh
```

This removes only the installed code, the background agent and its JSON file. Other RunCat metrics are unaffected.

## Development and testing

```bash
bash scripts/test.sh
```

Runs unit tests that work without macOS sensors, Bash syntax checks, and a release ZIP integrity check. The install ZIP is written to `dist/runcat-macwatt-v<VERSION>.zip` and the SHA-256 checksum to `dist/SHA256SUMS.txt`. See [CONTRIBUTING.md](CONTRIBUTING.md) and [PUBLISH_WITH_CLAUDE.md](PUBLISH_WITH_CLAUDE.md).

## Credits and license

- This RunCat integration and its install scripts: [MIT License](LICENSE) · Copyright (c) 2026 yes2310
- **macwatt**: Copyright (c) 2026 Amur Labs LLC, MIT License — keep its [original license](third_party/macwatt/LICENSE) and [notices](THIRD_PARTY_NOTICES.md).
- **RunCat Neo**: a separate project; the app is not redistributed here. [Custom Metrics JSON Schema](https://github.com/runcat-dev/RunCatNeo/blob/main/docs/CustomMetricsSchema.md)

*Unofficial integration. Not affiliated with or endorsed by RunCat Neo or macwatt.*
