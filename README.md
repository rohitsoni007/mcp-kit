<div align="center">
    <img src="./media/logo1.png" alt="MCP Kit Logo"/>
    <h1>MCP Kit</h1>
    <h3><em>Setup high-quality MCP servers faster.</em></h3>
</div>
<p align="center">
    <strong>CLI tool to quickly download, configure and deploy MCP servers for AI agents in minutes.</strong>
</p>
<p align="center">
    <a href="https://github.com/rohitsoni007/mcp-kit/actions/workflows/release.yml"><img src="https://github.com/rohitsoni007/mcp-kit/actions/workflows/release.yml/badge.svg" alt="Release"/></a>
    <a href="https://github.com/rohitsoni007/mcp-kit/stargazers"><img src="https://img.shields.io/github/stars/rohitsoni007/mcp-kit?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/rohitsoni007/mcp-kit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/github/spec-kit" alt="License"/></a>
    <a href="https://github.com/rohitsoni007/mcp-kit/"><img src="https://img.shields.io/badge/docs-GitHub_Pages-blue" alt="Documentation"/></a>
</p>

---

## 🤔 Overview

MCP Kit is a powerful Python CLI dev-tools package that provides an interactive way to discover, download, and configure Model Context Protocol (MCP) servers from the official [Model Context Protocol Servers](https://github.com/modelcontextprotocol/servers) and [Github MCP Registry](https://github.com/mcp) ecosystem. This AI-powered tool automatically configures model-context-protocol servers for your preferred AI coding agent with cross-platform support and intelligent configuration management.

## Features

- 🎯 Interactive AI agent selection and configuration
- 📋 Interactive MCP server selection with intelligent filtering
- 🔧 Automatic model-context-protocol configuration file generation
- 🌍 Cross-platform Python dev-tools support (Windows, Linux, macOS)
- 📁 Automatic AI agent configuration path detection
- 🛠️ CLI-based workflow for seamless developer experience

## ⚡ Installation

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


## 🤖 Supported AI Agents

| Agent | Support | Notes |
|-------|---------|-------|
| **[GitHub Copilot](https://code.visualstudio.com)** | ✅ |  |
| **[Continue](https://github.com/continuedev/continue)** | ✅ |  |
| **[Kiro](https://kiro.dev)** | ✅ |  |
| **[Cursor](https://cursor.sh)** | ✅ |  |
| **[Claude Code](https://claude.ai)** | ✅ |  |
| **[Gemini CLI](https://github.com/google-gemini/gemini-cli)** | ✅ |  |
| **[Qoder](https://qoder.com)** | ⚠️ | Qoder [does not support](https://forum.qoder.com/t/project-specific-mcp-support/260) project-level MCP configuration |
| **[LM Studio](https://lmstudio.ai)** | ✅ | LM Studio does not need project-level MCP configuration |

## 🔧 MCP CLI Reference

The `mcp` command supports the following options:

### Commands

| Command     | Description                                                    |
|-------------|----------------------------------------------------------------|
| `init`      | Initialize MCP configuration (supports both project-specific and global configuration) |

### `mcp init` Arguments & Options

| Argument/Option | Type     | Description                                                                  |
|-----------------|----------|------------------------------------------------------------------------------|
| `<directory>`   | Argument | Directory to initialize MCP configuration (use `.` for current directory, omit for global configuration)   |
| `--agent`, `-a` | Option   | AI agent to configure: `copilot`, `continue`, `kiro`, `cursor`, `claude`, `gemini`, `qoder`, or `lmstudio`  |
| `--version`, `-v` | Option | Specific MCP server version to download (e.g., `v0.0.5`)                   |

### 🔧 Usage Examples

```bash
# Interactive Model Context Protocol server selection (choose from available AI agents)
# Configure MCP globally
mcp init

# Configure MCP globally for GitHub Copilot AI agent
mcp init -a copilot

# Configure MCP globally for Continue AI
mcp init -a continue

# Configure MCP globally for Kiro AI agent
mcp init -a kiro

# Configure MCP globally for Cursor AI agent
mcp init -a cursor

# Configure MCP globally for Qoder AI agent
mcp init -a qoder

# Configure MCP globally for Claude Code
mcp init -a claude

# Configure MCP globally for Gemini CLI
mcp init -a gemini

# Configure MCP globally for LM Studio AI agent
mcp init -a lmstudio

# Specify MCP server version and AI agent for global configuration
mcp init --version v0.0.5 --agent kiro

# Short form CLI command for quick global setup
mcp init -v v0.0.5 -a cursor

# Initialize MCP in current directory
mcp init .

# Initialize MCP in a new project directory
mcp init my-project

# Initialize MCP for GitHub Copilot AI agent in new project directory
mcp init my-project -a copilot

# Initialize MCP for Continue AI agent in new project directory
mcp init my-project -a continue

# Initialize MCP for Kiro AI agent in new project directory
mcp init my-project -a kiro

# Initialize MCP for Cursor AI agent in new project directory
mcp init my-project -a cursor

# Initialize MCP for Claude Code in new project directory
mcp init my-project -a claude

# Initialize MCP for Gemini CLI in new project directory
mcp init my-project -a gemini

# Initialize MCP for Qoder AI agent in new project directory
mcp init my-project -a qoder

# Initialize with specific agent and version
mcp init my-project --agent kiro --version v0.0.5

# Short form for project initialization
mcp init . -a cursor -v v0.0.5

```


## Development

### Project Structure

```
mcp-kit/
├── src/mcp_cli/           # Main CLI package
│   ├── __init__.py        # Core CLI functionality
├── templates/             # Configuration templates
└── scripts/               # Build and deployment scripts
```

## 🔧 Requirements

- **Linux/macOS/Windows**
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
  
 If you encounter issues with an agent, please open an issue so we can refine the integration.

## 👥 Maintainers

- Rohit Soni ([@rohitsoni007](https://github.com/rohitsoni007))

## 💬 Support

For support, please open a [GitHub issue](https://github.com/rohitsoni007/mcp-kit/issues/new). We welcome bug reports, feature requests, and questions about using MCP CLI.

## 🙏 Acknowledgements

This project is based on the data from [Model Context Protocol Servers](https://github.com/modelcontextprotocol/servers) and [Github MCP Registry](https://github.com/mcp).

## Keywords

`MCP` `model-context-protocol` `ai` `cli` `dev-tools` `python` `artificial-intelligence` `developer-tools` `command-line` `automation` `ai-agents` `github-copilot` `continue` `configuration-management` `cross-platform`

## 📄 License

This project is licensed under the terms of the MIT open source license. Please refer to the [LICENSE](./LICENSE) file for the full terms.
