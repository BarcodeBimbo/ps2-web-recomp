# PS2 SDK / toolkit download links

**Target folder for the caller:** `E:\AI games`  
**Updated:** 2026-11-06  
**Rule:** Direct HTTP (Archive.org / GitHub) or `.torrent` only. No login, no payment.

Suggested layout after download:

```
E:\AI games\
  ps2-sdk\
    official\
    homebrew\
    docs\
    linux-kit\
    middleware\
```

URL-encode spaces as `%20` if a client chokes on raw spaces.

---

## Grab first (highest value for Hitman/NFS + R5)

| Name | What it is | URL |
|------|------------|-----|
| **ps2dev Windows prebuilt v2.0.0** | Full homebrew env: toolchain + ps2sdk + gsKit + ports + packer | https://github.com/ps2dev/ps2dev/releases/download/v2.0.0/ps2dev-windows-latest.tar.gz |
| **ps2sdk source (master zip)** | Open EE/IOP SDK — libcdvd, SIF, pad, cdvdfsv notes from SCE 3.1.0 | https://github.com/ps2dev/ps2sdk/archive/refs/heads/master.zip |
| **Open PS2 Loader source** | Best retail-like `cdvdfsv` / `cdvd_readee` / NCMD reference | https://github.com/ps2homebrew/Open-PS2-Loader/archive/refs/heads/master.zip |
| **Sony PS2 SDK 3.0.3 ISO** | Complete official July 2005 Runtime Library + docs + tools (preferred official) | https://archive.org/download/PlayStation2July2005SDKversion3.0.3/PlayStation%202%20July%202005%20SDK%20%28version%203.0.3%29.iso |
| **SDK 3.0.3 torrent** | Same item via BitTorrent | https://archive.org/download/PlayStation2July2005SDKversion3.0.3/PlayStation2July2005SDKversion3.0.3_archive.torrent |
| **libpad PDF (Release 1.5)** | Official Controller Library doc — **R5 pad** | https://archive.org/download/ps-2-programmer-tool-runtime-library-controller-library/PS2%20Programmer%20Tool%20Runtime%20Library%20-%20Controller%20Library.pdf |
| **libpad PDF (Release 1.1)** | Earlier libpad doc | https://archive.org/download/ps-2-programmer-tool-runtime-library-controller-library-v-1.1/PS2%20Programmer%20Tool%20Runtime%20Library%20-%20Controller%20Library%20-%20v1.1.pdf |

---

## Official Sony / third-party toolkits (Archive.org `ps2_sdks`)

**Collection page:** https://archive.org/details/ps2_sdks  
**Bulk torrent (whole pack ~1.6G):** https://archive.org/download/ps2_sdks/ps2_sdks_archive.torrent  
**Directory listing:** https://archive.org/download/ps2_sdks/

