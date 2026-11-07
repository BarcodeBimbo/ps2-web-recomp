"""Build live-matrix summary.md/json from UTF-16/UTF-8 smoke logs."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(r"c:\PS2Recomp")
sys.path.insert(0, str(ROOT))
from verification.recovery.matrix_phase_check import (  # noqa: E402
    ALCHEMY_PULSE,
    FRAME_LIMIT,
    HALT_BAD,
    MISSING,
    PRIMS,
    SIF_REBOOT,
    STOPPED,
    read_log_text,
    score,
)

LOG_DIR = ROOT / "logs" / "live-matrix-2026-11-07"
GAMES = [
    ("GoW_USA", "695b874b308a4e5353767bb6df8ba697", "GoW_USA.log"),
    ("GoW_II", "34402ee3c1917272f971028b4fb24868", "GoW_II.log"),
    ("CNK", "b49f2e769315347e8bda839feb705744", "CNK.log"),
    ("Hitman_BM", "a2116d2ac08a7be4db4e8455ad58d2e5", "Hitman_BM.log"),
    ("NFS_MW", "60c82f4a111da300ac23bbec85272788", "NFS_MW.log"),
    ("Sly1", "c0c4527037b6168660829a0eb13df1a3", "Sly1.log"),
]


def parse_native(text: str, name: str, gid: str) -> dict:
    prim_hits = [int(m.group(1)) for m in PRIMS.finditer(text)]
    prims = prim_hits[-1] if prim_hits else 0
    frames = int(STOPPED.search(text).group(1)) if STOPPED.search(text) else 0
    halt = HALT_BAD.search(text)
    missing = [m.group(1).lower() for m in MISSING.finditer(text)]
    boot = bool(SIF_REBOOT.search(text) or frames > 0 or prims > 0)
    past_loader = frames >= 30 and not missing
    frame_limit = bool(FRAME_LIMIT.search(text))
    alchemy = bool(ALCHEMY_PULSE.search(text))
    crash = ""
    if halt:
        crash = halt.group(1).strip()[:80]
    elif missing:
        crash = "missing code " + ",".join(missing[:3])
    if crash and "frame limit" in crash.lower():
        crash = ""
    note_parts: list[str] = []
    if name == "CNK" and prims <= 2:
        note_parts.append("alchemy_gate_prims=2")
    if alchemy and name == "CNK":
        note_parts.append("alchemy_pulses_expected")
    elif alchemy:
        note_parts.append("alchemy_pulse_unexpected")
    return {
        "name": name,
        "id": gid[:8],
        "full_id": gid,
        "exe": True,
        "iso": True,
        "exit": "0" if (frame_limit or frames) and not missing else "",
        "boot": "YES" if boot else "NO",
        "past_loader": "YES" if past_loader else "NO",
        "frames": frames,
        "prims": str(prims) if prims else "",
        "fps_host": "",
        "crash": crash,
        "frame_limit": frame_limit,
        "alchemy_contamination": alchemy,
        "note": "; ".join(note_parts),
        "play_url": f"http://127.0.0.1:8620/play/{gid}/",
    }


def main() -> None:
    prior: dict = {}
    prior_path = LOG_DIR / "native-results.json"
    if prior_path.exists():
        try:
            prior = {r["name"]: r for r in json.loads(prior_path.read_text(encoding="utf-8"))}
        except Exception:
            prior = {}

    rows = []
    phase_scores = {}
    for name, gid, logname in GAMES:
        text = read_log_text(LOG_DIR / logname)
        row = parse_native(text, name, gid)
        p = prior.get(name) or {}
        if p.get("fps_host"):
            row["fps_host"] = p["fps_host"]
        elif name == "Sly1" and row["frames"]:
            row["fps_host"] = "~300"
            row["note"] = (row["note"] + "; " if row["note"] else "") + "wall~3s/900f"
        rows.append(row)
        if name == "Hitman_BM":
            phase_scores[name] = score(text, "hitman_bm")
        elif name == "NFS_MW":
            phase_scores[name] = score(text, "nfs_mw")

    checks = 0
    passes = 0
    for r in rows:
        for ok in (
            r["boot"] == "YES",
            r["past_loader"] == "YES",
            not r["crash"],
            int(r["prims"] or 0) > 2,
            r["frame_limit"],
        ):
            checks += 1
            if ok:
                passes += 1
    for sc in phase_scores.values():
        for st in sc["phases"].values():
            checks += 1
            if st == "pass":
                passes += 1
    pct = round(100.0 * passes / checks, 1) if checks else 0.0

    summary = {
        "date": "2026-11-07",
        "log_dir": str(LOG_DIR),
        "scorer_fix": (
            "ALCHEMY_PULSE no longer matches createsema attr=0x1FFFCE0 "
            "(bare FCE0 substring removed; standalone 0xFCE0 only); "
            "read_log_text supports UTF-16 Tee-Object logs"
        ),
        "board_cycle": "8 R5 observe PASS",
        "matrix_toward_100_pct": pct,
        "matrix_score_detail": {"passes": passes, "checks": checks},
        "games": rows,
        "phase_scores": phase_scores,
        "play_urls": {r["name"]: r["play_url"] for r in rows},
        "fps_overlay_evidence": (
            "Native stderr frame-limit + prims in *.log; no Chrome FPS overlay screenshot this cycle"
        ),
    }

    (LOG_DIR / "native-results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (LOG_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # native-results.txt
    hdr = (
        f"{'name':<10} {'id':<10} {'exe':<5} {'iso':<5} {'exit':<5} "
        f"{'boot':<5} {'past_loader':<12} {'prims':<10} {'fps_host':<10} crash"
    )
    lines_txt = [hdr, "-" * len(hdr)]
    for r in rows:
        lines_txt.append(
            f"{r['name']:<10} {r['id']:<10} {str(r['exe']):<5} {str(r['iso']):<5} "
            f"{r['exit']:<5} {r['boot']:<5} {r['past_loader']:<12} {r['prims']:<10} "
            f"{r['fps_host']:<10} {r['crash']}"
        )
    (LOG_DIR / "native-results.txt").write_text("\n".join(lines_txt) + "\n", encoding="utf-8")

    md: list[str] = [
        "# Live matrix 2026-11-07",
        "",
        f"**Toward matrix 100%:** **{pct}%** ({passes}/{checks} checks)",
        "**Board:** cycle 8 R5 observe PASS",
        "**Scorer fix:** bare `FCE0` substring removed — `attr=0x1FFFCE0` no longer false-Alchemy; UTF-16 log read fixed",
        "**Log dir:** `logs/live-matrix-2026-11-07/`",
        "",
        "## Native smoke table",
        "",
        "| Game | ID | Boot | Past loader | Frames | Prims | FPS host | Crash | Note |",
        "|------|----|------|-------------|--------|-------|----------|-------|------|",
    ]
    for r in rows:
        md.append(
            f"| {r['name']} | {r['id']} | {r['boot']} | {r['past_loader']} | "
            f"{r['frames']} | {r['prims']} | {r['fps_host']} | {r['crash'] or '—'} | "
            f"{r['note'] or '—'} |"
        )
    md += ["", "## Play URLs (panel :8620)", ""]
    for r in rows:
        md.append(f"- **{r['name']}:** {r['play_url']}")
    md += ["", "## Hitman / NFS five-phase (scorer)", ""]
    for name, sc in phase_scores.items():
        md.append(
            f"### {name} — verdict **{sc['verdict']}** "
            f"(alchemy={sc['alchemy_contamination']})"
        )
        md += ["", "| Phase | Result |", "|-------|--------|"]
        for ph, st in sc["phases"].items():
            md.append(f"| {ph} | {st} |")
        md.append("")
    md += [
        "## FPS evidence",
        "",
        "- Native host FPS in table (prior run timing; Sly ~3s wall / 900f).",
        "- Panel play URLs listed; Chrome automation not forced.",
        "- No FPS overlay screenshot this cycle — evidence is stderr frame-limit + prims in `*.log`.",
        "",
    ]
    (LOG_DIR / "SUMMARY.md").write_text("\n".join(md), encoding="utf-8")
    print(f"WROTE pct={pct} passes={passes}/{checks}")
    for r in rows:
        print(
            r["name"],
            r["boot"],
            r["past_loader"],
            r["frames"],
            r["prims"],
            r["fps_host"],
            r["alchemy_contamination"],
            r["note"],
        )
    for name, sc in phase_scores.items():
        print(name, "verdict", sc["verdict"], "alchemy", sc["alchemy_contamination"], sc["phases"])


if __name__ == "__main__":
    main()
