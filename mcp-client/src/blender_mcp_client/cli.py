"""
Command-line interface for Blender MCP Client

Provides a rich CLI interface for interacting with Blender through MCP
with support for both direct commands and AI-assisted operations.
"""

import asyncio
import click
import json
import sys
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from .mcp_client import BlenderMCPClient, create_client
from .claude_integration import ClaudeBlenderIntegration, process_claude_prompt
from .ollama_integration import OllamaClient, OllamaBlenderIntegration, create_ollama_blender_session

console = Console()

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
def status(ctx):
    """Check connection status to Blender MCP server"""
    async def _status():
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
    
    asyncio.run(_status())

@cli.command()
@click.argument('prompt', required=False)
@click.option('--file', '-f', help='Read prompt from file')
@click.pass_context
def prompt(ctx, prompt, file):
    """Process a natural language prompt with Claude-style integration"""
    async def _prompt():
        host = ctx.obj['host']
        port = ctx.obj['port']
        user_prompt = prompt
        
        # Get prompt from argument or file
        if file:
            try:
                with open(file, 'r') as f:
                    user_prompt = f.read().strip()
            except Exception as e:
                console.print(f"[red]❌ Error reading file: {e}[/red]")
                return
        
        if not user_prompt:
            user_prompt = click.prompt("Enter your prompt")
        
        console.print(f"\n🎯 Processing prompt: [cyan]{user_prompt}[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Connecting and processing...", total=None)
            
            try:
                result = await process_claude_prompt(user_prompt, host, port)
                
                if result['success']:
                    progress.update(task, description="✅ Completed!")
                    
                    console.print("\n[green]✅ Success![/green]")
                    
                    if 'results' in result:
                        for action_result in result['results']:
                            if action_result['success']:
                                console.print(f"   ✅ {action_result['action']}")
                                if 'result' in action_result and action_result['result']:
                                    # Format the result nicely
                                    result_text = str(action_result['result'])
                                    if len(result_text) > 200:
                                        result_text = result_text[:200] + "..."
                                    console.print(f"      [dim]{result_text}[/dim]")
                            else:
                                console.print(f"   ❌ {action_result['action']}: {action_result.get('error', 'Unknown error')}")
                else:
                    console.print(f"[red]❌ Failed: {result.get('message', 'Unknown error')}[/red]")
                    if 'available_actions' in result:
                        console.print("\n[yellow]Available actions:[/yellow]")
                        for action in result['available_actions']:
                            console.print(f"   • {action}")
                            
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")
    
    asyncio.run(_prompt())

@cli.command()
@click.option('--model', default='llama3.2', help='Ollama model to use')
@click.option('--ollama-url', default='http://localhost:11434', help='Ollama server URL')
@click.option('--interactive', '-i', is_flag=True, help='Start interactive session')
@click.argument('prompt', required=False)
@click.pass_context
def ai(ctx, model, ollama_url, interactive, prompt):
    """Use local AI (Ollama) to interact with Blender"""
    async def _ai():
        host = ctx.obj['host']
        port = ctx.obj['port']
        
        if interactive:
            # Start interactive session
            console.print(f"\n🚀 Starting AI-powered Blender session")
            console.print(f"   Blender MCP: {host}:{port}")
            console.print(f"   Ollama: {ollama_url}")
            console.print(f"   Model: {model}")
            
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("Initializing AI session...", total=None)
                    
                    session = await create_ollama_blender_session(
                        blender_host=host,
                        blender_port=port,
                        ollama_url=ollama_url,
                        model=model
                    )
                    
                    progress.update(task, description="✅ Session ready!")
                    
                    await session.interactive_session(model)
                    
            except Exception as e:
                console.print(f"[red]❌ Error starting AI session: {e}[/red]")
                return
        
        elif prompt:
            # Process single prompt with AI
            console.print(f"\n🤖 Processing with {model}: [cyan]{prompt}[/cyan]")
            
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("Connecting and processing...", total=None)
                    
                    session = await create_ollama_blender_session(
                        blender_host=host,
                        blender_port=port,
                        ollama_url=ollama_url,
                        model=model
                    )
                    
                    result = await session.process_prompt_with_ai(prompt, model)
                    
                    progress.update(task, description="✅ Completed!")
                    
                    # Display AI response
                    console.print(f"\n🤖 {model}:")
                    console.print(Panel(result['ai_response'], title="AI Response"))
                    
                    # Display Blender results
                    if result['blender_results']:
                        if result['blender_results']['success']:
                            console.print("\n[green]⚡ Blender Actions Executed:[/green]")
                            for action_result in result['blender_results'].get('results', []):
                                if action_result['success']:
                                    console.print(f"   ✅ {action_result['action']}")
                                else:
                                    console.print(f"   ❌ {action_result['action']}: {action_result.get('error', 'Unknown error')}")
                        else:
                            console.print(f"[red]❌ Blender Error: {result['blender_results'].get('error', 'Unknown error')}[/red]")
                    
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")
        
        else:
            console.print("[yellow]Please provide a prompt or use --interactive flag[/yellow]")
    
    asyncio.run(_ai())

