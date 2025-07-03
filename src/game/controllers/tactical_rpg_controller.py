"""
Tactical RPG Main Game Controller

Central controller managing all aspects of the tactical RPG game.
Extracted from apex-tactics.py for better modularity and organization.
"""

from typing import List, Optional, Tuple, Dict, Any

try:
    from ursina import Entity, color, destroy, Button, Text, WindowPanel, camera, Tooltip
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

# Character state management
from game.state.character_state_manager import get_character_state_manager, CharacterStateManager
from core.assets.unit_data_manager import get_unit_data_manager
from core.assets.config_manager import get_config_manager

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
        
        # Initialize character state management
        self.unit_data_manager = get_unit_data_manager()
        self.character_state_manager = get_character_state_manager(self.unit_data_manager)
        
        # Legacy components for backwards compatibility
        self.grid = BattleGrid()
        self.units: List[Unit] = []
        self.unit_entities: List[UnitEntity] = []
        self.tile_entities: List[Any] = []  # Grid tiles for mouse interaction
        self.turn_manager: Optional[TurnManager] = None
        self.active_unit: Optional[Unit] = None
        self.targeted_units: List[Unit] = []  # List of units targeted for effects
        self.current_path: List[Tuple[int, int]] = []  # Track the selected movement path
        self.path_cursor: Optional[Tuple[int, int]] = None  # Current position in path selection
        self.movement_modal: Optional[Any] = None  # Reference to movement confirmation modal
        self.action_modal: Optional[Any] = None  # Reference to action selection modal
        self.current_mode: Optional[str] = None  # Track current action mode: 'move', 'attack', etc.
        self.attack_modal: Optional[Any] = None  # Reference to attack confirmation modal
        self.attack_target_tile: Optional[Tuple[int, int]] = None  # Currently targeted attack tile
        self.attack_modal_from_double_click: bool = False  # Track if attack modal was triggered by double-click
        self.magic_modal: Optional[Any] = None  # Reference to magic confirmation modal
        self.magic_target_tile: Optional[Tuple[int, int]] = None  # Currently targeted magic tile
        self.magic_modal_from_double_click: bool = False  # Track if magic modal was triggered by double-click
        self.health_bar: Optional[HealthBar] = None  # Health bar for active unit
        self.health_bar_label: Optional[Any] = None  # Health bar label
        self.resource_bar: Optional[HealthBar] = None  # Resource bar for active unit
        self.resource_bar_label: Optional[Any] = None  # Resource bar label
        
        # Hotkey ability slots
        self.hotkey_slots: List[Button] = []  # Hotkey ability buttons
        self.hotkey_config: Optional[Dict[str, Any]] = None  # Hotkey configuration
        
        # Targeted unit bars (can be multiple units for area effects)
        self.targeted_health_bars: List[HealthBar] = []  # Health bars for targeted units
        self.targeted_health_bar_labels: List[Any] = []  # Labels for targeted health bars
        self.targeted_resource_bars: List[HealthBar] = []  # Resource bars for targeted units
        self.targeted_resource_bar_labels: List[Any] = []  # Labels for targeted resource bars
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
        
        # Initialize hotkey system after all variable declarations
        self._load_hotkey_config()
        self._create_hotkey_slots()
        
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
            
            # Add unit to TacticalGrid for obstacle tracking
            if self.tactical_grid:
                unit_pos = Vector2Int(unit.x, unit.y)
                # Use unit name and position as unique identifier
                unit_id = f"{unit.name}_{unit.x}_{unit.y}"
                self.tactical_grid.occupy_cell(unit_pos, unit_id)
            
            # Register unit entity with ECS world entity manager
            try:
                # Skip ECS registration for now since Unit class doesn't have entity attribute
                # TODO: Add proper ECS integration when Unit class is updated
                # self.world.entity_manager._register_entity(unit.entity)
                print(f"✓ Unit {unit.name} prepared for ECS (registration skipped)")
            except Exception as e:
                print(f"⚠ Could not register {unit.name} with ECS World: {e}")
        
        self.turn_manager = TurnManager(self.units)
        self.refresh_all_ap()
        
        # Now that turn_manager exists, create the unit carousel
        if hasattr(self.control_panel, 'create_unit_carousel'):
            self.control_panel.create_unit_carousel()
        
        # Auto-activate the first unit in turn order
        first_unit = self.turn_manager.current_unit()
        if first_unit:
            # Use centralized method for consistent behavior
            self.set_active_unit(first_unit, update_highlights=True, update_ui=True)
            print(f"✓ Auto-selected first unit: {first_unit.name} (Speed: {first_unit.speed})")
        
        print(f"✓ Battle setup complete: {len(self.units)} units, ECS World with {self.world.entity_count} entities")
    
    def set_active_unit(self, unit: Optional[Unit], update_highlights: bool = True, update_ui: bool = True):
        """
        Centralized method to set the active unit with full integration.
        
        This method ensures consistent behavior across all unit selection methods:
        - Mouse click on grid tiles
        - End Turn button 
        - Unit carousel buttons
        - Programmatic selection
        
        Args:
            unit: Unit to set as active, or None to clear selection
            update_highlights: Whether to update visual highlights
            update_ui: Whether to update UI elements (health bars, control panel)
        """
        # Store the new active unit
        self.active_unit = unit
        
        if unit is not None:
            # === Unit Selected ===
            
            # Reset path and cursor for new unit
            self.current_path = []
            self.path_cursor = (unit.x, unit.y)
            self.current_mode = None
            
            # Update character state manager with selected character
            if hasattr(unit, 'character_instance_id'):
                self.character_state_manager.set_active_character(unit.character_instance_id)
            else:
                # Create character instance for legacy units without instance IDs
                try:
                    character_instance = self.character_state_manager.create_character_instance(
                        unit.type, f"legacy_{unit.name}_{id(unit)}"
                    )
                    unit.character_instance_id = character_instance.instance_id
                    self.character_state_manager.set_active_character(character_instance.instance_id)
                except Exception as e:
                    print(f"Warning: Could not create character instance for {unit.name}: {e}")
                    self.character_state_manager.set_active_character(None)
            
            # Update visual highlights if requested
            if update_highlights:
                self.update_path_highlights()
            
            # Update UI elements if requested
            if update_ui:
                # Update control panel with selected unit info
                if self.control_panel:
                    try:
                        self.control_panel.update_unit_info(unit)
                    except Exception as e:
                        print(f"⚠ Error updating control panel: {e}")
                
                # Create/update health bar and resource bar for selected unit
                self.update_health_bar(unit)
                self.update_resource_bar(unit)
                
                # Update hotkey slots for selected character
                self.update_hotkey_slots()
        
        else:
            # === Unit Deselected ===
            
            # Clear path and mode
            self.current_path = []
            self.path_cursor = None
            self.current_mode = None
            
            # Clear character state manager active character
            self.character_state_manager.set_active_character(None)
            
            # Hide UI elements if requested
            if update_ui:
                self.hide_health_bar()
                self.hide_resource_bar()
                self.hide_hotkey_slots()
                
                # Clear control panel unit info
                if self.control_panel:
                    try:
                        self.control_panel.update_unit_info(None)
                    except Exception as e:
                        print(f"⚠ Error updating control panel: {e}")
    
    def clear_active_unit(self):
        """
        Clear the active unit selection.
        Convenience method that calls set_active_unit(None).
        """
        self.set_active_unit(None)
    
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
            self.clear_active_unit()
            
            # Move to next turn
            self.turn_manager.next_turn()
            
            # Auto-select the new current unit
            current_unit = self.turn_manager.current_unit()
            if current_unit:
                # Use centralized method for consistent behavior
                self.set_active_unit(current_unit, update_highlights=True, update_ui=True)
                
                # Update control panel with new current unit
                if self.control_panel:
                    try:
                        self.control_panel.update_unit_info(current_unit)
                    except Exception as e:
                        print(f"⚠ Error updating control panel: {e}")
                
                print(f"Turn ended. Now it's {current_unit.name}'s turn (Auto-selected).")
    
    def handle_tile_click(self, x: int, y: int):
        """Handle clicks on grid tiles."""
        # Handle attack targeting if in attack mode
        if self.current_mode == "attack" and self.active_unit:
            self.handle_attack_target_selection(x, y)
            return
        
        # Handle magic targeting if in magic mode
        if self.current_mode == "magic" and self.active_unit:
            self.handle_magic_target_selection(x, y)
            return
            
        # Clear any existing highlights
        self.clear_highlights()
        
        # Check if there's a unit on the clicked tile
        if (x, y) in self.grid.units:
            clicked_unit = self.grid.units[(x, y)]
            
            # Use centralized method for consistent behavior
            self.set_active_unit(clicked_unit, update_highlights=True, update_ui=True)
            
            # Show action modal for the selected unit
            self.show_action_modal(clicked_unit)
        else:
            # Clicked on an empty tile
            if self.current_mode == "move":
                # In movement mode - don't clear selection, this could be path planning
                return
            else:
                # Not in movement mode - clear selection using centralized method
                self.clear_active_unit()
    
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
    
    def highlight_active_unit(self):
        """Highlight the currently active unit."""
        if self.active_unit:
            for entity in self.unit_entities:
                if entity.unit == self.active_unit:
                    entity.highlight_selected()
                    break
    
    def highlight_movement_range(self):
        """Highlight all tiles the selected unit can move to."""
        if not self.active_unit:
            return
        
        # Clear existing highlight entities
        self.clear_highlights()
        
        highlight_count = 0
        # Create highlight entities for movement range
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                distance = abs(x - self.active_unit.x) + abs(y - self.active_unit.y)
                if distance <= self.active_unit.current_move_points and self.grid.is_valid(x, y):
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
        if not self.active_unit or not self.path_cursor:
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
            total_distance = abs(new_pos[0] - self.active_unit.x) + abs(new_pos[1] - self.active_unit.y)
            
            # Don't allow path to exceed movement points
            if total_distance > self.active_unit.current_move_points:
                return
            
            # Update path cursor
            self.path_cursor = new_pos
            
            # Calculate complete path from unit position to cursor using pathfinder (like mouse movement)
            if self.pathfinder:
                try:
                    start_pos = Vector2Int(self.active_unit.x, self.active_unit.y)
                    end_pos = Vector2Int(new_pos[0], new_pos[1])
                    
                    calculated_path = self.pathfinder.calculate_movement_path(
                        start_pos, 
                        end_pos, 
                        float(self.active_unit.current_move_points)
                    )
                    
                    if calculated_path and len(calculated_path) > 1:
                        # Convert Vector2Int path back to tuple format (excluding start position)
                        self.current_path = [(pos.x, pos.y) for pos in calculated_path[1:]]
                    else:
                        # Fallback: direct path if pathfinder fails
                        self.current_path = [new_pos]
                        
                except Exception as e:
                    print(f"⚠ Pathfinding failed for keyboard movement: {e}")
                    # Fallback: simple direct path
                    self.current_path = [new_pos]
            else:
                # Fallback: simple direct path if no pathfinder
                self.current_path = [new_pos]
            
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
        if not self.active_unit or self.current_mode != "move":
            return False
        
        if not self.pathfinder:
            print("⚠ Pathfinder not available - falling back to manual path building")
            return False
        
        # Convert coordinates to Vector2Int for pathfinder
        start_pos = Vector2Int(self.active_unit.x, self.active_unit.y)
        end_pos = Vector2Int(clicked_tile[0], clicked_tile[1])
        
        # Check if clicking on same tile as unit (no movement needed)
        if start_pos.x == end_pos.x and start_pos.y == end_pos.y:
            return True
        
        # Validate that clicked tile is within unit's movement range
        distance = abs(end_pos.x - start_pos.x) + abs(end_pos.y - start_pos.y)
        if distance > self.active_unit.current_move_points:
            print(f"Target tile ({end_pos.x}, {end_pos.y}) is too far. Distance: {distance}, Movement points: {self.active_unit.current_move_points}")
            return True  # Handle the click but don't move
        
        # Check if target tile is occupied (blocked by another unit)
        if self.tactical_grid:
            target_cell = self.tactical_grid.get_cell(end_pos)
            if target_cell and target_cell.occupied:
                print(f"Target tile ({end_pos.x}, {end_pos.y}) is occupied by another unit")
                return True  # Handle the click but don't move
        
        # Calculate path using pathfinder
        try:
            calculated_path = self.pathfinder.calculate_movement_path(
                start_pos, 
                end_pos, 
                float(self.active_unit.current_move_points)
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
                    float(self.active_unit.current_move_points)
                )
                
                if reachable_positions:
                    # Find closest reachable position to clicked tile
                    closest_pos = min(reachable_positions, 
                                    key=lambda pos: abs(pos.x - end_pos.x) + abs(pos.y - end_pos.y))
                    
                    # Calculate path to closest position
                    closest_path = self.pathfinder.calculate_movement_path(
                        start_pos,
                        closest_pos,
                        float(self.active_unit.current_move_points)
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
            # Show movement range highlights now that movement mode is active
            self.update_path_highlights()
            print("Movement mode activated. Use WASD to plan movement, Enter to confirm. Tactical")
        elif action_name == "Attack":
            # Enter attack mode
            self.current_mode = "attack"
            self.handle_attack(unit)
        elif action_name == "Spirit":
            print("Spirit action selected - functionality to be implemented")
            # TODO: Implement spirit abilities
        elif action_name == "Magic":
            # Enter magic mode
            self.current_mode = "magic"
            self.handle_magic(unit)
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
        self.highlight_active_unit()
        self.highlight_attack_range(unit)
        
        print("Click on a target within red highlighted tiles to attack.")
    
    def handle_attack_target_selection(self, x: int, y: int, from_double_click: bool = False):
        """Handle tile clicks when in attack mode."""
        if not self.active_unit:
            return
            
        # Check if this is a double-click on the same tile while attack modal is open
        if (from_double_click and self.attack_modal and self.attack_modal.enabled and 
            self.attack_target_tile == (x, y)):
            # Auto-confirm the attack on double-click
            print(f"🖱️  Double-click confirming attack on ({x}, {y})")
            self._confirm_current_attack()
            return
            
        # Check if clicked tile is within attack range
        distance = abs(x - self.active_unit.x) + abs(y - self.active_unit.y)
        if distance <= self.active_unit.attack_range and distance > 0:
            # Valid attack target tile
            self.attack_target_tile = (x, y)
            self.attack_modal_from_double_click = from_double_click
            
            # Clear highlights and show attack effect area
            self.clear_highlights()
            self.highlight_active_unit()
            self.highlight_attack_range(self.active_unit)
            self.highlight_attack_effect_area(x, y)
            
            # Show attack confirmation modal
            self.show_attack_confirmation(x, y)
        else:
            print(f"Target at ({x}, {y}) is out of attack range!")
    
    def highlight_attack_effect_area(self, target_x: int, target_y: int):
        """Highlight the attack effect area around the target tile."""
        if not self.active_unit:
            return
        
        effect_radius = self.active_unit.attack_effect_area
        
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
        if not self.active_unit or not self.attack_target_tile:
            return
            
        # Find units that would be affected by the attack
        affected_units = self.get_units_in_effect_area(target_x, target_y)
        unit_list = affected_units  # Move unit_list declaration here
        
        # Set the targeted units for UI display
        self.set_targeted_units(unit_list)
        
        # Create confirmation buttons
        confirm_btn = Button(text='Confirm Attack', color=color.red)
        cancel_btn = Button(text='Cancel', color=color.gray)
        
        # Store attack data for keyboard handling
        self._current_attack_data = {
            'target_x': target_x,
            'target_y': target_y,
            'affected_units': unit_list
        }
        
        # Set up button callbacks
        def confirm_attack():
            self._confirm_current_attack()
            
        def cancel_attack():
            self._cancel_current_attack()
        
        confirm_btn.on_click = confirm_attack
        cancel_btn.on_click = cancel_attack
        
        # Create modal content
        unit_names = ", ".join([unit.name for unit in unit_list]) if unit_list else "No units"
        
        # Create modal window
        self.attack_modal = WindowPanel(
            title='Confirm Attack',
            content=(
                Text(f'{self.active_unit.name} attacks tile ({target_x}, {target_y})'),
                Text(f'Attack damage: {self.active_unit.physical_attack}'),
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
        effect_radius = self.active_unit.attack_effect_area
        
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                # Calculate distance from target tile
                distance = abs(x - target_x) + abs(y - target_y)
                
                # Check if tile is within effect area and has a unit
                if distance <= effect_radius and (x, y) in self.grid.units:
                    unit = self.grid.units[(x, y)]
                    # Don't include the attacking unit itself
                    if unit != self.active_unit:
                        affected_units.append(unit)
        
        return affected_units
    
    # Magic System Methods (Copy of Attack System with modifications)
    
    def handle_magic(self, unit):
        """Handle magic action - highlight magic range."""
        if not unit:
            return
            
        print(f"{unit.name} entering magic mode. Magic range: {unit.magic_range}")
        
        # Clear existing highlights and show magic range
        self.clear_highlights()
        self.highlight_active_unit()
        self.highlight_magic_range(unit)
        
        print("Click on a target within blue highlighted tiles to cast magic.")
    
    def handle_magic_target_selection(self, x: int, y: int, from_double_click: bool = False):
        """Handle tile clicks when in magic mode."""
        if not self.active_unit:
            return
            
        # Check if this is a double-click on the same tile while magic modal is open
        if (from_double_click and self.magic_modal and self.magic_modal.enabled and 
            self.magic_target_tile == (x, y)):
            # Auto-confirm the magic on double-click
            print(f"🖱️  Double-click confirming magic on ({x}, {y})")
            self._confirm_current_magic()
            return
            
        # Check if clicked tile is within magic range
        distance = abs(x - self.active_unit.x) + abs(y - self.active_unit.y)
        if distance <= self.active_unit.magic_range and distance > 0:
            # Valid magic target tile
            self.magic_target_tile = (x, y)
            self.magic_modal_from_double_click = from_double_click
            
            # Clear highlights and show magic effect area
            self.clear_highlights()
            self.highlight_active_unit()
            self.highlight_magic_range(self.active_unit)
            self.highlight_magic_effect_area(x, y)
            
            # Show magic confirmation modal
            self.show_magic_confirmation(x, y)
        else:
            print(f"Target at ({x}, {y}) is out of magic range!")
    
    def highlight_magic_effect_area(self, target_x: int, target_y: int):
        """Highlight the magic effect area around the target tile."""
        if not self.active_unit:
            return
        
        effect_radius = self.active_unit.magic_effect_area
        
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                # Calculate Manhattan distance from target tile to this tile
                distance = abs(x - target_x) + abs(y - target_y)
                
                # Highlight tiles within effect area
                if distance <= effect_radius:
                    if (x, y) == (target_x, target_y):
                        # Target tile gets special color (bright blue for target)
                        highlight_color = color.blue
                    else:
                        # Effect area tiles (lighter blue for area)
                        highlight_color = color.Color(0.5, 0.7, 1.0, 1.0)  # Light blue RGB
                    
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
    
    def show_magic_confirmation(self, target_x: int, target_y: int):
        """Show modal to confirm magic on target tile."""
        if not self.active_unit or not self.magic_target_tile:
            return
            
        # Find units that would be affected by the magic
        affected_units = self.get_units_in_magic_effect_area(target_x, target_y)
        unit_list = affected_units
        
        # Set the targeted units for UI display
        self.set_targeted_units(unit_list)
        
        # Create confirmation buttons
        confirm_btn = Button(text='Confirm Magic', color=color.blue)
        cancel_btn = Button(text='Cancel', color=color.gray)
        
        # Store magic data for keyboard handling
        self._current_magic_data = {
            'target_x': target_x,
            'target_y': target_y,
            'affected_units': unit_list
        }
        
        # Set up button callbacks
        def confirm_magic():
            self._confirm_current_magic()
            
        def cancel_magic():
            self._cancel_current_magic()
        
        confirm_btn.on_click = confirm_magic
        cancel_btn.on_click = cancel_magic
        
        # Create modal content
        unit_names = ", ".join([unit.name for unit in unit_list]) if unit_list else "No units"
        magic_spell_name = self.active_unit.magic_spell_name if hasattr(self.active_unit, 'magic_spell_name') else "Magic Spell"
        
        # Create modal window
        self.magic_modal = WindowPanel(
            title='Confirm Magic',
            content=(
                Text(f'{self.active_unit.name} casts {magic_spell_name} on tile ({target_x}, {target_y})'),
                Text(f'Magic damage: {self.active_unit.magical_attack}'),
                Text(f'MP cost: {self.active_unit.magic_mp_cost}'),
                Text(f'Units in effect area: {unit_names}'),
                confirm_btn,
                cancel_btn
            ),
            popup=True
        )
        
        # Center the window panel
        self.magic_modal.y = self.magic_modal.panel.scale_y / 2 * self.magic_modal.scale_y
        self.magic_modal.layout()
    
    def get_units_in_magic_effect_area(self, target_x: int, target_y: int) -> List[Any]:
        """Get all units within the magic effect area."""
        affected_units = []
        effect_radius = self.active_unit.magic_effect_area
        
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                # Calculate distance from target tile
                distance = abs(x - target_x) + abs(y - target_y)
                
                # Check if tile is within effect area and has a unit
                if distance <= effect_radius and (x, y) in self.grid.units:
                    unit = self.grid.units[(x, y)]
                    # Don't include the casting unit itself
                    if unit != self.active_unit:
                        affected_units.append(unit)
        
        return affected_units
            
    def show_movement_confirmation(self):
        """Show modal to confirm unit movement."""
        if not self.path_cursor or not self.active_unit:
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
                Text(f'Move {self.active_unit.name} to position ({self.path_cursor[0]}, {self.path_cursor[1]})?'),
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
        if not self.path_cursor or not self.active_unit:
            return 0
        
        # For mouse-generated paths, calculate actual path cost
        if self.current_path and self.pathfinder:
            try:
                # Convert current path to Vector2Int format
                start_pos = Vector2Int(self.active_unit.x, self.active_unit.y)
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
        return abs(self.path_cursor[0] - self.active_unit.x) + abs(self.path_cursor[1] - self.active_unit.y)
    
    def execute_movement(self):
        """Execute the planned movement."""
        if not self.path_cursor or not self.active_unit:
            return
            
        # Store old position for TacticalGrid update
        old_pos = Vector2Int(self.active_unit.x, self.active_unit.y)
        new_pos = Vector2Int(self.path_cursor[0], self.path_cursor[1])
        
        # Move unit to cursor position
        if self.grid.move_unit(self.active_unit, self.path_cursor[0], self.path_cursor[1]):
            # Update TacticalGrid positions
            if self.tactical_grid:
                self.tactical_grid.free_cell(old_pos)
                # Use unit name and new position as unique identifier
                unit_id = f"{self.active_unit.name}_{new_pos.x}_{new_pos.y}"
                self.tactical_grid.occupy_cell(new_pos, unit_id)
            
            self.update_unit_positions()
            # Keep unit selected after movement but clear path and mode
            moved_unit = self.active_unit  # Store reference before clearing path
            self.current_path = []
            self.path_cursor = None
            self.current_mode = None  # Exit movement mode
            self.clear_highlights()
            
            # Keep the unit selected and update its highlights
            if moved_unit:
                self.highlight_active_unit()
                # Don't show movement range - user needs to click Move again for that
                
                # Update control panel with moved unit info (keep it selected)
                if self.control_panel_callback:
                    try:
                        control_panel = self.control_panel_callback()
                        if control_panel:
                            control_panel.update_unit_info(moved_unit)
                    except Exception as e:
                        print(f"⚠ Error updating control panel: {e}")
                        
            print(f"Unit moved successfully. Press END TURN when ready.")
    
    def is_valid_move_destination(self, x: int, y: int) -> bool:
        """Check if a position is within the unit's movement range."""
        if not self.active_unit:
            return False
            
        # Calculate total distance from unit's starting position
        total_distance = abs(x - self.active_unit.x) + abs(y - self.active_unit.y)
        
        # Check if within movement points and valid grid position
        if total_distance > self.active_unit.current_move_points:
            return False
        
        if not (0 <= x < self.grid.width and 0 <= y < self.grid.height):
            return False
        
        # Check if position is occupied using TacticalGrid if available
        if self.tactical_grid:
            cell = self.tactical_grid.get_cell(Vector2Int(x, y))
            if cell and cell.occupied:
                return False
        else:
            # Fallback to legacy BattleGrid
            if (x, y) in self.grid.units:
                return False
                
        return True
    
    def update_path_highlights(self):
        """Update tile highlights to show movement range and current path."""
        # Clear existing highlights
        self.clear_highlights()
        
        if not self.active_unit:
            return
            
        # Highlight selected unit
        self.highlight_active_unit()
        
        # Only highlight movement range when in movement mode
        if self.current_mode == "move":
            self.highlight_movement_range()
        
        # Highlight current path in blue (but not the last tile - that will be yellow)
        for pos in self.current_path:
            # Skip highlighting the last tile in path if it's the cursor (will be yellow)
            if self.path_cursor and pos == self.path_cursor:
                continue
                
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
        
        # Highlight cursor position in yellow (always last, overrides blue)
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
    
    def highlight_magic_range(self, unit):
        """Highlight all tiles within the unit's magic range in blue."""
        if not unit:
            return
        
        # Clear existing highlights first
        self.clear_highlights()
        
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                # Calculate Manhattan distance from unit to tile
                distance = abs(x - unit.x) + abs(y - unit.y)
                
                # Highlight tiles within magic range (excluding unit's own tile)
                if distance <= unit.magic_range and distance > 0:
                    # Check if tile is within grid bounds
                    if 0 <= x < self.grid.width and 0 <= y < self.grid.height:
                        # Create highlight overlay entity
                        highlight = Entity(
                            model='cube',
                            color=color.blue,
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
        # Handle modal keyboard shortcuts first (highest priority)
        if self.movement_modal and self.movement_modal.enabled:
            if key == 'enter':
                # Confirm movement
                self.execute_movement()
                if self.movement_modal:
                    self.movement_modal.enabled = False
                    destroy(self.movement_modal)
                    self.movement_modal = None
                return True
            elif key == 'escape':
                # Cancel movement
                if self.movement_modal:
                    self.movement_modal.enabled = False
                    destroy(self.movement_modal)
                    self.movement_modal = None
                return True
        
        if self.attack_modal and self.attack_modal.enabled:
            if key == 'enter':
                # Confirm attack - need to execute the attack
                self._confirm_current_attack()
                return True
            elif key == 'escape':
                # Cancel attack - need to return to attack mode
                self._cancel_current_attack()
                return True
        
        if self.magic_modal and self.magic_modal.enabled:
            if key == 'enter':
                # Confirm magic - need to execute the magic
                self._confirm_current_magic()
                return True
            elif key == 'escape':
                # Cancel magic - need to return to magic mode
                self._cancel_current_magic()
                return True
        
        # Handle Escape key for movement and attack modes (before modals)
        if key == 'escape':
            if self.current_mode == "move":
                # Cancel movement mode and return to normal
                self._cancel_movement_mode()
                return True
            elif self.current_mode == "attack":
                # Cancel attack mode and return to normal
                self._cancel_attack_mode()
                return True
            elif self.current_mode == "magic":
                # Cancel magic mode and return to normal
                self._cancel_magic_mode()
                return True
        
        # Handle 'r' key to toggle control panel visibility
        if key == 'r':
            if hasattr(self, 'control_panel') and self.control_panel:
                self.control_panel.toggle_visibility()
                return True
        
        # Handle hotkey number keys (1-8) to activate abilities
        if key in ['1', '2', '3', '4', '5', '6', '7', '8']:
            slot_index = int(key) - 1  # Convert to 0-based index
            self._handle_hotkey_activation(slot_index)
            return True
        
        # Handle camera controls if no other input was processed
        if hasattr(self, 'camera_controller') and self.camera_controller:
            self.camera_controller.handle_input(key)
        
        return False
    
    def _confirm_current_attack(self):
        """Execute the current attack and clean up modal."""
        if not hasattr(self, '_current_attack_data') or not self._current_attack_data:
            return
            
        attack_data = self._current_attack_data
        target_x = attack_data['target_x']
        target_y = attack_data['target_y'] 
        unit_list = attack_data['affected_units']
        
        print(f"{self.active_unit.name} attacks tile ({target_x}, {target_y})!")
        
        # Apply damage to each unit in unit_list
        attack_damage = self.active_unit.physical_attack
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
        
        # Clean up modal and reset state
        if self.attack_modal:
            self.attack_modal.enabled = False
            destroy(self.attack_modal)
            self.attack_modal = None
        
        # Clear targeted units
        self.clear_targeted_units()
        
        # Return to normal mode
        self.current_mode = None
        self.attack_target_tile = None
        self.attack_modal_from_double_click = False
        self._current_attack_data = None
        self.clear_highlights()
        self.highlight_active_unit()
    
    def _cancel_current_attack(self):
        """Cancel the current attack and return to attack mode."""
        # Return to attack mode without attacking
        self.clear_highlights()
        self.highlight_active_unit()
        self.highlight_attack_range(self.active_unit)
        
        # Clean up modal
        if self.attack_modal:
            self.attack_modal.enabled = False
            destroy(self.attack_modal)
            self.attack_modal = None
        
        # Clear targeted units
        self.clear_targeted_units()
        
        # Clear attack data
        self.attack_modal_from_double_click = False
        self._current_attack_data = None
    
    def _confirm_current_magic(self):
        """Execute the current magic and clean up modal."""
        if not hasattr(self, '_current_magic_data') or not self._current_magic_data:
            return
            
        magic_data = self._current_magic_data
        target_x = magic_data['target_x']
        target_y = magic_data['target_y'] 
        unit_list = magic_data['affected_units']
        
        # Check if unit has enough MP
        mp_cost = self.active_unit.magic_mp_cost if hasattr(self.active_unit, 'magic_mp_cost') else 10
        if self.active_unit.mp < mp_cost:
            print(f"{self.active_unit.name} doesn't have enough MP to cast magic! (Need {mp_cost}, have {self.active_unit.mp})")
            self._cancel_current_magic()
            return
        
        # Consume MP
        self.active_unit.mp -= mp_cost
        print(f"{self.active_unit.name} consumes {mp_cost} MP (remaining: {self.active_unit.mp})")
        
        # Get magic spell name
        magic_spell_name = self.active_unit.magic_spell_name if hasattr(self.active_unit, 'magic_spell_name') else "Magic Spell"
        print(f"{self.active_unit.name} casts {magic_spell_name} on tile ({target_x}, {target_y})!")
        
        # Apply magic damage to each unit in unit_list
        magic_damage = self.active_unit.magical_attack
        for target_unit in unit_list:
            print(f"  {target_unit.name} takes {magic_damage} magical damage!")
            target_unit.take_damage(magic_damage, AttackType.MAGICAL)
            
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
        
        # Clean up modal and reset state
        if self.magic_modal:
            self.magic_modal.enabled = False
            destroy(self.magic_modal)
            self.magic_modal = None
        
        # Clear targeted units
        self.clear_targeted_units()
        
        # Return to normal mode
        self.current_mode = None
        self.magic_target_tile = None
        self.magic_modal_from_double_click = False
        self._current_magic_data = None
        self.clear_highlights()
        self.highlight_active_unit()
    
    def _cancel_current_magic(self):
        """Cancel the current magic and return to magic mode."""
        # Return to magic mode without casting
        self.clear_highlights()
        self.highlight_active_unit()
        self.highlight_magic_range(self.active_unit)
        
        # Clean up modal
        if self.magic_modal:
            self.magic_modal.enabled = False
            destroy(self.magic_modal)
            self.magic_modal = None
        
        # Clear targeted units
        self.clear_targeted_units()
        
        # Clear magic data
        self.magic_modal_from_double_click = False
        self._current_magic_data = None
    
    def _cancel_movement_mode(self):
        """Cancel movement mode and return to normal unit selection."""
        
        # Clear movement state
        self.current_path = []
        self.path_cursor = None if not self.active_unit else (self.active_unit.x, self.active_unit.y)
        
        # Return to normal mode while keeping unit selected
        self.current_mode = None
        
        # Clear movement highlights and show only unit selection
        self.clear_highlights()
        if self.active_unit:
            self.highlight_active_unit()
    
    def _cancel_attack_mode(self):
        """Cancel attack mode and return to normal unit selection."""
        
        # Clear attack state
        self.attack_target_tile = None
        self.attack_modal_from_double_click = False
        if hasattr(self, '_current_attack_data'):
            self._current_attack_data = None
        
        # Clear targeted units
        self.clear_targeted_units()
        
        # Return to normal mode while keeping unit selected
        self.current_mode = None
        
        # Clear attack highlights and show only unit selection
        self.clear_highlights()
        if self.active_unit:
            self.highlight_active_unit()
    
    def _cancel_magic_mode(self):
        """Cancel magic mode and return to normal unit selection."""
        
        # Clear magic state
        self.magic_target_tile = None
        self.magic_modal_from_double_click = False
        if hasattr(self, '_current_magic_data'):
            self._current_magic_data = None
        
        # Clear targeted units
        self.clear_targeted_units()
        
        # Return to normal mode while keeping unit selected
        self.current_mode = None
        
        # Clear magic highlights and show only unit selection
        self.clear_highlights()
        if self.active_unit:
            self.highlight_active_unit()
    
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
                color=style_manager.get_health_bar_bg_color()  # Background color
            )
            
            # Set the foreground bar color after creation
            if hasattr(self.health_bar, 'bar'):
                self.health_bar.bar.color = style_manager.get_health_bar_color()
    
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
        if self.health_bar and self.active_unit:
            self.health_bar.value = self.active_unit.hp
    
    def on_unit_hp_changed(self, unit):
        """Called when a unit's HP changes to update health bar if it's the selected unit"""
        if self.active_unit and self.active_unit == unit:
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
                color=style_manager.get_resource_bar_bg_color()  # Background color
            )
            
            # Set the foreground bar color after creation
            if hasattr(self.resource_bar, 'bar'):
                self.resource_bar.bar.color = bar_color
    
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
        if self.resource_bar and self.active_unit:
            self.resource_bar.value = self.active_unit.get_primary_resource_value()
    
    def on_unit_resource_changed(self, unit):
        """Called when a unit's resource changes to update resource bar if it's the selected unit"""
        if self.active_unit and self.active_unit == unit:
            self.refresh_resource_bar()
    
    # Hotkey Ability Slot Management Methods
    
    def _load_hotkey_config(self):
        """Load hotkey configuration from config file."""
        try:
            config_manager = get_config_manager()
            # Access the hotkey system config directly
            self.hotkey_config = {
                'hotkey_system': config_manager.get_value('character_interface_config.hotkey_system', {})
            }
            if not self.hotkey_config['hotkey_system']:
                self.hotkey_config = self._get_default_hotkey_config()
        except Exception as e:
            print(f"Warning: Failed to load hotkey config: {e}")
            self.hotkey_config = self._get_default_hotkey_config()
    
    def _get_default_hotkey_config(self):
        """Get default hotkey configuration if config file is unavailable."""
        return {
            "hotkey_system": {
                "max_hotkey_abilities": 8,
                "max_interface_slots": 8,
                "slot_layout": {
                    "rows": 1,
                    "columns": 8,
                    "slot_size": 0.06,
                    "slot_spacing": 0.01,
                    "start_position": {
                        "x": -0.4,
                        "y": 0.35,
                        "z": 0
                    }
                },
                "visual_settings": {
                    "empty_slot_color": "#404040",
                    "ability_slot_color": "#ffffff",
                    "cooldown_overlay_color": "#800000",
                    "hotkey_text_color": "#ffff00",
                    "hotkey_text_scale": 0.3,
                    "tooltip_enabled": True
                },
                "interaction": {
                    "click_to_activate": True,
                    "keyboard_shortcuts": True,
                    "keyboard_keys": ["1", "2", "3", "4", "5", "6", "7", "8"]
                },
                "display_options": {
                    "show_ability_icons": True,
                    "show_cooldown_timer": True,
                    "show_hotkey_numbers": True,
                    "show_ability_names": False,
                    "icon_fallback": "white_cube"
                }
            }
        }
    
    def _create_hotkey_slots(self):
        """Create hotkey ability slots positioned below the resource bar."""
        if not URSINA_AVAILABLE or not self.hotkey_config:
            return
        
        hotkey_settings = self.hotkey_config.get('hotkey_system', {})
        slot_layout = hotkey_settings.get('slot_layout', {})
        visual_settings = hotkey_settings.get('visual_settings', {})
        
        # Get configuration values
        max_slots = hotkey_settings.get('max_interface_slots', 8)
        slot_size = slot_layout.get('slot_size', 0.06)
        slot_spacing = slot_layout.get('slot_spacing', 0.01)
        start_pos = slot_layout.get('start_position', {'x': -0.4, 'y': 0.35, 'z': 0})
        
        # Colors
        empty_color = self._hex_to_color(visual_settings.get('empty_slot_color', '#404040'))
        
        # Clear existing slots
        self._clear_hotkey_slots()
        
        # Create slots
        for i in range(max_slots):
            x_offset = i * (slot_size + slot_spacing)
            
            # Create slot button
            slot_button = Button(
                parent=camera.ui,
                model='cube',
                texture='white_cube',
                color=empty_color,
                scale=slot_size,
                position=(start_pos['x'] + x_offset, start_pos['y'], start_pos['z']),
                on_click=lambda slot_index=i: self._on_hotkey_slot_clicked(slot_index)
            )
            
            # Add hotkey number text
            if hotkey_settings.get('display_options', {}).get('show_hotkey_numbers', True):
                hotkey_text_color = self._hex_to_color(visual_settings.get('hotkey_text_color', '#ffff00'))
                hotkey_text_scale = visual_settings.get('hotkey_text_scale', 0.3)
                
                hotkey_text = Text(
                    text=str(i + 1),
                    parent=slot_button,
                    position=(0, 0, -0.01),
                    scale=hotkey_text_scale,
                    color=hotkey_text_color,
                    origin=(0, 0)
                )
                slot_button.hotkey_text = hotkey_text
            
            # Initialize slot data
            slot_button.ability_data = None
            slot_button.tooltip = None
            slot_button.slot_index = i
            slot_button.enabled = False  # Start hidden
            
            self.hotkey_slots.append(slot_button)
    
    def _clear_hotkey_slots(self):
        """Clear existing hotkey slots."""
        for slot in self.hotkey_slots:
            if hasattr(slot, 'hotkey_text'):
                destroy(slot.hotkey_text)
            if hasattr(slot, 'tooltip') and slot.tooltip:
                destroy(slot.tooltip)
            destroy(slot)
        self.hotkey_slots.clear()
    
    def _hex_to_color(self, hex_color: str):
        """Convert hex color string to Ursina color."""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')
            # Convert to RGB values (0-1 range)
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return color.rgb(r, g, b)
        except:
            return color.gray  # Fallback color
    
    def _on_hotkey_slot_clicked(self, slot_index: int):
        """Handle clicking on a hotkey slot."""
        self._handle_hotkey_activation(slot_index)
    
    def _handle_hotkey_activation(self, slot_index: int):
        """Handle hotkey activation from either mouse click or keyboard shortcut."""
        if slot_index >= len(self.hotkey_slots):
            print(f"❌ Invalid hotkey slot {slot_index + 1}")
            return
        
        slot = self.hotkey_slots[slot_index]
        ability_data = slot.ability_data
        
        if ability_data:
            # Get ability name for feedback (try talent resolution first)
            ability_name = "Unknown"
            talent_id = ability_data.get('talent_id')
            
            if talent_id:
                from src.core.assets.data_manager import get_data_manager
                data_manager = get_data_manager()
                talent_data = data_manager.get_talent(talent_id)
                if talent_data:
                    ability_name = talent_data.name
            else:
                ability_name = ability_data.get('name', 'Unknown')
            
            print(f"🎯 Hotkey {slot_index + 1}: Activating {ability_name}")
            self._activate_ability(ability_data)
        else:
            print(f"❌ Empty hotkey slot {slot_index + 1}")
    
    def _activate_ability(self, ability_data: Dict[str, Any]):
        """Activate the specified ability by invoking the corresponding Unit Action."""
        if not self.active_unit:
            print("❌ No active unit selected")
            return
        
        # Check if this is talent_id reference or old format ability data
        talent_id = ability_data.get('talent_id')
        
        if talent_id:
            # New format: resolve talent by ID
            from src.core.assets.data_manager import get_data_manager
            data_manager = get_data_manager()
            talent_data = data_manager.get_talent(talent_id)
            
            if not talent_data:
                print(f"❌ Talent '{talent_id}' not found")
                return
            
            ability_name = talent_data.name
            action_type = talent_data.action_type
            
            print(f"🔥 Activating talent: {ability_name} (Action: {action_type})")
        else:
            # Legacy format: use provided ability data
            ability_name = ability_data.get('name', 'Unknown Ability')
            action_type = ability_data.get('action_type', 'Attack')  # Default to Attack
            
            print(f"🔥 Activating legacy ability: {ability_name} (Action: {action_type})")
        
        # Map talent action type to Unit Action
        if action_type == "Attack":
            self.handle_action_selection("Attack", self.active_unit)
        elif action_type == "Magic":
            self.handle_action_selection("Magic", self.active_unit)
        elif action_type == "Spirit":
            self.handle_action_selection("Spirit", self.active_unit)
        elif action_type == "Move":
            self.handle_action_selection("Move", self.active_unit)
        elif action_type == "Inventory":
            self.handle_action_selection("Inventory", self.active_unit)
        else:
            print(f"❌ Unknown action type: {action_type}")
            return
        
        print(f"   ✅ Unit Action '{action_type}' triggered for {self.active_unit.name}")
    
    def update_hotkey_slots(self):
        """Update hotkey slots with current active character's abilities."""
        if not self.hotkey_slots:
            return
        
        # Get active character
        active_character = self.character_state_manager.get_active_character()
        
        if not active_character:
            # No active character, hide all slots
            for slot in self.hotkey_slots:
                slot.enabled = False
            return
        
        # Get character's hotkey abilities
        hotkey_abilities = active_character.hotkey_abilities
        hotkey_settings = self.hotkey_config.get('hotkey_system', {})
        visual_settings = hotkey_settings.get('visual_settings', {})
        
        # Get data manager for talent resolution
        from src.core.assets.data_manager import get_data_manager
        data_manager = get_data_manager()
        
        # Colors
        empty_color = self._hex_to_color(visual_settings.get('empty_slot_color', '#404040'))
        ability_color = self._hex_to_color(visual_settings.get('ability_slot_color', '#ffffff'))
        
        # Update each slot
        for i, slot in enumerate(self.hotkey_slots):
            slot.enabled = True  # Show slot
            
            # hotkey_abilities from character state manager is a list of abilities
            if isinstance(hotkey_abilities, list) and i < len(hotkey_abilities):
                # Get ability data from the list
                ability_data = hotkey_abilities[i]
                slot.ability_data = ability_data
                slot.color = ability_color
                
                # Create tooltip with ability data
                if hasattr(slot, 'tooltip') and slot.tooltip:
                    destroy(slot.tooltip)
                
                ability_name = ability_data.get('name', 'Unknown Ability')
                ability_description = ability_data.get('description', 'No description available')
                action_type = ability_data.get('action_type', 'Unknown')
                tooltip_text = f"{ability_name}\n{ability_description}\nAction: {action_type}\nHotkey: {i + 1}"
                
                slot.tooltip = Tooltip(tooltip_text)
                slot.tooltip.background.color = color.hsv(0, 0, 0, .8)
            else:
                # Empty slot
                slot.ability_data = None
                slot.color = empty_color
                
                # Remove tooltip if exists
                if hasattr(slot, 'tooltip') and slot.tooltip:
                    destroy(slot.tooltip)
                    slot.tooltip = None
    
    def hide_hotkey_slots(self):
        """Hide hotkey slots when no unit is selected."""
        for slot in self.hotkey_slots:
            slot.enabled = False
    
    def show_hotkey_slots(self):
        """Show hotkey slots for active character."""
        self.update_hotkey_slots()
    
    # Targeted Unit Management Methods
    
    def add_targeted_unit(self, unit):
        """Add a unit to the targeted units list"""
        if unit not in self.targeted_units:
            self.targeted_units.append(unit)
            self.update_targeted_unit_bars()
    
    def remove_targeted_unit(self, unit):
        """Remove a unit from the targeted units list"""
        if unit in self.targeted_units:
            self.targeted_units.remove(unit)
            self.update_targeted_unit_bars()
    
    def clear_targeted_units(self):
        """Clear all targeted units"""
        self.targeted_units.clear()
        self.update_targeted_unit_bars()
    
    def set_targeted_units(self, units):
        """Set the targeted units list (replaces existing)"""
        self.targeted_units = list(units)
        self.update_targeted_unit_bars()
    
    def update_targeted_unit_bars(self):
        """Update health and resource bars for all targeted units"""
        # Clear existing targeted unit bars
        self.hide_targeted_unit_bars()
        
        # Create bars for each targeted unit
        if self.targeted_units:
            style_manager = get_ui_style_manager()
            
            for i, unit in enumerate(self.targeted_units):
                # Calculate position for multiple units (stack vertically)
                base_x = 0.4  # Right side of screen
                base_y = 0.45 - (i * 0.15)  # Stack downward
                
                # Create health bar label
                health_label = Text(
                    text=f"{unit.name} HP:",
                    parent=camera.ui,
                    position=(base_x - 0.07, base_y),
                    scale=0.8,
                    color=style_manager.get_bar_label_color(),
                    origin=(-0.5, 0)
                )
                self.targeted_health_bar_labels.append(health_label)
                
                # Create health bar
                health_bar = HealthBar(
                    max_value=unit.max_hp,
                    value=unit.hp,
                    position=(base_x, base_y),
                    parent=camera.ui,
                    scale=(0.25, 0.025),
                    color=style_manager.get_health_bar_bg_color()
                )
                
                # Set health bar color
                if hasattr(health_bar, 'bar'):
                    health_bar.bar.color = style_manager.get_health_bar_color()
                
                self.targeted_health_bars.append(health_bar)
                
                # Create resource bar label
                resource_type = unit.primary_resource_type
                resource_value = unit.get_primary_resource_value()
                resource_max = unit.get_primary_resource_max()
                resource_label_text = style_manager.get_resource_bar_label(resource_type)
                
                resource_label = Text(
                    text=f"{unit.name} {resource_label_text}:",
                    parent=camera.ui,
                    position=(base_x - 0.07, base_y - 0.05),
                    scale=0.8,
                    color=style_manager.get_bar_label_color(),
                    origin=(-0.5, 0)
                )
                self.targeted_resource_bar_labels.append(resource_label)
                
                # Create resource bar
                resource_bar = HealthBar(
                    max_value=resource_max,
                    value=resource_value,
                    position=(base_x, base_y - 0.05),
                    parent=camera.ui,
                    scale=(0.25, 0.025),
                    color=style_manager.get_resource_bar_bg_color()
                )
                
                # Set resource bar color
                bar_color = style_manager.get_resource_bar_color(resource_type)
                if hasattr(resource_bar, 'bar'):
                    resource_bar.bar.color = bar_color
                
                self.targeted_resource_bars.append(resource_bar)
    
    def hide_targeted_unit_bars(self):
        """Hide all targeted unit health and resource bars"""
        # Hide and clear health bars
        for bar in self.targeted_health_bars:
            if bar:
                bar.enabled = False
        self.targeted_health_bars.clear()
        
        # Hide and clear health bar labels
        for label in self.targeted_health_bar_labels:
            if label:
                label.enabled = False
        self.targeted_health_bar_labels.clear()
        
        # Hide and clear resource bars
        for bar in self.targeted_resource_bars:
            if bar:
                bar.enabled = False
        self.targeted_resource_bars.clear()
        
        # Hide and clear resource bar labels
        for label in self.targeted_resource_bar_labels:
            if label:
                label.enabled = False
        self.targeted_resource_bar_labels.clear()
    
    def refresh_targeted_unit_bars(self):
        """Refresh all targeted unit bars to match current HP/resource values"""
        for i, unit in enumerate(self.targeted_units):
            if i < len(self.targeted_health_bars):
                health_bar = self.targeted_health_bars[i]
                if health_bar:
                    health_bar.value = unit.hp
            
            if i < len(self.targeted_resource_bars):
                resource_bar = self.targeted_resource_bars[i]
                if resource_bar:
                    resource_bar.value = unit.get_primary_resource_value()
