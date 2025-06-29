#!/usr/bin/env python3
"""
Demo using imported TacticalRPG

This demonstrates how to use the TacticalRPG as an imported, modular component
rather than a monolithic application. Shows the clean separation and reusability.
"""

from ursina import *
from tactical_rpg import TacticalRPG

# Initialize Ursina
app = Ursina()

# Create title display
title = Text(
    "Modular TacticalRPG Demo",
    position=(0, 0.45),
    scale=2,
    color=color.cyan,
    origin=(0, 0)
)

subtitle = Text(
    "Using imported TacticalRPG component with imported CameraController",
    position=(0, 0.4),
    scale=1,
    color=color.white,
    origin=(0, 0)
)

# Create the tactical RPG game as an imported component
print("Creating TacticalRPG using imported module...")
game = TacticalRPG(grid_width=8, grid_height=8, create_ground=True)

# Add some custom lighting
DirectionalLight(
    direction=(1, -1, 1),
    color=color.white,
    shadows=True
)

AmbientLight(color=color.rgba(100, 100, 100, 0.1))

def input(key):
    """Global input handler that delegates to the imported TacticalRPG"""
    # Let the imported game handle all its input
    game.handle_input(key)
    
    # Add some demo-specific controls
    if key == 'escape':
        application.quit()
    elif key == 'r':
        # Reset camera to default
        game.camera_controller.reset_to_default()
        print("Camera reset to default position")
    elif key == 'i':
        # Show game info
        current_unit = game.get_current_unit()
        if current_unit:
            print(f"Current unit: {current_unit.name} at ({current_unit.x}, {current_unit.y})")
            print(f"Stats - HP: {current_unit.hp}/{current_unit.max_hp}, MP: {current_unit.mp}/{current_unit.max_mp}")
        else:
            print("No current unit")
        print(f"Camera mode: {game.camera_controller.get_mode_name()}")
    elif key == 'h':
        # Show help
        print("\n" + "="*50)
        print("MODULAR TACTICAL RPG DEMO - HELP")
        print("="*50)
        print("Camera Controls:")
        print("  1/2/3 - Switch camera modes (Orbit/Free/Top-down)")
        print("  WASD - Move camera (mode dependent)")
        print("  Mouse - Look around")
        print("  R - Reset camera to default")
        print()
        print("Game Controls:")
        print("  Click tiles - Select units or move")
        print("  Enter - Confirm movement")
        print("  Space - End current unit's turn")
        print("  ESC - Cancel action or exit")
        print()
        print("Info Controls:")
        print("  I - Show current unit info")
        print("  H - Show this help")
        print("="*50)

def update():
    """Global update function that delegates to the imported TacticalRPG"""
    # Let the imported game handle its update logic
    game.handle_update()

# Additional demo features
status_display = Text(
    "Press H for help, I for info, R to reset camera",
    position=(-0.8, -0.45),
    scale=0.8,
    color=color.yellow
)

print("\n" + "="*60)
print("MODULAR TACTICAL RPG DEMO STARTED")
print("="*60)
print("Successfully imported and initialized TacticalRPG!")
print(f"Grid size: {game.grid.width}x{game.grid.height}")
print(f"Units created: {len(game.units)}")
print(f"Camera controller: {type(game.camera_controller).__name__}")
print()
print("This demo shows how TacticalRPG works as a modular component:")
print("✓ Clean import from tactical_rpg module")
print("✓ Standalone initialization")
print("✓ All functionality preserved")
print("✓ Uses imported CameraController")
print("✓ Easy integration into any Ursina app")
print()
print("Controls:")
print("  1/2/3 - Camera modes")
print("  WASD - Move camera")
print("  Mouse - Look around") 
print("  Click tiles - Select/Move units")
print("  Space - End turn")
print("  H - Help, I - Info, R - Reset camera")
print("="*60)

# Initialize camera
game.camera_controller.update_camera()

if __name__ == "__main__":
    app.run()