"""ASSETS.GFC parser (Alchemy pack index) — own code from CNK A2 layout."""

from __future__ import annotations

import collections
import struct
from dataclasses import dataclass, field
from pathlib import Path


def be32(buf: bytes, off: int = 0) -> int:
    return struct.unpack_from(">I", buf, off)[0]


GFC_MAGIC = 0x00008008


@dataclass
class GfcBlock:
    compressed_size: int
    gob_byte_offset: int
    next_block: int


@dataclass
class GfcFile:
    index: int
    crc32: int
    uncompressed_size: int
    first_block: int
    name: str = ""


@dataclass
class GfcArchive:
    magic: int
    gob_size: int
    nblocks: int
    nfiles: int
    name_stride: int
    blocks: list[GfcBlock] = field(default_factory=list)
    adlers: list[int] = field(default_factory=list)
    files: list[GfcFile] = field(default_factory=list)

    def ext_census(self) -> dict[str, int]:
        c: collections.Counter[str] = collections.Counter()
        for f in self.files:
            name = f.name.lower()
            if "." in name:
                ext = "." + name.rsplit(".", 1)[-1]
            else:
                ext = ""
            c[ext] += 1
        return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def parse_gfc(data: bytes) -> GfcArchive:
    if len(data) < 16:
        raise ValueError("GFC too small")
    magic = be32(data, 0)
    if magic != GFC_MAGIC:
        raise ValueError(f"unexpected GFC magic 0x{magic:08X} (want 0x{GFC_MAGIC:08X})")
    gob_size = be32(data, 4)
    nblocks = be32(data, 8)
    nfiles = be32(data, 12)
    off = 16
    blocks: list[GfcBlock] = []
    for _ in range(nblocks):
        blocks.append(
            GfcBlock(be32(data, off), be32(data, off + 4), be32(data, off + 8))
        )
        off += 12
    adlers = [be32(data, off + i * 4) for i in range(nblocks)]
    off += nblocks * 4
    files: list[GfcFile] = []
    for i in range(nfiles):
        files.append(
            GfcFile(
                index=i,
                crc32=be32(data, off),
                uncompressed_size=be32(data, off + 4),
                first_block=be32(data, off + 8),
            )
        )
        off += 12
    name_stride = 0
    # CNK uses 72-byte name slots; fall back to 64 if that fits better.
    for stride in (72, 64, 48, 32):
        if off + nfiles * stride <= len(data):
            name_stride = stride
            for i in range(nfiles):
                raw = data[off : off + stride]
                off += stride
                name = raw.split(b"\x00", 1)[0].decode("ascii", "replace")
                files[i].name = name
            break
    return GfcArchive(
        magic=magic,
        gob_size=gob_size,
        nblocks=nblocks,
        nfiles=nfiles,
        name_stride=name_stride,
        blocks=blocks,
        adlers=adlers,
        files=files,
    )


def load_gfc_file(path: Path) -> GfcArchive:
    return parse_gfc(path.read_bytes())
