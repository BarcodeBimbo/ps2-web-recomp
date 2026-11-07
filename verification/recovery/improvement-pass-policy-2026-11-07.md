# Improvement-pass policy — additive optimization (2026-11-07)

**Applies to:** Hitman GS, 60 FPS, store→patch pipeline, self-heal, Alchemy (quarantined), Chrome flawless, agent handoff.

## What stays fixed (user theme / vision)

- **CyberArcade** loopback panel (`scripts/panel.py`, `:8620`), Chrome/Edge play, library per-game ids.
- **Custom** Windows PS2 path: explore → `eerecomp` → native `ps2run` + Emscripten `ps2web` (not wrapping upstream dumpers/binaries as the core).
- **Evidence culture:** `MASTER-CONTEXT.md`, `verification/recovery/`, `logs/` — no “ship without verify.”
- **Disc-fix protocol:** matrix board, SDK-aligned CDVD (`E:\usr\local\sce` research path), R5/HLE rewrite gated.
- **CNK Alchemy quarantine** vs Hitman/NFS disc-fix lane.
- **Standing mandates:** Chrome flawless library, ≥60 FPS (30 only if title requires), autonomous continuous execution, context rollover via snapshot (no in-thread trim).

## What improvements may do (additive + optimize + modernize)

| Kind | Examples | Boundary |
|------|----------|----------|
| **Optimize** | Shorter smokes for gates, parallel `autonomous_verify`, cache catalog TTL, rebuild only stale web | Same entry points (`panel`, `ps2run`, harness) |
| **Modernize** | Versioned `game-fix-registry.json`, `metrics.json` from harness, structured `install_issues.json`, optional `PS2_STRICT_VERIFY` | Extends existing scripts; no new primary app shell |
| **Harden** | `disc.iso` smoke guard, web/native mtime stale detection, ACL self-heal | Same publish path |
| **Measure** | FPS lines, `canvas_lum`, matrix JSON in verify summary | Does not change FPS bar or deferred V-Sync research ban |
| **Document** | GS invariant catalog, Chrome flawless checklist, wave table in snapshot | Docs only |

## What improvements must not do

- Replace panel/store with a different store product or drop torrent/downloader integration the user chose.
- Collapse disc-fix, matrix, Alchemy, and GS into one undifferentiated “mega patch” without board/quarantine.
- Rebrand, retarget Linux-only dumper, or rewrite README credits/GPL obligations (workspace rules).
- Auto-apply CNK host hacks or R5 HLE rewrite (`allow_discfix_apply` stays false until explicitly unlocked).

## Plan lanes (unchanged steps; refined allowance)

Each lane from the improvement-pass brief keeps the **same isolated steps**; work may now include **performance and API cleanup** on those steps:

1. **Hitman / GS** — golden capture, luminance metrics, invariant catalog (not a new renderer stack).
2. **60 FPS** — parse and record FPS in verify; allowlist for true 30 Hz titles (not new pacing product).
3. **Store pipeline** — manifests, post-download hooks, strict verify gate (optional env).
4. **Self-heal** — more detectors, idle-aware web rebuild, harness-driven canvas symptom.
5. **Matrix / Alchemy / handoff** — scorer tweaks, registry `proven_fixes[]`, snapshot discipline.

**Confirmation:** User-stated requirements are **not altered** — only tightened execution, measurement, and maintainability within the existing architecture.