| Name | What it is | Direct URL |
|------|------------|------------|
| **Runtime Library 2.0 (DTL-S12010)** | Official RTL 2.0 libraries | https://archive.org/download/ps2_sdks/Runtime_Library_2.0_DTL-S12010_fix.7z |
| **Runtime Library 2.0 RAR** | Same era, alternate archive | https://archive.org/download/ps2_sdks/DTL-S12010%20PS2_Runtime_Library_Release_2.0.rar |
| **Runtime Library 1.0 (DTL-S12000)** | Early NextGen RTL | https://archive.org/download/ps2_sdks/DTL-S12000%20NextGen_Playstation_Runtime_Library_Release_1.0.rar |
| **Toolchain 2.0 (DTL-S13010)** | Official EE/IOP GCC toolchain 2.0 | https://archive.org/download/ps2_sdks/Toolchain_2.0_DTL-S13010_fix.7z |
| **Toolchain 2.0 RAR** | Alternate | https://archive.org/download/ps2_sdks/DTL-S13010%20PS2_Tool_Chain_Release_2.0.rar |
| **EB Tool Chain 0.5.0** | Early Emotion Board toolchain | https://archive.org/download/ps2_sdks/EB-S8220%20NextGen_Playstation_EB_Tool_Chain_Release_0.5.0.rar |
| **SCE Tool-Libs 2.4.2** | Mid-era libs (marked broken in filename) | https://archive.org/download/ps2_sdks/SCE%20Tool-Libs%202.4.2%20-%20DTL-S2324_broken.zip |
| **tlib_250 … tlib_255** | Drop-in Standard Libraries tarballs (ProDG-era) | https://archive.org/download/ps2_sdks/tlib_250.tgz · … · https://archive.org/download/ps2_sdks/tlib_255.tgz |
| **ee001003_1.tgz** | EE compiler bits | https://archive.org/download/ps2_sdks/ee001003_1.tgz |
| **iop281.tgz** | IOP compiler bits | https://archive.org/download/ps2_sdks/iop281.tgz |
| **SN ProDG 3.01** | Win32 SN build/debug suite | https://archive.org/download/ps2_sdks/SN%20Systems%20ProDG_for_PS2_3.01.zip |
| **SN ProDG 2.0** | Older ProDG | https://archive.org/download/ps2_sdks/SN%20Systems%20ProDG_for_PS2_2.0.zip |
| **SN ProView 0.6.7** | SN viewer | https://archive.org/download/ps2_sdks/SN%20Systems%20ProView%20for%20PS2%200.6.7.zip |
| **SN NDK 1.02** | SN Network Dev Kit | https://archive.org/download/ps2_sdks/SN%20Systems%20NDK%20for%20PS2%201.02.zip |
| **ProDG Target Manager** | Target Manager zip | https://archive.org/download/ps2_sdks/ProDGTMforPS2v22815.zip |
| **CodeWarrior for PS2 3.01** | Metrowerks CW | https://archive.org/download/ps2_sdks/CodeWarrior_for_PS2_3.01.zip |
| **CodeWarrior for PS2 3.04** | CW 3.04 MPTP1 | https://archive.org/download/ps2_sdks/CodeWarrior_for_PS2_3.04_MPTP1.zip |
| **CodeWarrior 3.03J** | Japanese CW release | https://archive.org/download/ps2_sdks/CodeWarrior_for_PS2_Release_3.03J.zip |
| **Codewarrior 1.5 / 3 RAR** | Older CW dumps | https://archive.org/download/ps2_sdks/Codewarrior_1.5.rar · https://archive.org/download/ps2_sdks/Codewarrior_3.rar |
| **CW Analysis Tools** | Profiler / analysis | https://archive.org/download/ps2_sdks/CodeWarrior_Analysis_Tools_for_PS2_1.1.2.zip · https://archive.org/download/ps2_sdks/CodeWarrior_Analysis_Tools_for_PS2_2.0.zip · https://archive.org/download/ps2_sdks/Codewarrior_Analysis_Tool_1.0.rar |
| **CW ComUtil 1.0** | CW utility | https://archive.org/download/ps2_sdks/CodeWarrior_ComUtil_for_PS2_1.0.zip |
| **CD/DVD-ROM Generator 1.20 / 1.5 / 2.0** | Disc mastering tools | https://archive.org/download/ps2_sdks/CD_DVD-rom%20Generator%20ver1.20.zip · https://archive.org/download/ps2_sdks/CD_DVD-rom%20Generator%20ver1.5.7z · https://archive.org/download/ps2_sdks/CD_DVD-rom%20Generator%20ver2.0.7z |
| **cdgen150.zip** | CD generator alt | https://archive.org/download/ps2_sdks/cdgen150.zip |
| **PS2 Sound Artist Tool** | SPU2/MIDI authoring | https://archive.org/download/ps2_sdks/PS2%20Sound%20Artist%20Tool.rar |
| **LibDNAS** | Online auth libs | https://archive.org/download/ps2_sdks/LibDNAS.7z |
| **CRI SDK 1.10 patch5** | CRI middleware | https://archive.org/download/ps2_sdks/CRI_SDK_1.10_patch5.zip |
| **TIM2 tools** | Texture tools | https://archive.org/download/ps2_sdks/tim2img_e.zip · https://archive.org/download/ps2_sdks/tim2sample_e.zip · https://archive.org/download/ps2_sdks/tim2v4b_e.zip |
| **SCE-RT.rar** | SCE runtime bits | https://archive.org/download/ps2_sdks/SCE-RT.rar |
| **QATOOL304iso** | QA tool ISO zip | https://archive.org/download/ps2_sdks/QATOOL304iso.zip |
| **Super Bender Boot Disc** | Boot disc image | https://archive.org/download/ps2_sdks/Super_Bender_Boot_Disc-2007-05-08.7z |

