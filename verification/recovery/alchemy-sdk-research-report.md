# Alchemy SDK research report (Crash Nitro Kart / PS2Recomp)

**Job:** LIVE READ-ONLY research. **No code changes.**  
**Date:** 2026-11-06  
**ELF used:** `games/b49f2e769315347e8bda839feb705744/disc/boot.elf`  
**Note:** No file named `disc.elf` exists under the repo. `boot.elf` is the CNK EE binary (same size/entry as `SLUS_206.49` in public decomp work). Assets live in `disc.iso` (`ASSETS.GFC` / `ASSETS.GOB` present).

Parallel workers may still be writing `cnk-elf-alchemy-full-redo-report.md` / `_tmp_cnk_vt*.py`. This report **reads** those artifacts; it does not fight them.

---

## 1. What Alchemy is (for this game)

**Alchemy** is a cross-platform 3D middleware / game platform originally sold as **Intrinsic Alchemy** by Intrinsic Graphics. Vicarious Visions bought the technology in **May 2003** and kept developing it (later just “Alchemy”). CNK shipped the same year, so CNK is an early VV Alchemy title.

In CNK specifically:

| Layer | What it is |
|--------|------------|
| Runtime middleware | **Intrinsic Alchemy v3.0 -0909 (Static/Release)** — string baked into the EE ELF, built by `rdy` on **Tue Sep 9 19:28:21 2003** (matches TCRF). |
| Studio pipeline / codename | **Velocity** — config and tools names (`Velocity.igm`, `velocity-ps2-cw-dbg.elf`, `velocity-win-msvc-dbg.opt`). Not a different engine; VV’s packaging/build name around Alchemy. |
| Object model | Hundreds of C++-style classes named `ig*` (`igObject`, `igNode`, `igIGBFile`, `igFile`, `igPsx2*`, …). Reflective “meta object / meta field” serialization into **IGB** files. |
| Scene / asset binary | **IGB** (“Intrinsic Geometry Binary” / Alchemy scene graph dump): meshes, textures, UI graphs, refs. |
| Disc archive | **ASSETS.GFC** (index) + **ASSETS.GOB** (payload). GOB frames are **STBL** blocks (often zlib: magic `STBL` + tag `z`). Community shorthand “STBLz” means that compressed frame, **not** an Alchemy C++ class (no `STBLz` string in the ELF). |
| IOP file helper | **`igFileIO.irx`** — Alchemy’s IOP module for EE↔IOP file I/O (with `igUKbd.irx` / `igUMouse.irx`). Paths in ELF: `/usr/local/Alchemy/iop/modules`, `c:/Alchemy/iop/modules`. |
| Config / install roots | `alchemy.ini`, env-style tokens **`ALCHEMY_BASE`**, `ABSOLUTE_BASE`, `APPLICATION_BASE`, `$(AlchemyRoot)`. |

**Bottom line for patching:** CNK’s boot path is Alchemy FileIO + stream/loadgate + IGB object bind/parse. Emulators that “just work” still run this guest code; they do not skip Alchemy. Our host forgeries around FCE0 / soft-arm collide with Alchemy’s **bind registry**, not with a mystery custom engine.

---

## 2. Best external sources (links + plain-English takeaways)

### Tier A — directly about CNK + Alchemy

