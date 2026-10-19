# RunCat Neo × macwatt

**Power metrics for your Apple Silicon MacBook, inside RunCat Neo — without adding a wattage label to the menu bar.** [한국어 설명](README.md).

This independent integration reads the MacBook's actual power telemetry using [macwatt](https://github.com/ytomasch/macwatt) and maintains a local [RunCat Neo Custom Metrics](https://github.com/runcat-dev/RunCatNeo/blob/main/docs/CustomMetricsSchema.md) JSON file.

## What the card displays

| Metric | Example | Meaning |
| --- | --- | --- |
| `입력 전력` (input) | `86.1 W` | Measured power entering the Mac from the adapter |
| `배터리` (battery) | `충전 67.5 W` or `방전 18.6 W` | Battery charge/discharge power |
| `시스템 소비` (system) | `18.6 W` | System power consumption |
| `충전기` (adapter) | `140 W · 28 V / 5 A` | Advertised, negotiated charger contract |

The card title and row labels are currently Korean. Values above are illustrative. Adapter information is **not** the charger make/model or wall-meter reading. Some fields may be absent or stale on different Mac models or macOS versions.

## Requirements

- Apple Silicon MacBook providing `AppleSmartBattery` / `PowerTelemetryData` (checked during install)
- RunCat Neo with Custom Metrics support
- Python 3.8+ (standard library only)
- macOS user session; no `sudo`, `pip`, account tokens, or background network access

The GitHub Release ZIP already includes the unmodified MIT-licensed `macwatt.py` and its license. Installation works offline.

## Install

Download `runcat-macwatt-v1.0.0.zip` from GitHub Releases, extract it, then run:

```bash
cd ~/Downloads/runcat-macwatt
bash install.sh
```

In RunCat Neo choose **Settings → Metrics → Custom Metrics → Add Custom Metrics Source** and select:

```text
~/.config/runcat-neo-metrics/macbook-power.json
```

In the file picker press `Command + Shift + G` to enter the hidden path. Keep **Metrics Bar disabled**, or hide this source within it, to show only the cat in your menu bar.

### Upgrade from v2/v3

Run the same `bash install.sh`. The installer preflights live sensor access and replaces the existing `dev.runcat.macwatt` agent while retaining the same JSON path. There is no need to register another RunCat source. The installer attempts to restore the previous install if upgrading fails.

## Behavior

- One resident Python process starts at login through `launchd` and checks every **5 seconds**.
- The JSON file is atomically replaced **only if displayed values change**; RunCat detects file changes.
- The underlying Mac telemetry can refresh much less frequently than every 5 seconds. Polling does not force fresh sensor readings.
- When disconnected, adapter input is shown as `0.0 W` even if a previous input sample remains cached. A stale positive battery charge after unplugging is shown as `갱신 대기` (awaiting refresh).
- After 3 consecutive read errors the card shows `측정 불가` (unavailable); it recovers automatically when telemetry returns.

## Diagnose / remove

```bash
bash status.sh
python3 ~/.local/share/runcat-macwatt/power_metrics.py --check
launchctl print "gui/$(id -u)/dev.runcat.macwatt"
```

After removing the RunCat Custom Metrics source, run `bash uninstall.sh` to remove the background agent, integration code, and its JSON file.

If Homebrew replaces your Python interpreter, rerun `bash install.sh` to update the interpreter path in the launch agent.

## Build and publish

`bash scripts/test.sh` runs offline unit tests, shell checks, and produces the ZIP asset and `SHA256SUMS.txt` in `dist/`. See [PUBLISH_WITH_CLAUDE.md](PUBLISH_WITH_CLAUDE.md) for `gh`/Claude Code publishing steps.

## Credits and license

- This integration is released under [MIT](LICENSE), copyright (c) 2026 yes2310.
- `macwatt` by Amur Labs LLC is separately MIT-licensed; [upstream](https://github.com/ytomasch/macwatt), [license](third_party/macwatt/LICENSE), and [notices](THIRD_PARTY_NOTICES.md).
- RunCat Neo is not bundled. This project is unofficial and unaffiliated with either upstream project.
