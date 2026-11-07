# Alpha test finding — ATE on, GREATER than 2

## Live TRACE (present-time drawenv)

From `PS2_TRACE_DISPLAY` during native Hitman (~frame present):

```
[gs] present fb: dispfb=400 frame0=288 frame1=400 last_ctx=0 fbw=8 psm=0
[gs] drawenv0 xy=0x720000007000 sc=0x1BF000001FF0000 test=0x5002D alpha=0x0
             frame=0xFF00000000080120
[gs] drawenv1 xy=0x0 sc=0x1BF000001FF0000 test=0x20000 alpha=0x800000002A
             frame=0xFF00000000080190
```

### Decode `test = 0x5002D` (ctx0 — primary draw)

| Field | Bits | Value | Meaning |
|-------|------|-------|---------|
| ATE   | 0    | **1** | Alpha test **enabled** |
| ATST  | 1–3  | **6** | **GREATER** |
| AREF  | 4–11 | **2** | Reference **2** |
| AFAIL | 12–13| **0** | KEEP (fail → no FB/Z update) |
| ZTE   | 16   | 1     | Z test on |
| ZTST  | 17–18| 2     | GEQUAL |

**Rule:** fragment passes only if **A > 2**. Otherwise AFAIL=KEEP → **no framebuffer write**.

### Ctx1 (display-adjacent / clear-style)

- `test = 0x20000` → ATE **off**, Z disabled path used in clear setup
- `alpha = 0x800000002A` — blend formula used on that context

## Capture histogram (`01c-TRACE-draws-frame180.tsv`)

Around frame 180 (`PS2_CAPTURE=180,…`):

| TEST value | Count | Notes |
|------------|------:|-------|
| `0x5002D`  | 260 | Dominant draw path — **ATE GREATER 2** |
| `0x20000`  | 108 | Clear / no ATE |
| `0x30000`  | 3   | Init-style Z-always, ATE off |

FRAME targets:

| FRAME | Count | FBP |
|-------|------:|-----|
| `…80120` | 261 | **288** (draw) |
| `…80190` | 108 | **400** (matches DISPFB) |

## ELF context

- Init packet (`FUN_0028f2c4`) sets TEST to `0x30000` (ATE off).
- Clear path (`FUN_0029435c` / `FUN_0028f7fc`) uses TEST `0x20000` and clear color **0** (black) from `FUN_00291710(..., 0)`.
- Live UI/draw path elevates to `0x5002D` — that is **not** in the CRT init packet; it comes from later draw-context setup (engine).

## Implication

Alpha reject is a **leading** explanation for “prims without pixels” **if** fragments carry A≤2 (common with TEXA / missing tex alpha).  
Counter-evidence still in play: some captured batches with `test=0x30000` / full-screen boxes also left FBP 288 PPM **pure black** — so ATE is necessary but maybe not sufficient; continue loop on UV/tex and compose-to-400.
