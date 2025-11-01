<div align="center">
    <img src="./media/logo.png" alt="MCP Gearbox Logo"/>
    <h1>MCP Gearbox</h1>
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

MCP Gearbox is a powerful Python CLI dev-tools package that provides an interactive way to discover, download, and configure Model Context Protocol (MCP) servers from the official ecosystem. This AI-powered tool automatically configures model-context-protocol servers for your preferred AI coding agent with cross-platform support and intelligent configuration management.


## ⚡ Installation

### Using uv (recommended)

```bash
uv tool install mcp-gearbox --from git+https://github.com/rohitsoni007/mcp-kit
```

### To upgrade mcp-cli run:
```bash
uv tool install mcp-gearbox --force --from git+https://github.com/rohitsoni007/mcp-kit
```

### Using uvx (one-time execution)

```bash
uvx --from git+https://github.com/rohitsoni007/mcp-kit mcp-cli
```

### Using uv & pip

```bash
uv tool install mcp-gearbox
```

### Using npm

```bash
npm install -g mcp-gearbox
```

### Using pip

```bash
pip install mcp-gearbox
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
| **[Claude Code](https://www.claude.com/product/claude-code)** | ✅ |  |
| **[Gemini CLI](https://github.com/google-gemini/gemini-cli)** | ✅ |  |
| **[Qoder](https://qoder.com)** | ⚠️ | Qoder [does not support](https://forum.qoder.com/t/project-specific-mcp-support/260) project-level MCP configuration |
| **[LM Studio](https://lmstudio.ai)** | ✅ | LM Studio does not need project-level MCP configuration |

## 🔧 MCP CLI Reference

The `mcp` command supports the following options:

### Commands

| Command     | Description                                                    |
|-------------|----------------------------------------------------------------|
| `init`      | Initialize MCP configuration (supports both project-specific and global configuration) |
| `list`      | List configured MCP servers                                   |
| `rm`        | Remove MCP servers from configuration                         |

### `mcp init` Arguments & Options

| Argument/Option | Type     | Description                                                                  |
|-----------------|----------|------------------------------------------------------------------------------|
| `<directory>`   | Argument | Directory to initialize MCP configuration (use `.` for current directory, omit for global configuration)   |
| `--agent`, `-a` | Option   | AI agent to configure: `copilot`, `continue`, `kiro`, `cursor`, `claude`, `gemini`, `qoder`, or `lmstudio`  |

### `mcp list` Arguments & Options

| Argument/Option | Type     | Description                                                                  |
|-----------------|----------|------------------------------------------------------------------------------|
| `--agent`, `-a` | Option   | AI agent to list servers for: `copilot`, `continue`, `kiro`, `cursor`, `claude`, `gemini`, `qoder`, or `lmstudio`  |
| `--project`, `-p` | Option | Project path (use '.' for current directory, omit for global configuration) |

### `mcp rm` Arguments & Options

| Argument/Option | Type     | Description                                                                  |
|-----------------|----------|------------------------------------------------------------------------------|
| `<servers>`     | Argument | MCP server names to remove (e.g., 'git', 'filesystem') - optional          |
| `--all`, `-A`   | Option   | Remove all MCP servers                                                       |
| `--agent`, `-a` | Option   | AI agent to configure: `copilot`, `continue`, `kiro`, `cursor`, `claude`, `gemini`, `qoder`, or `lmstudio`  |
| `--project`, `-p` | Option | Project path (use '.' for current directory, omit for global configuration) |
| `--force`, `-f` | Option   | Skip confirmation prompts                                                    |

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
```

#### `mcp list` Examples

```bash
# Interactive MCP server listing (choose from available AI agents)
# List servers from global configuration
mcp list

# List servers for specific agent from global configuration
mcp list -a copilot
mcp list -a continue
mcp list -a kiro
mcp list -a cursor
mcp list -a claude
mcp list -a gemini
mcp list -a qoder
mcp list -a lmstudio

# List servers from current directory configuration
mcp list -p .

# List servers from specific project directory
mcp list -p my-project

# List servers for specific agent from project
mcp list -a copilot -p my-project
```

#### `mcp rm` Examples

```bash
# Interactive MCP server removal (choose from configured servers)
# Remove servers from global configuration
mcp rm

# Interactive removal for specific agent
mcp rm -a copilot

# Remove specific MCP servers from global configuration
mcp rm git filesystem

# Remove specific servers for GitHub Copilot AI agent
mcp rm git filesystem -a copilot

# Remove specific servers for Continue AI
mcp rm git filesystem -a continue

# Remove specific servers for Kiro AI agent
mcp rm git filesystem -a kiro

# Remove specific servers for Cursor AI agent
mcp rm git filesystem -a cursor

# Remove specific servers for Claude Code
mcp rm git filesystem -a claude

# Remove specific servers for Gemini CLI
mcp rm git filesystem -a gemini

# Remove all MCP servers from global configuration
mcp rm --all

# Remove all servers for specific agent
mcp rm --all -a copilot

# Interactive removal from current directory configuration
mcp rm -p .

# Interactive removal from specific project directory
mcp rm -p my-project

# Remove specific servers from current directory configuration
mcp rm git filesystem -p .

# Remove specific servers from specific project directory
mcp rm git filesystem -p my-project

# Remove all servers from project directory
mcp rm --all -p my-project

# Remove servers with force (skip confirmations)
mcp rm git filesystem --force

# Remove all servers with force
mcp rm --all --force
```

#### General Examples

```bash
# Show version
mcp --version
mcp -v
```
## 📚 Features

- 🎯 Interactive AI agent selection and configuration
- 📋 Interactive MCP server selection with intelligent filtering
- 🔧 Automatic model-context-protocol configuration file generation
- 🌍 Cross-platform Python dev-tools support (Windows, Linux, macOS)
- 📁 Automatic AI agent configuration path detection
- 🛠️ CLI-based workflow for seamless developer experience

## 🎯 Experimental Goals

- **Common MCP server for all AI agents** - Unified configuration and management across different AI platforms
- **Future edit feature** - Planned functionality to modify and update existing MCP configurations

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
