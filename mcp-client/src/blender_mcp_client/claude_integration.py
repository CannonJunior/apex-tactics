"""
Claude Code Integration for Blender MCP Client

Provides seamless integration with Claude Code environment for processing
natural language prompts and converting them to Blender MCP tool calls.
"""

import asyncio
import json
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from .mcp_client import BlenderMCPClient

logger = logging.getLogger("BlenderMCPClient.Claude")

@dataclass
class PromptAction:
    """Represents an action extracted from a natural language prompt"""
    action_type: str
    tool_name: str
    parameters: Dict[str, Any]
    description: str

class ClaudeBlenderIntegration:
    """
    Integration layer between Claude Code and Blender MCP client
    
    Processes natural language prompts and converts them to appropriate
    Blender MCP tool calls.
    """
    
    def __init__(self, mcp_client: BlenderMCPClient):
        self.client = mcp_client
        self.context_history = []
        self.last_screenshot = None
        
        # Define prompt patterns for different actions
        self.action_patterns = {
            'scene_info': [
                r'(?i).*(?:show|get|tell me about|describe).*(?:scene|current scene|what\'s in the scene)',
                r'(?i).*(?:what\'s|what is).*(?:in the scene|currently visible)',
                r'(?i).*(?:scene info|scene information|scene details)',
            ],
            'screenshot': [
                r'(?i).*(?:take|capture|get|show me).*(?:screenshot|image|picture|viewport)',
                r'(?i).*(?:what does it look like|show me the view|current view)',
                r'(?i).*(?:screenshot|viewport screenshot)',
            ],
            'object_info': [
                r'(?i).*(?:info|information|details|properties).*(?:about|of|for)\s+(\w+)',
                r'(?i).*(?:tell me about|describe|show|get info on)\s+(\w+)',
                r'(?i).*(?:what is|what\'s)\s+(\w+)',
            ],
            'execute_code': [
                r'(?i).*(?:run|execute|eval).*(?:code|script|python)',
                r'(?i).*(?:create|add|make).*(?:cube|sphere|plane|object|mesh)',
                r'(?i).*(?:delete|remove|move|rotate|scale)',
            ],
            'search_assets': [
                r'(?i).*(?:search|find|look for|get).*(?:asset|texture|material|model)',
                r'(?i).*(?:polyhaven|poly haven).*(?:asset|texture|hdri)',
                r'(?i).*(?:sketchfab).*(?:model|asset)',
            ],
            'generate_model': [
                r'(?i).*(?:generate|create|make).*(?:model|3d model|mesh).*(?:from|using|with)',
                r'(?i).*(?:hyper3d|ai generate|ai model)',
                r'(?i).*(?:text to 3d|prompt to model)',
            ]
        }
    
    async def process_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Process a natural language prompt and execute appropriate Blender actions
        
        Args:
            prompt: Natural language prompt from Claude Code
            
        Returns:
            Dictionary containing the result and metadata
        """
        logger.info(f"Processing prompt: {prompt}")
        
        # Add to context history
        self.context_history.append({
            "timestamp": asyncio.get_event_loop().time(),
            "prompt": prompt,
            "type": "user_input"
        })
        
        # Analyze prompt and determine actions
        actions = self._analyze_prompt(prompt)
        
        if not actions:
            return {
                "success": False,
                "message": "Could not understand the prompt. Try being more specific about what you want to do in Blender.",
                "available_actions": self._get_available_actions()
            }
        
        # Execute actions
        results = []
        for action in actions:
            try:
                result = await self._execute_action(action, prompt)
                results.append({
                    "action": action.description,
                    "success": True,
                    "result": result
                })
                
                # Add to context
                self.context_history.append({
                    "timestamp": asyncio.get_event_loop().time(),
                    "action": action.action_type,
                    "result": result,
                    "type": "action_result"
                })
                
            except Exception as e:
                logger.error(f"Error executing action {action.action_type}: {e}")
                results.append({
                    "action": action.description,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": any(r["success"] for r in results),
            "actions_executed": len(results),
            "results": results,
            "context_items": len(self.context_history)
        }
    
    def _analyze_prompt(self, prompt: str) -> List[PromptAction]:
        """Analyze prompt and extract actionable items"""
        actions = []
        
        # Check each pattern type
        for action_type, patterns in self.action_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, prompt)
                if match:
                    action = self._create_action_from_match(action_type, match, prompt)
                    if action:
                        actions.append(action)
                    break  # Only match first pattern per type
        
        # If no specific patterns matched, try to infer from keywords
        if not actions:
            actions = self._infer_actions_from_keywords(prompt)
        
        return actions
    
    def _create_action_from_match(self, action_type: str, match: re.Match, prompt: str) -> Optional[PromptAction]:
        """Create a PromptAction from a regex match"""
        
        if action_type == "scene_info":
            return PromptAction(
                action_type="scene_info",
                tool_name="get_scene_info",
                parameters={},
                description="Get current scene information"
            )
        
        elif action_type == "screenshot":
            # Extract size if mentioned
            size_match = re.search(r'(\d+)(?:px|pixels?)?', prompt)
            max_size = int(size_match.group(1)) if size_match else 800
            
            return PromptAction(
                action_type="screenshot",
                tool_name="get_viewport_screenshot",
                parameters={"max_size": max_size},
                description=f"Take viewport screenshot (max size: {max_size})"
            )
        
        elif action_type == "object_info":
            # Extract object name
            object_name = match.group(1) if match.groups() else self._extract_object_name(prompt)
            if object_name:
                return PromptAction(
                    action_type="object_info",
                    tool_name="get_object_info",
                    parameters={"object_name": object_name},
                    description=f"Get information about object '{object_name}'"
                )
        
        elif action_type == "execute_code":
            code = self._extract_or_generate_code(prompt)
            if code:
                return PromptAction(
                    action_type="execute_code",
                    tool_name="execute_blender_code",
                    parameters={"code": code},
                    description=f"Execute Blender Python code"
                )
        
        elif action_type == "search_assets":
            search_params = self._extract_search_parameters(prompt)
            if search_params:
                return PromptAction(
                    action_type="search_assets",
                    tool_name=search_params["tool"],
                    parameters=search_params["params"],
                    description=search_params["description"]
                )
        
        elif action_type == "generate_model":
            text_prompt = self._extract_generation_prompt(prompt)
            if text_prompt:
                return PromptAction(
                    action_type="generate_model",
                    tool_name="generate_hyper3d_model_via_text",
                    parameters={"text_prompt": text_prompt},
                    description=f"Generate 3D model: '{text_prompt}'"
                )
        
        return None
    
    def _infer_actions_from_keywords(self, prompt: str) -> List[PromptAction]:
        """Infer actions from keywords when no patterns match"""
        actions = []
        prompt_lower = prompt.lower()
        
        # Check for common Blender operations
        if any(word in prompt_lower for word in ['create', 'add', 'make', 'new']):
            if any(obj in prompt_lower for obj in ['cube', 'sphere', 'cylinder', 'plane', 'monkey', 'suzanne']):
                code = self._generate_creation_code(prompt)
                if code:
                    actions.append(PromptAction(
                        action_type="execute_code",
                        tool_name="execute_blender_code",
                        parameters={"code": code},
                        description="Create Blender object"
                    ))
        
        # Check for transformation operations
        if any(word in prompt_lower for word in ['move', 'rotate', 'scale', 'transform']):
            code = self._generate_transform_code(prompt)
            if code:
                actions.append(PromptAction(
                    action_type="execute_code",
                    tool_name="execute_blender_code",
                    parameters={"code": code},
                    description="Transform Blender object"
                ))
        
        return actions
    
    def _extract_object_name(self, prompt: str) -> Optional[str]:
        """Extract object name from prompt"""
        # Look for quoted strings first
        quoted_match = re.search(r'["\']([^"\']+)["\']', prompt)
        if quoted_match:
            return quoted_match.group(1)
        
        # Look for common object names
        common_objects = ['cube', 'sphere', 'cylinder', 'plane', 'camera', 'light', 'suzanne', 'monkey']
        for obj in common_objects:
            if obj.lower() in prompt.lower():
                return obj.title()
        
        # Extract word after "about", "of", "named", etc.
        pattern = r'(?:about|of|named|called)\s+(\w+)'
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_or_generate_code(self, prompt: str) -> Optional[str]:
        """Extract or generate Blender Python code from prompt"""
        # Look for code blocks
        code_match = re.search(r'```(?:python)?\s*(.*?)\s*```', prompt, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Look for inline code
        inline_match = re.search(r'`([^`]+)`', prompt)
        if inline_match:
            return inline_match.group(1).strip()
        
        # Generate code based on intent
        return self._generate_code_from_intent(prompt)
    
    def _generate_code_from_intent(self, prompt: str) -> Optional[str]:
        """Generate Blender Python code based on natural language intent"""
        prompt_lower = prompt.lower()
        
        # Object creation
        if 'create' in prompt_lower or 'add' in prompt_lower or 'make' in prompt_lower:
            return self._generate_creation_code(prompt)
        
        # Object deletion
        if 'delete' in prompt_lower or 'remove' in prompt_lower:
            return self._generate_deletion_code(prompt)
        
        # Transformation
        if any(word in prompt_lower for word in ['move', 'rotate', 'scale']):
            return self._generate_transform_code(prompt)
        
        return None
    
    def _generate_creation_code(self, prompt: str) -> Optional[str]:
        """Generate object creation code"""
        prompt_lower = prompt.lower()
        
        if 'cube' in prompt_lower:
            return "import bpy; bpy.ops.mesh.primitive_cube_add()"
        elif 'sphere' in prompt_lower:
            return "import bpy; bpy.ops.mesh.primitive_uv_sphere_add()"
        elif 'cylinder' in prompt_lower:
            return "import bpy; bpy.ops.mesh.primitive_cylinder_add()"
        elif 'plane' in prompt_lower:
            return "import bpy; bpy.ops.mesh.primitive_plane_add()"
        elif 'monkey' in prompt_lower or 'suzanne' in prompt_lower:
            return "import bpy; bpy.ops.mesh.primitive_monkey_add()"
        
        return None
    
    def _generate_deletion_code(self, prompt: str) -> Optional[str]:
        """Generate object deletion code"""
        object_name = self._extract_object_name(prompt)
        if object_name:
            return f"""
