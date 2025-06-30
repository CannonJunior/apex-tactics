from ursina import *
import sys
import os

# Add the alt-apex-tactics src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'alt-apex-tactics', 'src'))

from core.game.game_controller import TacticalRPG
from ui.panels.control_panel import ControlPanel
from ui.panels.talent_panel import TalentPanel
from ui.panels.inventory_panel import InventoryPanel
from ui.panels.party_panel import PartyPanel
from ui.panels.upgrade_panel import UpgradePanel
from ui.panels.character_panel import CharacterPanel

app = Ursina()

# Create a simple ground plane for better visibility
ground = Entity(model='plane', texture='white_cube', color=color.dark_gray, scale=(20, 1, 20), position=(4, -0.1, 4))

# Create all panels
control_panel = ControlPanel()
talent_panel = TalentPanel()
inventory_panel = InventoryPanel()
party_panel = PartyPanel()
upgrade_panel = UpgradePanel()
character_panel = CharacterPanel()

def input(key):
    # Handle panel toggles
    if key == 't':
        talent_panel.toggle_visibility()
        return
    elif key == 'i':
        inventory_panel.toggle_visibility()
        return
    elif key == 'p':
        party_panel.toggle_visibility()
        return
    elif key == 'u':
        upgrade_panel.toggle_visibility()
        return
    elif key == 'c':
        character_panel.toggle_visibility()
        return
    
    # Handle path movement for selected unit ONLY if in move mode
    if (game.selected_unit and game.current_mode == "move" and 
        key in ['w', 'a', 's', 'd', 'enter']):
        game.handle_path_movement(key)
        return  # Don't process camera controls if unit is selected and WASD/Enter is pressed
    
    # Handle camera controls only if not handling unit movement
    game.camera_controller.handle_input(key, control_panel)

# Initialize game
game = TacticalRPG()

# Set game reference for all panels
control_panel.set_game_reference(game)
talent_panel.game_reference = game
inventory_panel.game_reference = game
party_panel.game_reference = game
upgrade_panel.game_reference = game
character_panel.game_reference = game

def update():
    # Update camera
    game.camera_controller.handle_mouse_input()
    game.camera_controller.update_camera()
    
    # Update control panel with current unit info
    if game.turn_manager and game.turn_manager.current_unit() and not game.selected_unit:
        control_panel.update_unit_info(game.turn_manager.current_unit())

# Set initial camera position
game.camera_controller.update_camera()

# Add lighting
DirectionalLight(y=10, z=5)

app.run()