---

## PS2 Linux Kit

| Name | What it is | URL |
|------|------------|-----|
| **Linux Kit collection** | Item page | https://archive.org/details/linux-for-playstation-2 |
| **Torrent (all discs)** | BitTorrent for the set | https://archive.org/download/linux-for-playstation-2/linux-for-playstation-2_archive.torrent |
| **RTE Disc 1 (Europe) ISO** | Runtime Environment | https://archive.org/download/linux-for-playstation-2/Linux%20%28for%20PlayStation%202%29%20Release%201.0%20%28Europe%29%20%28Disc%201%29%20%28Runtime%20Environment%29.iso |
| **Software Packages Disc 2 (Japan) ISO** | Package disc | https://archive.org/download/linux-for-playstation-2/Linux%20for%20PlayStation%202%20-%20Release%201.0%20%28Japan%29%20%28Disc%202%29%20%28Software%20Packages%29.iso |
| **Beta Release 1 ISO** | Early kit | https://archive.org/download/linux-for-playstation-2/PS2%20Linux%20Beta%20Release%201%20%28Japan%29%20%28En%2CJa%29.iso |
| **Linux Kit handbook (HTML)** | Hardware / EE / IOP overview | https://ps2-linux.tensioncore.com/download/p2lsd/p2lkit-handbook.html |
| **Unofficial VU FAQ** | VU0/VU1 programming notes | https://ps2-linux.tensioncore.com/download/p2lsd/ps2vufaq.html |

---

## Homebrew / community (GitHub — no login for public zips)

| Name | What it is | URL |
|------|------------|-----|
| **ps2dev meta** | Install scripts + release binaries | https://github.com/ps2dev/ps2dev/archive/refs/heads/master.zip · releases: https://github.com/ps2dev/ps2dev/releases |
| **ps2sdk** | Core open SDK | https://github.com/ps2dev/ps2sdk/archive/refs/heads/master.zip |
| **ps2sdk-ports** | Ported libs | https://github.com/ps2dev/ps2sdk-ports/archive/refs/heads/master.zip |
| **gsKit** | GS graphics library (+ dmaKit) | https://github.com/ps2dev/gsKit/archive/refs/heads/master.zip |
| **ps2toolchain** | ee-gcc / iop-gcc build scripts | https://github.com/ps2dev/ps2toolchain/archive/refs/heads/master.zip |
| **ps2-packer** | Packed ELF tool | https://github.com/ps2dev/ps2-packer/archive/refs/heads/master.zip |
| **ps2client** | Host↔PS2 loader | https://github.com/ps2dev/ps2client/archive/refs/heads/master.zip |
| **openvcl** | Open VU Command Line preprocessor | https://github.com/ps2dev/openvcl/archive/refs/heads/master.zip |
| **Open-PS2-Loader** | OPL (CDVD IOP reference) | https://github.com/ps2homebrew/Open-PS2-Loader/archive/refs/heads/master.zip |
| **ps2sdk HTML docs** | Generated API docs (browse online) | https://ps2dev.github.io/ps2sdk/ |

---

## Middleware / docs extras

| Name | What it is | URL |
|------|------------|-----|
| **Alchemy Kit (5.0-era eval)** | Intrinsic Alchemy eval + docs — **CNK concepts only**, not PS2 3.0 | https://archive.org/download/alchemy-kit/AlchemyKit.zip |
| **Alchemy Docs zip** | Docs pack | https://archive.org/download/alchemy-kit/Alchemy_Docs.zip |
| **Alchemy torrent** | Whole alchemy-kit item | https://archive.org/download/alchemy-kit/alchemy-kit_archive.torrent |
| **Alchemy Maya artist pack** | Artist tools installer | https://archive.org/download/alchemy-kit/Alchemy25-ArtistPackMaya-030218.exe |
| **GOB tools** | Small GOB utilities | https://archive.org/download/alchemy-kit/GOBtools.zip |
| **PS2Tek** | EE/IOP/BIOS/CDVD hardware notes (online) | https://israpps.github.io/ps2tek/ |
| **psdevwiki PS2** | Memory maps / subsystem wiki | https://www.psdevwiki.com/ps2/ |
| **Official SDK version table** | Chronology of Sony RTL versions | https://www.retroreversing.com/ps2-official-sdk |
| **ProDG 3.01 mirror notes** | Installer layout / GCC paths | https://github.com/AngheloAlf/SN-Systems-ProDG_for_PS2_3.01 |

