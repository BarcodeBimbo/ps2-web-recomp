# PS2 BIOS zip research (restarted worker)

Source: [BIOS zip hybrid research](fd25ff9e-5495-46a3-90ba-40817fa4c8a2). No code changes. BIOS stays user-local; do not copy into the repo.

## Verdict

Use BIOS as a **behavioral reference / offline oracle** for HLE contracts (CDVD completion, SIF end, WaitSema fidelity). Do **not** execute retail BIOS in-browser.

## Sets in zip (`e:\AI Browser Games\ps2-bios-usa.zip`)

| Set | Version | Prefer for |
|---|---|---|
| SCPH-39001 | 1.60 BIN | Early fat diffs |
| **SCPH-70012** | 2.00 BIN | **Best default** mid-gen contracts |
| **SCPH-77001** | 2.20 ROM0(+ROM1) | Matches stub `ROMVER` era |
| SCPH-90001 | 2.30 | Late; real NVM dump |

Ignore `__MACOSX/` and **`.DIFF`** (~99.94% zeros — packaging junk).

## High-leverage HLE teaches (cross-game)

1. cdvdfsv read completion (readee + curReadPos + sync wake) — R3  
2. SIF RPC end — R1  
3. WaitSema / iSignalSema — R2  

Does **not** unpark CNK Alchemy/IGFILEIO by itself.
