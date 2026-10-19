"""Unit tests run on any OS; no ioreg, RunCat, or sudo needed."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "third_party/macwatt"))
sys.path.insert(0, str(ROOT))

import macwatt  # noqa: E402
import power_metrics as pm  # noqa: E402


CHARGING = {
    "on_ac": True,
    "charging": True,
    "input_mw": 86100,
    "battery_mw": 67500,
    "system_mw": 18600,
    "adapter_watts": 140,
    "adapter_voltage_mv": 28000,
    "adapter_current_ma": 5000,
}


class PowerCardTests(unittest.TestCase):
    def test_connected_reading_has_four_rows_and_no_metrics_bar(self):
        result = pm.build_snapshot(CHARGING)
        self.assertEqual(result["title"], "전력")
        self.assertEqual(result["symbol"], "bolt.fill")
        self.assertNotIn("metricsBarValue", result)
        self.assertEqual(result["metrics"], [
            {"title": "입력 전력", "formattedValue": "86.1 W"},
            {"title": "배터리", "formattedValue": "충전 67.5 W"},
            {"title": "시스템 소비", "formattedValue": "18.6 W"},
            {"title": "충전기", "formattedValue": "140 W · 28 V / 5 A"},
        ])
        self.assertTrue(result["lastUpdatedDate"].endswith("Z"))

    def test_battery_discharging(self):
        data = dict(CHARGING, on_ac=False, charging=False, battery_mw=-18600,
                    system_mw=18600, input_mw=20000)
        rows = pm.metric_rows(data)
        self.assertEqual(rows[0]["formattedValue"], "0.0 W")
        self.assertEqual(rows[1]["formattedValue"], "방전 18.6 W")
        self.assertEqual(rows[3]["formattedValue"], "미연결")

    def test_stale_battery_power_after_unplug(self):
        data = dict(CHARGING, on_ac=False)
        self.assertEqual(pm.battery_flow(data), "갱신 대기")

    def test_charging_threshold_and_maintaining(self):
        self.assertEqual(pm.battery_flow(dict(CHARGING, battery_mw=100)), "유지 0.0 W")
        self.assertEqual(pm.battery_flow(dict(CHARGING, battery_mw=0)), "유지 0.0 W")
        self.assertEqual(pm.battery_flow(dict(CHARGING, battery_mw=-100)), "유지 0.0 W")
        self.assertEqual(pm.battery_flow(dict(CHARGING, battery_mw=-101)), "방전 0.1 W")

    def test_missing_or_partial_adapter(self):
        data = dict(CHARGING, adapter_watts=None, adapter_voltage_mv=None,
                    adapter_current_ma=None)
        self.assertEqual(pm.charger_spec(data), "정보 없음")
        self.assertEqual(pm.charger_spec(dict(data, adapter_watts=96)), "96 W")
        self.assertEqual(pm.charger_spec(dict(data, adapter_current_ma=3050)), "3.05 A")
        self.assertEqual(pm.charger_spec(dict(data, adapter_voltage_mv=20300)), "20.3 V")

    def test_missing_sensor_readings_do_not_fake_zeros(self):
        data = dict(CHARGING, input_mw=None, battery_mw=None, system_mw=None)
        rows = pm.metric_rows(data)
        self.assertEqual([x["formattedValue"] for x in rows[:3]], ["—", "—", "—"])

    def test_finite_number_checks(self):
        for invalid in (None, "20000", True, float("inf"), float("nan")):
            self.assertEqual(pm.format_watts(invalid), "—")
        self.assertEqual(pm.format_watts(0), "0.0 W")

    def test_failure_has_four_rows_and_no_false_readings(self):
        result = pm.build_snapshot(None)
        self.assertEqual(len(result["metrics"]), 4)
        self.assertTrue(all(row["formattedValue"] == "측정 불가"
                            for row in result["metrics"]))

    def test_atomic_write_only_when_visible_values_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "nested" / "output.json"
            original = pm.build_snapshot(CHARGING)
            self.assertTrue(pm.atomic_write_if_changed(original, output))
            before = output.stat().st_mtime_ns
            self.assertEqual(json.loads(output.read_text()), original)
            newest_time = dict(original, lastUpdatedDate="2099-01-01T00:00:00Z")
            self.assertFalse(pm.atomic_write_if_changed(newest_time, output))
            self.assertEqual(output.stat().st_mtime_ns, before)
            second = pm.build_snapshot(dict(CHARGING, system_mw=19000))
            self.assertTrue(pm.atomic_write_if_changed(second, output))
            self.assertEqual(json.loads(output.read_text())["metrics"][2]["formattedValue"],
                             "19.0 W")
            self.assertEqual(list(output.parent.glob("*.tmp")), [])

    def test_invalid_json_is_repaired(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "metrics.json"
            output.write_text("{broken", encoding="utf-8")
            self.assertTrue(pm.atomic_write_if_changed(pm.build_snapshot(CHARGING), output))
            self.assertEqual(json.loads(output.read_text())["title"], "전력")

    def test_update_once_clears_stale_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "metrics.json"
            error = Path(tmp) / "last-error.txt"
            error.write_text("old error\n")
            with mock.patch.object(pm, "read_power", return_value=CHARGING), \
                 mock.patch.object(pm, "ERROR_LOG", error):
                pm.update_once(output)
            self.assertFalse(error.exists())
            self.assertTrue(output.is_file())

    def test_read_power_uses_local_macwatt(self):
        with mock.patch.object(pm.macwatt, "fetch", return_value="data") as fetch, \
             mock.patch.object(pm.macwatt, "sample", return_value=CHARGING) as sample:
            self.assertEqual(pm.read_power(), CHARGING)
            fetch.assert_called_once_with(host=None, timeout=10)
            sample.assert_called_once_with("data")

    def test_failed_reads_show_error_after_three_consecutive_attempts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "metrics.json"
            stop = mock.Mock()
            stop.is_set.side_effect = [False, False, False, True]
            with mock.patch.object(pm, "_STOP", stop), \
                 mock.patch.object(pm, "update_once", side_effect=OSError("ioreg failed")), \
                 mock.patch.object(pm, "log_error"):
                pm.monitor(0.5, path)
            self.assertEqual(json.loads(path.read_text())["metrics"][0]["formattedValue"],
                             "측정 불가")
            self.assertEqual(stop.wait.call_count, 3)

    def test_poll_recovers_after_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "metrics.json"
            stop = mock.Mock()
            stop.is_set.side_effect = [False, False, False, False, True]
            with mock.patch.object(pm, "_STOP", stop), \
                 mock.patch.object(pm, "update_once", side_effect=[
                     OSError("lost"), OSError("lost"), OSError("lost"),
                     lambda: None,
                 ]) as update, \
                 mock.patch.object(pm, "log_error"):
                # The fourth call succeeds: a side-effect sentinel return is
                # enough for monitor() to reset its local failure counter.
                pm.monitor(0.2, path)
            self.assertEqual(update.call_count, 4)
            self.assertEqual(json.loads(path.read_text())["metrics"][0]["formattedValue"],
                             "측정 불가")  # mocked success did not write new data


class VendoredMacwattTests(unittest.TestCase):
    def test_parse_realistic_charging_ioreg_text(self):
        data = '''+-- AppleSmartBattery <class AppleSmartBattery>
        | |   "PowerTelemetryData" = {"SystemPowerIn"=86100,"BatteryPower"=67500,"SystemLoad"=18600,"SystemVoltageIn"=28000}
        | |   "PowerDistribution" = {"IPDInputPower"=140000,"IPDInputCurrent"=5000}
        | |   "AdapterDetails" = {"Watts"=140,"AdapterVoltage"=28000,"Current"=5000}
        | |   "CurrentCapacity" = 65
        | |   "ExternalConnected" = Yes
        | |   "IsCharging" = Yes
        '''
        result = macwatt.sample(data)
        self.assertEqual(result["input_mw"], 86100)
        self.assertEqual(result["battery_mw"], 67500)
        self.assertEqual(result["system_mw"], 18600)
        self.assertEqual(result["adapter_watts"], 140)
        self.assertEqual(result["on_ac"], True)
        self.assertEqual(result["input_mw"], result["battery_mw"] + result["system_mw"])

    def test_unsigned_negative_battery_current_becomes_signed(self):
        text = '''+-- AppleSmartBattery
            "PowerTelemetryData" = {"SystemPowerIn"=0,"BatteryPower"=18446744073709531616,"SystemLoad"=20000}
            "ExternalConnected" = No
        '''
        reading = macwatt.sample(text)
        self.assertEqual(reading["battery_mw"], -20000)
        self.assertEqual(pm.battery_flow(reading), "방전 20.0 W")

    def test_missing_power_telemetry_fails_clearly(self):
        with self.assertRaises(SystemExit):
            macwatt.sample('+-- AppleSmartBattery "ExternalConnected"=No')


if __name__ == "__main__":
    unittest.main()
