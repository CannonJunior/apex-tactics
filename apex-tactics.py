from ursina import *
from enum import Enum
import random
import math

app = Ursina()

# Create a simple ground plane for better visibility
ground = Entity(model='plane', texture='white_cube', color=color.dark_gray, scale=(20, 1, 20), position=(4, -0.1, 4))

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

# Camera Control System
class CameraController:
    def __init__(self, grid_width=8, grid_height=8):
        self.grid_center = Vec3(grid_width/2 - 0.5, 0, grid_height/2 - 0.5)
        self.camera_target = Vec3(self.grid_center.x, self.grid_center.y, self.grid_center.z)
        self.camera_distance = 8
        self.camera_angle_x = 30
        self.camera_angle_y = 0
        self.camera_mode = 0  # 0: orbit, 1: free, 2: top-down
        self.move_speed = 0.5
        self.rotation_speed = 50
        
    def update_camera(self):
        if self.camera_mode == 0:  # Orbit mode
            rad_y = math.radians(self.camera_angle_y)
            rad_x = math.radians(self.camera_angle_x)
            
            x = self.camera_target.x + self.camera_distance * math.cos(rad_x) * math.sin(rad_y)
            y = self.camera_target.y + self.camera_distance * math.sin(rad_x)
            z = self.camera_target.z + self.camera_distance * math.cos(rad_x) * math.cos(rad_y)
            
            camera.position = (x, y, z)
            camera.look_at(self.camera_target)
        
        elif self.camera_mode == 1:  # Free camera mode
            pass  # Handled by input functions
        
        elif self.camera_mode == 2:  # Top-down mode
            camera.position = (self.camera_target.x, 12, self.camera_target.z)
            camera.rotation = (90, 0, 0)
    
    def handle_input(self, key):
        # Camera mode switching
        if key == '1':
            self.camera_mode = 0
            print("Orbit Camera Mode")
            control_panel.update_camera_mode(0)
        elif key == '2':
            self.camera_mode = 1
            print("Free Camera Mode")
            control_panel.update_camera_mode(1)
        elif key == '3':
            self.camera_mode = 2
            print("Top-down Camera Mode")
            control_panel.update_camera_mode(2)
        
        # Orbit camera controls
        elif self.camera_mode == 0:
            if key == 'scroll up':
                self.camera_distance = max(3, self.camera_distance - 0.5)
            elif key == 'scroll down':
                self.camera_distance = min(15, self.camera_distance + 0.5)
        
        # Free camera controls
        elif self.camera_mode == 1:
            if key == 'w':
                camera.position += camera.forward * self.move_speed
            elif key == 's':
                camera.position -= camera.forward * self.move_speed
            elif key == 'a':
                camera.position -= camera.right * self.move_speed
            elif key == 'd':
                camera.position += camera.right * self.move_speed
            elif key == 'q':
                camera.position += camera.up * self.move_speed
            elif key == 'e':
                camera.position -= camera.up * self.move_speed
        
        # Top-down camera movement
        elif self.camera_mode == 2:
            if key == 'w':
                self.camera_target.z -= self.move_speed
            elif key == 's':
                self.camera_target.z += self.move_speed
            elif key == 'a':
                self.camera_target.x -= self.move_speed
            elif key == 'd':
                self.camera_target.x += self.move_speed
    
    def handle_mouse_input(self):
        if self.camera_mode == 0:  # Orbit mode
            if held_keys['left mouse']:
                self.camera_angle_y += mouse.velocity.x * 50
                self.camera_angle_x = max(-80, min(80, self.camera_angle_x - mouse.velocity.y * 50))
            
            # Keyboard rotation
            rotation_speed = self.rotation_speed * time.dt
            if held_keys['left arrow']:
                self.camera_angle_y -= rotation_speed
            elif held_keys['right arrow']:
                self.camera_angle_y += rotation_speed
            elif held_keys['up arrow']:
                self.camera_angle_x = max(-80, self.camera_angle_x - rotation_speed)
            elif held_keys['down arrow']:
                self.camera_angle_x = min(80, self.camera_angle_x + rotation_speed)
        
        elif self.camera_mode == 1:  # Free camera mode
            if held_keys['left mouse']:
                camera.rotation_y += mouse.velocity.x * 40
                camera.rotation_x -= mouse.velocity.y * 40
                camera.rotation_x = max(-90, min(90, camera.rotation_x))

