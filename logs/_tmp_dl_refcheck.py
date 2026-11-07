from pathlib import Path

root = Path(r"c:/PS2Recomp")
dl = root / "downloads"
games = root / "games"

game_ids = {p.name for p in games.iterdir() if p.is_dir()} if games.exists() else set()
print("game_ids", len(game_ids))

dl_stems = []
for p in sorted(dl.iterdir(), key=lambda x: x.name.lower()):
    name = p.name
    stem = name
    for suf in (
        ".7z.webtorrent-store",
        ".browser-dl",
        ".7z.part",
        ".zip",
        ".7z",
    ):
        if name.endswith(suf):
            stem = name[: -len(suf)]
            break
    if stem.startswith("_"):
        kind = "probe"
    elif name.endswith(".part") or name.endswith(".webtorrent-store") or name.endswith(".browser-dl"):
        kind = "incomplete"
    elif name.endswith(".zip") or name.endswith(".7z"):
        kind = "complete"
    else:
        kind = "other"
    sz = p.stat().st_size if p.is_file() else sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
    dl_stems.append((stem, name, sz, kind, stem in game_ids))

print("=== downloads vs games/ id overlap ===")
for stem, name, sz, kind, hit in dl_stems:
    tag = "MATCH_GAME_ID" if hit else "no_game_id"
    print(f"  [{kind:10}] [{tag:14}] {sz/(1024**3):6.2f} GB  {name}")

# Search active project code for path references to downloads/ and each hash
search_roots = [
    root / "config",
    root / "downloader",
    root / "web",
    root / "tools",
    root / "runtime",
    root / "tests",
    root,
]
skip_parts = {"node_modules", ".git", "RomDL", "build", "tools", "downloads", "logs", "generated"}
exts = {".py", ".mjs", ".js", ".ts", ".json", ".html", ".md", ".cmake", ".txt", ".cmd", ".ps1", ".yml", ".yaml"}

hashes = [s for s, *_ in dl_stems if not s.startswith("_") and len(s) >= 16]
path_hits = []
hash_hits = {h: [] for h in hashes}

for sr in search_roots:
    if not sr.exists():
        continue
    files = []
    if sr == root:
        files = [p for p in sr.iterdir() if p.is_file()]
    else:
        for p in sr.rglob("*"):
            if not p.is_file():
                continue
            if any(part in skip_parts for part in p.parts):
                continue
            files.append(p)
    for p in files:
        if p.suffix.lower() not in exts and p.name not in {"CMakeLists.txt", "Setup.cmd"}:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = str(p.relative_to(root))
        if "downloads/" in text.replace("\\", "/") or "downloads\\" in text:
            # ignore emsdk generic "downloads" docs noise by requiring project-ish context
            if "PS2Recomp" in text or "destination" in text or "store" in text.lower() or "games/" in text or "disc" in text.lower():
                path_hits.append(rel)
        for h in hashes:
            if h in text:
                hash_hits[h].append(rel)

print("=== code/docs mentioning downloads/ (filtered) ===")
for rel in sorted(set(path_hits))[:40]:
    print(" ", rel)

print("=== per-archive hash mentions outside downloads/ ===")
any_hash = False
for h, refs in hash_hits.items():
    refs = [r for r in refs if not r.startswith("downloads")]
    if refs:
        any_hash = True
        print(h, refs[:10])
if not any_hash:
    print("  none")

# How builds consume discs: look for games/<id>/disc
print("=== sample games disc presence ===")
for gid in sorted(game_ids)[:5]:
    g = games / gid
    iso = g / "disc.iso"
    print(f"  {gid[:12]}... disc.iso={iso.exists()} size_GB={(iso.stat().st_size/(1024**3) if iso.exists() else 0):.2f}")
