"""
Ollama Integration for Blender MCP Client

Provides local AI model support using Ollama for processing natural language
prompts and generating Blender actions.
"""

import asyncio
import json
import logging
import httpx
from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass
from .claude_integration import ClaudeBlenderIntegration

logger = logging.getLogger("BlenderMCPClient.Ollama")

@dataclass
class OllamaModel:
    """Represents an available Ollama model"""
    name: str
    size: str
    modified: str
    digest: str
    details: Dict[str, Any] = None

class OllamaClient:
    """
    Client for interacting with local Ollama models
    """
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=60.0)
        self.available_models = []
    
    async def check_connection(self) -> bool:
        """Check if Ollama server is available"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
    
    async def list_models(self) -> List[OllamaModel]:
        """List available Ollama models"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            
            data = response.json()
            models = []
            
            for model_data in data.get("models", []):
                model = OllamaModel(
                    name=model_data["name"],
                    size=model_data.get("size", "unknown"),
                    modified=model_data.get("modified_at", ""),
                    digest=model_data.get("digest", ""),
                    details=model_data.get("details", {})
                )
                models.append(model)
            
            self.available_models = models
            return models
            
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    async def generate_response(self, 
                              model: str, 
                              prompt: str, 
                              system_message: str = None,
                              stream: bool = False) -> AsyncGenerator[str, None]:
        """Generate response from Ollama model"""
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        
        try:
            async with self.client.stream(
                "POST", 
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                response.raise_for_status()
                
                if stream:
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    yield data["message"]["content"]
                            except json.JSONDecodeError:
                                continue
                else:
                    content = await response.aread()
                    data = json.loads(content)
                    if "message" in data and "content" in data["message"]:
                        yield data["message"]["content"]
                        
        except Exception as e:
            logger.error(f"Failed to generate response from Ollama: {e}")
            yield f"Error: {e}"
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

class OllamaBlenderIntegration:
    """
    Integration between Ollama models and Blender MCP client
    
    Uses local AI models to process natural language and generate Blender actions
    """
    
    def __init__(self, 
                 blender_integration: ClaudeBlenderIntegration,
                 ollama_client: OllamaClient,
                 default_model: str = "llama3.2"):
        self.blender_integration = blender_integration
        self.ollama_client = ollama_client
        self.default_model = default_model
        self.conversation_history = []
        
        self.system_prompt = """You are an AI assistant that helps users interact with Blender through natural language.

You can help with:
- Getting scene information
- Taking screenshots of the 3D viewport
- Getting information about specific objects
- Executing Blender Python code
- Searching for assets on PolyHaven and Sketchfab
- Generating 3D models using AI

When users ask for something, analyze their request and respond with specific, actionable instructions. If they want to create something in Blender, provide the exact Python code needed.

Available Blender operations:
- Scene info: Get current scene details
- Screenshot: Capture viewport image
- Object info: Get details about specific objects
- Code execution: Run Blender Python scripts
- Asset search: Find textures, HDRIs, and 3D models
- AI generation: Create 3D models from text descriptions

Be helpful, specific, and provide clear instructions or code when needed."""
    
    async def process_prompt_with_ai(self, 
                                   user_prompt: str, 
                                   model: str = None,
                                   include_context: bool = True) -> Dict[str, Any]:
        """
        Process user prompt using Ollama AI model, then execute Blender actions
        
        Args:
            user_prompt: User's natural language prompt
            model: Ollama model to use (defaults to self.default_model)
            include_context: Whether to include conversation history
            
        Returns:
            Dictionary with AI response and Blender execution results
        """
        model = model or self.default_model
        
        # Add conversation context if requested
        full_prompt = user_prompt
        if include_context and self.conversation_history:
            context = "\n".join([
                f"User: {item['user']}\nAssistant: {item['assistant']}" 
                for item in self.conversation_history[-3:]  # Last 3 exchanges
            ])
            full_prompt = f"Previous conversation:\n{context}\n\nCurrent request: {user_prompt}"
        
        # Get AI response
        logger.info(f"Processing prompt with {model}: {user_prompt}")
        
        ai_response = ""
        async for chunk in self.ollama_client.generate_response(
            model=model,
            prompt=full_prompt,
            system_message=self.system_prompt,
            stream=True
        ):
            ai_response += chunk
        
        # Add to conversation history
        self.conversation_history.append({
            "user": user_prompt,
            "assistant": ai_response
        })
        
        # Extract actionable items from AI response
        blender_actions = await self._extract_blender_actions(ai_response, user_prompt)
        
        # Execute Blender actions if any were identified
        blender_results = None
        if blender_actions:
            try:
                blender_results = await self.blender_integration.process_prompt(blender_actions)
            except Exception as e:
                logger.error(f"Error executing Blender actions: {e}")
                blender_results = {"success": False, "error": str(e)}
        
        return {
            "ai_response": ai_response,
            "blender_actions": blender_actions,
            "blender_results": blender_results,
            "model_used": model,
            "conversation_length": len(self.conversation_history)
        }
    
    async def _extract_blender_actions(self, ai_response: str, original_prompt: str) -> Optional[str]:
        """
        Extract actionable Blender commands from AI response
        
        This function analyzes the AI response to identify specific Blender actions
        that should be executed.
        """
        response_lower = ai_response.lower()
        
        # Look for code blocks in AI response
        import re
        code_blocks = re.findall(r'```(?:python)?\s*(.*?)\s*```', ai_response, re.DOTALL)
        if code_blocks:
            # If AI provided code, use it directly
            return f"execute code: {code_blocks[0].strip()}"
        
        # Look for specific action keywords in AI response
        action_keywords = {
            'screenshot': ['screenshot', 'capture', 'image', 'viewport'],
            'scene_info': ['scene info', 'scene information', 'current scene'],
            'object_info': ['object info', 'object information', 'details about'],
            'search': ['search', 'find assets', 'look for'],
            'generate': ['generate', 'create model', 'ai model']
        }
        
        for action, keywords in action_keywords.items():
            if any(keyword in response_lower for keyword in keywords):
                # If AI suggests an action, convert it back to a prompt for the Blender integration
                if action == 'screenshot':
                    return "take a screenshot"
                elif action == 'scene_info':
                    return "get scene info"
                elif action == 'search':
                    return original_prompt  # Pass through original search request
                elif action == 'generate':
                    return original_prompt  # Pass through original generation request
        
        # If AI provides specific instructions, try to convert them to actions
        if any(word in response_lower for word in ['create', 'add', 'make', 'delete', 'move']):
            return original_prompt  # Let the Blender integration handle it
        
        return None
    
    async def interactive_session(self, model: str = None) -> None:
        """
        Start an interactive session with the AI and Blender
        
        This runs a command-line loop where users can chat with the AI
        and have it execute Blender actions.
        """
        model = model or self.default_model
        
        print(f"\n🤖 Starting interactive Blender AI session with {model}")
        print("💡 You can ask me to help with Blender operations!")
        print("   Examples:")
        print("   - 'Create a red cube'")
        print("   - 'Take a screenshot'")
        print("   - 'Search for wood textures'")
        print("   - 'What's in the current scene?'")
        print("\n📝 Type 'quit' or 'exit' to end the session")
        print("=" * 60)
        
        while True:
            try:
                # Get user input
                user_input = input("\n🎯 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\n👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                print("\n🤔 AI thinking...")
                
                # Process with AI and execute Blender actions
                result = await self.process_prompt_with_ai(user_input, model)
                
                # Display AI response
                print(f"\n🤖 AI ({model}):")
                print(result["ai_response"])
                
                # Display Blender results if any
                if result["blender_results"]:
                    print(f"\n⚡ Blender Actions:")
                    if result["blender_results"]["success"]:
                        for action_result in result["blender_results"].get("results", []):
                            if action_result["success"]:
                                print(f"   ✅ {action_result['action']}")
                            else:
                                print(f"   ❌ {action_result['action']}: {action_result.get('error', 'Unknown error')}")
                    else:
                        print(f"   ❌ Error: {result['blender_results'].get('error', 'Unknown error')}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                continue
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of the conversation"""
        return {
            "total_exchanges": len(self.conversation_history),
            "blender_context": self.blender_integration.get_context_summary(),
            "recent_topics": [
                item["user"][:50] + "..." if len(item["user"]) > 50 else item["user"]
                for item in self.conversation_history[-5:]
            ]
        }

# Utility functions
async def create_ollama_blender_session(
    blender_host: str = "localhost",
    blender_port: int = 9876,
    ollama_url: str = "http://localhost:11434",
    model: str = "llama3.2"
) -> OllamaBlenderIntegration:
    """
    Create a complete Ollama + Blender integration session
    
    Args:
        blender_host: Blender MCP server host
        blender_port: Blender MCP server port  
        ollama_url: Ollama server URL
        model: Default Ollama model to use
        
    Returns:
        Configured OllamaBlenderIntegration instance
    """
    # Connect to Blender MCP
    from .mcp_client import BlenderMCPClient
    from .claude_integration import ClaudeBlenderIntegration
    
    blender_client = BlenderMCPClient(blender_host, blender_port)
    await blender_client.connect()
    
    blender_integration = ClaudeBlenderIntegration(blender_client)
    
    # Connect to Ollama
    ollama_client = OllamaClient(ollama_url)
    
    if not await ollama_client.check_connection():
        raise Exception(f"Cannot connect to Ollama at {ollama_url}")
    
    # Check if model is available
    models = await ollama_client.list_models()
    available_model_names = [m.name for m in models]
    
    if model not in available_model_names:
        logger.warning(f"Model '{model}' not found. Available models: {available_model_names}")
        if available_model_names:
            model = available_model_names[0]
            logger.info(f"Using model: {model}")
        else:
            raise Exception("No Ollama models available")
    
    return OllamaBlenderIntegration(blender_integration, ollama_client, model)