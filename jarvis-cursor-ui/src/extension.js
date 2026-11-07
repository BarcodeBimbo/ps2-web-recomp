"use strict";

const vscode = require("vscode");
const { FileMapProvider } = require("./fileMapProvider");
const { CommandCenterViewProvider } = require("./commandCenterView");
const { getSuit, setSuit, pickSuit } = require("./suitModes");
const { toggle, bumpKeystroke, getState } = require("./sessionCinema");
const { savePreset, applyPreset } = require("./workspacePresets");
const voice = require("./voiceBridge");

/** @param {vscode.ExtensionContext} context */
function activate(context) {
  const fileMap = new FileMapProvider(context);
  const commandCenter = new CommandCenterViewProvider(context, fileMap);

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("jarvis.commandCenter", commandCenter, {
      webviewOptions: { retainContextWhenHidden: true },
    }),
    vscode.window.registerWebviewViewProvider("jarvis.fileMap", fileMap, {
      webviewOptions: { retainContextWhenHidden: true },
    }),
    vscode.commands.registerCommand("jarvis.fileMap.refresh", () => {
      fileMap.refresh();
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.fileMap.focus", async () => {
      await vscode.commands.executeCommand("workbench.view.extension.jarvisCommand");
      if (typeof fileMap.reveal === "function") fileMap.reveal();
    }),
    vscode.commands.registerCommand("jarvis.commandCenter.focus", async () => {
      await vscode.commands.executeCommand("workbench.view.extension.jarvisCommand");
      if (typeof commandCenter.reveal === "function") commandCenter.reveal();
    }),
    vscode.commands.registerCommand("jarvis.theme.applyHints", async () => {
      const suit = getSuit(context);
      const cfg = vscode.workspace.getConfiguration();
      await cfg.update("workbench.colorTheme", suit.theme, vscode.ConfigurationTarget.Global);
      await cfg.update("workbench.sideBar.location", "left", vscode.ConfigurationTarget.Global);
      vscode.window.showInformationMessage(
        `${suit.theme} applied. Open Command Center for JARVIS HUD + File Map.`
      );
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.suit.pick", async () => {
      await pickSuit(context);
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.suit.set", async (id) => {
      await setSuit(context, id || "mark1");
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.voice.talk", () => voice.startVoice()),
    vscode.commands.registerCommand("jarvis.voice.chat", () => voice.openChat()),
    vscode.commands.registerCommand("jarvis.toggle.focusFortress", async () => {
      await toggle(context, "focusFortress");
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.toggle.cinema", async () => {
      await toggle(context, "cinema");
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.toggle.streamPack", async () => {
      await toggle(context, "streamPack");
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.toggle.friday", async () => {
      await toggle(context, "friday");
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.preset.save", async () => {
      await savePreset(context);
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.preset.apply", async () => {
      await applyPreset(context);
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.hud.refresh", () => commandCenter.refresh())
  );

  const watcher = vscode.workspace.createFileSystemWatcher("**/*");
  const bounce = debounce(() => {
    fileMap.refresh();
    commandCenter.refresh();
  }, 800);
  watcher.onDidCreate(bounce);
  watcher.onDidDelete(bounce);
  watcher.onDidChange(bounce);
  context.subscriptions.push(watcher);

  context.subscriptions.push(
    vscode.languages.onDidChangeDiagnostics(() => commandCenter.refresh())
  );

  context.subscriptions.push(
    vscode.workspace.onDidChangeTextDocument(() => {
      bumpKeystroke(context);
      const st = getState(context);
      commandCenter.post({
        type: "energy",
        keystrokes: st.keystrokes,
      });
    })
  );

  // Periodic GitHUD / threat soft refresh (no splash remount)
  const gitTimer = setInterval(() => commandCenter.refresh({ full: false }), 15000);
  context.subscriptions.push({ dispose: () => clearInterval(gitTimer) });
}

function debounce(fn, ms) {
  let t;
  return () => {
    clearTimeout(t);
    t = setTimeout(fn, ms);
  };
}

function deactivate() {}

module.exports = { activate, deactivate };
