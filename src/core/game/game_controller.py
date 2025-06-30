"""
Game Controller Module - Main game logic for the tactical RPG
Extracted from apex-tactics.py
"""

import random
import math
from ursina import *
from ursina.prefabs.window_panel import WindowPanel

# Import core modules
from core.models.unit_types import UnitType
from core.models.unit import Unit
from core.game.battle_grid import BattleGrid
from core.game.turn_manager import TurnManager
from ui.camera.camera_controller import CameraController
from ui.battlefield.grid_tile import GridTile
from ui.battlefield.unit_entity import UnitEntity


class TacticalRPG:
    """Main game controller that handles the game state, combat, movement, and UI interactions"""
    
    def __init__(self):
        self.grid = BattleGrid()
        self.units = []
        self.unit_entities = []
        self.tile_entities = []
        self.turn_manager = None
        self.selected_unit = None
        self.current_path = []  # Track the selected movement path
        self.path_cursor = None  # Current position in path selection
        self.movement_modal = None  # Reference to movement confirmation modal
        self.action_modal = None  # Reference to action selection modal
        self.current_mode = None  # Track current action mode: 'move', 'attack', etc.
        self.attack_modal = None  # Reference to attack confirmation modal
        self.attack_target_tile = None  # Currently targeted attack tile
        self.camera_controller = CameraController(self.grid.width, self.grid.height)
        self.control_panel = None  # Reference to control panel for UI updates
        
        self.setup_battle()
        
    def setup_battle(self):
        """Initialize the battle with grid tiles and units"""
        # Create grid tiles
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                self.tile_entities.append(GridTile(x, y, self))
                
        # Create units with randomized attributes based on type
        player_units = [
            Unit("Hero", UnitType.HEROMANCER, 1, 1),
            Unit("Sage", UnitType.MAGI, 2, 1)
        ]
        enemy_units = [
            Unit("Orc", UnitType.UBERMENSCH, 6, 6),
            Unit("Spirit", UnitType.REALM_WALKER, 5, 6)
        ]
        
        self.units = player_units + enemy_units
        
        # Equip weapons for demonstration
        self.equip_demo_weapons()
        
        for unit in self.units:
            self.grid.add_unit(unit)
            self.unit_entities.append(UnitEntity(unit))
            
        self.turn_manager = TurnManager(self.units)
        self.refresh_all_ap()
    
    def equip_demo_weapons(self):
        """Equip demonstration weapons to show range/area effects"""
        # Create spear weapon
        spear_data = {
            "id": "spear",
            "name": "Spear",
            "type": "Weapons",
            "tier": "BASE",
            "description": "A long-reach spear with extended attack range and area effect.",
            "stats": {
                "physical_attack": 14,
                "attack_range": 2,
                "effect_area": 2
            }
        }
        
        # Create bow weapon for comparison
        bow_data = {
            "id": "magic_bow",
            "name": "Magic Bow",
            "type": "Weapons", 
            "tier": "ENCHANTED",
            "description": "An enchanted bow with long range.",
            "stats": {
                "physical_attack": 22,
                "magical_attack": 8,
                "attack_range": 3,
                "effect_area": 1
            }
        }
        
        # Equip weapons to units
        if len(self.units) >= 4:
            # Give Hero the spear (range 2, area 2)
            self.units[0].equip_weapon(spear_data)
            print(f"🔥 {self.units[0].name} equipped {spear_data['name']} - Range: {self.units[0].attack_range}, Area: {self.units[0].attack_effect_area}")
            
            # Give Sage the bow (range 3, area 1)
            self.units[1].equip_weapon(bow_data)
            print(f"🏹 {self.units[1].name} equipped {bow_data['name']} - Range: {self.units[1].attack_range}, Area: {self.units[1].attack_effect_area}")
            
            print("\n📋 Test Instructions:")
            print("1. Click on Hero - notice spear gives Range 2, Area 2")
            print("2. Click Attack - see red tiles show 2-tile attack range")
            print("3. Click target - see yellow area effect covering 2-tile radius")
            print("4. Try same with Sage - bow has Range 3, Area 1")
            print("5. Compare the different weapon effects!")
        
        print("✅ Demo weapons equipped for testing")
        
    def end_current_turn(self):
        """End the current unit's turn and move to next unit"""
        if self.turn_manager:
            # Clear current selection
            self.clear_highlights()
            self.selected_unit = None
            
            # Move to next turn
            self.turn_manager.next_turn()
            
            # Update control panel with new current unit
            current_unit = self.turn_manager.current_unit()
            if self.control_panel:
                self.control_panel.update_unit_info(current_unit)
            
            print(f"Turn ended. Now it's {current_unit.name}'s turn.")
    
    def set_control_panel(self, control_panel):
        """Set reference to control panel for UI updates"""
        self.control_panel = control_panel
        
    def handle_tile_click(self, x, y):
        """Handle clicks on grid tiles"""
        # Handle attack targeting if in attack mode
        if self.current_mode == "attack" and self.selected_unit:
            self.handle_attack_target_selection(x, y)
            return
            
        # Clear any existing highlights
        self.clear_highlights()
        
        # Check if there's a unit on the clicked tile
        if (x, y) in self.grid.units:
            clicked_unit = self.grid.units[(x, y)]
            
            # Select the clicked unit and show action modal
            self.selected_unit = clicked_unit
            self.current_path = []  # Reset path when selecting new unit
            self.path_cursor = (clicked_unit.x, clicked_unit.y)  # Start cursor at unit position
            self.current_mode = None  # Reset mode
            self.highlight_selected_unit()
            self.highlight_movement_range()
            
            # Update control panel with selected unit info
            if self.control_panel:
                self.control_panel.update_unit_info(clicked_unit)
            
            # Show action modal for the selected unit
            self.show_action_modal(clicked_unit)
        else:
            # Clicked on an empty tile - clear selection
            self.selected_unit = None
            self.current_path = []
            self.path_cursor = None
            self.current_mode = None
            
            # Clear control panel unit info
            if self.control_panel:
                self.control_panel.update_unit_info(None)
                
    def highlight_movement_range(self):
        """Highlight all tiles the selected unit can move to"""
        if not self.selected_unit:
            return
            
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                distance = abs(x - self.selected_unit.x) + abs(y - self.selected_unit.y)
                if distance <= self.selected_unit.current_move_points and self.grid.is_valid(x, y):
                    tile = self.get_tile_at(x, y)
                    if tile:
                        if distance == 0:
                            # Current position - different color
                            tile.highlight(color.white)
                        else:
                            # Valid movement range
                            tile.highlight(color.green)
                    
    def highlight_selected_unit(self):
        """Highlight the currently selected unit"""
        if self.selected_unit:
            for entity in self.unit_entities:
                if entity.unit == self.selected_unit:
                    entity.highlight_selected()
                    break
                    
    def highlight_possible_moves(self):
        """This method is now replaced by highlight_movement_range"""
        self.highlight_movement_range()
                            
    def get_tile_at(self, x, y):
        """Get the tile entity at the given grid coordinates"""
        for tile in self.tile_entities:
            if tile.grid_x == x and tile.grid_y == y:
                return tile
        return None
        
    def handle_path_movement(self, direction):
        """Handle path movement and confirmation"""
        if not self.selected_unit or not self.path_cursor:
            return
            
        if direction == 'enter':
            # Show confirmation modal for movement
            self.show_movement_confirmation()
            return
            
        # Calculate new cursor position based on direction
        x, y = self.path_cursor
        if direction == 'w':  # Forward/Up
            new_pos = (x, y - 1)
        elif direction == 's':  # Backward/Down
            new_pos = (x, y + 1)
        elif direction == 'a':  # Right (swapped)
            new_pos = (x + 1, y)
        elif direction == 'd':  # Left (swapped)
            new_pos = (x - 1, y)
        else:
            return
            
        # Check if new position is valid (within movement range)
        if self.is_valid_move_destination(new_pos[0], new_pos[1]):
            # Calculate the distance from unit's starting position to the new position
            total_distance = abs(new_pos[0] - self.selected_unit.x) + abs(new_pos[1] - self.selected_unit.y)
            
            # Don't allow path to exceed movement points
            if total_distance > self.selected_unit.current_move_points:
                return
            
            # Update path cursor
            self.path_cursor = new_pos
            
            # Update current path
            if new_pos not in self.current_path:
                # Add to path if not already in it
                self.current_path.append(new_pos)
            else:
                # If position is already in path, truncate path to that point
                path_index = self.current_path.index(new_pos)
                self.current_path = self.current_path[:path_index + 1]
            
            # Update highlights
            self.update_path_highlights()
    
    def show_action_modal(self, unit):
        """Show modal with available actions for the selected unit"""
        if not unit:
            return
            
        # Create action buttons dynamically based on unit's action options
        action_buttons = []
        
        def create_action_callback(action_name):
            def action_callback():
                self.handle_action_selection(action_name, unit)
                self.action_modal.enabled = False
                destroy(self.action_modal)
                self.action_modal = None
            return action_callback
        
        # Create buttons for each action option
        for action in unit.action_options:
            btn = Button(text=action, color=color.azure)
            btn.on_click = create_action_callback(action)
            action_buttons.append(btn)
        
        # Add cancel button
        cancel_btn = Button(text='Cancel', color=color.red)
        def cancel_action():
            self.action_modal.enabled = False
            destroy(self.action_modal)
            self.action_modal = None
            
        cancel_btn.on_click = cancel_action
        action_buttons.append(cancel_btn)
        
        # Create content tuple
        content = [Text(f'Select action for {unit.name}:')] + action_buttons
        
        # Create modal window
        self.action_modal = WindowPanel(
            title='Unit Actions',
            content=tuple(content),
            popup=True
        )
        
        # Center the window panel
        self.action_modal.y = self.action_modal.panel.scale_y / 2 * self.action_modal.scale_y
        self.action_modal.layout()
    
    def handle_action_selection(self, action_name, unit):
        """Handle the selected action for a unit"""
        print(f"{unit.name} selected action: {action_name}")
        
        if action_name == "Move":
            # Enter movement mode - user can now use WASD to plan movement
            self.current_mode = "move"
            print("Movement mode activated. Use WASD to plan movement, Enter to confirm. Core")
        elif action_name == "Attack":
            # Enter attack mode
            self.current_mode = "attack"
            self.handle_attack(unit)
        elif action_name == "Spirit":
            print("Spirit action selected - functionality to be implemented")
            # TODO: Implement spirit abilities
        elif action_name == "Magic":
            print("Magic action selected - functionality to be implemented")
            # TODO: Implement magic spells
        elif action_name == "Inventory":
            print("Inventory action selected - functionality to be implemented")
            # TODO: Implement inventory management
        else:
            print(f"Unknown action: {action_name}")
    
    def handle_attack(self, unit):
        """Handle attack action - highlight attack range"""
        if not unit:
            return
            
        print(f"{unit.name} entering attack mode. Attack range: {unit.attack_range}")
        
        # Clear existing highlights and show attack range
        self.clear_highlights()
        self.highlight_selected_unit()
        self.highlight_attack_range(unit)
        
        print("Click on a target within red highlighted tiles to attack.")
    
    def handle_attack_target_selection(self, x, y):
        """Handle tile clicks when in attack mode"""
        if not self.selected_unit:
            return
            
        # Check if clicked tile is within attack range
        distance = abs(x - self.selected_unit.x) + abs(y - self.selected_unit.y)
        if distance <= self.selected_unit.attack_range and distance > 0:
            # Valid attack target tile
            self.attack_target_tile = (x, y)
            
            # Clear highlights and show attack effect area
            self.clear_highlights()
            self.highlight_selected_unit()
            self.highlight_attack_range(self.selected_unit)
            self.highlight_attack_effect_area(x, y)
            
            # Show attack confirmation modal
            self.show_attack_confirmation(x, y)
        else:
            print(f"Target at ({x}, {y}) is out of attack range!")
    
    def highlight_attack_effect_area(self, target_x, target_y):
        """Highlight the attack effect area around the target tile"""
        if not self.selected_unit:
            return
            
        effect_radius = self.selected_unit.attack_effect_area
        
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                # Calculate Manhattan distance from target tile to this tile
                distance = abs(x - target_x) + abs(y - target_y)
                
                # Highlight tiles within effect area
                if distance <= effect_radius:
                    tile = self.get_tile_at(x, y)
                    if tile:
                        if (x, y) == (target_x, target_y):
                            # Target tile gets special color
                            tile.highlight(color.orange)
                        else:
                            # Effect area tiles
                            tile.highlight(color.yellow)
    
    def show_attack_confirmation(self, target_x, target_y):
        """Show modal to confirm attack on target tile"""
        if not self.selected_unit or not self.attack_target_tile:
            return
            
        # Find units that would be affected by the attack
        affected_units = self.get_units_in_effect_area(target_x, target_y)
        unit_list = affected_units  # Move unit_list declaration here
        
        # Create confirmation buttons
        confirm_btn = Button(text='Confirm Attack', color=color.red)
        cancel_btn = Button(text='Cancel', color=color.gray)
        
        # Set up button callbacks
        def confirm_attack():
            print(f"{self.selected_unit.name} attacks tile ({target_x}, {target_y})!")
            
            # Apply damage to each unit in unit_list
            attack_damage = self.selected_unit.physical_attack
            for target_unit in unit_list:
                print(f"  {target_unit.name} takes {attack_damage} physical damage!")
                target_unit.take_damage(attack_damage, "physical")
                
                if not target_unit.alive:
                    print(f"  {target_unit.name} has been defeated!")
                    # Remove dead unit from grid
                    if (target_unit.x, target_unit.y) in self.grid.units:
                        del self.grid.units[(target_unit.x, target_unit.y)]
                    
                    # Remove unit entity from scene
                    for entity in self.unit_entities:
                        if entity.unit == target_unit:
                            destroy(entity)
                            self.unit_entities.remove(entity)
                            break
            
            if self.attack_modal:
                self.attack_modal.enabled = False
                destroy(self.attack_modal)
                self.attack_modal = None
            # Return to normal mode
            self.current_mode = None
            self.attack_target_tile = None
            self.clear_highlights()
            self.highlight_selected_unit()
            
        def cancel_attack():
            # Return to attack mode without attacking
            self.clear_highlights()
            self.highlight_selected_unit()
            self.highlight_attack_range(self.selected_unit)
            if self.attack_modal:
                self.attack_modal.enabled = False
                destroy(self.attack_modal)
                self.attack_modal = None
        
        confirm_btn.on_click = confirm_attack
        cancel_btn.on_click = cancel_attack
        
        # Create modal content
        unit_names = ", ".join([unit.name for unit in unit_list]) if unit_list else "No units"
        
        # Create modal window
        self.attack_modal = WindowPanel(
            title='Confirm Attack',
            content=(
                Text(f'{self.selected_unit.name} attacks tile ({target_x}, {target_y})'),
                Text(f'Attack damage: {self.selected_unit.physical_attack}'),
                Text(f'Units in effect area: {unit_names}'),
                confirm_btn,
                cancel_btn
            ),
            popup=True
        )
        
        # Center the window panel
        self.attack_modal.y = self.attack_modal.panel.scale_y / 2 * self.attack_modal.scale_y
        self.attack_modal.layout()
    
    def get_units_in_effect_area(self, target_x, target_y):
        """Get all units within the attack effect area"""
        affected_units = []
        effect_radius = self.selected_unit.attack_effect_area
        
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                # Calculate distance from target tile
                distance = abs(x - target_x) + abs(y - target_y)
                
                # Check if tile is within effect area and has a unit
                if distance <= effect_radius and (x, y) in self.grid.units:
                    unit = self.grid.units[(x, y)]
                    # Don't include the attacking unit itself
                    if unit != self.selected_unit:
                        affected_units.append(unit)
        
        return affected_units
            
    def show_movement_confirmation(self):
        """Show modal to confirm unit movement"""
        if not self.path_cursor or not self.selected_unit:
            return
            
        # Create confirmation buttons
        confirm_btn = Button(text='Confirm Move', color=color.green)
        cancel_btn = Button(text='Cancel', color=color.red)
        
        # Set up button callbacks
        def confirm_move():
            self.execute_movement()
            self.movement_modal.enabled = False
            destroy(self.movement_modal)
            self.movement_modal = None
            
        def cancel_move():
            self.movement_modal.enabled = False
            destroy(self.movement_modal)
            self.movement_modal = None
        
        confirm_btn.on_click = confirm_move
        cancel_btn.on_click = cancel_move
        
        # Create modal window
        self.movement_modal = WindowPanel(
            title='Confirm Movement',
            content=(
                Text(f'Move {self.selected_unit.name} to position ({self.path_cursor[0]}, {self.path_cursor[1]})?'),
                Text(f'This will use {self.calculate_path_cost()} movement points.'),
                confirm_btn,
                cancel_btn
            ),
            popup=True
        )
        
        # Center the window panel
        self.movement_modal.y = self.movement_modal.panel.scale_y / 2 * self.movement_modal.scale_y
        self.movement_modal.layout()
    
    def calculate_path_cost(self):
        """Calculate the movement cost of the current path"""
        if not self.path_cursor or not self.selected_unit:
            return 0
        return abs(self.path_cursor[0] - self.selected_unit.x) + abs(self.path_cursor[1] - self.selected_unit.y)
    
    def execute_movement(self):
        """Execute the planned movement"""
        if not self.path_cursor or not self.selected_unit:
            return
            
        # Move unit to cursor position
        if self.grid.move_unit(self.selected_unit, self.path_cursor[0], self.path_cursor[1]):
            self.update_unit_positions()
            # Clear selection and path
            self.selected_unit = None
            self.current_path = []
            self.path_cursor = None
            self.clear_highlights()
            print(f"Unit moved successfully. Press END TURN when ready.")
    
    def is_valid_move_destination(self, x, y):
        """Check if a position is within the unit's movement range"""
        if not self.selected_unit:
            return False
            
        # Calculate total distance from unit's starting position
        total_distance = abs(x - self.selected_unit.x) + abs(y - self.selected_unit.y)
        
        # Check if within movement points and valid grid position
        return (total_distance <= self.selected_unit.current_move_points and 
                0 <= x < self.grid.width and 
                0 <= y < self.grid.height and
                (x, y) not in self.grid.units)
    
    def update_path_highlights(self):
        """Update tile highlights to show movement range and current path"""
        # Clear existing highlights
        self.clear_highlights()
        
        if not self.selected_unit:
            return
            
        # Highlight selected unit
        self.highlight_selected_unit()
        
        # Highlight all valid movement tiles in green
        self.highlight_movement_range()
        
        # Highlight current path in blue (override green)
        for pos in self.current_path:
            tile = self.get_tile_at(pos[0], pos[1])
            if tile:
                tile.highlight(color.blue)
        
        # Highlight cursor position in yellow
        if self.path_cursor:
            cursor_tile = self.get_tile_at(self.path_cursor[0], self.path_cursor[1])
            if cursor_tile:
                cursor_tile.highlight(color.yellow)
                    
    def highlight_attack_range(self, unit):
        """Highlight all tiles within the unit's attack range in red"""
        if not unit:
            return
            
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                # Calculate Manhattan distance from unit to tile
                distance = abs(x - unit.x) + abs(y - unit.y)
                
                # Highlight tiles within attack range (excluding unit's own tile)
                if distance <= unit.attack_range and distance > 0:
                    # Check if tile is within grid bounds
                    if 0 <= x < self.grid.width and 0 <= y < self.grid.height:
                        tile = self.get_tile_at(x, y)
                        if tile:
                            tile.highlight(color.red)
                    
    def clear_highlights(self):
        """Clear all tile and unit highlights"""
        for tile in self.tile_entities:
            tile.unhighlight()
        for entity in self.unit_entities:
            entity.unhighlight()

    def refresh_all_ap(self):
        """Refresh action points for all units"""
        for unit in self.units:
            unit.ap = unit.max_ap
            unit.current_move_points = unit.move_points  # Reset movement points

    def update_unit_positions(self):
        """Update the 3D positions of unit entities to match their grid positions"""
        for entity in self.unit_entities:
            entity.position = (entity.unit.x, 1.0, entity.unit.y)
