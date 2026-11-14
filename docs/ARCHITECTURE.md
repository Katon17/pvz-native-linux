# Architecture & Data Flow

This document explains **how the parts of the project work together**, for
anyone who wants to modify or audit the code.

> **Bahasa Indonesia**: lihat [ARCHITECTURE.id.md](ARCHITECTURE.id.md)

---

## 1. Big picture

```
┌──────────────────────────────────────────────────────────────────┐
│  User                                                            │
│    ├── Application menu  ──► pvz-native (sh script)              │
│    ├── "Settings" menu   ─► pvz-native --settings                │
│    └── "About" menu      ─► pvz-native --about                   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  /usr/bin/pvz-native            (POSIX sh, ~380 lines)           │
│    • parse arguments                                             │
│    • check whether assets are present                            │
│    • export PVZ_WIDESCREEN                                       │
│    • exec the engine                                             │
└──────────────────────────────────────────────────────────────────┘
        │                              │
        │ assets missing               │ assets present
        ▼                              ▼
┌──────────────────────────┐   ┌──────────────────────────────────┐
│ python3 -m pvznative     │   │ /usr/lib/pvz-native/engine/      │
│   setup  (wizard)        │   │   pvz-portable  (static binary)  │
│   • detect ISO/ZIP/EXE   │   │   -resdir <assets>/              │
│   • scan & extract       │   │   -savedir <saves>/              │
│   • verify               │   └──────────────────────────────────┘
└──────────────────────────┘
```

---

## 2. Code layers

| Layer | Location | Language | Responsibility |
|---|---|---|---|
| **Launcher** | `scripts/pvz-native` | POSIX sh | Argument parsing, asset check, exec engine. Deliberately "dumb" — all heavy logic lives in Python. |
| **Wizard & tools** | `tools/pvznative/` | Python 3.9+ | Source detection, CAB/ZIP/ISO extraction, verification, diagnostics. |
| **GUI** | `tools/pvznative/settings_gui.py`, `about.py` | Python + GTK3 | Settings and About windows. |
| **Packaging** | `build-deb.sh`, `packaging/debian/` | sh + dpkg | Builds `.deb` and `.tar.gz`, embeds the engine checksum. |
| **Engine** | `lib/pvz-native/engine/pvz-portable` | C++20 (binary) | PvZ-Portable — built separately, see §5. |
| **Tests** | `tests/` | Python unittest | 68 tests, no real game assets needed. |

### Why is the launcher written in sh, not Python?

So it still runs when Python is broken, and so `pvz-native --where` remains
usable for diagnosing Python problems. The rule: **the launcher must not contain
logic that needs testing.** Everything with non-trivial branching lives in
`tools/pvznative/`, which has tests.

---

## 3. Asset data flow

Assets are **never** shipped inside the package. The flow is:

```
Source owned by the user         User data
────────────────────────         ──────────
ISO installer        ──┐
ZIP                  ──┤
Game folder          ──┼──► wizard ──► ~/.local/share/pvz-native/
Installer .exe       ──┘   (selective)     ├── assets/
                                            │   ├── main.pak
                                            │   └── properties/
                                            ├── saves/
                                            └── logs/
```

**Only two things are extracted:** `main.pak` and the `properties/` folder.
Everything else (the installer, the rest of the ISO) is neither copied nor
modified.

### Source detection

| Type | How it is detected |
|---|---|
| ISO 9660 | `CD001` magic at offset 0x8001; level-1 uppercase names handled (case-insensitive matching) |
| ZIP | `PK\x03\x04` magic |
| Folder | Check for the presence of `main.pak` + `properties/` |
| Installer `.exe` | CAB payload located via the `MSCF` magic inside the binary, then `cabextract -F "*main.pak"` |

**Pitfalls already handled:** a level-1 ISO stores folder names in uppercase
(`PROPERTIES/`), while the code expects `properties/`. All names inside an
archive are matched case-insensitively.

---

## 4. Preferences & state storage

| State | Location | Format |
|---|---|---|
| Assets | `$XDG_DATA_HOME/pvz-native/assets/` | binary (from the user) |
| Save games | `$XDG_DATA_HOME/pvz-native/saves/` | `userdata/` + `registry.regemu` |
| Logs | `$XDG_DATA_HOME/pvz-native/logs/` | text |
| Widescreen preference | `$XDG_CONFIG_HOME/pvz-native/widescreen` | `"1"` / `"0"` |
| Screen mode | `saves/registry.regemu` | custom binary, key `ScreenMode` |

### `registry.regemu` format

```
"REGEMU" | u16 version=1 | u32 numKeys |
  per key: u32 nameLen | name (utf-8) | u8 type | value
```

Type `4` = integer, `2` = float, `1` = empty key. Keys actually written by the
engine: `CustomCursors, InProgress, MusicVolume, Muted, PreferredX, PreferredY,
ScreenMode, SfxVolume, WidescreenStretch, WaitForVSync`.

