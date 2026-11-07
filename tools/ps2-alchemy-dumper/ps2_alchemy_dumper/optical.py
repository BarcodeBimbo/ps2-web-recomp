"""Optical rip stub — redumper-inspired notes; no drive I/O yet (own future code)."""

from __future__ import annotations

STUB_NOTES = """
Phase 4 plan (Windows primary):

  Inspired by redumper patterns (https://github.com/superg/redumper, GPL-3.0):
  - Select drive by letter (e.g. E:)
  - Read DVD user-data sectors (2048 bytes) by LBA via Windows SPTI / SCSI PASS THROUGH
  - Optional retries on sense errors
  - Write a plain .iso for the ISO-first Alchemy mapper

  Explicitly NOT ported from redumper:
  - CDDA / scrambled CD / subchannel / C2 sample-state machine
  - refine/split, firmware flash, OmniDrive / Xbox / Nintendo paths
  - Shelling out to the redumper binary

  This stub does not open devices yet.
"""


def describe_stub(drive: str | None = None) -> dict:
    return {
        "implemented": False,
        "drive_arg": drive,
        "platform_target": "windows",
        "planned_api": "SPTI SCSI READ(10/12) → .iso",
        "notes": STUB_NOTES.strip(),
    }
