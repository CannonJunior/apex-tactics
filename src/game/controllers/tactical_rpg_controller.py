"""
Tactical RPG Main Game Controller

Central controller managing all aspects of the tactical RPG game.
Extracted from apex-tactics.py for better modularity and organization.
"""

from typing import List, Optional, Tuple, Dict, Any

try:
    from ursina import Entity, color, destroy, Button, Text, WindowPanel, camera
    from ursina.prefabs.health_bar import HealthBar
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

# Core ECS imports
from core.ecs.world import World
from core.math.pathfinding import AStarPathfinder
from core.math.vector import Vector2Int
from core.math.grid import TacticalGrid

# Component imports
from core.models.unit_types import UnitType
from components.combat.damage import AttackType

# Legacy model imports
from core.models.unit import Unit
from core.game.battle_grid import BattleGrid
from core.game.turn_manager import TurnManager

# UI system imports
from ui.camera.camera_controller import CameraController
from ui.visual.grid_visualizer import GridVisualizer
from ui.visual.tile_highlighter import TileHighlighter
from ui.visual.unit_renderer import UnitEntity
from ui.battlefield.grid_tile import GridTile
from ui.interaction.interaction_manager import InteractionManager
from ui.panels.control_panel import CharacterAttackInterface
from ui.core.ui_style_manager import get_ui_style_manager


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
    
    def __init__(self, control_panel_callback: Optional[callable] = None, control_panel: Optional[CharacterAttackInterface] = None):
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
        self.tile_entities: List[Any] = []  # Grid tiles for mouse interaction
        self.turn_manager: Optional[TurnManager] = None
        self.selected_unit: Optional[Unit] = None
        self.current_path: List[Tuple[int, int]] = []  # Track the selected movement path
        self.path_cursor: Optional[Tuple[int, int]] = None  # Current position in path selection
        self.movement_modal: Optional[Any] = None  # Reference to movement confirmation modal
        self.action_modal: Optional[Any] = None  # Reference to action selection modal
        self.current_mode: Optional[str] = None  # Track current action mode: 'move', 'attack', etc.
        self.attack_modal: Optional[Any] = None  # Reference to attack confirmation modal
        self.attack_target_tile: Optional[Tuple[int, int]] = None  # Currently targeted attack tile
        self.health_bar: Optional[HealthBar] = None  # Health bar for selected unit
        self.health_bar_label: Optional[Any] = None  # Health bar label
        self.resource_bar: Optional[HealthBar] = None  # Resource bar for selected unit
        self.resource_bar_label: Optional[Any] = None  # Resource bar label
        self.control_panel: Optional[Any] = None  # Reference to character attack interface for UI updates
        
        # Store control panel callback for camera updates
        self.control_panel_callback = control_panel_callback
        
        # Initialize camera controller
        self.camera_controller = CameraController(
            self.grid.width, 
            self.grid.height
        )
        
        # Initialize pathfinder first (required by other systems)
        try:
            # Create a TacticalGrid for pathfinding (BattleGrid is for legacy unit management)
            self.tactical_grid = TacticalGrid(self.grid.width, self.grid.height)
            self.pathfinder = AStarPathfinder(self.tactical_grid)
            print("✓ AStarPathfinder initialized successfully")
        except Exception as e:
            print(f"⚠ Could not initialize AStarPathfinder: {e}")
            self.pathfinder = None
            self.tactical_grid = None
        
        # Initialize grid visualizer (disabled to avoid conflicts with direct Entity highlighting)
        # if self.pathfinder and self.tactical_grid:
        #     try:
        #         self.grid_visualizer = GridVisualizer(self.tactical_grid, self.pathfinder)
        #         print("✓ GridVisualizer initialized successfully")
        #     except Exception as e:
        #         print(f"⚠ Could not initialize GridVisualizer: {e}")
        #         self.grid_visualizer = None
        # else:
        #     print("⚠ Skipping GridVisualizer - AStarPathfinder not available")
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
        if self.grid_visualizer and self.pathfinder and self.tactical_grid:
            try:
                self.interaction_manager = InteractionManager(
                    self.tactical_grid, 
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
            self.control_panel = CharacterAttackInterface(game_reference=self)
        
        # Setup initial battle
        self.setup_battle()
    
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
        
        # Create grid tiles for mouse interaction
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                self.tile_entities.append(GridTile(x, y, self))
        
        print(f"✓ Created {len(self.tile_entities)} grid tiles for mouse interaction")
        
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
        
        # Add units to both legacy and ECS systems
        for unit in self.units:
            # Set game controller reference for HP change notifications
            unit._game_controller = self
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
        
        # Now that turn_manager exists, create the unit carousel
        if hasattr(self.control_panel, 'create_unit_carousel'):
            self.control_panel.create_unit_carousel()
        
        print(f"✓ Battle setup complete: {len(self.units)} units, ECS World with {self.world.entity_count} entities")
    
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
        """End the current unit's turn and move to next unit."""
        if self.turn_manager:
            # Clear current selection
            self.clear_highlights()
            self.selected_unit = None
            self.hide_health_bar()
            
            # Move to next turn
            self.turn_manager.next_turn()
            
            # Update control panel with new current unit
            current_unit = self.turn_manager.current_unit()
            if self.control_panel:
                try:
                    self.control_panel.update_unit_info(current_unit)
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
            
            # Update control panel with selected unit info
            if self.control_panel:
                try:
                    self.control_panel.update_unit_info(clicked_unit)
                except Exception as e:
                    print(f"⚠ Error updating control panel: {e}")
            
            # Create/update health bar and resource bar for selected unit
            self.update_health_bar(clicked_unit)
            self.update_resource_bar(clicked_unit)
            
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
                self.hide_health_bar()
                self.hide_resource_bar()
                # Clear control panel unit info
                if self.control_panel:
                    try:
                        self.control_panel.update_unit_info(None)
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
                        position=(x + 0.5, 0, y + 0.5),  # Same height as grid tiles
                        alpha=1.0  # Same transparency as grid
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
    
    def handle_mouse_movement(self, clicked_tile: Tuple[int, int]) -> bool:
        """
        Handle mouse click for movement path creation.
        
        Args:
            clicked_tile: (x, y) coordinates of clicked tile
            
        Returns:
            True if click was handled, False otherwise
        """
        if not self.selected_unit or self.current_mode != "move":
            return False
        
        if not self.pathfinder:
            print("⚠ Pathfinder not available - falling back to manual path building")
            return False
        
        # Convert coordinates to Vector2Int for pathfinder
        start_pos = Vector2Int(self.selected_unit.x, self.selected_unit.y)
        end_pos = Vector2Int(clicked_tile[0], clicked_tile[1])
        
        # Check if clicking on same tile as unit (no movement needed)
        if start_pos.x == end_pos.x and start_pos.y == end_pos.y:
            return True
        
        # Calculate path using pathfinder
        try:
            calculated_path = self.pathfinder.calculate_movement_path(
                start_pos, 
                end_pos, 
                float(self.selected_unit.current_move_points)
            )
            
            if calculated_path and len(calculated_path) > 1:
                # Convert Vector2Int path back to tuple format (excluding start position)
                self.current_path = [(pos.x, pos.y) for pos in calculated_path[1:]]
                self.path_cursor = (end_pos.x, end_pos.y)
                
                # Update visual highlights
                self.update_path_highlights()
                
                print(f"Path calculated: {len(self.current_path)} steps to ({end_pos.x}, {end_pos.y})")
                return True
            else:
                # No valid path found - try to get as close as possible
                reachable_positions = self.pathfinder.find_reachable_positions(
                    start_pos, 
                    float(self.selected_unit.current_move_points)
                )
                
                if reachable_positions:
                    # Find closest reachable position to clicked tile
                    closest_pos = min(reachable_positions, 
                                    key=lambda pos: abs(pos.x - end_pos.x) + abs(pos.y - end_pos.y))
                    
                    # Calculate path to closest position
                    closest_path = self.pathfinder.calculate_movement_path(
                        start_pos,
                        closest_pos,
                        float(self.selected_unit.current_move_points)
                    )
                    
                    if closest_path and len(closest_path) > 1:
                        self.current_path = [(pos.x, pos.y) for pos in closest_path[1:]]
                        self.path_cursor = (closest_pos.x, closest_pos.y)
                        self.update_path_highlights()
                        
                        print(f"Target unreachable. Path to closest position: ({closest_pos.x}, {closest_pos.y})")
                        return True
                
                print(f"No valid path to ({end_pos.x}, {end_pos.y}) within movement range")
                return True
                
        except Exception as e:
            print(f"⚠ Error calculating path: {e}")
            return False
    
    def show_action_modal(self, unit):
        """Show modal with available actions for the selected unit."""
        if not unit:
            return
            
        # Create action buttons dynamically based on unit's action options
        action_buttons = []
        
        def create_action_callback(action_name):
            def action_callback():
                self.handle_action_selection(action_name, unit)
                # Hide the modal after action selection
                if self.action_modal:
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
            if self.action_modal:
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
                        position=(x + 0.5, 0, y + 0.5),  # Same height as grid tiles
                        alpha=1.0  # Same transparency as grid
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
            if self.movement_modal:
                self.movement_modal.enabled = False
                destroy(self.movement_modal)
                self.movement_modal = None
            
        def cancel_move():
            if self.movement_modal:
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
        
        # For mouse-generated paths, calculate actual path cost
        if self.current_path and self.pathfinder:
            try:
                # Convert current path to Vector2Int format
                start_pos = Vector2Int(self.selected_unit.x, self.selected_unit.y)
                path_positions = [start_pos] + [Vector2Int(pos[0], pos[1]) for pos in self.current_path]
                
                # Calculate actual path cost using grid movement costs
                total_cost = 0.0
                for i in range(len(path_positions) - 1):
                    cost = self.pathfinder.grid.get_movement_cost(path_positions[i], path_positions[i + 1])
                    if cost == float('inf'):
                        return 999  # Invalid path
                    total_cost += cost
                
                return int(total_cost)
            except Exception as e:
                print(f"⚠ Error calculating path cost: {e}")
                # Fallback to Manhattan distance
                pass
        
        # Fallback: Manhattan distance for WASD paths or when pathfinder unavailable
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
            self.hide_health_bar()
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
                alpha=1.0  # Same transparency as grid
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
                alpha=1.0  # Same transparency as grid
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
                            position=(x + 0.5, 0, y + 0.5),  # Same height as grid tiles
                            alpha=1.0  # Same transparency as grid
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
    
    def set_control_panel(self, control_panel):
        """Set reference to character attack interface for UI updates"""
        self.control_panel = control_panel
    
    def update_health_bar(self, unit):
        """Create or update health bar for the selected unit"""
        if self.health_bar:
            self.health_bar.enabled = False
            self.health_bar = None
        
        if self.health_bar_label:
            self.health_bar_label.enabled = False
            self.health_bar_label = None
        
        if unit:
            # Get UI style manager
            style_manager = get_ui_style_manager()
            
            # Create health bar label
            self.health_bar_label = Text(
                text="HP",
                parent=camera.ui,
                position=(-0.47, 0.45),  # Position to the left of health bar
                scale=1.0,
                color=style_manager.get_bar_label_color(),
                origin=(-0.5, 0)  # Right-align the text
            )
            
            self.health_bar = HealthBar(
                max_value=unit.max_hp,
                value=unit.hp,
                position=(-0.4, 0.45),
                parent=camera.ui,
                scale=(0.3, 0.03),
                color=style_manager.get_health_bar_color(),
                bg_color=style_manager.get_health_bar_bg_color()
            )
    
    def hide_health_bar(self):
        """Hide the health bar when no unit is selected"""
        if self.health_bar:
            self.health_bar.enabled = False
            self.health_bar = None
        
        if self.health_bar_label:
            self.health_bar_label.enabled = False
            self.health_bar_label = None
    
    def refresh_health_bar(self):
        """Refresh health bar to match selected unit's current HP"""
        if self.health_bar and self.selected_unit:
            self.health_bar.value = self.selected_unit.hp
    
    def on_unit_hp_changed(self, unit):
        """Called when a unit's HP changes to update health bar if it's the selected unit"""
        if self.selected_unit and self.selected_unit == unit:
            self.refresh_health_bar()
    
    def update_resource_bar(self, unit):
        """Create or update resource bar for the selected unit"""
        if self.resource_bar:
            self.resource_bar.enabled = False
            self.resource_bar = None
        
        if self.resource_bar_label:
            self.resource_bar_label.enabled = False
            self.resource_bar_label = None
        
        if unit:
            # Get UI style manager
            style_manager = get_ui_style_manager()
            
            # Get resource type and values based on unit type
            resource_type = unit.primary_resource_type
            resource_value = unit.get_primary_resource_value()
            resource_max = unit.get_primary_resource_max()
            
            # Get color and label from style manager
            bar_color = style_manager.get_resource_bar_color(resource_type)
            label_text = style_manager.get_resource_bar_label(resource_type)
            
            # Create resource bar label
            self.resource_bar_label = Text(
                text=label_text,
                parent=camera.ui,
                position=(-0.47, 0.4),  # Position to the left of resource bar
                scale=1.0,
                color=style_manager.get_bar_label_color(),
                origin=(-0.5, 0)  # Right-align the text
            )
            
            self.resource_bar = HealthBar(
                max_value=resource_max,
                value=resource_value,
                position=(-0.4, 0.4),  # Position just below health bar
                parent=camera.ui,
                scale=(0.3, 0.03),
                color=bar_color,
                bg_color=style_manager.get_resource_bar_bg_color()
            )
    
    def hide_resource_bar(self):
        """Hide the resource bar when no unit is selected"""
        if self.resource_bar:
            self.resource_bar.enabled = False
            self.resource_bar = None
        
        if self.resource_bar_label:
            self.resource_bar_label.enabled = False
            self.resource_bar_label = None
    
    def refresh_resource_bar(self):
        """Refresh resource bar to match selected unit's current resource value"""
        if self.resource_bar and self.selected_unit:
            self.resource_bar.value = self.selected_unit.get_primary_resource_value()
    
    def on_unit_resource_changed(self, unit):
        """Called when a unit's resource changes to update resource bar if it's the selected unit"""
        if self.selected_unit and self.selected_unit == unit:
            self.refresh_resource_bar()
