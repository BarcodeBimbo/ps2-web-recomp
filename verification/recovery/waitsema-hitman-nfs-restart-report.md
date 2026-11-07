# WaitSema leftovers — Hitman BM + NFS MW (restarted worker)

Source: [Map Hitman/NFS WaitSema leftovers](f68b4c09-ab7a-4beb-be4c-06ac3f1d97f9). No code changes. Sly was not handled here.

## Bottom line

Both titles draw at 2k frames. Leftovers are side-thread parks; SIF queue drained. Sema **2** on both = early durable CreateSema / libcdvd-class parking (ID coincidence), not CNK Alchemy. Hitman **7** and NFS **17/23/29/30/32** = per-game private.

## Recommended next (matches sprint fix order)

1. Observe-only CreateSema trace (id, init_count, max, RA)
2. Under-load SIF end contract assert
3. Harden cdvdfsv readee + curReadPos before complete_call (prove-before-swap)
4. Per-game private semas last — never CNK host_signal hacks
