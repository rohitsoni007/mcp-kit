# Changelog

All notable changes to MCP Kit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.8] - 2025-10-31

### Added
- updated mutliple argument passing to **oraios/serena** or similar

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
