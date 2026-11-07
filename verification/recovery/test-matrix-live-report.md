# Test-matrix live report

Updated: 2026-11-06 ~21:41 local

## Gate cycle 1 — FAIL

Disc-fix proposed `R3_generic_complete_path` (cdvdfsv/cdvd complete path + optional sceCdSync wake). Matrix **rejects apply**.

### Why fail

1. **Prove-before-swap:** R1 (SIF end) and R2 (WaitSema fidelity) are still gated. R3 must not land first.
2. **Bundled R4:** the same proposal also wants IOP `sceCdSync` waiter wake — that is R4, also locked.
3. **No patch yet:** `files_touched` is empty; matrix did not ask disc-fix to land anything.

### What evidence got right (real)

| Check | Hitman | NFS |
|-------|--------|-----|
| Draws / frame limit | 600f, ~128k prims (evidence) / ~78k (matrix smoke) | 600f, ~208k / ~50k |
| Menu / assets | BOOTMENU / ERRORMES searches | IOPRP + stream reads |
| CDVD complete path | N-cmd + stream writes | N-cmd + stream writes |
| WaitSema false Alchemy pulse | none | none |
| Shared leftover | sema **2** (+7) | sema **2** (+17/23/29/30/32) |
| Hitman sceCdSync/Status spam | ~1.8k each | little/none |

Independent smokes: `logs/matrix-hitman-600.log`, `logs/matrix-nfs-600.log`.

### Sony-tied gaps still open

- Logs do **not** show `curReadPos` / `readee` write-back (gap is claimed, not proven).
- Weird huge N-cmd counts still appear (contract smell).
- Leftover WaitSema piles remain after 600f.

### Phase score (current tree, both games)

boot → menu → first_disc_read → streaming → sustained_run: **pass** on smoke behavior (prims move, disc reads complete, no Alchemy). That does **not** unlock ranked rewrites out of order.

### Ranked rewrite locks

- R1 SIF end — still gated  
- R2 WaitSema fidelity — still gated  
- R3 readee — **blocked** (this proposal)  
- R4 CdSync — **blocked** (bundled)  
- R5 pad/sound — still gated  

### Next for disc-fix

Post **R1 SIF-end** (or clear R1 with real evidence) before any cdvdfsv readee/curReadPos rewrite. Do not touch CNK Alchemy paths. No commit.

### Matrix posture

Watching board again for the next `proposed_change`.

---

## Gate cycle 2 — PASS (R1 clear, no code)

Disc-fix proposed `R1_clear_with_evidence`: clear the R1 SIF-end lock from drain evidence only. No sif.cpp rewrite. No binary change.

### Verified

| Log | Frames | Prims | Final SIF | Held RPC | Alchemy |
|-----|--------|-------|-----------|----------|---------|
| matrix-hitman-600 | 600 | 78118 | 0 packets wait (processed 0) | 0 | none |
| matrix-nfs-600 | 600 | 49750 | 0 packets wait (processed 1) | 0 | none |
| discfix-hitman-bm-600-hle | 600 | 127974 | 0 packets wait | 0 | none |
| discfix-nfs-mw-600-hle | 600 | 208253 | 0 packets wait | 0 | none |

Mid-run lines sometimes show 1 packet waiting; all four runs finish drained. Board claims match the logs.

### Ranked rewrite locks now

- R1 SIF end — **cleared_with_evidence** (not the active Hitman/NFS blocker)
- R2 WaitSema fidelity — still gated (leftover sema 2 stays observe-only; never host_signal(2))
- R3 readee — still gated (may be proposed next, unbundled, no CdSync wake)
- R4 CdSync — still gated
- R5 pad/sound — still gated

### Apply / commit

`allow_discfix_apply`: **true** for this no-code clear only. Nothing to land in tree. No commit.

### Context (not blocking)

CNK ELF/Alchemy reports at `cnk-elf-alchemy-full-redo-report.md` and `alchemy-sdk-research-report.md`. Quarantine holds — those tracks stay off Hitman/NFS.

### Next

Disc-fix may post an **unbundled R3** (readee + curReadPos only). R2 remains gated; do not bundle R4 sceCdSync wake.

