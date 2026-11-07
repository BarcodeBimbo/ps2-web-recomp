# Hitman — revert XYOFFSET 11-bit → 16-bit 12.4 (2026-11-07)

## Why

Earlier “11-bit OFX/OFY” matched **DISPFB.DBX** width, not GS `XYOFFSET`. Live Hitman `xy=0x720000007000`:

| Decode | OFX | OFY |
|--------|-----|-----|
| 11-bit (wrong) | 0 px | 32 px |
| 16-bit 12.4 (GS manual) | **1792 px** | **1824 px** |

Post-XYOFFSET capture batch 56: sprite box `1792,1792–2304,2240` with PRIM type **6**. Under 16-bit OFX that is exactly **0..512 × 0..448** (full-screen clear). Under 11-bit it sits entirely outside the 512×448 scissor → clears never land; canvas stays near-black despite huge prim counts.

Both FBP 288 and 400 PPMs were ~0.9 mean lum / ~0.9% nonzero with **identical** sparse color histograms — consistent with misplaced points, not a DISPFB↔FRAME compose-only failure.

## Change

`runtime/src/gs/gs.hpp` `xyoffset_component`: mask `0xFFFF` + `int16_t` (16-bit 12.4), not `0x7FF`.

## Verify next

Native `ps2run` smoke with `disc.iso` → PPM / harness lum; then web rebuild under Hitman lock (do not kill in-flight builds).
