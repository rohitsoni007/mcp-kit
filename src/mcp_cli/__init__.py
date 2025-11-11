# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "rich",
#     "platformdirs",
#     "readchar",
#     "httpx",
# ]
# ///
"""MCP Kit - A command-line tool for initializing MCP in agents.
Usage:
    uv venv
    ./.venv/Scripts/Activate.ps1
    ./.venv-new/Scripts/Activate.ps1
"""

__version__ = "0.0.12"

import os
import subprocess
import sys
import zipfile
import tempfile
import shutil
import shlex
import json
import platform
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import typer
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.live import Live
from rich.align import Align
from rich.table import Table
from rich.tree import Tree
from rich.prompt import Prompt, Confirm
from typer.core import TyperGroup

# For cross-platform keyboard input
import readchar
import ssl
import truststore

ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
client = httpx.Client(verify=ssl_context)
console = Console()

def _github_token(cli_token: str | None = None) -> str | None:
    """Return sanitized GitHub token (cli arg takes precedence) or None."""
    return ((cli_token or os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or "").strip()) or None

def _github_auth_headers(cli_token: str | None = None) -> dict:
    """Return Authorization header dict only when a non-empty token exists."""
    token = _github_token(cli_token)
    return {"Authorization": f"Bearer {token}"} if token else {}

# Agent configuration with name, folder, install URL, and CLI tool requirement
AGENT_CONFIG = {
    "claude": {
        "name": "Claude Code",
        "folder": ".claude/",
        "install_url": "https://www.claude.com/product/claude-code",
        "requires_cli": False,
    },
    "continue": {
        "name": "Continue",
        "folder": ".continue/",
        "install_url": None,  # IDE-based, no CLI check needed
        "requires_cli": False,
    },
    "copilot": {
        "name": "GitHub Copilot",
        "folder": ".vscode/",
        "install_url": None,  # IDE-based, no CLI check needed
        "requires_cli": False,
    },
    "copilot-cli": {
        "name": "Copilot CLI",
        "folder": ".copilot/",
        "install_url": "https://github.com/github/copilot-cli",
        "requires_cli": True,
    },
    "cursor": {
        "name": "Cursor",
        "folder": ".cursor/",
        "install_url": "https://cursor.sh",
        "requires_cli": False,
    },
    "gemini": {
        "name": "Gemini CLI",
        "folder": ".gemini/",
        "install_url": "https://github.com/google-gemini/gemini-cli",
        "requires_cli": True,
    },
    "kiro": {
        "name": "Kiro",
        "folder": ".kiro/",
        "install_url": "https://kiro.dev",
        "requires_cli": False,
    },
    "lmstudio": {
        "name": "LM Studio",
        "folder": ".lmstudio/",
        "install_url": "https://lmstudio.ai",
        "requires_cli": False,
    },
    "qoder": {
        "name": "Qoder",
        "folder": ".qoder/",
        "install_url": "https://qoder.com",
        "requires_cli": False,
    }
}

BANNER = r"""
███╗   ███╗ ██████╗██████╗      ██████╗██╗     ██╗
████╗ ████║██╔════╝██╔══██╗    ██╔════╝██║     ██║
██╔████╔██║██║     ██████╔╝    ██║     ██║     ██║
██║╚██╔╝██║██║     ██╔═══╝     ██║     ██║     ██║
██║ ╚═╝ ██║╚██████╗██║         ╚██████╗███████╗██║
╚═╝     ╚═╝ ╚═════╝╚═╝          ╚═════╝╚══════╝╚═╝
"""

TAGLINE = "Setup high-quality MCP servers faster"


    
class BannerGroup(TyperGroup):
    """Custom group that shows banner before help."""

    def format_help(self, ctx, formatter):
        # Show banner before help
        show_banner()
        super().format_help(ctx, formatter)

def version_callback(value: bool):
    """Handle version flag."""
    if value:
        console.print(__version__)
        raise typer.Exit()

app = typer.Typer(
    name="MCP-Gearbox",
    help="Setup tool for MCP for agents",
    add_completion=False,
    invoke_without_command=True,
    cls=BannerGroup,
)

def show_banner():
    """Display the ASCII art banner."""
    banner_lines = BANNER.strip().split('\n')
    colors = ["dark_cyan", "cyan", "bright_cyan", "blue", "bright_blue", "light_blue"]

    styled_banner = Text()
    for i, line in enumerate(banner_lines):
        color = colors[i % len(colors)]
        styled_banner.append(line + "\n", style=color)

    console.print(Align.center(styled_banner))
    console.print(Align.center(Text(TAGLINE, style="italic bright_yellow")))
    console.print()

def get_mcp_config_path(agent: str = "copilot", project_path: Optional[Path] = None) -> Path:
    """Get the MCP configuration path based on the agent and operating system.
    
    Args:
        agent: The agent to configure (copilot, copilot-cli, continue, kiro, cursor, qoder, lmstudio, claude, gemini)
        project_path: If provided, returns project-specific path instead of global path
    """
    if project_path:
        # Project-specific paths
        if agent == "copilot":
            # VS Code project: .vscode/mcp.json
            return project_path / ".vscode" / "mcp.json"
        elif agent == "continue":
            # Continue project: .continue/mcpServers/mcp.json
            return project_path / ".continue" / "mcpServers" / "mcp.json"
        elif agent == "kiro":
            # Kiro project: .kiro/settings/mcp.json
            return project_path / ".kiro" / "settings" / "mcp.json"
        elif agent == "cursor":
            # Cursor project: .cursor/mcp.json
            return project_path / ".cursor" / "mcp.json"
        elif agent == "claude":
            # Claude project: .mcp.json (for Claude Agent) or .claude/mcp.json (for Claude Code)
            return project_path / ".mcp.json"
        elif agent == "gemini":
            # Gemini project: .gemini/settings.json
            return project_path / ".gemini" / "settings.json"
        elif agent == "qoder":
            # Qoder does not support project-level configuration, use global path
            return get_mcp_config_path(agent)
        elif agent == "lmstudio":
            # LM Studio does not support project-level configuration, use global path
            return get_mcp_config_path(agent)
        elif agent == "copilot-cli":
            # Copilot CLI does not support project-level configuration, use global path
            return get_mcp_config_path(agent)
    
    # Global/user-level paths (existing functionality)
    if agent == "continue": 
        # Continue uses ~/.continue/mcpServers/mcp.json
        return Path.home() / ".continue" / "mcpServers" / "mcp.json"
    elif agent == "kiro":
        # Kiro uses ~/.kiro/settings/mcp.json
        return Path.home() / ".kiro" / "settings" / "mcp.json"
    elif agent == "cursor":
        # Cursor uses ~/.cursor/mcp.json
        return Path.home() / ".cursor" / "mcp.json"
    elif agent == "claude":
        # Claude uses ~/.claude.json (for Claude Agent) or ~/.claude/mcp.json (for Claude Code)
        return Path.home() / ".claude.json"
    elif agent == "gemini":
        # Gemini uses ~/.gemini/settings.json
        return Path.home() / ".gemini" / "settings.json"
    elif agent == "qoder":
        # Qoder uses ~/AppData/Roaming/Qoder/SharedClientCache/mcp.json on Windows
        system = platform.system().lower()
        if system == "windows":
            return Path.home() / "AppData" / "Roaming" / "Qoder" / "SharedClientCache" / "mcp.json"
        else:
            # For non-Windows systems, use a similar pattern in user config
            return Path.home() / ".config" / "Qoder" / "SharedClientCache" / "mcp.json"
    elif agent == "lmstudio":
        # LM Studio uses ~/.lmstudio/mcp.json
        return Path.home() / ".lmstudio" / "mcp.json"
    elif agent == "copilot-cli":
        # Copilot CLI uses ~/.copilot/mcp-config.json
        return Path.home() / ".copilot" / "mcp-config.json"
    
    # Default to Copilot configuration path
    system = platform.system().lower()
    
    if system == "windows":
        # Windows: ~/AppData/Roaming/Code/User/mcp.json
        return Path.home() / "AppData" / "Roaming" / "Code" / "User" / "mcp.json"
    elif system == "linux":
        # Linux: ~/.config/Code/User/mcp.json
        return Path.home() / ".config" / "Code" / "User" / "mcp.json"
    elif system == "darwin":
        # macOS: ~/Library/Application Support/Code/User/mcp.json
        return Path.home() / "Library" / "Application Support" / "Code" / "User" / "mcp.json"
    else:
        # Fallback to Linux path
        return Path.home() / ".config" / "Code" / "User" / "mcp.json"

