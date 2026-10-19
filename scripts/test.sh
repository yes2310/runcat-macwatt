#!/bin/bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 -B -m unittest discover -s tests -v
bash -n install.sh uninstall.sh status.sh scripts/test.sh
if [[ "$(uname -s)" == "Linux" ]]; then
  bash tests/test_mock_install.sh
fi
python3 -B scripts/make_release.py
python3 - "$ROOT/dist/runcat-macwatt-v$(cat VERSION).zip" <<'PY'
import sys,zipfile
with zipfile.ZipFile(sys.argv[1]) as archive:
    bad = archive.testzip()
    if bad:
        raise SystemExit("ZIP CRC error: " + bad)
    assert "runcat-macwatt/third_party/macwatt/LICENSE" in archive.namelist()
print("ZIP integrity verified")
PY
python3 - "$ROOT/dist/SHA256SUMS.txt" "$ROOT/dist/runcat-macwatt-v$(cat VERSION).zip" <<'VERIFY'
from pathlib import Path
import hashlib,sys
sha_file, zip_file = map(Path, sys.argv[1:])
expected, name = sha_file.read_text().strip().split('  ', 1)
actual = hashlib.sha256(zip_file.read_bytes()).hexdigest()
assert name == zip_file.name and actual == expected
print('SHA256 verified')
VERIFY
