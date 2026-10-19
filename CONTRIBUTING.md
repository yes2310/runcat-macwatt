# Contributing

Issues and pull requests are welcome, especially compatibility reports from
different Apple Silicon MacBook models. Please avoid sharing serial numbers,
full device dumps or other personal identifiers in bug reports.

To test:

```bash
python3 -m unittest discover -s tests -v
bash -n install.sh uninstall.sh status.sh
```

When proposing changes to `third_party/macwatt/macwatt.py`, identify the
original upstream commit/source and retain the MIT license. Keep RunCat's JSON
schema, the fixed source path and v2/v3 upgrade behavior backward-compatible.

Test changes against an actual MacBook when possible, including unplug/plug,
sleep/wake, login, changing power adapters and unsupported sensors.
