# Equipment Components

## Overview

This directory contains components that implement the equipment system for Apex Tactics. The equipment system allows units to equip weapons, armor, and accessories that modify their stats and capabilities, providing a flexible progression and customization system.

## Architecture

### Equipment System Design
The equipment system uses a modular component approach where:
- **EquipmentComponent** - Manages individual equipment pieces and their effects
- **EquipmentManager** - Coordinates equipment across multiple units and manages equipment rules
- **Asset Integration** - Equipment data loaded from the asset system
- **Stat Integration** - Equipment modifies unit stats through the stat system

### Equipment Flow
```
Asset System (equipment data)
    ↓
EquipmentComponent (individual unit equipment)
    ↓
Stat System (stat calculations with equipment bonuses)
    ↓
Combat/Movement Systems (gameplay effects)
```

## Component Files

### `equipment.py` - Individual Equipment Management
Handles equipment for individual units and equipment pieces:

#### EquipmentComponent
```python
@dataclass
class EquipmentComponent(BaseComponent):
    def __init__(self):
        super().__init__()
        
        # Equipment slots
        self.weapon_slot = None
        self.armor_slot = None
        self.accessory_slot = None
        
        # Equipment history
        self.equipment_history = []
        
        # Durability tracking
        self.equipment_durability = {}
    
    def equip_weapon(self, weapon_data: Dict[str, Any]) -> bool:
        """Equip weapon and apply stat modifications"""
        
    def equip_armor(self, armor_data: Dict[str, Any]) -> bool:
        """Equip armor and apply defensive bonuses"""
        
    def equip_accessory(self, accessory_data: Dict[str, Any]) -> bool:
        """Equip accessory and apply special bonuses"""
        
    def unequip_item(self, slot_type: str) -> Optional[Dict[str, Any]]:
        """Remove item from slot and return item data"""
        
    def get_total_stat_bonuses(self) -> Dict[str, int]:
        """Calculate total stat bonuses from all equipment"""
```

#### Equipment Slot Management
```python
class EquipmentSlot:
    def __init__(self, slot_type: str, compatible_types: List[str]):
        self.slot_type = slot_type  # "weapon", "armor", "accessory"
        self.compatible_types = compatible_types  # Item types that fit
        self.equipped_item = None
        self.slot_restrictions = {}  # Level, attribute requirements
    
    def can_equip(self, item_data: Dict) -> Tuple[bool, str]:
        """Check if item can be equipped in this slot"""
        # Type compatibility
        if item_data.get('type') not in self.compatible_types:
            return False, f"Item type {item_data['type']} not compatible with {self.slot_type} slot"
        
        # Requirements check
        requirements = item_data.get('requirements', {})
        for req_type, req_value in requirements.items():
            if not self.meets_requirement(req_type, req_value):
                return False, f"Does not meet {req_type} requirement: {req_value}"
        
        return True, "Can equip"
    
    def equip_item(self, item_data: Dict) -> bool:
        """Equip item to this slot"""
        can_equip, reason = self.can_equip(item_data)
        if can_equip:
            self.equipped_item = item_data
            return True
        return False
```

#### Stat Bonus Calculation
```python
def calculate_equipment_bonuses(self) -> Dict[str, Any]:
    """Calculate all bonuses from equipped items"""
    bonuses = {
        # Combat stats
        'physical_attack': 0,
        'magical_attack': 0,
        'spiritual_attack': 0,
        'physical_defense': 0,
        'magical_defense': 0,
        'spiritual_defense': 0,
        
        # Special properties
        'attack_range': 0,
        'effect_area': 0,
        'movement_bonus': 0,
        
        # Attribute bonuses
        'strength': 0,
        'finesse': 0,
        'fortitude': 0,
        'wisdom': 0,
        'wonder': 0,
        'spirit': 0,
        'faith': 0,
        'worthy': 0,
        'speed': 0
    }
    
    for slot in [self.weapon_slot, self.armor_slot, self.accessory_slot]:
        if slot and slot.equipped_item:
            item_stats = slot.equipped_item.get('stats', {})
            
            # Add numeric bonuses
            for stat, value in item_stats.items():
                if stat in bonuses and isinstance(value, (int, float)):
                    bonuses[stat] += value
    
    return bonuses
```

### `equipment_manager.py` - Global Equipment Management
Manages equipment rules, restrictions, and cross-unit equipment coordination:

