"use strict";

const vscode = require("vscode");
const { FileMapProvider } = require("./fileMapProvider");
const { CommandCenterViewProvider } = require("./commandCenterView");

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
    vscode.commands.registerCommand("jarvis.theme.applyHints", async () => {
      const cfg = vscode.workspace.getConfiguration();
      await cfg.update("workbench.colorTheme", "JARVIS Command", vscode.ConfigurationTarget.Global);
      await cfg.update("workbench.sideBar.location", "left", vscode.ConfigurationTarget.Global);
      vscode.window.showInformationMessage(
        "Command theme applied. Open the Command Center activity icon for overview + File Map."
      );
    })
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
