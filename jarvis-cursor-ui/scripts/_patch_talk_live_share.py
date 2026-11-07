#!/usr/bin/env python3
"""Wake/voice: set .jcc-talk.is-live + share getUserMedia stream with waveform agent."""
from pathlib import Path

WI = Path(__file__).resolve().parents[1] / "src" / "workbenchInject.js"
text = WI.read_text(encoding="utf-8")

# --- Shared helpers injected into voice script (loads before wake) ---
VOICE_SHARE_HELPERS = r'''
    "var liveTimer=0;",
    "function talkEl(){return document.getElementById('cortana-talk-cta')||document.querySelector('#cortana-cc-hud .jcc-talk');}",
    "function setTalkLive(on){",
    "var talk=talkEl(),h=document.getElementById('cortana-cc-hud');",
    "on=!!on;",
    "if(talk){talk.classList.toggle('is-live',on);if(on)talk.setAttribute('data-voice-live','1');else talk.removeAttribute('data-voice-live');}",
    "if(h){if(on)h.setAttribute('data-voice-live','1');else h.removeAttribute('data-voice-live');}",
    "try{window.dispatchEvent(new CustomEvent('cortana-voice-live',{detail:{live:on}}));}catch(e){}",
    "}",
    "function publishMic(stream,meta){",
    "if(!stream)return;",
    "window.__cortanaMicStream=stream;",
    "if(typeof window.__cortanaOnMicStream==='function'){",
    "try{window.__cortanaOnMicStream(stream,meta||{source:'voice'});}catch(e){}",
    "}",
    "try{window.dispatchEvent(new CustomEvent('cortana-mic-stream',{detail:{stream:stream,meta:meta||{source:'voice'}}}));}catch(e){}",
    "}",
    "function ensureTalkMic(meta,cb){",
    "var existing=window.__cortanaMicStream;",
    "if(existing&&existing.active){publishMic(existing,meta);if(cb)cb(existing);return;}",
    "var md=navigator.mediaDevices;",
    "if(!md||!md.getUserMedia){if(cb)cb(null);return;}",
    "md.getUserMedia({audio:true}).then(function(stream){",
    "publishMic(stream,meta);if(cb)cb(stream);",
    "}).catch(function(){if(cb)cb(null);});",
    "}",
    "function beginTalkSession(source){",
    "setTalkLive(true);",
    "ensureTalkMic({source:source||'voice',live:true});",
    "clearTimeout(liveTimer);",
    "liveTimer=setTimeout(function(){setTalkLive(false);},18000);",
    "}",
    "window.__cortanaSetTalkLive=setTalkLive;",
    "window.__cortanaPublishMicStream=publishMic;",
    "window.__cortanaEnsureTalkMic=ensureTalkMic;",
    "window.__cortanaBeginTalkSession=beginTalkSession;",
'''

# Insert helpers after __cortanaVoiceWired line if not present
if "__cortanaBeginTalkSession" not in text:
    needle = '"if(window.__cortanaVoiceWired)return;window.__cortanaVoiceWired=true;",'
    if needle not in text:
        raise SystemExit("voice wired needle missing")
    text = text.replace(
        needle,
        needle + "\n" + VOICE_SHARE_HELPERS,
        1,
    )
    print("inserted share helpers into voice script")
else:
    print("share helpers already present")

# Patch startVoice to begin talk session
old_start = '''    "function startVoice(){",
    "signal();",
    "revealIde();",
    "if(tryVoiceDom()){toast('Voice channel — Cursor mic engaged');return;}",'''

new_start = '''    "function startVoice(){",
    "beginTalkSession('mic');",
    "signal();",
    "revealIde();",
    "if(tryVoiceDom()){toast('Voice channel — Cursor mic engaged');return;}",'''

if "beginTalkSession('mic')" not in text.split("function buildHudVoiceScript")[1].split("function buildHudWakeScript")[0]:
    if old_start not in text:
        raise SystemExit("startVoice block not found")
    text = text.replace(old_start, new_start, 1)
    print("patched startVoice beginTalkSession")
else:
    print("startVoice already begins talk session")

# --- Wake script: onWake begins talk session; arm publishes stream without stopping if callback wants it ---
# Replace onWake + arm getUserMedia sections

old_onwake = '''    "function onWake(){",
    "var now=Date.now();if(now-lastFire<4500)return;lastFire=now;",
    "setStatus('Cortana responding\\u2026','is-responding');",
    "invokeVoice();",
    "setTimeout(function(){if(armed&&wakeAllowed())setStatus('Listening\\u2026','is-listening');},2200);",
    "}",'''

new_onwake = '''    "function onWake(){",
    "var now=Date.now();if(now-lastFire<4500)return;lastFire=now;",
    "setStatus('Cortana responding\\u2026','is-responding');",
    "if(typeof window.__cortanaBeginTalkSession==='function'){",
    "try{window.__cortanaBeginTalkSession('wake');}catch(e){}",
    "}else{",
    "var talk=document.getElementById('cortana-talk-cta');",
    "if(talk){talk.classList.add('is-live');talk.setAttribute('data-voice-live','1');}",
    "var h=hud();if(h)h.setAttribute('data-voice-live','1');",
    "}",
    "invokeVoice();",
    "setTimeout(function(){if(armed&&wakeAllowed())setStatus('Listening\\u2026','is-listening');},2200);",
    "}",'''

