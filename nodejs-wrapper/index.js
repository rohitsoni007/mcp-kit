const { spawn } = require('cross-spawn');
const which = require('which');
const path = require('path');

/**
 * Execute mcp-cli command with given arguments
 * @param {string[]} args - Command line arguments
 * @param {Object} options - Spawn options
 * @returns {Promise<{code: number, stdout: string, stderr: string}>}
 */
async function executeMcpCli(args = [], options = {}) {
  return new Promise((resolve, reject) => {
    // Try to find Python executable
    const pythonCommands = ['python3', 'python', 'py'];
    let pythonPath = null;

    for (const cmd of pythonCommands) {
      try {
        pythonPath = which.sync(cmd);
        break;
      } catch (e) {
        // Continue to next command
      }
    }

    if (!pythonPath) {
      return reject(new Error('Python not found. Please install Python 3.11+ to use mcp-cli.'));
    }

    // Execute mcp-cli using python -m
    const child = spawn(pythonPath, ['-m', 'mcp_cli', ...args], {
      stdio: options.stdio || 'inherit',
      ...options
    });

    let stdout = '';
    let stderr = '';

    if (child.stdout) {
      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });
    }

    if (child.stderr) {
      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });
    }

    child.on('close', (code) => {
      resolve({ code, stdout, stderr });
    });

    child.on('error', (error) => {
      reject(error);
    });
  });
}

/**
 * Check if mcp-cli is installed
 * @returns {Promise<boolean>}
 */
async function isMcpCliInstalled() {
  try {
    const result = await executeMcpCli(['--version'], { stdio: 'pipe' });
    return result.code === 0;
  } catch (e) {
    return false;
  }
}

module.exports = {
  executeMcpCli,
  isMcpCliInstalled
};