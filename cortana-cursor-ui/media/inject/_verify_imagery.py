from pathlib import Path

root = Path(r"c:\PS2Recomp\jarvis-cursor-ui")
html = (root / "media/inject/hud-markup.html").read_text(encoding="utf-8")
css = (root / "media/inject/hud.css").read_text(encoding="utf-8")
inj = (root / "src/workbenchInject.js").read_text(encoding="utf-8")
assets = root / "media/inject/hud-photo-assets.css"
at = assets.read_text(encoding="utf-8") if assets.exists() else ""
part = css[css.find(".jcc-particles") : css.find(".jcc-particles") + 220]
checks = {
    "mic_btn_id": 'id="cortana-mic-btn"' in html,
    "talk_cta_id": 'id="cortana-talk-cta"' in html,
    "voice_attrs": html.count("data-cortana-voice") >= 2,
    "action_voice": html.count('data-cortana-action="voice"') >= 2,
    "no_mic_emoji": "🎙" not in html,
    "no_weather_emoji": "☁" not in html,
    "globe_photo": "jcc-globe-photo" in html,
    "talk_photo": "jcc-talk-wave-photo" in html,
    "photo_css_registered": "hud-photo-assets.css" in inj,
    "photo_vars": "--jcc-photo-hero-globe" in at and "--jcc-photo-voice-mic" in at,
    "particles_hidden": "display: none !important" in part,
}
print(checks)
print("ok", all(checks.values()))
