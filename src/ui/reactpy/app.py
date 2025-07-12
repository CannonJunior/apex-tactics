"""
ReactPy FastAPI Application

Web server hosting ReactPy components for Apex Tactics UI.
Runs alongside the main Ursina game on a separate port.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from reactpy import component, html
from reactpy.backend.fastapi import configure

from .components.end_turn_button import EndTurnButton
from .bridge.game_bridge import GameBridge


class ReactPyApp:
    """ReactPy application server for Apex Tactics UI"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.app = FastAPI(title="Apex Tactics ReactPy UI")
        self.game_bridge = GameBridge()
        
        # Configure ReactPy with FastAPI
        configure(self.app, self.create_app_component)
        
        # Add WebSocket endpoint for game communication
        self.app.websocket("/ws/game")(self.websocket_game_endpoint)
        
        # Serve static files if needed
        # self.app.mount("/static", StaticFiles(directory="static"), name="static")
    
    @component
    def create_app_component(self):
        """Main ReactPy application component"""
        return html.div(
            {"style": {
                "position": "fixed",
                "top": "0",
                "left": "0", 
                "width": "100%",
                "height": "100%",
                "pointer-events": "none",  # Allow clicks to pass through to Ursina
                "z-index": "1000"
            }},
            EndTurnButton(game_bridge=self.game_bridge)
        )
    
    async def websocket_game_endpoint(self, websocket: WebSocket):
        """WebSocket endpoint for communication with the game"""
        await websocket.accept()
        self.game_bridge.set_websocket(websocket)
        
        try:
            while True:
                # Keep connection alive and handle game state updates
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types from game
                if message.get("type") == "game_state_update":
                    await self.game_bridge.handle_game_state_update(message.get("data"))
                elif message.get("type") == "button_state_update":
                    await self.game_bridge.handle_button_state_update(message.get("data"))
                    
        except WebSocketDisconnect:
            self.game_bridge.set_websocket(None)
            print("Game WebSocket disconnected")
    
    def run(self):
        """Start the ReactPy server"""
        print(f"🌐 Starting ReactPy UI server on port {self.port}")
        uvicorn.run(
            self.app,
            host="127.0.0.1",
            port=self.port,
            log_level="info"
        )


def start_reactpy_server(port: int = 8080):
    """Start the ReactPy server (called from main game)"""
    app = ReactPyApp(port)
    app.run()


if __name__ == "__main__":
    # Run standalone
    start_reactpy_server()