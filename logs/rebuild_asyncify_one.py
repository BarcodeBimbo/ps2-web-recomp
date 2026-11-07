"""Rebuild one game's browser player in Asyncify mode."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("PS2_WEB_ASYNC_MODE", "asyncify")
os.environ.setdefault("PS2_BUILD_JOBS", "1")

from windows_port import build_web  # noqa: E402

if len(sys.argv) != 2:
    raise SystemExit("usage: rebuild_asyncify_one.py GAME_ID")
gid = sys.argv[1]
print("== rebuilding", gid, flush=True)
build_web(gid)
print("== done", gid, flush=True)
