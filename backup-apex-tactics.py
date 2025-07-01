"""
Apex Tactics - Modular Tactical RPG

Main entry point for the Apex Tactics tactical RPG game. This file serves as the 
application launcher and coordinator for the modular game architecture.

Architecture Overview:
- Modular ECS system in src/core/ecs/
- Game controllers in src/game/controllers/
- UI system in src/ui/ (panels, interaction, visual)
- Input handling in src/ui/interaction/input_handler.py
- Game loop management in src/core/game_loop.py

Key Features:
- Turn-based tactical combat
- Character progression and equipment
- Multiple camera modes (orbit, free, top-down)
- Comprehensive UI panels for game management
- Modular component-based architecture

Controls:
- Camera: [1] Orbit | [2] Free | [3] Top-down
- Panels: [R] Control | [C] Character | [I] Inventory | [T] Talents | [P] Party | [U] Upgrade
- Game: Click units to select | Click tiles to move | WASD for movement planning
"""

from ursina import *
import sys
import os

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import modular components
from core.ecs.world import World
from core.ecs.entity import Entity as ECSEntity
from core.game_loop import create_game_loop_manager
from components.stats.attributes import AttributeStats
from components.gameplay.unit_type import UnitType, UnitTypeComponent
from components.movement.movement import MovementComponent
from components.combat.attack import AttackComponent
from components.combat.defense import DefenseComponent
from components.combat.damage import AttackType
from core.math.grid import TacticalGrid
from core.math.vector import Vector2Int
from game.battle.turn_manager import TurnManager as ModularTurnManager
from ui.visual.grid_visualizer import GridVisualizer
from ui.visual.tile_highlighter import TileHighlighter
from ui.interaction.interactive_tile import InteractiveTile
from ui.interaction.interaction_manager import InteractionManager
from ui.interaction.input_handler import create_input_handler
from ui.camera.camera_controller import CameraController
from ui.panels.control_panel import ControlPanel
from ui.panels import create_game_panels
from ui.visual.unit_renderer import UnitEntity
from ui.visual.grid_utilities import create_clean_grid_lines, create_ground_plane
from game.legacy.unit_wrapper import Unit
from game.legacy.battle_grid_wrapper import BattleGrid
from game.legacy.turn_manager_wrapper import TurnManager
from game.factories.unit_factory import create_unit_entity
from game.controllers.tactical_rpg_controller import TacticalRPG

import random
import math

class GameHandlers:
    """Container class for game handlers that need to be accessible to global functions."""
    input_handler = None
    game_loop_manager = None


def input(key):
    """Global input function that delegates to the input handler."""
    if GameHandlers.input_handler:
        GameHandlers.input_handler.handle_input(key)


def update():
    """Global update function that delegates to the game loop manager."""
    if GameHandlers.game_loop_manager:
        GameHandlers.game_loop_manager.update()


def main():
    """
    Main function to initialize and run the Apex Tactics game.
    
    Sets up all game systems including:
    - Ursina application and visual elements
    - Game controller and ECS systems
    - UI panels and control systems
    - Input handling and game loop management
    """
    # Initialize Ursina application
    app = Ursina()
    
    # Create visual elements
    print("🎨 Creating visual elements...")
    ground = create_ground_plane()
    grid_entities = create_clean_grid_lines()
    
    # Add lighting
    DirectionalLight(y=10, z=5)
    
    # Create control panel
    print("🎛️ Initializing control panel...")
    control_panel = ControlPanel()
    
    # Initialize main game controller
    print("🎮 Initializing game controller...")
    game = TacticalRPG(control_panel_callback=lambda: control_panel, control_panel=control_panel)
    
    # Initialize game panels
    print("📋 Initializing game panels...")
    game_panels = None
    try:
        game_panels = create_game_panels(game)
        print("🎮 Game panels integrated successfully!")
        print("📋 Available panels: Character (C), Inventory (I), Talents (T), Party (P), Upgrade (U)")
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize game panels: {e}")
        game_panels = None
    
    # Initialize input handler and store in class for global access
    print("⌨️ Initializing input handler...")
    GameHandlers.input_handler = create_input_handler(game, game_panels)
    print("⌨️ Input handler initialized successfully!")
    
    # Initialize game loop manager and store in class for global access
    print("🔄 Initializing game loop manager...")
    GameHandlers.game_loop_manager = create_game_loop_manager(game, control_panel, game_panels)
    print("🔄 Game loop manager initialized successfully!")
    
    # Set initial camera position
    game.camera_controller.update_camera()
    
    print("🚀 Starting Apex Tactics...")
    print("=" * 50)
    print("APEX TACTICS - Tactical RPG")
    print("Camera Controls: [1] Orbit | [2] Free | [3] Top-down")
    print("Panel Controls: [R] Control Panel | [C] Character | [I] Inventory | [T] Talents | [P] Party | [U] Upgrade")
    print("Game Controls: Click units to select | Click tiles to move | WASD for movement planning")
    print("=" * 50)
    
    # Run the application
    app.run()

if __name__ == "__main__":
    main()