import bpy
if '{object_name}' in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects['{object_name}'], do_unlink=True)
"""
        else:
            return "import bpy; bpy.ops.object.delete()"
    
    def _generate_transform_code(self, prompt: str) -> Optional[str]:
        """Generate transformation code"""
        # Extract numbers for transformation values
        numbers = re.findall(r'-?\d+(?:\.\d+)?', prompt)
        
        if 'move' in prompt.lower():
            if len(numbers) >= 3:
                return f"import bpy; bpy.context.active_object.location = ({numbers[0]}, {numbers[1]}, {numbers[2]})"
            else:
                return "import bpy; bpy.context.active_object.location.z += 2"
        
        elif 'rotate' in prompt.lower():
            if numbers:
                return f"import bpy; import math; bpy.context.active_object.rotation_euler.z = math.radians({numbers[0]})"
            else:
                return "import bpy; import math; bpy.context.active_object.rotation_euler.z += math.radians(45)"
        
        elif 'scale' in prompt.lower():
            if numbers:
                scale = numbers[0]
                return f"import bpy; bpy.context.active_object.scale = ({scale}, {scale}, {scale})"
            else:
                return "import bpy; bpy.context.active_object.scale *= 2"
        
        return None
    
    def _extract_search_parameters(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Extract search parameters for asset search"""
        prompt_lower = prompt.lower()
        
        # PolyHaven search
        if 'polyhaven' in prompt_lower or 'poly haven' in prompt_lower:
            query_match = re.search(r'(?:search|find|look for)\s+(.+?)(?:\s+on|\s+from|$)', prompt, re.IGNORECASE)
            query = query_match.group(1).strip() if query_match else "textures"
            
            asset_type = "textures"
            if 'hdri' in prompt_lower:
                asset_type = "hdris"
            elif 'model' in prompt_lower:
                asset_type = "models"
            
            return {
                "tool": "search_polyhaven_assets",
                "params": {"asset_type": asset_type},
                "description": f"Search PolyHaven {asset_type}"
            }
        
        # Sketchfab search
        elif 'sketchfab' in prompt_lower:
            query_match = re.search(r'(?:search|find|look for)\s+(.+?)(?:\s+on|\s+from|$)', prompt, re.IGNORECASE)
            query = query_match.group(1).strip() if query_match else "models"
            
            return {
                "tool": "search_sketchfab_models",
                "params": {"query": query, "count": 10},
                "description": f"Search Sketchfab for '{query}'"
            }
        
        return None
    
    def _extract_generation_prompt(self, prompt: str) -> Optional[str]:
        """Extract text prompt for 3D model generation"""
        # Look for "generate", "create", "make" followed by description
        patterns = [
            r'(?:generate|create|make)(?:\s+a?)?\s+(.+?)(?:\s+(?:using|with|via)|\s*$)',
            r'(?:text to 3d|prompt to model):\s*(.+)',
            r'(?:hyper3d|ai).*?(?:generate|create)\s+(.+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                description = match.group(1).strip()
                # Clean up the description
                description = re.sub(r'\s+', ' ', description)
                return description
        
        return None
    
    async def _execute_action(self, action: PromptAction, original_prompt: str) -> Any:
        """Execute a single action using the MCP client"""
        logger.info(f"Executing action: {action.description}")
        
        try:
            result = await self.client.call_tool(action.tool_name, action.parameters)
            
            # Special handling for screenshots
            if action.action_type == "screenshot":
                self.last_screenshot = result
                return "Screenshot captured successfully"
            
            # Special handling for code execution
            elif action.action_type == "execute_code":
                return f"Code executed: {result}"
            
            return result
            
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            raise
    
    def _get_available_actions(self) -> List[str]:
        """Get list of available action types"""
        return [
            "Get scene information",
            "Take viewport screenshot", 
            "Get object information",
            "Execute Blender Python code",
            "Search PolyHaven assets",
            "Search Sketchfab models",
            "Generate 3D models with AI"
        ]
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of conversation context"""
        return {
            "total_interactions": len(self.context_history),
            "recent_actions": [
                item for item in self.context_history[-5:] 
                if item["type"] == "action_result"
            ],
            "has_screenshot": self.last_screenshot is not None
        }

# Convenience function for Claude Code integration
async def process_claude_prompt(prompt: str, host: str = "localhost", port: int = 9876) -> Dict[str, Any]:
    """
    Process a Claude Code prompt with Blender MCP integration
    
    Args:
        prompt: Natural language prompt from Claude Code
        host: MCP server host
        port: MCP server port
        
    Returns:
        Dictionary with execution results
    """
    try:
        from .mcp_client import BlenderMCPClient
        
        client = BlenderMCPClient(host, port)
        await client.connect()
        
        integration = ClaudeBlenderIntegration(client)
        result = await integration.process_prompt(prompt)
        
        await client.disconnect()
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to connect to Blender MCP server"
        }