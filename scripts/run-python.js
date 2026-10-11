/**
 * Cross-platform runner that automatically executes Python commands
 * using the local virtual environment (venv) if present, or system python.
 */
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const rootDir = path.resolve(__dirname, '..');
const isWin = process.platform === 'win32';

const venvPythonWin = path.join(rootDir, 'venv', 'Scripts', 'python.exe');
const venvPythonUnix = path.join(rootDir, 'venv', 'bin', 'python');

let pythonCmd = 'python';
if (isWin && fs.existsSync(venvPythonWin)) {
  pythonCmd = venvPythonWin;
} else if (!isWin && fs.existsSync(venvPythonUnix)) {
  pythonCmd = venvPythonUnix;
}

const args = process.argv.slice(2);
const child = spawn(pythonCmd, args, {
  cwd: rootDir,
  stdio: 'inherit',
  shell: false,
});

child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
  } else {
    process.exit(code !== null ? code : 0);
  }
});

process.on('SIGINT', () => {
  if (child && !child.killed) child.kill('SIGINT');
});

process.on('SIGTERM', () => {
  if (child && !child.killed) child.kill('SIGTERM');
});
