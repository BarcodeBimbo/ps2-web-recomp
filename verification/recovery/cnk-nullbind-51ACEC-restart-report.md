# CNK null jalr @ ra=0x0051ACEC — restarted worker report

Source: [CNK null bind 0x51ACEC](20a8949c-4f93-403f-9b29-85e37d1e0877) (restart of evening research). No code changes.

## Bottom line

Forcing FCE0 / `0x110100` after soft-arm `+45` reaches live `vt+108`, then dies on a **second** virtual call: `jalr` to PC 0 with `ra=0x51ACEC`. That is `*(returned_object->vtable+84)` after lookup through `0x00725F50`. Soft-arm without host FCE0 is stable (~20k) but parse never finishes (`prims=2`). AlignReadBuffer-only is insufficient (`ee1 dest` stays 0/0).

## Safe next step (read-only)

Log `ee32(0x725F50)`, `r2` after the `vt+80` call, and key at `obj+32` one instruction before `0x51ACD4` on forced-FCE0 vs soft-arm baseline. Do **not** blind-stuff function pointers. Keep CNK quarantined from Hitman/NFS disc-fix.
