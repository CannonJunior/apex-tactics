"""
Fixed CLI with proper asyncio.run() wrappers
"""

import asyncio
import click
import json
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Apply asyncio wrapper to all async CLI commands
def async_command(f):
    """Decorator to handle async functions in Click commands"""
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

@click.group()
@click.option('--host', default='localhost', help='Blender MCP server host')
@click.option('--port', default=9876, help='Blender MCP server port')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, host, port, verbose):
    """Blender MCP Client - Connect to Blender through Model Context Protocol"""
    ctx.ensure_object(dict)
    ctx.obj['host'] = host
    ctx.obj['port'] = port
    ctx.obj['verbose'] = verbose
    
    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)

@cli.command()
@click.pass_context
@async_command
async def status(ctx):
    """Check connection status to Blender MCP server"""
    from blender_mcp_client.mcp_client import BlenderMCPClient
    
    console = Console()
    host = ctx.obj['host']
    port = ctx.obj['port']
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Connecting to Blender MCP server...", total=None)
        
        try:
            client = BlenderMCPClient(host, port)
            connected = await client.connect()
            
            if connected:
                progress.update(task, description="✅ Connected! Getting server info...")
                
                tools = client.get_available_tools()
                await client.disconnect()
                
                # Display status
                panel = Panel.fit(
                    f"[green]✅ Connected to Blender MCP Server[/green]\n"
                    f"Host: {host}:{port}\n"
                    f"Available tools: {len(tools)}\n"
                    f"Session ID: {client.session_id}",
                    title="Connection Status"
                )
                console.print(panel)
                
                # Show available tools
                if tools:
                    table = Table(title="Available Tools")
                    table.add_column("Tool Name", style="cyan")
                    table.add_column("Description", style="green")
                    
                    for tool_name in tools:
                        tool_info = client.get_tool_info(tool_name)
                        description = tool_info.get('description', 'No description') if tool_info else 'No description'
                        table.add_row(tool_name, description)
                    
                    console.print(table)
                
            else:
                console.print("[red]❌ Failed to connect to Blender MCP server[/red]")
                sys.exit(1)
                
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
            sys.exit(1)

if __name__ == '__main__':
    cli()