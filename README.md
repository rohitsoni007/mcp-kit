# MCP Kit

A command-line interface tool for downloading and configuring Model Context Protocol (MCP) servers from the official MCP ecosystem.

## Overview

MCP Kit provides an interactive way to discover, download, and configure MCP servers from the official [Model Context Protocol Servers](https://github.com/modelcontextprotocol/servers) and [Github Mcp Registry](https://github.com/mcp) ecosystem. The tool automatically configures servers for your preferred AI coding agent with cross-platform support and intelligent configuration management.

The Model Context Protocol (MCP) is an open standard that enables AI assistants to securely access external data sources and tools. MCP Kit simplifies the process of integrating these powerful capabilities into your development workflow.

## Features

- 🚀 Download MCP servers from GitHub releases
- 🎯 Interactive agent selection
- 📋 Interactive MCP server selection
- 🔧 Automatic configuration file generation
- 🌍 Cross-platform support (Windows, Linux, macOS)
- 📁 Automatic configuration path detection

## Installation

### Prerequisites

First, install uv (Python package manager):

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Using uv (recommended)

```bash
uv tool install mcp-cli --from git+https://github.com/rohitsoni007/mcp-kit
```

### To upgrade mcp-cli run:
```bash
uv tool install mcp-cli --force --from git+https://github.com/rohitsoni007/mcp-kit
```

### Using uvx (one-time execution)

```bash
uvx --from git+https://github.com/rohitsoni007/mcp-kit mcp-cli
```

### Development installation

```bash
git clone https://github.com/rohitsoni007/mcp-kit
cd mcp-kit
uv sync
```


## Supported AI Agents

| Agent | CLI ID | Support |
|-------|--------|---------|
| **[GitHub Copilot](https://code.visualstudio.com)** | `copilot` | ✅ |
| **[Continue](https://github.com/continuedev/continue)** | `continue` | ✅ |
| **[Kiro](https://kiro.dev)** | `kiro` | 🚧 Coming Soon |

### Usage Examples

```bash
# Interactive selection (choose from available agents)
mcp download

# Configure for GitHub Copilot
mcp download --agent copilot

# Configure for Continue
mcp download --agent continue

# Specify version and agent
mcp download --version v0.1.0 --agent copilot

# Short form
mcp download -v v0.2.0 -a copilot

```

### Initialize New Project With MCP's & Rules for MCP (🚧 Not Implemented yet)

```bash
mcp init <project_name>
```

## Development

### Project Structure

```
mcp-kit/
├── src/mcp_cli/           # Main CLI package
│   ├── __init__.py        # Core CLI functionality
├── templates/             # Configuration templates
├── scripts/               # Build and deployment scripts
└── tests/                 # Test files
```

## Requirements

- Python 3.11 or higher
- Internet connection for downloading MCP servers
- Supported AI coding agent (GitHub Copilot, Continue, etc.)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.