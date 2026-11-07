# Test-matrix live report

Updated: 2026-11-07 (~07:40) — TARGET 2 live matrix + scorer fix

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


---

## Gate cycle 3 — FAIL (R3 blocked by R2)

Disc-fix proposed `R3_readee_length_harden`: unbundled readee length harden in `cdvdfsv.cpp` only. No R4. No WaitSema rewrite. No CNK. Diag-only logs already in tree; behavioral patch not applied.

### Why fail

**Prove-before-swap:** R1 is cleared, but **R2 WaitSema fidelity is still gated**. Any R3 *code* change stays locked until R2 is cleared (same rule as cycle 1 — order is R1 → R2 → R3). Unbundled is good; skipping R2 is not.

### Evidence spot-check (not enough to unlock)

| Check | Result |
|-------|--------|
| Hitman curReadPos exact | 35/35 in `discfix-hitman-curpos-300.log` |
| NFS curReadPos exact (regex) | 45/60 in `discfix-nfs-curpos-300.log` |
| Hitman unaligned dst `0x52C098` | present |
| Alchemy / host_signal(2) | none |
| R4 sceCdSync wake bundled | no |

Five-phase smoke was **not** re-run this cycle — ranked order failed before apply. Prior 600f phase passes still stand.

### Ranked locks now

- R1 — cleared_with_evidence
- R2 — **still_gated** (next clear target)
- R3 — **blocked_until_R2_clear**
- R4 / R5 — still gated

`allow_discfix_apply`: **false**. Do not land readee-length harden yet.

### Next for disc-fix

Post **`R2_clear_with_evidence`** (observe-only, like R1). Ownership report already shows sema 2 = durable libcdvd-class parking — never `host_signal(2)`. After that passes, re-post unbundled R3.

### Matrix posture

Watching board for the next `proposed_change`.


---

## Gate cycle 4 — PASS (R2 clear, no code)

Disc-fix proposed `R2_clear_with_evidence` right after cycle-3 fail (as requested). Observe-only clear. No WaitSema rewrite. No `host_signal(2)`.

### Verified

| | Hitman | NFS |
|--|--------|-----|
| Log | waitsema-createsema-hitman-2k | waitsema-createsema-nfs-2k |
| Frames / prims | 2000 / 586246 | 2000 / 1153253 |
| Sema 2 create | once, init=0 max=255, ra `0x001038CC` | once, init=0 max=255, ra `0x00495EA8` |
| Sema 2 delete | 0 | 0 |
| End dump | waiters 1, same create_ra | waiters 1, same create_ra |
| SIF end | 0 packets wait | 0 packets wait |
| Alchemy | none | none |

Sema 2 = durable libcdvd-class parking (ID coincidence across titles). Not a missing CDVD wake. Blind pulse would be wrong.

### Ranked locks now

- R1 — cleared_with_evidence
- R2 — **cleared_with_evidence**
- R3 — **unlocked_for_unbundled_proposal** (re-post length-harden; still no R4)
- R4 / R5 — still gated

`allow_discfix_apply`: **true** for this no-code clear only. Nothing to land. No commit.

### Next for disc-fix

Re-post **unbundled `R3_readee_length_harden`** (readee lengths only; no sceCdSync wake). Matrix will then run five-phase smokes before allowing the behavioral patch.

### Matrix posture

Watching board for the R3 re-post.


---

## Gate cycle 5 — PASS (unbundled R3 allowed to apply)

Disc-fix re-posted `R3_readee_length_harden` after R1+R2 clears. No R4. No WaitSema rewrite. No CNK.

### Prove-before-swap

R1 and R2 are cleared_with_evidence → unbundled R3 code change is allowed.

### Five-phase pre-apply smokes

| Game | Log | Frames | Prims | Disc | SIF end | Alchemy | Phases |
|------|-----|--------|-------|------|---------|---------|--------|
| Hitman | matrix-c5-hitman-600 | 600 | 78118 | 19 searches / 288 streams | 0 wait | none | all pass |
| NFS | matrix-c5-nfs-600 | 600 | 49750 | 67 streams | 0 wait | none | all pass |

Leftover WaitSema 2 remains (durable parking — OK).

### Apply

`allow_discfix_apply`: **true**. Disc-fix may land readee length harden in `cdvdfsv.cpp` only (b1len/b2len + unaligned head/tail). Do **not** add sceCdSync wake. Do **not** pulse semas. No commit until post-apply verify is green.

### Ranked locks now

- R1 / R2 — cleared
- R3 — **allowed_apply_pending_verify**
- R4 / R5 — still gated

### Next

Disc-fix applies the patch, then posts verify evidence (or matrix will re-smoke both games).


---

## Gate cycle 6 — PASS (R3 post-apply verified)

Disc-fix applied unbundled readee-length harden and posted `R3_post_apply_verify`.

### Verified

| | Hitman (`discfix-r3-hitman-600`) | NFS (`discfix-r3-nfs-600`) |
|--|--|--|
| Frames / prims | 600 / 127974 | 600 / 208253 |
| Unaligned readee | `dst=0x52C098 head=8 tail=8` | n/a this run |
| curReadPos exact | 35/35 | continues matching |
| SIF end | 0 packets wait | 0 packets wait |
| Alchemy | none | none |
| Five phases | all pass | all pass |

R4 not unlocked. No sceCdSync wake. No `host_signal(2)`.

