#!/usr/bin/env python3
import json
import os
import sqlite3

db = os.path.join(os.environ["APPDATA"], "Cursor", "User", "globalStorage", "state.vscdb")
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
cur = con.cursor()
key = "src.vs.platform.reactivestorage.browser.reactiveStorageServiceImpl.persistentStorage.applicationUser"
raw = cur.execute("SELECT value FROM ItemTable WHERE key=?", (key,)).fetchone()[0]
data = json.loads(raw)
models = data.get("availableDefaultModels2") or []
out = []
for m in models:
    out.append(
        {
            "id": m.get("name") or m.get("serverModelName"),
            "label": m.get("clientDisplayName") or m.get("inputboxShortModelName"),
            "defaultOn": bool(m.get("defaultOn")),
            "degradationStatus": m.get("degradationStatus", 0),
            "supportsAgent": bool(m.get("supportsAgent")),
            "serverModelName": m.get("serverModelName"),
        }
    )
print(json.dumps({"count": len(out), "models": out}, indent=2))