@cli.command()
@click.pass_context
def tools(ctx):
    """List all available tools on the Blender MCP server"""
    async def _tools():
        host = ctx.obj['host']
        port = ctx.obj['port']
        
        try:
            client = await create_client(host, port)
            tools = client.get_available_tools()
            
            if not tools:
                console.print("[yellow]No tools available or server not connected[/yellow]")
                return
            
            table = Table(title=f"Blender MCP Tools ({len(tools)} available)")
            table.add_column("Tool Name", style="cyan", no_wrap=True)
            table.add_column("Description", style="green")
            table.add_column("Parameters", style="yellow")
            
            for tool_name in tools:
                tool_info = client.get_tool_info(tool_name)
                
                if tool_info:
                    description = tool_info.get('description', 'No description')
                    
                    # Extract parameter info
                    input_schema = tool_info.get('inputSchema', {})
                    properties = input_schema.get('properties', {})
                    
                    if properties:
                        params = []
                        for param_name, param_info in properties.items():
                            param_type = param_info.get('type', 'unknown')
                            required = param_name in input_schema.get('required', [])
                            req_marker = '*' if required else ''
                            params.append(f"{param_name}{req_marker}: {param_type}")
                        param_text = "\n".join(params)
                    else:
                        param_text = "None"
                    
                    table.add_row(tool_name, description, param_text)
                else:
                    table.add_row(tool_name, "No information available", "Unknown")
            
            console.print(table)
            await client.disconnect()
            
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
    
    asyncio.run(_tools())

@cli.command()
@click.argument('tool_name')
@click.option('--params', '-p', help='Tool parameters as JSON string')
@click.option('--param', multiple=True, help='Individual parameter as key=value (can be used multiple times)')
@click.pass_context
def call(ctx, tool_name, params, param):
    """Call a specific tool on the Blender MCP server"""
    async def _call():
        host = ctx.obj['host']
        port = ctx.obj['port']
        
        # Parse parameters
        tool_params = {}
        
        if params:
            try:
                tool_params = json.loads(params)
            except json.JSONDecodeError as e:
                console.print(f"[red]❌ Invalid JSON in params: {e}[/red]")
                return
        
        # Add individual parameters
        for p in param:
            if '=' not in p:
                console.print(f"[red]❌ Invalid parameter format: {p}. Use key=value[/red]")
                return
            key, value = p.split('=', 1)
            
            # Try to parse value as JSON, otherwise use as string
            try:
                tool_params[key] = json.loads(value)
            except json.JSONDecodeError:
                tool_params[key] = value
        
        console.print(f"\n🔧 Calling tool: [cyan]{tool_name}[/cyan]")
        if tool_params:
            console.print(f"Parameters: {json.dumps(tool_params, indent=2)}")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Executing tool...", total=None)
                
                client = await create_client(host, port)
            result = await client.call_tool(tool_name, tool_params)
            await client.disconnect()
            
            progress.update(task, description="✅ Completed!")
            
            console.print("\n[green]✅ Tool executed successfully![/green]")
            
            # Format and display result
            if isinstance(result, dict):
                formatted_result = json.dumps(result, indent=2)
            else:
                formatted_result = str(result)
            
                console.print(Panel(formatted_result, title="Result"))
                
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
    
    asyncio.run(_call())

@cli.command()
@click.option('--ollama-url', default='http://localhost:11434', help='Ollama server URL')
@click.pass_context
def models(ctx, ollama_url):
    """List available Ollama models"""
    async def _models():
        try:
            ollama_client = OllamaClient(ollama_url)
            
            if not await ollama_client.check_connection():
                console.print(f"[red]❌ Cannot connect to Ollama at {ollama_url}[/red]")
                return
            
            models = await ollama_client.list_models()
            
            if not models:
                console.print("[yellow]No Ollama models found[/yellow]")
                return
            
            table = Table(title=f"Available Ollama Models ({len(models)})")
            table.add_column("Model Name", style="cyan")
            table.add_column("Size", style="green")
            table.add_column("Modified", style="yellow")
            
            for model in models:
                # Format size in a more readable way
                size = model.size
                if isinstance(size, int):
                    if size > 1024**3:  # GB
                        size_str = f"{size / (1024**3):.1f} GB"
                    elif size > 1024**2:  # MB
                        size_str = f"{size / (1024**2):.1f} MB"
                    else:
                        size_str = f"{size} bytes"
                else:
                    size_str = str(size)
                
                table.add_row(model.name, size_str, model.modified)
            
            console.print(table)
            await ollama_client.close()
            
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
    
    asyncio.run(_models())

def main():
    """Main entry point for the CLI"""
    cli()

if __name__ == '__main__':
    main()