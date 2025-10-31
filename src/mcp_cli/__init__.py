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
    # Global configuration (default)
    uvx mcp-cli.py init
    
    # Project-specific configuration
    uvx mcp-cli.py init <project-name>
    uvx mcp-cli.py init .

Or install globally:
    uv tool install --from mcp-cli.py mcp-cli
    mcp init                    # Global configuration
    mcp init <project-name>     # Project-specific
    mcp init .                  # Current directory
"""

__version__ = "0.0.8"

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
        "requires_cli": True,
    },
    "continue": {
        "name": "Continue",
        "folder": ".continue/",
        "install_url": None,  # IDE-based, no CLI check needed
        "requires_cli": False,
    },
    "copilot": {
        "name": "GitHub Copilot",
        "folder": ".github/",
        "install_url": None,  # IDE-based, no CLI check needed
        "requires_cli": False,
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

app = typer.Typer(
    name="MCP-CLI",
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
        agent: The agent to configure (copilot, continue, kiro, cursor, qoder, lmstudio, claude, gemini)
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
        config = {"servers": {}, "inputs": []}
        
        for server in selected_servers:
            mcp_config = server.get("mcp", {})
            # Copy the internal server data exactly as it is, just change the top-level key
            config["servers"].update(mcp_config)
    else:
        # Continue, Kiro, Cursor, Qoder, LM Studio, Claude Agent and other agents format: {"mcpServers": {...}}
        config = {"mcpServers": {}}
        
        for server in selected_servers:
            mcp_config = server.get("mcp", {})
            config["mcpServers"].update(mcp_config)
    
    return config

def save_mcp_config(config: Dict[str, Any], config_path: Path, agent: str) -> bool:
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
                console.print(f"[yellow]Found existing configuration, merging entries...[/yellow]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read existing config: {e}[/yellow]")
                if not Confirm.ask(f"Continue and merge the file?"):
                    return False
        
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
            console.print(f"[green]Adding {len(new_servers)} servers to existing configuration:[/green]")
            for server in new_servers:
                console.print(f"  • {server}")
        
        # Save merged configuration
        with open(config_path, 'w') as f:
            json.dump(existing_config, f, indent=2)
        
        console.print(f"[green]✓ MCP configuration saved to {config_path}[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]Failed to save configuration: {str(e)}[/red]")
        return False



@app.command()
def init(
    project_name: Optional[str] = typer.Argument(None, help="Name of the project to initialize (use '.' for current directory, omit for global configuration)"),
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Agent to configure (copilot, continue, kiro, cursor, qoder, lmstudio, claude, gemini)"),
    version: str = typer.Option(None, "--version", "-v", help="Version to download (defaults to current package version)"),
):
    """Initialize MCP configuration in a project directory or globally."""
    show_banner()
    
    # Determine if this is global configuration (when no project name is provided)
    is_global = project_name is None
    
    if is_global:
        # Global configuration mode
        project_info = None
        project_path = None
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
    servers = download_mcp_servers(version)
    if not servers:
        raise typer.Exit(1)
    
    console.print(f"[green]✓ Downloaded {len(servers)} MCP servers[/green]")
    
    # Select agent if not provided
    if not agent:
        agent = select_agent(project_info)
        if not agent:
            console.print("[red]No agent selected. Exiting.[/red]")
            raise typer.Exit(1)
    
    if agent not in AGENT_CONFIG:
        console.print(f"[red]Unknown agent: {agent}. Available: {', '.join(AGENT_CONFIG.keys())}[/red]")
        raise typer.Exit(1)
    
    console.print(f"\n[bold green]Selected Agent: {AGENT_CONFIG[agent]['name']}[/bold green]")
    
    # Check if agent supports project-level configuration
    if agent == "qoder":
        console.print(f"[yellow]⚠️  Note: Qoder does not support project-level MCP configuration.[/yellow]")
        console.print(f"[yellow]   Configuration will be saved to global Qoder settings instead.[/yellow]")
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
    
    # Select MCP servers
    selected_servers = select_mcp_servers(servers, agent, project_info)
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
    if is_global or agent == "qoder" or agent == "lmstudio":
        config_path = get_mcp_config_path(agent)  # Global path
    else:
        config_path = get_mcp_config_path(agent, project_path)  # Project-specific path
    
    # Save configuration
    if save_mcp_config(config, config_path, agent):
        if is_global:
            console.print(f"\n[bold green]🎉 MCP global configuration completed successfully![/bold green]")
            console.print(f"[dim]Global configuration saved to: {config_path}[/dim]")
            
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
        else:
            console.print(f"\n[bold green]🎉 MCP project initialization completed successfully![/bold green]")
            
            if agent == "qoder":
                console.print(f"[dim]Global configuration saved to: {config_path}[/dim]")
            else:
                console.print(f"[dim]Project configuration saved to: {config_path}[/dim]")
            
            # Show next steps for project configuration
            console.print(f"\n[bold cyan]Next steps:[/bold cyan]")
            console.print(f"1. Open your project in {AGENT_CONFIG[agent]['name']}")
            
            if agent == "qoder":
                console.print(f"2. The MCP servers will be loaded from global Qoder settings")
                console.print(f"3. Open the project in Qoder IDE")
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
        raise typer.Exit(1)

@app.callback()
def callback(ctx: typer.Context):
    """Show banner when no subcommand is provided."""
    if ctx.invoked_subcommand is None and "--help" not in sys.argv and "-h" not in sys.argv:
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