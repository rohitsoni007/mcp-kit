# MCP CLI - Node.js Wrapper

A Node.js wrapper for the [MCP Kit](https://github.com/rohitsoni007/mcp-kit) Python CLI tool, allowing easy installation and usage via npm.

## Installation

```bash
npm install -g mcp-cli
```

## Prerequisites

- Node.js 16.0.0 or higher
- Python 3.11+ (automatically detected during installation)
- Git (for installation from source)

## Usage

After installation, you can use the CLI commands directly:

```bash
# Interactive MCP server selection
mcp init

# Configure for specific AI agent
mcp init -a copilot
mcp init -a continue
mcp init -a kiro
mcp init -a cursor

# Initialize in current directory
mcp init .

# Initialize in specific directory
mcp init my-project -a kiro
```

## How it works

This Node.js wrapper:

1. **Installation**: Automatically installs the Python `mcp-cli` package using `uv` (preferred) or `pip` (fallback)
2. **Execution**: Provides `mcp-cli` and `mcp` commands that proxy to the Python implementation
3. **Cross-platform**: Works on Windows, macOS, and Linux

## Programmatic Usage

You can also use this package programmatically in your Node.js applications:

```javascript
const { executeMcpCli, isMcpCliInstalled } = require('mcp-cli');

async function example() {
  // Check if mcp-cli is installed
  const isInstalled = await isMcpCliInstalled();
  console.log('MCP CLI installed:', isInstalled);

  // Execute mcp-cli command
  const result = await executeMcpCli(['init', '.', '-a', 'kiro']);
  console.log('Exit code:', result.code);
}
```

## Troubleshooting

### Python not found
If you get a "Python not found" error:
1. Install Python 3.11+ from [python.org](https://www.python.org/downloads/)
2. Ensure Python is in your PATH
3. Try reinstalling: `npm uninstall -g mcp-cli && npm install -g mcp-cli`

### Installation fails
If the automatic installation fails:
1. Install manually: `pip install git+https://github.com/rohitsoni007/mcp-kit`
2. Or use uv: `uv tool install mcp-cli --from git+https://github.com/rohitsoni007/mcp-kit`

## Supported AI Agents

- GitHub Copilot
- Continue
- Kiro
- Cursor
- Claude Code
- Gemini CLI
- Qoder
- LM Studio

## License

MIT - See the main [MCP Kit repository](https://github.com/rohitsoni007/mcp-kit) for details.

## Links

- [Main Repository](https://github.com/rohitsoni007/mcp-kit)
- [Python Package (PyPI)](https://pypi.org/project/mcp-cli/)
- [Issues](https://github.com/rohitsoni007/mcp-kit/issues)