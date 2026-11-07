"""ASSETS.GOB STBL inflate + IGB head probes — own code from CNK A2 layout."""

from __future__ import annotations

import re
import zlib
from dataclasses import dataclass
from typing import Callable, Sequence

from .gfc import GfcArchive, GfcFile

BLOCK_END = 0x7FFF
DA_FA = b"\xDA\xFA"
FA_DA = b"\xFA\xDA"
IG_META = re.compile(rb"ig[A-Z][A-Za-z0-9_]{2,48}")

# Priority assets from CNK A2 research (basenames).
PRIORITY_IGB = (
    "butanim.igb",
    "introtxr.igb",
    "background.igb",
    "citadel_logo.igb",
    "fetextur.igb",
    "fonts.igb",
    "backanim.igb",
    "pedecam.igb",
)


@dataclass
class ExtractResult:
    data: bytes | None
    error: str | None
    blocks_walked: int
    complete: bool


def inflate_cluster(src: bytes) -> bytes | None:
    """Decode one STBL cluster body (STBL0 raw or STBLz zlib)."""
    if len(src) < 5:
        return None
    tag = src[:5]
    if tag == b"STBL0":
        return src[5:]
    if tag != b"STBLz":
        return None
    try:
        return zlib.decompress(src[5:])
    except zlib.error:
        return None


def read_block_bytes(
    gob_reader: Callable[[int, int], bytes],
    archive: GfcArchive,
    block_index: int,
) -> bytes | None:
    if block_index < 0 or block_index >= archive.nblocks:
        return None
    blk = archive.blocks[block_index]
    if blk.compressed_size <= 0:
        return None
    return gob_reader(blk.gob_byte_offset, blk.compressed_size)


def extract_file(
    gob_reader: Callable[[int, int], bytes],
    archive: GfcArchive,
    fe: GfcFile,
    *,
    max_bytes: int = 128 * 1024,
) -> ExtractResult:
    """Walk GFC block chain and inflate STBL clusters until max_bytes."""
    out = bytearray()
    block = fe.first_block
    guard = 0
    while (
        block != BLOCK_END
        and 0 <= block < archive.nblocks
        and guard < archive.nblocks
        and len(out) < max_bytes
    ):
        raw = read_block_bytes(gob_reader, archive, block)
        if raw is None:
            return ExtractResult(None, f"read_fail block={block}", guard, False)
        piece = inflate_cluster(raw)
        if piece is None:
            head = raw[:5]
            return ExtractResult(
                None,
                f"inflate_fail block={block} head={head!r}",
                guard,
                False,
            )
        out.extend(piece)
        block = archive.blocks[block].next_block
        guard += 1
    data = bytes(out[:max_bytes])
    complete = fe.uncompressed_size <= max_bytes and len(data) >= fe.uncompressed_size
    if block != BLOCK_END and len(data) >= max_bytes:
        complete = False
    return ExtractResult(data, None, guard, complete)


def verify_blocks(
    gob_reader: Callable[[int, int], bytes],
    archive: GfcArchive,
    indices: Sequence[int] | None = None,
) -> list[dict]:
    """Confirm sampled GFC block offsets land on STBL* heads."""
    if indices is None:
        n = archive.nblocks
        candidates = [0, 1, 2, 3, 4, 10, 100, 500, 1000, min(2000, n - 1), n - 1]
        indices = [i for i in candidates if 0 <= i < n]
    out: list[dict] = []
    for bi in indices:
        blk = archive.blocks[bi]
        head = gob_reader(blk.gob_byte_offset, min(16, max(blk.compressed_size, 0)))
        tag = head[:5].decode("ascii", "replace") if head else ""
        out.append(
            {
                "index": bi,
                "compressed_size": blk.compressed_size,
                "gob_byte_offset": blk.gob_byte_offset,
                "next_block": blk.next_block,
                "head_tag": tag,
                "head_hex": head[:16].hex() if head else "",
                "is_stbl": bool(head) and head[:4] == b"STBL",
            }
        )
    return out


def probe_igb_head(data: bytes) -> dict:
    """Inspect inflated IGB bytes for DA FA cookie + ig* meta strings."""
    cookie_off = None
    cookie = None
    for needle in (DA_FA, FA_DA):
        idx = data.find(needle, 0, min(len(data), 512))
        if idx >= 0:
            cookie_off = idx
            cookie = needle.hex()
            break
    at_28 = data[0x28:0x2A] if len(data) >= 0x2A else b""
    ver_word = None
    if len(data) >= 0x30:
        ver_word = f"0x{int.from_bytes(data[0x2C:0x30], 'little'):08X}"
    window = data[: min(len(data), 65536)]
    ig_hits = sorted({m.group(0).decode("ascii") for m in IG_META.finditer(window)})
    return {
        "da_fa_offset": cookie_off,
        "da_fa_bytes": cookie,
        "da_fa_at_0x28": at_28 == DA_FA,
        "version_word_le": ver_word,
        "head_hex": data[:64].hex(),
        "ig_meta_strings": ig_hits[:24],
        "ig_meta_count": len(ig_hits),
    }


