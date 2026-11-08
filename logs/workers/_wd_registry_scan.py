import json
import pathlib
from datetime import datetime

root = pathlib.Path(r"C:\PS2Recomp\games")
reg_path = pathlib.Path(r"C:\PS2Recomp\verification\recovery\game-fix-registry.json")
reg = json.loads(reg_path.read_text(encoding="utf-8"))
have = set(reg["per_game"])

MATRIX = {
    "c0c4527037b6168660829a0eb13df1a3": ("sly1", ["gs_stq_path3_clut", "live_matrix"], 600),
    "76615f9956b13094771e370c883c7170": ("defjam_ffny", ["live_matrix"], 600),
    "1e5a12a02722175839d88d0301949cd9": ("ratchet2", ["library"], 600),
    "34402ee3c1917272f971028b4fb24868": ("gow2", ["fps_followon", "library"], 600),
    "9ce58de36f3fbe96fb260a3221d91f20": ("gt4", ["library"], 600),
    "c0671389c296be6afe9e5224c97d30df": ("nfs_ug2", ["disc_fix_stable", "library"], 600),
    "f141051d9b9fae0fb48deced01311f44": ("hitman2_sa", ["gs_black_canvas", "library"], 600),
    "f29093e1f939f924fb11cc605b592b11": ("hsg3", ["library"], 400),
    "ffb47d7e14cf9f5c02425d9158c29b76": ("re4", ["library"], 600),
    "ff676a9829a95d13c3aba981334c0ae8": ("downhill_dom", ["library_duplicate"], 400),
}

added = []
for p in sorted(root.glob("*/library.json")):
    gid = p.parent.name
    lj = json.loads(p.read_text(encoding="utf-8"))
    title = lj.get("title") or gid
    status = lj.get("status")
    mark = "HAVE" if gid in have else "MISS"
    print(f"{mark} {gid} title={title!r} status={status!r}")
    if gid in have:
        # refresh title from library if stub
        if not reg["per_game"][gid].get("title"):
            reg["per_game"][gid]["title"] = title
        continue
    mk, tracks, frames = MATRIX.get(gid, ("unknown", ["library"], 400))
    entry = {
        "title": title,
        "matrix_key": mk,
        "tracks": tracks,
        "smoke_frames": frames,
        "library_status": status,
        "registry_seeded_by": "overnight-watchdog",
    }
    if status == "duplicate" and lj.get("duplicate_of"):
        entry["duplicate_of"] = lj["duplicate_of"]
    reg["per_game"][gid] = entry
    added.append(gid)

cnk = reg["per_game"].get("b49f2e769315347e8bda839feb705744")
if cnk is not None and "proven_fixes" not in cnk:
    cnk["proven_fixes"] = []

# Hitman known_issues note from overnight compose research (additive)
hit = reg["per_game"].get("a2116d2ac08a7be4db4e8455ad58d2e5")
if hit is not None:
    issues = hit.setdefault("known_issues", [])
    for issue in ("dispfb400_vs_frame288", "compose_mode_b_sprite_tex"):
        if issue not in issues:
            issues.append(issue)

now = datetime.now().astimezone()
reg["updated"] = now.strftime("%Y-%m-%dT%H:%M:%S") + now.strftime("%z")
if len(reg["updated"]) >= 5 and reg["updated"][-5] in "+-" and ":" not in reg["updated"][-5:]:
    reg["updated"] = reg["updated"][:-2] + ":" + reg["updated"][-2:]

reg_path.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
out = {
    "added": added,
    "total": len(reg["per_game"]),
    "updated": reg["updated"],
}
pathlib.Path(r"C:\PS2Recomp\logs\overnight-watchdog-registry-seed-2026-11-07.json").write_text(
    json.dumps(out, indent=2) + "\n", encoding="utf-8"
)
print("ADDED", len(added), added)
print("TOTAL", len(reg["per_game"]))