#### EquipmentManager
```python
class EquipmentManager:
    def __init__(self):
        self.equipment_rules = self._load_equipment_rules()
        self.unique_items = set()  # Track unique equipment
        self.equipment_registry = {}  # Global equipment tracking
        
    def validate_equipment_change(self, unit_entity: Entity, 
                                 item_data: Dict, slot_type: str) -> bool:
        """Validate equipment change across all game rules"""
        
    def handle_unique_item_equipping(self, unit_entity: Entity, 
                                   item_data: Dict) -> bool:
        """Handle unique items that can only be equipped by one unit"""
        
    def get_equipment_conflicts(self, unit_entity: Entity, 
                              item_data: Dict) -> List[str]:
        """Check for equipment conflicts and incompatibilities"""
        
    def calculate_set_bonuses(self, unit_entity: Entity) -> Dict[str, Any]:
        """Calculate bonuses for wearing complete equipment sets"""
```

#### Equipment Rules System
```python
class EquipmentRules:
    def __init__(self):
        self.slot_restrictions = self._define_slot_restrictions()
        self.item_restrictions = self._define_item_restrictions()
        self.set_bonuses = self._define_set_bonuses()
        
    def _define_slot_restrictions(self):
        """Define what can be equipped in each slot"""
        return {
            'weapon': {
                'compatible_types': ['Weapons'],
                'max_items': 1,
                'requirements': ['strength', 'finesse', 'level']
            },
            'armor': {
                'compatible_types': ['Armor'],
                'max_items': 1,
                'requirements': ['fortitude', 'level']
            },
            'accessory': {
                'compatible_types': ['Accessories'],
                'max_items': 1,
                'requirements': ['level']
            }
        }
    
    def _define_set_bonuses(self):
        """Define equipment set bonuses"""
        return {
            'iron_set': {
                'items': ['iron_sword', 'iron_armor', 'iron_shield'],
                'bonuses': {
                    2: {'physical_defense': 5},  # 2 pieces
                    3: {'physical_defense': 10, 'strength': 2}  # 3 pieces
                }
            },
            'mage_set': {
                'items': ['mage_robe', 'mage_staff', 'mage_amulet'],
                'bonuses': {
                    2: {'magical_attack': 8},
                    3: {'magical_attack': 15, 'wonder': 3}
                }
            }
        }
```

#### Durability and Maintenance
```python
class DurabilitySystem:
    def __init__(self):
        self.durability_rules = self._load_durability_rules()
        
    def apply_durability_damage(self, equipment_comp: EquipmentComponent, 
                               damage_amount: int, damage_type: str):
        """Apply durability damage to equipment"""
        for slot in equipment_comp.get_all_slots():
            if slot.equipped_item:
                item_id = slot.equipped_item['id']
                current_durability = equipment_comp.equipment_durability.get(item_id, 
                                   slot.equipped_item.get('stats', {}).get('durability', 100))
                
                # Calculate damage based on type and item
                actual_damage = self._calculate_durability_damage(
                    slot.equipped_item, damage_amount, damage_type
                )
                
                new_durability = max(0, current_durability - actual_damage)
                equipment_comp.equipment_durability[item_id] = new_durability
                
                # Check for equipment breaking
                if new_durability <= 0:
                    self._handle_equipment_break(equipment_comp, slot)
    
    def _handle_equipment_break(self, equipment_comp: EquipmentComponent, slot):
        """Handle equipment breaking due to durability loss"""
        broken_item = slot.equipped_item
        slot.equipped_item = None  # Remove broken equipment
        
        # Emit event for UI feedback
        self._emit_equipment_break_event(broken_item)
        
        # Apply stat penalties for broken equipment
        equipment_comp.recalculate_bonuses()
```

## Equipment Integration Patterns

### Asset System Integration
```python
def load_equipment_from_assets(self, item_id: str) -> Optional[Dict]:
    """Load equipment data from asset system"""
    try:
        data_manager = get_data_manager()
        item_data = data_manager.get_item(item_id)
        
        if item_data and item_data.type in ['Weapons', 'Armor', 'Accessories']:
            return item_data.to_inventory_format()
        else:
            return None
            
    except Exception as e:
        print(f"Failed to load equipment {item_id}: {e}")
        return None

def equip_item_from_inventory(self, unit_entity: Entity, item_id: str):
    """Equip item loaded from game assets"""
    item_data = self.load_equipment_from_assets(item_id)
    if not item_data:
        return False
    
    equipment_comp = unit_entity.get_component(EquipmentComponent)
    if not equipment_comp:
        return False
    
    # Determine slot type
    slot_type = self._determine_slot_type(item_data['type'])
    
    # Equip item
    return equipment_comp.equip_item(item_data, slot_type)
```

