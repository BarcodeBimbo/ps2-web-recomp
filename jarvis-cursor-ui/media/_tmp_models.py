import sqlite3, json, re

db = r"C:\Users\joshy\AppData\Roaming\Cursor\User\globalStorage\state.vscdb"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
cur = con.cursor()
print("tables:", cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())

keys = cur.execute(
    "SELECT key FROM ItemTable WHERE "
    "key LIKE '%model%' OR key LIKE '%Model%' OR key LIKE '%composer%' "
    "OR key LIKE '%aichat%' OR key LIKE '%availableModels%' OR key LIKE '%aiService%' "
    "OR key LIKE '%cursor/%' OR key LIKE '%cursor.%' "
    "LIMIT 200"
).fetchall()
print("key count", len(keys))
for (k,) in keys:
    print("K", k)

# Dump interesting values (truncated)
interesting = []
for (k,) in keys:
    kl = k.lower()
    if any(x in kl for x in ["available", "modelids", "modellist", "defaultmodel", "selectedmodel", "composer.model", "aichat", "aiservice", "enabledmodels", "modelconfig"]):
        interesting.append(k)

print("\nINTERESTING", interesting)
for k in interesting[:30]:
    row = cur.execute("SELECT value FROM ItemTable WHERE key=?", (k,)).fetchone()
    if not row:
        continue
    v = row[0]
    if isinstance(v, bytes):
        try:
            v = v.decode("utf-8", "replace")
        except Exception:
            v = repr(v[:200])
    s = str(v)
    print("\n===", k, "len", len(s))
    print(s[:1500])

# Also search values containing composer-2 or grok-4.7
print("\n--- value scan ---")
rows = cur.execute("SELECT key, value FROM ItemTable").fetchall()
hits = []
for k, v in rows:
    if v is None:
        continue
    if isinstance(v, bytes):
        try:
            s = v.decode("utf-8", "replace")
        except Exception:
            continue
    else:
        s = str(v)
    if re.search(r"composer-2|grok-4\.7|claude-opus-5|gpt-5\.6|availableModels|modelPicker", s, re.I):
        hits.append((k, s[:300]))
print("hits", len(hits))
for k, s in hits[:40]:
    print(k, "=>", s.replace("\n", " ")[:250])
