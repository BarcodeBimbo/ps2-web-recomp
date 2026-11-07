"use strict";

const vscode = require("vscode");
const os = require("os");
const path = require("path");

/**
 * Command Center shell modeled on jarvis.institute dashboard layout
 * (top modes, left status, center core, right activity) — copy is Cursor voice.
 */
class CommandCenterViewProvider {
  /**
   * @param {vscode.ExtensionContext} context
   * @param {import("./fileMapProvider").FileMapProvider} fileMap
   */
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
    if (this.view) {
      this.view.webview.html = this._html(this.view.webview);
    }
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
      case "openFolder":
        vscode.commands.executeCommand("vscode.openFolder");
        break;
      case "runCommand":
        if (msg.command) vscode.commands.executeCommand(msg.command);
        break;
      default:
        break;
    }
  }

  _workspaceName() {
    const folders = vscode.workspace.workspaceFolders || [];
    if (!folders.length) return "No folder open";
    if (folders.length === 1) return folders[0].name;
    return `${folders.length} workspaces`;
  }

  _html(webview) {
    const nonce = String(Date.now());
    const icon = webview.asWebviewUri(
      vscode.Uri.joinPath(this.context.extensionUri, "media", "arc-reactor.svg")
    );
    const snap = this.fileMap.getSnapshot ? this.fileMap.getSnapshot() : { stats: {} };
    const stats = snap.stats || { files: 0, folders: 0, truncated: false };
    const editors = vscode.window.visibleTextEditors.length;
    const ws = this._workspaceName();
    const host = os.hostname();
    const now = new Date().toLocaleString();

    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src ${webview.cspSource} data:; script-src 'nonce-${nonce}';"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Cursor Command Center</title>
<style>
  :root {
    --bg: #040c16;
    --panel: rgba(7, 24, 40, 0.92);
    --border: #0e2a44;
    --cyan: #00d4ff;
    --cyan2: #5ce1ff;
    --text: #c8d6e5;
    --muted: #6a8094;
    --ok: #3dd68c;
    --warn: #ffc94d;
    --glow: 0 0 14px rgba(0, 212, 255, 0.28);
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0; min-height: 100%;
    color: var(--text);
    background:
      radial-gradient(90% 60% at 50% 0%, #0b2a44 0%, transparent 55%),
      linear-gradient(180deg, #030a12 0%, #040c16 100%);
    font: 12px/1.45 "Segoe UI", system-ui, sans-serif;
  }
  .top {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 12px;
    border-bottom: 1px solid var(--border);
  }
  .top img { width: 20px; height: 20px; filter: drop-shadow(var(--glow)); }
  .brand {
    font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase;
    color: var(--cyan2); font-weight: 700;
  }
  .status-pill {
    margin-left: auto;
    font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--ok); border: 1px solid #1f5a40; background: #0a281c;
    padding: 3px 8px; border-radius: 999px;
  }
  .modes {
    display: flex; gap: 4px; padding: 8px 10px;
    border-bottom: 1px solid var(--border);
    overflow-x: auto;
  }
  .mode {
    flex: 0 0 auto;
    border: 1px solid var(--border); background: #061320; color: var(--muted);
    border-radius: 6px; padding: 6px 10px; font-size: 10px; letter-spacing: 0.06em;
    text-transform: uppercase; cursor: pointer;
  }
  .mode.active {
    color: #e8f7ff; border-color: #1a6a88; background: #0a3a55;
    box-shadow: var(--glow);
  }
  .grid {
    display: grid; gap: 8px; padding: 10px;
    grid-template-columns: 1fr;
  }
  .card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 12px;
    box-shadow: inset 0 0 0 1px rgba(0, 212, 255, 0.04);
  }
  .card h2 {
    margin: 0 0 8px;
    font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase;
    color: var(--cyan2); font-weight: 650;
  }
  .row { display: flex; justify-content: space-between; gap: 8px; margin: 4px 0; }
  .k { color: var(--muted); }
  .v { color: var(--text); font-weight: 600; }
  .v.ok { color: var(--ok); }
  .v.cyan { color: var(--cyan); }
  .core {
    text-align: center; padding: 16px 10px 12px;
  }
  .core img {
    width: 64px; height: 64px;
    filter: drop-shadow(0 0 18px rgba(0, 212, 255, 0.45));
  }
  .core .label {
    margin-top: 8px; font-size: 11px; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--cyan2);
  }
  .core .sub { color: var(--muted); font-size: 11px; margin-top: 4px; }
  .actions { display: grid; gap: 6px; }
  button {
    width: 100%;
    background: #0a3a55; color: #e8f7ff; border: 1px solid #1a5a7a;
    border-radius: 6px; padding: 8px 10px; cursor: pointer; font-size: 11px;
    text-align: left;
  }
  button:hover { background: #0d4d70; box-shadow: var(--glow); }
  .feed { display: grid; gap: 6px; }
  .feed .item {
    border-left: 2px solid var(--cyan);
    padding: 6px 8px; background: #061320; border-radius: 0 6px 6px 0;
    color: var(--text); font-size: 11px;
  }
  .feed .item span { color: var(--muted); display: block; font-size: 10px; margin-top: 2px; }
  .bottom {
    margin: 4px 10px 14px;
    border: 1px solid var(--border); border-radius: 10px;
    background: linear-gradient(180deg, #0a2034 0%, #061320 100%);
    padding: 10px 12px;
  }
  .bottom .hint { color: var(--muted); font-size: 10px; margin-bottom: 6px; }
  .bottom .cta {
    font-size: 12px; font-weight: 700; letter-spacing: 0.04em;
    color: #e8f7ff;
  }
</style>
</head>
<body>
  <div class="top">
    <img src="${icon}" alt=""/>
    <div class="brand">Cursor Command Center</div>
    <div class="status-pill">Session ready</div>
  </div>

  <div class="modes">
    <button class="mode active" data-mode="center">Command Center</button>
    <button class="mode" data-mode="map" id="gotoMap">File Map</button>
    <button class="mode" data-mode="theme" id="applyTheme">Theme</button>
  </div>

  <div class="grid">
    <div class="card">
      <h2>Workspace pulse</h2>
      <div class="row"><span class="k">Folder</span><span class="v cyan">${escapeHtml(ws)}</span></div>
      <div class="row"><span class="k">Host</span><span class="v">${escapeHtml(host)}</span></div>
      <div class="row"><span class="k">Open editors</span><span class="v">${editors}</span></div>
      <div class="row"><span class="k">Mapped files</span><span class="v cyan">${stats.files || 0}</span></div>
      <div class="row"><span class="k">Mapped dirs</span><span class="v">${stats.folders || 0}</span></div>
      <div class="row"><span class="k">Scan</span><span class="v ${stats.truncated ? "" : "ok"}">${stats.truncated ? "Truncated — raise jarvis.fileMap.maxEntries" : "Complete"}</span></div>
    </div>

    <div class="card core">
      <img src="${icon}" alt=""/>
      <div class="label">Cursor agent core</div>
      <div class="sub">Coding agent online · ${escapeHtml(now)}</div>
    </div>

    <div class="card">
      <h2>Active lanes</h2>
      <div class="row"><span class="k">Editor</span><span class="v ok">Active</span></div>
      <div class="row"><span class="k">File Map</span><span class="v ok">Ready</span></div>
      <div class="row"><span class="k">Theme</span><span class="v cyan">JARVIS Command palette</span></div>
      <div class="row"><span class="k">Voice persona</span><span class="v">Cursor (not third-party assistant)</span></div>
    </div>

    <div class="card">
      <h2>Quick actions</h2>
      <div class="actions">
        <button id="refresh">Refresh workspace map</button>
        <button id="gotoMap2">Open large File Map</button>
        <button id="applyTheme2">Apply Command theme</button>
        <button id="cmdPalette">Open command palette</button>
      </div>
    </div>

    <div class="card">
      <h2>Live feed</h2>
      <div class="feed">
        <div class="item">Command Center shell mirrors jarvis.institute layout patterns.<span>Structure reference only — Cursor owns the voice.</span></div>
        <div class="item">File Map is the holographic project tree for this workspace.<span>${stats.files || 0} files indexed</span></div>
        <div class="item">Ask me in chat when you want a change — I’ll keep edits scoped and concrete.<span>Cursor coding agent</span></div>
      </div>
    </div>
  </div>

  <div class="bottom">
    <div class="hint">Interaction bar (Cursor voice)</div>
    <div class="cta">Ready when you are — say what to build, fix, or map next.</div>
  </div>

  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    const post = (type, extra = {}) => vscode.postMessage({ type, ...extra });
    document.getElementById("refresh").onclick = () => post("refresh");
    document.getElementById("gotoMap").onclick = () => post("openFileMap");
    document.getElementById("gotoMap2").onclick = () => post("openFileMap");
    document.getElementById("applyTheme").onclick = () => post("applyTheme");
    document.getElementById("applyTheme2").onclick = () => post("applyTheme");
    document.getElementById("cmdPalette").onclick = () => post("runCommand", { command: "workbench.action.showCommands" });
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
