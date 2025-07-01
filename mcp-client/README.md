# Blender MCP Client

A comprehensive client for connecting to Blender MCP server with support for Claude Code integration and local AI models via Ollama.

## Features

- 🔌 **MCP Protocol Support**: Full WebSocket-based MCP client implementation
- 🤖 **Claude Code Integration**: Natural language prompts processed in Claude Code environment  
- 🧠 **Ollama Integration**: Local AI models for command-line interaction
- 🛠️ **Rich CLI Interface**: Beautiful command-line interface with progress indicators
- 📸 **Blender Tools**: Scene info, screenshots, code execution, asset search, AI generation

## Installation

From the mcp-client directory:

```bash
# Install in development mode
uv pip install -e .

# Or install dependencies directly
uv add mcp[cli] httpx rich click ollama websockets
```

## Quick Start

### 1. Check Connection Status

```bash
blender-mcp-client status
```

### 2. Process Natural Language Prompts

```bash
# Direct prompt
blender-mcp-client prompt "Create a red cube and take a screenshot"

# From file
blender-mcp-client prompt --file my_prompt.txt
```

### 3. AI-Powered Interaction (Ollama)

```bash
# Interactive session with local AI
blender-mcp-client ai --interactive

# Single prompt with AI
blender-mcp-client ai "I want to create a scene with trees and rocks"
```

### 4. Direct Tool Calls

```bash
# List available tools
blender-mcp-client tools

# Call specific tool
blender-mcp-client call get_scene_info

# Call with parameters
blender-mcp-client call execute_blender_code --param code="import bpy; bpy.ops.mesh.primitive_cube_add()"
```

### 5. Claude Code Integration

```python
# Import the interface
import sys
sys.path.append('/path/to/mcp-client/src')
from blender_mcp_client.claude_code_interface import *

# Show examples
blender_examples()

# Discover capabilities
capabilities = discover_blender_capabilities()
print(capabilities)

# Use synchronous functions
result = run_blender_prompt("Create a blue sphere")
print(result)

scene_info = run_blender_scene_info()
print(scene_info)

screenshot = run_blender_screenshot()
print(screenshot)
```

## Available Tools

The client supports all Blender MCP server tools:

### Core Blender Operations
- **get_scene_info**: Get detailed scene information
- **get_object_info**: Get specific object details
- **get_viewport_screenshot**: Capture viewport images
- **execute_blender_code**: Run Python scripts in Blender

### Asset Management
- **search_polyhaven_assets**: Search PolyHaven textures/HDRIs/models
- **download_polyhaven_asset**: Download and import assets
- **search_sketchfab_models**: Search Sketchfab 3D models  
- **download_sketchfab_model**: Download and import models

### AI Generation
- **generate_hyper3d_model_via_text**: Generate 3D models from text
- **generate_hyper3d_model_via_images**: Generate from images
- **poll_rodin_job_status**: Check generation status
- **import_generated_asset**: Import generated models

## Configuration

### Default Settings
- **Blender MCP Server**: `localhost:9876`
- **Ollama Server**: `http://localhost:11434`
- **Default AI Model**: `llama3.2`

### Custom Configuration
```bash
# Custom Blender server
blender-mcp-client --host 192.168.1.100 --port 8080 status

# Custom Ollama setup
blender-mcp-client ai --ollama-url http://localhost:11434 --model llama3.1 --interactive
```

## Usage Examples

### Natural Language Processing

The client can understand and execute natural language commands:

```bash
# Scene operations
blender-mcp-client prompt "What's in the current scene?"
blender-mcp-client prompt "Take a screenshot"

# Object creation
blender-mcp-client prompt "Create a red cube"
blender-mcp-client prompt "Add a monkey head and scale it by 2"

# Asset search
blender-mcp-client prompt "Search for wood textures on PolyHaven"
blender-mcp-client prompt "Find chair models on Sketchfab"

# AI generation
blender-mcp-client prompt "Generate a medieval sword using AI"
```

### AI-Powered Interaction

Start an interactive session with local AI:

```bash
blender-mcp-client ai --interactive
```

