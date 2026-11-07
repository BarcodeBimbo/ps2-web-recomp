"use strict";

const vscode = require("vscode");

async function openChat() {
  const tries = [
    "workbench.action.chat.open",
    "aichat.newchataction",
    "composer.openComposer",
    "workbench.panel.chat.view.copilot.focus",
  ];
  for (const cmd of tries) {
    try {
      await vscode.commands.executeCommand(cmd);
      return true;
    } catch {
      /* next */
    }
  }
  vscode.window.showInformationMessage("Open Cursor Chat to talk to CORTANA.");
  return false;
}

async function startVoice() {
  const tries = [
    "workbench.action.chat.startVoiceChat",
    "workbench.action.chat.speech.startVoiceChat",
    "inlineChat.startVoiceChat",
    "aichat.startVoiceChat",
  ];
  for (const cmd of tries) {
    try {
      await vscode.commands.executeCommand(cmd);
      return true;
    } catch {
      /* next */
    }
  }
  // Fall back to chat — user can hit the mic there
  return openChat();
}

/**
 * Palette/keybinding entry for wake listen.
 * Continuous "Hey Cortana" recognition is armed by the inject HUD script;
 * this command starts the voice channel (same path as Talk).
 */
async function wakeListen() {
  return startVoice();
}

module.exports = { openChat, startVoice, wakeListen };
