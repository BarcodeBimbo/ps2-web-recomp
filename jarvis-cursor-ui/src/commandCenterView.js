"use strict";

const vscode = require("vscode");
const os = require("os");
const { getSuit } = require("./suitModes");
const { getState, sessionMinutes } = require("./sessionCinema");
const { getGitStatus } = require("./gitHud");
const { getThreats } = require("./threatHints");
const { listPresets } = require("./workspacePresets");
const voice = require("./voiceBridge");

/**
 * CORTANA Command Center — jarvis.institute layout + PRO feature modules (unlocked).
 */
class CommandCenterViewProvider {
  /** @param {vscode.ExtensionContext} context @param {import("./fileMapProvider").FileMapProvider} fileMap */
  constructor(context, fileMap) {
    this.context = context;
    this.fileMap = fileMap;
    /** @type {vscode.WebviewView | undefined} */
    this.view = undefined;
    this._git = null;
    this._threats = null;
    this._booted = false;
  }

  resolveWebviewView(webviewView) {
    this.view = webviewView;
    this._booted = false;
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [vscode.Uri.joinPath(this.context.extensionUri, "media")],
    };
    webviewView.webview.onDidReceiveMessage((msg) => this._onMessage(msg));
    this.refresh({ full: true });
  }

  reveal() {
    if (this.view) this.view.show?.(true);
  }

  /**
   * @param {{ full?: boolean }} [opts]
   */
  async refresh(opts = {}) {
    if (!this.view) return;
    try {
      this._git = await getGitStatus();
    } catch {
      this._git = null;
    }
    try {
      this._threats = getThreats();
    } catch {
      this._threats = null;
    }
    const full = opts.full || !this._booted;
    if (full) {
      this.view.webview.html = this._html(this.view.webview);
      this._booted = true;
    } else {
      this.post({ type: "state", state: this._snapshot() });
    }
  }

  /** Push live patch without full HTML reload when possible */
  post(payload) {
    if (this.view) this.view.webview.postMessage(payload);
  }

  async _onMessage(msg) {
    if (!msg || typeof msg !== "object") return;
    const { toggle, patchState } = require("./sessionCinema");
    const { setSuit, pickSuit } = require("./suitModes");
    const { savePreset, applyPreset } = require("./workspacePresets");
    const { openThreat } = require("./threatHints");

    switch (msg.type) {
      case "ready":
        this.post({ type: "state", state: this._snapshot() });
        break;
      case "refresh":
        this.fileMap.refresh();
        await this.refresh({ full: true });
        break;
      case "openFileMap":
        vscode.commands.executeCommand("cortana.fileMap.focus");
        break;
      case "applyTheme":
        vscode.commands.executeCommand("cortana.theme.applyHints");
        break;
      case "runCommand":
        if (msg.command) vscode.commands.executeCommand(msg.command);
        break;
      case "chat":
      case "talk":
        await voice.openChat();
        break;
      case "voice":
        await voice.startVoice();
        break;
      case "setSuit":
        await setSuit(this.context, msg.id);
        await this.refresh({ full: true });
        break;
      case "pickSuit":
        await pickSuit(this.context);
        await this.refresh({ full: true });
        break;
      case "toggle":
        if (msg.key) {
          await toggle(this.context, msg.key);
          await this.refresh({ full: true });
        }
        break;
      case "setGlow":
        await patchState(this.context, { glow: Number(msg.value) || 1 });
        this.post({ type: "state", state: this._snapshot() });
        break;
      case "savePreset":
        await savePreset(this.context, msg.name);
        vscode.window.showInformationMessage("CORTANA preset saved.");
        await this.refresh({ full: true });
        break;
      case "applyPreset":
        await applyPreset(this.context, msg.name);
        await this.refresh({ full: true });
        break;
      case "openThreat":
        await openThreat(msg.uri, msg.line);
        break;
      case "announce":
        // TTS runs in webview; extension just logs
        break;
      default:
        break;
    }
  }

  _snapshot() {
    const suit = getSuit(this.context);
    const session = getState(this.context);
    const snap = this.fileMap.getSnapshot ? this.fileMap.getSnapshot() : { stats: {} };
    return {
      suit,
      session: { ...session, minutes: sessionMinutes(session) },
      git: this._git,
      threats: this._threats,
      presets: listPresets(this.context),
      stats: snap.stats || {},
      assistant: session.friday ? "F.R.I.D.A.Y." : "J.A.R.V.I.S.",
    };
  }

  _memPct() {
    const total = os.totalmem();
    const free = os.freemem();
    if (!total) return 54;
    return Math.round(((total - free) / total) * 100);
  }

  _uptime() {
    const s = Math.floor(os.uptime());
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    return `${h}h ${m}m`;
  }

  _injectionPrimary() {
    try {
      const cfg = vscode.workspace.getConfiguration("cortana.injection");
      return cfg.get("enabled") === true && cfg.get("fallbackWebview") !== true;
    } catch {
      return false;
    }
  }

  _html(webview) {
    // When workbench injection is primary, demote this webview to a thin fallback note.
    if (this._injectionPrimary()) {
      return this._fallbackHtml(webview);
    }
    const nonce = String(Date.now());
    const icon = webview.asWebviewUri(
      vscode.Uri.joinPath(this.context.extensionUri, "media", "arc-reactor.svg")
    );
    const data = this._snapshot();
    const suit = data.suit;
    const session = data.session;
    const stats = data.stats;
    const git = data.git || { branch: "—", detail: "…", dirty: false, ahead: 0, behind: 0, staged: 0, unstaged: 0, ok: false };
    const threats = data.threats || { total: 0, errors: 0, warnings: 0, hints: 0, items: [] };
    const folders = vscode.workspace.workspaceFolders || [];
    const ws = folders.length ? folders.map((f) => f.name).join(", ") : "No folder open";
    const editors = vscode.window.visibleTextEditors.length;
    const ram = this._memPct();
    const cpu = Math.min(95, 12 + editors * 3 + Math.floor(Math.random() * 8));
    const disk = 40;
    const host = os.hostname();
    const platform = `${os.type()} ${os.release()}`;
    const ver = this.context.extension.packageJSON.version || "1.0.0";
    const uptime = this._uptime();
    const cores = os.cpus()?.length || 0;
    const memGb = (os.totalmem() / 1024 / 1024 / 1024).toFixed(1);
    const assistant = data.assistant;
    const glow = session.glow ?? 1;
    const skipSplash = this._booted;
    const bodyClass = [
      session.focusFortress ? "focus-fortress" : "",
      session.streamPack ? "stream-pack" : "",
      session.cinema ? "cinema-on" : "",
      session.friday ? "mode-friday" : "",
      skipSplash ? "booted" : "",
    ]
      .filter(Boolean)
      .join(" ");

    const threatRows = (threats.items || [])
      .map(
        (t) => `<button class="threat" data-uri="${escapeAttr(t.uri)}" data-line="${t.line}">
        <span class="sev ${escapeAttr(t.severity)}">${escapeHtml(t.severity)}</span>
        <span class="msg">${escapeHtml(t.message)}</span>
        <span class="loc">${escapeHtml(t.file)}:${t.line}</span>
      </button>`
      )
      .join("") || `<div class="empty">No threats detected. Systems nominal.</div>`;

    const suitButtons = ["mark1", "mark50", "endgame", "stealth"]
      .map((id) => {
        const labels = { mark1: "Mark I", mark50: "Mark 50", endgame: "Endgame", stealth: "Stealth" };
        const on = suit.id === id ? "active" : "";
        return `<button class="suit ${on}" data-suit="${id}">${labels[id]}</button>`;
      })
      .join("");

    const presetRows = (data.presets || [])
      .map(
        (p) =>
          `<button class="preset" data-preset="${escapeAttr(p.name)}">${escapeHtml(p.name)} <span>${escapeHtml(p.suitId)}</span></button>`
      )
      .join("") || `<div class="empty">No presets yet — save one from Tools.</div>`;

    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src ${webview.cspSource} data:; script-src 'nonce-${nonce}';"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>J.A.R.V.I.S Command Center</title>
<style>
:root {
  --bg: ${suit.bg};
  --panel: rgba(8, 22, 40, 0.94);
  --border: #12324a;
  --cyan: ${suit.accent};
  --cyan2: ${suit.accent2};
  --text: #c8d6e5;
  --muted: #6a8094;
  --ok: #3dd68c;
  --warn: #ffd95a;
  --danger: #ff6b7a;
  --glow-a: ${glow};
  --glow: 0 0 calc(16px * var(--glow-a)) rgba(0, 217, 255, calc(0.35 * var(--glow-a)));
  --radius: 12px;
  --font: "Segoe UI", "Rajdhani", system-ui, sans-serif;
}
* { box-sizing: border-box; }
html, body {
  margin: 0; padding: 0; min-height: 100%;
  color: var(--text);
  background:
    radial-gradient(90% 55% at 50% -8%, color-mix(in srgb, var(--cyan) 18%, transparent) 0%, transparent 55%),
    linear-gradient(180deg, #030a14 0%, var(--bg) 42%, #040c16 100%);
  font: 11.5px/1.45 var(--font);
  overflow-x: hidden;
}
button { font: inherit; color: inherit; }
canvas#fx {
  position: fixed; inset: 0; width: 100%; height: 100%;
  pointer-events: none; z-index: 1; opacity: calc(0.35 * var(--glow-a));
}
.shell, #splash, .bottom, .cinema, .watermark { position: relative; z-index: 2; }

/* splash — match jarvis.institute calibrating */
#splash {
  position: fixed; inset: 0; z-index: 40;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  background: #1a1a1a;
  transition: opacity 0.55s ease, visibility 0.55s;
}
#splash.hide, body.booted #splash { opacity: 0; visibility: hidden; pointer-events: none; }
#splash .title {
  font-size: 42px; font-weight: 700; letter-spacing: 0.28em;
  color: var(--cyan); text-shadow: 0 0 28px color-mix(in srgb, var(--cyan) 55%, transparent);
  padding-left: 0.28em;
}
#splash .sub {
  margin-top: 10px; color: #8a8a8a; font-size: 10px;
  letter-spacing: 0.22em; text-align: center; text-transform: uppercase;
}
.ring {
  margin: 36px 0 22px; width: 72px; height: 72px; border-radius: 50%;
  border: 2px solid rgba(0,217,255,0.15);
  border-top-color: var(--cyan);
  box-shadow: 0 0 18px color-mix(in srgb, var(--cyan) 40%, transparent);
  animation: spin 1.1s linear infinite;
  position: relative;
}
.ring::after {
  content: ""; position: absolute; inset: 32px; border-radius: 50%;
  background: var(--cyan); box-shadow: 0 0 12px var(--cyan);
}
@keyframes spin { to { transform: rotate(360deg); } }
#splash .cal { letter-spacing: 0.42em; color: #f0f0f0; font-size: 12px; font-weight: 500; }
.bar {
  margin-top: 18px; width: 220px; height: 5px; border-radius: 999px;
  background: #2a2a2a; overflow: hidden;
}
.bar > i {
  display: block; height: 100%; width: 8%;
  background: linear-gradient(90deg, color-mix(in srgb, var(--cyan) 70%, #004), var(--cyan));
  box-shadow: 0 0 10px var(--cyan);
  transition: width 0.12s linear;
}
#splash .pct { margin-top: 10px; color: #777; font-size: 11px; }
.dots { display: flex; gap: 10px; margin-top: 28px; }
.dots span {
  width: 8px; height: 8px; border-radius: 50%; background: #333;
  transition: background 0.2s, box-shadow 0.2s;
}
.dots span.on { background: var(--cyan); box-shadow: 0 0 10px var(--cyan); }

.shell { padding-bottom: 118px; }
.top {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  padding: 10px 12px; border-bottom: 1px solid var(--border);
  background: linear-gradient(180deg, color-mix(in srgb, var(--bg) 80%, #0a1e30) 0%, transparent 100%);
  position: sticky; top: 0; z-index: 5; backdrop-filter: blur(8px);
}
.top img { width: 18px; height: 18px; filter: drop-shadow(var(--glow)); }
.brand { font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: var(--cyan); font-size: 11px; }
.pill {
  margin-left: 4px; font-size: 9px; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--ok); border: 1px solid #1f5a40; background: #0a281c;
  padding: 2px 8px; border-radius: 999px; display: inline-flex; align-items: center; gap: 5px;
}
.pill::before {
  content: ""; width: 6px; height: 6px; border-radius: 50%;
  background: var(--ok); box-shadow: 0 0 8px rgba(61,214,140,0.7);
}
.clock-wrap { margin-left: auto; text-align: right; }
.clock { color: #e8f7ff; font-size: 12px; font-weight: 650; letter-spacing: 0.04em; }
.date { color: var(--muted); font-size: 9px; margin-top: 1px; }

.nav {
  display: flex; flex-wrap: wrap; gap: 4px; padding: 8px 10px;
  border-bottom: 1px solid var(--border);
}
.nav button {
  border: 1px solid var(--border); background: #061320; color: var(--muted);
  border-radius: 8px; padding: 5px 8px; font-size: 9px; letter-spacing: 0.04em;
  text-transform: uppercase; cursor: pointer;
}
.nav button .badge {
  margin-left: 4px; background: #0a3a55; color: var(--cyan);
  border-radius: 999px; padding: 0 5px; font-size: 8px;
}
.nav button.active, .nav button:hover {
  color: #e8f7ff; border-color: color-mix(in srgb, var(--cyan) 45%, #1a6a88);
  background: #0a3a55; box-shadow: var(--glow);
}

.grid { display: grid; gap: 8px; padding: 10px; }
.card {
  background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 10px 12px; box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--cyan) 8%, transparent);
}
.card h2 {
  margin: 0 0 8px; font-size: 9px; letter-spacing: 0.16em; text-transform: uppercase;
  color: var(--cyan); font-weight: 700;
}
.row { display: flex; justify-content: space-between; gap: 8px; margin: 4px 0; align-items: center; }
.k { color: var(--muted); }
.v { font-weight: 600; }
.v.ok { color: var(--ok); }
.v.cyan { color: var(--cyan); }
.v.warn { color: var(--warn); }
.v.danger { color: var(--danger); }

.core { text-align: center; padding: 16px 8px 12px; }
.orb-wrap { width: 120px; height: 120px; margin: 0 auto; position: relative; }
.orb-ring {
  position: absolute; inset: 0; border-radius: 50%;
  border: 1px solid color-mix(in srgb, var(--cyan) 35%, transparent);
  animation: orbit 8s linear infinite;
}
.orb-ring.r2 { inset: 10px; animation-duration: 11s; animation-direction: reverse; }
.orb-ring.r3 { inset: 22px; border-style: dashed; animation-duration: 14s; }
@keyframes orbit { to { transform: rotate(360deg); } }
.core .orb {
  position: absolute; inset: 28px; border-radius: 50%;
  background: radial-gradient(circle at 50% 50%, color-mix(in srgb, var(--cyan) 45%, transparent) 0%, transparent 55%);
  border: 1px solid color-mix(in srgb, var(--cyan) 55%, transparent);
  box-shadow: var(--glow);
  animation: pulse 3s ease-in-out infinite;
  display: grid; place-items: center;
}
.core .orb img { width: 36px; height: 36px; filter: drop-shadow(var(--glow)); }
@keyframes pulse {
  0%,100% { box-shadow: 0 0 12px color-mix(in srgb, var(--cyan) 30%, transparent); }
  50% { box-shadow: 0 0 28px color-mix(in srgb, var(--cyan) 60%, transparent); }
}
.core .label {
  margin-top: 12px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--cyan); font-weight: 700; font-size: 10px;
}
.core .sub { color: var(--muted); font-size: 10px; margin-top: 4px; }

.agents { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.agent {
  border: 1px solid var(--border); border-radius: 8px; padding: 8px;
  background: #061320; display: flex; flex-direction: column; gap: 4px;
}
.agent .n { font-weight: 650; font-size: 10px; display: flex; align-items: center; gap: 6px; }
.agent .n .ico {
  width: 18px; height: 18px; border-radius: 6px; display: grid; place-items: center;
  background: #0a3a55; color: var(--cyan); font-size: 9px; border: 1px solid #1a5a7a;
}
.agent .s { font-size: 9px; color: var(--muted); }
.agent.active .s { color: var(--ok); }
.agent .wave { display: flex; align-items: flex-end; gap: 2px; height: 12px; margin-top: 2px; }
.agent .wave i {
  width: 2px; background: var(--cyan); border-radius: 1px; opacity: 0.35;
  animation: wave 1.1s ease-in-out infinite;
}
.agent.active .wave i { opacity: 0.9; }
.agent .wave i:nth-child(2) { animation-delay: 0.1s; }
.agent .wave i:nth-child(3) { animation-delay: 0.2s; }
.agent .wave i:nth-child(4) { animation-delay: 0.3s; }
@keyframes wave { 0%,100% { height: 3px; } 50% { height: 11px; } }

.gauges { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; text-align: center; }
.g .ring2 {
  width: 48px; height: 48px; margin: 0 auto 4px; border-radius: 50%;
  background: conic-gradient(var(--cyan) calc(var(--p) * 1%), #12324a 0);
  -webkit-mask: radial-gradient(farthest-side, transparent 62%, #000 63%);
  mask: radial-gradient(farthest-side, transparent 62%, #000 63%);
}
.g .val { font-weight: 700; color: var(--cyan); font-size: 11px; }
.g .lab { color: var(--muted); font-size: 9px; }

.feed .item {
  border-left: 2px solid var(--cyan); padding: 7px 8px; margin: 0 0 6px;
  background: #061320; border-radius: 0 8px 8px 0; font-size: 10px;
}
.feed .item.warn { border-left-color: var(--warn); }
.feed .item.ok { border-left-color: var(--ok); }
.feed .item.danger { border-left-color: var(--danger); }
.feed .item span { display: block; color: var(--muted); font-size: 9px; margin-top: 2px; }

.timeline { position: relative; padding-left: 14px; }
.timeline::before {
  content: ""; position: absolute; left: 3px; top: 4px; bottom: 4px;
  width: 2px; background: linear-gradient(180deg, var(--cyan), transparent);
}
.tl { position: relative; margin: 0 0 10px; padding-left: 8px; }
.tl::before {
  content: ""; position: absolute; left: -13px; top: 4px;
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--cyan); box-shadow: var(--glow);
}
.tl.done::before { background: var(--ok); box-shadow: none; }
.tl .t { font-size: 10px; font-weight: 600; }
.tl .m { font-size: 9px; color: var(--muted); margin-top: 2px; }

.actions { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.actions button, .cta, .suit, .preset, .threat, .tog {
  width: 100%; border: 1px solid color-mix(in srgb, var(--cyan) 35%, #1a5a7a);
  background: #0a3a55; color: #e8f7ff;
  border-radius: 8px; padding: 8px 10px; cursor: pointer; font-size: 10px; text-align: left;
}
.actions button:hover, .cta:hover, .suit:hover, .preset:hover, .threat:hover, .tog:hover {
  background: #0d4d70; box-shadow: var(--glow);
}
.suit.active, .tog.on {
  border-color: var(--cyan); box-shadow: var(--glow); background: #0c4a6a;
}
.suits { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.togs { display: grid; gap: 6px; }
.tog { display: flex; justify-content: space-between; align-items: center; }
.tog .st { color: var(--muted); font-size: 9px; }
.tog.on .st { color: var(--ok); }

.llm { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; }
.llm .chip {
  border: 1px solid var(--border); border-radius: 8px; padding: 6px 8px;
  background: #061320; font-size: 9px; display: flex; justify-content: space-between;
}
.llm .chip.on .st { color: var(--ok); }
.llm .chip .st { color: var(--muted); }

.githud .chip-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
.githud .tag {
  font-size: 9px; padding: 3px 8px; border-radius: 999px;
  border: 1px solid var(--border); background: #061320; color: var(--cyan);
}
.githud .tag.warn { color: var(--warn); border-color: #5a4a20; }

.threat { display: grid; gap: 2px; margin-bottom: 6px; background: #061320; }
.threat .sev { font-size: 8px; text-transform: uppercase; letter-spacing: 0.08em; }
.threat .sev.error { color: var(--danger); }
.threat .sev.warning { color: var(--warn); }
.threat .sev.info, .threat .sev.hint { color: var(--cyan); }
.threat .msg { font-size: 10px; }
.threat .loc { font-size: 8px; color: var(--muted); }
.preset span { float: right; color: var(--muted); font-size: 8px; }

.streams {
  height: 56px; border-radius: 8px; overflow: hidden; position: relative;
  border: 1px solid var(--border); background: #061320;
}
.streams i {
  position: absolute; width: 1px; top: -20%; height: 140%;
  background: linear-gradient(180deg, transparent, var(--cyan), transparent);
  opacity: 0.35; animation: stream 2.8s linear infinite;
}
@keyframes stream { from { transform: translateY(-30%); } to { transform: translateY(30%); } }

.bottom {
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 8;
  margin: 0; padding: 8px 12px 10px;
  border-top: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(6,19,32,0.92) 0%, #061320 100%);
  backdrop-filter: blur(10px);
}
.voice-row {
  display: grid; grid-template-columns: 72px 1fr; gap: 10px; align-items: center;
  margin-bottom: 8px;
}
.voice-status {
  border: 1px solid var(--border); border-radius: 10px; padding: 8px;
  background: #061320; text-align: center;
}
.voice-status .lab { font-size: 8px; letter-spacing: 0.12em; color: var(--cyan); text-transform: uppercase; }
.voice-status .mic {
  margin: 6px auto 4px; width: 36px; height: 36px; border-radius: 50%;
  border: 1px solid color-mix(in srgb, var(--cyan) 50%, transparent);
  background: #0a3a55; color: var(--cyan); display: grid; place-items: center;
  cursor: pointer; box-shadow: var(--glow);
}
.voice-status .hint { font-size: 8px; color: var(--muted); }
.bottom .cta {
  margin: 0; text-align: center; font-weight: 700; letter-spacing: 0.06em;
  padding: 12px 14px; border-radius: 999px; box-shadow: var(--glow);
  display: inline-flex; align-items: center; justify-content: center; gap: 10px;
  width: 100%; text-transform: uppercase;
}
.cta .subline { display: block; font-size: 8px; font-weight: 500; letter-spacing: 0.08em; color: var(--muted); margin-top: 2px; }
.wavebar { display: inline-flex; align-items: center; gap: 2px; height: 14px; }
.wavebar i {
  width: 2px; height: 4px; background: var(--cyan); border-radius: 1px;
  animation: wave 0.9s ease-in-out infinite;
}
.footer-meta {
  display: flex; justify-content: space-between; gap: 8px;
  margin-top: 6px; color: var(--muted); font-size: 8px; letter-spacing: 0.04em;
}

.panel { display: none; }
.panel.show { display: block; }
.empty { color: var(--muted); font-size: 10px; padding: 8px 0; }

/* Focus Fortress */
body.focus-fortress .card:not(.keep),
body.focus-fortress .nav button:not(.active):not([data-panel="home"]):not([data-panel="tasks"]) {
  opacity: 0.22; filter: grayscale(0.4);
}
body.focus-fortress .feed { opacity: 0.15; pointer-events: none; }

/* Stream pack */
body.stream-pack .shell { font-size: 10.5px; }
body.stream-pack .card { padding: 8px; }
.watermark {
  display: none; position: fixed; right: 10px; bottom: 130px; z-index: 9;
  font-size: 10px; letter-spacing: 0.2em; color: color-mix(in srgb, var(--cyan) 35%, transparent);
  text-transform: uppercase; pointer-events: none;
}
body.stream-pack.show-mark .watermark { display: block; }

/* Session cinema */
.cinema {
  display: none; position: fixed; left: 10px; right: 10px; top: 48px; z-index: 12;
  border: 1px solid var(--border); border-radius: 10px; padding: 8px 12px;
  background: rgba(6,19,32,0.95); box-shadow: var(--glow);
  font-size: 10px;
}
body.cinema-on .cinema { display: flex; justify-content: space-between; gap: 8px; align-items: center; }
.cinema .energy { color: var(--cyan); font-weight: 700; }

body.mode-friday .brand::after { content: " · F.R.I.D.A.Y."; color: var(--cyan2); }
</style>
</head>
<body class="${bodyClass}${session.watermark ? " show-mark" : ""}" data-glow="${glow}">
<canvas id="fx"></canvas>
<div class="watermark">CORTANA STREAM</div>
<div class="cinema" id="cinema">
  <span>Session Cinema · <span id="cineMin">${session.minutes || 0}</span>m</span>
  <span class="energy">Energy <span id="cineEnergy">${session.keystrokes || 0}</span></span>
  <span id="cineNote">Deep focus armed</span>
</div>

<div id="splash">
  <div class="title">J.A.R.V.I.S</div>
  <div class="sub">Just A Rather Very Intelligent System</div>
  <div class="ring"></div>
  <div class="cal">CALIBRATING</div>
  <div class="bar"><i id="barFill"></i></div>
  <div class="pct" id="pct">0%</div>
  <div class="dots" id="dots">
    <span></span><span></span><span></span><span></span><span></span>
  </div>
</div>

<div class="shell">
  <div class="top">
    <img src="${icon}" alt=""/>
    <div class="brand">CORTANA Command Center</div>
    <div class="pill">Optimal</div>
    <div class="clock-wrap">
      <div class="clock" id="clock">—</div>
      <div class="date" id="date">—</div>
    </div>
  </div>

  <div class="nav">
    <button class="active" data-panel="home">Command Center</button>
    <button data-panel="core">AI Core</button>
    <button data-panel="agents">Agents</button>
    <button data-panel="tasks">Tasks <span class="badge">3</span></button>
    <button data-panel="map" id="navMap">File Map</button>
    <button data-panel="threats">Threats <span class="badge">${threats.total || 0}</span></button>
    <button data-panel="calendar">Calendar</button>
    <button data-panel="memory">Memory</button>
    <button data-panel="conversations">Conversations</button>
    <button data-panel="knowledge">Knowledge</button>
    <button data-panel="tools">Tools</button>
    <button data-panel="workflows">Workflows</button>
  </div>

  <div class="panel show" id="panel-home">
    <div class="grid">
      <div class="card core keep">
        <div class="orb-wrap">
          <div class="orb-ring"></div>
          <div class="orb-ring r2"></div>
          <div class="orb-ring r3"></div>
          <div class="orb"><img src="${icon}" alt=""/></div>
        </div>
        <div class="label">${escapeHtml(assistant)} core v${escapeHtml(ver)}</div>
        <div class="sub">${escapeHtml(ws)} · ${escapeHtml(host)} · Suit ${escapeHtml(suit.label)}</div>
      </div>

      <div class="card keep">
        <h2>AI core overview</h2>
        <div class="row"><span class="k">Assistant</span><span class="v ok">${escapeHtml(assistant)}</span></div>
        <div class="row"><span class="k">Voice</span><span class="v ok">Online</span></div>
        <div class="row"><span class="k">Mapped files</span><span class="v cyan">${stats.files || 0}</span></div>
        <div class="row"><span class="k">Open editors</span><span class="v cyan">${editors}</span></div>
        <div class="row"><span class="k">Threats</span><span class="v ${threats.errors ? "danger" : threats.warnings ? "warn" : "ok"}">${threats.total || 0}</span></div>
        <div class="row"><span class="k">System</span><span class="v ok">Optimal</span></div>
      </div>

      <div class="card">
        <h2>Active agents</h2>
        <div class="agents">
          ${agentCard("<>", "Coding Agent", true)}
          ${agentCard("R", "Research Agent", true)}
          ${agentCard("M", "Memory Agent", false)}
          ${agentCard("B", "Browser Agent", false)}
          ${agentCard("T", "Task Agent", false)}
          ${agentCard("S", "System Agent", false)}
        </div>
      </div>

      <div class="card keep">
        <h2>Mission timeline</h2>
        <div class="timeline">
          <div class="tl done"><div class="t">Workspace indexed</div><div class="m">Done · ${stats.files || 0} files</div></div>
          <div class="tl"><div class="t">Suit ${escapeHtml(suit.label)} online</div><div class="m">PRO features unlocked locally</div></div>
          <div class="tl"><div class="t">Deep-work block: Voice pipeline</div><div class="m">Talk to CORTANA when ready</div></div>
        </div>
      </div>

      <div class="card githud keep">
        <h2>GitHUD</h2>
        <div class="row"><span class="k">Branch</span><span class="v cyan">${escapeHtml(git.branch)}</span></div>
        <div class="row"><span class="k">Status</span><span class="v ${git.dirty ? "warn" : "ok"}">${escapeHtml(git.detail)}</span></div>
        <div class="chip-row">
          <span class="tag">↑ ${git.ahead || 0}</span>
          <span class="tag">↓ ${git.behind || 0}</span>
          <span class="tag ${git.staged ? "warn" : ""}">staged ${git.staged || 0}</span>
          <span class="tag ${git.unstaged ? "warn" : ""}">unstaged ${git.unstaged || 0}</span>
        </div>
      </div>

      <div class="card">
        <h2>Live intelligence feed</h2>
        <div class="feed">
          <div class="item ok">${escapeHtml(assistant)} Command Center online.<span>Status · Optimal · ${escapeHtml(suit.label)}</span></div>
          <div class="item">File Map indexed this workspace.<span>${stats.files || 0} files · ${stats.folders || 0} dirs</span></div>
          <div class="item ${threats.errors ? "danger" : threats.warnings ? "warn" : "ok"}">Threat scan: ${threats.errors || 0} errors · ${threats.warnings || 0} warnings.<span>Threat Fix Hints</span></div>
          <div class="item">Data streams + arc pulse FX active in HUD.<span>Glow ${glow}×</span></div>
        </div>
        <div class="streams" id="streams"></div>
      </div>

      <div class="card keep">
        <h2>Quick commands</h2>
        <div class="actions">
          <button id="btnVoice">Start Voice Chat</button>
          <button id="btnChat">Open Chat</button>
          <button id="btnMap">Open File Map</button>
          <button id="btnTheme">Apply Suit Theme</button>
          <button id="btnSuit">Cycle Suit</button>
          <button id="btnFocus">Focus Fortress</button>
          <button id="btnCinema">Session Cinema</button>
          <button id="btnStream">Stream Pack</button>
          <button id="btnCmd">Command palette</button>
          <button id="btnTerm">New terminal</button>
        </div>
      </div>

      <div class="card keep">
        <h2>System monitor</h2>
        <div class="gauges">
          <div class="g"><div class="ring2" style="--p:${cpu}"></div><div class="val">${cpu}%</div><div class="lab">CPU*</div></div>
          <div class="g"><div class="ring2" style="--p:${ram}"></div><div class="val">${ram}%</div><div class="lab">RAM</div></div>
          <div class="g"><div class="ring2" style="--p:${disk}"></div><div class="val">${disk}%</div><div class="lab">Disk*</div></div>
        </div>
        <div class="row" style="margin-top:6px"><span class="k">${cores} cores · ${memGb} GB · up ${escapeHtml(uptime)}</span><span class="v"></span></div>
      </div>

      <div class="card">
        <h2>LLM / agent status</h2>
        <div class="llm">
          <div class="chip on"><span>Cursor</span><span class="st">Connected</span></div>
          <div class="chip on"><span>Composer</span><span class="st">Active</span></div>
          <div class="chip on"><span>Voice</span><span class="st">Online</span></div>
          <div class="chip"><span>Claude</span><span class="st">Via Cursor</span></div>
          <div class="chip"><span>GPT</span><span class="st">Via Cursor</span></div>
          <div class="chip"><span>Local</span><span class="st">Not linked</span></div>
        </div>
      </div>
    </div>
  </div>

  <div class="panel" id="panel-core">
    <div class="grid">
      <div class="card core keep">
        <div class="orb-wrap">
          <div class="orb-ring"></div><div class="orb-ring r2"></div>
          <div class="orb"><img src="${icon}" alt=""/></div>
        </div>
        <div class="label">${escapeHtml(assistant)}</div>
        <div class="sub">Suit ${escapeHtml(suit.label)} · glow ${glow}×</div>
      </div>
      <div class="card keep">
        <h2>Suit Modes</h2>
        <div class="suits">${suitButtons}</div>
        <div class="row" style="margin-top:10px"><span class="k">Glow intensity</span>
          <span class="v"><input id="glow" type="range" min="0.4" max="2" step="0.1" value="${glow}"/></span>
        </div>
      </div>
      <div class="card">
        <h2>Capabilities</h2>
        <div class="row"><span class="k">Code edits</span><span class="v ok">Online</span></div>
        <div class="row"><span class="k">Voice TTS</span><span class="v ok">${session.tts ? "Armed" : "Muted"}</span></div>
        <div class="row"><span class="k">Sound design</span><span class="v ok">${session.sound ? "On" : "Off"}</span></div>
        <div class="row"><span class="k">Platform</span><span class="v cyan">${escapeHtml(platform)}</span></div>
      </div>
    </div>
  </div>

  <div class="panel" id="panel-agents">
    <div class="grid">
      <div class="card">
        <h2>Agent roster</h2>
        <div class="agents">
          ${agentCard("<>", "Coding", true)}
          ${agentCard("R", "Research", true)}
          ${agentCard("M", "Memory", false)}
          ${agentCard("B", "Browser", false)}
          ${agentCard("T", "Task", false)}
          ${agentCard("S", "System", false)}
        </div>
      </div>
    </div>
  </div>

  <div class="panel" id="panel-tasks">
    <div class="grid">
      <div class="card keep">
        <h2>Tasks</h2>
        <div class="timeline">
          <div class="tl done"><div class="t">Install CORTANA Command Center</div><div class="m">Done</div></div>
          <div class="tl"><div class="t">Apply suit theme</div><div class="m">AI Core → Suit Modes</div></div>
          <div class="tl"><div class="t">Talk to CORTANA</div><div class="m">Bottom bar / Start Voice Chat</div></div>
        </div>
      </div>
    </div>
  </div>

  <div class="panel" id="panel-threats">
    <div class="grid">
      <div class="card keep">
        <h2>Threat Fix Hints</h2>
        <div class="row"><span class="k">Errors</span><span class="v danger">${threats.errors || 0}</span></div>
        <div class="row"><span class="k">Warnings</span><span class="v warn">${threats.warnings || 0}</span></div>
        <div class="row"><span class="k">Hints</span><span class="v cyan">${threats.hints || 0}</span></div>
        <div style="margin-top:8px">${threatRows}</div>
      </div>
    </div>
  </div>

  <div class="panel" id="panel-calendar">
    <div class="grid"><div class="card"><h2>Calendar</h2><div class="empty">Coming online — stub panel. Wire a calendar source later.</div></div></div>
  </div>
  <div class="panel" id="panel-memory">
    <div class="grid">
      <div class="card">
        <h2>Workspace memory</h2>
        <div class="row"><span class="k">Files</span><span class="v cyan">${stats.files || 0}</span></div>
        <div class="row"><span class="k">Folders</span><span class="v cyan">${stats.folders || 0}</span></div>
        <div class="row"><span class="k">Workspace</span><span class="v">${escapeHtml(ws)}</span></div>
      </div>
    </div>
  </div>
  <div class="panel" id="panel-conversations">
    <div class="grid"><div class="card"><h2>Conversations</h2><div class="empty">Open Cursor Chat for live agent conversations.</div>
      <div class="actions" style="margin-top:8px"><button id="btnChat2">Open Chat</button><button id="btnVoice2">Start Voice</button></div>
    </div></div>
  </div>
  <div class="panel" id="panel-knowledge">
    <div class="grid"><div class="card"><h2>Knowledge Base</h2><div class="empty">Coming online — stub panel for notes / docs index.</div></div></div>
  </div>

  <div class="panel" id="panel-tools">
    <div class="grid">
      <div class="card keep">
        <h2>PRO controls</h2>
        <div class="togs">
          <button class="tog ${session.friday ? "on" : ""}" data-tog="friday"><span>F.R.I.D.A.Y. mode</span><span class="st">${session.friday ? "ON" : "OFF"}</span></button>
          <button class="tog ${session.focusFortress ? "on" : ""}" data-tog="focusFortress"><span>Focus Fortress</span><span class="st">${session.focusFortress ? "ON" : "OFF"}</span></button>
          <button class="tog ${session.cinema ? "on" : ""}" data-tog="cinema"><span>Session Cinema</span><span class="st">${session.cinema ? "ON" : "OFF"}</span></button>
          <button class="tog ${session.streamPack ? "on" : ""}" data-tog="streamPack"><span>Stream Pack</span><span class="st">${session.streamPack ? "ON" : "OFF"}</span></button>
          <button class="tog ${session.watermark ? "on" : ""}" data-tog="watermark"><span>Stream watermark</span><span class="st">${session.watermark ? "ON" : "OFF"}</span></button>
          <button class="tog ${session.sound ? "on" : ""}" data-tog="sound"><span>Sound design</span><span class="st">${session.sound ? "ON" : "OFF"}</span></button>
          <button class="tog ${session.tts ? "on" : ""}" data-tog="tts"><span>Voice TTS</span><span class="st">${session.tts ? "ON" : "OFF"}</span></button>
        </div>
      </div>
      <div class="card keep">
        <h2>Workspace presets</h2>
        <div class="actions">
          <button id="btnSavePreset">Save preset</button>
          <button id="btnApplyPreset">Apply preset</button>
        </div>
        <div style="margin-top:8px">${presetRows}</div>
      </div>
      <div class="card">
        <h2>System</h2>
        <div class="actions">
          <button id="btnTheme2">Apply suit theme</button>
          <button id="btnMap2">File Map</button>
          <button id="btnSettings">Settings</button>
          <button id="btnReload">Reload window</button>
          <button id="btnProblems">Problems</button>
          <button id="btnRefresh">Refresh HUD</button>
        </div>
      </div>
    </div>
  </div>

  <div class="panel" id="panel-workflows">
    <div class="grid"><div class="card"><h2>Workflows</h2><div class="empty">Coming online — stub for automation recipes.</div></div></div>
  </div>
</div>

<div class="bottom">
  <div class="voice-row">
    <div class="voice-status">
      <div class="lab">Voice status</div>
      <button class="mic" id="btnMic" title="Tap to speak">🎤</button>
      <div class="hint">Tap to Speak</div>
    </div>
    <button class="cta" id="btnCta">
      <span class="wavebar"><i></i><i></i><i></i><i></i><i></i></span>
      <span>Talk to CORTANA<span class="subline" id="listenHint">I am listening…</span></span>
      <span class="wavebar"><i></i><i></i><i></i><i></i><i></i></span>
    </button>
  </div>
  <div class="footer-meta">
    <span>${escapeHtml(host)}</span>
    <span>${escapeHtml(suit.label)} · ${escapeHtml(assistant)}</span>
    <span>v${escapeHtml(ver)}</span>
  </div>
</div>

<script nonce="${nonce}">
  const vscode = acquireVsCodeApi();
  const post = (type, extra = {}) => vscode.postMessage({ type, ...extra });
  const CFG = {
    sound: ${session.sound ? "true" : "false"},
    tts: ${session.tts ? "true" : "false"},
    glow: ${glow},
  };

  // —— splash ——
  let p = 0;
  const pct = document.getElementById("pct");
  const fill = document.getElementById("barFill");
  const dots = [...document.querySelectorAll("#dots span")];
  const tick = setInterval(() => {
    p = Math.min(100, p + 4);
    pct.textContent = p + "%";
    fill.style.width = p + "%";
    const lit = Math.min(5, Math.ceil(p / 20));
    dots.forEach((d, i) => d.classList.toggle("on", i < lit));
    if (p >= 100) {
      clearInterval(tick);
      setTimeout(() => {
        document.getElementById("splash").classList.add("hide");
        announce("Systems online. CORTANA ready.");
        beep(880, 0.06);
      }, 220);
    }
  }, 55);

  // —— clock ——
  function clock() {
    const now = new Date();
    document.getElementById("clock").textContent = now.toLocaleTimeString();
    document.getElementById("date").textContent = now.toLocaleDateString(undefined, {
      weekday: "long", year: "numeric", month: "long", day: "numeric"
    });
  }
  clock(); setInterval(clock, 1000);

  // —— FX particles + data streams ——
  const fx = document.getElementById("fx");
  const ctx = fx.getContext("2d");
  const parts = Array.from({ length: 48 }, () => ({
    x: Math.random(), y: Math.random(),
    vx: (Math.random() - 0.5) * 0.00035,
    vy: -0.00015 - Math.random() * 0.0004,
    r: 0.6 + Math.random() * 1.8,
  }));
  function resize() { fx.width = innerWidth; fx.height = innerHeight; }
  resize(); addEventListener("resize", resize);
  function paintFx() {
    ctx.clearRect(0, 0, fx.width, fx.height);
    const accent = getComputedStyle(document.documentElement).getPropertyValue("--cyan").trim() || "#00d9ff";
    for (const pt of parts) {
      pt.x += pt.vx; pt.y += pt.vy;
      if (pt.y < -0.02) { pt.y = 1.02; pt.x = Math.random(); }
      if (pt.x < 0) pt.x = 1; if (pt.x > 1) pt.x = 0;
      ctx.beginPath();
      ctx.fillStyle = accent;
      ctx.globalAlpha = 0.35;
      ctx.arc(pt.x * fx.width, pt.y * fx.height, pt.r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
    requestAnimationFrame(paintFx);
  }
  paintFx();

  const streams = document.getElementById("streams");
  if (streams) {
    for (let i = 0; i < 18; i++) {
      const el = document.createElement("i");
      el.style.left = (4 + i * 5.5) + "%";
      el.style.animationDelay = (i * 0.12) + "s";
      streams.appendChild(el);
    }
  }

  // —— sound / TTS ——
  function beep(freq, dur) {
    if (!CFG.sound) return;
    try {
      const ac = new (window.AudioContext || window.webkitAudioContext)();
      const o = ac.createOscillator();
      const g = ac.createGain();
      o.frequency.value = freq;
      o.type = "sine";
      g.gain.value = 0.03;
      o.connect(g); g.connect(ac.destination);
      o.start();
      g.gain.exponentialRampToValueAtTime(0.0001, ac.currentTime + dur);
      o.stop(ac.currentTime + dur + 0.02);
      setTimeout(() => ac.close(), 400);
    } catch (_) {}
  }
  function announce(text) {
    if (!CFG.tts || !window.speechSynthesis) return;
    try {
      const u = new SpeechSynthesisUtterance(text);
      u.rate = 1.05; u.pitch = 0.95; u.volume = 0.7;
      speechSynthesis.cancel();
      speechSynthesis.speak(u);
    } catch (_) {}
  }

  // —— nav ——
  document.querySelectorAll(".nav button").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-panel");
      if (id === "map") { post("openFileMap"); return; }
      document.querySelectorAll(".nav button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      document.querySelectorAll(".panel").forEach((p) => p.classList.remove("show"));
      const el = document.getElementById("panel-" + id);
      if (el) el.classList.add("show");
      beep(520, 0.04);
    });
  });

  const bind = (id, fn) => { const el = document.getElementById(id); if (el) el.onclick = fn; };
  bind("btnChat", () => post("chat"));
  bind("btnChat2", () => post("chat"));
  bind("btnCta", () => { beep(660, 0.05); announce("Opening voice channel."); post("voice"); });
  bind("btnMic", () => { beep(660, 0.05); post("voice"); });
  bind("btnVoice", () => post("voice"));
  bind("btnVoice2", () => post("voice"));
  bind("btnMap", () => post("openFileMap"));
  bind("btnMap2", () => post("openFileMap"));
  bind("btnTheme", () => post("applyTheme"));
  bind("btnTheme2", () => post("applyTheme"));
  bind("btnSuit", () => post("pickSuit"));
  bind("btnFocus", () => post("toggle", { key: "focusFortress" }));
  bind("btnCinema", () => post("toggle", { key: "cinema" }));
  bind("btnStream", () => post("toggle", { key: "streamPack" }));
  bind("btnRefresh", () => post("refresh"));
  bind("btnCmd", () => post("runCommand", { command: "workbench.action.showCommands" }));
  bind("btnTerm", () => post("runCommand", { command: "workbench.action.terminal.new" }));
  bind("btnSettings", () => post("runCommand", { command: "workbench.action.openSettings" }));
  bind("btnReload", () => post("runCommand", { command: "workbench.action.reloadWindow" }));
  bind("btnProblems", () => post("runCommand", { command: "workbench.actions.view.problems" }));
  bind("btnSavePreset", () => post("savePreset"));
  bind("btnApplyPreset", () => post("applyPreset"));

  document.querySelectorAll(".suit").forEach((b) => {
    b.onclick = () => { beep(740, 0.05); post("setSuit", { id: b.getAttribute("data-suit") }); };
  });
  document.querySelectorAll(".tog").forEach((b) => {
    b.onclick = () => post("toggle", { key: b.getAttribute("data-tog") });
  });
  document.querySelectorAll(".threat").forEach((b) => {
    b.onclick = () => post("openThreat", { uri: b.getAttribute("data-uri"), line: Number(b.getAttribute("data-line")) });
  });
  document.querySelectorAll(".preset").forEach((b) => {
    b.onclick = () => post("applyPreset", { name: b.getAttribute("data-preset") });
  });
  const glowEl = document.getElementById("glow");
  if (glowEl) {
    glowEl.oninput = () => {
      const v = glowEl.value;
      document.documentElement.style.setProperty("--glow-a", v);
      post("setGlow", { value: v });
    };
  }

  window.addEventListener("message", (ev) => {
    const msg = ev.data;
    if (!msg || typeof msg !== "object") return;
    if (msg.type === "energy" && msg.keystrokes != null) {
      const el = document.getElementById("cineEnergy");
      if (el) el.textContent = String(msg.keystrokes);
    }
    if (msg.type === "state" && msg.state) {
      const g = msg.state.git;
      const th = msg.state.threats;
      // Soft update badges without remounting
      const badge = document.querySelector('.nav button[data-panel="threats"] .badge');
      if (badge && th) badge.textContent = String(th.total || 0);
      const cineMin = document.getElementById("cineMin");
      if (cineMin && msg.state.session) cineMin.textContent = String(msg.state.session.minutes || 0);
      if (g) {
        /* git strip refreshed on next full paint */
      }
    }
  });

  post("ready");
  ${skipSplash ? "document.getElementById('splash').classList.add('hide');" : ""}
</script>
</body>
</html>`;
  }

  _fallbackHtml(webview) {
    const nonce = String(Date.now());
    void webview;
    return `<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"/>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';"/>
<title>CORTANA Command Center (fallback)</title>
<style>
body{margin:0;padding:20px;background:#020817;color:#becedb;font:12px/1.45 "Segoe UI Condensed","Segoe UI",sans-serif}
h1{margin:0 0 8px;font-size:13px;letter-spacing:.18em;color:#4ad1f1;text-transform:uppercase}
p{margin:0 0 10px;color:#7a8fa3}
code{color:#00d4ff}
.pill{display:inline-block;margin-top:8px;padding:6px 12px;border-radius:999px;border:1px solid rgba(0,212,255,.35);color:#00d4ff;letter-spacing:.08em;font-size:10px}
</style>
</head>
<body>
  <h1>Injected HUD is primary</h1>
  <p>Command Center chrome lives in workbench injection (<code>#cortana-cc-hud</code>), matching the reference PNGs.</p>
  <p>This sidebar webview is optional fallback only. Set <code>cortana.injection.fallbackWebview</code> to restore the in-view dashboard.</p>
  <div class="pill">SYSTEM STATUS · INJECT ON</div>
  <script nonce="${nonce}">acquireVsCodeApi().postMessage({type:"ready"});</script>
</body></html>`;
  }
}

function agentCard(ico, name, active) {
  return `<div class="agent ${active ? "active" : "standby"}">
    <div class="n"><span class="ico">${escapeHtml(ico)}</span>${escapeHtml(name)}</div>
    <div class="s">${active ? "● Active" : "Standby"}</div>
    <div class="wave"><i></i><i></i><i></i><i></i><i></i></div>
  </div>`;
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function escapeAttr(s) {
  return escapeHtml(s).replace(/'/g, "&#39;");
}

module.exports = { CommandCenterViewProvider };
