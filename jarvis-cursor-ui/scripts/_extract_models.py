#!/usr/bin/env python3
"""Extract Cursor model catalog from state.vscdb serverConfig + related keys."""
import json
import os
import re
import sqlite3
from collections import OrderedDict

DB = os.path.join(os.environ["APPDATA"], "Cursor", "User", "globalStorage", "state.vscdb")

INTERESTING_KEYS = [
    "cursorai/serverConfig",
    "cursor/seenNewModelBadgeModelNames",
    "cursor/initialModelState",
    "aicontext.personalContext",
    "cursorAuth/cachedEmail",
    "cursorAuth/stripeMembershipType",
    "cursorAuth/stripeSubscriptionStatus",
]


def get_item(cur, key):
    row = cur.execute("SELECT value FROM ItemTable WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


def walk_models(obj, found):
    if isinstance(obj, dict):
        # common shapes
        mid = obj.get("name") or obj.get("id") or obj.get("modelId") or obj.get("modelName")
        label = obj.get("clientDisplayName") or obj.get("displayName") or obj.get("title") or obj.get("label")
        if mid and isinstance(mid, str) and (
            any(x in mid for x in ("claude", "gpt", "gemini", "grok", "composer", "o3", "o4", "muse", "cursor", "deepseek", "sonnet", "opus", "haiku"))
            or (label and obj.get("provider") is not None)
        ):
            found[mid] = {
                "id": mid,
                "label": label or mid,
                "defaultOn": obj.get("defaultOn"),
                "supportsAgent": obj.get("supportsAgent"),
                "supportsTools": obj.get("supportsTools"),
                "provider": obj.get("provider") or obj.get("vendor"),
                "keys": sorted([k for k in obj.keys()])[:20],
            }
        for k, v in obj.items():
            kl = str(k).lower()
            if kl in ("models", "availablemodels", "modelconfigs", "modelcatalog", "hardcodedmodels", "modelnames", "allmodels"):
                walk_models(v, found)
            else:
                walk_models(v, found)
    elif isinstance(obj, list):
        for x in obj:
            walk_models(x, found)
    elif isinstance(obj, str):
        # bare model id strings
        if re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,80}", obj) and any(
            obj.startswith(p) for p in ("claude-", "gpt-", "gemini-", "grok-", "composer-", "o3", "o4-", "muse-", "deepseek-", "cursor-")
        ):
            found.setdefault(obj, {"id": obj, "label": obj})


def main():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    cur = con.cursor()

    # Dump interesting keys metadata
    for k in INTERESTING_KEYS:
        v = get_item(cur, k)
        print(f"KEY {k}: {'MISSING' if v is None else f'len={len(v)}'}")

    # Auth / membership for availability
    for k in (
        "cursorAuth/cachedEmail",
        "cursorAuth/stripeMembershipType",
        "cursorAuth/stripeSubscriptionStatus",
        "cursorAuth/cachedSignUpType",
        "cursorai/featureStatusCache",
    ):
        v = get_item(cur, k)
        if v is not None:
            print(f"AUTH {k} = {v[:500]}")

    raw = get_item(cur, "cursorai/serverConfig")
    cfg = json.loads(raw)
    print("\nserverConfig top keys:", sorted(cfg.keys()))

    # Find nested keys that look like model catalogs
    def find_paths(obj, path="$"):
        paths = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                p = f"{path}.{k}"
                kl = k.lower()
                if "model" in kl:
                    n = len(v) if isinstance(v, (list, dict)) else type(v).__name__
                    paths.append((p, n, type(v).__name__))
                paths.extend(find_paths(v, p))
        elif isinstance(obj, list) and obj and isinstance(obj[0], dict):
            # check first element
            if any("model" in str(k).lower() or k in ("name", "id") for k in obj[0].keys()):
                paths.append((path + "[]", len(obj), "list"))
        return paths

    paths = find_paths(cfg)
    print("\npaths with 'model':")
    for p, n, t in paths[:80]:
        print(f"  {p} -> {t} {n}")

    found = OrderedDict()
    walk_models(cfg, found)
    print(f"\n=== EXTRACTED MODELS ({len(found)}) ===")
    for mid, info in found.items():
        print(json.dumps(info, ensure_ascii=False))

    # Also pull modelMigrations targets
    migrations = cfg.get("modelMigrations") or []
    mig_models = set()
    for m in migrations:
        for field in ("targetModel", "previousModel"):
            if m.get(field):
                mig_models.add(m[field])
    print("\n=== MIGRATION MODELS ===")
    for m in sorted(mig_models):
        print(m)

    # seenNewModelBadgeModelNames
    badges = get_item(cur, "cursor/seenNewModelBadgeModelNames")
    if badges:
        print("\n=== BADGE MODELS ===")
        print(badges)

    # Search ItemTable for any value that looks like a JSON array of model objects with clientDisplayName
    print("\n=== scanning ItemTable for clientDisplayName catalogs ===")
    rows = cur.execute(
        "SELECT key, value FROM ItemTable WHERE value LIKE '%clientDisplayName%' OR value LIKE '%availableModels%' OR value LIKE '%\"models\":[{%' LIMIT 50"
    ).fetchall()
    for k, v in rows:
        print(f"HIT {k} len={len(v)}")
        # try parse and extract model names
        try:
            data = json.loads(v)
            f2 = OrderedDict()
            walk_models(data, f2)
            print(f"  models in key: {len(f2)}")
            for mid in list(f2)[:30]:
                print("   ", mid, "->", f2[mid].get("label"))
        except Exception as e:
            print("  parse err", e)

    # cursorDiskKV
    print("\n=== cursorDiskKV model-ish keys ===")
    try:
        kv = cur.execute(
            "SELECT key, length(value) FROM cursorDiskKV WHERE lower(key) LIKE '%model%' OR lower(key) LIKE '%available%' LIMIT 100"
        ).fetchall()
        for k, ln in kv:
            print(f"  {k} ({ln})")
    except Exception as e:
        print(e)

    con.close()


if __name__ == "__main__":
    main()
