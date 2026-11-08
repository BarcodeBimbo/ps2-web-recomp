# PS2 recomp/decomp GitHub map (read-only) — 2026-11-07

Source: research worker [PS2 recomp/decomp GitHub research](ba1da034-1f6a-4257-928b-9e85aea67a49). Stars/dates approximate from public indexes.

## Campaign / tabgames overlap (primary)

| Game | Repo | Type | Activity | Blocker relevance |
|------|------|------|----------|-------------------|
| Ratchet & Clank 1 | [OpenRAC/rac1-decomp](https://github.com/OpenRAC/rac1-decomp) | Matching decomp | Active Nov 2026 | Overlays/assets |
| Ratchet & Clank 1 | [lombyte-project/Lombyte](https://github.com/lombyte-project/Lombyte) | Matching decomp | Active | NTSC-U |
| Ratchet series PC | [OpenRAC/OpenRAC](https://github.com/OpenRAC/OpenRAC) | Native from decomp | Active | Disc assets at runtime |
| Ratchet 1 recomp | [vetusmagnus/project-solana](https://github.com/vetusmagnus/project-solana) | Static recomp + host | Active | **GS/VU/DMA/disc** |
| Going Commando+ | [OpenRAC/rac2-decomp](https://github.com/OpenRAC/rac2-decomp) (+ rac3/rac4) | Matching decomp | Active | Series |
| Midnight Club 3 Remix | [siddharthakumar-98/MC3DER](https://github.com/siddharthakumar-98/MC3DER) | Decomp→Rust | Early | Weak PS2 MC3 otherwise |
| MC3 (Xbox) | [laureladastra/mcdub3-nx](https://github.com/laureladastra/mcdub3-nx) | Xbox static recomp | Active | Not PS2 EE |
| TimeSplitters 1 | [GTTeancum/Timesplitters](https://github.com/GTTeancum/Timesplitters) | Static recomp | v1.0 Oct 2026 | **OpenGL GS, VU→C++** |
| Silent Hill 3 | [dreamingmoths/memory-of-alessa](https://github.com/dreamingmoths/memory-of-alessa) | Matching decomp | ~166★ | MFA assets / SH2 engine |
| Silent Hill 2 | [dreamingmoths/mirror-of-alessa](https://github.com/dreamingmoths/mirror-of-alessa) | Matching decomp | Active | |
| Def Jam Vendetta | [jcsix694/def-jam-vendetta-recomp](https://github.com/jcsix694/def-jam-vendetta-recomp) | Static recomp | Active | **paraLLEl-GS/Vulkan** |
| Def Jam Vendetta | [Cwf1997/defjamvendetta](https://github.com/Cwf1997/defjamvendetta) | Matching decomp | Dec 2025 | Early |
| FFNY Online | [sweeax-exe/ffny-online](https://github.com/sweeax-exe/ffny-online) | Xbox recomp + **online** | Active | Online lockstep; not PS2 |
| SSX 3 | [ssxdecomp/ssx3](https://github.com/ssxdecomp/ssx3) | Matching decomp | Active | `SLUS_207.72` |
| SSX 3 | [andersfischernielsen/ssx3-decomp](https://github.com/andersfischernielsen/ssx3-decomp) | AI decomp→Rust/wgpu | Active | **VU/IOP/GS draw-list** |
| CNK | [YacaloX-Studios/cnk-decomp](https://github.com/YacaloX-Studios/cnk-decomp) | Matching decomp | Early ~0% | Alchemy-adjacent |
| NFS MW (PS2) | [dbalatoni13/nfsmw](https://github.com/dbalatoni13/nfsmw) | Matching decomp | ~247★ | Render/physics; PS2 BE |
| Sly 1 | [TheOnlyZac/sly1](https://github.com/TheOnlyZac/sly1) | Matching decomp | Active | Engine/GIF/VU names |
| Sly 1 PC | [theclub654/ProjectCane](https://github.com/theclub654/ProjectCane) | Native rewrite | Playable | Assets/shaders |
| God of War | [KIexster/god-of-war-recomp](https://github.com/KIexster/god-of-war-recomp) | Static recomp | ~228★ | **VU1 AOT, OpenGL GS** |
| God of War | [Waffle565/God-Of-War-Native-Port](https://github.com/Waffle565/God-Of-War-Native-Port) | Native runtime | Active | Same stack |
| God of War | [yyozcan/tobiichi-port](https://github.com/yyozcan/tobiichi-port) / [Vnnc1/gow-native-pc](https://github.com/Vnnc1/gow-native-pc) | Static recomp | Active | Installer/IR |

## Gaps

- **Hitman Contracts/Blood Money PS2** — no public PS2 recomp/decomp
- **NBA 2K / Formula 1 PS2** — no dedicated BYO-disc repos found
- **Midnight Club 3** (non-Remix PS2) — weak coverage

## Tooling (game-tied)

- [ran-j/PS2Recomp](https://github.com/ran-j/PS2Recomp) — EE→C++ used by many ports
- [snuri00/ps2-web-recomp](https://github.com/snuri00/ps2-web-recomp) — EE→WASM WebGPU (related class)
