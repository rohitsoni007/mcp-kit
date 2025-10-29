# MCP Kit

A command-line interface tool for initializing Model Context Protocol (MCP) projects.

## Overview

MCP Kit provides an interactive way to bootstrap MCP projects by allowing users to select from available MCP servers and automatically generating the necessary configuration files. The tool integrates with the official MCP registry API to provide up-to-date server information and supports multiple platforms and installation methods.

## Installation

Install MCP Kit using uv:

```bash
uv tool install mcp-cli --from git+https://github.com/rohitsoni007/mcp-kit
```

## Usage

Initialize a new MCP project:

```bash
mcp init <project_name>
```

This will:
1. Create a new project directory
2. Fetch available MCP servers from the registry
3. Present an interactive selection interface
4. Generate the appropriate `mcp.json` configuration file

## Requirements

- Python 3.8 or higher
- Internet connection for fetching server information

## Development

To set up for development:

```bash
git clone https://github.com/rohitsoni007/mcp-kit
cd mcp-kit
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

## License

MIT License - see LICENSE file for details.