# Visual Components
class GridTile(Entity):
    def __init__(self, x, y):
        super().__init__(
            parent=scene,
            model='cube',
            color=color.light_gray,
            scale=(0.9, 0.1, 0.9),
            position=(x, 0, y),
            collider='box'  # Add collider for click detection
        )
        self.grid_x, self.grid_y = x, y
        self.original_color = color.light_gray
        
    def on_click(self):
        print(f"Tile clicked at: ({self.grid_x}, {self.grid_y})")
        game.handle_tile_click(self.grid_x, self.grid_y)
            
    def highlight(self, highlight_color=color.yellow):
        self.color = highlight_color
        
    def unhighlight(self):
        self.color = self.original_color

class UnitEntity(Entity):
    def __init__(self, unit):
        colors = {
            UnitType.HEROMANCER: color.orange, 
            UnitType.UBERMENSCH: color.red, 
            UnitType.SOUL_LINKED: color.light_gray,
            UnitType.REALM_WALKER: color.rgb32(128, 0, 128),
            UnitType.WARGI: color.blue, 
            UnitType.MAGI: color.cyan
        }
        super().__init__(
            parent=scene,
            model='cube',
            color=colors[unit.type],
            scale=(0.8, 2.0, 0.8),
            position=(unit.x, 1.0, unit.y)
        )
        self.unit = unit
        self.original_color = colors[unit.type]
        
    def highlight_selected(self):
        self.color = color.white
        
    def unhighlight(self):
        self.color = self.original_color

# Main Game Controller
class TacticalRPG:
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
        
        self.setup_battle()
        
    def setup_battle(self):
        # Create grid tiles
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                self.tile_entities.append(GridTile(x, y))
                
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
            control_panel.update_unit_info(current_unit)
            
            # Update carousel to show new current turn
            control_panel.update_carousel_highlighting()
            
            print(f"Turn ended. Now it's {current_unit.name}'s turn.")
        
    def handle_tile_click(self, x, y):
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
            control_panel.update_unit_info(clicked_unit)
            
            # Show action modal for the selected unit
            self.show_action_modal(clicked_unit)
        else:
            # Clicked on an empty tile - clear selection
            self.selected_unit = None
            self.current_path = []
            self.path_cursor = None
            self.current_mode = None
            control_panel.update_unit_info(None)
                
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
        if self.selected_unit:
            for entity in self.unit_entities:
                if entity.unit == self.selected_unit:
                    entity.highlight_selected()
                    break
                    
    def highlight_possible_moves(self):
        # This method is now replaced by highlight_movement_range
        self.highlight_movement_range()
                            
    def get_tile_at(self, x, y):
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
            print("Movement mode activated. Use WASD to plan movement, Enter to confirm.")
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
            control_panel.update_unit_info(None)
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
        for tile in self.tile_entities:
            tile.unhighlight()
        for entity in self.unit_entities:
            entity.unhighlight()

    def refresh_all_ap(self):
        for unit in self.units:
            unit.ap = unit.max_ap
            unit.current_move_points = unit.move_points  # Reset movement points

    def update_unit_positions(self):
        for entity in self.unit_entities:
            entity.position = (entity.unit.x, 1.0, entity.unit.y)
from ursina.prefabs.window_panel import WindowPanel

