# Campaign owner — permanent overnight mode

**Encoded:** 2026-11-07 ~19:04 (God final standing order)  
**Authority:** `logs/call-log-2026-11-07.md` §8  
**Seed on every resume:** this file + `verification/recovery/AGENT-CAMPAIGN-SNAPSHOT.md` + `logs/master-campaign-plan-2026-11-07.md`

## Rules

1. Non-stop: testing, updating, fixing, improving — until God personally says stop.
2. Never idle. Never wait for permission.
3. Checkbox done → immediately next open checkbox (no celebration pause).
4. No kill-on-retry. No session-end stalls. Fresh agent + snapshot on overflow/crash.
5. Single-writer locks per build; parallel platform lanes (not one-game monopoly).
6. Speak/report to God **only** on: breakage, or major verified green.

## Heartbeat

Keep `logs/campaign-owner-alive.txt` + `logs/campaign-owner-heartbeat.json` fresh (~60s). Silence to God ≠ idle.
