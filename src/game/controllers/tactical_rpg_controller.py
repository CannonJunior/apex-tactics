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
from core.assets.talent_type_config import get_talent_type_config

# UI system imports
from ui.camera.camera_controller import CameraController
from ui.visual.grid_visualizer import GridVisualizer
from ui.visual.tile_highlighter import TileHighlighter
from ui.visual.unit_renderer import UnitEntity
from ui.battlefield.grid_tile import GridTile
from ui.interaction.interaction_manager import InteractionManager
from ui.panels.control_panel import CharacterAttackInterface
from ui.panels.talent_panel import TalentPanel
from ui.core.ui_style_manager import get_ui_style_manager

# Utility imports
from game.utils.effects.apply_targeted_effects import apply_targeted_effects
from game.utils.effects.talents import execute_specific_talent, execute_talent_effects, talent_requires_targeting, build_spell_params_from_effects, apply_immediate_effects, setup_talent_magic_mode, restore_original_magic_properties, handle_talent, highlight_talent_range
from game.utils.ui_bars import util_update_health_bar, util_hide_health_bar, util_refresh_health_bar, util_on_unit_hp_changed, util_update_resource_bar, util_hide_resource_bar, util_refresh_resource_bar, util_on_unit_resource_changed, util_update_action_points_bar, util_hide_action_points_bar, util_refresh_action_points_bar, util_on_unit_action_points_changed
from game.utils.targets import target_update_targeted_unit_bars, target_hide_targeted_unit_bars, target_refresh_targeted_unit_bars, target_highlight_magic_range_no_clear, target_highlight_talent_range_no_clear
from game.utils.setters import setters_setup_battle, setters_set_active_unit, setters_clear_active_unit, setters_equip_demo_weapons
from game.utils.movement import movement_handle_path_movement, movement_handle_mouse_movement
from game.utils.ui.hotkeys import hotkey_update_hotkey_slot_ability_data, hotkey_get_hotkey_slot_ability_data, create_hotkey_slots, hotkey_update_hotkey_slots, get_talent_action_color, handle_hotkey_activation, activate_ability

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
        
        # Initialize MCP integration (Phase 2 - MCP Integration)
        self.mcp_integration_manager = None
        try:
            from ..config.feature_flags import FeatureFlags
            if FeatureFlags.USE_MCP_TOOLS:
                from ..managers.mcp_integration_manager import MCPIntegrationManager
                self.mcp_integration_manager = MCPIntegrationManager(self)
                self.mcp_integration_manager.initialize()
                print("✅ MCP integration enabled")
        except ImportError as e:
            print(f"ℹ️ MCP integration not available: {e}")
        
        # Load battlefield configuration
        config_manager = get_config_manager()
        self.battlefield_config = config_manager.get_value('battlefield_config', {
            'grid': {'width': 8, 'height': 8},
            'units': {'player_units': [], 'enemy_units': []},
            'demo_weapons': {}
        })
        
        # Load highlighting configuration
        self.highlighting_config = config_manager.get_value('highlighting_config', {
            'highlight_styles': {},
            'unit_rendering': {}
        })
        
        # Legacy components for backwards compatibility  
        grid_config = self.battlefield_config.get('grid', {})
        self.grid = BattleGrid(
            width=grid_config.get('width', 8),
            height=grid_config.get('height', 8)
        )
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
        self.action_points_bar: Optional[HealthBar] = None  # Action points bar for active unit
        self.action_points_bar_label: Optional[Any] = None  # Action points bar label
        
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
        
        # Initialize talent panel
        try:
            self.talent_panel = TalentPanel(game_reference=self)
            print("✓ Talent panel initialized successfully")
        except Exception as e:
            print(f"⚠ Could not initialize talent panel: {e}")
            self.talent_panel = None
        
        # Setup initial battle
        self.setup_battle()
    
    def setup_battle(self):
        """Initialize the battle with units and systems."""
        setters_setup_battle(self)

    def set_active_unit(self, unit: Optional[Unit], update_highlights: bool = True, update_ui: bool = True):
        setters_set_active_unit(self, unit, update_highlights, update_ui)
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

    def clear_active_unit(self):
        """
        Clear the active unit selection.
        Convenience method that calls set_active_unit(None).
        """
        self.set_active_unit(None)
    
    def equip_demo_weapons(self):
        """Equip demonstration weapons to show range/area effects"""
        setters_equip_demo_weapons(self)

    def update_hotkey_slot_ability_data(self, slot_index: int, ability_data: Dict[str, Any]):
        hotkey_update_hotkey_slot_ability_data(self, slot_index, ability_data)
        """Update the ability_data for a specific hotkey slot."""

    def get_hotkey_slot_ability_data(self, slot_index: int) -> Optional[Dict[str, Any]]:
        hotkey_get_hotkey_slot_ability_data(self, slot_index)
        """Get the ability_data for a specific hotkey slot."""

    def clear_hotkey_slot(self, slot_index: int):
        """Clear the ability_data for a specific hotkey slot."""
        return self.update_hotkey_slot_ability_data(slot_index, None)
    
    def _get_highlight_style(self, style_name: str, fallback_color=None):
        """Get highlight style from configuration."""
        styles = self.highlighting_config.get('highlight_styles', {})
        style = styles.get(style_name, {})
        
        # Convert color array to ursina color if available
        color_data = style.get('color', fallback_color or [1, 1, 1])
        if isinstance(color_data, list) and len(color_data) >= 3:
            return color.rgb(color_data[0], color_data[1], color_data[2])
        
        # Fallback to provided color or white
        return fallback_color or color.white
    
    def _get_button_config(self, modal_type: str, button_type: str):
        """Get button configuration from UI layout config."""
        try:
            ui_config = get_config_manager().get_value('layout_config.ui_layout.modal_dialogs', {})
            modal_config = ui_config.get(modal_type, {})
            buttons = modal_config.get('buttons', {})
            return buttons.get(button_type, {})
        except:
            return {}
    
    def _get_button_color(self, modal_type: str, button_type: str, fallback_color):
        """Get button color from configuration."""
        button_config = self._get_button_config(modal_type, button_type)
        color_data = button_config.get('color', fallback_color)
        
        if isinstance(color_data, list) and len(color_data) >= 3:
            return color.rgb(color_data[0], color_data[1], color_data[2])
        
        return fallback_color
    
    def _create_highlight_entity(self, x: int, y: int, highlight_color, style_name: str = 'movement'):
        """Create a highlight entity with configurable style."""
        style_data = self.highlighting_config.get('highlight_styles', {}).get(style_name, {})
        scale = style_data.get('scale', [0.9, 0.2, 0.9])
        position_offset = style_data.get('position_offset', [0.5, 0, 0.5])
        alpha = style_data.get('alpha', 1.0)
        
        return Entity(
            model='cube',
            color=highlight_color,
            scale=tuple(scale),
            position=(x + position_offset[0], position_offset[1], y + position_offset[2]),
            alpha=alpha
        )
    
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
        """Highlight all tiles the selected unit can move to based on movement points and AP."""
        if not self.active_unit:
            return
        
        # Clear existing highlight entities
        self.clear_highlights()
        
        highlight_count = 0
        # Get AP-based movement limit
        from game.config.action_costs import ACTION_COSTS
        current_ap = getattr(self.active_unit, 'ap', 0)
        max_ap_distance = current_ap  # Since movement costs 1 AP per tile
        
        # Create highlight entities for movement range
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                distance = abs(x - self.active_unit.x) + abs(y - self.active_unit.y)
                
                # Check both movement points and AP limits
                within_move_points = distance <= self.active_unit.current_move_points
                within_ap_limit = distance <= max_ap_distance
                
                if within_move_points and within_ap_limit and self.grid.is_valid(x, y):
                    if distance == 0:
                        # Current position - different color
                        highlight_color = self._get_highlight_style('selection', color.white)
                    else:
                        # Valid movement range
                        highlight_color = self._get_highlight_style('movement', color.green)
                    
                    # Create highlight overlay entity
                    style_name = 'selection' if distance == 0 else 'movement'
                    highlight = self._create_highlight_entity(x, y, highlight_color, style_name)
                    # Store in a list for cleanup
                    if not hasattr(self, 'highlight_entities'):
                        self.highlight_entities = []
                    self.highlight_entities.append(highlight)
                    highlight_count += 1
    
    def handle_path_movement(self, direction: str):
        """Handle path movement and confirmation."""
        movement_handle_path_movement(self, direction)

    def handle_mouse_movement(self, clicked_tile: Tuple[int, int]) -> bool:
        """
        Handle mouse click for movement path creation.
        
        Args:
            clicked_tile: (x, y) coordinates of clicked tile
            
        Returns:
            True if click was handled, False otherwise
        """
        #movement_handle_mouse_movement(self, clicked_tile)

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
        
        # FIXED: Reset cancellation flag when new action is selected
        self.talent_cancelled = False
        
        # Check if unit has enough AP for the action
        from ..config.action_costs import ACTION_COSTS
        required_ap = ACTION_COSTS.get_action_cost(action_name.lower())
        
        if required_ap > 0 and hasattr(unit, 'ap'):
            if unit.ap < required_ap:
                print(f"❌ Not enough AP for {action_name}! Need {required_ap}, have {unit.ap}")
                return
        
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
            # FIXED: Check if talent was cancelled to prevent double-click confirmation
            if getattr(self, 'talent_cancelled', False):
                print(f"🚫 Double-click ignored - talent was cancelled")
                return
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
            
            # Save target unit if there's a unit on the targeted tile
            if (x, y) in self.grid.units:
                target_unit = self.grid.units[(x, y)]
                self.set_unit_target(self.active_unit, target_unit)
            else:
                # Clear target if attacking empty tile
                self.set_unit_target(self.active_unit, None)
            
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
        confirm_btn = Button(
            text=self._get_button_config('attack_confirmation', 'confirm').get('text', 'Confirm Attack'),
            color=self._get_button_color('attack_confirmation', 'confirm', color.red)
        )
        cancel_btn = Button(
            text=self._get_button_config('attack_confirmation', 'cancel').get('text', 'Cancel'),
            color=self._get_button_color('attack_confirmation', 'cancel', color.gray)
        )
        
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
            # FIXED: Check if talent was cancelled to prevent double-click confirmation
            if getattr(self, 'talent_cancelled', False):
                print(f"🚫 Double-click ignored - talent was cancelled")
                return
            # Auto-confirm the magic on double-click
            print(f"🖱️  Double-click confirming magic on ({x}, {y})")
            self._confirm_current_magic()
            return
            
        # Check if clicked tile is within magic range (use talent range if available)
        distance = abs(x - self.active_unit.x) + abs(y - self.active_unit.y)
        magic_range = getattr(self.active_unit, '_talent_magic_range', self.active_unit.magic_range)
        if distance <= magic_range and distance > 0:
            # Valid magic target tile
            self.magic_target_tile = (x, y)
            self.magic_modal_from_double_click = from_double_click
            
            # Save target unit if there's a unit on the targeted tile
            if (x, y) in self.grid.units:
                target_unit = self.grid.units[(x, y)]
                self.set_unit_target(self.active_unit, target_unit)
            else:
                # Clear target if casting magic on empty tile
                self.set_unit_target(self.active_unit, None)
            
            # Clear highlights and show magic effect area
            self.clear_highlights()
            self.highlight_active_unit()
            
            # Use talent-specific highlighting if in talent mode
            if hasattr(self.active_unit, '_talent_magic_range') and hasattr(self, 'current_talent_data'):
                talent_type = self.current_talent_data.action_type if self.current_talent_data else 'Magic'
                talent_config = get_talent_type_config()
                range_color = talent_config.get_range_color(talent_type)
                self._highlight_talent_range_no_clear(self.active_unit, talent_type, range_color)
            else:
                self.highlight_magic_range_no_clear(self.active_unit)
            
            # Use type-aware effect area highlighting if in talent mode
            if hasattr(self.active_unit, '_talent_magic_range') and hasattr(self, 'current_talent_data'):
                talent_type = self.current_talent_data.action_type if self.current_talent_data else 'Magic'
                self.highlight_talent_effect_area(x, y, talent_type)
            else:
                self.highlight_magic_effect_area(x, y)
            
            # Show magic confirmation modal
            self.show_magic_confirmation(x, y)
        else:
            print(f"Target at ({x}, {y}) is out of magic range!")
    
    def highlight_magic_effect_area(self, target_x: int, target_y: int):
        """Highlight the magic effect area around the target tile (legacy magic system)."""
        self.highlight_talent_effect_area(target_x, target_y, 'Magic')
    
    def highlight_talent_effect_area(self, target_x: int, target_y: int, talent_type: str):
        """Highlight the talent effect area around the target tile with type-specific colors."""
        if not self.active_unit:
            return
        
        # Get talent type configuration
        talent_config = get_talent_type_config()
        
        # Use talent-specific area if available, otherwise use unit's default or type default
        effect_radius = getattr(self.active_unit, '_talent_magic_effect_area', 
                               getattr(self.active_unit, 'magic_effect_area', 
                                       talent_config.get_default_area(talent_type)))
        
        # Get type-specific colors
        target_color = talent_config.get_target_color(talent_type)
        area_color = talent_config.get_area_color(talent_type)
        
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                # Calculate Manhattan distance from target tile to this tile
                distance = abs(x - target_x) + abs(y - target_y)
                
                # Highlight tiles within effect area
                if distance <= effect_radius:
                    if (x, y) == (target_x, target_y):
                        # Target tile gets special color (bright color for target)
                        highlight_color = target_color
                    else:
                        # Effect area tiles (lighter color for area)
                        highlight_color = area_color
                    
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
        confirm_btn = Button(
            text=self._get_button_config('magic_confirmation', 'confirm').get('text', 'Confirm Magic'),
            color=self._get_button_color('magic_confirmation', 'confirm', color.blue)
        )
        cancel_btn = Button(
            text=self._get_button_config('magic_confirmation', 'cancel').get('text', 'Cancel'),
            color=self._get_button_color('magic_confirmation', 'cancel', color.gray)
        )
        
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
        # Use talent-specific area if available, otherwise use unit's default
        effect_radius = getattr(self.active_unit, '_talent_magic_effect_area', self.active_unit.magic_effect_area)
        
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
        confirm_btn = Button(
            text=self._get_button_config('movement_confirmation', 'confirm').get('text', 'Confirm Move'),
            color=self._get_button_color('movement_confirmation', 'confirm', color.green)
        )
        cancel_btn = Button(
            text=self._get_button_config('movement_confirmation', 'cancel').get('text', 'Cancel'),
            color=self._get_button_color('movement_confirmation', 'cancel', color.red)
        )
        
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
        
        # Calculate movement distance and AP cost
        distance = abs(new_pos.x - old_pos.x) + abs(new_pos.y - old_pos.y)
        
        # Import action costs and calculate AP required
        from ..config.action_costs import ACTION_COSTS
        ap_cost = ACTION_COSTS.get_movement_cost(distance)
        
        # Check if unit has enough AP for movement
        if hasattr(self.active_unit, 'ap') and ap_cost > 0:
            if self.active_unit.ap < ap_cost:
                print(f"❌ Not enough AP for movement! Need {ap_cost}, have {self.active_unit.ap}")
                return
        
        # Consume AP before attempting movement
        if hasattr(self.active_unit, 'ap') and ap_cost > 0:
            old_ap = self.active_unit.ap
            self.active_unit.ap -= ap_cost
            print(f"🏃 Movement consumed {ap_cost} AP (was: {old_ap}, now: {self.active_unit.ap})")
            
            # Update AP bar immediately
            self.refresh_action_points_bar()
        
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
        
        # Handle 't' key to toggle talent panel visibility
        if key == 't':
            if hasattr(self, 'talent_panel') and self.talent_panel:
                self.talent_panel.toggle_visibility()
                return True
        
        # Handle hotkey number keys (1-8) to activate abilities
        if key in ['1', '2', '3', '4', '5', '6', '7', '8']:
            slot_index = int(key) - 1  # Convert to 0-based index
            
            # Check if unit has sufficient AP before processing hotkey
            if self.active_unit:
                current_ap = getattr(self.active_unit, 'ap', 0)
                if current_ap <= 0:
                    print(f"❌ Cannot use hotkey {key}: No AP remaining ({current_ap})")
                    return True
            
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
        
        # FIXED: Check if this is a talent-based attack and consume MP/AP
        talent_data = getattr(self, 'current_talent_data', None)
        
        # Handle talent-based attacks
        if talent_data and talent_data.cost:
            mp_cost = talent_data.cost.get('mp_cost', 0)
            ap_cost = talent_data.cost.get('ap_cost', 0)
            
            # Check MP availability
            if mp_cost > 0:
                if self.active_unit.mp >= mp_cost:
                    self.active_unit.mp -= mp_cost
                    print(f"   💙 Consumed {mp_cost} MP (remaining: {self.active_unit.mp})")
                    # FIXED: Update resource bar immediately after MP consumption
                    self.refresh_resource_bar()
                else:
                    print(f"❌ Not enough MP! Need {mp_cost}, have {self.active_unit.mp}")
                    return
            
            # Check AP availability and consume
            if ap_cost > 0:
                if hasattr(self.active_unit, 'ap') and self.active_unit.ap >= ap_cost:
                    self.active_unit.ap -= ap_cost
                    print(f"   🏃 Consumed {ap_cost} AP (remaining: {self.active_unit.ap})")
                    # Update action points bar immediately after AP consumption
                    self.refresh_action_points_bar()
                else:
                    ap_available = getattr(self.active_unit, 'ap', 0)
                    print(f"❌ Not enough AP! Need {ap_cost}, have {ap_available}")
                    return
        else:
            # Handle generic (non-talent) attacks - consume default AP cost
            from ..config.action_costs import ACTION_COSTS
            ap_cost = ACTION_COSTS.get_action_cost('attack')
            
            if ap_cost > 0:
                if hasattr(self.active_unit, 'ap') and self.active_unit.ap >= ap_cost:
                    self.active_unit.ap -= ap_cost
                    print(f"   🏃 Attack consumed {ap_cost} AP (remaining: {self.active_unit.ap})")
                    # Update action points bar immediately after AP consumption
                    self.refresh_action_points_bar()
                else:
                    ap_available = getattr(self.active_unit, 'ap', 0)
                    print(f"❌ Not enough AP for attack! Need {ap_cost}, have {ap_available}")
                    return
        
        print(f"{self.active_unit.name} attacks tile ({target_x}, {target_y})!")
        
        # Apply damage to each unit in unit_list
        # Use talent damage if available, otherwise use unit's physical attack
        if talent_data and talent_data.effects:
            effects = talent_data.effects
            attack_damage = (effects.get('base_damage', 0) or 
                           effects.get('physical_damage', 0) or 
                           self.active_unit.physical_attack)
        else:
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
        
        # FIXED: MCP notification for talent-based attacks on successful execution
        if talent_data:
            try:
                from ..config.feature_flags import FeatureFlags
                if (FeatureFlags.USE_MCP_TOOLS and 
                    hasattr(self, 'mcp_integration_manager') and 
                    self.mcp_integration_manager):
                    
                    talent_info = {
                        'id': talent_data.id,
                        'name': talent_data.name,
                        'action_type': talent_data.action_type,
                        'effects': talent_data.effects,
                        'cost': talent_data.cost
                    }
                    self.mcp_integration_manager.notify_talent_executed(talent_info)
                    print(f"📡 MCP notified: talent {talent_data.name} executed")
            except Exception as e:
                print(f"⚠️ MCP notification failed: {e}")
        
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
        # FIXED: Set cancellation flag to prevent double-click confirmation
        self.talent_cancelled = True
        
        # FIXED: Check for MP restoration on talent-based attacks
        talent_data = getattr(self, 'current_talent_data', None)
        if talent_data and talent_data.cost:
            mp_cost = talent_data.cost.get('mp_cost', 0)
            if mp_cost > 0:
                # Note: MP was not consumed yet, so no restoration needed
                # This message confirms proper cancellation behavior
                print(f"   💙 Attack cancelled - no MP consumed ({self.active_unit.mp} MP remaining)")
        
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
        
        # Check if this is talent-specific magic or generic magic
        is_talent_magic = hasattr(self, 'current_spell_params') and self.current_spell_params
        
        if is_talent_magic:
            # Execute talent-specific magic
            self._execute_talent_magic(target_x, target_y, unit_list)
        else:
            # Execute generic magic (fallback)
            self._execute_generic_magic(target_x, target_y, unit_list)
    
    def _execute_talent_magic(self, target_x: int, target_y: int, unit_list: List):
        """Execute talent-specific magic with multiple possible effects."""
        spell_params = self.current_spell_params
        talent_data = self.current_talent_data
        spell_name = spell_params.get('spell_name', 'Talent Spell')
        
        # FIXED: Consume MP/AP here during actual execution, not activation
        if talent_data and talent_data.cost:
            mp_cost = talent_data.cost.get('mp_cost', 0)
            ap_cost = talent_data.cost.get('ap_cost', 0)
            
            # Check MP availability and consume
            if mp_cost > 0:
                if self.active_unit.mp >= mp_cost:
                    self.active_unit.mp -= mp_cost
                    print(f"   💙 Consumed {mp_cost} MP (remaining: {self.active_unit.mp})")
                    # FIXED: Update resource bar immediately after MP consumption
                    self.refresh_resource_bar()
                else:
                    print(f"❌ Not enough MP! Need {mp_cost}, have {self.active_unit.mp}")
                    return
            
            # Check AP availability and consume
            if ap_cost > 0:
                if hasattr(self.active_unit, 'ap') and self.active_unit.ap >= ap_cost:
                    self.active_unit.ap -= ap_cost
                    print(f"   🏃 Consumed {ap_cost} AP (remaining: {self.active_unit.ap})")
                    # Update action points bar immediately after AP consumption
                    self.refresh_action_points_bar()
                else:
                    ap_available = getattr(self.active_unit, 'ap', 0)
                    print(f"❌ Not enough AP! Need {ap_cost}, have {ap_available}")
                    return
        
        print(f"{self.active_unit.name} casts {spell_name} on tile ({target_x}, {target_y})!")
        
        # Apply multiple effects from talent data
        effects = talent_data.effects if talent_data else {}
        self._apply_targeted_effects(effects, unit_list, spell_params)
        
        # FIXED: MCP notification here on successful execution
        if talent_data:
            try:
                from ..config.feature_flags import FeatureFlags
                if (FeatureFlags.USE_MCP_TOOLS and 
                    hasattr(self, 'mcp_integration_manager') and 
                    self.mcp_integration_manager):
                    
                    talent_info = {
                        'id': talent_data.id,
                        'name': talent_data.name,
                        'action_type': talent_data.action_type,
                        'effects': talent_data.effects,
                        'cost': talent_data.cost
                    }
                    self.mcp_integration_manager.notify_talent_executed(talent_info)
                    print(f"📡 MCP notified: talent {talent_data.name} executed")
            except Exception as e:
                print(f"⚠️ MCP notification failed: {e}")
        
        # Restore original magic properties after execution
        self._restore_original_magic_properties()
        
        # Complete the magic execution cleanup
        self._complete_magic_execution()
    
    def _apply_targeted_effects(self, effects, target_units: List, spell_params: dict):
        apply_targeted_effects(self, effects, target_units, spell_params)
    
    def _get_attack_type_from_damage_effect(self, damage_effect: str):
        """Convert damage effect name to AttackType enum."""
        if 'magical' in damage_effect:
            return AttackType.MAGICAL
        elif 'physical' in damage_effect:
            return AttackType.PHYSICAL
        elif 'spiritual' in damage_effect:
            return AttackType.SPIRITUAL
        else:
            return AttackType.MAGICAL  # Default to magical
    
    def _is_valid_damage_target(self, target_unit, effects) -> bool:
        """Check if unit is a valid target for damage effects."""
        target_type = effects.get('target_type', 'enemy')
        if target_type == 'ally':
            return False  # Don't damage allies
        elif target_type == 'self':
            return target_unit == self.active_unit
        else:  # 'enemy' or 'any'
            return True
    
    def _is_valid_healing_target(self, target_unit, effects) -> bool:
        """Check if unit is a valid target for healing effects."""
        target_type = effects.get('target_type', 'ally')
        if target_type == 'enemy':
            return False  # Don't heal enemies
        elif target_type == 'self':
            return target_unit == self.active_unit
        else:  # 'ally' or 'any'
            return True  # TODO: Implement proper ally detection
    
    def _is_valid_mp_target(self, target_unit, effects) -> bool:
        """Check if unit is a valid target for MP restoration."""
        return self._is_valid_healing_target(target_unit, effects)
    
    def _is_valid_buff_target(self, target_unit, effects) -> bool:
        """Check if unit is a valid target for buff effects."""
        return self._is_valid_healing_target(target_unit, effects)
    
    def _is_valid_debuff_target(self, target_unit, effects) -> bool:
        """Check if unit is a valid target for debuff effects."""
        return self._is_valid_damage_target(target_unit, effects)
    
    def _parse_area_of_effect(self, area_value):
        """Parse area of effect value from various formats."""
        if isinstance(area_value, int):
            return area_value
        elif isinstance(area_value, str):
            # Handle formats like "2x2", "3x3", "2"
            if 'x' in area_value.lower():
                # For "2x2" format, take the first number as radius
                try:
                    return int(area_value.split('x')[0])
                except (ValueError, IndexError):
                    return 1
            else:
                # Try to parse as simple integer string
                try:
                    return int(area_value)
                except ValueError:
                    return 1
        else:
            # Default fallback
            return 1
    
    def _execute_generic_magic(self, target_x: int, target_y: int, unit_list: List):
        """Execute generic magic (fallback for non-talent magic)."""
        # Check if unit has enough MP
        mp_cost = self.active_unit.magic_mp_cost if hasattr(self.active_unit, 'magic_mp_cost') else 10
        if self.active_unit.mp < mp_cost:
            print(f"{self.active_unit.name} doesn't have enough MP to cast magic! (Need {mp_cost}, have {self.active_unit.mp})")
            self._cancel_current_magic()
            return
        
        # Consume MP
        self.active_unit.mp -= mp_cost
        print(f"{self.active_unit.name} consumes {mp_cost} MP (remaining: {self.active_unit.mp})")
        # FIXED: Update resource bar immediately after MP consumption
        self.refresh_resource_bar()
        
        # Consume AP for generic magic
        from ..config.action_costs import ACTION_COSTS
        ap_cost = ACTION_COSTS.get_action_cost('magic')
        
        if ap_cost > 0:
            if hasattr(self.active_unit, 'ap') and self.active_unit.ap >= ap_cost:
                self.active_unit.ap -= ap_cost
                print(f"   🏃 Magic consumed {ap_cost} AP (remaining: {self.active_unit.ap})")
                # Update action points bar immediately after AP consumption
                self.refresh_action_points_bar()
            else:
                ap_available = getattr(self.active_unit, 'ap', 0)
                print(f"❌ Not enough AP for magic! Need {ap_cost}, have {ap_available}")
                return
        
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
                self._remove_defeated_unit(target_unit)
        
        # Complete the magic execution cleanup
        self._complete_magic_execution()
    
    def _remove_defeated_unit(self, target_unit):
        """Remove a defeated unit from the grid and scene."""
        # Remove dead unit from grid
        if (target_unit.x, target_unit.y) in self.grid.units:
            del self.grid.units[(target_unit.x, target_unit.y)]
        
        # Remove unit entity from scene
        for entity in self.unit_entities:
            if entity.unit == target_unit:
                destroy(entity)
                self.unit_entities.remove(entity)
                break
    
    def _complete_magic_execution(self):
        """Complete magic execution and clean up state."""
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
        # FIXED: Set cancellation flag to prevent double-click confirmation
        self.talent_cancelled = True
        
        # FIXED: Restore MP if talent was cancelled before execution
        # Since we no longer consume MP at activation, this ensures no MP loss on cancellation
        talent_data = getattr(self, 'current_talent_data', None)
        if talent_data and talent_data.cost:
            mp_cost = talent_data.cost.get('mp_cost', 0)
            if mp_cost > 0:
                # Note: MP was not consumed yet, so no restoration needed
                # This message confirms proper cancellation behavior
                print(f"   💙 Magic cancelled - no MP consumed ({self.active_unit.mp} MP remaining)")
        
        # If this was talent magic, restore original properties
        if hasattr(self, 'current_spell_params') and self.current_spell_params:
            self._restore_original_magic_properties()
        
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
        util_update_health_bar(self, unit)
    
    def hide_health_bar(self):
        """Hide the health bar when no unit is selected"""
        util_hide_health_bar(self)
    
    def refresh_health_bar(self):
        """Refresh health bar to match selected unit's current HP"""
        util_refresh_health_bar(self)
    
    def on_unit_hp_changed(self, unit):
        """Called when a unit's HP changes to update health bar if it's the selected unit"""
        util_on_unit_hp_changed(self, unit)
    
    def update_resource_bar(self, unit):
        """Create or update resource bar for the selected unit"""
        util_update_resource_bar(self, unit)
    
    def hide_resource_bar(self):
        """Hide the resource bar when no unit is selected"""
        util_hide_resource_bar(self)
    
    def refresh_resource_bar(self):
        """Refresh resource bar to match selected unit's current resource value"""
        util_refresh_resource_bar(self)
    
    def on_unit_resource_changed(self, unit):
        """Called when a unit's resource changes to update resource bar if it's the selected unit"""
        util_on_unit_resource_changed(self, unit)
    
    def update_action_points_bar(self, unit):
        """Create or update action points bar for the selected unit"""
        util_update_action_points_bar(self, unit)
    
    def hide_action_points_bar(self):
        """Hide the action points bar when no unit is selected"""
        util_hide_action_points_bar(self)
    
    def refresh_action_points_bar(self):
        """Refresh action points bar to match selected unit's current AP"""
        util_refresh_action_points_bar(self)
        # Update hotkey slots when AP changes
        self.update_hotkey_slots()
    
    def on_unit_action_points_changed(self, unit):
        """Called when a unit's action points change to update AP bar if it's the selected unit"""
        util_on_unit_action_points_changed(self, unit)
        # Update hotkey slots when any unit's AP changes
        if unit == self.active_unit:
            self.update_hotkey_slots()
    
    def can_unit_perform_action(self, unit, action_name: str) -> bool:
        """Check if a unit can perform a specific action based on AP requirements."""
        if not unit or not hasattr(unit, 'ap'):
            return True  # If no AP system, allow action
        
        from ..config.action_costs import ACTION_COSTS
        required_ap = ACTION_COSTS.get_action_cost(action_name.lower())
        
        return unit.ap >= required_ap
    
    def get_action_ap_info(self, unit, action_name: str) -> dict:
        """Get AP information for an action including current AP, required AP, and availability."""
        if not unit or not hasattr(unit, 'ap'):
            return {'available': True, 'current_ap': 100, 'required_ap': 0, 'reason': 'No AP system'}
        
        from ..config.action_costs import ACTION_COSTS
        required_ap = ACTION_COSTS.get_action_cost(action_name.lower())
        current_ap = unit.ap
        
        return {
            'available': current_ap >= required_ap,
            'current_ap': current_ap,
            'required_ap': required_ap,
            'reason': f"Need {required_ap} AP, have {current_ap}" if current_ap < required_ap else "Available"
        }
    
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
                    "icon_fallback": "brick"
                }
            }
        }
    
    def _create_hotkey_slots(self):
        create_hotkey_slots(self)
        """Create hotkey ability slots positioned below the resource bar."""

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
    
    def _get_talent_action_color(self, action_type: str):
        get_talent_action_color(self, action_type)
        """Get color for talent based on action type using unified configuration."""

    def _on_hotkey_slot_clicked(self, slot_index: int):
        """Handle clicking on a hotkey slot."""
        self._handle_hotkey_activation(slot_index)
    
    def _handle_hotkey_activation(self, slot_index: int):
        handle_hotkey_activation(self, slot_index)
        """Handle hotkey activation from either mouse click or keyboard shortcut."""

    def _activate_ability(self, ability_data: Dict[str, Any]):
        activate_ability(self, ability_data)
        """Activate the specified ability by executing the specific talent."""

    def _execute_specific_talent(self, talent_data):
        """Execute a specific talent with its unique effects."""
        execute_specific_talent(self, talent_data)
    
    def _execute_talent_effects(self, talent_data):
        """Execute talent using generalized effect system supporting multiple effects."""
        execute_talent_effects(self, talent_data)
    
    def _talent_requires_targeting(self, talent_data):
        """Determine if a talent requires target selection."""
        #talent_requires_targeting(self, talent_data)
        effects = talent_data.effects
        action_type = talent_data.action_type
        
        # Check for effects that require targeting
        targeting_effects = [
            'base_damage', 'magical_damage', 'physical_damage', 'spiritual_damage',
            'healing_amount', 'healing', 'area_of_effect', 'range'
        ]
        
        # Check if any targeting effects are present
        has_targeting_effects = any(effect in effects for effect in targeting_effects)
        
        # Check if range is specified (range > 0 means targeting needed)
        has_range = int(effects.get('range', 0)) > 0
        
        # Magic and Attack actions typically require targeting unless self-only
        requires_targeting_by_type = action_type in ['Magic', 'Attack'] and not effects.get('self_target_only', False)
        
        return has_targeting_effects or has_range or requires_targeting_by_type

    def _build_spell_params_from_effects(self, talent_data):
        """Build spell parameters from talent effects for targeting mode."""
        build_spell_params_from_effects(self, talent_data)
        effects = talent_data.effects
        talent_name = talent_data.name
        
        spell_params = {
            'spell_name': talent_name,
            'area_of_effect': self._parse_area_of_effect(effects.get('area_of_effect', 1)),
            'range': int(effects.get('range', 3)),
            'mp_cost': int(talent_data.cost.get('mp_cost', 0)),
        }
        
        # Add damage if present
        if 'base_damage' in effects:
            spell_params['damage'] = int(effects['base_damage'])
        elif 'magical_damage' in effects:
            spell_params['damage'] = int(effects['magical_damage'])
        elif 'physical_damage' in effects:
            spell_params['damage'] = int(effects['physical_damage'])
        elif 'spiritual_damage' in effects:
            spell_params['damage'] = int(effects['spiritual_damage'])
        
        # Add healing if present
        if 'healing_amount' in effects or 'healing' in effects:
            spell_params['healing'] = int(effects.get('healing_amount', effects.get('healing', 0)))
            spell_params['target_type'] = 'ally'
        
        # Add special properties
        if effects.get('guaranteed_hit', False):
            spell_params['guaranteed_hit'] = True
        
        return spell_params

    def _apply_immediate_effects(self, talent_data):
        """Apply effects that don't require targeting (self-buffs, instant effects)."""
        apply_immediate_effects(self, talent_data)
    
    def _setup_talent_magic_mode(self, talent_data, spell_params):
        """Set up magic mode with talent-specific parameters."""
        # FIXED: Reset cancellation flag when new talent is activated
        self.talent_cancelled = False
        setup_talent_magic_mode(self, talent_data, spell_params)
    
    def _restore_original_magic_properties(self):
        """Restore unit's original magic properties after talent casting."""
        restore_original_magic_properties(self)
    
    def _handle_talent(self, unit, talent_type: str):
        """Handle talent activation with type-specific highlighting and behavior."""
        handle_talent(self, unit, talent_type)
    
    def _highlight_talent_range(self, unit, talent_type: str, highlight_color):
        """Highlight the talent-specific range around the unit with type-specific color."""
        highlight_talent_range(self, unit, talent_type, highlight_color)
    
    def update_hotkey_slots(self):
        hotkey_update_hotkey_slots(self)
        """Update hotkey slots with current active character's abilities and AP availability."""

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
        target_update_targeted_unit_bars(self)

    def hide_targeted_unit_bars(self):
        """Hide all targeted unit health and resource bars"""
        target_hide_targeted_unit_bars(self)

    def refresh_targeted_unit_bars(self):
        """Refresh all targeted unit bars to match current HP/resource values"""
        target_refresh_targeted_unit_bars(self)

    def highlight_magic_range_no_clear(self, unit):
        """Highlight all tiles within the unit's magic range in blue (without clearing existing highlights)."""
        target_highlight_magic_range_no_clear(self, unit)

    def _highlight_talent_range_no_clear(self, unit, talent_type: str, highlight_color):
        """Highlight the talent-specific range around the unit (without clearing existing highlights)."""
        target_highlight_talent_range_no_clear(self, unit, talent_type, highlight_color)
    
    # Target Management Methods
    
    def _restore_unit_target(self, unit, target_unit):
        """Restore a unit's target selection when the unit is reactivated"""
        try:
            if target_unit and hasattr(target_unit, 'x') and hasattr(target_unit, 'y'):
                # Use target_set_targeted_units to properly set the target
                from game.utils.targets import target_set_targeted_units
                
                # Set the target unit as a targeted unit (creates health bars, etc.)
                target_set_targeted_units(self, [target_unit])
                
                # Also restore visual highlighting for the target
                if hasattr(self, 'clear_highlights'):
                    self.clear_highlights()
                
                # Highlight the unit itself
                if hasattr(self, 'highlight_active_unit'):
                    self.highlight_active_unit()
                
                # Highlight the target
                self._highlight_target_unit(target_unit)
                
                print(f"✅ Target restored with targeting system: {unit.name} → {target_unit.name}")
                
        except Exception as e:
            print(f"⚠️ Failed to restore target: {e}")
            # Clear invalid target
            unit.target_unit = None
    
    def _highlight_target_unit(self, target_unit):
        """Add special highlighting for a targeted unit"""
        try:
            if hasattr(self, 'highlight_entities'):
                # Create a target highlight overlay
                target_highlight = Entity(
                    model='cube',
                    color=color.orange,  # Orange color for targets
                    scale=(0.9, 0.2, 0.9),
                    position=(target_unit.x + 0.5, 0.1, target_unit.y + 0.5),  # Slightly above ground
                    alpha=0.8
                )
                
                # Store in highlight entities for cleanup
                if not hasattr(self, 'highlight_entities'):
                    self.highlight_entities = []
                self.highlight_entities.append(target_highlight)
                
                print(f"🎯 Highlighted target: {target_unit.name} at ({target_unit.x}, {target_unit.y})")
                
        except Exception as e:
            print(f"⚠️ Failed to highlight target: {e}")
    
    def set_unit_target(self, unit, target_unit):
        """Set a unit's target and store it for persistence"""
        try:
            if hasattr(unit, 'target_unit'):
                unit.target_unit = target_unit
                if target_unit:
                    print(f"🎯 {unit.name} now targets {target_unit.name}")
                    self._highlight_target_unit(target_unit)
                else:
                    print(f"🎯 {unit.name} target cleared")
            
        except Exception as e:
            print(f"⚠️ Failed to set unit target: {e}")
    
    def clear_unit_target(self, unit):
        """Clear a unit's target"""
        try:
            if hasattr(unit, 'target_unit'):
                if unit.target_unit:
                    print(f"🎯 Clearing target for {unit.name}")
                unit.target_unit = None
                
        except Exception as e:
            print(f"⚠️ Failed to clear unit target: {e}")
