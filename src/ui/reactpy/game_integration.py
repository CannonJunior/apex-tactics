"""
Game Integration for ReactPy

Integrates ReactPy UI with the main Ursina game engine.
Handles WebSocket communication and bridges button clicks.
"""

import asyncio
import json
import threading
import websockets
from typing import Optional, Callable, Dict, Any


class ReactPyGameIntegration:
    """Integrates ReactPy UI with the game engine"""
    
    def __init__(self, game_controller, reactpy_port: int = 8080):
        self.game_controller = game_controller
        self.reactpy_port = reactpy_port
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.server_thread: Optional[threading.Thread] = None
        self.client_thread: Optional[threading.Thread] = None
        self.is_running = False
        
        # WebSocket URL for connecting to ReactPy server
        self.reactpy_ws_url = f"ws://localhost:{reactpy_port}/ws/game"
        
    def start_integration(self):
        """Start the ReactPy integration"""
        print("🌐 Starting ReactPy integration...")
        
        # Start ReactPy server in a separate thread
        self.server_thread = threading.Thread(target=self._start_reactpy_server, daemon=True)
        self.server_thread.start()
        
        # Start WebSocket client in a separate thread with its own event loop
        self.client_thread = threading.Thread(target=self._start_websocket_client, daemon=True)
        self.client_thread.start()
        
        self.is_running = True
        print("✅ ReactPy integration started")
    
    def _start_reactpy_server(self):
        """Start the ReactPy server in a separate thread"""
        try:
            from .app import start_reactpy_server
            start_reactpy_server(self.reactpy_port)
        except Exception as e:
            print(f"❌ Failed to start ReactPy server: {e}")
    
    def _start_websocket_client(self):
        """Start the WebSocket client in a separate thread with its own event loop"""
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the async connection in this loop
            loop.run_until_complete(self._connect_to_reactpy())
        except Exception as e:
            print(f"❌ Failed to start WebSocket client: {e}")
        finally:
            try:
                loop.close()
            except:
                pass
    
    async def _connect_to_reactpy(self):
        """Connect to the ReactPy server via WebSocket"""
        max_retries = 10
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 Attempting to connect to ReactPy server (attempt {attempt + 1}/{max_retries})")
                
                self.websocket = await websockets.connect(self.reactpy_ws_url)
                print("✅ Connected to ReactPy server")
                
                # Listen for messages from ReactPy
                await self._listen_to_reactpy()
                break
                
            except Exception as e:
                print(f"⚠️ Failed to connect to ReactPy server: {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    print("❌ Max retries exceeded, ReactPy integration failed")
    
    async def _listen_to_reactpy(self):
        """Listen for messages from ReactPy server"""
        try:
            async for message in self.websocket:
                await self._handle_reactpy_message(message)
        except websockets.exceptions.ConnectionClosed:
            print("🔌 ReactPy WebSocket connection closed")
        except Exception as e:
            print(f"❌ Error in ReactPy WebSocket: {e}")
    
    async def _handle_reactpy_message(self, message: str):
        """Handle incoming messages from ReactPy"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "button_click":
                await self._handle_button_click(data)
            elif message_type == "command":
                await self._handle_command(data)
            else:
                print(f"🤷 Unknown ReactPy message type: {message_type}")
                
        except Exception as e:
            print(f"❌ Error handling ReactPy message: {e}")
    
    async def _handle_button_click(self, data: Dict[str, Any]):
        """Handle button click from ReactPy"""
        button_id = data.get("button_id")
        button_data = data.get("data", {})
        
        print(f"🎮 ReactPy button clicked: {button_id}")
        
        if button_id == "end_turn":
            # Call the same end_turn_clicked function as the Ursina button
            if hasattr(self.game_controller, 'control_panel') and self.game_controller.control_panel:
                print("📞 Calling game controller end_turn_clicked")
                self.game_controller.control_panel.end_turn_clicked()
            else:
                print("⚠️ No control panel available for end turn")
        else:
            print(f"🤷 Unknown button ID: {button_id}")
    
    async def _handle_command(self, data: Dict[str, Any]):
        """Handle generic commands from ReactPy"""
        command = data.get("command")
        command_data = data.get("data", {})
        
        print(f"🎮 ReactPy command: {command}")
        
        # Handle different commands here
        # For now, just log them
        
    def send_game_state_update(self, state_data: Dict[str, Any]):
        """Send game state update to ReactPy"""
        if self.websocket and not self.websocket.closed:
            message = {
                "type": "game_state_update",
                "data": state_data
            }
            
            # Schedule the async send in a separate thread
            threading.Thread(
                target=self._send_message_sync,
                args=(json.dumps(message),),
                daemon=True
            ).start()
    
    def send_button_state_update(self, button_id: str, button_data: Dict[str, Any]):
        """Send button state update to ReactPy"""
        if self.websocket and not self.websocket.closed:
            message = {
                "type": "button_state_update",
                "data": {
                    "button_id": button_id,
                    **button_data
                }
            }
            
            # Schedule the async send in a separate thread
            threading.Thread(
                target=self._send_message_sync,
                args=(json.dumps(message),),
                daemon=True
            ).start()
    
    def _send_message_sync(self, message: str):
        """Send message to ReactPy server synchronously"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            loop.run_until_complete(self._send_message(message))
        except Exception as e:
            print(f"❌ Error sending message to ReactPy: {e}")
        finally:
            try:
                loop.close()
            except:
                pass
    
    async def _send_message(self, message: str):
        """Send message to ReactPy server"""
        try:
            if self.websocket and not self.websocket.closed:
                await self.websocket.send(message)
        except Exception as e:
            print(f"❌ Error sending message to ReactPy: {e}")
    
    def stop_integration(self):
        """Stop the ReactPy integration"""
        self.is_running = False
        
        if self.websocket:
            try:
                # Close WebSocket synchronously
                threading.Thread(target=self._close_websocket_sync, daemon=True).start()
            except Exception as e:
                print(f"⚠️ Error stopping WebSocket: {e}")
        
        print("🛑 ReactPy integration stopped")
    
    def _close_websocket_sync(self):
        """Close WebSocket synchronously"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            loop.run_until_complete(self.websocket.close())
        except Exception as e:
            print(f"❌ Error closing WebSocket: {e}")
        finally:
            try:
                loop.close()
            except:
                pass