| URL | Takeaway |
|-----|----------|
| [TCRF: Crash Nitro Kart (PS2/GC/Xbox)](https://tcrf.tiago.zip/wiki/Crash_Nitro_Kart_(PlayStation_2%2C_GameCube%2C_Xbox)) | Exact Alchemy version strings per platform. PS2 = `Intrinsic Alchemy v3.0 -0909 … Sep 9 2003`. Many unused assets are `.igb` under `ps2/gfx/...`. |
| [YacaloX-Studios/cnk-decomp](https://github.com/YacaloX-Studios/cnk-decomp) | Best public CNK RE repo. Documents GFC/GOB/STBL, IGB layout, ELF = `SLUS_206.49` entry `0x00108D28`, notes Alchemy 3.0 vs studio name **Velocity**. Tools for extract/parse; executable match still early (~0% matched on decomp.dev). Docs: `docs/01_FORMATS.md`, `06_IGB_VARIANTS.md`, `07_EXECUTABLES.md`. |
| [ZenHAX: CNK ASSETS.GOB](https://zenhax.com/viewtopic.php@t=8254.html) | GFC = file table, GOB = archive; same family as Over the Hedge BMS; Zlb/zlib compression. |
| [ZenHAX: CNK PNG / STBL fix](https://www.zenhax.com/viewtopic.php@t=17123.html) | Confirms `STBL` framing, compression tag `z` vs `0`, `ENBL` end mark; CNK name length 72 in GFC. |
| [Xentax: Star Wars Jedi Academy Xbox GOB](https://wiki.xentax.spektr.name/index.php/Star_Wars_Jedi_Academy_XBox_GOB) | Clear STBL / `z`|`0` / ENBL / zlib layout used by VV-style GOB packs (same pattern CNK uses). |
| [Reddit: CNK / Alchemy kit leak](https://www.reddit.com/r/crashteamracing/comments/10n2h59/crash_nitro_kart_dev_tools_leaked_online/) | Points at public Alchemy tooling dump. |
| [Internet Archive: alchemy-kit](https://archive.org/details/alchemy-kit) | **Intrinsic Alchemy 5.0 evaluation** + docs (`AlchemyKit.zip`, GettingStarted / UsersGuide). Explains scene graph, **Fast IGB**, Finalizer / Insight / Optimizer, PS2 CodeWarrior paths, `IG_ROOT` / plugins. **Version is newer than CNK’s 3.0** — use for concepts, not byte-identical runtime. Also ships `GOBtools.zip`. |

### Tier B — Alchemy object model / IGB (later games, still useful)

| URL | Takeaway |
|-----|----------|
| [XentaxWiki: Alchemy IGB](https://wiki.xentax.spektr.name/index.php/Alchemy_IGB) | IGB = Alchemy scene files; tags like `igInfoList`, `igImage`; format “complicated”; tools Finalizer + InsightViewer. |
| [gist mateon1 — Alchemy 3.2 IGB parser](https://gist.github.com/mateon1/b123a53d824305767989ebc2ba3e5814) | Working Python parse of Alchemy **3.2** IGB: meta inheritance (`igInfo` / `igSceneInfo` / lists / `igImage`). Closest public code to CNK’s era (CNK is 3.0; treat field layouts as *near*, not identical). |
| [MarvelMods Alchemy 5 tutorial](https://marvelmods.com/forum/index.php/topic,11158.0.html) | History (Intrinsic → VV); version matrix (3.2 / 3.5 / 4 / 5 / 6); **IGB version nibble ≠ always game marketing version**; Alchemy 5 tools often want Alchemy 2.5 for older console content. |
| [marvelmods igb format thread](https://marvelmods.com/forum/index.php?topic=824.0) | Header layout: 32-byte per-file header + 16-byte version block including `DA FA` endian cookie. |
| [Product overview (Intrinsic Alchemy)](http://www.thesoftwarenetwork.com/Video-Game-Developers/Product_Overview_3349567.htm) | Marketing but accurate: reflective object model, Fast IGB streaming, PS2-tuned microcode, Finalizer/Insight/Optimizer. |
| [MobyGames: Game Engine Alchemy](https://www.mobygames.com/group/4109/game-engine-alchemy/) | Engine attribution / title list. |
| [RetroReversing: PS2 IRX list](https://www.retroreversing.com/irx-ps2) | Census entry for **`igfileio.irx`** (rare) and **`igaudio2.irx`**. |

### Tier C — later Alchemy (Skylanders / MUA tooling; do not over-apply)

| URL | Takeaway |
|-----|----------|
| [NefariousTechSupport/igRewrite8](https://github.com/NefariousTechSupport/igRewrite8/) | Modern `igLibrary` for late Alchemy (Skylanders). Shows durable naming (`igIGBFile`, archives) but formats evolved. |
| [NefariousTechSupport/igArchiveExtractor](https://github.com/NefariousTechSupport/igArchiveExtractor/) | `.arc`/`.bld`/IGZ — post-CNK. |
| [KaikoClanworth1/igb-blender](https://github.com/KaikoClanworth1/igb-blender) | Blender IGB for XML2/MUA (Alchemy ~3.2–4). Useful UI for “what an IGB contains,” not CNK slot-paging. |
| [ChmtTnky/IGBDataExtractor](https://github.com/ChmtTnky/IGBDataExtractor) | Uses **Alchemy 5.0 SDK** privately — proves SDK still circulates; “DO NOT ASK FOR ACCESS.” |
| [nikita488/actorConverter](https://github.com/nikita488/actorConverter) | `#include <igCore/igIGBFile.h>` — evidence of leaked/private Alchemy headers in modding community; **no public SDK tree**. |
| [Superredstone/Skylands-Untrapped](https://github.com/Superredstone/Skylands-Untrapped) | Alchemy **v8.1** format crate naming `igIGBFile` — late lineage only. |

### What we did **not** find

- No public **Alchemy 3.0 PS2 SDK source** or full `igFileIO` API docs.
- No PCSX2 wiki page dedicated to Alchemy FileIO / CNK IGB parse.
- No GitHub “Alchemy PS2 SDK” dump matching CNK’s static lib (only IRX name hits + later tools).
- `ALCHEMY_BASE` on GitHub is almost always the unrelated **Alchemy.com blockchain RPC** — ignore those hits.

---

## 3. ELF signatures / vtables / structure map

### 3.1 Binary identity

| Field | Value |
|-------|--------|
| Path | `…/disc/boot.elf` (no `disc.elf`) |
| Size | 6,234,672 bytes (same as cnk-decomp `SLUS_206.49`) |
| Entry | **`0x00108D28`** |
| PT_LOAD | file `0x80` → VA **`0x00100000`**, filesz `0x5F2000`, memsz `0x62A480` |
| BSS | **`0x006F2000`–`0x0072A480`** (includes bind globals) |
| Symbols | Stripped (no useful `.symtab`) |

### 3.2 Hard Alchemy string signatures (VA)

| VA | String / meaning |
|----|------------------|
| `0x006B4920` | `Intrinsic Alchemy  v3.0 -0909 (Static/Release)` + build line |
| `0x006B2288` | `ALCHEMY_BASE` (with `ABSOLUTE_BASE` / `APPLICATION_BASE`) |
| `0x006B4B08` | `alchemy.ini` |
| `0x006B4B18` / `0x006BA100` | `Alchemy` |
| `0x006B8F18` | **`igFileIO.irx`** |
| `0x006B8E90` / `0x006B8EB0` | `/usr/local/Alchemy/iop/modules`, `c:/Alchemy/iop/modules` |
| `0x006B2B90` | `igIGBFile` |
| `0x006B5080` | `igIGBFile::readFile() - External Entry "%s" failed…` |
| `0x006B5150` | `igIGBFile::readFile(%s) - unable to read this oldversion… Run igbUpdate…` |
| `0x006B3198` | `igFile` |
| `0x006BD768` | `igFileImage` |
| `0x006B4890` | `igPsx2IopRpcConnection` |
| `0x00640870` | `igStreamingSource` |
| `0x0061099C` | Embedded debug/config mentioning **`Velocity.igm`** and `velocity-ps2-cw-dbg.elf` |
| `0x006A3BD0` | `Alchemy display %dx%d…` |

**~670** distinct `ig[A-Za-z0-9_]+` class-name strings. Absolute pointer tables to those names are sparse (GUI/attr clusters around `0x63ACxx`); most type registration is **factory / runtime**, not RTTI dumps.

### 3.3 Anchor map (runtime)

```
boot entry 0x00108D28
    │
    ├─ early factory use of 0x00508930 (alloc via *0x725F00 vtable+8, arg type=3)
    │
loadgate object (host nickname) ── slots stride 96, ~250 slots
    │  flags: +24008, +24016, +24020  (see 0x0010F5CC…)
    │  stream buffer ptr often at slot/stream +0x48 → host saw 0xBD1000
    │
0x0010F5EC  jal  0x0010FCE0     ← “FCE0” drain (only 1 call site)
0x0010FD3C  jal  0x00110100     ← parse/finalize when status matches
0x00110100  checks obj+44 / obj+45; else forces status (+76) = 4 and tears down
    │
bind registry BSS pointer  0x00725F50   ← MUST be live before some virtual calls
    │  installer 0x00520160:
    │     jal 0x508930 → sw v0, 0x725F50
    │     then vt+208 / vt+84 registration of child object (+44 = 1)
    │  teardown 0x00520210: clears 0x725F50 to 0
    │
0x0051AC80  post-load / unbind-ish path (callers include 0x10FF10)
0x0051ACBC  lw a0, [0x725F50]
0x0051ACC8  jalr  *(vtable+80)   ← lookup with key from obj+32
0x0051ACE0  jalr  *(returned->vtable+84)
0x0051ACEC  ← RA when returned object/vtable slot is NULL  (“null bind”)
```

### 3.4 Nearby BSS / factory pool (partial)

| VA | Role (evidence-based) |
|----|------------------------|
| `0x00725F50` | **Bind registry singleton pointer** (installed `sw` @ `0x520180`, cleared @ `0x5202AC`) |
| `0x00725F00` | Factory “type/allocator” object used by `0x508930` (`lw a0,[0x725F00]; jalr vt+8`) |
| `0x00725EF0` / `0x00725EF8` | Alternate pools selected inside factory |
| `0x00725EE0` | Heavily referenced sibling global (many lw sites) |
| `0x00705C18` / `0x00705F18` / `0x00705C10` | Sema-related storage (cross-checked by parallel ELF scripts; used by CD/loadgate wait paths) |

### 3.5 Virtual-call convention (this path)

Observed pattern (standard Alchemy/C++ on EE):

1. `lw t9, 0(obj)` → vtable  
2. `lw t9, N(t9)` → slot at byte offset **N**  
3. `jalr t9`

On the crashing path:

- **N = 80** (`0x50`): registry lookup; delay slot loads key from **`s0+32`**.  
- **N = 84** (`0x54`): method on **returned** object — **this** is what dies when `v0` is null / empty vtable (`ra=0x51ACEC`).  
- Installer also uses **N = 208** (`0xD0`) when registering.

### 3.6 Prior local cross-checks (read, not rewritten)

| Artifact | What it already established |
|----------|-----------------------------|
| `verification/recovery/_cnk_elf_xrefs.json` | entry `0x108d28`, load `0x100000`, ~677 ig names; RTTI heuristic mostly empty |
| `verification/recovery/_cnk_bind_xrefs.json` | Class name VAs; `0x725F50` / `0x725EE0` access sites |
| `verification/host-session-2026-11-06-overnight-cnk-10p.json` | Bytes can land in `BD1000`, `+76=1`, but parse/UI stuck; forced `0x110100` → null jalr |
| `cnk-nullbind-51ACEC-restart-report.md` | Soft-arm `+45` without host FCE0 stable; forced FCE0 → `vt+84` null @ `0x51ACEC` |
| Parallel `_tmp_cnk_vt*.py` | Disasm of installer `0x520160`, factory `0x508930`, FCE0 flag gates — consistent with above |

`cnk-elf-alchemy-full-redo-report.md` was **not present** when this report was written.

---

## 4. Cross-ref table (web ↔ ELF)

| Claim | Web / docs | ELF / overnight | Confidence |
|-------|------------|-----------------|------------|
| Engine is Intrinsic Alchemy ~3.0 | TCRF, cnk-decomp README | Exact version string @ `0x6B4920` | **Sure** |
| Studio name “Velocity” | cnk-decomp formats + opt manifest | `Velocity.igm` / `velocity-ps2-cw-dbg.elf` in ELF | **Sure** |
| Assets are IGB scenes | TCRF paths, Xentax, MarvelMods | `igIGBFile`, readFile error strings | **Sure** |
| Disc pack is GFC+GOB / STBL(+z) | ZenHAX, cnk-decomp, Xentax GOB | ISO has `ASSETS.GFC`/`GOB`; no `STBLz` C-string (format is binary) | **Sure** |
| `igFileIO.irx` is Alchemy IOP FileIO | RetroReversing rare IRX; Alchemy module paths | String + module path list in ELF | **Sure** |
| `ig*` naming = Alchemy object model | Product docs, igRewrite, MarvelMods | 600+ `ig*` names in ELF | **Sure** |
| Entry `0x108D28` | cnk-decomp `07_EXECUTABLES.md` | ELF `e_entry` | **Sure** |
| `0x725F50` is bind registry | Overnight / nullbind reports | Installer `sw v0,0x725F50`; crash path loads it | **Sure** |
| `0x10FCE0` / `0x110100` are loadgate drain / parse | Overnight session language | Single jal sites; flag checks match | **Sure** |
| Null crash = `*(lookup()->vt+84)` | nullbind report | Exact disasm `0x51ACC8` / `0x51ACE4` | **Sure** |
| Alchemy 5 kit docs describe CNK runtime | Archive kit is **5.0** | CNK is **3.0 static** | **Concept-only** |
| CNK IGB ≡ Alchemy 3.2 gist / MUA tools | mateon1 / igb-blender | Same family; CNK has 64KB slot paging (cnk-decomp) | **Near / verify** |
| `STBLz` is an Alchemy class | Forum shorthand | **Not** in ELF; archive framing only | **Reject as class name** |
| Host-forcing FCE0 can finish IGB parse | Earlier hope | Killed by `0x51ACEC` when registry cold | **Reject** |
| `loadgate` / `AlignReadBuffer` symbol names | Host nicknames | **Not** present as C strings | **Nickname only** |
| Full public SDK / headers for PS2 3.0 | Searches | Only later private `#include <igCore/…>` crumbs | **Unavailable** |

---

## 5. What to stop guessing / safe next analysis steps

### Stop guessing

1. **CNK is Alchemy 3.0 + Velocity pipeline** — not a one-off proprietary engine.  
2. **Do not treat Alchemy 5 / Skylanders tools as drop-in truth** for CNK FileIO or IGB paging.  
3. **Do not force host FCE0 / `0x110100`** hoping to “finish parse” — guest needs a live object from **`*0x725F50` lookup** first.  
4. **`STBLz` is GOB frame compression**, not a runtime type to bind.  
5. **`ALCHEMY_BASE` is an Alchemy path token**, not a blockchain constant and not a code address.  
6. **`disc.elf` does not exist** — keep using `boot.elf` / ISO `SLUS_206.49`.  
7. **Quarantine:** none of this CNK Alchemy bind/FCE0 knowledge should be applied to Hitman/NFS disc-fix.

### Safe next analysis (still read-only / observe-first)

1. **One-instruction dump before `0x51ACD4`:** `ee32(0x725F50)`, `v0` after vt+80, key at `obj+32`, and `*(v0)` — forced-FCE0 vs soft-arm baseline (already recommended in nullbind report).  
2. **Trace who calls `0x520160` installer** and when relative to first IGB status=1 — ensure registry exists *before* any drain that reaches `0x51AC80`.  
3. **Map factory type id `3`** at `0x508930` / pools `0x725EF0`–`0x725F00` to an `ig*` class name if possible (string side-channel or cnk-decomp `symbols.csv`).  
4. **Pull cnk-decomp** `docs/*` + `symbols.csv` offline and align addresses (same ELF). Prefer their IGB/GFC facts over re-deriving.  
5. **From `disc.iso`:** confirm whether `igFileIO.irx` is a standalone MODULES file or only referenced/embedded; list MODULES vs ELF string list (`vvaa.irx`, `cri_adxi.irx`, …).  
6. **IGB header check** on planted butanim/intro streams: expect Alchemy `0xFADA` cookie / version flags (cnk-decomp); compare to what `0x110100` assumes.  
7. **Optional concept read:** Alchemy 5 GettingStarted (Archive) for scene graph / IGB vocabulary only — then return to CNK 3.0 ELF.

### Explicit scope seal

**NO CODE CHANGES in this job.** No Hitman/NFS/runtime patches. No fighting the parallel CNK ELF redo worker’s files.

---

## 6. Spoken-friendly summary

Crash Nitro Kart is running **Intrinsic Alchemy 3.0** (Vicarious Visions’ middleware), with their studio pipeline nicknamed **Velocity**. Models and UI come from **IGB** files packed in **ASSETS.GFC/GOB** as **STBL** (often zlib) frames, and the EE talks to IOP through Alchemy’s **`igFileIO.irx`**.

The public web has strong confirmation of that (TCRF, cnk-decomp, ZenHAX, an Alchemy 5 eval kit on Archive.org), but **no full PS2 3.0 SDK**. Our `boot.elf` matches the known CNK executable and still contains the Alchemy version string, hundreds of `ig*` class names, and the bind/loadgate code we’ve been hitting.

The crash at **`ra=0x51ACEC`** is not mysterious anymore in structure: after CD/stream work, code looks up something through the BSS pointer **`0x725F50`**, then calls **vtable slot +84** on the result — and that result is null when we force parse too early. Soft-arm without forced FCE0 stays alive but never finishes drawing UI.

Next safe work is **observe the bind registry install and the lookup key**, not more host FCE0 guessing — and keep CNK Alchemy tricks quarantined from Hitman/NFS.
