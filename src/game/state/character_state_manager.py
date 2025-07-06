"""
Character State Manager

Manages runtime character state and bridges asset data with game state.
Provides dynamic character instances created from static template data.
"""

import uuid
from typing import Dict, Any, Optional, List, Set, Tuple, Callable
from dataclasses import dataclass, field
from copy import deepcopy

from core.models.unit_types import UnitType
from core.assets.unit_data_manager import UnitDataManager


@dataclass
class CharacterInstance:
    """
    Runtime instance of a character with dynamic state.
    
    Combines template data with runtime modifications for gameplay.
    """
    # Identity
    instance_id: str
    unit_type: UnitType
    
    # Base character data (from template)
    template_data: Dict[str, Any]
    
    # Runtime state
    current_stats: Dict[str, int] = field(default_factory=dict)
    current_inventory: List[Dict[str, Any]] = field(default_factory=list)
    unlocked_talents: Set[str] = field(default_factory=set)
    equipped_items: Dict[str, Any] = field(default_factory=dict)
    status_effects: List[Dict[str, Any]] = field(default_factory=list)
    
    # Game progression
    experience: int = 0
    level: int = 1
    skill_points: int = 0
    
    # Battle state
    current_hp: int = 0
    current_mp: int = 0
    current_rage: int = 0
    current_kwan: int = 0
    current_ap: int = 0
    position: Optional[Tuple[int, int]] = None
    
    def __post_init__(self):
        """Initialize derived data after creation."""
        if not self.current_stats:
            self._initialize_stats()
        if not self.current_inventory:
            self._initialize_inventory()
        if not self.unlocked_talents:
            self._initialize_talents()
        if not self.current_hp:
            self._initialize_resources()
    
    def _initialize_stats(self):
        """Initialize current stats from template base stats."""
        base_stats = self.template_data.get('stats', {})
        self.current_stats = {
            'strength': 10,
            'fortitude': 10,
            'finesse': 10,
            'wisdom': 10,
            'wonder': 10,
            'worthy': 10,
            'faith': 10,
            'spirit': 10,
            'speed': 10,
            # Base combat stats
            'base_health': base_stats.get('base_health', 80),
            'base_mp': base_stats.get('base_mp', 5),
            'base_move_points': base_stats.get('base_move_points', 3),
            'base_attack_range': base_stats.get('base_attack_range', 1),
            'base_effect_area': base_stats.get('base_effect_area', 1),
        }
        
        # Apply attribute bonuses from template
        attribute_bonuses = base_stats.get('attribute_bonuses', [])
        for attr in attribute_bonuses:
            if attr in self.current_stats:
                self.current_stats[attr] += 5  # Bonus for specialized attributes
    
    def _initialize_inventory(self):
        """Initialize inventory from template starting items."""
        starting_items = self.template_data.get('inventory', {}).get('starting_items', [])
        self.current_inventory = deepcopy(starting_items)
        
        # Mark equipped items
        for item in self.current_inventory:
            if item.get('equipped', False):
                slot = item.get('slot', 'unknown')
                self.equipped_items[slot] = item
    
    def _initialize_talents(self):
        """Initialize unlocked talents from template."""
        talents = self.template_data.get('talents', {})
        for talent_id, talent_data in talents.items():
            if talent_data.get('unlocked', False):
                self.unlocked_talents.add(talent_id)
    
    def _initialize_resources(self):
        """Initialize current resources based on stats."""
        # Calculate HP (simplified formula)
        self.current_hp = self.current_stats['base_health']
        
        # Calculate MP
        self.current_mp = self.current_stats['base_mp']
        
        # Initialize other resources
        self.current_rage = 0
        self.current_kwan = 0
        self.current_ap = self.current_stats.get('speed', 10)
    
    def get_effective_stats(self) -> Dict[str, int]:
        """Calculate final stats including equipment and status effects."""
        effective_stats = self.current_stats.copy()
        
        # Apply equipment bonuses
        for slot, item in self.equipped_items.items():
            item_stats = item.get('stats', {})
            for stat, bonus in item_stats.items():
                if stat in effective_stats:
                    effective_stats[stat] += bonus
        
        # Apply status effect modifiers
        for effect in self.status_effects:
            modifiers = effect.get('stat_modifiers', {})
            for stat, modifier in modifiers.items():
                if stat in effective_stats:
                    effective_stats[stat] += modifier
        
        # Apply talent effects
        talents = self.template_data.get('talents', {})
        for talent_id in self.unlocked_talents:
            if talent_id in talents:
                talent_effects = talents[talent_id].get('effects', {})
                for stat, bonus in talent_effects.items():
                    if stat in effective_stats and stat.endswith('_bonus'):
                        base_stat = stat.replace('_bonus', '')
                        if base_stat in effective_stats:
                            effective_stats[base_stat] += bonus
        
        return effective_stats
    
    def get_inventory_items(self) -> List[Dict[str, Any]]:
        """Get current inventory with equipped status."""
        return self.current_inventory.copy()
    
    def get_available_abilities(self) -> List[Dict[str, Any]]:
        """Get currently available hotkey abilities."""
        hotkey_abilities = self.template_data.get('hotkey_abilities', {})
        available = []
        
        for key, ability in hotkey_abilities.items():
            ability_copy = ability.copy()
            ability_copy['hotkey'] = key
            # TODO: Add cooldown and resource availability checks
            ability_copy['available'] = True
            available.append(ability_copy)
        
        return available
    
    def unlock_talent(self, talent_id: str) -> bool:
        """Unlock a talent if requirements are met."""
        talents = self.template_data.get('talents', {})
        if talent_id not in talents:
            return False
        
        talent = talents[talent_id]
        requirements = talent.get('requirements', {})
        
        # Check level requirement
        if requirements.get('level', 0) > self.level:
            return False
        
        # Check other requirements (kills, damage, etc.)
        # TODO: Implement requirement checking
        
        self.unlocked_talents.add(talent_id)
        return True
    
    def equip_item(self, item_id: str, slot: str) -> bool:
        """Equip an item to a slot."""
        # Find item in inventory
        item_to_equip = None
        for item in self.current_inventory:
            if item.get('item_id') == item_id:
                item_to_equip = item
                break
        
        if not item_to_equip:
            return False
        
        # Unequip current item in slot
        if slot in self.equipped_items:
            old_item = self.equipped_items[slot]
            old_item['equipped'] = False
        
        # Equip new item
        item_to_equip['equipped'] = True
        item_to_equip['slot'] = slot
        self.equipped_items[slot] = item_to_equip
        
        return True
    
    def get_display_name(self) -> str:
        """Get character display name."""
        return self.template_data.get('display_name', self.unit_type.value.title())
    
    def get_character_class(self) -> str:
        """Get character class name."""
        return self.unit_type.value.title()
    
    @property
    def hotkey_abilities(self) -> List[Dict[str, Any]]:
        """Get hotkey abilities in slot order for the Character Interface."""
        hotkey_abilities_data = self.template_data.get('hotkey_abilities', {})
        
        # Convert to ordered list based on slot numbers (FIXED: sparse list with None for empty slots)
        abilities_list = []
        
        # Process slots 1-8 (or max configured slots) - maintain slot-to-index mapping
        for i in range(1, 9):  # Slots 1-8
            slot_key = str(i)
            if slot_key in hotkey_abilities_data:
                ability_data = hotkey_abilities_data[slot_key].copy()
                
                # Check if this is a talent_id reference that needs resolution
                if 'talent_id' in ability_data and 'name' not in ability_data:
                    talent_id = ability_data['talent_id']
                    
                    # Attempt to resolve talent_id to full ability data
                    try:
                        from src.core.assets.data_manager import get_data_manager
                        data_manager = get_data_manager()
                        talent_data = data_manager.get_talent(talent_id)
                        
                        if talent_data:
                            # Normalize cost format from talent data (TalentData object)
                            talent_cost = talent_data.cost
                            normalized_cost = {}
                            for key, value in talent_cost.items():
                                # Convert talent cost format to ability cost format
                                if key == 'mp_cost':
                                    normalized_cost['mp'] = value
                                elif key == 'rage_cost':
                                    normalized_cost['rage'] = value
                                elif key == 'kwan_cost':
                                    normalized_cost['kwan'] = value
                                elif key == 'action_points':
                                    normalized_cost['ap'] = value
                                else:
                                    # Keep other cost types as-is
                                    normalized_cost[key] = value
                            
                            # Use talent data to populate ability information
                            ability = {
                                'ability_id': talent_id,
                                'talent_id': talent_id,  # Keep reference
                                'name': talent_data.name,
                                'description': talent_data.description,
                                'cooldown': 0,  # Cooldown not in TalentData schema
                                'cost': normalized_cost,
                                'range': 1,  # Range not in TalentData schema
                                'area_of_effect': 1,  # AoE not in TalentData schema
                                'effects': talent_data.effects,
                                'action_type': talent_data.action_type
                            }
                        else:
                            # Fallback if talent not found
                            ability = {
                                'ability_id': talent_id,
                                'talent_id': talent_id,
                                'name': f'Unknown Talent: {talent_id}',
                                'description': f'Talent ID {talent_id} not found in talent trees',
                                'cooldown': 0,
                                'cost': {},
                                'range': 1,
                                'area_of_effect': 1,
                                'effects': {}
                            }
                    except Exception as e:
                        # Fallback if talent manager fails
                        ability = {
                            'ability_id': talent_id,
                            'talent_id': talent_id,
                            'name': f'Error: {talent_id}',
                            'description': f'Failed to resolve talent: {e}',
                            'cooldown': 0,
                            'cost': {},
                            'range': 1,
                            'area_of_effect': 1,
                            'effects': {}
                        }
                else:
                    # Use existing detailed format
                    ability = ability_data
                
                # Add common interface properties
                ability['slot_index'] = i - 1  # Convert to 0-based index
                ability['hotkey'] = slot_key
                # TODO: Add real availability checking
                ability['available'] = True
                ability['on_cooldown'] = False
                ability['cooldown_remaining'] = 0
                abilities_list.append(ability)
            else:
                # FIXED: Add None for empty slots to maintain index alignment
                abilities_list.append(None)
        
        return abilities_list
    
    def activate_hotkey_ability(self, slot_index: int) -> bool:
        """Activate a hotkey ability by slot index."""
        hotkey_abilities = self.hotkey_abilities
        
        if slot_index < 0 or slot_index >= len(hotkey_abilities):
            return False
        
        ability = hotkey_abilities[slot_index]
        
        # FIXED: Check if slot is empty (None value)
        if ability is None:
            return False
        
        # Check if ability is available
        if not ability.get('available', False) or ability.get('on_cooldown', False):
            return False
        
        # Check resource costs
        cost = ability.get('cost', {})
        if cost.get('ap', 0) > self.current_ap:
            return False
        if cost.get('mp', 0) > self.current_mp:
            return False
        if cost.get('rage', 0) > self.current_rage:
            return False
        if cost.get('kwan', 0) > self.current_kwan:
            return False
        
        # TODO: Implement actual ability execution
        # For now, just consume resources and start cooldown
        self.current_ap -= cost.get('ap', 0)
        self.current_mp -= cost.get('mp', 0)
        self.current_rage -= cost.get('rage', 0)
        self.current_kwan -= cost.get('kwan', 0)
        
        print(f"🔥 Activated ability: {ability.get('name', 'Unknown')}")
        return True