Modified through `pvznative/display.py` (CLI) and `settings_gui.py` (GUI) — both
use the same functions, so there is no duplicated logic.

---

## 5. Engine patching

The engine is a **third-party binary** (PvZ-Portable, LGPL-3.0). We change
nothing without documenting it.

| File | Contents |
|---|---|
| `patches/widescreen.patch` | Full diff against upstream (635 lines), the source of our LGPL obligation. |
| `ENGINE_SHA256` in `build-deb.sh` | Checksum of the binary allowed into the package. The build fails on mismatch. |

**The rule we hold to:** if the patch changes, the checksum **must** be updated
in the same commit. This prevents an unknown binary from entering the package
without a trace.

> **Note on how the official release is built.** `build-deb.sh` points at the
> **unmodified upstream release** (`0.2.7`), not at a locally patched binary.
> The widescreen behaviour the patch describes is applied at runtime through
> `registry.regemu` and the `PVZ_WIDESCREEN` environment variable, so the
> shipped engine stays byte-identical to what upstream publishes and anyone can
> verify it with `curl | sha256sum`. See `docs/BUILDING.md` §3.7.

### What the patch changes

1. `GLInterface.cpp` — *stretch* branch in `UpdateViewport()` when
   `gWideScreenStretch` is active (viewport becomes `0,0,1366,768` instead of
   `171,0,1024,768`).
2. `SexyAppBase.cpp` — reads `PVZ_WIDESCREEN` + registry key, default **on**.
3. `NewOptionsDialog.cpp/.h` — the "Fill Screen (16:9)" row, the About panel,
   and the donation buttons (`SDL_OpenURL`).
4. `Window.cpp` — syncs `mIsWindowed` with the actual SDL flag.
5. `LawnApp.cpp` — `SwitchScreenMode(..., true)` so mode changes are not ignored.

---

## 6. Render flow (why widescreen works)

```
LawnApp::Init
  mWidth = gLogicalWidth   (800 normally, 1067 when stretched)
       │
       ▼
GLInterface::Init
  mWidth = mApp->mWidth
  glUniformMatrix4fv(ortho 0..mWidth)     ← horizontal drawing space widens
       │
       ▼
GLInterface::UpdateViewport()   ← PATCH POINT
  normal mode : viewport 171,0,1024,768   (4:3 pillarbox)
  stretch mode: viewport 0,0,1366,768     (full 16:9 fill)
       │
       ▼
glViewport(...) every frame
```

Gameplay stays at **5 lanes**. Only the mapping of coordinates to the screen
changes; grid logic, collisions, and lane count are untouched.

**A limitation you should know:** reanimation assets have a fixed 800×600
canvas. Adding lanes is therefore impossible without replacing assets — that
approach was tried and rejected.

---

## 7. GUI flow

```
pvz-native --settings
  └─ check GTK_PYTHON (/usr/bin/python3, not a pyenv/venv one)
     └─ python3 -m pvznative settings
        ├─ read state: read_wide(), display.screen_mode()
        ├─ show 2 checkboxes + 4 buttons
        └─ actions:
            Save             → display.set_screen_mode(), write_wide()
            Save & Play      → apply_now() → Popen(launcher, start_new_session)
            About            → about.run(parent)
            (Close)          → exit without applying
```

**Why the GTK interpreter is looked up separately:** `python3-gi` is only
installed for `/usr/bin/python3`. If the user has pyenv/conda/venv active,
`python3` may point there and `import gi` fails. The launcher checks several
candidates and picks the one that actually has `gi`.

---

## 8. Testing

| Kind | Command | Coverage |
|---|---|---|
| Unit tests | `python3 -m unittest discover -s tests -t tests` | 68 tests: parser, CAB extraction, registry, preferences, About dialog |
| Shell syntax | `sh -n scripts/pvz-native && bash -n build-deb.sh` | syntax |
| Build | `./build-deb.sh` | package produced + checksum matches |
| Integrity | `dpkg-deb -c release/*.deb` | ensures **no** game assets are packaged |

Tests deliberately use **synthetic ISO/CAB** files created inside the test, not
real game assets. That is why the suite can run on public CI without infringing
copyright.

---

## 9. Final design decisions

Recorded so they are not proposed again:

| Decision | Reason |
|---|---|
| **No Wine/Proton** | This is a native port; Wine was rejected from the start. |
| **Assets are never bundled** | Legal obligation; a package without assets is safe to distribute. |
| **Stretch, not extra lanes** | Reanimation assets are locked to 800×600. Extra lanes are impossible without replacing assets. |
| **POSIX sh launcher** | Must keep working when Python is broken. |
| **50 lanes? No.** | Gameplay stays at 5 lanes, per the original design. |
| **Engine binary pinned by checksum** | Prevents an unknown binary from entering a release. |
| **Runtime hooking rejected** | The engine is static with 0 undefined GL/SDL symbols — technically impossible. |
