# Worker w3 resume — CNK null-bind `51ACEC` (2026-11-07)

**GID:** `b49f2e769315347e8bda839feb705744`  
**Mode:** OBSERVE ONLY — no CNK Alchemy patches (no host_signal 16/54/55, soft-arm edits, FCE0 force, virt-LBA, +24008). Quarantined from Hitman/NFS.

## Re-ack

`*0x725F50` → jalr **vt+80** → if null `v0` → jalr **vt+84** via `*(0)` → PC0, **`ra=0x51ACEC`**. Soft-arm still **prims=2**.

## Done this resume

- Offline **live vtable dump** from existing `logs/ram/cnk-*.ram` (no new host run, no patch).
- Registry vt `0x6DF110`: vt+80=`0x53B940`, vt+84=`0x53BA50` (non-null when installed).
- Forced-FCE0 crash remains **tid map miss** (`r2=0`), not empty method slots.
- Updated: `verification/recovery/cnk-nullbind-51ACEC-live-report.md` (RESUMED section).

## Next (still observe / diagnostic-only)

1. Prefer guest parse on tid **1** or **4** (map owners); do not host-force FCE0 from `g_current==0`.
2. Optional future mid-site log at `0x51ACCC→0x51ACD4` — **requires explicit diagnostic instrumentation approval**; do not sneak in via Alchemy host_signal/soft-arm/FCE0 patches.
3. Gate red until `prims >> 2` without null jalr.

## Return blob

```
{worker:w3, status:resumed_observe, prims_note:still_2, vtable_dump:done, resume_file:verification/recovery/worker-resume-cnk-nullbind-w3-2026-11-07.md}
```
