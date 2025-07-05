"""
Setters

"""

from core.game.turn_manager import TurnManager
from core.math.vector import Vector2Int, Vector3
from core.models.unit import Unit
from core.models.unit_types import UnitType
from typing import Dict, Any, List, Optional, Tuple
from ui.battlefield.grid_tile import GridTile
from ui.visual.unit_renderer import UnitEntity
from ursina import Entity, color, destroy, Button, Text, WindowPanel, camera, Tooltip

def setters_setup_battle(self):
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
        
    # Create units from configuration
    player_units = []
    enemy_units = []
        
    # Load player units from config
    for unit_config in self.battlefield_config.get('units', {}).get('player_units', []):
        unit_type = getattr(UnitType, unit_config.get('type', 'HEROMANCER'))
        player_units.append(Unit(
            unit_config.get('name', 'Player'),
            unit_type,
            unit_config.get('start_x', 1),
            unit_config.get('start_y', 1)
        ))
        
    # Load enemy units from config  
    for unit_config in self.battlefield_config.get('units', {}).get('enemy_units', []):
        unit_type = getattr(UnitType, unit_config.get('type', 'UBERMENSCH'))
        enemy_units.append(Unit(
            unit_config.get('name', 'Enemy'),
            unit_type,
            unit_config.get('start_x', 6),
            unit_config.get('start_y', 6)
        ))
        
    # Fallback to hard-coded units if config is empty
    if not player_units:
        player_units = [
            Unit("Hero", UnitType.HEROMANCER, 1, 1),
            Unit("Sage", UnitType.MAGI, 2, 1)
        ]
    if not enemy_units:
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
    
def setters_set_active_unit(self, unit: Optional[Unit], update_highlights: bool = True, update_ui: bool = True):
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
    
def setters_clear_active_unit(self):
    """
    Clear the active unit selection.
    Convenience method that calls set_active_unit(None).
    """
    self.set_active_unit(None)
    
def setters_equip_demo_weapons(self):
    """Equip demonstration weapons to show range/area effects"""
    demo_weapons_config = self.battlefield_config.get('demo_weapons', {})
        
    # Load weapon data from data manager
    from core.assets.data_manager import get_data_manager
    data_manager = get_data_manager()
        
    # Equip weapons based on configuration
    for unit in self.units:
        weapon_id = demo_weapons_config.get(unit.name)
        if weapon_id:
            weapon_data = data_manager.get_item(weapon_id)
            if weapon_data:
                unit.equip_weapon(weapon_data)
                print(f"🔥 {unit.name} equipped {weapon_data.name} - Range: {unit.attack_range}, Area: {unit.attack_effect_area}")
            else:
                print(f"⚠️ Weapon '{weapon_id}' not found for {unit.name}")
            
    print("\n📋 Test Instructions:")
    print("1. Click on Hero - notice spear gives Range 2, Area 2")
    print("2. Click Attack - see red tiles show 2-tile attack range")
    print("3. Click target - see yellow area effect covering 2-tile radius")
    print("4. Try same with Sage - bow has Range 3, Area 1")
    print("5. Compare the different weapon effects!")
    print("✅ Demo weapons equipped for testing")

