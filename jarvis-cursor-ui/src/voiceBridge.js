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
  // Cursor (current): composer voice dictation — obsolete *startVoiceChat IDs are gone.
  const tries = [
    "composer.toggleVoiceDictation",
    "composer.cancelVoiceDictation",
    "workbench.action.chat.startVoiceChat",
    "workbench.action.chat.speech.startVoiceChat",
    "inlineChat.startVoiceChat",
    "aichat.startVoiceChat",
  ];
  const failures = [];
  for (const cmd of tries) {
    // cancelVoiceDictation alone would stop mic — only use toggle first; skip cancel in start path
    if (cmd === "composer.cancelVoiceDictation") continue;
    try {
      await vscode.commands.executeCommand(cmd);
      return true;
    } catch (err) {
      failures.push(`${cmd}: ${err && err.message ? err.message : "fail"}`);
    }
  }
  try {
    console.warn("[cortana.voice] startVoice failed:", failures.join(" | "));
  } catch {
    /* ignore */
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
