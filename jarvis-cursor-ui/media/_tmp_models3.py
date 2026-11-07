import sqlite3, json

db = r"C:\Users\joshy\AppData\Roaming\Cursor\User\globalStorage\state.vscdb"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
cur = con.cursor()
row = cur.execute(
    "SELECT value FROM ItemTable WHERE key=?",
    ("src.vs.platform.reactivestorage.browser.reactiveStorageServiceImpl.persistentStorage.applicationUser",),
).fetchone()
data = json.loads(row[0])
models = data["availableDefaultModels2"]
print("TOTAL", len(models))

# Prefer defaultOn models with clientDisplayName; skip Auto variants that are just "default" aliases if needed
out = []
for m in models:
    name = m.get("name")
    display = m.get("clientDisplayName") or m.get("inputboxShortModelName") or name
    default_on = bool(m.get("defaultOn"))
    deg = m.get("degradationStatus", 0)
    out.append({
        "id": name,
        "display": display,
        "defaultOn": default_on,
        "degradationStatus": deg,
        "supportsAgent": m.get("supportsAgent"),
    })

on = [x for x in out if x["defaultOn"]]
off = [x for x in out if not x["defaultOn"]]
print("\nDEFAULT ON", len(on))
for x in on:
    print(f"  {x['id']:40} | {x['display']:28} | deg={x['degradationStatus']}")

print("\nDEFAULT OFF sample", len(off))
for x in off[:20]:
    print(f"  {x['id']:40} | {x['display']}")

# Write catalog snapshot for the extension
catalog = {
    "source": "Cursor User globalStorage state.vscdb → applicationUser.availableDefaultModels2",
    "syncedFrom": "this machine Cursor reactive storage",
    "models": [
        {
            "id": x["id"],
            "label": x["display"],
            "defaultOn": x["defaultOn"],
            "degradationStatus": x["degradationStatus"],
        }
        for x in out
    ],
}
path = r"c:\PS2Recomp\jarvis-cursor-ui\media\inject\cursor-models.json"
with open(path, "w", encoding="utf-8") as f:
    json.dump(catalog, f, indent=2)
print("\nWROTE", path, "models", len(catalog["models"]))

# Pick 8 chips for 2x4 grid: Auto + primary Cursor first-party + key third-party defaultOn
priority = [
    "default",
    "composer-2.5",
    "grok-4.7",
    "grok-4.6",
    "grok-4.5",
    "claude-opus-5-5",
    "claude-sonnet-5-5",
    "gpt-5.6-sol",
    "gemini-4-argon",
    "muse-wonder-1.0",
    "claude-fable-5-1",
]
by_id = {x["id"]: x for x in out}
picked = []
for pid in priority:
    # fuzzy: exact or startswith
    if pid in by_id:
        picked.append(by_id[pid])
    else:
        for x in out:
            if x["id"] == pid or x["id"].startswith(pid):
                picked.append(x)
                break
    if len(picked) >= 8:
        break
# fill from defaultOn if short
if len(picked) < 8:
    for x in on:
        if x not in picked and x["id"] != "default":
            picked.append(x)
        if len(picked) >= 8:
            break

print("\nPICKED 8:")
for x in picked[:8]:
    status = "Available" if x["defaultOn"] and x["degradationStatus"] == 0 else (
        "Degraded" if x["degradationStatus"] else "Off"
    )
    print(f"  {x['display']} ({x['id']}) → {status}")
