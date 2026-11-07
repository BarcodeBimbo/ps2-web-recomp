from pathlib import Path


def ppm_stats(path: Path):
    data = path.read_bytes()
    parts = []
    while len(parts) < 3:
        line, data = data.split(b"\n", 1)
        if not line.startswith(b"#"):
            parts.append(line)
    w, h = map(int, parts[1].split())
    rs, gs, bs = data[0::3], data[1::3], data[2::3]
    n = len(rs)
    nz = sum(1 for i in range(n) if rs[i] | gs[i] | bs[i])
    return {
        "w": w,
        "h": h,
        "r_mean": sum(rs) / n,
        "g_mean": sum(gs) / n,
        "b_mean": sum(bs) / n,
        "nz_pct": 100.0 * nz / n,
    }


for gid, label in [
    ("60c82f4a111da300ac23bbec85272788", "MW"),
    ("c0671389c296be6afe9e5224c97d30df", "U2"),
    ("b49f2e769315347e8bda839feb705744", "CNK"),
]:
    shots = sorted((Path("games") / gid / "shots").glob("frame_*.ppm"))
    print("===", label, len(shots), "===")
    chosen = shots[::3][:4] + (shots[-1:] if shots else [])
    for path in chosen:
        stats = ppm_stats(path)
        print(
            path.name,
            {k: (round(v, 1) if isinstance(v, float) else v) for k, v in stats.items()},
        )