if "__cortanaBeginTalkSession==='function'" not in text.split("function buildHudWakeScript")[1].split("function buildHudBlock")[0]:
    if old_onwake not in text:
        raise SystemExit("onWake block not found")
    text = text.replace(old_onwake, new_onwake, 1)
    print("patched onWake talk live")
else:
    print("onWake already begins talk session")

# Arm: keep stream shared for waveform agent instead of immediately stopping
old_arm_gum = '''    "if(md&&md.getUserMedia){",
    "md.getUserMedia({audio:true}).then(function(stream){",
    "try{stream.getTracks().forEach(function(t){t.stop();});}catch(e){}",
    "startRec();",
    "}).catch(function(){setStatus('Offline','is-offline');});",
    "}else{startRec();}",'''

new_arm_gum = '''    "if(md&&md.getUserMedia){",
    "md.getUserMedia({audio:true}).then(function(stream){",
    "if(typeof window.__cortanaPublishMicStream==='function'){",
    "try{window.__cortanaPublishMicStream(stream,{source:'wake-arm',live:false});}catch(e){}",
    "}else{window.__cortanaMicStream=stream;",
    "try{window.dispatchEvent(new CustomEvent('cortana-mic-stream',{detail:{stream:stream,meta:{source:'wake-arm',live:false}}}));}catch(e){}",
    "if(typeof window.__cortanaOnMicStream==='function'){try{window.__cortanaOnMicStream(stream,{source:'wake-arm',live:false});}catch(e){}}",
    "}",
    "startRec();",
    "}).catch(function(){setStatus('Offline','is-offline');});",
    "}else{startRec();}",'''

wake_part = text[text.index("function buildHudWakeScript") : text.index("function buildHudBlock")]
if "wake-arm" not in wake_part:
    if old_arm_gum not in text:
        raise SystemExit("arm getUserMedia block not found")
    text = text.replace(old_arm_gum, new_arm_gum, 1)
    print("patched arm to share mic stream")
else:
    print("arm already shares mic stream")

# buildHudBlock: include liveScript if missing
old_block = """function buildHudBlock({ uuid, markup, clockScript, voiceScript, wakeScript }) {
  return [
    `<!-- ${MARKER_HUD_START} uuid=${uuid} -->`,
    markup.trim(),
    clockScript,
    voiceScript || "",
    wakeScript || "",
    `<!-- ${MARKER_HUD_END} -->`,
  ].join("\\n");
}"""
new_block = """function buildHudBlock({ uuid, markup, clockScript, liveScript, voiceScript, wakeScript }) {
  return [
    `<!-- ${MARKER_HUD_START} uuid=${uuid} -->`,
    markup.trim(),
    clockScript,
    liveScript || "",
    voiceScript || "",
    wakeScript || "",
    `<!-- ${MARKER_HUD_END} -->`,
  ].join("\\n");
}"""
if "liveScript || \"\"" not in text.split("function buildHudBlock")[1][:400]:
    if old_block not in text:
        # try without escape
        old_block2 = old_block.replace("\\n", "\n")
        new_block2 = new_block.replace("\\n", "\n")
        if old_block2 not in text:
            print("WARN buildHudBlock pattern mismatch — skipping")
        else:
            text = text.replace(old_block2, new_block2, 1)
            print("patched buildHudBlock liveScript")
    else:
        text = text.replace(old_block, new_block, 1)
        print("patched buildHudBlock liveScript")
else:
    print("buildHudBlock already has liveScript")

# enable call site
if "liveScript: hudBundle.liveScript" not in text:
    old_call = """  const hudBlock = buildHudBlock({
    uuid: markerUuid,
    markup: hudBundle.markup,
    clockScript: hudBundle.clockScript,
    voiceScript: hudBundle.voiceScript,
    wakeScript: hudBundle.wakeScript,
  });"""
    new_call = """  const hudBlock = buildHudBlock({
    uuid: markerUuid,
    markup: hudBundle.markup,
    clockScript: hudBundle.clockScript,
    liveScript: hudBundle.liveScript,
    voiceScript: hudBundle.voiceScript,
    wakeScript: hudBundle.wakeScript,
  });"""
    if old_call in text:
        text = text.replace(old_call, new_call, 1)
        print("patched enable liveScript")
    else:
        print("WARN enable call pattern mismatch")
else:
    print("enable already passes liveScript")

# strip live script
if "cortana-hud-live-script" not in text.split("function stripHudMarkup")[1].split("function stripPatch")[0]:
    text = text.replace(
        """.replace(/<script[^>]*id=["']cortana-hud-clock-script["'][\\s\\S]*?<\\/script>\\s*/gi, "")""",
        """.replace(/<script[^>]*id=["']cortana-hud-clock-script["'][\\s\\S]*?<\\/script>\\s*/gi, "")
    .replace(/<script[^>]*id=["']cortana-hud-live-script["'][\\s\\S]*?<\\/script>\\s*/gi, "")""",
        1,
    )
    print("patched strip live script")

WI.write_text(text, encoding="utf-8")
print("wrote", WI)