def select_igb_targets(archive: GfcArchive, limit: int = 16) -> list[GfcFile]:
    """Priority UI/font IGBs first, then fill with other .igb names."""
    files = [f for f in archive.files if f.name.lower().endswith(".igb")]
    selected: list[GfcFile] = []
    seen: set[int] = set()

    def add(fe: GfcFile) -> None:
        if fe.crc32 in seen:
            return
        seen.add(fe.crc32)
        selected.append(fe)

    for pn in PRIORITY_IGB:
        for fe in files:
            low = fe.name.lower().replace("\\", "/")
            if pn in low:
                add(fe)
    for fe in files:
        low = fe.name.lower().replace("\\", "/")
        if any(x in low for x in ("logo", "font", "ui/", "intro", "butanim", "title")):
            add(fe)
        if len(selected) >= limit:
            break
    for fe in files:
        if len(selected) >= limit:
            break
        add(fe)
    return selected[:limit]


def sample_stbl_heads(gob_bytes: bytes, max_hits: int = 8) -> dict:
    """Lightweight signature peek over a GOB window."""
    tags = {b"STBLz": 0, b"STBL0": 0, b"ENBL": 0}
    samples: list[dict] = []
    for tag in tags:
        start = 0
        while True:
            idx = gob_bytes.find(tag, start)
            if idx < 0:
                break
            tags[tag] += 1
            if len(samples) < max_hits and tag in (b"STBLz", b"STBL0"):
                samples.append(
                    {
                        "offset": idx,
                        "tag": tag.decode("ascii"),
                        "head_hex": gob_bytes[idx : idx + 16].hex(),
                    }
                )
            start = idx + 4
            if tags[tag] > 100000:
                break
    return {
        "scanned": True,
        "window_bytes": len(gob_bytes),
        "counts_in_window": {k.decode("ascii"): v for k, v in tags.items()},
        "samples": samples,
    }


def _gob_reader_from_bytes(gob: bytes) -> Callable[[int, int], bytes]:
    def reader(offset: int, size: int) -> bytes:
        if offset < 0 or size < 0:
            return b""
        end = min(len(gob), offset + size)
        if offset >= len(gob):
            return b""
        return gob[offset:end]

    return reader


def verify_gob_via_gfc(gob: bytes, archive: GfcArchive) -> dict:
    """Confirm GFC block table offsets land on STBL* tags across the full GOB."""
    reader = _gob_reader_from_bytes(gob)
    samples = verify_blocks(reader, archive)
    census: dict[str, int] = {}
    for s in samples:
        tag = s.get("head_tag") or "?"
        census[tag] = census.get(tag, 0) + 1
    stbl_ok = sum(1 for s in samples if s.get("is_stbl"))
    return {
        "scanned": True,
        "method": "gfc_block_table",
        "gob_bytes": len(gob),
        "blocks_sampled": len(samples),
        "stbl_ok": stbl_ok,
        "block_tag_census": census,
        "samples": samples,
    }


def sample_igb_files(
    gob: bytes,
    archive: GfcArchive,
    *,
    limit: int = 16,
    name_prefer: list[str] | None = None,
    write_dir: "Path | None" = None,
    max_bytes: int = 128 * 1024,
) -> list[dict]:
    """Inflate priority / first N .igb files and probe DA FA heads."""
    from pathlib import Path

    prefer = [p.lower().replace("/", "\\") for p in (name_prefer or list(PRIORITY_IGB))]
    reader = _gob_reader_from_bytes(gob)

    # Prefer-list first, then select_igb_targets fill.
    files = [f for f in archive.files if f.name.lower().endswith(".igb")]
    selected: list[GfcFile] = []
    seen: set[int] = set()

    def add(fe: GfcFile) -> None:
        if fe.crc32 in seen:
            return
        seen.add(fe.crc32)
        selected.append(fe)

    for pn in prefer:
        for fe in files:
            low = fe.name.lower().replace("/", "\\")
            if pn in low:
                add(fe)
    for fe in select_igb_targets(archive, limit=limit * 2):
        add(fe)
        if len(selected) >= limit:
            break
    selected = selected[:limit]

    out_path: Path | None = None
    if write_dir is not None:
        out_path = Path(write_dir)
        out_path.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    for fe in selected:
        er = extract_file(reader, archive, fe, max_bytes=max_bytes)
        row: dict = {
            "name": fe.name,
            "crc32": f"0x{fe.crc32:08X}",
            "uncompressed_size": fe.uncompressed_size,
            "first_block": fe.first_block,
            "blocks_walked": er.blocks_walked,
            "complete": er.complete,
            "ok": er.data is not None and er.error is None,
            "error": er.error,
            "bytes_inflated": len(er.data) if er.data else 0,
            "da_fa": None,
        }
        if er.data is not None:
            probe = probe_igb_head(er.data)
            row["da_fa"] = probe
            if out_path is not None:
                safe = fe.name.replace("\\", "_").replace("/", "_")
                (out_path / f"{safe}.head.bin").write_bytes(er.data[: min(len(er.data), 4096)])
        results.append(row)
    return results
