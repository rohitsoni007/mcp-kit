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

__version__ = "0.0.4"

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
    }
}

BANNER = r"""
 __  __  ____  ____     ____  _     ___ 
|  \/  |/ ___||  _ \   / ___|| |   |_ _|
| |\/| | |    | |_) | | |    | |    | | 
| |  | | |___ |  __/  | |___ | |___ | | 
|_|  |_|\____||_|      \____||_____|___|
"""

TAGLINE = "MCP Kit - SETUP MCP"


    
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
    colors = ["bright_blue", "blue", "cyan", "bright_cyan", "white", "bright_white"]

    styled_banner = Text()
    for i, line in enumerate(banner_lines):
        color = colors[i % len(colors)]
        styled_banner.append(line + "\n", style=color)

    console.print(Align.center(styled_banner))
    console.print(Align.center(Text(TAGLINE, style="italic bright_yellow")))
    console.print()

def get_mcp_config_path() -> Path:
    """Get the MCP configuration path based on the operating system."""
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
    """Interactive agent selection."""
    console.print("\n[bold cyan]Available Agents:[/bold cyan]")
    
    agents = list(AGENT_CONFIG.keys())
    for i, agent_key in enumerate(agents, 1):
        agent = AGENT_CONFIG[agent_key]
        console.print(f"  {i}. {agent['name']}")
    
    while True:
        try:
            choice = Prompt.ask(
                "\nSelect an agent",
                choices=[str(i) for i in range(1, len(agents) + 1)],
                default="1"
            )
            return agents[int(choice) - 1]
        except (ValueError, IndexError):
            console.print("[red]Invalid selection. Please try again.[/red]")

def select_mcp_servers(servers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Interactive MCP server selection."""
    console.print("\n[bold cyan]Available MCP Servers:[/bold cyan]")
    
    for i, server in enumerate(servers, 1):
        console.print(f"  {i}. {server['name']} - {server['description']}")
    
    selected_servers = []
    
    while True:
        try:
            choices = Prompt.ask(
                "\nSelect MCP servers (comma-separated numbers, e.g., 1,3,5)",
                default="1"
            )
            
            indices = [int(x.strip()) - 1 for x in choices.split(",")]
            
            # Validate indices
            for idx in indices:
                if idx < 0 or idx >= len(servers):
                    raise ValueError(f"Invalid server number: {idx + 1}")
            
            selected_servers = [servers[idx] for idx in indices]
            break
            
        except ValueError as e:
            console.print(f"[red]Invalid selection: {str(e)}. Please try again.[/red]")
    
    return selected_servers

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
        # Continue and other agents format: {"mcpServers": {...}}
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
                if not Confirm.ask(f"Continue and overwrite the file?"):
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
            # Continue and other agents format
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
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Agent to configure (copilot, continue)"),
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
    selected_servers = select_mcp_servers(servers)
    console.print(f"\n[bold green]Selected {len(selected_servers)} MCP servers[/bold green]")
    
    # Create configuration
    config = create_mcp_config(selected_servers, agent)
    
    # Get configuration path
    config_path = get_mcp_config_path()
    
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