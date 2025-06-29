#!/usr/bin/env python3
"""
TacticalRPG - Standalone tactical RPG game system

Extracted from apex-tactics.py to be a reusable, importable component.
Includes all game logic, units, grid system, turn management, and visual components.

Usage:
    from tactical_rpg import TacticalRPG
    
    # Initialize Ursina app first
    from ursina import *
    app = Ursina()
    
    # Create the game
    game = TacticalRPG()
    
    # Set up input and update handlers
    def input(key):
        game.handle_input(key)
    
    def update():
        game.handle_update()
    
    # Run the game
    app.run()
"""

from ursina import *
from enum import Enum
import random
import math

# Import the standalone CameraController
from camera_controller import CameraController

# Core Data Models
class UnitType(Enum):
    HEROMANCER = "heromancer"
    UBERMENSCH = "ubermensch"
    SOUL_LINKED = "soul_linked"
    REALM_WALKER = "realm_walker"
    WARGI = "wargi"
    MAGI = "magi"

class Unit:
    def __init__(self, name, unit_type, x, y, wisdom=None, wonder=None, worthy=None, faith=None, finesse=None, fortitude=None, speed=None, spirit=None, strength=None):
        self.name = name
        self.type = unit_type
        self.x, self.y = x, y
        
        # Randomize attributes based on unit type
        self._randomize_attributes(wisdom, wonder, worthy, faith, finesse, fortitude, speed, spirit, strength)
        
        # Derived Stats
        self.max_hp = self.hp = (self.strength + self.fortitude + self.faith + self.worthy) * 5
        self.max_mp = self.mp = (self.wisdom + self.wonder + self.spirit + self.finesse) * 3
        self.max_ap = self.ap = self.speed
        self.move_points = self.speed // 2 + 2  # Movement based on speed attribute
        self.current_move_points = self.move_points  # Current movement available this turn
        self.alive = True
        
        # Combat attributes
        self.attack_range = 1  # Default attack range
        self.attack_effect_area = 0  # Default single-target attack (0 means only target tile)
        self.equipped_weapon = None  # Could be expanded later
        
        # Default action options for all units
        self.action_options = ["Move", "Attack", "Spirit", "Magic", "Inventory"]
        
    def _randomize_attributes(self, wisdom, wonder, worthy, faith, finesse, fortitude, speed, spirit, strength):
        # Base random values (5-15)
        base_attrs = {
            'wisdom': wisdom or random.randint(5, 15),
            'wonder': wonder or random.randint(5, 15),
            'worthy': worthy or random.randint(5, 15),
            'faith': faith or random.randint(5, 15),
            'finesse': finesse or random.randint(5, 15),
            'fortitude': fortitude or random.randint(5, 15),
            'speed': speed or random.randint(5, 15),
            'spirit': spirit or random.randint(5, 15),
            'strength': strength or random.randint(5, 15)
        }
        
        # Type-specific bonuses (+3-8)
        type_bonuses = {
            UnitType.HEROMANCER: ['speed', 'strength', 'finesse'],
            UnitType.UBERMENSCH: ['speed', 'strength', 'fortitude'],
            UnitType.SOUL_LINKED: ['faith', 'fortitude', 'worthy'],
            UnitType.REALM_WALKER: ['spirit', 'faith', 'worthy'],
            UnitType.WARGI: ['wisdom', 'wonder', 'spirit'],
            UnitType.MAGI: ['wisdom', 'wonder', 'finesse']
        }
        
        for attr in type_bonuses[self.type]:
            base_attrs[attr] += random.randint(3, 8)
            
        # Assign to self
        for attr, value in base_attrs.items():
            setattr(self, attr, value)
        
    @property
    def physical_defense(self):
        return (self.speed + self.strength + self.fortitude) // 3
        
    @property
    def magical_defense(self):
        return (self.wisdom + self.wonder + self.finesse) // 3
        
    @property
    def spiritual_defense(self):
        return (self.spirit + self.faith + self.worthy) // 3
        
    @property
    def physical_attack(self):
        return (self.speed + self.strength + self.finesse) // 2
        
    @property
    def magical_attack(self):
        return (self.wisdom + self.wonder + self.spirit) // 2
        
    @property
    def spiritual_attack(self):
        return (self.faith + self.fortitude + self.worthy) // 2
        
    def take_damage(self, damage, damage_type="physical"):
        defense = {"physical": self.physical_defense, "magical": self.magical_defense, "spiritual": self.spiritual_defense}[damage_type]
        self.hp = max(0, self.hp - max(1, damage - defense))
        self.alive = self.hp > 0

    def can_move_to(self, x, y, grid):
        distance = abs(x - self.x) + abs(y - self.y)
        return distance <= self.current_move_points and grid.is_valid(x, y)

