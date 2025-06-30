"""
Claude Code Interface for Blender MCP Client

Provides functions that can be called directly from Claude Code environment
to interact with Blender through the MCP server.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from .mcp_client import BlenderMCPClient
from .claude_integration import ClaudeBlenderIntegration

logger = logging.getLogger("BlenderMCPClient.ClaudeCode")

# Global client instance for persistent connections
_global_client: Optional[BlenderMCPClient] = None
_global_integration: Optional[ClaudeBlenderIntegration] = None

async def _get_client(host: str = "localhost", port: int = 9876) -> BlenderMCPClient:
    """Get or create a global client instance"""
    global _global_client
    
    if _global_client is None or not _global_client.connected:
        _global_client = BlenderMCPClient(host, port)
        await _global_client.connect()
    
    return _global_client

async def _get_integration(host: str = "localhost", port: int = 9876) -> ClaudeBlenderIntegration:
    """Get or create a global integration instance"""
    global _global_integration
    
    if _global_integration is None:
        client = await _get_client(host, port)
        _global_integration = ClaudeBlenderIntegration(client)
    
    return _global_integration

# Direct tool call functions
async def blender_get_scene_info(host: str = "localhost", port: int = 9876) -> str:
    """Get detailed information about the current Blender scene"""
    try:
        client = await _get_client(host, port)
        return await client.get_scene_info()
    except Exception as e:
        return f"Error getting scene info: {e}"

async def blender_get_object_info(object_name: str, host: str = "localhost", port: int = 9876) -> str:
    """Get information about a specific object in Blender"""
    try:
        client = await _get_client(host, port)
        return await client.get_object_info(object_name)
    except Exception as e:
        return f"Error getting object info: {e}"

async def blender_take_screenshot(max_size: int = 800, host: str = "localhost", port: int = 9876) -> str:
    """Take a screenshot of the Blender viewport"""
    try:
        client = await _get_client(host, port)
        result = await client.get_viewport_screenshot(max_size)
        return f"Screenshot captured successfully: {result}"
    except Exception as e:
        return f"Error taking screenshot: {e}"

async def blender_execute_code(code: str, host: str = "localhost", port: int = 9876) -> str:
    """Execute Python code in Blender"""
    try:
        client = await _get_client(host, port)
        return await client.execute_blender_code(code)
    except Exception as e:
        return f"Error executing code: {e}"

async def blender_search_polyhaven(asset_type: str = "textures", categories: str = None, 
                                 host: str = "localhost", port: int = 9876) -> str:
    """Search PolyHaven assets"""
    try:
        client = await _get_client(host, port)
        return await client.search_polyhaven_assets(asset_type, categories)
    except Exception as e:
        return f"Error searching PolyHaven: {e}"

async def blender_search_sketchfab(query: str, categories: str = None, count: int = 20,
                                 host: str = "localhost", port: int = 9876) -> str:
    """Search Sketchfab models"""
    try:
        client = await _get_client(host, port)
        return await client.search_sketchfab_models(query, categories, count)
    except Exception as e:
        return f"Error searching Sketchfab: {e}"

async def blender_generate_model(text_prompt: str, bbox_condition: List[float] = None,
                                host: str = "localhost", port: int = 9876) -> str:
    """Generate 3D model using Hyper3D"""
    try:
        client = await _get_client(host, port)
        return await client.generate_hyper3d_model(text_prompt, bbox_condition)
    except Exception as e:
        return f"Error generating model: {e}"

# Natural language interface
async def blender_process_prompt(prompt: str, host: str = "localhost", port: int = 9876) -> Dict[str, Any]:
    """Process a natural language prompt and execute Blender actions"""
    try:
        integration = await _get_integration(host, port)
        return await integration.process_prompt(prompt)
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to process prompt"
        }

# Utility functions
async def blender_list_tools(host: str = "localhost", port: int = 9876) -> List[str]:
    """Get list of available Blender MCP tools"""
    try:
        client = await _get_client(host, port)
        return client.get_available_tools()
    except Exception as e:
        return [f"Error: {e}"]

async def blender_get_tool_info(tool_name: str, host: str = "localhost", port: int = 9876) -> Dict[str, Any]:
    """Get detailed information about a specific tool"""
    try:
        client = await _get_client(host, port)
        info = client.get_tool_info(tool_name)
        return info if info else {"error": f"Tool '{tool_name}' not found"}
    except Exception as e:
        return {"error": str(e)}

async def blender_disconnect():
    """Disconnect from the Blender MCP server"""
    global _global_client, _global_integration
    
    if _global_client:
        await _global_client.disconnect()
        _global_client = None
    
    _global_integration = None

# Synchronous wrappers for easier use in Claude Code
def run_blender_prompt(prompt: str, host: str = "localhost", port: int = 9876) -> Dict[str, Any]:
    """Synchronous wrapper for processing Blender prompts"""
    return asyncio.run(blender_process_prompt(prompt, host, port))

def run_blender_scene_info(host: str = "localhost", port: int = 9876) -> str:
    """Synchronous wrapper for getting scene info"""
    return asyncio.run(blender_get_scene_info(host, port))

def run_blender_screenshot(max_size: int = 800, host: str = "localhost", port: int = 9876) -> str:
    """Synchronous wrapper for taking screenshots"""
    return asyncio.run(blender_take_screenshot(max_size, host, port))

def run_blender_code(code: str, host: str = "localhost", port: int = 9876) -> str:
    """Synchronous wrapper for executing Blender code"""
    return asyncio.run(blender_execute_code(code, host, port))

def run_blender_search_polyhaven(asset_type: str = "textures", categories: str = None,
                                host: str = "localhost", port: int = 9876) -> str:
    """Synchronous wrapper for PolyHaven search"""
    return asyncio.run(blender_search_polyhaven(asset_type, categories, host, port))

def run_blender_search_sketchfab(query: str, categories: str = None, count: int = 20,
                                host: str = "localhost", port: int = 9876) -> str:
    """Synchronous wrapper for Sketchfab search"""
    return asyncio.run(blender_search_sketchfab(query, categories, count, host, port))

def run_blender_generate_model(text_prompt: str, bbox_condition: List[float] = None,
                              host: str = "localhost", port: int = 9876) -> str:
    """Synchronous wrapper for model generation"""
    return asyncio.run(blender_generate_model(text_prompt, bbox_condition, host, port))

def run_blender_list_tools(host: str = "localhost", port: int = 9876) -> List[str]:
    """Synchronous wrapper for listing tools"""
    return asyncio.run(blender_list_tools(host, port))

# Example usage functions
def blender_examples():
    """Show example usage of the Blender MCP client"""
    examples = {
        "Get scene information": "run_blender_scene_info()",
        "Take a screenshot": "run_blender_screenshot()",
        "Create a cube": "run_blender_code('import bpy; bpy.ops.mesh.primitive_cube_add()')",
        "Natural language": "run_blender_prompt('Create a red cube and take a screenshot')",
        "Search textures": "run_blender_search_polyhaven('textures')",
        "Search models": "run_blender_search_sketchfab('chair')",
        "Generate model": "run_blender_generate_model('a wooden chair')",
        "List tools": "run_blender_list_tools()"
    }
    
    print("🎨 Blender MCP Client Examples:")
    print("=" * 50)
    
    for description, code in examples.items():
        print(f"\n📌 {description}:")
        print(f"   {code}")
    
    print("\n💡 Tips:")
    print("   - All functions accept optional host and port parameters")
    print("   - Use run_blender_prompt() for natural language commands")
    print("   - Functions return strings or dictionaries with results")
    print("   - Call blender_disconnect() when done to clean up connections")

# Auto-discovery function
def discover_blender_capabilities(host: str = "localhost", port: int = 9876) -> Dict[str, Any]:
    """Discover and summarize Blender server capabilities"""
    try:
        tools = run_blender_list_tools(host, port)
        scene_info = run_blender_scene_info(host, port)
        
        return {
            "connected": True,
            "server": f"{host}:{port}",
            "available_tools": len(tools),
            "tools": tools,
            "scene_accessible": "error" not in scene_info.lower(),
            "capabilities": {
                "scene_info": "get_scene_info" in tools,
                "screenshots": "get_viewport_screenshot" in tools,
                "code_execution": "execute_blender_code" in tools,
                "polyhaven_search": "search_polyhaven_assets" in tools,
                "sketchfab_search": "search_sketchfab_models" in tools,
                "ai_generation": any("hyper3d" in tool for tool in tools)
            }
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "server": f"{host}:{port}"
        }