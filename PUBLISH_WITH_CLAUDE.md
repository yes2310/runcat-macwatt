# Publishing with Claude Code + GitHub CLI (`gh`)

> Intended for the maintainer's own Mac. The source ZIP is a **GitHub repository starter**, not a preexisting Git checkout. Do not force-push to or overwrite an existing repository.

## Start Claude Code

1. Extract `runcat-macwatt-github-ready-v1.0.0.zip` into `~/Downloads/`.
2. From Terminal:

```bash
cd ~/Downloads/runcat-macwatt
claude
```

3. Paste this prompt:

```text
Read CLAUDE.md and PUBLISH_WITH_CLAUDE.md in this directory.
This is my RunCat Neo x macwatt integration. I want you to publish it as
an open-source GitHub repository using the already-installed GitHub CLI (gh).
Run tests and inspect the bundled third-party MIT license first.
Verify gh authentication, initialize Git if needed, create a PUBLIC repository
named runcat-macwatt under my authenticated account (do not overwrite an existing one),
push main, build the v1.0.0 installation ZIP, create the v1.0.0 tag and GitHub Release
with that ZIP and RELEASE_NOTES.md. Report the repository and release URLs.
If a repository with the same name exists, stop and ask me before changing it.
```

## Equivalent commands (for review)

From the project root, after checking the contents:

```bash
# 1. Confirm the current GitHub account and run offline tests
 gh auth status
 bash scripts/test.sh

# 2. Create and publish repository (ONLY if repo name isn't already taken)
 git init -b main
 git add .
 git commit -m "Initial public release: RunCat Neo macwatt integration"
 gh repo create runcat-macwatt --public --source=. --remote=origin --push \
   --description "MacBook charging and power metrics for RunCat Neo"

# 3. Tag and attach the prebuilt ZIP to the release
 git tag v1.0.0
 git push origin v1.0.0
 gh release create v1.0.0 dist/runcat-macwatt-v1.0.0.zip dist/SHA256SUMS.txt \
   --title "v1.0.0" --notes-file RELEASE_NOTES.md
```

`gh repo create` defaults to the authenticated owner when no `OWNER/` is given. If Git has already been initialized, do **not** repeat `git init`; if a remote exists, inspect it first. See [GitHub CLI repo create](https://cli.github.com/manual/gh_repo_create) and [release create](https://cli.github.com/manual/gh_release_create).

## Before you publish

- Verify the GitHub account with `gh auth status` and the target repository name.
- Check `LICENSE`, `THIRD_PARTY_NOTICES.md`, and `third_party/macwatt/LICENSE`.
- Run `bash scripts/test.sh` and check `dist/runcat-macwatt-v1.0.0.zip` exists.
- Run `bash install.sh`, `bash status.sh` and `bash uninstall.sh` on a real supported MacBook if practical. **Unit tests in CI cannot validate real hardware sensors or RunCat's UI.**
- Add your own real screenshot later if desired (do not use fabricated screenshots as evidence of UI functionality).
- Never commit tokens, credentials, local JSON sensor output or machine-specific logs.

For subsequent releases: update `VERSION`, readmes and `RELEASE_NOTES.md`, run tests, commit/push, tag a **new** version, package, and create a release. Avoid moving published tags.
