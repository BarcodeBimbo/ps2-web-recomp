# Owner follow-up — compose research + NFS (2026-11-07)

## Merged workers

| Worker | Verdict | Action taken |
|--------|---------|--------------|
| [W-HITMAN-compose](f858f950-e5e1-410c-9cef-3161ee7cb882) | **(B)** sprite/tex; defer host blit | Agreed; XYOFFSET already 16-bit; PRIM type7 probe below |
| [W-NFS](d687f486-1771-4f45-8cd9-0605050a2363) | Chrome hitch = web disc prefetch | Spawned [W-NFS-2](c0ba844b-8f75-46a4-8af0-2122dc0e19b1) to implement `host/web.cpp` prefetch |

## PRIM type 7 probe (Hitman)

- 513 batches are type **7** (`0x07F`×363, `0x7FF`×150); CPU/GPU `default` previously **dropped** them.
- Capture `n≈2` looked sprite-like, but mapping **7→sprite** wiped present FB (paired verts → huge black quads); lum 0.11→0.00.
- Mapping **7→point** restores baseline lum (~0.11) and keeps kicks; not the black-canvas root cause alone.

## Still open (Hitman)

Mesh/tex fill after correct 16-bit clears; web-next rebuild in flight for XYOFFSET+type7point (`build/web-a2116…-next`, ~90/931).
