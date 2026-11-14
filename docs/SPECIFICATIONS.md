# Minimum & Recommended Specifications

This document answers one question: **"Can my computer run this?"**

Tested on a **ThinkPad X270** (i5-7200U, Intel HD 620, 8 GB RAM, Linux Mint
22.3 XFCE, X11) — a low-end 2017 machine. If that laptop works, almost any
laptop works.

> **Bahasa Indonesia**: lihat [SPECIFICATIONS.id.md](SPECIFICATIONS.id.md)

---

## 1. Quick summary

| | Absolute minimum | Recommended | Tested on |
|---|---|---|---|
| **CPU** | x86_64 with SSE2 | 2 cores, 1.6 GHz | i5-7200U (2C/4T, 2.5 GHz) |
| **RAM** | **1 GB** | 2 GB | 8 GB |
| **GPU** | OpenGL ES 2.0 **or** OpenGL 2.1 | Intel HD 4000 or newer | Intel HD 620 |
| **VRAM** | 128 MB (shared is fine) | 256 MB | shared |
| **Disk** | **350 MB** free | 1 GB | — |
| **Display** | 1024×768 | 1366×768 | 1366×768 |
| **OS** | glibc ≥ 2.34, x86_64 | Linux Mint 22.x / Ubuntu 24.04 | Mint 22.3 |
| **Desktop** | X11 or Wayland | X11 + compositor | XFCE / X11 |

> **A note on FPS.** PvZ locks game logic at **30 FPS** (thick fog) or
> **60 FPS** (light fog) — that is a PopCap design decision, not a port
> limitation. Do not trust any "100+ FPS" claim from any source.

---

## 2. Component details

### 2.1 CPU

- **x86_64** (amd64) required. ARM/ARM64 builds are **not available yet**.
- **SSE2** required — every x86_64 CPU since 2003 has it. Nothing to check.
- No AVX, AVX2, or any other modern instruction set needed.

**Check:**

```bash
uname -m                        # must print x86_64
grep -o -m1 sse2 /proc/cpuinfo  # must print "sse2"
```

### 2.2 RAM

| Condition | Real usage |
|---|---|
| Idle (main menu) | ~180 MB |
| Normal level | ~250 MB |
| Level with many zombies | ~320 MB |
| Peak while loading assets | ~450 MB |

**1 GB is enough** if your desktop is light (XFCE, LXQt). GNOME or KDE with
many extensions should have 2 GB or more, because the desktop itself can eat
800 MB before the game even starts.

**Check:**

```bash
free -h
```

### 2.3 GPU & drivers

This is **the most common source of problems**, so read it slowly.

**What is required:** an **OpenGL ES 2.0** or **OpenGL 2.1** context. The
engine tries ES 2.0 first, then falls back to compatibility GL 2.1.

| GPU | Status | Notes |
|---|---|---|
| Intel HD 3000 (Sandy Bridge) | ✅ works | GL 3.1 via `i965`/`crocus` |
| Intel HD 4000–620 | ✅ works smoothly | `i965` / `iris` |
| Intel UHD 620+ | ✅ works smoothly | `iris` |
| AMD HD 5000+ (GCN) | ✅ works | `radeonsi` |
| Older AMD (r600) | ⚠️ may work | needs full `libgl1-mesa-dri` |
| NVIDIA (nouveau) | ⚠️ may work | slower than proprietary |
| NVIDIA proprietary | ✅ works | driver 470+ |
| Virtual GPU (VMware/VirtualBox) | ⚠️ often fails | enable 3D acceleration |
| No GPU / llvmpipe | ✅ works, slow | software rendering, ~20–30 FPS |

**Mandatory driver verification:**

```bash
# 1. Is the GL driver installed?
sudo apt install libgl1-mesa-dri mesa-utils

# 2. Which renderer is in use?
glxinfo -B | grep -E "OpenGL renderer|OpenGL version|OpenGL core profile version"

# 3. Find out which driver is active
ls /usr/lib/x86_64-linux-gnu/dri/ | grep -E "iris|i965|radeonsi|swrast|llvmpipe"
```

A renderer of `llvmpipe` or `softpipe` is **not acceptable**, **unless** you
genuinely have no GPU. If it shows up while you do have a GPU, the hardware
driver is not installed — the game will run, but slowly.

**If `glxinfo` reports a context error:** run `pvz-native --doctor`. It checks
the driver, any interfering environment variables (e.g.
`MESA_GL_VERSION_OVERRIDE`), and your desktop session.

### 2.4 Disk

| Component | Size |
|---|---|
| `.deb` package | 2.8 MB |
| Engine (installed) | 9.2 MB |
| Wizard + launcher (Python) | ~500 KB |
| Game assets (`main.pak` + `properties/`) | **~90 MB** |
| Shader cache & saves | ~15 MB |
| **Total after installation** | **~120 MB** |
| Working space while extracting an ISO | +200 MB temporary |

