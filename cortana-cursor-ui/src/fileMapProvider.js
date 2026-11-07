"use strict";

const vscode = require("vscode");
const path = require("path");
const fs = require("fs");

const SKIP_DEFAULT = [
  ".git",
  "node_modules",
  ".next",
  "dist",
  "out",
  "build",
  ".cursor",
  "agent-transcripts",
  "terminals",
];

class FileMapProvider {
  /** @param {vscode.ExtensionContext} context */
  constructor(context) {
    this.context = context;
    /** @type {vscode.WebviewView | undefined} */
    this.view = undefined;
    this._tree = null;
    this._stats = { files: 0, folders: 0, truncated: false };
  }

  reveal() {
    if (this.view) this.view.show?.(true);
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
    this._tree = this._scanWorkspace();
    if (this.view) {
      this.view.webview.html = this._html(this.view.webview);
    }
  }

  getSnapshot() {
    return { tree: this._tree, stats: this._stats };
  }

  _onMessage(msg) {
    if (!msg || typeof msg !== "object") return;
    if (msg.type === "open" && msg.path) {
      const uri = vscode.Uri.file(msg.path);
      vscode.commands.executeCommand("vscode.open", uri);
    } else if (msg.type === "reveal" && msg.path) {
      vscode.commands.executeCommand("revealInExplorer", vscode.Uri.file(msg.path));
    } else if (msg.type === "refresh") {
      this.refresh();
    }
  }

  _ignoreSet() {
    const cfg = vscode.workspace.getConfiguration("CORTANA");
    const list = cfg.get("fileMap.ignore", SKIP_DEFAULT);
    return new Set((list || SKIP_DEFAULT).map((s) => String(s).toLowerCase()));
  }

  _maxEntries() {
    return vscode.workspace.getConfiguration("CORTANA").get("fileMap.maxEntries", 4000);
  }

  _scanWorkspace() {
    const folders = vscode.workspace.workspaceFolders || [];
    this._stats = { files: 0, folders: 0, truncated: false };
    if (!folders.length) {
      return { name: "(no workspace)", path: "", kind: "root", children: [] };
    }
    const ignore = this._ignoreSet();
    const max = this._maxEntries();
    const roots = folders.map((f) =>
      this._walk(f.uri.fsPath, f.name, ignore, max, { count: 0 })
    );
    if (roots.length === 1) return roots[0];
    return {
      name: "workspaces",
      path: "",
      kind: "root",
      children: roots,
    };
  }

