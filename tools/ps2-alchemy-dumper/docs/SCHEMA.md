# alchemy-map.json schema

Version: `1.1` (field `meta.schema_version`)

```json
{
  "meta": {
    "schema_version": "1.1",
    "tool": "ps2-alchemy-dumper",
    "tool_version": "0.2.0",
    "generated_at": "ISO-8601",
    "input_iso": "absolute path",
    "game_id_hint": "optional hash folder name",
    "platform_target": "windows"
  },
  "disc_toc": [
    { "path": "ASSETS.GFC", "lba": 1518969, "size": 222968, "flags": 0, "is_dir": false }
  ],
  "assets_gfc": {
    "present": true,
    "magic": "0x00008008",
    "gob_size": 88856576,
    "nblocks": 4327,
    "nfiles": 1830,
    "name_stride": 72,
    "ext_census": { ".igb": 520, ".vag": 541 },
    "files": [
      {
        "index": 0,
        "name": ".\\ps2\\gfx\\ui\\butanim.igb",
        "crc32": "0xD4E36BE1",
        "uncompressed_size": 4248,
        "first_block": 3801
      }
    ]
  },
  "assets_gob": {
    "present": true,
    "lba": 1519078,
    "size": 88856576,
    "gob_size_matches_gfc": true,
    "block_verify_all_stbl": true,
    "block_verify": [
      { "index": 0, "head_tag": "STBLz", "is_stbl": true }
    ]
  },
  "igb_samples": [
    {
      "name": ".\\ps2\\gfx\\ui\\butanim.igb",
      "crc32": "0xD4E36BE1",
      "da_fa_offset": 40,
      "da_fa_at_0x28": true,
      "version_word_le": "0x80000005",
      "ig_meta_count": 74,
      "extracted_len": 4248,
      "error": null
    }
  ],
  "elf_alchemy": {
    "alchemy_version": {
      "string": "Intrinsic Alchemy  v3.0 -0909 (Static/Release)",
      "va": "0x006B4920",
      "found": true
    },
    "key_vas": { "loadgate_fce0": "0x0010FCE0", "bind_registry_bss": "0x00725F50" },
    "ig_class_whole_strings": 595,
    "igb_raw_hits": 47,
    "igb_path_strings": 28,
    "named_irx_in_elf": ["igFileIO.irx", "igUKbd.irx", "igUMouse.irx"],
    "prefix_density": { "Psx2": 40 },
    "ig_class_catalog_count": 595
  },
  "elf_gfc_correlation": [
    { "gfc_name": "...", "needle": "butanim.igb", "approx_va": "0x0061...." }
  ],
  "modules": {
    "irx": ["PADMAN.IRX", "LIBSD.IRX"],
    "alchemy_irx_on_disc": {
      "igFileIO.irx": false,
      "igUKbd.irx": false,
      "igUMouse.irx": false
    }
  },
  "notes": []
}
```

## TSV sidecars

| File | Columns |
|------|---------|
| `disc-toc.tsv` | path, lba, size, flags, is_dir |
| `gfc-files.tsv` | index, name, crc32, uncompressed_size, first_block |
| `igb-samples.tsv` | name, crc32, size, first_block, extracted_len, da_fa_*, error, ig_meta_count |
| `class-map.tsv` | index, class (`ig*` whole-string catalog) |