Allow **350 MB** free to be safe. The source ISO is not copied wholesale — only
`main.pak` and `properties/` are extracted.

### 2.5 Display

| Resolution | Result |
|---|---|
| 1024×768 (4:3) | ✅ fits, no black bars |
| 1280×800 | ✅ works, small black bars |
| 1366×768 | ✅ primary target (tested) |
| 1920×1080 | ✅ works, black bars |
| Below 1024×768 | ⚠️ untested, UI may be clipped |

**About the black bars:** PvZ is natively 4:3 (800×600). On a 16:9 display you
have two options:

- **Keep 4:3** → full image, black bars on left and right.
- **Fill the whole screen (16:9)** → image stretched to fill. Some menu
  elements shift slightly toward the edges, but the 5-lane gameplay is
  unchanged.

Set this from **Options inside the game** (the *Fill Screen (16:9)* row, on by
default) or from the Settings window.

### 2.6 Operating system

| Requirement | Value |
|---|---|
| Architecture | x86_64 (amd64) |
| glibc | ≥ 2.34 (Ubuntu 22.04 / Debian 12 / Mint 21 and newer) |
| Python | ≥ 3.9 |
| Desktop | X11 or Wayland |

**Fully supported:**

- Linux Mint 21.x / 22.x
- Ubuntu 22.04 / 24.04
- Debian 12 / 13
- Pop!_OS 22.04+
- Zorin OS 17+
- Fedora 39+ (via tarball, not `.deb`)
- Arch / Manjaro (via tarball)

**Not supported yet:** ARM, RISC-V, musl (Alpine), ChromeOS, WSL1.

### 2.7 Desktop session

| Session | Status |
|---|---|
| X11 (XFCE, MATE, Cinnamon, KDE) | ✅ most stable |
| Wayland (GNOME, KDE) | ✅ works via XWayland |
| Wayland without XWayland | ❌ will not run |
| SSH without X forwarding | ❌ will not run |
| Multi-monitor | ✅ works, game fills one screen |

---

## 3. Real-world comparison

Numbers measured on a ThinkPad X270, 1366×768, light fog:

| Scenario | CPU | RAM | FPS |
|---|---|---|---|
| Main menu | 3% | 180 MB | 60 |
| Level 1-2 (3 zombies) | 8% | 240 MB | 60 |
| Survival, wave 10 | 18% | 310 MB | 60 |
| Survival, wave 20+ | 26% | 340 MB | 60 (steady) |
| First asset load | 45% | 450 MB | — |

CPU load is low because the engine only draws 2D sprites. What matters most is
the **GPU driver**: if you fall back to `llvmpipe`, CPU usage climbs to 70–90%.

---

## 4. If it feels slow

Try these in order:

```bash
# 1. Make sure the hardware driver is used, not software
glxinfo -B | grep "OpenGL renderer"

# 2. Disable the compositor while playing (XFCE)
xfconf-query -c xfwm4 -p /general/use_compositing -s false

# 3. Lower the display resolution
xrandr --output eDP-1 --mode 1280x720

# 4. Run the built-in diagnostic
pvz-native --doctor
```

If `glxinfo` shows `llvmpipe` even though you have a GPU, the problem is the
**driver**, not the game. See section 2.3.

---

## 5. What is NOT required

So nobody wastes time installing things they do not need:

- ❌ **Wine / Proton / Lutris** — this is a native port, not a Windows wrapper.
- ❌ **Vulkan** — the engine uses OpenGL; Vulkan is unused.
- ❌ **Java / .NET / Electron** — no extra runtime.
- ❌ **Node.js / npm** — not used at all.
- ❌ **Discrete GPU** — integrated graphics is more than enough.
- ❌ **SSD** — a 5400 rpm HDD is fine; asset load takes ~2 seconds.
- ❌ **Internet access** while playing — only needed for the initial install.

---

## 6. Package dependencies

Installed and checked automatically by `apt`:

| Package | Purpose |
|---|---|
| `python3` ≥ 3.9 | launcher & wizard |
| `python3-gi`, `gir1.2-gtk-3.0` | Settings & About windows |
| `zenity` \| `kdialog` | file dialog when picking an ISO |
| `cabextract` | extracting `main.pak` from `.exe` installers that use LZX/Quantum compression |
| `libopenmpt0`, `libmpg123-0`, `libvorbis0a`, `libvorbisfile3`, `libogg0` | audio |
| `libc6` ≥ 2.34, `zlib1g` | basics |

Optional but recommended: `libgl1-mesa-dri` (GL driver), `mesa-utils` (for
`glxinfo`).

If something is missing, `pvz-native --doctor` will list each item together
with the exact `apt install` command you need.
