#!/usr/bin/env uv run
"""
Practice Battle Demo

A demonstration tactical battle using components from the apex-tactics system.
Integrated with the start screen demo for Phase 4.5.

Run with: uv run src/ui/screens/practice_battle.py
"""

import sys
import os
import random
import math
from enum import Enum

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from ursina import *
    from ursina.prefabs.window_panel import WindowPanel
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False
    print("Ursina not available - practice battle cannot run")
    print("Install with: uv add ursina")

# Core game classes adapted from apex-tactics.py
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
        
        # Combat attributes
        self.attack_range = 1  # Default attack range
        self.attack_effect_area = 0  # Default single-target attack (0 means only target tile)
        self.equipped_weapon = None  # Could be expanded later
        
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
        actual_damage = max(1, damage - defense)
        self.hp = max(0, self.hp - actual_damage)
        self.alive = self.hp > 0
        return actual_damage

    def can_move_to(self, x, y, grid):
        distance = abs(x - self.x) + abs(y - self.y)
        return distance <= self.current_move_points and grid.is_valid(x, y)

class BattleGrid:
    def __init__(self, width=8, height=8):
        self.width = width
        self.height = height
        self.units = {}  # Dictionary mapping (x, y) to Unit objects
        
    def place_unit(self, unit, x, y):
        if self.is_valid(x, y) and (x, y) not in self.units:
            # Remove unit from old position if it exists
            old_pos = (unit.x, unit.y)
            if old_pos in self.units and self.units[old_pos] == unit:
                del self.units[old_pos]
            
            # Place unit at new position
            unit.x, unit.y = x, y
            self.units[(x, y)] = unit
            return True
        return False
        
    def is_valid(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height
        
    def get_unit_at(self, x, y):
        return self.units.get((x, y), None)
        
    def remove_unit(self, unit):
        pos = (unit.x, unit.y)
        if pos in self.units and self.units[pos] == unit:
            del self.units[pos]

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

class GridTile(Entity):
    def __init__(self, x, y, **kwargs):
        super().__init__(
            model='cube',
            color=color.gray,
            scale=(0.9, 0.1, 0.9),
            position=(x, 0, y),
            **kwargs
        )
        self.grid_x = x
        self.grid_y = y
        self.default_color = color.gray
        self.highlighted = False
        
    def highlight(self, highlight_color=color.orange):
        self.color = highlight_color
        self.highlighted = True
        
    def clear_highlight(self):
        self.color = self.default_color
        self.highlighted = False

class UnitEntity(Entity):
    def __init__(self, unit, **kwargs):
        super().__init__(
            model='cube',
            color=self._get_unit_color(unit),
            scale=(0.8, 1.5, 0.8),
            position=(unit.x, 0.8, unit.y),
            **kwargs
        )
        self.unit = unit
        
    def _get_unit_color(self, unit):
        unit_colors = {
            UnitType.HEROMANCER: color.red,
            UnitType.UBERMENSCH: color.orange,
            UnitType.SOUL_LINKED: color.cyan,
            UnitType.REALM_WALKER: color.magenta,
            UnitType.WARGI: color.green,
            UnitType.MAGI: color.blue
        }
        return unit_colors.get(unit.type, color.white)
        
    def update_position(self):
        self.position = (self.unit.x, 0.8, self.unit.y)

class PracticeBattle:
    """Practice battle demonstration"""
    
    def __init__(self, on_exit=None):
        if not URSINA_AVAILABLE:
            print("Ursina is required for practice battle")
            return
        
        self.on_exit = on_exit
        
        # Initialize battle systems
        self.grid = BattleGrid(8, 8)
        self.camera_controller = CameraController(8, 8)
        
        # Battle state
        self.selected_unit = None
        self.turn_count = 1
        self.current_player = 1  # 1 or 2
        self.battle_phase = "setup"  # setup, active, ended
        
        # Visual elements
        self.grid_tiles = []
        self.unit_entities = []
        self.info_panel = None
        
        # Create visual elements
        self._create_environment()
        self._create_grid()
        self._create_demo_units()
        self._create_ui()
        
        # Set up camera
        self.camera_controller.update_camera()
        
        print("Practice Battle Started!")
        print("Controls:")
        print("- Left click: Select unit")
        print("- Right click: Move selected unit")
        print("- WASD: Move camera (same as phase4_visual_demo.py)")
        print("- Mouse drag: Rotate camera (orbit mode)")
        print("- 1/2/3: Camera modes (Orbit/Free/Top-down)")
        print("- Scroll: Zoom in/out")
        print("- Space: End turn")
        print("- Enter: Show battle log")
        print("- ESC: Exit battle")
        
    def _create_environment(self):
        """Create battle environment"""
        # Background plane
        Entity(
            model='plane',
            texture='white_cube',
            color=color.dark_gray,
            scale=(20, 1, 20),
            position=(4, -0.1, 4)
        )
        
        # Lighting
        DirectionalLight(y=2, z=-1, rotation=(45, -45, 0))
        AmbientLight(color=color.rgba(100, 100, 100, 100))
        
    def _create_grid(self):
        """Create battle grid tiles"""
        self.grid_tiles = []
        for x in range(self.grid.width):
            row = []
            for y in range(self.grid.height):
                tile = GridTile(x, y)
                tile.on_click = lambda t=tile: self._handle_tile_click(t)
                row.append(tile)
            self.grid_tiles.append(row)
            
    def _create_demo_units(self):
        """Create demonstration units for the battle"""
        # Player 1 units (bottom of grid)
        player1_units = [
            Unit("Alexios", UnitType.HEROMANCER, 1, 0),
            Unit("Kassandra", UnitType.UBERMENSCH, 2, 0),
            Unit("Barnabas", UnitType.WARGI, 3, 0),
        ]
        
        # Player 2 units (top of grid)  
        player2_units = [
            Unit("Deimos", UnitType.SOUL_LINKED, 4, 7),
            Unit("Chrysis", UnitType.MAGI, 5, 7),
            Unit("Stentor", UnitType.REALM_WALKER, 6, 7),
        ]
        
        # Place units on grid and create visual entities
        all_units = player1_units + player2_units
        for unit in all_units:
            self.grid.place_unit(unit, unit.x, unit.y)
            unit_entity = UnitEntity(unit)
            unit_entity.on_click = lambda u=unit: self._handle_unit_click(u)
            self.unit_entities.append(unit_entity)
            
        self.battle_phase = "active"
        
    def _create_ui(self):
        """Create battle UI"""
        # Battle info panel
        self.info_panel = WindowPanel(
            title='Practice Battle - Turn 1',
            content=(
                Text('Practice Battle Tutorial', color=color.white, scale=1.2),
                Text(''),
                Text('Player 1 Turn', color=color.cyan),
                Text('Select a unit to see its stats'),
                Text(''),
                Text('Controls:', color=color.yellow),
                Text('Left click: Select unit'),
                Text('Right click: Move unit'),
                Text('1/2/3: Camera modes'),
                Text('ESC: Exit battle'),
            ),
            popup=False
        )
        
        # Position panel on right side
        self.info_panel.x = 0.7
        self.info_panel.y = 0.2
        self.info_panel.scale = 0.8
        
    def _handle_tile_click(self, tile):
        """Handle clicking on a grid tile"""
        if self.battle_phase != "active":
            return
            
        x, y = tile.grid_x, tile.grid_y
        
        # Clear previous highlights
        self._clear_highlights()
        
        # If we have a selected unit, try to move it
        if self.selected_unit:
            if self.selected_unit.can_move_to(x, y, self.grid) and not self.grid.get_unit_at(x, y):
                self._move_unit(self.selected_unit, x, y)
                self.selected_unit = None
            else:
                print(f"Cannot move to ({x}, {y})")
        
        # Highlight clicked tile
        tile.highlight(color.yellow)
        
    def _handle_unit_click(self, unit):
        """Handle clicking on a unit"""
        if self.battle_phase != "active":
            return
            
        # Clear previous highlights
        self._clear_highlights()
        
        # Select the unit
        self.selected_unit = unit
        
        # Highlight unit's tile
        tile = self.grid_tiles[unit.x][unit.y]
        tile.highlight(color.cyan)
        
        # Highlight movement range
        self._highlight_movement_range(unit)
        
        # Update info panel
        self._update_info_panel()
        
        print(f"Selected {unit.name} ({unit.type.value})")
        
    def _move_unit(self, unit, new_x, new_y):
        """Move a unit to a new position"""
        old_x, old_y = unit.x, unit.y
        
        if self.grid.place_unit(unit, new_x, new_y):
            # Update visual entity
            for entity in self.unit_entities:
                if entity.unit == unit:
                    entity.update_position()
                    break
                    
            # Reduce movement points
            distance = abs(new_x - old_x) + abs(new_y - old_y)
            unit.current_move_points = max(0, unit.current_move_points - distance)
            
            print(f"Moved {unit.name} to ({new_x}, {new_y})")
            
            # Check if turn should end
            if unit.current_move_points == 0:
                self._end_turn()
                
    def _highlight_movement_range(self, unit):
        """Highlight tiles the unit can move to"""
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                if unit.can_move_to(x, y, self.grid) and not self.grid.get_unit_at(x, y):
                    if x != unit.x or y != unit.y:  # Don't highlight current position
                        self.grid_tiles[x][y].highlight(color.green)
                        
    def _clear_highlights(self):
        """Clear all tile highlights"""
        for row in self.grid_tiles:
            for tile in row:
                tile.clear_highlight()
                
    def _update_info_panel(self):
        """Update the information panel"""
        if not self.selected_unit:
            return
            
        unit = self.selected_unit
        content = [
            Text(f'Turn {self.turn_count} - Player {self.current_player}', color=color.cyan, scale=1.2),
            Text(''),
            Text(f'Selected: {unit.name}', color=color.white, scale=1.1),
            Text(f'Type: {unit.type.value.title()}', color=color.light_gray),
            Text(f'Position: ({unit.x}, {unit.y})'),
            Text(''),
            Text('Stats:', color=color.yellow),
            Text(f'HP: {unit.hp}/{unit.max_hp}'),
            Text(f'MP: {unit.mp}/{unit.max_mp}'),
            Text(f'Movement: {unit.current_move_points}/{unit.move_points}'),
            Text(''),
            Text('Attributes:', color=color.orange),
            Text(f'Strength: {unit.strength}'),
            Text(f'Speed: {unit.speed}'),
            Text(f'Wisdom: {unit.wisdom}'),
            Text(''),
            Text('Combat:', color=color.red),
            Text(f'Physical Attack: {unit.physical_attack}'),
            Text(f'Physical Defense: {unit.physical_defense}'),
        ]
        
        # Update panel content
        for child in self.info_panel.content:
            destroy(child)
        self.info_panel.content = content
        self.info_panel.layout()
        
    def _end_turn(self):
        """End current player's turn"""
        print(f"Player {self.current_player} turn ended")
        
        # Reset movement points for all units
        for unit in self.grid.units.values():
            unit.current_move_points = unit.move_points
            
        # Switch players
        self.current_player = 2 if self.current_player == 1 else 1
        if self.current_player == 1:
            self.turn_count += 1
            
        # Clear selection
        self.selected_unit = None
        self._clear_highlights()
        
        # Update UI
        self.info_panel.title = f'Practice Battle - Turn {self.turn_count}'
        
        # Simple AI for player 2 (or manual control)
        if self.current_player == 2:
            print("Player 2 turn (Auto-skip for demo)")
            invoke(self._end_turn, delay=1)  # Auto-end after 1 second
        
    def handle_input(self, key):
        """Handle input for the battle"""
        # Pass camera controls to camera controller
        self.camera_controller.handle_input(key)
        
        # Battle-specific controls
        if key == 'escape':
            self._exit_battle()
        elif key == 'space':
            self._end_turn()
        elif key == 'enter':
            print("Battle log:")
            for unit in self.grid.units.values():
                print(f"  {unit.name}: HP {unit.hp}/{unit.max_hp}, MP {unit.current_move_points}/{unit.move_points}")
                
    def _exit_battle(self):
        """Exit the practice battle"""
        print("Exiting practice battle...")
        
        # Cleanup
        for row in self.grid_tiles:
            for tile in row:
                destroy(tile)
        
        for entity in self.unit_entities:
            destroy(entity)
            
        if self.info_panel:
            destroy(self.info_panel)
            
        # Call exit callback
        if self.on_exit:
            self.on_exit()
            
    def update(self):
        """Update battle state"""
        # Update camera controller
        self.camera_controller.update_camera()
        self.camera_controller.handle_mouse_input()
        
        # WASD Camera movement (same as phase4_visual_demo.py)
        camera_speed = 5
        camera_move = Vec3(0, 0, 0)
        if held_keys['w']:
            camera_move += camera.forward * time.dt * camera_speed
        if held_keys['s']:
            camera_move += camera.back * time.dt * camera_speed
        if held_keys['a']:
            camera_move += camera.left * time.dt * camera_speed
        if held_keys['d']:
            camera_move += camera.right * time.dt * camera_speed
        
        camera.position += camera_move

def run_practice_battle():
    """Run the practice battle as standalone demo"""
    print("Starting Practice Battle Demo")
    print("=" * 40)
    
    if not URSINA_AVAILABLE:
        print("Cannot run practice battle without Ursina. Install with:")
        print("uv add ursina")
        return
    
    # Initialize Ursina
    app = Ursina()
    
    # Set up window
    window.title = "Apex Tactics - Practice Battle"
    window.borderless = False
    window.fullscreen = False
    window.exit_button.visible = False
    
    # Create battle
    battle = PracticeBattle(on_exit=lambda: application.quit())
    
    # Set up input handling
    def input(key):
        battle.handle_input(key)
    
    # Set up update loop with camera controls
    def update():
        battle.update()
        
        # WASD Camera movement (like phase4_visual_demo.py)
        camera_speed = 5
        camera_move = Vec3(0, 0, 0)
        if held_keys['w']:
            camera_move += camera.forward * time.dt * camera_speed
        if held_keys['s']:
            camera_move += camera.back * time.dt * camera_speed
        if held_keys['a']:
            camera_move += camera.left * time.dt * camera_speed
        if held_keys['d']:
            camera_move += camera.right * time.dt * camera_speed
        
        camera.position += camera_move
    
    # Run the application
    try:
        app.run()
    except Exception as e:
        print(f"Practice battle failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Practice battle finished")

if __name__ == "__main__":
    run_practice_battle()