#!/usr/bin/env python3
"""
Test script for Blender MCP Client
"""

import sys
import os
import asyncio

# Add mcp-client to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mcp-client', 'src'))

async def test_mcp_client():
    """Test the MCP client components"""
    print("🧪 Testing Blender MCP Client")
    print("=" * 50)
    
    try:
        # Test imports
        print("\n📦 Testing imports...")
        from blender_mcp_client.mcp_client import BlenderMCPClient
        from blender_mcp_client.claude_integration import ClaudeBlenderIntegration
        from blender_mcp_client.claude_code_interface import discover_blender_capabilities
        print("✅ All imports successful!")
        
        # Test connection to Blender MCP server
        print("\n🔌 Testing connection to Blender MCP server...")
        try:
            client = BlenderMCPClient("localhost", 9876)
            connected = await client.connect()
            
            if connected:
                print("✅ Connected to Blender MCP server!")
                
                # Test getting available tools
                tools = client.get_available_tools()
                print(f"✅ Found {len(tools)} available tools")
                
                if tools:
                    print("📋 Available tools:")
                    for tool in tools[:5]:  # Show first 5 tools
                        print(f"   • {tool}")
                    if len(tools) > 5:
                        print(f"   ... and {len(tools) - 5} more")
                
                await client.disconnect()
                print("✅ Disconnected successfully")
                
            else:
                print("❌ Failed to connect to Blender MCP server")
                print("   Make sure Blender MCP server is running on port 9876")
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            print("   This is expected if Blender MCP server is not running")
        
        # Test Claude Code interface functions
        print("\n🎭 Testing Claude Code interface...")
        try:
            capabilities = discover_blender_capabilities()
            if capabilities.get("connected"):
                print("✅ Claude Code interface working!")
                print(f"   Server: {capabilities['server']}")
                print(f"   Tools available: {capabilities['available_tools']}")
                print(f"   Scene accessible: {capabilities['scene_accessible']}")
            else:
                print("⚠️  Claude Code interface loaded but server not connected")
                print(f"   Error: {capabilities.get('error', 'Unknown')}")
        except Exception as e:
            print(f"❌ Claude Code interface error: {e}")
        
        # Test CLI imports
        print("\n💻 Testing CLI components...")
        try:
            from blender_mcp_client.cli import cli
            print("✅ CLI interface imported successfully!")
        except Exception as e:
            print(f"❌ CLI import error: {e}")
        
        # Test Ollama integration (optional)
        print("\n🤖 Testing Ollama integration...")
        try:
            from blender_mcp_client.ollama_integration import OllamaClient
            
            ollama_client = OllamaClient("http://localhost:11434")
            ollama_connected = await ollama_client.check_connection()
            
            if ollama_connected:
                print("✅ Ollama server is available!")
                models = await ollama_client.list_models()
                print(f"   Available models: {len(models)}")
                for model in models[:3]:  # Show first 3 models
                    print(f"   • {model.name}")
                await ollama_client.close()
            else:
                print("⚠️  Ollama server not available (this is optional)")
                
        except Exception as e:
            print(f"⚠️  Ollama integration error: {e} (this is optional)")
        
        print("\n🎉 Test completed!")
        print("\nNext steps:")
        print("1. Make sure Blender MCP server is running on port 9876")
        print("2. Try: python -c \"from mcp-client.src.blender_mcp_client.claude_code_interface import *; blender_examples()\"")
        print("3. Try CLI: cd mcp-client && python -m blender_mcp_client.cli status")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_client())