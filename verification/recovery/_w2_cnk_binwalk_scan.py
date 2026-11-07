#!/usr/bin/env python3
"""CNK disc Alchemy GFC/GOB structural scan — research only."""
from __future__ import annotations

import collections
import json
import mmap
import re
import struct
import zlib
from pathlib import Path

ROOT = Path(r"C:\PS2Recomp\games\b49f2e769315347e8bda839feb705744")
ISO = ROOT / "disc.iso"
ELF = ROOT / "disc" / "boot.elf"
RAM = ROOT / "explore_ram.bin"
OUT_DIR = Path(r"C:\PS2Recomp\verification\recovery")
SAMPLE_DIR = OUT_DIR / "alchemy-rebuild-w2-samples"
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

SECTOR = 2048


def be32(b: bytes, off: int = 0) -> int:
    return struct.unpack_from(">I", b, off)[0]


def le32(b: bytes, off: int = 0) -> int:
    return struct.unpack_from("<I", b, off)[0]


def main() -> None:
    results: dict = {
        "iso_files": [],
        "gfc": {},
        "gob_stbl": {},
        "igb_samples": [],
        "elf_corr": {},
        "ram_corr": {},
        "tools": ["python3 mmap/struct/zlib (binwalk CLI not found)"],
    }

    with ISO.open("rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        def read_at(lba: int, size: int) -> bytes:
            return bytes(mm[lba * SECTOR : lba * SECTOR + size])

        pvd = read_at(16, 2048)
        assert pvd[0:6] == b"\x01CD001"
        root_lba = le32(pvd, 156 + 2)
        root_size = le32(pvd, 156 + 10)

        def list_dir(lba: int, size: int):
            data = read_at(lba, size)
            off = 0
            out = []
            while off < len(data):
                length = data[off]
                if length == 0:
                    off = (off + 2048) & ~2047
                    if off >= len(data):
                        break
                    continue
                loc = le32(data, off + 2)
                sz = le32(data, off + 10)
                flags = data[off + 25]
                name_len = data[off + 32]
                name = data[off + 33 : off + 33 + name_len]
                if name not in (b"\x00", b"\x01"):
                    n = name.split(b";")[0].decode("ascii", "replace")
                    out.append((n, loc, sz, flags))
                off += length
            return out

        root = list_dir(root_lba, root_size)
        for n, loc, sz, flags in root:
            results["iso_files"].append({"name": n, "lba": loc, "size": sz, "flags": flags})
            if flags & 2 and n in ("MUSIC", "VIDEO", "VOICE", "MODULES"):
                try:
                    for sn, sl, ss, sf in list_dir(loc, sz)[:40]:
                        results["iso_files"].append(
                            {"name": f"{n}/{sn}", "lba": sl, "size": ss, "flags": sf}
                        )
                except Exception:
                    pass

        gfc_e = next(e for e in root if e[0].startswith("ASSETS.GFC"))
        gob_e = next(e for e in root if e[0].startswith("ASSETS.GOB"))
        gfc_lba, gfc_size = gfc_e[1], gfc_e[2]
        gob_lba, gob_size = gob_e[1], gob_e[2]
        print("GFC", gfc_lba, gfc_size, "GOB", gob_lba, gob_size)

        gfc = read_at(gfc_lba, gfc_size)
        assert be32(gfc, 0) == 0x00008008
        gob_size_hdr = be32(gfc, 4)
        nblocks = be32(gfc, 8)
        nfiles = be32(gfc, 12)
        off = 16
        blocks = []
        for i in range(nblocks):
            compressed = be32(gfc, off)
            offset = be32(gfc, off + 4)
            nxt = be32(gfc, off + 8)
            blocks.append((compressed, offset, nxt))
            off += 12
        adlers = [be32(gfc, off + i * 4) for i in range(nblocks)]
        off += nblocks * 4
        files = []
        for i in range(nfiles):
            crc = be32(gfc, off)
            size = be32(gfc, off + 4)
            first = be32(gfc, off + 8)
            files.append({"crc": crc, "size": size, "first": first, "name": ""})
            off += 12
        name_table = False
        if off + nfiles * 72 <= len(gfc):
            name_table = True
            for i in range(nfiles):
                raw = gfc[off : off + 72]
                name = raw.split(b"\x00", 1)[0].decode("ascii", "replace")
                files[i]["name"] = name
                off += 72
        leftover = len(gfc) - off
        results["gfc"] = {
            "lba": gfc_lba,
            "size": gfc_size,
            "sig": hex(be32(gfc, 0)),
            "gob_size_hdr": gob_size_hdr,
            "nblocks": nblocks,
            "nfiles": nfiles,
            "name_table": name_table,
            "name_stride": 72 if name_table else None,
            "parse_end_off": off,
            "leftover_bytes": leftover,
            "gob_size_iso": gob_size,
            "gob_size_match": gob_size_hdr == gob_size,
            "block0": {
                "compressed": blocks[0][0],
                "offset": blocks[0][1],
                "next": blocks[0][2],
                "adler": hex(adlers[0]),
            },
            "block_last": {
                "compressed": blocks[-1][0],
                "offset": blocks[-1][1],
                "next": blocks[-1][2],
            },
            "file0": files[0],
        }

        ext_counts: collections.Counter = collections.Counter()
        path_prefix: collections.Counter = collections.Counter()
        igb_files = []
        for fe in files:
            name = fe["name"]
            low = name.lower().replace("\\", "/")
            ext = low.rsplit(".", 1)[-1] if "." in low else ""
            ext_counts[ext] += 1
            parts = low.split("/")
            if len(parts) >= 2:
                path_prefix["/".join(parts[:2])] += 1
            elif parts[0]:
                path_prefix[parts[0]] += 1
            if low.endswith(".igb"):
                igb_files.append(fe)

        results["gfc"]["ext_counts"] = dict(ext_counts.most_common(30))
        results["gfc"]["path_prefix_top"] = dict(path_prefix.most_common(25))
        results["gfc"]["igb_count"] = len(igb_files)

        catalog_path = SAMPLE_DIR / "gfc-file-catalog.tsv"
        with catalog_path.open("w", encoding="utf-8") as cat:
            cat.write("index\tcrc\tsize\tfirst_block\tname\n")
            for i, fe in enumerate(files):
                cat.write(
                    f"{i}\t{fe['crc']:08X}\t{fe['size']}\t{fe['first']}\t{fe['name']}\n"
                )
        print("catalog", catalog_path, "files", nfiles, "igb", len(igb_files))

        gob_mm_base = gob_lba * SECTOR
        stbl_counts: collections.Counter = collections.Counter()
        stbl_offsets_sample = []
        chunk = 4 * 1024 * 1024
        enbl_count = 0
        dafa_count = 0
        for base in range(0, gob_size, chunk):
            end = min(base + chunk + 4, gob_size)
            data = bytes(mm[gob_mm_base + base : gob_mm_base + end])
            enbl_count += data.count(b"ENBL")
            dafa_count += data.count(b"\xDA\xFA") + data.count(b"\xFA\xDA")
            idx = 0
            while True:
                i = data.find(b"STBL", idx)
                if i < 0 or base + i >= gob_size:
                    break
                abs_off = base + i
                if abs_off + 5 <= gob_size:
                    tag = bytes(mm[gob_mm_base + abs_off : gob_mm_base + abs_off + 5])
                    kind = tag.decode("ascii", "replace")
                    stbl_counts[kind] += 1
                    if len(stbl_offsets_sample) < 40:
                        stbl_offsets_sample.append(
                            {"off": abs_off, "kind": kind, "hex": tag.hex()}
                        )
                idx = i + 1

        block_verify = []
        for bi in [0, 1, 2, 3, 4, 10, 100, 500, 1000, min(2000, nblocks - 1), nblocks - 1]:
            if bi >= nblocks:
                continue
            c, o, n = blocks[bi]
            head = (
                bytes(mm[gob_mm_base + o : gob_mm_base + o + 16])
                if o + 16 <= gob_size
                else b""
            )
            block_verify.append(
                {
                    "i": bi,
                    "compressed": c,
                    "offset": o,
                    "next": n,
                    "head_ascii": head[:5].decode("ascii", "replace"),
                    "head_hex": head[:16].hex(),
                    "is_stbl": head[:4] == b"STBL",
                }
            )

        results["gob_stbl"] = {
            "lba": gob_lba,
            "size": gob_size,
            "stbl_kind_counts": dict(stbl_counts),
            "stbl_sample_offsets": stbl_offsets_sample,
            "enbl_count": enbl_count,
            "dafa_cookie_count": dafa_count,
            "block_verify": block_verify,
            "stblz_vs_nblocks_delta": stbl_counts.get("STBLz", 0) - nblocks,
        }
        print("STBL", dict(stbl_counts), "ENBL", enbl_count, "DAFA", dafa_count)

        def inflate_cluster(src: bytes):
            if len(src) < 5:
                return None
            if src[:5] == b"STBL0":
                return src[5:]
            if src[:5] != b"STBLz":
                return None
            try:
                return zlib.decompress(src[5:])
            except Exception:
                return None

        def extract_file_partial(fe, max_bytes=128 * 1024):
            out = bytearray()
            block = fe["first"]
            guard = 0
            while (
                block != 0x7FFF
                and block < nblocks
                and guard < nblocks
                and len(out) < max_bytes
            ):
                c, o, nxt = blocks[block]
                raw = bytes(mm[gob_mm_base + o : gob_mm_base + o + c])
                piece = inflate_cluster(raw)
                if piece is None:
                    return None, f"inflate_fail block={block}"
                out.extend(piece)
                block = nxt
                guard += 1
            return bytes(out[:max_bytes]), None

        priority_names = [
            "butanim.igb",
            "introtxr.igb",
            "background.igb",
            "citadel_logo.igb",
            "fetextur.igb",
            "fonts.igb",
            "pools.csv",
        ]
        sample_targets = []
        for pn in priority_names:
            for fe in files:
                if fe["name"] and pn.lower() in fe["name"].lower().replace("\\", "/"):
                    sample_targets.append(fe)
        for fe in files:
            low = fe["name"].lower().replace("\\", "/")
            if low.endswith(".igb") and any(
                x in low for x in ("logo", "font", "ui/", "intro", "butanim", "title")
            ):
                sample_targets.append(fe)
                if len(sample_targets) > 40:
                    break
        seen = set()
        uniq = []
        for fe in sample_targets:
            if fe["crc"] in seen:
                continue
            seen.add(fe["crc"])
            uniq.append(fe)
        sample_targets = uniq[:18]

        for fe in sample_targets:
            data, err = extract_file_partial(fe, max_bytes=128 * 1024)
            info = {
                "name": fe["name"],
                "crc": f"{fe['crc']:08X}",
                "size": fe["size"],
                "first": fe["first"],
                "err": err,
            }
            if data:
                info["extracted_len"] = len(data)
                info["head_hex"] = data[:64].hex()
                info["head_ascii"] = "".join(
                    chr(b) if 32 <= b < 127 else "." for b in data[:64]
                )
                info["has_dafa"] = (b"\xDA\xFA" in data[:512]) or (
                    b"\xFA\xDA" in data[:512]
                )
                ig_hits = sorted(
                    set(
                        re.findall(
                            rb"ig[A-Z][A-Za-z0-9_]{2,40}",
                            data[: min(len(data), 65536)],
                        )
                    )
                )[:20]
                info["ig_string_hits"] = [x.decode("ascii") for x in ig_hits]
                safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", fe["name"])[:80]
                sp = SAMPLE_DIR / f"igb_head_{fe['crc']:08X}_{safe}.bin"
                sp.write_bytes(data[: min(len(data), 4096)])
                info["sample_file"] = sp.name
                info["complete"] = fe["size"] <= 128 * 1024 and len(data) >= fe["size"]
            results["igb_samples"].append(info)
            print(
                "sample",
                fe["name"],
                info.get("has_dafa"),
                info.get("ig_string_hits", [])[:5],
                err,
            )

        elf = ELF.read_bytes()
        elf_name_hits = []
        for fe in files:
            name = fe["name"]
            if not name or not name.lower().endswith(".igb"):
                continue
            base = name.replace("\\", "/").split("/")[-1]
            cands = [
                name,
                name.replace("\\", "/"),
                name.lower(),
                base,
                base.lower(),
                base.upper(),
            ]
            for c in cands:
                b = c.encode("ascii", "ignore")
                if len(b) < 8:
                    continue
                fo = elf.find(b)
                if fo >= 0:
                    va = 0x00100000 + (fo - 0x80)
                    elf_name_hits.append(
                        {
                            "name": name,
                            "needle": c,
                            "file_off": fo,
                            "approx_va": hex(va),
                        }
                    )
                    break
            if len(elf_name_hits) >= 40:
                break
        results["elf_corr"]["igb_path_strings_in_elf"] = elf_name_hits
        results["elf_corr"]["igb_path_hit_count"] = len(elf_name_hits)

        known_vas = [
            0x00108D28,
            0x00108F60,
            0x0010FCE0,
            0x00110100,
            0x00508930,
            0x00520160,
            0x0051AC80,
            0x0051ACEC,
            0x00725F50,
            0x00725F00,
            0x00705C18,
            0x00705F18,
            0x00BD1000,
            0x006B4920,
            0x006B2B90,
        ]
        va_hits = []
        for va in known_vas:
            needle = struct.pack("<I", va)
            hits_gfc = []
            start = 0
            while len(hits_gfc) < 5:
                i = gfc.find(needle, start)
                if i < 0:
                    break
                hits_gfc.append(i)
                start = i + 1
            gob_hits = []
            for region_off, region_len in [
                (0, 2 * 1024 * 1024),
                (gob_size // 2, 1 * 1024 * 1024),
                (max(0, gob_size - 2 * 1024 * 1024), 2 * 1024 * 1024),
            ]:
                blob = bytes(
                    mm[gob_mm_base + region_off : gob_mm_base + region_off + region_len]
                )
                start = 0
                while len(gob_hits) < 3:
                    i = blob.find(needle, start)
                    if i < 0:
                        break
                    gob_hits.append(region_off + i)
                    start = i + 1
            va_hits.append(
                {"va": hex(va), "gfc_offs": hits_gfc, "gob_sample_offs": gob_hits}
            )
        results["elf_corr"]["va_le32_in_disc"] = va_hits

        # Alchemy / IGB-related strings in ELF (for report table)
        alchemy_needles = [
            b"Intrinsic Alchemy",
            b"igIGBFile",
            b"ASSETS.GFC",
            b"ASSETS.GOB",
            b"gfx/ui/butanim.igb",
            b"ui/introtxr.igb",
            b"pools.csv",
            b"STBLz",
            b"STBL0",
            b"STBL",
        ]
        elf_str = []
        for n in alchemy_needles:
            fo = elf.find(n)
            if fo >= 0:
                elf_str.append(
                    {
                        "needle": n.decode("ascii", "replace"),
                        "file_off": fo,
                        "approx_va": hex(0x00100000 + (fo - 0x80)),
                    }
                )
            else:
                elf_str.append({"needle": n.decode("ascii", "replace"), "file_off": None})
        results["elf_corr"]["alchemy_strings"] = elf_str

        if RAM.exists():
            ram = RAM.read_bytes()
            ram_info: dict = {
                "size": len(ram),
                "stbl_counts": {},
                "gfc_sig_hits": [],
                "path_hits": [],
                "va_as_ptr_hits": [],
            }
            for kind in (b"STBLz", b"STBL0"):
                ram_info["stbl_counts"][kind.decode()] = ram.count(kind)
            c = 0
            start = 0
            while True:
                i = ram.find(b"STBL", start)
                if i < 0:
                    break
                c += 1
                start = i + 1
            ram_info["stbl_counts"]["STBL*"] = c
            sig = struct.pack(">I", 0x00008008)
            start = 0
            while len(ram_info["gfc_sig_hits"]) < 10:
                i = ram.find(sig, start)
                if i < 0:
                    break
                ram_info["gfc_sig_hits"].append(hex(i))
                start = i + 1
            for pn in [
                "ASSETS.GFC",
                "ASSETS.GOB",
                "butanim.igb",
                "introtxr.igb",
                "Intrinsic Alchemy",
                "igIGBFile",
            ]:
                i = ram.find(pn.encode())
                ram_info["path_hits"].append(
                    {"needle": pn, "off": hex(i) if i >= 0 else None}
                )
            for va in [0x00725F50, 0x00725F00, 0x00BD1000, 0x0010FCE0]:
                needle = struct.pack("<I", va)
                hits = []
                start = 0
                while len(hits) < 8:
                    i = ram.find(needle, start)
                    if i < 0:
                        break
                    if i % 4 == 0:
                        hits.append(hex(i))
                    start = i + 1
                ram_info["va_as_ptr_hits"].append(
                    {"va": hex(va), "aligned_hits": hits}
                )
            stbl_ram = []
            start = 0
            while len(stbl_ram) < 30:
                i = ram.find(b"STBL", start)
                if i < 0:
                    break
                kind = ram[i : i + 5]
                stbl_ram.append(
                    {"off": hex(i), "kind": kind.decode("ascii", "replace")}
                )
                start = i + 1
            ram_info["stbl_offsets_sample"] = stbl_ram
            results["ram_corr"] = ram_info
            print("RAM STBL", ram_info["stbl_counts"], "gfc sig", ram_info["gfc_sig_hits"][:5])

        chain_lens = []
        for fe in igb_files[:500]:
            b = fe["first"]
            n = 0
            guard = 0
            while b != 0x7FFF and b < nblocks and guard < 10000:
                b = blocks[b][2]
                n += 1
                guard += 1
            chain_lens.append(n)
        if chain_lens:
            results["gfc"]["igb_chain_len_stats"] = {
                "sample": min(500, len(igb_files)),
                "min": min(chain_lens),
                "max": max(chain_lens),
                "avg": sum(chain_lens) / len(chain_lens),
            }

        largest = sorted(files, key=lambda x: -x["size"])[:20]
        results["gfc"]["largest_files"] = [
            {
                "name": f["name"],
                "size": f["size"],
                "crc": f"{f['crc']:08X}",
                "first": f["first"],
            }
            for f in largest
        ]
        interesting_ext = [
            f
            for f in files
            if f["name"]
            and any(
                f["name"].lower().endswith(e)
                for e in (".csv", ".ini", ".txt", ".igm", ".opt")
            )
        ]
        results["gfc"]["configish"] = [
            {"name": f["name"], "size": f["size"], "crc": f"{f['crc']:08X}"}
            for f in interesting_ext[:40]
        ]

        # Compress-size histogram for blocks
        sizes = [b[0] for b in blocks]
        results["gob_stbl"]["block_comp_size"] = {
            "min": min(sizes),
            "max": max(sizes),
            "avg": sum(sizes) / len(sizes),
        }

        json_path = OUT_DIR / "alchemy-rebuild-w2-cnk-binwalk-toc-2026-11-07.json"
        json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print("JSON", json_path)
        print("DONE")
        mm.close()


if __name__ == "__main__":
    main()