Example conversation:
```
🎯 You: Create a simple room scene
🤖 AI: I'll help you create a simple room scene in Blender...
⚡ Blender Actions:
   ✅ Execute Blender Python code

🎯 You: Add some furniture
🤖 AI: Let me add some basic furniture to the room...
⚡ Blender Actions:
   ✅ Execute Blender Python code

🎯 You: Take a screenshot to see how it looks
🤖 AI: I'll capture a screenshot of the current viewport...
⚡ Blender Actions:
   ✅ Take viewport screenshot
```

### Python Integration

```python
from blender_mcp_client.claude_code_interface import *

# Process natural language
result = run_blender_prompt("Create a scene with a cube, sphere, and plane")
if result['success']:
    print("✅ Scene created successfully!")
    for action in result['results']:
        print(f"   {action['action']}")

# Execute specific operations  
scene_info = run_blender_scene_info()
print(f"Current scene: {scene_info}")

# Search for assets
textures = run_blender_search_polyhaven("textures")
print(f"Available textures: {textures}")

# Generate 3D models
model_result = run_blender_generate_model("a fantasy castle")
print(f"Model generation: {model_result}")
```

## Architecture

### Component Overview

```
┌─────────────────────┐    ┌──────────────────────┐
│   Claude Code       │    │   Command Line       │
│   Interface         │    │   Interface (CLI)    │
└─────────┬───────────┘    └──────────┬───────────┘
          │                           │
          └─────────┬───────────────── │
                    │                  │
          ┌─────────▼───────────┐     │
          │ Claude Integration  │     │
          │ (Natural Language)  │     │
          └─────────┬───────────┘     │
                    │                  │
                    │    ┌─────────────▼─────────────┐
                    │    │    Ollama Integration     │
                    │    │    (Local AI Models)      │
                    │    └─────────────┬─────────────┘
                    │                  │
                    └─────────┬────────┘
                              │
                    ┌─────────▼───────────┐
                    │   MCP Client Core   │
                    │   (WebSocket/RPC)   │
                    └─────────┬───────────┘
                              │
                    ┌─────────▼───────────┐
                    │  Blender MCP Server │
                    │     (Port 9876)     │
                    └─────────────────────┘
```

### Key Components

1. **MCP Client Core** (`mcp_client.py`): WebSocket-based MCP protocol implementation
2. **Claude Integration** (`claude_integration.py`): Natural language processing for Claude Code
3. **Ollama Integration** (`ollama_integration.py`): Local AI model support
4. **CLI Interface** (`cli.py`): Rich command-line interface
5. **Claude Code Interface** (`claude_code_interface.py`): Easy-to-use functions for Claude Code

## Development

### Project Structure

```
mcp-client/
├── src/blender_mcp_client/
│   ├── __init__.py
│   ├── mcp_client.py           # Core MCP client
│   ├── claude_integration.py   # Claude Code integration
│   ├── ollama_integration.py   # Ollama AI integration  
│   ├── cli.py                  # Command-line interface
│   └── claude_code_interface.py # Synchronous interface
├── pyproject.toml              # Project configuration
└── README.md                   # This file
```

### Adding New Features

1. **New Tools**: Add methods to `mcp_client.py` and update CLI commands
2. **Natural Language**: Extend patterns in `claude_integration.py`
3. **AI Prompts**: Enhance system prompts in `ollama_integration.py`
4. **CLI Commands**: Add new click commands in `cli.py`

## Troubleshooting

### Connection Issues

```bash
# Check if Blender MCP server is running
blender-mcp-client status

# Check specific host/port
blender-mcp-client --host localhost --port 9876 status
```

### Ollama Issues

```bash
# List available models
blender-mcp-client models

# Test with different model
blender-mcp-client ai --model llama3.1 "test prompt"
```

### Debugging

```bash
# Enable verbose logging
blender-mcp-client --verbose status
blender-mcp-client --verbose prompt "debug test"
```

## Requirements

- Python 3.10+
- Blender MCP Server running on port 9876
- Optional: Ollama for AI features
- Optional: Local Ollama models (llama3.2, llama3.1, etc.)

## License

MIT License - see LICENSE file for details.