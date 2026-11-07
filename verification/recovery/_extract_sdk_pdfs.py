#!/usr/bin/env python3
"""Extract key PS2 SDK PDFs to text for R1-R5 compliance audit."""
from pathlib import Path
import re
import sys

from pypdf import PdfReader

OUT = Path(r"C:\PS2Recomp\verification\recovery\_sdk_pdf_extract")
OUT.mkdir(parents=True, exist_ok=True)

PDFS = [
    r"E:\usr\local\sce\doc\tips\cdvdtips_3.0.pdf",
    r"E:\usr\local\sce\doc\ee\PS2_EE-Overview-Device-3.0.2.pdf",
    r"E:\usr\local\sce\doc\ee\PS2_EE-Reference-Device-3.0.3.pdf",
    r"E:\usr\local\sce\doc\ee\PS2_EE-Overview-Sif-3.0.pdf",
    r"E:\usr\local\sce\doc\ee\PS2_EE-Reference-Sif-3.0.2.pdf",
    r"E:\usr\local\sce\doc\iop\PS2_IOP-Overview-Kernel-3.0.pdf",
    r"E:\usr\local\sce\doc\iop\PS2_IOP-Reference-Sif-3.0.2.pdf",
    r"E:\usr\local\sce\doc\ee\PS2_EE-Overview-Sound-3.0.2.pdf",
    r"E:\usr\local\sce\doc\ee\PS2_EE-Reference-Sound-3.0.1.pdf",
    r"E:\usr\local\sce\doc\iop\PS2_IOP-Overview-Sound-3.0.1.pdf",
    r"E:\usr\local\sce\doc\iop\PS2_IOP-Reference-Sound-3.0.2.pdf",
    r"E:\usr\local\sce\doc\iop\PS2_IOP-Overview-Device-3.0.pdf",
    r"E:\usr\local\sce\doc\iop\PS2_IOP-Reference-Device-3.0.2.pdf",
    r"E:\usr\local\sce\doc\ee\PS2_EE-Overview-Kernel-3.0.2.pdf",
]

KEYS = [
    "sceCdSync",
    "DiskReady",
    "sceCdDiskReady",
    "AlignRead",
    "readee",
    "b1len",
    "WaitSema",
    "Alchemy",
    "Intrinsic",
    "padman",
    "libsd",
    "sceSd",
    "scePad",
    "sceSif",
    "CallRpc",
    "GetReadPos",
    "sceCdRead",
    "sceCdStatus",
]


def extract(pdf: Path) -> str:
    reader = PdfReader(str(pdf))
    parts = []
    for i, page in enumerate(reader.pages):
        try:
            t = page.extract_text() or ""
        except Exception as e:  # noqa: BLE001
            t = f"[extract error page {i}: {e}]"
        parts.append(f"\n\n===== PAGE {i + 1} =====\n\n{t}")
    return "".join(parts)


def main() -> int:
    for p in PDFS:
        pdf = Path(p)
        if not pdf.exists():
            print(f"MISSING {pdf}")
            continue
        text = extract(pdf)
        dest = OUT / (pdf.name + ".txt")
        dest.write_text(text, encoding="utf-8", errors="replace")
        print(f"{pdf.name}: pages chars={len(text)}")
        low = text.lower()
        for k in KEYS:
            cnt = low.count(k.lower())
            if cnt:
                print(f"  HIT {k}: {cnt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
