#!/usr/bin/env python3
"""
Apex Tactics WebSocket Client

Following the exact same pattern as the working apex-tactics.py
but with WebSocket integration.
"""

from ursina import *
import sys
import os
import asyncio
import threading

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from game.controllers.tactical_rpg_controller import TacticalRPG
from ui.panels.control_panel import CharacterAttackInterface
from ui.panels.talent_panel import TalentPanel
from ui.panels.inventory_panel import InventoryPanel
from ui.panels.party_panel import PartyPanel
from ui.panels.upgrade_panel import UpgradePanel
from ui.panels.character_panel import CharacterPanel

print("🎮 Starting Apex Tactics WebSocket Client...")

app = Ursina()

# Create all panels (same as working apex-tactics.py)
print("📋 Creating UI panels...")
control_panel = CharacterAttackInterface()
talent_panel = TalentPanel()
inventory_panel = InventoryPanel()
party_panel = PartyPanel()
upgrade_panel = UpgradePanel()
character_panel = CharacterPanel()
print("✅ All panels created")

# WebSocket client (import after panels like the working version)
ws_client = None
try:
    from client.websocket_game_client import WebSocketGameClient
    ws_client = WebSocketGameClient("ws://localhost:8002")
    print("🌐 WebSocket client created")
except Exception as e:
    print(f"⚠️ WebSocket client creation failed: {e}")

def input(key):
    # Handle game input first (same as working apex-tactics.py)
    if game.handle_input(key):
        return  # Input was handled by game controller
    
    # Handle panel toggles (same as working apex-tactics.py)
    if key == 't':
        talent_panel.toggle_visibility()
        print("📋 Talent panel toggled")
        return
    elif key == 'i':
        inventory_panel.toggle_visibility()
        print("🎒 Inventory panel toggled")
        return
    elif key == 'p':
        party_panel.toggle_visibility()
        print("👥 Party panel toggled")
        return
    elif key == 'u':
        upgrade_panel.toggle_visibility()
        print("⬆️ Upgrade panel toggled")
        return
    elif key == 'c':
        character_panel.toggle_visibility()
        print("🧙 Character panel toggled")
        return
    
    # Handle path movement for selected unit (same as working apex-tactics.py)
    if (game.active_unit and game.current_mode == "move" and 
        key in ['w', 'a', 's', 'd', 'enter']):
        game.handle_path_movement(key)
        return
    
    # Handle camera controls (same as working apex-tactics.py)
    game.camera_controller.handle_input(key, control_panel)

# Initialize game (pass control_panel to prevent duplication)
print("🧪 Initializing TacticalRPG...")
game = TacticalRPG(control_panel=control_panel)
print("✅ TacticalRPG initialized - battlefield should be created")

# Set game reference for all panels (same as working apex-tactics.py)
control_panel.set_game_reference(game)
talent_panel.game_reference = game
inventory_panel.game_reference = game
party_panel.game_reference = game
upgrade_panel.game_reference = game
character_panel.game_reference = game

# WebSocket connection in background
async def connect_to_server():
    if ws_client:
        try:
            success = await ws_client.connect("default_session", "player1")
            if success:
                print("✅ Connected to game server")
            else:
                print("⚠️ Server connection failed")
        except Exception as e:
            print(f"⚠️ Server connection error: {e}")

def start_websocket_thread():
    if ws_client:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(connect_to_server())
        except Exception as e:
            print(f"⚠️ WebSocket thread error: {e}")

# Start WebSocket in background
if ws_client:
    ws_thread = threading.Thread(target=start_websocket_thread, daemon=True)
    ws_thread.start()

def update():
    # Update camera (same as working apex-tactics.py)
    game.camera_controller.handle_mouse_input()
    game.camera_controller.update_camera()
    
    # Update control panel (same as working apex-tactics.py)
    if game.turn_manager and game.turn_manager.current_unit() and not game.active_unit:
        control_panel.update_unit_info(game.turn_manager.current_unit())

# Set initial camera position (same as working apex-tactics.py)
game.camera_controller.update_camera()

# Add lighting (same as working apex-tactics.py)
DirectionalLight(y=10, z=5)

print(f"""
🎮 Apex Tactics WebSocket Client Ready!

This follows the EXACT same pattern as the working apex-tactics.py:
✅ UI panels created first
✅ TacticalRPG controller initialized (creates battlefield)
✅ Game references set for all panels
✅ WebSocket client added for server communication

Controls (same as original):
T - Talent Panel     |  WASD - Camera/Movement
I - Inventory Panel  |  Arrow Keys - Camera
P - Party Panel      |  Mouse - Camera Rotation
U - Upgrade Panel    |  Click - Select/Interact
C - Character Panel  |  M/A/ESC - Game Modes

If apex-tactics.py works, this should work the same way!
""")

app.run()