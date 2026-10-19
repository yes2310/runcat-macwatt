#!/usr/bin/env python3
"""macwatt — read real charger/power telemetry off an Apple Silicon Mac.

Apple's SMC exposes instrumented power numbers via IOKit that `powermetrics`
does not report (and that `powermetrics` gets wrong on M4 — CPU Power reads
0 mW). The dictionary is AppleSmartBattery -> PowerTelemetryData, and the
budget closes exactly:

    SystemPowerIn = BatteryPower + SystemLoad

No sudo required. Read-only.
Usage:
    macwatt                 one snapshot of this machine
    macwatt -w              watch (refresh every 15s; SMC cadence is ~15-20s)
    macwatt -w -i 30        watch at a custom interval
    macwatt -n 5            take 5 samples and stop
    macwatt -j              JSON out (one object per sample, newline delimited)
    macwatt --host user@ip  read a different Mac over SSH

Set MACWATT_HOST to make an SSH target the default, e.g. for running this
from a machine that is not itself a Mac.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

IOREG_ARGV = ["ioreg", "-rn", "AppleSmartBattery", "-w0"]


def fetch(host=None, timeout=15):
    """Pull the raw AppleSmartBattery property blob, locally or over SSH."""
    if host:
        argv = ["ssh", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", host,
                " ".join(IOREG_ARGV)]
        where = host
    else:
        argv = IOREG_ARGV
        where = "this machine"
    try:
        out = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise SystemExit(f"macwatt: timed out reading {where}")
    except FileNotFoundError:
        # No ioreg means we are not on a Mac and no --host was given.
        raise SystemExit("macwatt: ioreg not found — run this on a Mac, "
                         "or pass --host user@mac (or set MACWATT_HOST)")
    if out.returncode != 0:
        verb = "ssh to" if host else "reading"
        raise SystemExit(f"macwatt: {verb} {where} failed: {out.stderr.strip()}")
    if "AppleSmartBattery" not in out.stdout:
        raise SystemExit("macwatt: no AppleSmartBattery node — is this an Apple laptop?")
    return out.stdout


def subdict(blob, name):
    """Extract a nested ioreg dict by name, brace-balanced."""
    m = re.search(r'"%s"\s*=\s*\{' % re.escape(name), blob)
    if not m:
        return ""
    i, depth = m.end() - 1, 0
    for j in range(i, len(blob)):
        if blob[j] == "{":
            depth += 1
        elif blob[j] == "}":
            depth -= 1
            if depth == 0:
                return blob[i:j + 1]
    return ""


def num(scope, key):
    """Read an integer field. Tolerates both `"k"=1` and `"k" = 1` spellings.

    ioreg prints these as unsigned 64-bit, so a negative value (BatteryPower
    while discharging) arrives as a near-2^64 number. Fold it back to signed.
    """
    m = re.search(r'"%s"\s*=\s*(-?\d+)' % re.escape(key), scope)
    if not m:
        return None
    v = int(m.group(1))
    return v - (1 << 64) if v >= (1 << 63) else v


def flag(scope, key):
    m = re.search(r'"%s"\s*=\s*(Yes|No)' % re.escape(key), scope)
    return None if not m else m.group(1) == "Yes"


def sample(blob):
    tel = subdict(blob, "PowerTelemetryData")
    pd = subdict(blob, "PowerDistribution")
    ad = subdict(blob, "AdapterDetails")
    d = {
        # what the adapter advertises it can supply
        "adapter_watts": num(ad, "Watts"),
        "adapter_voltage_mv": num(ad, "AdapterVoltage"),
        "adapter_current_ma": num(ad, "Current"),
        # the ceiling the PMU actually configures itself to draw
        "input_limit_mw": num(pd, "IPDInputPower"),
        "input_limit_ma": num(pd, "IPDInputCurrent"),
        # what is genuinely flowing right now
        "input_mw": num(tel, "SystemPowerIn"),
        "input_mv": num(tel, "SystemVoltageIn"),
        "input_ma": num(tel, "SystemCurrentIn"),
        "battery_mw": num(tel, "BatteryPower"),
        "system_mw": num(tel, "SystemLoad"),
        "adapter_loss_mw": num(tel, "AdapterEfficiencyLoss"),
        # state
        "charge_pct": num(blob, "CurrentCapacity"),
        "charging": flag(blob, "IsCharging"),
        "on_ac": flag(blob, "ExternalConnected"),
    }
    if d["input_mw"] is None:
        raise SystemExit("macwatt: PowerTelemetryData missing — unsupported Mac?")
    return d


def w(mw):
    return "  --  " if mw is None else f"{mw / 1000:6.1f} W"


def render(d):
    lines = []
    state = "charging" if d["charging"] else ("on AC" if d["on_ac"] else "on battery")
    pct = "--" if d["charge_pct"] is None else f"{d['charge_pct']}%"
    lines.append(f"  battery {pct}, {state}")
    lines.append("")
    if d["adapter_watts"]:
        v = (d["adapter_voltage_mv"] or 0) / 1000
        a = (d["adapter_current_ma"] or 0) / 1000
        lines.append(f"  adapter offers     {d['adapter_watts']:6.1f} W   ({v:.0f} V @ {a:.2f} A contract)")
    if d["input_limit_mw"]:
        pctc = 100 * d["input_limit_mw"] / (d["adapter_watts"] * 1000) if d["adapter_watts"] else 0
        lines.append(f"  PMU input ceiling  {w(d['input_limit_mw'])}   ({d['input_limit_ma']} mA cap"
                     + (f", {pctc:.0f}% of adapter)" if d["adapter_watts"] else ")"))
    lines.append("  " + "-" * 52)
    hdr = f"  drawing now        {w(d['input_mw'])}"
    if d["input_mv"] and d["input_ma"]:
        hdr += f"   ({d['input_mv'] / 1000:.2f} V @ {d['input_ma'] / 1000:.2f} A)"
    if d["input_limit_mw"]:
        hdr += f"  = {100 * d['input_mw'] / d['input_limit_mw']:.0f}% of ceiling"
    lines.append(hdr)
    bat = d["battery_mw"]
    if bat is not None and bat < 0:
        # discharging: the cell is a source, not a sink
        lines.append(f"       from battery  {w(-bat)}  (discharging)")
    else:
        lines.append(f"       into battery  {w(bat)}")
    lines.append(f"       into system   {w(d['system_mw'])}")
    # sanity: the SMC's own budget should close to the milliwatt
    if d["battery_mw"] is not None and d["system_mw"] is not None:
        resid = d["input_mw"] - d["battery_mw"] - d["system_mw"]
        mark = "ok" if abs(resid) <= 50 else f"MISMATCH {resid} mW"
        lines.append(f"       (budget check: {mark})")
    if d["adapter_loss_mw"]:
        wall = d["input_mw"] + d["adapter_loss_mw"]
        lines.append("")
        lines.append(f"  brick loss         {w(d['adapter_loss_mw'])}   -> ~{wall / 1000:.1f} W at the wall")
    # Voltage shortfall vs the negotiated contract, and the resistance it would
    # imply if the whole drop were resistive (cable + connectors).
    #
    # Compare this figure across two DIFFERENT currents to tell cause apart:
    # a real series resistance stays put, so the implied ohms hold steady. If
    # the implied ohms move a lot between operating points, the drop is not
    # resistive -- the brick is regulating below its contract voltage.
    if d["adapter_voltage_mv"] and d["input_mv"] and d["input_ma"]:
        drop_mv = d["adapter_voltage_mv"] - d["input_mv"]
        lines.append("")
        lines.append(f"  volt at the Mac    {d['input_mv'] / 1000:6.2f} V   "
                     f"({d['adapter_voltage_mv'] / 1000:.0f} V contract, "
                     f"{'-' if drop_mv > 0 else '+'}{abs(drop_mv) / 1000:.2f} V)")
        if drop_mv > 0:
            ohms = drop_mv / d["input_ma"]
            heat = (d["input_ma"] / 1000) ** 2 * ohms
            lines.append(f"  implied path R     {ohms:6.3f} ohm  = {heat:.1f} W of heat if it is really cable")
        else:
            # Measuring at or above the contract voltage means there is no
            # resistive drop to explain -- the source is holding the rail up.
            lines.append("  implied path R      none   at or above contract; source is holding the rail")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(prog="macwatt", add_help=True)
    p.add_argument("--host", default=os.environ.get("MACWATT_HOST"),
                   help="ssh target to read instead of this machine "
                        "(default: $MACWATT_HOST, else local)")
    p.add_argument("-w", "--watch", action="store_true", help="loop until interrupted")
    p.add_argument("-i", "--interval", type=int, default=15, help="seconds between samples (default 15)")
    p.add_argument("-n", "--samples", type=int, default=0, help="stop after N samples")
    p.add_argument("-j", "--json", action="store_true", help="newline-delimited JSON")
    a = p.parse_args()
    count, first = 0, True
    while True:
        d = sample(fetch(a.host))
        count += 1
        if a.json:
            d["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            print(json.dumps(d), flush=True)
        else:
            if not first:
                print()
            print(render(d), flush=True)
        first = False
        if a.samples and count >= a.samples:
            break
        if not a.watch and not a.samples:
            break
        try:
            time.sleep(a.interval)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