### Stat System Integration
```python
def apply_equipment_to_stats(self, unit_entity: Entity):
    """Apply equipment bonuses to unit stats"""
    equipment_comp = unit_entity.get_component(EquipmentComponent)
    stats_comp = unit_entity.get_component(UnitStatsComponent)
    
    if not equipment_comp or not stats_comp:
        return
    
    # Get all equipment bonuses
    equipment_bonuses = equipment_comp.calculate_equipment_bonuses()
    set_bonuses = self.equipment_manager.calculate_set_bonuses(unit_entity)
    
    # Combine bonuses
    total_bonuses = self._combine_bonuses(equipment_bonuses, set_bonuses)
    
    # Apply to stats component
    stats_comp.apply_equipment_bonuses(total_bonuses)

def _combine_bonuses(self, equipment_bonuses: Dict, set_bonuses: Dict) -> Dict:
    """Combine equipment and set bonuses"""
    combined = equipment_bonuses.copy()
    
    for stat, bonus in set_bonuses.items():
        combined[stat] = combined.get(stat, 0) + bonus
    
    return combined
```

### Combat System Integration
```python
def get_weapon_properties_for_combat(self, unit_entity: Entity) -> Dict:
    """Get weapon properties for combat calculations"""
    equipment_comp = unit_entity.get_component(EquipmentComponent)
    
    if not equipment_comp or not equipment_comp.weapon_slot.equipped_item:
        return {
            'attack_range': 1,
            'effect_area': 0,
            'damage_bonus': 0,
            'special_properties': []
        }
    
    weapon = equipment_comp.weapon_slot.equipped_item
    weapon_stats = weapon.get('stats', {})
    
    return {
        'attack_range': weapon_stats.get('attack_range', 1),
        'effect_area': weapon_stats.get('effect_area', 0),
        'damage_bonus': weapon_stats.get('physical_attack', 0),
        'special_properties': weapon.get('weapon_properties', {}),
        'enchantments': weapon.get('enchantments', [])
    }

def apply_weapon_effects_to_attack(self, attack_data: Dict, weapon_properties: Dict):
    """Apply weapon special effects to attack"""
    # Range modification
    attack_data['range'] = weapon_properties['attack_range']
    attack_data['area_effect'] = weapon_properties['effect_area']
    
    # Damage modification
    attack_data['base_damage'] += weapon_properties['damage_bonus']
    
    # Special properties
    if weapon_properties.get('special_properties', {}).get('never_miss'):
        attack_data['hit_chance'] = 1.0
    
    if weapon_properties.get('special_properties', {}).get('area_attack'):
        attack_data['hits_multiple_targets'] = True
```

## Equipment Progression System

### Equipment Tiers
```python
class EquipmentTier(Enum):
    BASE = "BASE"
    ENHANCED = "ENHANCED"
    ENCHANTED = "ENCHANTED"
    SUPERPOWERED = "SUPERPOWERED"
    METAPOWERED = "METAPOWERED"

def get_tier_multipliers(tier: EquipmentTier) -> Dict[str, float]:
    """Get stat multipliers for equipment tier"""
    tier_multipliers = {
        EquipmentTier.BASE: {'stats': 1.0, 'durability': 1.0},
        EquipmentTier.ENHANCED: {'stats': 1.5, 'durability': 1.2},
        EquipmentTier.ENCHANTED: {'stats': 2.0, 'durability': 1.5},
        EquipmentTier.SUPERPOWERED: {'stats': 3.0, 'durability': 2.0},
        EquipmentTier.METAPOWERED: {'stats': 4.0, 'durability': 3.0}
    }
    
    return tier_multipliers.get(tier, tier_multipliers[EquipmentTier.BASE])
```