# Battle Grid System
class BattleGrid:
    def __init__(self, width=8, height=8):
        self.width, self.height = width, height
        self.tiles = {}
        self.units = {}
        self.selected_unit = None
        
    def is_valid(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height and (x, y) not in self.units
        
    def add_unit(self, unit):
        self.units[(unit.x, unit.y)] = unit
        
    def move_unit(self, unit, x, y):
        if unit.can_move_to(x, y, self):
            distance = abs(x - unit.x) + abs(y - unit.y)
            del self.units[(unit.x, unit.y)]
            unit.x, unit.y = x, y
            unit.current_move_points -= distance
            self.units[(x, y)] = unit
            return True
        return False

# Turn Management
class TurnManager:
    def __init__(self, units):
        self.units = sorted(units, key=lambda u: u.speed, reverse=True)
        self.current_turn = 0
        self.phase = "move"  # move, action, end
        
    def next_turn(self):
        self.current_turn = (self.current_turn + 1) % len(self.units)
        if self.current_turn == 0:
            for unit in self.units:
                unit.ap = unit.max_ap
                unit.current_move_points = unit.move_points  # Reset movement points
                
    def current_unit(self):
        return self.units[self.current_turn] if self.units else None

# Visual Components
class GridTile:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.entity = Entity(model='cube', color=color.dark_gray, scale=(0.9, 0.1, 0.9), position=(x, 0, y))
        self.original_color = color.dark_gray
        self.highlighted = False
    
    def highlight(self, highlight_color=color.yellow):
        self.entity.color = highlight_color
        self.highlighted = True
    
    def clear_highlight(self):
        self.entity.color = self.original_color
        self.highlighted = False

class UnitEntity:
    def __init__(self, unit):
        self.unit = unit
        
        # Unit type colors
        type_colors = {
            UnitType.HEROMANCER: color.red,
            UnitType.UBERMENSCH: color.blue,
            UnitType.SOUL_LINKED: color.green,
            UnitType.REALM_WALKER: color.yellow,
            UnitType.WARGI: color.magenta,
            UnitType.MAGI: color.cyan
        }
        
        self.entity = Entity(
            model='cube',
            color=type_colors.get(unit.type, color.white),
            scale=(0.8, 1.2, 0.8),
            position=(unit.x, 0.6, unit.y)
        )
        
        # Add name label
        self.label = Text(
            unit.name,
            parent=self.entity,
            scale=10,
            color=color.white,
            position=(0, 1, 0),
            billboard=True
        )
    
    def update_position(self):
        self.entity.position = (self.unit.x, 0.6, self.unit.y)

# Control Panel
class ControlPanel:
    def __init__(self):
        self.panel = WindowPanel(
            title="Tactical RPG Control",
            content=[],
            popup=False,
            position=(-0.65, 0),
            size=(0.3, 0.8)
        )
        
        self.camera_mode_text = Text("Camera Mode: Orbit", parent=self.panel, scale=0.6, position=(-0.1, 0.35))
        self.turn_text = Text("Turn: 1", parent=self.panel, scale=0.6, position=(-0.1, 0.3))
        self.unit_text = Text("Current Unit: None", parent=self.panel, scale=0.6, position=(-0.1, 0.25))
        self.stats_text = Text("", parent=self.panel, scale=0.5, position=(-0.1, 0.1))
        
        # Add instructions
        Text("Instructions:", parent=self.panel, scale=0.6, position=(-0.1, 0))
        Text("1/2/3 - Camera modes", parent=self.panel, scale=0.4, position=(-0.1, -0.05))
        Text("WASD - Move camera", parent=self.panel, scale=0.4, position=(-0.1, -0.1))
        Text("Mouse - Look around", parent=self.panel, scale=0.4, position=(-0.1, -0.15))
        Text("Click tiles - Select/Move", parent=self.panel, scale=0.4, position=(-0.1, -0.2))
        Text("Enter - Confirm move", parent=self.panel, scale=0.4, position=(-0.1, -0.25))
        Text("Space - End turn", parent=self.panel, scale=0.4, position=(-0.1, -0.3))
        
    def update_camera_mode(self, mode):
        mode_names = ["Orbit", "Free", "Top-down"]
        self.camera_mode_text.text = f"Camera Mode: {mode_names[mode]}"
    
    def update_turn_info(self, turn, unit):
        self.turn_text.text = f"Turn: {turn + 1}"
        if unit:
            self.unit_text.text = f"Current Unit: {unit.name}"
            stats = f"HP: {unit.hp}/{unit.max_hp}\\nMP: {unit.mp}/{unit.max_mp}\\nAP: {unit.ap}/{unit.max_ap}\\nMove: {unit.current_move_points}"
            self.stats_text.text = stats
        else:
            self.unit_text.text = "Current Unit: None"
            self.stats_text.text = ""

# Main TacticalRPG Class
class TacticalRPG:
    """
    Standalone Tactical RPG game system
    
    A complete tactical RPG implementation that can be imported and used
    in any Ursina application. Includes units, grid system, turn management,
    combat, movement, and camera controls.
    """
    
    def __init__(self, grid_width=8, grid_height=8, create_ground=True):
        """
        Initialize the tactical RPG game
        
        Args:
            grid_width: Width of the battle grid
            grid_height: Height of the battle grid
            create_ground: Whether to create the ground plane automatically
        """
        # Initialize core systems
        self.grid = BattleGrid(grid_width, grid_height)
        self.units = []
        self.unit_entities = []
        self.tile_entities = []
        self.turn_manager = None
        self.selected_unit = None
        self.current_path = []
        self.path_cursor = None
        self.movement_modal = None
        self.action_modal = None
        self.current_mode = None
        self.attack_modal = None
        self.attack_target_tile = None
        
        # Create control panel
        self.control_panel = ControlPanel()
        
        # Create camera controller with control panel
        self.camera_controller = CameraController(
            grid_width=self.grid.width, 
            grid_height=self.grid.height,
            control_panel=self.control_panel
        )
        
        # Create visual elements
        if create_ground:
            self.create_ground()
        self.create_visual_grid()
        
        # Setup the battle
        self.setup_battle()
        
        print(f"TacticalRPG initialized: {grid_width}x{grid_height} grid with {len(self.units)} units")
    
    def create_ground(self):
        """Create the ground plane"""
        self.ground = Entity(
            model='plane', 
            texture='white_cube', 
            color=color.dark_gray, 
            scale=(20, 1, 20), 
            position=(self.grid.width/2, -0.1, self.grid.height/2)
        )
    
    def create_visual_grid(self):
        """Create visual representation of the battle grid"""
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                tile = GridTile(x, y)
                self.tile_entities.append(tile)
    
    def setup_battle(self):
        """Initialize the battle with default units"""
        # Create test units
        test_units_data = [
            ("Hero1", UnitType.HEROMANCER, 1, 1),
            ("Uber1", UnitType.UBERMENSCH, 3, 2),
            ("Soul1", UnitType.SOUL_LINKED, 5, 1),
            ("Realm1", UnitType.REALM_WALKER, 2, 4),
            ("Wargi1", UnitType.WARGI, 6, 3),
            ("Magi1", UnitType.MAGI, 4, 5)
        ]
        
        for name, unit_type, x, y in test_units_data:
            unit = Unit(name, unit_type, x, y)
            self.units.append(unit)
            self.grid.add_unit(unit)
            
            unit_entity = UnitEntity(unit)
            self.unit_entities.append(unit_entity)
        
        # Initialize turn manager
        self.turn_manager = TurnManager(self.units)
        self.update_control_panel()
        
        print(f"Battle setup complete: {len(self.units)} units ready")
    
    def get_tile_at(self, x, y):
        """Get the visual tile at grid coordinates"""
        if 0 <= x < self.grid.width and 0 <= y < self.grid.height:
            index = y * self.grid.width + x
            if 0 <= index < len(self.tile_entities):
                return self.tile_entities[index]
        return None
    
    def handle_tile_click(self, x, y):
        """Handle clicking on a tile"""
        if not (0 <= x < self.grid.width and 0 <= y < self.grid.height):
            return
            
        # Check if there's a unit at this position
        unit = self.grid.units.get((x, y))
        
        if self.selected_unit and self.current_mode == "move":
            # We're in movement mode, try to move to this tile
            if self.selected_unit.can_move_to(x, y, self.grid):
                self.current_path.append((x, y))
                self.show_movement_confirmation()
            else:
                print(f"Cannot move to ({x}, {y})")
        elif unit:
            # Select this unit and show action modal
            self.selected_unit = unit
            self.clear_highlights()
            self.show_action_modal(unit)
        else:
            # Clicked empty tile, clear selection
            self.selected_unit = None
            self.clear_highlights()
            self.hide_modals()
    
    def show_action_modal(self, unit):
        """Show action selection modal for a unit"""
        if self.action_modal:
            destroy(self.action_modal)
        
        self.action_modal = WindowPanel(
            title=f"Actions for {unit.name}",
            content=[],
            popup=True,
            position=(0, 0)
        )
        
        # Create action buttons
        button_y = 0.1
        for action in unit.action_options:
            button = Button(
                text=action,
                color=color.azure,
                scale=(0.2, 0.05),
                position=(0, button_y),
                parent=self.action_modal
            )
            button.on_click = lambda action=action: self.handle_action_selection(action, unit)
            button_y -= 0.07
    
    def handle_action_selection(self, action_name, unit):
        """Handle action selection"""
        print(f"{unit.name} selected action: {action_name}")
        
        if action_name == "Move":
            self.current_mode = "move"
            self.current_path = []
            self.highlight_movement_range()
            self.hide_modals()
        else:
            print(f"Action '{action_name}' not yet implemented")
            self.hide_modals()
    
    def highlight_movement_range(self):
        """Highlight tiles the selected unit can move to"""
        if not self.selected_unit:
            return
            
        self.clear_highlights()
        unit = self.selected_unit
        
        for x in range(max(0, unit.x - unit.current_move_points), 
                      min(self.grid.width, unit.x + unit.current_move_points + 1)):
            for y in range(max(0, unit.y - unit.current_move_points), 
                          min(self.grid.height, unit.y + unit.current_move_points + 1)):
                if unit.can_move_to(x, y, self.grid):
                    tile = self.get_tile_at(x, y)
                    if tile:
                        tile.highlight(color.green)
    
    def clear_highlights(self):
        """Clear all tile highlights"""
        for tile in self.tile_entities:
            tile.clear_highlight()
    
    def show_movement_confirmation(self):
        """Show movement confirmation modal"""
        if not self.current_path:
            return
            
        target_x, target_y = self.current_path[-1]
        
        if self.movement_modal:
            destroy(self.movement_modal)
        
        self.movement_modal = WindowPanel(
            title="Confirm Movement",
            content=[],
            popup=True,
            position=(0, 0)
        )
        
        Text(f"Move to ({target_x}, {target_y})?", parent=self.movement_modal, position=(0, 0.05), scale=0.7)
        
        confirm_btn = Button(
            text="Confirm (Enter)",
            color=color.green,
            scale=(0.15, 0.05),
            position=(-0.08, -0.05),
            parent=self.movement_modal
        )
        confirm_btn.on_click = self.execute_movement
        
        cancel_btn = Button(
            text="Cancel (Esc)",
            color=color.red,
            scale=(0.15, 0.05),
            position=(0.08, -0.05),
            parent=self.movement_modal
        )
        cancel_btn.on_click = self.cancel_movement
    
    def execute_movement(self):
        """Execute the planned movement"""
        if not self.selected_unit or not self.current_path:
            return
            
        target_x, target_y = self.current_path[-1]
        
        if self.grid.move_unit(self.selected_unit, target_x, target_y):
            # Update visual representation
            for unit_entity in self.unit_entities:
                if unit_entity.unit == self.selected_unit:
                    unit_entity.update_position()
                    break
            
            print(f"{self.selected_unit.name} moved to ({target_x}, {target_y})")
            
            # Clear movement state
            self.current_path = []
            self.current_mode = None
            self.clear_highlights()
            self.hide_modals()
            self.update_control_panel()
        else:
            print("Movement failed!")
    
    def cancel_movement(self):
        """Cancel the planned movement"""
        self.current_path = []
        self.current_mode = None
        self.clear_highlights()
        self.hide_modals()
    
    def handle_path_movement(self, direction):
        """Handle WASD movement for path planning"""
        if self.current_mode != "move" or not self.selected_unit:
            return
            
        # Direction mapping
        directions = {
            'w': (0, -1),  # North
            's': (0, 1),   # South
            'a': (-1, 0),  # West
            'd': (1, 0)    # East
        }
        
        if direction not in directions:
            return
            
        dx, dy = directions[direction]
        current_x, current_y = self.selected_unit.x, self.selected_unit.y
        
        # Apply path if exists
        if self.current_path:
            current_x, current_y = self.current_path[-1]
        
        new_x, new_y = current_x + dx, current_y + dy
        
        # Check if the move is valid
        if self.selected_unit.can_move_to(new_x, new_y, self.grid):
            # Calculate total distance including path
            total_distance = len(self.current_path) + 1
            if total_distance <= self.selected_unit.current_move_points:
                self.current_path.append((new_x, new_y))
                print(f"Planned move to ({new_x}, {new_y})")
                # You could add path visualization here
        else:
            print(f"Cannot move to ({new_x}, {new_y})")
    
    def end_current_turn(self):
        """End the current unit's turn"""
        if self.turn_manager:
            current_unit = self.turn_manager.current_unit()
            if current_unit:
                print(f"{current_unit.name}'s turn ended")
            
            self.turn_manager.next_turn()
            self.selected_unit = None
            self.current_mode = None
            self.current_path = []
            self.clear_highlights()
            self.hide_modals()
            self.update_control_panel()
    
    def hide_modals(self):
        """Hide all modals"""
        if self.action_modal:
            destroy(self.action_modal)
            self.action_modal = None
        if self.movement_modal:
            destroy(self.movement_modal)
            self.movement_modal = None
    
    def update_control_panel(self):
        """Update control panel information"""
        if self.turn_manager:
            current_unit = self.turn_manager.current_unit()
            self.control_panel.update_turn_info(self.turn_manager.current_turn, current_unit)
    
    def handle_input(self, key):
        """Handle all input for the tactical RPG"""
        # Pass input to camera controller first
        self.camera_controller.handle_input(key)
        
        # Handle game-specific input
        if key == 'space':
            self.end_current_turn()
        elif key == 'enter':
            if self.movement_modal:
                self.execute_movement()
        elif key == 'escape':
            if self.movement_modal or self.action_modal:
                self.cancel_movement()
            else:
                self.selected_unit = None
                self.clear_highlights()
        elif key in ['w', 'a', 's', 'd'] and self.current_mode == "move":
            self.handle_path_movement(key)
    
    def handle_update(self):
        """Handle per-frame updates"""
        # Update camera
        self.camera_controller.handle_mouse_input()
        self.camera_controller.update_camera()
    
    def get_current_unit(self):
        """Get the current active unit"""
        return self.turn_manager.current_unit() if self.turn_manager else None
    
    def get_unit_at(self, x, y):
        """Get unit at grid coordinates"""
        return self.grid.units.get((x, y))
    
    def is_valid_position(self, x, y):
        """Check if position is valid on the grid"""
        return self.grid.is_valid(x, y)


# Test function to demonstrate the standalone TacticalRPG
def test_tactical_rpg():
    """Test the standalone TacticalRPG system"""
    print("Testing standalone TacticalRPG...")
    
    # Create Ursina app
    app = Ursina()
    
    # Create the tactical RPG game
    game = TacticalRPG()
    
    # Global input and update handlers
    def input(key):
        game.handle_input(key)
        
        if key == 'escape':
            application.quit()
        elif key == 't':
            current_unit = game.get_current_unit()
            if current_unit:
                print(f"Current unit: {current_unit.name} at ({current_unit.x}, {current_unit.y})")
            else:
                print("No current unit")
    
    def update():
        game.handle_update()
    
    print("TacticalRPG Test Controls:")
    print("  1/2/3 - Camera modes")
    print("  WASD - Move camera OR plan movement")
    print("  Mouse - Look around")
    print("  Click tiles - Select/Move units")
    print("  Enter - Confirm movement")
    print("  Space - End turn")
    print("  T - Show current unit")
    print("  ESC - Cancel/Exit")
    
    # Initialize camera
    game.camera_controller.update_camera()
    
    app.run()


if __name__ == "__main__":
    test_tactical_rpg()