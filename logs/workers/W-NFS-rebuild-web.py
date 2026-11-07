#!/usr/bin/env python3
"""NFS-only web rebuild launcher for W-NFS-2 (prefetch fix)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from windows_port import build_web  # noqa: E402

GID = "60c82f4a111da300ac23bbec85272788"
print(f"START build_web {GID}", flush=True)
build_web(GID)
print("DONE build_web", flush=True)