class CharacterStateManager:
    """
    Manages runtime character state and bridges asset data with game state.
    
    Responsibilities:
    - Create character instances from templates
    - Track character state changes during gameplay
    - Provide character data to UI panels
    - Manage inventory, talents, and ability state
    """
    
    def __init__(self, unit_data_manager: UnitDataManager):
        """
        Initialize character state manager.
        
        Args:
            unit_data_manager: Manager for character template data
        """
        self.unit_data_manager = unit_data_manager
        self.character_instances: Dict[str, CharacterInstance] = {}
        self.active_character_id: Optional[str] = None
        self.observers: List[Callable] = []
    
    def create_character_instance(self, unit_type: UnitType, instance_id: Optional[str] = None) -> CharacterInstance:
        """
        Create runtime character from template data.
        
        Args:
            unit_type: Type of character to create
            instance_id: Optional custom ID, generates UUID if not provided
            
        Returns:
            CharacterInstance: New character instance
        """
        if instance_id is None:
            instance_id = f"{unit_type.value}_{uuid.uuid4().hex[:8]}"
        
        # Get template data from asset manager
        if self.unit_data_manager.is_character_type(unit_type):
            # Use enhanced character data
            template_data = self.unit_data_manager._get_unit_data(unit_type)
        else:
            # Fall back to basic unit data
            template_data = {
                'id': unit_type.value.lower(),
                'display_name': unit_type.value.title(),
                'stats': self.unit_data_manager.get_unit_base_stats(unit_type),
                'combat': self.unit_data_manager.get_unit_combat_data(unit_type),
                'ai': self.unit_data_manager.get_unit_ai_data(unit_type),
                'visual': self.unit_data_manager.get_unit_visual_properties(unit_type),
                'inventory': {'starting_items': [], 'max_inventory_size': 20, 'gold': 0},
                'talents': {},
                'hotkey_abilities': {},
                'game_state_effects': {}
            }
        
        # Create character instance
        character = CharacterInstance(
            instance_id=instance_id,
            unit_type=unit_type,
            template_data=template_data
        )
        
        # Store instance
        self.character_instances[instance_id] = character
        
        # Notify observers
        self._notify_observers('character_created', instance_id, character)
        
        return character
    
    def get_character_instance(self, instance_id: str) -> Optional[CharacterInstance]:
        """Get character instance by ID."""
        return self.character_instances.get(instance_id)
    
    def get_active_character(self) -> Optional[CharacterInstance]:
        """Get currently active character for UI display."""
        if self.active_character_id:
            return self.character_instances.get(self.active_character_id)
        return None
    
    def set_active_character(self, instance_id: Optional[str]):
        """
        Set active character and notify UI panels.
        
        Args:
            instance_id: ID of character to make active, None to clear
        """
        old_active = self.active_character_id
        self.active_character_id = instance_id
        
        if old_active != instance_id:
            self._notify_observers('active_character_changed', instance_id, 
                                 self.get_active_character())
    
    def update_character_state(self, instance_id: str, updates: Dict[str, Any]):
        """
        Update character state and notify observers.
        
        Args:
            instance_id: ID of character to update
            updates: Dictionary of state updates to apply
        """
        if instance_id not in self.character_instances:
            return
        
        character = self.character_instances[instance_id]
        
        # Apply updates
        for key, value in updates.items():
            if key == 'inventory':
                character.current_inventory = value
            elif key == 'stats':
                character.current_stats.update(value)
            elif key == 'unlocked_talents':
                if isinstance(value, (list, set)):
                    character.unlocked_talents.update(value)
                else:
                    character.unlocked_talents.add(value)
            elif key == 'equipped_items':
                character.equipped_items.update(value)
            elif key == 'status_effects':
                character.status_effects = value
            elif key == 'experience':
                character.experience = value
            elif key == 'level':
                character.level = value
            elif key == 'skill_points':
                character.skill_points = value
            elif key == 'position':
                character.position = value
            elif key in ['current_hp', 'current_mp', 'current_rage', 'current_kwan', 'current_ap']:
                setattr(character, key, value)
        
        # Notify observers
        self._notify_observers('character_updated', instance_id, updates)
    
    def add_observer(self, callback: Callable):
        """
        Add observer for character state changes.
        
        Args:
            callback: Function to call on state changes (event_type, character_id, data)
        """
        if callback not in self.observers:
            self.observers.append(callback)
    
    def remove_observer(self, callback: Callable):
        """Remove observer from notification list."""
        if callback in self.observers:
            self.observers.remove(callback)
    
    def _notify_observers(self, event_type: str, character_id: Optional[str], data: Any):
        """Notify all observers of character state changes."""
        for observer in self.observers:
            try:
                observer(event_type, character_id, data)
            except Exception as e:
                print(f"Warning: Observer notification failed: {e}")
    
    def get_all_character_instances(self) -> Dict[str, CharacterInstance]:
        """Get all character instances."""
        return self.character_instances.copy()
    
    def remove_character_instance(self, instance_id: str):
        """Remove character instance and clean up references."""
        if instance_id in self.character_instances:
            # Clear active character if removing active
            if self.active_character_id == instance_id:
                self.set_active_character(None)
            
            # Remove instance
            del self.character_instances[instance_id]
            
            # Notify observers
            self._notify_observers('character_removed', instance_id, None)
    
    def save_character_states(self) -> Dict[str, Any]:
        """Serialize character states for save system."""
        return {
            'characters': {
                instance_id: {
                    'instance_id': char.instance_id,
                    'unit_type': char.unit_type.value,
                    'current_stats': char.current_stats,
                    'current_inventory': char.current_inventory,
                    'unlocked_talents': list(char.unlocked_talents),
                    'equipped_items': char.equipped_items,
                    'status_effects': char.status_effects,
                    'experience': char.experience,
                    'level': char.level,
                    'skill_points': char.skill_points,
                    'current_hp': char.current_hp,
                    'current_mp': char.current_mp,
                    'current_rage': char.current_rage,
                    'current_kwan': char.current_kwan,
                    'current_ap': char.current_ap,
                    'position': char.position,
                }
                for instance_id, char in self.character_instances.items()
            },
            'active_character_id': self.active_character_id
        }
    
    def load_character_states(self, data: Dict[str, Any]):
        """Restore character states from save data."""
        # Clear existing instances
        self.character_instances.clear()
        
        # Restore character instances
        for instance_id, char_data in data.get('characters', {}).items():
            try:
                unit_type = UnitType(char_data['unit_type'].upper())
                
                # Get template data
                if self.unit_data_manager.is_character_type(unit_type):
                    template_data = self.unit_data_manager._get_unit_data(unit_type)
                else:
                    template_data = {}
                
                # Create character instance
                character = CharacterInstance(
                    instance_id=instance_id,
                    unit_type=unit_type,
                    template_data=template_data,
                    current_stats=char_data.get('current_stats', {}),
                    current_inventory=char_data.get('current_inventory', []),
                    unlocked_talents=set(char_data.get('unlocked_talents', [])),
                    equipped_items=char_data.get('equipped_items', {}),
                    status_effects=char_data.get('status_effects', []),
                    experience=char_data.get('experience', 0),
                    level=char_data.get('level', 1),
                    skill_points=char_data.get('skill_points', 0),
                    current_hp=char_data.get('current_hp', 0),
                    current_mp=char_data.get('current_mp', 0),
                    current_rage=char_data.get('current_rage', 0),
                    current_kwan=char_data.get('current_kwan', 0),
                    current_ap=char_data.get('current_ap', 0),
                    position=char_data.get('position'),
                )
                
                self.character_instances[instance_id] = character
                
            except Exception as e:
                print(f"Warning: Failed to restore character {instance_id}: {e}")
        
        # Restore active character
        self.active_character_id = data.get('active_character_id')
        
        # Notify observers of full reload
        self._notify_observers('characters_loaded', None, self.character_instances)


# Global instance for easy access
_character_state_manager = None

def get_character_state_manager(unit_data_manager: Optional[UnitDataManager] = None) -> CharacterStateManager:
    """
    Get the global character state manager instance.
    
    Args:
        unit_data_manager: Required for first call to initialize manager
        
    Returns:
        CharacterStateManager instance
    """
    global _character_state_manager
    if _character_state_manager is None:
        if unit_data_manager is None:
            from core.assets.unit_data_manager import get_unit_data_manager
            unit_data_manager = get_unit_data_manager()
        _character_state_manager = CharacterStateManager(unit_data_manager)
    return _character_state_manager