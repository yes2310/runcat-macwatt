# Claude Code maintainer instructions

Project: **RunCat Neo × macwatt** — unofficial Apple Silicon MacBook power telemetry bridge for RunCat Neo's Custom Metrics JSON schema.

## User-requested goal

Publish the provided repository to GitHub using `gh` on the maintainer's Mac with a `v1.0.0` release ZIP. The user has authorized public publication, but do not clobber an existing repository, tag or release. If the requested repository name exists, ask for another name.

## Before publishing

1. Inspect README.md, README_EN.md, LICENSE, THIRD_PARTY_NOTICES.md, the bundled `third_party/macwatt/LICENSE`, and the installer source. Do not drop upstream copyright/permission notice.
2. Run `bash scripts/test.sh`; stop publication if it fails. The test builds `dist/runcat-macwatt-v1.0.0.zip`.
3. Check `gh auth status`, confirm correct owner, and inspect whether `runcat-macwatt` already exists. Check `git status` and `git remote -v` before changing anything.
4. Prefer running a real Mac preflight `python3 power_metrics.py --check` with `PYTHONPATH=third_party/macwatt` or `bash install.sh` if RunCat/telemetry exists. Do not claim hardware testing if not performed.
5. Initialize a Git repository only if `.git` does not exist; make the initial commit. Create a public repository `runcat-macwatt` under the currently authenticated gh user and push main.
6. Create tag `v1.0.0` for that exact commit, push it, and run `gh release create v1.0.0 dist/runcat-macwatt-v1.0.0.zip dist/SHA256SUMS.txt --title v1.0.0 --notes-file RELEASE_NOTES.md`.
7. Report final repository and release URLs, tests run, and any remaining limitations honestly.

## Constraints

- Keep menu bar **cat only**; do not add `metricsBarValue`. Users must also leave RunCat's Metrics Bar off.
- Poll `macwatt` every **5 seconds**, write JSON only if visible values change, keep the existing output file path for upgrades.
- The macwatt source is independently MIT-licensed by Amur Labs LLC, not authored here. Do not take credit for its original parsing logic.
- Do not make third-party source updates without separately validating licensing, API compatibility, and tests.
- Do not upload secrets or data from the maintainer's machine.
- The hardware API is undocumented; clearly distinguish test fixtures from real MacBook verification.

See `PUBLISH_WITH_CLAUDE.md` for the walkthrough. Do not create an App Store submission; this is a GitHub-based Python/launchd integration.
