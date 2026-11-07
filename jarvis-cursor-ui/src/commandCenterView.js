"use strict";

const vscode = require("vscode");
const os = require("os");

/**
 * Full Command Center dashboard (jarvis.institute / reference screenshot layout).
 * Visual chrome: cyan HUD on navy. Copy/voice: Cursor coding agent — never JARVIS persona.
 */
class CommandCenterViewProvider {
  /** @param {vscode.ExtensionContext} context @param {import("./fileMapProvider").FileMapProvider} fileMap */
  constructor(context, fileMap) {
    this.context = context;
    this.fileMap = fileMap;
    /** @type {vscode.WebviewView | undefined} */
    this.view = undefined;
  }

  resolveWebviewView(webviewView) {
    this.view = webviewView;
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [vscode.Uri.joinPath(this.context.extensionUri, "media")],
    };
    webviewView.webview.onDidReceiveMessage((msg) => this._onMessage(msg));
    this.refresh();
  }

  refresh() {
    if (this.view) this.view.webview.html = this._html(this.view.webview);
  }

  _onMessage(msg) {
    if (!msg || typeof msg !== "object") return;
    switch (msg.type) {
      case "refresh":
        this.fileMap.refresh();
        this.refresh();
        break;
      case "openFileMap":
        vscode.commands.executeCommand("jarvis.fileMap.focus");
        break;
      case "applyTheme":
        vscode.commands.executeCommand("jarvis.theme.applyHints");
        break;
      case "runCommand":
        if (msg.command) vscode.commands.executeCommand(msg.command);
        break;
      case "chat":
        vscode.commands.executeCommand("workbench.action.chat.open").then(undefined, () => {
          vscode.commands.executeCommand("aichat.newchataction").then(undefined, () => {
            vscode.window.showInformationMessage("Open Cursor Chat when you want the coding agent.");
          });
        });
        break;
      default:
        break;
    }
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

  _html(webview) {
    const nonce = String(Date.now());
    const icon = webview.asWebviewUri(
      vscode.Uri.joinPath(this.context.extensionUri, "media", "arc-reactor.svg")
    );
    const snap = this.fileMap.getSnapshot ? this.fileMap.getSnapshot() : { stats: {} };
    const stats = snap.stats || { files: 0, folders: 0, truncated: false };
    const folders = vscode.workspace.workspaceFolders || [];
    const ws = folders.length ? folders.map((f) => f.name).join(", ") : "No folder open";
    const editors = vscode.window.visibleTextEditors.length;
    const ram = this._memPct();
    const cpu = Math.min(95, 12 + (editors * 3) + Math.floor(Math.random() * 8));
    const disk = 40;
    const host = os.hostname();
    const platform = `${os.type()} ${os.release()}`;
    const ver = this.context.extension.packageJSON.version || "1.0.0";
    const uptime = this._uptime();
    const cores = os.cpus()?.length || 0;
    const memGb = (os.totalmem() / 1024 / 1024 / 1024).toFixed(1);

    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src ${webview.cspSource} data:; script-src 'nonce-${nonce}';"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Cursor Command Center</title>
<style>
:root {
  --bg: #050d1a;
  --panel: rgba(8, 22, 40, 0.94);
  --border: #12324a;
  --cyan: #00d9ff;
  --cyan2: #4d9fff;
  --text: #c8d6e5;
  --muted: #6a8094;
  --ok: #3dd68c;
  --warn: #ffd95a;
  --danger: #ff6b7a;
  --glow: 0 0 16px rgba(0, 217, 255, 0.35);
  --radius: 12px;
  --font: "Segoe UI", "Rajdhani", system-ui, sans-serif;
}
* { box-sizing: border-box; }
html, body {
  margin: 0; padding: 0; min-height: 100%;
  color: var(--text);
  background:
    radial-gradient(90% 55% at 50% -8%, #0b2a48 0%, transparent 55%),
    linear-gradient(180deg, #030a14 0%, var(--bg) 42%, #040c16 100%);
  font: 11.5px/1.45 var(--font);
}
button { font: inherit; }

/* —— splash —— */
#splash {
  position: fixed; inset: 0; z-index: 30;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  background: radial-gradient(circle at 50% 38%, #0a2540 0%, #02060c 72%);
  transition: opacity 0.55s ease, visibility 0.55s;
}
#splash.hide { opacity: 0; visibility: hidden; pointer-events: none; }
#splash .title {
  font-size: 26px; font-weight: 800; letter-spacing: 0.32em;
  color: var(--cyan); text-shadow: 0 0 22px rgba(0,217,255,0.55);
}
#splash .sub {
  margin-top: 8px; color: var(--muted); font-size: 9px;
  letter-spacing: 0.18em; text-align: center; max-width: 240px;
}
.ring {
  margin: 30px 0 20px; width: 78px; height: 78px; border-radius: 50%;
  border: 2px solid rgba(0,217,255,0.18);
  border-top-color: var(--cyan);
  border-right-color: rgba(0,217,255,0.55);
  box-shadow: var(--glow);
  animation: spin 1.05s linear infinite;
  position: relative;
}
.ring::after {
  content: ""; position: absolute; inset: 30px; border-radius: 50%;
  background: var(--cyan); box-shadow: var(--glow);
}
@keyframes spin { to { transform: rotate(360deg); } }
#splash .cal { letter-spacing: 0.38em; color: #e8f7ff; font-size: 11px; }
.bar {
  margin-top: 16px; width: 200px; height: 6px; border-radius: 999px;
  border: 1px solid var(--border); background: #061320; overflow: hidden;
}
.bar > i {
  display: block; height: 100%; width: 8%;
  background: linear-gradient(90deg, #0088aa, var(--cyan));
  box-shadow: 0 0 10px rgba(0,217,255,0.5);
  transition: width 0.12s linear;
}
#splash .pct { margin-top: 8px; color: var(--muted); font-size: 10px; }
.dots { display: flex; gap: 6px; margin-top: 20px; }
.dots span {
  width: 18px; height: 5px; border-radius: 999px; background: #2a4055;
  transition: background 0.2s, box-shadow 0.2s;
}
.dots span.on { background: var(--cyan); box-shadow: var(--glow); }

/* —— chrome —— */
.shell { padding-bottom: 88px; }
.top {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 12px; border-bottom: 1px solid var(--border);
  background: linear-gradient(180deg, #0a1e30 0%, transparent 100%);
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
  text-transform: uppercase; cursor: pointer; position: relative;
}
.nav button .badge {
  margin-left: 4px; background: #0a3a55; color: var(--cyan);
  border-radius: 999px; padding: 0 5px; font-size: 8px;
}
.nav button.active, .nav button:hover {
  color: #e8f7ff; border-color: #1a6a88; background: #0a3a55; box-shadow: var(--glow);
}

.grid { display: grid; gap: 8px; padding: 10px; }
.card {
  background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 10px 12px; box-shadow: inset 0 0 0 1px rgba(0,217,255,0.04);
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

.core { text-align: center; padding: 16px 8px 12px; }
.orb-wrap {
  width: 120px; height: 120px; margin: 0 auto; position: relative;
}
.orb-ring {
  position: absolute; inset: 0; border-radius: 50%;
  border: 1px solid rgba(0,217,255,0.28);
  box-shadow: inset 0 0 20px rgba(0,217,255,0.08);
  animation: orbit 8s linear infinite;
}
.orb-ring.r2 {
  inset: 10px; border-color: rgba(77,159,255,0.35);
  animation-duration: 11s; animation-direction: reverse;
}
.orb-ring.r3 {
  inset: 22px; border-style: dashed; border-color: rgba(0,217,255,0.22);
  animation-duration: 14s;
}
@keyframes orbit { to { transform: rotate(360deg); } }
.core .orb {
  position: absolute; inset: 28px; border-radius: 50%;
  background:
    radial-gradient(circle at 50% 50%, rgba(0,217,255,0.4) 0%, transparent 55%),
    radial-gradient(circle at 50% 50%, transparent 40%, rgba(0,217,255,0.18) 41%, transparent 42%);
  border: 1px solid rgba(0,217,255,0.5);
  box-shadow: var(--glow);
  animation: pulse 3s ease-in-out infinite;
  display: grid; place-items: center;
}
.core .orb img {
  width: 36px; height: 36px;
  filter: drop-shadow(var(--glow));
}
@keyframes pulse {
  0%,100% { box-shadow: 0 0 12px rgba(0,217,255,0.25); }
  50% { box-shadow: 0 0 28px rgba(0,217,255,0.55); }
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
.agent .wave {
  display: flex; align-items: flex-end; gap: 2px; height: 12px; margin-top: 2px;
}
.agent .wave i {
  width: 2px; background: var(--cyan); border-radius: 1px; opacity: 0.35;
  animation: wave 1.1s ease-in-out infinite;
}
.agent.active .wave i { opacity: 0.9; }
.agent .wave i:nth-child(2) { animation-delay: 0.1s; }
.agent .wave i:nth-child(3) { animation-delay: 0.2s; }
.agent .wave i:nth-child(4) { animation-delay: 0.3s; }
.agent .wave i:nth-child(5) { animation-delay: 0.15s; }
@keyframes wave {
  0%,100% { height: 3px; }
  50% { height: 11px; }
}

.gauges { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; text-align: center; }
.g { padding: 6px 4px; }
.g .ring2 {
  width: 48px; height: 48px; margin: 0 auto 4px; border-radius: 50%;
  display: grid; place-items: center;
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
.feed .item span { display: block; color: var(--muted); font-size: 9px; margin-top: 2px; }

.timeline { position: relative; padding-left: 14px; }
.timeline::before {
  content: ""; position: absolute; left: 3px; top: 4px; bottom: 4px;
  width: 2px; background: linear-gradient(180deg, var(--cyan), transparent);
}
.tl {
  position: relative; margin: 0 0 10px; padding-left: 8px;
}
.tl::before {
  content: ""; position: absolute; left: -13px; top: 4px;
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--cyan); box-shadow: var(--glow);
}
.tl.done::before { background: var(--ok); box-shadow: none; }
.tl .t { font-size: 10px; font-weight: 600; }
.tl .m { font-size: 9px; color: var(--muted); margin-top: 2px; }

.actions { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.actions button, .cta {
  width: 100%; border: 1px solid #1a5a7a; background: #0a3a55; color: #e8f7ff;
  border-radius: 8px; padding: 8px 10px; cursor: pointer; font-size: 10px; text-align: left;
}
.actions button:hover, .cta:hover { background: #0d4d70; box-shadow: var(--glow); }

.llm { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; }
.llm .chip {
  border: 1px solid var(--border); border-radius: 8px; padding: 6px 8px;
  background: #061320; font-size: 9px; display: flex; justify-content: space-between;
}
.llm .chip.on .st { color: var(--ok); }
.llm .chip .st { color: var(--muted); }

.mem-graph {
  height: 84px; border-radius: 8px; position: relative; overflow: hidden;
  background:
    radial-gradient(circle at 20% 40%, rgba(0,217,255,0.25) 0 2px, transparent 3px),
    radial-gradient(circle at 55% 30%, rgba(77,159,255,0.35) 0 2px, transparent 3px),
    radial-gradient(circle at 75% 65%, rgba(0,217,255,0.3) 0 2px, transparent 3px),
    radial-gradient(circle at 35% 70%, rgba(92,225,255,0.25) 0 2px, transparent 3px),
    linear-gradient(135deg, #061320, #0a2540);
  border: 1px solid var(--border);
}
.mem-graph::before {
  content: ""; position: absolute; inset: 10px 14px;
  background:
    linear-gradient(115deg, transparent 48%, rgba(0,217,255,0.35) 49%, transparent 51%),
    linear-gradient(35deg, transparent 45%, rgba(77,159,255,0.25) 50%, transparent 55%),
    linear-gradient(160deg, transparent 40%, rgba(0,217,255,0.2) 50%, transparent 60%);
}

.bottom {
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 8;
  margin: 0; padding: 10px 12px 12px;
  border-top: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(6,19,32,0.92) 0%, #061320 100%);
  backdrop-filter: blur(10px);
  text-align: center;
}
.bottom .hint { color: var(--muted); font-size: 9px; letter-spacing: 0.08em; text-transform: uppercase; }
.bottom .cta {
  margin-top: 6px; text-align: center; font-weight: 700; letter-spacing: 0.04em;
  padding: 11px 14px; border-radius: 999px; box-shadow: var(--glow);
  display: inline-flex; align-items: center; justify-content: center; gap: 10px;
  width: calc(100% - 8px);
}
.wavebar { display: inline-flex; align-items: center; gap: 2px; height: 14px; }
.wavebar i {
  width: 2px; height: 4px; background: var(--cyan); border-radius: 1px;
  animation: wave 0.9s ease-in-out infinite;
}
.wavebar i:nth-child(odd) { animation-delay: 0.12s; }
.footer-meta {
  display: flex; justify-content: space-between; gap: 8px;
  margin-top: 6px; color: var(--muted); font-size: 8px; letter-spacing: 0.04em;
}

.panel { display: none; }
.panel.show { display: block; }
.empty {
  color: var(--muted); font-size: 10px; padding: 8px 0;
}
</style>
</head>
<body>
<div id="splash">
  <div class="title">CURSOR</div>
  <div class="sub">COMMAND CENTER · CODING AGENT HUD</div>
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
    <div class="brand">Command Center</div>
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
    <button data-panel="memory">Memory</button>
    <button data-panel="tools">Tools <span class="badge">6</span></button>
  </div>

  <div class="panel show" id="panel-home">
    <div class="grid">
      <div class="card core">
        <div class="orb-wrap">
          <div class="orb-ring"></div>
          <div class="orb-ring r2"></div>
          <div class="orb-ring r3"></div>
          <div class="orb"><img src="${icon}" alt=""/></div>
        </div>
        <div class="label">Cursor agent core v${escapeHtml(ver)}</div>
        <div class="sub">${escapeHtml(ws)} · ${escapeHtml(host)}</div>
      </div>

      <div class="card">
        <h2>AI core overview</h2>
        <div class="row"><span class="k">Agent core</span><span class="v ok">Active</span></div>
        <div class="row"><span class="k">Mapped files</span><span class="v cyan">${stats.files || 0}</span></div>
        <div class="row"><span class="k">Mapped dirs</span><span class="v cyan">${stats.folders || 0}</span></div>
        <div class="row"><span class="k">Open editors</span><span class="v cyan">${editors}</span></div>
        <div class="row"><span class="k">Scan</span><span class="v ${stats.truncated ? "warn" : "ok"}">${stats.truncated ? "Truncated" : "Complete"}</span></div>
        <div class="row"><span class="k">System</span><span class="v ok">Optimal</span></div>
      </div>

      <div class="card">
        <h2>Active agents</h2>
        <div class="agents">
          ${agentCard("<>", "Coding Agent", true)}
          ${agentCard("🔍", "Research Agent", true)}
          ${agentCard("◈", "Memory Agent", false)}
          ${agentCard("⌂", "Browser Agent", false)}
          ${agentCard("▣", "Task Agent", false)}
          ${agentCard("⚙", "System Agent", false)}
        </div>
      </div>

      <div class="card">
        <h2>Mission timeline</h2>
        <div class="timeline">
          <div class="tl done"><div class="t">Workspace indexed</div><div class="m">Done · ${stats.files || 0} files</div></div>
          <div class="tl"><div class="t">HUD theme ready</div><div class="m">Apply from Tools when needed</div></div>
          <div class="tl"><div class="t">Deep-work block</div><div class="m">Ask Cursor when you want a change</div></div>
        </div>
      </div>

      <div class="card">
        <h2>Live intelligence feed</h2>
        <div class="feed">
          <div class="item ok">Command Center online — cyan HUD aligned to your reference layout.<span>Status · Optimal</span></div>
          <div class="item">File Map indexed this workspace for fast navigation.<span>${stats.files || 0} files · ${stats.folders || 0} dirs</span></div>
          <div class="item warn">CPU/Disk gauges in the sidebar are illustrative; RAM is live from the host.<span>System monitor</span></div>
          <div class="item">Voice is Cursor’s coding agent — not a third-party persona.<span>Policy</span></div>
        </div>
      </div>

      <div class="card">
        <h2>Quick commands</h2>
        <div class="actions">
          <button id="btnChat">Open Cursor Chat</button>
          <button id="btnMap">Open File Map</button>
          <button id="btnTheme">Apply HUD theme</button>
          <button id="btnRefresh">Refresh map</button>
          <button id="btnCmd">Command palette</button>
          <button id="btnTerm">New terminal</button>
        </div>
      </div>

      <div class="card">
        <h2>System monitor</h2>
        <div class="gauges">
          <div class="g"><div class="ring2" style="--p:${cpu}"></div><div class="val">${cpu}%</div><div class="lab">CPU*</div></div>
          <div class="g"><div class="ring2" style="--p:${ram}"></div><div class="val">${ram}%</div><div class="lab">RAM</div></div>
          <div class="g"><div class="ring2" style="--p:${disk}"></div><div class="val">${disk}%</div><div class="lab">Disk*</div></div>
        </div>
        <div class="row" style="margin-top:6px"><span class="k">${cores} cores · ${memGb} GB · up ${escapeHtml(uptime)}</span><span class="v"></span></div>
      </div>

      <div class="card">
        <h2>Memory insights</h2>
        <div class="mem-graph"></div>
        <div class="row" style="margin-top:8px"><span class="k">Mapped nodes</span><span class="v cyan">${(stats.files || 0) + (stats.folders || 0)}</span></div>
        <div class="row"><span class="k">Session editors</span><span class="v">${editors}</span></div>
        <div class="row"><span class="k">Host uptime</span><span class="v">${escapeHtml(uptime)}</span></div>
      </div>

      <div class="card">
        <h2>LLM / agent status</h2>
        <div class="llm">
          <div class="chip on"><span>Cursor</span><span class="st">Connected</span></div>
          <div class="chip on"><span>Composer</span><span class="st">Active</span></div>
          <div class="chip"><span>Claude</span><span class="st">Via Cursor</span></div>
          <div class="chip"><span>GPT</span><span class="st">Via Cursor</span></div>
          <div class="chip"><span>Gemini</span><span class="st">Via Cursor</span></div>
          <div class="chip"><span>Local</span><span class="st">Not linked</span></div>
        </div>
      </div>
    </div>
  </div>

  <div class="panel" id="panel-core">
    <div class="grid">
      <div class="card core">
        <div class="orb-wrap">
          <div class="orb-ring"></div>
          <div class="orb-ring r2"></div>
          <div class="orb"><img src="${icon}" alt=""/></div>
        </div>
        <div class="label">Agent core</div>
        <div class="sub">Session ready · palette JARVIS Command · voice = Cursor</div>
      </div>
      <div class="card">
        <h2>Capabilities</h2>
        <div class="row"><span class="k">Code edits</span><span class="v ok">Online</span></div>
        <div class="row"><span class="k">Workspace map</span><span class="v ok">Online</span></div>
        <div class="row"><span class="k">Theme HUD</span><span class="v ok">Online</span></div>
        <div class="row"><span class="k">Third-party JARVIS speak</span><span class="v">Off by design</span></div>
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
          ${agentCard("🔍", "Research", true)}
          ${agentCard("◈", "Memory", false)}
          ${agentCard("⌂", "Browser", false)}
          ${agentCard("▣", "Task", false)}
          ${agentCard("⚙", "System", false)}
        </div>
      </div>
      <div class="card">
        <h2>Lane notes</h2>
        <div class="feed">
          <div class="item">Coding + Research stay active while you work in Cursor Chat.<span>Primary lanes</span></div>
          <div class="item">Browser / Task / System stay standby until you invoke them.<span>On demand</span></div>
        </div>
      </div>
    </div>
  </div>

  <div class="panel" id="panel-tasks">
    <div class="grid">
      <div class="card">
        <h2>Tasks</h2>
        <div class="timeline">
          <div class="tl done"><div class="t">Install Command Center UI</div><div class="m">Done</div></div>
          <div class="tl"><div class="t">Apply JARVIS Command theme</div><div class="m">Run from Tools or Quick commands</div></div>
          <div class="tl"><div class="t">Explore File Map</div><div class="m">Open the File Map view</div></div>
        </div>
      </div>
      <div class="card">
        <h2>Actions</h2>
        <div class="actions">
          <button id="btnThemeT">Apply HUD theme</button>
          <button id="btnMapT">Open File Map</button>
          <button id="btnChatT">Open Cursor Chat</button>
          <button id="btnRefreshT">Refresh map</button>
        </div>
      </div>
    </div>
  </div>

  <div class="panel" id="panel-memory">
    <div class="grid">
      <div class="card">
        <h2>Workspace memory</h2>
        <div class="mem-graph"></div>
        <div class="row" style="margin-top:8px"><span class="k">Files</span><span class="v cyan">${stats.files || 0}</span></div>
        <div class="row"><span class="k">Folders</span><span class="v cyan">${stats.folders || 0}</span></div>
        <div class="row"><span class="k">Workspace</span><span class="v">${escapeHtml(ws)}</span></div>
      </div>
      <div class="card">
        <h2>Host snapshot</h2>
        <div class="row"><span class="k">Hostname</span><span class="v cyan">${escapeHtml(host)}</span></div>
        <div class="row"><span class="k">RAM in use</span><span class="v">${ram}%</span></div>
        <div class="row"><span class="k">Uptime</span><span class="v">${escapeHtml(uptime)}</span></div>
      </div>
    </div>
  </div>

  <div class="panel" id="panel-tools">
    <div class="grid">
      <div class="card">
        <h2>Tools & skills</h2>
        <div class="actions">
          <button id="btnTheme2">Apply Command theme</button>
          <button id="btnMap2">Large File Map</button>
          <button id="btnSettings">Open settings</button>
          <button id="btnReload">Reload window</button>
          <button id="btnExplorer">Show explorer</button>
          <button id="btnProblems">Problems panel</button>
        </div>
      </div>
      <div class="card">
        <h2>Extension</h2>
        <div class="row"><span class="k">Package</span><span class="v cyan">jarvis-cursor-ui</span></div>
        <div class="row"><span class="k">Version</span><span class="v">${escapeHtml(ver)}</span></div>
        <div class="row"><span class="k">Theme</span><span class="v">JARVIS Command</span></div>
      </div>
    </div>
  </div>
</div>

<div class="bottom">
  <div class="hint">Cursor coding agent</div>
  <button class="cta" id="btnCta">
    <span class="wavebar"><i></i><i></i><i></i><i></i><i></i></span>
    Ask Cursor — ready when you are
    <span class="wavebar"><i></i><i></i><i></i><i></i><i></i></span>
  </button>
  <div class="footer-meta">
    <span>${escapeHtml(host)}</span>
    <span>Network · Local</span>
    <span>v${escapeHtml(ver)}</span>
  </div>
</div>

<script nonce="${nonce}">
  const vscode = acquireVsCodeApi();
  const post = (type, extra = {}) => vscode.postMessage({ type, ...extra });

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
      setTimeout(() => document.getElementById("splash").classList.add("hide"), 220);
    }
  }, 55);

  function clock() {
    const now = new Date();
    document.getElementById("clock").textContent = now.toLocaleTimeString();
    document.getElementById("date").textContent = now.toLocaleDateString(undefined, {
      weekday: "long", year: "numeric", month: "long", day: "numeric"
    });
  }
  clock(); setInterval(clock, 1000);

  document.querySelectorAll(".nav button").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-panel");
      if (id === "map") { post("openFileMap"); return; }
      document.querySelectorAll(".nav button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      document.querySelectorAll(".panel").forEach((p) => p.classList.remove("show"));
      const el = document.getElementById("panel-" + id);
      if (el) el.classList.add("show");
    });
  });

  const bind = (id, fn) => {
    const el = document.getElementById(id);
    if (el) el.onclick = fn;
  };
  bind("btnChat", () => post("chat"));
  bind("btnChatT", () => post("chat"));
  bind("btnCta", () => post("chat"));
  bind("btnMap", () => post("openFileMap"));
  bind("btnMap2", () => post("openFileMap"));
  bind("btnMapT", () => post("openFileMap"));
  bind("btnTheme", () => post("applyTheme"));
  bind("btnTheme2", () => post("applyTheme"));
  bind("btnThemeT", () => post("applyTheme"));
  bind("btnRefresh", () => post("refresh"));
  bind("btnRefreshT", () => post("refresh"));
  bind("btnCmd", () => post("runCommand", { command: "workbench.action.showCommands" }));
  bind("btnTerm", () => post("runCommand", { command: "workbench.action.terminal.new" }));
  bind("btnSettings", () => post("runCommand", { command: "workbench.action.openSettings" }));
  bind("btnReload", () => post("runCommand", { command: "workbench.action.reloadWindow" }));
  bind("btnExplorer", () => post("runCommand", { command: "workbench.view.explorer" }));
  bind("btnProblems", () => post("runCommand", { command: "workbench.actions.view.problems" }));
</script>
</body>
</html>`;
  }
}

function agentCard(ico, name, active) {
  return `<div class="agent ${active ? "active" : "standby"}">
    <div class="n"><span class="ico">${ico}</span>${escapeHtml(name)}</div>
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

module.exports = { CommandCenterViewProvider };
