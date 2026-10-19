# RunCat Neo × macwatt

**English** | [한국어](README.ko.md)

Adds a **Power** card to the [RunCat Neo](https://github.com/runcat-dev/RunCatNeo) dashboard showing your MacBook's live charging and power draw. The menu bar stays cat-only.

```text
⚡ 전력 (Power)
   입력 전력 (Input)      86.1 W
   배터리   (Battery)     충전 67.5 W      ← charging / 방전 = discharging
   시스템 소비 (System)    18.6 W
   충전기   (Charger)     140 W · 28 V / 5 A
```

> Card labels are in Korean for now. Numbers above are an example.

---

## Before you start

- An **Apple Silicon MacBook** (M1 or later)
- **RunCat Neo** installed
- **Python 3.8+** — check with `python3 --version` in Terminal

---

## Setup

### Step 1 — Install

Open **Terminal** and paste the whole block:

```bash
cd ~/Downloads
curl -LO https://github.com/yes2310/runcat-macwatt/releases/download/v1.0.0/runcat-macwatt-v1.0.0.zip
unzip -o runcat-macwatt-v1.0.0.zip
cd runcat-macwatt
bash install.sh
```

When you see **`Installed!`**, it's done. It now runs in the background and starts automatically at login.

<details>
<summary>Prefer to download by hand?</summary>

1. Download `runcat-macwatt-v1.0.0.zip` from the [Releases page](https://github.com/yes2310/runcat-macwatt/releases/latest).
2. Double-click it to extract (Safari may do this for you).
3. In Terminal:
   ```bash
   cd ~/Downloads/runcat-macwatt
   bash install.sh
   ```

</details>

### Step 2 — Add it to RunCat Neo

1. Click the **cat in the menu bar** to open the dashboard, then open **Settings**.
2. Go to **Metrics → Custom Metrics** and click **Add Custom Metrics Source**.
3. In the file picker, press **`Command + Shift + G`**, paste the path below, press **Return**, then click **Open**.

```text
~/.config/runcat-neo-metrics/macbook-power.json
```

### Step 3 — Check

Click the cat in the menu bar. A **⚡ 전력** card should appear on the dashboard and update by itself.

> **Keep the menu bar cat-only:** new sources are hidden from RunCat's *Metrics Bar* by default. Leave this source's toggle off there.

---

## Update

Download the new release and run `bash install.sh` again. The file path doesn't change, so there's nothing to redo in RunCat.

## Uninstall

1. RunCat Neo → **Settings → Metrics → Custom Metrics**: remove the `macbook-power.json` source.
2. In the extracted folder, run:
   ```bash
   bash uninstall.sh
   ```

---

## Troubleshooting

First, run this in the extracted folder to see the current state:

```bash
bash status.sh
```

| Problem | Fix |
| --- | --- |
| Install stops with *power telemetry is not available* | This Mac doesn't expose the power sensors this tool needs. It won't guess values. |
| `python3` not found / version too old | Install Python 3.8 or later, then run `bash install.sh` again. |
| Card doesn't appear | Make sure Step 2 is done and the path is exactly the one above. |
| Card shows `측정 불가` (unavailable) | Sensor reads failed 3 times in a row. It recovers on its own; if not, check `bash status.sh`. |
| Battery shows `갱신 대기` (waiting) | Normal right after unplugging — macOS takes a moment to refresh. |
| Stopped updating after a macOS or Homebrew Python update | Run `bash install.sh` again. |

Log files live in `~/.local/share/runcat-macwatt/` (`last-error.txt`, `service-error.log`).

---

## How it works

<details>
<summary>Details</summary>

- A small background service (`launchd`, label `dev.runcat.macwatt`) reads the Mac's power sensors through [macwatt](https://github.com/ytomasch/macwatt) **every 5 seconds**.
- It rewrites the JSON file **only when a displayed value changes**, and RunCat Neo refreshes the card when the file changes.
- macOS itself may refresh its power sensors less often than every 5 seconds.
- **Charger** is the power contract the Mac negotiated with the adapter — not the brand/model, and not a wall-meter reading.
- No `sudo`, no internet, no extra dependencies. Everything is bundled in the ZIP.

Installed files:

| What | Where |
| --- | --- |
| Program | `~/.local/share/runcat-macwatt/` |
| Card data (JSON) | `~/.config/runcat-neo-metrics/macbook-power.json` |
| Login service | `~/Library/LaunchAgents/dev.runcat.macwatt.plist` |

</details>

## Development

```bash
bash scripts/test.sh
```

Runs offline unit tests and builds the release ZIP into `dist/`. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

- This project: [MIT](LICENSE) © 2026 yes2310
- Bundled **macwatt**: MIT © 2026 Amur Labs LLC — see [license](third_party/macwatt/LICENSE) and [notices](THIRD_PARTY_NOTICES.md)
- RunCat Neo is a separate app and is not included.

*Unofficial. Not affiliated with RunCat Neo or macwatt.*
