# Security Policy

> **Bahasa Indonesia**: lihat [SECURITY.id.md](SECURITY.id.md)

## Supported versions

| Version | Supported |
|---|---|
| 0.5.x (latest) | ✅ yes |
| 0.4.x | ⚠️ critical security fixes only |
| ≤ 0.3.x | ❌ no |

Always use the latest release from
[GitHub Releases](https://github.com/Katon17/pvz-native-linux/releases).

---

## Reporting a vulnerability

**Do not open a public issue for a security problem.**

Use one of these private channels:

1. **GitHub Security Advisory** (preferred):
   <https://github.com/Katon17/pvz-native-linux/security/advisories/new>
2. Email: **cimong2356@gmail.com** with the subject `[SECURITY] pvz-native`.

Include, where possible:

- package version (`pvz-native --version` or `dpkg -l pvz-native`)
- distro & kernel version (`uname -a`)
- reproduction steps
- the impact you expect
- whether you have a proof of concept (do not attach a ready-to-use exploit)

**Response times we aim for:**

| Stage | Target |
|---|---|
| Acknowledgement | 3 business days |
| Initial assessment | 7 business days |
| Fix / mitigation | 30 days (depending on severity) |
| Public disclosure | after the fix ships, by agreement |

We will credit you in the release notes if you allow it.

---

## Scope

### In scope

| Area | Example issues |
|---|---|
| **Archive extraction** | Path traversal (`../`) in ISO/ZIP/CAB, symlink escape, zip bomb exhausting memory |
| **`.exe` installer handling** | CAB payload scanning with wrong bounds, writing outside the target folder |
| **File permissions** | Assets/saves created with overly permissive modes (world-writable) |
| **Argument injection** | Unescaped names producing separate arguments when calling `cabextract`, `xdg-open`, or the engine |
| **Launcher script** | Paths with spaces, newlines, or shell characters that are not quoted |
| **Registry parser** | Reading a corrupt `registry.regemu` causing a buffer overflow / crash |
| **Binary provenance** | An engine binary passing `ENGINE_SHA256` verification while being different |
| **Data leakage** | Anything that sends user files over the network (there should be **none**) |

### Out of scope

- Vulnerabilities in the **PvZ-Portable engine** → report to
  [upstream](https://github.com/wszqkzqk/PvZ-Portable).
- Vulnerabilities in **SDL3 / SDL3_mixer / libopenmpt** → report to the
  respective projects.
- Issues requiring physical access to the machine.
- Attacks that require the attacker to already have root.
- Display, audio, or performance bugs (use a regular issue).
- Automated scanner output without evidence of real impact.

---

## Security principles of this project

A few things are deliberately designed this way:

1. **No network access while playing.** The launcher uploads nothing. The only
   outbound connection is when you yourself open a donation link.
2. **No execution from archives.** The wizard only copies `main.pak` and
   `properties/`; it never runs a file from inside an ISO.
3. **Engine binary pinned by checksum.** The build fails if the binary does not
   match `ENGINE_SHA256` in `build-deb.sh`.
4. **No `sudo` while playing.** All user data is written under the user's own
   `$XDG_DATA_HOME` directory.
5. **No asset downloader.** This project has no "download the game" feature; you
   must supply the assets yourself.

---

## Verifying a release package

Always check the checksum before installing:

```bash
cd ~/Downloads
sha256sum -c pvz-native_0.5.2_amd64.deb.sha256
# must print: pvz-native_0.5.2_amd64.deb: OK
```

Also check the package contents — there must be **no game assets**:

```bash
dpkg-deb -c pvz-native_0.5.2_amd64.deb \
  | grep -iE 'main\.pak|LawnStrings|properties/' \
  && echo "SUSPICIOUS" || echo "OK: clean"
```

Check the engine binary itself:

```bash
rm -rf /tmp/v && mkdir /tmp/v
dpkg-deb -x pvz-native_0.5.2_amd64.deb /tmp/v
sha256sum /tmp/v/usr/lib/pvz-native/engine/pvz-portable
# compare against ENGINE_SHA256 in build-deb.sh at the same tag
```

If a checksum does not match, **do not install** and report it.
