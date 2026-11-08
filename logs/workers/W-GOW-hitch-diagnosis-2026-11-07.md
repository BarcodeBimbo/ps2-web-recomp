# W-GOW hitch diagnosis — 2026-11-07 ~19:14

## Verdict
Prior FAIL is **panel/CPU contention**, not a GoW regression vs 2026-11-06 PASS.

## Evidence
| Signal | PASS (2026-11-06) | FAIL (19:05 run) |
|---|---|---|
| avg fps | 60.0 | 60.00 |
| min fps | 59.8 | **56.8** |
| below60 | 0 | **15** |
| audio queue | ~70–90 ms | **241–330 ms** (stable avg ~299) |
| Hitman panel | idle/ready | **building** |
| Host CPU | quieter | **100%** (16 logical) |

## Dip anatomy (stable t≥70)
- **t=72.0** worst: fps 56.8, on-screen 43, **hitch 197.8 ms**, q=241, dprim spike 29k→55k (scene burst under load).
- Later dips 59.0–59.4 with hitch 25–43 ms while q stays 250–330 ms — no discWaiting.
- Queue grew hold-long: early t<40 avg q≈171 → stable avg≈299 → end ≈330 (audio ahead / main-thread starvation under compile storm).

## Live contention (do not kill)
- ninja: 2× `ps2web -j1` (Hitman web-next + NFS web-next), 3× `ps2run` (-j1/-j4)
- panel Hitman status=`building`
- locks: web-a2116-next, web-60c82f, native-a2116, native-b49f2e

## Plan
1. Hold `logs/locks/gow-min60-browser.lock`.
2. Poll until CPU LoadPercentage ≲70 **or** Hitman panel ≠ building **and** fewer than 2 live ninja — then re-run `_gow_min60_accept.py 90 200 70` with Chrome AboveNormal.
3. Flip master-plan checkbox **only** if `pass_all_min60=true`.