def load_local_mcp_servers() -> Optional[List[Dict[str, Any]]]:
    """Load MCP servers from local template file as fallback."""
    local_files = [
        Path("templates/mcp-servers-sample.json"),
        Path("templates/base_mcp.json"),
        Path("mcp-servers-sample.json"),  # In case it's in root
    ]
    
    for local_file in local_files:
        if local_file.exists():
            try:
                with open(local_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load {local_file}: {e}[/yellow]")
                continue
    
    # If no local files found, return a minimal default configuration
    return [
        {
            "name": "Fetch",
            "description": "A Model Context Protocol server providing tools to fetch and convert web content for usage by LLMs",
            "mcp": {
                "modelcontextprotocol/fetch": {
                    "type": "stdio",
                    "command": "uvx",
                    "args": ["mcp-server-fetch"],
                    "gallery": "https://github.com/modelcontextprotocol/servers/tree/main/src/fetch",
                    "version": "0.6.3"
                }
            }
        },
        {
            "name": "Filesystem", 
            "description": "MCP server for filesystem access with read/write capabilities",
            "mcp": {
                "modelcontextprotocol/filesystem": {
                    "type": "stdio",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                    "gallery": "https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem",
                    "version": "0.6.3"
                }
            }
        },
        {
            "name": "Git",
            "description": "A Model Context Protocol server providing tools to read, search, and manipulate Git repositories",
            "mcp": {
                "modelcontextprotocol/git": {
                    "type": "stdio",
                    "command": "uvx",
                    "args": ["mcp-server-git"],
                    "gallery": "https://github.com/modelcontextprotocol/servers/tree/main/src/git",
                    "version": "0.6.2"
                }
            }
        },
        {
            "name": "Markitdown",
            "description": "Convert various file formats (PDF, Word, Excel, images, audio) to Markdown",
            "mcp": {
                "microsoft/markitdown": {
                    "type": "stdio",
                    "command": "uvx",
                    "args": ["markitdown-mcp==0.0.1a4"],
                    "gallery": "https://api.mcp.github.com/2025-09-15/v0/servers/976a2f68-e16c-4e2b-9709-7133487f8c14",
                    "version": "1.0.0"
                }
            }
        }
    ]

def download_mcp_servers(version: str = None) -> Optional[List[Dict[str, Any]]]:
    """Download MCP servers from GitHub release with fallback to local files."""
    if version is None:
        version = f"v{__version__}"
    url = f"https://github.com/rohitsoni007/mcp-kit/releases/download/{version}/mcp-servers-{version}.zip"
    
    try:
        with console.status(f"[bold green]Downloading MCP servers {version}..."):
            # Create client with redirect following
            client_with_redirects = httpx.Client(
                verify=ssl_context,
                follow_redirects=True,
                timeout=30.0
            )
            
            response = client_with_redirects.get(url)
            response.raise_for_status()
            
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = Path(temp_dir) / f"mcp-servers-{version}.zip"
                
                # Save zip file
                with open(zip_path, "wb") as f:
                    f.write(response.content)
                
                # Extract zip file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Look for JSON files in extracted content
                json_files = list(Path(temp_dir).rglob("*.json"))
                if not json_files:
                    console.print("[yellow]No JSON configuration files found in the downloaded package.[/yellow]")
                    console.print("[yellow]Falling back to local configuration...[/yellow]")
                    return load_local_mcp_servers()
                
                # Read the first JSON file (assuming it contains MCP server configs)
                config_file = json_files[0]
                with open(config_file, 'r') as f:
                    return json.load(f)
                    
    except httpx.HTTPStatusError as e:
        console.print(f"[yellow]Failed to download MCP servers: HTTP {e.response.status_code}[/yellow]")
        console.print("[yellow]This is expected if the release doesn't exist yet.[/yellow]")
        console.print("[yellow]Falling back to local configuration...[/yellow]")
        return load_local_mcp_servers()
    except Exception as e:
        console.print(f"[yellow]Error downloading MCP servers: {str(e)}[/yellow]")
        console.print("[yellow]Falling back to local configuration...[/yellow]")
        return load_local_mcp_servers()

def select_agent(project_info: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Interactive agent selection with keyboard navigation using table format."""
    agents = list(AGENT_CONFIG.keys())
    selected_index = 0
    
    def render_agent_table():
        """Render the agent selection interface using a table."""
        try:
            console.clear()
        except Exception:
            # Fallback if clear doesn't work
            console.print("\n" * 50)
        
        # Show banner
        show_banner()
        
        # Show project info if provided
        if project_info:
            setup_table = Table(show_header=False, box=None, padding=(0, 1))
            setup_table.add_column("Label", style="cyan", width=18)
            setup_table.add_column("Path", style="white")
            
            setup_table.add_row("Project:", project_info["project_name"])
            setup_table.add_row("Working Path:", project_info["working_directory"])
            setup_table.add_row("Target Path:", project_info["target_directory"])
            
            setup_panel = Panel(
                setup_table,
                title="[bold cyan]Project Setup[/bold cyan]",
                border_style="cyan",
                padding=(1, 2)
            )
            
            console.print(setup_panel)
            console.print()
        
        # Create table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Selector", style="cyan", width=3)
        table.add_column("Agent", style="white", min_width=20)
        table.add_column("Description", style="dim")
        
        # Add rows to table
        for i, agent_key in enumerate(agents):
            agent = AGENT_CONFIG[agent_key]
            
            if i == selected_index:
                # Highlighted selection
                selector = "▶"
                agent_style = "bold cyan"
                desc_style = "cyan"
            else:
                # Normal item
                selector = " "
                agent_style = "cyan"
                desc_style = "dim"
            
            table.add_row(
                Text(selector, style="cyan"),
                Text(agent_key, style=agent_style),
                Text(f"({agent['name']})", style=desc_style)
            )
        
        # Wrap table in a panel with border
        panel = Panel(
            table,
            title="[bold cyan]Choose your AI assistant:[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        )
        
        console.print(panel)
        console.print()
        console.print(Text("Use ↑/↓ to navigate, Enter to select, Esc to cancel", style="dim"))
    
    # Initial render
    render_agent_table()
    
    while True:
        try:
            # Read a single character
            key = readchar.readkey()
            
            if key == readchar.key.UP:
                selected_index = (selected_index - 1) % len(agents)
                render_agent_table()
            elif key == readchar.key.DOWN:
                selected_index = (selected_index + 1) % len(agents)
                render_agent_table()
            elif key == readchar.key.ENTER or key == '\r' or key == '\n':
                return agents[selected_index]
            elif key == readchar.key.ESC or key == '\x1b':
                return None
            elif key.lower() == 'q':
                return None
                
        except KeyboardInterrupt:
            return None
        except Exception:
            # Handle any readchar exceptions gracefully
            continue

def select_servers_to_remove(configured_servers: List[str], available_servers: List[Dict[str, Any]], agent: str, project_info: Optional[Dict[str, str]] = None) -> Optional[List[str]]:
    """Interactive server selection for removal with keyboard navigation, table format, and pagination."""
    
    # Match configured servers with available server data
    matched_servers = []
    for configured_name in configured_servers:
        # Find matching server in available_servers list
        matched_server = None
        for server in available_servers:
            server_mcp = server.get("mcp", {})
            # Check if any key in the mcp dict matches the configured server name
            for mcp_key in server_mcp.keys():
                # For copilot-cli, convert hyphenated names back to slash format for matching
                if agent == "copilot-cli":
                    # Convert configured_name from hyphenated to slash format
                    if '-' in configured_name and '/' not in configured_name:
                        slash_name = configured_name.replace('-', '/')
                        if mcp_key == slash_name or mcp_key.endswith('/' + slash_name.split('/')[-1]):
                            matched_server = {
                                'name': server['name'],
                                'by': server.get('by', 'Unknown'),
                                'stargazer_count': server.get('stargazer_count', 0),
                                'configured_name': configured_name,
                                'mcp_key': mcp_key
                            }
                            break
                else:
                    # For other agents, use existing matching logic
                    if mcp_key == configured_name or mcp_key.endswith('/' + configured_name.split('/')[-1]):
                        matched_server = {
                            'name': server['name'],
                            'by': server.get('by', 'Unknown'),
                            'stargazer_count': server.get('stargazer_count', 0),
                            'configured_name': configured_name,
                            'mcp_key': mcp_key
                        }
                        break
            if matched_server:
                break
        
        # If no match found, create a basic entry with better defaults
        if not matched_server:
            # For copilot-cli, server names use hyphens instead of slashes
            if agent == "copilot-cli":
                name_parts = configured_name.split('-')
            else:
                name_parts = configured_name.split('/')
            
            if len(name_parts) > 1:
                # Format: org-name or org/name - use org as 'by' field and name as server name
                by_org = name_parts[0]
                server_name = name_parts[-1].title()
            else:
                # Format: name - use the name as server name and 'Unknown' as org
                by_org = 'Unknown'
                server_name = configured_name.title()
            
            matched_server = {
                'name': server_name,
                'by': by_org,
                'stargazer_count': 0,
                'configured_name': configured_name,
                'mcp_key': configured_name
            }
        
        matched_servers.append(matched_server)
    
    selected_indices = set()
    current_index = 0
    current_page = 0
    items_per_page = 10  # Show 10 servers per page
    search_query = ""
    filtered_servers = matched_servers.copy()
    original_to_filtered_mapping = {i: i for i in range(len(matched_servers))}  # Maps original indices to filtered indices
    
    def filter_servers():
        """Filter servers based on search query."""
        nonlocal filtered_servers, original_to_filtered_mapping, current_index, current_page
        
        if not search_query.strip():
            filtered_servers = matched_servers.copy()
            original_to_filtered_mapping = {i: i for i in range(len(matched_servers))}
        else:
            query_lower = search_query.lower()
            filtered_servers = []
            original_to_filtered_mapping = {}
            
            for i, server in enumerate(matched_servers):
                # Search in name and by (organization/author)
                name_match = query_lower in server['name'].lower()
                by_match = query_lower in server.get('by', '').lower()
                
                if name_match or by_match:
                    filtered_index = len(filtered_servers)
                    original_to_filtered_mapping[i] = filtered_index
                    filtered_servers.append(server)
        
        # Reset pagination and selection after filtering
        current_index = 0
        current_page = 0
    
    def get_page_items():
        """Get items for the current page."""
        start_idx = current_page * items_per_page
        end_idx = min(start_idx + items_per_page, len(filtered_servers))
        return filtered_servers[start_idx:end_idx], start_idx, end_idx
    
    def get_total_pages():
        """Calculate total number of pages."""
        return (len(filtered_servers) + items_per_page - 1) // items_per_page
    
    def get_original_index(filtered_index):
        """Get the original server index from filtered index."""
        for orig_idx, filt_idx in original_to_filtered_mapping.items():
            if filt_idx == filtered_index:
                return orig_idx
        return filtered_index
    
    def render_server_table():
        """Render the MCP server removal interface using a table with pagination."""
        try:
            console.clear()
        except Exception:
            # Fallback if clear doesn't work
            console.print("\n" * 50)
        
        # Show banner
        show_banner()
        
        # Show project info if provided
        if project_info:
            setup_table = Table(show_header=False, box=None, padding=(0, 1))
            setup_table.add_column("Label", style="cyan", width=18)
            setup_table.add_column("Path", style="white")
            
            setup_table.add_row("Project:", project_info["project_name"])
            setup_table.add_row("Working Path:", project_info["working_directory"])
            setup_table.add_row("Target Path:", project_info["target_directory"])
            
            setup_panel = Panel(
                setup_table,
                title="[bold cyan]Project Setup[/bold cyan]",
                border_style="cyan",
                padding=(1, 2)
            )
            
            console.print(setup_panel)
            console.print()
        
        # Show selected agent with border
        agent_content = f"🤖 {agent} ({AGENT_CONFIG[agent]['name']})"
        agent_panel = Panel(
            Align.center(Text(agent_content, style="bold green")),
            title="[bold cyan]Selected Agent[/bold cyan]",
            border_style="green",
            padding=(0, 1),
            height=3
        )
        console.print(agent_panel)
        console.print()
        
        # Show search box with border
        if search_query:
            search_content = f"🔍 {search_query}"
            search_style = "bold yellow"
            border_style = "yellow"
        else:
            search_content = "🔍 (type to filter servers)"
            search_style = "dim"
            border_style = "dim"
        
        search_panel = Panel(
            Align.center(Text(search_content, style=search_style)),
            title="[bold cyan]Search[/bold cyan]" if search_query else "[dim]Search[/dim]",
            border_style=border_style,
            padding=(0, 1),
            height=3
        )
        console.print(search_panel)
        console.print()
        
        # Get current page items
        page_items, start_idx, end_idx = get_page_items()
        total_pages = get_total_pages()
        
        # Create table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Selector", style="cyan", width=3)
        table.add_column("Checkbox", style="white", width=3)
        table.add_column("Server", style="white", min_width=20)
        table.add_column("By", style="dim", width=28)
        table.add_column("Stars", style="dim", width=10)
        
        # Add rows to table for current page
        for i, server in enumerate(page_items):
            filtered_index = start_idx + i
            original_index = get_original_index(filtered_index)
            
            if filtered_index == current_index:
                # Highlighted selection
                selector = "▶"
                checkbox_style = "bold cyan"
                server_style = "bold cyan"
                desc_style = "cyan"
            else:
                # Normal item
                selector = " "
                if original_index in selected_indices:
                    checkbox_style = "bright_red"
                    server_style = "bright_red"
                    desc_style = "red"
                else:
                    checkbox_style = "white"
                    server_style = "white"
                    desc_style = "dim"
            
            checkbox = "☑" if original_index in selected_indices else "☐"
            
            # Get by (author/organization) field with "By " prefix
            by_org = server.get('by', 'Unknown')
            # Truncate long organization names to fit in column
            if len(by_org) > 20:
                by_org = by_org[:20] + "..."
            by_text = f"By: {by_org}"
            
            # Get stargazer_count and format it with unfilled star icon
            stars = server.get('stargazer_count', 0)
            if stars >= 1000:
                stars_text = f"☆ {stars/1000:.1f}k"
            else:
                stars_text = f"☆ {stars}"
            
            table.add_row(
                Text(selector, style="cyan"),
                Text(checkbox, style=checkbox_style),
                Text(server['name'], style=server_style),
                Text(by_text, style=desc_style),
                Text(stars_text, style=desc_style)
            )
        
        # Create status info for the panel subtitle
        selected_count = len(selected_indices)
        status_info = f"Selected: {selected_count} server{'s' if selected_count != 1 else ''} for removal"
        
        if total_pages > 1:
            status_info += f" | Page {current_page + 1} of {total_pages} | Showing {start_idx + 1}-{end_idx} of {len(filtered_servers)}"
        
        if search_query and len(filtered_servers) != len(matched_servers):
            status_info += f" | Filtered: {len(filtered_servers)}/{len(matched_servers)}"
        
        # Wrap table in a panel with border
        panel = Panel(
            table,
            title="[bold red]Choose MCP servers to remove:[/bold red]",
            subtitle=f"[bold yellow]{status_info}[/bold yellow]",
            border_style="red",
            padding=(1, 2)
        )
        
        console.print(panel)
        console.print()
        
        # Help text
        help_lines = [
            "Use ↑/↓ to navigate, Space to toggle, Enter to confirm, Esc to cancel",
            "Type to search/filter servers, Backspace to delete search, Delete to clear search"
        ]
        
        if total_pages > 1:
            help_lines.append("Use ←/→ or PgUp/PgDn to change pages")
        
        help_lines.append("Ctrl+A=select all, Ctrl+N=select none")
        
        for line in help_lines:
            console.print(Text(line, style="dim"))
    
    # Initial render
    render_server_table()
    
    while True:
        try:
            # Read a single character
            key = readchar.readkey()
            
            if key == readchar.key.UP:
                if current_index > 0:
                    current_index -= 1
                    # Check if we need to go to previous page
                    if current_index < current_page * items_per_page and current_page > 0:
                        current_page -= 1
                else:
                    # Wrap to last item
                    current_index = len(filtered_servers) - 1
                    current_page = get_total_pages() - 1
                render_server_table()
                
            elif key == readchar.key.DOWN:
                if current_index < len(filtered_servers) - 1:
                    current_index += 1
                    # Check if we need to go to next page
                    if current_index >= (current_page + 1) * items_per_page:
                        current_page += 1
                else:
                    # Wrap to first item
                    current_index = 0
                    current_page = 0
                render_server_table()
                
            elif key == readchar.key.LEFT or key == readchar.key.PAGE_UP:
                if current_page > 0:
                    current_page -= 1
                    current_index = current_page * items_per_page
                    render_server_table()
                    
            elif key == readchar.key.RIGHT or key == readchar.key.PAGE_DOWN:
                if current_page < get_total_pages() - 1:
                    current_page += 1
                    current_index = current_page * items_per_page
                    render_server_table()
                    
            elif key == ' ':  # Space to toggle selection
                original_index = get_original_index(current_index)
                if original_index in selected_indices:
                    selected_indices.remove(original_index)
                else:
                    selected_indices.add(original_index)
                render_server_table()
                
            elif key == readchar.key.ENTER or key == '\r' or key == '\n':
                if selected_indices:
                    return [matched_servers[i]['configured_name'] for i in sorted(selected_indices)]
                else:
                    # If nothing selected, select the current one
                    original_index = get_original_index(current_index)
                    return [matched_servers[original_index]['configured_name']]
                    
            elif key == readchar.key.ESC or key == '\x1b':
                return None
                
            elif key.lower() == 'q':
                return []
                
            elif key == '\x01':  # Ctrl+A to select all (filtered servers)
                for filtered_idx in range(len(filtered_servers)):
                    original_idx = get_original_index(filtered_idx)
                    selected_indices.add(original_idx)
                render_server_table()
                
            elif key == '\x0e':  # Ctrl+N to select none
                selected_indices.clear()
                render_server_table()
                
            elif key == readchar.key.BACKSPACE or key == '\b' or key == '\x7f':  # Backspace
                if search_query:
                    search_query = search_query[:-1]
                    filter_servers()
                    render_server_table()
                    
            elif key == readchar.key.DELETE or key == readchar.key.SUPR:  # Delete key to clear search
                if search_query:
                    search_query = ""
                    filter_servers()
                    render_server_table()
                    
            elif key == '\x03':  # Ctrl+C to exit
                return None  # Return None to indicate cancellation
                    
            elif len(key) == 1 and key.isprintable():  # Regular character input for search
                search_query += key
                filter_servers()
                render_server_table()
                
        except KeyboardInterrupt:
            return None
        except Exception:
            # Handle any readchar exceptions gracefully
            continue

def select_mcp_servers(servers: List[Dict[str, Any]], agent: str, project_info: Optional[Dict[str, str]] = None) -> Optional[List[Dict[str, Any]]]:
    """Interactive MCP server selection with keyboard navigation, table format, pagination, and search filtering."""
    selected_indices = set()
    current_index = 0
    current_page = 0
    items_per_page = 10  # Show 10 servers per page
    search_query = ""
    filtered_servers = servers.copy()
    original_to_filtered_mapping = {i: i for i in range(len(servers))}  # Maps original indices to filtered indices
    
    def filter_servers():
        """Filter servers based on search query."""
        nonlocal filtered_servers, original_to_filtered_mapping, current_index, current_page
        
        if not search_query.strip():
            filtered_servers = servers.copy()
            original_to_filtered_mapping = {i: i for i in range(len(servers))}
        else:
            query_lower = search_query.lower()
            filtered_servers = []
            original_to_filtered_mapping = {}
            
            for i, server in enumerate(servers):
                # Search in name and by (organization/author)
                name_match = query_lower in server['name'].lower()
                by_match = query_lower in server.get('by', '').lower()
                
                if name_match or by_match:
                    filtered_index = len(filtered_servers)
                    original_to_filtered_mapping[i] = filtered_index
                    filtered_servers.append(server)
        
        # Reset pagination and selection after filtering
        current_index = 0
        current_page = 0
    
    def get_page_items():
        """Get items for the current page."""
        start_idx = current_page * items_per_page
        end_idx = min(start_idx + items_per_page, len(filtered_servers))
        return filtered_servers[start_idx:end_idx], start_idx, end_idx
    
    def get_total_pages():
        """Calculate total number of pages."""
        return (len(filtered_servers) + items_per_page - 1) // items_per_page
    
    def get_original_index(filtered_index):
        """Get the original server index from filtered index."""
        for orig_idx, filt_idx in original_to_filtered_mapping.items():
            if filt_idx == filtered_index:
                return orig_idx
        return filtered_index
    
    def render_server_table():
        """Render the MCP server selection interface using a table with pagination."""
        try:
            console.clear()
        except Exception:
            # Fallback if clear doesn't work
            console.print("\n" * 50)
        
        # Show banner
        show_banner()
        
        # Show project info if provided
        if project_info:
            setup_table = Table(show_header=False, box=None, padding=(0, 1))
            setup_table.add_column("Label", style="cyan", width=18)
            setup_table.add_column("Path", style="white")
            
            setup_table.add_row("Project:", project_info["project_name"])
            setup_table.add_row("Working Path:", project_info["working_directory"])
            setup_table.add_row("Target Path:", project_info["target_directory"])
            
            setup_panel = Panel(
                setup_table,
                title="[bold cyan]Project Setup[/bold cyan]",
                border_style="cyan",
                padding=(1, 2)
            )
            
            console.print(setup_panel)
            console.print()
        
        # Show selected agent with border
        agent_content = f"🤖 {agent} ({AGENT_CONFIG[agent]['name']})"
        agent_panel = Panel(
            Align.center(Text(agent_content, style="bold green")),
            title="[bold cyan]Selected Agent[/bold cyan]",
            border_style="green",
            padding=(0, 1),
            height=3
        )
        console.print(agent_panel)
        console.print()
        
        # Show search box with border
        if search_query:
            search_content = f"🔍 {search_query}"
            search_style = "bold yellow"
            border_style = "yellow"
        else:
            search_content = "🔍 (type to filter servers)"
            search_style = "dim"
            border_style = "dim"
        
        search_panel = Panel(
            Align.center(Text(search_content, style=search_style)),
            title="[bold cyan]Search[/bold cyan]" if search_query else "[dim]Search[/dim]",
            border_style=border_style,
            padding=(0, 1),
            height=3
        )
        console.print(search_panel)
        console.print()
        
        # Get current page items
        page_items, start_idx, end_idx = get_page_items()
        total_pages = get_total_pages()
        
        # Create table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Selector", style="cyan", width=3)
        table.add_column("Checkbox", style="white", width=3)
        table.add_column("Server", style="white", min_width=20)
        table.add_column("By", style="dim", width=28)
        table.add_column("Stars", style="dim", width=10)
        
        # Add rows to table for current page
        for i, server in enumerate(page_items):
            filtered_index = start_idx + i
            original_index = get_original_index(filtered_index)
            
            if filtered_index == current_index:
                # Highlighted selection
                selector = "▶"
                checkbox_style = "bold cyan"
                server_style = "bold cyan"
                desc_style = "cyan"
            else:
                # Normal item
                selector = " "
                if original_index in selected_indices:
                    checkbox_style = "bright_green"
                    server_style = "bright_green"
                    desc_style = "green"
                else:
                    checkbox_style = "white"
                    server_style = "white"
                    desc_style = "dim"
            
            checkbox = "☑" if original_index in selected_indices else "☐"
            
            # Get by (author/organization) field with "By " prefix
            by_org = server.get('by', 'Unknown')
            # Truncate long organization names to fit in column
            if len(by_org) > 20:
                by_org = by_org[:20] + "..."
            by_text = f"By: {by_org}"
            
            # Get stargazer_count and format it with unfilled star icon
            stars = server.get('stargazer_count', 0)
            if stars >= 1000:
                stars_text = f"☆ {stars/1000:.1f}k"
            else:
                stars_text = f"☆ {stars}"
            
            table.add_row(
                Text(selector, style="cyan"),
                Text(checkbox, style=checkbox_style),
                Text(server['name'], style=server_style),
                Text(by_text, style=desc_style),
                Text(stars_text, style=desc_style)
            )
        
        # Create status info for the panel subtitle
        selected_count = len(selected_indices)
        status_info = f"Selected: {selected_count} server{'s' if selected_count != 1 else ''}"
        
        if total_pages > 1:
            status_info += f" | Page {current_page + 1} of {total_pages} | Showing {start_idx + 1}-{end_idx} of {len(filtered_servers)}"
        
        if search_query and len(filtered_servers) != len(servers):
            status_info += f" | Filtered: {len(filtered_servers)}/{len(servers)}"
        
        # Wrap table in a panel with border
        panel = Panel(
            table,
            title="[bold cyan]Choose MCP servers to install:[/bold cyan]",
            subtitle=f"[bold yellow]{status_info}[/bold yellow]",
            border_style="cyan",
            padding=(1, 2)
        )
        
        console.print(panel)
        console.print()
        
        # Help text
        help_lines = [
            "Use ↑/↓ to navigate, Space to toggle, Enter to confirm, Esc to cancel",
            "Type to search/filter servers, Backspace to delete search, Delete to clear search"
        ]
        
        if total_pages > 1:
            help_lines.append("Use ←/→ or PgUp/PgDn to change pages")
        
        help_lines.append("Ctrl+A=select all, Ctrl+N=select none")
        
        for line in help_lines:
            console.print(Text(line, style="dim"))
    
    # Initial render
    render_server_table()
    
    while True:
        try:
            # Read a single character
            key = readchar.readkey()
            
            if key == readchar.key.UP:
                if current_index > 0:
                    current_index -= 1
                    # Check if we need to go to previous page
                    if current_index < current_page * items_per_page and current_page > 0:
                        current_page -= 1
                else:
                    # Wrap to last item
                    current_index = len(filtered_servers) - 1
                    current_page = get_total_pages() - 1
                render_server_table()
                
            elif key == readchar.key.DOWN:
                if current_index < len(filtered_servers) - 1:
                    current_index += 1
                    # Check if we need to go to next page
                    if current_index >= (current_page + 1) * items_per_page:
                        current_page += 1
                else:
                    # Wrap to first item
                    current_index = 0
                    current_page = 0
                render_server_table()
                
            elif key == readchar.key.LEFT or key == readchar.key.PAGE_UP:
                if current_page > 0:
                    current_page -= 1
                    current_index = current_page * items_per_page
                    render_server_table()
                    
            elif key == readchar.key.RIGHT or key == readchar.key.PAGE_DOWN:
                if current_page < get_total_pages() - 1:
                    current_page += 1
                    current_index = current_page * items_per_page
                    render_server_table()
                    
            elif key == ' ':  # Space to toggle selection
                original_index = get_original_index(current_index)
                if original_index in selected_indices:
                    selected_indices.remove(original_index)
                else:
                    selected_indices.add(original_index)
                render_server_table()
                
            elif key == readchar.key.ENTER or key == '\r' or key == '\n':
                if selected_indices:
                    return [servers[i] for i in sorted(selected_indices)]
                else:
                    # If nothing selected, select the current one
                    original_index = get_original_index(current_index)
                    return [servers[original_index]]
                    
            elif key == readchar.key.ESC or key == '\x1b':
                return None
                
            elif key.lower() == 'q':
                return []
                
            elif key == '\x01':  # Ctrl+A to select all (filtered servers)
                for filtered_idx in range(len(filtered_servers)):
                    original_idx = get_original_index(filtered_idx)
                    selected_indices.add(original_idx)
                render_server_table()
                
            elif key == '\x0e':  # Ctrl+N to select none
                selected_indices.clear()
                render_server_table()
                
            elif key == readchar.key.BACKSPACE or key == '\b' or key == '\x7f':  # Backspace
                if search_query:
                    search_query = search_query[:-1]
                    filter_servers()
                    render_server_table()
                    
            elif key == readchar.key.DELETE or key == readchar.key.SUPR:  # Delete key to clear search
                if search_query:
                    search_query = ""
                    filter_servers()
                    render_server_table()
                    
            elif key == '\x03':  # Ctrl+C to exit
                return None  # Return None to indicate cancellation
                    
            elif len(key) == 1 and key.isprintable():  # Regular character input for search
                search_query += key
                filter_servers()
                render_server_table()
                
        except KeyboardInterrupt:
            return None
        except Exception:
            # Handle any readchar exceptions gracefully
            continue

def create_mcp_config(selected_servers: List[Dict[str, Any]], agent: str) -> Dict[str, Any]:
    """Create MCP configuration from selected servers based on agent format."""
    if agent == "copilot":
        # GitHub Copilot format: {"servers": {...}, "inputs": []}
        # Keep gallery and version fields for copilot
        config = {"servers": {}, "inputs": []}
        
        for server in selected_servers:
            mcp_config = server.get("mcp", {})
            # Copy the internal server data exactly as it is for copilot
            config["servers"].update(mcp_config)
    elif agent == "copilot-cli":
        # Copilot CLI format: {"mcpServers": {...}}
        # For copilot-cli, we need different formats based on server type:
        # - For stdio type: change to local type and format server name with hyphens
        # - For http type: include headers field like {"headers": {"CONTEXT7_API_KEY": "YOUR_API_KEY"}}
        config = {"mcpServers": {}}
        
        for server in selected_servers:
            mcp_config = server.get("mcp", {})
            for server_key, server_data in mcp_config.items():
                # Clean the server configuration by removing gallery and version fields
                cleaned_server_data = {k: v for k, v in server_data.items() if k not in ["gallery", "version"]}
                
                # Format server name with hyphens instead of slashes
                formatted_server_key = server_key.replace("/", "-")
                
                # For copilot-cli, change stdio type to local and add tools field
                if cleaned_server_data.get("type") == "stdio":
                    cleaned_server_data["type"] = "local"
                    if "tools" not in cleaned_server_data:
                        cleaned_server_data["tools"] = ["*"]
                elif cleaned_server_data.get("type") == "http":
                    # For http type, add headers field if not present
                    if "headers" not in cleaned_server_data:
                        cleaned_server_data["headers"] = {}
                    # Also add tools field for http type servers
                    if "tools" not in cleaned_server_data:
                        cleaned_server_data["tools"] = ["*"]
                
                config["mcpServers"][formatted_server_key] = cleaned_server_data
    else:
        # Continue, Kiro, Cursor, Qoder, LM Studio, Claude Agent and other agents format: {"mcpServers": {...}}
        # Remove gallery and version fields for other agents
        config = {"mcpServers": {}}
        
        for server in selected_servers:
            mcp_config = server.get("mcp", {})
            # Clean the server configuration by removing gallery and version fields
            cleaned_config = {}
            for server_key, server_data in mcp_config.items():
                cleaned_server_data = {k: v for k, v in server_data.items() if k not in ["gallery", "version"]}
                cleaned_config[server_key] = cleaned_server_data
            config["mcpServers"].update(cleaned_config)
    
    return config

def save_mcp_config(config: Dict[str, Any], config_path: Path, agent: str, json_output: bool = False) -> bool:
    """Save MCP configuration to the specified path, merging with existing entries."""
    try:
        # Create directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        existing_config = {}
        
        # Load existing configuration if it exists
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    existing_config = json.load(f)
                if not json_output:
                    console.print(f"[yellow]Found existing configuration, merging entries...[/yellow]")
            except Exception as e:
                if not json_output:
                    console.print(f"[yellow]Warning: Could not read existing config: {e}[/yellow]")
                    if not Confirm.ask(f"Continue and merge the file?"):
                        return False
                else:
                    # In JSON mode, just continue without prompting
                    pass
        
        # Merge configurations based on agent format
        if agent == "copilot":
            # GitHub Copilot format
            if "servers" not in existing_config:
                existing_config["servers"] = {}
            if "inputs" not in existing_config:
                existing_config["inputs"] = []
            
            # Merge new servers with existing ones
            existing_config["servers"].update(config["servers"])
            
            # Show what's being added
            new_servers = list(config["servers"].keys())
            if not json_output:
                console.print(f"[green]Adding {len(new_servers)} servers to existing configuration:[/green]")
                for server in new_servers:
                    console.print(f"  • {server}")
                
        elif agent == "copilot-cli":
            # Copilot CLI format
            if "mcpServers" not in existing_config:
                existing_config["mcpServers"] = {}
            
            # Merge new servers with existing ones
            existing_config["mcpServers"].update(config["mcpServers"])
            
            # Show what's being added
            new_servers = list(config["mcpServers"].keys())
            if not json_output:
                console.print(f"[green]Adding {len(new_servers)} servers to existing configuration:[/green]")
                for server in new_servers:
                    console.print(f"  • {server}")
        else:
            # Continue, Kiro, Cursor, Qoder, LM Studio, Claude Agent and other agents format
            if "mcpServers" not in existing_config:
                existing_config["mcpServers"] = {}
            
            # Merge new servers with existing ones
            existing_config["mcpServers"].update(config["mcpServers"])
            
            # Show what's being added
            new_servers = list(config["mcpServers"].keys())
            if not json_output:
                console.print(f"[green]Adding {len(new_servers)} servers to existing configuration:[/green]")
                for server in new_servers:
                    console.print(f"  • {server}")
        
        # Save merged configuration
        with open(config_path, 'w') as f:
            json.dump(existing_config, f, indent=2)
        
        if not json_output:
            console.print(f"[green]✓ MCP configuration saved to {config_path}[/green]")
        return True
        
    except Exception as e:
        if not json_output:
            console.print(f"[red]Failed to save configuration: {str(e)}[/red]")
        return False



def load_existing_mcp_config(config_path: Path, agent: str) -> Dict[str, Any]:
    """Load existing MCP configuration from the specified path."""
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[red]Error reading configuration: {e}[/red]")
        return {}

def list_configured_servers(config: Dict[str, Any], agent: str) -> List[str]:
    """List all configured MCP servers from the configuration."""
    if agent == "copilot":
        return list(config.get("servers", {}).keys())
    elif agent == "copilot-cli":
        return list(config.get("mcpServers", {}).keys())
    else:
        return list(config.get("mcpServers", {}).keys())

def remove_servers_from_config(config: Dict[str, Any], servers_to_remove: List[str], agent: str) -> Tuple[Dict[str, Any], List[str], List[str]]:
    """Remove specified servers from configuration. Returns updated config, removed servers, and not found servers."""
    removed_servers = []
    not_found_servers = []
    
    if agent == "copilot":
        servers_dict = config.get("servers", {})
    elif agent == "copilot-cli":
        servers_dict = config.get("mcpServers", {})
    else:
        servers_dict = config.get("mcpServers", {})
    
    for server_name in servers_to_remove:
        # First try exact match
        if server_name in servers_dict:
            del servers_dict[server_name]
            removed_servers.append(server_name)
        else:
            # Try partial matching - look for servers that end with the given name
            # This allows "fetch" to match "modelcontextprotocol/fetch" or "modelcontextprotocol-fetch" for copilot-cli
            matches = []
            for full_name in servers_dict.keys():
                # Check if the server name ends with the given name (after a slash or hyphen)
                if full_name.endswith('/' + server_name) or full_name.endswith('-' + server_name) or full_name == server_name:
                    matches.append(full_name)
            
            if len(matches) == 1:
                # Single match found, remove it
                full_name = matches[0]
                del servers_dict[full_name]
                removed_servers.append(full_name)
            elif len(matches) > 1:
                # Multiple matches found, this is ambiguous
                console.print(f"[yellow]Ambiguous server name '{server_name}'. Multiple matches found:[/yellow]")
                for match in matches:
                    console.print(f"  • {match}")
                console.print(f"[yellow]Please use the full server name to specify which one to remove.[/yellow]")
                not_found_servers.append(server_name)
            else:
                # No matches found
                not_found_servers.append(server_name)
    
    return config, removed_servers, not_found_servers

@app.command("list")
def list_servers(
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Agent to list servers for (copilot, copilot-cli, continue, kiro, cursor, qoder, lmstudio, claude, gemini)"),
    project_path: Optional[str] = typer.Option(None, "--project", "-p", help="Project path (use '.' for current directory, omit for global configuration)"),
    available_servers: bool = typer.Option(False, "--servers", "-s", help="List all available MCP servers instead of configured ones"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output in JSON format without banner or UI"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output when listing available servers (default: false)"),
):
    """List configured MCP servers or all available servers."""
    # Handle listing available servers
    if available_servers:
        # Download MCP servers
        servers_data = download_mcp_servers()
        if not servers_data:
            error_data = {"error": "Failed to download MCP servers"}
            if json_output:
                if pretty:
                    print(json.dumps(error_data, indent=2))
                else:
                    print(json.dumps(error_data))
            else:
                console.print("[red]Failed to download MCP servers[/red]")
            raise typer.Exit(1)
        
        # Output the servers data
        if json_output:
            if pretty:
                print(json.dumps(servers_data, indent=2))
            else:
                print(json.dumps(servers_data))
        else:
            # Show banner for non-JSON output
            show_banner()
            console.print(Panel(
                Align.center(Text("Available MCP Servers", style="bold yellow")),
                title="[bold cyan]Servers List[/bold cyan]",
                border_style="yellow",
                padding=(0, 1),
                height=3
            ))
            console.print()
            
            # Display servers in table format
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("Server", style="white", min_width=20)
            table.add_column("By", style="dim", width=28)
            table.add_column("Stars", style="dim", width=10)
            
            for server in servers_data:
                # Get by (author/organization) field with "By " prefix
                by_org = server.get('by', 'Unknown')
                # Truncate long organization names to fit in column
                if len(by_org) > 20:
                    by_org = by_org[:20] + "..."
                by_text = f"By: {by_org}"
                
                # Get stargazer_count and format it with unfilled star icon
                stars = server.get('stargazer_count', 0)
                if stars >= 1000:
                    stars_text = f"☆ {stars/1000:.1f}k"
                else:
                    stars_text = f"☆ {stars}"
                
                table.add_row(
                    Text(server['name'], style="white"),
                    Text(by_text, style="dim"),
                    Text(stars_text, style="dim")
                )
            
            # Wrap table in a panel with border
            panel = Panel(
                table,
                title=f"[bold cyan]Available MCP Servers ({len(servers_data)} total)[/bold cyan]",
                border_style="cyan",
                padding=(1, 2)
            )
            
            console.print(panel)
            console.print()
            console.print(Text("Use 'mcp init --servers <server_name> -a <agent>' to add servers to your configuration", style="dim"))
        
        return
    
    # Original logic for listing configured servers
    # Skip banner and UI for JSON output
    if not json_output:
        show_banner()
    
    # Determine if this is global configuration
    is_global = project_path is None
    
    if not json_output:
        if is_global:
            console.print(Panel(
                Align.center(Text("Global MCP Configuration", style="bold yellow")),
                title="[bold cyan]List Mode[/bold cyan]",
                border_style="yellow",
                padding=(0, 1),
                height=3
            ))
            console.print()
        else:
            console.print(Panel(
                Align.center(Text(f"Project: {project_path}", style="bold yellow")),
                title="[bold cyan]List Mode[/bold cyan]",
                border_style="yellow",
                padding=(0, 1),
                height=3
            ))
            console.print()
    
    if not is_global:
        working_directory = Path.cwd()
        if project_path == ".":
            target_path = working_directory
        else:
            target_path = working_directory / project_path
            
        if not target_path.exists():
            if json_output:
                print(json.dumps({"error": f"Project directory does not exist: {target_path}"}, indent=2))
            else:
                console.print(f"[red]Project directory does not exist: {target_path}[/red]")
            raise typer.Exit(1)
    else:
        target_path = None
    
    # Select agent if not provided
    if not agent:
        if json_output:
            print(json.dumps({"error": "Agent must be specified with --agent when using --json"}, indent=2))
            raise typer.Exit(1)
        agent = select_agent()
        if not agent:
            console.print("[red]No agent selected. Exiting.[/red]")
            raise typer.Exit(1)
    
    if agent not in AGENT_CONFIG:
        error_msg = f"Unknown agent: {agent}. Available: {', '.join(AGENT_CONFIG.keys())}"
        if json_output:
            print(json.dumps({"error": error_msg}, indent=2))
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise typer.Exit(1)
    
    if not json_output:
        console.print(f"[bold green]Selected Agent: {AGENT_CONFIG[agent]['name']}[/bold green]")
    
    # Get configuration path
    if is_global or agent == "qoder" or agent == "lmstudio" or agent == "copilot-cli":
        config_path = get_mcp_config_path(agent)
    else:
        config_path = get_mcp_config_path(agent, target_path)
    
    if not json_output:
        console.print(f"[dim]Configuration path: {config_path}[/dim]")
        console.print()
    
    # Load existing configuration
    existing_config = load_existing_mcp_config(config_path, agent)
    if not existing_config:
        if json_output:
            print(json.dumps({"servers": [], "message": "No MCP configuration found"}, indent=2))
        else:
            console.print(f"[yellow]No MCP configuration found at: {config_path}[/yellow]")
            console.print("[dim]Run 'mcp init' to create a new configuration.[/dim]")
        raise typer.Exit(0)
    
    # Get list of configured servers
    configured_servers = list_configured_servers(existing_config, agent)
    if not configured_servers:
        if json_output:
            print(json.dumps({"servers": [], "message": "No MCP servers are currently configured"}, indent=2))
        else:
            console.print("[yellow]No MCP servers are currently configured.[/yellow]")
            console.print("[dim]Run 'mcp init' to add MCP servers.[/dim]")
        raise typer.Exit(0)
    
    # Download available servers to get rich display data
    available_servers = download_mcp_servers()
    if not available_servers and not json_output:
        console.print("[yellow]Could not download server information. Using basic display.[/yellow]")
        available_servers = []
    
    # Match configured servers with available server data
    matched_servers = []
    for configured_name in configured_servers:
        # Find matching server in available_servers list
        matched_server = None
        for server in available_servers:
            server_mcp = server.get("mcp", {})
            # Check if any key in the mcp dict matches the configured server name
            for mcp_key in server_mcp.keys():
                # For copilot-cli, convert hyphenated names back to slash format for matching
                if agent == "copilot-cli":
                    # Convert configured_name from hyphenated to slash format
                    if '-' in configured_name and '/' not in configured_name:
                        slash_name = configured_name.replace('-', '/')
                        if mcp_key == slash_name or mcp_key.endswith('/' + slash_name.split('/')[-1]):
                            matched_server = {
                                'name': server['name'],
                                'by': server.get('by', 'Unknown'),
                                'stargazer_count': server.get('stargazer_count', 0),
                                'configured_name': configured_name,
                                'mcp_key': mcp_key,
                                'description': server.get('description', 'No description available')
                            }
                            break
                else:
                    # For other agents, use existing matching logic
                    if mcp_key == configured_name or mcp_key.endswith('/' + configured_name.split('/')[-1]):
                        matched_server = {
                            'name': server['name'],
                            'by': server.get('by', 'Unknown'),
                            'stargazer_count': server.get('stargazer_count', 0),
                            'configured_name': configured_name,
                            'mcp_key': mcp_key,
                            'description': server.get('description', 'No description available')
                        }
                        break
            if matched_server:
                break
        
        # If no match found, create a basic entry with better defaults
        if not matched_server:
            # For copilot-cli, server names use hyphens instead of slashes
            if agent == "copilot-cli":
                name_parts = configured_name.split('-')
            else:
                name_parts = configured_name.split('/')
            
            if len(name_parts) > 1:
                # Format: org-name or org/name - use org as 'by' field and name as server name
                by_org = name_parts[0]
                server_name = name_parts[-1].title()
            else:
                # Format: name - use the name as server name and 'Unknown' as org
                by_org = 'Unknown'
                server_name = configured_name.title()
            
            matched_server = {
                'name': server_name,
                'by': by_org,
                'stargazer_count': 0,
                'configured_name': configured_name,
                'mcp_key': configured_name,
                'description': 'No description available'
            }
        
        matched_servers.append(matched_server)
    
    # Output in JSON format or display table
    if json_output:
        # Output clean JSON without any UI elements
        output_data = {
            "agent": agent,
            "agent_name": AGENT_CONFIG[agent]['name'],
            "config_path": str(config_path),
            "is_global": is_global,
            "servers": matched_servers
        }
        if pretty:
            print(json.dumps(output_data, indent=2))
        else:
            print(json.dumps(output_data))
    else:
        # Display servers in the same format as mcp init (Server, By, Stars)
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Server", style="white", min_width=20)
        table.add_column("By", style="dim", width=28)
        table.add_column("Stars", style="dim", width=10)
        
        for server in matched_servers:
            # Get by (author/organization) field with "By " prefix
            by_org = server.get('by', 'Unknown')
            # Truncate long organization names to fit in column
            if len(by_org) > 20:
                by_org = by_org[:20] + "..."
            by_text = f"By: {by_org}"
            
            # Get stargazer_count and format it with unfilled star icon
            stars = server.get('stargazer_count', 0)
            if stars >= 1000:
                stars_text = f"☆ {stars/1000:.1f}k"
            else:
                stars_text = f"☆ {stars}"
            
            table.add_row(
                Text(server['name'], style="cyan"),
                Text(by_text, style="dim"),
                Text(stars_text, style="dim")
            )
        
        # Wrap table in a panel
        panel = Panel(
            table,
            title=f"[bold cyan]Configured MCP Servers ({len(configured_servers)})[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        )
        
        console.print(panel)
    




@app.command()
def rm(
    servers: Optional[List[str]] = typer.Argument(None, help="MCP server names to remove (e.g., 'git', 'filesystem')"),
    all_servers: bool = typer.Option(False, "--all", "-A", help="Remove all MCP servers"),
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Agent to configure (copilot, copilot-cli, continue, kiro, cursor, qoder, lmstudio, claude, gemini)"),
    project_path: Optional[str] = typer.Option(None, "--project", "-p", help="Project path (use '.' for current directory, omit for global configuration)"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompts"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output in JSON format without banner or UI"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output (default: false)"),
):
    """Remove MCP servers from configuration."""
    # Skip banner and UI for JSON output
    if not json_output:
        show_banner()
    
    # Determine if this is global configuration
    is_global = project_path is None
    
    if not json_output:
        if is_global:
            console.print(Panel(
                Align.center(Text("Global MCP Configuration", style="bold yellow")),
                title="[bold cyan]Remove Mode[/bold cyan]",
                border_style="yellow",
                padding=(0, 1),
                height=3
            ))
            console.print()
        else:
            console.print(Panel(
                Align.center(Text(f"Project: {project_path}", style="bold yellow")),
                title="[bold cyan]Remove Mode[/bold cyan]",
                border_style="yellow",
                padding=(0, 1),
                height=3
            ))
            console.print()
    
    if not is_global:
        working_directory = Path.cwd()
        if project_path == ".":
            target_path = working_directory
        else:
            target_path = working_directory / project_path
            
        if not target_path.exists():
            error_msg = f"Project directory does not exist: {target_path}"
            if json_output:
                print(json.dumps({"error": error_msg}, indent=2))
            else:
                console.print(f"[red]{error_msg}[/red]")
            raise typer.Exit(1)
        target_path = target_path
    else:
        target_path = None
    
    # Select agent if not provided
    if not agent:
        if json_output:
            print(json.dumps({"error": "Agent must be specified with --agent when using --json"}, indent=2))
            raise typer.Exit(1)
        agent = select_agent()
        if not agent:
            console.print("[red]No agent selected. Exiting.[/red]")
            raise typer.Exit(1)
    
    if agent not in AGENT_CONFIG:
        error_msg = f"Unknown agent: {agent}. Available: {', '.join(AGENT_CONFIG.keys())}"
        if json_output:
            print(json.dumps({"error": error_msg}, indent=2))
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise typer.Exit(1)
    
    if not json_output:
        console.print(f"[bold green]Selected Agent: {AGENT_CONFIG[agent]['name']}[/bold green]")
    
    # Get configuration path
    if is_global or agent == "qoder" or agent == "lmstudio" or agent == "copilot-cli":
        config_path = get_mcp_config_path(agent)
    else:
        config_path = get_mcp_config_path(agent, target_path)
    
    # Load existing configuration
    existing_config = load_existing_mcp_config(config_path, agent)
    if not existing_config:
        error_msg = f"No MCP configuration found at: {config_path}"
        if json_output:
            print(json.dumps({"error": error_msg}, indent=2))
        else:
            console.print(f"[yellow]{error_msg}[/yellow]")
        raise typer.Exit(0)
    
    # Get list of configured servers
    configured_servers = list_configured_servers(existing_config, agent)
    if not configured_servers:
        error_msg = "No MCP servers are currently configured"
        if json_output:
            print(json.dumps({"error": error_msg}, indent=2))
        else:
            console.print(f"[yellow]{error_msg}.[/yellow]")
        raise typer.Exit(0)
    
    if not json_output:
        console.print(f"\n[cyan]Currently configured servers ({len(configured_servers)}):[/cyan]")
        for server in configured_servers:
            console.print(f"  • {server}")
        console.print()
    
    # Determine which servers to remove
    if all_servers:
        servers_to_remove = configured_servers.copy()
        if not force and not json_output:
            if not Confirm.ask(f"[bold red]Are you sure you want to remove ALL {len(servers_to_remove)} MCP servers?[/bold red]"):
                console.print("[yellow]Operation cancelled.[/yellow]")
                raise typer.Exit(0)
    elif servers:
        servers_to_remove = servers
        if not force and not json_output:
            console.print(f"[yellow]Servers to remove: {', '.join(servers_to_remove)}[/yellow]")
            if not Confirm.ask("Continue with removal?"):
                console.print("[yellow]Operation cancelled.[/yellow]")
                raise typer.Exit(0)
    else:
        if json_output:
            print(json.dumps({"error": "Interactive server selection not supported with --json. Specify servers to remove or use --all"}, indent=2))
            raise typer.Exit(1)
        
        # Interactive server selection for removal
        # Download available servers to get rich display data
        available_servers = download_mcp_servers()
        if not available_servers:
            console.print("[yellow]Could not download server information. Using basic display.[/yellow]")
            available_servers = []
        
        # Prepare project info for display if in project mode
        project_info = None
        if not is_global:
            project_info = {
                "project_name": target_path.name if target_path else "current",
                "working_directory": str(Path.cwd()),
                "target_directory": str(target_path) if target_path else str(Path.cwd())
            }
        
        selected_servers = select_servers_to_remove(configured_servers, available_servers, agent, project_info)
        
        if selected_servers is None:
            console.print("[yellow]Server selection cancelled.[/yellow]")
            raise typer.Exit(0)
        if not selected_servers:
            console.print("[yellow]No servers selected for removal.[/yellow]")
            raise typer.Exit(0)
        
        servers_to_remove = selected_servers
        
        if not force:
            console.print(f"[yellow]Selected servers to remove: {', '.join(servers_to_remove)}[/yellow]")
            if not Confirm.ask("Continue with removal?"):
                console.print("[yellow]Operation cancelled.[/yellow]")
                raise typer.Exit(0)
    
    # Remove servers from configuration
    updated_config, removed_servers, not_found_servers = remove_servers_from_config(
        existing_config, servers_to_remove, agent
    )
    
    # Save updated configuration
    try:
        with open(config_path, 'w') as f:
            json.dump(updated_config, f, indent=2)
        
        # Get remaining servers
        remaining_servers = list_configured_servers(updated_config, agent)
        
        # Output results
        if json_output:
            # Output clean JSON without any UI elements
            output_data = {
                "agent": agent,
                "agent_name": AGENT_CONFIG[agent]['name'],
                "config_path": str(config_path),
                "is_global": is_global,
                "operation": "remove",
                "requested_servers": servers_to_remove,
                "removed_servers": removed_servers,
                "not_found_servers": not_found_servers,
                "remaining_servers": remaining_servers,
                "total_removed": len(removed_servers),
                "total_remaining": len(remaining_servers)
            }
            if pretty:
                print(json.dumps(output_data, indent=2))
            else:
                print(json.dumps(output_data))
        else:
            # Report results with UI
            if removed_servers:
                console.print(f"[green]✓ Successfully removed {len(removed_servers)} server(s):[/green]")
                for server in removed_servers:
                    console.print(f"  • {server}")
            
            if not_found_servers:
                console.print(f"[yellow]⚠ Could not find {len(not_found_servers)} server(s):[/yellow]")
                for server in not_found_servers:
                    console.print(f"  • {server}")
            
            if not removed_servers:
                console.print("[yellow]No servers were removed.[/yellow]")
                raise typer.Exit(0)
            
            console.print(f"\n[green]✓ Configuration updated: {config_path}[/green]")
            
            # Show remaining servers
            if remaining_servers:
                console.print(f"\n[cyan]Remaining servers ({len(remaining_servers)}):[/cyan]")
                for server in remaining_servers:
                    console.print(f"  • {server}")
            else:
                console.print(f"\n[dim]No MCP servers remain in the configuration.[/dim]")
            
    except Exception as e:
        error_msg = f"Failed to save configuration: {str(e)}"
        if json_output:
            print(json.dumps({"error": error_msg}, indent=2))
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise typer.Exit(1)

def check_agent_installation(agent_key: str, agent_config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if an agent is installed on the system."""
    result = {
        "agent": agent_key,
        "name": agent_config["name"],
        "installed": False,
        "config_exists": False,
        "config_path": None,
        "cli_available": False,
        "install_url": agent_config.get("install_url"),
        "details": []
    }
    
    # Check for configuration folder/file
    try:
        config_path = get_mcp_config_path(agent_key)
        result["config_path"] = str(config_path)
        
        # Check if config file exists
        if config_path.exists():
            result["config_exists"] = True
            result["details"].append(f"Config found: {config_path}")
        else:
            result["details"].append(f"Config not found: {config_path}")
        
        # Check if parent directory exists (indicates agent might be installed)
        if agent_config["folder"]:
            # Check global agent folder
            agent_folder = Path.home() / agent_config["folder"]
            if agent_folder.exists():
                result["installed"] = True
                result["details"].append(f"Agent folder found: {agent_folder}")
            else:
                result["details"].append(f"Agent folder not found: {agent_folder}")
    except Exception as e:
        result["details"].append(f"Error checking config: {str(e)}")
    
    # Check CLI availability if required
    if agent_config.get("requires_cli", False):
        try:
            # Try to run the CLI command to check if it's available
            cli_commands = {
                # "claude": ["claude", "--version"], comment not working with electron
                "gemini": ["gemini", "--version"],
                "copilot-cli": ["copilot", "--version"],
            }
            
            if agent_key in cli_commands:
                try:
                    # On Windows, some CLI tools might be PowerShell scripts
                    # Try direct execution first, then PowerShell if that fails
                    cmd = cli_commands[agent_key]
                    
                    try:
                        result_cmd = subprocess.run(
                            cmd, 
                            capture_output=True, 
                            text=True, 
                            timeout=5
                        )
                        if result_cmd.returncode == 0:
                            result["cli_available"] = True
                            result["details"].append("CLI tool available")
                        else:
                            result["details"].append("CLI tool not available or not working")
                    except FileNotFoundError:
                        # If direct execution fails on Windows, try with PowerShell
                        if platform.system().lower() == "windows":
                            try:
                                powershell_cmd = ["powershell", "-Command"] + cmd
                                result_cmd = subprocess.run(
                                    powershell_cmd,
                                    capture_output=True,
                                    text=True,
                                    timeout=5
                                )
                                if result_cmd.returncode == 0:
                                    result["cli_available"] = True
                                    result["details"].append("CLI tool available (via PowerShell)")
                                else:
                                    result["details"].append("CLI tool not available or not working")
                            except Exception:
                                result["details"].append("CLI tool not found in PATH")
                        else:
                            result["details"].append("CLI tool not found in PATH")
                            
                except subprocess.TimeoutExpired:
                    result["details"].append("CLI tool check timed out")
        except Exception as e:
            result["details"].append(f"Error checking CLI: {str(e)}")
    else:
        # For IDE-based agents, assume CLI is available if the agent folder exists
        result["cli_available"] = result["installed"]
    
    # Overall installation status
    if agent_config.get("requires_cli", False):
        result["installed"] = result["cli_available"]
    
    return result


@app.command()
def check(
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Specific agent to check (copilot, copilot-cli, continue, kiro, cursor, qoder, lmstudio, claude, gemini)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output in JSON format without banner or UI"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output (default: false)"),
):
    """Check which AI agents are installed on your system."""
    # Skip banner and UI for JSON output
    if not json_output:
        show_banner()
        
        console.print(Panel(
            Align.center(Text("Agent Installation Check", style="bold yellow")),
            title="[bold cyan]System Check[/bold cyan]",
            border_style="yellow",
            padding=(0, 1),
            height=3
        ))
        console.print()
    
    # Check specific agent or all agents
    if agent:
        if agent not in AGENT_CONFIG:
            error_msg = f"Unknown agent: {agent}. Available: {', '.join(AGENT_CONFIG.keys())}"
            if json_output:
                print(json.dumps({"error": error_msg}, indent=2))
            else:
                console.print(f"[red]{error_msg}[/red]")
            raise typer.Exit(1)
        agents_to_check = {agent: AGENT_CONFIG[agent]}
    else:
        agents_to_check = AGENT_CONFIG
    
    # Check each agent
    results = []
    if json_output:
        # Skip status display for JSON output
        for agent_key, agent_config in agents_to_check.items():
            result = check_agent_installation(agent_key, agent_config)
            results.append(result)
    else:
        with console.status("[bold green]Checking installed agents..."):
            for agent_key, agent_config in agents_to_check.items():
                result = check_agent_installation(agent_key, agent_config)
                results.append(result)
    
    # Count installed and configured agents
    installed_count = sum(1 for result in results if result["installed"])
    configured_count = sum(1 for result in results if result["config_exists"])
    
    # Output in JSON format or display table
    if json_output:
        # Output clean JSON without any UI elements
        output_data = {
            "total_agents": len(results),
            "installed_count": installed_count,
            "configured_count": configured_count,
            "agents": results
        }
        if pretty:
            print(json.dumps(output_data, indent=2))
        else:
            print(json.dumps(output_data))
    else:
        # Display results in a table
        table = Table(show_header=True, box=None, padding=(0, 1))
        table.add_column("Agent", style="white", min_width=15)
        table.add_column("Status", style="white", width=12)
        table.add_column("Config", style="white", width=8)
        
        for result in results:
            # Status column
            if result["installed"]:
                status = Text("✓ Installed", style="bold green")
            else:
                status = Text("✗ Not Found", style="bold red")
            
            # Config column  
            if result["config_exists"]:
                config_status = Text("✓ Yes", style="green")
            else:
                config_status = Text("✗ No", style="red")
            
            # Agent name with install URL if available
            agent_name = result["name"]
            if not result["installed"] and result["install_url"]:
                agent_name = f"{agent_name} (install: {result['install_url']})"
            
            table.add_row(
                Text(agent_name, style="cyan"),
                status,
                config_status
            )
        
        # Wrap table in a panel
        summary = f"Found {installed_count}/{len(results)} installed, {configured_count}/{len(results)} configured"
        panel = Panel(
            table,
            title="[bold cyan]AI Agent Status[/bold cyan]",
            subtitle=f"[bold yellow]{summary}[/bold yellow]",
            border_style="cyan",
            padding=(1, 2)
        )
        
        console.print(panel)
        console.print()
        
        if installed_count == 0:
            console.print("[yellow]No AI agents found installed on your system.[/yellow]")
            console.print("[dim]Install an agent and run 'mcp init' to get started with MCP servers.[/dim]")
        elif configured_count == 0:
            console.print("[yellow]No agents have MCP configuration yet.[/yellow]")
            console.print("[dim]Run 'mcp init' to configure MCP servers for your installed agents.[/dim]")
        else:
            console.print(f"[green]You have {configured_count} agent(s) with MCP configuration.[/green]")
            console.print("[dim]Run 'mcp list' to see configured servers or 'mcp init' to add more.[/dim]")

@app.command()
def init(
    project_name: Optional[str] = typer.Argument(None, help="Name of the project to initialize (use '.' for current directory, omit for global configuration)"),
    servers: Optional[List[str]] = typer.Option(None, "--servers", "-s", help="MCP server names to add directly. Use multiple times (-s git -s filesystem) or space-separated (-s 'git filesystem')"),
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Agent to configure (copilot, copilot-cli, continue, kiro, cursor, qoder, lmstudio, claude, gemini)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output in JSON format without banner or UI"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output (default: false)"),
):
    """Initialize MCP configuration in a project directory or globally."""
    # Skip banner and UI for JSON output
    if not json_output:
        show_banner()
    
    # Determine if this is global configuration (when no project name is provided)
    is_global = project_name is None
    
    if is_global:
        # Global configuration mode
        project_info = None
        project_path = None
        if not json_output:
            console.print(Panel(
                Align.center(Text("Global MCP Configuration", style="bold yellow")),
                title="[bold cyan]Setup Mode[/bold cyan]",
                border_style="yellow",
                padding=(0, 1),
                height=3
            ))
            console.print()
    else:
        # Project-specific configuration mode
        working_directory = Path.cwd()
        if project_name == ".":
            project_path = working_directory
            target_directory = working_directory
            directory_created = False
        else:
            project_path = working_directory / project_name
            target_directory = project_path
            
            # Check if directory exists before creating
            directory_existed = project_path.exists()
            
            # Create project directory if it doesn't exist
            if not directory_existed:
                project_path.mkdir(parents=True, exist_ok=True)
                directory_created = True
            else:
                directory_created = False
        
        # Prepare project info for display
        project_info = {
            "project_name": project_name,
            "working_directory": str(working_directory),
            "target_directory": str(target_directory)
        }
        
        # Display project setup information
        if not json_output:
            setup_table = Table(show_header=False, box=None, padding=(0, 1))
            setup_table.add_column("Label", style="cyan", width=18)
            setup_table.add_column("Path", style="white")
            
            setup_table.add_row("Project:", project_name)
            setup_table.add_row("Working Path:", str(working_directory))
            setup_table.add_row("Target Path:", str(target_directory))
            
            setup_panel = Panel(
                setup_table,
                title="[bold cyan]Project Setup[/bold cyan]",
                border_style="cyan",
                padding=(1, 2)
            )
            
            console.print(setup_panel)
            console.print()
            
            if project_name != "." and directory_created:
                console.print(f"[green]✓ Created project directory: {project_path}[/green]")
    
    # Download MCP servers
    available_servers = download_mcp_servers()
    if not available_servers:
        if json_output:
            print(json.dumps({"error": "Failed to download MCP servers"}, indent=2))
        raise typer.Exit(1)
    
    if not json_output:
        console.print(f"[green]✓ Downloaded {len(available_servers)} MCP servers[/green]")
    
    # Select agent if not provided
    if not agent:
        if json_output:
            print(json.dumps({"error": "Agent must be specified with --agent when using --json"}, indent=2))
            raise typer.Exit(1)
        agent = select_agent(project_info)
        if not agent:
            console.print("[red]No agent selected. Exiting.[/red]")
            raise typer.Exit(1)
    
    if agent not in AGENT_CONFIG:
        error_msg = f"Unknown agent: {agent}. Available: {', '.join(AGENT_CONFIG.keys())}"
        if json_output:
            print(json.dumps({"error": error_msg}, indent=2))
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise typer.Exit(1)
    
    if not json_output:
        console.print(f"\n[bold green]Selected Agent: {AGENT_CONFIG[agent]['name']}[/bold green]")
    
    # Check if agent supports project-level configuration
    if not json_output:
        if agent == "qoder":
            console.print(f"[yellow]⚠️  Note: Qoder does not support project-level MCP configuration.[/yellow]")
            console.print(f"[yellow]   Configuration will be saved to global Qoder settings instead.[/yellow]")
            console.print()
        elif agent == "copilot-cli":
            console.print(f"[yellow]⚠️  Note: Copilot CLI does not support project-level MCP configuration.[/yellow]")
            console.print(f"[yellow]   Configuration will be saved to global Copilot CLI settings instead.[/yellow]")
            console.print()
        elif agent == "lmstudio":
            console.print(f"[yellow]⚠️  Note: LM Studio does not need project-level MCP configuration.[/yellow]")
            console.print(f"[yellow]   Configuration will be saved to global LM Studio settings instead.[/yellow]")
            console.print()
        elif agent == "claude":
            if is_global:
                console.print(f"[cyan]ℹ️  Claude global configuration will be saved to ~/.claude.json[/cyan]")
            else:
                console.print(f"[cyan]ℹ️  Claude project configuration will be saved to .mcp.json[/cyan]")
            console.print()
        elif agent == "gemini":
            if is_global:
                console.print(f"[cyan]ℹ️  Gemini global configuration will be saved to ~/.gemini/settings.json[/cyan]")
            else:
                console.print(f"[cyan]ℹ️  Gemini project configuration will be saved to .gemini/settings.json[/cyan]")
            console.print()
    
    # Select MCP servers - either from command line arguments or interactive selection
    if servers:
        # Direct server specification via command line
        # Handle both formats: -s git -s filesystem AND -s "git filesystem"
        flattened_servers = []
        for server_spec in servers:
            # Split by spaces to handle "git filesystem" format
            flattened_servers.extend(server_spec.split())
        
        selected_servers = []
        not_found_servers = []
        
        for server_name in flattened_servers:
            # Find matching server in available_servers list
            matched_server = None
            for server in available_servers:
                lower_name = server['name'].lower()
                if lower_name == server_name:
                    matched_server = server
                    break
                server_mcp = server.get("mcp", {})
                # Check if any key in the mcp dict matches the server name
                for mcp_key in server_mcp.keys():
                    if mcp_key == server_name or mcp_key.endswith('/' + server_name.split('/')[-1]):
                        matched_server = server
                        break
                if matched_server:
                    break
            
            if matched_server:
                selected_servers.append(matched_server)
            else:
                not_found_servers.append(server_name)
        
        if not_found_servers:
            error_msg = f"Could not find servers: {', '.join(not_found_servers)}"
            if json_output:
                print(json.dumps({"error": error_msg, "available_servers": [s["name"] for s in available_servers]}, indent=2))
            else:
                console.print(f"[red]{error_msg}[/red]")
                console.print(f"[dim]Available servers: {', '.join([s['name'] for s in available_servers])}[/dim]")
            raise typer.Exit(1)
        
        if not json_output:
            console.print(f"\n[bold green]Selected {len(selected_servers)} MCP servers directly[/bold green]")
    else:
        # Interactive server selection
        if json_output:
            print(json.dumps({"error": "Interactive server selection not supported with --json. Specify servers with --servers"}, indent=2))
            raise typer.Exit(1)
        
        selected_servers = select_mcp_servers(available_servers, agent, project_info)
        if selected_servers is None:
            console.print("[red]Server selection cancelled. Exiting.[/red]")
            raise typer.Exit(1)
        if not selected_servers:
            console.print("[yellow]No servers selected. Exiting.[/yellow]")
            raise typer.Exit(0)
        
        console.print(f"\n[bold green]Selected {len(selected_servers)} MCP servers[/bold green]")
    
    # Create configuration
    config = create_mcp_config(selected_servers, agent)
    
    # Get configuration path based on mode (global vs project-specific)
    if is_global or agent == "qoder" or agent == "lmstudio" or agent == "copilot-cli":
        config_path = get_mcp_config_path(agent)  # Global path
    else:
        config_path = get_mcp_config_path(agent, project_path)  # Project-specific path
    
    # Save configuration
    if save_mcp_config(config, config_path, agent, json_output):
        if json_output:
            # Output clean JSON without any UI elements
            output_data = {
                "agent": agent,
                "agent_name": AGENT_CONFIG[agent]['name'],
                "config_path": str(config_path),
                "is_global": is_global,
                "operation": "init",
                "servers_added": [s["name"] for s in selected_servers],
                "total_servers": len(selected_servers),
                "success": True
            }
            if not is_global:
                output_data["project_name"] = project_name
                output_data["project_path"] = str(project_path) if project_path else None
            if pretty:
                print(json.dumps(output_data, indent=2))
            else:
                print(json.dumps(output_data))
        else:
            if is_global:
                console.print(f"\n[bold green]🎉 MCP global configuration completed successfully![/bold green]")
                
                # Show next steps for global configuration
                console.print(f"\n[bold cyan]Next steps:[/bold cyan]")
                console.print(f"1. Open {AGENT_CONFIG[agent]['name']}")
                console.print(f"2. The MCP servers will be loaded from global settings")
                if agent == "copilot":
                    console.print(f"3. Make sure you have the GitHub Copilot extension installed in VS Code")
                elif agent == "continue":
                    console.print(f"3. Make sure you have the Continue extension installed in your IDE")
                elif agent == "kiro":
                    console.print(f"3. The configuration is available across all Kiro projects")
                elif agent == "cursor":
                    console.print(f"3. The configuration is available across all Cursor projects")
                elif agent == "qoder":
                    console.print(f"3. The configuration is available across all Qoder projects")
                elif agent == "lmstudio":
                    console.print(f"3. The configuration is available across all LM Studio projects")
                elif agent == "claude":
                    console.print(f"3. Use 'claude' command to start a new conversation")
                elif agent == "gemini":
                    console.print(f"3. Use 'gemini' command to start a new conversation")
                elif agent == "copilot-cli":
                    console.print(f"3. Use 'copilot' command to start a new conversation")
            else:
                console.print(f"\n[bold green]🎉 MCP project initialization completed successfully![/bold green]")
                
                # Show next steps for project configuration
                console.print(f"\n[bold cyan]Next steps:[/bold cyan]")
                console.print(f"1. Open your project in {AGENT_CONFIG[agent]['name']}")
                
                if agent == "qoder":
                    console.print(f"2. The MCP servers will be loaded from global Qoder settings")
                    console.print(f"3. Open the project in Qoder IDE")
                elif agent == "copilot-cli":
                    console.print(f"2. The MCP servers will be loaded from global Copilot CLI settings")
                    console.print(f"3. Open the chat in Copilot CLI")
                elif agent == "lmstudio":
                    console.print(f"2. The MCP servers will be loaded from global LM Studio settings")
                    console.print(f"3. Open the chat in LM Studio")
                else:
                    console.print(f"2. The MCP servers will be automatically loaded from: {config_path.relative_to(project_path)}")
                    if agent == "copilot":
                        console.print(f"3. Make sure you have the GitHub Copilot extension installed in VS Code")
                    elif agent == "continue":
                        console.print(f"3. Make sure you have the Continue extension installed in your IDE")
                    elif agent == "kiro":
                        console.print(f"3. Open the project in Kiro IDE")
                    elif agent == "cursor":
                        console.print(f"3. Open the project in Cursor IDE")
                    elif agent == "lmstudio":
                        console.print(f"3. Open the chat in LM Studio")
                    elif agent == "claude":
                        console.print(f"3. Use 'claude' command in this project directory")
                        console.print(f"4. The MCP servers will be automatically loaded from .mcp.json")
                    elif agent == "gemini":
                        console.print(f"3. Use 'gemini' command in this project directory")
                        console.print(f"4. The MCP servers will be automatically loaded from .gemini/settings.json")
    else:
        if json_output:
            print(json.dumps({"error": "Failed to save configuration", "success": False}, indent=2))
        raise typer.Exit(1)

@app.callback()
def callback(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(None, "--version", "-v", callback=version_callback, is_eager=True, help="Show version and exit")
):
    """Show banner when no subcommand is provided."""
    if ctx.invoked_subcommand is None and "--help" not in sys.argv and "-h" not in sys.argv and "--version" not in sys.argv and "-v" not in sys.argv:
        show_banner()
        console.print(Align.center("[dim]Run 'mcp --help' for usage information[/dim]"))
        console.print()

def main():
    """Main entry point for the CLI."""
    app()

if __name__ == "__main__":
    main()

__all__ = [
    "main",
    "download_mcp_servers",
    "get_mcp_config_path",
]