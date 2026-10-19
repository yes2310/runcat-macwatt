#!/usr/bin/env python3
"""Build an offline, no-dependencies installation ZIP for GitHub Releases."""
from pathlib import Path
import hashlib
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if not VERSION or any(c not in "0123456789." for c in VERSION):
    raise SystemExit("Invalid VERSION file")

FILES = (
    "install.sh", "uninstall.sh", "status.sh", "power_metrics.py",
    "README.md", "README_EN.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "CHANGELOG.md", "VERSION",
    "third_party/macwatt/macwatt.py", "third_party/macwatt/LICENSE", "third_party/macwatt/SOURCE.md",
)
OUTPUT = ROOT / "dist" / ("runcat-macwatt-v" + VERSION + ".zip")
OUTPUT.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for name in FILES:
        file = ROOT / name
        if not file.is_file():
            raise SystemExit("Missing required file: " + name)
        info = zipfile.ZipInfo("runcat-macwatt/" + name, date_time=(2026, 10, 19, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.create_system = 3
        perms = 0o755 if name.endswith(".sh") or name == "power_metrics.py" else 0o644
        info.external_attr = (stat.S_IFREG | perms) << 16
        archive.writestr(info, file.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
(OUTPUT.parent / "SHA256SUMS.txt").write_text(
    f"{digest}  {OUTPUT.name}\n", encoding="utf-8"
)
print(OUTPUT)
print("SHA256:", digest)
