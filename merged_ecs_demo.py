#!/usr/bin/env uv run
"""
Merged ECS Demo

This demo merges the CameraController from apex_ecs_demo_final.py with all the
systems and components referenced in run_modular_demo.py, ensuring full input
functionality is preserved.
"""

import sys
import os
import time
import random
import math
from typing import List, Dict, Optional

# Setup imports - exactly like run_modular_demo.py
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import Ursina
from ursina import *

# Import ECS framework - from run_modular_demo.py
from core.ecs.world import World
from core.ecs.entity import Entity as ECSEntity
from core.math.vector import Vector3, Vector2Int
from core.math.grid import TacticalGrid

# Import components - from run_modular_demo.py
from components.stats.attributes import AttributeStats
from components.combat.attack import AttackComponent
from components.combat.defense import DefenseComponent  
from components.movement.movement import MovementComponent
from components.gameplay.unit_type import UnitTypeComponent, UnitType
from components.gameplay.tactical_movement import TacticalMovementComponent

# Import systems - from run_modular_demo.py
from systems.combat_system import CombatSystem
from game.battle.battle_manager import BattleManager

# Import demo utilities - from run_modular_demo.py
from demos.unit_converter import UnitConverter

app = Ursina()

# Create ground plane
ground = Entity(model='plane', texture='white_cube', color=color.dark_gray, scale=(20, 1, 20), position=(4, -0.1, 4))

# ECS World
ecs_world = World()

class Transform:
    """Simple transform component for position"""
    def __init__(self, position=None):
        self.position = position or Vector3(0, 0, 0)

# CRITICAL: CameraController from apex_ecs_demo_final.py - EXACTLY preserved for input
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

# Visual entity classes - similar to modular demo but enhanced
class GridTileEntity(Entity):
    """Visual representation of grid tiles"""
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
        
    def highlight(self, highlight_color=None):
        if highlight_color is None:
            highlight_color = color.orange
        self.color = highlight_color
        self.highlighted = True
        
    def clear_highlight(self):
        self.color = self.default_color
        self.highlighted = False

class UnitEntityVisual(Entity):
    """Visual representation of game units - enhanced with ECS integration"""
    def __init__(self, game_entity: ECSEntity, **kwargs):
        # Get unit info from ECS components
        unit_type_comp = game_entity.get_component(UnitTypeComponent)
        color_map = {
            UnitType.HEROMANCER: color.red,
            UnitType.UBERMENSCH: color.orange,
            UnitType.SOUL_LINKED: color.cyan,
            UnitType.REALM_WALKER: color.magenta,
            UnitType.WARGI: color.green,
            UnitType.MAGI: color.blue
        }
        unit_color = color_map.get(unit_type_comp.unit_type if unit_type_comp else UnitType.HEROMANCER, color.white)
        
        # Get position from ECS transform
        x, z = 0, 0
        try:
            transform = game_entity.get_component(Transform)
            if transform:
                x, z = transform.position.x, transform.position.z
        except:
            pass
        
        super().__init__(
            model='cube',
            color=unit_color,
            scale=(0.8, 1.5, 0.8),
            position=(x, 0.8, z),
            **kwargs
        )
        
        self.game_entity = game_entity
        self.selected = False
        
        # Add unit name text
        unit_name = f"Unit_{game_entity.id[:6]}"
        if unit_type_comp:
            unit_name = f"{unit_type_comp.unit_type.value.title()}"
        
        self.name_text = Text(
            unit_name,
            position=(0, 1.2, 0),
            scale=3,
            color=color.white,
            parent=self,
            billboard=True
        )
        
    def update_from_entity(self):
        """Update visual from ECS entity state"""
        try:
            transform = self.game_entity.get_component(Transform)
            if transform:
                self.position = (transform.position.x, 0.8, transform.position.z)
        except:
            pass
        
        # Update selection visual
        if self.selected:
            self.scale = (1.0, 1.8, 1.0)
        else:
            self.scale = (0.8, 1.5, 0.8)