  _walk(dir, name, ignore, max, counter) {
    /** @type {{ name: string, path: string, kind: string, children?: any[] }} */
    const node = { name, path: dir, kind: "folder", children: [] };
    if (counter.count >= max) {
      this._stats.truncated = true;
      return node;
    }
    let entries = [];
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return node;
    }
    entries.sort((a, b) => {
      if (a.isDirectory() !== b.isDirectory()) return a.isDirectory() ? -1 : 1;
      return a.name.localeCompare(b.name);
    });
    for (const ent of entries) {
      if (counter.count >= max) {
        this._stats.truncated = true;
        break;
      }
      if (ent.name === "." || ent.name === "..") continue;
      if (ignore.has(ent.name.toLowerCase())) continue;
      const full = path.join(dir, ent.name);
      counter.count += 1;
      if (ent.isDirectory()) {
        this._stats.folders += 1;
        node.children.push(this._walk(full, ent.name, ignore, max, counter));
      } else if (ent.isFile()) {
        this._stats.files += 1;
        node.children.push({ name: ent.name, path: full, kind: "file" });
      }
    }
    return node;
  }

  _html(webview) {
    const tree = this._tree || { name: "…", children: [] };
    const stats = this._stats;
    const nonce = String(Date.now());
    const icon = webview.asWebviewUri(
      vscode.Uri.joinPath(this.context.extensionUri, "media", "arc-reactor.svg")
    );
    const data = JSON.stringify(tree).replace(/</g, "\\u003c");
    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src ${webview.cspSource} data:; script-src 'nonce-${nonce}';"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Cursor File Map</title>
<style>
  :root {
    --bg: #040c16;
    --panel: #071828;
    --panel-border: #0e2a44;
    --cyan: #00d4ff;
    --cyan-dim: #5ce1ff;
    --text: #c8d6e5;
    --muted: #6a8094;
    --glow: 0 0 12px rgba(0, 212, 255, 0.35);
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0; height: 100%;
    background: radial-gradient(120% 80% at 50% -10%, #0a2540 0%, var(--bg) 55%);
    color: var(--text);
    font: 12px/1.45 "Segoe UI", system-ui, sans-serif;
  }
  .hdr {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 12px 8px;
    border-bottom: 1px solid var(--panel-border);
    background: linear-gradient(180deg, #0a1e30 0%, transparent 100%);
  }
  .hdr img { width: 18px; height: 18px; filter: drop-shadow(var(--glow)); }
  .hdr h1 {
    margin: 0; font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase;
    color: var(--cyan-dim); font-weight: 600;
  }
  .hdr .meta { margin-left: auto; color: var(--muted); font-size: 10px; }
  .toolbar {
    display: flex; gap: 6px; padding: 8px 10px;
    border-bottom: 1px solid var(--panel-border);
  }
  input[type="search"] {
    flex: 1; background: #050e18; border: 1px solid #14324a; color: var(--text);
    border-radius: 4px; padding: 6px 8px; outline: none;
  }
  input[type="search"]:focus { border-color: var(--cyan); box-shadow: var(--glow); }
  button {
    background: #0a3a55; color: #e8f7ff; border: 1px solid #1a5a7a;
    border-radius: 4px; padding: 5px 8px; cursor: pointer; font-size: 11px;
  }
  button:hover { background: #0d4d70; box-shadow: var(--glow); }
  .tree-wrap {
    padding: 6px 4px 16px;
    overflow: auto; height: calc(100vh - 88px);
  }
  ul { list-style: none; margin: 0; padding-left: 14px; }
  ul.root { padding-left: 6px; }
  li { margin: 1px 0; }
  .row {
    display: flex; align-items: center; gap: 6px;
    padding: 3px 6px; border-radius: 4px; cursor: pointer;
    border: 1px solid transparent;
  }
  .row:hover {
    background: rgba(0, 212, 255, 0.08);
    border-color: rgba(0, 212, 255, 0.22);
  }
  .tw { width: 12px; color: var(--cyan); opacity: 0.7; font-size: 10px; user-select: none; }
  .ic { width: 12px; opacity: 0.85; }
  .nm { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .folder .nm { color: var(--cyan-dim); font-weight: 600; }
  .file .nm { color: var(--text); }
  .collapsed > ul { display: none; }
  .badge {
    margin: 8px 10px; padding: 6px 8px; border-radius: 6px;
    background: var(--panel); border: 1px solid var(--panel-border);
    color: var(--muted); font-size: 10px;
  }
  .badge strong { color: var(--cyan); font-weight: 600; }
</style>
</head>
<body>
  <div class="hdr">
    <img src="${icon}" alt=""/>
    <h1>Workspace File Map</h1>
    <div class="meta"><strong style="color:var(--cyan)">${stats.files}</strong> files · ${stats.folders} dirs${stats.truncated ? " · truncated" : ""}</div>
  </div>
  <div class="toolbar">
    <input id="q" type="search" placeholder="Filter map…" spellcheck="false"/>
    <button id="refresh" title="Refresh">↻</button>
  </div>
  <div class="badge">CORTANA File Map — click a file to open it. Holographic project structure for this workspace.</div>
  <div class="tree-wrap"><ul class="root" id="root"></ul></div>
  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    const TREE = ${data};

    function el(tag, cls, text) {
      const n = document.createElement(tag);
      if (cls) n.className = cls;
      if (text != null) n.textContent = text;
      return n;
    }

    function render(node, ul) {
      const li = el("li");
      li.className = node.kind === "folder" || node.kind === "root" ? "folder" : "file";
      if (node.kind === "folder" || node.kind === "root") li.classList.add("collapsed");
      const row = el("div", "row " + (node.kind === "file" ? "file" : "folder"));
      const tw = el("span", "tw", node.children && node.children.length ? "▸" : " ");
      const ic = el("span", "ic", node.kind === "file" ? "▣" : "⌂");
      const nm = el("span", "nm", node.name);
      row.appendChild(tw); row.appendChild(ic); row.appendChild(nm);
      row.title = node.path || node.name;
      row.addEventListener("click", (e) => {
        e.stopPropagation();
        if (node.kind === "file" && node.path) {
          vscode.postMessage({ type: "open", path: node.path });
        } else if (node.children) {
          li.classList.toggle("collapsed");
          tw.textContent = li.classList.contains("collapsed") ? "▸" : "▾";
        }
      });
      row.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        if (node.path) vscode.postMessage({ type: "reveal", path: node.path });
      });
      li.appendChild(row);
      if (node.children && node.children.length) {
        const cul = el("ul");
        for (const c of node.children) render(c, cul);
        li.appendChild(cul);
      }
      ul.appendChild(li);
    }

    const root = document.getElementById("root");
    render(TREE, root);
    // expand first level
    root.querySelectorAll(":scope > li.folder").forEach((li) => {
      li.classList.remove("collapsed");
      const tw = li.querySelector(".tw");
      if (tw) tw.textContent = "▾";
    });

    document.getElementById("refresh").onclick = () => vscode.postMessage({ type: "refresh" });
    document.getElementById("q").addEventListener("input", (e) => {
      const q = e.target.value.trim().toLowerCase();
      root.querySelectorAll("li").forEach((li) => {
        const name = (li.querySelector(".nm") || {}).textContent || "";
        const hit = !q || name.toLowerCase().includes(q);
        li.style.display = hit ? "" : "none";
        if (hit && q) {
          li.classList.remove("collapsed");
          const tw = li.querySelector(":scope > .row .tw");
          if (tw && li.querySelector(":scope > ul")) tw.textContent = "▾";
        }
      });
    });
  </script>
</body>
</html>`;
  }
}

module.exports = { FileMapProvider };
