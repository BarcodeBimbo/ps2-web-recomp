"""Minimal ISO9660 directory reader for PS2 DVD images (own code).

Inspired by dumps2iso's LBA/path file-table idea; does not port mkps2iso source.
UDF FID walk can be added later; ISO9660 PVD is enough for CNK root + MODULES.
"""

from __future__ import annotations

import mmap
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterator

SECTOR = 2048


@dataclass
class IsoEntry:
    path: str
    lba: int
    size: int
    flags: int

    @property
    def is_dir(self) -> bool:
        return bool(self.flags & 0x02)


def _le32(buf: bytes | memoryview, off: int) -> int:
    return struct.unpack_from("<I", buf, off)[0]


class Iso9660Image:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._fh: BinaryIO | None = None
        self._mm: mmap.mmap | None = None

    def __enter__(self) -> "Iso9660Image":
        self._fh = self.path.open("rb")
        self._mm = mmap.mmap(self._fh.fileno(), 0, access=mmap.ACCESS_READ)
        return self

    def __exit__(self, *exc) -> None:
        if self._mm is not None:
            self._mm.close()
            self._mm = None
        if self._fh is not None:
            self._fh.close()
            self._fh = None

    def read_at(self, lba: int, size: int) -> bytes:
        assert self._mm is not None
        start = lba * SECTOR
        return bytes(self._mm[start : start + size])

    def pvd(self) -> bytes:
        pvd = self.read_at(16, SECTOR)
        if pvd[0:6] != b"\x01CD001":
            raise ValueError(f"ISO9660 PVD not found at LBA 16 in {self.path}")
        return pvd

    def _list_dir(self, lba: int, size: int) -> list[tuple[str, int, int, int]]:
        data = self.read_at(lba, size)
        off = 0
        out: list[tuple[str, int, int, int]] = []
        while off < len(data):
            length = data[off]
            if length == 0:
                off = (off + SECTOR) & ~(SECTOR - 1)
                if off >= len(data):
                    break
                continue
            loc = _le32(data, off + 2)
            sz = _le32(data, off + 10)
            flags = data[off + 25]
            name_len = data[off + 32]
            name = bytes(data[off + 33 : off + 33 + name_len])
            if name not in (b"\x00", b"\x01"):
                n = name.split(b";")[0].decode("ascii", "replace")
                out.append((n, loc, sz, flags))
            off += length
        return out

    def iter_entries(self, recursive_dirs: tuple[str, ...] = ("MODULES",)) -> Iterator[IsoEntry]:
        pvd = self.pvd()
        root_lba = _le32(pvd, 156 + 2)
        root_size = _le32(pvd, 156 + 10)
        root = self._list_dir(root_lba, root_size)
        for name, loc, sz, flags in root:
            yield IsoEntry(name, loc, sz, flags)
            if (flags & 0x02) and name.upper() in {d.upper() for d in recursive_dirs}:
                try:
                    for sn, sl, ss, sf in self._list_dir(loc, sz):
                        yield IsoEntry(f"{name}/{sn}", sl, ss, sf)
                except Exception:
                    continue

    def find(self, entries: list[IsoEntry], prefix: str) -> IsoEntry | None:
        prefix_u = prefix.upper()
        for e in entries:
            base = e.path.split("/")[-1].upper()
            if base.startswith(prefix_u):
                return e
        return None
