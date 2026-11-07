import sqlite3, json, re

db = r"C:\Users\joshy\AppData\Roaming\Cursor\User\globalStorage\state.vscdb"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
cur = con.cursor()

keys = [
    "cursor/initialModelState",
    "cursor/seenNewModelBadgeModelNames",
    "cursor/selectedDismissibleModelBadgeKeys",
    "cursor/modelNudgesEnabled",
    "src.vs.platform.reactivestorage.browser.reactiveStorageServiceImpl.persistentStorage.applicationUser",
]

for k in keys:
    row = cur.execute("SELECT value FROM ItemTable WHERE key=?", (k,)).fetchone()
    if not row:
        print("MISSING", k)
        continue
    v = row[0]
    if isinstance(v, bytes):
        v = v.decode("utf-8", "replace")
    print("\n====", k, "len", len(v))
    print(v[:8000])
    if len(v) > 8000:
        print("...[truncated]...")

# cursorDiskKV model-ish keys
print("\n==== cursorDiskKV keys sample ====")
try:
    rows = cur.execute(
        "SELECT key FROM cursorDiskKV WHERE key LIKE '%model%' OR key LIKE '%Model%' OR key LIKE '%catalog%' LIMIT 50"
    ).fetchall()
    for (k,) in rows:
        print(k)
except Exception as e:
    print("err", e)

# Search applicationUser JSON for model catalog fields
row = cur.execute(
    "SELECT value FROM ItemTable WHERE key=?",
    ("src.vs.platform.reactivestorage.browser.reactiveStorageServiceImpl.persistentStorage.applicationUser",),
).fetchone()
if row:
    raw = row[0]
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    data = json.loads(raw)
    print("\n==== applicationUser top keys ====")
    for k in sorted(data.keys()):
        print(k)
    for want in ["availableModels", "modelConfig", "models", "aiSettings", "composerState", "chatModel", "modelState", "featureModelConfigs", "usableModels", "defaultModel"]:
        for k in data.keys():
            if want.lower() in k.lower():
                s = json.dumps(data[k])
                print(f"\nFOUND {k} len={len(s)}")
                print(s[:3000])

    # Deep search for composer-2 / grok model ids in nested structure
    blob = json.dumps(data)
    ids = sorted(set(re.findall(
        r'"(?:composer-2[^"]*|grok-4[^"]*|claude-[^"]*|gpt-5[^"]*|gemini-[^"]*|muse-[^"]*|cursor-[^"]*)"',
        blob,
    )))
    print("\n==== model-like ids in applicationUser ====")
    for i in ids[:80]:
        print(i)
    print("total", len(ids))
