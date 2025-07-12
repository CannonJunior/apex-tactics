"""
Game Bridge

Handles communication between ReactPy UI and the Ursina game engine.
Provides methods to send commands to the game and receive state updates.
"""

import asyncio
import json
from typing import Dict, Any, Optional, Callable
from fastapi import WebSocket


class GameBridge:
    """Bridge for communication between ReactPy UI and game engine"""
    
    def __init__(self):
        self.websocket: Optional[WebSocket] = None
        self.button_callbacks: Dict[str, Callable] = {}
        self.game_state: Dict[str, Any] = {}
        
    def set_websocket(self, websocket: Optional[WebSocket]):
        """Set the WebSocket connection to the game"""
        self.websocket = websocket
        if websocket:
            print("✅ Game bridge WebSocket connected")
        else:
            print("❌ Game bridge WebSocket disconnected")
    
    def register_button_callback(self, button_id: str, callback: Callable):
        """Register a callback for button clicks"""
        self.button_callbacks[button_id] = callback
        print(f"🔗 Registered callback for button: {button_id}")
    
    async def send_button_click(self, button_id: str, button_data: Dict[str, Any] = None):
        """Send button click event to the game"""
        if not self.websocket:
            print(f"⚠️ No WebSocket connection - cannot send {button_id} click")
            return
        
        message = {
            "type": "button_click",
            "button_id": button_id,
            "data": button_data or {}
        }
        
        try:
            await self.websocket.send_text(json.dumps(message))
            print(f"📤 Sent {button_id} click to game")
        except Exception as e:
            print(f"❌ Failed to send {button_id} click: {e}")
    
    async def send_command(self, command: str, data: Dict[str, Any] = None):
        """Send generic command to the game"""
        if not self.websocket:
            print(f"⚠️ No WebSocket connection - cannot send command: {command}")
            return
        
        message = {
            "type": "command",
            "command": command,
            "data": data or {}
        }
        
        try:
            await self.websocket.send_text(json.dumps(message))
            print(f"📤 Sent command to game: {command}")
        except Exception as e:
            print(f"❌ Failed to send command {command}: {e}")
    
    async def handle_game_state_update(self, state_data: Dict[str, Any]):
        """Handle game state updates from the game engine"""
        self.game_state.update(state_data)
        print(f"🔄 Game state updated: {list(state_data.keys())}")
    
    async def handle_button_state_update(self, button_data: Dict[str, Any]):
        """Handle button state updates (enabled/disabled, etc.)"""
        button_id = button_data.get("button_id")
        if button_id in self.button_callbacks:
            callback = self.button_callbacks[button_id]
            if asyncio.iscoroutinefunction(callback):
                await callback(button_data)
            else:
                callback(button_data)
    
    def get_game_state(self, key: str = None, default: Any = None) -> Any:
        """Get current game state"""
        if key:
            return self.game_state.get(key, default)
        return self.game_state
    
    def is_connected(self) -> bool:
        """Check if WebSocket connection is active"""
        return self.websocket is not None