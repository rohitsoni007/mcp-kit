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
    uvx mcp-cli.py init <project-name>
    uvx mcp-cli.py init .
    uvx mcp-cli.py init --here

Or install globally:
    uv tool install --from mcp-cli.py mcp-cli
    mcp init <project-name>
    mcp init .
    mcp init --here
"""

__version__ = "0.0.5"

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
    "copilot": {
        "name": "GitHub Copilot",
        "folder": ".github/",
        "install_url": None,  # IDE-based, no CLI check needed
        "requires_cli": False,
    },
    "continue": {
        "name": "Continue",
        "folder": ".continue/",
        "install_url": None,  # IDE-based, no CLI check needed
        "requires_cli": False,
    },
    "kiro": {
        "name": "Kiro",
        "folder": ".kiro/",
        "install_url": "https://kiro.dev",
        "requires_cli": False,
    },
    "cursor": {
        "name": "Cursor",
        "folder": ".cursor/",
        "install_url": "https://cursor.sh",
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

def get_mcp_config_path(agent: str = "copilot") -> Path:
    """Get the MCP configuration path based on the agent and operating system."""
    if agent == "continue": 
        # Continue uses ~/.continue/mcpServers/mcp.json
        return Path.home() / ".continue" / "mcpServers" / "mcp.json"
    elif agent == "kiro":
        # Kiro uses ~/.kiro/settings/mcp.json
        return Path.home() / ".kiro" / "settings" / "mcp.json"
    elif agent == "cursor":
        # Cursor uses ~/.cursor/mcp.json
        return Path.home() / ".cursor" / "mcp.json"
    elif agent == "qoder":
        # Qoder uses ~/AppData/Roaming/Qoder/SharedClientCache/mcp.json on Windows
        system = platform.system().lower()
        if system == "windows":
            return Path.home() / "AppData" / "Roaming" / "Qoder" / "SharedClientCache" / "mcp.json"
        else:
            # For non-Windows systems, use a similar pattern in user config
            return Path.home() / ".config" / "Qoder" / "SharedClientCache" / "mcp.json"
    
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

def select_agent() -> Optional[str]:
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

def select_mcp_servers(servers: List[Dict[str, Any]], agent: str) -> List[Dict[str, Any]]:
    """Interactive MCP server selection with keyboard navigation, table format, and pagination."""
    selected_indices = set()
    current_index = 0
    current_page = 0
    items_per_page = 10  # Show 10 servers per page
    
    def get_page_items():
        """Get items for the current page."""
        start_idx = current_page * items_per_page
        end_idx = min(start_idx + items_per_page, len(servers))
        return servers[start_idx:end_idx], start_idx, end_idx
    
    def get_total_pages():
        """Calculate total number of pages."""
        return (len(servers) + items_per_page - 1) // items_per_page
    
    def render_server_table():
        """Render the MCP server selection interface using a table with pagination."""
        try:
            console.clear()
        except Exception:
            # Fallback if clear doesn't work
            console.print("\n" * 50)
        
        # Show banner
        show_banner()
        
        # Show selected agent
        agent_info = f"Selected Agent: {agent} ({AGENT_CONFIG[agent]['name']})"
        console.print(Align.center(Text(agent_info, style="bold green")))
        console.print()
        
        # Get current page items
        page_items, start_idx, end_idx = get_page_items()
        total_pages = get_total_pages()
        
        # Create table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Selector", style="cyan", width=3)
        table.add_column("Checkbox", style="white", width=3)
        table.add_column("Server", style="white", min_width=20)
        table.add_column("Description", style="dim", max_width=60)
        
        # Add rows to table for current page
        for i, server in enumerate(page_items):
            global_index = start_idx + i
            
            if global_index == current_index:
                # Highlighted selection
                selector = "▶"
                checkbox_style = "bold cyan"
                server_style = "bold cyan"
                desc_style = "cyan"
            else:
                # Normal item
                selector = " "
                if global_index in selected_indices:
                    checkbox_style = "bright_green"
                    server_style = "bright_green"
                    desc_style = "green"
                else:
                    checkbox_style = "white"
                    server_style = "white"
                    desc_style = "dim"
            
            checkbox = "☑" if global_index in selected_indices else "☐"
            
            # Truncate description if too long
            description = server['description']
            if len(description) > 60:
                description = description[:57] + "..."
            
            table.add_row(
                Text(selector, style="cyan"),
                Text(checkbox, style=checkbox_style),
                Text(server['name'], style=server_style),
                Text(description, style=desc_style)
            )
        
        # Create status info for the panel subtitle
        selected_count = len(selected_indices)
        status_info = f"Selected: {selected_count} server{'s' if selected_count != 1 else ''}"
        
        if total_pages > 1:
            status_info += f" | Page {current_page + 1} of {total_pages} | Showing {start_idx + 1}-{end_idx} of {len(servers)}"
        
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
        ]
        
        if total_pages > 1:
            help_lines.append("Use ←/→ or PgUp/PgDn to change pages")
        
        help_lines.append("A=select all, N=select none")
        
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
                    current_index = len(servers) - 1
                    current_page = get_total_pages() - 1
                render_server_table()
                
            elif key == readchar.key.DOWN:
                if current_index < len(servers) - 1:
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
                if current_index in selected_indices:
                    selected_indices.remove(current_index)
                else:
                    selected_indices.add(current_index)
                render_server_table()
                
            elif key == readchar.key.ENTER or key == '\r' or key == '\n':
                if selected_indices:
                    return [servers[i] for i in sorted(selected_indices)]
                else:
                    # If nothing selected, select the current one
                    return [servers[current_index]]
                    
            elif key == readchar.key.ESC or key == '\x1b':
                return []
                
            elif key.lower() == 'q':
                return []
                
            elif key.lower() == 'a':  # 'a' to select all
                selected_indices = set(range(len(servers)))
                render_server_table()
                
            elif key.lower() == 'n':  # 'n' to select none
                selected_indices.clear()
                render_server_table()
                
        except KeyboardInterrupt:
            return []
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
        # Continue, Kiro, Cursor, Qoder and other agents format: {"mcpServers": {...}}
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
            # Continue, Kiro, Cursor, Qoder and other agents format
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
def download(
    version: str = typer.Option(None, "--version", "-v", help="Version to download (defaults to current package version)"),
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Agent to configure (copilot, continue, kiro, cursor, qoder)"),
):
    """Download MCP servers and configure for selected agent."""
    show_banner()
    
    # Download MCP servers
    servers = download_mcp_servers(version)
    if not servers:
        raise typer.Exit(1)
    
    console.print(f"[green]✓ Downloaded {len(servers)} MCP servers[/green]")
    
    # Select agent if not provided
    if not agent:
        agent = select_agent()
        if not agent:
            console.print("[red]No agent selected. Exiting.[/red]")
            raise typer.Exit(1)
    
    if agent not in AGENT_CONFIG:
        console.print(f"[red]Unknown agent: {agent}. Available: {', '.join(AGENT_CONFIG.keys())}[/red]")
        raise typer.Exit(1)
    
    console.print(f"\n[bold green]Selected Agent: {AGENT_CONFIG[agent]['name']}[/bold green]")
    
    # Select MCP servers
    selected_servers = select_mcp_servers(servers, agent)
    console.print(f"\n[bold green]Selected {len(selected_servers)} MCP servers[/bold green]")
    
    # Create configuration
    config = create_mcp_config(selected_servers, agent)
    
    # Get configuration path based on selected agent
    config_path = get_mcp_config_path(agent)
    
    # Save configuration
    if save_mcp_config(config, config_path, agent):
        console.print(f"\n[bold green]🎉 MCP configuration completed successfully![/bold green]")
        console.print(f"[dim]Configuration saved to: {config_path}[/dim]")
    else:
        raise typer.Exit(1)

@app.command()
def init(project_name: str = typer.Argument(..., help="Name of the project to initialize")):
    """Initialize a new MCP project (existing functionality)."""
    show_banner()
    console.print(f"[bold green]Initializing MCP project: {project_name}[/bold green]")
    # Add existing init functionality here
    console.print("[yellow]Init functionality not yet implemented[/yellow]")

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