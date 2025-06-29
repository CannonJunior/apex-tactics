import random
from .unit_types import UnitType

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
        
        # Combat attributes - base values
        self.base_attack_range = 1  # Default attack range
        self.base_attack_effect_area = 0  # Default single-target attack (0 means only target tile)
        
        # Equipment slots
        self.equipped_weapon = None
        self.equipped_armor = None
        self.equipped_accessory = None
        
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
    def attack_range(self):
        """Get current attack range including weapon bonuses"""
        base_range = self.base_attack_range
        
        # Add weapon range bonus
        if self.equipped_weapon and isinstance(self.equipped_weapon, dict) and 'stats' in self.equipped_weapon:
            weapon_range = self.equipped_weapon['stats'].get('attack_range', 0)
            return max(base_range, weapon_range)  # Use higher value
        
        return base_range
    
    @property
    def attack_effect_area(self):
        """Get current attack effect area including weapon bonuses"""
        base_area = self.base_attack_effect_area
        
        # Add weapon area bonus
        if self.equipped_weapon and isinstance(self.equipped_weapon, dict) and 'stats' in self.equipped_weapon:
            weapon_area = self.equipped_weapon['stats'].get('effect_area', 0)
            return max(base_area, weapon_area)  # Use higher value
        
        return base_area
    
    @property
    def physical_attack(self):
        base_attack = (self.speed + self.strength + self.finesse) // 2
        
        # Add weapon attack bonus
        if self.equipped_weapon and isinstance(self.equipped_weapon, dict) and 'stats' in self.equipped_weapon:
            weapon_attack = self.equipped_weapon['stats'].get('physical_attack', 0)
            base_attack += weapon_attack
        
        return base_attack
        
    @property
    def magical_attack(self):
        base_attack = (self.wisdom + self.wonder + self.spirit) // 2
        
        # Add weapon magical attack bonus
        if self.equipped_weapon and isinstance(self.equipped_weapon, dict) and 'stats' in self.equipped_weapon:
            weapon_attack = self.equipped_weapon['stats'].get('magical_attack', 0)
            base_attack += weapon_attack
        
        return base_attack
        
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
    
    def equip_weapon(self, weapon_data):
        """
        Equip a weapon and update combat stats.
        
        Args:
            weapon_data: Weapon data from asset system or dict with stats
            
        Returns:
            True if weapon was equipped successfully
        """
        if isinstance(weapon_data, dict) and weapon_data.get('type') == 'Weapons':
            self.equipped_weapon = weapon_data
            print(f"{self.name} equipped {weapon_data['name']}")
            return True
        return False
    
    def equip_armor(self, armor_data):
        """
        Equip armor and update defensive stats.
        
        Args:
            armor_data: Armor data from asset system
            
        Returns:
            True if armor was equipped successfully
        """
        if isinstance(armor_data, dict) and armor_data.get('type') == 'Armor':
            self.equipped_armor = armor_data
            print(f"{self.name} equipped {armor_data['name']}")
            return True
        return False
    
    def equip_accessory(self, accessory_data):
        """
        Equip an accessory and update stats.
        
        Args:
            accessory_data: Accessory data from asset system
            
        Returns:
            True if accessory was equipped successfully
        """
        if isinstance(accessory_data, dict) and accessory_data.get('type') == 'Accessories':
            self.equipped_accessory = accessory_data
            print(f"{self.name} equipped {accessory_data['name']}")
            return True
        return False
    
    def get_equipment_summary(self):
        """Get summary of equipped items"""
        return {
            'weapon': self.equipped_weapon['name'] if self.equipped_weapon else 'None',
            'armor': self.equipped_armor['name'] if self.equipped_armor else 'None',
            'accessory': self.equipped_accessory['name'] if self.equipped_accessory else 'None'
        }