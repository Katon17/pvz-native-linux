# Contributing

> **Bahasa Indonesia**: lihat [CONTRIBUTING.id.md](CONTRIBUTING.id.md)

Thanks for wanting to help. Two important things before you start:

1. **Never attach game assets** (or derivatives) to issues, PRs, or comments —
   including screenshots of `main.pak`, the contents of `properties/`, and
   download links. PRs containing assets will be closed without discussion.
2. **Do not propose ways to obtain the game illegally.** This project only helps
   people who already own the game.

## Project scope

| Area | In scope? |
|---|---|
| Launcher, wizard, asset extraction | ✅ yes |
| Packaging (.deb, AppImage, Flatpak) | ✅ yes |
| Documentation & troubleshooting | ✅ yes |
| Rendering/audio/gameplay bugs in the engine | ❌ report to [PvZ-Portable](https://github.com/wszqkzqk/PvZ-Portable) |

If you find a bug that turns out to live in the engine, you may still open an
issue here so we can confirm it is not a launcher problem — we will point you in
the right direction.

## Development setup

```bash
git clone https://github.com/Katon17/pvz-native-linux
cd pvz-native-linux

export PYTHONPATH="$PWD/tools"
export PVZ_ENGINE="$PWD/lib/pvz-native/engine/pvz-portable"

python3 -m pvznative doctor
python3 -m unittest discover -s tests -t tests -v
```

Requires Python 3.9+. To get the engine: `./build-deb.sh --fetch-engine`.

## Before sending a PR

- [ ] `python3 -m unittest discover -s tests -t tests` is green.
- [ ] `sh -n scripts/pvz-native` and `bash -n build-deb.sh` produce no errors.
- [ ] Behaviour changes are added to `CHANGELOG.md` under `[Unreleased]`.
- [ ] No absolute paths, credentials, or game assets in the diff.
- [ ] If you touch asset extraction: add a test that builds a synthetic ISO/ZIP
      (see `tests/make_test_iso.py`).

## Code style

**Python**
- Type hints on all public signatures.
- `pathlib` for every path, never string concatenation.
- User-facing error messages are written in Bahasa Indonesia and must answer
  "so what do I do now?" — not merely state what failed.
- Do not add external dependencies. This project deliberately uses only the
  standard library so installation stays lightweight.

**Shell**
- `#!/bin/sh` + `set -eu`, POSIX-compatible.
- Quote every variable: `"$VAR"`.
- Watch `shellcheck` (`SC2086` is intentional on `$PASSTHROUGH` and commented).

## Adding distro support

For Debian-based distros, edit `packaging/debian/`. For other distros, the
priority is **AppImage** (one file, runs anywhere) before splitting into
per-distro package formats.

## Reporting bugs

Include this output — most reports can be resolved from it:

```bash
pvz-native --doctor
pvz-native --verify
cat ~/.local/share/pvz-native/logs/*.log
```

Do not include `main.pak` or the contents of `properties/`. The file name, size,
and checksum of `main.pak` are enough and do not infringe copyright.

## Contribution license

By submitting a pull request you state that:

1. Your work is **original**, or you have the right to contribute it;
2. You agree to license your work under **GPL-3.0-or-later**, the same as this
   project;
3. You have **no objection** to your name appearing in the commit history and
   the contributor list.

This project does **not** ask for a copyright assignment (CLA). Your work stays
yours; you simply grant the GPL permissions to everyone, including this project.

### PR checklist

```
[ ] python3 -m unittest discover -s tests -t tests    → all pass
[ ] sh -n scripts/pvz-native && bash -n build-deb.sh  → no errors
[ ] No game assets in the diff (main.pak, properties/, game images/audio)
[ ] No credentials, tokens, or private paths included
[ ] CHANGELOG.md updated if behaviour changed
[ ] If you change the engine patch: ENGINE_SHA256 updated in the same commit
[ ] Commit message follows Conventional Commits (see below)
```

## Commit style

```
<type>(<scope>): <short summary>

Optional explanation: why this change is needed.
```

| Type | For |
|---|---|
| `feat` | new feature |
| `fix` | bug fix |
| `docs` | documentation only |
| `test` | adding/fixing tests |
| `build` | build, packaging, dependencies |
| `refactor` | tidying code without behaviour change |
| `legal` | license, NOTICE, legal documents |

Example:

```
fix(options): respect the Full Screen checkbox when turned off

SwitchScreenMode returns early via the mIsWindowed == wantWindowed check,
so the SDL window was never changed. Forced with force=true and
mIsWindowed is synced from the SDL flag.

Refs: #12
```

## What will be rejected

- Code that takes shortcuts by copying license-incompatible code (e.g.
  GPL-2.0-only, proprietary code).
- Changes that add telemetry, analytics, or any network connection without
  prior discussion.
- "Fixes" that remove copyright notices or attribution.
- Bundling game assets in any form.