class MergedECSDemo:
    """
    Merged demo that combines:
    - CameraController from apex_ecs_demo_final.py
    - All systems and components from run_modular_demo.py
    """
    
    def __init__(self):
        # ECS World - like modular demo
        self.world = World()
        
        # Game systems - from modular demo
        self.battle_manager = BattleManager(self.world)
        self.combat_system = CombatSystem()
        
        # Camera system - EXACT copy from apex_ecs_demo_final.py for input preservation
        self.camera_controller = CameraController(8, 8)
        
        # Grid system - from modular demo
        self.tactical_grid = TacticalGrid(8, 8, cell_size=1.0)
        
        # Game state
        self.game_entities: List[ECSEntity] = []
        self.visual_entities: List[UnitEntityVisual] = []
        self.grid_tiles: List[List[GridTileEntity]] = []
        self.selected_entity: Optional[ECSEntity] = None
        self.current_turn = 0
        
        # UI state
        self.info_panel = None
        
        # Setup demo
        self._setup_scene()
        self._create_grid_visual()
        self._create_demo_units()
        self._create_ui()
        
        print("=== Merged ECS Demo ===")
        print("Combining apex_ecs_demo_final.py camera with modular demo systems")
        print()
        print("Controls:")
        print("  WASD - Move camera")
        print("  Mouse - Look around (hold left button)")
        print("  Left click - Select unit")
        print("  1/2/3 - Camera modes")
        print("  Space - End turn")
        print("  Tab - Show entity info")
        print("  ESC - Exit")
        print()
    
    def _setup_scene(self):
        """Setup basic Ursina scene"""
        window.title = "Merged ECS Demo - Camera + Modular Systems"
        window.borderless = False
        window.fullscreen = False
        window.exit_button.visible = False
        
        # Basic lighting
        DirectionalLight(y=2, z=-1, rotation=(45, -45, 0))
        AmbientLight(color=color.rgba(100, 100, 100, 100))
        
        # Sky
        Sky()
    
    def _create_grid_visual(self):
        """Create visual grid representation"""
        self.grid_tiles = []
        for x in range(8):
            row = []
            for y in range(8):
                tile = GridTileEntity(x, y)
                tile.on_click = lambda t=tile: self._handle_tile_click(t)
                row.append(tile)
            self.grid_tiles.append(row)
    
    def _create_demo_units(self):
        """Create demo units using ECS from modular demo"""
        print("Creating demo units with ECS architecture...")
        
        # Use UnitConverter from modular demo
        self.game_entities = UnitConverter.create_demo_army(self.world, 6)
        
        # Add Transform components and position units
        positions = [(0, 0), (2, 0), (4, 0), (0, 2), (2, 2), (4, 2)]
        for i, game_entity in enumerate(self.game_entities):
            if i < len(positions):
                x, y = positions[i]
                # Add transform component
                transform = Transform(Vector3(x, 0, y))
                game_entity.add_component(transform)
                
                # Create visual representation
                visual_entity = UnitEntityVisual(game_entity)
                visual_entity.on_click = lambda ge=game_entity: self._handle_unit_click(ge)
                self.visual_entities.append(visual_entity)
        
        print(f"Created {len(self.game_entities)} ECS entities with visual representation")
        
        # Show unit information
        for i, entity in enumerate(self.game_entities):
            unit_type_comp = entity.get_component(UnitTypeComponent)
            attributes_comp = entity.get_component(AttributeStats)
            if unit_type_comp and attributes_comp:
                print(f"  {i+1}. {unit_type_comp.unit_type.value.title()} - HP: {attributes_comp.current_hp}")
    
    def _create_ui(self):
        """Create demo UI"""
        try:
            from ursina.prefabs.window_panel import WindowPanel
            
            self.info_panel = WindowPanel(
                title='Merged ECS Demo',
                content=(
                    Text('Camera from apex_ecs_demo_final.py', color=color.white, scale=1.2),
                    Text('Systems from run_modular_demo.py', color=color.white, scale=1.2),
                    Text(''),
                    Text('Select a unit to see ECS components', color=color.light_gray),
                    Text(''),
                    Text('Features:', color=color.yellow),
                    Text('• Preserved input system'),
                    Text('• ECS component architecture'),
                    Text('• Modular systems integration'),
                    Text('• Visual representation'),
                    Text(''),
                    Text('Press Tab for ECS statistics', color=color.cyan),
                ),
                popup=False
            )
            
            # Position panel
            self.info_panel.x = 0.7
            self.info_panel.y = 0.2
            self.info_panel.scale = 0.8
            
        except ImportError:
            print("WindowPanel not available - running without UI")
    
    def _handle_tile_click(self, tile: GridTileEntity):
        """Handle clicking on grid tile"""
        print(f"Clicked tile ({tile.grid_x}, {tile.grid_y})")
        
        # Clear previous highlights
        self._clear_tile_highlights()
        
        # Highlight clicked tile
        tile.highlight(color.yellow)
        
        # If we have a selected unit, try to move it
        if self.selected_entity:
            self._attempt_move_unit(self.selected_entity, tile.grid_x, tile.grid_y)
    
    def _handle_unit_click(self, game_entity: ECSEntity):
        """Handle clicking on unit"""
        print(f"Selected entity: {game_entity.id}")
        
        # Clear previous selection
        if self.selected_entity:
            old_visual = self._get_visual_for_entity(self.selected_entity)
            if old_visual:
                old_visual.selected = False
        
        # Select new entity
        self.selected_entity = game_entity
        visual_entity = self._get_visual_for_entity(game_entity)
        if visual_entity:
            visual_entity.selected = True
        
        # Update UI
        self._update_info_panel()
        
        # Show movement range
        self._show_movement_range(game_entity)
    
    def _attempt_move_unit(self, game_entity: ECSEntity, target_x: int, target_y: int):
        """Attempt to move unit to target position"""
        # Get current position
        transform = game_entity.get_component(Transform)
        if not transform:
            return
        
        current_x, current_y = int(transform.position.x), int(transform.position.z)
        
        # Calculate distance
        distance = abs(target_x - current_x) + abs(target_y - current_y)
        
        # Check movement component
        tactical_movement = game_entity.get_component(TacticalMovementComponent)
        if not tactical_movement:
            print("Unit has no movement component")
            return
        
        if not tactical_movement.can_move(distance):
            print(f"Unit cannot move {distance} tiles (MP: {tactical_movement.current_movement_points})")
            return
        
        # Move unit
        transform.position = Vector3(target_x, 0, target_y)
        tactical_movement.consume_movement(distance)
        print(f"Moved unit to ({target_x}, {target_y})")
        self._update_info_panel()
    
    def _show_movement_range(self, game_entity: ECSEntity):
        """Show movement range for selected unit"""
        self._clear_tile_highlights()
        
        tactical_movement = game_entity.get_component(TacticalMovementComponent)
        transform = game_entity.get_component(Transform)
        if not tactical_movement or not transform:
            return
        
        current_x, current_y = int(transform.position.x), int(transform.position.z)
        movement_range = tactical_movement.get_remaining_movement()
        
        # Highlight tiles in movement range
        for x in range(8):
            for y in range(8):
                distance = abs(x - current_x) + abs(y - current_y)
                if distance <= movement_range and distance > 0:
                    if x < len(self.grid_tiles) and y < len(self.grid_tiles[0]):
                        self.grid_tiles[x][y].highlight(color.green)
        
        # Highlight current position
        if (current_x < len(self.grid_tiles) and current_y < len(self.grid_tiles[0])):
            self.grid_tiles[current_x][current_y].highlight(color.cyan)
    
    def _get_visual_for_entity(self, game_entity: ECSEntity) -> Optional[UnitEntityVisual]:
        """Get visual entity for game entity"""
        for visual in self.visual_entities:
            if visual.game_entity == game_entity:
                return visual
        return None
    
    def _clear_tile_highlights(self):
        """Clear all tile highlights"""
        for row in self.grid_tiles:
            for tile in row:
                tile.clear_highlight()
    
    def _update_info_panel(self):
        """Update info panel with selected entity data"""
        if not self.info_panel or not self.selected_entity:
            return
        
        entity = self.selected_entity
        
        # Get components
        unit_type_comp = entity.get_component(UnitTypeComponent)
        attributes_comp = entity.get_component(AttributeStats)
        tactical_movement_comp = entity.get_component(TacticalMovementComponent)
        
        # Build content
        content = [
            Text(f'Entity: {entity.id[:8]}...', color=color.white, scale=1.2),
            Text(''),
        ]
        
        if unit_type_comp:
            content.extend([
                Text(f'Type: {unit_type_comp.unit_type.value.title()}', color=color.yellow),
                Text(f'Bonuses: {", ".join(unit_type_comp.get_primary_attributes())}'),
                Text(''),
            ])
        
        if attributes_comp:
            content.extend([
                Text('Attributes:', color=color.cyan),
                Text(f'HP: {attributes_comp.current_hp}/{attributes_comp.max_hp}'),
                Text(f'MP: {attributes_comp.current_mp}/{attributes_comp.max_mp}'),
                Text(f'STR: {attributes_comp.strength} | FOR: {attributes_comp.fortitude}'),
                Text(f'WIS: {attributes_comp.wisdom} | SPD: {attributes_comp.speed}'),
                Text(''),
            ])
        
        if tactical_movement_comp:
            content.extend([
                Text('Movement:', color=color.orange),
                Text(f'MP: {tactical_movement_comp.current_movement_points}/{tactical_movement_comp.max_movement_points}'),
                Text(f'AP: {tactical_movement_comp.current_action_points}/{tactical_movement_comp.max_action_points}'),
                Text(''),
            ])
        
        content.extend([
            Text('Components:', color=color.light_gray),
            Text(f'{len(entity._components)} components'),
        ])
        
        # Update panel
        for child in self.info_panel.content:
            destroy(child)
        self.info_panel.content = content
        self.info_panel.layout()
    
    def _end_turn(self):
        """End current turn and refresh units"""
        self.current_turn += 1
        print(f"Turn {self.current_turn} - Refreshing all units")
        
        # Refresh all units
        for entity in self.game_entities:
            tactical_movement = entity.get_component(TacticalMovementComponent)
            if tactical_movement:
                tactical_movement.refresh_for_new_turn()
        
        # Update UI
        self._update_info_panel()
        self._clear_tile_highlights()
    
    def _show_ecs_statistics(self):
        """Show ECS system statistics"""
        print("\n=== ECS Statistics ===")
        
        # Entity manager stats
        entity_stats = self.world.entity_manager.get_statistics()
        print(f"Entities: {entity_stats['active_entities']}")
        print(f"Components: {entity_stats['component_counts']}")
        
        # Conversion stats
        conversion_stats = UnitConverter.get_conversion_statistics(self.game_entities)
        print(f"Unit Types: {conversion_stats['unit_types']}")
        
        # Performance info
        total_entities = len(self.game_entities)
        print(f"Visual Entities: {len(self.visual_entities)}")
        print(f"Grid Tiles: {len(self.grid_tiles) * len(self.grid_tiles[0]) if self.grid_tiles else 0}")
        
        # Component breakdown per entity
        if self.game_entities:
            sample_entity = self.game_entities[0]
            print(f"Sample Entity Components: {[c.__name__ for c in sample_entity._components.values()]}")
        
        print("==================\n")
    
    def _exit_demo(self):
        """Exit the demo"""
        print("Exiting Merged ECS Demo")
        self._show_ecs_statistics()
        application.quit()
    
    def run(self):
        """Start the demo"""
        try:
            # Set initial camera
            self.camera_controller.update_camera()
            
            # Register global input and update functions for Ursina
            self._register_global_functions()
            
            # Run Ursina app
            app.run()
            
        except Exception as e:
            print(f"Demo error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("Demo finished")
    
    def _register_global_functions(self):
        """Register global functions that Ursina expects"""
        demo = self
        
        # Create global input function (must be named 'input' in global scope)
        def global_input(key):
            demo._handle_input(key)
        
        # Create global update function  
        def global_update():
            demo._handle_update()
        
        # Register with the main module's globals (where Ursina will look)
        import __main__
        __main__.input = global_input
        __main__.update = global_update
    
    def _handle_input(self, key):
        """Handle input events - EXACT preservation from apex_ecs_demo_final.py"""
        # Camera controls - preserved exactly
        self.camera_controller.handle_input(key)
        
        # Demo controls
        if key == 'escape':
            self._exit_demo()
        elif key == 'space':
            self._end_turn()
        elif key == 'tab':
            self._show_ecs_statistics()
    
    def _handle_update(self):
        """Handle update events - EXACT preservation from apex_ecs_demo_final.py"""
        # Update camera
        self.camera_controller.update_camera()
        self.camera_controller.handle_mouse_input()
        
        # WASD camera movement (preserved functionality)
        camera_speed = 5
        camera_move = Vec3(0, 0, 0)
        if held_keys['w'] and self.camera_controller.camera_mode != 1:  # Don't interfere with free mode
            camera_move += camera.forward * time.dt * camera_speed
        if held_keys['s'] and self.camera_controller.camera_mode != 1:
            camera_move += camera.back * time.dt * camera_speed
        if held_keys['a'] and self.camera_controller.camera_mode != 1:
            camera_move += camera.left * time.dt * camera_speed
        if held_keys['d'] and self.camera_controller.camera_mode != 1:
            camera_move += camera.right * time.dt * camera_speed
        
        # Only apply movement if not in free camera mode (which handles WASD internally)
        if self.camera_controller.camera_mode != 1:
            camera.position += camera_move
        
        # Update visual entities from game entities
        for visual_entity in self.visual_entities:
            visual_entity.update_from_entity()

# Control Panel for merged demo
class ControlPanel:
    def __init__(self):
        self.last_camera_mode = None
    
    def update_camera_mode(self, mode):
        self.last_camera_mode = mode

# Initialize demo
print("=" * 50)
print("MERGED ECS DEMO")
print("=" * 50)
print("Camera from apex_ecs_demo_final.py")
print("Systems from run_modular_demo.py")
print("Input functionality fully preserved")
print("=" * 50)

# Create control panel
control_panel = ControlPanel()

# Create and run demo
demo = MergedECSDemo()
demo.run()