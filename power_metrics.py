#!/usr/bin/env python3
"""macwatt -> RunCat Neo Custom Metrics (unofficial integration).

Read local macOS IORegistry telemetry every five seconds using the bundled
MIT-licensed macwatt parser, updating the RunCat JSON only when visible values
change. This process needs no admin privileges, pip dependencies, or network.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import signal
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import macwatt  # Vendored MIT-licensed upstream module; see THIRD_PARTY_NOTICES.md.

DEFAULT_OUTPUT = Path.home() / ".config/runcat-neo-metrics/macbook-power.json"
ERROR_LOG = Path(__file__).resolve().parent / "last-error.txt"
DEFAULT_INTERVAL = 5.0
_STOP = threading.Event()


def is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def format_watts(mw: Any) -> str:
    return f"{mw / 1000:.1f} W" if is_number(mw) else "—"


def format_quantity(milliunits: Any, unit: str) -> str | None:
    if not is_number(milliunits) or milliunits <= 0:
        return None
    value = milliunits / 1000
    precision = f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{precision} {unit}"


def charger_spec(reading: dict[str, Any]) -> str:
    """Show the negotiated adapter offer, NOT a charger make/model or wall draw."""
    if reading.get("on_ac") is False:
        return "미연결"

    watts = reading.get("adapter_watts")
    offered = f"{watts:g} W" if is_number(watts) and watts > 0 else None
    voltage = format_quantity(reading.get("adapter_voltage_mv"), "V")
    current = format_quantity(reading.get("adapter_current_ma"), "A")
    contract = " / ".join(x for x in (voltage, current) if x)
    if offered and contract:
        return f"{offered} · {contract}"
    return offered or contract or "정보 없음"


def battery_flow(reading: dict[str, Any]) -> str:
    mw = reading.get("battery_mw")
    if not is_number(mw):
        return "—"
    if reading.get("on_ac") is False and mw >= -100:
        # PowerTelemetryData may lag behind unplugging by tens of seconds.
        # Do not show stale positive charging power on a disconnected Mac.
        return "갱신 대기"
    if mw > 100:
        return f"충전 {format_watts(mw)}"
    if mw < -100:
        return f"방전 {format_watts(-mw)}"
    return "유지 0.0 W"


def metric_rows(reading: dict[str, Any]) -> list[dict[str, str]]:
    if reading.get("on_ac") is False:
        # An unplugged Mac can't draw *from the adapter* even if cached SMC
        # telemetry takes time to refresh.
        input_power = "0.0 W"
    else:
        input_power = format_watts(reading.get("input_mw"))
    return [
        {"title": "입력 전력", "formattedValue": input_power},
        {"title": "배터리", "formattedValue": battery_flow(reading)},
        {"title": "시스템 소비", "formattedValue": format_watts(reading.get("system_mw"))},
        {"title": "충전기", "formattedValue": charger_spec(reading)},
    ]


def build_snapshot(reading: dict[str, Any] | None = None) -> dict[str, Any]:
    if reading is None:
        rows = [
            {"title": title, "formattedValue": "측정 불가"}
            for title in ("입력 전력", "배터리", "시스템 소비", "충전기")
        ]
    else:
        rows = metric_rows(reading)
    return {
        "title": "전력",
        "symbol": "bolt.fill",
        # Do NOT set metricsBarValue: keep the RunCat menu bar cat-only.
        # The source must also remain disabled in RunCat's Metrics Bar UI.
        "metrics": rows,
        "lastUpdatedDate": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def display_data(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Return only fields affecting the card display (not the timestamp)."""
    return {k: v for k, v in snapshot.items() if k != "lastUpdatedDate"}


def atomic_write_if_changed(payload: dict[str, Any], path: Path = DEFAULT_OUTPUT) -> bool:
    """Atomically write a new JSON file only when visible values change."""
    try:
        previous = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(previous, dict) and display_data(previous) == display_data(payload):
            return False
    except (FileNotFoundError, OSError, ValueError):
        pass

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", dir=path.parent, prefix=".macbook-power-", suffix=".tmp",
            encoding="utf-8", delete=False
        ) as handle:
            tmp = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
        os.replace(tmp, path)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
    return True


def read_power() -> dict[str, Any]:
    # Set an absolute path for launchd (which uses a restricted PATH).
    if Path("/usr/sbin/ioreg").is_file():
        macwatt.IOREG_ARGV[0] = "/usr/sbin/ioreg"
    # Passing no host forces local, read-only IORegistry access.
    return macwatt.sample(macwatt.fetch(host=None, timeout=10))


def log_error(exc: BaseException) -> None:
    message = f"{type(exc).__name__}: {exc}\n"
    try:
        if not ERROR_LOG.exists() or ERROR_LOG.read_text(encoding="utf-8") != message:
            ERROR_LOG.write_text(message, encoding="utf-8")
    except OSError:
        pass


def update_once(path: Path = DEFAULT_OUTPUT) -> bool:
    changed = atomic_write_if_changed(build_snapshot(read_power()), path)
    ERROR_LOG.unlink(missing_ok=True)
    return changed


def monitor(interval: float = DEFAULT_INTERVAL, path: Path = DEFAULT_OUTPUT) -> None:
    """Single resident process: no overlapping reads, bounded error behavior."""
    failures = 0
    while not _STOP.is_set():
        started = time.monotonic()
        try:
            update_once(path)
            failures = 0
        except (Exception, SystemExit) as exc:
            failures += 1
            log_error(exc)
            if failures >= 3:
                try:
                    atomic_write_if_changed(build_snapshot(None), path)
                except OSError:
                    pass
        # Use Event.wait so SIGTERM can stop the loop promptly.
        _STOP.wait(max(0.0, interval - (time.monotonic() - started)))


def main() -> int:
    parser = argparse.ArgumentParser(description="RunCat Neo x macwatt power metrics")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="Sample and update the JSON once")
    mode.add_argument("--check", action="store_true", help="Print raw macwatt readings without writing JSON")
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL,
                        help="Sensor polling interval in seconds (default 5)")
    args = parser.parse_args()
    if not 0.2 <= args.interval <= 3600 or not math.isfinite(args.interval):
        parser.error("--interval must be a finite number between 0.2 and 3600")

    if args.once or args.check:
        try:
            if args.check:
                print(json.dumps(read_power(), indent=2, ensure_ascii=False))
            else:
                update_once()
                print(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
            return 0
        except (Exception, SystemExit) as exc:
            log_error(exc)
            print(f"Power telemetry unavailable: {exc}", file=sys.stderr)
            return 1

    signal.signal(signal.SIGTERM, lambda *_: _STOP.set())
    signal.signal(signal.SIGINT, lambda *_: _STOP.set())
    monitor(args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
