"""Disc access layer — ISO-first sector/LBA reads (own code).

Inspired by dumps2iso's LBA/path table idea and redumper's sector model;
does not port or invoke either upstream.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator

from .iso9660 import SECTOR, Iso9660Image, IsoEntry


@dataclass
class DiscFile:
    path: str
    lba: int
    size: int
    flags: int

    @property
    def is_dir(self) -> bool:
        return bool(self.flags & 0x02)

    @property
    def byte_offset(self) -> int:
        return self.lba * SECTOR


class DiscAccess:
    """Open a PS2 DVD .iso and resolve Alchemy-bearing paths by LBA."""

    def __init__(self, iso_path: Path):
        self.iso_path = Path(iso_path)
        self._img: Iso9660Image | None = None
        self.toc: list[IsoEntry] = []

    def __enter__(self) -> "DiscAccess":
        self._img = Iso9660Image(self.iso_path)
        self._img.__enter__()
        self.toc = list(self._img.iter_entries())
        return self

    def __exit__(self, *exc) -> None:
        if self._img is not None:
            self._img.__exit__(*exc)
            self._img = None

    @property
    def img(self) -> Iso9660Image:
        if self._img is None:
            raise RuntimeError("DiscAccess not opened")
        return self._img

    def find(self, prefix: str) -> IsoEntry | None:
        return self.img.find(self.toc, prefix)

    def find_boot(self) -> IsoEntry | None:
        for pref in ("SLUS_", "SLES_", "SCUS_", "SCES_", "BOOT.ELF"):
            ent = self.find(pref)
            if ent is not None and not ent.is_dir:
                return ent
        return None

    def modules_irx(self) -> list[str]:
        return sorted(
            e.path.split("/", 1)[-1]
            for e in self.toc
            if e.path.upper().startswith("MODULES/")
            and e.path.upper().endswith(".IRX")
        )

    def read_entry(self, entry: IsoEntry) -> bytes:
        return self.img.read_at(entry.lba, entry.size)

    def gob_reader(self, gob_entry: IsoEntry) -> Callable[[int, int], bytes]:
        """Return (offset, size) -> bytes against ASSETS.GOB payload."""

        def _read(offset: int, size: int) -> bytes:
            if offset < 0 or offset >= gob_entry.size or size <= 0:
                return b""
            if offset + size > gob_entry.size:
                size = gob_entry.size - offset
            abs_off = gob_entry.lba * SECTOR + offset
            assert self._img is not None and self._img._mm is not None
            return bytes(self._img._mm[abs_off : abs_off + size])

        return _read

    def iter_files(self) -> Iterator[DiscFile]:
        for e in self.toc:
            yield DiscFile(e.path, e.lba, e.size, e.flags)
