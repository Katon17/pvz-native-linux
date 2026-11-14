# Protecting This Work — Read This First

This document explains **what is allowed, what is not**, and **what the project
owner will do if a violation occurs**.

Project: **pvz-native-linux** — <https://github.com/Katon17/pvz-native-linux>
Copyright holder: **Katon Bagaskoro**

> **Bahasa Indonesia**: lihat [PROTECTION.id.md](PROTECTION.id.md)

---

## 1. One-paragraph summary

The code in this repository is **free to use, study, and modify**, but **not
free to take over**. Anyone distributing a modified version **must** publish
their source under the same license, **must** credit the original author, and
**may not** use this project's name or identity to mislead people into thinking
their version is official.

---

## 2. Code license: GPL-3.0-or-later

All code **owned by this project** (`scripts/`, `tools/`, `tests/`,
`build-deb.sh`, `packaging/`) is licensed under the **GNU General Public License
version 3 or later**. The full text is in [`LICENSE`](../LICENSE).

The legally important consequences:

| You may | You must | You may not |
|---|---|---|
| Use it for anything, including commercially | Publish the source of your modified version | Close the source of your modifications |
| Change it however you like | Keep the original copyright notice | Claim this code is your own work |
| Redistribute it | Include the license text | Add restrictions on top of the GPL |
| Study and learn from it | State the changes you made | Hold the original author liable for damages |

**If you use this code in your product and modify it, your source must be
open.** That is the point of copyleft — not merely "free", but "still free for
the next person".

### Why GPL-3.0 and not MIT?

MIT lets anyone take the code, close it, and sell it without giving anything
back. For a project built from scratch over hundreds of hours — including
difficult engine patch research — that is not fair. The GPL ensures derivative
work keeps giving back to the community.

### Why not AGPL?

The AGPL adds a network-service (SaaS) clause. This is a desktop application
that runs locally, so that clause is irrelevant and would only complicate
compatibility with other projects. GPL-3.0 is enough.

---

## 3. Engine: LGPL-3.0 (not ours)

The **PvZ-Portable** engine binary is someone else's work:

- Source: <https://github.com/wszqkzqk/PvZ-Portable>
- License: **LGPL-3.0-or-later**

We **do not own** that engine and **cannot** change its license. We only:

1. build it from its public source,
2. apply a small patch (fully documented in
   [`patches/widescreen.patch`](../patches/widescreen.patch)),
3. include that diff — **this is an LGPL obligation, not a choice** (§4 LGPL).

That means our patch to the engine is also subject to LGPL-3.0. Anyone may reuse
it as long as they comply with the LGPL.

**What you may not do:** bundle the engine and then claim the whole thing as
your own work, or close your modifications to the engine. That is an LGPL
violation and can be pursued by the upstream copyright holders **and** by anyone
who is harmed.

---

## 4. What this project does NOT cover

To be clear and not misleading:

| Item | Status |
|---|---|
| Game assets (`main.pak`, `properties/`, images, audio) | **© Electronic Arts Inc.** — not ours, never distributed by us |
| The names "Plants vs. Zombies", "PopCap", "EA" | Trademarks of Electronic Arts Inc. |
| The PvZ-Portable engine | LGPL-3.0, owned by its upstream contributors |
| SDL3, SDL3_mixer | zlib license, owned by SDL contributors |
| libopenmpt | BSD-3-Clause |
| Fonts/images in this repo (if any) | GPL-3.0, owned by this project |

**This package contains not a single byte of game assets.** That is not a
coincidence — it is a legal decision. If you find game assets inside a release
package, that is a serious bug; report it through the Security Policy.

---

## 5. Trademark & project identity

The name **"pvz-native-linux"**, the package name `pvz-native`, the command
`pvz-native`, the project icon, and the name **Katon Bagaskoro** as author are
**not** licensed along with the code.

**Allowed:**

- Saying "based on pvz-native-linux by Katon Bagaskoro" in your README.
- Using the code in a fork, under a different name.
- Writing articles or tutorials that mention this project.

**Not allowed:**

- Publishing a fork under the same name and making people think it is the
  official release.
- Using the project icon for another product.
- Removing the copyright notice and passing the work off as your own.
- Using the author's name to imply endorsement that does not exist.

---

## 6. If a violation occurs

The steps that will be taken, in order:

1. **Friendly contact.** We send a message with a link to this document and a
   reasonable deadline (usually 14 days) to fix the issue.
2. **Platform takedown.** Without a response, we file a copyright infringement
   report with GitHub or the hosting provider under DMCA or an equivalent
   provision.
3. **License termination.** A GPL violation means the license for this code
   **terminates automatically** for the violator (§8 GPL-3.0). After that, any
   further use is ordinary copyright infringement.
4. **Legal action.** If necessary, we pursue the legal route in the applicable
   jurisdiction.

**Proof of ownership** available: signed commit history, release dates, binary
checksums, and public archives on GitHub Releases. All of that makes a "I made
this first" claim easy to refute.

---

## 7. What to do when you fork

A short checklist so your fork is legally safe:

```
[ ] Keep LICENSE (GPL-3.0) and NOTICE
[ ] Keep the "Copyright (C) 2026 Katon Bagaskoro" notice
[ ] State in your README: "Fork of pvz-native-linux by Katon Bagaskoro"
[ ] Rename the package & command if you distribute it
[ ] Publish your modifications (the GPL requires it)
[ ] Do not include game assets
[ ] If you ship a patched engine, include patches/ as well (LGPL)
```

---

## 8. How to honour this project properly

If this project is useful to you, the simplest lawful way to give back:

- ⭐ star it on GitHub — it helps others find it,
- 🐛 report bugs with clear reproduction steps,
- 🔧 send pull requests, not a separate copy,
- ☕ support it via [Saweria](https://saweria.co/Kabako) or
  [Ko-fi](https://ko-fi.com/katonbagaskoro),
- 📣 credit the source when discussing it on forums.

That is worth far more than taking the code and erasing the author's name.

---

## 9. Frequently asked questions

**"May I sell a modified version?"**
Yes, the GPL allows it. But you **must** publish the source, credit the
original, and **may not** use this project's name as though you were the
official release. Selling without publishing source = violation.

**"May I use the code in a closed-source project?"**
No. GPL code merged into a closed-source project makes that entire distribution
subject to the GPL.

**"May I use a small part, say one function?"**
The boundary of "a small part" is vague and risky. If you copy code that is
meaningful (not just a common idiom), assume the GPL applies. If you need
certainty, ask first via an issue.

**"What if I only use the tool, not the code?"**
Running or installing the software creates no GPL obligation. Obligations arise
when you **distribute** a copy or a modified version.

**"I found someone reselling this package on a marketplace."**
Report it through the route in §6. It is often both a trademark and a GPL
violation.

---

## 10. Contact

- License violations / takedown: open an issue labelled `legal`, or reach the
  owner through the GitHub profile <https://github.com/Katon17>.
- Security vulnerabilities: do **not** open a public issue — see
  [`SECURITY.md`](../SECURITY.md).

---

*This document is not legal advice. For high-value disputes, consult an
intellectual property lawyer in your jurisdiction.*
