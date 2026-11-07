# -*- coding: utf-8 -*-
from pathlib import Path

raw = Path("logs/nfs-mw-sif0hold.log").read_bytes()
text = raw.decode("utf-8-sig") if raw.startswith(b"\xef\xbb\xbf") else raw.decode("utf-8", errors="replace")
marker = 'IOP reboot requested with ""'
idx = text.find(marker)
print("idx", idx)
after = text[idx : idx + 25000]
for l in after.splitlines()[:80]:
    print(l[:180])
print("---- counts ----")
print("80000002", after.count("80000002"))
print("bind", after.count("[sif] bind"))
print("call server", after.count("call server"))
print("to EE", after.count("[sif] to EE"))
