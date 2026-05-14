const vscode = require("vscode");
const { spawn } = require("child_process");
const path = require("path");
const os = require("os");

function activate(context) {
  const runCmd = vscode.commands.registerCommand("angis.run", function () {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;

    const filePath = editor.document.uri.fsPath;
    if (!filePath.endsWith(".ang")) return;

    const outPath = path.join(os.tmpdir(), "angis_output.py");
    const projectDir = path.dirname(filePath);

    const terminal = vscode.window.createTerminal("Angis");
    terminal.show();
    terminal.sendText(
      `python3 -m angis "${filePath}" "${outPath}" && python3 "${outPath}"`,
      true
    );
  });

  context.subscriptions.push(runCmd);
}

function deactivate() {}

module.exports = { activate, deactivate };
