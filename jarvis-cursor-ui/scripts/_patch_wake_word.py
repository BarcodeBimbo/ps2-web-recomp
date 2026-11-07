#!/usr/bin/env python3
"""Add Hey Cortana wake-word inject script + wire buildHudBlock."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WI = ROOT / "src" / "workbenchInject.js"

WAKE_FN = r'''
/**
 * Hands-free wake word ("Hey Cortana") via SpeechRecognition.
 * Privacy: mic/recognition only while inject HUD is present and data-cortana-wake is on
 * (paused in Focus Mode / data-cortana-mute). No listening when injection is disabled.
 * Calls the same window.__cortanaStartVoice helper as the rail mic click.
 */
function buildHudWakeScript() {
  const body = [
    "(function(){",
    "if(window.__cortanaWakeWired)return;window.__cortanaWakeWired=true;",
    "var PHRASE=/\\bhey\\s+cortana\\b/i;",
    "var lastFire=0,rec=null,armed=false,want=true;",
    "function hud(){return document.getElementById('cortana-cc-hud');}",
    "function voiceBox(){var h=hud();return h?h.querySelector('.jcc-voice'):null;}",
    "function statusEl(){var h=hud();return h?(h.querySelector('#cortana-voice-status')||h.querySelector('.jcc-listen')):null;}",
    "function ovVoice(){var h=hud();return h?h.querySelector('[data-row=\"voice\"] .jcc-ov-v'):null;}",
    "function setStatus(text,mode){",
    "var s=statusEl(),box=voiceBox(),ov=ovVoice();",
    "if(s)s.textContent=text;",
    "if(box){box.classList.remove('is-listening','is-offline','is-responding');",
    "if(mode)box.classList.add(mode);}",
    "if(ov){if(mode==='is-offline'){ov.textContent='Offline';ov.setAttribute('data-tone','');}",
    "else if(mode==='is-listening'||mode==='is-responding'){ov.textContent='Online';ov.setAttribute('data-tone','ok');}",
    "}",
    "}",
    "function wakeAllowed(){",
    "var h=hud();if(!h)return false;",
    "var mute=(h.getAttribute('data-cortana-mute')||'').toLowerCase();",
    "if(mute==='1'||mute==='true'||mute==='on')return false;",
    "var wake=(h.getAttribute('data-cortana-wake')||'on').toLowerCase();",
    "if(wake==='off'||wake==='0'||wake==='false')return false;",
    "var focus=document.getElementById('cortana-focus-toggle');",
    "if(focus&&focus.checked)return false;",
    "return true;",
    "}",
    "function invokeVoice(){",
    "if(typeof window.__cortanaStartVoice==='function'){try{window.__cortanaStartVoice();return true;}catch(e){}}",
    "try{window.dispatchEvent(new CustomEvent('cortana-voice',{detail:{source:'wake',action:'talk'}}));}catch(e){}",
    "return false;",
    "}",
    "function onWake(){",
    "var now=Date.now();if(now-lastFire<4500)return;lastFire=now;",
    "setStatus('Cortana responding\\u2026','is-responding');",
    "invokeVoice();",
    "setTimeout(function(){if(armed&&wakeAllowed())setStatus('Listening\\u2026','is-listening');},2200);",
    "}",
    "function matches(text){",
    "var t=String(text||'').toLowerCase().replace(/[^a-z0-9\\s]/g,' ').replace(/\\s+/g,' ').trim();",
    "return PHRASE.test(t);",
    "}",
    "function stopRec(){",
    "armed=false;",
    "if(rec){try{rec.onend=null;rec.onerror=null;rec.onresult=null;rec.stop();}catch(e){}rec=null;}",
    "}",
    "function bindRec(r){",
    "r.continuous=true;r.interimResults=true;r.lang='en-US';",
    "r.onstart=function(){armed=true;if(wakeAllowed())setStatus('Listening\\u2026','is-listening');};",
    "r.onresult=function(ev){",
    "if(!wakeAllowed())return;",
    "for(var i=ev.resultIndex;i<ev.results.length;i++){",
    "var tr=ev.results[i][0]&&ev.results[i][0].transcript;",
    "if(matches(tr)){onWake();break;}",
    "}",
    "};",
    "r.onerror=function(ev){",
    "var err=ev&&ev.error?String(ev.error):'error';",
    "if(err==='aborted'||err==='no-speech')return;",
    "setStatus('Offline','is-offline');armed=false;",
    "};",
    "r.onend=function(){",
    "if(!want||!wakeAllowed()){armed=false;return;}",
    "try{r.start();}catch(e){setTimeout(function(){try{r.start();}catch(e2){setStatus('Offline','is-offline');}},400);}",
    "};",
    "}",
    "function startRec(){",
    "if(!wakeAllowed()){setStatus('Standby','');return;}",
    "var SR=window.SpeechRecognition||window.webkitSpeechRecognition;",
    "if(!SR){setStatus('Offline','is-offline');return;}",
    "stopRec();",
    "rec=new SR();bindRec(rec);want=true;",
    "try{rec.start();}catch(e){setStatus('Offline','is-offline');}",
    "}",
    "function arm(){",
    "if(!hud())return;",
    "if(!wakeAllowed()){stopRec();setStatus('Standby','');return;}",
    "if(armed)return;",
    "setStatus('Standby','');",
    "var md=navigator.mediaDevices;",
    "if(md&&md.getUserMedia){",
    "md.getUserMedia({audio:true}).then(function(stream){",
    "try{stream.getTracks().forEach(function(t){t.stop();});}catch(e){}",
    "startRec();",
    "}).catch(function(){setStatus('Offline','is-offline');});",
    "}else{startRec();}",
    "}",
    "function onFocusChange(){",
    "if(wakeAllowed()){want=true;arm();}",
    "else{want=false;stopRec();setStatus('Standby','');}",
    "}",
    "function boot(){",
    "if(!hud()){setTimeout(boot,800);return;}",
    "var focus=document.getElementById('cortana-focus-toggle');",
    "if(focus&&!focus.__cortanaWakeBound){focus.__cortanaWakeBound=1;focus.addEventListener('change',onFocusChange);}",
    "arm();",
    "}",
    "if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);",
    "else boot();",
    "})();",
  ].join("");
  return `<script id="cortana-hud-wake-script">${body}</script>`;
}

'''

text = WI.read_text(encoding="utf-8")

# 1) strip wake script id
old_strip = '''    .replace(/<script[^>]*id=["']cortana-hud-voice-script["'][\\s\\S]*?<\\/script>\\s*/gi, "")
    .replace(/\\n{3,}/g, "\\n\\n");'''
new_strip = '''    .replace(/<script[^>]*id=["']cortana-hud-voice-script["'][\\s\\S]*?<\\/script>\\s*/gi, "")
    .replace(/<script[^>]*id=["']cortana-hud-wake-script["'][\\s\\S]*?<\\/script>\\s*/gi, "")
    .replace(/\\n{3,}/g, "\\n\\n");'''
if "cortana-hud-wake-script" not in text.split("function stripHudMarkup")[1].split("function stripPatch")[0]:
    if old_strip not in text:
        raise SystemExit("strip pattern not found")
    text = text.replace(old_strip, new_strip, 1)
    print("patched stripHudMarkup")
else:
    print("strip already has wake")

# 2) readHudMarkup return wakeScript
old_ret = """  const voiceScript = buildHudVoiceScript();
  return { markup, clockScript, voiceScript };
}"""
new_ret = """  const voiceScript = buildHudVoiceScript();
  const wakeScript = buildHudWakeScript();
  return { markup, clockScript, voiceScript, wakeScript };
}"""
if "buildHudWakeScript()" not in text.split("async function readHudMarkup")[1].split("function buildHudVoiceScript")[0]:
    if old_ret not in text:
        raise SystemExit("readHudMarkup return not found")
    text = text.replace(old_ret, new_ret, 1)
    print("patched readHudMarkup")
else:
    print("readHudMarkup already has wake")

# 3) insert buildHudWakeScript before buildHudBlock if missing
if "function buildHudWakeScript()" not in text:
    marker = "function buildHudBlock({ uuid, markup, clockScript, voiceScript }) {"
    if marker not in text:
        raise SystemExit("buildHudBlock marker not found")
    text = text.replace(marker, WAKE_FN + "\n" + marker, 1)
    print("inserted buildHudWakeScript")
else:
    print("buildHudWakeScript already present")

# 4) buildHudBlock include wakeScript
old_block = """function buildHudBlock({ uuid, markup, clockScript, voiceScript }) {
  return [
    `<!-- ${MARKER_HUD_START} uuid=${uuid} -->`,
    markup.trim(),
    clockScript,
    voiceScript || "",
    `<!-- ${MARKER_HUD_END} -->`,
  ].join("\\n");
}"""
new_block = """function buildHudBlock({ uuid, markup, clockScript, voiceScript, wakeScript }) {
  return [
    `<!-- ${MARKER_HUD_START} uuid=${uuid} -->`,
    markup.trim(),
    clockScript,
    voiceScript || "",
    wakeScript || "",
    `<!-- ${MARKER_HUD_END} -->`,
  ].join("\\n");
}"""
if "wakeScript || \"\"" not in text.split("function buildHudBlock")[1].split("// ---------------------------------------------------------------------------")[0]:
    if old_block not in text:
        raise SystemExit("buildHudBlock body not found")
    text = text.replace(old_block, new_block, 1)
    print("patched buildHudBlock")
else:
    print("buildHudBlock already has wakeScript")

# 5) enable() call site
old_call = """  const hudBlock = buildHudBlock({
    uuid: markerUuid,
    markup: hudBundle.markup,
    clockScript: hudBundle.clockScript,
    voiceScript: hudBundle.voiceScript,
  });"""
new_call = """  const hudBlock = buildHudBlock({
    uuid: markerUuid,
    markup: hudBundle.markup,
    clockScript: hudBundle.clockScript,
    voiceScript: hudBundle.voiceScript,
    wakeScript: hudBundle.wakeScript,
  });"""
if "wakeScript: hudBundle.wakeScript" not in text:
    if old_call not in text:
        raise SystemExit("enable buildHudBlock call not found")
    text = text.replace(old_call, new_call, 1)
    print("patched enable call")
else:
    print("enable call already has wakeScript")

WI.write_text(text, encoding="utf-8")
print("wrote", WI)
print("done")
