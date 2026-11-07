"""End-to-end verification checks for alchemy-map.json (CNK expectations)."""

from __future__ import annotations

from typing import Any


# Anchors from A1–A2 research for Crash Nitro Kart.
CNK_EXPECT = {
    "gfc_magic": "0x00008008",
    "gfc_nfiles": 1830,
    "gfc_nblocks": 4327,
    "igb_ext_count": 520,
    "vag_ext_count": 541,
    "csv_ext_count": 519,
    "ig_class_min": 580,
    "ig_class_max": 620,
    "igb_raw_hits": 47,
    "igb_path_strings_min": 20,
    "modules_irx_min": 10,
    "alchemy_irx_absent": ("igFileIO.irx", "igUKbd.irx", "igUMouse.irx"),
    "version_substr": "Intrinsic Alchemy",
}


def verify_alchemy_map(doc: dict[str, Any], *, profile: str = "cnk") -> list[dict]:
    """Return list of {name, ok, detail}. Empty failures => clean run."""
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    if profile != "cnk":
        add("profile", False, f"unknown profile {profile!r}")
        return checks

    exp = CNK_EXPECT
    gfc = doc.get("assets_gfc") or {}
    gob = doc.get("assets_gob") or {}
    elf = doc.get("elf_alchemy") or {}
    mods = doc.get("modules") or {}
    samples = doc.get("igb_samples") or []

    add("gfc_present", bool(gfc.get("present")), f"present={gfc.get('present')}")
    add(
        "gfc_magic",
        gfc.get("magic") == exp["gfc_magic"],
        f"got {gfc.get('magic')}",
    )
    add(
        "gfc_nfiles",
        gfc.get("nfiles") == exp["gfc_nfiles"],
        f"got {gfc.get('nfiles')}",
    )
    add(
        "gfc_nblocks",
        gfc.get("nblocks") == exp["gfc_nblocks"],
        f"got {gfc.get('nblocks')}",
    )

    census = gfc.get("ext_census") or {}
    add(
        "ext_igb",
        census.get(".igb") == exp["igb_ext_count"],
        f"got {census.get('.igb')}",
    )
    add(
        "ext_vag",
        census.get(".vag") == exp["vag_ext_count"],
        f"got {census.get('.vag')}",
    )
    add(
        "ext_csv",
        census.get(".csv") == exp["csv_ext_count"],
        f"got {census.get('.csv')}",
    )

    add("gob_present", bool(gob.get("present")), f"present={gob.get('present')}")
    verify = gob.get("block_verify") or []
    stbl_ok = bool(verify) and all(v.get("is_stbl") for v in verify)
    add("gob_block_verify_stbl", stbl_ok, f"checked={len(verify)}")

    add("elf_present", bool(elf), "elf_alchemy missing" if not elf else "ok")
    ver = (elf.get("alchemy_version") or {}).get("string") or ""
    add(
        "alchemy_version",
        exp["version_substr"] in ver,
        f"got {ver!r}",
    )
    nclass = elf.get("ig_class_whole_strings") or 0
    add(
        "ig_class_count",
        exp["ig_class_min"] <= nclass <= exp["ig_class_max"],
        f"got {nclass}",
    )
    add(
        "igb_raw_hits",
        elf.get("igb_raw_hits") == exp["igb_raw_hits"],
        f"got {elf.get('igb_raw_hits')} (A1 raw .igb count)",
    )
    add(
        "igb_path_strings",
        (elf.get("igb_path_strings") or 0) >= exp["igb_path_strings_min"],
        f"got {elf.get('igb_path_strings')} unique",
    )

    irx = mods.get("irx") or []
    add(
        "modules_irx_count",
        len(irx) >= exp["modules_irx_min"],
        f"got {len(irx)}",
    )
    absent = mods.get("alchemy_irx_on_disc") or {}
    for name in exp["alchemy_irx_absent"]:
        add(
            f"absent_{name}",
            absent.get(name) is False,
            f"got {absent.get(name)}",
        )

    # IGB samples: at least one successful inflate with DA FA
    ok_samples = [
        s
        for s in samples
        if s.get("error") is None
        and s.get("extracted_len", 0) > 0
        and (s.get("da_fa_at_0x28") or s.get("da_fa_offset") is not None)
    ]
    add(
        "igb_da_fa_samples",
        len(ok_samples) >= 1,
        f"ok_samples={len(ok_samples)} total={len(samples)}",
    )

    # Priority butanim should be among successes when present
    butanim = [
        s
        for s in samples
        if "butanim.igb" in (s.get("name") or "").lower().replace("\\", "/")
    ]
    if butanim:
        b = butanim[0]
        add(
            "butanim_da_fa",
            bool(b.get("da_fa_at_0x28") or b.get("da_fa_offset") is not None)
            and b.get("error") is None,
            f"da_fa_at_0x28={b.get('da_fa_at_0x28')} err={b.get('error')}",
        )

    return checks


def summarize(checks: list[dict]) -> tuple[int, int]:
    passed = sum(1 for c in checks if c["ok"])
    return passed, len(checks)
