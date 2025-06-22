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
        self.alive = True
        
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
    def physical_attack(self):
        return (self.speed + self.strength + self.finesse) // 2
        
    @property
    def magical_attack(self):
        return (self.wisdom + self.wonder + self.spirit) // 2
        
    @property
    def spiritual_attack(self):
        return (self.faith + self.fortitude + self.worthy) // 2
        
    def take_damage(self, damage, damage_type="physical"):
        defense = {"physical": self.physical_defense, "magical": self.magical_defense, "spiritual": self.spiritual_defense}[damage_type]
        self.hp = max(0, self.hp - max(1, damage - defense))
        self.alive = self.hp > 0

    def can_move_to(self, x, y, grid):
        return abs(x - self.x) + abs(y - self.y) <= self.ap and grid.is_valid(x, y)

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
            del self.units[(unit.x, unit.y)]
            unit.x, unit.y = x, y
            unit.ap -= abs(x - unit.x) + abs(y - unit.y)
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
        elif key == '2':
            self.camera_mode = 1
            print("Free Camera Mode")
        elif key == '3':
            self.camera_mode = 2
            print("Top-down Camera Mode")
        
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
            position=(x, 0, y)
        )
        self.grid_x, self.grid_y = x, y
        self.original_color = color.light_gray
        
    def input(self, key):
        if key == 'left mouse down':
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
        for unit in self.units:
            self.grid.add_unit(unit)
            self.unit_entities.append(UnitEntity(unit))
            
        self.turn_manager = TurnManager(self.units)
        self.refresh_all_ap()
        
    def handle_tile_click(self, x, y):
        if self.selected_unit:
            if self.grid.move_unit(self.selected_unit, x, y):
                self.update_unit_positions()
                self.clear_highlights()
                self.selected_unit = None
                self.turn_manager.next_turn()
        else:
            if (x, y) in self.grid.units:
                unit = self.grid.units[(x, y)]
                if unit == self.turn_manager.current_unit():
                    self.selected_unit = unit
                    self.highlight_selected_unit()
                    self.highlight_possible_moves()
                    
    def highlight_selected_unit(self):
        if self.selected_unit:
            for entity in self.unit_entities:
                if entity.unit == self.selected_unit:
                    entity.highlight_selected()
                    break
                    
    def highlight_possible_moves(self):
        if self.selected_unit:
            for x in range(self.grid.width):
                for y in range(self.grid.height):
                    if self.selected_unit.can_move_to(x, y, self.grid):
                        tile = self.get_tile_at(x, y)
                        if tile:
                            tile.highlight(color.green)
                            
    def get_tile_at(self, x, y):
        for tile in self.tile_entities:
            if tile.grid_x == x and tile.grid_y == y:
                return tile
        return None
        
    def clear_highlights(self):
        for tile in self.tile_entities:
            tile.unhighlight()
        for entity in self.unit_entities:
            entity.unhighlight()
                    
    def refresh_all_ap(self):
        for unit in self.units:
            unit.ap = unit.max_ap
                    
    def update_unit_positions(self):
        for entity in self.unit_entities:
            entity.position = (entity.unit.x, 1.0, entity.unit.y)

# Initialize game
game = TacticalRPG()

# UI
ui_text = Text("Tactical RPG - Camera Controls", position=(-0.8, 0.48), scale=2, color=color.white)
turn_text = Text("", position=(-0.8, 0.43), scale=1.5, color=color.light_gray)
camera_text = Text("1: Orbit | 2: Free | 3: Top-down", position=(-0.8, 0.38), scale=1, color=color.cyan)
controls_text1 = Text("Orbit: Mouse/Arrows rotate, Scroll zoom", position=(-0.8, 0.33), scale=0.8, color=color.light_gray)
controls_text2 = Text("Free: WASD move, QE up/down, Mouse look", position=(-0.8, 0.28), scale=0.8, color=color.light_gray)
controls_text3 = Text("Top-down: WASD pan", position=(-0.8, 0.23), scale=0.8, color=color.light_gray)
game_text = Text("Click units to select, click tiles to move", position=(-0.8, 0.18), scale=0.8, color=color.yellow)

def input(key):
    # Handle camera controls first
    game.camera_controller.handle_input(key)

def update():
    # Update camera
    game.camera_controller.handle_mouse_input()
    game.camera_controller.update_camera()
    
    # Update UI
    if game.turn_manager and game.turn_manager.current_unit():
        current = game.turn_manager.current_unit()
        turn_text.text = f"{current.name}'s Turn (AP: {current.ap}/{current.max_ap}) | HP: {current.hp}/{current.max_hp}"

# Set initial camera position
game.camera_controller.update_camera()

# Add lighting
DirectionalLight(y=10, z=5)

app.run()
