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
        vscode.commands.executeCommand("workbench.view.extension.jarvisCommand");
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
    const cpu = 15; // sidebar can't read real CPU cheaply; placeholder gauge
    const disk = 40;
    const host = os.hostname();
    const ver = this.context.extension.packageJSON.version || "0.3.0";

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
  --panel: rgba(8, 22, 40, 0.92);
  --border: #12324a;
  --cyan: #00d9ff;
  --cyan2: #4d9fff;
  --text: #c8d6e5;
  --muted: #6a8094;
  --ok: #3dd68c;
  --warn: #ffd95a;
  --glow: 0 0 16px rgba(0, 217, 255, 0.35);
  --radius: 12px;
}
* { box-sizing: border-box; }
html, body {
  margin: 0; padding: 0; min-height: 100%;
  color: var(--text);
  background:
    radial-gradient(80% 50% at 50% -5%, #0b2a48 0%, transparent 55%),
    linear-gradient(180deg, #030a14 0%, var(--bg) 40%, #040c16 100%);
  font: 11.5px/1.45 "Segoe UI", system-ui, sans-serif;
}
/* —— splash —— */
#splash {
  position: fixed; inset: 0; z-index: 20;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  background: radial-gradient(circle at 50% 40%, #0a2540 0%, #02060c 70%);
  transition: opacity 0.5s ease, visibility 0.5s;
}
#splash.hide { opacity: 0; visibility: hidden; pointer-events: none; }
#splash .title {
  font-size: 22px; font-weight: 800; letter-spacing: 0.28em;
  color: var(--cyan); text-shadow: var(--glow);
}
#splash .sub { margin-top: 6px; color: var(--muted); font-size: 10px; letter-spacing: 0.12em; }
.ring {
  margin: 28px 0 18px; width: 72px; height: 72px; border-radius: 50%;
  border: 2px solid rgba(0,217,255,0.25);
  border-top-color: var(--cyan);
  box-shadow: var(--glow);
  animation: spin 1.1s linear infinite;
  position: relative;
}
.ring::after {
  content: ""; position: absolute; inset: 28px; border-radius: 50%;
  background: var(--cyan); box-shadow: var(--glow);
}
@keyframes spin { to { transform: rotate(360deg); } }
#splash .cal { letter-spacing: 0.35em; color: #e8f7ff; font-size: 11px; }
.bar {
  margin-top: 16px; width: 180px; height: 6px; border-radius: 999px;
  border: 1px solid var(--border); background: #061320; overflow: hidden;
}
.bar > i {
  display: block; height: 100%; width: 33%;
  background: linear-gradient(90deg, #0088aa, var(--cyan));
  animation: grow 1.4s ease forwards;
}
@keyframes grow { from { width: 8%; } to { width: 100%; } }
#splash .pct { margin-top: 8px; color: var(--muted); font-size: 10px; }
.dots { display: flex; gap: 6px; margin-top: 18px; }
.dots span { width: 6px; height: 6px; border-radius: 50%; background: #2a4055; }
.dots span.on { background: var(--cyan); box-shadow: var(--glow); }

/* —— shell —— */
.top {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 12px; border-bottom: 1px solid var(--border);
}
.top img { width: 18px; height: 18px; filter: drop-shadow(var(--glow)); }
.brand { font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: var(--cyan); font-size: 11px; }
.pill {
  margin-left: 6px; font-size: 9px; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--ok); border: 1px solid #1f5a40; background: #0a281c;
  padding: 2px 8px; border-radius: 999px;
}
.clock { margin-left: auto; color: var(--muted); font-size: 10px; }

.nav {
  display: flex; flex-wrap: wrap; gap: 4px; padding: 8px 10px;
  border-bottom: 1px solid var(--border);
}
.nav button {
  border: 1px solid var(--border); background: #061320; color: var(--muted);
  border-radius: 8px; padding: 5px 8px; font-size: 9px; letter-spacing: 0.04em;
  text-transform: uppercase; cursor: pointer;
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
.row { display: flex; justify-content: space-between; gap: 8px; margin: 4px 0; }
.k { color: var(--muted); } .v { font-weight: 600; } .v.ok { color: var(--ok); } .v.cyan { color: var(--cyan); }

.core { text-align: center; padding: 14px 8px 10px; }
.core .orb {
  width: 88px; height: 88px; margin: 0 auto; position: relative;
  border-radius: 50%;
  background:
    radial-gradient(circle at 50% 50%, rgba(0,217,255,0.35) 0%, transparent 55%),
    radial-gradient(circle at 50% 50%, transparent 40%, rgba(0,217,255,0.15) 41%, transparent 42%),
    radial-gradient(circle at 50% 50%, transparent 58%, rgba(77,159,255,0.25) 59%, transparent 60%);
  border: 1px solid rgba(0,217,255,0.45);
  box-shadow: var(--glow);
  animation: pulse 3s ease-in-out infinite;
}
.core .orb img {
  position: absolute; inset: 22px; width: 44px; height: 44px;
  filter: drop-shadow(var(--glow));
}
@keyframes pulse {
  0%,100% { box-shadow: 0 0 12px rgba(0,217,255,0.25); }
  50% { box-shadow: 0 0 28px rgba(0,217,255,0.55); }
}
.core .label { margin-top: 10px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--cyan); font-weight: 700; font-size: 10px; }
.core .sub { color: var(--muted); font-size: 10px; margin-top: 4px; }

.agents { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.agent {
  border: 1px solid var(--border); border-radius: 8px; padding: 7px 8px; background: #061320;
}
.agent .n { font-weight: 650; font-size: 10px; }
.agent .s { font-size: 9px; color: var(--muted); margin-top: 2px; }
.agent.active .s { color: var(--ok); }
.agent.standby .s { color: var(--muted); }

.gauges { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; text-align: center; }
.g { padding: 6px 4px; }
.g .ring2 {
  width: 46px; height: 46px; margin: 0 auto 4px; border-radius: 50%;
  display: grid; place-items: center;
  background: conic-gradient(var(--cyan) calc(var(--p) * 1%), #12324a 0);
  mask: radial-gradient(farthest-side, transparent 62%, #000 63%);
  -webkit-mask: radial-gradient(farthest-side, transparent 62%, #000 63%);
}
.g .val { font-weight: 700; color: var(--cyan); font-size: 11px; }
.g .lab { color: var(--muted); font-size: 9px; }

.feed .item {
  border-left: 2px solid var(--cyan); padding: 6px 8px; margin: 0 0 6px;
  background: #061320; border-radius: 0 8px 8px 0; font-size: 10px;
}
.feed .item span { display: block; color: var(--muted); font-size: 9px; margin-top: 2px; }

.actions { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.actions button, .cta {
  width: 100%; border: 1px solid #1a5a7a; background: #0a3a55; color: #e8f7ff;
  border-radius: 8px; padding: 8px 10px; cursor: pointer; font-size: 10px; text-align: left;
}
.actions button:hover, .cta:hover { background: #0d4d70; box-shadow: var(--glow); }

.bottom {
  margin: 4px 10px 14px; padding: 12px;
  border: 1px solid var(--border); border-radius: 14px;
  background: linear-gradient(180deg, #0a2540 0%, #061320 100%);
  text-align: center;
}
.bottom .hint { color: var(--muted); font-size: 9px; letter-spacing: 0.08em; text-transform: uppercase; }
.bottom .cta {
  margin-top: 8px; text-align: center; font-weight: 700; letter-spacing: 0.04em;
  padding: 12px; border-radius: 999px; box-shadow: var(--glow);
}
.panel { display: none; }
.panel.show { display: block; }
</style>
</head>
<body>
<div id="splash">
  <div class="title">CURSOR</div>
  <div class="sub">COMMAND CENTER · CODING AGENT</div>
  <div class="ring"></div>
  <div class="cal">CALIBRATING</div>
  <div class="bar"><i></i></div>
  <div class="pct" id="pct">33%</div>
  <div class="dots"><span class="on"></span><span class="on"></span><span></span><span></span><span></span></div>
</div>

<div class="top">
  <img src="${icon}" alt=""/>
  <div class="brand">Command Center</div>
  <div class="pill">Optimal</div>
  <div class="clock" id="clock">—</div>
</div>

<div class="nav">
  <button class="active" data-panel="home">Command Center</button>
  <button data-panel="core">AI Core</button>
  <button data-panel="agents">Agents</button>
  <button data-panel="map" id="navMap">File Map</button>
  <button data-panel="tools">Tools</button>
</div>

<div class="panel show" id="panel-home">
  <div class="grid">
    <div class="card core">
      <div class="orb"><img src="${icon}" alt=""/></div>
      <div class="label">Cursor agent core v${escapeHtml(ver)}</div>
      <div class="sub">${escapeHtml(ws)} · ${escapeHtml(host)}</div>
    </div>

    <div class="card">
      <h2>Workspace pulse</h2>
      <div class="row"><span class="k">Open editors</span><span class="v cyan">${editors}</span></div>
      <div class="row"><span class="k">Mapped files</span><span class="v cyan">${stats.files || 0}</span></div>
      <div class="row"><span class="k">Mapped dirs</span><span class="v">${stats.folders || 0}</span></div>
      <div class="row"><span class="k">Scan</span><span class="v ${stats.truncated ? "" : "ok"}">${stats.truncated ? "Truncated" : "Complete"}</span></div>
    </div>

    <div class="card">
      <h2>Active agents</h2>
      <div class="agents">
        <div class="agent active"><div class="n">Coding Agent</div><div class="s">● Active</div></div>
        <div class="agent active"><div class="n">Research Agent</div><div class="s">● Active</div></div>
        <div class="agent standby"><div class="n">Memory Agent</div><div class="s">Standby</div></div>
        <div class="agent standby"><div class="n">Browser Agent</div><div class="s">Standby</div></div>
        <div class="agent standby"><div class="n">Task Agent</div><div class="s">Standby</div></div>
        <div class="agent standby"><div class="n">System Agent</div><div class="s">Standby</div></div>
      </div>
    </div>

    <div class="card">
      <h2>System monitor</h2>
      <div class="gauges">
        <div class="g"><div class="ring2" style="--p:${cpu}"></div><div class="val">${cpu}%</div><div class="lab">CPU*</div></div>
        <div class="g"><div class="ring2" style="--p:${ram}"></div><div class="val">${ram}%</div><div class="lab">RAM</div></div>
        <div class="g"><div class="ring2" style="--p:${disk}"></div><div class="val">${disk}%</div><div class="lab">Disk*</div></div>
      </div>
      <div class="row" style="margin-top:6px"><span class="k">*CPU/Disk illustrative in sidebar</span><span class="v"></span></div>
    </div>

    <div class="card">
      <h2>Live feed</h2>
      <div class="feed">
        <div class="item">Command Center layout matches your reference HUD.<span>Cyan on navy · Cursor voice</span></div>
        <div class="item">File Map indexes this workspace for fast navigation.<span>${stats.files || 0} files</span></div>
        <div class="item">Ask in chat when you want a change — I’ll keep edits scoped.<span>Coding agent</span></div>
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
  </div>
</div>

<div class="panel" id="panel-core">
  <div class="grid">
    <div class="card core">
      <div class="orb"><img src="${icon}" alt=""/></div>
      <div class="label">Agent core</div>
      <div class="sub">Session ready · theme JARVIS Command palette · voice = Cursor</div>
    </div>
    <div class="card">
      <h2>Capabilities</h2>
      <div class="row"><span class="k">Code edits</span><span class="v ok">Online</span></div>
      <div class="row"><span class="k">Workspace map</span><span class="v ok">Online</span></div>
      <div class="row"><span class="k">Third-party JARVIS speak</span><span class="v">Off by design</span></div>
    </div>
  </div>
</div>

<div class="panel" id="panel-agents">
  <div class="grid">
    <div class="card">
      <h2>Agent roster</h2>
      <div class="agents">
        <div class="agent active"><div class="n">Coding</div><div class="s">● Active</div></div>
        <div class="agent active"><div class="n">Research</div><div class="s">● Active</div></div>
        <div class="agent standby"><div class="n">Memory</div><div class="s">Standby</div></div>
        <div class="agent standby"><div class="n">Browser</div><div class="s">Standby</div></div>
        <div class="agent standby"><div class="n">Task</div><div class="s">Standby</div></div>
        <div class="agent standby"><div class="n">System</div><div class="s">Standby</div></div>
      </div>
    </div>
  </div>
</div>

<div class="panel" id="panel-tools">
  <div class="grid">
    <div class="card">
      <h2>Tools</h2>
      <div class="actions">
        <button id="btnTheme2">Apply Command theme</button>
        <button id="btnMap2">Large File Map</button>
        <button id="btnSettings">Open settings</button>
        <button id="btnReload">Reload window</button>
      </div>
    </div>
  </div>
</div>

<div class="bottom">
  <div class="hint">Cursor coding agent</div>
  <button class="cta" id="btnCta">Ask Cursor — ready when you are</button>
</div>

<script nonce="${nonce}">
  const vscode = acquireVsCodeApi();
  const post = (type, extra = {}) => vscode.postMessage({ type, ...extra });

  // splash
  let p = 33;
  const pct = document.getElementById("pct");
  const tick = setInterval(() => {
    p = Math.min(100, p + 7);
    pct.textContent = p + "%";
    if (p >= 100) {
      clearInterval(tick);
      setTimeout(() => document.getElementById("splash").classList.add("hide"), 200);
    }
  }, 120);

  function clock() {
    document.getElementById("clock").textContent = new Date().toLocaleString();
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

  document.getElementById("btnChat").onclick = () => post("chat");
  document.getElementById("btnCta").onclick = () => post("chat");
  document.getElementById("btnMap").onclick = () => post("openFileMap");
  document.getElementById("btnMap2").onclick = () => post("openFileMap");
  document.getElementById("btnTheme").onclick = () => post("applyTheme");
  document.getElementById("btnTheme2").onclick = () => post("applyTheme");
  document.getElementById("btnRefresh").onclick = () => post("refresh");
  document.getElementById("btnCmd").onclick = () => post("runCommand", { command: "workbench.action.showCommands" });
  document.getElementById("btnTerm").onclick = () => post("runCommand", { command: "workbench.action.terminal.new" });
  document.getElementById("btnSettings").onclick = () => post("runCommand", { command: "workbench.action.openSettings" });
  document.getElementById("btnReload").onclick = () => post("runCommand", { command: "workbench.action.reloadWindow" });
</script>
</body>
</html>`;
  }
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

module.exports = { CommandCenterViewProvider };