### Equipment Upgrading
```python
def upgrade_equipment(self, equipment_comp: EquipmentComponent, 
                     slot_type: str, upgrade_materials: List[Dict]) -> bool:
    """Upgrade equipment using materials"""
    slot = getattr(equipment_comp, f"{slot_type}_slot")
    if not slot or not slot.equipped_item:
        return False
    
    current_item = slot.equipped_item
    current_tier = EquipmentTier(current_item['tier'])
    
    # Check if upgrade is possible
    next_tier = self._get_next_tier(current_tier)
    if not next_tier:
        return False  # Already max tier
    
    # Check materials
    required_materials = self._get_upgrade_requirements(current_item, next_tier)
    if not self._has_required_materials(upgrade_materials, required_materials):
        return False
    
    # Perform upgrade
    upgraded_item = self._create_upgraded_item(current_item, next_tier)
    slot.equipped_item = upgraded_item
    
    # Consume materials
    self._consume_upgrade_materials(upgrade_materials, required_materials)
    
    return True
```

## Equipment Events and Notifications

### Equipment Event System
```python
class EquipmentEventType(Enum):
    ITEM_EQUIPPED = "item_equipped"
    ITEM_UNEQUIPPED = "item_unequipped"
    ITEM_BROKEN = "item_broken"
    ITEM_UPGRADED = "item_upgraded"
    SET_BONUS_ACTIVATED = "set_bonus_activated"

def emit_equipment_event(self, event_type: EquipmentEventType, data: Dict):
    """Emit equipment-related events"""
    event_data = {
        'event_type': event_type,
        'timestamp': time.time(),
        **data
    }
    
    # Notify event system
    self.event_manager.emit(event_type.value, event_data)
    
    # Update UI
    self._update_equipment_ui(event_type, event_data)

def on_item_equipped(self, event_data):
    """Handle item equipped event"""
    unit = event_data['unit']
    item = event_data['item']
    slot_type = event_data['slot_type']
    
    # Update unit stats
    self._recalculate_unit_stats(unit)
    
    # Check for set bonuses
    self._check_set_bonuses(unit)
    
    # Notify UI panels
    self._update_character_panel(unit)
    self._update_inventory_panel()
```

## Testing Equipment System

### Equipment Component Tests
```python
def test_equipment_equipping():
    """Test basic equipment functionality"""
    unit = create_test_unit()
    equipment_comp = EquipmentComponent()
    unit.add_component(equipment_comp)
    
    # Test weapon equipping
    spear_data = create_test_spear()
    success = equipment_comp.equip_weapon(spear_data)
    
    assert success
    assert equipment_comp.weapon_slot.equipped_item == spear_data
    
    # Test stat bonuses
    bonuses = equipment_comp.calculate_equipment_bonuses()
    assert bonuses['attack_range'] == 2
    assert bonuses['effect_area'] == 2
    assert bonuses['physical_attack'] == 14

def test_equipment_requirements():
    """Test equipment requirement checking"""
    low_level_unit = create_test_unit(level=1, strength=5)
    equipment_comp = EquipmentComponent()
    
    # High-level weapon should fail
    advanced_weapon = create_test_weapon(requirements={'level': 10, 'strength': 15})
    
    can_equip, reason = equipment_comp.can_equip_weapon(advanced_weapon)
    assert not can_equip
    assert 'level' in reason or 'strength' in reason

def test_set_bonuses():
    """Test equipment set bonus calculation"""
    unit = create_test_unit()
    equipment_comp = EquipmentComponent()
    equipment_manager = EquipmentManager()
    
    # Equip 2 pieces of iron set
    equipment_comp.equip_weapon(create_iron_sword())
    equipment_comp.equip_armor(create_iron_armor())
    
    set_bonuses = equipment_manager.calculate_set_bonuses(unit)
    assert set_bonuses['physical_defense'] == 5  # 2-piece bonus
```

## Best Practices

### Equipment Design
- **Clear Progression** - Obvious upgrade paths and improvements
- **Meaningful Choices** - Different equipment for different playstyles
- **Balance** - No single "best" equipment for all situations
- **Visual Consistency** - Equipment appearance matches its properties

### Performance
- **Efficient Calculations** - Cache equipment bonuses where possible
- **Lazy Updates** - Recalculate stats only when equipment changes
- **Memory Management** - Clean up equipment references properly
- **Asset Loading** - Load equipment data efficiently

### User Experience
- **Clear Feedback** - Show equipment effects clearly
- **Easy Management** - Intuitive equipment interfaces
- **Comparison Tools** - Help players make informed choices
- **Undo Options** - Allow reversing equipment decisions

### Integration
- **Modular Design** - Equipment system works with any unit type
- **Event Driven** - Use events for equipment change notifications
- **Data Driven** - Equipment properties defined in data files
- **Extensible** - Easy to add new equipment types and effects