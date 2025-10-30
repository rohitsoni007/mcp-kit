<div align="center">
    <img src="./media/logo1.png" alt="MCP Kit Logo"/>
    <h1>MCP Kit</h1>
    <h3><em>Setup high-quality MCP servers faster.</em></h3>
</div>
<p align="center">
    <strong>Python CLI dev-tools for Model Context Protocol (MCP) - quickly download, configure and deploy MCP servers for AI agents in minutes.</strong>
</p>
<p align="center">
    <a href="https://github.com/rohitsoni007/mcp-kit/actions/workflows/release.yml"><img src="https://github.com/rohitsoni007/mcp-kit/actions/workflows/release.yml/badge.svg" alt="Release"/></a>
    <a href="https://github.com/rohitsoni007/mcp-kit/stargazers"><img src="https://img.shields.io/github/stars/rohitsoni007/mcp-kit?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/rohitsoni007/mcp-kit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/github/spec-kit" alt="License"/></a>
    <a href="https://github.com/rohitsoni007/mcp-kit/"><img src="https://img.shields.io/badge/docs-GitHub_Pages-blue" alt="Documentation"/></a>
</p>

---

## Overview

MCP Kit is a powerful Python CLI dev-tools package that provides an interactive way to discover, download, and configure Model Context Protocol (MCP) servers from the official [Model Context Protocol Servers](https://github.com/modelcontextprotocol/servers) and [Github MCP Registry](https://github.com/mcp) ecosystem. This AI-powered tool automatically configures model-context-protocol servers for your preferred AI coding agent with cross-platform support and intelligent configuration management.

## Features

- 🚀 Download Model Context Protocol (MCP) servers from GitHub releases
- 🎯 Interactive AI agent selection and configuration
- 📋 Interactive MCP server selection with intelligent filtering
- 🔧 Automatic model-context-protocol configuration file generation
- 🌍 Cross-platform Python dev-tools support (Windows, Linux, macOS)
- 📁 Automatic AI agent configuration path detection
- 🛠️ CLI-based workflow for seamless developer experience

## Installation

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
# Interactive Model Context Protocol server selection (choose from available AI agents)
mcp download

# Configure MCP for GitHub Copilot AI agent
mcp download --agent copilot

# Configure model-context-protocol for Continue AI
mcp download --agent continue

# Specify MCP server version and AI agent
mcp download --version v0.1.0 --agent copilot

# Short form CLI command for quick setup
mcp download -v v0.2.0 -a copilot

```

### Initialize New Project With MCP's & Rules (🚧 Not Implemented yet)

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
- Internet connection for downloading Model Context Protocol (MCP) servers
- Supported AI coding agent (GitHub Copilot, Continue, etc.)
- Compatible with all major dev-tools and CLI environments

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Keywords

`MCP` `model-context-protocol` `ai` `cli` `dev-tools` `python` `artificial-intelligence` `developer-tools` `command-line` `automation` `ai-agents` `github-copilot` `continue` `configuration-management` `cross-platform`

## License

MIT License - see LICENSE file for details.