# Changelog

All notable changes to MCP Gearbox will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added support for `mcp list -a continue -j` for json output
- Added support for `mcp check -j` for json output
- Added support for `mcp rm git -a continue -j` for json output
- Added support for `mcp init --servers "git filesystem" -a copilot` to add MCP servers directly without interactive selection
- Added support for `mcp init -s git -s filesystem -a copilot` (multiple option format)
- Added support for `mcp init --servers "git filesystem" -a copilot --json` for JSON output without banner/UI


## [0.0.10] - 2025-11-02

### Added
- Added support for `mcp check` command to show list of installed agents on the user PC
- Added support for `mcp rm` command to remove mcp servers
- Added support for `mcp list` command to show configured mcp servers


## [0.0.9] - 2025-11-01

### Added
- LM Studio agent support for MCP server configuration
- Claude Code agent support for MCP server configuration
- Gemini CLI agent support for MCP server configuration
- Agents Alphabetically Ordered
- Cleaner MCP server configuration removing gallery & version for agents other than copilot

## [0.0.8] - 2025-10-31

### Added
- updated mutliple argument passing to **oraios/serena** or similar
- removed description for better ui for choose mcp server

## [0.0.7] - 2025-10-31

### Changed
- **BREAKING**: Removed separate `mcp download` command for global configuration
- Consolidated all MCP functionality into `mcp init` command
- Simplified command structure: `mcp init` (no arguments) now defaults to global configuration
- Updated CLI behavior: `mcp init` = global, `mcp init .` or `mcp init <project>` = project-specific

## [0.0.6] - 2025-10-31

### Added
- Enhanced MCP server selection interface with popularity metrics
- Added stargazer_count (GitHub stars) column with star icons (☆)
- Added "By" column showing organization/author information
- Enhanced search/filter functionality to include organization/author field
- Smart truncation for long organization names
- Servers now sorted by popularity (stargazer_count) by default

## [0.0.5] - 2025-10-30

### Added
- Kiro agent support for MCP server configuration
- Cursor agent support for MCP server configuration
- Qoder agent support for MCP server configuration
- Support for project-level MCP configurations
- Filter MCP Server by name and description


## [0.0.5] - 2025-10-29

### Added
- Enhance UI with improved banner 
- keyboard navigation for agent/server selection
- Continue agent support for MCP server configuration


## [0.0.4] - 2025-10-29

### Added
- GitHub Copilot agent support for MCP server configuration
- Interactive agent selection with GitHub Copilot integration
- Automatic configuration path detection for VS Code/GitHub Copilot
- Cross-platform support for GitHub Copilot MCP configuration (Windows, Linux, macOS)


### Fixed

N/A

### Changed

N/A