---

## Suggested curl one-liners (caller → `E:\AI games`)

```powershell
$dir = 'E:\AI games\ps2-sdk'
New-Item -ItemType Directory -Force -Path $dir\official,$dir\homebrew,$dir\docs,$dir\linux-kit,$dir\middleware | Out-Null

# Priority
Invoke-WebRequest -Uri 'https://github.com/ps2dev/ps2dev/releases/download/v2.0.0/ps2dev-windows-latest.tar.gz' -OutFile "$dir\homebrew\ps2dev-windows-latest.tar.gz"
Invoke-WebRequest -Uri 'https://github.com/ps2dev/ps2sdk/archive/refs/heads/master.zip' -OutFile "$dir\homebrew\ps2sdk-master.zip"
Invoke-WebRequest -Uri 'https://github.com/ps2homebrew/Open-PS2-Loader/archive/refs/heads/master.zip' -OutFile "$dir\homebrew\Open-PS2-Loader-master.zip"
Invoke-WebRequest -Uri 'https://archive.org/download/PlayStation2July2005SDKversion3.0.3/PlayStation%202%20July%202005%20SDK%20%28version%203.0.3%29.iso' -OutFile "$dir\official\PS2-SDK-3.0.3.iso"
Invoke-WebRequest -Uri 'https://archive.org/download/ps-2-programmer-tool-runtime-library-controller-library/PS2%20Programmer%20Tool%20Runtime%20Library%20-%20Controller%20Library.pdf' -OutFile "$dir\docs\libpad-1.5.pdf"

# Bulk official pack via torrent (recommended for the rest of ps2_sdks)
Invoke-WebRequest -Uri 'https://archive.org/download/ps2_sdks/ps2_sdks_archive.torrent' -OutFile "$dir\official\ps2_sdks_archive.torrent"
```

---

## Login / paywall / not publicly grab-able (skip)

| Name | Why skipped | Notes |
|------|-------------|-------|
| **Sony ps2-pro.com / SCE DevNet** | Licensed developer portal (dead / account-gated) | Historical source of RTL updates |
| **Modern PlayStation partner SDK portals** | Login + NDA | Not usable for this project |
| **Alchemy 3.0 PS2 full SDK** | No public direct download found | Only 5.0-ish eval on IA; private RE repos / “don’t ask” tools |
| **Private Reddit / gated Alchemy 3.0 RE trees** | Approval / invite | Tracked separately in MASTER-CONTEXT |
| **Physical PS2 Linux Kit HDD+Ethernet** | Hardware purchase | ISOs above are software-only |
| **ASSEMBLERgames attachment threads** (e.g. older 3.0 / 3.0.2 7z shares) | Forum login often required for attachments | Prefer IA 3.0.3 ISO instead — it supersedes incomplete 3.0/3.0.2 leaks |
| **Commercial SN / Metrowerks storefronts** | Payment (defunct) | Use Archive.org dumps above |

---

## Not found as a free direct file (as of this pass)

- **Sony RTL 3.1.0** complete disc — referenced as last version; no clean IA ISO found (use **3.0.3** + **ps2sdk** which cites 3.1.0 module lineage).  
- **Sony RTL 3.0.0 / 3.0.2** complete public ISO — circulates on forums behind login; **3.0.3** is the open complete grab.  
- **BlackRhino** full ISO mirror — project page exists; no single verified bulk direct link located this pass (Linux Kit ISOs cover kit software).

---

## Priority reminder

1. ps2dev Windows + ps2sdk + OPL  
2. SDK **3.0.3** ISO + libpad PDFs  
3. `ps2_sdks` torrent (ProDG/CW/RTL 2.0/sound/pad tooling)  
4. Alchemy kit only for CNK  
5. Linux Kit last
