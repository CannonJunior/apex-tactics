"""
Core MCP Client for connecting to Blender MCP server
"""

import asyncio
import json
import logging
import websockets
import httpx
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BlenderMCPClient")

@dataclass
class MCPRequest:
    """Represents an MCP request"""
    method: str
    params: Dict[str, Any] = None
    id: str = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.params is None:
            self.params = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "method": self.method,
            "params": self.params,
            "id": self.id
        }

@dataclass
class MCPResponse:
    """Represents an MCP response"""
    id: str
    result: Any = None
    error: Dict[str, Any] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPResponse':
        return cls(
            id=data.get("id"),
            result=data.get("result"),
            error=data.get("error")
        )

class BlenderMCPClient:
    """
    MCP Client for connecting to Blender MCP server
    
    Supports both WebSocket and HTTP connections depending on server configuration
    """
    
    def __init__(self, host: str = "localhost", port: int = 9876):
        self.host = host
        self.port = port
        self.websocket = None
        self.http_client = None
        self.connected = False
        self.available_tools = {}
        self.session_id = str(uuid.uuid4())
        self.connection_type = None  # 'websocket' or 'sse'
        
    async def connect(self) -> bool:
        """Connect to the MCP server"""
        try:
            # Try WebSocket connection first (standard MCP)
            uri = f"ws://{self.host}:{self.port}"
            logger.info(f"Attempting WebSocket connection to {uri}")
            
            self.websocket = await websockets.connect(uri)
            self.connected = True
            self.connection_type = 'websocket'
            
            # Initialize the connection with MCP handshake
            await self._initialize_connection()
            
            logger.info(f"Successfully connected to Blender MCP server at {uri}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect via WebSocket: {e}")
            
            # Try alternative connection methods if WebSocket fails
            try:
                # Try SSE (Server-Sent Events) connection
                return await self._try_sse_connection()
            except Exception as e2:
                logger.error(f"All connection methods failed: {e2}")
                return False
    
    async def _try_sse_connection(self) -> bool:
        """Try connecting via SSE (Server-Sent Events) over HTTP"""
        try:
            # Initialize HTTP client for SSE
            self.http_client = httpx.AsyncClient(timeout=30.0)
            
            # Test connection to the server
            test_url = f"http://{self.host}:{self.port}/health"
            logger.info(f"Attempting SSE connection to http://{self.host}:{self.port}")
            
            try:
                response = await self.http_client.get(test_url)
                if response.status_code == 200:
                    self.connected = True
                    self.connection_type = 'sse'
                    
                    # Initialize the connection with MCP handshake
                    await self._initialize_sse_connection()
                    
                    logger.info(f"Successfully connected via SSE to http://{self.host}:{self.port}")
                    return True
                else:
                    logger.warning(f"SSE endpoint responded with status {response.status_code}")
                    return False
                    
            except httpx.ConnectError:
                logger.warning("SSE connection failed - server not reachable via HTTP")
                return False
                
        except Exception as e:
            logger.error(f"Failed to establish SSE connection: {e}")
            if self.http_client:
                await self.http_client.aclose()
                self.http_client = None
            return False
    
    async def _initialize_connection(self):
        """Initialize MCP connection with handshake (WebSocket)"""
        # Send initialize request
        init_request = MCPRequest(
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "blender-mcp-client",
                    "version": "0.1.0"
                }
            }
        )
        
        response = await self._send_request(init_request)
        if response.error:
            raise Exception(f"Initialization failed: {response.error}")
        
        logger.info("MCP connection initialized successfully")
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        await self._send_notification(initialized_notification)
        
        # Get available tools
        await self._discover_tools()
    
    async def _initialize_sse_connection(self):
        """Initialize MCP connection with handshake (SSE)"""
        # For SSE, we'll use HTTP POST for requests and GET for responses
        init_request = MCPRequest(
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "blender-mcp-client",
                    "version": "0.1.0"
                }
            }
        )
        
        response = await self._send_sse_request(init_request)
        if response.error:
            raise Exception(f"SSE Initialization failed: {response.error}")
        
        logger.info("MCP SSE connection initialized successfully")
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        await self._send_sse_notification(initialized_notification)
        
        # Get available tools
        await self._discover_tools()
    
    async def _send_request(self, request: MCPRequest) -> MCPResponse:
        """Send an MCP request and wait for response"""
        if not self.connected:
            raise Exception("Not connected to MCP server")
        
        if self.connection_type == 'websocket':
            return await self._send_websocket_request(request)
        elif self.connection_type == 'sse':
            return await self._send_sse_request(request)
        else:
            raise Exception("Unknown connection type")
    
    async def _send_websocket_request(self, request: MCPRequest) -> MCPResponse:
        """Send MCP request via WebSocket"""
        if not self.websocket:
            raise Exception("WebSocket not connected")
        
        request_data = json.dumps(request.to_dict())
        logger.debug(f"Sending WebSocket request: {request_data}")
        
        await self.websocket.send(request_data)
        
        # Wait for response
        response_data = await self.websocket.recv()
        logger.debug(f"Received WebSocket response: {response_data}")
        
        response_dict = json.loads(response_data)
        return MCPResponse.from_dict(response_dict)
    
    async def _send_sse_request(self, request: MCPRequest) -> MCPResponse:
        """Send MCP request via SSE (HTTP)"""
        if not self.http_client:
            raise Exception("HTTP client not connected")
        
        request_data = request.to_dict()
        logger.debug(f"Sending SSE request: {request_data}")
        
        # Send request via HTTP POST
        url = f"http://{self.host}:{self.port}/mcp/request"
        response = await self.http_client.post(url, json=request_data)
        response.raise_for_status()
        
        response_dict = response.json()
        logger.debug(f"Received SSE response: {response_dict}")
        
        return MCPResponse.from_dict(response_dict)
    
    async def _send_notification(self, notification: Dict[str, Any]):
        """Send an MCP notification (no response expected)"""
        if not self.connected:
            raise Exception("Not connected to MCP server")
        
        if self.connection_type == 'websocket':
            await self._send_websocket_notification(notification)
        elif self.connection_type == 'sse':
            await self._send_sse_notification(notification)
        else:
            raise Exception("Unknown connection type")
    
    async def _send_websocket_notification(self, notification: Dict[str, Any]):
        """Send MCP notification via WebSocket"""
        if not self.websocket:
            raise Exception("WebSocket not connected")
        
        notification_data = json.dumps(notification)
        logger.debug(f"Sending WebSocket notification: {notification_data}")
        
        await self.websocket.send(notification_data)
    
    async def _send_sse_notification(self, notification: Dict[str, Any]):
        """Send MCP notification via SSE (HTTP)"""
        if not self.http_client:
            raise Exception("HTTP client not connected")
        
        logger.debug(f"Sending SSE notification: {notification}")
        
        # Send notification via HTTP POST
        url = f"http://{self.host}:{self.port}/mcp/notification"
        await self.http_client.post(url, json=notification)
    
    async def _discover_tools(self):
        """Discover available tools from the MCP server"""
        try:
            tools_request = MCPRequest(method="tools/list")
            response = await self._send_request(tools_request)
            
            if response.error:
                logger.error(f"Failed to get tools list: {response.error}")
                return
            
            tools = response.result.get("tools", [])
            self.available_tools = {tool["name"]: tool for tool in tools}
            
            logger.info(f"Discovered {len(self.available_tools)} tools: {list(self.available_tools.keys())}")
            
        except Exception as e:
            logger.error(f"Error discovering tools: {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """Call a tool on the MCP server"""
        if tool_name not in self.available_tools:
            available = list(self.available_tools.keys())
            raise ValueError(f"Tool '{tool_name}' not found. Available tools: {available}")
        
        tool_request = MCPRequest(
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments or {}
            }
        )
        
        response = await self._send_request(tool_request)
        
        if response.error:
            raise Exception(f"Tool call failed: {response.error}")
        
        return response.result
    
    async def get_scene_info(self) -> str:
        """Get Blender scene information"""
        return await self.call_tool("get_scene_info")
    
    async def get_object_info(self, object_name: str) -> str:
        """Get information about a specific Blender object"""
        return await self.call_tool("get_object_info", {"object_name": object_name})
    
    async def get_viewport_screenshot(self, max_size: int = 800) -> Any:
        """Get a screenshot of the Blender viewport"""
        return await self.call_tool("get_viewport_screenshot", {"max_size": max_size})
    
    async def execute_blender_code(self, code: str) -> str:
        """Execute Python code in Blender"""
        return await self.call_tool("execute_blender_code", {"code": code})
    
    async def search_polyhaven_assets(self, asset_type: str = "all", categories: str = None) -> str:
        """Search PolyHaven assets"""
        params = {"asset_type": asset_type}
        if categories:
            params["categories"] = categories
        return await self.call_tool("search_polyhaven_assets", params)
    
    async def search_sketchfab_models(self, query: str, categories: str = None, count: int = 20) -> str:
        """Search Sketchfab models"""
        params = {"query": query, "count": count}
        if categories:
            params["categories"] = categories
        return await self.call_tool("search_sketchfab_models", params)
    
    async def generate_hyper3d_model(self, text_prompt: str, bbox_condition: List[float] = None) -> str:
        """Generate 3D model using Hyper3D"""
        params = {"text_prompt": text_prompt}
        if bbox_condition:
            params["bbox_condition"] = bbox_condition
        return await self.call_tool("generate_hyper3d_model_via_text", params)
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
        self.connected = False
        self.connection_type = None
        logger.info("Disconnected from MCP server")
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return list(self.available_tools.keys())
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific tool"""
        return self.available_tools.get(tool_name)

# Context manager support
class BlenderMCPContext:
    """Context manager for MCP client connections"""
    
    def __init__(self, host: str = "localhost", port: int = 9876):
        self.client = BlenderMCPClient(host, port)
    
    async def __aenter__(self):
        await self.client.connect()
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.disconnect()

# Convenience function
async def create_client(host: str = "localhost", port: int = 9876) -> BlenderMCPClient:
    """Create and connect to a Blender MCP client"""
    client = BlenderMCPClient(host, port)
    await client.connect()
    return client