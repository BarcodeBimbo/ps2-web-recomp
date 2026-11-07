"use strict";

const vscode = require("vscode");
const { execFile } = require("child_process");
const { promisify } = require("util");

const execFileAsync = promisify(execFile);

/**
 * @returns {Promise<{branch:string,dirty:boolean,ahead:number,behind:number,staged:number,unstaged:number,ok:boolean,detail:string}>}
 */
async function getGitStatus() {
  const folders = vscode.workspace.workspaceFolders;
  if (!folders?.length) {
    return empty("No workspace");
  }
  const cwd = folders[0].uri.fsPath;
  try {
    const { stdout: branchOut } = await execFileAsync(
      "git",
      ["rev-parse", "--abbrev-ref", "HEAD"],
      { cwd, windowsHide: true }
    );
    const branch = branchOut.trim() || "HEAD";
    const { stdout: statusOut } = await execFileAsync(
      "git",
      ["status", "--porcelain", "-b"],
      { cwd, windowsHide: true }
    );
    const lines = statusOut.split(/\r?\n/).filter(Boolean);
    const header = lines[0] || "";
    let ahead = 0;
    let behind = 0;
    const aheadM = /ahead (\d+)/.exec(header);
    const behindM = /behind (\d+)/.exec(header);
    if (aheadM) ahead = Number(aheadM[1]);
    if (behindM) behind = Number(behindM[1]);
    const files = lines.slice(1);
    let staged = 0;
    let unstaged = 0;
    for (const line of files) {
      const x = line[0];
      const y = line[1];
      if (x && x !== " " && x !== "?") staged += 1;
      if (y && y !== " ") unstaged += 1;
      if (line.startsWith("??")) unstaged += 1;
    }
    const dirty = files.length > 0;
    return {
      branch,
      dirty,
      ahead,
      behind,
      staged,
      unstaged,
      ok: true,
      detail: dirty ? `${files.length} changed` : "Clean",
    };
  } catch (e) {
    return empty(e && e.message ? String(e.message).slice(0, 80) : "Not a git repo");
  }
}

function empty(detail) {
  return {
    branch: "—",
    dirty: false,
    ahead: 0,
    behind: 0,
    staged: 0,
    unstaged: 0,
    ok: false,
    detail,
  };
}

module.exports = { getGitStatus };
