# R3 — readee / AlignReadBuffer compliance (research only)

**Track:** A · R3  
**SDK root:** `E:\usr\local\sce`  
**Runtime:** `runtime/src/iop/cdvdfsv.cpp` `read_to_ee` (~L49–236) — **READ ONLY; no patch**  
**Product status (matrix):** R3 **`verified_apply`** — b1len/b2len when dest fed; unaligned head/tail at +16/+80

---

## MASTER next action — Device Reference deep-read (AlignReadBuffer / readee)

**Finding:** The symbol **`AlignReadBuffer` / `_CdAlignReadBuffer` does not appear** in:

- Public `E:\usr\local\sce\common\include\libcdvd.h` (no AlignReadBuffer declaration)
- `_sdk_pdf_extract/PS2_EE-Reference-Device-3.0.3.pdf.txt` (no symbol by that name)
- `_sdk_pdf_extract/PS2_IOP-Reference-Device-3.0.2.pdf.txt`
- SDK tree `*.{c,h}` grep under `E:\usr\local\sce`

Sony documents the **behavior** as internal EE-side **alignment compensation**, not as a public API:

| Doc | What it says |
|-----|----------------|
| EE Device Ref 3.0.3 · `sceCdRead` Notes | “When data is transferred to the EE, sometimes the library will **adjust the alignment** of the buffer address.” Prefer **64-byte** alignment. |
| EE Device Ref · `sceCdGetReadPos` | Progress in bytes; **because of alignment adjustment**, non-64-byte-aligned buffers need care on the last transfer (edges of the buffer). Returns 0 when read terminates. |
| `cdvdtips_3.0` | If buffer is not 64-byte aligned, `sceCdRead` performs **compensation processing internally**; use `memalign(64,…)` / `aligned(64)`. Case study: unaligned buffers cost ~22% more time. |
| EE Device · `sceCdSetEEReadMode` | EE↔IOP read issue modes (NoCheckReady / NoWriteBackDCache) — related EE read path, not the readee block layout. |

**Implication for MASTER:** treat **`_CdAlignReadBuffer` as EE libcdvd private** (observed in titles / retail cdvdfsv naming). Compliance is against Device PDF **alignment-adjustment + GetReadPos** contract and the **IOP→EE readee staging layout** that private callback consumes — not against a public header symbol.

### Inferred readee / `_rd_intr_data` layout (product + retail naming)

IOP `cdvdfsv` writes EE-side interrupt/read staging (`eeaddr1` / readee), then EE callback copies using lengths/dests:

| Offset | Field (product names) | Role |
|--------|----------------------|------|
| +0 | b1len | Byte count for dest1 / head fragment |
| +4 | b2len | Byte count for dest2 / tail fragment |
| +8 | dest1 | EE copy-out target 1 |
| +12 | dest2 | EE copy-out target 2 |
| +16 | head payload | Up to ~64B head fragment for unaligned start |
| +80 | tail payload | End-misaligned tail bytes |
| (size) | ~144B zeroed block | Product clears then restores dests |

`eeaddr2` = **curReadPos** (byte count for `sceCdGetReadPos` progress).

Public API surface remains: `sceCdRead` / `sceCdSync` / `sceCdGetReadPos` / `sceCdCallback` in `libcdvd.h` L270–282.

---

## Product status (`read_to_ee` ~L49–236)

| Step | Behavior |
|------|----------|
| Payload | Disc/virt sectors → `write_dst` (caller bounce) |
| eeaddr1 | Preserve dest1/dest2; memset ~144B; restore dests |
| Fed dest | If dest1/dest2 valid: memcpy payload → dest; set **b1len/b2len = nbytes** |
| Unaligned | If no fed dest and `dst & 0xF`: stage head at +16, optional tail at +80; set lengths |
| eeaddr2 | Write `nbytes` for curReadPos |
| Order | Comments: payload + readee + curReadPos, then complete (matches Sony “progress then sync/callback” flow) |

Post-apply smoke: Hitman unaligned `dst=0x52C098 head=8 tail=8` (`DISCFIX-R1-R4-STABLE.md`).

---

## Match flags

| # | Item | Verdict |
|---|------|---------|
| M1 | Non-64B-aligned EE buffers need IOP/EE compensation path | **MATCH** Device Ref + tips (product stages readee fragments) |
| M2 | curReadPos / GetReadPos byte progress updated during/after transfer | **MATCH** intent (`eeaddr2 = nbytes`) |
| M3 | b1len/b2len non-zero when dests fed | **MATCH** private AlignReadBuffer contract (R3 harden) |
| M4 | Public `libcdvd.h` has no AlignReadBuffer | **MATCH** Sony public surface (deviation would be exposing a fake public API) |

---

## Deviation flags (observe-only)

| # | Item | Severity | Notes |
|---|------|----------|-------|
| D1 | Virt LBA plant / Alchemy stream-sector host assemble (`sector >= 0xF0000000`) | **CNK quarantine** | Not part of Sony Device contract; must stay off Hitman/NFS generic path. |
| D2 | Host-side dest1 fill when EE already staged dest | medium/research | Product may pre-copy into dest before EE callback; hardware relies on EE AlignReadBuffer. Works for verified Hitman unaligned path; keep observe if a title double-copies. |
| D3 | Exact 144B / +16 / +80 layout not in public PDFs | doc gap | Derived from retail cdvdfsv / title RE; MASTER should keep Device PDF alignment text as normative *behavior*, layout as *implementation evidence*. |
| D4 | `sceCdGetReadPos` doc: progress in **16-sector units (32768)** wording vs “size in bytes” return | SDK ambiguity | Product writes raw byte count; sample polls `sceCdGetReadPos` during `sceCdSync(1)`. Flag if a title assumes 32KB quanta only. |

---

## Evidence paths

- Runtime: `runtime/src/iop/cdvdfsv.cpp` L49–236 (`read_to_ee`)  
- Public header: `E:\usr\local\sce\common\include\libcdvd.h` (no AlignReadBuffer; `sceCdGetReadPos` / `sceCdRead`)  
- Extracts:  
  - `PS2_EE-Reference-Device-3.0.3.pdf.txt` (`sceCdRead` align note; `sceCdGetReadPos` ~2-27)  
  - `cdvdtips_3.0.pdf.txt` (64-byte alignment compensation)  
- Smokes / board: `DISCFIX-R1-R4-STABLE.md`, `test-matrix-live-report.md` (R3 verified_apply)

---

## No-patch

Research audit only. R3 behavioral change already landed under matrix gate; **this track does not modify** `cdvdfsv.cpp` further.
