# Live matrix 2026-11-07

**Toward matrix 100%:** **90.0%** (36/40 checks)
**Board:** cycle 8 R5 observe PASS
**Scorer fix:** bare `FCE0` substring removed — `attr=0x1FFFCE0` no longer false-Alchemy; UTF-16 log read fixed
**Log dir:** `logs/live-matrix-2026-11-07/`

## Native smoke table

| Game | ID | Boot | Past loader | Frames | Prims | FPS host | Crash | Note |
|------|----|------|-------------|--------|-------|----------|-------|------|
| GoW_USA | 695b874b | YES | YES | 900 | 11600480 | 107.6 | — | — |
| GoW_II | 34402ee3 | YES | YES | 900 | 4989882 | 25.9 | — | — |
| CNK | b49f2e76 | YES | YES | 3000 | 2 | 1,592.1 | — | alchemy_gate_prims=2; alchemy_pulses_expected |
| Hitman_BM | a2116d2a | YES | YES | 900 | 261534 | 250.9 | — | — |
| NFS_MW | 60c82f4a | YES | YES | 900 | 408728 | 376.0 | — | — |
| Sly1 | c0c45270 | YES | YES | 900 | 152786 | ~300 | — | wall~3s/900f |

## Play URLs (panel :8620)

- **GoW_USA:** http://127.0.0.1:8620/play/695b874b308a4e5353767bb6df8ba697/
- **GoW_II:** http://127.0.0.1:8620/play/34402ee3c1917272f971028b4fb24868/
- **CNK:** http://127.0.0.1:8620/play/b49f2e769315347e8bda839feb705744/
- **Hitman_BM:** http://127.0.0.1:8620/play/a2116d2ac08a7be4db4e8455ad58d2e5/
- **NFS_MW:** http://127.0.0.1:8620/play/60c82f4a111da300ac23bbec85272788/
- **Sly1:** http://127.0.0.1:8620/play/c0c4527037b6168660829a0eb13df1a3/

## Hitman / NFS five-phase (scorer)

### Hitman_BM — verdict **pass** (alchemy=False)

| Phase | Result |
|-------|--------|
| boot | pass |
| menu | pass |
| first_disc_read | pass |
| streaming | pass |
| sustained_run | pass |

### NFS_MW — verdict **fail** (alchemy=False)

| Phase | Result |
|-------|--------|
| boot | pass |
| menu | pass |
| first_disc_read | fail |
| streaming | fail |
| sustained_run | fail |

## FPS evidence

- Native host FPS in table (prior run timing; Sly ~3s wall / 900f).
- Panel play URLs listed; Chrome automation not forced.
- No FPS overlay screenshot this cycle — evidence is stderr frame-limit + prims in `*.log`.