### Ranked locks now

- R1 / R2 / R3 — cleared / verified
- R4 CdSync — still gated
- R5 pad/sound — still gated

`allow_discfix_apply`: **false** (verify-only). Joint commit OK when disc-fix is ready.

### Matrix posture

Watching for any next proposal (R4 only if separately posted).


**Alive ~22:10:** Cycle 6 PASS confirmed on board; R4/R5 still gated; watching for next proposed_change.


---

## Gate cycle 7 — PASS (R4 clear, no code)

Disc-fix proposed `R4_clear_with_evidence`. No `cdvd.cpp` wake. No `host_signal(2)`.

Post-R3 five-phase still green (Hitman 600f/127974; NFS 600f/208253; SIF 0). Hitman `sceCdSync` is ~1854 mode=1 polls vs ~10 mode=0 — not a stuck blocking-waiter case. NFS has little/no sync spam. Leftover sema 2 stays durable parking.

**Ranked now:** R1/R2/R4 cleared_with_evidence; R3 verified_apply; **R5 still gated**.

`allow_discfix_apply`: true for this no-code clear only. Matrix did not unlock R4 preemptively — gated the clear proposal on evidence.

**Alive:** watching for next `proposed_change` (R5 / soak / commit note).


**Alive ~22:25:** Cycle 6+7 PASS confirmed; disc-fix idle (4_pass_acknowledged); R5 still gated; no new proposed_change yet — still watching.


---

## PAUSED — Cursor reload (~2026-11-06 23:51:01 -05:00)

- Last matrix status: `watching` / verdict `pass`; `last_completed` = `R4_clear_with_evidence`; disc-fix `r4_pass_acknowledged`; `proposed_change` = null; step 7.
- Ranked: R1/R2/R4 cleared_with_evidence; R3 verified_apply; **R5 still gated**.
- Matrix did **not** unlock R5. No commits. No CNK. No `host_signal(2)`.
- Board watch **stopped** for Cursor reload (SAFE PAUSE).

---

## RESUMED — w2 idle watcher (2026-11-07)

- **RESUMED** as idle board watcher. No proposal invented. No smokes. No patches. No R5 apply.
- Board live: step **8** / `awaiting_matrix`; discfix `proposed` `R5_pad_sound_observe` (code_change false); matrix `pending`; `allow_discfix_apply` false; R5 still gated for apply.
- Differs from pause snapshot (step 7 / null proposal) — disc-fix posted observe gate while matrix was paused.
- Full note: `verification/recovery/worker-resume-matrix-w2-2026-11-07.md`.
- Awaiting: process observe gate when directed, or next disc-fix proposal / optional R5 when ungated.

---

## Gate cycle 8 — PASS (R5 pad/sound OBSERVE)

Disc-fix proposed `R5_pad_sound_observe` (`code_change: false`). Matrix **OBSERVE gate PASS**. No R5 apply. Evidence: `verification/recovery/discfix-r5-observe-matrix-2026-11-07.md`.

**Ranked now:** R1–R4 cleared/verified; **R5 still gated for apply**. `allow_discfix_apply=false`.

---

## Live matrix lane — 2026-11-07 → toward 100% (~90%)

**Log dir:** `logs/live-matrix-2026-11-07/` (`SUMMARY.md`, `summary.json`, `native-results.json`)

### Scorer fix (done)

`matrix_phase_check.py` `ALCHEMY_PULSE` no longer matches bare `FCE0` substring — Hitman `createsema attr=0x1FFFCE0` is **not** Alchemy. Standalone `0xFCE0` / `host_signal(16|54|55)` / soft-arm / virt-LBA still flag. Also reads UTF-16 Tee-Object logs.

### Native smoke table (relative `disc.iso` + `runtime-deps` PATH)

| Game | ID | Boot | Loader | Frames | Prims | FPS host | Crash | Note |
|------|----|------|--------|--------|-------|----------|-------|------|
| GoW USA | 695b874b | YES | YES | 900 | 11600480 | 107.6 | — | |
| GoW II | 34402ee3 | YES | YES | 900 | 4989882 | 25.9 | — | |
| CNK | b49f2e76 | YES | YES | 3000 | 2 | 1592.1 | — | alchemy gate |
| Hitman BM | a2116d2a | YES | YES | 900 | 261534 | 250.9 | — | five-phase **pass** |
| NFS MW | 60c82f4a | YES | YES | 900 | 408728 | 376.0 | — | five-phase fail: no `cdvdfsv` search in this log |
| Sly1 | c0c45270 | YES | YES | 900 | 152786 | ~300 | — | native exe was present; prior miss was path lookup |

**Toward 100%:** **90%** (36/40 checks) — remaining: CNK `prims=2` + NFS CDVD-search phases on this live log.

### Play URLs (panel http://127.0.0.1:8620)

- GoW USA: `/play/695b874b308a4e5353767bb6df8ba697/`
- GoW II: `/play/34402ee3c1917272f971028b4fb24868/`
- CNK: `/play/b49f2e769315347e8bda839feb705744/`
- Hitman: `/play/a2116d2ac08a7be4db4e8455ad58d2e5/`
- NFS: `/play/60c82f4a111da300ac23bbec85272788/`
- Sly: `/play/c0c4527037b6168660829a0eb13df1a3/`

FPS evidence: native stderr frame-limit + prims in `*.log` (no Chrome overlay screenshot; prefer native).

