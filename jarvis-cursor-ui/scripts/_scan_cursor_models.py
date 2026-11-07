#!/usr/bin/env python3
"""Scan Cursor state.vscdb + product/resources for model IDs."""
import json
import os
import re
import sqlite3
import sys

APPDATA = os.environ.get("APPDATA", "")
DB = os.path.join(APPDATA, "Cursor", "User", "globalStorage", "state.vscdb")
STORAGE = os.path.join(APPDATA, "Cursor", "User", "globalStorage", "storage.json")
PRODUCT = r"C:\Program Files\cursor\resources\app\product.json"


def scan_db(path: str) -> None:
    if not os.path.exists(path):
        print("NO DB", path)
        return
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    cur = con.cursor()
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    print("TABLES:", tables)
    for t in tables:
        info = list(cur.execute(f"PRAGMA table_info({t})"))
        colnames = [c[1] for c in info]
        print(f"COLS {t}:", colnames)
        if "key" not in colnames or "value" not in colnames:
            continue
        q = (
            f"SELECT key, value FROM {t} WHERE "
            "lower(key) LIKE '%model%' OR lower(key) LIKE '%composer%' OR "
            "lower(key) LIKE '%aichat%' OR lower(key) LIKE '%aiservice%' OR "
            "lower(key) LIKE '%available%' OR lower(key) LIKE '%llm%' OR "
            "lower(key) LIKE '%cursorai%' OR lower(key) LIKE '%openai%' OR "
            "lower(key) LIKE '%claude%' OR lower(key) LIKE '%agent%' OR "
            "lower(key) LIKE '%chat.%' OR lower(key) LIKE '%ai.%' "
            "LIMIT 300"
        )
        hits = list(cur.execute(q))
        print(f"\n=== KEY HITS in {t}: {len(hits)} ===")
        for k, v in hits:
            vs = v if isinstance(v, str) else (v.decode("utf-8", "replace") if isinstance(v, (bytes, bytearray)) else str(v))
            print(f"\nKEY: {k}")
            print(f"LEN: {len(vs)}")
            print(vs[:4000])
            if len(vs) > 4000:
                print("...[truncated]...")
    con.close()


def scan_storage(path: str) -> None:
    if not os.path.exists(path):
        print("NO STORAGE", path)
        return
    raw = open(path, "r", encoding="utf-8").read()
    print("\n=== storage.json size", len(raw), "===")
    for m in re.finditer(r".{0,40}(model|composer|claude|gpt-|gemini|grok).{0,80}", raw, re.I):
        print(m.group(0)[:200])


def scan_product(path: str) -> None:
    if not os.path.exists(path):
        print("NO PRODUCT", path)
        return
    raw = open(path, "r", encoding="utf-8").read()
    print("\n=== product.json size", len(raw), "===")
    data = json.loads(raw)
    print("top keys sample:", list(data.keys())[:80])
    for k, v in data.items():
        kl = k.lower()
        if any(x in kl for x in ("model", "ai", "chat", "composer", "agent")):
            s = json.dumps(v) if not isinstance(v, str) else v
            print(f"\nPRODUCT KEY {k}:", s[:2000])


def main() -> None:
    print("DB", DB)
    scan_db(DB)
    scan_storage(STORAGE)
    scan_product(PRODUCT)


if __name__ == "__main__":
    main()
