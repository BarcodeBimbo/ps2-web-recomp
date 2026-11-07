"""Score Hitman/NFS smoke logs against the five-phase Sony-tied matrix.

Validate only. Does not patch cdvdfsv/cdvd.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PRIMS = re.compile(r"\[gs\]\s+(\d+)\s+primitives drawn", re.I)
FRAME = re.compile(r"\[frame\]\s+(\d+)\s+prims\s+(\d+)", re.I)
STOPPED = re.compile(r"\[ee\] stopped after (\d+) frames", re.I)
HALT_BAD = re.compile(r"halted:\s*(?!frame limit reached)(\S.+)", re.I)
FRAME_LIMIT = re.compile(r"frame limit reached", re.I)
SIF_REBOOT = re.compile(r"\[sif\] IOP reboot requested", re.I)
LOADFILE = re.compile(r"\[(?:sif|loadfile)\].*(?:LOADFILE|loadfile|IOPRP)", re.I)
CDVD_SEARCH = re.compile(r"\[cdvdfsv\] search .+ -> found", re.I)
CDVD_N = re.compile(r"\[cdvdfsv\] N 0x", re.I)
CDVD_STREAM = re.compile(r"\[cdvdfsv\] stream", re.I)
CURREAD = re.compile(r"curReadPos|eeaddr2|read.?pos", re.I)
READEE = re.compile(r"readee|eeaddr1|_rd_intr", re.I)
# Real Alchemy host/guest pulses only. Do NOT use bare "FCE0" — Hitman CreateSema
# often logs attr=0x1FFFCE0 (hex ending in FCE0) which is not an Alchemy pulse.
ALCHEMY_PULSE = re.compile(
    r"host_signal(?:_sema)?\((?:16|54|55)\)|"
    r"Alchemy|"
    r"virt.?LBA|"
    r"\+24008|"
    r"(?<![0-9A-Fa-f])(?:0x)?0*FCE0(?![0-9A-Fa-f])|"  # standalone FCE0 / 0xFCE0 only
    r"soft-arm",
    re.I,
)
SEMA_END = re.compile(r"\[sema\]\s+(\d+)\s+count\s+(\d+)\s+waiters\s+(\d+)", re.I)
SIF_WAIT = re.compile(r"\[sif\]\s+(\d+)\s+packets wait for the EE", re.I)
MISSING = re.compile(r"missing code at 0x([0-9A-Fa-f]+)", re.I)

HITMAN_MENU = re.compile(r"BOOTMENU|HITMANBL|ERRORMES|HM3GPAD", re.I)
NFS_MENU = re.compile(r"NFS\\|IRX281|SLUS_212|frontend|FE_", re.I)


def score(text: str, game: str) -> dict:
    prim_hits = [int(m.group(1)) for m in PRIMS.finditer(text)]
    frame_hits = [(int(a), int(b)) for a, b in FRAME.findall(text)]
    prims = prim_hits[-1] if prim_hits else (frame_hits[-1][1] if frame_hits else 0)
    frames = int(STOPPED.search(text).group(1)) if STOPPED.search(text) else (
        frame_hits[-1][0] if frame_hits else 0
    )
    searches = len(CDVD_SEARCH.findall(text))
    alchemy = bool(ALCHEMY_PULSE.search(text))
    missing = [m.group(1).lower() for m in MISSING.finditer(text)]
    halt = HALT_BAD.search(text)
    sif_wait = int(SIF_WAIT.search(text).group(1)) if SIF_WAIT.search(text) else None
    leftover = [
        {"id": int(a), "count": int(b), "waiters": int(c)}
        for a, b, c in SEMA_END.findall(text)
    ]

    menu_hit = bool(HITMAN_MENU.search(text)) if game == "hitman_bm" else bool(
        NFS_MENU.search(text) or searches >= 1
    )
    prims_move = prims >= 100
    boot_ok = (
        bool(SIF_REBOOT.search(text))
        and frames >= 30
        and not halt
        and not missing
    )
    menu_ok = boot_ok and prims_move and menu_hit and not alchemy
    # Without explicit curReadPos/readee trace lines, require CDVD found + prims + no alchemy pulse.
    first_read_ok = (
        menu_ok
        and searches >= 1
        and not alchemy
        and (bool(CURREAD.search(text) or READEE.search(text) or CDVD_N.search(text)) or prims_move)
    )
    streaming_ok = first_read_ok and (searches >= 3 or bool(CDVD_STREAM.search(text)) or frames >= 200)
    sustained_ok = (
        streaming_ok
        and bool(FRAME_LIMIT.search(text))
        and prims_move
        and frames >= 200
        and (sif_wait is None or sif_wait == 0)
        and not alchemy
    )

    phases = {
        "boot": "pass" if boot_ok else "fail",
        "menu": "pass" if menu_ok else "fail",
        "first_disc_read": "pass" if first_read_ok else "fail",
        "streaming": "pass" if streaming_ok else "fail",
        "sustained_run": "pass" if sustained_ok else "fail",
    }
    order = list(phases)
    first_fail = next((p for p in order if phases[p] == "fail"), None)
    return {
        "game": game,
        "frames": frames,
        "primitives": prims,
        "cdvd_searches_found": searches,
        "alchemy_contamination": alchemy,
        "missing_code": missing,
        "halt": halt.group(1).strip()[:80] if halt else None,
        "sif_packets_waiting": sif_wait,
        "leftover_semas": leftover,
        "phases": phases,
        "verdict": "pass" if first_fail is None else "fail",
        "first_fail_phase": first_fail,
    }


def read_log_text(path: Path) -> str:
    """Read smoke logs; PowerShell Tee-Object often writes UTF-16 LE with BOM."""
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16", errors="replace")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig", errors="replace")
    # Heuristic: NUL every other byte → UTF-16 LE without relying on BOM alone
    if len(raw) >= 4 and raw[1:2] == b"\x00" and raw[3:4] == b"\x00":
        return raw.decode("utf-16-le", errors="replace")
    return raw.decode("utf-8", errors="replace")


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: matrix_phase_check.py <hitman|nfs_mw|hitman_bm> <logfile>")
        return 2
    game = "hitman_bm" if argv[1] in ("hitman", "hitman_bm") else "nfs_mw"
    text = read_log_text(Path(argv[2]))
    print(json.dumps(score(text, game), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
