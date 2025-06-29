"""
Tactical RPG Main Game Controller

Central controller managing all aspects of the tactical RPG game.
Extracted from apex-tactics.py for better modularity and organization.
"""

from typing import List, Optional, Tuple, Dict, Any

try:
    from ursina import Entity, color, destroy, Button, Text, WindowPanel, camera
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

# Core ECS imports
from core.ecs.world import World
from core.math.pathfinding import AStarPathfinder

# Component imports
from components.gameplay.unit_type import UnitType
from components.combat.damage import AttackType

# Legacy wrapper imports
from game.legacy.unit_wrapper import Unit
from game.legacy.battle_grid_wrapper import BattleGrid
from game.legacy.turn_manager_wrapper import TurnManager

# UI system imports
from ui.camera.camera_controller import CameraController
from ui.visual.grid_visualizer import GridVisualizer
from ui.visual.tile_highlighter import TileHighlighter
from ui.visual.unit_renderer import UnitEntity
from ui.interaction.interaction_manager import InteractionManager
from ui.panels.control_panel import ControlPanel


class TacticalRPG:
    """
    Main game controller for the tactical RPG.
    
    Manages all game systems including:
    - ECS World and entities
    - Grid and unit management
    - Turn management and combat flow
    - Camera controls and visual systems
    - User input and interaction
    """
    
    def __init__(self, control_panel_callback: Optional[callable] = None, control_panel: Optional[ControlPanel] = None):
        """
        Initialize the tactical RPG game controller.
        
        Args:
            control_panel_callback: Optional callback to get control panel reference
            control_panel: Optional direct reference to control panel instance
        """
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for TacticalRPG")
        
        # Initialize ECS World
        self.world = World()
        
        # Legacy components for backwards compatibility
        self.grid = BattleGrid()
        self.units: List[Unit] = []
        self.unit_entities: List[UnitEntity] = []
        self.turn_manager: Optional[TurnManager] = None
        self.selected_unit: Optional[Unit] = None
        self.current_path: List[Tuple[int, int]] = []  # Track the selected movement path
        self.path_cursor: Optional[Tuple[int, int]] = None  # Current position in path selection
        self.movement_modal: Optional[Any] = None  # Reference to movement confirmation modal
        self.action_modal: Optional[Any] = None  # Reference to action selection modal
        self.current_mode: Optional[str] = None  # Track current action mode: 'move', 'attack', etc.
        self.attack_modal: Optional[Any] = None  # Reference to attack confirmation modal
        self.attack_target_tile: Optional[Tuple[int, int]] = None  # Currently targeted attack tile
        
        # Store control panel callback for camera updates
        self.control_panel_callback = control_panel_callback
        
        # Initialize camera controller
        self.camera_controller = CameraController(
            self.grid.width, 
            self.grid.height, 
            mode_change_callback=self._on_camera_mode_change
        )
        
        # Initialize pathfinder first (required by other systems)
        try:
            self.pathfinder = AStarPathfinder(self.grid.grid)
            print("✓ AStarPathfinder initialized successfully")
        except Exception as e:
            print(f"⚠ Could not initialize AStarPathfinder: {e}")
            self.pathfinder = None
        
        # Initialize grid visualizer (requires pathfinder)
        if self.pathfinder:
            try:
                self.grid_visualizer = GridVisualizer(self.grid.grid, self.pathfinder)
                print("✓ GridVisualizer initialized successfully")
            except Exception as e:
                print(f"⚠ Could not initialize GridVisualizer: {e}")
                self.grid_visualizer = None
        else:
            print("⚠ Skipping GridVisualizer - AStarPathfinder not available")
            self.grid_visualizer = None
        
        # Initialize tile highlighter (requires grid visualizer)
        if self.grid_visualizer:
            try:
                self.tile_highlighter = TileHighlighter(self.grid_visualizer)
                print("✓ TileHighlighter initialized successfully")
            except Exception as e:
                print(f"⚠ Could not initialize TileHighlighter: {e}")
                self.tile_highlighter = None
        else:
            print("⚠ Skipping TileHighlighter - GridVisualizer not available")
            self.tile_highlighter = None
        
        # Initialize interaction manager for enhanced UI (only if all dependencies available)
        if self.grid_visualizer and self.pathfinder:
            try:
                self.interaction_manager = InteractionManager(
                    self.grid.grid, 
                    self.pathfinder, 
                    self.grid_visualizer
                )
                print("✓ InteractionManager initialized successfully")
            except Exception as e:
                print(f"⚠ Could not initialize InteractionManager: {e}")
                self.interaction_manager = None
        else:
            print("⚠ Skipping InteractionManager - missing dependencies")
            self.interaction_manager = None
        
        # Initialize highlight entities list for cleanup
        self.highlight_entities: List[Entity] = []
        
        # Use passed control panel or create one if none provided
        if control_panel:
            self.control_panel = control_panel
            # Set game reference if not already set
            if hasattr(self.control_panel, 'set_game_reference'):
                self.control_panel.set_game_reference(self)
        else:
            # Fallback: create control panel if none provided
            self.control_panel = ControlPanel(game_reference=self)
        
        # Setup initial battle
        self.setup_battle()
    
    def _on_camera_mode_change(self, mode: int):
        """Handle camera mode changes."""
        if self.control_panel_callback:
            try:
                control_panel = self.control_panel_callback()
                if control_panel:
                    control_panel.update_camera_mode(mode)
            except Exception as e:
                print(f"⚠ Error updating control panel camera mode: {e}")
    
    def setup_battle(self):
        """Initialize the battle with units and systems."""
        # Initialize ECS systems
        try:
            from systems.stat_system import StatSystem
            from systems.movement_system import MovementSystem
            from systems.combat_system import CombatSystem
            
            # Add systems to world
            self.world.add_system(StatSystem())
            self.world.add_system(MovementSystem())
            self.world.add_system(CombatSystem())
            
            print("✓ ECS systems initialized successfully")
        except ImportError as e:
            print(f"⚠ Could not import all ECS systems: {e}")
            print("  Continuing with legacy components...")
        
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
        
        # Add units to both legacy and ECS systems
        for unit in self.units:
            self.grid.add_unit(unit)
            self.unit_entities.append(UnitEntity(unit))
            
            # Register unit entity with ECS world entity manager
            try:
                self.world.entity_manager._register_entity(unit.entity)
                print(f"✓ Registered {unit.name} with ECS World")
            except Exception as e:
                print(f"⚠ Could not register {unit.name} with ECS World: {e}")
        
        self.turn_manager = TurnManager(self.units)
        self.refresh_all_ap()
        
        print(f"✓ Battle setup complete: {len(self.units)} units, ECS World with {self.world.entity_count} entities")
    
    def end_current_turn(self):
        """End the current unit's turn and move to next unit."""
        if self.turn_manager:
            # Clear current selection
            self.clear_highlights()
            self.selected_unit = None
            
            # Move to next turn
            self.turn_manager.next_turn()
            
            # Update control panel with new current unit
            current_unit = self.turn_manager.current_unit()
            if self.control_panel_callback:
                try:
                    control_panel = self.control_panel_callback()
                    if control_panel:
                        control_panel.update_unit_info(current_unit)
                except Exception as e:
                    print(f"⚠ Error updating control panel: {e}")
            
            print(f"Turn ended. Now it's {current_unit.name}'s turn.")
    
    def handle_tile_click(self, x: int, y: int):
        """Handle clicks on grid tiles."""
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
            
            if self.control_panel_callback:
                try:
                    control_panel = self.control_panel_callback()
                    if control_panel:
                        control_panel.update_unit_info(clicked_unit)
                except Exception as e:
                    print(f"⚠ Error updating control panel: {e}")
            
            # Show action modal for the selected unit
            self.show_action_modal(clicked_unit)
        else:
            # Clicked on an empty tile
            if self.current_mode == "move":
                # In movement mode - don't clear selection, this could be path planning
                return
            else:
                # Not in movement mode - clear selection
                self.selected_unit = None
                self.current_path = []
                self.path_cursor = None
                self.current_mode = None
                if self.control_panel_callback:
                    try:
                        control_panel = self.control_panel_callback()
                        if control_panel:
                            control_panel.update_unit_info(None)
                    except Exception as e:
                        print(f"⚠ Error updating control panel: {e}")
    
    # Complete TacticalRPG controller implementation
    
    def refresh_all_ap(self):
        """Reset action points for all units."""
        for unit in self.units:
            unit.ap = unit.max_ap
            unit.current_move_points = unit.move_points  # Reset movement points

    def update_unit_positions(self):
        """Update visual positions of all unit entities."""
        for entity in self.unit_entities:
            entity.position = (entity.unit.x + 0.5, 1.0, entity.unit.y + 0.5)  # Center on grid tiles
    
    def clear_highlights(self):
        """Clear all highlighting."""
        # Clear unit highlighting
        for entity in self.unit_entities:
            entity.unhighlight()
        
        # Clear tile highlight entities
        if hasattr(self, 'highlight_entities'):
            for highlight in self.highlight_entities:
                destroy(highlight)
            self.highlight_entities = []
        
        # Clear tile highlighting through modular system (if available)
        if self.tile_highlighter:
            self.tile_highlighter.clear_all_highlights()
    
    def highlight_selected_unit(self):
        """Highlight the currently selected unit."""
        if self.selected_unit:
            for entity in self.unit_entities:
                if entity.unit == self.selected_unit:
                    entity.highlight_selected()
                    break
    
    def highlight_movement_range(self):
        """Highlight all tiles the selected unit can move to."""
        if not self.selected_unit:
            return
        
        # Clear existing highlight entities
        self.clear_highlights()
        
        highlight_count = 0
        # Create highlight entities for movement range
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                distance = abs(x - self.selected_unit.x) + abs(y - self.selected_unit.y)
                if distance <= self.selected_unit.current_move_points and self.grid.is_valid(x, y):
                    if distance == 0:
                        # Current position - different color
                        highlight_color = color.white
                    else:
                        # Valid movement range
                        highlight_color = color.green
                    
                    # Create highlight overlay entity
                    highlight = Entity(
                        model='cube',
                        color=highlight_color,
                        scale=(0.9, 0.2, 0.9),
                        position=(x + 0.5, 0, y + 0.5),  # Center on tile, same level as grid
                        alpha=0.5  # Same transparency as grid
                    )
                    # Store in a list for cleanup
                    if not hasattr(self, 'highlight_entities'):
                        self.highlight_entities = []
                    self.highlight_entities.append(highlight)
                    highlight_count += 1
    
    def handle_path_movement(self, direction: str):
        """Handle path movement and confirmation."""
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
        """Show modal with available actions for the selected unit."""
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
    
    def handle_action_selection(self, action_name: str, unit):
        """Handle the selected action for a unit."""
        print(f"{unit.name} selected action: {action_name}")
        
        if action_name == "Move":
            # Enter movement mode - user can now use WASD to plan movement
            self.current_mode = "move"
            print("Movement mode activated. Use WASD to plan movement, Enter to confirm. Tactical")
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
        """Handle attack action - highlight attack range."""
        if not unit:
            return
            
        print(f"{unit.name} entering attack mode. Attack range: {unit.attack_range}")
        
        # Clear existing highlights and show attack range
        self.clear_highlights()
        self.highlight_selected_unit()
        self.highlight_attack_range(unit)
        
        print("Click on a target within red highlighted tiles to attack.")
    
    def handle_attack_target_selection(self, x: int, y: int):
        """Handle tile clicks when in attack mode."""
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
    
    def highlight_attack_effect_area(self, target_x: int, target_y: int):
        """Highlight the attack effect area around the target tile."""
        if not self.selected_unit:
            return
        
        effect_radius = self.selected_unit.attack_effect_area
        
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                # Calculate Manhattan distance from target tile to this tile
                distance = abs(x - target_x) + abs(y - target_y)
                
                # Highlight tiles within effect area
                if distance <= effect_radius:
                    if (x, y) == (target_x, target_y):
                        # Target tile gets special color
                        highlight_color = color.orange
                    else:
                        # Effect area tiles
                        highlight_color = color.yellow
                    
                    # Create highlight overlay entity
                    highlight = Entity(
                        model='cube',
                        color=highlight_color,
                        scale=(0.9, 0.2, 0.9),
                        position=(x + 0.5, 0, y + 0.5),  # Center on tile, same level as grid
                        alpha=0.5  # Same transparency as grid
                    )
                    # Store in a list for cleanup
                    if not hasattr(self, 'highlight_entities'):
                        self.highlight_entities = []
                    self.highlight_entities.append(highlight)
    
    def show_attack_confirmation(self, target_x: int, target_y: int):
        """Show modal to confirm attack on target tile."""
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
                target_unit.take_damage(attack_damage, AttackType.PHYSICAL)
                
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
    
    def get_units_in_effect_area(self, target_x: int, target_y: int) -> List[Any]:
        """Get all units within the attack effect area."""
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
        """Show modal to confirm unit movement."""
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
    
    def calculate_path_cost(self) -> int:
        """Calculate the movement cost of the current path."""
        if not self.path_cursor or not self.selected_unit:
            return 0
        return abs(self.path_cursor[0] - self.selected_unit.x) + abs(self.path_cursor[1] - self.selected_unit.y)
    
    def execute_movement(self):
        """Execute the planned movement."""
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
            if self.control_panel_callback:
                try:
                    control_panel = self.control_panel_callback()
                    if control_panel:
                        control_panel.update_unit_info(None)
                except Exception as e:
                    print(f"⚠ Error updating control panel: {e}")
            print(f"Unit moved successfully. Press END TURN when ready.")
    
    def is_valid_move_destination(self, x: int, y: int) -> bool:
        """Check if a position is within the unit's movement range."""
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
        """Update tile highlights to show movement range and current path."""
        # Clear existing highlights
        self.clear_highlights()
        
        if not self.selected_unit:
            return
            
        # Highlight selected unit
        self.highlight_selected_unit()
        
        # Highlight all valid movement tiles
        self.highlight_movement_range()
        
        # Highlight current path in blue (override green)
        for pos in self.current_path:
            highlight = Entity(
                model='cube',
                color=color.blue,
                scale=(0.9, 0.2, 0.9),
                position=(pos[0] + 0.5, 0, pos[1] + 0.5),  # Center on tile, same level as grid
                alpha=0.5  # Same transparency as grid
            )
            # Store in a list for cleanup
            if not hasattr(self, 'highlight_entities'):
                self.highlight_entities = []
            self.highlight_entities.append(highlight)
        
        # Highlight cursor position in yellow
        if self.path_cursor:
            highlight = Entity(
                model='cube',
                color=color.yellow,
                scale=(0.9, 0.2, 0.9),
                position=(self.path_cursor[0] + 0.5, 0, self.path_cursor[1] + 0.5),  # Center on tile, same level as grid
                alpha=0.5  # Same transparency as grid
            )
            if not hasattr(self, 'highlight_entities'):
                self.highlight_entities = []
            self.highlight_entities.append(highlight)
                    
    def highlight_attack_range(self, unit):
        """Highlight all tiles within the unit's attack range in red."""
        if not unit:
            return
        
        # Clear existing highlights first
        self.clear_highlights()
        
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                # Calculate Manhattan distance from unit to tile
                distance = abs(x - unit.x) + abs(y - unit.y)
                
                # Highlight tiles within attack range (excluding unit's own tile)
                if distance <= unit.attack_range and distance > 0:
                    # Check if tile is within grid bounds
                    if 0 <= x < self.grid.width and 0 <= y < self.grid.height:
                        # Create highlight overlay entity
                        highlight = Entity(
                            model='cube',
                            color=color.red,
                            scale=(0.9, 0.2, 0.9),
                            position=(x + 0.5, 0, y + 0.5),  # Center on tile, same level as grid
                            alpha=0.5  # Same transparency as grid
                        )
                        # Store in a list for cleanup
                        if not hasattr(self, 'highlight_entities'):
                            self.highlight_entities = []
                        self.highlight_entities.append(highlight)
    
    def get_tile_at(self, x: int, y: int):
        """Get tile at position (legacy compatibility)."""
        # Using modular grid system - no individual tile entities
        return None
        
    def highlight_possible_moves(self):
        """Highlight possible moves (legacy compatibility)."""
        # This method is now replaced by highlight_movement_range
        self.highlight_movement_range()
    
    def handle_input(self, key: str):
        """
        Handle keyboard input for the tactical RPG game.
        
        Args:
            key: The key that was pressed
        """
        # Handle 'r' key to toggle control panel visibility
        if key == 'r':
            if hasattr(self, 'control_panel') and self.control_panel:
                self.control_panel.toggle_visibility()
                return True
        
        # Handle camera controls if no other input was processed
        if hasattr(self, 'camera_controller') and self.camera_controller:
            self.camera_controller.handle_input(key)
        
        return False