class ControlPanel:
    def __init__(self):
        # Current unit info text
        self.unit_info_text = Text('No unit selected')
        
        # Camera controls text
        self.camera_controls_text = Text('CAMERA: [1] Orbit | [2] Free | [3] Top-down | ACTIVE: Orbit')
        
        # Game controls text
        self.game_controls_text = Text('CONTROLS: Click unit to select | Click tile to move | Mouse/WASD for camera')
        
        # Stats display text
        self.stats_display_text = Text('')
        
        # Unit carousel variables
        self.unit_carousel_icons = []
        self.carousel_container = Entity(parent=camera.ui)
        self.game_reference = None
        
        # Create action buttons first
        self.end_turn_btn = Button(
            text='END TURN',
            color=color.orange
        )
        
        self.attack_btn = Button(
            text='ATTACK',
            color=color.red
        )
        
        self.defend_btn = Button(
            text='DEFEND',
            color=color.blue
        )
        
        # Set up button functionality
        self.end_turn_btn.on_click = self.end_turn_clicked
        self.attack_btn.on_click = self.attack_clicked
        self.defend_btn.on_click = self.defend_clicked
        
        # Create unit carousel label
        self.carousel_label = Text('Turn Order:', parent=camera.ui)
        
        # Create main window panel with all content including buttons
        self.panel = WindowPanel(
            title='Tactical RPG Control Panel',
            content=(
                self.unit_info_text,
                self.camera_controls_text,
                self.game_controls_text,
                self.stats_display_text,
                Text('Actions:'),  # Label for buttons
                self.end_turn_btn,
                self.attack_btn,
                self.defend_btn
            ),
            popup=False
        )
        
        # Position the control panel at the bottom
        self.panel.x = 0
        self.panel.y = -0.3
        
        # Position carousel elements
        self.carousel_label.position = (-0.45, -0.45, 0)
        self.carousel_label.scale = 0.8
        
        # Layout the content within the panel
        self.panel.layout()
    
    def end_turn_clicked(self):
        print("End Turn button clicked!")
        if hasattr(self, 'game_reference') and self.game_reference:
            self.game_reference.end_current_turn()
    
    def attack_clicked(self):
        print("Attack button clicked!")
        # TODO: Implement attack functionality
    
    def defend_clicked(self):
        print("Defend button clicked!")
        # TODO: Implement defend functionality
    
    def set_game_reference(self, game):
        """Set reference to the main game object for button interactions"""
        self.game_reference = game
        # Initialize carousel with game units
        if game and hasattr(game, 'turn_manager') and game.turn_manager:
            self.create_unit_carousel()
    
    def create_unit_carousel(self):
        """Create carousel of unit icons in turn order"""
        if not self.game_reference or not self.game_reference.turn_manager:
            return
        
        # Clear existing carousel
        self.clear_carousel()
        
        # Get units in turn order
        units_in_order = self.game_reference.turn_manager.units
        
        # Create icon for each unit
        for i, unit in enumerate(units_in_order):
            unit_icon = self.create_unit_icon(unit, i)
            self.unit_carousel_icons.append(unit_icon)
        
        print(f"Created unit carousel with {len(self.unit_carousel_icons)} units")
    
    def create_unit_icon(self, unit, index):
        """Create a single unit icon for the carousel"""
        # Calculate position (spacing icons horizontally)
        icon_size = 0.06
        icon_spacing = 0.07
        start_x = -0.3  # Start position
        icon_x = start_x + (index * icon_spacing)
        icon_y = -0.45
        
        # Determine icon color based on unit type and status
        icon_color = self.get_unit_icon_color(unit)
        
        # Create the icon as a clickable button
        unit_icon = Button(
            parent=self.carousel_container,
            model='cube',
            texture='white_cube',
            color=icon_color,
            scale=icon_size,
            position=(icon_x, icon_y, 0)
        )
        
        # Set up click callback
        unit_icon.on_click = lambda u=unit: self.on_unit_icon_clicked(u)
        
        # Store unit reference
        unit_icon.unit = unit
        
        # Add unit name text below icon
        unit_name_text = Text(
            text=unit.name[:4],  # Abbreviate long names
            parent=self.carousel_container,
            position=(icon_x, icon_y - 0.04, 0),
            scale=0.5,
            origin=(0, 0)
        )
        
        # Store text reference for cleanup
        unit_icon.name_text = unit_name_text
        
        return unit_icon
    
    def get_unit_icon_color(self, unit):
        """Get color for unit icon based on unit type and status"""
        # Current turn unit gets special highlighting
        if (self.game_reference and 
            self.game_reference.turn_manager and 
            self.game_reference.turn_manager.current_unit() == unit):
            return color.yellow
        
        # Color by unit type
        type_colors = {
            UnitType.HEROMANCER: color.blue,
            UnitType.UBERMENSCH: color.red,
            UnitType.SOUL_LINKED: color.magenta,
            UnitType.REALM_WALKER: color.green,
            UnitType.WARGI: color.orange,
            UnitType.MAGI: color.cyan
        }
        
        base_color = type_colors.get(unit.type, color.gray)
        
        # Dim color if unit is low on health
        if unit.hp < unit.max_hp * 0.3:
            return color.rgb(base_color.r * 0.5, base_color.g * 0.5, base_color.b * 0.5)
        
        return base_color
    
    def create_unit_tooltip(self, unit):
        """Create tooltip text for unit icon"""
        weapon_name = unit.equipped_weapon['name'] if unit.equipped_weapon else 'None'
        tooltip_text = f"{unit.name} ({unit.type.value})\n"
        tooltip_text += f"HP: {unit.hp}/{unit.max_hp}\n"
        tooltip_text += f"MP: {unit.current_move_points}/{unit.move_points}\n"
        tooltip_text += f"Weapon: {weapon_name}"
        return tooltip_text
    
    def on_unit_icon_clicked(self, unit):
        """Handle clicking on a unit icon"""
        if self.game_reference:
            print(f"Unit icon clicked: {unit.name}")
            
            # Select the unit in the game
            self.game_reference.selected_unit = unit
            
            # Update UI to show selected unit
            self.update_unit_info(unit)
            
            # Highlight the unit on the battlefield
            self.game_reference.clear_highlights()
            self.game_reference.highlight_selected_unit()
            self.game_reference.highlight_movement_range()
            
            # Update carousel to reflect current selection
            self.update_carousel_highlighting()
    
    def update_carousel_highlighting(self):
        """Update carousel icon highlighting to show current turn and selection"""
        if not self.unit_carousel_icons or not self.game_reference:
            return
        
        current_turn_unit = None
        if self.game_reference.turn_manager:
            current_turn_unit = self.game_reference.turn_manager.current_unit()
        
        selected_unit = self.game_reference.selected_unit
        
        for icon in self.unit_carousel_icons:
            unit = icon.unit
            
            # Determine icon color
            if unit == current_turn_unit:
                icon.color = color.yellow  # Current turn
            elif unit == selected_unit:
                icon.color = color.white   # Selected
            else:
                icon.color = self.get_unit_icon_color(unit)  # Default
    
    def clear_carousel(self):
        """Clear all carousel icons"""
        for icon in self.unit_carousel_icons:
            if hasattr(icon, 'name_text'):
                destroy(icon.name_text)
            destroy(icon)
        self.unit_carousel_icons.clear()
    
    def update_carousel(self):
        """Update carousel when units or turn order changes"""
        if self.game_reference and self.game_reference.turn_manager:
            self.create_unit_carousel()
    
    def cleanup_carousel(self):
        """Clean up carousel resources"""
        self.clear_carousel()
        if self.carousel_container:
            destroy(self.carousel_container)
        if self.carousel_label:
            destroy(self.carousel_label)
    
    def update_unit_info(self, unit):
        if unit:
            # Get weapon info
            weapon_name = unit.equipped_weapon['name'] if unit.equipped_weapon else 'None'
            range_info = f"Range: {unit.attack_range} | Area: {unit.attack_effect_area}"
            
            self.unit_info_text.text = f"ACTIVE: {unit.name} ({unit.type.value}) | MP: {unit.current_move_points}/{unit.move_points} | HP: {unit.hp}/{unit.max_hp}"
            self.stats_display_text.text = f"WEAPON: {weapon_name} | {range_info}\nATK - Physical: {unit.physical_attack} | Magical: {unit.magical_attack} | Spiritual: {unit.spiritual_attack}\nDEF - Physical: {unit.physical_defense} | Magical: {unit.magical_defense} | Spiritual: {unit.spiritual_defense}"
        else:
            self.unit_info_text.text = "No unit selected"
            self.stats_display_text.text = ""
        
        # Re-layout after text changes
        self.panel.layout()
        
        # Update carousel highlighting
        self.update_carousel_highlighting()
    
    def update_camera_mode(self, mode):
        mode_names = ["Orbit", "Free", "Top-down"]
        self.camera_controls_text.text = f"CAMERA: [1] Orbit | [2] Free | [3] Top-down | ACTIVE: {mode_names[mode]}"
        
        # Re-layout after text changes
        self.panel.layout()

# Create control panel
control_panel = ControlPanel()

def input(key):
    # Handle path movement for selected unit ONLY if in move mode
    if (game.selected_unit and game.current_mode == "move" and 
        key in ['w', 'a', 's', 'd', 'enter']):
        game.handle_path_movement(key)
        return  # Don't process camera controls if unit is selected and WASD/Enter is pressed
    
    # Handle camera controls only if not handling unit movement
    game.camera_controller.handle_input(key)

# Initialize game
game = TacticalRPG()

# Set game reference for control panel
control_panel.set_game_reference(game)

def update():
    # Update camera
    game.camera_controller.handle_mouse_input()
    game.camera_controller.update_camera()
    
    # Update control panel with current unit info
    if game.turn_manager and game.turn_manager.current_unit() and not game.selected_unit:
        control_panel.update_unit_info(game.turn_manager.current_unit())

# Set initial camera position
game.camera_controller.update_camera()

# Add lighting
DirectionalLight(y=10, z=5)

app.run()
