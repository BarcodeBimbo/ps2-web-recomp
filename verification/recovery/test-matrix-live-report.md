# Test-matrix live report

Updated: 2026-11-06 ~21:37 local

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
